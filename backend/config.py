"""Application configuration constants."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "industrial.db"))

# CORS origins allowed to access the API
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

API_PREFIX = "/api"

# Queue configuration for real-time data streaming
QUEUE_MAX_SIZE = 1000
QUEUE_SPILL_THRESHOLD = 500  # Flush to DB at 50% capacity

# Background data generator interval (seconds)
DATA_GENERATOR_INTERVAL = 5
