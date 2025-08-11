# agent.py (The Definitive V3 - Hierarchical Agent Architecture)

import asyncio
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
from tools.long_term_memory import save_experience, recall_experiences
from tools.script_runner import run_python_script

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
            FunctionTool.from_defaults(fn=create_directory, name="create_directory"),
        ]

        self.memory_tools = [
            FunctionTool.from_defaults(fn=save_experience, name="save_experience"),
            FunctionTool.from_defaults(fn=recall_experiences, name="recall_experiences"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
        ]
        
        self.system_tools = [
            FunctionTool.from_defaults(fn=run_shell_command, name="run_shell_command"),
            FunctionTool.from_defaults(fn=get_current_datetime, name="get_current_datetime"),
        ]
        
        # This is the short-term conversation memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    def _get_personal_query_engine(self, data_directory):
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        return index.as_query_engine()

    def _route_query(self, query: str) -> list:
        """
        The CEO's router. It uses the LLM to decide which specialized 'department'
        (toolset) is best suited to handle the user's query.
        """
        tool_descriptions = {
            "Coding": "Best for writing, reviewing, or executing Python code and scripts.",
            "Web": "Best for searching the web, browsing websites, or checking facts online.",
            "Vision": "Best for analyzing the contents of specific image files or the entire screen.",
            "System": "Best for running general non-python shell commands (like pip, git) or getting system time.",
            "General": "A general-purpose category for simple questions or tasks not covered by other categories."
        }

        prompt = f"""
        Given the user's query, determine the single best specialized tool category to handle the request.
        The foundational tools for file management and memory are always available. You only need to choose the specialist.
        
        Available specialist categories:
        {tool_descriptions}

        User Query: "{query}"

        Based on the query, the single most appropriate specialist category is:
        """

        response = Settings.llm.complete(prompt)
        chosen_category = response.text.strip().replace("'", "").replace("`", "")
        
        print(f"INFO: Router chose category: '{chosen_category}' for the query.")

        if chosen_category == "Coding":
            return self.coding_tools
        elif chosen_category == "Web":
            return self.web_tools
        elif chosen_category == "Vision":
            return self.vision_tools
        elif chosen_category == "System":
            return self.system_tools
        else:
            # If the LLM gives a weird answer or a general question is asked,
            # don't provide any specialist tools. The foundational tools will handle it.
            print(f"WARN: Router chose '{chosen_category}'. Defaulting to foundational tools only.")
            return []

    async def ask(self, question):
        """
        The V3.1 'ask' method. It uses the V3 router with the proven V2 execution logic.
        """
        print(f"\n[User Query]: {question}")
        
        # --- STEP 1 & 2: ROUTE AND ASSEMBLE (This part is working perfectly) ---
        specialist_tools = self._route_query(question)
        foundational_tools = self.file_management_tools + self.memory_tools
        final_tools = specialist_tools + foundational_tools
        final_tools = list({tool.metadata.name: tool for tool in final_tools}.values())
        
        chat_history = self.memory.get_all()

        # --- STEP 3: EXECUTE (This is the corrected part) ---
        print(f"INFO: Deploying agent with tools: {[t.metadata.name for t in final_tools]}")
        
        agent_system_prompt = (
            "You are a helpful and efficient AI assistant. Your goal is to complete the user's request using only your provided tools. "
            "You have access to foundational tools for file management and memory, and specialist tools for your current task. "
            "Think step-by-step and be precise."
        )

        try:
            # --- THE PROVEN EXECUTION PATTERN ---

            # Step 3a: Create the agent with the direct, stable constructor.
            specialized_agent = ReActAgent(
                tools=final_tools,
                llm=Settings.llm,
                verbose=True,
                system_prompt=agent_system_prompt
            )

            # Step 3b: Call the synchronous .run() method. It returns a handler.
            response_handler = specialized_agent.run(question, chat_history=chat_history)

            # Step 3c: Await the handler to get the final result. This is the key.
            final_result = await response_handler

            # Step 3d: The result is now safely set.
            response_str = str(final_result)
            
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=response_str))
            return response_str
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during specialized agent execution: {e}"
        
    def reset_memory(self):
        self.memory.reset()