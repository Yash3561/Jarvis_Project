# tools/screen_reader.py (Upgraded for Multi-Monitor Gemini Vision)

import os
from mss import mss
from PIL import Image
import google.generativeai as genai

try:
    import config
    genai.configure(api_key=config.Settings.gemini_api_key)
except (ImportError, AttributeError, ValueError) as e:
    print(f"CRITICAL WARNING: Could not configure Gemini API. Vision tool will fail. Error: {e}")

def analyse_screen_with_gemini() -> str:
    """
    Captures screenshots of ALL connected monitors, sends them to the Gemini model for analysis,
    and returns a single, structured report describing each monitor separately.
    """
    try:
        print("INFO: Capturing all screens for Gemini Vision analysis...")
        
        # This will hold the parts of our multi-modal prompt
        prompt_parts = [
            "You are an expert screen analyst. Analyze the following series of screenshots, which represent different monitors on a user's system. For each monitor, provide a detailed, separate description under a clear heading (e.g., '--- MONITOR 1 ANALYSIS ---'). Describe the active applications, their layout, any key information visible, and what the user is likely doing on that specific screen."
        ]
        
        images_captured = []
        with mss() as sct:
            # Loop through all monitors, starting from monitor 1
            for i, monitor in enumerate(sct.monitors[1:]):
                monitor_number = i + 1
                print(f"INFO: Capturing Monitor {monitor_number}...")
                
                # Grab data from the current monitor
                sct_img = sct.grab(monitor)
                # Create a Pillow Image object
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                images_captured.append(img)

        if not images_captured:
            return "Error: No monitors were found to capture."

        # Add the images to the prompt parts
        for i, img in enumerate(images_captured):
            monitor_number = i + 1
            prompt_parts.append(f"\n\n--- IMAGE FOR MONITOR {monitor_number} ---")
            prompt_parts.append(img)

        print(f"INFO: Sending {len(images_captured)} images to Gemini for analysis...")
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt_parts)
        
        analysis_text = response.text
        print("INFO: Gemini multi-monitor analysis complete.")
        return analysis_text

    except Exception as e:
        print(f"ERROR during Gemini Vision analysis: {e}")
        return f"An error occurred while analyzing the screen with the vision model: {e}"

# This tool remains single-monitor for simplicity, as per its description.
def save_screenshot_to_file(file_path: str) -> str:
    """
    Captures a screenshot of the PRIMARY monitor and saves it to the specified file_path.
    """
    try:
        if not file_path.lower().endswith('.png'):
            file_path += '.png'
        with mss() as sct:
            screenshot_path = sct.shot(mon=1, output=file_path)
        return f"Successfully saved screenshot of the primary monitor to {screenshot_path}"
    except Exception as e:
        return f"An error occurred while saving the screenshot: {e}"
    
def analyze_image_file(file_path: str, user_prompt: str) -> str:
    """
    Analyzes a single image file from a given path and answers a question about it.
    Use this to look at and understand specific images on the local disk.
    For example: analyze_image_file(file_path='path/to/image.png', user_prompt='What is in this image?')
    """
    print(f"INFO: Analyzing local image file: '{file_path}' with prompt: '{user_prompt}'")

    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist."

    try:
        # Configure the Gemini API client
        genai.configure(api_key=config.Settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')

        # Open the image and prepare it for the API
        img = Image.open(file_path)
        
        # Prepare the prompt for Gemini
        response = model.generate_content([user_prompt, img])
        
        print("INFO: Gemini image file analysis complete.")
        return response.text

    except Exception as e:
        print(f"ERROR: Failed to analyze image file '{file_path}'. Exception: {e}")
        return f"Error during image analysis: {e}"