# main_controller.py (V9 - Batch Generation & Orchestration Fixes)

import os
import platform
import re
import time
import traceback
from agent import AIAgent
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
from tools import terminal, browser, file_system

class MainController:
    # ======================================================================================
    # == INITIALIZATION AND CORE UI COMMUNICATION                                         ==
    # ======================================================================================
    
    def __init__(self, agent: AIAgent, ui_handler=None):
        """Initializes the MainController, the central brain of the application."""
        self.agent = agent
        self.ui = ui_handler

    def _update_status(self, message: str):
        """Sends a status update to the console and the UI."""
        print(message)
        if self.ui:
            # This formatting seems specific to your UI, keeping it as is.
            formatted_message = f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>"
            self.ui.response_received.emit(formatted_message)

    # ======================================================================================
    # == PRIMARY ORCHESTRATOR FOR CREATING NEW PROJECTS (execute_project)                 ==
    # ======================================================================================

    def execute_project(self, user_prompt: str):
        """
        The main entry point for creating a new software project. This method orchestrates
        a multi-agent, playbook-driven, "build-then-launch" workflow.
        """
        self.agent.original_user_prompt = user_prompt
        workspace_path = self._initialize_workspace_directory(user_prompt)

        try:
            # === PHASE 1: ANALYSIS & SETUP ===
            self._update_status(f"🚀 **Workspace Initialized:** `{workspace_path}`")
            terminal.initialize_workspace(
                base_directory=workspace_path,
                output_callback=self.ui.update_terminal_display if self.ui else print
            )

            language_guess = self._analyze_language(user_prompt)
            playbook = self._load_playbook(language_guess)
            dependencies_str = self._analyze_dependencies(user_prompt, language_guess)
            self._setup_environment(playbook, dependencies_str)

            # === PHASE 2: HIGH-LEVEL PLANNING ===
            high_level_plan_str = self._generate_high_level_plan(user_prompt, language_guess)
            
            # === PHASE 3: CODE IMPLEMENTATION (BUILD) ===
            self._update_status("🏗️ **Constructing application from plan...**")
            self._implement_plan_from_scratch(high_level_plan_str, workspace_path, language_guess)
            
            # === PHASE 4: LAUNCH & PREVIEW ===
            self._update_status("🚀 **Starting development servers...**")
            self._launch_dev_servers(playbook, workspace_path)
            
            self._update_status(f"✅ **Development complete. Final application is live in the browser.**")
            return workspace_path

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR:** An unexpected error occurred.\n\n{error_details}")
            return None
        
        finally:
            self._update_status("✅ **Orchestration complete. Workspace remains active for launched app.**")
    
    # --- Orchestrator Helper Methods ---

    def _initialize_workspace_directory(self, user_prompt: str) -> str:
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:40]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        return os.path.join(os.getcwd(), 'workspaces', project_name)

    def _analyze_language(self, user_prompt: str) -> str:
        self._update_status("🔬 **Analyzing project stack...**")
        lang_message = [ChatMessage(role=MessageRole.SYSTEM, content="You are a senior architect. Identify the primary tech stack from the user's request. Respond with keywords ONLY. E.g., 'Python, Pygame', 'React, JavaScript, Node.js'."), ChatMessage(role=MessageRole.USER, content=f"User request: \"{user_prompt}\"")]
        return Settings.llm.chat(lang_message).message.content.strip().lower()

    def _load_playbook(self, language_guess: str) -> dict:
        playbook_dir = "data/playbooks"
        try:
            playbook_files = [f for f in os.listdir(playbook_dir) if f.endswith(".md")]
            if playbook_files:
                selector_prompt = [ChatMessage(role=MessageRole.SYSTEM, content="You are an expert architect. Select the single best playbook file from the list based on the user's analyzed tech stack. Respond with ONLY the filename."), ChatMessage(role=MessageRole.USER, content=f"Available Playbooks: {', '.join(playbook_files)}\nUser's Tech Stack: \"{language_guess}\"")]
                selected_filename = Settings.llm.chat(selector_prompt).message.content.strip().replace('`', '')
                if selected_filename in playbook_files:
                    self._update_status(f"📖 **Playbook Selected:** `{selected_filename}`")
                    content = file_system.read_file(os.path.join(playbook_dir, selected_filename))
                    playbook = {'setup': content.split("## Setup Commands")[1].split("##")[0].strip(), 'install': content.split("## Dependency Installation Command")[1].split("##")[0].strip(), 'launch': content.split("## Launch Commands")[1].split("##")[0].strip(), 'port': content.split("## Default Port")[1].split("##")[0].strip()}
                    return playbook
        except Exception as e:
            self._update_status(f"⚠️ **Playbook loading error:** {e}")
        
        self._update_status("⚠️ **No specific playbook found. Using generic Python fallback.**")
        return {"setup": "python -m venv venv", "install": ".\\venv\\Scripts\\python.exe -m pip install [packages]", "launch": ".\\venv\\Scripts\\python.exe main.py", "port": "None"}

    def _analyze_dependencies(self, user_prompt: str, language_guess: str) -> str:
        dep_message = [ChatMessage(role=MessageRole.SYSTEM, content=f"You are a dependency analyst. For a '{language_guess}' project, list required pip/npm packages. Respond with a comma-separated list or 'None'. Do not include built-in libraries."), ChatMessage(role=MessageRole.USER, content=f"User request: \"{user_prompt}\"")]
        return Settings.llm.chat(dep_message).message.content.strip()

    def _setup_environment(self, playbook: dict, dependencies_str: str):
        self._update_status(f"📦 **Setting up environment using playbook...**")
        if playbook.get('setup') and "none" not in playbook.get('setup').lower():
            for command in playbook['setup'].split('\n'):
                terminal.run_command_in_terminal(command.strip())
        if dependencies_str and "none" not in dependencies_str.lower():
            self._update_status(f"  Installing dependencies: {dependencies_str}...")
            install_template = playbook.get('install', "echo 'No install command'")
            install_command = install_template.replace("[packages]", dependencies_str.replace(',', ' '))
            install_result = terminal.run_command_in_terminal(install_command)
            if "error" in install_result.lower():
                self._update_status(f"⚠️ **Dependency Installation Warning:** Log:\n{install_result}")

    def _generate_high_level_plan(self, user_prompt: str, language_guess: str) -> str:
        self._update_status("🧠 **Generating high-level, multi-file plan...**")
        plan_message = [ChatMessage(role=MessageRole.SYSTEM, content=f"You are a senior software architect. Create a machine-readable plan of files and their components for a '{language_guess}' project. Structure your plan by filename, starting with `File:`. Do NOT add any conversational text."), ChatMessage(role=MessageRole.USER, content=f"User Request: \"{user_prompt}\"")]
        plan_str = Settings.llm.chat(plan_message).message.content.strip()
        if not plan_str.lower().startswith("file:"):
            raise Exception(f"Planner failed to produce a valid plan. Response: '{plan_str}'")
        self._update_status(f"📝 **Plan Created:**\n{plan_str}")
        return plan_str

    def _implement_plan_from_scratch(self, plan_str: str, workspace_path: str, language_guess: str):
        """Builds the entire project from scratch, file by file, using a more efficient 'batch' approach."""
        self._update_status("📄 **Parsing structured plan...**")
        structured_plan = self._parse_plan_to_dict(plan_str)
        file_list = "\n".join(structured_plan.keys())

        for file_name, components in structured_plan.items():
            self._update_status(f"  - **Generating code for:** `{file_name}`")
            
            # If a file was created by a setup command (e.g., npx create-react-app), we should skip overwriting it
            # unless there are specific components planned for it. This avoids deleting boilerplate.
            file_path_on_disk = os.path.join(workspace_path, file_name)
            if os.path.exists(file_path_on_disk) and not components:
                self._update_status(f"    -> Skipping file `{file_name}` as it already exists and has no planned changes.")
                continue

            generation_prompt = f"""You are an expert full-stack developer specializing in '{language_guess}'. Your task is to write the complete code for a single file based on the provided project plan.

**Project Goal:** "{self.agent.original_user_prompt}"

**Overall File Structure for Context:**
{file_list}

---

**Current File to Generate:** `{file_name}`

**Key Components/Features for this file:**
- {"\n- ".join(components)}

---

Respond with ONLY the raw, complete code for the `{file_name}` file. Do not include any conversational text, explanations, or markdown formatting like ```.
"""
            try:
                generated_code = Settings.llm.complete(generation_prompt).text.strip()
                
                # Robustness: Clean up markdown code blocks if the LLM adds them anyway
                if generated_code.startswith("```"):
                    match = re.search(r"```(?:\w+\n)?(.*)```", generated_code, re.DOTALL)
                    if match:
                        generated_code = match.group(1).strip()
                
                self.agent.write_file(file_path=file_name, content=generated_code)
                self._update_status(f"    -> Successfully wrote {len(generated_code)} characters to `{file_name}`")
                time.sleep(0.5) # Brief pause for file system operations

            except Exception as e:
                self._update_status(f"    -> ⚠️ **Error:** Failed to generate code for `{file_name}`. Details: {e}")

    def _launch_dev_servers(self, playbook: dict, workspace_path: str):
        """Launches the development servers after the initial code has been written."""
        if playbook.get('port') and "none" not in playbook['port'].lower():
            launch_commands_str = playbook.get('launch', 'echo "No launch command found."')
            launch_commands = [line.strip() for line in launch_commands_str.split('\n') if line.strip() and not line.startswith('#')]
            
            for command in launch_commands:
                terminal_name_match = re.match(r'\[(\w+)\]\s*(.*)', command)
                if terminal_name_match:
                    server_terminal = terminal_name_match.group(1)
                    actual_command = terminal_name_match.group(2)
                    self._update_status(f"  - Starting dev server in '{server_terminal}' terminal: `{actual_command}`")
                    terminal.create_headless_terminal(server_terminal)
                    terminal.start_server_in_terminal(actual_command, server_terminal)

            self._update_status(f"✅ **Dev servers started. Opening live preview browser...**")
            time.sleep(15) # Give servers a generous amount of time to start up
            browser.navigate_to(f"http://localhost:{playbook['port']}")

    def _parse_plan_to_dict(self, plan_str: str) -> dict:
        """Parses the planner's output into a dictionary of {filename: [components]}."""
        structured_plan = {}
        current_file = None
        for line in plan_str.split('\n'):
            line = line.strip()
            if not line: continue
            # Handle "File: path/to/file.js" and "File: path/to/file.js Components:"
            if line.lower().startswith("file:"):
                current_file = re.sub(r'components:.*', '', line.split(':', 1)[1], flags=re.IGNORECASE).strip().replace('`', '')
                if current_file not in structured_plan:
                    structured_plan[current_file] = []
            elif current_file and (line.startswith('-') or line.startswith('*') or line.strip()[0].isdigit() or "Components:" in line):
                 # Ignore lines that are just "Components:"
                if line.strip().lower() != "components:":
                    # Clean up bullet points
                    component = re.sub(r'^[-\*\d\.]+\s*', '', line).strip()
                    structured_plan[current_file].append(component)
        return structured_plan

    # ======================================================================================
    # == ORCHESTRATOR FOR MODIFYING EXISTING PROJECTS (execute_follow_up)                 ==
    # ======================================================================================

    def execute_follow_up(self, user_prompt: str, workspace_path: str):
        """Re-opens a workspace and intelligently modifies the existing project based on user feedback."""
        self.agent.original_user_prompt = user_prompt
        try:
            self._update_status(f"🚀 **Re-opening Workspace:** `{workspace_path}`")
            terminal.initialize_workspace(
                base_directory=workspace_path,
                output_callback=self.ui.update_terminal_display if self.ui else print
            )

            self._update_status("🧠 **Generating modification plan...**")
            
            try:
                all_files = []
                for root, _, files in os.walk(workspace_path):
                    for name in files:
                        all_files.append(os.path.relpath(os.path.join(root, name), workspace_path))
                file_list_str = "\n".join(all_files)
            except Exception:
                file_list_str = "Could not list files."

            plan_prompt = f"""You are a senior developer. The user has provided feedback on an existing project. Create a concise plan to address their feedback. The plan can have two types of steps:
1. `run_command(command="...")` to run a build step, install a dependency, or other terminal command.
2. `edit_file(file_path="...", task="...")` to modify an existing file. Describe the change that needs to be made.

**User Feedback:** "{user_prompt}"
**Files in Workspace:**
{file_list_str}

Generate the sequence of `run_command` or `edit_file` calls now.
"""
            plan_str = Settings.llm.complete(plan_prompt).text.strip()
            plan_steps = self._extract_tool_calls(plan_str)

            if not plan_steps:
                raise Exception("The modification planner failed to produce any steps.")

            for step in plan_steps:
                parsed_step = self._parse_tool_call(step)
                tool_name = parsed_step.get('name')
                tool_args = parsed_step.get('args')

                if tool_name == "run_command":
                    self._update_status(f"  - **Executing Command:** `{tool_args.get('command')}`")
                    terminal.run_command_in_terminal(**tool_args)
                
                elif tool_name == "edit_file":
                    file_path = tool_args.get('file_path')
                    task = tool_args.get('task')
                    self._update_status(f"  - **Editing File:** `{file_path}` to `{task}`")
                    
                    current_content = file_system.read_file(os.path.join(workspace_path, file_path))
                    
                    edit_prompt = f"""You are an expert programmer. Here is a script. Perform a specific modification and return the new, complete script.
                    
**File to Edit:** `{file_path}`
**Current Content:**
```
{current_content}
```
**Modification Task:**
"{task}"

Respond with ONLY the new, complete code for the file.
"""
                    edited_code = Settings.llm.complete(edit_prompt).text.strip()
                    
                    # Robustness: Clean markdown from edit operations as well
                    if edited_code.startswith("```"):
                        match = re.search(r"```(?:\w+\n)?(.*)```", edited_code, re.DOTALL)
                        if match:
                            edited_code = match.group(1).strip()
                    
                    self.agent.write_file(file_path=file_path, content=edited_code)

            self._update_status("✅ **Modification complete. Please check the result.**")

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR in follow-up:**\n\n{error_details}")
        finally:
            self._update_status("✅ **Orchestration complete. Workspace remains active.**")

    # ======================================================================================
    # == UTILITY METHODS FOR PARSING LLM OUTPUT                                           ==
    # ======================================================================================

    def _parse_tool_call(self, task_string: str) -> dict:
        tool_name_match = re.match(r"(\w+)\(", task_string)
        if not tool_name_match: return {'error': f"Could not parse tool name from: {task_string}"}
        tool_name = tool_name_match.group(1)
        try:
            first_paren_index = task_string.index('(')
            open_paren_count = 1
            last_paren_index = -1
            for i, char in enumerate(task_string[first_paren_index + 1:]):
                if char == '(': open_paren_count += 1
                elif char == ')': open_paren_count -= 1
                if open_paren_count == 0:
                    last_paren_index = first_paren_index + 1 + i
                    break
            if last_paren_index == -1: raise ValueError("Mismatched parentheses")
            args_str = task_string[first_paren_index + 1 : last_paren_index].strip()
        except ValueError as e: return {'error': f"Mismatched parentheses in tool call: {task_string}. Details: {e}"}

        args = {}
        arg_pattern = re.compile(r"(\w+)\s*=\s*(\"\"\"(.*?)\"\"\"|'''(.*?)'''|\"(.*?)\"|'(.*?)')", re.DOTALL)
        for match in arg_pattern.finditer(args_str):
            key = match.group(1)
            value = next((g for g in match.groups()[2:] if g is not None), "")
            args[key] = value
        return {'name': tool_name, 'args': args}

    def _extract_tool_calls(self, plan: str) -> list[str]:
        tool_pattern = r"(run_command|edit_file)\("
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
                self._update_status(f"⚠️ Warning: Could not parse tool call at index {start_index}.")
                cursor = open_paren_index + 1
        return tool_calls