import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from groq import Groq

from app.db import get_db, ChatMessage
from app.rag import retrieve_context
from app.auth import get_current_user

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
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {"role": m.role if m.role != "model" else "assistant",
         "content": m.content}
        for m in reversed(messages)
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session_id = request.session_id or str(uuid.uuid4())

    # 1. Retrieve relevant course content
    context = retrieve_context(request.message, course_id=request.course_id)

    # 2. Build system prompt with context
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n=== COURSE CONTENT ===\n{context}\n=== END ==="

    # 3. Get conversation history
    history = await get_history(session_id, db)

    # 4. Call Groq
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        messages = [
            {"role": "system", "content": system},
            *history,
            {"role": "user", "content": request.message}
        ]
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Save to database
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