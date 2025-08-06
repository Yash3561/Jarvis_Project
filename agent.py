# agent.py (v2.1 - The Final, Compatible Fix)

import os
from dotenv import load_dotenv

load_dotenv()
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

# --- Custom Tools ---
from web_search_tool import search_the_web

load_dotenv()
Settings.llm = GoogleGenAI(model="models/gemini-1.5-pro-latest", temperature=0.3)
Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

class AIAgent:
    def __init__(self, data_directory="./data"):
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=4000)
        self.agent = self._create_agent(data_directory)
    
    def _create_agent(self, data_directory):
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        personal_query_engine = index.as_query_engine()
        
        personal_data_tool = FunctionTool.from_defaults(
            fn=personal_query_engine.query, 
            name="personal_knowledge_base", 
            description="Use this tool for questions about Yash Chaudhary's personal skills and resume."
        )
        
        web_search_tool_instance = FunctionTool.from_defaults(
            fn=search_the_web, 
            name="web_search", 
            description="Provides real-time information from the internet. Use for all general knowledge, current events, or questions that don't relate to the user's personal documents."
        )
        
        system_prompt = "You are Jarvis, a helpful AI assistant. Use the `web_search` tool for most questions. Use the `personal_knowledge_base` only for questions about Yash Chaudhary."
        
        print("INFO: Creating simplified ReAct Agent...")
        # We do NOT pass memory to the agent constructor, as it is incompatible with .run() in this version.
        agent = ReActAgent(
            tools=[personal_data_tool, web_search_tool_instance],
            llm=Settings.llm, 
            verbose=True, 
            system_prompt=system_prompt
        )
        return agent

    async def ask(self, question):
        print(f"\n[User Query]: {question}")

        # --- THIS IS THE CORRECT, STABLE PATTERN ---
        # 1. Manually inject the conversation history into the prompt.
        chat_history = self.memory.get_all()
        if chat_history:
            history_str = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in chat_history])
            final_question = (
                f"Please use the following conversation history for context:\n--- HISTORY ---\n{history_str}\n--- END HISTORY ---\n\n"
                f"Now, answer this new user question: {question}"
            )
        else:
            final_question = question

        print("INFO: Jarvis agent is reasoning...");
        try:
            # 2. Use the compatible .run() method.
            response = await self.agent.run(final_question)

            # 3. Manually update the memory object after the call.
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=str(response)))

            return str(response)
        except Exception as e: 
            import traceback; traceback.print_exc()
            return f"ERROR during agent response: {e}"

    def reset_memory(self):
        # 4. Reset the memory object directly.
        self.memory.reset()