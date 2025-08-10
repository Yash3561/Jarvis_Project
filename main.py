# main.py (Definitive Version with Centralized Configuration)

import sys
from PyQt6.QtWidgets import QApplication

# --- CRITICAL FIX: CONFIGURE SETTINGS FIRST ---
# Import the necessary LlamaIndex components here
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config # Your config.py that loads .env

# Configure the global settings object BEFORE importing any other project modules
Settings.llm = GoogleGenAI(model="models/gemini-1.5-pro-latest", api_key=config.Settings.gemini_api_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
# ---------------------------------------------

# Now it is safe to import our other modules
from agent import AIAgent
from ui import ChatWindow
from tools.system_commands import set_ui_update_callback

if __name__ == "__main__":
    print("Initializing Jarvis...")
    agent_instance = AIAgent()
    
    app = QApplication(sys.argv)
    
    window = ChatWindow(agent_instance)
    
    set_ui_update_callback(window.terminal_output_received.emit)
    
    window.show()
    
    sys.exit(app.exec())