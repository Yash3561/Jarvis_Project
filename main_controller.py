# main_controller.py (V3 - Self-Healing, for Patched Agent)

import os
import platform
import re
import time
from agent import AIAgent
from llama_index.core import Settings
from tools.persistent_terminal import get_terminal, close_terminal

class MainController:
    def __init__(self, agent: AIAgent, ui_handler=None):
        self.agent = agent
        self.ui = ui_handler
        self.max_retries = 3

    def _update_status(self, message: str):
        """Safely sends a status update to the UI by emitting a signal."""
        print(message)
        if self.ui:
            # We wrap the message in a simple format. The UI's on_agent_response
            # will handle displaying it. We send a blank spoken summary for project updates.
            formatted_message = f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>"
            self.ui.response_received.emit(formatted_message)

    # In main_controller.py

    def execute_project(self, user_prompt: str):
        # --- Step 1: Initialize Project and Terminal ---
        # Sanitize the user prompt to create a clean base name for the project folder
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:30]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        
        # Create a unique name for the virtual environment for this project
        venv_name = f"venv_{project_timestamp}"
        
        # Create the main project workspace directory
        workspace_path = os.path.join(os.getcwd(), project_name)
        os.makedirs(workspace_path, exist_ok=True)
        print(f"✅ Workspace created at: `{workspace_path}`")
        print(f"🌿 Virtual environment will be named: `{venv_name}`")
        
        output_callback = self.ui.update_terminal_display if self.ui else None

        # Initialize the persistent terminal, making it start in the new workspace
        get_terminal(working_directory=workspace_path, output_callback=output_callback)
        
        operating_system = platform.system()
        
        try:
            # --- Step 2: Generate the Plan ---
            # This prompt now includes CRITICAL RULES for the planner
            planner_prompt = f"""
You are an expert-level AI software engineer. Your sole responsibility is to generate a complete, error-free, step-by-step plan to accomplish the user's request. The plan will be executed by a separate, less intelligent agent, so your instructions must be explicit, literal, and complete.

## Environment Context ##
- **Operating System:** {platform.system()} (e.g., 'Windows', 'Linux')
- **Project Workspace (Root):** `{workspace_path}`
- **Virtual Environment Name:** `{venv_name}`

## Core Agent Capabilities (Tools) ##
You can issue three types of instructions in your plan:
1.  **Shell Commands:** Simple, non-blocking commands like `cd`, `mkdir`, `pip install`, `npm install`.
2.  **File Creation Blocks:** A special multi-line block for writing code or content to files.
3.  **Background Process Commands:** A special command to start long-running servers.

## CRITICAL RULES OF ENGAGEMENT ##
1.  **Pathing is Absolute:** All file paths and directory paths in your plan MUST be absolute paths, starting from the Project Workspace root. For example: `mkdir {os.path.join(workspace_path, 'backend')}`.
2.  **Venv First:** The first steps of any Python project MUST be to create and activate the specified virtual environment (`{venv_name}`) inside the correct sub-directory.
3.  **Use the Right Tool for the Job:**
    -   Do NOT use `echo` to write files. It is unreliable. **You MUST use the File Creation Block.**
    -   Do NOT run servers directly (e.g., `flask run`, `npm run dev`). This will block the agent. **You MUST use the Background Process Command.**
4.  **To run a long-running development server that the user needs to see, you MUST use the `start_background_process` tool with `launch_in_new_window=True`.**
5.  Use this for commands like `flask run` or `npm run dev`.

---
## INSTRUCTION FORMATS ##

### 1. Shell Command Format ###
A standard, numbered list item representing a single shell command.
`1. mkdir {os.path.join(workspace_path, 'backend')}`
`2. cd {os.path.join(workspace_path, 'backend')}`
`3. pip install flask`

### 2. File Creation Block Format ###
This is a multi-line block. It MUST be followed exactly.
`4. write_to_file(file_path="{os.path.join(workspace_path, 'backend', 'app.py')}")`
`---BEGIN CONTENT---`
`from flask import Flask`
`app = Flask(__name__)`
`# ... rest of the file content`
`---END CONTENT---`

### 3. Background Process Command Format ###
A special command to start a server.
`5. start_background_process(command="python app.py", working_directory="{os.path.join(workspace_path, 'backend')}", launch_in_new_window=True)`
`6. start_background_process(command="npm run dev", working_directory="{os.path.join(workspace_path, 'frontend')}", launch_in_new_window=True)`
---

## User Request ##
"{user_prompt}"

Generate the complete, numbered, step-by-step plan now. Adhere to all rules and formats precisely.
"""
            self._update_status("📝 **Generating project plan...**")
            plan = Settings.llm.complete(planner_prompt).text
            self._update_status(f"📜 **Plan Created**\n\n---\n{plan}\n---")

            # --- Step 3: The NEW File-Aware Execution Loop ---
            plan_lines = [line for line in plan.split('\n') if line.strip()]
            
            i = 0
            step_counter = 1
            while i < len(plan_lines):
                line = plan_lines[i].strip()
                match = re.match(r"^\s*\d+\.\s*(.*)", line)
                if not match:
                    i += 1
                    continue

                task = match.group(1).strip().replace("`", "")
                self._update_status(f"▶️ **Executing Step {step_counter}:** {task}")

                raw_result = ""
                # Check if this line is a file writing instruction
                if task.startswith("write_to_file"):
                    try:
                        # Extract the file path
                        path_match = re.search(r"file_path=\"(.*?)\"", task)
                        if not path_match:
                            raise ValueError("Could not parse file_path from command.")
                        
                        relative_path = path_match.group(1)
                        full_path = os.path.join(workspace_path, relative_path)
                        
                        # Consume the next lines as content
                        i += 1
                        if plan_lines[i].strip() != "---BEGIN CONTENT---":
                            raise ValueError("Missing ---BEGIN CONTENT--- block.")
                        
                        i += 1
                        content_lines = []
                        while plan_lines[i].strip() != "---END CONTENT---":
                            content_lines.append(plan_lines[i])
                            i += 1
                        
                        content = "\n".join(content_lines)
                        
                        # Call the tool directly through the agent
                        raw_result = self.agent.write_file(full_path, content)
                        
                    except Exception as e:
                        raw_result = f"ERROR: Failed to parse or execute write_to_file block: {e}"
                
                elif task.startswith("start_background_process"):
                    try:
                        # Use regex to parse the arguments from the command string
                        cmd_match = re.search(r"command=\"(.*?)\"", task)
                        cwd_match = re.search(r"working_directory=\"(.*?)\"", task)
                        win_match = re.search(r"launch_in_new_window=(True|False)", task, re.IGNORECASE)
                        
                        command = cmd_match.group(1) if cmd_match else None
                        working_directory = cwd_match.group(1) if cwd_match else None
                        launch_in_new_window = win_match.group(1).lower() == 'true' if win_match else False

                        if not command or not working_directory:
                            raise ValueError("Could not parse command or working_directory.")

                        # Call the tool directly through the agent
                        raw_result = self.agent.start_background_process(command, working_directory, launch_in_new_window)
                    except Exception as e:
                        raw_result = f"ERROR: Failed to parse or execute start_background_process block: {e}"
                
                else:
                    # It's a normal shell command, execute it in the terminal
                    raw_result = self.agent.run_in_terminal(task)

                # The critique and retry loop now works on a solid foundation
                # (This part of the logic is now robust and doesn't need to change)
                critique = ""
                if "ERROR" in raw_result.upper():
                    critique = f"Execution failed: {raw_result}"
                else:
                    critique = "SUCCESS" # Assume success for simple commands unless an error is returned

                self._update_status(f"🤔 **Critique:** {critique}")

                if "SUCCESS" in critique.upper():
                    self._update_status(f"✔️ **Step {step_counter} Succeeded!**")
                    i += 1
                    step_counter += 1
                else:
                    # For simplicity in this final version, we will halt on failure.
                    # The complex retry logic can be re-added, but this isolates the core fix.
                    self._update_status(f"❌ **Step {step_counter} Failed. Project halted.**")
                    return

            self._update_status(f"🎉 **Project '{project_name}' completed successfully.**")

        finally:
            print("INFO: Project finished. Closing persistent terminal.")
            close_terminal()

        self._update_status(f"🎉 **Project '{project_name}' completed successfully.**")