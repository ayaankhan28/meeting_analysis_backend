from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.services.media_analysis_service import MediaAnalysisService
from app.services.storage_service import StorageService
from app.models.models import Analysis, AnalysisStatus
from typing import Dict, Optional
from fastapi import BackgroundTasks
import uuid
import asyncio

router = APIRouter()

async def create_background_analysis_task(media_id: str):
    """
    Create and execute analysis task with a fresh database session.
    This prevents blocking the main API session.
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            storage_service = StorageService()
            analysis_service = MediaAnalysisService(db, storage_service)
            await analysis_service.process_media(media_id)
        except Exception as e:
            print(f"Background analysis failed for media {media_id}: {str(e)}")
            # Update analysis status to failed in case of error
            try:
                analysis_query = select(Analysis).where(
                    Analysis.media_id == media_id,
                    Analysis.status == AnalysisStatus.PROCESSING
                )
                result = await db.execute(analysis_query)
                analysis = result.scalar_one_or_none()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.meta = {'error': str(e)}
                    await db.commit()
            except Exception as commit_error:
                print(f"Failed to update analysis status: {str(commit_error)}")

@router.post("/media/{media_id}/analyze")
async def analyze_media(
    media_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Trigger analysis for a media file.
    """
    try:
        # Check if analysis already exists (quick check)
        query = select(Analysis).where(
            Analysis.media_id == media_id,
            Analysis.status.in_([AnalysisStatus.PROCESSING, AnalysisStatus.DONE])
        )
        result = await db.execute(query)
        existing_analysis = result.scalar_one_or_none()
        
        if existing_analysis:
            if existing_analysis.status == AnalysisStatus.PROCESSING:
                return {
                    "status": "processing",
                    "message": "Analysis is already in progress",
                    "analysis_id": str(existing_analysis.id)
                }
            else:
                return {
                    "status": "completed",
                    "message": "Analysis already exists for this media",
                    "analysis_id": str(existing_analysis.id)
                }
        
        # Create initial analysis record with PROCESSING status
        analysis = Analysis(
            media_id=media_id,
            status=AnalysisStatus.PROCESSING
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Start the background task with asyncio.create_task for better async handling
        asyncio.create_task(create_background_analysis_task(str(media_id)))
        
        return {
            "status": "processing",
            "message": "Analysis started in background",
            "analysis_id": str(analysis.id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{media_id}/analysis/status")
async def get_analysis_status(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get the current status of analysis for a media file.
    """
    try:
        query = select(Analysis).where(Analysis.media_id == media_id).order_by(Analysis.created_at.desc())
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return {
                "status": "not_found",
                "message": "No analysis found for this media"
            }
            
        return {
            "status": "success",
            "data": {
                "analysis_id": str(analysis.id),
                "status": analysis.status,
                "created_at": analysis.created_at,
                "updated_at": analysis.updated_at,
                "has_results": analysis.meta is not None and analysis.status == AnalysisStatus.DONE
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{media_id}/analysis")
async def get_media_analysis(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get the analysis results for a media file.
    """
    try:
        # Query the analysis table using select() - get the latest analysis
        query = select(Analysis).where(
            Analysis.media_id == media_id
        ).order_by(Analysis.created_at.desc())
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.status == AnalysisStatus.PROCESSING:
            return {
                "status": "processing",
                "message": "Analysis is still in progress",
                "data": {
                    "analysis_id": str(analysis.id),
                    "status": analysis.status,
                    "created_at": analysis.created_at,
                    "updated_at": analysis.updated_at
                }
            }
        elif analysis.status == AnalysisStatus.FAILED:
            return {
                "status": "failed",
                "message": "Analysis failed",
                "data": {
                    "analysis_id": str(analysis.id),
                    "status": analysis.status,
                    "error": analysis.meta.get('error', 'Unknown error') if analysis.meta else 'Unknown error',
                    "created_at": analysis.created_at,
                    "updated_at": analysis.updated_at
                }
            }
        elif analysis.status == AnalysisStatus.DONE:
            return {
                "status": "success",
                "data": {
                    "analysis_id": str(analysis.id),
                    "status": analysis.status,
                    "meta": analysis.meta,
                    "created_at": analysis.created_at,
                    "updated_at": analysis.updated_at
                }
            }
        else:
            return {
                "status": "unknown",
                "message": f"Unknown analysis status: {analysis.status}",
                "data": {
                    "analysis_id": str(analysis.id),
                    "status": analysis.status,
                    "created_at": analysis.created_at,
                    "updated_at": analysis.updated_at
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 