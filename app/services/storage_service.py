from typing import Dict
from datetime import datetime
from fastapi import HTTPException
import aiohttp
import os
from app.services.database import get_db
class StorageService:
    def __init__(self):
        self.supabase = get_db()

    async def generate_presigned_url(self, file_name: str, file_type: str, user_id: str) -> Dict:
        """Generate a pre-signed URL for file upload

        Args:
            file_name (str): Original name of the file
            file_type (str): MIME type of the file
            user_id (str): ID of the user uploading the file

        Returns:
            Dict: Dictionary containing upload_url for file upload and file_url for future access
        """
        try:
            bucket_name = 'recordings'
            file_path = f"{user_id}/{datetime.now().timestamp()}_{file_name}"
            
            # Generate pre-signed URL for upload
            signed_url_response = self.supabase.storage.from_(bucket_name).create_signed_upload_url(
                file_path
            )
            print(signed_url_response)
            # Get the public URL that will be accessible after upload
            public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)
            
            return {
                'upload_url': signed_url_response['signed_url'],
                'file_url': public_url,
                'file_path': file_path
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating pre-signed URL: {str(e)}")

    async def download_video(self, file_path: str, local_path: str) -> str:
        """Download a video file from Supabase storage.
        
        Args:
            file_path (str): Path of the file in the storage bucket
            local_path (str): Local path where the file should be saved
            
        Returns:
            str: Path to the downloaded file
        """
        try:
            bucket_name = 'ai_media'
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get signed URL for downloading
            signed_url = self.supabase.storage.from_(bucket_name).create_signed_url(
                file_path,
                3600  # URL valid for 1 hour
            )
            
            # Download the file using the signed URL
            async with aiohttp.ClientSession() as session:
                async with session.get(signed_url['signedURL']) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)  # Read in chunks
                                if not chunk:
                                    break
                                f.write(chunk)
                        return local_path
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Failed to download file: HTTP {response.status}"
                        )
                        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}") 