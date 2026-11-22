import os
from typing import Final

MONGO_URI: Final[str] = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
DB_NAME: Final[str] = os.getenv("DB_NAME", "saas_app")
JWT_SECRET: Final[str] = os.getenv("JWT_SECRET", "lab15-demo-secret")
JWT_ALGORITHM: Final[str] = "HS256"
RATE_LIMIT_PER_MINUTE: Final[int] = 30
RATE_LIMIT_WINDOW_SECONDS: Final[int] = 60
