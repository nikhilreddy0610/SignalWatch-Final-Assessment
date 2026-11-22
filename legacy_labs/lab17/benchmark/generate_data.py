"""Create a deterministic, topic-structured 5,000-vector benchmark corpus."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from pymongo import UpdateOne

from benchmark.settings import DATA_PATH, DIMENSIONS, DOCUMENT_COUNT, TOPICS


def _token_vector(token: str) -> np.ndarray:
    seed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "little")
    return np.random.default_rng(seed).standard_normal(DIMENSIONS, dtype=np.float32)


def create_corpus(seed: int = 17) -> tuple[list[dict[str, str]], np.ndarray]:
    rng = np.random.default_rng(seed)
    docs = []
    vectors = np.empty((DOCUMENT_COUNT, DIMENSIONS), dtype=np.float32)
    topic_vectors = {
        topic: np.mean([_token_vector(word) for word in topic.split()], axis=0)
        for topic in TOPICS
    }
    for i in range(DOCUMENT_COUNT):
        topic = TOPICS[i % len(TOPICS)]
        words = topic.split()
        phrase = " ".join(words + ["threat", "analysis", "report", f"record-{i}"])
        vector = topic_vectors[topic] + rng.normal(0, 0.30, DIMENSIONS).astype(np.float32)
        vector /= np.linalg.norm(vector)
        docs.append({"_id": f"sample-{i:05d}", "text": phrase, "source": topic})
        vectors[i] = vector
    return docs, vectors


def save_corpus(docs: list[dict[str, str]], vectors: np.ndarray) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DATA_PATH, vectors=vectors)
    with DATA_PATH.with_suffix(".json").open("w", encoding="utf-8") as handle:
        json.dump(docs, handle)


def store_in_mongodb(docs: list[dict[str, str]], vectors: np.ndarray) -> None:
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("MongoDB storage skipped: set MONGO_URI to upload benchmark vectors.")
        return
    from pymongo import MongoClient

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    collection = client[os.getenv("MONGO_DATABASE", "lab17")]["benchmark_vectors"]
    operations = []
    for doc, vector in zip(docs, vectors, strict=True):
        document = {**doc, "embedding": vector.tolist()}
        operations.append(UpdateOne({"_id": doc["_id"]}, {"$set": document}, upsert=True))
    for offset in range(0, len(operations), 500):
        collection.bulk_write(operations[offset : offset + 500], ordered=False)
    print(f"Stored {len(docs)} benchmark vectors in MongoDB.")


def main() -> None:
    docs, vectors = create_corpus()
    save_corpus(docs, vectors)
    store_in_mongodb(docs, vectors)
    print(f"Generated {len(docs)} documents with {vectors.shape[1]} dimensions at {DATA_PATH}.")


if __name__ == "__main__":
    main()
