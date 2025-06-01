import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

def convert_video_to_audio(video_path, audio_path):
    """Convert video to audio using FFmpeg."""
    try:
        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path]
        subprocess.run(command, check=True)
        print(f"Audio saved to {audio_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting video to audio: {e}")

async def convert_video_to_audio_async(video_path, audio_path, executor=None):
    """Convert video to audio using FFmpeg asynchronously."""
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=1)
    
    def convert():
        try:
            command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Audio saved to {audio_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error converting video to audio: {e}")
            print(f"stderr: {e.stderr}")
            raise
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, convert)
