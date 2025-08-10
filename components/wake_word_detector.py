# components/wake_word_detector.py (Qt Signal Version)

import struct
import pvporcupine
import pyaudio
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class WakeWordDetector(QObject):
    # This signal will be emitted when the wake word is detected
    wakeWordDetected = pyqtSignal()

    def __init__(self, access_key, keyword_path):
        super().__init__()
        self.access_key = access_key
        self.keyword_path = keyword_path
        self.is_running = False
        self.porcupine = None
        self.audio_stream = None
        self.pa = None

    def run(self):
        """This method will run in the background thread."""
        self.is_running = True
        print("INFO: Wake word detector started. Listening for 'Jarvis'...")
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.keyword_path]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            while self.is_running:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                if self.porcupine.process(pcm) >= 0:
                    print("INFO: Wake word 'Jarvis' detected!")
                    self.wakeWordDetected.emit() # Emit the signal instead of calling a function
                    self.is_running = False # Stop after detection

        except Exception as e:
            print(f"ERROR in WakeWordDetector run: {e}")
        finally:
            if self.porcupine:
                self.porcupine.delete()
            if self.audio_stream:
                self.audio_stream.close()
            if self.pa:
                self.pa.terminate()
            print("INFO: Wake word detector thread finished.")

    def stop(self):
        self.is_running = False