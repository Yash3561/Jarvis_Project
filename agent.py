# agent.py (Final Definitive Version)

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config
from tools.master_tool import intelligent_router
from tools.file_system import read_file_content, list_files_in_directory, write_to_file, create_directory, copy_file
from tools.screen_reader import analyse_screen_with_gemini
from tools.web_search import search_the_web
from tools.code_writer import generate_code

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
            FunctionTool.from_defaults(fn=intelligent_router, name="intelligent_router", description="The first tool to call to understand the user's intent."),
            FunctionTool.from_defaults(fn=generate_code, name="code_writer"),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_screen", description="Analyzes the screen to answer visual questions."),
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files", description="Lists files and directories."),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file", description="Reads the content of a file."),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file", description="Writes content to a file."),
            FunctionTool.from_defaults(fn=create_directory, name="create_directory", description="Creates a new folder."),
            FunctionTool.from_defaults(fn=copy_file, name="copy_file", description="Duplicates a file."),
            FunctionTool.from_defaults(fn=search_the_web, name="web_search", description="Searches the web for information."),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base", description="Answers questions about Yash Chaudhary."),
        ]
        
        # --- A POWERFUL, STEP-BY-STEP REASONING PROMPT ---
        system_prompt = (
            "You are Jarvis, a powerful AI assistant that creates software. Your primary goal is to write code and save it to files based on user requests.\n"
            "## Your Thought Process for Writing Code:\n"
            "1.  **Clarify the Goal:** Use the `intelligent_router` to understand the user's high-level goal. If they want to write code, the router will point to `code_writer`.\n"
            "2.  **Generate the Code:** Call the `code_writer` tool with a detailed description of the task. For example: 'a Python script that adds two numbers'.\n"
            "3.  **Save the Code:** Once the `code_writer` tool returns the code block, you MUST use the `write_file` tool to save the generated code to a file. You should ask the user for a filename if they have not provided one.\n"
            "**Example Task:** 'Write a hello world script and save it as hello.py'\n"
            "**Your Plan:**\n"
            "   - Action 1: `code_writer(task_description='a python script that prints hello world')`\n"
            "   - Action 2: `write_file(file_path='hello.py', content='<the code from Action 1>')`\n"
        )
        
        print("INFO: Creating ReAct Agent with all tools...")
        agent = ReActAgent(
            tools=tools,
            llm=Settings.llm,
            verbose=True, # Verbose is critical for debugging ReAct agents
            system_prompt=system_prompt,
            max_iterations=30
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