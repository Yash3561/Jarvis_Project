import os, asyncio
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

class AudioTranscriber:
    def __init__(self):
        self.deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
        self.dg_connection = None
        self.full_transcript_parts = []
    def get_full_transcript(self): return " ".join(self.full_transcript_parts)
    def reset_transcript(self): self.full_transcript_parts = []
    async def start(self):
        options = LiveOptions(model="nova-2-general", language="en-US", smart_format=True, encoding="linear16", channels=1, sample_rate=16000)
        try:
            self.dg_connection = self.deepgram_client.listen.asynclive.v("1")
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)
            await self.dg_connection.start(options)
            print("INFO: Deepgram connection established.")
            return True
        except Exception as e: print(f"ERROR: Could not start Deepgram connection: {e}"); return False
    async def stop(self):
        if self.dg_connection: await self.dg_connection.finish(); self.dg_connection = None; print("INFO: Deepgram connection closed.")
    async def send_audio(self, audio_chunk):
        if self.dg_connection: await self.dg_connection.send(audio_chunk)
    async def _on_message(self, *args, **kwargs):
        result = kwargs.get('result'); transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0 and result.is_final: self.full_transcript_parts.append(transcript); print(f"FINAL TRANSCRIPT PART: {transcript}")
    async def _on_error(self, *args, **kwargs): print(f"ERROR: Deepgram error: {kwargs.get('error')}")