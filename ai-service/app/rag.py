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

os.environ["ANONYMIZED_TELEMETRY"] = "false"

MONGO_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://openedx:password@mongodb:27017"
)
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_data")

_collection = None


def _normalize_course_id(course_id: str) -> str:
    """Canonical form: course-v1:ORG+COURSE+RUN (URL-decoded spaces → +)."""
    if not course_id:
        return course_id
    prefix = "course-v1:"
    if course_id.startswith(prefix):
        return prefix + course_id[len(prefix):].replace(" ", "+")
    return course_id.replace(" ", "+")


def get_collection():
    global _collection
    if _collection is None:
        chroma = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
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
    course_id = _normalize_course_id(course_id)
    mongo = MongoClient(MONGO_URL)
    db = mongo["openedx"]
    collection = get_collection()
    total = 0

    # Parse "course-v1:ORG+COURSE+RUN"
    try:
        parts = course_id.replace("course-v1:", "").split("+")
        org, course, run = parts[0], parts[1], parts[2]
    except (IndexError, ValueError):
        mongo.close()
        return 0

    # Find the published structure for this specific course
    active = db["modulestore.active_versions"].find_one(
        {"org": org, "course": course, "run": run}
    )
    if not active:
        mongo.close()
        return 0

    structure_id = active.get("versions", {}).get("published-branch")
    if not structure_id:
        mongo.close()
        return 0

    structure = db["modulestore.structures"].find_one({"_id": structure_id})
    if not structure:
        mongo.close()
        return 0

    blocks = structure.get("blocks", {})
    if isinstance(blocks, dict):
        blocks_list = list(blocks.values())
    else:
        blocks_list = blocks

    for block in blocks_list:
        block_type = block.get("block_type", "")
        if block_type not in ["html", "problem", "video"]:
            continue

        block_id = str(block.get("block_id", block.get("_id", "")))
        fields = block.get("fields", {})

        # Content lives in definitions; structure-side fields only carry metadata
        if block.get("definition"):
            definition = db["modulestore.definitions"].find_one(
                {"_id": block["definition"]},
                {"fields": 1}
            )
            if definition and definition.get("fields"):
                fields = definition["fields"]

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
                    "block_id": block_id,
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
    course_id = _normalize_course_id(course_id) if course_id else course_id
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