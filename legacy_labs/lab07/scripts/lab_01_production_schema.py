"""Lab 7.1: seed a CTI schema and measure document sizes with $bsonSize."""

import os
from datetime import datetime, timezone

from pymongo import MongoClient


DATABASE = os.getenv("MONGO_DATABASE", "cyber_threat_intelligence")
URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
LIMIT_BYTES = 16 * 1024 * 1024

SOURCES = [
    {
        "_id": "cisa",
        "name": "CISA",
        "url": "https://www.cisa.gov/",
        "feedUrl": "https://www.cisa.gov/news.xml",
        "trustTier": "government",
    },
    {
        "_id": "bleepingcomputer",
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/",
        "feedUrl": "https://www.bleepingcomputer.com/feed/",
        "trustTier": "news",
    },
    {
        "_id": "thehackernews",
        "name": "The Hacker News",
        "url": "https://thehackernews.com/",
        "feedUrl": "https://feeds.feedburner.com/TheHackersNews",
        "trustTier": "news",
    },
]

INDICATORS = [
    {
        "_id": "ioc-demo-1",
        "type": "domain",
        "value": "suspicious-example.invalid",
        "confidence": "medium",
        "category": "malware",
        "firstSeen": datetime(2026, 11, 10, tzinfo=timezone.utc),
    },
    {
        "_id": "ioc-demo-2",
        "type": "sha256",
        "value": "0" * 64,
        "confidence": "low",
        "category": "malware",
        "firstSeen": datetime(2026, 11, 12, tzinfo=timezone.utc),
    },
]

REPORTS = [
    {
        "_id": "report-demo-1",
        "title": "CISA adds an actively exploited vulnerability to its catalog",
        "summary": "Review affected products, prioritize remediation, and monitor for exploitation.",
        "url": "https://example.com/cti-lab/report-demo-1",
        "publishedAt": datetime(2026, 11, 18, tzinfo=timezone.utc),
        "category": "vulnerability",
        "confidence": "high",
        "tags": ["CISA", "KEV", "patching"],
        "sourceId": "cisa",
        "indicatorIds": ["ioc-demo-1"],
    },
    {
        "_id": "report-demo-2",
        "title": "Researchers warn of a new ransomware campaign",
        "summary": "The campaign uses phishing lures and data theft before file encryption.",
        "url": "https://example.com/cti-lab/report-demo-2",
        "publishedAt": datetime(2026, 11, 17, tzinfo=timezone.utc),
        "category": "ransomware",
        "confidence": "medium",
        "tags": ["ransomware", "phishing", "incident response"],
        "sourceId": "bleepingcomputer",
        "indicatorIds": ["ioc-demo-2"],
    },
    {
        "_id": "report-demo-3",
        "title": "Threat intelligence update with defensive guidance",
        "summary": "An intelligence update shares monitoring and mitigation advice.",
        "url": "https://example.com/cti-lab/report-demo-3",
        "publishedAt": datetime(2026, 11, 15, tzinfo=timezone.utc),
        "category": "threat-intel",
        "confidence": "low",
        "tags": ["indicators", "defense", "monitoring"],
        "sourceId": "thehackernews",
        "indicatorIds": [],
    },
]


def size_stats(collection):
    pipeline = [
        {"$project": {"size": {"$bsonSize": "$$ROOT"}}},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "averageBytes": {"$avg": "$size"},
                "maximumBytes": {"$max": "$size"},
                "minimumBytes": {"$min": "$size"},
            }
        },
    ]
    return list(collection.aggregate(pipeline))


def main():
    with MongoClient(URI, serverSelectionTimeoutMS=5000) as client:
        db = client[DATABASE]
        for name, documents in (
            ("sources", SOURCES),
            ("indicators", INDICATORS),
            ("reports", REPORTS),
        ):
            collection = db[name]
            collection.delete_many({"_id": {"$in": [doc["_id"] for doc in documents]}})
            collection.insert_many(documents)

        print(f"Lab 7.1 — BSON size analysis in {DATABASE}")
        grand_count = 0
        grand_size = 0.0
        largest = 0
        for name in ("sources", "indicators", "reports"):
            result = size_stats(db[name])
            if not result:
                continue
            stats = result[0]
            grand_count += stats["count"]
            grand_size += stats["averageBytes"] * stats["count"]
            largest = max(largest, stats["maximumBytes"])
            print(
                f"{name:12} count={stats['count']:>3} "
                f"avg={stats['averageBytes']:>8.1f} B "
                f"min={stats['minimumBytes']:>6} B "
                f"max={stats['maximumBytes']:>6} B"
            )
        average = grand_size / grand_count if grand_count else 0
        print(f"\nAcross all documents: count={grand_count}, average={average:.1f} B")
        print(f"MongoDB document limit: {LIMIT_BYTES:,} B (16 MiB)")
        print(
            f"Largest measured document: {largest:,} B "
            f"({largest / LIMIT_BYTES:.4%} of limit)"
        )
        if largest >= LIMIT_BYTES * 0.75:
            raise SystemExit("A document is approaching the 16 MiB limit; review unbounded fields.")
        print("PASS: no seeded document approaches the 16 MiB limit.")
        print(
            "\nEmbedding alternative experiment: copy the selected source's name, trustTier, "
            "and URL into each report. This can remove a lookup for report cards, but duplicates "
            "source data and requires fan-out updates when that source changes."
        )


if __name__ == "__main__":
    main()
