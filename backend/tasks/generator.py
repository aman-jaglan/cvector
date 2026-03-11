"""Background task that generates continuous sensor readings.

Produces realistic sensor data for all assets at a configurable interval,
publishing each reading to the queue for real-time streaming to dashboards.
"""

import asyncio
import math
import random
from datetime import datetime

import aiosqlite

from backend.config import DATA_GENERATOR_INTERVAL
from backend.queue import sensor_queue

# Metric profiles: baseline value, amplitude of sine variation, unit
METRIC_PROFILES = {
    "turbine": {
        "temperature": (540, 15, "°C"),
        "pressure": (12.5, 0.8, "MPa"),
        "power_consumption": (2.1, 0.3, "MW"),
        "production_output": (45, 5, "MW"),
    },
    "boiler": {
        "temperature": (480, 20, "°C"),
        "pressure": (14.0, 1.0, "MPa"),
        "power_consumption": (1.8, 0.2, "MW"),
        "production_output": (120, 10, "t/h"),
    },
    "reactor": {
        "temperature": (350, 10, "°C"),
        "pressure": (8.0, 0.5, "MPa"),
        "power_consumption": (3.5, 0.4, "MW"),
        "production_output": (28, 3, "t/h"),
    },
    "compressor": {
        "temperature": (95, 8, "°C"),
        "pressure": (22.0, 1.5, "MPa"),
        "power_consumption": (4.2, 0.5, "MW"),
        "production_output": (850, 50, "m³/h"),
    },
    "pump": {
        "temperature": (65, 5, "°C"),
        "pressure": (3.5, 0.3, "MPa"),
        "power_consumption": (0.8, 0.1, "MW"),
        "production_output": (220, 15, "m³/h"),
    },
}


def generate_sensor_value(baseline: float, amplitude: float) -> float:
    """Generate a realistic sensor value with random variation.

    Uses a combination of sine wave (for gradual drift) and random noise
    to simulate real equipment behavior.
    """
    time_factor = datetime.utcnow().timestamp()
    phase = (time_factor % 3600) / 3600 * 2 * math.pi
    sine_component = amplitude * math.sin(phase)
    noise = random.gauss(0, amplitude * 0.15)
    return round(baseline + sine_component + noise, 2)


async def generate_readings_for_assets(db: aiosqlite.Connection) -> list[dict]:
    """Generate one reading per metric for each asset in the database.

    Args:
        db: Database connection to query assets.

    Returns:
        List of reading dictionaries ready to publish to the queue.
    """
    async with db.execute(
        "SELECT id, facility_id, type FROM assets"
    ) as cursor:
        assets = await cursor.fetchall()

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    readings = []

    for asset in assets:
        asset_id = asset["id"]
        facility_id = asset["facility_id"]
        asset_type = asset["type"]

        profiles = METRIC_PROFILES.get(asset_type, {})

        for metric_name, (baseline, amplitude, unit) in profiles.items():
            value = generate_sensor_value(baseline, amplitude)
            readings.append({
                "asset_id": asset_id,
                "facility_id": facility_id,
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "recorded_at": timestamp,
            })

    return readings


async def run_generator(db: aiosqlite.Connection) -> None:
    """Main generator loop that runs until cancelled.

    Generates readings for all assets every DATA_GENERATOR_INTERVAL seconds
    and publishes them to the sensor queue.

    Args:
        db: Database connection for querying assets.
    """
    while True:
        try:
            readings = await generate_readings_for_assets(db)

            for reading_data in readings:
                await sensor_queue.publish(reading_data)

        except asyncio.CancelledError:
            break
        except Exception as e:
            # Log error but continue running
            print(f"Generator error: {e}")

        await asyncio.sleep(DATA_GENERATOR_INTERVAL)
