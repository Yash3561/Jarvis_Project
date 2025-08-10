# tools/code_writer.py

import google.generativeai as genai
import config

try:
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini for the code writer tool. It will fail. Error: {e}")

def generate_code(task_description: str) -> str:
    """
    A powerful tool that takes a detailed description of a programming task
    and returns complete, high-quality code to accomplish that task.
    Use this for any request that involves writing scripts, code, or frontend components.
    """
    print(f"INFO: Code Writer received task: '{task_description}'")
    
    # Use your most powerful model for code generation
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    prompt = f"""
    You are an expert programmer. Your sole task is to write a complete, high-quality, and runnable code block that accomplishes the user's goal.
    - Write only the code. Do not add any explanation, commentary, or markdown formatting like ```python.
    - If the user asks for a specific language (e.g., Python, HTML, JavaScript), write the code in that language.
    - If the language is not specified, default to Python.

    User's Task: "{task_description}"

    Code:
    """
    
    try:
        response = model.generate_content(prompt)
        code_block = response.text.strip()
        print(f"INFO: Code Writer generated {len(code_block)} characters of code.")
        return code_block
    except Exception as e:
        print(f"ERROR in code writer: {e}")
        return f"# Error: Could not generate code for the task. {e}"