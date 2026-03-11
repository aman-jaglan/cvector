"""In-memory sensor reading queue for real-time data streaming.

Implements a producer-consumer pattern where the background generator
produces readings to the queue, and the dashboard consumes by polling.
When the queue reaches 50% capacity, readings are spilled to the
database to prevent data loss.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Awaitable

from backend.config import QUEUE_MAX_SIZE, QUEUE_SPILL_THRESHOLD


@dataclass
class SensorReading:
    """A single sensor reading ready for queue storage."""

    id: int
    asset_id: str
    facility_id: str
    metric_name: str
    value: float
    unit: str
    recorded_at: str


@dataclass
class SensorQueue:
    """Bounded queue for sensor readings with spill-to-db support.

    Attributes:
        readings: The underlying deque storing readings.
        next_id: Auto-incrementing ID for each reading.
        spill_callback: Async function called when queue needs to flush to DB.
    """

    readings: deque = field(default_factory=lambda: deque(maxlen=QUEUE_MAX_SIZE))
    next_id: int = 1
    spill_callback: Callable[[list[SensorReading]], Awaitable[None]] | None = None

    def set_spill_callback(
        self, callback: Callable[[list[SensorReading]], Awaitable[None]]
    ) -> None:
        """Set the callback function for spilling data to the database."""
        self.spill_callback = callback

    async def publish(self, reading_data: dict) -> SensorReading:
        """Add a new reading to the queue.

        If the queue reaches the spill threshold, flush half the readings
        to the database to make room for new data.

        Args:
            reading_data: Dictionary with asset_id, facility_id, metric_name,
                         value, unit, and recorded_at fields.

        Returns:
            The created SensorReading with assigned ID.
        """
        reading = SensorReading(
            id=self.next_id,
            asset_id=reading_data["asset_id"],
            facility_id=reading_data["facility_id"],
            metric_name=reading_data["metric_name"],
            value=reading_data["value"],
            unit=reading_data["unit"],
            recorded_at=reading_data["recorded_at"],
        )
        self.next_id += 1

        # Check if we need to spill to database
        if len(self.readings) >= QUEUE_SPILL_THRESHOLD and self.spill_callback:
            await self._spill_to_db()

        self.readings.append(reading)
        return reading

    async def _spill_to_db(self) -> None:
        """Flush current readings to the database and clear the queue."""
        if not self.readings or not self.spill_callback:
            return

        readings_to_persist = list(self.readings)
        self.readings.clear()
        await self.spill_callback(readings_to_persist)

    def subscribe(self) -> list[SensorReading]:
        """Drain all readings from the queue.

        Returns:
            List of all readings currently in the queue. Queue is cleared.
        """
        readings = list(self.readings)
        self.readings.clear()
        return readings

    def peek(self) -> list[SensorReading]:
        """View all readings without removing them.

        Returns:
            List of all readings currently in the queue.
        """
        return list(self.readings)

    def size(self) -> int:
        """Return the current number of readings in the queue."""
        return len(self.readings)

    def is_empty(self) -> bool:
        """Check if the queue has no readings."""
        return len(self.readings) == 0


# Global queue instance
sensor_queue = SensorQueue()
