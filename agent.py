# agent.py (Final Version - with create_directory tool)

import os
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config
from tools.web_search import search_the_web
from tools.screen_reader import analyse_screen_with_gemini, save_screenshot_to_file
# Import the new create_directory function
from tools.file_system import list_files_in_directory, write_to_file, read_file_content, create_directory

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
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base", description="For questions about Yash Chaudhary."),
            FunctionTool.from_defaults(fn=search_the_web, name="web_search", description="For general knowledge and current events."),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_all_screens", description="Analyzes screenshots of all connected monitors to answer any question about visual content."),
            FunctionTool.from_defaults(fn=save_screenshot_to_file, name="save_primary_screenshot", description="Captures the PRIMARY screen and saves it as a PNG image file."),

            # --- FULL FILE SYSTEM TOOLKIT ---
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files", description="Lists files and directories."),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file", description="Reads the content of a specific file."),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file", description="Writes or creates a file with specific content."),
            # --- THE NEW TOOL ---
            FunctionTool.from_defaults(fn=create_directory, name="create_directory", description="Creates a new directory/folder at a specified path."),
        ]
        
        system_prompt = (
            "You are Jarvis, an AI assistant that accomplishes tasks by using tools. You must select the best tool for the job. "
            "1. **For visual questions about the screen:** Use `analyze_all_screens`. "
            "2. **For file operations:** You have tools to `list_files`, `read_file`, `write_file`, and `create_directory`. Use them for any request involving files on the disk. "
            "3. **To solve a multi-step task, you must chain your tools.** For example, to 'create a duplicate file in a new folder,' first use `create_directory`, then `read_file` to get the content, and finally `write_file` to save that content to the new path. Think step-by-step."
        )
        
        print("INFO: Creating ReAct Agent with all tools...")
        agent = ReActAgent(
            tools=tools,
            llm=Settings.llm,
            verbose=True,
            system_prompt=system_prompt,
            max_iterations=30
        )
        return agent

    async def ask(self, question):
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