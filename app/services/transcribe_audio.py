import os
import requests
import httpx
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from backend.app.config import DEEPGRAM_API_KEY

def transcribe_audio(audio_path):
    """Transcribe an audio file using Deepgram."""
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        # Read the audio file
        with open(audio_path, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Deepgram transcription options
        options = PrerecordedOptions(
            model="nova-2-general",
            smart_format=True,
            utterances=True,
            punctuate=True,
            diarize=True,
            language='hi'
        )

        # Transcribe audio
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options, timeout=httpx.Timeout(300.0, connect=10.0))

        # Extract transcription
        transcription = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        print("Transcription successful")

        return transcription

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None



