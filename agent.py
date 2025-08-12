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
        The V3.2 'ask' method. It uses a final 'post-processing' step to
        guarantee the response is correctly formatted.
        """
        print(f"\n[User Query]: {question}")
        
        # --- Steps 1 & 2 are perfect, no changes ---
        specialist_tools = self._route_query(question)
        foundational_tools = self.file_management_tools + self.memory_tools
        final_tools = list({tool.metadata.name: tool for tool in (specialist_tools + foundational_tools)}.values())
        chat_history = self.memory.get_all()

        print(f"INFO: Deploying agent with tools: {[t.metadata.name for t in final_tools]}")
        
        # We give the expert a simpler prompt now. Its only job is to solve the problem.
        expert_system_prompt = (
            "You are a task-specific expert AI. Your goal is to use your tools to find the answer to the user's request. "
            "Provide a complete and thorough answer. Do not worry about formatting."
        )

        try:
            # --- STEP 3: EXECUTE ---
            specialized_agent = ReActAgent(
                tools=final_tools,
                llm=Settings.llm,
                verbose=True,
                system_prompt=expert_system_prompt
            )
            response_handler = specialized_agent.run(question, chat_history=chat_history)
            raw_response_str = str(await response_handler)

            # --- STEP 4: POST-PROCESS AND FORMAT (THE FIX) ---
            print("INFO: Post-processing final response for formatting...")
            
            formatting_prompt = f"""
            You are a formatting assistant. Your task is to take a raw response from an AI agent and format it into a strict XML template.

            ## Raw Agent Response ##
            {raw_response_str}

            ## Instructions ##
            Based on the raw response, fill out the following template.
            - The SPOKEN_SUMMARY should be a single, concise sentence.
            - For code, the summary should be "I have generated the code as requested."
            - The FULL_RESPONSE should contain all the details, including any markdown code blocks.

            ## RESPONSE TEMPLATE ##
            <SPOKEN_SUMMARY>
                (Your one-sentence summary here)
            </SPOKEN_SUMMARY>

            <FULL_RESPONSE>
                (The full, detailed response here)
            </FULL_RESPONSE>
            """

            # Make a direct, final LLM call to do the formatting
            final_formatted_response = Settings.llm.complete(formatting_prompt).text

            # Update memory with the RAW response so the agent remembers what it actually did
            self.memory.put(ChatMessage(role=MessageRole.USER, content=question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=raw_response_str))
            
            # Return the BEAUTIFUL formatted response to the UI
            return final_formatted_response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR during specialized agent execution: {e}"
        
    def reset_memory(self):
        self.memory.reset()