#!/usr/bin/env python3
"""Test the complete application flow to isolate the connection issue."""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def test_full_flow():
    """Test the complete application flow that's failing."""
    from dnld_telegram.download.client import get_client, validate_credentials
    from dnld_telegram.download.database.schema import get_connection
    from dnld_telegram.download.file_discovery_coordinator import (
        FileDiscoveryCoordinator,
    )
    from loguru import logger

    channel_name = "jcexclusive"

    try:
        # Step 1: Test client connection (this might be the issue)
        logger.info("Step 1: Testing client connection...")
        API_ID, API_HASH, SESSION_STRING = validate_credentials()
        client = await get_client(API_ID, API_HASH, SESSION_STRING)
        logger.info("✅ Client connection successful")

        # Step 2: Test database connection
        logger.info("Step 2: Testing database connection...")
        async with get_connection(channel_name) as conn:
            cursor = await conn.execute("SELECT 1")
            result = await cursor.fetchone()
            await cursor.close()
            logger.info(f"✅ Database connection successful: {result}")

        # Step 3: Test file discovery (this is where the error occurs)
        logger.info("Step 3: Testing file discovery...")
        coordinator = FileDiscoveryCoordinator(channel_name)
        database_files = await coordinator._get_database_files()
        logger.info(f"✅ File discovery successful: {len(database_files)} files")

        # Step 4: Test the specific failing function
        logger.info("Step 4: Testing complete discovery...")
        discovery = await coordinator.discover_complete_file_state()
        logger.info(
            f"✅ Complete discovery successful: {len(discovery.files_on_disk)} files on disk"
        )

        await client.disconnect()

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_flow())
