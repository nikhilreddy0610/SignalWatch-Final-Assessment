"""Lab 7.2: seed a 100,000-document working set and monitor WiredTiger cache."""

import argparse
import os
import random
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import feedparser
from bson import BSON
from pymongo import MongoClient, ASCENDING


DATABASE = os.getenv("MONGO_DATABASE", "cyber_threat_intelligence")
URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
COUNT = 100_000
TARGET_BYTES = 2 * 1024
FEEDS = {
    "cisa": ("CISA", "https://www.cisa.gov/news.xml"),
    "bleepingcomputer": ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    "thehackernews": ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
}


def seed(collection, reset: bool) -> None:
    if reset:
        collection.drop()
    existing = collection.count_documents({})
    if existing:
        if existing != COUNT:
            raise RuntimeError(
                f"{collection.full_name} contains {existing:,} documents; "
                "use --reset to replace it with the requested 100,000."
            )
        print(f"Using existing {existing:,}-document working set.")
        return

    collection.create_index([("sequence", ASCENDING)])
    base = {"sensor": "S-000000", "reading": 0.0, "metadata": "", "sequence": 0}
    payload_length = TARGET_BYTES - len(BSON.encode(base))
    batch_size = 1000
    started = time.perf_counter()
    for offset in range(0, COUNT, batch_size):
        batch = [
            {
                **base,
                "sensor": f"S-{index:06d}",
                "reading": index * 0.01,
                "metadata": "x" * payload_length,
                "sequence": index,
            }
            for index in range(offset, min(offset + batch_size, COUNT))
        ]
        collection.insert_many(batch, ordered=False)
    elapsed = time.perf_counter() - started
    print(
        f"Inserted {COUNT:,} documents, approximately {TARGET_BYTES:,} bytes each "
        f"(~{COUNT * TARGET_BYTES / 1024 / 1024:.1f} MiB payload) in {elapsed:.1f}s."
    )


def cache_metrics(client):
    status = client.admin.command("serverStatus")
    cache = status.get("wiredTiger", {}).get("cache", {})
    requested = cache.get("pages requested from the cache")
    loaded = cache.get("pages read into cache")
    return {
        "maximum": cache.get("maximum bytes configured"),
        "used": cache.get("bytes currently in the cache"),
        "dirty": cache.get("tracked dirty bytes in the cache"),
        "requested": requested,
        "loaded": loaded,
        "evicted": cache.get("pages evicted by application threads"),
    }


def update_new_reports(db) -> int:
    added = 0
    latest = db.reports.find_one(
        {"publishedAt": {"$type": "date"}},
        sort=[("publishedAt", -1)],
        projection={"publishedAt": 1},
    )
    latest_published = latest.get("publishedAt") if latest else None
    if latest_published and latest_published.tzinfo is None:
        latest_published = latest_published.replace(tzinfo=timezone.utc)
    for source_id, (source_name, feed_url) in FEEDS.items():
        request_object = Request(feed_url, headers={"User-Agent": "CTI-Lab-Student-Project/1.0"})
        with urlopen(request_object, timeout=8) as response:
            parsed = feedparser.parse(response.read())
        db.sources.update_one(
            {"_id": source_id},
            {"$set": {"name": source_name, "feedUrl": feed_url}},
            upsert=True,
        )
        for entry in parsed.entries[:30]:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            if not link or not title:
                continue
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            published_at = (
                datetime(*published[:6], tzinfo=timezone.utc)
                if published
                else datetime.now(timezone.utc)
            )
            if latest_published and published_at <= latest_published:
                continue
            result = db.reports.update_one(
                {"url": link},
                {
                    "$setOnInsert": {
                        "title": title[:300],
                        "summary": entry.get("summary", "")[:1200],
                        "url": link,
                        "publishedAt": published_at,
                        "category": "unclassified",
                        "confidence": "low",
                        "tags": [],
                        "sourceId": source_id,
                        "indicatorIds": [],
                    }
                },
                upsert=True,
            )
            if result.upserted_id is not None:
                added += 1
                latest_published = (
                    max(latest_published, published_at)
                    if latest_published
                    else published_at
                )
    return added


def ratio(current, previous):
    if (
        previous is None
        or current["requested"] is None
        or current["loaded"] is None
        or previous["requested"] is None
        or previous["loaded"] is None
    ):
        return None
    requested_delta = current["requested"] - previous["requested"]
    loaded_delta = current["loaded"] - previous["loaded"]
    if requested_delta <= 0 or loaded_delta < 0:
        return None
    return max(0.0, min(1.0, 1 - loaded_delta / requested_delta))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="Drop and recreate the working-set collection.")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between monitoring samples.")
    parser.add_argument("--reads", type=int, default=500, help="Random reads per monitoring interval.")
    args = parser.parse_args()
    if args.interval < 1 or args.reads < 1:
        parser.error("--interval and --reads must be positive integers")

    with MongoClient(URI, serverSelectionTimeoutMS=5000) as client:
        db = client[DATABASE]
        collection = db.working_set_docs
        seed(collection, args.reset)
        previous = cache_metrics(client)
        print(
            "Monitoring cache every "
            f"{args.interval}s; Ctrl-C to stop. Cache hit ratio is estimated from "
            "delta(page requests - pages read into cache) / page requests."
        )
        try:
            while True:
                started = time.monotonic()
                for _ in range(args.reads):
                    sequence = random.randrange(COUNT)
                    collection.find_one({"sequence": sequence}, {"_id": 0, "reading": 1})
                new_reports = 0
                feed_errors = []
                try:
                    new_reports = update_new_reports(db)
                except Exception as error:
                    feed_errors.append(str(error))
                current = cache_metrics(client)
                hit_ratio = ratio(current, previous)
                previous = current
                used, maximum = current["used"], current["maximum"]
                used_pct = (100 * used / maximum) if used is not None and maximum else None
                ratio_text = f"{hit_ratio:.1%}" if hit_ratio is not None else "n/a"
                usage_text = (
                    f"{used / 1024 / 1024:.1f}/{maximum / 1024 / 1024:.1f} MiB "
                    f"({used_pct:.1f}%)"
                    if used_pct is not None
                    else "n/a"
                )
                print(
                    f"{datetime.now().astimezone().isoformat(timespec='seconds')} "
                    f"hit={ratio_text} cache={usage_text} "
                    f"pagesLoaded={current['loaded']} evicted={current['evicted']} "
                    f"newReports={new_reports}"
                )
                for error in feed_errors:
                    print(f"Feed warning: {error}")
                time.sleep(max(0, args.interval - (time.monotonic() - started)))
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()
