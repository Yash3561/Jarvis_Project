# tools/file_system.py (Corrected and Expanded)

import os

def list_files_in_directory(directory_path: str = ".") -> str:
    """
    Lists all files and directories in a specified directory path.
    The default path is the current working directory where the project is running.
    """
    try:
        if not os.path.isdir(directory_path):
            return f"Error: Directory not found at '{directory_path}'"
        
        files = os.listdir(directory_path)
        if not files:
            return f"The directory '{directory_path}' is empty."
        
        return "\n".join(files)
    except Exception as e:
        return f"An error occurred while listing files: {e}"

def write_to_file(file_path: str, content: str) -> str:
    """
    Writes the given content to a specified file.
    This will create the file if it doesn't exist, and overwrite it if it does.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote content to {file_path}"
    except Exception as e:
        return f"An error occurred while writing to file: {e}"

# --- THIS IS THE NEW TOOL ---
def read_file_content(file_path: str) -> str:
    """
    Reads the entire content of a specified text file and returns it as a string.
    Requires the full path to the file.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: The file '{file_path}' was not found."
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"--- START OF FILE: {os.path.basename(file_path)} ---\n{content}\n--- END OF FILE ---"
    except Exception as e:
        return f"An error occurred while reading the file: {e}"
    

def create_directory(directory_path: str) -> str:
    """
    Creates a new directory at the specified path.
    Use this when you need to create a folder to store files in.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Successfully created directory (or it already existed): {directory_path}"
    except Exception as e:
        return f"An error occurred while creating the directory: {e}"