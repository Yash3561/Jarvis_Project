# main.py (The Definitive, Stable V1.0 Launcher)

import sys
from PyQt6.QtWidgets import QApplication

# --- CRITICAL: CONFIGURE GLOBAL SETTINGS FIRST ---
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config

print("INFO: Configuring global AI settings...")
Settings.llm = GoogleGenAI(model="models/gemini-1.5-pro-latest", api_key=config.Settings.gemini_api_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
print("INFO: AI settings configured.")

# --- Now it is safe to import our application modules ---
from agent import AIAgent
from ui import ChatWindow
from tools.system_commands import set_ui_window_instance

if __name__ == "__main__":
    print("Initializing Jarvis...")
    agent_instance = AIAgent()
    
    app = QApplication(sys.argv)
    
    window = ChatWindow(agent_instance)
    
    # This is the crucial link that allows tools to talk to the UI
    set_ui_window_instance(window)
    
    window.show()
    
    sys.exit(app.exec())