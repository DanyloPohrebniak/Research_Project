import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from google import genai
from google.genai import types


from app.db import get_db, ChatMessage
from app.rag import retrieve_context
from app.auth import get_current_user

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter()

SYSTEM_PROMPT = """You are an AI learning assistant integrated into an Open edX course platform.
Your role is to help students understand course materials, answer questions, and guide their learning.

Guidelines:
- Answer questions based on the course content provided in the context
- If the context does not contain relevant information, say so and provide general help
- Be encouraging and supportive
- Keep answers concise but complete
- Use examples when helpful
"""


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "anonymous"
    course_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


async def get_history(
    session_id: str,
    db: AsyncSession,
    limit: int = 10
) -> list[dict]:
    """Fetch recent chat history for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {"role": m.role, "parts": [m.content]}
        for m in reversed(messages)
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session_id = request.session_id or str(uuid.uuid4())

    # Retrieve relevant course content
    context = retrieve_context(request.message, course_id=request.course_id)

    # Build system prompt with context
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n=== COURSE CONTENT ===\n{context}\n=== END ==="

    # Get conversation history
    history = await get_history(session_id, db)

    # Call Gemini
    try:
        response = gemini.models.generate_content(
            model="gemini-1.5-flash", # version of model
            contents=[
                *[f"{m['role']}: {m['parts'][0]}" for m in history],
                f"user: {request.message}"
            ],
            config=types.GenerateContentConfig(
                system_instruction=system,
            )
        )
        reply = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to database
    db.add(ChatMessage(
        session_id=session_id,
        user_id=request.user_id,
        course_id=request.course_id,
        role="user",
        content=request.message,
    ))
    db.add(ChatMessage(
        session_id=session_id,
        user_id=request.user_id,
        course_id=request.course_id,
        role="model",
        content=reply,
    ))
    await db.commit()

    return ChatResponse(reply=reply, session_id=session_id)


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]