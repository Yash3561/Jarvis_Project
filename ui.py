# ui.py (More Robust Audio State Management)

import sys, os, threading, asyncio, markdown, struct, time
import sounddevice as sd
import pvporcupine
import pyaudio
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from components.audio_transcriber import AudioTranscriber
import config

PICOVOICE_KEYWORD_PATH = "jarvis_windows.ppn"

class ChatWindow(QWidget):
    response_received = pyqtSignal(str)
    wake_word_detected_signal = pyqtSignal()

    def __init__(self, agent_instance):
        super().__init__()
        self.agent = agent_instance
        self.transcriber = AudioTranscriber()
        self.is_listening = False
        self.mic_stream = None
        self.audio_loop = None
        self.audio_thread = None
        
        # --- NEW STATE MANAGEMENT ---
        self.is_wake_word_detector_running = False
        self.wake_word_thread = None

        self.init_ui()
        self.response_received.connect(self.on_agent_response)
        self.wake_word_detected_signal.connect(self.on_wake_word_detected)
        self.start_wake_word_detector() # Start on launch

    def closeEvent(self, event):
        self.stop_wake_word_detector()
        self.stop_audio_backend()
        event.accept()

    def init_ui(self):
        # ... your UI code is perfect, no changes ...
        self.setWindowTitle("Jarvis Co-Pilot"); self.setGeometry(300, 300, 700, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setStyleSheet("background-color: #161B22;")
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(10, 10, 10, 10); self.layout.setSpacing(10)
        self.chat_display = QTextBrowser(self); self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("QTextBrowser { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; font-family: 'Segoe UI', sans-serif; font-size: 14px; padding: 15px; } a { color: #58A6FF; } p { margin-bottom: 10px; } ul, ol { margin-left: 20px; } li { margin-bottom: 5px; } code { background-color: #2D333B; color: #A6ACCD; border-radius: 4px; padding: 2px 5px; font-family: 'Fira Code', monospace; } pre { background-color: #010409; border: 1px solid #3036D; border-radius: 5px; padding: 10px; margin: 5px 0; font-family: 'Fira Code', monospace; color: #A6ACCD; white-space: pre-wrap; }")
        self.layout.addWidget(self.chat_display)
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit(self); self.input_box.setPlaceholderText("Ask Jarvis...")
        self.input_box.setStyleSheet("QLineEdit { background-color: #0D1117; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; padding: 10px; } QLineEdit:focus { border: 1px solid #58A6FF; }")
        self.input_box.returnPressed.connect(self.handle_input); input_layout.addWidget(self.input_box)
        self.listen_button = QPushButton("🎤", self); self.listen_button.setFixedSize(40, 40)
        self.listen_button.setStyleSheet("QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 20px; } QPushButton:hover { background-color: #30363D; }")
        self.listen_button.clicked.connect(self.toggle_listening); input_layout.addWidget(self.listen_button)
        self.layout.addLayout(input_layout)
        self.add_message_to_display("system", "Jarvis is ready. Awaiting wake word...")

    # --- ROBUST WAKE WORD MANAGEMENT ---
    def start_wake_word_detector(self):
        if not self.is_wake_word_detector_running:
            self.is_wake_word_detector_running = True
            self.wake_word_thread = threading.Thread(target=self.run_wake_word_loop, daemon=True)
            self.wake_word_thread.start()

    def stop_wake_word_detector(self):
        self.is_wake_word_detector_running = False
        # The thread will see the flag and exit gracefully

    def run_wake_word_loop(self):
        try:
            porcupine = pvporcupine.create(
                access_key=config.Settings.picovoice_access_key,
                keyword_paths=[PICOVOICE_KEYWORD_PATH]
            )
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
                input=True, frames_per_buffer=porcupine.frame_length)
            
            print("INFO: Wake word detector running in background...")
            while self.is_wake_word_detector_running:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                if porcupine.process(pcm) >= 0:
                    print("INFO: Wake word detected!")
                    self.wake_word_detected_signal.emit()
        except Exception as e:
            print(f"Error in wake word detector thread: {e}")
        finally:
            if 'audio_stream' in locals() and audio_stream.is_active(): audio_stream.close()
            if 'pa' in locals(): pa.terminate()
            if 'porcupine' in locals(): porcupine.delete()
            print("INFO: Wake word detector shut down.")

    def on_wake_word_detected(self):
        if not self.is_listening:
            self.stop_wake_word_detector() # Stop listening for wake word
            self.toggle_listening() # Start listening for command

    def add_message_to_display(self, role, text):
        # ... no changes needed ...
        if role == 'user': html = f"<p style='color: #88C0D0; margin-bottom: 5px;'><b>&gt; {text.replace('<', '&lt;')}</b></p>"
        else: html = markdown.markdown(text, extensions=['fenced_code', 'tables']);
        if role == 'system': html = f"<div style='color: #A3BE8C; margin-bottom: 15px;'><i>{html}</i></div>"
        self.chat_display.append(html); self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
    
    def handle_input(self):
        # ... no changes needed ...
        user_text = self.input_box.text().strip()
        if not user_text: return
        self.add_message_to_display("user", user_text); self.input_box.clear()
        self.handle_input_from_speech(user_text) # Route through common logic

    def run_agent_task(self, question):
        # ... no changes needed ...
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        suggestion = loop.run_until_complete(self.agent.ask(question)); self.response_received.emit(suggestion)

    def on_agent_response(self, response):
        # ... no changes needed ...
        self.add_message_to_display("assistant", response)
        self.add_message_to_display("system", "Jarvis is ready. Awaiting wake word...")
        self.start_wake_word_detector() # Restart wake word detector after response

    def audio_callback(self, indata, frames, time, status):
        # ... no changes needed ...
        if status: print(status, file=sys.stderr)
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.send_audio(indata.tobytes()), self.audio_loop)

    def toggle_listening(self):
        # ... no changes needed, this logic is sound ...
        if not self.is_listening:
            self.listen_button.setText("...")
            self.listen_button.setStyleSheet("background-color: #D24242;")
            self.add_message_to_display("system", "Listening... Press the mic again to stop.")
            self.transcriber.reset_transcript()
            self.audio_thread = threading.Thread(target=self.start_audio_backend)
            self.audio_thread.start()
            self.is_listening = True
        else:
            self.listen_button.setText("🎤")
            self.listen_button.setStyleSheet("QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 20px; } QPushButton:hover { background-color: #30363D; }")
            self.stop_audio_backend()
            final_transcript = self.transcriber.get_full_transcript()
            if final_transcript:
                self.handle_input_from_speech(final_transcript)
            else:
                self.add_message_to_display("system", "No speech detected. Awaiting wake word...")
                self.start_wake_word_detector() # If no speech, go back to sleep
            self.is_listening = False
        
    def handle_input_from_speech(self, transcript):
        # ... no changes needed ...
        self.add_message_to_display("user", transcript)
        self.add_message_to_display("system", "Jarvis is thinking...")
        threading.Thread(target=self.run_agent_task, args=(transcript,)).start()

    def start_audio_backend(self):
        # ... no changes needed ...
        self.audio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.audio_loop)
        connection = self.audio_loop.run_until_complete(self.transcriber.start())
        
        if connection:
            self.mic_stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=self.audio_callback)
            self.mic_stream.start()
            self.audio_loop.run_forever()
        else:
            self.response_received.emit("**Error:** Could not connect to transcription service.")
            self.is_listening = False

    def stop_audio_backend(self):
        # ... no changes needed, the last fix was good ...
        if self.mic_stream:
            self.mic_stream.stop(); self.mic_stream.close(); self.mic_stream = None
        if self.audio_loop and self.audio_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.transcriber.stop(), self.audio_loop)
            try:
                future.result(timeout=1)
            except asyncio.TimeoutError:
                print("Warning: Timed out waiting for transcriber to stop.")
            
            self.audio_loop.call_soon_threadsafe(self.audio_loop.stop)
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join()
            if not self.audio_loop.is_closed():
                self.audio_loop.close()
                print("INFO: Audio event loop closed.")