import time

from app.fraud_query_service import CircuitBreaker, FraudQueryService


class DummyMongo:
    def seed_data(self):
        return None

    def get_transaction(self, txn_id):
        return {"txn_id": txn_id, "user_id": "U-1001", "amount": 150.0, "merchant": "Sample Market", "timestamp": "2024-11-15T10:00:00Z", "risk_score": 0.8}


class DummyCassandra:
    def seed_data(self):
        return None

    def get_user_profile(self, user_id, limit=10):
        return [{"user_id": user_id, "txn_id": "TXN-1001", "event_type": "payment", "merchant": "Sample Market", "amount": 150.0, "risk_score": 0.8, "event_time": "2024-11-15T10:00:00Z"}]


class DummyNeo4j:
    def seed_data(self):
        return None

    def detect_fraud_rings(self, user_id, max_hops=3, limit=50):
        return [{"user_id": "U-1002", "hops": 2, "path": [user_id, "U-1002", "U-1003"]}]


class FailingMongo:
    def seed_data(self):
        return None

    def get_transaction(self, txn_id):
        raise ConnectionError("mongo down")


class FailingCassandra:
    def seed_data(self):
        return None

    def get_user_profile(self, user_id, limit=10):
        raise ConnectionError("cassandra down")


class FailingNeo4j:
    def seed_data(self):
        return None

    def detect_fraud_rings(self, user_id, max_hops=3, limit=50):
        raise ConnectionError("neo4j down")


def test_mongo_transaction_lookup():
    service = FraudQueryService(mongo_db=DummyMongo(), cassandra_db=DummyCassandra(), neo4j_db=DummyNeo4j(), auto_seed=False)
    txn = service.get_transaction("TXN-1001")
    assert txn["txn_id"] == "TXN-1001"
    assert txn["merchant"] == "Sample Market"


def test_cassandra_user_profile_retrieval():
    service = FraudQueryService(mongo_db=DummyMongo(), cassandra_db=DummyCassandra(), neo4j_db=DummyNeo4j(), auto_seed=False)
    profile = service.get_user_profile("U-1001")
    assert len(profile) == 1
    assert profile[0]["user_id"] == "U-1001"


def test_neo4j_fraud_ring_detection():
    service = FraudQueryService(mongo_db=DummyMongo(), cassandra_db=DummyCassandra(), neo4j_db=DummyNeo4j(), auto_seed=False)
    rings = service.detect_fraud_rings("U-1001")
    assert rings[0]["path"][0] == "U-1001"
    assert rings[0]["hops"] == 2


def test_combined_fraudqueryservice_response():
    service = FraudQueryService(mongo_db=DummyMongo(), cassandra_db=DummyCassandra(), neo4j_db=DummyNeo4j(), auto_seed=False)
    response = service.get_combined_response("U-1001", "TXN-1001")
    assert response["user_id"] == "U-1001"
    assert response["transaction"]["txn_id"] == "TXN-1001"
    assert response["user_profile"][0]["user_id"] == "U-1001"
    assert response["fraud_rings"][0]["user_id"] == "U-1002"
    assert response["backend_status"]["mongo"] == "ok"


def test_circuit_breaker_functionality():
    breaker = CircuitBreaker(failure_threshold=2, retry_seconds=1)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.can_attempt() is False
    time.sleep(1.1)
    assert breaker.can_attempt() is True


def test_database_failure_handling():
    service = FraudQueryService(mongo_db=FailingMongo(), cassandra_db=FailingCassandra(), neo4j_db=FailingNeo4j(), auto_seed=False)
    assert service.get_transaction("TXN-X") is None
    assert service.get_user_profile("U-1001") == []
    assert service.detect_fraud_rings("U-1001") == []
    assert service.backend_status["mongo"] == "unavailable"
    assert service.backend_status["cassandra"] == "unavailable"
    assert service.backend_status["neo4j"] == "unavailable"
