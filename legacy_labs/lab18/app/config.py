import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "threat_intelligence")
CASSANDRA_CONTACT_POINTS = [p.strip() for p in os.getenv("CASSANDRA_CONTACT_POINTS", "localhost").split(",") if p.strip()]
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "threat_intelligence")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "lab18pass")
THREAT_COUNT = int(os.getenv("THREAT_COUNT", "100000"))
