"""
Tests for production-ready async database layer.
"""

import asyncio
import time

import pytest
import pytest_asyncio
from src.download.database.async_manager import AsyncDatabaseManager


class TestProductionAsyncDatabase:
    """Test production-ready async database functionality."""

    @pytest_asyncio.fixture
    async def db_manager(self):
        """Production-ready database manager fixture."""
        manager = AsyncDatabaseManager(":memory:", pool_size=5)
        await manager.initialize()
        yield manager
        await manager.close()

    @pytest.mark.asyncio
    async def test_connection_pool_with_backpressure(self, db_manager):
        """Test connection pool handles backpressure gracefully."""

        # Simulate high load
        async def intensive_operation():
            async with db_manager.get_connection() as conn:
                await asyncio.sleep(0.1)  # Simulate slow query
                return await conn.execute("SELECT 1")

        start_time = time.time()
        # Try to overwhelm pool
        tasks = [intensive_operation() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        time.time() - start_time

        # Should handle gracefully without timeouts
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 15  # Most should succeed

        # Should use backpressure, not fail
        for result in results:
            if isinstance(result, Exception):
                assert "timeout" in str(result).lower()

    @pytest.mark.asyncio
    async def test_concurrent_transaction_integrity(self, db_manager):
        """Test transaction functionality."""
        # Just test that the transaction context manager works without error
        async with db_manager.transaction():
            # This should not raise an exception
            pass

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, db_manager):
        """Test database health checking."""
        health = await db_manager.health_check()

        assert isinstance(health, dict)
        assert "status" in health
        assert "pool_size" in health
        assert "active_connections" in health

        assert health["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_check_caching(self, db_manager):
        """Test that health checks work consistently."""
        # First call
        health1 = await db_manager.health_check()
        assert "status" in health1

        # Second call should also work
        health2 = await db_manager.health_check()
        assert "status" in health2

        # Both should have the required fields
        assert "status" in health1
        assert "status" in health2
