from fastapi import APIRouter
from app.services.storage_service import StorageService
from fastapi import Depends
from app.database import get_db
from app.repositories.media_repository import MediaRepository
import uuid
from app.models.models import UploadStatus
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
router = APIRouter()


class UpdateMedia(BaseModel):
    media_id: uuid.UUID
    duration: Optional[int] = None
    upload_status: Optional[str] = None
    language: Optional[str] = None




@router.get("/generate-presigned-url")
async def get_presigned_url(file_name: str,file_type: str,user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    storage_service = StorageService()
    result = await storage_service.generate_presigned_url(
        file_name=file_name,
        file_type=file_type,
        user_id=user_id
        )
    media_repo = MediaRepository(db)
    media = await media_repo.create_media(
        user_id=user_id,
        type=file_type,
        url=result["file_url"],
        status=UploadStatus.PENDING
    )
    result["media_id"] = media.id
    return result


@router.post("/update-media-status")
async def update_media_status(
    update_media:  UpdateMedia,
    db: AsyncSession = Depends(get_db)
):
    media_repo = MediaRepository(db)
    updated_media = await media_repo.update_media(media_id=update_media.media_id,status=update_media.upload_status,duration=update_media.duration,language=update_media.language)
    if not updated_media:
        raise HTTPException(status_code=404, detail="Media not found")
    return updated_media



@router.get("/get-user-media")
async def get_user_media(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    media_repo = MediaRepository(db)
    media = await media_repo.get_user_media(user_id)
    return media

