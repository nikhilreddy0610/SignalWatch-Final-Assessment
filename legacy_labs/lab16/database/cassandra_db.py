from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

from app.configuration import CASSANDRA_CONTACT_POINTS, CASSANDRA_KEYSPACE, CASSANDRA_PORT


class CassandraDatabase:
    def __init__(self, contact_points=None, port=None, keyspace=None):
        self.contact_points = contact_points or CASSANDRA_CONTACT_POINTS
        self.port = port or CASSANDRA_PORT
        self.keyspace = keyspace or CASSANDRA_KEYSPACE
        self.cluster = None
        self.session = None
        self.connected = False
        self.connect()

    def connect(self) -> None:
        try:
            self.cluster = Cluster(contact_points=self.contact_points, port=self.port)
            self.session = self.cluster.connect()
            self.session.execute("CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}" % self.keyspace)
            self.session.set_keyspace(self.keyspace)
            self.session.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT,
                    event_time TIMESTAMP,
                    txn_id TEXT,
                    event_type TEXT,
                    merchant TEXT,
                    amount DOUBLE,
                    risk_score DOUBLE,
                    PRIMARY KEY ((user_id), event_time)
                ) WITH CLUSTERING ORDER BY (event_time DESC)
                """
            )
            self.connected = True
        except Exception:
            self.connected = False
            self.session = None
            self.cluster = None

    def seed_data(self) -> None:
        if not self.connected or self.session is None:
            return
        try:
            existing = self.session.execute("SELECT COUNT(*) FROM user_profiles LIMIT 1")
            if existing and existing.one() and existing.one()[0] > 0:
                return
        except Exception:
            pass

        base_time = datetime.utcnow() - timedelta(days=7)
        sample_rows = [
            ("U-1001", base_time + timedelta(hours=2), "TXN-101", "payment", "Northwind Market", 220.5, 0.91),
            ("U-1001", base_time + timedelta(hours=3), "TXN-102", "refund", "CloudPay", 75.0, 0.32),
            ("U-1002", base_time + timedelta(hours=5), "TXN-103", "payment", "Greenway Food", 310.0, 0.68),
            ("U-1002", base_time + timedelta(hours=8), "TXN-104", "transfer", "Apex Travels", 540.0, 0.78),
            ("U-1003", base_time + timedelta(hours=11), "TXN-105", "payment", "Gadget Mart", 899.0, 0.87),
            ("U-1004", base_time + timedelta(hours=13), "TXN-106", "transfer", "Metro Retail", 680.0, 0.66),
            ("U-1004", base_time + timedelta(hours=15), "TXN-107", "payment", "Beacon Books", 195.5, 0.44),
            ("U-1005", base_time + timedelta(hours=18), "TXN-108", "payment", "Summit Fuel", 450.0, 0.71),
            ("U-1005", base_time + timedelta(hours=20), "TXN-109", "transfer", "Everlight Telecom", 655.0, 0.82),
            ("U-1001", base_time + timedelta(hours=24), "TXN-110", "payment", "QuickFin", 134.0, 0.58),
        ]

        for user_id, event_time, txn_id, event_type, merchant, amount, risk_score in sample_rows:
            self.session.execute(
                "INSERT INTO user_profiles (user_id, event_time, txn_id, event_type, merchant, amount, risk_score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, event_time, txn_id, event_type, merchant, amount, risk_score),
            )

    def get_user_profile(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.connected or self.session is None:
            raise ConnectionError("Cassandra unavailable")
        query = SimpleStatement(
            "SELECT user_id, event_time, txn_id, event_type, merchant, amount, risk_score FROM user_profiles WHERE user_id = %s LIMIT %s",
            fetch_size=limit,
        )
        rows = self.session.execute(query, [user_id, limit])
        result = []
        for row in rows:
            result.append({
                "user_id": row.user_id,
                "event_time": row.event_time.isoformat(timespec="seconds") + "Z",
                "txn_id": row.txn_id,
                "event_type": row.event_type,
                "merchant": row.merchant,
                "amount": row.amount,
                "risk_score": row.risk_score,
            })
        return result
