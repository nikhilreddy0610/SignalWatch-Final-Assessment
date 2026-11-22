# MongoDB Lab 10: Multi-document Transactions

This project contains runnable solutions for:

- **Lab 10.1:** an atomic bank transfer with insufficient-funds rollback verification and exponential-backoff retries for `TransientTransactionError`.
- **Lab 10.2:** inventory reservation and order creation in one transaction, concurrent requests against the last five units, and a throughput benchmark at 1, 4, 8, and 16 workers.

The Compose setup starts a single-node MongoDB 7 replica set, which is required for multi-document transactions.

## Run the demonstration

Requirements: Docker Engine and Docker Compose.

```sh
docker compose pull app
docker compose up --wait -d mongo
docker compose run --rm app
```

The application verifies the bank rollback and the inventory invariants (five reservations, zero stock, five orders). It then reports successful reservations per second for each benchmark concurrency level. A successful run exits with `All Lab 10 transaction checks passed.`

The app seeds and resets only its own `bank.accounts`, `bank.transactions`, `inventory.inventory`, and `inventory.orders` collections when it runs. The benchmark uses additional `BENCH-*` inventory product IDs.

Stop the replica set when done:

```sh
docker compose down
```

To remove the persisted MongoDB data as well:

```sh
docker compose down --volumes
```

## Docker Hub image

The application image is published at:

```sh
docker pull nikhil1386/mongodb-lab10:latest
```

Docker Hub repository: https://hub.docker.com/r/nikhil1386/mongodb-lab10

To rebuild and republish after changing the source:

```sh
docker build -t nikhil1386/mongodb-lab10:latest .
docker login
docker push nikhil1386/mongodb-lab10:latest
```

The image contains the Python lab application; MongoDB runs as the separate replica-set service in `compose.yaml`. Keep both services in the Compose setup when demonstrating the labs.

## Run the scripts without Compose

Python 3.12+ and `pymongo==4.9.1` are required. Point `MONGO_URI` at a replica set, then run:

```sh
MONGO_URI='mongodb://localhost:27020/?replicaSet=rs0' python run_labs.py
```

The published host port defaults to `27020` to avoid colliding with an existing local MongoDB. Override it with `MONGO_PORT` if needed.

You can run either activity independently with `python lab_10_1_bank_transfer.py` or `python lab_10_2_inventory_reservation.py`.
