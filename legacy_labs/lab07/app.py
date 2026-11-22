from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser
from bson import BSON
from flask import Flask, jsonify, request, send_from_directory
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError


ROOT = Path(__file__).resolve().parent
DATABASE_NAME = os.getenv("MONGO_DATABASE", "cyber_threat_intelligence")
MONGO_URI = os.getenv("MONGO_URI")
app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500) if MONGO_URI else None
db = client[DATABASE_NAME] if client is not None else None

SOURCES = [
    {
        "_id": "cisa",
        "name": "CISA",
        "url": "https://www.cisa.gov/news.xml",
        "feedUrl": "https://www.cisa.gov/news.xml",
    },
    {
        "_id": "bleepingcomputer",
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/",
        "feedUrl": "https://www.bleepingcomputer.com/feed/",
    },
    {
        "_id": "thehackernews",
        "name": "The Hacker News",
        "url": "https://thehackernews.com/",
        "feedUrl": "https://feeds.feedburner.com/TheHackersNews",
    },
]

DEMO_REPORTS = [
    {
        "_id": "demo-1",
        "title": "CISA adds actively exploited vulnerability to its catalog",
        "summary": "A software vulnerability has been added to the Known Exploited Vulnerabilities catalog. Review affected products and apply vendor mitigations.",
        "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "publishedAt": datetime(2026, 11, 18, tzinfo=timezone.utc),
        "category": "vulnerability",
        "confidence": "high",
        "tags": ["CISA", "KEV", "patching"],
        "sourceId": "cisa",
        "indicatorIds": ["ioc-demo-1"],
    },
    {
        "_id": "demo-2",
        "title": "Researchers warn of a new ransomware campaign targeting businesses",
        "summary": "Incident responders describe a ransomware operation using phishing lures and data exfiltration before encryption.",
        "url": "https://www.bleepingcomputer.com/news/security/",
        "publishedAt": datetime(2026, 11, 17, tzinfo=timezone.utc),
        "category": "ransomware",
        "confidence": "medium",
        "tags": ["ransomware", "phishing", "incident response"],
        "sourceId": "bleepingcomputer",
        "indicatorIds": [],
    },
    {
        "_id": "demo-3",
        "title": "Malware campaign uses credential theft to gain initial access",
        "summary": "A security report details malicious files and credential-stealing activity, with recommended detection and response steps.",
        "url": "https://thehackernews.com/",
        "publishedAt": datetime(2026, 11, 15, tzinfo=timezone.utc),
        "category": "malware",
        "confidence": "medium",
        "tags": ["malware", "credentials", "detection"],
        "sourceId": "thehackernews",
        "indicatorIds": ["ioc-demo-2"],
    },
    {
        "_id": "demo-4",
        "title": "Security teams investigate a targeted phishing email campaign",
        "summary": "The advisory recommends reviewing suspicious links, sender domains, and authentication logs for signs of compromise.",
        "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
        "publishedAt": datetime(2026, 11, 12, tzinfo=timezone.utc),
        "category": "phishing",
        "confidence": "medium",
        "tags": ["phishing", "email", "identity"],
        "sourceId": "cisa",
        "indicatorIds": [],
    },
    {
        "_id": "demo-5",
        "title": "Threat intelligence update: indicators and defensive guidance",
        "summary": "An intelligence update shares defensive recommendations and indicators associated with ongoing malicious activity.",
        "url": "https://www.cisa.gov/",
        "publishedAt": datetime(2026, 11, 9, tzinfo=timezone.utc),
        "category": "threat-intel",
        "confidence": "low",
        "tags": ["indicators", "defense", "monitoring"],
        "sourceId": "bleepingcomputer",
        "indicatorIds": [],
    },
]

DEMO_INDICATORS = [
    {
        "_id": "ioc-demo-1",
        "type": "domain",
        "value": "suspicious-example.invalid",
        "confidence": "medium",
        "category": "malware",
    },
    {
        "_id": "ioc-demo-2",
        "type": "sha256",
        "value": "0" * 64,
        "confidence": "low",
        "category": "malware",
    },
]

CLASSIFICATION_RULES = [
    ("ransomware", ("ransomware", "encryption", "extortion")),
    ("phishing", ("phishing", "credential theft", "spoofed email")),
    ("malware", ("malware", "trojan", "backdoor", "botnet")),
    ("vulnerability", ("vulnerability", "cve-", "zero-day", "zero day", "patch")),
    ("espionage", ("espionage", "apt", "state-sponsored", "state sponsored")),
]


def classify_text(text: str) -> dict:
    lowered = text.lower()
    matches = [
        {"category": category, "signals": [term for term in terms if term in lowered]}
        for category, terms in CLASSIFICATION_RULES
    ]
    matches = [match for match in matches if match["signals"]]
    matches.sort(key=lambda item: len(item["signals"]), reverse=True)
    if not matches:
        return {
            "category": "unclassified",
            "confidence": "low",
            "signals": [],
            "note": "Keyword-based educational classification; verify against trusted sources.",
        }
    count = len(matches[0]["signals"])
    return {
        "category": matches[0]["category"],
        "confidence": "high" if count >= 2 else "medium",
        "signals": matches[0]["signals"],
        "note": "Keyword-based educational classification; this is not a verified threat verdict.",
    }


def ensure_indexes() -> None:
    if db is not None:
        db.reports.create_index([("publishedAt", DESCENDING)])
        db.reports.create_index([("category", ASCENDING), ("publishedAt", DESCENDING)])
        db.reports.create_index([("sourceId", ASCENDING)])
        db.reports.create_index("url", unique=True)
        db.indicators.create_index("value", unique=True)
        for source in SOURCES:
            db.sources.update_one(
                {"_id": source["_id"]},
                {"$setOnInsert": source},
                upsert=True,
            )
        for indicator in DEMO_INDICATORS:
            db.indicators.update_one(
                {"_id": indicator["_id"]},
                {"$setOnInsert": indicator},
                upsert=True,
            )
        for report in DEMO_REPORTS:
            db.reports.update_one(
                {"_id": report["_id"]},
                {"$setOnInsert": report},
                upsert=True,
            )


def serialize_report(report: dict, source_map: dict) -> dict:
    published = report.get("publishedAt")
    if isinstance(published, datetime):
        published = published.isoformat()
    return {
        "id": str(report.get("_id", "")),
        "title": report.get("title", "Untitled report"),
        "summary": report.get("summary", ""),
        "url": report.get("url", ""),
        "publishedAt": published,
        "category": report.get("category", "unclassified"),
        "confidence": report.get("confidence", "low"),
        "tags": report.get("tags", []),
        "sourceId": report.get("sourceId", ""),
        "sourceName": source_map.get(report.get("sourceId"), "Unknown source"),
        "indicatorCount": len(report.get("indicatorIds", [])),
    }


def read_reports(query: str, category: str, page: int, page_size: int) -> tuple[list, int]:
    if db is None:
        source_map = {source["_id"]: source["name"] for source in SOURCES}
        reports = DEMO_REPORTS
        if category and category != "all":
            reports = [report for report in reports if report["category"] == category]
        if query:
            needle = query.casefold()
            reports = [
                report for report in reports
                if needle in " ".join(
                    [report["title"], report["summary"], report["category"], *report["tags"]]
                ).casefold()
            ]
        reports = sorted(reports, key=lambda report: report["publishedAt"], reverse=True)
        total = len(reports)
        selected = reports[(page - 1) * page_size : page * page_size]
        return [serialize_report(report, source_map) for report in selected], total

    filter_query = {}
    if category and category != "all":
        filter_query["category"] = category
    if query:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        filter_query["$or"] = [
            {"title": pattern},
            {"summary": pattern},
            {"category": pattern},
            {"tags": pattern},
        ]
    total = db.reports.count_documents(filter_query)
    cursor = (
        db.reports.find(filter_query)
        .sort("publishedAt", DESCENDING)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    reports = list(cursor)
    source_ids = {report.get("sourceId") for report in reports if report.get("sourceId")}
    source_map = {
        source["_id"]: source["name"]
        for source in db.sources.find({"_id": {"$in": list(source_ids)}})
    }
    return [serialize_report(report, source_map) for report in reports], total


@app.get("/")
def index():
    return send_from_directory(ROOT / "static", "index.html")


@app.get("/api/reports")
def reports():
    try:
        page = max(1, int(request.args.get("page", "1")))
        page_size = min(50, max(1, int(request.args.get("limit", "20"))))
        items, total = read_reports(
            request.args.get("q", "").strip()[:200],
            request.args.get("category", "all"),
            page,
            page_size,
        )
        return jsonify({"items": items, "total": total, "page": page, "limit": page_size})
    except (ValueError, PyMongoError) as error:
        app.logger.exception("Could not retrieve reports")
        return jsonify({"error": str(error)}), 503


@app.get("/api/stats")
def stats():
    if db is None:
        reports_data = DEMO_REPORTS
        return jsonify(
            {
                "reports": len(reports_data),
                "sources": len(SOURCES),
                "indicators": len(DEMO_INDICATORS),
                "categories": len({report["category"] for report in reports_data}),
                "mode": "demo",
            }
        )
    try:
        return jsonify(
            {
                "reports": db.reports.count_documents({}),
                "sources": db.sources.count_documents({}),
                "indicators": db.indicators.count_documents({}),
                "categories": len(db.reports.distinct("category")),
                "mode": "mongodb",
            }
        )
    except PyMongoError as error:
        app.logger.exception("Could not retrieve database statistics")
        return jsonify({"error": str(error)}), 503


@app.get("/api/lab/schema")
def schema_stats():
    if db is None:
        collections = {
            "sources": SOURCES,
            "indicators": DEMO_INDICATORS,
            "reports": DEMO_REPORTS,
        }
        measured = {
            name: {
                "count": len(documents),
                "averageBytes": round(
                    sum(len(BSON.encode(document)) for document in documents) / len(documents)
                )
                if documents
                else 0,
                "maximumBytes": max(
                    (len(BSON.encode(document)) for document in documents), default=0
                ),
            }
            for name, documents in collections.items()
        }
    else:
        measured = {}
        try:
            for name in ("sources", "indicators", "reports"):
                result = list(
                    db[name].aggregate(
                        [
                            {"$project": {"size": {"$bsonSize": "$$ROOT"}}},
                            {
                                "$group": {
                                    "_id": None,
                                    "count": {"$sum": 1},
                                    "averageBytes": {"$avg": "$size"},
                                    "maximumBytes": {"$max": "$size"},
                                }
                            },
                        ]
                    )
                )
                stats = result[0] if result else {}
                measured[name] = {
                    "count": stats.get("count", 0),
                    "averageBytes": round(stats.get("averageBytes", 0)),
                    "maximumBytes": stats.get("maximumBytes", 0),
                }
        except PyMongoError as error:
            app.logger.exception("Could not measure BSON sizes")
            return jsonify({"error": str(error)}), 503
    counts = [stats["count"] for stats in measured.values()]
    total = sum(counts)
    average = (
        round(
            sum(stats["averageBytes"] * stats["count"] for stats in measured.values())
            / total
        )
        if total
        else 0
    )
    return jsonify(
        {
            "collections": measured,
            "averageBytes": average,
            "maximumBytes": max(
                (stats["maximumBytes"] for stats in measured.values()), default=0
            ),
            "limitBytes": 16 * 1024 * 1024,
            "mode": "mongodb" if db is not None else "demo",
        }
    )


@app.post("/api/classify")
def classify():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Provide non-empty report text."}), 400
    if len(text) > 10_000:
        return jsonify({"error": "Report text must be 10,000 characters or fewer."}), 400
    return jsonify(classify_text(text))


def fetch_feed(source: dict) -> list[dict]:
    request_object = Request(
        source["feedUrl"],
        headers={"User-Agent": "CTI-Lab-Student-Project/1.0"},
    )
    with urlopen(request_object, timeout=8) as response:
        parsed = feedparser.parse(response.read())
    items = []
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
        summary = re.sub(r"<[^>]*>", " ", entry.get("summary", ""))
        summary = re.sub(r"\s+", " ", summary).strip()[:1200]
        classification = classify_text(f"{title} {summary}")
        items.append(
            {
                "_id": str(uuid.uuid5(uuid.NAMESPACE_URL, link)),
                "title": title[:300],
                "summary": summary,
                "url": link,
                "publishedAt": published_at,
                "category": classification["category"],
                "confidence": classification["confidence"],
                "tags": classification["signals"],
                "sourceId": source["_id"],
                "indicatorIds": [],
            }
        )
    return items


@app.post("/api/refresh")
def refresh():
    inserted = 0
    errors = []
    for source in SOURCES:
        try:
            fetched = fetch_feed(source)
            if db is None:
                known_urls = {report["url"] for report in DEMO_REPORTS}
                new_reports = [report for report in fetched if report["url"] not in known_urls]
                DEMO_REPORTS.extend(new_reports)
                inserted += len(new_reports)
            else:
                db.sources.update_one(
                    {"_id": source["_id"]},
                    {"$set": {key: value for key, value in source.items() if key != "_id"}},
                    upsert=True,
                )
                for report in fetched:
                    result = db.reports.update_one(
                        {"url": report["url"]},
                        {"$setOnInsert": report},
                        upsert=True,
                    )
                    inserted += int(result.upserted_id is not None)
        except Exception as error:
            app.logger.warning("Feed refresh failed for %s: %s", source["name"], error)
            errors.append(f"{source['name']}: {error}")
    if errors and not inserted:
        return jsonify({"error": "No feeds could be refreshed.", "details": errors}), 502
    return jsonify({"inserted": inserted, "errors": errors})


ensure_indexes()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
