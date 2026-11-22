from pathlib import Path

DIMENSIONS = 384
DOCUMENT_COUNT = 5000
QUERY_COUNT = 100
TOP_K = 20
TOPICS = [
    "ransomware incident response backups encryption",
    "phishing credential theft multifactor authentication",
    "command control dns network traffic indicators",
    "vulnerability patch management exposure",
    "malware endpoint detection persistence",
    "threat intelligence indicators confidence sharing",
    "cloud security identity access tokens",
    "data exfiltration monitoring incident containment",
    "supply chain software security advisory",
    "cyber espionage attribution campaign analysis",
]
DATA_PATH = Path(__file__).parent / "results" / "benchmark_data.npz"
RESULTS_DIR = Path(__file__).parent / "results"
