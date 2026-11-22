"""Per-user conversation history stored in MongoDB."""

from datetime import datetime, timezone


class ConversationMemory:
    def __init__(self, collection, user_id: str):
        self.collection = collection
        self.user_id = user_id
        self.collection.create_index([("user_id", 1), ("timestamp", -1)])

    def recent_messages(self, limit: int = 5) -> list[dict[str, str]]:
        cursor = (
            self.collection.find(
                {"user_id": self.user_id},
                {"_id": 0, "role": 1, "content": 1, "timestamp": 1},
            )
            .sort([("timestamp", -1), ("_id", -1)])
            .limit(limit)
        )
        messages = list(cursor)
        return [{"role": item["role"], "content": item["content"]} for item in reversed(messages)]

    def save(self, role: str, content: str) -> None:
        self.collection.insert_one(
            {
                "user_id": self.user_id,
                "timestamp": datetime.now(timezone.utc),
                "role": role,
                "content": content,
            }
        )
