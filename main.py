# main.py (v14.1 - The Final Stable Version)

import sys, os, threading, asyncio, re, markdown
from dotenv import load_dotenv
load_dotenv()
import sounddevice as sd

from agent import AIAgent
from audio_transcriber import AudioTranscriber
from ocr_tool import read_text_from_image
from file_system_tool import list_files_in_directory



from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor

# ==============================================================================
# 3. THE INTERACTIVE CHAT UI & COMMAND ROUTER
# ==============================================================================
class ChatWindow(QWidget):
    response_received = pyqtSignal(str)
    
    def __init__(self, agent_instance):
        super().__init__()
        self.agent = agent_instance
        # This now correctly calls the simplified AudioTranscriber
        self.transcriber = AudioTranscriber()
        self.is_listening = False
        self.mic_stream = None
        self.audio_loop = None
        self.audio_thread = None
        self.init_ui()
        self.response_received.connect(self.on_agent_response)

    def closeEvent(self, event):
        """Ensure threads are cleaned up on window close."""
        self.stop_audio_backend()
        event.accept()

    def init_ui(self):
        self.setWindowTitle("Jarvis Co-Pilot"); self.setGeometry(300, 300, 700, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool); self.setStyleSheet("background-color: #161B22;")
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(10, 10, 10, 10); self.layout.setSpacing(10)
        self.chat_display = QTextBrowser(self); self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("QTextBrowser { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; font-family: 'Segoe UI', sans-serif; font-size: 14px; padding: 15px; } a { color: #58A6FF; } p { margin-bottom: 10px; } ul, ol { margin-left: 20px; } li { margin-bottom: 5px; } code { background-color: #2D333B; color: #A6ACCD; border-radius: 4px; padding: 2px 5px; font-family: 'Fira Code', monospace; } pre { background-color: #010409; border: 1px solid #30363D; border-radius: 5px; padding: 10px; margin: 5px 0; font-family: 'Fira Code', monospace; color: #A6ACCD; white-space: pre-wrap; }")
        self.layout.addWidget(self.chat_display)
        input_layout = QHBoxLayout(); self.input_box = QLineEdit(self); self.input_box.setPlaceholderText("Ask Jarvis...")
        self.input_box.setStyleSheet("QLineEdit { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; padding: 10px; } QLineEdit:focus { border: 1px solid #58A6FF; }")
        self.input_box.returnPressed.connect(self.handle_input); input_layout.addWidget(self.input_box)
        self.listen_button = QPushButton("🎤", self); self.listen_button.setFixedSize(40, 40)
        self.listen_button.setStyleSheet("QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 20px; } QPushButton:hover { background-color: #30363D; }")
        self.listen_button.clicked.connect(self.toggle_listening); input_layout.addWidget(self.listen_button)
        self.layout.addLayout(input_layout)
        self.add_message_to_display("system", "Jarvis is ready. Type or press the mic to speak.")

    def add_message_to_display(self, role, text):
        if role == 'user': html = f"<p style='color: #88C0D0; margin-bottom: 5px;'><b>&gt; {text.replace('<', '&lt;')}</b></p>"
        else: html = markdown.markdown(text, extensions=['fenced_code', 'tables']);
        if role == 'system': html = f"<div style='color: #A3BE8C; margin-bottom: 15px;'><i>{html}</i></div>"
        self.chat_display.append(html); self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
    
    def handle_input(self):
        user_text = self.input_box.text().strip()
        if not user_text: return
        self.add_message_to_display("user", user_text)
        self.input_box.clear()
        if not self.route_command(user_text):
            self.add_message_to_display("system", "Jarvis is thinking...")
            threading.Thread(target=self.run_agent_task, args=(user_text,)).start()

    def route_command(self, text):
        path_regex = r'["\']?([a-zA-Z]:\\[^"\'\s]+|~/[^"\'\s]+|/[^"\'\s]+)\.(png|jpg|jpeg|bmp)["\']?'
        match = re.search(path_regex, text, re.IGNORECASE)
        if match:
            file_path = match.group(0).strip().replace('"', '')
            print(f"INFO: OCR command detected for path: {file_path}")
            threading.Thread(target=self.run_ocr_and_analyze_task, args=(file_path,)).start()
            return True

        list_keywords = ['list files', 'list my files', 'what\'s on my desktop', 'show my desktop', 'list down the files']
        if any(keyword in text.lower() for keyword in list_keywords):
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            print(f"INFO: List files command detected for path: {desktop_path}")
            threading.Thread(target=self.run_list_files_task, args=(desktop_path,)).start()
            return True

        if text.lower() == 'reset': self.agent.reset_memory(); self.add_message_to_display("system", "Conversation history cleared."); return True
        elif text.lower() == 'quit': self.close(); return True
        return False

    def run_agent_task(self, question):
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        suggestion = loop.run_until_complete(self.agent.ask(question)); self.response_received.emit(suggestion)

    def run_ocr_and_analyze_task(self, image_path):
        self.add_message_to_display("system", f"Reading text from '{os.path.basename(image_path)}'...")
        extracted_text = read_text_from_image(image_path)
        if "Error:" in extracted_text: self.response_received.emit(extracted_text); return
        self.add_message_to_display("system", "Text extracted. Asking Jarvis to analyze...")
        analysis_question = f"Please analyze and summarize the following text which was extracted from a screenshot:\n\n---\n{extracted_text}\n---"
        self.run_agent_task(analysis_question)

    def run_list_files_task(self, directory_path):
        self.add_message_to_display("system", f"Listing files in '{directory_path}'...")
        result = list_files_in_directory(directory_path)
        self.response_received.emit(result)

    def on_agent_response(self, response):
        cursor = self.chat_display.textCursor(); cursor.movePosition(QTextCursor.MoveOperation.End); cursor.select(QTextCursor.SelectionType.BlockUnderCursor);
        if "<i>" in cursor.selection().toHtml(): cursor.removeSelectedText(); cursor.deletePreviousChar()
        self.chat_display.setTextCursor(cursor); self.add_message_to_display("assistant", response)

    def audio_callback(self, indata, frames, time, status):
        if status: print(status, file=sys.stderr)
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.send_audio(indata.tobytes()), self.audio_loop)

    def toggle_listening(self):
        if not self.is_listening:
            self.listen_button.setText("..."); self.listen_button.setStyleSheet("background-color: #D24242;")
            self.add_message_to_display("system", "Listening... Press the mic again to stop.")
            self.transcriber.reset_transcript()
            self.audio_thread = threading.Thread(target=self.start_audio_backend)
            self.audio_thread.start()
        else:
            self.listen_button.setText("🎤"); self.listen_button.setStyleSheet("QPushButton { ... }")
            self.stop_audio_backend()
            final_transcript = self.transcriber.get_full_transcript()
            if final_transcript: self.handle_input_from_speech(final_transcript)
            else: self.add_message_to_display("system", "No speech detected.")
        self.is_listening = not self.is_listening
        
    def handle_input_from_speech(self, transcript):
        self.add_message_to_display("user", transcript)
        if not self.route_command(transcript):
            self.add_message_to_display("system", "Jarvis is thinking...")
            threading.Thread(target=self.run_agent_task, args=(transcript,)).start()

    def start_audio_backend(self):
        self.audio_loop = asyncio.new_event_loop(); asyncio.set_event_loop(self.audio_loop)
        if self.audio_loop.run_until_complete(self.transcriber.start()):
            self.mic_stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=self.audio_callback)
            self.mic_stream.start(); self.audio_loop.run_forever()
        else: self.response_received.emit("**Error:** Could not connect to transcription service.")
        self.is_listening = False

    def stop_audio_backend(self):
        if self.mic_stream: self.mic_stream.stop(); self.mic_stream.close(); self.mic_stream = None
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.stop(), self.audio_loop)
            self.audio_loop.call_soon_threadsafe(self.audio_loop.stop)
            if self.audio_thread and self.audio_thread.is_alive(): self.audio_thread.join()
            self.audio_loop.close()

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    agent_instance = AIAgent()
    window = ChatWindow(agent_instance)
    window.show()
    sys.exit(app.exec())