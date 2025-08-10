# tools/browser_tool.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import google.generativeai as genai
import config

# Configure Gemini for the summarization task
try:
    genai.configure(api_key=config.Settings.gemini_api_key)
except Exception as e:
    print(f"CRITICAL WARNING: Could not configure Gemini for the browser tool. It will fail. Error: {e}")

def browse_and_summarize_website(url: str, task_description: str) -> str:
    """
    Navigates to a URL, extracts its text content, and uses an LLM to summarize it
    in the context of a specific task. Use this to read documentation, tutorials,
    or find solutions to errors online.
    """
    print(f"INFO: Browsing URL: {url} for task: {task_description}")
    driver = None
    try:
        # Set up Chrome options for headless browsing
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Automatically download and manage the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        time.sleep(2) # Allow time for JavaScript to render the page

        # Extract the page content and clean it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        clean_text = "\n".join(line for line in lines if line)

        if not clean_text:
            return "Error: Could not extract any text content from the URL."

        print(f"INFO: Extracted {len(clean_text)} characters of text. Summarizing...")

        # Use a fast LLM to summarize the content in the context of the task
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        You are an expert at summarizing technical content. The user is trying to accomplish the following task: '{task_description}'.
        Below is the text content scraped from the URL '{url}'.
        Summarize this content, focusing ONLY on the information that is most relevant to the user's task.
        Provide a concise, actionable summary.

        --- START OF CONTENT ---
        {clean_text[:10000]} 
        --- END OF CONTENT ---

        Summary:
        """

        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        print("INFO: Summarization complete.")
        return summary

    except Exception as e:
        print(f"ERROR in browser tool: {e}")
        return f"Error: An unexpected error occurred while browsing the website. {e}"
    finally:
        if driver:
            driver.quit()