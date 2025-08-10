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
    
def review_and_refine_code(task_description: str, code_to_review: str) -> str:
    """
    Analyzes a block of existing code against a task description.
    If the code is correct, it returns the original code.
    If the code is incorrect or could be improved, it returns a new, corrected version.
    Use this to verify and debug code before executing it.
    """
    print(f"INFO: Code Reviewer received task: '{task_description}'")
    print(f"INFO: Reviewing code:\n---\n{code_to_review}\n---")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    prompt = f"""
    You are a Senior Software Quality Assurance Engineer. Your job is to review a block of code and ensure it perfectly accomplishes the given task.
    
    **Task Description:** "{task_description}"

    **Code to Review:**
    ```python
    {code_to_review}
    ```

    **Your Task:**
    1.  Carefully analyze the "Code to Review." Does it flawlessly and correctly achieve the "Task Description"?
    2.  If the code is perfect, respond with ONLY the original, unchanged code block.
    3.  If the code has any bugs, errors, or fails to meet all the requirements of the task, you MUST rewrite it to be correct. Respond with ONLY the new, corrected code block. Do not add any explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        refined_code = response.text.strip().replace("```python", "").replace("```", "").strip()
        
        if refined_code == code_to_review:
            print("INFO: Code Reviewer approved the code as correct.")
        else:
            print("INFO: Code Reviewer found issues and returned a refined version.")
            
        return refined_code
    except Exception as e:
        print(f"ERROR in code reviewer: {e}")
        return f"# Error: Could not review the code. {e}"