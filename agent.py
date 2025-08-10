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
from tools.code_writer import generate_code, review_and_refine_code
from tools.system_commands import run_shell_command, get_current_datetime, get_time_for_location, get_timestamp
from tools.browser_tool import browse_and_summarize_website
from tools.long_term_memory import save_experience, recall_experiences
from tools.browser_automation import navigate, type_text, click, extract_text_from_element


class AIAgent:
    def __init__(self, data_directory="./data"):
        self.agent = self._create_agent(data_directory)
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    def _create_agent(self, data_directory):
        # Settings.llm = config.Settings.llm
        # Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        print("INFO: Loading knowledge from personal documents...")
        documents = SimpleDirectoryReader(data_directory).load_data()
        index = VectorStoreIndex.from_documents(documents)
        personal_query_engine = index.as_query_engine()
        
        tools = [
            FunctionTool.from_defaults(fn=intelligent_router, name="intelligent_router"),
            FunctionTool.from_defaults(fn=generate_code, name="code_writer"),
            FunctionTool.from_defaults(fn=review_and_refine_code, name="code_reviewer"),
            FunctionTool.from_defaults(fn=analyse_screen_with_gemini, name="analyze_screen"),
            FunctionTool.from_defaults(fn=list_files_in_directory, name="list_files"),
            FunctionTool.from_defaults(fn=read_file_content, name="read_file"),
            FunctionTool.from_defaults(fn=write_to_file, name="write_file"),
            FunctionTool.from_defaults(fn=create_directory, name="create_directory"),
            FunctionTool.from_defaults(fn=copy_file, name="copy_file"),
            FunctionTool.from_defaults(fn=personal_query_engine.query, name="personal_knowledge_base"),
            FunctionTool.from_defaults(fn=run_shell_command, name="run_shell_command"),
            FunctionTool.from_defaults(fn=browse_and_summarize_website, name="browse_website", 
                                       description="Use ONLY when you have a specific URL and need to read the content of that webpage, for example, to read documentation or an article."),
            FunctionTool.from_defaults(fn=search_the_web, name="fact_checker", 
                                       description="Use this as your primary tool to get current, verified, and up-to-date answers to any factual question. This is your ONLY source for truth about current events, people, and objective facts."),
            FunctionTool.from_defaults(fn=get_current_datetime, name="get_current_datetime", description="Use to get the user's current LOCAL date and time."),
            FunctionTool.from_defaults(fn=get_time_for_location, name="get_time_for_location", description="Use to get the current date and time for a specific city, country, or timezone."),
            # --- THE NEW MEMORY TOOLS ---
            FunctionTool.from_defaults(fn=save_experience, name="save_experience", 
                                       description="Saves a summary of a completed task and its output to long-term memory."),
            FunctionTool.from_defaults(fn=recall_experiences, name="recall_experiences",
                                       description="Searches long-term memory for relevant past actions or information."),
            # --- THE FULL BROWSER SUITE ---
            FunctionTool.from_defaults(fn=navigate, name="navigate_to_url"),
            FunctionTool.from_defaults(fn=type_text, name="type_into_browser"),
            FunctionTool.from_defaults(fn=click, name="click_browser_element"),
            FunctionTool.from_defaults(fn=extract_text_from_element, name="extract_text_from_element", 
                                       description="A precision tool to get the text from a specific element on a webpage, using a CSS selector."),
            FunctionTool.from_defaults(fn=get_timestamp, name="get_timestamp", description="Generates a unique, file-safe timestamp string."),
        ]
        
        # --- THE "AUTONOMOUS DEBUGGER" PROMPT ---
        system_prompt = (
            "You are Jarvis, an autonomous AI assistant that completes tasks by executing a plan and then reports the results directly.\n"
            "## Core Reasoning Loop:\n"
            "1.  **Plan:** Deconstruct the user's goal into a sequence of tool calls.\n"
            "2.  **Execute & Observe:** Run your tools and critically analyze the output.\n"
            "3.  **Self-Correct:** If a tool fails, use your other tools to debug and find a solution.\n"
            "\n"
            "## **CRITICAL FINAL REPORTING PROTOCOL:**\n"
            "After all tools have been executed and the goal is complete, you MUST follow these rules for your final response:\n"
            "   a. **If the final tool call returned a direct answer** (e.g., a joke, a web search result, the content of a file), your final response **MUST be that information and nothing more.** Do not comment on it, react to it, or add conversational filler. Simply present the result.\n"
            "   b. **If the final tool call was an action** (e.g., `write_file`, `run_shell_command`), your final response should be a concise confirmation that the action was completed successfully.\n"
        )
        
        print("INFO: Creating ReAct Agent with all tools...")
        agent = ReActAgent(
            tools=tools,
            llm=Settings.llm,
            verbose=True,
            system_prompt=system_prompt,
            max_iterations=40
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