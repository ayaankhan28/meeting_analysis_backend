import subprocess

def convert_video_to_audio(video_path, audio_path):
    """Convert video to audio using FFmpeg."""
    try:
        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path]
        subprocess.run(command, check=True)
        print(f"Audio saved to {audio_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting video to audio: {e}")
