#!/usr/bin/env python3
"""MongoDB monitoring dashboard with alerts and logging."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from tabulate import tabulate

from config import LOG_DIR, MONGODB_URI, WEBHOOK_URL

LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "metrics.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def alert_webhook(metric_name: str, actual_value: Any, threshold: Any, timestamp: str) -> bool:
    if not WEBHOOK_URL:
        return False

    message = (
        f"[MongoDB Alert] {metric_name}: {actual_value} | threshold: {threshold} | "
        f"timestamp: {timestamp}"
    )
    payload = {"text": message}

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        logging.info("Webhook alert sent: %s", message)
        return True
    except requests.RequestException as exc:
        logging.warning("Webhook alert failure for %s: %s", metric_name, exc)
        return False


def get_replica_status(client: MongoClient) -> Dict[str, Any]:
    replica_data: Dict[str, Any] = {
        "replica_set_name": None,
        "primary_member": None,
        "secondary_members": [],
        "replication_lag_seconds": None,
        "member_health": [],
    }

    try:
        status = client.admin.command("replSetGetStatus")
    except Exception:
        return replica_data

    replica_data["replica_set_name"] = status.get("set")
    members = status.get("members", [])

    if not members:
        return replica_data

    primary = None
    primary_optime = None
    for member in members:
        state = member.get("stateStr", "UNKNOWN")
        replica_data["member_health"].append({"name": member.get("name"), "state": state})
        if state == "PRIMARY":
            primary = member.get("name")
            primary_optime = member.get("optimeDate")
        if state == "SECONDARY":
            replica_data["secondary_members"].append(member.get("name"))

    replica_data["primary_member"] = primary

    if primary_optime is not None and members:
        lag_values = []
        for member in members:
            member_optime = member.get("optimeDate")
            if member.get("stateStr") == "SECONDARY" and member_optime is not None:
                try:
                    lag_seconds = (primary_optime - member_optime).total_seconds()
                    lag_values.append(abs(lag_seconds))
                except Exception:
                    continue
        if lag_values:
            replica_data["replication_lag_seconds"] = max(lag_values)

    return replica_data


def get_cache_hit_ratio(wired_tiger: Dict[str, Any]) -> Optional[float]:
    cache = wired_tiger.get("cache", {})
    hit_ratio = cache.get("hit ratio")
    if hit_ratio is not None:
        return safe_float(hit_ratio)

    pages_read = safe_float(cache.get("pages read into cache"), 0.0)
    pages_written = safe_float(cache.get("pages written from cache"), 0.0)
    total = pages_read + pages_written
    if total <= 0:
        return None
    return round((pages_read / total) * 100, 2)


def collect_metrics(client: MongoClient) -> Dict[str, Any]:
    try:
        server_status = client.admin.command("serverStatus")
    except PyMongoError as exc:
        raise RuntimeError(f"Unable to retrieve serverStatus: {exc}") from exc

    connections = server_status.get("connections", {})
    opcounters = server_status.get("opcounters", {})
    wired_tiger = server_status.get("wiredTiger", {})
    replica_status = get_replica_status(client)

    cache_hit_ratio = get_cache_hit_ratio(wired_tiger)
    current_connections = connections.get("current", 0)
    available_connections = connections.get("available", 0)
    total_connections = connections.get("totalCreated", 0)
    metrics = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "current_connections": current_connections,
        "available_connections": available_connections,
        "total_connections": total_connections,
        "insert_ops": opcounters.get("insert", 0),
        "query_ops": opcounters.get("query", 0),
        "update_ops": opcounters.get("update", 0),
        "delete_ops": opcounters.get("delete", 0),
        "getmore_ops": opcounters.get("getmore", 0),
        "command_ops": opcounters.get("command", 0),
        "wiredtiger_cache_bytes_used": wired_tiger.get("cache", {}).get("bytes currently in the cache", 0),
        "wiredtiger_cache_max_bytes": wired_tiger.get("cache", {}).get("maximum bytes configured", 0),
        "wiredtiger_cache_dirty_bytes": wired_tiger.get("cache", {}).get("tracked dirty bytes in the cache", 0),
        "cache_hit_ratio": cache_hit_ratio,
        "replica_set_name": replica_status.get("replica_set_name"),
        "primary_member": replica_status.get("primary_member"),
        "secondary_members": replica_status.get("secondary_members"),
        "replication_lag_seconds": replica_status.get("replication_lag_seconds"),
        "member_health": replica_status.get("member_health"),
    }
    return metrics


def check_thresholds(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []

    cache_hit_ratio = metrics.get("cache_hit_ratio")
    if cache_hit_ratio is not None and cache_hit_ratio < 80:
        alerts.append(
            {
                "metric_name": "Cache hit ratio",
                "actual_value": cache_hit_ratio,
                "threshold": 80,
                "timestamp": metrics["timestamp"],
            }
        )

    lag = metrics.get("replication_lag_seconds")
    if lag is not None and lag > 10:
        alerts.append(
            {
                "metric_name": "Replication lag",
                "actual_value": lag,
                "threshold": 10,
                "timestamp": metrics["timestamp"],
            }
        )

    return alerts


def render_table(metrics: Dict[str, Any]) -> str:
    rows = [
        ["Current connections", metrics.get("current_connections", 0)],
        ["Available connections", metrics.get("available_connections", 0)],
        ["Total connections", metrics.get("total_connections", 0)],
        ["Insert ops", metrics.get("insert_ops", 0)],
        ["Query ops", metrics.get("query_ops", 0)],
        ["Update ops", metrics.get("update_ops", 0)],
        ["Delete ops", metrics.get("delete_ops", 0)],
        ["GetMore ops", metrics.get("getmore_ops", 0)],
        ["Command ops", metrics.get("command_ops", 0)],
        ["WiredTiger cache bytes used", metrics.get("wiredtiger_cache_bytes_used", 0)],
        ["WiredTiger cache dirty bytes", metrics.get("wiredtiger_cache_dirty_bytes", 0)],
        ["Cache hit ratio", f"{metrics.get('cache_hit_ratio', 'N/A')}%" if metrics.get("cache_hit_ratio") is not None else "N/A"],
        ["Replica set", metrics.get("replica_set_name") or "Standalone"],
        ["Primary member", metrics.get("primary_member") or "N/A"],
        ["Secondary members", ", ".join(metrics.get("secondary_members", [])) or "N/A"],
        ["Replication lag", f"{metrics.get('replication_lag_seconds', 'N/A')}s" if metrics.get("replication_lag_seconds") is not None else "N/A"],
    ]
    return tabulate(rows, headers=["Metric", "Value"], tablefmt="grid")


def monitor_forever(uri: str = MONGODB_URI, sleep_seconds: int = 30) -> None:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        print("[OK] Connected to MongoDB. Monitoring started. Press Ctrl+C to stop.")
        while True:
            try:
                metrics = collect_metrics(client)
                print("\n" + render_table(metrics))
                logging.info(json.dumps(metrics, default=str))

                alerts = check_thresholds(metrics)
                for alert in alerts:
                    print(f"WARNING: {alert['metric_name']} = {alert['actual_value']} exceeds threshold {alert['threshold']}.")
                    logging.warning("%s above threshold: %s > %s", alert["metric_name"], alert["actual_value"], alert["threshold"])
                    alert_webhook(
                        alert["metric_name"],
                        alert["actual_value"],
                        alert["threshold"],
                        alert["timestamp"],
                    )
            except Exception as exc:
                logging.exception("Metrics collection failed: %s", exc)
                print(f"[ERROR] Unable to collect metrics: {exc}")

            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped by user.")
    finally:
        client.close()


if __name__ == "__main__":
    monitor_forever()
