# Lab 7 Submission Report

## Student information

- **Name:** K J NIKHIL REDDY
- **USN:** 24BTRCL091
- **Course activity:** MongoDB Labs 7.1 and 7.2

## Project

**SignalWatch — Cyber Threat Intelligence Platform**

The project provides a searchable cyber-threat report dashboard, keyword-based threat classification, RSS refresh for selected public sources, and MongoDB lab scripts for schema sizing and WiredTiger working-set analysis.

## Lab 7.1 — Production schema analysis

Reports contain bounded tags, classification, source IDs, and indicator IDs. Tags and classification are embedded because they are small and commonly read with the report. Source and indicator details are stored in their own collections and referenced from reports: sources are shared among reports and indicators may be shared across reports and have independent metadata and lifecycle.

Embedding source metadata or IOC values in a report could reduce reads when displaying that report. It also duplicates data and makes source corrections, indicator updates, and cross-report queries harder. For the activity redesign, an actual-threat report can contain an embedded source snapshot and threat assessment to make the report-detail read self-contained; keeping a source reference as well supports normalized maintenance.

The `scripts/lab_01_production_schema.py` script seeds illustrative source, report, and indicator documents and measures BSON sizes using `$bsonSize`. It calculates a document-weighted overall average and verifies the largest document is well below the 16 MiB MongoDB limit. The dashboard's Lab 7.1 view also displays measured dataset sizes.

## Lab 7.2 — Working-set analysis

The `scripts/lab_02_working_set_analysis.py` script targets 100,000 BSON documents of exactly 2,048 bytes each (approximately 195.3 MiB of raw BSON documents), performs randomized reads, and samples WiredTiger cache counters from `serverStatus` every 10 seconds. It estimates the interval hit ratio from page-request and page-read counter deltas, displays cache occupancy and evictions, and polls configured RSS feeds for new reports.

The 2,048-byte target was checked using BSON encoding. Actual storage footprint is larger because WiredTiger, indexes, and filesystem storage add overhead. The hit ratio is an estimate based on counter deltas, not an independent MongoDB metric.

## Verification results

- Automated dashboard/API tests: **6 passed**.
- Lab 7.1 run against Docker MongoDB: **13 measured documents**, weighted average **334.5 bytes**, largest **492 bytes** (**0.0029%** of 16 MiB).
- Lab 7.2 dataset seeded in MongoDB: **100,000 documents**, each **2,048 BSON bytes**. A sample of 500 randomized indexed reads measured an **87.8% interval cache-hit estimate**, with no application-thread evictions in that sample. Cache counters showed about 188 MB in use of about 1.52 GB configured at the sample time. Results vary with workload and environment.
- Docker Compose app and MongoDB started; report search and `$bsonSize` API endpoints returned Mongo-backed results.

## Run and deployment

For a local Docker deployment, from the project directory:

```bash
docker compose up --build
```

Open <http://localhost:5001> (or set `HOST_PORT` to choose another host port). Compose starts MongoDB and the application, and persists MongoDB data in a named volume. See [README.md](README.md) for Python setup and lab script commands.

The application image is tagged locally as `signalwatch-cti:lab7`.

## Data and limitations

Seeded report and indicator values are illustrative training data and are not validated threat intelligence. RSS content and keyword classifications require analyst verification. Live feed refresh requires internet access. The working-set monitor requires MongoDB `serverStatus` permissions.
