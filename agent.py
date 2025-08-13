# agent.py (The Definitive V3 - Hierarchical Agent Architecture)

import asyncio
import threading
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

# --- Import ALL your tool functions. This list must be complete. ---
from tools.file_system import read_file_content, list_files_in_directory, write_to_file, create_directory
from tools.screen_reader import analyse_screen_with_gemini, save_screenshot_to_file, analyze_image_file
from tools.web_search import search_the_web
from tools.code_writer import generate_code, review_and_refine_code
from tools.system_commands import run_shell_command, get_current_datetime, get_time_for_location, get_timestamp
from tools.browser_tool import browse_and_summarize_website
from tools.browser_automation import navigate, type_text, click, extract_text_from_element
from tools.persistent_terminal import run_in_terminal
from tools.long_term_memory import save_experience, recall_experiences
from tools.script_runner import run_python_script
from tools.process_manager import start_background_process, check_process_status, stop_background_process

# ADD the new, consolidated tool imports
from tools.workspace_tools import create_terminal, run_command

class AIAgent:
    def __init__(self, data_directory="./data"):
        print("INFO: V3 Agent Initializing: Setting up expert toolsets...")
        
        # --- (1) DEFINE YOUR EXPERT TOOLKITS ---
        personal_query_engine = self._get_personal_query_engine(data_directory)
        
        self.coding_tools = [
            FunctionTool.from_defaults(fn=generate_code, name="code_writer"),
            FunctionTool.from_defaults(fn=review_and_refine_code, name="code_reviewer"),
            FunctionTool.from_defaults(fn=run_python_script, name="run_python_script"),
        ]
        
        self.web_tools = [
            FunctionTool.from_defaults(fn=search_the_web, name="fact_checker"),
            FunctionTool.from_defaults(fn=browse_and_summarize_website, name="browse_website"),
            FunctionTool.from_defaults(fn=navigate, name="navigate_to_url"),
            FunctionTool.from_defaults(fn=type_text, name="type_into_browser"),
            FunctionTool.from_defaults(fn=click, name="click_browser_element"),
        ]
        
        self.vision_tools = [
            FunctionTool.from_defaults(fn=analyze_image_file, name="analyze_image_file"),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_entire_screen"),
        ]

        # --- (2) DEFINE FOUNDATIONAL TOOLKITS (Always available) ---
        self.file_management_tools = [
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files"),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file"),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file"),
            # FunctionTool.from_defaults(fn=create_directory, name="create_directory"),
        ]

        self.memory_tools = [
            FunctionTool.from_defaults(fn=save_experience, name="save_experience"),
            FunctionTool.from_defaults(fn=recall_experiences, name="recall_experiences"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
        ]
        
        self.system_tools = [
            FunctionTool.from_defaults(fn=run_shell_command, name="run_shell_command"),
            FunctionTool.from_defaults(fn=create_terminal, name="create_terminal"),
            FunctionTool.from_defaults(fn=get_current_datetime, name="get_current_datetime"),
        ]
        
        self.process_management_tools = [
            FunctionTool.from_defaults(fn=start_background_process),
            FunctionTool.from_defaults(fn=check_process_status),
            FunctionTool.from_defaults(fn=stop_background_process),
        ]
        
        # This is the short-term conversation memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    def write_file(self, file_path: str, content: str) -> str:
        """A direct pass-through to the file writing tool for the controller."""
        return write_to_file(file_path, content)
    
    def _get_personal_query_engine(self, data_directory):
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        return index.as_query_engine()

    def _route_query(self, query: str) -> list:
        """
        The CEO's router. This version is robust and understands verbose LLM responses.
        """
        tool_descriptions = {
            "FileManagement": "For creating, reading, listing, or managing files and directories.",
            "Coding": "For writing, reviewing, or executing Python code and scripts.",
            "Web": "For searching the web, browsing websites, or checking facts online.",
            "Vision": "For analyzing the contents of specific image files or the entire screen.",
            "Memory": "For saving new information or recalling past experiences and knowledge.",
             "System": "For creating or interacting with stateful, named terminal sessions using commands like `create_terminal` and `run_command`.",
            "KnowledgeBase": "For answering questions about my personal documents (resume, strengths, etc.).",
            "ProcessManagement": "For starting, stopping, or checking long-running background processes like web servers.",
        }

        prompt = f"""
        Given the user's query, determine the single best tool category to handle the request.
        The available categories are:
        {tool_descriptions}

        User Query: "{query}"

        Based on the query, the single most appropriate category is:
        """

        response = Settings.llm.complete(prompt)
        # Clean up the response to get just the category name, just in case
        raw_choice = response.text.strip().replace("'", "").replace("`", "")
        
        print(f"INFO: Router chose category: '{raw_choice}' for the query.")

        # --- THE FIX: Use 'in' instead of '==' for robust matching ---
        # This correctly handles cases where the LLM adds extra explanations.
        if "FileManagement" in raw_choice:
            return self.file_management_tools
        elif "Coding" in raw_choice:
            return self.coding_tools
        elif "Web" in raw_choice:
            return self.web_tools
        elif "Vision" in raw_choice:
            return self.vision_tools
        elif "Memory" in raw_choice:
            return self.memory_tools
        elif "System" in raw_choice:
            return self.system_tools
        elif "KnowledgeBase" in raw_choice:
            return self.knowledge_base_tools
        else:
            print(f"WARN: Router returned ambiguous category '{raw_choice}'. Defaulting to general tools.")
            # We also give it the web tools as a safe fallback for general questions.
            return self.file_management_tools + self.system_tools + self.web_tools
        
    def run_in_terminal(self, command: str) -> str:
        """A direct pass-through to the terminal tool for the controller."""
        return run_in_terminal(command)
    
    def create_terminal(self, name: str) -> str:
        """Direct pass-through to the workspace tool for the controller."""
        return create_terminal(name)

    def run_command(self, command: str, terminal_name: str = "default") -> str:
        """Direct pass-through to the workspace tool for the controller."""
        return run_command(command, terminal_name)
    
    def _summarize_and_save_turn(self, query, response):
        """
        A background task to summarize the conversation turn and save it to long-term memory.
        """
        print("INFO: Auto-summarizing turn for long-term memory...")
        try:
            if "ERROR" in response or len(query) < 15:
                print("INFO: Skipping memory save for short query or error.")
                return

            summarization_prompt = f"""
            Based on the following user query and AI response, create a concise, one-sentence summary of the key fact or conclusion.
            This summary will be saved to a long-term knowledge base.

            User Query: "{query}"
            AI Response: "{response}"

            Concise Summary:
            """
            summary_response = Settings.llm.complete(summarization_prompt).text.strip()

            # --- THE FINAL FIX ---
            # Call save_experience with POSITIONAL arguments, not keyword arguments.
            # The first argument is the summary, the second is the supporting data.
            save_experience(
                f"User asked about '{query}'. Key conclusion: {summary_response}",
                response
            )
        except Exception as e:
            print(f"WARN: Auto-summary failed. {e}")

    async def ask(self, question):
        """
        The Definitive V4 'ask' method. It combines the CEO/Router architecture
        with robust execution, guaranteed formatting, auto-memory, and universal
        web access for all specialized agents.
        """
        raw_response_str = ""  # Initialize for the 'finally' block
        try:
            print(f"\n[User Query]: {question}")
            
            # --- STEP 1: ROUTE to get the specialist tools ---
            specialist_tools = self._route_query(question)
            
            # --- STEP 2: ASSEMBLE the final toolkit ---
            # All experts get access to the foundational tools: File Management, Memory, AND Web.
            foundational_tools = (
                self.file_management_tools + 
                self.memory_tools + 
                self.web_tools
            )
            
            # Combine them and remove any potential duplicates.
            final_tools = specialist_tools + foundational_tools
            final_tools = list({tool.metadata.name: tool for tool in final_tools}.values())
            
            # Get conversational history for context
            chat_history = self.memory.get_all()

            # --- STEP 3: EXECUTE with the specialized agent ---
            print(f"INFO: Deploying agent with tools: {[t.metadata.name for t in final_tools]}")
            
            expert_system_prompt = (
    "You are an autonomous AI project manager. Your sole purpose is to achieve the user's objective by breaking it down into a sequence of executable steps.\n\n"
    "## Guiding Principles:\n"
    "1.  **Decompose:** Break down the user's request into the smallest possible, logical next step.\n"
    "2.  **Execute:** Use one of your available tools to execute that single step.\n"
    "3.  **Verify:** After every action, especially file creation or modification, use a tool like `list_files` or `read_file` to confirm the action was successful.\n"
    "4.  **Iterate:** Continue this Decompose -> Execute -> Verify loop until the user's entire objective is complete.\n"
    "5.  **Report:** Only provide the final, complete answer after all steps have been successfully executed and verified.\n\n"
    "Your task is to manage and execute the user's project from start to finish."
)

            # Create the agent using the direct, stable constructor
            agent = ReActAgent(
                tools=final_tools,
                llm=Settings.llm,
                verbose=True,
                system_prompt=expert_system_prompt
            )

            response_handler = agent.run(question, chat_history=chat_history)
            raw_response_str = str(await response_handler)

                        # --- STEP 4: POST-PROCESS AND FORMAT ---
            print("INFO: Post-processing final response for formatting...")
            
            formatting_prompt = f"""
You are a formatting assistant. Your job is to take a raw response from an AI agent and reformat it into a clean, two-part response for a user interface.

## Guiding Principles:
1.  **Spoken Summary:** Create a concise, conversational, one-sentence summary of the action taken. This is what the text-to-speech engine will say. It should sound natural, like a helpful assistant reporting back. Start with phrases like "Okay, I've...", "Done. The...", "Here is the...". Do NOT include markdown like backticks or asterisks.
2.  **Full Response:** This is the detailed, written response for the user to read. Preserve all important details, code blocks, and file names from the raw response. Format it nicely using Markdown. Use code blocks (```) for code and file contents.

## Raw Agent Response ##
{raw_response_str}

## Instructions ##
- Analyze the Raw Agent Response.
- Create a spoken summary and a detailed full response based on the principles above.
- If the raw response is a simple greeting or a short answer, the spoken and full responses can be similar.
- **CRITICAL:** If the raw response mentions creating an image or a file (e.g., "Saved to population_chart.png"), you MUST include that exact filename in the FULL_RESPONSE so the UI can find and display it.

## RESPONSE TEMPLATE (Use this exact format) ##
<SPOKEN_SUMMARY>A brief, friendly summary of what was done.</SPOKEN_SUMMARY>
<FULL_RESPONSE>The full, detailed, markdown-formatted answer with all necessary information and code blocks.</FULL_RESPONSE>
"""

            final_formatted_response = Settings.llm.complete(formatting_prompt).text
            
            # Update short-term memory with the RAW response for context
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=raw_response_str))
            
            # Return the beautifully formatted response to the UI
            return final_formatted_response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during specialized agent execution: {e}"
        
        finally:
            # --- STEP 5: AUTO-MEMORY (in the background) ---
            if raw_response_str:
                memory_thread = threading.Thread(
                    target=self._summarize_and_save_turn, 
                    args=(question, raw_response_str), 
                    daemon=True
                )
                memory_thread.start()
                
    # --- ADD THIS NEW METHOD ---
    def start_background_process(self, command: str, working_directory: str, launch_in_new_window: bool = False) -> str:
        """A direct pass-through to the process manager tool for the controller."""
        return start_background_process(command, working_directory, launch_in_new_window)
    
    def execute_task(self, task_prompt: str, workspace_path: str):
        # We use asyncio.run to call our async method from the synchronous controller thread
        return asyncio.run(self.aexecute_task(task_prompt, workspace_path))

    async def aexecute_task(self, task_prompt: str, workspace_path: str):
        try:
            print(f"\n[Agent Task]: {task_prompt}")
            specialist_tools = self._route_query(task_prompt)
            # Project tasks don't need memory or web browsing unless specified
            foundational_tools = self.file_management_tools + self.system_tools
            final_tools = list({tool.metadata.name: tool for tool in (specialist_tools + foundational_tools)}.values())

            task_system_prompt = f"You are a subordinate AI assistant. Your only job is to execute the given task precisely as instructed. You are operating within the workspace: '{workspace_path}'. All file operations MUST use relative paths from this workspace. Your current task is: \"{task_prompt}\""
            
            # --- API FIX ---
            # Create the agent using the documented .from_tools() method
            agent = ReActAgent(
                tools=final_tools,
                llm=Settings.llm,
                system_prompt=task_system_prompt,
                verbose=True
            )

            # --- API FIX ---
            # Execute the agent using the modern await .achat() method
            response = await agent.run(task_prompt)
            return str(response)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during task execution: {e}"
        
    def reset_memory(self):
        self.memory.reset()