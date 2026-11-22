import argparse
from pathlib import Path

from app.false_positive_detector import evaluate_threats
from app.threat_generator import generate_dataset
from app.mongodb.operations import MongoThreatStore
from app.cassandra.operations import CassandraThreatStore
from app.neo4j.operations import Neo4jThreatStore
from benchmark.run_benchmark import benchmark_suite


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)


def run_pipeline(records=100000, benchmark=True, false_positive_only=False):
    dataset = generate_dataset(records)

    if false_positive_only:
        flagged = evaluate_threats(dataset)
        print(f'Generated {len(flagged)} false-positive evaluation records.')
        return dataset

    try:
        mongo_store = MongoThreatStore()
        cassandra_store = CassandraThreatStore()
        neo4j_store = Neo4jThreatStore()

        mongo_store.insert_dataset(dataset)
        cassandra_store.insert_dataset(dataset)
        neo4j_store.insert_dataset(dataset)

        print(f'Inserted {len(dataset)} records into MongoDB, Cassandra and Neo4j.')
    except Exception as exc:
        print(f'Database connection unavailable: {exc}. Dataset generated locally without insertion.')
        mongo_store = cassandra_store = neo4j_store = None

    flagged = evaluate_threats(dataset[:500])
    print(f'Generated {len(flagged)} false-positive evaluation records.')
    if benchmark and mongo_store is not None and cassandra_store is not None and neo4j_store is not None:
        benchmark_suite(mongo_store, cassandra_store, neo4j_store, dataset)
    return dataset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Threat Intelligence Lab 18 demo')
    parser.add_argument('--records', type=int, default=100000)
    parser.add_argument('--benchmark-only', action='store_true')
    parser.add_argument('--false-positive-only', action='store_true')
    args = parser.parse_args()
    run_pipeline(
        records=args.records,
        benchmark=not args.benchmark_only and not args.false_positive_only,
        false_positive_only=args.false_positive_only,
    )
