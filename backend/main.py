"""FastAPI application entry point.

Configures the app with CORS middleware, database lifecycle management,
and router registration. The lifespan handler initializes the database
connection and seeds sample data on startup, then closes cleanly on shutdown.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ALLOWED_ORIGINS, DATABASE_PATH
from backend.db.connection import create_connection, initialize_schema
from backend.db.seed import seed_database
from backend.routers import dashboard, facilities, sensors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection across the application lifecycle."""
    db = await create_connection(DATABASE_PATH)
    await initialize_schema(db)
    await seed_database(db)
    app.state.db = db
    yield
    await db.close()


app = FastAPI(
    title="Industrial Dashboard API",
    description="REST API for monitoring power stations and chemical plants",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(facilities.router)
app.include_router(sensors.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["health"])
async def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok"}
