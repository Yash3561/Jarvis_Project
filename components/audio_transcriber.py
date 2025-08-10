# components/audio_transcriber.py (The Final, async-Corrected Version)

import asyncio
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

class AudioTranscriber:
    def __init__(self):
        self.deepgram_client = DeepgramClient()
        self.dg_connection = None
        self.full_transcript_parts = []

    def get_full_transcript(self): 
        return " ".join(self.full_transcript_parts).strip()
    
    def reset_transcript(self): 
        self.full_transcript_parts = []
    
    # --- THE FIX IS HERE: These are now async methods ---
    async def _on_message(self, *args, **kwargs):
        result = kwargs.get('result')
        if not result: return
        
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0 and result.is_final:
            self.full_transcript_parts.append(transcript)
            print(f"FINAL TRANSCRIPT PART: {transcript}")
            
    async def _on_error(self, *args, **kwargs):
        error = kwargs.get('error')
        print(f"ERROR: Deepgram error: {error}")

    async def start(self):
        options = LiveOptions(
            model="nova-2", 
            language="en-US", 
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000
        )
        try:
            self.dg_connection = self.deepgram_client.listen.asynclive.v("1")
            
            # Bind the event handlers
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)
            
            print("INFO: Connecting to Deepgram...")
            connection_result = await self.dg_connection.start(options)
            print("INFO: Deepgram connection established.")
            return connection_result
            
        except Exception as e: 
            print(f"ERROR: Could not start Deepgram connection: {e}")
            return None

    async def stop(self):
        if self.dg_connection: 
            await self.dg_connection.finish()
            self.dg_connection = None
            print("INFO: Deepgram connection closed.")
    
    async def send_audio(self, audio_chunk):
        if self.dg_connection: 
            await self.dg_connection.send(audio_chunk)