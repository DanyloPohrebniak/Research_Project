import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db

app = FastAPI(
    title="VLE AI Assistant",
    version="1.0.0",
    description="AI-powered learning assistant for Open edX"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}