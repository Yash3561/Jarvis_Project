# main_controller.py (V-Final - Tool-Aware Controller)

import os
import platform
import re
import time
from agent import AIAgent
from llama_index.core import Settings
from tools.workspace import initialize_workspace, close_workspace

class MainController:
    def __init__(self, agent: AIAgent, ui_handler=None):
        self.agent = agent
        self.ui = ui_handler

    def _update_status(self, message: str):
        """Safely sends a status update to the UI."""
        print(message)
        if self.ui:
            formatted_message = f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>"
            self.ui.response_received.emit(formatted_message)

    def execute_project(self, user_prompt: str):
        # --- Step 1: Initialize Project and Workspace ---
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:30]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        workspace_path = os.path.join(os.getcwd(), project_name)
        os.makedirs(workspace_path, exist_ok=True)
        print(f"✅ Workspace created at: `{workspace_path}`")

        output_callback = self.ui.update_terminal_display if self.ui else None
        initialize_workspace(base_directory=workspace_path, output_callback=output_callback)

        try:
            # --- Step 2: Generate the Advanced Plan ---
            planner_prompt = f"""
You are an expert-level AI software engineer. Your task is to generate a complete, step-by-step plan of commands to achieve the user's goal.

## Environment Context ##
- **Operating System:** {platform.system()}
- **Project Workspace:** `{workspace_path}`

## Core Agent Capabilities ##
1.  **File Writing:** Use the special `write_to_file(...)` block. All paths must be absolute.
2.  **Shell Commands:** Use `run_command(...)` for synchronous tasks that need to finish before the next step (like `mkdir`, `cd`, `pip install`).
3.  **Visible Server Launch:** To start a long-running server in a **NEW VISIBLE WINDOW**, you MUST use a `run_command` with the Windows `start` command.

## CRITICAL RULES ##
1.  All file paths and directory paths MUST be absolute.
2.  Do not use `echo` to write files. Use the `write_to_file` block.
3.  The final plan MUST launch the servers in new windows for the user to see.

## INSTRUCTION FORMATS ##

### Shell Command (Synchronous) ###
1. Step Title
```tool_code
run_command(command="cd {workspace_path}\\backend && pip install flask")
```

### File Creation Block ###
2. Step Title
```tool_code
write_to_file(file_path="{workspace_path}\\backend\\app.py", content="...")
```

### Visible Server Launch (Asynchronous) ###
3. Step Title
```tool_code
run_command(command="start cmd /k python app.py", terminal_name="backend")
```
`# The 'start cmd /k' is the Windows command to open a new terminal and run a command.`

### Browser Launch ###
4. Step Title
```tool_code
open_url_in_browser(url="http://localhost:5173")
```
---
## User Request ##
"{user_prompt}"

Generate the complete plan now.
"""
            self._update_status("📝 **Generating project plan...**")
            plan = Settings.llm.complete(planner_prompt).text
            self._update_status(f"📜 **Plan Created**\n\n---\n{plan}\n---")

            # --- Step 3: The FINAL, Tool-Aware Execution Loop ---
            plan_lines = [line for line in plan.split('\n') if line.strip()]
            i = 0
            step_counter = 1
            while i < len(plan_lines):
                line = plan_lines[i].strip()
                
                # Find the human-readable step title
                title_match = re.match(r"^\s*\d+\.\s*(.*)", line)
                if not title_match:
                    i += 1
                    continue

                step_title = title_match.group(1).strip()
                self._update_status(f"▶️ **Executing Step {step_counter}:** {step_title}")

                # Find the corresponding ```tool_code block
                task_string = ""
                try:
                    # Find the start of the code block
                    start_index = i + plan_lines[i+1:].index("```tool_code") + 1
                    end_index = start_index + plan_lines[start_index:].index("```")
                    task_lines = plan_lines[start_index:end_index]
                    task_string = "\n".join(task_lines).strip()
                    i = end_index + 1 # Move the main loop counter past this entire block
                except (ValueError, IndexError):
                    self._update_status(f"❌ **PARSING ERROR:** Could not find a valid ```tool_code block for step: {step_title}. Project halted.")
                    return

                # Execute the parsed task_string
                raw_result = ""
                if task_string.startswith("write_to_file"):
                    try:
                        path_match = re.search(r"file_path=\"(.*?)\"", task_string, re.DOTALL)
                        content_match = re.search(r"content=\"\"\"(.*?)\"\"\"", task_string, re.DOTALL)
                        file_path = path_match.group(1)
                        content = content_match.group(1)
                        raw_result = self.agent.write_file(file_path, content)
                    except Exception as e:
                        raw_result = f"ERROR parsing write_to_file: {e}"
                
                elif task_string.startswith("create_terminal"):
                    try:
                        name_match = re.search(r"name=\"(.*?)\"", task_string)
                        name = name_match.group(1)
                        raw_result = self.agent.create_terminal(name)
                    except Exception as e:
                        raw_result = f"ERROR parsing create_terminal: {e}"

                elif task_string.startswith("run_command"):
                    try:
                        cmd_match = re.search(r"command=\"(.*?)\"", task_string, re.DOTALL)
                        term_match = re.search(r"terminal_name=\"(.*?)\"", task_string, re.DOTALL)
                        command = cmd_match.group(1)
                        terminal_name = term_match.group(1) if term_match else "default"
                        raw_result = self.agent.run_command(command, terminal_name)
                    except Exception as e:
                        raw_result = f"ERROR parsing run_command: {e}"

                elif task_string.startswith("start_server_command"):
                    try:
                        cmd_match = re.search(r"command=\"(.*?)\"", task_string, re.DOTALL)
                        term_match = re.search(r"terminal_name=\"(.*?)\"", task_string, re.DOTALL)
                        command = cmd_match.group(1)
                        terminal_name = term_match.group(1)
                        raw_result = self.agent.start_server_command(command, terminal_name)
                    except Exception as e:
                        raw_result = f"ERROR parsing start_server_command: {e}"
                
                elif task_string.startswith("open_url_in_browser"):
                    try:
                        url_match = re.search(r"url=\"(.*?)\"", task_string)
                        url = url_match.group(1)
                        raw_result = self.agent.open_url_in_browser(url)
                    except Exception as e:
                        raw_result = f"ERROR parsing open_url_in_browser: {e}"

                # Simplified critique logic
                self._update_status(f"🤔 **Critique:** {raw_result}")
                if "ERROR" in str(raw_result).upper():
                    self._update_status(f"❌ **Step {step_counter} Failed. Project halted.**")
                    return
                
                self._update_status(f"✔️ **Step {step_counter} Succeeded!**")
                step_counter += 1

            self._update_status(f"🎉 **Project completed successfully.**")

        finally:
            print("INFO: Project finished. Closing workspace.")
            close_workspace()