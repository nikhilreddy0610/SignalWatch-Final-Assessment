"""Retrieval-augmented generation over MongoDB Atlas Vector Search."""

import os

from dotenv import load_dotenv
from openai import OpenAI

from app.conversation_memory import ConversationMemory
from app.database import (
    CHUNKS_COLLECTION,
    CONVERSATIONS_COLLECTION,
    ensure_vector_index,
    get_database,
    upsert_chunks,
    vector_search,
)
from app.documents import get_chunks
from app.embeddings import embed_texts

load_dotenv()


def initialize() -> tuple[object, object]:
    database = get_database()
    chunks_collection = database[CHUNKS_COLLECTION]
    chunks = get_chunks()
    vectors = embed_texts([chunk["text"] for chunk in chunks], "document")
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk["embedding"] = vector
    count = upsert_chunks(chunks_collection, chunks)
    ensure_vector_index(chunks_collection)
    print(f"Seeded {len(chunks)} threat-intelligence chunks ({count} writes).")
    return chunks_collection, database[CONVERSATIONS_COLLECTION]


def answer_question(question: str, user_id: str, chunks_collection, conversations_collection) -> str:
    memory = ConversationMemory(conversations_collection, user_id)
    prior_messages = memory.recent_messages(limit=5)
    memory.save("user", question)
    query_vector = embed_texts([question], "query")[0]
    matches = vector_search(chunks_collection, query_vector, limit=3)
    if not matches:
        answer = "I could not find relevant threat-intelligence material for that question."
        memory.save("assistant", answer)
        return answer

    context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}" for item in matches
    )
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Answer using the supplied threat-intelligence context and recent conversation. "
                "Be concise, distinguish evidence from uncertainty, and say when the context "
                "does not support a claim. Cite source names in brackets."
            ),
        },
        *prior_messages,
        {
            "role": "user",
            "content": f"Retrieved context:\n{context}\n\nQuestion: {question}",
        },
    ]
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.2,
    )
    answer = response.choices[0].message.content
    if not answer:
        raise RuntimeError("The configured LLM returned an empty response.")

    memory.save("assistant", answer)
    return answer
