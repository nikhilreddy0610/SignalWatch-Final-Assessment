import os
import uuid

from pymongo import MongoClient


uri = os.environ.get("MONGODB_URI")
if not uri:
    raise SystemExit("Set MONGODB_URI to an authenticated rs0 connection string.")

with MongoClient(uri, serverSelectionTimeoutMS=15_000) as client:
    client.admin.command("ping")
    collection = client["lab13"]["verification"]
    document = {"_id": str(uuid.uuid4()), "message": "MongoDB Lab 13 PyMongo check"}
    collection.insert_one(document)
    saved = collection.find_one({"_id": document["_id"]})
    if saved != document:
        raise RuntimeError(f"Read-back did not match inserted document: {saved!r}")
    print(f"PASS: inserted and read back document {document['_id']}")
