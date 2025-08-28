# tools/browser.py (The Unified Web Interaction Tool)

import os
import time
import webbrowser
import google.generativeai as genai
from tavily import TavilyClient
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import config

# --- Configuration ---
try:
    # Configure Gemini for the summarization task
    genai.configure(api_key=config.Settings.gemini_api_key)
    # Configure Tavily for web search
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure AI services for the browser tool. It will fail. Error: {e}")
    tavily_client = None


# --- Core Browser Controller Class ---
# This class manages a single, persistent Selenium browser instance.
class Browser:
    """Manages a stateful, single browser instance for automation tasks."""
    def __init__(self):
        self.driver = None

    def _start_if_needed(self):
        """Starts the Selenium browser instance if it's not already running."""
        if self.driver is None:
            print("INFO: Starting new browser instance for automation...")
            try:
                options = webdriver.ChromeOptions()
                # options.add_argument("--headless") # Uncomment for non-visible browsing
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument('--log-level=3') # Suppress most informational logs
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("INFO: Browser started successfully.")
            except Exception as e:
                print(f"ERROR: Could not start browser: {e}")
                self.driver = None
    
    def navigate(self, url: str) -> str:
        """Navigates the managed browser to the specified URL."""
        self._start_if_needed()
        if not self.driver: return "Error: Browser is not available."
        
        try:
            print(f"INFO: Navigating to {url}")
            self.driver.get(url)
            return f"Successfully navigated to {url}."
        except Exception as e:
            return f"Error navigating to {url}: {e}"

    def type(self, selector: str, text: str) -> str:
        """Finds an element by CSS selector and types text into it."""
        if not self.driver: return "Error: Browser not started."
        try:
            print(f"INFO: Typing '{text}' into element '{selector}'")
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.clear() # Clear the field before typing
            element.send_keys(text)
            return f"Successfully typed into element '{selector}'."
        except Exception as e:
            return f"Error typing into element '{selector}': {e}"

    def click(self, selector: str) -> str:
        """Finds an element by CSS selector and clicks it."""
        if not self.driver: return "Error: Browser not started."
        try:
            print(f"INFO: Clicking element '{selector}'")
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            time.sleep(2) # Wait for page to potentially react/load
            return f"Successfully clicked element '{selector}'."
        except Exception as e:
            return f"Error clicking element '{selector}': {e}"

    def read_element(self, selector: str) -> str:
        """Extracts the text content from an element identified by a CSS selector."""
        if not self.driver or not self.driver.current_url:
            return "Error: Browser is not on a page. Please use `navigate` first."
        
        print(f"INFO: Reading text from element '{selector}'")
        try:
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            text = element.text
            return f"Extracted text: '{text}'"
        except Exception as e:
            return f"ERROR: Could not find or extract text from element with selector '{selector}'. Error: {e}"

    def close(self):
        """Closes the managed browser instance."""
        if self.driver:
            print("INFO: Closing browser instance.")
            self.driver.quit()
            self.driver = None

# --- Global Browser Singleton ---
# This ensures all tool calls share the same browser session.
_BROWSER_INSTANCE = Browser()


# --- High-Level Tool Functions for the Agent ---

def open_url(url: str) -> str:
    """
    Opens the specified URL in the user's default web browser.
    Use this for showing the user a final result, like a generated report or a launched web app.
    """
    try:
        webbrowser.open(url, new=2)
        return f"Successfully opened {url} in the user's default browser."
    except Exception as e:
        return f"Error opening URL: {e}"

def search_web(query: str) -> str:
    """
    Performs a web search to answer a question or find information.
    Use this when you need a direct answer or a list of relevant web pages.
    """
    if not tavily_client: return "ERROR: TavilyClient is not configured."
    try:
        # qna_search is best for getting a direct, summarized answer
        response = tavily_client.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e: 
        return f"Error during web search: {e}"

def browse_and_summarize(url: str, task_description: str) -> str:
    """
    Navigates to a URL in a headless browser, extracts its text, and summarizes it
    in the context of a specific task.
    Use this to "read" a webpage, documentation, or an article to find specific information.
    """
    print(f"INFO: Browsing URL: {url} for task: {task_description}")
    # This tool uses its own temporary browser instance to avoid interfering with the main one.
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        clean_text = "\n".join(line for line in lines if line)

        if not clean_text:
            return "Error: Could not extract any text from the URL."

        print(f"INFO: Extracted {len(clean_text)} characters. Summarizing...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        Analyze the following text from {url} to help with this task: '{task_description}'.
        Provide a concise, actionable summary of the most relevant information.

        --- CONTENT ---
        {clean_text[:10000]}
        --- END CONTENT ---
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: An unexpected error occurred while browsing the website: {e}"
    finally:
        if driver:
            driver.quit()

# --- Stateful Browser Automation Tools ---
# These all operate on the single, shared browser instance.

def navigate_to(url: str) -> str:
    """Navigates the persistent browser to a URL for automation tasks."""
    return _BROWSER_INSTANCE.navigate(url)

def type_into(selector: str, text: str) -> str:
    """Types text into an element on the current page, identified by a CSS selector."""
    return _BROWSER_INSTANCE.type(selector, text)

def click_element(selector: str) -> str:
    """Clicks an element on the current page, identified by a CSS selector."""
    return _BROWSER_INSTANCE.click(selector)

def read_element_text(selector: str) -> str:
    """Reads the text content from an element on the current page, identified by a CSS selector."""
    return _BROWSER_INSTANCE.read_element(selector)

def close_browser():
    """Closes the persistent browser used for automation."""
    _BROWSER_INSTANCE.close()
    return "Automation browser has been closed."