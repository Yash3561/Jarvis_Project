# main.py (Corrected and Simplified)

import sys
from PyQt6.QtWidgets import QApplication
from agent import AIAgent
from ui import ChatWindow
# We no longer need MainController

if __name__ == "__main__":
    print("Initializing Jarvis...")
    agent_instance = AIAgent()
    
    app = QApplication(sys.argv)
    
    # We just create the agent and the window. 
    # The window now manages everything itself.
    window = ChatWindow(agent_instance)
    
    window.show()
    
    sys.exit(app.exec())