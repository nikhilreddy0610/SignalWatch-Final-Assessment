# Lab 15: Multi-Tenant SaaS with FastAPI and MongoDB

This project completes the two-part assignment described in the professor's sample repository:

- Lab 15.1: design a document-level multi-tenant API using FastAPI + MongoDB with JWT auth and rate limiting.
- Lab 15.2: migrate tenant data from a shared collection into separate collection-per-tenant structures and validate the result.

## Project layout

- `app/` – FastAPI application and MongoDB helpers.
- `scripts/` – seeding, migration, and benchmark scripts.
- `tests/` – API and security tests for tenant isolation and rate limiting.
- `docker-compose.yml` – MongoDB + API startup configuration.

## Quick start

1. Start the Docker Hub image and MongoDB:
   `docker compose up -d`
2. The API is available at `http://localhost:8000/docs`.
3. To run locally instead, install dependencies:
   `python3 -m pip install -r requirements.txt`
4. Start the local API:
   `uvicorn app.main:app --reload`
5. Use the demo token route to create a JWT for a tenant/user.

Docker Hub image: https://hub.docker.com/r/nikhil1386/mongodb-lab15

## Demo requests

```bash
curl -X POST http://localhost:8000/auth/demo-token \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"tenant_1","user_id":"user_42","role":"ADMIN"}'
```

Use the returned token as a bearer token in subsequent requests.

## Validation

Run the API tests with:

```bash
pytest -q
```

Run the migration and benchmark script with:

```bash
python3 scripts/migration_demo.py
```
