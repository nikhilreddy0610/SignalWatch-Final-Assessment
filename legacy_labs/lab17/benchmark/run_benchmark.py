"""Measure local FAISS HNSW and IVF against exact brute force."""

import csv
import json
import shutil
import time

import faiss
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmark.exact_search import exact_top_k
from benchmark.generate_data import create_corpus, save_corpus, store_in_mongodb
from benchmark.hnsw_benchmark import build_hnsw, search_hnsw
from benchmark.ivf_benchmark import build_ivf, search_ivf
from benchmark.settings import QUERY_COUNT, RESULTS_DIR, TOP_K


def recall_percent(approximate: np.ndarray, exact: np.ndarray) -> float:
    overlap = sum(len(set(a).intersection(e)) for a, e in zip(approximate, exact, strict=True))
    return overlap / (len(exact) * TOP_K) * 100


def measure_search(search_fn, queries: np.ndarray) -> tuple[np.ndarray, float]:
    latencies = []
    results = []
    for query in queries:
        start = time.perf_counter()
        indices = search_fn(query.reshape(1, -1))
        latencies.append((time.perf_counter() - start) * 1000)
        results.append(indices[0])
    return np.asarray(results), float(np.mean(latencies))


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    reports_dir = RESULTS_DIR.parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    faiss.omp_set_num_threads(1)
    docs, vectors = create_corpus()
    save_corpus(docs, vectors)
    store_in_mongodb(docs, vectors)

    rng = np.random.default_rng(2026)
    sample_ids = rng.choice(len(vectors), size=QUERY_COUNT, replace=False)
    queries = vectors[sample_ids] + rng.normal(0, 0.05, (QUERY_COUNT, vectors.shape[1])).astype(np.float32)
    faiss.normalize_L2(queries)

    start = time.perf_counter()
    exact = exact_top_k(vectors, queries, TOP_K)
    exact_ms = (time.perf_counter() - start) * 1000 / QUERY_COUNT
    results = [
        {
            "Index Type": "Exact Flat (reference)",
            "Parameters": "brute-force cosine; k=20",
            "Build Time (seconds)": 0.0,
            "Average Query Latency (ms)": round(exact_ms, 3),
            "Recall (%)": 100.0,
        }
    ]
    for name, builder, searcher, params in [
        ("HNSW", build_hnsw, search_hnsw, "M=32, efConstruction=80, efSearch=64"),
        ("IVF", build_ivf, search_ivf, "nlist=100, nprobe=10, Flat"),
    ]:
        start = time.perf_counter()
        index = builder(faiss, vectors)
        build_seconds = time.perf_counter() - start
        found, latency = measure_search(lambda q: searcher(index, q), queries)
        results.append(
            {
                "Index Type": name,
                "Parameters": params,
                "Build Time (seconds)": round(build_seconds, 4),
                "Average Query Latency (ms)": round(latency, 3),
                "Recall (%)": round(recall_percent(found, exact), 2),
            }
        )

    csv_path = RESULTS_DIR / "comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    shutil.copy2(csv_path, reports_dir / "comparison.csv")

    approximate = [row for row in results if row["Index Type"] != "Exact Flat (reference)"]
    fig, axis = plt.subplots(figsize=(7, 4.5))
    for row in approximate:
        axis.scatter(row["Recall (%)"], row["Average Query Latency (ms)"], s=85, label=row["Index Type"])
        axis.annotate(row["Index Type"], (row["Recall (%)"], row["Average Query Latency (ms)"]), xytext=(6, 6), textcoords="offset points")
    axis.set(title="FAISS HNSW vs IVF: Latency and Recall", xlabel="Recall@20 (%)", ylabel="Mean query latency (ms)")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "latency_recall.png", dpi=180)
    shutil.copy2(RESULTS_DIR / "latency_recall.png", reports_dir / "latency_recall.png")
    plt.close(fig)
    print(f"Measured 5,000 vectors and {QUERY_COUNT} queries against exact top-{TOP_K}.")
    for row in results:
        print(row)
    print(f"Saved {reports_dir / 'comparison.csv'} and {reports_dir / 'latency_recall.png'}")


if __name__ == "__main__":
    main()
