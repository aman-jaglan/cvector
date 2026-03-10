"""Generate realistic sample data for the industrial monitoring system.

Creates two facilities with multiple assets each, then generates
sensor readings over the past 2 hours at 5-minute intervals. Values
use sine waves with small random noise to simulate real equipment
behavior — gradual fluctuations rather than random jumps.
"""

import math
import random
import uuid
from datetime import datetime, timedelta

import aiosqlite

# Facility definitions with their assets
FACILITIES = [
    {
        "id": "fac-001",
        "name": "Riverside Power Station",
        "type": "power_station",
        "location": "Portland, OR",
        "status": "online",
        "assets": [
            {"name": "Steam Turbine A", "type": "turbine", "status": "running"},
            {"name": "Steam Turbine B", "type": "turbine", "status": "running"},
            {"name": "Main Boiler", "type": "boiler", "status": "running"},
            {"name": "Feedwater Pump", "type": "pump", "status": "warning"},
        ],
    },
    {
        "id": "fac-002",
        "name": "Eastside Chemical Plant",
        "type": "chemical_plant",
        "location": "Houston, TX",
        "status": "online",
        "assets": [
            {"name": "Reactor Unit 1", "type": "reactor", "status": "running"},
            {"name": "Reactor Unit 2", "type": "reactor", "status": "running"},
            {"name": "Gas Compressor", "type": "compressor", "status": "running"},
        ],
    },
]

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


def generate_sensor_value(
    baseline: float, amplitude: float, time_index: int, total_points: int
) -> float:
    """Generate a realistic sensor value using a sine wave with noise.

    The sine wave provides gradual variation over time, while small
    random noise adds the irregularity seen in real sensor data.
    """
    phase = (2 * math.pi * time_index) / total_points
    sine_component = amplitude * math.sin(phase)
    noise = random.gauss(0, amplitude * 0.1)
    return round(baseline + sine_component + noise, 2)


async def seed_database(db: aiosqlite.Connection) -> None:
    """Populate the database with sample facilities, assets, and readings."""

    # Check if data already exists
    async with db.execute("SELECT COUNT(*) FROM facilities") as cursor:
        row = await cursor.fetchone()
        if row and row[0] > 0:
            return

    now = datetime.utcnow()
    reading_interval_minutes = 5
    total_points = 24  # 2 hours at 5-minute intervals

    for facility in FACILITIES:
        await db.execute(
            "INSERT INTO facilities (id, name, type, location, status) VALUES (?, ?, ?, ?, ?)",
            (facility["id"], facility["name"], facility["type"], facility["location"], facility["status"]),
        )

        for asset_def in facility["assets"]:
            asset_id = str(uuid.uuid4())

            await db.execute(
                "INSERT INTO assets (id, facility_id, name, type, status) VALUES (?, ?, ?, ?, ?)",
                (asset_id, facility["id"], asset_def["name"], asset_def["type"], asset_def["status"]),
            )

            # Generate readings for each metric over the past 2 hours
            profiles = METRIC_PROFILES[asset_def["type"]]
            readings = []

            for time_index in range(total_points):
                recorded_at = now - timedelta(minutes=(total_points - 1 - time_index) * reading_interval_minutes)
                timestamp = recorded_at.strftime("%Y-%m-%dT%H:%M:%S")

                for metric_name, (baseline, amplitude, unit) in profiles.items():
                    value = generate_sensor_value(baseline, amplitude, time_index, total_points)
                    readings.append((asset_id, facility["id"], metric_name, value, unit, timestamp))

            await db.executemany(
                "INSERT INTO sensor_readings (asset_id, facility_id, metric_name, value, unit, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                readings,
            )

    await db.commit()
