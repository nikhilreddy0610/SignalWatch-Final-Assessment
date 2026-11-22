#!/usr/bin/env python3
"""Hourly MongoDB backup scheduling with retention cleanup."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import schedule

from backup_verify import cleanup_old_backups, run_backup
from config import BACKUP_OUTPUT_DIR, MONGODB_URI

LOG_FILE = Path(__file__).resolve().parent / "logs" / "backup_scheduler.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_hourly_backup() -> None:
    logging.info("Running scheduled backup")
    result = run_backup(uri=MONGODB_URI, output_dir=BACKUP_OUTPUT_DIR)
    logging.info("Backup result: %s", result)


if __name__ == "__main__":
    schedule.every().hour.do(run_backup)
    print("[INFO] Backup scheduler active. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)
