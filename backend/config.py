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
