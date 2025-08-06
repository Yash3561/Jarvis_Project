import pytesseract
from PIL import Image
import os

# --- THIS IS THE NEW, CRUCIAL LINE ---
# Explicitly tell pytesseract where to find the Tesseract-OCR executable.
# The 'r' before the string is important; it tells Python to treat backslashes as literal characters.
pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract-OCR\tesseract.exe'
# ------------------------------------

def read_text_from_image(image_path: str) -> str:
    """
    Reads text from an image file using Tesseract OCR.

    Args:
        image_path: The full path to the image file.

    Returns:
        The extracted text as a string, or an error message if something goes wrong.
    """
    print(f"INFO: OCR tool received path: {image_path}")

    # Check if the file exists before trying to open it
    if not os.path.exists(image_path):
        return f"Error: File not found at the specified path: {image_path}"

    try:
        # Open the image file
        img = Image.open(image_path)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
            return "Info: OCR completed, but no text was found in the image."
            
        print("INFO: OCR successful, text extracted.")
        return text

    except pytesseract.TesseractNotFoundError:
        # This error is now less likely but good to keep for diagnostics
        return "Error: Tesseract is not installed or isn't in your PATH. Please check your Tesseract installation."
    except Exception as e:
        # This will catch other errors, including permissions issues like WinError 740
        print(f"ERROR: An unexpected error occurred during OCR process: {e}")
        return f"Error: An unexpected error occurred during OCR: {e}"