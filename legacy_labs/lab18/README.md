# Lab 18 Threat Intelligence Comparative System

This project builds a synthetic threat intelligence pipeline that inserts the same logical dataset into MongoDB, Apache Cassandra and Neo4j, then compares latency, false-positive findings and graph structure.

## Features
- Synthetic 100,000-record threat dataset in realistic intelligence formats.
- MongoDB stores source summaries and full history.
- Cassandra uses denormalized source and type tables.
- Neo4j stores source, threat and target nodes with suspicious relationships.
- False-positive detection using transparent business rules.
- Benchmark and reporting for the four required queries.
- Docker Compose environment for local reproduction.

## Technologies
- Python 3.12
- PyMongo
- Cassandra Python Driver
- Neo4j Python Driver
- pandas, matplotlib, reportlab
- Docker Compose

## Installation
1. Copy `.env.example` to `.env` and adjust values if desired.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the services: `docker compose up -d --build`

## Generate dataset
`python -m app.main --records 100000`

## Run benchmarks
`python -m app.main --records 100000 --benchmark-only`

## Demonstrate false positives
`python -m app.main --records 100000 --false-positive-only`

## Access Neo4j
Open http://localhost:7474 with user `neo4j` and password `lab18pass`.

## Docker Hub
A Docker image may be built locally with:
`docker build -t YOUR_DOCKERHUB_USER/threat-intelligence-lab18:latest .`
Then push to Docker Hub once credentials are configured.
