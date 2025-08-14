# agent.py (The FINAL "Unstoppable" V6)

# This file is now a simple, clean interface to all the project's tools.
# The complex logic of routing and planning has been moved to the MainController.

# --- Import ALL the tool functions that the controller will need ---
from tools.file_system import write_to_file
from tools.workspace_tools import create_terminal, run_command
from tools.interaction_tools import wait_for_user_input
from tools.screen_reader import analyse_screen_with_gemini

# --- Import the NEW, UPGRADED browser tools ---
from tools.browser_automation import (
    navigate_and_scan,
    list_current_elements,
    click_element,
    type_into_element,
    get_page_content,
    browser_controller # We need this for cleanup
)

class AIAgent:
    """
    The AIAgent class now acts as a clean 'API layer' for the MainController.
    It holds no state and performs no complex reasoning. Its only job is to
    expose all available tools as simple methods.
    """
    def __init__(self):
        print("INFO: V6 Agent Initializing: Exposing toolset API...")
        # No complex setup is needed here anymore.
        pass

    # --- Pass-through methods for the Main Controller ---
    
    def write_file(self, file_path: str, content: str) -> str:
        return write_to_file(file_path=file_path, content=content)
    
    def create_terminal(self, name: str) -> str:
        return create_terminal(name=name)

    def run_command(self, command: str, terminal_name: str = "default") -> str:
        return run_command(command=command, terminal_name=terminal_name)
    
    def wait_for_user_input(self, prompt: str = "Execution paused.") -> str:
        return wait_for_user_input(prompt=prompt)

    def analyze_entire_screen(self, question_about_screen: str) -> str:
        return analyse_screen_with_gemini(question_about_screen=question_about_screen)

    # --- Pass-through methods for the NEW browser tools ---
    def navigate_and_scan(self, url: str) -> str:
        return navigate_and_scan(url=url)

    def list_current_elements(self) -> str:
        return list_current_elements()

    def click_element(self, uid: str) -> str:
        return click_element(uid=uid)

    def type_into_element(self, uid: str, text: str) -> str:
        return type_into_element(uid=uid, text=text)
        
    def get_page_content(self) -> str:
        return get_page_content()

    # This method is for the controller to call during cleanup.
    def close_browser(self):
        browser_controller.close_browser()