import sys, os
sys.path.insert(0, "/app")
os.environ.setdefault("CHROMA_DIR", "/app/chroma_data")

from app.rag import retrieve_context

result = retrieve_context("what is AI", course_id="course-v1:ATU+AI1111+4_1")
print("Result:", result[:300] if result else "EMPTY")
