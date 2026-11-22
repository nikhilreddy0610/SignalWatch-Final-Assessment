"""Voyage AI embedding client."""

import os

import voyageai
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("VOYAGE_MODEL", "voyage-3-lite")
DIMENSIONS = 512


def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError("VOYAGE_API_KEY is required. Add it to your local .env file.")
    client = voyageai.Client(api_key=api_key)
    result = client.embed(texts, model=MODEL, input_type=input_type)
    return result.embeddings
