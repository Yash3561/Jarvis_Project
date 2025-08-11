# agent.py (The Definitive, Stable V1.0 Version)

import asyncio # Add this import for the async ask method
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

# --- Import ALL the simple tool functions directly ---
from tools.file_system import read_file_content, list_files_in_directory, write_to_file, create_directory, copy_file
from tools.screen_reader import analyse_screen_with_gemini, save_screenshot_to_file
from tools.web_search import search_the_web
from tools.code_writer import generate_code, review_and_refine_code
from tools.system_commands import run_shell_command, get_current_datetime, get_time_for_location, get_timestamp
from tools.browser_tool import browse_and_summarize_website
from tools.browser_automation import navigate, type_text, click, extract_text_from_element
from tools.long_term_memory import save_experience, recall_experiences
from tools.script_runner import run_python_script
# We remove master_tool as it's part of the failed V2 architecture
# from tools.master_tool import intelligent_router 


class AIAgent:
    def __init__(self, data_directory="./data"):
        # We pass data_directory here again, as per your stable version
        self.agent = self._create_agent(data_directory)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    def _create_agent(self, data_directory):
        # The global settings are configured in main.py, so we don't need them here.
        # This was correct in your original file.
        
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        personal_query_engine = index.as_query_engine()
        
        # This is your full, powerful V1.0 tool list
        tools = [
            FunctionTool.from_defaults(fn=generate_code, name="code_writer"),
            FunctionTool.from_defaults(fn=review_and_refine_code, name="code_reviewer"),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_screen"),
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files"),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file"),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file"),
            FunctionTool.from_defaults(fn=create_directory, name="create_directory"),
            FunctionTool.from_defaults(fn=copy_file, name="copy_file"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
            FunctionTool.from_defaults(fn=run_shell_command, name="run_shell_command", 
                                       description="Use for NON-PYTHON, general shell commands like 'pip install', 'git', 'ls', 'mkdir'."),
            FunctionTool.from_defaults(fn=browse_and_summarize_website, name="browse_website"),
            FunctionTool.from_defaults(fn=search_the_web, name="fact_checker"),
            FunctionTool.from_defaults(fn=get_current_datetime, name="get_current_datetime"),
            FunctionTool.from_defaults(fn=get_time_for_location, name="get_time_for_location"),
            FunctionTool.from_defaults(fn=save_experience, name="save_experience"),
            FunctionTool.from_defaults(fn=recall_experiences, name="recall_experiences"),
            FunctionTool.from_defaults(fn=navigate, name="navigate_to_url"),
            FunctionTool.from_defaults(fn=type_text, name="type_into_browser"),
            FunctionTool.from_defaults(fn=click, name="click_browser_element"),
            FunctionTool.from_defaults(fn=extract_text_from_element, name="extract_text_from_element"),
            FunctionTool.from_defaults(fn=get_timestamp, name="get_timestamp"),
            FunctionTool.from_defaults(fn=run_python_script, name="run_python_script", 
                                       description="The ONLY tool to be used for executing .py script files. It is safe and provides all output."),
        ]
        
        # In agent.py, replace the system_prompt

        system_prompt = (
    "You are Jarvis, an autonomous AI Software Developer running on a WINDOWS machine. You are meticulous, stateful, and use all available capabilities.\n"
    "## CRITICAL TOOL USAGE RULES:\n"
    "1.  **To create or write to a file:** You MUST use the `write_file` tool.\n"
    "2.  **To list directory contents:** You MUST use the `list_files` tool.\n"
    "3.  **To execute Python scripts:** You MUST use the `run_python_script` tool.\n"
    "4.  **For other terminal commands (pip, git):** Use `run_shell_command`.\n"
    "5.  **HONESTY PROTOCOL:** You MUST be truthful about the tools you use. Do not fabricate tool usage.\n"
    "\n"
    "## SPECIAL CAPABILITIES:\n" #<-- NEW SECTION
    "**Displaying Images in Chat:** To show an image to the user, you do not need a special tool. Simply include the full filename (e.g., `confusion_matrix.png`) in your final text response. The user interface will automatically detect the filename and display the image.\n"
    "\n"
    "## Core Workflow:\n"
    "Plan -> Choose Correct Tool -> Execute -> Verify -> Report Truthfully (and mention image filenames to display them)." #<-- UPDATED WORKFLOW
)
        
        print("INFO: Creating ReAct Agent with all tools...")
        agent = ReActAgent(
            tools=tools,
            llm=Settings.llm,
            verbose=True,
            system_prompt=system_prompt,
            max_iterations=50
        )
        return agent

    async def ask(self, question): # <-- This must stay async
        print(f"\n[User Query]: {question}")
        chat_history = self.memory.get_all()
        if chat_history:
            history_str = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in chat_history])
            final_question = (f"CONTEXT:\n{history_str}\n\nQUESTION: {question}")
        else:
            final_question = question
        
        print("INFO: Jarvis agent is reasoning...")
        try:
            # Step 1: Call the synchronous .run() method. It does NOT block forever.
            # It kicks off the workflow and IMMEDIATELY returns a handler object.
            response_handler = self.agent.run(final_question)
            
            # Step 2: THE FIX. Await the handler object itself.
            # This tells the event loop: "Pause this 'ask' function, let the
            # handler's background tasks run, and wake me up when you have the result."
            final_result = await response_handler

            # Step 3: The result is now safely set. We can work with it.
            response_str = str(final_result)
            
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=response_str))
            return response_str
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during agent response: {e}"

    def reset_memory(self):
        self.memory.reset()