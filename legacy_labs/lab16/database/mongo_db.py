from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.configuration import MONGO_COLLECTION, MONGO_DATABASE, MONGO_URI


class MongoDatabase:
    def __init__(self, uri: str = MONGO_URI, database: str = MONGO_DATABASE, collection: str = MONGO_COLLECTION):
        self.uri = uri
        self.database = database
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
        self.connect()

    def connect(self) -> None:
        try:
            self.client = MongoClient(self.uri, maxPoolSize=10, serverSelectionTimeoutMS=3000)
            self.db = self.client[self.database]
            self.collection = self.db[self.collection_name]
            self.collection.database.client.admin.command("ping")
            self.connected = True
        except Exception:
            self.connected = False
            self.client = None
            self.db = None
            self.collection = None

    def seed_data(self) -> None:
        if not self.connected or self.collection is None:
            return
        if self.collection.count_documents({}) > 0:
            return

        sample_docs = []
        txn_ids = ["TXN-101", "TXN-102", "TXN-103", "TXN-104", "TXN-105", "TXN-106", "TXN-107", "TXN-108", "TXN-109", "TXN-110"]
        merchants = ["Northwind Market", "Apex Travels", "Greenway Food", "CloudPay", "Metro Retail", "Summit Fuel", "QuickFin", "Beacon Books", "Everlight Telecom", "Gadget Mart"]
        users = ["U-1001", "U-1002", "U-1003", "U-1004", "U-1005"]

        base_time = datetime.utcnow() - timedelta(days=7)
        for index, txn_id in enumerate(txn_ids):
            user_id = users[index % len(users)]
            sample_docs.append({
                "txn_id": txn_id,
                "user_id": user_id,
                "amount": round(120.0 + (index * 73.5), 2),
                "merchant": merchants[index],
                "timestamp": (base_time + timedelta(hours=index * 5)).isoformat(timespec="seconds") + "Z",
                "risk_score": round(0.25 + (index % 5) * 0.12, 2),
            })

        self.collection.insert_many(sample_docs)

    def get_transaction(self, txn_id: str) -> Optional[Dict[str, Any]]:
        if not self.connected or self.collection is None:
            raise ConnectionError("MongoDB unavailable")
        try:
            return self.collection.find_one({"txn_id": txn_id}, {"_id": 0})
        except PyMongoError as exc:
            raise ConnectionError(str(exc)) from exc

    def get_transactions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.connected or self.collection is None:
            raise ConnectionError("MongoDB unavailable")
        try:
            return list(self.collection.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).limit(10))
        except PyMongoError as exc:
            raise ConnectionError(str(exc)) from exc
