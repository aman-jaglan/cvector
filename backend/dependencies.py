"""Shared FastAPI dependencies for dependency injection."""

import aiosqlite
from fastapi import Request


async def get_db(request: Request) -> aiosqlite.Connection:
    """Retrieve the database connection from application state."""
    return request.app.state.db
