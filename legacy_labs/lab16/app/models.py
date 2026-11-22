from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TransactionRecord:
    txn_id: str
    user_id: str
    amount: float
    merchant: str
    timestamp: str
    risk_score: float


@dataclass
class UserEvent:
    txn_id: str
    user_id: str
    event_type: str
    merchant: str
    amount: float
    risk_score: float
    event_time: str


@dataclass
class FraudRingResult:
    user_id: str
    hops: int
    path: List[str] = field(default_factory=list)


@dataclass
class BackendStatus:
    mongo: str = "unknown"
    cassandra: str = "unknown"
    neo4j: str = "unknown"


@dataclass
class UnifiedFraudResponse:
    user_id: str
    transaction: Optional[Dict[str, Any]] = None
    user_profile: List[Dict[str, Any]] = field(default_factory=list)
    fraud_rings: List[Dict[str, Any]] = field(default_factory=list)
    backend_status: BackendStatus = field(default_factory=BackendStatus)
    execution_latency_ms: int = 0
