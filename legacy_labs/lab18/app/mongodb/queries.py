def source_history_query(db, source):
    return list(db['full_threats'].find({'from_source': source}).sort('timestamp', -1).limit(20))


def target_spread_query(db, target):
    return list(db['full_threats'].find({'target': target}).sort('timestamp', -1).limit(20))


def daily_analytics_query(db):
    return list(db['full_threats'].aggregate([
        {'$project': {'day': {'$substr': ['$timestamp', 0, 10]}, 'source': '$from_source'}},
        {'$group': {'_id': {'day': '$day', 'source': '$source'}, 'count': {'$sum': 1}}},
        {'$sort': {'_id.day': 1, '_id.source': 1}},
    ]))
