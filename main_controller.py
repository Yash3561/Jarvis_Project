# main_controller.py (Qt Signal Version)

from PyQt6.QtCore import QThread
from components.wake_word_detector import WakeWordDetector
import time
import threading
import config

PICOVOICE_KEYWORD_PATH = "jarvis_windows.ppn" # CHANGE THIS if needed

class MainController:
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.agent = ui_instance.agent
        self.transcriber = self.ui.transcriber
        self.state = "sleeping"
        self.is_running = True

        # Setup the QThread and the worker
        self.wake_word_thread = QThread()
        self.wake_word_detector = WakeWordDetector(
            access_key=config.Settings.picovoice_access_key,
            keyword_path=PICOVOICE_KEYWORD_PATH
        )
        self.wake_word_detector.moveToThread(self.wake_word_thread)
        
        # Connect signals and slots
        self.wake_word_thread.started.connect(self.wake_word_detector.run)
        self.wake_word_detector.wakeWordDetected.connect(self.handle_wake_word_detection)
        self.wake_word_thread.finished.connect(self.wake_word_thread.deleteLater)

    def start(self):
        self.start_sleeping()

    def stop(self):
        self.is_running = False
        self.wake_word_detector.stop()
        self.wake_word_thread.quit()
        self.wake_word_thread.wait()
        self.ui.stop_audio_backend()

    def start_sleeping(self):
        if not self.is_running or self.state != "sleeping": return
        self.ui.update_status("Awaiting wake word...")
        self.wake_word_thread.start()

    def handle_wake_word_detection(self):
        # This method is now safely called in the MAIN UI THREAD
        if self.state != "sleeping": return
        
        self.state = "listening"
        # Stop the thread safely
        self.wake_word_thread.quit()
        self.wake_word_thread.wait()
        
        # Use the UI's proven method to start listening
        self.ui.start_listening_from_controller()

    def process_transcript(self, transcript):
        if self.state != "listening": return
        
        self.state = "thinking"
        self.ui.add_message_to_display("user", transcript)
        self.ui.update_status("Jarvis is thinking...")
        
        threading.Thread(target=self.run_agent_and_finish, args=(transcript,)).start()

    def run_agent_and_finish(self, transcript):
        response = self.ui.run_agent_task_and_get_response(transcript)
        self.ui.on_agent_response(response)
        
        self.state = "sleeping" # Reset state
        time.sleep(1)
        self.start_sleeping()