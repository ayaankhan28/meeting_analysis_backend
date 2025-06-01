import os
import json
import cv2
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Media, Analysis, AnalysisStatus
from app.services.storage_service import StorageService
from app.services.video_to_audio import convert_video_to_audio_async
from app.services.transcription_service import TranscriptionService
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY
import tempfile
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

class MediaAnalysisService:
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service
        self.transcription_service = TranscriptionService()
        self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def process_media(self, media_id: str) -> Dict:
        """Process a media file (video or audio) and generate analysis."""
        analysis = None
        try:
            print(f"Starting analysis for media_id: {media_id}")
            
            # Get media details first
            query = select(Media).where(Media.id == media_id)
            result = await self.db.execute(query)
            media = result.scalar_one_or_none()
            
            if not media:
                raise ValueError("Media not found")
            
            print(f"Media found: {media.type}")
            
            # Update analysis record to processing if it exists, otherwise it should already be created
            analysis_query = select(Analysis).where(
                Analysis.media_id == media_id,
                Analysis.status == AnalysisStatus.PROCESSING
            )
            analysis_result = await self.db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()
            
            if not analysis:
                print("No processing analysis found, this shouldn't happen")
                return {"error": "No analysis record found"}
                
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Using temp directory: {temp_dir}")
                
                # Download the media file
                media_extension = 'mp4' if media.type == 'video' else 'mp3'
                media_path = os.path.join(temp_dir, f"media_file.{media_extension}")
                
                print(f"Downloading media to: {media_path}")
                await self.storage_service.download_video(media.url, media_path)
                
                # Convert video to audio if needed (run in thread pool to avoid blocking)
                audio_path = os.path.join(temp_dir, "audio.mp3")
                if media.type == 'video':
                    print("Converting video to audio...")
                    await convert_video_to_audio_async(media_path, audio_path, self.executor)
                else:
                    audio_path = media_path
                
                print("Starting transcription...")
                # Transcribe using Groq's Whisper model
                transcription = await self.transcription_service.transcribe_audio(audio_path)
                
                print("Generating analysis...")
                # Generate analysis using OpenAI (now async)
                analysis_result = await self._generate_analysis(transcription)
                
                # If video, extract frames for each chapter (run in thread pool)
                if media.type == 'video':
                    print("Extracting chapter thumbnails...")
                    analysis_result = await self._add_chapter_thumbnails_async(media_path, analysis_result)
                else:
                    # For audio files, set thumbnail_url to None
                    for chapter in analysis_result.get('chapters', []):
                        chapter['thumbnail_url'] = None
                
                # Update analysis record
                analysis.status = AnalysisStatus.DONE
                analysis.meta = analysis_result
                await self.db.commit()
                
                print(f"Analysis completed successfully for media_id: {media_id}")
                return analysis_result
                
        except Exception as e:
            print(f"Analysis failed for media_id {media_id}: {str(e)}")
            # Update analysis record with error
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.meta = {'error': str(e)}
                await self.db.commit()
            raise
    
    async def _generate_analysis(self, transcription: str) -> Dict:
        """Generate structured analysis using OpenAI."""
        print("Generating analysis with OpenAI...")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Analyze the transcription and return a JSON object with the following fields:\n"
                                  "- video_title: A concise, descriptive title for the content\n"
                                  "- description: A brief overview of the content\n"
                                  "- chapters: An array of chapters, each containing:\n"
                                  "  - chapter_title: A concise title for the chapter\n"
                                  "  - timestamp: The timestamp in [XX.XXs] format where the chapter starts\n"
                                  "  - content: A detailed summary of what was discussed\n"
                                  "- final_decision: The main conclusion or decision reached\n"
                                  "- action_items: A list of concrete next steps or tasks\n"
                                  "- summary: A comprehensive summary of the entire content\n\n"
                                  "Important: Preserve the exact timestamps from the transcription."
                    },
                    {
                        "role": "user",
                        "content": transcription
                    }
                ],
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            print("OpenAI analysis completed successfully")
            return analysis
        except Exception as e:
            print(f"Error in OpenAI analysis: {str(e)}")
            raise
        
    async def _add_chapter_thumbnails_async(self, video_path: str, analysis: Dict) -> Dict:
        """Extract and upload thumbnails for each chapter using async processing."""
        def extract_frame(video_path: str, timestamp: float, output_path: str) -> bool:
            """Extract a single frame at timestamp."""
            video = cv2.VideoCapture(video_path)
            try:
                video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                success, frame = video.read()
                if success:
                    cv2.imwrite(output_path, frame)
                    return True
                return False
            finally:
                video.release()
        
        loop = asyncio.get_event_loop()
        
        for i, chapter in enumerate(analysis.get('chapters', [])):
            try:
                # Parse timestamp (assuming format "[XX.XXs]")
                timestamp_str = chapter['timestamp'].strip('[]s')
                timestamp = float(timestamp_str)
                
                # Create unique frame path
                frame_path = f"temp_frame_{i}_{timestamp}.jpg"
                
                # Extract frame in thread pool
                success = await loop.run_in_executor(
                    self.executor, 
                    extract_frame, 
                    video_path, 
                    timestamp, 
                    frame_path
                )
                
                if success:
                    # Upload frame to storage
                    frame_url = await self._upload_frame(frame_path)
                    chapter['thumbnail_url'] = frame_url
                    
                    # Clean up temp file
                    try:
                        os.remove(frame_path)
                    except OSError:
                        pass
                else:
                    chapter['thumbnail_url'] = None
                    
            except Exception as e:
                print(f"Error extracting thumbnail for chapter {i}: {str(e)}")
                chapter['thumbnail_url'] = None
                
        return analysis
        
    async def _upload_frame(self, frame_path: str) -> str:
        """Upload a frame to storage and return its URL."""
        try:
            # Generate a unique filename for the frame
            filename = f"frames/{uuid.uuid4()}.jpg"
            
            # Upload to storage using StorageService
            upload_result = await self.storage_service.upload_file(
                file_path=frame_path,
                destination_path=filename,
                content_type='image/jpeg'
            )
            
            return upload_result['file_url']
            
        except Exception as e:
            print(f"Error uploading frame: {str(e)}")
            return None 