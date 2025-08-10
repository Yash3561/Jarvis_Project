# tools/master_tool.py (Final Definitive Version)

import google.generativeai as genai
import config

try:
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini for the master tool. Routing will fail. Error: {e}")

def intelligent_router(query: str) -> str:
    """
    Analyzes the user's query and determines the best tool to use.
    This is the first tool that should be called for any user request.
    """
    print(f"INFO: Intelligent Router received query: '{query}'")
    
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    prompt = f"""
    You are an expert at routing user queries to the correct tool.
    Based on the user's query, choose exactly one of the following tools.
    Respond with ONLY the name of the tool.

    Available Tools:
    - code_writer (Use for any request to 'write a script', 'create code', 'make a program', 'build a frontend', etc.)
    - analyze_screen (...)
    - list_files (...)
    - read_file (...)
    - write_file (...)
    - copy_file (...)
    - create_directory (...)
    - web_search (...)
    - personal_knowledge_base (...)

    User Query: "{query}"

    Chosen Tool:
    """
    
    try:
        response = model.generate_content(prompt)
        tool_choice = response.text.strip()
        print(f"INFO: Intelligent Router chose: '{tool_choice}'")
        # Return a structured thought process for the main agent
        return f"Thought: The user's query is best handled by the '{tool_choice}' tool. I should now call that tool with the appropriate parameters from the original query."
    except Exception as e:
        print(f"ERROR in intelligent router: {e}")
        return f"Error: Could not determine the correct tool. I should ask the user for clarification."