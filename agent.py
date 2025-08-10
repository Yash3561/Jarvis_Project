# agent.py (Final Version with Browser for Debugging)

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config

# Import all tools, including the new browser tool
from tools.master_tool import intelligent_router
from tools.file_system import read_file_content, list_files_in_directory, write_to_file, create_directory, copy_file
from tools.screen_reader import analyse_screen_with_gemini
from tools.web_search import search_the_web
from tools.code_writer import generate_code
from tools.system_commands import run_shell_command
from tools.browser_tool import browse_and_summarize_website

class AIAgent:
    def __init__(self, data_directory="./data"):
        self.agent = self._create_agent(data_directory)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    def _create_agent(self, data_directory):
        Settings.llm = config.Settings.llm
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        personal_query_engine = index.as_query_engine()
        
        tools = [
            FunctionTool.from_defaults(fn=intelligent_router, name="intelligent_router"),
            FunctionTool.from_defaults(fn=generate_code, name="code_writer"),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_screen"),
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files"),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file"),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file"),
            FunctionTool.from_defaults(fn=create_directory, name="create_directory"),
            FunctionTool.from_defaults(fn=copy_file, name="copy_file"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
            FunctionTool.from_defaults(fn=run_shell_command, name="run_shell_command"),
            # --- THE NEW SUPERPOWER ---
            FunctionTool.from_defaults(fn=browse_and_summarize_website, name="browse_website", description="Reads and summarizes the content of a URL."),
            # Note: We keep web_search for quick, simple queries
            FunctionTool.from_defaults(fn=search_the_web, name="web_search", description="For quick facts and finding URLs."),
        ]
        
        # --- THE "AUTONOMOUS DEBUGGER" PROMPT ---
        system_prompt = (
            "You are Jarvis, an autonomous AI Software Developer. Your goal is to use your tools to accomplish the user's request. You operate in a 'Plan-Execute-Observe-Debug' loop.\n"
            "## CORE DIRECTIVE:\n"
            "1.  **PLAN:** Analyze the user's goal and create a step-by-step plan.\n"
            "2.  **EXECUTE:** Use your tools to perform the next step in your plan.\n"
            "3.  **OBSERVE:** Carefully analyze the output from the tool. Did it succeed or fail?\n"
            "4.  **DEBUG:** **If a step fails (e.g., a `run_shell_command` returns an error), your immediate next action MUST be to debug it.** To debug, first use the `web_search` tool with the exact error message to find a relevant URL (like a Stack Overflow page). Then, use the `browse_website` tool on that URL to read the solution. Finally, refine your plan and try again.\n"
            "5.  **CONFIRM:** After all steps are complete, provide a final confirmation to the user."
        )
        
        print("INFO: Creating ReAct Agent with all tools...")
        agent = ReActAgent(
            tools=tools,
            llm=Settings.llm,
            verbose=True,
            system_prompt=system_prompt,
            max_iterations=40 # Increased for longer, more complex tasks
        )
        return agent

    async def ask(self, question):
        # ... your ask method is correct and does not need changes ...
        print(f"\n[User Query]: {question}")
        chat_history = self.memory.get_all()
        if chat_history:
            history_str = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in chat_history])
            final_question = (f"CONTEXT:\n{history_str}\n\nQUESTION: {question}")
        else:
            final_question = question
        
        print("INFO: Jarvis agent is reasoning...")
        try:
            response = await self.agent.run(final_question)
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=str(response)))
            return str(response)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during agent response: {e}"

    def reset_memory(self):
        self.memory.reset()