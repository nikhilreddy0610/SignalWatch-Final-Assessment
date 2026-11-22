"""Interactive command-line RAG demonstration."""

import os

from app.rag_pipeline import answer_question, initialize


def main() -> None:
    user_id = os.getenv("RAG_USER_ID", "demo-user")
    chunks, conversations = initialize()
    print("Lab 17 Threat Intelligence RAG (type 'exit' to quit)")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        try:
            answer = answer_question(question, user_id, chunks, conversations)
        except Exception as exc:
            print(f"Request failed: {exc}")
            continue
        print(f"\nAssistant: {answer}")


if __name__ == "__main__":
    main()
