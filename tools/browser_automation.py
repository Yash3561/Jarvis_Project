# tools/browser_automation.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import webbrowser

class BrowserController:
    def __init__(self):
        self.driver = None

    def start_browser(self):
        if not self.driver:
            print("INFO: Starting new browser instance...")
            try:
                options = webdriver.ChromeOptions()
                # options.add_argument("--headless") # You can uncomment this to run without a visible window
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                # --- ADD THESE LINES TO REDUCE LOGGING NOISE ---
                options.add_argument('--log-level=3') # Suppresses most informational logs
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                # -------------------------------------------------
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("INFO: Browser started successfully.")
            except Exception as e:
                print(f"ERROR: Could not start browser: {e}")
                self.driver = None

    def close_browser(self):
        if self.driver:
            print("INFO: Closing browser instance.")
            self.driver.quit()
            self.driver = None

    def navigate_to_url(self, url: str) -> str:
        """Navigates the browser to the specified URL."""
        if not self.driver:
            self.start_browser()
        
        try:
            print(f"INFO: Navigating to {url}")
            self.driver.get(url)
            return f"Successfully navigated to {url}."
        except Exception as e:
            return f"Error navigating to {url}: {e}"

    def type_into_element(self, selector: str, text: str) -> str:
        """Finds an element by CSS selector and types text into it."""
        if not self.driver:
            return "Error: Browser not started."
        try:
            print(f"INFO: Typing '{text}' into element '{selector}'")
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.send_keys(text)
            return f"Successfully typed '{text}' into element '{selector}'."
        except Exception as e:
            return f"Error typing into element '{selector}': {e}"

    def click_element(self, selector: str) -> str:
        """Finds an element by CSS selector and clicks it."""
        if not self.driver:
            return "Error: Browser not started."
        try:
            print(f"INFO: Clicking element '{selector}'")
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            time.sleep(2) # Wait for page to potentially react/load
            return f"Successfully clicked element '{selector}'."
        except Exception as e:
            return f"Error clicking element '{selector}': {e}"

# --- Global instance of our browser controller ---
# This ensures that all tools share the same browser session.
browser_controller = BrowserController()

# --- Tool functions that the agent will call ---
# These are simple wrappers around our controller's methods.

def navigate(url: str) -> str:
    """Navigates the browser to a URL."""
    return browser_controller.navigate_to_url(url)

def type_text(selector: str, text: str) -> str:
    """Types text into an element identified by a CSS selector."""
    return browser_controller.type_into_element(selector, text)

def click(selector: str) -> str:
    """Clicks an element identified by a CSS selector."""
    return browser_controller.click_element(selector)

# Add this new function to the end of tools/browser_automation.py

def extract_text_from_element(url: str, selector: str) -> str:
    """
    Navigates to a URL and extracts the text content from a single element
    identified by a CSS selector. This is a precision tool for targeted data scraping.
    """
    if not browser_controller.driver:
        # Use a temporary headless driver for this one-shot operation
        print(f"INFO: One-shot extraction from {url} using selector '{selector}'")
        temp_driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            # ... other options
            service = Service(ChromeDriverManager().install())
            temp_driver = webdriver.Chrome(service=service, options=options)
            temp_driver.get(url)
            wait = WebDriverWait(temp_driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            text = element.text
            return f"Extracted text: '{text}'"
        except Exception as e:
            return f"Error extracting text: {e}"
        finally:
            if temp_driver:
                temp_driver.quit()
    else:
        # Use the existing, open browser if available
        print(f"INFO: Extracting text from current page using selector '{selector}'")
        try:
            wait = WebDriverWait(browser_controller.driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            text = element.text
            return f"Extracted text: '{text}'"
        except Exception as e:
            return f"Error extracting text: {e}"
        
def open_url_in_browser(url: str) -> str:
    """Opens the specified URL in the user's default web browser."""
    try:
        webbrowser.open(url, new=2) # new=2 opens in a new tab
        return f"Successfully opened {url} in the browser."
    except Exception as e:
        return f"Error opening URL: {e}"