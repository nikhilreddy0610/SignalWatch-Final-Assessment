"""MongoDB Atlas persistence and Atlas Vector Search operations."""

import os
import time

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from app.embeddings import DIMENSIONS

load_dotenv()

DATABASE_NAME = os.getenv("MONGO_DATABASE", "lab17")
CHUNKS_COLLECTION = os.getenv("MONGO_CHUNKS_COLLECTION", "threat_chunks")
CONVERSATIONS_COLLECTION = os.getenv("MONGO_CONVERSATIONS_COLLECTION", "conversations")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "threat_vector_index")


def get_database():
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGO_URI is required. Add your Atlas connection string to .env.")
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    return client[DATABASE_NAME]


def ensure_vector_index(collection, timeout_seconds: int = 120) -> None:
    definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": DIMENSIONS,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "source"},
        ]
    }
    indexes = list(collection.list_search_indexes())
    if not any(index.get("name") == VECTOR_INDEX_NAME for index in indexes):
        collection.create_search_index(
            model={
                "name": VECTOR_INDEX_NAME,
                "type": "vectorSearch",
                "definition": definition,
            }
        )
        print(f"Requested Atlas Vector Search index creation: {VECTOR_INDEX_NAME}")

    deadline = time.monotonic() + timeout_seconds
    while True:
        index = next(
            (
                item
                for item in collection.list_search_indexes()
                if item.get("name") == VECTOR_INDEX_NAME
            ),
            None,
        )
        if index and index.get("status") == "READY":
            return
        if index and index.get("status") == "FAILED":
            raise RuntimeError(f"Atlas Vector Search index {VECTOR_INDEX_NAME} failed to build.")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Atlas Vector Search index {VECTOR_INDEX_NAME} did not become ready.")
        time.sleep(2)


def upsert_chunks(collection, chunks: list[dict]) -> int:
    operations = [
        UpdateOne(
            {"source": chunk["source"], "text": chunk["text"]},
            {"$set": chunk},
            upsert=True,
        )
        for chunk in chunks
    ]
    if not operations:
        return 0
    result = collection.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count


def vector_search(collection, query_vector: list[float], limit: int = 3) -> list[dict]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": max(30, limit * 10),
                "limit": limit,
            }
        },
        {
            "$project": {
                "_id": 0,
                "text": 1,
                "source": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return list(collection.aggregate(pipeline))
