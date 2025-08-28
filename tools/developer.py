# tools/developer.py (The Code Generation and Review Tool)

import google.generativeai as genai
import config

try:
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini for the developer tool. It will fail. Error: {e}")

def generate_code(task_description: str) -> str:
    """
    Writes a complete, high-quality code block based on a detailed task description.
    Use this for any request that involves writing new scripts, functions, or UI components.
    The task description should be as specific as possible.
    """
    print(f"INFO: Generating code for task: '{task_description}'")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    You are an expert software engineer. Your task is to write a complete, runnable code block that accomplishes the user's goal.
    - Respond with ONLY the raw code.
    - Do not add any explanation, commentary, or markdown formatting like ```python.
    - Ensure the code is clean, efficient, and follows best practices.

    User's Task: "{task_description}"
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up potential markdown in case the model ignores instructions
        code_block = response.text.strip().replace("```python", "").replace("```", "").strip()
        print(f"INFO: Code generation complete.")
        return code_block
    except Exception as e:
        return f"# Error: Could not generate code for the task. {e}"
    
def review_and_refine_code(code_to_review: str, objective: str) -> str:
    """
    Analyzes a block of code against a specific objective, identifies bugs or improvements,
    and returns a corrected version. Use this to debug or enhance existing code.
    """
    print(f"INFO: Reviewing code against objective: '{objective}'")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    You are a Senior Quality Assurance Engineer. Your job is to review a block of code and ensure it perfectly accomplishes the given objective.
    
    **Objective:** "{objective}"

    **Code to Review:**
    ```
    {code_to_review}
    ```

    **Your Task:**
    Analyze the "Code to Review." If it has bugs or fails to meet the objective, rewrite it to be correct.
    If the code is already perfect, return the original code.
    Respond with ONLY the final, correct code block. Do not add explanations.
    """
    
    try:
        response = model.generate_content(prompt)
        refined_code = response.text.strip().replace("```python", "").replace("```", "").strip()
        
        if refined_code == code_to_review:
            print("INFO: Code review passed with no changes.")
        else:
            print("INFO: Code review resulted in a refined version.")
        return refined_code
    except Exception as e:
        return f"# Error: Could not review the code. {e}"