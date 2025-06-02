from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.send_notification import send_whatsapp_message
from app.models.models import User, Chat, Analysis
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import update, select
import uuid
from app.config import OPENAI_API_KEY
from openai import AsyncOpenAI
import os

router = APIRouter()

class ChatMessage(BaseModel):
    user_id: uuid.UUID
    message: str
    media_id: uuid.UUID

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

@router.post("/chat")
async def chat_with_ai(data: ChatMessage, db: AsyncSession = Depends(get_db)):
    try:
        # Store user message in database
        user_chat = Chat(
            media_id=data.media_id,
            user_type="user",
            message=data.message
        )
        db.add(user_chat)
        await db.commit()

        # First check if we already have insights in chat
        query = select(Chat).where(
            Chat.media_id == data.media_id,
            Chat.user_type == "insights"
        )
        result = await db.execute(query)
        insights_chat = result.scalar_one_or_none()

        # If no insights found in chat, fetch from analysis and store
        if not insights_chat:
            analysis_query = select(Analysis).where(Analysis.media_id == data.media_id)
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()
            
            if analysis and analysis.meta:
                insights_chat = Chat(
                    media_id=data.media_id,
                    user_type="insights",
                    message=str(analysis.meta["summary"])
                )
                db.add(insights_chat)
                await db.commit()

        # Fetch all chat history including insights
        query = select(Chat).where(Chat.media_id == data.media_id).order_by(Chat.created)
        result = await db.execute(query)
        chat_history = result.scalars().all()

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": "You are a helpful assistant for minutes.ai who answers about insgits of a video always under in short under 50 words, introduce yourself Hi I'm minutes.ai assistant"}]
        
        # Add chat history including insights
        for chat in chat_history:
            if chat.user_type == "insights":
                messages.append({"role": "system", "content": f"Video insights: {chat.message}"})
            else:
                role = "assistant" if chat.user_type == "assistant" else "user"
                messages.append({"role": role, "content": chat.message})

        # Create chat completion with OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        # Extract the response text
        ai_response = response.choices[0].message.content

        # Store assistant response in database
        assistant_chat = Chat(
            media_id=data.media_id,
            user_type="assistant",
            message=ai_response
        )
        db.add(assistant_chat)
        await db.commit()

        return {
            "status": "success",
            "response": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
