# tools/script_runner.py (The New, Safe, General-Purpose Executor)

import subprocess
import os
import sys

# Get the path to the python executable in the current virtual environment
python_executable = sys.executable

def run_python_script(file_path: str, working_directory: str = None) -> str:
    """
    Executes a Python script safely.
    It's best to provide the full file_path.
    The working_directory will be the directory from which the script is run.
    """
    try:
        print(f"INFO: Safely executing Python script: {file_path} in CWD: {working_directory}")
        
        # If a full path isn't provided, we can't be sure where it is.
        # The agent should be prompted to provide full paths.
        if not os.path.exists(file_path) and working_directory:
             # Let's try to find it in the working directory
             file_path = os.path.join(working_directory, file_path)
             if not os.path.exists(file_path):
                 return f"Error: The script file '{os.path.basename(file_path)}' was not found in the workspace."

        # A bootstrap script that safely runs the target script.
        # This forces the 'Agg' backend for matplotlib and captures all output.
        bootstrap_code = f"""
import matplotlib
matplotlib.use('Agg')
import runpy
import traceback
import os
try:
    print('--- SCRIPT STDOUT ---')
    # Change CWD before running, so the script can find its own files
    if {working_directory!r}:
        os.chdir({working_directory!r})
    runpy.run_path('{os.path.basename(file_path)}', run_name='__main__')
except Exception as e:
    print('--- SCRIPT STDERR ---')
    traceback.print_exc()
"""
        
        result = subprocess.run(
            [python_executable, "-c", bootstrap_code],
            capture_output=True,
            text=True,
            check=False,
            cwd=working_directory # This is the crucial argument
        )

        output = f"Script '{os.path.basename(file_path)}' finished with exit code {result.returncode}.\n"
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        
        print(f"INFO: Script {os.path.basename(file_path)} finished.")
        return output

    except Exception as e:
        return f"An unexpected error occurred while trying to run the script: {e}"