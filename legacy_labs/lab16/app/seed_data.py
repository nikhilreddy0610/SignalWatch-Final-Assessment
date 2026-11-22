from __future__ import annotations

from app.fraud_query_service import FraudQueryService


def seed_all() -> None:
    service = FraudQueryService(auto_seed=True)
    print("Sample data initialized for MongoDB, Cassandra and Neo4j.")
    return service


if __name__ == "__main__":
    seed_all()
