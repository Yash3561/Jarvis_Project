# tools/system_commands.py (Upgraded with Location-Aware Time)

import subprocess
import os
from datetime import datetime
import pytz  # <--- Import the new library

# This global callback system is correct and does not need changes
UI_UPDATE_CALLBACK = None
def set_ui_update_callback(callback):
    global UI_UPDATE_CALLBACK
    UI_UPDATE_CALLBACK = callback

def get_current_datetime() -> str:
    """
    Gets the current LOCAL date and time for the system where the code is running.
    Use this only when the user does not specify a location.
    """
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"INFO: get_current_datetime tool called. Returning local time: {formatted_time}")
    return formatted_time

# --- THIS IS THE NEW, LOCATION-AWARE TOOL ---
def get_time_for_location(location: str) -> str:
    """
    Gets the current time for a specific city or timezone (e.g., 'Tokyo', 'Paris', 'America/New_York').
    Use this when the user asks for the time in a particular place.
    """
    try:
        print(f"INFO: get_time_for_location tool called for: {location}")
        # Find the full timezone name from a partial location string
        target_timezone_str = None
        for tz in pytz.all_timezones:
            if location.lower().replace(" ", "_") in tz.lower():
                target_timezone_str = tz
                break

        if not target_timezone_str:
            return f"Error: Could not find a valid timezone for the location '{location}'."

        target_timezone = pytz.timezone(target_timezone_str)
        now_in_timezone = datetime.now(target_timezone)
        formatted_time = now_in_timezone.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        
        return f"The current time in {target_timezone_str} is {formatted_time}."

    except Exception as e:
        return f"An error occurred while getting the time for {location}: {e}"

# The shell command tool is still essential and does not need changes
def run_shell_command(command: str) -> str:
    """
    Executes a shell command and streams its output in real-time.
    """
    if not UI_UPDATE_CALLBACK:
        return "ERROR: UI callback not set. Cannot stream output."

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    UI_UPDATE_CALLBACK(f"$ {command}\n")
    
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=project_root, bufsize=1, universal_newlines=True
        )
        # ... rest of the function is correct ...
        full_stdout = ""
        for line in process.stdout:
            UI_UPDATE_CALLBACK(line)
            full_stdout += line
        
        process.wait()

        if process.returncode == 0:
            return f"Command '{command}' executed successfully."
        else:
            stderr_output = process.stderr.read()
            UI_UPDATE_CALLBACK(f"ERROR:\n{stderr_output}")
            return f"ERROR: Command '{command}' failed with exit code {process.returncode}.\nSTDERR:\n{stderr_output}"
            
    except Exception as e:
        error_message = f"ERROR: Failed to execute command '{command}'. Exception: {e}"
        UI_UPDATE_CALLBACK(error_message)
        return error_message