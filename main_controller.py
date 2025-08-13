# main_controller.py (V3 - Self-Healing, for Patched Agent)

import os
import platform
import re
import time
from agent import AIAgent
from llama_index.core import Settings
from tools.persistent_terminal import get_terminal, close_terminal
from tools.workspace import initialize_workspace, close_workspace

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
            # --- Step 2: Generate the Multi-Terminal Plan ---
            planner_prompt = f"""
You are an expert-level AI software engineer. Your task is to generate a complete, step-by-step plan of commands to achieve the user's goal.

## Environment Context ##
- **Operating System:** {platform.system()}
- **Project Workspace:** `{workspace_path}`

## Core Agent Capabilities ##
1.  **File Writing:** Use the special `write_to_file(file_path="...")` block. All paths must be absolute.
2.  **Multi-Terminal Shell:** You have a workspace with multiple, named terminals.
    -   You start with one terminal named `default`.
    -   You can create new terminals with `create_terminal(name="...")`.
    -   You can run commands in any terminal with `run_command(command="...", terminal_name="...")`.

## CRITICAL RULES ##
1.  **Run servers in their own terminals.** For a full-stack app, create a `backend` terminal and a `frontend` terminal.
2.  All file paths MUST be absolute.
3.  Do not use `echo` to write files; use the `write_to_file` block.

## User Request ##
"{user_prompt}"

Generate the complete, numbered, step-by-step plan now.
"""
            self._update_status("📝 **Generating project plan...**")
            plan = Settings.llm.complete(planner_prompt).text
            self._update_status(f"📜 **Plan Created**\n\n---\n{plan}\n---")

            # --- Step 3: The FINAL, Tool-Aware Execution Loop ---
            plan_lines = [line for line in plan.split('\n') if line.strip()]
            i = 0
            step_counter = 1
            while i < len(plan_lines):
                # ... (This is the file-aware parsing and execution loop from our last successful version) ...
                # It now correctly handles run_command and create_terminal as normal shell commands
                # because the controller passes them to the agent, which calls the tools.
                # The logic does not need to change here, just the planner prompt.
                line = plan_lines[i].strip()
                match = re.match(r"^\s*\d+\.\s*(.*)", line)
                if not match:
                    i += 1; continue
                
                task = match.group(1).strip().replace("`", "")
                self._update_status(f"▶️ **Executing Step {step_counter}:** {task}")

                raw_result = ""
                # Parse and execute different command types
                if task.startswith("write_to_file"):
                    # (Your existing, correct file-writing logic)
                    pass 
                elif task.startswith("create_terminal"):
                    try:
                        name_match = re.search(r"name=\"(.*?)\"", task)
                        name = name_match.group(1)
                        raw_result = self.agent.create_terminal(name)
                    except Exception as e:
                        raw_result = f"ERROR parsing create_terminal: {e}"
                else: # Default to a shell command
                    try:
                        cmd_match = re.search(r"command=\"(.*?)\"", task)
                        term_match = re.search(r"terminal_name=\"(.*?)\"", task)
                        command = cmd_match.group(1) if cmd_match else task
                        terminal_name = term_match.group(1) if term_match else "default"
                        raw_result = self.agent.run_command(command, terminal_name)
                    except Exception as e:
                        raw_result = f"ERROR parsing run_command: {e}"

                # Simplified critique logic
                self._update_status(f"🤔 **Critique:** {raw_result}")
                if "ERROR" in raw_result.upper():
                    self._update_status(f"❌ **Step {step_counter} Failed. Project halted.**")
                    return
                
                self._update_status(f"✔️ **Step {step_counter} Succeeded!**")
                i += 1
                step_counter += 1

            self._update_status(f"🎉 **Project completed successfully.**")

        finally:
            print("INFO: Project finished. Closing workspace.")
            close_workspace()

        self._update_status(f"🎉 **Project '{project_name}' completed successfully.**")