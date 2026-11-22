import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "lab16")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "transactions")
CASSANDRA_CONTACT_POINTS = [point.strip() for point in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",") if point.strip()]
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "university_demo")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
