"""Runnable solutions for MongoDB Labs 11.1 and 11.2."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pprint import pformat
from textwrap import wrap

from bson import ObjectId
from pymongo import MongoClient

DATABASE = "lab11"
DOCUMENT_COUNT = int(os.environ.get("DOCUMENT_COUNT", "10000"))
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
STUDENT_NAME = "K J NIKHIL REDDY"
STUDENT_USN = "24BTRCL091"


def evaluate_shard_keys() -> None:
    """Print the Lab 11.1 decision matrix and recommendation."""
    rows = [
        (
            "order_id",
            "Very high (usually unique)",
            "Even if random; skewed if sequential",
            "Excellent for order lookup; customer/date queries scatter",
            "Medium: depends on ID generation",
            "Good only when order-ID lookups dominate",
        ),
        (
            "customer_id",
            "High (one value per customer)",
            "Potentially skewed by heavy-order customers",
            "Excellent for customer order history",
            "Low for writes; hot customers remain concentrated",
            "Good when customer locality matters more than balance",
        ),
        (
            "order_date",
            "High over time, but temporally clustered",
            "Skewed; new dates map to the upper range",
            "Good for date ranges; customer queries scatter",
            "High for insert-heavy workloads",
            "Avoid as a sole ascending key for write-heavy traffic",
        ),
        (
            "hashed customer_id",
            "High (inherits customer cardinality)",
            "Generally even across distinct customers",
            "Good for exact customer lookups; date ranges scatter",
            "Low for distinct-customer writes; hot customers can still skew",
            "Recommended for this customer-centric workload",
        ),
    ]

    headers = ("Shard key", "Cardinality", "Distribution", "Query targeting", "Hotspot risk", "Verdict")
    widths = [19, 22, 27, 30, 30, 32]
    print("LAB 11.1 - E-COMMERCE SHARD-KEY DECISION MATRIX")
    print(" | ".join(value.ljust(width) for value, width in zip(headers, widths)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        wrapped = [
            wrap(value, width=width) or [""]
            for value, width in zip(row, widths)
        ]
        for line_index in range(max(map(len, wrapped))):
            print(
                " | ".join(
                    (lines[line_index] if line_index < len(lines) else "").ljust(width)
                    for lines, width in zip(wrapped, widths)
                )
            )
    print(
        "\nRecommendation: {customer_id: 'hashed'} is the best of these four when the "
        "dominant access pattern is customer-scoped order lookup. It spreads different "
        "customers across shards and targets equality queries by customer. Hashing does "
        "not split one customer's orders across shards, and it sacrifices useful "
        "customer/date range locality. Confirm the choice against measured query and "
        "write distributions; consider a compound key if order-date queries dominate."
    )
    print(
        "\nResharding note (MongoDB 5.0+): disable the balancer, run "
        "db.adminCommand({reshardCollection: 'db.collection', key: {customer_id: 'hashed'}}) "
        "through mongos, monitor with $currentOp, then re-enable the balancer. "
        "Plan for temporary extra disk/I/O/CPU and a brief write-blocking critical "
        "section. Only one collection resharding/move/unshard/rewrite operation can "
        "run at a time; duplicate _id values, unsupported queryable-encryption "
        "collections, uniqueness constraints, and in-progress index builds can block "
        "or fail the operation. Review version-specific documentation before production use."
    )


def explain_shards(database, collection_name: str, query: dict) -> tuple[set[str], dict]:
    result = database.command(
        "explain",
        {"find": collection_name, "filter": query},
        verbosity="queryPlanner",
    )
    names: set[str] = set()

    def collect(value) -> None:
        if isinstance(value, dict):
            shard_name = value.get("shardName")
            if isinstance(shard_name, str):
                names.add(shard_name)
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(result.get("queryPlanner", {}).get("winningPlan", {}))
    return names, result


def print_distribution(database, collection_name: str) -> None:
    stats = database.command("collStats", collection_name, scale=1)
    shard_stats = stats.get("shards", {})
    print(f"\n{collection_name}: total={stats.get('count', 0)} documents")
    if not shard_stats:
        print("  No per-shard statistics returned by this server.")
        return
    for shard, detail in sorted(shard_stats.items()):
        print(
            f"  {shard}: count={detail.get('count', 'n/a')}, "
            f"size={detail.get('size', 'n/a')} bytes"
        )


def run_hotspot_demo() -> None:
    """Build both sharded collections, insert sample data, and compare routing."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=120_000)
    client.admin.command("ping")
    database = client[DATABASE]
    client.admin.command("enableSharding", DATABASE)

    for name in ("hotspot_data", "even_data"):
        database.drop_collection(name)

    database["hotspot_data"].create_index([("ts", 1)])
    database["even_data"].create_index([("user_id", "hashed")])
    client.admin.command(
        "shardCollection",
        f"{DATABASE}.hotspot_data",
        key={"ts": 1},
    )
    client.admin.command(
        "shardCollection",
        f"{DATABASE}.even_data",
        key={"user_id": "hashed"},
        numInitialChunks=2,
    )

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    customers = [ObjectId() for _ in range(max(1, (DOCUMENT_COUNT + 4) // 5))]
    batch_size = 1000
    for offset in range(0, DOCUMENT_COUNT, batch_size):
        batch = []
        end = min(offset + batch_size, DOCUMENT_COUNT)
        for index in range(offset, end):
            timestamp = start + timedelta(seconds=index)
            batch.append(
                {
                    "ts": timestamp,
                    "user_id": customers[index % len(customers)],
                    "order_number": index,
                    "amount": round((index % 500) + 10.0, 2),
                }
            )
        database["hotspot_data"].insert_many(
            [{"ts": document["ts"], "order_number": document["order_number"], "amount": document["amount"]}
             for document in batch]
        )
        database["even_data"].insert_many(batch)

    print(f"Inserted {DOCUMENT_COUNT:,} documents into each collection.")
    print_distribution(database, "hotspot_data")
    print_distribution(database, "even_data")

    date_range = {
        "ts": {
            "$gte": start,
            "$lt": start + timedelta(seconds=DOCUMENT_COUNT),
        }
    }
    print("\nIdentical date-range query on both collections:")
    for collection_name in ("hotspot_data", "even_data"):
        shards, explain = explain_shards(database, collection_name, date_range)
        print(f"  {collection_name}: targeted shards={sorted(shards) or 'not identified'}")
        print(f"    winning plan: {pformat(explain.get('queryPlanner', {}).get('winningPlan', {}))}")

    customer_query = {"user_id": customers[0]}
    shards, explain = explain_shards(database, "even_data", customer_query)
    print("\nEquality query on the hashed shard key:")
    print(f"  even_data: targeted shards={sorted(shards) or 'not identified'}")
    print(f"  winning plan: {pformat(explain.get('queryPlanner', {}).get('winningPlan', {}))}")

    low_id = ObjectId("000000000000000000000000")
    high_id = ObjectId("ffffffffffffffffffffffff")
    hashed_range = {"user_id": {"$gte": low_id, "$lt": high_id}}
    shards, explain = explain_shards(database, "even_data", hashed_range)
    print("\nRange query on the hashed shard-key field:")
    print(f"  even_data: targeted shards={sorted(shards) or 'not identified'}")
    print(f"  winning plan: {pformat(explain.get('queryPlanner', {}).get('winningPlan', {}))}")
    print(
        "\nInterpretation: the ascending timestamp key routes new writes to the "
        "highest-key chunk, which initially resides on one shard. The hashed key's "
        "pre-split chunks distribute writes across both shards. Shard counts are "
        "a snapshot: later chunk balancing can move data, and the balancer does "
        "not remove the timestamp key's concurrent insert hotspot. A ts range "
        "targets hotspot_data but scatters on even_data because ts is not its "
        "shard key; a range on a hashed key cannot use ordered range locality."
    )
    client.close()


def main() -> None:
    import argparse

    print(f"Student: {STUDENT_NAME} | USN: {STUDENT_USN}")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "lab",
        choices=("evaluate", "hotspot", "all"),
        help="which lab to run",
    )
    arguments = parser.parse_args()
    if arguments.lab in ("evaluate", "all"):
        evaluate_shard_keys()
    if arguments.lab in ("hotspot", "all"):
        run_hotspot_demo()


if __name__ == "__main__":
    main()
