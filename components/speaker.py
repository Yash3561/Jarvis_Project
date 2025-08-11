# components/speaker.py (The Final, Thread-Safe, "One-Shot" Version)

import pyttsx3
import threading

# --- THE FIX: Create a global lock to protect access to the system's TTS driver ---
# This lock ensures that only one 'say' function can run at any given time,
# preventing race conditions.
speaker_lock = threading.Lock()

def say(text: str):
    """
    Creates a new TTS engine instance, speaks the text, and then destroys the engine.
    This entire process is protected by a lock to ensure thread safety.
    This is a blocking call.
    """
    # Only one thread can acquire the lock and enter this block at a time.
    with speaker_lock:
        try:
            # Your reliable "One-Shot" logic is preserved inside the lock
            engine = pyttsx3.init()
            print(f"INFO: Jarvis speaking (pyttsx3): '{text[:70]}...'")
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            # This can catch the "run loop" error if it somehow still occurs,
            # or other issues like the app closing mid-speech.
            print(f"ERROR in Speaker.say: {e}")

def speak_in_thread(text: str):
    """
    Speaks the text in a non-blocking background thread.
    The 'say' function it calls is now thread-safe.
    """
    thread = threading.Thread(target=say, args=(text,), daemon=True)
    thread.start()