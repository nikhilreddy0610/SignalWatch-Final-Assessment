"""Run both Chapter 10 transaction labs against the configured MongoDB replica set."""

import os

from pymongo import MongoClient

from lab_10_1_bank_transfer import run_demo as run_bank_transfer
from lab_10_2_inventory_reservation import run_demo as run_inventory_reservation

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")


def main() -> None:
    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=10_000) as client:
        client.admin.command("ping")
        run_bank_transfer(client)
        run_inventory_reservation(client)
    print("\nAll Lab 10 transaction checks passed.")


if __name__ == "__main__":
    main()
