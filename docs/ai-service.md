# AI Service Architecture

## Overview
FastAPI-based microservice that provides AI assistant functionality
for the Open edX VLE platform.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Send message, get AI reply |
| GET | `/api/v1/history/{session_id}` | Get chat history |

## Request/Response

### POST /api/v1/chat
Request:
```json
{
  "message": "What is machine learning?",
  "session_id": "optional-uuid",
  "user_id": "student123",
  "course_id": "course-v1:Org+Course+Run"
}
```
Response:
```json
{
  "reply": "Machine learning is...",
  "session_id": "uuid"
}
```

## Components
- **FastAPI** — REST API framework
- **Gemini 2.0 Flash** — Language model (Google AI Studio)
- **ChromaDB** — Vector store for course content
- **PostgreSQL** — Chat history storage
- **SQLAlchemy async** — ORM layer

## RAG Pipeline
1. User sends message
2. Message embedded via `gemini-embedding-001`
3. ChromaDB retrieves top-4 relevant course chunks
4. Context injected into Gemini system prompt
5. Gemini generates response
6. Message + response saved to PostgreSQL