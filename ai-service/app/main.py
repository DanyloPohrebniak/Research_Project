import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db import init_db
from app.chat import router as chat_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vle-ai")

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

app.include_router(chat_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.on_event("startup")
async def startup():
    logger.info("Starting VLE AI Assistant...")
    await init_db()
    logger.info("Database initialized successfully")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down VLE AI Assistant...")


@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}