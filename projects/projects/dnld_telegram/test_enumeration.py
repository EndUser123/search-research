#!/usr/bin/env python3
"""Test the enumeration function that might be causing disconnection."""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def test_enumeration():
    """Test just the enumeration step to see where it fails."""
    from dnld_telegram.download.client import get_client, validate_credentials
    from dnld_telegram.download.plugins.enumeration import enumerate_media_in_channel
    from loguru import logger

    try:
        logger.info("Testing just the enumeration step...")
        API_ID, API_HASH, SESSION_STRING = validate_credentials()
        client = await get_client(API_ID, API_HASH, SESSION_STRING)

        logger.info("Client connected, now testing enumeration...")
        # This is what fails in the main app
        await enumerate_media_in_channel(
            client, -1002436706028, 3, "jcexclusive", True, None, None
        )
        logger.info("✅ Enumeration completed successfully")
        await client.disconnect()

    except Exception as e:
        logger.error(f"❌ Enumeration failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enumeration())
