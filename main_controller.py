# main_controller.py (The FINAL, "Unstoppable" V6)

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
            self.ui.response_received.emit(f"<SPOKEN_SUMMARY> </SPOKEN_SUMMARY><FULL_RESPONSE>{message}</FULL_RESPONSE>")

    def _parse_and_execute_step(self, tool_call_string: str) -> str:
        """Parses a tool call and executes it using the agent's methods."""
        # This is a simplified but effective parser for the new agent's output.
        tool_name_match = re.match(r"(\w+)\(", tool_call_string)
        if not tool_name_match:
            return f"ERROR: Could not parse tool name from call: {tool_call_string}"
        tool_name = tool_name_match.group(1)

        args = {}
        arg_pattern = re.compile(r"(\w+)=['\"](.*?)['\"]")
        for match in arg_pattern.finditer(tool_call_string):
            args[match.group(1)] = match.group(2)
        
        # --- THE NEWLINE FIX IS PERMANENTLY HERE ---
        if tool_name == "write_to_file" and 'content' in args:
            args['content'] = args['content'].replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")

        # Map tool names to the actual methods in the AIAgent class
        tool_map = {
            "navigate_and_scan": self.agent.navigate_and_scan,
            "list_current_elements": self.agent.list_current_elements,
            "click_element": self.agent.click_element,
            "type_into_element": self.agent.type_into_element,
            "get_page_content": self.agent.get_page_content,
            "write_to_file": self.agent.write_file,
            "run_command": self.agent.run_command,
            "finish_project": lambda: "PROJECT_FINISHED"
        }

        if tool_name not in tool_map:
            return f"ERROR: Unknown tool '{tool_name}' was called."

        try:
            # Special case for finish_project which has no arguments
            if tool_name == "finish_project":
                return tool_map[tool_name]()
            else:
                return tool_map[tool_name](**args)
        except Exception as e:
            return f"ERROR: Executing tool '{tool_name}' failed. Reason: {e}"

    def execute_project(self, user_prompt: str):
        project_name_base = re.sub(r'\W+', '_', user_prompt.lower())[:40]
        project_timestamp = str(int(time.time()))
        project_name = f"{project_name_base}_{project_timestamp}"
        workspace_path = os.path.join(os.getcwd(), 'workspaces', project_name)
        
        initialize_workspace(
            base_directory=workspace_path,
            output_callback=self.ui.update_terminal_display if self.ui else print
        )
        self._update_status(f"🚀 **Workspace Initialized:** `{workspace_path}`")
        
        project_successful = False
        try:
            project_successful = self._execute_agentic_loop(user_prompt)
            if project_successful:
                self._update_status(f"✅ **Project Completed Successfully.**")
            else:
                self._update_status(f"⏹️ **Project Aborted.** The agent did not finish the goal.")

        except Exception as e:
            error_details = traceback.format_exc()
            self._update_status(f"💥 **FATAL ERROR:** An unexpected error occurred.\n\n{error_details}")
        
        finally:
            self._update_status("🧹 **Closing workspace and all terminals...**")
            self.agent.close_browser()
            close_workspace()


    def _execute_agentic_loop(self, user_prompt: str) -> bool:
        """The main 'Reason-Act' loop that powers the unstoppable agent."""
        operation_history = [f"User's Goal: {user_prompt}"]
        max_turns = 25

        for i in range(max_turns):
            self._update_status(f"--- Thinking Cycle {i+1}/{max_turns} ---") # "Thinking Cycle"

            # This is the new brain of the operation.
            next_step_prompt = f"""
You are Jarvis, a world-class autonomous web agent. You operate in a loop: Observe, Reason, Act.
Your goal is to accomplish the user's objective by figuring out the single best next action.

## User's Ultimate Goal ##
{user_prompt}

## Operation History (What You Have Done and Seen) ##
{chr(10).join(operation_history)}

## Your Task ##
Based on the goal and the history, determine the single best tool to call NEXT.

## Guiding Principles ##
1.  **Start with Navigation:** Your first step is almost always `navigate_and_scan(url=...)`.
2.  **Scan, then Act:** After navigating or clicking, your next step should be `list_current_elements()` to see what is on the new page.
3.  **Reason from Observations:** Look at the list of elements from your last observation. Find the `uid` of the element that matches your goal (e.g., a link with the text 'Next Page').
4.  **Extract Data:** If you need to scrape data, use `get_page_content()`, then analyze the text in your next thought cycle to construct a `write_to_file` call with the extracted data.
5.  **Finish:** When the user's goal is fully accomplished, you MUST call `finish_project()`.

## AVAILABLE TOOLS ##
`navigate_and_scan(url="...")`
`list_current_elements()`
`click_element(uid="element_...")`
`type_into_element(uid="element_...", text="...")`
`get_page_content()`
`write_to_file(file_path="...", content="...")`
`run_command(command="...")`
`finish_project()`

Your single next action is:
"""
            self._update_status("🧠 **Jarvis is thinking...**")
            next_step = Settings.llm.complete(next_step_prompt).text.strip()
            
            # --- THE FINAL MARKDOWN CLEANING FIX ---
            # This now handles both triple and single backticks, making it truly robust.
            if "```" in next_step:
                match = re.search(r"```(?:\w+\n)?(.*?)\n?```", next_step, re.DOTALL)
                if match: next_step = match.group(1).strip()
            elif next_step.startswith("`") and next_step.endswith("`"):
                next_step = next_step[1:-1]
            # --- END OF FIX ---
            
            self._update_status(f"▶️ **Action:** `{next_step}`")
            operation_history.append(f"Action: {next_step}")
            
            result = self._parse_and_execute_step(next_step)
            
            if result == "PROJECT_FINISHED":
                self._update_status("🏁 **Jarvis has finished the project.**")
                return True

            observation = result if len(result) < 2000 else result[:2000] + "\n... (truncated)"
            self._update_status(f"👀 **Observation:** `{observation}`")
            operation_history.append(f"Observation: {observation}")
        
        return False # Max turns reached