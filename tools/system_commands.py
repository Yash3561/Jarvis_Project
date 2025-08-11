# tools/system_commands.py (The Definitive Web-UI Version)

import subprocess
import os
from datetime import datetime
import pytz

# This global variable will hold a direct reference to the UI window instance.
UI_WINDOW_INSTANCE = None

def set_ui_window_instance(window_instance):
    """Stores the main UI window instance so tools can talk to it."""
    global UI_WINDOW_INSTANCE
    UI_WINDOW_INSTANCE = window_instance

# --- All your proven, working time/date tools are preserved ---
def get_current_datetime() -> str:
    """Gets the current LOCAL date and time."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_time_for_location(location: str) -> str:
    """Gets the current time for a specific city or timezone."""
    try:
        target_timezone_str = None
        for tz in pytz.all_timezones:
            if location.lower().replace(" ", "_") in tz.lower():
                target_timezone_str = tz
                break
        if not target_timezone_str: return f"Error: Could not find timezone for '{location}'."
        target_timezone = pytz.timezone(target_timezone_str)
        now_in_timezone = datetime.now(target_timezone)
        return now_in_timezone.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        return f"Error getting time for {location}: {e}"

def get_timestamp() -> str:
    """Returns a clean, file-safe timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# --- The updated shell command tool ---
def run_shell_command(command: str) -> str:
    """Executes a shell command and streams its output to the UI terminal."""
    if not UI_WINDOW_INSTANCE:
        return "ERROR: UI instance not set. Cannot stream output."

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Directly call the UI's method to update the terminal via the JS bridge
    UI_WINDOW_INSTANCE.update_terminal_display(f"$ {command}")
    
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=project_root, bufsize=1, universal_newlines=True
        )
        for line in process.stdout:
            UI_WINDOW_INSTANCE.update_terminal_display(line.strip())
        for line in process.stderr:
            UI_WINDOW_INSTANCE.update_terminal_display(f"ERROR: {line.strip()}")
        process.wait()
        if process.returncode == 0:
            return f"Command '{command}' executed successfully."
        else:
            return f"ERROR: Command '{command}' failed with exit code {process.returncode}."
            
    except Exception as e:
        error_message = f"ERROR: Failed to execute command '{command}'. Exception: {e}"
        UI_WINDOW_INSTANCE.update_terminal_display(error_message)
        return error_message