"""Insert on the primary and verify the document on both secondaries."""

import sys
import time

from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError
from pymongo.write_concern import WriteConcern


PORTS = (27217, 27218, 27219)


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

        print("Replica set status:")
        for member in status["members"]:
            print(
                f"  {member['name']}: {member['stateStr']}, "
                f"health={member['health']}"
            )

        primary_port = int(primary["name"].rsplit(":", 1)[1])
        collection = clients[primary_port]["lab81"]["replication_check"]
        document = {
            "message": "Replication verified",
            "created_at": time.time(),
        }
        result = collection.with_options(
            write_concern=WriteConcern("majority")
        ).insert_one(document)
        document["_id"] = result.inserted_id
        print(f"\nInserted on primary {primary['name']}: {document}")

        secondary_members = [
            member
            for member in status["members"]
            if member["stateStr"] == "SECONDARY"
        ]
        if len(secondary_members) != 2:
            raise RuntimeError(
                f"Expected two secondaries, found {len(secondary_members)}"
            )

        for member in secondary_members:
            port = int(member["name"].rsplit(":", 1)[1])
            secondary = clients[port]
            collection = secondary.get_database(
                "lab81", read_preference=ReadPreference.SECONDARY_PREFERRED
            )["replication_check"]
            deadline = time.monotonic() + 30
            while True:
                found = collection.find_one({"_id": result.inserted_id})
                if found:
                    print(f"Read from secondary {member['name']}: {found}")
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Document was not replicated to {member['name']}"
                    )
                time.sleep(1)
        return 0
    except (PyMongoError, RuntimeError, TimeoutError) as error:
        print(f"Replica set verification failed: {error}", file=sys.stderr)
        return 1
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
