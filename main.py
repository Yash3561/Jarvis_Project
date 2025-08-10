import sys, ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from agent import AIAgent
from ui import ChatWindow
def set_window_cloak(window_handle):
    try:
        WDA_EXCLUDEFROMCAPTURE = 0x11; user32 = ctypes.windll.user32
        result = user32.SetWindowDisplayAffinity(wintypes.HWND(window_handle), wintypes.DWORD(WDA_EXCLUDEFROMCAPTURE))
        if result == 0: raise ctypes.WinError()
        print("INFO: Window cloaking enabled.")
    except Exception as e: print(f"ERROR: Failed to cloak window: {e}")
if __name__ == "__main__":
    print("Initializing Jarvis..."); agent_instance = AIAgent()
    app = QApplication(sys.argv)
    window = ChatWindow(agent_instance)
    window.show()
    # To enable cloaking, uncomment these lines
    # window_id = window.winId()
    # QTimer.singleShot(200, lambda: set_window_cloak(int(window_id)))
    sys.exit(app.exec())