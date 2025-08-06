import os

def write_to_file(file_path: str, content: str) -> str:
    """
    Writes the given content to a file at the specified path.
    If the file already exists, it will be overwritten.

    Args:
        file_path (str): The name or path of the file to be created (e.g., 'my_code.py').
        content (str): The string content to write into the file.

    Returns:
        str: A confirmation message upon success, or an error message.
    """
    try:
        # Determine the full path. If just a filename is given,
        # it will be saved in the project's root directory.
        full_path = os.path.abspath(file_path)
        
        # Get the directory and create it if it doesn't exist
        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        success_message = f"Successfully saved content to '{full_path}'"
        print(f"INFO: {success_message}")
        return success_message

    except Exception as e:
        error_message = f"Error: Failed to write to file '{file_path}'. Reason: {e}"
        print(f"ERROR: {error_message}")
        return error_message