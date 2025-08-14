# tools/interaction_tools.py

# Import the library you just installed
import inputimeout
from inputimeout import TimeoutOccurred

def wait_for_user_input(prompt: str = "Execution paused. The application is running in a separate window. Press Enter in this terminal to shut it down and continue.", timeout: int = 3600) -> str:
    """
    Pauses the agent's execution and waits for the user to press Enter in the
    console where the main agent is running. This is used to keep long-running
    processes like GUIs or web servers alive for inspection.
    
    Args:
        prompt (str): The message to display to the user in the terminal.
        timeout (int): The number of seconds to wait before continuing automatically.
                       Defaults to 1 hour (3600 seconds).
    """
    print(f"\n[USER INTERACTION REQUIRED]")
    print(f"=======================================")
    print(prompt)
    print(f"=======================================")
    
    try:
        # This is the core function call from the library
        inputimeout.inputimeout(prompt=">>> Press Enter to continue... ", timeout=timeout)
        return "User confirmed continuation. Proceeding with shutdown."
    except TimeoutOccurred:
        return f"Timeout of {timeout} seconds occurred. Continuing automatically."