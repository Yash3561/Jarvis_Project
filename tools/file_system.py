# tools/file_system.py (The Unified File I/O and Image Analysis Tool)

import os
import shutil
from mss import mss
from PIL import Image
import google.generativeai as genai
import config
from .terminal import get_workspace

try:
    # This configuration is needed for the image analysis tool
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini API for file_system tool. Image analysis will fail. Error: {e}")


# --- Core Directory and File Operations ---

def list_files(directory_path: str = ".") -> str:
    """
    Lists all files and subdirectories in a specified directory path.
    If no path is provided, it lists the contents of the current working directory.
    """
    # For safety, ensure we are not trying to list files outside the project root
    # This is a conceptual check; a real implementation would need robust sandboxing.
    if ".." in directory_path:
        return "Error: Access to parent directories is not allowed."
        
    try:
        if not os.path.isdir(directory_path):
            return f"Error: Directory not found at '{directory_path}'"
        
        files = os.listdir(directory_path)
        if not files:
            return f"The directory '{directory_path}' is empty."
        
        return "\n".join(files)
    except Exception as e:
        return f"An error occurred while listing files: {e}"

def read_file(file_path: str) -> str:
    """Reads the entire content of a specified text file and returns it as a string."""
    try:
        if not os.path.exists(file_path):
            return f"Error: The file '{file_path}' was not found."
            
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return f"--- START OF FILE: {os.path.basename(file_path)} ---\n{content}\n--- END OF FILE ---"
    except Exception as e:
        return f"An error occurred while reading the file: {e}"

def write_file(file_path: str, content: str) -> str:
    """Writes content to a file, strictly sandboxed to the active workspace."""
    try:
        workspace = get_workspace()
        # --- SANDBOX ENFORCEMENT ---
        # Create the full path and then resolve it to its absolute, canonical path
        full_path = os.path.join(workspace.base_directory, file_path)
        absolute_path = os.path.abspath(full_path)
        
        # Check if the resolved path is still inside our workspace directory
        if not absolute_path.startswith(os.path.abspath(workspace.base_directory)):
            return f"ERROR: Path '{file_path}' is outside the allowed workspace. Access denied."
            
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {absolute_path}"
    except Exception as e:
        return f"ERROR: Failed to write to file {file_path}. Reason: {e}"

def create_directory(directory_path: str) -> str:
    """Creates a new directory (and any parent directories) at the specified path."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Successfully created directory (or it already existed): {directory_path}"
    except Exception as e:
        return f"An error occurred while creating the directory: {e}"

def delete_file(file_path: str) -> str:
    """Deletes the specified file."""
    try:
        os.remove(file_path)
        return f"Successfully deleted file: {file_path}"
    except FileNotFoundError:
        return f"Error: The file '{file_path}' was not found."
    except Exception as e:
        return f"An error occurred while deleting the file: {e}"


# --- Image File Operations ---

def save_screenshot(file_path: str) -> str:
    """
    Captures a screenshot of the PRIMARY monitor and saves it to the specified file_path.
    The file path should end in .png.
    """
    try:
        if not file_path.lower().endswith('.png'):
            file_path += '.png'
        with mss() as sct:
            screenshot_path = sct.shot(mon=1, output=file_path)
        return f"Successfully saved screenshot of the primary monitor to {screenshot_path}"
    except Exception as e:
        return f"An error occurred while saving the screenshot: {e}"

def analyze_image(file_path: str, prompt: str) -> str:
    """
    Analyzes an image file from a local path and answers a question about it.
    Use this to understand the contents of specific images saved on the disk.
    For example: analyze_image(file_path='path/to/chart.png', prompt='What is the value of the red bar?')
    """
    print(f"INFO: Analyzing local image file: '{file_path}' with prompt: '{prompt}'")

    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist."

    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        img = Image.open(file_path)
        response = model.generate_content([prompt, img])
        
        print("INFO: Gemini image file analysis complete.")
        return response.text
    except Exception as e:
        return f"Error during image analysis: {e}"