# Database Architecture

## Overview
The AI service uses two databases:
- **PostgreSQL** — stores chat sessions and messages
- **ChromaDB** — vector store for course content embeddings

## PostgreSQL Schema

### Table: `chat_messages`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment |
| session_id | VARCHAR(64) | Groups messages into conversations |
| user_id | VARCHAR(64) | Open edX user identifier |
| course_id | VARCHAR(255) | Optional course context |
| role | VARCHAR(16) | `user` or `model` |
| content | TEXT | Message content |
| created_at | DATETIME | Timestamp |

## ChromaDB Collection: `course_content`
| Field | Description |
|-------|-------------|
| id | MD5 hash of block_id + chunk index |
| embedding | 768-dim vector (Gemini text-embedding-004) |
| document | Text chunk from course content |
| metadata | course_id, block_id, block_type |

## Data Flow
```
Open edX MongoDB → RAG pipeline → ChromaDB (embeddings)
                                        ↓
User message → FastAPI → Gemini API → Response
                    ↓
              PostgreSQL (chat history)
```