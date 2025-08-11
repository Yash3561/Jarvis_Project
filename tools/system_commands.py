# tools/system_commands.py (The Definitive, Hybrid, Safe & Streaming Version)

import subprocess
import os
from datetime import datetime
import pytz
import threading

# This global variable will hold a direct reference to the UI window instance.
UI_WINDOW_INSTANCE = None

def set_ui_window_instance(window_instance):
    """Stores the main UI window instance so tools can talk to it."""
    global UI_WINDOW_INSTANCE
    UI_WINDOW_INSTANCE = window_instance

# --- TIME/DATE TOOLS (UNCHANGED) ---
def get_current_datetime() -> str:
    """Gets the current LOCAL date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_time_for_location(location: str) -> str:
    """Gets the current time for a specific city or timezone."""
    # ... (your existing code for this is fine)
    try:
        target_timezone_str = next((tz for tz in pytz.all_timezones if location.lower().replace(" ", "_") in tz.lower()), None)
        if not target_timezone_str: return f"Error: Could not find timezone for '{location}'."
        target_timezone = pytz.timezone(target_timezone_str)
        now_in_timezone = datetime.now(target_timezone)
        return now_in_timezone.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        return f"Error getting time for {location}: {e}"

def get_timestamp() -> str:
    """Returns a clean, file-safe timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# --- THE ULTIMATE SHELL COMMAND TOOL ---
def run_shell_command(command: str) -> str:
    """
    Executes a shell command safely, streams its output live to the UI terminal,
    and returns a final summary. This is the definitive, safe version.
    """
    print(f"INFO: Streaming shell command: '{command}'")

    # --- SAFETY NET: Block dangerous interactive or conflicting commands ---
    forbidden_commands = ["cmd", "powershell", "bash", "sh", "zsh", "python"]
    command_start = command.strip().lower().split()[0]
    if command_start in forbidden_commands:
        error_msg = f"ERROR: Interactive shell '{command_start}' is forbidden. Use the correct dedicated tool."
        if UI_WINDOW_INSTANCE:
            UI_WINDOW_INSTANCE.update_terminal_display(error_msg)
        return error_msg

    full_output = []
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=os.getcwd(), bufsize=1, universal_newlines=True,
            encoding='utf-8', errors='replace'
        )
        
        # We need to read stdout and stderr in separate threads to avoid deadlocks
        def stream_reader(pipe, output_list, is_stderr=False):
            prefix = "ERROR: " if is_stderr else ""
            for line in pipe:
                line_content = line.strip()
                output_list.append(line_content)
                if UI_WINDOW_INSTANCE:
                    UI_WINDOW_INSTANCE.update_terminal_display(f"{prefix}{line_content}")
        
        stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, full_output, False))
        stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, full_output, True))
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for the process to complete, with a generous timeout
        process.wait(timeout=300) # 5-minute timeout for long installs

        # Wait for the reader threads to finish
        stdout_thread.join()
        stderr_thread.join()
        
        if process.returncode == 0:
            summary = f"Command '{command}' executed successfully."
            if UI_WINDOW_INSTANCE:
                UI_WINDOW_INSTANCE.update_terminal_display(f"\nSUCCESS: {summary}")
            return summary
        else:
            summary = f"ERROR: Command '{command}' failed with exit code {process.returncode}."
            if UI_WINDOW_INSTANCE:
                UI_WINDOW_INSTANCE.update_terminal_display(f"\nFAILURE: {summary}")
            return f"{summary}\nFULL LOG:\n{' '.join(full_output)}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        return f"ERROR: Command timed out after 300 seconds and was terminated."
    except Exception as e:
        return f"ERROR: An unexpected exception occurred: {e}"