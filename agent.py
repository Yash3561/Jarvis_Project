# agent.py (V4 - Refactored with a Clean Tool Architecture)

import asyncio
import threading
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

# --- NEW: Import from our clean, consolidated tool files ---
from tools import browser, desktop, developer, file_system, memory, terminal
from tools.interaction_tools import wait_for_user_confirmation, ask_user_for_help

class AIAgent:
    def __init__(self, data_directory="./data"):
        print("INFO: V4 Agent Initializing: Setting up expert toolsets...")
        
        # --- (1) DEFINE YOUR EXPERT TOOLKITS using the new modules ---
        personal_query_engine = self._get_personal_query_engine(data_directory)
        
        # DEVELOPER: For writing, reviewing, and executing code.
        self.developer_tools = [
            FunctionTool.from_defaults(fn=developer.generate_code, name="generate_code"),
            FunctionTool.from_defaults(fn=developer.review_and_refine_code, name="review_code"),
            FunctionTool.from_defaults(fn=ask_user_for_help, name="ask_user_for_help"),
            # The 'run_command' tool in terminal.py is now the primary way to run scripts.
        ]
        
        self.interaction_tools = [
            FunctionTool.from_defaults(fn=wait_for_user_confirmation, name="wait_for_user_confirmation"),
            FunctionTool.from_defaults(fn=ask_user_for_help, name="ask_user_for_help"),
        ]
        
        # BROWSER: For all web interaction, from search to deep automation.
        self.browser_tools = [
            FunctionTool.from_defaults(fn=browser.search_web, name="search_web"),
            FunctionTool.from_defaults(fn=browser.browse_and_summarize, name="browse_and_summarize"),
            FunctionTool.from_defaults(fn=browser.navigate_to, name="navigate_to_url"),
            FunctionTool.from_defaults(fn=browser.type_into, name="type_into_browser"),
            FunctionTool.from_defaults(fn=browser.click_element, name="click_browser_element"),
            FunctionTool.from_defaults(fn=browser.read_element_text, name="read_browser_element"),
            FunctionTool.from_defaults(fn=browser.open_url, name="open_url_in_browser"),
            FunctionTool.from_defaults(fn=browser.close_browser, name="close_automation_browser"),
        ]
        
        # DESKTOP: For controlling the mouse, keyboard, and seeing the screen.
        self.desktop_tools = [
            FunctionTool.from_defaults(fn=desktop.analyze_entire_screen, name="analyze_screen"),
            FunctionTool.from_defaults(fn=desktop.find_on_screen, name="find_on_screen"),
            FunctionTool.from_defaults(fn=desktop.move_mouse, name="move_mouse"),
            FunctionTool.from_defaults(fn=desktop.click, name="click_mouse"),
            FunctionTool.from_defaults(fn=desktop.type_text, name="type_text"),
            FunctionTool.from_defaults(fn=desktop.press_keys, name="press_hotkey"),
        ]

        # --- (2) DEFINE FOUNDATIONAL TOOLKITS (Often available) ---
        
        # FILE SYSTEM: Core file operations, including image files.
        self.file_system_tools = [
            FunctionTool.from_defaults(fn=file_system.list_files, name="list_files"),
            FunctionTool.from_defaults(fn=file_system.read_file, name="read_file"),
            FunctionTool.from_defaults(fn=file_system.write_file, name="write_file"),
            FunctionTool.from_defaults(fn=file_system.create_directory, name="create_directory"),
            FunctionTool.from_defaults(fn=file_system.delete_file, name="delete_file"),
            FunctionTool.from_defaults(fn=file_system.save_screenshot, name="save_screenshot"),
            FunctionTool.from_defaults(fn=file_system.analyze_image, name="analyze_image_file"),
        ]

        # MEMORY: Saving and recalling past experiences.
        self.memory_tools = [
            FunctionTool.from_defaults(fn=memory.save_experience, name="save_experience"),
            FunctionTool.from_defaults(fn=memory.recall_experiences, name="recall_experiences"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
        ]
        
        # TERMINAL: For running commands and managing workspaces/projects.
        self.terminal_tools = [
            FunctionTool.from_defaults(fn=terminal.launch_application, name="launch_application"),
            FunctionTool.from_defaults(fn=terminal.create_headless_terminal, name="create_headless_terminal"),
            FunctionTool.from_defaults(fn=terminal.run_command_in_terminal, name="run_command"),
            FunctionTool.from_defaults(fn=terminal.start_server_in_terminal, name="start_server"),
        ]
        
        # This is the short-term conversation memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    # --- Pass-through methods for the MainController ---
    # These allow the controller to call tools without being coupled to the tools module itself.
    def write_file(self, file_path: str, content: str) -> str:
        return file_system.write_file(file_path, content)

    def run_command(self, command: str, terminal_name: str = "default") -> str:
        return terminal.run_command(command, terminal_name)
    
    def create_terminal(self, name: str) -> str:
        return terminal.create_terminal(name)
        
    def start_background_process(self, command: str, terminal_name: str) -> str:
        return terminal.start_background_process(command, terminal_name)
    
    def launch_application(self, command: str) -> str:
        """A direct pass-through to the terminal tool for the controller."""
        return terminal.launch_application(command)

    
    # --- The rest of your agent.py logic ---
    # The _get_personal_query_engine, _route_query, _summarize_and_save_turn, 
    # ask, execute_task, and reset_memory methods can remain largely the same,
    # but the router needs to be updated.

    def _get_personal_query_engine(self, data_directory):
        print("INFO: Loading knowledge from personal documents...")
        try:
            documents = SimpleDirectoryReader(data_directory).load_data()
            index = VectorStoreIndex.from_documents(documents)
            return index.as_query_engine()
        except Exception as e:
            print(f"WARNING: Could not load personal documents from '{data_directory}'. Knowledge base will be empty. Error: {e}")
            # Return a dummy query engine
            return VectorStoreIndex.from_documents([]).as_query_engine()

    def _route_query(self, query: str) -> list:
        """
        Routes the user's query to the most appropriate toolset.
        """
        tool_descriptions = {
            "Developer": "For writing, reviewing, or executing code and scripts.",
            "Browser": "For searching the web, browsing websites, scraping content, or performing complex browser automation.",
            "Desktop": "For analyzing the screen or controlling the mouse and keyboard to interact with GUI applications.",
            "FileSystem": "For creating, reading, listing, or managing files and directories on the local disk.",
            "Memory": "For saving new information to long-term memory or recalling past experiences.",
            "Terminal": "For executing shell commands, creating concurrent terminals, and managing system processes. Ideal for 'Project' work.",
            "KnowledgeBase": "For answering questions about myself, my capabilities, or information from personal documents.",
            "Conversational": "For general greetings, small talk, or simple acknowledgments that do not require tool usage.",
        }

        prompt = f"""
        Given the user's query, determine the single best tool category to handle the request.
        The available categories are:
        {tool_descriptions}

        User Query: "{query}"
        
        Output ONLY the exact category name (e.g., 'Developer', 'Browser', 'Terminal').
        """

        response = Settings.llm.complete(prompt)
        choice = response.text.strip().replace("'", "").replace("`", "")
        
        print(f"INFO: Router chose category: '{choice}' for the query.")

        if choice == "Developer":
            return self.developer_tools
        elif choice == "Browser":
            return self.browser_tools
        elif choice == "Desktop":
            return self.desktop_tools
        elif choice == "FileSystem":
            return self.file_system_tools
        elif choice == "Memory":
            return self.memory_tools
        elif choice == "Terminal":
            return self.terminal_tools
        elif choice == "KnowledgeBase":
            return self.memory_tools # Assuming personal_knowledge_base is part of memory_tools
        elif choice == "Conversational":
            return [] # No tools needed
        else:
            print(f"WARN: Router returned unrecognized category '{choice}'. Defaulting to general tools.")
            # A safe default fallback
            return self.browser_tools + self.file_system_tools
        
    async def ask(self, question):
        # This entire method can remain exactly as it was.
        # It's already designed to work with whatever tools the router provides.
        # No changes needed here.
        raw_response_str = ""
        try:
            print(f"\n[User Query]: {question}")
            specialist_tools = self._route_query(question)
            
            if not specialist_tools:
                print("INFO: Handling conversational query directly.")
                simple_response = Settings.llm.chat([ChatMessage(role=MessageRole.USER, content=f"You are a helpful assistant. Respond naturally and concisely to: '{question}'")])
                simple_response_text = simple_response.message.content.strip()
                
                final_formatted_response = f"<SPOKEN_SUMMARY>{simple_response_text}</SPOKEN_SUMMARY><FULL_RESPONSE>{simple_response_text}</FULL_RESPONSE>"
                
                self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
                self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=simple_response_text))
                
                return final_formatted_response

            foundational_tools = self.file_system_tools + self.memory_tools

            # If the specialist toolkit is for browsing or requires facts, ensure web tools are included.
            if specialist_tools is self.browser_tools or specialist_tools is self.memory_tools:
                foundational_tools += self.browser_tools
                        
            # Combine the specialist and foundational tools, removing duplicates.
            final_tools = specialist_tools + foundational_tools
            final_tools = list({tool.metadata.name: tool for tool in final_tools}.values())
            
            chat_history = self.memory.get_all()

            print(f"INFO: Deploying agent with tools: {[t.metadata.name for t in final_tools]}")
            
            expert_system_prompt = f"""
You are Jarvis, a hyper-intelligent AI assistant. Your goal is to assist the user by reasoning, planning, and executing tasks using your available tools.

## CORE PRINCIPLES ##
1.  **Reason First:** Before acting, think step-by-step about the user's intent. Your thought process should be logical and clear.
2.  **Use Your Senses:** For desktop tasks, start by using `analyze_screen` to understand your environment. Don't guess where a button is; see what's actually on the screen.
3.  **Be Precise:** When using tools like `click_element` or `type_into_browser`, use specific and unique identifiers (like CSS selectors). For desktop `click_mouse`, use coordinates found with `find_on_screen`.
4.  **Stateful Interaction:** You have a single browser for automation (`_BROWSER_INSTANCE`). If the user asks you to do something on a webpage, assume it's the one you already have open. Only open a new page with `navigate_to_url` if necessary. Use `close_automation_browser` when you are completely finished with a browser task.
5.  **Confirm and Clarify:** If a user's request is ambiguous (e.g., "click the button"), ask for clarification ("Which button? The blue 'Submit' button or the red 'Cancel' button?").

You are now in control. Analyze the user's request and begin.
"""
            # --- END OF ADDITION ---
            
            agent = ReActAgent(
                    tools=final_tools,
                    llm=Settings.llm,
                    memory=self.memory,
                    system_prompt=expert_system_prompt, # Pass the new prompt here
                    verbose=True
                )
            
            response = await agent.run(question, chat_history=chat_history)
            raw_response_str = str(response)

            print("INFO: Post-processing final response for formatting...")
            formatting_prompt = f"""
            You are a formatting assistant. Your job is to take a raw response from an AI agent and reformat it into a clean, two-part response using the provided XML template.
            1.  **Spoken Summary:** Create a concise, conversational, one-sentence summary of the action taken. This is what the text-to-speech engine will say. Start with phrases like "Okay, I've...", "Done. The...", "Here is the...".
            2.  **Full Response:** This is the detailed, written response for the user to read. Preserve all important details, code blocks, and file names from the raw response. Format it nicely using Markdown.

            Raw Agent Response: {raw_response_str}

            RESPONSE TEMPLATE:
            <SPOKEN_SUMMARY>A brief, friendly summary of what was done.</SPOKEN_SUMMARY>
            <FULL_RESPONSE>The full, detailed, markdown-formatted answer with all necessary information.</FULL_RESPONSE>
            """
            final_formatted_response = Settings.llm.complete(formatting_prompt).text
            
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=raw_response_str))
            
            return final_formatted_response
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"<SPOKEN_SUMMARY>An error occurred.</SPOKEN_SUMMARY><FULL_RESPONSE>ERROR: {e}\n{traceback.format_exc()}</FULL_RESPONSE>"
        finally:
            if raw_response_str:
                memory_thread = threading.Thread(target=self._summarize_and_save_turn, args=(question, raw_response_str), daemon=True)
                memory_thread.start()

    def _summarize_and_save_turn(self, query, response):
        # This method can also remain as it was.
        try:
            if "error" in response.lower() or len(query) < 10:
                return
            
            summarization_prompt = f"""Create a concise, one-sentence summary of the key fact or conclusion from this user query and AI response.
            User Query: "{query}"
            AI Response: "{response}"
            Summary:"""
            summary = Settings.llm.complete(summarization_prompt).text.strip()
            memory.save_experience(f"On the topic of '{query}', it was concluded that: {summary}", f"FULL_RESPONSE:\n{response}")
        except Exception as e:
            print(f"WARN: Auto-summary failed. {e}")
    
    def reset_memory(self):
        self.memory.reset()