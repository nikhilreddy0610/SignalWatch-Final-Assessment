"""Verify data replication with two data-bearing members and an arbiter."""

import sys
import time

from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError
from pymongo.write_concern import WriteConcern


PORTS = (27117, 27118, 27119)


def direct_clients() -> dict[int, MongoClient]:
    return {
        port: MongoClient(
            f"mongodb://localhost:{port}/?directConnection=true",
            serverSelectionTimeoutMS=3000,
        )
        for port in PORTS
    }


def get_status(clients: dict[int, MongoClient]) -> dict:
    last_error = None
    for client in clients.values():
        try:
            return client.admin.command("replSetGetStatus")
        except PyMongoError as error:
            last_error = error
    if last_error:
        raise last_error
    raise RuntimeError("No MongoDB members were configured")


def main() -> int:
    clients = direct_clients()
    try:
        deadline = time.monotonic() + 60
        while True:
            try:
                status = get_status(clients)
                primary = next(
                    (
                        member
                        for member in status["members"]
                        if member["stateStr"] == "PRIMARY"
                    ),
                    None,
                )
                if primary:
                    break
            except PyMongoError:
                if time.monotonic() >= deadline:
                    raise
            if time.monotonic() >= deadline:
                raise TimeoutError("No primary was elected within 60 seconds")
            time.sleep(2)

        print("Replica set rs1 status:")
        for member in status["members"]:
            print(
                f"  {member['name']}: {member['stateStr']}, "
                f"health={member['health']}"
            )
        arbiters = [
            member for member in status["members"] if member["stateStr"] == "ARBITER"
        ]
        if not arbiters:
            raise RuntimeError("No healthy arbiter is present in rs1")

        primary_port = int(primary["name"].rsplit(":", 1)[1])
        collection = clients[primary_port]["lab81_arbiter"]["replication_check"]
        result = collection.with_options(
            write_concern=WriteConcern("majority")
        ).insert_one(
            {"message": "Two data nodes plus an arbiter", "created_at": time.time()}
        )

        secondary_member = next(
            member
            for member in status["members"]
            if member["stateStr"] == "SECONDARY"
        )
        secondary_port = int(secondary_member["name"].rsplit(":", 1)[1])
        collection = clients[secondary_port].get_database(
            "lab81_arbiter", read_preference=ReadPreference.SECONDARY_PREFERRED
        )["replication_check"]
        deadline = time.monotonic() + 30
        while True:
            document = collection.find_one({"_id": result.inserted_id})
            if document:
                print(
                    f"\nSecondary read from {secondary_member['name']}: {document}"
                )
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Document was not replicated to {secondary_member['name']}"
                )
            time.sleep(1)
        print(f"Arbiter verified: {arbiters[0]['name']} (health={arbiters[0]['health']})")
        return 0
    except (PyMongoError, RuntimeError, TimeoutError) as error:
        print(f"Arbiter verification failed: {error}", file=sys.stderr)
        return 1
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
