# wake_word_detector.py
import os, struct, pyaudio
import pvporcupine
from dotenv import load_dotenv

load_dotenv()
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

class WakeWordDetector:
    def __init__(self, on_wake_word_detected):
        self.on_wake_word_detected = on_wake_word_detected
        self.porcupine = None; self.audio_stream = None; self.pyaudio_instance = None
        self._is_running = False

    def start(self):
        if not PICOVOICE_ACCESS_KEY: print("ERROR: PICOVOICE_ACCESS_KEY not found."); return
        try:
            self.porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keywords=['jarvis'], sensitivities=[0.6])
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
                input=True, frames_per_buffer=self.porcupine.frame_length)
            self._is_running = True
            print("INFO: Wake word detector started. Listening for 'Jarvis'...")
            while self._is_running:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                if self.porcupine.process(pcm) >= 0:
                    print("INFO: Wake word 'Jarvis' detected!")
                    self.on_wake_word_detected()
        except Exception as e: print(f"ERROR in WakeWordDetector: {e}")
        finally: self.stop()

    def stop(self):
        if self._is_running: self._is_running = False
        if self.audio_stream: self.audio_stream.stop_stream(); self.audio_stream.close(); self.audio_stream = None
        if self.pyaudio_instance: self.pyaudio_instance.terminate(); self.pyaudio_instance = None
        if self.porcupine: self.porcupine.delete(); self.porcupine = None
        print("INFO: Wake word detector stopped.")