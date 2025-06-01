import os
import time
from groq import Groq
import json
import asyncio
from app.config import GROQ_API_KEY
from concurrent.futures import ThreadPoolExecutor

class TranscriptionService:
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using Groq's Whisper model.
        Returns the transcription with timestamps.
        """
        try:
            start_time = time.time()
            
            # Since Groq's API is synchronous, run it in a thread pool
            def transcribe():
                with open(audio_path, 'rb') as audio_file:
                    response = self.groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3-turbo",
                        response_format="verbose_json",
                        timestamp_granularities=["word","segment"],
                        language="en",
                        temperature=0.0
                    )
                    # Convert response to dict to avoid serialization issues
                    return {
                        "text": response.text,
                        "words": [
                            {
                                "word": word["word"],
                                "start": word["start"],
                                "end": word["end"]
                            } for word in response.words
                        ]
                    }
            
            # Run the synchronous code in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, transcribe)
            
            print(f"Transcription took {time.time() - start_time:.2f} seconds")
            # print("GROQ ANSWER",response)
            # Process the response to include timestamps
            segments = []
            current_segment = {"text": "", "words": [], "start": None, "end": None}
            
            for word in response["words"]:
                # If this is the first word of a segment or current segment is too long
                if current_segment["text"] == "" or len(current_segment["text"].split()) > 30:
                    if current_segment["text"] != "":
                        segments.append(current_segment)
                    current_segment = {
                        "text": word["word"],
                        "words": [word],
                        "start": word["start"],
                        "end": word["end"]
                    }
                else:
                    current_segment["text"] += " " + word["word"]
                    current_segment["words"].append(word)
                    current_segment["end"] = word["end"]
            
            # Add the last segment
            if current_segment["text"] != "":
                segments.append(current_segment)
            
            # Format the transcription with timestamps
            formatted_transcription = ""
            for segment in segments:
                timestamp = f"[{segment['start']:.2f}s]"
                formatted_transcription += f"{timestamp} {segment['text']}\n"
            print("GROQ ANSWER",formatted_transcription)
            return formatted_transcription
            
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            raise 