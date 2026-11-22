from __future__ import annotations

from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, basic_auth

from app.configuration import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER


class Neo4jDatabase:
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        self.connect()

    def connect(self) -> None:
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
        except Exception:
            self.connected = False
            self.driver = None

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()
            self.driver = None

    def seed_data(self) -> None:
        if not self.connected or self.driver is None:
            return

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            relationships = [
                ("U-1001", "U-1002", "TXN-101", 200.0),
                ("U-1002", "U-1003", "TXN-102", 175.0),
                ("U-1003", "U-1004", "TXN-103", 340.0),
                ("U-1004", "U-1005", "TXN-104", 225.0),
                ("U-1002", "U-1005", "TXN-105", 420.0),
                ("U-1003", "U-1001", "TXN-106", 280.0),
            ]

            for source, target, txn_id, amount in relationships:
                session.run(
                    """
                    MERGE (a:User {user_id: $source})
                    MERGE (b:User {user_id: $target})
                    MERGE (a)-[:TRANSFERRED_TO {txn_id: $txn_id, amount: $amount}]->(b)
                    """,
                    source=source,
                    target=target,
                    txn_id=txn_id,
                    amount=amount,
                )

    def detect_fraud_rings(self, user_id: str, max_hops: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.connected or self.driver is None:
            raise ConnectionError("Neo4j unavailable")

        query = """
            MATCH path = (start:User {user_id: $user_id})-[:TRANSFERRED_TO*1..$max_hops]-(related:User)
            WHERE related.user_id <> $user_id
            RETURN [n in nodes(path) | n.user_id] AS path, length(path) AS hops
            LIMIT $limit
        """

        with self.driver.session() as session:
            records = session.run(query, user_id=user_id, max_hops=max_hops, limit=limit)
            result = []
            for record in records:
                result.append({
                    "user_id": record["path"][-1],
                    "hops": record["hops"],
                    "path": record["path"],
                })
            return result
