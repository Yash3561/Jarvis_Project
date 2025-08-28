# tools/interaction_tools.py (The Complete User Interaction Toolkit)

import inputimeout
from inputimeout import TimeoutOccurred

# --- TOOL 1: THE "PAUSE BUTTON" ---
def wait_for_user_confirmation(prompt: str = "Execution paused. Press Enter to continue...", timeout: int = 3600) -> str:
    """
    Pauses the agent's execution and waits for the user to press Enter in the
    main application's terminal. This is used to keep long-running processes like GUIs
    or web servers alive for user inspection.
    """
    print(f"\n\n========================================")
    print(f"  PAUSED: WAITING FOR USER")
    print(f"========================================")
    print(f"Reason: {prompt}")
    print(f"----------------------------------------")
    
    try:
        # The core function call from the library
        inputimeout.inputimeout(prompt=">>> Press Enter to continue... ", timeout=timeout)
        return "User confirmed continuation."
    except TimeoutOccurred:
        return f"Timeout of {timeout} seconds occurred. Continuing automatically."

# --- TOOL 2: THE "COLLABORATION TOOL" ---
def ask_user_for_help(question_for_user: str) -> str:
    """
    Pauses execution and asks the user for specific help, guidance, or information.
    The user's typed response will be returned. Use this when you are stuck, an error
    is too complex, or a user's intent is ambiguous.
    """
    print(f"\n\n========================================")
    print(f"  ASSISTANCE REQUIRED: WAITING FOR USER")
    print(f"========================================")
    print(f"Jarvis needs help: {question_for_user}")
    print(f"----------------------------------------")
    response = input("Your response: ")
    print(f"========================================")
    return response