from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.database.cassandra_db import CassandraDatabase
from app.database.mongo_db import MongoDatabase
from app.database.neo4j_db import Neo4jDatabase


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, retry_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.retry_seconds = retry_seconds
        self.consecutive_failures = 0
        self.open_until = 0.0

    def can_attempt(self) -> bool:
        if self.consecutive_failures < self.failure_threshold:
            return True
        if time.monotonic() >= self.open_until:
            self.consecutive_failures = 0
            return True
        return False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.open_until = time.monotonic() + self.retry_seconds

    @property
    def state(self) -> str:
        if self.consecutive_failures >= self.failure_threshold and time.monotonic() < self.open_until:
            return "unavailable"
        return "available"


class FraudQueryService:
    def __init__(self, mongo_db: Optional[MongoDatabase] = None, cassandra_db: Optional[CassandraDatabase] = None, neo4j_db: Optional[Neo4jDatabase] = None, auto_seed: bool = True):
        self.mongo = mongo_db or MongoDatabase()
        self.cassandra = cassandra_db or CassandraDatabase()
        self.neo4j = neo4j_db or Neo4jDatabase()
        self.breakers = {
            "mongo": CircuitBreaker(),
            "cassandra": CircuitBreaker(),
            "neo4j": CircuitBreaker(),
        }
        self.backend_status = {"mongo": "unknown", "cassandra": "unknown", "neo4j": "unknown"}
        if auto_seed:
            self.seed_demo_data()

    def seed_demo_data(self) -> None:
        for backend_name, seeder in (
            ("mongo", self.mongo.seed_data),
            ("cassandra", self.cassandra.seed_data),
            ("neo4j", self.neo4j.seed_data),
        ):
            try:
                seeder()
                self.backend_status[backend_name] = "ok"
            except Exception:
                self.backend_status[backend_name] = "unavailable"

    def _execute(self, backend: str, func, *args, **kwargs):
        breaker = self.breakers[backend]
        if not breaker.can_attempt():
            self.backend_status[backend] = "unavailable"
            return None, "unavailable"
        try:
            result = func(*args, **kwargs)
            breaker.record_success()
            self.backend_status[backend] = "ok"
            return result, "ok"
        except Exception:
            breaker.record_failure()
            self.backend_status[backend] = "unavailable"
            return None, "unavailable"

    def get_transaction(self, txn_id: str) -> Optional[Dict[str, Any]]:
        result, _ = self._execute("mongo", self.mongo.get_transaction, txn_id)
        return result

    def get_user_profile(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        result, _ = self._execute("cassandra", self.cassandra.get_user_profile, user_id, limit)
        return result or []

    def detect_fraud_rings(self, user_id: str, max_hops: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        result, _ = self._execute("neo4j", self.neo4j.detect_fraud_rings, user_id, max_hops, limit)
        return result or []

    def get_combined_response(self, user_id: str, txn_id: Optional[str] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        transaction = None
        if txn_id:
            transaction = self.get_transaction(txn_id)

        user_profile = self.get_user_profile(user_id)
        fraud_rings = self.detect_fraud_rings(user_id)
        execution_latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "user_id": user_id,
            "transaction": transaction,
            "user_profile": user_profile,
            "fraud_rings": fraud_rings,
            "backend_status": self.backend_status,
            "execution_latency_ms": execution_latency_ms,
        }
