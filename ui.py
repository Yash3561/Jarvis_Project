# ui.py (The Final, Polished, and Complete Version)

import sys, os, threading, asyncio, markdown, struct, time, re
import sounddevice as sd
import pvporcupine
import pyaudio
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from components.audio_transcriber import AudioTranscriber
from components import speaker
import config
import styles # Import our new stylesheet

# --- NEW: Imports for Syntax Highlighting ---
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

PICOVOICE_KEYWORD_PATH = "jarvis_windows.ppn"

class ChatWindow(QWidget):
    response_received = pyqtSignal(str)
    wake_word_detected_signal = pyqtSignal()
    terminal_output_received = pyqtSignal(str)

    def __init__(self, agent_instance):
        super().__init__()
        self.agent = agent_instance
        self.transcriber = AudioTranscriber()
        self.is_listening = False
        self.is_thinking = False
        self.mic_stream = None
        self.audio_loop = None
        self.audio_thread = None
        self.is_wake_word_detector_running = False
        self.wake_word_thread = None

        self.init_ui()
        
        self.response_received.connect(self.on_agent_response)
        self.wake_word_detected_signal.connect(self.on_wake_word_detected)
        self.terminal_output_received.connect(self.update_terminal_display)
        
        self.start_wake_word_detector()

    def closeEvent(self, event):
        self.stop_wake_word_detector()
        self.stop_audio_backend()
        event.accept()

    def init_ui(self):
        self.setWindowTitle("Jarvis Co-Pilot"); self.setGeometry(300, 300, 700, 800)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setStyleSheet(styles.MAIN_WINDOW_STYLE)
        
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(10, 10, 10, 10); self.layout.setSpacing(10)
        
        self.chat_display = QTextBrowser(self); self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet(styles.CHAT_DISPLAY_STYLE)
        self.layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit(self); self.input_box.setPlaceholderText("Ask Jarvis...")
        self.input_box.setStyleSheet(styles.INPUT_BOX_STYLE)
        self.input_box.returnPressed.connect(self.handle_input); input_layout.addWidget(self.input_box)
        
        self.listen_button = QPushButton("🎤", self); self.listen_button.setFixedSize(40, 40)
        self.listen_button.setStyleSheet(styles.LISTEN_BUTTON_STYLE)
        self.listen_button.clicked.connect(self.toggle_listening); input_layout.addWidget(self.listen_button)
        self.layout.addLayout(input_layout)
        
        self.terminal_display = QTextBrowser(self)
        self.terminal_display.setPlaceholderText("Jarvis's Terminal Output...")
        self.terminal_display.setStyleSheet(styles.TERMINAL_DISPLAY_STYLE)
        self.terminal_display.setFixedHeight(150)
        self.layout.addWidget(self.terminal_display)
        
        self.add_message_to_display("system", "Jarvis is ready. Awaiting wake word...")

    def update_terminal_display(self, text):
        self.terminal_display.append(text)
        self.terminal_display.verticalScrollBar().setValue(self.terminal_display.verticalScrollBar().maximum())

    def format_code(self, code_text):
        try:
            lexer = guess_lexer(code_text)
        except:
            lexer = get_lexer_by_name("python", stripall=True)
            
        formatter = HtmlFormatter(style="monokai", noclasses=True) # Use inline styles
        highlighted_code = highlight(code_text, lexer, formatter)
        return f"<div style='background-color: #010409; border-radius: 5px; padding: 10px;'>{highlighted_code}</div>"

    def add_message_to_display(self, role, text):
        if role == 'user':
            html = f"<p style='color: #88C0D0; margin-bottom: 5px;'><b>&gt; {text.replace('<', '&lt;')}</b></p>"
        else:
            # Handle code blocks first
            parts = re.split(r"(```(?:\w+\n)?[\s\S]*?```)", text)
            html_parts = []
            for part in parts:
                if part.startswith("```"):
                    # It's a code block
                    code_match = re.match(r"```(\w+)?\n([\s\S]*)```", part)
                    if code_match:
                        lang, code = code_match.groups()
                        html_parts.append(self.format_code(code))
                    else: # Fallback for code block without language
                        html_parts.append(f"<pre><code>{part[3:-3]}</code></pre>")
                else:
                    # It's regular markdown text
                    html_parts.append(markdown.markdown(part, extensions=['fenced_code', 'tables']))
            html = "".join(html_parts)

        if role == 'system':
            html = f"<div style='color: #A3BE8C; margin-bottom: 15px;'><i>{html}</i></div>"
        
        self.chat_display.append(html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        
    def on_agent_response(self, response):
        self.is_thinking = False
        self.listen_button.setText("🎤")
        
        self.add_message_to_display("assistant", response)
        
        spoken_response = response
        match = re.search(r"Final Answer:(.*?)(Supporting Data:|$)", response, re.DOTALL)
        if match:
            spoken_response = match.group(1).strip()
        
        speaker.speak_in_thread(spoken_response)
        
        image_matches = re.findall(r'(\w+\.png)', response)
        if image_matches:
            image_path = image_matches[-1]
            if os.path.exists(image_path):
                print(f"INFO: Found generated image '{image_path}'. Displaying in UI.")
                abs_path = os.path.abspath(image_path).replace('\\', '/')
                image_html = f'<p><b>Generated Image:</b></p><img src="file:///{abs_path}" alt="{image_path}" style="max-width: 100%; height: auto; border-radius: 5px;">'
                self.chat_display.append(image_html)
        
        self.add_message_to_display("system", "Jarvis is ready. Awaiting wake word...")
        self.start_wake_word_detector()

    def process_user_query(self, query: str):
        if self.is_thinking: return
        self.is_thinking = True
        self.listen_button.setText("🧠")
        self.add_message_to_display("user", query)
        self.add_message_to_display("system", "Jarvis is thinking...")
        threading.Thread(target=self.run_agent_task, args=(query,)).start()

    def handle_input(self):
        user_text = self.input_box.text().strip()
        if not user_text: return
        self.input_box.clear()
        self.process_user_query(user_text)

    def toggle_listening(self):
        if self.is_thinking: return

        if not self.is_listening:
            self.listen_button.setText("...")
            self.listen_button.setStyleSheet(styles.LISTENING_BUTTON_STYLE)
            self.add_message_to_display("system", "Listening... Press the mic again to stop.")
            self.transcriber.reset_transcript()
            self.audio_thread = threading.Thread(target=self.start_audio_backend)
            self.audio_thread.start()
            self.is_listening = True
        else:
            self.listen_button.setText("🎤")
            self.listen_button.setStyleSheet(styles.LISTEN_BUTTON_STYLE)
            if self.is_listening:
                self.stop_audio_backend()
                final_transcript = self.transcriber.get_full_transcript()
                if final_transcript:
                    self.process_user_query(final_transcript)
                else:
                    self.add_message_to_display("system", "No speech detected. Awaiting wake word...")
                    self.start_wake_word_detector()
            self.is_listening = False
            
    # The rest of your proven, working functions
    def start_wake_word_detector(self):
        if not self.is_wake_word_detector_running:
            self.is_wake_word_detector_running = True
            self.wake_word_thread = threading.Thread(target=self.run_wake_word_loop, daemon=True)
            self.wake_word_thread.start()

    def stop_wake_word_detector(self):
        self.is_wake_word_detector_running = False

    def run_wake_word_loop(self):
        try:
            porcupine = pvporcupine.create(access_key=config.Settings.picovoice_access_key, keyword_paths=[PICOVOICE_KEYWORD_PATH])
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
            print("INFO: Wake word detector running in background...")
            while self.is_wake_word_detector_running:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                if porcupine.process(pcm) >= 0:
                    print("INFO: Wake word detected!")
                    time.sleep(0.5)
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
            self.stop_wake_word_detector()
            self.toggle_listening()

    def run_agent_task(self, question):
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        suggestion = loop.run_until_complete(self.agent.ask(question)); self.response_received.emit(suggestion)

    def audio_callback(self, indata, frames, time, status):
        if status: print(status, file=sys.stderr)
        if self.audio_loop and self.audio_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.transcriber.send_audio(indata.tobytes()), self.audio_loop)

    def start_audio_backend(self):
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