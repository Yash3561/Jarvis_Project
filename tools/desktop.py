# tools/desktop.py (The Unified GUI Automation and Vision Tool)

import os
import time
import platform
import pyautogui
import pyperclip
from mss import mss
from PIL import Image
import google.generativeai as genai
import config

# --- Configuration ---
try:
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini API for desktop tool. Vision will fail. Error: {e}")

# --- Core "Eyes": Vision and Screen Analysis Tools ---

def analyze_entire_screen() -> str:
    """
    Captures screenshots of ALL connected monitors, sends them to a vision model for a comprehensive analysis,
    and returns a single, detailed report describing the contents and layout of each monitor.
    Use this to get an overview of what's happening on the computer.
    """
    try:
        print("INFO: Capturing all screens for vision analysis...")
        
        prompt_parts = [
            "You are an expert computer operator. Your task is to analyze the following screenshots from a user's monitors. For each monitor, provide a detailed, separate description under a clear heading (e.g., '--- MONITOR 1 ---'). Describe the active applications, their layout, any key information visible (like text in an editor or a URL in a browser), and what the user is likely doing."
        ]
        
        images = []
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:]): # sct.monitors[0] is the full desktop
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                images.append(img)

        if not images:
            return "Error: No monitors were found to capture."

        for i, img in enumerate(images):
            prompt_parts.extend([f"\n\n--- IMAGE FOR MONITOR {i+1} ---", img])

        print(f"INFO: Sending {len(images)} images to Gemini for analysis...")
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt_parts)
        analysis_text = response.text.strip()
        
        print("INFO: Multi-monitor screen analysis complete.")
        return analysis_text

    except Exception as e:
        print(f"ERROR during vision analysis: {e}")
        return f"An error occurred while analyzing the screen: {e}"

def find_on_screen(description: str) -> str:
    """
    Analyzes the entire screen to find the coordinates of a specific UI element based on a text description.
    For example: 'the blue button that says Submit' or 'the search bar at the top of the window'.
    Returns the coordinates in 'x,y' format if found, otherwise returns an error.
    """
    try:
        print(f"INFO: Visually searching for '{description}' on screen...")
        
        with mss() as sct:
            # Capturing the primary monitor is usually sufficient and faster for finding specific elements.
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        prompt = [
            f"You are a computer vision expert. Analyze this screenshot and find the UI element that best matches the description: '{description}'. Your response MUST be ONLY the pixel coordinates of the CENTER of that element in the format 'x,y'. For example: '845,231'. If you cannot find the element, respond with ONLY the word 'Error'.",
            img
        ]

        model = genai.GenerativeModel('gemini-1.5-pro-latest') # or flash for speed
        response = model.generate_content(prompt)
        
        coords_str = response.text.strip()
        if "error" in coords_str.lower():
            return f"Error: Could not find '{description}' on the screen."
        
        # Validate that the response is in the correct x,y format
        parts = coords_str.split(',')
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            x, y = int(parts[0].strip()), int(parts[1].strip())
            print(f"INFO: Found '{description}' at coordinates: {x},{y}")
            # Add the monitor's offset to the coordinates to get absolute screen position
            abs_x = monitor["left"] + x
            abs_y = monitor["top"] + y
            return f"{abs_x},{abs_y}"
        else:
            return f"Error: Vision model returned an invalid coordinate format: '{coords_str}'"
            
    except Exception as e:
        print(f"ERROR during visual search: {e}")
        return f"An error occurred while trying to find the element: {e}"


# --- Core "Hands": Mouse and Keyboard Control Tools ---

def move_mouse(x: int, y: int) -> str:
    """Moves the mouse cursor to the specified x, y coordinates on the screen."""
    try:
        pyautogui.moveTo(x, y, duration=0.5)
        return f"Mouse moved to {x},{y}."
    except Exception as e:
        return f"Error moving mouse: {e}"

def click(x: int = None, y: int = None, button: str = 'left', clicks: int = 1) -> str:
    """
    Performs a mouse click.
    If x and y are provided, it moves to that position first.
    'button' can be 'left', 'right', or 'middle'.
    'clicks' can be 1 for a single click or 2 for a double click.
    """
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y, duration=0.2)
        
        pyautogui.click(button=button, clicks=clicks)
        return f"Performed a {button} {'double ' if clicks == 2 else ''}click at {pyautogui.position()}."
    except Exception as e:
        return f"Error performing click: {e}"

def type_text(text: str, interval_secs: float = 0.05) -> str:
    """
    Types the given text using the keyboard.
    Using the clipboard is faster and more reliable for long text.
    """
    try:
        # For longer text, using the clipboard is much better
        if len(text) > 10:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(text, interval=interval_secs)
        return f"Typed text: '{text[:50]}...'"
    except Exception as e:
        return f"Error typing text: {e}"

def press_keys(keys: list[str]) -> str:
    """
    Presses a sequence of special keys. For hotkeys, provide them as a list.
    For example: to press Win+R, use `press_keys(keys=['win', 'r'])`.
    """
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey: {'+'.join(keys)}"
    except Exception as e:
        return f"Error pressing keys: {e}"