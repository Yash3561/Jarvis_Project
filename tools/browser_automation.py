# tools/browser_automation.py (The new "Smart Hands" V5)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class BrowserController:
    def __init__(self):
        self.driver = None
        self.current_page_elements = []

    def start_browser(self):
        if not self.driver:
            print("INFO: Starting new browser instance...")
            try:
                options = webdriver.ChromeOptions()
                # options.add_argument("--headless")
                options.add_argument('--log-level=3')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
            self.current_page_elements = []

    def _scan_page_for_elements(self):
        if not self.driver: return
        print("INFO: Scanning page for interactable elements...")
        self.current_page_elements = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, input[type='text'], input[type='submit'], textarea, [role='button'], [role='link']")
        for i, element in enumerate(elements):
            try:
                text = element.text.strip()
                aria_label = element.get_attribute("aria-label") or ""
                # Prioritize visible text, fall back to aria-label
                visible_text = text if text else aria_label
                if not visible_text: continue # Skip elements with no discernible text

                uid = f"element_{i}"
                # Inject a unique ID directly into the DOM for later access
                self.driver.execute_script(f"arguments[0].setAttribute('data-jarvis-id', '{uid}');", element)
                self.current_page_elements.append({ "uid": uid, "text": visible_text[:150] })
            except Exception:
                continue

# --- V5 Tool Functions: The New High-Level API for the Agent ---

browser_controller = BrowserController()

def navigate_and_scan(url: str) -> str:
    """
    Navigates to a URL and scans the page for interactable elements, returning a summary.
    This should be the first step for any web task.
    """
    if not browser_controller.driver: browser_controller.start_browser()
    try:
        browser_controller.driver.get(url)
        time.sleep(2) # Wait for JS to load
        browser_controller._scan_page_for_elements()
        summary = f"Navigated to {url}. Found {len(browser_controller.current_page_elements)} interactable elements. Use `list_current_elements()` to see them."
        return summary
    except Exception as e:
        return f"ERROR: Failed to navigate to {url}. Reason: {e}"

def list_current_elements() -> str:
    """
    Lists all interactable elements found on the current page.
    """
    if not browser_controller.current_page_elements:
        return "No elements found. Use `navigate_and_scan(url=...)` first."
    return "Found elements:\n" + "\n".join([str(e) for e in browser_controller.current_page_elements])

def click_element(uid: str) -> str:
    """
    Clicks an element identified by its unique ID (uid).
    Always run `list_current_elements` first to get the correct uid.
    """
    if not browser_controller.driver: return "ERROR: Browser not started."
    try:
        element = browser_controller.driver.find_element(By.CSS_SELECTOR, f"[data-jarvis-id='{uid}']")
        element.click()
        time.sleep(2) # Wait for page to react
        browser_controller._scan_page_for_elements() # Re-scan after click
        return f"Clicked element {uid}. Page re-scanned. Found {len(browser_controller.current_page_elements)} new elements."
    except Exception as e:
        return f"ERROR: Could not click element {uid}. Is it still on the page? Reason: {e}"

def type_into_element(uid: str, text: str) -> str:
    """
    Types text into an input element identified by its unique ID (uid).
    Always run `list_current_elements` first to get the correct uid.
    """
    if not browser_controller.driver: return "ERROR: Browser not started."
    try:
        element = browser_controller.driver.find_element(By.CSS_SELECTOR, f"[data-jarvis-id='{uid}']")
        element.clear()
        element.send_keys(text)
        return f"Typed '{text}' into element {uid}."
    except Exception as e:
        return f"ERROR: Could not type into element {uid}. Is it an input field? Reason: {e}"

def get_page_content() -> str:
    """
    Returns the full text content of the current webpage.
    """
    if not browser_controller.driver: return "ERROR: Browser not started."
    try:
        return browser_controller.driver.find_element(By.TAG_NAME, 'body').text
    except Exception as e:
        return f"ERROR: Could not get page content. Reason: {e}"