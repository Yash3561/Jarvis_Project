# config.py
from dotenv import load_dotenv
import os
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings
load_dotenv()

class Settings:
    # This is your main LLM, likely also from Google
    llm = GoogleGenAI(model="models/gemini-1.5-pro-latest", temperature=0.1)
    embed_model = "local:BAAI/bge-small-en-v1.5"
    # --- THIS IS THE IMPORTANT PART ---
    # We are getting the Google key from the .env file
    # and making it available for the Gemini Vision tool.
    gemini_api_key = os.getenv("GOOGLE_API_KEY")

    # Load other keys as well
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")