# tools/script_runner.py (The New, Safe, General-Purpose Executor)

import subprocess
import os
import sys

# Get the path to the python executable in the current virtual environment
python_executable = sys.executable

def run_python_script(file_path: str) -> str:
    """
    Executes ANY Python script safely in a separate, non-interactive process.
    This is the ONLY tool that should be used to run .py files.
    It automatically handles matplotlib backends and prevents GUI conflicts.
    It returns the full output (stdout and stderr) of the script.
    """
    try:
        print(f"INFO: Safely executing Python script: {file_path}")
        
        if not os.path.exists(file_path):
            return f"Error: The script file '{file_path}' was not found."

        # A bootstrap script that safely runs the target script.
        # This forces the 'Agg' backend for matplotlib and captures all output.
        bootstrap_code = f"""
import matplotlib
matplotlib.use('Agg')
import runpy
import traceback
try:
    print('--- SCRIPT STDOUT ---')
    runpy.run_path('{file_path}', run_name='__main__')
except Exception as e:
    print('--- SCRIPT STDERR ---')
    traceback.print_exc()
"""
        
        result = subprocess.run(
            [python_executable, "-c", bootstrap_code],
            capture_output=True,
            text=True,
            check=False # We check the return code manually
        )

        output = f"Script '{file_path}' finished with exit code {result.returncode}.\n"
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        
        print(f"INFO: Script {file_path} finished.")
        return output

    except Exception as e:
        return f"An unexpected error occurred while trying to run the script: {e}"