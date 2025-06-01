from fastapi import APIRouter, HTTPException
from app.services.storage_service import StorageService
from fastapi import Depends
from app.database import get_db
from app.repositories.media_repository import MediaRepository
import uuid
from app.models.models import UploadStatus, User
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func, or_
from datetime import datetime

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
        url=result["file_path"],
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
    media_list = await media_repo.get_user_media(user_id)
    
    formatted_media = []
    for media in media_list:
        # Get the latest analysis status if any analysis exists
        analysis_status = None
        if media.analysis:
            latest_analysis = max(media.analysis, key=lambda x: x.created_at)
            analysis_status = latest_analysis.status
            
        formatted_media.append({
            "media_id": str(media.id),
            "file_type": media.type,
            "duration": media.duration,
            "language": media.language,
            "thumbnail": media.media_thumbnail,
            "created_at": media.created_at.isoformat(),
            "upload_status": media.upload_status,
            "analysis_status": analysis_status,
            "url": media.url
        })
    
    return formatted_media


@router.get("/process-media")
async def process_media(media_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    media_repo = MediaRepository(db)
    media = await media_repo.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media

class UserSync(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

@router.post("/sync_user")
async def sync_user(user_data: UserSync, db: AsyncSession = Depends(get_db)):
    """
    Sync user data with the database. This endpoint is called when a user logs in or signs up.
    It ensures the user data is up to date in our database.
    """
    try:
        print("Received user data:", user_data)
        
        if not user_data.id or not user_data.email:
            raise HTTPException(status_code=400, detail="Missing required user data")
        
        try:
            user_uuid = uuid.UUID(user_data.id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
            
        # Check if user exists by either ID or email
        stmt = select(User).where(
            or_(
                User.id == user_uuid,
                User.email == user_data.email
            )
        )
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        current_time = datetime.utcnow()
        
        if existing_user:
            # Update existing user
            existing_user.id = user_uuid  # Ensure ID is updated if found by email
            existing_user.email = user_data.email
            existing_user.full_name = user_data.name
            existing_user.avatar_url = user_data.avatar_url
            existing_user.last_login = current_time
            user = existing_user
        else:
            # Create new user
            user = User(
                id=user_uuid,
                email=user_data.email,
                full_name=user_data.name,
                avatar_url=user_data.avatar_url,
                last_login=current_time,
                created_at=current_time
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        
        return {
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.full_name,
                "avatar_url": user.avatar_url,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
        
    except Exception as e:
        await db.rollback()
        print("Error in sync_user:", str(e))
        raise HTTPException(status_code=500, detail=str(e))