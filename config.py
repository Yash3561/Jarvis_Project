# config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # Environment keys only; LLM is configured in main.py to avoid API calls on import
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")