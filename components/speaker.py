# components/speaker.py (The Final, Reliable pyttsx3 Version)

import pyttsx3
import threading

def say(text: str):
    """
    Creates a new TTS engine instance, speaks the text, and then destroys the engine.
    This is the "One-Shot" pattern, which is very reliable in threaded applications.
    This is a blocking call.
    """
    try:
        engine = pyttsx3.init()
        print(f"INFO: Jarvis speaking (pyttsx3): '{text[:70]}...'")
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        # On some systems, a small delay helps ensure the engine is released
        # import time; time.sleep(0.1) 
    except Exception as e:
        print(f"ERROR in Speaker.say: {e}")

def speak_in_thread(text: str):
    """
    Speaks the text in a non-blocking background thread using a fresh TTS instance.
    """
    thread = threading.Thread(target=say, args=(text,), daemon=True)
    thread.start()