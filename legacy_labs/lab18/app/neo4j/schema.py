from app.neo4j.connection import get_driver


class Neo4jSchema:
    def __init__(self):
        self.driver = None
        try:
            self.driver = get_driver()
        except Exception:
            self.driver = None

    def initialize(self):
        if self.driver is None:
            self.driver = get_driver()
        with self.driver.session() as session:
            session.run('CREATE CONSTRAINT source_name IF NOT EXISTS FOR (s:Source) REQUIRE s.name IS UNIQUE')
            session.run('CREATE CONSTRAINT threat_id IF NOT EXISTS FOR (t:Threat) REQUIRE t.threat_id IS UNIQUE')
            session.run('CREATE CONSTRAINT target_name IF NOT EXISTS FOR (t:Target) REQUIRE t.name IS UNIQUE')
            session.run('CREATE INDEX source_index IF NOT EXISTS FOR (s:Source) ON (s.name)')
            session.run('CREATE INDEX target_index IF NOT EXISTS FOR (t:Target) ON (t.name)')
        return self.driver
