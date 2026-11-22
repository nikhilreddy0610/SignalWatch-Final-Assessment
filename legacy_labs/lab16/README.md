# NoSQL Lab 16 Submission

This project contains a complete MongoDB + Cassandra + Neo4j hybrid lab implementation with a FastAPI service, Docker Compose setup, seeding scripts, and automated submission PDF generation.

## Project structure

- `app/main.py` — FastAPI application
- `app/fraud_query_service.py` — hybrid query service with circuit breaker logic
- `app/database/mongo_db.py` — MongoDB adapter
- `app/database/cassandra_db.py` — Cassandra adapter
- `app/database/neo4j_db.py` — Neo4j adapter
- `app/configuration.py` — environment settings
- `app/seed_data.py` — data initialization routine
- `scripts/lab_16_1_university_model.py` — university enrollment modeling demo for MongoDB, Cassandra, and Neo4j
- `docker-compose.yml` — Docker orchestration
- `Dockerfile` — API image
- `tests/test_services.py` — pytest coverage for service behavior
- `generate_report.py` — PDF report generator

## Run locally

1. Use Python 3.12.x (required for compatibility with the pinned FastAPI/Pydantic stack).
2. Create a Python environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the local services via Docker Compose:

```bash
docker compose up -d --build
```

4. Access the API:

- Health: `http://localhost:8000/health`
- Transaction: `http://localhost:8000/transaction/TXN-101`
- User profile: `http://localhost:8000/user/U-1001`
- Fraud ring: `http://localhost:8000/fraud/U-1001`

## Generate the PDF report

```bash
python generate_report.py
```

The report is written to `submission_report.pdf` in the project root.

## Testing

```bash
pytest -q
```

## Notes

The services initialize automatically with sample data if the backends are reachable. If a backend is unavailable, the service returns degraded responses rather than crashing the entire application.
