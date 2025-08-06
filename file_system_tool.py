import os

def list_files_in_directory(directory_path: str, file_type_filter: str = None) -> str:
    """
    Lists files and subdirectories in a given directory path on the local system.
    Can optionally filter the results to show only files of a specific type (e.g., '.png', '.jpg').

    Args:
        directory_path (str): The absolute path to the directory to inspect.
        file_type_filter (str, optional): The file extension to filter by (e.g., '.png'). Defaults to None.

    Returns:
        str: A formatted string listing the contents, or an error message.
    """
    expanded_path = os.path.expanduser(directory_path)

    if not os.path.isdir(expanded_path):
        return f"Error: The path '{expanded_path}' is not a valid directory."
    
    try:
        contents = os.listdir(expanded_path)
        
        if file_type_filter:
            # Filter the list if a file type is specified
            filtered_contents = [item for item in contents if item.lower().endswith(file_type_filter.lower()) and os.path.isfile(os.path.join(expanded_path, item))]
            contents = filtered_contents
            if not contents:
                return f"No files of type '{file_type_filter}' were found in '{expanded_path}'."
        
        if not contents:
            return f"The directory '{expanded_path}' is empty."
        
        result = f"Contents of '{expanded_path}':\n"
        for item in contents:
            result += f"- {item}\n"
        return result
        
    except Exception as e:
        return f"Error listing files in '{expanded_path}': {e}"