"""Measure sequential insert latency for replica-set write concerns."""

import csv
import os
import statistics
import time
import uuid

from pymongo import MongoClient, WriteConcern

DOC_COUNT = 1_000
DEFAULT_URI = (
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/"
    "?replicaSet=rs0&serverSelectionTimeoutMS=5000"
)
CONFIGURATIONS = (
    ("w:1, j:false", 1, False),
    ("w:1, j:true", 1, True),
    ("w:majority, j:false", "majority", False),
    ("w:majority, j:true", "majority", True),
    ("w:3 (all members), j:false", 3, False),
    ("w:3 (all members), j:true", 3, True),
)


def benchmark_configuration(database, run_id, label, write_concern):
    collection = database[f"{run_id}_{label}"].with_options(write_concern=write_concern)
    latencies = []
    started = time.perf_counter()

    for index in range(DOC_COUNT):
        document = {"run_id": run_id, "index": index, "label": label}
        write_started = time.perf_counter()
        collection.insert_one(document)
        latencies.append(time.perf_counter() - write_started)

    total_seconds = time.perf_counter() - started
    sorted_latencies = sorted(latencies)
    return {
        "label": label,
        "total_seconds": total_seconds,
        "average_ms": statistics.mean(latencies) * 1_000,
        "p50_ms": sorted_latencies[len(sorted_latencies) // 2] * 1_000,
        "p99_ms": sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1_000,
    }


def write_csv(results, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=("configuration", "documents", "total_seconds", "average_ms", "p50_ms", "p99_ms"),
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "configuration": result["label"],
                    "documents": DOC_COUNT,
                    "total_seconds": f'{result["total_seconds"]:.6f}',
                    "average_ms": f'{result["average_ms"]:.4f}',
                    "p50_ms": f'{result["p50_ms"]:.4f}',
                    "p99_ms": f'{result["p99_ms"]:.4f}',
                }
            )


def main():
    uri = os.getenv("REPLICA_SET_URI", DEFAULT_URI)
    output_path = os.getenv("RESULTS_CSV", "write_concern_results.csv")
    run_id = uuid.uuid4().hex[:12]
    client = MongoClient(uri, serverSelectionTimeoutMS=5_000)

    try:
        client.admin.command("ping")
        database = client[f"lab9_latency_{run_id}"]
        print(f"Connected to replica set. Inserting {DOC_COUNT:,} documents per configuration.")
        print('MongoDB has no literal w:"all"; w:3 means all three voting data-bearing members.')

        results = []
        for label, w_value, journal in CONFIGURATIONS:
            concern = WriteConcern(w=w_value, j=journal, wtimeout=30_000)
            result = benchmark_configuration(database, run_id, label, concern)
            results.append(result)
            print(f"Completed {label}")

        print()
        print(f"{'Configuration':<32} {'Total (s)':>10} {'Avg (ms)':>10} {'P50 (ms)':>10} {'P99 (ms)':>10}")
        print("-" * 76)
        for result in results:
            print(
                f'{result["label"]:<32} {result["total_seconds"]:>10.3f} '
                f'{result["average_ms"]:>10.3f} {result["p50_ms"]:>10.3f} '
                f'{result["p99_ms"]:>10.3f}'
            )

        write_csv(results, output_path)
        print(f"\nCSV results written to {output_path}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
