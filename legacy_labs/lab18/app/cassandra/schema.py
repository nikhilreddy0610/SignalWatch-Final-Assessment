from app.cassandra.connection import get_session


class CassandraSchema:
    def __init__(self):
        self.session = None
        try:
            self.session = get_session()
        except Exception:
            self.session = None

    def initialize(self):
        if self.session is None:
            self.session = get_session()
        self.session.execute("CREATE KEYSPACE IF NOT EXISTS threat_intelligence WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1}")
        self.session.set_keyspace('threat_intelligence')
        self.session.execute('''
            CREATE TABLE IF NOT EXISTS threats_by_source (
                source_id text,
                timestamp text,
                threat_id text,
                threat_type text,
                target text,
                severity text,
                confidence_score double,
                status text,
                PRIMARY KEY ((source_id), timestamp, threat_id)
            )
        ''')
        self.session.execute('''
            CREATE TABLE IF NOT EXISTS threats_by_type (
                threat_type text,
                timestamp text,
                threat_id text,
                source_id text,
                target text,
                severity text,
                confidence_score double,
                PRIMARY KEY ((threat_type), timestamp, threat_id)
            )
        ''')
        return self.session
