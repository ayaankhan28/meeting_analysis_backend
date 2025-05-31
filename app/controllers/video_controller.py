# video_controller.py

from fastapi import APIRouter
from backend.app.services.fetch_video import download_video_from_s3
from backend.app.services.video_to_audio import convert_video_to_audio
from backend.app.services.transcribe_audio import transcribe_audio
from backend.app.services.summarize_text import summarize_text
from backend.app.services.db_utils import save_to_db
from backend.app.services.send_notification import send_whatsapp_message
from pydantic import BaseModel
router = APIRouter()
class VideoProcessRequest(BaseModel):
    video_key: str
    phone_number: str
@router.post("/process_video/")
def process_video(request: VideoProcessRequest):
    print(f"Processing video: {request.video_key}")
    video_path = f"{request.video_key.split('/')[-1]}"
    print(f"Video path: {video_path}")
    audio_path = video_path.replace(".mp4", ".mp3")

    print(f"Audio path: {audio_path}")

    download_video_from_s3(request.video_key, video_path)
    print(f"Video downloaded: {video_path}")
    convert_video_to_audio(video_path, audio_path)

    print(f"Audio converted: {audio_path}")

    transcription = transcribe_audio(audio_path)

    print(f"Transcription: {transcription}")
    summary, key_points = summarize_text(transcription)

    print(f"Summary: {summary}")

    save_to_db(request.video_key, audio_path, transcription, summary, key_points)

    send_whatsapp_message(summary, request.phone_number)

    print(f"Video saved to database: {request.video_key}")
    # return "done"
    return {"message": "Processing completed", "summary": summary, "key_points": key_points}

