#!/usr/bin/env python3
"""Restore verification for MongoDB backups with isolated test databases."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from pymongo import MongoClient

from backup_verify import run_backup
from config import BACKUP_OUTPUT_DIR, MONGODB_URI


def generate_documents(count: int = 1000) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for index in range(count):
        docs.append(
            {
                "doc_id": index,
                "name": f"sample_document_{index}",
                "status": "active",
                "region": "us-east" if index % 2 == 0 else "us-west",
                "score": (index * 17) % 1000,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    return docs


def _stable_hash(documents: List[Dict[str, Any]]) -> str:
    canonical = [json.dumps(doc, sort_keys=True) for doc in documents]
    joined = "\n".join(canonical)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def verify_restore(
    uri: str = MONGODB_URI,
    database_name: str | None = None,
    collection_name: str | None = None,
    document_count: int = 1000,
    output_dir: str | Path = BACKUP_OUTPUT_DIR,
) -> Dict[str, Any]:
    database_name = database_name or f"lab14_restore_test_{uuid.uuid4().hex[:8]}"
    collection_name = collection_name or "lab14_restore_collection"

    if shutil.which("mongodump") is None or shutil.which("mongorestore") is None:
        print("[ERROR] mongodump or mongorestore is not installed on PATH.")
        return {"success": False, "database_name": database_name, "collection_name": collection_name, "error": "MongoDB tools unavailable"}

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[database_name]
    collection = db[collection_name]

    try:
        if collection_name in db.list_collection_names():
            collection.drop()

        original_docs = generate_documents(document_count)
        collection.insert_many(original_docs)
        saved_original = list(collection.find({}, {"_id": 0}).sort("doc_id", 1))
        original_hash = _stable_hash(saved_original)

        backup = run_backup(uri=uri, output_dir=output_dir, database_name=database_name, collection_name=collection_name)
        if not backup["success"]:
            print("[ERROR] Backup failed before restore verification could proceed.")
            return {"success": False, "database_name": database_name, "backup_result": backup}

        collection.update_many({}, {"$set": {"status": "modified", "region": "restored-from-backup"}})
        restored_after_change = list(collection.find({}, {"_id": 0}).sort("doc_id", 1))
        if len(restored_after_change) != len(saved_original):
            print("[ERROR] Test data changed unexpectedly before restore.")

        restore_command = [
            "mongorestore",
            "--uri",
            uri,
            "--drop",
            "--dir",
            backup["backup_dir"],
        ]
        restore_process = subprocess.run(restore_command, capture_output=True, text=True)

        restored_docs = list(collection.find({}, {"_id": 0}).sort("doc_id", 1))
        restored_hash = _stable_hash(restored_docs)
        count_ok = len(restored_docs) == len(saved_original)
        hash_ok = restored_hash == original_hash
        fields_ok = all(doc.get("status") == "active" for doc in restored_docs)
        success = count_ok and hash_ok and fields_ok

        print("SUCCESS" if success else "FAILURE")
        print(f"Document count check: {len(restored_docs)} vs {len(saved_original)}")
        print(f"Field verification: {'OK' if fields_ok else 'FAILED'}")

        return {
            "success": success,
            "database_name": database_name,
            "collection_name": collection_name,
            "document_count": len(restored_docs),
            "original_hash": original_hash,
            "restored_hash": restored_hash,
            "count_ok": count_ok,
            "hash_ok": hash_ok,
            "fields_ok": fields_ok,
            "restore_returncode": restore_process.returncode,
            "backup_result": backup,
        }
    except Exception as exc:
        print(f"[ERROR] Restore verification failed: {exc}")
        return {"success": False, "database_name": database_name, "collection_name": collection_name, "error": str(exc)}
    finally:
        client.close()


if __name__ == "__main__":
    verify_restore(document_count=1000)
