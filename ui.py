import sys
import os
import threading
import asyncio
import markdown
import sounddevice as sd

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor

from audio_transcriber import AudioTranscriber

class ChatWindow(QWidget):
    response_received = pyqtSignal(str)
    
    def __init__(self, agent_instance):
        super().__init__()
        self.agent = agent_instance
        self.transcriber = AudioTranscriber(on_final_transcript_received=None)
        self.is_listening = False
        self.mic_stream = None
        self.audio_loop = None
        self.audio_thread = None
        self.init_ui()
        self.response_received.connect(self.on_agent_response)

    def init_ui(self):
        self.setWindowTitle("Jarvis Co-Pilot")
        self.setGeometry(300, 300, 700, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setStyleSheet("background-color: #161B22;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.chat_display = QTextBrowser(self)
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("""
            QTextBrowser { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; font-family: "Segoe UI", sans-serif; font-size: 14px; padding: 15px; }
            a { color: #58A6FF; text-decoration: none; } p { margin-bottom: 10px; } ul, ol { margin-left: 20px; } li { margin-bottom: 5px; }
            code { background-color: #2D333B; color: #A6ACCD; border-radius: 4px; padding: 2px 5px; font-family: "Fira Code", monospace; }
            pre { background-color: #010409; border: 1px solid #30363D; border-radius: 5px; padding: 10px; margin: 5px 0; font-family: "Fira Code", monospace; color: #A6ACCD; white-space: pre-wrap; }
        """)
        self.layout.addWidget(self.chat_display)
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Ask Jarvis...")
        self.input_box.setStyleSheet("QLineEdit { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; padding: 10px; } QLineEdit:focus { border: 1px solid #58A6FF; }")
        self.input_box.returnPressed.connect(self.handle_input)
        input_layout.addWidget(self.input_box)
        self.listen_button = QPushButton("🎤", self)
        self.listen_button.setFixedSize(40, 40)
        self.listen_button.setStyleSheet("QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 20px; } QPushButton:hover { background-color: #30363D; }")
        self.listen_button.clicked.connect(self.toggle_listening)
        input_layout.addWidget(self.listen_button)
        self.layout.addLayout(input_layout)
        self.add_message_to_display("system", "Jarvis is ready. Type or press the mic to speak.")

    def add_message_to_display(self, role, text):
        if role == 'user': html = f"<p style='color: #88C0D0; margin-bottom: 5px;'><b>&gt; {text.replace('<', '&lt;')}</b></p>"
        else: html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
        if role == 'system': html = f"<div style='color: #A3BE8C; margin-bottom: 15px;'><i>{html}</i></div>"
        self.chat_display.append(html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def handle_input(self):
        user_text = self.input_box.text().strip()
        if not user_text: return
        self.add_message_to_display("user", user_text)
        self.input_box.clear()
        
        if user_text.lower() == 'reset':
            self.agent.reset_memory()
            self.add_message_to_display("system", "Conversation history cleared.")
        elif user_text.lower() == 'quit':
            self.close()
        else:
            self.add_message_to_display("system", "Jarvis is thinking...")
            threading.Thread(target=self.run_agent_task, args=(user_text,)).start()

    def run_agent_task(self, question):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        suggestion = loop.run_until_complete(self.agent.ask(question))
        self.response_received.emit(suggestion)

    def on_agent_response(self, response):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        if "<i>" in cursor.selection().toHtml():
            cursor.removeSelectedText()
            cursor.deletePreviousChar()
        self.chat_display.setTextCursor(cursor)
        self.add_message_to_display("assistant", response)

    def audio_callback(self, indata, frames, time, status):
        if status: print(status, file=sys.stderr)
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.send_audio(indata.tobytes()), self.audio_loop)

    def toggle_listening(self):
        if not self.is_listening:
            self.listen_button.setText("...")
            self.listen_button.setStyleSheet("background-color: #D24242;")
            self.add_message_to_display("system", "Listening... Press the mic again to stop.")
            self.transcriber.reset_transcript()
            self.audio_thread = threading.Thread(target=self.start_audio_backend)
            self.audio_thread.start()
        else:
            self.listen_button.setText("🎤")
            self.listen_button.setStyleSheet("QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 20px; } QPushButton:hover { background-color: #30363D; }")
            self.stop_audio_backend()
            final_transcript = self.transcriber.get_full_transcript()
            if final_transcript:
                self.handle_input_from_speech(final_transcript)
            else:
                self.add_message_to_display("system", "No speech detected.")
        self.is_listening = not self.is_listening
        
    def handle_input_from_speech(self, transcript):
        self.add_message_to_display("user", transcript)
        self.add_message_to_display("system", "Jarvis is thinking...")
        threading.Thread(target=self.run_agent_task, args=(transcript,)).start()

    def start_audio_backend(self):
        self.audio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.audio_loop)
        if self.audio_loop.run_until_complete(self.transcriber.start()):
            self.mic_stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=self.audio_callback)
            self.mic_stream.start()
            self.audio_loop.run_forever()
        else:
            self.response_received.emit("**Error:** Could not connect to transcription service.")
            self.is_listening = False

    def stop_audio_backend(self):
        if self.mic_stream:
            self.mic_stream.stop()
            self.mic_stream.close()
            self.mic_stream = None
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.stop(), self.audio_loop)
            self.audio_loop.call_soon_threadsafe(self.audio_loop.stop)
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_loop.close()