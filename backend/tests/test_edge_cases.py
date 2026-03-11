"""Edge case tests for the real-time streaming system.

Tests the extreme scenarios discussed during development:
1. Queue overflow and spill to database
2. Data duplication prevention on recovery
3. Facility switching with per-facility cursors
4. Dashboard down recovery
5. High throughput (100+ readings/second)
6. Fetch performance under load
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.queue import SensorQueue, SensorReading
from backend.config import QUEUE_MAX_SIZE, QUEUE_SPILL_THRESHOLD


class TestQueueOverflow:
    """Test 1: Queue overflow triggers spill to database at 50% threshold."""

    def test_queue_spills_at_threshold(self):
        """When queue reaches 500 items, it should spill to database."""
        queue = SensorQueue()
        spilled_data = []

        async def mock_spill_callback(readings):
            spilled_data.extend(readings)

        queue.set_spill_callback(mock_spill_callback)

        async def fill_queue():
            # Fill queue to threshold
            for i in range(QUEUE_SPILL_THRESHOLD + 1):
                await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0 + i,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

        asyncio.run(fill_queue())

        # Should have spilled data to database
        assert len(spilled_data) > 0, "Queue should spill to DB at threshold"
        # Queue should be mostly empty after spill
        assert queue.size() < QUEUE_SPILL_THRESHOLD, "Queue should be cleared after spill"

    def test_no_data_loss_on_overflow(self):
        """All data should be preserved either in queue or spilled to DB."""
        queue = SensorQueue()
        spilled_data = []

        async def mock_spill_callback(readings):
            spilled_data.extend(readings)

        queue.set_spill_callback(mock_spill_callback)

        total_readings = QUEUE_SPILL_THRESHOLD + 100

        async def fill_and_count():
            for i in range(total_readings):
                await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })
            return queue.subscribe()

        remaining = asyncio.run(fill_and_count())

        # Total data = spilled + remaining in queue
        total_preserved = len(spilled_data) + len(remaining)
        assert total_preserved == total_readings, f"Expected {total_readings}, got {total_preserved}"


class TestDuplicationPrevention:
    """Test 2: No duplicate readings after dashboard reconnects."""

    def test_subscribe_clears_queue(self):
        """After subscribe, queue should be empty (no re-reading same data)."""
        queue = SensorQueue()

        async def test():
            await queue.publish({
                "asset_id": "asset-1",
                "facility_id": "fac-1",
                "metric_name": "temperature",
                "value": 100.0,
                "unit": "°C",
                "recorded_at": datetime.utcnow().isoformat(),
            })

            first_read = queue.subscribe()
            second_read = queue.subscribe()

            assert len(first_read) == 1, "First read should get the data"
            assert len(second_read) == 0, "Second read should be empty (no duplicates)"

        asyncio.run(test())

    def test_sequential_ids_for_cursor_tracking(self):
        """Each reading should have unique sequential ID for cursor tracking."""
        queue = SensorQueue()

        async def test():
            ids = []
            for i in range(10):
                reading = await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })
                ids.append(reading.id)

            # IDs should be sequential
            assert ids == list(range(1, 11)), "IDs should be sequential 1-10"

        asyncio.run(test())


class TestFacilitySwitching:
    """Test 3: Facility switching with per-facility data isolation."""

    def test_readings_have_facility_id(self):
        """Each reading should carry facility_id for filtering."""
        queue = SensorQueue()

        async def test():
            await queue.publish({
                "asset_id": "asset-1",
                "facility_id": "fac-001",
                "metric_name": "temperature",
                "value": 100.0,
                "unit": "°C",
                "recorded_at": datetime.utcnow().isoformat(),
            })
            await queue.publish({
                "asset_id": "asset-2",
                "facility_id": "fac-002",
                "metric_name": "temperature",
                "value": 200.0,
                "unit": "°C",
                "recorded_at": datetime.utcnow().isoformat(),
            })

            readings = queue.subscribe()

            fac1_readings = [r for r in readings if r.facility_id == "fac-001"]
            fac2_readings = [r for r in readings if r.facility_id == "fac-002"]

            assert len(fac1_readings) == 1, "Should have 1 reading for fac-001"
            assert len(fac2_readings) == 1, "Should have 1 reading for fac-002"
            assert fac1_readings[0].value == 100.0
            assert fac2_readings[0].value == 200.0

        asyncio.run(test())


class TestDashboardRecovery:
    """Test 4: Dashboard recovers all missed data after downtime."""

    def test_queue_preserves_data_when_not_consumed(self):
        """Data should stay in queue until consumed (simulating dashboard down)."""
        queue = SensorQueue()

        async def test():
            # Simulate dashboard down - data accumulates
            for i in range(50):
                await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0 + i,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            # Dashboard comes back - should get all 50 readings
            readings = queue.subscribe()
            assert len(readings) == 50, "Should recover all 50 readings"

        asyncio.run(test())

    def test_spilled_data_available_for_recovery(self):
        """Data spilled to DB should be queryable for recovery."""
        queue = SensorQueue()
        spilled_data = []

        async def mock_spill_callback(readings):
            spilled_data.extend(readings)

        queue.set_spill_callback(mock_spill_callback)

        async def test():
            # Fill beyond threshold to trigger spill
            for i in range(QUEUE_SPILL_THRESHOLD + 10):
                await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            # Spilled data should be available for DB recovery query
            assert len(spilled_data) > 0, "Spilled data should be available"
            # All spilled readings should have valid IDs for cursor tracking
            assert all(r.id > 0 for r in spilled_data), "All readings should have valid IDs"

        asyncio.run(test())


class TestHighThroughput:
    """Test 5: Queue handles 100+ readings in 1 second."""

    def test_queue_handles_100_readings_per_second(self):
        """Queue should handle burst of 100 readings without data loss."""
        queue = SensorQueue()

        async def test():
            start_time = time.time()

            # Publish 100 readings as fast as possible
            for i in range(100):
                await queue.publish({
                    "asset_id": f"asset-{i % 5}",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0 + i,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            elapsed = time.time() - start_time

            readings = queue.subscribe()
            assert len(readings) == 100, f"Should handle 100 readings, got {len(readings)}"
            assert elapsed < 1.0, f"Should complete in under 1 second, took {elapsed:.2f}s"

        asyncio.run(test())

    def test_queue_handles_500_readings_burst(self):
        """Queue should handle burst up to spill threshold."""
        queue = SensorQueue()
        spilled = []

        async def mock_spill(readings):
            spilled.extend(readings)

        queue.set_spill_callback(mock_spill)

        async def test():
            start_time = time.time()

            for i in range(500):
                await queue.publish({
                    "asset_id": f"asset-{i % 10}",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            elapsed = time.time() - start_time
            remaining = queue.subscribe()

            total = len(spilled) + len(remaining)
            assert total == 500, f"No data loss: expected 500, got {total}"
            assert elapsed < 2.0, f"Should handle 500 in under 2 seconds, took {elapsed:.2f}s"

        asyncio.run(test())


class TestFetchPerformance:
    """Test 6: Fetching large batches within 1 second polling interval."""

    def test_subscribe_performance_with_large_batch(self):
        """Subscribe should return large batch quickly."""
        queue = SensorQueue()

        async def test():
            # Fill queue with data
            for i in range(400):
                await queue.publish({
                    "asset_id": f"asset-{i % 10}",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0 + i,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            # Measure subscribe time
            start_time = time.time()
            readings = queue.subscribe()
            elapsed = time.time() - start_time

            assert len(readings) == 400, "Should get all 400 readings"
            assert elapsed < 0.1, f"Subscribe should be under 100ms, took {elapsed*1000:.2f}ms"

        asyncio.run(test())

    def test_reading_serialization_performance(self):
        """Converting readings to response format should be fast."""
        queue = SensorQueue()

        async def test():
            for i in range(200):
                await queue.publish({
                    "asset_id": f"asset-{i % 10}",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0 + i,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })

            readings = queue.subscribe()

            # Measure serialization time
            start_time = time.time()
            serialized = [
                {
                    "id": r.id,
                    "asset_id": r.asset_id,
                    "facility_id": r.facility_id,
                    "metric_name": r.metric_name,
                    "value": r.value,
                    "unit": r.unit,
                    "recorded_at": r.recorded_at,
                }
                for r in readings
            ]
            elapsed = time.time() - start_time

            assert len(serialized) == 200, "Should serialize all readings"
            assert elapsed < 0.05, f"Serialization should be under 50ms, took {elapsed*1000:.2f}ms"

        asyncio.run(test())


class TestPollingRaceCondition:
    """Test 5 (additional): Verify queue state consistency during concurrent access."""

    def test_concurrent_publish_and_subscribe(self):
        """Queue should handle concurrent publish and subscribe safely."""
        queue = SensorQueue()
        results = {"published": 0, "consumed": 0}

        async def publisher():
            for i in range(50):
                await queue.publish({
                    "asset_id": "asset-1",
                    "facility_id": "fac-1",
                    "metric_name": "temperature",
                    "value": 100.0,
                    "unit": "°C",
                    "recorded_at": datetime.utcnow().isoformat(),
                })
                results["published"] += 1
                await asyncio.sleep(0.01)

        async def consumer():
            await asyncio.sleep(0.05)  # Let some data accumulate
            for _ in range(10):
                readings = queue.subscribe()
                results["consumed"] += len(readings)
                await asyncio.sleep(0.05)

        async def test():
            await asyncio.gather(publisher(), consumer())

        asyncio.run(test())

        # All published data should eventually be consumed
        # (some might still be in queue)
        remaining = len(queue.subscribe())
        total_consumed = results["consumed"] + remaining

        assert total_consumed == results["published"], \
            f"Published {results['published']}, consumed {total_consumed}"
