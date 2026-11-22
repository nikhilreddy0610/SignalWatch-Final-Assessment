# SignalWatch — Cyber Threat Intelligence Labs 7.1 & 7.2

A compact MongoDB-backed threat intelligence dashboard and lab submission. It includes searchable reports, transparent educational classification, an embed/reference schema analysis using `$bsonSize`, and a WiredTiger working-set monitor.

Student details and the written submission summary are in [SUBMISSION_REPORT.md](SUBMISSION_REPORT.md).

## Run with Docker Compose

With Docker Desktop (or another Docker daemon) running:

```bash
docker compose up --build
```

This starts the web app and MongoDB, and stores database files in the Compose `mongo-data` volume. Open <http://localhost:5001> (or the value of `HOST_PORT`). The app seeds illustrative records on first start.

## Run the application

Requirements: Python 3.10+ and (for MongoDB mode) a reachable MongoDB server.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Set MONGO_URI if using MongoDB
python app.py
```

Open <http://127.0.0.1:5000>. Without `MONGO_URI`, the API uses a small in-memory demo dataset; dashboard search and classification still work, but the MongoDB lab scripts require a running database. To use MongoDB, set `MONGO_URI` and optionally `MONGO_DATABASE` in the shell before starting the server. `app.py` also accepts `PORT`.

The **Refresh feeds** button checks RSS feeds published by CISA, BleepingComputer, and The Hacker News. Feed access requires an internet connection. Feed parsing and keyword classification are best-effort and are not analyst-confirmed threat verdicts.

Run the local API and BSON-size checks with:

```bash
python -m unittest discover -s tests
```

## Lab 7.1 — Analyze a production schema

```bash
python scripts/lab_01_production_schema.py
```

The script seeds three sources, three reports, and two indicators into the `cyber_threat_intelligence` database (or `MONGO_DATABASE`). It replaces only those sample IDs, then uses a `$bsonSize` aggregation per collection to report count, average, minimum, and maximum BSON sizes. The overall average is document-weighted across these collections. The script checks the largest document against a conservative 75% of MongoDB's 16 MiB document limit.

### Relationship decisions

| Relationship / field | Design | Why |
|---|---|---|
| Report → tags and classification | Embed small arrays/scalars in the report | Bounded data is usually read with the report; no separate lookup is needed. |
| Report → source | Reference via `sourceId` | Many reports reuse a source; source details can change independently. A reference avoids repeated metadata and fan-out updates. |
| Report → indicators | Reference IDs via `indicatorIds` | Indicators can be shared across reports and have their own confidence, type, and lifecycle. The relationship is potentially many-to-many. |

**Embedded alternatives:** embed `{name, trustTier, url}` for the source in each report, or embed each indicator's `{type, value, confidence}` in its report. Those alternatives can make report-detail reads faster by removing lookups. They duplicate data, make corrections/global IOC search more difficult, and can leave stale copies. For the activity redesign, embed a source snapshot plus an analyst threat assessment in a report when that source is assessed as an actual threat. The report can then be read in one document read; updates and cross-report comparisons become harder. Retaining `sourceId` alongside the snapshot is a practical hybrid.

The dashboard's schema panel reports BSON sizes for its current dataset. `$bsonSize` is an aggregation operator available on MongoDB versions that support it; the script requires MongoDB 4.4+.

## Lab 7.2 — Working set analysis

```bash
python scripts/lab_02_working_set_analysis.py
```

The script inserts **100,000 BSON documents targeted to 2,048 bytes each** into `working_set_docs` (about 195.3 MiB before index and storage-engine overhead), then performs randomized reads, samples `db.serverStatus().wiredTiger.cache`, and checks the RSS feeds for new report URLs every 10 seconds. New reports are inserted into the same reports collection used by the dashboard.

The monitor reports:

- `maximum bytes configured`, `bytes currently in the cache`, and dirty bytes;
- `pages requested from the cache` and `pages read into cache`;
- `pages evicted by application threads`;
- an interval cache hit estimate: `1 - delta(pages read into cache) / delta(pages requested from the cache)`.

This is an estimate based on counter deltas, not a server-provided single cache-hit metric. `serverStatus` output and permissions vary by MongoDB deployment. If the collection already exists and has a different size, the script stops rather than replacing it. **Only use `--reset` if you intend to drop the dedicated `working_set_docs` collection.**

```bash
python scripts/lab_02_working_set_analysis.py --reset
python scripts/lab_02_working_set_analysis.py --interval 10 --reads 500
```

The expected working set is roughly 195 MiB plus indexes and storage overhead. Compare that estimate to the configured WiredTiger cache and observe the hit estimate and evictions over time; an entire working set fitting in cache is not guaranteed. Lab monitoring also polls the same RSS sources to discover reports absent from MongoDB.

## Data references

- CTI Digest: <https://ctidigest.com/> (the assignment's threat-intelligence platform reference).
- Chapter 7 sample scripts and lab notes: <https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-07>.
- RSS feeds used for live refresh: [CISA](https://www.cisa.gov/news.xml), [BleepingComputer](https://www.bleepingcomputer.com/feed/), and [The Hacker News](https://feeds.feedburner.com/TheHackersNews).

The seeded reports and indicator values are illustrative examples, not real or validated threat intelligence. Treat all third-party feed content as untrusted input.
