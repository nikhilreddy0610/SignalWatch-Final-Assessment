import time

from app.neo4j.schema import Neo4jSchema


class Neo4jThreatStore:
    def __init__(self):
        self.driver = None
        try:
            self.driver = Neo4jSchema().initialize()
        except Exception:
            self.driver = None

    def _require_driver(self):
        if self.driver is None:
            raise RuntimeError('Neo4j is not available. Start the Neo4j service and try again.')
        return self.driver

    def insert_dataset(self, threats):
        driver = self._require_driver()
        with driver.session() as session:
            session.run('MATCH (n) DETACH DELETE n')
            for threat in threats:
                session.run(
                    '''
                    MERGE (s:Source {name: $source})
                    MERGE (t:Target {name: $target})
                    MERGE (th:Threat {threat_id: $threat_id, source: $source, target: $target, severity: $severity, confidence_score: $confidence, timestamp: $timestamp})
                    MERGE (s)-[:REPORTED]->(th)
                    MERGE (th)-[:TARGETS]->(t)
                    ''',
                    source=threat['from_source'],
                    target=threat['target'],
                    threat_id=threat['threat_id'],
                    severity=threat['severity'],
                    confidence=threat['confidence_score'],
                    timestamp=threat['timestamp'],
                )
            return len(threats)

    def history_by_source(self, source_name):
        with self._require_driver().session() as session:
            results = session.run(
                '''
                MATCH (s:Source {name: $source})-[:REPORTED]->(th:Threat)
                RETURN th.threat_id AS threat_id, th.source AS source, th.target AS target, th.severity AS severity,
                       th.confidence_score AS confidence_score, th.timestamp AS timestamp
                ORDER BY th.timestamp DESC LIMIT 20
                ''',
                source=source_name,
            )
            return [dict(record) for record in results]

    def common_targets(self, source_name):
        with self._require_driver().session() as session:
            results = session.run(
                '''
                MATCH (s:Source {name: $source})-[:REPORTED]->(:Threat)-[:TARGETS]->(t:Target)<-[:TARGETS]-(:Threat)<-[:REPORTED]-(other:Source)
                WHERE other.name <> $source
                RETURN other.name AS related_source, collect(DISTINCT t.name) AS targets, count(DISTINCT t.name) AS target_count
                ORDER BY target_count DESC LIMIT 10
                ''',
                source=source_name,
            )
            return [dict(record) for record in results]

    def suspicious_sources(self):
        with self._require_driver().session() as session:
            results = session.run(
                '''
                MATCH (s1:Source)-[:REPORTED]->(:Threat)-[:TARGETS]->(t:Target)<-[:TARGETS]-(:Threat)<-[:REPORTED]-(s2:Source)
                WHERE s1.name <> s2.name
                WITH s1, s2, count(DISTINCT t) AS sharedTargets
                WHERE sharedTargets >= 2
                MERGE (s1)-[:SUSPICIOUS]->(s2)
                RETURN s1.name AS source_a, s2.name AS source_b, sharedTargets
                ORDER BY sharedTargets DESC LIMIT 10
                '''
            )
            return [dict(record) for record in results]

    def daily_patterns(self):
        with self._require_driver().session() as session:
            results = session.run(
                '''
                MATCH (s:Source)-[:REPORTED]->(th:Threat)
                WITH date(datetime(th.timestamp)) AS day, s.name AS source, count(th) AS volume
                RETURN day, source, volume ORDER BY day DESC, source ASC LIMIT 20
                '''
            )
            return [dict(record) for record in results]

    def community_summary(self):
        with self._require_driver().session() as session:
            results = session.run(
                '''
                MATCH (s1:Source)-[:SUSPICIOUS]->(s2:Source)
                RETURN s1.name AS source_a, s2.name AS source_b, count(*) AS suspicious_links
                ORDER BY suspicious_links DESC LIMIT 20
                '''
            )
            return [dict(record) for record in results]

    def insert_throughput(self, threats, batch_size=500):
        driver = self._require_driver()
        start = time.perf_counter()
        with driver.session() as session:
            for offset in range(0, len(threats), batch_size):
                batch = threats[offset:offset + batch_size]
                for threat in batch:
                    session.run(
                        '''
                        MERGE (s:Source {name: $source})
                        MERGE (t:Target {name: $target})
                        MERGE (th:Threat {threat_id: $threat_id, source: $source, target: $target, severity: $severity, confidence_score: $confidence, timestamp: $timestamp})
                        MERGE (s)-[:REPORTED]->(th)
                        MERGE (th)-[:TARGETS]->(t)
                        ''',
                        source=threat['from_source'],
                        target=threat['target'],
                        threat_id=threat['threat_id'],
                        severity=threat['severity'],
                        confidence=threat['confidence_score'],
                        timestamp=threat['timestamp'],
                    )
        elapsed = time.perf_counter() - start
        return len(threats) / elapsed if elapsed > 0 else 0.0
