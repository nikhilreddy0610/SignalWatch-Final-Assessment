"""Poll a replica set, read from its current primary, and report failover."""

import os
import sys
import time

from pymongo import MongoClient
from pymongo.errors import PyMongoError


PORTS = (27217, 27218, 27219)


def main() -> int:
    duration = int(os.getenv("OBSERVE_SECONDS", "90"))
    clients = {
        port: MongoClient(
            f"mongodb://localhost:{port}/?directConnection=true",
            serverSelectionTimeoutMS=3000,
        )
        for port in PORTS
    }
    last_primary = None
    deadline = time.monotonic() + duration
    print(f"Monitoring rs0 for {duration} seconds (poll interval: 2s).")
    print("In another terminal, step down the current primary.")
    try:
        while time.monotonic() < deadline:
            try:
                status = next(
                    client.admin.command("replSetGetStatus")
                    for client in clients.values()
                )
                primary = next(
                    (
                        member
                        for member in status["members"]
                        if member["stateStr"] == "PRIMARY"
                    ),
                    None,
                )
                if primary is None:
                    if last_primary is not None:
                        print("Election in progress: no PRIMARY reported.")
                    last_primary = None
                else:
                    name = primary["name"]
                    port = int(name.rsplit(":", 1)[1])
                    document = clients[port]["lab81"]["replication_check"].find_one()
                    if name != last_primary:
                        if last_primary is None:
                            print(f"PRIMARY detected: {name}")
                        else:
                            print(f"FAILOVER: {last_primary} -> {name}")
                        last_primary = name
                    print(f"Connected to {name}; read succeeded ({document is not None})")
            except PyMongoError as error:
                print(f"Temporary connection/election gap: {error.__class__.__name__}")
                last_primary = None
            time.sleep(2)
        print(f"Monitoring finished. Last primary observed: {last_primary}")
        return 0
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        return 0
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, PyMongoError) as error:
        print(f"Failover observer failed: {error}", file=sys.stderr)
        raise SystemExit(1)
