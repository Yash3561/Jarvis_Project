# test_driver.py

import os
import sys
import subprocess
import platform

# --- We are temporarily copying the function here for isolated testing ---
# This is the exact logic from our proposed tools/desktop_driver.py

def launch_gui_app(script_path: str, working_directory: str) -> str:
    """
    Launches a Python GUI application in a NEW, VISIBLE terminal window.
    """
    if platform.system() != "Windows":
        return "ERROR: This GUI launcher is configured for Windows only."

    if not os.path.exists(script_path):
        return f"ERROR: The script path '{script_path}' does not exist."

    try:
        print(f"INFO: Attempting to launch '{script_path}' in a new window...")
        
        python_executable = sys.executable
        
        # --- THE FIX ---
        # We create a command list. This is much safer for handling paths with spaces.
        # The 'start' command will launch the python executable, which will in turn run our script.
        # This avoids complex nested quotes.
        command_list = [
            "cmd", "/c", "start", "Jarvis Test App",
            python_executable,
            script_path
        ]

        # We use Popen with this list. shell=True is no longer needed.
        # The 'cwd' argument ensures the new terminal starts in the correct directory.
        subprocess.Popen(command_list, cwd=working_directory)
        
        return f"Successfully sent launch command for '{os.path.basename(script_path)}'."

    except Exception as e:
        return f"ERROR during GUI launch: {e}"

# --- The Main Test Logic ---
if __name__ == "__main__":
    print("--- Starting Desktop Driver Unit Test ---")
    
    # Define the path to our test subject
    # os.path.abspath ensures we have a full, correct path
    test_script_path = os.path.abspath("test_app.py")
    
    # The working directory is just the current directory
    project_root = os.path.abspath(".")
    
    print(f"Test App Path: {test_script_path}")
    print(f"Working Directory: {project_root}")
    
    # Run the function we are testing
    result = launch_gui_app(script_path=test_script_path, working_directory=project_root)
    
    print(f"\nResult of launch command: {result}")
    
    if "ERROR" in result:
        print("\n--- TEST FAILED ---")
    else:
        print("\n--- TEST SUCCEEDED ---")
        print("Check your desktop for a new terminal and a new window titled 'Jarvis Desktop Driver Test'.")