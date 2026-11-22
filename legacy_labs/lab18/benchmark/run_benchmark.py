import csv
import statistics
import time
from pathlib import Path

from app.dashboard import create_architecture_diagram, create_performance_chart
from app.report_generator import generate_pdf_report


REPORTS_PATH = Path(__file__).resolve().parents[1] / 'reports'


def median_ms(values):
    return round(statistics.median(values), 3)


def run_benchmark(label, query_name, function, runs=10):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        function()
        elapsed_ms = (time.perf_counter() - start) * 1000
        samples.append(elapsed_ms)
    return {
        'database': label,
        'query': query_name,
        'run_count': runs,
        'median_latency_ms': median_ms(samples),
        'samples_ms': samples,
    }


def write_csv(results, output_file):
    fieldnames = ['database', 'query', 'run_count', 'median_latency_ms']
    with open(output_file, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            writer.writerow({
                'database': item['database'],
                'query': item['query'],
                'run_count': item['run_count'],
                'median_latency_ms': item['median_latency_ms'],
            })


def benchmark_suite(mongo_store, cassandra_store, neo4j_store, threat_dataset, sample_target='vpn-gateway'):
    mongo_results = [
        run_benchmark('MongoDB', 'Threat History', lambda: mongo_store.history_by_source('APT-Alpha')),
        run_benchmark('MongoDB', 'Target and Spread', lambda: mongo_store.threats_by_target(sample_target)),
        run_benchmark('MongoDB', 'Daily Analytics', lambda: mongo_store.daily_volume()),
    ]
    cassandra_results = [
        run_benchmark('Cassandra', 'Threat History', lambda: cassandra_store.history_by_source('APT-Alpha')),
        run_benchmark('Cassandra', 'Target and Spread', lambda: cassandra_store.threat_type_query('DDoS')),
        run_benchmark('Cassandra', 'Daily Analytics', lambda: cassandra_store.daily_volume()),
    ]
    neo4j_results = [
        run_benchmark('Neo4j', 'Threat History', lambda: neo4j_store.history_by_source('APT-Alpha')),
        run_benchmark('Neo4j', 'Target and Spread', lambda: neo4j_store.common_targets('APT-Alpha')),
        run_benchmark('Neo4j', 'Daily Analytics', lambda: neo4j_store.daily_patterns()),
    ]

    dataset = threat_dataset[:200]
    insert_mongo = mongo_store.insert_throughput(dataset, batch_size=100)
    insert_cassandra = cassandra_store.insert_throughput(dataset, batch_size=100)
    insert_neo4j = neo4j_store.insert_throughput(dataset, batch_size=100)

    throughput_rows = [
        {'database': 'MongoDB', 'query': 'Insert Throughput', 'run_count': 1, 'median_latency_ms': round((1 / insert_mongo) * 1000 if insert_mongo else 0, 3), 'throughput_rps': insert_mongo},
        {'database': 'Cassandra', 'query': 'Insert Throughput', 'run_count': 1, 'median_latency_ms': round((1 / insert_cassandra) * 1000 if insert_cassandra else 0, 3), 'throughput_rps': insert_cassandra},
        {'database': 'Neo4j', 'query': 'Insert Throughput', 'run_count': 1, 'median_latency_ms': round((1 / insert_neo4j) * 1000 if insert_neo4j else 0, 3), 'throughput_rps': insert_neo4j},
    ]
    results = mongo_results + cassandra_results + neo4j_results + throughput_rows

    output = REPORTS_PATH / 'benchmark_results.csv'
    write_csv(results, output)
    chart_output = REPORTS_PATH / 'performance_comparison.png'
    arch_output = REPORTS_PATH / 'architecture.png'
    create_performance_chart(str(output), str(chart_output))
    create_architecture_diagram(str(arch_output))
    report_output = REPORTS_PATH / 'lab18_threat_intelligence_report.pdf'
    generate_pdf_report(results, str(report_output), chart_path=str(chart_output))
    return results
