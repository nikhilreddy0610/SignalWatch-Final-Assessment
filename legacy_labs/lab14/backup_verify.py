#!/usr/bin/env python3
"""MongoDB backup utility with retention and logging."""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List

from config import BACKUP_OUTPUT_DIR, MONGODB_URI

LOG_FILE = Path(__file__).resolve().parent / "logs" / "backup.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_backup(
    uri: str = MONGODB_URI,
    output_dir: str | Path = BACKUP_OUTPUT_DIR,
    database_name: str | None = None,
    collection_name: str | None = None,
) -> Dict[str, Any]:
    backup_root = Path(output_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_root / f"backup_{timestamp}"

    command = ["mongodump", "--uri", uri, "--out", str(backup_path)]
    if database_name:
        command.extend(["--db", database_name])
    if collection_name:
        command.extend(["--collection", collection_name])

    start = time.perf_counter()
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError as exc:
        duration = time.perf_counter() - start
        logging.error("Backup FAILED because mongodump is unavailable: %s", exc)
        return {
            "success": False,
            "backup_dir": str(backup_path),
            "duration_seconds": round(duration, 2),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
        }

    duration = time.perf_counter() - start

    success = result.returncode == 0 and backup_path.exists() and any(backup_path.iterdir())
    message = (
        f"Backup {'SUCCEEDED' if success else 'FAILED'} | duration={duration:.2f}s | "
        f"path={backup_path}"
    )
    if success:
        logging.info(message)
    else:
        logging.error("%s | stderr=%s", message, result.stderr.strip())

    deleted = cleanup_old_backups(backup_root, retention_days=7)
    result_data = {
        "success": success,
        "backup_dir": str(backup_path),
        "duration_seconds": round(duration, 2),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "deleted_old_backups": deleted,
    }
    return result_data


def cleanup_old_backups(output_dir: str | Path = BACKUP_OUTPUT_DIR, retention_days: int = 7) -> List[str]:
    root = Path(output_dir)
    if not root.exists():
        return []

    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted: List[str] = []

    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if path.stat().st_mtime < cutoff.timestamp():
            shutil.rmtree(path, ignore_errors=True)
            deleted.append(str(path))
            logging.info("Deleted expired backup directory: %s", path)

    return deleted


if __name__ == "__main__":
    backup_result = run_backup()
    print(f"Backup success: {backup_result['success']}")
    print(f"Backup duration: {backup_result['duration_seconds']} seconds")
    print(f"Backup directory: {backup_result['backup_dir']}")
    cleanup_old_backups()
