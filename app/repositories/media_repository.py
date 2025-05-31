from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.models.models import Media, UploadStatus, MediaType
import uuid
from datetime import datetime

class MediaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_media(self, 
                         user_id: uuid.UUID,
                         url: str,
                         type: Optional[MediaType] = MediaType.VIDEO,
                         language: Optional[str] = None,
                         duration: Optional[int] = None,
                         status: Optional[UploadStatus] = None) -> Media:
        """Create a new media entry"""
        media = Media(
            user_id=user_id,
            type=type,
            url=url,
            language=language,
            duration=duration,
            upload_status=status
        )
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get_media_by_id(self, media_id: uuid.UUID) -> Optional[Media]:
        """Get media by ID"""
        query = select(Media).where(Media.id == media_id).options(selectinload(Media.user))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_media_status(self, media_id: uuid.UUID, status: UploadStatus) -> Optional[Media]:
        """Update media status"""
        query = (
            update(Media)
            .where(Media.id == media_id)
            .values(
                upload_status=status,
                updated_at=datetime.utcnow()
            )
            .returning(Media)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def update_media(self,
                         media_id: uuid.UUID,
                         duration: Optional[int] = None,
                         language: Optional[str] = None,
                         url: Optional[str] = None,
                         status: Optional[UploadStatus] = None) -> Optional[Media]:
        """Update media details"""
        update_data = {}
        if duration is not None:
            update_data["duration"] = duration
        if language is not None:
            update_data["language"] = language
        if url is not None:
            update_data["url"] = url
        if status is not None:
            update_data["upload_status"] = status
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            query = (
                update(Media)
                .where(Media.id == media_id)
                .values(**update_data)
                .returning(Media)
            )
            result = await self.session.execute(query)
            await self.session.commit()
            return result.scalar_one_or_none()
        return None

    async def get_user_media(self, user_id: uuid.UUID) -> List[Media]:
        """Get all media for a specific user"""
        query = select(Media).where(Media.user_id == user_id).order_by(Media.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_media(self, media_id: uuid.UUID) -> bool:
        """Delete media by ID"""
        media = await self.get_media_by_id(media_id)
        if media:
            await self.session.delete(media)
            await self.session.commit()
            return True
        return False 