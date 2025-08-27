import os
import platform
import re
import time
import traceback
from agent import AIAgent
from llama_index.core import Settings
from tools.workspace import initialize_workspace, close_workspace

class MainController:
    def __init__(self, agent: AIAgent, ui_handler=None):
        self.agent = agent
        self.ui = ui_handler

    def _update_status(self, message: str):
        print(message)
        if self.ui:
            formatted_message = f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>"
            self.ui.response_received.emit(formatted_message)

    def _parse_tool_call(self, task_string: str) -> dict:
        """
        Parses a tool call string into a structured dictionary.
        This FIXED version uses re.finditer for maximum robustness against
        LLM output variations. It finds all key=value pairs instead of
        relying on a fragile sequential parse.
        """
        tool_name_match = re.match(r"(\w+)\(", task_string)
        if not tool_name_match:
            return {'error': f"Could not parse tool name from: {task_string}"}
        tool_name = tool_name_match.group(1)

        try:
            first_paren_index = task_string.index('(')
            open_paren_count = 0
            last_paren_index = -1
            for i, char in enumerate(task_string):
                if i > first_paren_index:
                    if char == '(':
                        open_paren_count += 1
                    elif char == ')':
                        if open_paren_count == 0:
                            last_paren_index = i
                            break
                        else:
                            open_paren_count -= 1
            
            if last_paren_index == -1:
                raise ValueError("Mismatched parentheses")

            args_str = task_string[first_paren_index + 1 : last_paren_index].strip()
        except ValueError:
            return {'error': f"Mismatched or missing parentheses in tool call: {task_string}"}

        args = {}
        arg_pattern = re.compile(
            r"(\w+)\s*=\s*("
            r"\"\"\"(.*?)\"\"\"|"
            r"'''(.*?)'''|"
            r"\"(.*?)\"|"
            r"'(.*?)'"
            r")", re.DOTALL
        )

        for match in arg_pattern.finditer(args_str):
            key = match.group(1)
            full_quoted_string = match.group(2)
            if full_quoted_string.startswith(('"""', "'''")):
                value = full_quoted_string[3:-3]
            else:
                value = full_quoted_string[1:-1]
            args[key] = value.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")

        if not args and args_str:
            return {'error': f"Could not parse any arguments from: '{args_str[:100]}...'"}

        return {'name': tool_name, 'args': args}

    def execute_project(self, user_prompt: str):
        # ... (This function remains the same) ...
        self.agent.original_user_prompt = user_prompt
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:40]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        workspace_path = os.path.join(os.getcwd(), 'workspaces', project_name)
        
        initialize_workspace(
            base_directory=workspace_path,
            output_callback=self.ui.update_terminal_display if self.ui else print
        )
        self._update_status(f"🚀 **Workspace Initialized:** `{workspace_path}`")

        try:
            is_windows = platform.system() == "Windows"
            python_executable = ".\\venv\\Scripts\\python.exe" if is_windows else "./venv/bin/python"
            pip_executable = ".\\venv\\Scripts\\pip.exe" if is_windows else "./venv/bin/pip"
            planner_prompt = f"""
You are "Jarvis," a world-class autonomous software engineer running on a {platform.system()} computer. Generate a complete, step-by-step plan to fulfill the user's request. You MUST follow these directives:
1.  **VENV IS MANDATORY** for any Python project. First, create it with `run_command(command="python -m venv venv")`.
2.  **USE THE CORRECT VENV EXECUTABLES** for this OS. For all subsequent commands, use `{python_executable}` for Python and `{pip_executable}` for pip.
3.  **DO NOT USE `cd`**. The terminal is already in the correct workspace directory.
4.  **VERIFY YOUR WORK**. After writing a file, you can view its contents with `run_command(command="type your_file.py")` (Windows) or `run_command(command="cat your_file.py")` (Linux/macOS).
5.  **RUN THE CODE**. To execute a script, you MUST use the command: `run_command(command="{python_executable} your_script.py")`.
6.  **For long-running apps (servers, GUIs), you must first create a named terminal, then run the start command in it.**

## AVAILABLE TOOLS ##
`run_command(command="your-shell-command-here")`
`write_to_file(file_path="relative/path/to/file.py", content='Your file content here...')`
`create_terminal(name="my_app_server")`
`run_command(command="start cmd /k ...", terminal_name="my_app_server")`

## User Request ##
"{user_prompt}"

Generate the plan now. Do not use markdown code blocks.
"""
            self._update_status("🧠 **Generating project plan...**")
            plan = Settings.llm.complete(planner_prompt).text
            self._execute_plan(plan)
            self._update_status(f"✅ **Project Completed Successfully.**")
            
            return workspace_path

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR:** An unexpected error occurred in the controller.\n\n{error_details}")
            return None
        
        finally:
            self._update_status("🧹 **Closing workspace and all terminals...**")
            close_workspace()

    def _extract_tool_calls(self, plan: str) -> list[str]:
        """
        Extracts tool calls from a plan string using parenthesis-counting.
        This regex MUST include ALL available tools.
        """
        tool_calls = []
        # --- THIS IS THE CORRECTED REGEX ---
        tool_pattern = r"(run_command|write_to_file|create_terminal|wait_for_user_input|navigate|extract_text_from_element|analyze_entire_screen)\("
        
        cursor = 0
        while cursor < len(plan):
            match = re.search(tool_pattern, plan[cursor:])
            if not match:
                break
            
            start_index = cursor + match.start()
            open_paren_index = cursor + match.end() - 1
            paren_level = 1
            
            i = open_paren_index + 1
            while i < len(plan) and paren_level > 0:
                if plan[i] == '(':
                    paren_level += 1
                elif plan[i] == ')':
                    paren_level -= 1
                i += 1
            
            if paren_level == 0:
                end_index = i
                tool_calls.append(plan[start_index:end_index])
                cursor = end_index
            else:
                self._update_status(f"⚠️ Warning: Could not find matching parenthesis for call starting at index {start_index}.")
                cursor = open_paren_index + 1

        return tool_calls

    def _execute_plan(self, plan: str):
        """
        Executes a multi-step plan, with a self-correction loop to handle errors.
        This is the resilient core of the autonomous agent.
        """
        self._update_status("⚙️ **Parsing execution plan...**")
        
        # We will maintain a history of the execution for the agent's context
        execution_history = []
        # Set a limit to prevent infinite loops
        max_retries = 5 
        current_retry = 0

        while current_retry < max_retries:
            matches = self._extract_tool_calls(plan)
            
            if not matches:
                self._update_status("❌ **CRITICAL PARSING ERROR:** No tool calls found in the current plan.")
                raise ValueError("No executable steps found in the generated plan.")

            plan_succeeded = True # Assume the plan will work until a step fails
            
            for i, task_string in enumerate(matches):
                step_number = len(execution_history) + 1
                self._update_status(f"▶️ **Executing Step {step_number}:** `{task_string.split('(')[0]}`")

                parsed_tool = self._parse_tool_call(task_string)
                if parsed_tool.get('error'):
                    error_message = f"Tool call parsing failed: {parsed_tool['error']} on task: '{task_string}'"
                    execution_history.append(f"Step {step_number} FAILED. Error: {error_message}")
                    plan_succeeded = False
                    break # Stop executing this failed plan

                tool_name = parsed_tool['name']
                tool_args = parsed_tool['args']
                
                raw_result = ""
                try:
                    # --- Argument Validation: The Fix for the TypeError ---
                    if tool_name == "write_to_file":
                        if 'file_path' not in tool_args or 'content' not in tool_args:
                            raise ValueError("Missing 'file_path' or 'content' for write_to_file.")
                        raw_result = self.agent.write_file(**tool_args)
                    elif tool_name == "run_command":
                        # run_command is already safe and returns errors as strings
                        raw_result = self.agent.run_command(**tool_args)
                    elif tool_name == "create_terminal":
                        raw_result = self.agent.create_terminal(**tool_args)
                    else:
                        raise ValueError(f"Unknown tool '{tool_name}' requested.")
                    
                    # Check for errors reported by the tools themselves
                    if raw_result and "ERROR:" in str(raw_result).upper():
                        # This is not a fatal exception, but a failure to be reported to the agent
                        raise Exception(raw_result)
                    
                    # If we get here, the step was a success
                    self._update_status(f"✔️ **Step {step_number} Succeeded!**")
                    execution_history.append(f"Step {step_number}: {task_string}\nResult: {raw_result}")

                except Exception as e:
                    # --- THIS IS THE SELF-CORRECTION TRIGGER ---
                    error_message = f"EXECUTION FAILED on Step {step_number}. Reason: {e}"
                    self._update_status(f"❌ **{error_message}**")
                    execution_history.append(f"Step {step_number} FAILED. Error: {e}")
                    plan_succeeded = False
                    break # Stop executing this failed plan

            # --- AFTER THE LOOP: Check if the whole plan succeeded ---
            if plan_succeeded:
                # The entire list of tasks was completed without errors. We're done.
                return # Exit the function successfully

            # --- REMEDIATION STEP ---
            # If we're here, plan_succeeded is False. We need to ask the agent for a new plan.
            current_retry += 1
            self._update_status(f" D **Plan failed. Attempting self-correction ({current_retry}/{max_retries}). Asking agent for a new plan...**")
            
            remediation_prompt = f"""
    You are an expert debugger. A multi-step plan has failed. Your task is to analyze the history of execution, identify the error, and generate a NEW, complete, and corrected plan to achieve the original goal.

    ## Original User Request ##
    "{self.agent.original_user_prompt}"  # You might need to store this in your agent/controller

    ## Execution History (Last step failed) ##
    {"\n".join(execution_history)}

    ## Your Task ##
    Based on the error in the last step, create a new, full plan starting from scratch. Do not just provide the single corrected step. Provide the entire sequence of commands needed to recover and complete the task. For example, if a file has a syntax error, the new plan should be:
    1. `write_to_file(file_path="...", content="...")` with the corrected code.
    2. `run_command(command="...")` to run the now-fixed script.

    Generate the new plan now.
    """
            # Get the new plan from the LLM
            plan = Settings.llm.complete(remediation_prompt).text
            # The while loop will now run again with the new plan

        # If the loop finishes without success
        raise Exception(f"Project failed after {max_retries} attempts. Last error: {execution_history[-1]}")