"""Database connection management and initialization.

Uses a single long-lived aiosqlite connection stored on app.state.
SQLite has no network overhead, so connection pooling is unnecessary.
"""

import aiosqlite
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


async def create_connection(database_path: str) -> aiosqlite.Connection:
    """Open a connection with optimal SQLite settings for async use."""
    db = await aiosqlite.connect(database_path)
    db.row_factory = aiosqlite.Row

    # WAL mode allows concurrent readers alongside a single writer
    await db.execute("PRAGMA journal_mode=WAL")
    # Enforce foreign key constraints (off by default in SQLite)
    await db.execute("PRAGMA foreign_keys=ON")
    # Wait up to 5 seconds when the database is locked
    await db.execute("PRAGMA busy_timeout=5000")

    return db


async def initialize_schema(db: aiosqlite.Connection) -> None:
    """Create tables and indexes if they don't exist."""
    schema_sql = SCHEMA_PATH.read_text()

    # aiosqlite doesn't support executescript, so run each statement individually
    for statement in schema_sql.split(";"):
        statement = statement.strip()
        if statement:
            await db.execute(statement)

    await db.commit()
