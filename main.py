# main.py (Final Version)
import sys
from PyQt6.QtWidgets import QApplication
from agent import AIAgent
from ui import ChatWindow
# Import the function from the system_commands tool
from tools.system_commands import set_ui_update_callback

if __name__ == "__main__":
    print("Initializing Jarvis...")
    agent_instance = AIAgent()
    app = QApplication(sys.argv)
    window = ChatWindow(agent_instance)
    
    # --- THIS IS THE CONNECTION ---
    # Give the shell tool the ability to emit the UI's signal
    set_ui_update_callback(window.terminal_output_received.emit)
    
    window.show()
    sys.exit(app.exec())