from collections import Counter, defaultdict


def classify_threat(threat, source_stats=None):
    if source_stats is None:
        source_stats = {}
    score = threat.get("confidence_score", 0)
    source_name = threat.get("from_source", "unknown")
    repeated_count = source_stats.get(source_name, {}).get("count", 0)
    target_signals = source_stats.get(source_name, {}).get("target_count", 0)
    if score < 45 and repeated_count >= 3:
        return "POSSIBLE FALSE POSITIVE", "Low confidence with repeated source activity"
    if threat.get("is_false_positive"):
        return "POSSIBLE FALSE POSITIVE", "Synthetic validation label flagged this record"
    if score >= 80 and target_signals >= 2:
        return "TRUE POSITIVE", "High confidence and repeated target targeting"
    if score < 60 and threat.get("status") in {"resolved", "blocked"}:
        return "POSSIBLE FALSE POSITIVE", "Low confidence and already resolved"
    return "NEEDS MANUAL REVIEW", "Insufficient evidence to classify confidently"


def evaluate_threats(threats):
    source_counter = Counter()
    target_counter = Counter()
    for threat in threats:
        source_counter[threat.get("from_source")] += 1
        target_counter[threat.get("target")] += 1
    stats = defaultdict(dict)
    for threat in threats:
        source = threat.get("from_source")
        stats[source]["count"] = source_counter.get(source, 0)
        stats[source]["target_count"] = target_counter.get(threat.get("target"), 0)

    results = []
    for threat in threats:
        label, reason = classify_threat(threat, stats)
        results.append({
            **threat,
            "detection_label": label,
            "detection_reason": reason,
        })
    return results
