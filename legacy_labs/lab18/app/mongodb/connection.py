from pymongo import MongoClient, ASCENDING

from app.config import MONGO_DB, MONGO_URI


def get_mongo_client():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client


def get_mongo_db():
    client = get_mongo_client()
    return client[MONGO_DB]


def initialize_mongodb_indexes(db):
    threat_collection = db['threat']
    full_collection = db['full_threats']
    for index_name in ['threat_id_1']:
        try:
            threat_collection.drop_index(index_name)
        except Exception:
            pass
    threat_collection.create_index([('from_source', ASCENDING), ('timestamp', ASCENDING)])
    threat_collection.create_index([('threat_type', ASCENDING)])
    threat_collection.create_index([('target', ASCENDING)])
    threat_collection.create_index([('threat_id', ASCENDING)])
    full_collection.create_index([('from_source', ASCENDING), ('timestamp', ASCENDING)])
    full_collection.create_index([('threat_type', ASCENDING)])
    full_collection.create_index([('target', ASCENDING)])
    full_collection.create_index([('threat_id', ASCENDING)], unique=True)
    return threat_collection, full_collection
