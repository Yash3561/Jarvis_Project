# tools/system_commands.py (Streaming Version)
import subprocess
import os
import threading

# A global variable to hold a reference to the UI instance
# This is a simple way to give tools access to the UI's signals.
# A more advanced architecture might use a dedicated event bus.
UI_UPDATE_CALLBACK = None

def set_ui_update_callback(callback):
    global UI_UPDATE_CALLBACK
    UI_UPDATE_CALLBACK = callback

def run_shell_command(command: str) -> str:
    """
    Executes a shell command and streams its output in real-time.
    Returns the final status and a summary of the output.
    """
    if not UI_UPDATE_CALLBACK:
        return "ERROR: UI callback not set. Cannot stream output."

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    UI_UPDATE_CALLBACK(f"$ {command}\n") # Show the command being run
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root,
            bufsize=1, # Line-buffered
            universal_newlines=True
        )

        full_stdout = ""
        full_stderr = ""

        # Read output line by line in real-time
        for line in process.stdout:
            UI_UPDATE_CALLBACK(line)
            full_stdout += line
        for line in process.stderr:
            UI_UPDATE_CALLBACK(f"ERROR: {line}")
            full_stderr += line
            
        process.wait() # Wait for the process to complete

        if process.returncode == 0:
            final_status = f"Command '{command}' executed successfully."
            return final_status
        else:
            final_status = f"ERROR: Command '{command}' failed with exit code {process.returncode}."
            return f"{final_status}\nSTDERR:\n{full_stderr}"
            
    except Exception as e:
        error_message = f"ERROR: Failed to execute command '{command}'. Exception: {e}"
        UI_UPDATE_CALLBACK(error_message)
        return error_message