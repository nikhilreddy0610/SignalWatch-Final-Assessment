import random
from datetime import datetime, timedelta, timezone

THREAT_TYPES = [
    "Phishing", "Malware", "Credential Stuffing", "Botnet", "Ransomware",
    "DDoS", "Data Exfiltration", "Reconnaissance", "Exploit", "Spam Campaign"
]
SOURCES = [
    "APT-Alpha", "CobaltWatch", "DarkNimbus", "Northstar Intel", "HexShield",
    "SableRift", "VioletScouts", "Aegis Sentinel", "BluePhantom", "RedOrbit"
]
TARGETS = [
    "payroll.app", "vpn-gateway", "customer-portal", "inventory-db", "identity-stack",
    "mail-relay", "analytics-cluster", "finance-api", "hr-sso", "partner-portal"
]
SEVERITIES = ["low", "medium", "high", "critical"]
STATUSES = ["open", "investigating", "blocked", "resolved"]


def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def generate_dataset(record_count=100000, seed=42):
    random.seed(seed)
    start = datetime.now(timezone.utc) - timedelta(days=90)
    records = []
    for index in range(1, record_count + 1):
        ts = start + timedelta(minutes=index * 5 + random.randint(0, 120))
        source = random.choice(SOURCES)
        threat_type = random.choice(THREAT_TYPES)
        target = random.choice(TARGETS)
        severity = random.choice(SEVERITIES)
        confidence = random.randint(30, 99)
        source_ip = random_ip()
        destination_ip = random_ip()
        status = random.choice(STATUSES)
        is_false_positive = random.random() < 0.18
        threat_id = f"THREAT-{index:06d}"
        record = {
            "threat_id": threat_id,
            "from_source": source,
            "threat_type": threat_type,
            "target": target,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "severity": severity,
            "confidence_score": confidence,
            "timestamp": ts.isoformat(),
            "status": status,
            "is_false_positive": is_false_positive,
            "synthetic": True,
        }
        records.append(record)
    return records
