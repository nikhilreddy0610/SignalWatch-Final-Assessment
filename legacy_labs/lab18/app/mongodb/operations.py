from datetime import datetime
import time

from app.mongodb.connection import get_mongo_db, initialize_mongodb_indexes


class MongoThreatStore:
    def __init__(self):
        self.db = get_mongo_db()
        self.threat_collection = self.db['threat']
        self.full_collection = self.db['full_threats']
        try:
            self.threat_collection, self.full_collection = initialize_mongodb_indexes(self.db)
        except Exception:
            self.threat_collection = self.db['threat']
            self.full_collection = self.db['full_threats']

    def insert_dataset(self, threats):
        self.full_collection.delete_many({})
        self.threat_collection.delete_many({})
        for threat in threats:
            self.full_collection.insert_one(threat)
            self.threat_collection.update_one(
                {'from_source': threat['from_source']},
                {
                    '$set': {
                        'source_name': threat['from_source'],
                        'updated_at': datetime.utcnow(),
                        'last_timestamp': threat['timestamp'],
                    },
                    '$inc': {'total_threats': 1},
                    '$push': {'recent_threats': {'$each': [threat], '$slice': -50}},
                },
                upsert=True,
            )
        return len(threats)

    def history_by_source(self, source, limit=20):
        return list(self.full_collection.find({'from_source': source}).sort('timestamp', -1).limit(limit))

    def threats_by_target(self, target):
        return list(self.full_collection.find({'target': target}).sort('timestamp', -1))

    def daily_volume(self):
        pipeline = [
            {'$project': {'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': {'$toDate': '$timestamp'}}}, 'from_source': 1}},
            {'$group': {'_id': {'date': '$date', 'source': '$from_source'}, 'count': {'$sum': 1}}},
            {'$sort': {'_id.date': 1, '_id.source': 1}},
        ]
        return list(self.full_collection.aggregate(pipeline))

    def insert_throughput(self, threats, batch_size=500):
        start = time.perf_counter()
        for index in range(0, len(threats), batch_size):
            chunk = threats[index:index + batch_size]
            self.full_collection.insert_many(chunk)
        elapsed = time.perf_counter() - start
        return len(threats) / elapsed if elapsed > 0 else 0.0
