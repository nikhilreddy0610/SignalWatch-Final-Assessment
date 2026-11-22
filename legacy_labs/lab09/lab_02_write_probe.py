"""Compare w:1 and w:majority writes while one secondary is isolated."""

import os
import time
import uuid

from pymongo import MongoClient, WriteConcern
from pymongo.errors import PyMongoError

URI = os.getenv(
    "REPLICA_SET_URI",
    "mongodb://mongo1:27017/?directConnection=true&serverSelectionTimeoutMS=5000",
)


def main():
    client = MongoClient(URI, serverSelectionTimeoutMS=5_000)
    collection = client["lab9_partition"]["write_probe"]

    try:
        client.admin.command("ping")
        for label, w_value in (("w:1", 1), ("w:majority", "majority")):
            concern = WriteConcern(w=w_value, j=False, wtimeout=5_000)
            target = collection.with_options(write_concern=concern)
            started = time.perf_counter()
            try:
                target.insert_one(
                    {"probe_id": uuid.uuid4().hex, "concern": label, "created_at": time.time()}
                )
                elapsed_ms = (time.perf_counter() - started) * 1_000
                print(f"{label}: acknowledged in {elapsed_ms:.2f} ms")
            except PyMongoError as error:
                elapsed_ms = (time.perf_counter() - started) * 1_000
                print(f"{label}: failed after {elapsed_ms:.2f} ms ({type(error).__name__}: {error})")
    finally:
        client.close()


if __name__ == "__main__":
    main()
