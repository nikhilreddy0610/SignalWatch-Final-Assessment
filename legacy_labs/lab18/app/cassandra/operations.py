import time

from app.cassandra.schema import CassandraSchema


class CassandraThreatStore:
    def __init__(self):
        self.schema = CassandraSchema()
        self.session = None
        try:
            self.session = self.schema.initialize()
        except Exception:
            self.session = None

    def _require_session(self):
        if self.session is None:
            raise RuntimeError('Cassandra is not available. Start the Cassandra service and try again.')
        return self.session

    def insert_dataset(self, threats):
        session = self._require_session()
        session.execute('TRUNCATE threats_by_source')
        session.execute('TRUNCATE threats_by_type')
        for threat in threats:
            session.execute(
                '''
                INSERT INTO threats_by_source (
                    source_id, timestamp, threat_id, threat_type, target, severity, confidence_score, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    threat['from_source'], threat['timestamp'], threat['threat_id'],
                    threat['threat_type'], threat['target'], threat['severity'],
                    float(threat['confidence_score']), threat['status'],
                )
            )
            session.execute(
                '''
                INSERT INTO threats_by_type (
                    threat_type, timestamp, threat_id, source_id, target, severity, confidence_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    threat['threat_type'], threat['timestamp'], threat['threat_id'],
                    threat['from_source'], threat['target'], threat['severity'],
                    float(threat['confidence_score'])
                )
            )
        return len(threats)

    def history_by_source(self, source_id):
        rows = self._require_session().execute(
            'SELECT * FROM threats_by_source WHERE source_id = %s LIMIT 20',
            (source_id,),
        )
        return list(rows)

    def threat_type_query(self, threat_type):
        rows = self._require_session().execute(
            'SELECT * FROM threats_by_type WHERE threat_type = %s LIMIT 20',
            (threat_type,),
        )
        return list(rows)

    def daily_volume(self):
        rows = self._require_session().execute('SELECT source_id, timestamp FROM threats_by_source LIMIT 50')
        return list(rows)

    def insert_throughput(self, threats, batch_size=500):
        session = self._require_session()
        start = time.perf_counter()
        for offset in range(0, len(threats), batch_size):
            batch = threats[offset:offset + batch_size]
            for threat in batch:
                session.execute(
                    '''
                    INSERT INTO threats_by_source (
                        source_id, timestamp, threat_id, threat_type, target, severity, confidence_score, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        threat['from_source'], threat['timestamp'], threat['threat_id'],
                        threat['threat_type'], threat['target'], threat['severity'],
                        float(threat['confidence_score']), threat['status'],
                    )
                )
                session.execute(
                    '''
                    INSERT INTO threats_by_type (
                        threat_type, timestamp, threat_id, source_id, target, severity, confidence_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        threat['threat_type'], threat['timestamp'], threat['threat_id'],
                        threat['from_source'], threat['target'], threat['severity'],
                        float(threat['confidence_score'])
                    )
                )
        elapsed = time.perf_counter() - start
        return len(threats) / elapsed if elapsed > 0 else 0.0
