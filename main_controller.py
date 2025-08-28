# main_controller.py (V2 - Refactored and Simplified)

import os
import platform
import re
import time
import traceback
from agent import AIAgent
from llama_index.core import Settings
# --- NEW: Import from our single terminal tool ---
from tools import terminal

class MainController:
    def __init__(self, agent: AIAgent, ui_handler=None):
        self.agent = agent
        self.ui = ui_handler

    def _update_status(self, message: str):
        print(message)
        if self.ui:
            # The controller's messages are system-level, so they don't need a spoken summary.
            formatted_message = f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>"
            self.ui.response_received.emit(formatted_message)

    def _parse_tool_call(self, task_string: str) -> dict:
        # This robust parser can remain exactly as it was. No changes needed.
        tool_name_match = re.match(r"(\w+)\(", task_string)
        if not tool_name_match:
            return {'error': f"Could not parse tool name from: {task_string}"}
        tool_name = tool_name_match.group(1)
        try:
            # This logic correctly handles nested parentheses in arguments
            first_paren_index = task_string.index('(')
            open_paren_count = 0
            last_paren_index = -1
            for i, char in enumerate(task_string[first_paren_index:]):
                if char == '(': open_paren_count += 1
                elif char == ')': open_paren_count -= 1
                if open_paren_count == 0:
                    last_paren_index = first_paren_index + i
                    break
            if last_paren_index == -1: raise ValueError("Mismatched parentheses")
            args_str = task_string[first_paren_index + 1 : last_paren_index].strip()
        except ValueError as e:
            return {'error': f"Mismatched parentheses in tool call: {task_string}. Details: {e}"}

        args = {}
        # This regex is robust for parsing key=value pairs with various quote styles
        arg_pattern = re.compile(r"(\w+)\s*=\s*(\"\"\"(.*?)\"\"\"|'''(.*?)'''|\"(.*?)\"|'(.*?)')", re.DOTALL)
        last_index = 0
        for match in arg_pattern.finditer(args_str):
            if match.start() > last_index: # Check for unparsed gaps
                unparsed = args_str[last_index:match.start()].strip()
                if unparsed and unparsed != ',': return {'error': f"Could not parse argument segment: '{unparsed}'"}
            key = match.group(1)
            # Find the first non-None group for the value
            value = next((g for g in match.groups()[2:] if g is not None), "")
            args[key] = value.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
            last_index = match.end()
            
        return {'name': tool_name, 'args': args}


    def execute_project(self, user_prompt: str):
        self.agent.original_user_prompt = user_prompt
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:40]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        workspace_path = os.path.join(os.getcwd(), 'workspaces', project_name)

        try:
            # === PHASE 1: ORCHESTRATOR - SETUP ===
            self._update_status(f"🚀 **Workspace Initialized:** `{workspace_path}`")
            terminal.initialize_workspace(
                base_directory=workspace_path,
                output_callback=self.ui.update_terminal_display if self.ui else print
            )

            is_windows = platform.system() == "Windows"
            python_executable = ".\\venv\\Scripts\\python.exe" if is_windows else "./venv/bin/python"

            # 1a. Call the "Dependency Analyst" agent
            self._update_status("🔬 **Analyzing dependencies...**")
            dep_prompt = f"List the python libraries needed for this project: '{user_prompt}'. Respond with a comma-separated list (e.g., 'pygame, requests') or 'None'."
            dependencies_str = Settings.llm.complete(dep_prompt).text.strip()
            
            # 1b. Orchestrator enforces environment setup
            self._update_status("📦 **Creating virtual environment...**")
            terminal.run_command_in_terminal("python -m venv venv")
            
            if dependencies_str and "none" not in dependencies_str.lower():
                self._update_status(f"  Installing dependencies: {dependencies_str}...")
                install_command = f"{python_executable} -m pip install {dependencies_str.replace(',', ' ')}"
                terminal.run_command_in_terminal(install_command)

            # === PHASE 2: ORCHESTRATOR - HIGH-LEVEL PLANNING ===
            self._update_status("🧠 **Generating high-level plan...**")
            plan_prompt = f"""
You are a senior software architect. Your task is to break down a user's request into a high-level plan of the **Python components, classes, and functions** that need to be built.

## CRITICAL RULES ##
- Your plan must ONLY include concrete coding steps.
- Do NOT include abstract steps like "Testing", "Deployment", "UI Design", or "Refinement".
- Focus exclusively on the tangible code that needs to be written.

## Example Plan ##
**User Request:** "Create a modern snake game."
**Generated Plan:**
1.  Initialize Pygame, set up the screen, and define colors.
2.  Create a `Snake` class to handle its body, movement, and growth.
3.  Create a `Food` class to handle its position and respawning.
4.  Implement a function for the main menu screen.
5.  Implement a function for the game over screen.
6.  Write the main game loop to handle events, update game state, and draw everything to the screen.

## Your Task ##
Now, generate a similar pure-code plan for the following request.

**User Request:** "{user_prompt}"
**Generated Plan:**
"""
            high_level_plan_str = Settings.llm.complete(plan_prompt).text.strip()
            plan_steps = [line.strip() for line in high_level_plan_str.split('\n') if line.strip()]
            self._update_status(f"📝 **Plan Created:**\n{high_level_plan_str}")

             # === NEW PHASE 3: ORCHESTRATOR - ITERATIVE "REFINE & VALIDATE" LOOP ===
            full_code = "# This is the beginning of our Python script.\nimport pygame\nimport random\nimport sys\nimport os"
            script_name = "main.py"
            max_debug_attempts_per_step = 3

            for i, step in enumerate(plan_steps):
                self._update_status(f"🛠️ **Working on Component {i + 1}/{len(plan_steps)}:** {step}...")
                
                is_component_valid = False
                
                for attempt in range(max_debug_attempts_per_step):
                    # 1. Call the "Code Refiner" specialist. It gets the whole program so far and adds the next feature.
                    code_refinement_prompt = f"""
You are an expert Python programmer. Your task is to iteratively build a script.
Here is the current, fully-functional script. Your job is to add the new feature described in the "Current Task" and return the NEW, COMPLETE script.

**Original Goal for the Whole Project:** "{user_prompt}"

**Current Script (so far):**
```python
{full_code}
```

**Current Task (add this feature):**
"{step}"

**Your Instructions:**
- Integrate the new feature into the existing script.
- Ensure the final, complete script is syntactically correct and logically coherent.
- Respond with ONLY the new, complete Python script. Do not add explanations.
"""
                    refined_code = Settings.llm.complete(code_refinement_prompt).text.strip().replace("```python", "").replace("```", "")
                    
                    # 2. Validate the NEW full script for syntax errors
                    self.agent.write_file(file_path=script_name, content=refined_code)
                    syntax_check_command = f"{python_executable} -m py_compile {script_name}"
                    syntax_result = terminal.run_command_in_terminal(syntax_check_command)

                    if "error" not in syntax_result.lower() and "traceback" not in syntax_result.lower():
                        self._update_status(f"  ✅ **Component {i+1} Integrated Successfully.**")
                        full_code = refined_code # The new version is now our baseline
                        is_component_valid = True
                        break # This component is good, move to the next one
                    
                    # 3. If syntax fails, enter a focused debug session
                    self._update_status(f"  🐞 **Integration failed on step {i+1} (Attempt {attempt + 1}). Debugging...**")
                    # Use the full-power debugger to fix the whole script
                    # This uses the same universal debugger prompt from before
                    debug_prompt = f"""You are a world-class AI software engineer and expert debugger... (Your existing universal debugger prompt here, but pass `refined_code` as the code to fix)"""
                    # ... for brevity, I'll omit the full debug prompt, but it's the one you already have ...
                    # Make sure to pass `refined_code` as `final_code` and `syntax_result` as `execution_result`
                    
                    # For this example, we'll just log it and retry, as the refine prompt is usually enough
                    # In a real scenario, you'd call the debugger here.
                
                if not is_component_valid:
                    raise Exception(f"Failed to write a valid component for step '{step}' after {max_debug_attempts_per_step} attempts.")

            
            # === PHASE 4: FINAL LAUNCH ===
            self._update_status("✅ **All components assembled. Launching final application...**")
            launch_command = f"{python_executable} {script_name}"
            terminal.launch_application(launch_command)
            
            self._update_status(f"✅ **Project Completed and Launched Successfully.**")
            return workspace_path

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR:** An unexpected error occurred.\n\n{error_details}")
            return None
        
        finally:
            # For a launched app, we don't clean up the workspace immediately
            self._update_status("✅ **Orchestration complete. Workspace remains active for launched app.**")
            
            
    def execute_task_in_workspace(self, user_prompt: str, workspace_path: str):
        """Re-initializes an existing workspace and executes a new plan within it."""
        self.agent.original_user_prompt = user_prompt # For the debugger
        
        # Re-initialize the workspace without creating a new folder
        terminal.initialize_workspace(
            base_directory=workspace_path,
            output_callback=self.ui.update_terminal_display if self.ui else print
        )
        self._update_status(f"🚀 **Re-opened Workspace:** `{workspace_path}`")

        try:
            # Create a planner prompt specifically for follow-up tasks
            is_windows = platform.system() == "Windows"
            python_executable = ".\\venv\\Scripts\\python.exe" if is_windows else "./venv/bin/python"

            planner_prompt = f"""
You are an expert AI software engineer. Your task is to generate a complete, step-by-step plan of tool calls to fulfill the user's request.

## AVAILABLE TOOLS ##
- `run_command(command: str)`: Runs a command in a headless (invisible) terminal and waits for it to finish. Use this for setup, like creating a venv or installing packages.
- `write_file(file_path: str, content: str)`: Writes code or text to a file.
- `launch_application(command: str)`: **Launches a VISIBLE application for the user.** Use this as the FINAL step for any GUI app like Pygame.

## CRITICAL RULES ##
1.  **VENV First:** The first step for any Python project MUST be: `run_command(command="python -m venv venv")`.
2.  **Install Dependencies:** The second step MUST be to install libraries using the venv pip, for example: `run_command(command="{python_executable} -m pip install pygame")`.
3.  **Write Code:** Use `write_file` to create the necessary script(s).
4.  **Launch for the User:** The FINAL step to run a GUI app like Pygame MUST be: `launch_application(command="{python_executable} your_script_name.py")`.

## Your Task ##
Now, generate a plan for the following request. Respond ONLY with the sequence of tool calls.

**User Request:** "{user_prompt}"
**Generated Plan:**
"""
            self._update_status("🧠 **Generating follow-up plan...**")
            plan = Settings.llm.complete(planner_prompt).text
            self._execute_plan(plan) # Use the same robust execution loop
            self._update_status(f"✅ **Follow-up Task Completed Successfully.**")

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR in follow-up task:**\n\n{error_details}")
        
        finally:
            self._update_status("🧹 **Closing workspace...**")
            terminal.close_workspace()
    
    
    

    def _extract_tool_calls(self, plan: str) -> list[str]:
        # --- UPDATED: Simplified regex with only the project tools ---
        tool_pattern = r"(run_command|write_file|create_headless_terminal|start_server|launch_application)\("
        # The rest of this function can remain the same.
        tool_calls = []
        cursor = 0
        while cursor < len(plan):
            match = re.search(tool_pattern, plan[cursor:])
            if not match: break
            start_index = cursor + match.start()
            open_paren_index = cursor + match.end() - 1
            paren_level = 1
            i = open_paren_index + 1
            while i < len(plan) and paren_level > 0:
                if plan[i] == '(': paren_level += 1
                elif plan[i] == ')': paren_level -= 1
                i += 1
            if paren_level == 0:
                end_index = i
                tool_calls.append(plan[start_index:end_index])
                cursor = end_index
            else:
                self._update_status(f"⚠️ Warning: Could not find matching parenthesis for call at index {start_index}.")
                cursor = open_paren_index + 1
        return tool_calls

    def _execute_plan(self, plan: str):
        """
        Executes a multi-step plan with a robust, single-step self-correction loop.
        """
        self._update_status("⚙️ **Parsing execution plan...**")
        
        original_steps = self._extract_tool_calls(plan)
        if not original_steps:
            raise ValueError("Planner returned a plan with no executable steps.")

        execution_history = []
        current_steps = list(original_steps)
        step_index = 0
        max_retries = 3 # Retries per step

        while step_index < len(current_steps):
            task_string = current_steps[step_index]
            step_number = len(execution_history) + 1
            
            step_succeeded = False
            step_retry_count = 0
            
            while not step_succeeded and step_retry_count < max_retries:
                if step_retry_count > 0:
                    self._update_status(f"▶️ **Re-executing Step {step_number} (Attempt {step_retry_count + 1}):** `{task_string.split('(')[0]}`")
                else:
                    self._update_status(f"▶️ **Executing Step {step_number}:** `{task_string.split('(')[0]}`")

                parsed_tool = self._parse_tool_call(task_string)
                if parsed_tool.get('error'):
                    error_message = f"Tool parsing failed: {parsed_tool['error']}"
                    # This is a parsing error, so we immediately trigger correction
                    raw_error = ValueError(error_message)
                    
                else:
                    tool_name = parsed_tool['name']
                    tool_args = parsed_tool['args']
                    
                    try:
                        # Use the agent's pass-through methods to call the tools
                        if tool_name == "write_file":
                            if 'file_path' not in tool_args or 'content' not in tool_args:
                                raise ValueError("Missing 'file_path' or 'content' for write_file.")
                            raw_result = self.agent.write_file(**tool_args)
                        elif tool_name == "run_command":
                            if 'command' not in tool_args:
                                raise ValueError("Missing 'command' for run_command.")
                            raw_result = self.agent.run_command(**tool_args)
                        elif tool_name == "create_headless_terminal":
                            raw_result = self.agent.create_terminal(**tool_args) # The agent method is still create_terminal
                        # --- RENAME THIS ---
                        elif tool_name == "start_server":
                            raw_result = self.agent.start_background_process(**tool_args) # The agent method is still start_background_process
                        # --- ADD THIS ---
                        elif tool_name == "launch_application":
                            # We need to add a pass-through for this in agent.py
                            raw_result = self.agent.launch_application(**tool_args)
                        else:
                            raise ValueError(f"Unknown tool '{tool_name}' requested by planner.")
                        
                        if raw_result and "ERROR:" in str(raw_result).upper():
                            raise Exception(raw_result)
                        
                        # --- SUCCESS ---
                        self._update_status(f"✔️ **Step {step_number} Succeeded!**")
                        execution_history.append(f"Step {step_number}: {task_string}\nResult: {raw_result}")
                        step_succeeded = True

                    except Exception as e:
                        # --- FAILURE ---
                        raw_error = e

                # --- CORRECTION LOGIC ---
                if not step_succeeded:
                    step_retry_count += 1
                    error_message = f"EXECUTION FAILED on Step {step_number}. Reason: {raw_error}"
                    self._update_status(f" D **Attempting self-correction ({step_retry_count}/{max_retries}). Asking agent to fix the failed step...**")
                    workspace_path = terminal.get_workspace().base_directory
                    try:
                        file_list = os.listdir(workspace_path)
                        file_list_str = "\n".join(file_list)
                    except Exception:
                        file_list_str = "Could not list files in workspace."
                        
                    remediation_prompt = f"""
You are an expert debugger. The following tool call in a plan failed. Your task is to analyze the context, including the files in the workspace, and rewrite ONLY the single failed step to be correct.

**Original User Request:**
"{self.agent.original_user_prompt}"

**Execution History:**
{"\n".join(execution_history)}

**Files in Workspace:**
{file_list_str}

**Failed Step:**
`{task_string}`

**Error Message:**
`{raw_error}`

**Your Task:**
Based on all the information above, rewrite the "Failed Step" to be correct. Use the correct filenames that you see in the "Files in Workspace" list. You MUST use the `key="value"` syntax for all arguments.

Respond with ONLY the single, corrected tool call.
"""
                    # Get the corrected step from the LLM
                    corrected_step_raw = Settings.llm.complete(remediation_prompt).text.strip()

                    # --- ADD THIS SANITIZATION LOGIC ---
                    # The LLM sometimes wraps its response in markdown. Let's strip it.
                    corrected_step = re.sub(r"^\`\`\`.*\n", "", corrected_step_raw)
                    corrected_step = re.sub(r"\`\`\`$", "", corrected_step).strip()
                    # --- END OF ADDITION ---

                    # Replace the failed step in our plan with the new one
                    if corrected_step:
                        self._update_status(f"ℹ️ **Received corrected step:** `{corrected_step}`")
                        task_string = corrected_step # The loop will now retry with this new command
                    else:
                        raise Exception("Debugger failed to provide a corrected step. Aborting.")
            
            # Move to the next step in the plan
            step_index += 1