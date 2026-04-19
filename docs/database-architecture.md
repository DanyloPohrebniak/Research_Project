# Database Architecture

## Components

### PostgreSQL
- **Purpose:** Stores chat history
- **Container:** `chatbot-db` (postgres:16-alpine)
- **Connection:** SQLAlchemy async via `asyncpg`
- **Schema:** Auto-created on service startup via `Base.metadata.create_all`

### ChromaDB
- **Purpose:** Vector store for course content (RAG)
- **Type:** Persistent local instance
- **Location:** `/data/chroma` (Docker volume)
- **Embedding model:** Gemini `text-embedding-004` (768 dimensions)
- **Similarity metric:** Cosine distance

### MongoDB (read-only)
- **Purpose:** Source of Open edX course content
- **Access:** Read-only via `pymongo`
- **Collections read:**
  - `modulestore.structures` — XBlock content

## Migration Strategy
No external migration tool is used.
Tables are created automatically on service startup:
```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

## Connection Parameters
All configured via environment variables:
| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://chatbot:chatbot@chatbot-db:5432/chatbot` |
| `MONGODB_URL` | `mongodb://openedx:password@mongodb:27017` |
| `CHROMA_DIR` | `/data/chroma` |
| `GEMINI_API_KEY` | — (required) |