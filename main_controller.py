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
            # --- UPDATED THE PROMPT TO INCLUDE THE NEW TOOLS ---
            planner_prompt = f"""
You are "Jarvis," a world-class autonomous software engineer. Your task is to generate a complete, step-by-step plan.

## CRITICAL DIRECTIVES ##
1.  **THE PLAN MUST BE STATIC:** You cannot use loops (like 'for i in range...'), variables, or f-strings in your plan. If you need to perform an action five times, you must write out the tool call five separate times with the numbers 1, 2, 3, 4, 5 hardcoded.
2.  **USE THE RIGHT TOOL:** For web scraping, **always** prefer using the `navigate` and `extract_text_from_element` tools. Do not write a custom Python script with `requests`.
3.  **VENV IS MANDATORY:** For any project that DOES require custom Python scripts, you must create and use a venv.
4.  **VERIFY WORK:** Use commands like `dir` or `ls -R` to check your work.
5.  **GUI/SERVER APPS:** For long-running apps, use `wait_for_user_input()` as the final step.

## EXAMPLE OF A CORRECT, STATIC PLAN ##
# To get the top 3 items from a list on a webpage:
navigate(url="https://example.com")
extract_text_from_element(selector="li:nth-child(1)")
extract_text_from_element(selector="li:nth-child(2)")
extract_text_from_element(selector="li:nth-child(3)")

## AVAILABLE TOOLS ##
`run_command(command="your-shell-command-here")`
`write_to_file(file_path="file.py", content='...')`
`navigate(url="https://example.com")`
`extract_text_from_element(selector="css.selector.here")`
`wait_for_user_input(prompt="...")`

## User Request ##
"{user_prompt}"

Generate the complete, static, step-by-step plan now.
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
        FULLY-AGENTIC EXECUTION LOOP WITH SELF-CORRECTION (V4).
        This version has a more robust correction parser and a more directive
        prompt to guide the agent towards better tool usage (e.g., Selenium over requests).
        """
        self._update_status("⚙️ **Parsing execution plan...**")
        matches = self._extract_tool_calls(plan)
        
        if not matches:
            self._update_status(f"❌ **CRITICAL PARSING ERROR:** No tool calls found in the plan.")
            raise ValueError("No executable steps found in the generated plan.")

        step_counter = 1
        # Use a while loop because the 'matches' list can now be modified during execution
        while step_counter <= len(matches):
            task_string = matches[step_counter - 1]
            self._update_status(f"▶️ **Executing Step {step_counter}/{len(matches)}:** {task_string.split('(')[0]}")

            max_retries = 3
            for attempt in range(max_retries):
                parsed_tool = self._parse_tool_call(task_string)
                if parsed_tool.get('error'):
                    self._update_status(f"❌ **CRITICAL PARSING ERROR on Step {step_counter}:** {parsed_tool['error']}")
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
                    elif tool_name == "wait_for_user_input":
                        raw_result = self.agent.wait_for_user_input(**tool_args)
                    elif tool_name == "navigate":
                        raw_result = self.agent.navigate(**tool_args)
                    elif tool_name == "extract_text_from_element":
                        raw_result = self.agent.extract_text_from_element(**tool_args)
                    elif tool_name == "analyze_entire_screen":
                        raw_result = self.agent.analyze_entire_screen(**tool_args)
                    else:
                        raise ValueError(f"Unknown tool '{tool_name}' requested.")
                    
                    if raw_result and ("ERROR" in str(raw_result).upper() or "TRACEBACK" in str(raw_result).upper()):
                        raise Exception(raw_result)
                    
                    self._update_status(f"✔️ **Step {step_counter} Succeeded!**")
                    break

                except Exception as e:
                    error_output = str(e)
                    self._update_status(f"⚠️ **EXECUTION FAILED on Step {step_counter}, Attempt {attempt + 1}/{max_retries}.**")

                    if attempt + 1 >= max_retries:
                        self._update_status(f"❌ **CRITICAL FAILURE:** Max retries reached for this step. Aborting project.")
                        raise

                    self._update_status("🧠 **Agent is attempting to self-correct...**")
                    
                    correction_prompt = f"""
You are a debugging AI assistant. Your previous step failed. You are stuck in a loop. You must try a different strategy.

## Original Failed Task ##
`{task_string}`

## Full Error Output ##
```
{error_output}
```

## ANALYSIS & THE NUCLEAR OPTION ##
Your plan is failing repeatedly because your CSS selector is wrong. Guessing a new selector is not working.

**YOUR NEW STRATEGY IS THE NUCLEAR OPTION:**
You must use your `analyze_entire_screen` tool to LOOK at the webpage and figure out the correct CSS selectors. This tool will describe the visual layout of the screen, allowing you to build a correct plan.

## AVAILABLE VISION TOOL ##
`analyze_entire_screen(question_about_screen="...")`

## YOUR NEW PLAN ##
Your new plan MUST consist of a SINGLE step: a call to `analyze_entire_screen`. Your question should be something like: "What are the correct CSS selectors for the names of the top 5 trending repositories on this page?"

## REQUIRED OUTPUT FORMAT ##
Place the single `analyze_entire_screen` tool call inside `<CORRECTED_PLAN>` tags.

<CORRECTED_PLAN>
</CORRECTED_PLAN>
"""
                    
                    correction_response = Settings.llm.complete(correction_prompt).text
                    
                    new_steps = []
                    plan_match = re.search(r"<CORRECTED_PLAN>(.*?)</CORRECTED_PLAN>", correction_response, re.DOTALL)
                    
                    if plan_match:
                        plan_text = plan_match.group(1).strip()
                        new_steps = [step.strip() for step in plan_text.split('\n') if step.strip()]

                    if not new_steps:
                        self._update_status(f"❌ **CORRECTION FAILED:** Agent did not provide a valid corrective plan. Retrying...")
                        continue

                    self._update_status(f"💡 **Agent's New Multi-Step Corrective Plan:**")
                    for step in new_steps:
                        self._update_status(f"  - {step}")

                    matches[step_counter - 1 : step_counter] = new_steps
                    # The plan has changed, so we need to break the retry loop and let the main loop continue
                    # from the newly inserted steps.
                    break 
            
            step_counter += 1