# ui.py (The Final, Definitive, and 100% Correct "Web Bridge" Version)

import sys, os, threading, asyncio, markdown, re, time, struct
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# --- NEW: Imports for Triage Agent & Error Handling ---
from llama_index.core import Settings
import traceback

import sounddevice as sd
import pvporcupine
import pyaudio

from components.audio_transcriber import AudioTranscriber
from components import speaker
import config

from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter

PICOVOICE_KEYWORD_PATH = "jarvis_windows.ppn"

class Bridge(QObject):
    # This class is perfect as is. No changes needed.
    def __init__(self, agent_instance, ui_window):
        super().__init__()
        self.agent = agent_instance
        self.ui = ui_window
    @pyqtSlot(str)
    def process_user_query(self, query: str):
        self.ui.process_user_query(query)
    @pyqtSlot()
    def toggle_listening(self):
        self.ui.toggle_listening()
    def escape_for_js(self, text: str) -> str:
        return text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '').replace('`','\\`')
    def escape_for_js_template(self, text: str) -> str:
        return text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    @pyqtSlot(bool)
    def toggle_mute(self, is_muted):
        # We need to add this method to ChatWindow
        self.ui.toggle_mute(is_muted)

class ChatWindow(QMainWindow):
    response_received = pyqtSignal(str)
    terminal_output_received = pyqtSignal(str)
    wake_word_detected_signal = pyqtSignal()

    def __init__(self, agent_instance):
        # Your __init__ is perfect. No changes needed.
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
        self.code_block_count = 0
        self.agent_thread = None
        self.init_ui()
        self.response_received.connect(self.on_agent_response)
        self.terminal_output_received.connect(self.on_terminal_output)
        self.wake_word_detected_signal.connect(self.on_wake_word_detected)
        self.start_wake_word_detector()

    def closeEvent(self, event):
        # Perfect. No changes.
        self.stop_wake_word_detector()
        self.stop_audio_backend()
        event.accept()

    def init_ui(self):
        # Perfect. No changes.
        self.setWindowTitle("Jarvis Co-Pilot"); self.setGeometry(300, 300, 700, 800)
        self.setStyleSheet("background-color: #0d1117;")
        self.web_view = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = Bridge(self.agent, self)
        self.channel.registerObject('backend_bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "index.html"))
        self.web_view.setUrl(QUrl.fromLocalFile(file_path))
        self.setCentralWidget(self.web_view)

    def run_js(self, script: str):
        # Perfect. No changes.
        self.web_view.page().runJavaScript(script)

    # --- NEW: Adding the mute function handler back in ---
    def toggle_mute(self, is_muted: bool):
        speaker.set_mute(is_muted)

    @pyqtSlot(str)
    def on_terminal_output(self, text):
        # Perfect. No changes.
        self.run_js(f"add_terminal_output('{self.bridge.escape_for_js(text)}')")
        
    def update_terminal_display(self, text):
        # Perfect. No changes.
        self.terminal_output_received.emit(text)
    
    # --- UPDATED: on_agent_response now handles project steps ---
    @pyqtSlot(str)
    def on_agent_response(self, response):
        self.is_thinking = False
        self.run_js("update_mic_button('idle')")

        spoken_summary = ""
        full_response_for_display = response
        
        summary_match = re.search(r"<SPOKEN_SUMMARY>(.*?)</SPOKEN_SUMMARY>", response, re.DOTALL)
        full_match = re.search(r"<FULL_RESPONSE>(.*?)</FULL_RESPONSE>", response, re.DOTALL)

        if summary_match and full_match:
            spoken_summary = summary_match.group(1).strip()
            full_response_for_display = full_match.group(1).strip()
        else:
            # This is okay, it means it's likely a project update message
            # which doesn't use the XML tags.
            pass

        # Determine if the project/task is over to restart the wake word detector.
        is_final_message = "completed successfully" in full_response_for_display.lower() or "project failed" in full_response_for_display.lower() or "fatal error" in full_response_for_display.lower()

        # Your excellent formatting logic handles everything perfectly.
        display_html = self.format_response_for_html(full_response_for_display)
        escaped_html = self.bridge.escape_for_js_template(display_html)
        escaped_raw_text = self.bridge.escape_for_js_template(full_response_for_display)
        self.run_js(f"add_message('assistant', `{escaped_html}`, `{escaped_raw_text}`)")
        
        if spoken_summary:
            speaker.speak_in_thread(spoken_summary)

        # Your image handling logic is perfect.
        image_matches = re.findall(r'(\w+\.png)', full_response_for_display)
        if image_matches:
            image_path = image_matches[-1]
            if os.path.exists(image_path):
                abs_path = os.path.abspath(image_path).replace('\\', '/')
                image_html = f'<img src="file:///{abs_path}" alt="{image_path}" style="max-width: 100%; height: auto; border-radius: 10px;">'
                self.run_js(f"add_message('assistant', '{self.bridge.escape_for_js(image_html)}', '')")
        
        # Only restart the wake word listener when the conversation/project is truly over.
        if is_final_message:
            self.run_js("add_message('system', 'Jarvis is ready. Awaiting wake word...')")
            self.start_wake_word_detector()

    def format_code(self, code_text):
        # Perfect. No changes.
        self.code_block_count += 1
        try: lexer = guess_lexer(code_text)
        except: lexer = get_lexer_by_name("text", stripall=True)
        formatter = HtmlFormatter(style="monokai", noclasses=True)
        highlighted_code = highlight(code_text, lexer, formatter)
        html = f"""<pre><button class="code-copy-btn" onclick="copyCode(this)">Copy</button><code>{highlighted_code}</code></pre>"""
        return html

    def format_response_for_html(self, text):
        # Perfect. No changes.
        parts = re.split(r"(```(?:\w+\n)?[\s\S]*?```)", text)
        content_html = ""
        for part in parts:
            if part.startswith("```"):
                code_match = re.match(r"```(?:\w+)?\n([\s\S]*)```", part)
                if code_match: content_html += self.format_code(code_match.group(1).strip())
                else: content_html += self.format_code(part[3:-3].strip())
            else:
                md_html = markdown.markdown(part)
                if md_html.startswith("<p>") and md_html.endswith("</p>"): md_html = md_html[3:-4]
                content_html += md_html
        return content_html

    # --- NEW: The Triage Agent ---
    def _classify_query(self, query: str) -> str:
        print("INFO: Triage agent classifying query...")
        prompt = f"You are a Triage Dispatcher AI. Classify the user's request as 'CHAT' or 'PROJECT'.\n1. CHAT: Simple, single-step requests...\n2. PROJECT: Complex, multi-step requests...\nUser Request: \"{query}\"\nRespond with only a single word: CHAT or PROJECT."
        try:
            response = Settings.llm.complete(prompt)
            decision = response.text.strip().upper()
            if "PROJECT" in decision:
                print("INFO: Triage decision: PROJECT")
                return "PROJECT"
            return "CHAT"
        except Exception as e:
            print(f"ERROR: Triage classification failed: {e}. Defaulting to CHAT.")
            return "CHAT"
            
    # --- UPDATED: The new main input processor ---
    def process_user_query(self, query: str):
        if self.is_thinking: return
        self.is_thinking = True
        self.run_js("update_mic_button('thinking')")
        escaped_query = self.bridge.escape_for_js_template(query)
        self.run_js(f"add_message('user', `{escaped_query}`, `{escaped_query}`)")
        
        decision = self._classify_query(query)
        
        if decision == "PROJECT":
            self.run_js("add_message('system', 'Understood. Initiating project...')")
            self.agent_thread = threading.Thread(target=self.run_controller_task, args=(query,), daemon=True)
            self.agent_thread.start()
        else: # CHAT
            self.run_js("add_message('system', 'Jarvis is thinking...')")
            self.agent_thread = threading.Thread(target=self.run_agent_task, args=(query,), daemon=True)
            self.agent_thread.start()

    # --- UPDATED: The task runners ---
    def run_agent_task(self, question):
        """Runs the simple CHAT agent."""
        try:
            # We use asyncio.run() because our patched agent.ask is now async
            suggestion = asyncio.run(self.agent.ask(question))
            self.response_received.emit(suggestion)
        except Exception as e:
            self.response_received.emit(f"A fatal error occurred: {traceback.format_exc()}")

    def run_controller_task(self, project_prompt: str):
        """Runs the PROJECT controller with robust error handling."""
        try:
            from main_controller import MainController
            controller = MainController(self.agent, self)
            controller.execute_project(project_prompt)
        except Exception as e:
            error_message = f"<SPOKEN_SUMMARY>A fatal error occurred during the project.</SPOKEN_SUMMARY><FULL_RESPONSE>**Project Failed with a Critical Error:**\n\n```\n{traceback.format_exc()}\n```</FULL_RESPONSE>"
            self.response_received.emit(error_message)
            
    def toggle_listening(self):
        if self.is_thinking: return
        if not self.is_listening:
            self.is_listening = True
            self.run_js("update_mic_button('listening')")
            self.run_js("add_message('system', 'Listening...')")
            self.transcriber.reset_transcript()
            self.audio_thread = threading.Thread(target=self.start_audio_backend, daemon=True)
            self.audio_thread.start()
        else:
            self.is_listening = False
            self.run_js("update_mic_button('idle')")
            self.stop_audio_backend()
            final_transcript = self.transcriber.get_full_transcript()
            if final_transcript: self.process_user_query(final_transcript)
            else:
                self.run_js("add_message('system', 'No speech detected. Awaiting wake word...')")
                self.start_wake_word_detector()
    
    def start_wake_word_detector(self):
        if not self.is_wake_word_detector_running:
            self.is_wake_word_detector_running = True
            self.wake_word_thread = threading.Thread(target=self.run_wake_word_loop, daemon=True)
            self.wake_word_thread.start()

    def stop_wake_word_detector(self):
        self.is_wake_word_detector_running = False

    @pyqtSlot()
    def on_wake_word_detected(self):
        if not self.is_listening and not self.is_thinking:
            self.stop_wake_word_detector()
            self.toggle_listening()
            
    def run_wake_word_loop(self):
        porcupine = None; pa = None; audio_stream = None
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
            if audio_stream: audio_stream.close()
            if pa: pa.terminate()
            if porcupine: porcupine.delete()
            print("INFO: Wake word detector shut down.")

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