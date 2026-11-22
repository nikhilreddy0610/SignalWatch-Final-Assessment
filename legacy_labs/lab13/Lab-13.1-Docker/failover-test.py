import os
import time

from pymongo import MongoClient, errors


uri = os.environ.get("MONGODB_URI")
if not uri:
    raise SystemExit("Set MONGODB_URI to an authenticated rs0 connection string.")

with MongoClient(uri, serverSelectionTimeoutMS=5_000) as client:
    before = client.admin.command("hello").get("me")
    if not before:
        raise RuntimeError("Could not identify the current primary.")
    print(f"Current primary: {before}")

    try:
        client.admin.command({"replSetStepDown": 30, "force": True})
    except (errors.AutoReconnect, errors.NetworkTimeout, errors.ServerSelectionTimeoutError):
        pass

    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with MongoClient(uri, serverSelectionTimeoutMS=3_000) as candidate:
                hello = candidate.admin.command("hello")
                after = hello.get("me")
                if hello.get("isWritablePrimary") and after and after != before:
                    print(f"PASS: failover elected a different primary: {after}")
                    break
        except (errors.AutoReconnect, errors.NetworkTimeout, errors.ServerSelectionTimeoutError):
            time.sleep(2)
    else:
        raise RuntimeError("FAIL: no different primary was observed within 90 seconds.")
