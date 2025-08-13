# tools/desktop_driver.py

import pyautogui
import pyperclip
import time
import platform

def open_terminal_and_run(commands: list[str]):
    """
    Opens the default terminal, types a series of commands, and presses Enter after each.
    This is for direct, visible interaction with the desktop.
    """
    if platform.system() != "Windows":
        return "ERROR: This tool is currently configured for Windows only."

    try:
        # Open the new Windows Terminal
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        pyautogui.write('wt.exe')
        pyautogui.press('enter')
        time.sleep(2) # Wait for terminal to open

        # Type each command
        for command in commands:
            # Using the clipboard is much faster and more reliable than typing
            pyperclip.copy(command)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(1) # Wait between commands
        
        return f"Successfully executed {len(commands)} commands in a new terminal."

    except Exception as e:
        return f"ERROR during desktop automation: {e}"