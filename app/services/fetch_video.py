from app.services.storage_service import StorageService

async def download_video(storage_service: StorageService, "file_path": str, local_path: str) -> str:

    try:
        downloaded_path = await storage_service.download_video(file_path, local_path)
        print(f"Video downloaded to {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        raise
