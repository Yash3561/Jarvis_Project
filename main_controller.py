# main_controller.py (The new "Brain" of Jarvis)

import os
import time
from agent import AIAgent
from llama_index.core import Settings
# ... (your other main imports for settings) ...

class MainController:
    def __init__(self, agent: AIAgent):
        self.agent = agent

    def execute_project(self, user_prompt: str):
        # 1. Create a dedicated workspace for this project
        project_name = "project_" + str(int(time.time()))
        workspace_path = os.path.join(os.getcwd(), project_name)
        os.makedirs(workspace_path, exist_ok=True)
        print(f"--- Workspace created at: {workspace_path} ---")

        # 2. PLAN: The first step is to create a high-level plan.
        planner_prompt = f"""
        You are a high-level planner. Based on the user's request, create a concise, step-by-step plan as a numbered list.
        Each step should be a single, clear action that can be executed by another AI agent.

        User Request: "{user_prompt}"

        The plan is:
        """
        plan = Settings.llm.complete(planner_prompt).text
        with open(os.path.join(workspace_path, "plan.md"), "w") as f:
            f.write(plan)
        print(f"--- Plan Created ---\n{plan}\n--------------------")

        # 3. EXECUTE & REFLECT LOOP
        plan_steps = [line for line in plan.split('\n') if line.strip()]
        for i, step in enumerate(plan_steps):
            print(f"\n--- EXECUTING STEP {i+1}: {step} ---")
            
            # Use our existing agent to execute ONE step.
            # We add context about the workspace.
            execution_prompt = f"""
            Your current task is: "{step}".
            You are working inside the directory: "{workspace_path}".
            All file paths should be relative to this directory.
            Execute this task and provide a detailed report of your actions and the final result.
            """
            # We need to make agent.ask take the workspace path
            raw_result = self.agent.execute_task(execution_prompt, workspace_path) # We'll create this method

            # 4. REFLECT: After each step, a "critic" agent reviews the work.
            reflector_prompt = f"""
            You are a Quality Assurance critic.
            The original plan was: "{plan}"
            The current step was: "{step}"
            The result of the execution was: "{raw_result}"

            Critique this result. Did the step succeed? Is the result correct?
            If it failed, provide a single, corrected step to try next.
            If it succeeded, simply say "SUCCESS".
            """
            critique = Settings.llm.complete(reflector_prompt).text
            print(f"--- CRITIQUE: {critique} ---")

            if "SUCCESS" not in critique.upper():
                print("--- Step failed. Halting project. ---")
                # In a more advanced version, you would retry with the corrected step
                return "Project failed during critique."
        
        return f"Project '{project_name}' completed successfully."

# You would then modify your main.py or ui.py to call this controller
# For a quick test:
if __name__ == '__main__':
    # ... (your code to configure Settings.llm) ...
    agent_instance = AIAgent()
    controller = MainController(agent_instance)
    
    grand_finale_prompt = "..." # Paste the big prompt here
    controller.execute_project(grand_finale_prompt)