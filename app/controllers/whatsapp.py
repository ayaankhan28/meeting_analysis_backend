from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.send_notification import send_whatsapp_message
from app.models.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import update

router = APIRouter()

class WhatsAppConnect(BaseModel):
    phone_number: str
    user_id: str

class WhatsAppDisconnect(BaseModel):
    user_id: str

@router.post("/connect")
async def connect_whatsapp(data: WhatsAppConnect, db: AsyncSession = Depends(get_db)):
    try:
        # Update user's phone number in database
        stmt = update(User).where(User.id == data.user_id).values(
            phone_number=data.phone_number,
            notification_active=True
        )
        await db.execute(stmt)
        await db.commit()

        # Send welcome message
        welcome_message = "Welcome to MeetingIQ Pro! 🎉\nYou'll receive notifications here when your meeting analysis is complete."
        send_whatsapp_message(welcome_message, data.phone_number)
        
        return {"status": "success", "message": "WhatsApp connection established"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect_whatsapp(data: WhatsAppDisconnect, db: AsyncSession = Depends(get_db)):
    try:
        # Update user's notification status in database
        stmt = update(User).where(User.id == data.user_id).values(
            notification_active=False
        )
        await db.execute(stmt)
        await db.commit()
        
        return {"status": "success", "message": "WhatsApp notifications disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 