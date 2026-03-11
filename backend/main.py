"""FastAPI application entry point.

Configures the app with CORS middleware, database lifecycle management,
and router registration. The lifespan handler initializes the database
connection, seeds sample data, starts the background data generator,
and configures the pub/sub queue for real-time streaming.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ALLOWED_ORIGINS, DATABASE_PATH
from backend.db.connection import create_connection, initialize_schema
from backend.db.seed import seed_database
from backend.queue import sensor_queue, SensorReading
from backend.routers import dashboard, facilities, sensors, stream
from backend.tasks.generator import run_generator


async def spill_readings_to_db(readings: list[SensorReading]) -> None:
    """Callback for queue overflow — persists readings to database."""
    db = app.state.db
    await db.executemany(
        """
        INSERT INTO sensor_readings
            (asset_id, facility_id, metric_name, value, unit, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (r.asset_id, r.facility_id, r.metric_name, r.value, r.unit, r.recorded_at)
            for r in readings
        ],
    )
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection and background tasks across the application lifecycle."""
    db = await create_connection(DATABASE_PATH)
    await initialize_schema(db)
    await seed_database(db)
    app.state.db = db

    # Configure queue to spill to database when threshold reached
    sensor_queue.set_spill_callback(spill_readings_to_db)

    # Start background data generator
    generator_task = asyncio.create_task(run_generator(db))
    app.state.generator_task = generator_task

    yield

    # Cleanup: cancel generator and close database
    generator_task.cancel()
    try:
        await generator_task
    except asyncio.CancelledError:
        pass
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
app.include_router(stream.router)


@app.get("/api/health", tags=["health"])
async def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok"}
