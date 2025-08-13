# tools/process_manager.py

import subprocess
import os
import time
from .persistent_terminal import get_terminal

# A dictionary to keep track of running background processes by their PID
RUNNING_PROCESSES = {}

def start_background_process(command: str, working_directory: str, launch_in_new_window: bool = False) -> str:
    """
    Starts a command as a long-running background process,
    intelligently using the active virtual environment if one is set.
    """
    try:
        print(f"INFO: Starting background process in '{working_directory}': {command}")

        # --- THE FINAL FIX ---
        # Get the currently active terminal to see if a venv is set
        active_terminal = get_terminal()
        final_command = command
        
        # Check if the terminal exists AND has an active venv path
        if active_terminal and hasattr(active_terminal, 'active_venv_path') and active_terminal.active_venv_path:
            print(f"INFO: Active venv detected at '{active_terminal.active_venv_path}'")
            scripts_dir = os.path.join(active_terminal.active_venv_path, 'Scripts' if os.name == 'nt' else 'bin')
            cmd_executable = command.split()[0]
            venv_executable_path = os.path.join(scripts_dir, cmd_executable)

            if os.path.exists(venv_executable_path) or os.path.exists(venv_executable_path + '.exe'):
                final_command = f'"{venv_executable_path}" {" ".join(command.split()[1:])}'
                print(f"INFO: Rewrote command to use venv executable: {final_command}")

        if launch_in_new_window and os.name == 'nt':
            full_command_to_run_in_new_window = f'start cmd /k "{final_command}"'
            subprocess.Popen(
                full_command_to_run_in_new_window,
                cwd=working_directory,
                shell=True
            )
            return f"Successfully launched command '{command}' in a new terminal window."
        else:
            # --- EXISTING: Logic for silent background process ---
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.DETACHED_PROCESS

            process = subprocess.Popen(
                command.split(),
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
            )
            pid = process.pid
            RUNNING_PROCESSES[pid] = process
            time.sleep(3)
            if process.poll() is not None:
                 stdout, stderr = process.communicate()
                 return f"ERROR: Process {pid} terminated immediately. Output:\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            return f"Successfully started silent background process with PID: {pid}."

    except Exception as e:
        return f"Error starting background process: {e}"


def check_process_status(pid: int) -> str:
    """
    Checks the status of a background process using its PID.
    Returns any new output from the process.
    """
    pid = int(pid) # Ensure PID is an integer
    if pid not in RUNNING_PROCESSES:
        return f"Error: No process with PID {pid} is being managed."
        
    process = RUNNING_PROCESSES[pid]
    
    # Check if the process has terminated
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        del RUNNING_PROCESSES[pid]
        return f"Process {pid} has terminated. Final Output:\nSTDOUT: {stdout}\nSTDERR: {stderr}"

    # Non-blocking read of stdout
    # In a real system, you'd use select or async IO. This is a simple approximation.
    return f"Process {pid} is still running. (Note: Real-time output check is a complex feature for a future version)."


def stop_background_process(pid: int) -> str:
    """
    Stops a background process using its PID.
    """
    pid = int(pid) # Ensure PID is an integer
    if pid not in RUNNING_PROCESSES:
        return f"Error: No process with PID {pid} is being managed."
        
    process = RUNNING_PROCESSES[pid]
    try:
        process.terminate() # Politely ask it to stop
        process.wait(timeout=5) # Wait for it to stop
        print(f"INFO: Terminated process {pid}.")
    except subprocess.TimeoutExpired:
        process.kill() # Forcefully kill it
        print(f"INFO: Killed process {pid}.")
        
    del RUNNING_PROCESSES[pid]
    return f"Successfully stopped process {pid}."