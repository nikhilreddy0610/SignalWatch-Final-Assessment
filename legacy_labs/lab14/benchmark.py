#!/usr/bin/env python3
"""Benchmark backup and restore performance for multiple document counts."""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid
from typing import Dict, List

from pymongo import MongoClient
from tabulate import tabulate

from backup_verify import run_backup
from config import BACKUP_OUTPUT_DIR, MONGODB_URI
from restore_verify import generate_documents, verify_restore


def benchmark_document_count(uri: str, database_name: str, collection_name: str, document_count: int) -> Dict[str, object]:
    if shutil.which("mongodump") is None or shutil.which("mongorestore") is None:
        return {
            "document_count": document_count,
            "backup_time": "N/A",
            "restore_time": "N/A",
            "verification": "SKIPPED (MongoDB tools missing)",
            "restore_returncode": 127,
        }

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[database_name]
    collection = db[collection_name]
    collection.drop()

    documents = generate_documents(document_count)
    collection.insert_many(documents)

    backup_start = time.perf_counter()
    backup_result = run_backup(uri=uri, output_dir=BACKUP_OUTPUT_DIR, database_name=database_name, collection_name=collection_name)
    backup_duration = time.perf_counter() - backup_start

    collection.update_many({}, {"$set": {"status": "modified", "region": "benchmark-restore"}})

    restore_start = time.perf_counter()
    restore_command = [
        "mongorestore",
        "--uri",
        uri,
        "--drop",
        "--dir",
        backup_result["backup_dir"],
    ]
    restore_process = subprocess.run(restore_command, capture_output=True, text=True)
    restore_duration = time.perf_counter() - restore_start

    restored_docs = list(collection.find({}, {"_id": 0}).sort("doc_id", 1))
    verification = "SUCCESS" if len(restored_docs) == document_count and all(doc.get("status") == "active" for doc in restored_docs) else "FAILURE"
    client.close()

    return {
        "document_count": document_count,
        "backup_time": round(backup_duration, 3),
        "restore_time": round(restore_duration, 3),
        "verification": verification,
        "restore_returncode": restore_process.returncode,
    }


def benchmark_suite(uri: str = MONGODB_URI, output_dir: str = str(BACKUP_OUTPUT_DIR)) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    document_counts = [1000, 10000, 100000]

    for document_count in document_counts:
        db_name = f"lab14_benchmark_{uuid.uuid4().hex[:8]}"
        collection_name = f"benchmark_set_{document_count}"
        result = benchmark_document_count(uri, db_name, collection_name, document_count)
        results.append(result)

    print(
        tabulate(
            [[r["document_count"], r["backup_time"], r["restore_time"], r["verification"]] for r in results],
            headers=["Document Count", "Backup Time", "Restore Time", "Verification"],
            tablefmt="grid",
        )
    )
    return results


if __name__ == "__main__":
    benchmark_suite()
