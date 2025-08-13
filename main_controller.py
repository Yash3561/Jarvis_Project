# main_controller.py (The Battle-Hardened Version)

import os
import platform
import re
import time
import traceback
from agent import AIAgent
from llama_index.core import Settings
from tools.workspace import initialize_workspace, close_workspace

class MainController:
    # ... (keep your __init__, _update_status, and _parse_tool_call methods exactly as they were from the last fix) ...
    # PASTE THE ROBUST PARSER FROM THE PREVIOUS STEP HERE IF YOU HAVEN'T ALREADY
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
            planner_prompt = f"""
You are "Jarvis," a world-class autonomous software engineer. Generate a complete, step-by-step plan to fulfill the user's request. You MUST follow these directives:
1.  **VENV IS MANDATORY** for any Python project. First, create it with `run_command(command="python -m venv venv")`.
2.  **USE THE VENV's EXECUTABLES** for all subsequent `python` and `pip` commands (e.g., `.\\venv\\Scripts\\python.exe ...` on Windows or `./venv/bin/python ...` on Linux/macOS).
3.  **DO NOT USE `cd`**. The terminal is already in the correct directory.
4.  **VERIFY YOUR WORK** with commands like `ls -R` or `pip freeze`.
5.  **For long-running apps (servers, GUIs), you must first create a named terminal, then run the start command in it.**
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

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR:** An unexpected error occurred in the controller.\n\n{error_details}")
        
        finally:
            self._update_status("🧹 **Closing workspace and all terminals...**")
            close_workspace()

    def _extract_tool_calls(self, plan: str) -> list[str]:
        """
        NEW AND IMPROVED: Extracts tool calls from a plan string using
        parenthesis-counting to correctly handle nested structures.
        """
        tool_calls = []
        # Regex to find the start of a potential tool call
        tool_pattern = r"(run_command|write_to_file|create_terminal)\("
        
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
                # Mismatched parens, skip this potential call and log an error
                self._update_status(f"⚠️ Warning: Could not find matching parenthesis for call starting at index {start_index}.")
                cursor = open_paren_index + 1

        return tool_calls

    def _execute_plan(self, plan: str):
        """
        MODIFIED: This now uses the robust _extract_tool_calls method
        instead of a brittle regex to find steps.
        """
        self._update_status("⚙️ **Parsing execution plan...**")
        matches = self._extract_tool_calls(plan)
        
        if not matches:
            self._update_status(f"❌ **CRITICAL PARSING ERROR:** No tool calls found in the plan.")
            raise ValueError("No executable steps found in the generated plan.")

        step_counter = 1
        for task_string in matches:
            self._update_status(f"▶️ **Executing Step {step_counter}:** {task_string.split('(')[0]}")

            parsed_tool = self._parse_tool_call(task_string)
            if parsed_tool.get('error'):
                raise ValueError(f"Tool call parsing failed: {parsed_tool['error']}")

            tool_name = parsed_tool['name']
            tool_args = parsed_tool['args']
            
            try:
                if tool_name == "write_to_file":
                    raw_result = self.agent.write_file(**tool_args)
                elif tool_name == "run_command":
                    raw_result = self.agent.run_command(**tool_args)
                elif tool_name == "create_terminal":
                    raw_result = self.agent.create_terminal(**tool_args)
                else:
                    raise ValueError(f"Unknown tool '{tool_name}' requested.")
                
                if raw_result and "ERROR" in str(raw_result).upper():
                    raise Exception(raw_result)
                
                self._update_status(f"✔️ **Step {step_counter} Succeeded!**")
                step_counter += 1
            except Exception as e:
                self._update_status(f"❌ **EXECUTION FAILED on Step {step_counter}. Reason: {e}")
                raise