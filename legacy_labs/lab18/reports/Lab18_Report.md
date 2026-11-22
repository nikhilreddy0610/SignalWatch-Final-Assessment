# Lab 18 Threat Intelligence Comparative System Report

- Student Name: K J NIKHIL REDDY
- USN: 24BTRCL091
- Lab 18 URL: https://hub.docker.com/r/nikhil1386/threat-intelligence-lab18

## Aim
To compare MongoDB, Apache Cassandra and Neo4j for a synthetic threat-intelligence workload, focusing on insert performance, query latency, false-positive detection and model suitability.

## Objective
- Generate realistic synthetic threat data labeled as synthetic.
- Insert the same logical dataset into all three databases.
- Benchmark the required query patterns and insert throughput.
- Produce a performance comparison and formal report.

## Procedure
1. Generate 100,000 synthetic threat records with realistic fields such as source, target, severity, confidence_score, timestamp and status.
2. Define database schemas and indexes for MongoDB, Cassandra and Neo4j.
3. Insert the dataset into each database.
4. Run benchmark queries across the databases:
   - Threat History
   - Target and Spread
   - Daily Analytics
   - Insert Throughput
5. Record median latency for 10 runs per query and generate charts.
6. Export results to CSV and PDF.

## What We Did
- Built the Python application to generate synthetic threat intelligence records.
- Implemented MongoDB source summary and full-history storage with indexing.
- Implemented Cassandra denormalized source/type tables.
- Implemented Neo4j source-target-threat graph model with suspicious relationships.
- Added false-positive detection logic.
- Generated benchmark output and a structured PDF report.

## Output
- Comparative CSV benchmark file
- Performance chart image
- Architecture diagram
- PDF report

## Result
The project generated synthetic threat records and executed the benchmark workflow successfully in code. The report clearly labels the data as synthetic. Docker image publishing was attempted, but this environment does not currently have a working Docker daemon or Docker Hub authentication, so a real `docker push` could not complete here.

## Docker status
The project is ready for Docker build/push in a machine with Docker enabled.

Example commands:

```bash
docker build -t <dockerhub-user>/threat-intelligence-lab18:latest .
docker push <dockerhub-user>/threat-intelligence-lab18:latest
```
