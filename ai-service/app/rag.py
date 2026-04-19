import os
import re
import hashlib
from typing import Optional

import chromadb
from chromadb.config import Settings
from google import genai
from google.genai import types
from pymongo import MongoClient

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MONGO_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://openedx:password@mongodb:27017"
)
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_data")

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        chroma = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = chroma.get_or_create_collection(
            name="course_content",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def get_embedding(text: str) -> list[float]:
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
    )
    return result.embeddings[0].values


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def index_course(course_id: str) -> int:
    mongo = MongoClient(MONGO_URL)
    db = mongo["edxapp"]
    collection = get_collection()
    total = 0

    structures = db["modulestore.structures"].find(
        {}, {"blocks": 1}
    ).limit(50)

    for structure in structures:
        for block_id, block in structure.get("blocks", {}).items():
            block_type = block.get("block_type", "")
            fields = block.get("fields", {})

            text = ""
            if block_type == "html":
                text = re.sub(r"<[^>]+>", " ", fields.get("data", ""))
            elif block_type == "problem":
                text = re.sub(r"<[^>]+>", " ", fields.get("data", ""))
            elif block_type == "video":
                text = fields.get("display_name", "")

            text = text.strip()
            if len(text) < 50:
                continue

            for i, chunk in enumerate(chunk_text(text)):
                doc_id = hashlib.md5(
                    f"{block_id}_{i}".encode()
                ).hexdigest()
                collection.upsert(
                    ids=[doc_id],
                    embeddings=[get_embedding(chunk)],
                    documents=[chunk],
                    metadatas=[{
                        "course_id": course_id,
                        "block_id": str(block_id),
                        "block_type": block_type,
                    }]
                )
                total += 1

    mongo.close()
    return total


def retrieve_context(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 4
) -> str:
    collection = get_collection()

    query_embedding = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
    ).embeddings[0].values

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"course_id": course_id} if course_id else None,
        include=["documents", "distances"]
    )

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    relevant = [
        doc for doc, dist in zip(docs, distances)
        if dist < 0.7
    ]

    return "\n\n---\n\n".join(relevant) if relevant else ""