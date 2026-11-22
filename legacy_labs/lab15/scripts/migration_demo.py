from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from bson import ObjectId
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
DB_NAME = os.getenv("DB_NAME", "saas_app")
TENANTS = [f"tenant_{index}" for index in range(1, 6)]
SHARED_COLLECTION = "tasks"
BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)


def get_client() -> MongoClient:
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def seed_shared_tasks() -> None:
    client = get_client()
    db = client[DB_NAME]
    collection = db[SHARED_COLLECTION]
    collection.delete_many({})
    docs: list[dict[str, Any]] = []
    for tenant in TENANTS:
        for index in range(100):
            docs.append(
                {
                    "_id": ObjectId(),
                    "tenant_id": tenant,
                    "user_id": f"user_{tenant}_{index % 10}",
                    "title": f"{tenant} task {index + 1}",
                    "description": f"Description for {tenant} task {index + 1}",
                    "priority": ["low", "medium", "high"][index % 3],
                    "status": ["open", "in_progress", "completed"][index % 3],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
    collection.insert_many(docs)
    total = collection.count_documents({})
    print(f"Seeded {total} shared tasks across {len(TENANTS)} tenants.")
    assert total == 500


def migrate_tenant_collections() -> dict[str, int]:
    client = get_client()
    db = client[DB_NAME]
    shared = db[SHARED_COLLECTION]
    totals: dict[str, int] = {}

    for tenant in TENANTS:
        collection_name = f"tasks_{tenant}"
        target = db[collection_name]
        target.drop()
        source_tasks = list(shared.find({"tenant_id": tenant}))
        for task in source_tasks:
            target.replace_one({"_id": task["_id"]}, task, upsert=True)
        counts = target.count_documents({})
        totals[tenant] = counts
        print(f"Migrated {tenant}: {counts} documents into {collection_name}.")
        assert counts == 100
    return totals


def validate_migration() -> dict[str, Any]:
    client = get_client()
    db = client[DB_NAME]
    shared = db[SHARED_COLLECTION]
    shared_total = shared.count_documents({})
    tenant_totals = {tenant: shared.count_documents({"tenant_id": tenant}) for tenant in TENANTS}
    migrated_totals: dict[str, int] = {}
    per_tenant_ids: dict[str, set[str]] = defaultdict(set)
    for doc in shared.find({}):
        per_tenant_ids[doc["tenant_id"]].add(str(doc["_id"]))

    all_ok = True
    for tenant in TENANTS:
        target = db[f"tasks_{tenant}"]
        migrated_total = target.count_documents({})
        migrated_totals[tenant] = migrated_total
        # Validate counts and no leakage.
        leaked = list(target.find({"tenant_id": {"$ne": tenant}}))
        mismatched = list(target.find({"_id": {"$nin": [ObjectId(value) for value in per_tenant_ids[tenant]]}}))
        if migrated_total != 100 or leaked or mismatched:
            all_ok = False
            print(f"Validation failed for {tenant}: migrated_total={migrated_total}, leaked={len(leaked)}, mismatched={len(mismatched)}")

    result = {
        "shared_total": shared_total,
        "tenant_totals": tenant_totals,
        "migrated_totals": migrated_totals,
        "all_ok": all_ok,
    }
    if not all_ok:
        raise AssertionError("Migration validation failed.")
    return result


def benchmark_strategy(strategy_name: str, tenant_id: str, iterations: int = 50) -> dict[str, float]:
    client = get_client()
    db = client[DB_NAME]
    collection = db[SHARED_COLLECTION]
    target = db[f"tasks_{tenant_id}"]

    def list_tasks_shared() -> None:
        list(collection.find({"tenant_id": tenant_id}).sort("created_at", 1).limit(20))

    def list_tasks_target() -> None:
        list(target.find({}).sort("created_at", 1).limit(20))

    def create_shared_task() -> None:
        doc = {
            "_id": ObjectId(),
            "tenant_id": tenant_id,
            "user_id": f"benchmark_user_{tenant_id}",
            "title": f"Benchmark task {tenant_id}",
            "description": "benchmark create",
            "priority": "medium",
            "status": "open",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        inserted = collection.insert_one(doc)
        collection.delete_one({"_id": inserted.inserted_id})

    def create_target_task() -> None:
        doc = {
            "_id": ObjectId(),
            "tenant_id": tenant_id,
            "user_id": f"benchmark_user_{tenant_id}",
            "title": f"Benchmark task {tenant_id}",
            "description": "benchmark create",
            "priority": "medium",
            "status": "open",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        inserted = target.insert_one(doc)
        target.delete_one({"_id": inserted.inserted_id})

    def analytics_shared() -> None:
        list(collection.aggregate([
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {"_id": "$tenant_id", "total": {"$sum": 1}}}
        ]))

    def analytics_target() -> None:
        _ = target.count_documents({})

    runner = {
        "document": {"list": list_tasks_shared, "create": create_shared_task, "analytics": analytics_shared},
        "collection": {"list": list_tasks_target, "create": create_target_task, "analytics": analytics_target},
    }[strategy_name]

    metrics: dict[str, float] = {}
    for label, func in runner.items():
        start = perf_counter()
        for _ in range(iterations):
            func()
        metrics[label] = perf_counter() - start
    return metrics


def write_csv(rows: list[dict[str, Any]]) -> Path:
    path = RESULTS_DIR / "benchmark_results.csv"
    fieldnames = ["strategy", "operation", "avg_seconds", "measurements"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def write_recommendation_report(rows: list[dict[str, Any]]) -> Path:
    path = RESULTS_DIR / "recommendation_report.md"
    fastest = {}
    for row in rows:
        fastest.setdefault(row["operation"], {})[row["strategy"]] = row["avg_seconds"]

    lines = [
        "# Multi-Tenant Recommendation Report",
        "",
        "## Actual benchmark summary",
        "",
        "| Strategy | Operation | Average seconds |",
        "| --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(f"| {row['strategy']} | {row['operation']} | {row['avg_seconds']:.6f} |")

    lines.extend([
        "",
        "## Document-level isolation",
        "- Advantages: simpler operational model, one shared collection, easy tenant filtering, lower infrastructure overhead.",
        "- Disadvantages: every query must include tenant_id, risk of accidental cross-tenant queries, more application-level enforcement responsibility.",
        "- Query performance: efficient for moderate tenant sizes and mixed workload; best when cross-tenant data is usually queried together.",
        "- Backup considerations: backups are easier to manage because everything is in one data set, but recovery must preserve tenant-scoped filtering discipline.",
        "- Schema evolution: lower operational cost, but schema changes affect every tenant in the same collection.",
        "",
        "## Collection-per-tenant isolation",
        "- Advantages: better physical isolation, reduced chance of accidental cross-tenant access, easier tenant-specific maintenance and security boundaries.",
        "- Disadvantages: more collections to manage, more operational complexity, higher storage and index costs.",
        "- Query performance: very strong for single-tenant analytic workloads because scans are limited to one tenant's collection; may require more connection and management overhead.",
        "- Backup considerations: tenant-by-tenant backup and restore are straightforward but require careful retention and collection-level operational automation.",
        "- Schema evolution: more isolated but changes need careful rollout across each tenant's collection.",
        "",
        "## Recommendation",
        "- Use document-level isolation for the default SaaS model when tenants are smaller or data volumes are moderate, and a shared operational profile is acceptable.",
        "- Use collection-per-tenant isolation for enterprise or compliance-sensitive tenants, workloads requiring stronger data boundaries, or cases where a single tenant's operational blast radius must remain isolated.",
        "- The benchmark data in this repository should guide the final choice for each workload and customer tier.",
    ])

    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    print("=== Step 1: seed shared collection ===")
    seed_shared_tasks()
    print("=== Step 2: migrate tenant collections ===")
    migrate_tenant_collections()
    print("=== Step 3: validate migration ===")
    validation = validate_migration()
    print("Local validation summary:")
    print(f"  Shared collection total: {validation['shared_total']}")
    print(f"  Tenant totals: {validation['tenant_totals']}")
    print(f"  Migrated totals: {validation['migrated_totals']}")
    print(f"  All valid: {validation['all_ok']}")

    print("=== Step 4: benchmark strategies ===")
    rows: list[dict[str, Any]] = []
    for strategy in ("document", "collection"):
        metrics = benchmark_strategy(strategy, "tenant_3", iterations=20)
        for operation, elapsed in metrics.items():
            rows.append({
                "strategy": strategy,
                "operation": operation,
                "avg_seconds": elapsed / 20,
                "measurements": 20,
            })
    csv_path = write_csv(rows)
    report_path = write_recommendation_report(rows)
    print(f"Benchmark CSV saved to {csv_path}")
    print(f"Recommendation report saved to {report_path}")
    print("Migration complete.")


if __name__ == "__main__":
    main()
