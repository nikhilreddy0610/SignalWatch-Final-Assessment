import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "admin")
BACKUP_OUTPUT_DIR = Path(os.getenv("BACKUP_OUTPUT_DIR", str(BASE_DIR / "backups")))
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

BACKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def ensure_directories() -> None:
    BACKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
