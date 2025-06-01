from typing import Dict
from datetime import datetime
from fastapi import HTTPException
import aiohttp
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.database import get_db

class StorageService:
    def __init__(self):
        self.supabase = get_db()
        self.executor = ThreadPoolExecutor(max_workers=2)

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
            bucket_name = 'recordings'
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get signed URL for downloading
            print("File path 1", file_path)
            signed_url = self.supabase.storage.from_(bucket_name).create_signed_url(
                file_path,
                3600  # URL valid for 1 hour
            )
            print("Signed URL 1", signed_url)
            
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

    async def upload_file(self, file_path: str, destination_path: str, content_type: str) -> Dict:
        """Upload a file to Supabase storage asynchronously.
        
        Args:
            file_path (str): Local path of the file to upload
            destination_path (str): Path where the file should be stored in the bucket
            content_type (str): MIME type of the file
            
        Returns:
            Dict: Dictionary containing the file URL and other upload details
        """
        try:
            bucket_name = 'recordings'
            
            # Upload the file to Supabase storage in a thread pool to avoid blocking
            def upload_sync():
                with open(file_path, 'rb') as f:
                    self.supabase.storage.from_(bucket_name).upload(
                        destination_path,
                        f,
                        file_options={"content-type": content_type}
                    )
                return True
            
            # Run the upload in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, upload_sync)
            
            # Get the public URL of the uploaded file
            file_url = self.supabase.storage.from_(bucket_name).get_public_url(destination_path)
            
            return {
                'file_url': file_url,
                'file_path': destination_path
            }
                        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}") 