# MongoDB Lab 14: Monitoring, Backup, and Restore Verification

This project implements the two required lab activities for MongoDB operational monitoring and disaster-recovery validation:

1. Lab 14.1: Monitoring dashboard
2. Lab 14.2: Backup and restore verification

## Files

- `monitoring.py` – live MongoDB monitoring dashboard with terminal table output, metric logging, and threshold alerts.
- `backup_verify.py` – automated `mongodump` backup with log capture, success/failure detection, and retention cleanup.
- `restore_verify.py` – isolated restore verification for a test database and collection.
- `benchmark.py` – benchmark script for backup and restore timings across 1,000, 10,000, and 100,000 documents.
- `backup_scheduler.py` – runs hourly backups using the `schedule` library.
- `config.py` – environment-driven configuration for connection details and backup paths.
- `requirements.txt` – Python dependencies for the lab.

## Prerequisites

- Python 3.9+
- MongoDB running locally or remotely
- MongoDB Database Tools installed and on your `PATH` (`mongodump`, `mongorestore`)
- Docker Desktop with Docker Compose (for the containerized demonstration)

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Configuration

Set environment variables before running the scripts:

```bash
export MONGODB_URI="mongodb://localhost:27017"
export BACKUP_OUTPUT_DIR="./backups"
export LOG_DIR="./logs"
export WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

If these variables are not set, the scripts use default values:

- `MONGODB_URI`: `mongodb://localhost:27017`
- `BACKUP_OUTPUT_DIR`: `./backups`
- `LOG_DIR`: `./logs`
- `WEBHOOK_URL`: not set by default

## Lab 14.1: Monitoring Dashboard

Run the dashboard:

```bash
python3 monitoring.py
```

What it does:

- Connects to MongoDB using PyMongo.
- Reads `serverStatus` metrics including connection information, operation counters, and WiredTiger cache statistics.
- Collects replica set information using `replSetGetStatus` when available.
- Prints a clean terminal table of key metrics.
- Writes values to `logs/metrics.log` every 30 seconds.
- Triggers warnings when:
  - cache hit ratio is below 80%
  - replication lag exceeds 10 seconds
- Sends optional webhook alerts if `WEBHOOK_URL` is configured.

## Lab 14.2: Automated Backup and Restore Verification

Run a single verification cycle:

```bash
python3 restore_verify.py
```

This verifies the following sequence:

1. Create an isolated test database and collection.
2. Insert 1,000 test documents.
3. Save the original data.
4. Perform a `mongodump` backup.
5. Modify the documents.
6. Run `mongorestore` against the dedicated test database.
7. Verify document count and important field values.
8. Print `SUCCESS` or `FAILURE` based on the result.

Run a backup directly:

```bash
python3 backup_verify.py
```

Run the hourly scheduler:

```bash
python3 backup_scheduler.py
```

The scheduler runs `run_backup()` on an hourly schedule and also performs a seven-day retention cleanup.

## Benchmarking

Run benchmark tests:

```bash
python3 benchmark.py
```

This measures backup and restore time for:

- 1,000 documents
- 10,000 documents
- 100,000 documents

The script prints a professional table in the form:

| Document Count | Backup Time | Restore Time | Verification |
|---|---:|---:|---|
| 1,000 | ... | ... | SUCCESS / FAILURE |
| 10,000 | ... | ... | SUCCESS / FAILURE |
| 100,000 | ... | ... | SUCCESS / FAILURE |

If the 100,000-document benchmark exceeds the time limit, the smaller benchmarks are still completed and the remaining test is reported as not executed or delayed, without fabricating results.

## Backup Retention Policy

Backups are kept for seven days. Any backup directories older than seven days are removed automatically and logged.

## RPO / RTO

- RPO: 1 hour, based on the hourly backup schedule.
- RTO: depends on the actual restore duration measured during verification. A verified restore is the basis for an operational RTO estimate.

## Notes

- The project uses an isolated test database to avoid overwriting an application database.
- Webhook delivery is optional; basic monitoring does not require webhook credentials.
- Missing or unavailable metrics are handled safely so the monitoring loop keeps running.

## Docker Demonstration

The Docker image contains the Python lab scripts and MongoDB Database Tools. Docker Compose starts a MongoDB 7.0 server and the monitoring dashboard; backup and restore outputs persist under the local `backups/` and `logs/` directories.

Pull the published app image and start the demonstration:

```bash
docker compose pull lab14
docker compose up -d
docker compose logs -f lab14
```

In another terminal, run restore verification and benchmarks against the Compose MongoDB service:

```bash
docker compose run --rm lab14 python3 restore_verify.py
docker compose run --rm lab14 python3 benchmark.py
```

Run an hourly backup scheduler:

```bash
docker compose run --rm lab14 python3 backup_scheduler.py
```

The MongoDB service is published on host port `27021` to avoid conflicts with other local MongoDB containers. The app container connects to `mongodb://mongo:27017` over the Compose network. To stop the demo, use `docker compose down`.

To publish the built application image to Docker Hub, tag it with your Docker Hub namespace and push it:

```bash
docker buildx build --platform linux/arm64 \
  -t nikhil1386/mongodb-lab14-demo:1.0.0 \
  -t nikhil1386/mongodb-lab14-demo:latest \
  --push .
```

Docker Hub repository: https://hub.docker.com/r/nikhil1386/mongodb-lab14-demo
