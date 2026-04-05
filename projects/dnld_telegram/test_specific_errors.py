import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first (find .env in project root)
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Add the src directory to the path
import sys

sys.path.insert(0, os.path.join(project_root, "src"))

from dnld_telegram.download.client import get_client, validate_credentials
from dnld_telegram.download.file_discovery_coordinator import FileDiscoveryCoordinator
from dnld_telegram.download.plugins.enumeration import enumerate_media_in_channel


async def test_specific_errors():
    """Test the specific errors we're seeing"""
    print("=== Testing Specific Errors ===")

    try:
        # 1. Test client connection
        print("1. Testing client connection...")
        api_id, api_hash, session_string = validate_credentials()
        client = await get_client(api_id, api_hash, session_string)
        print("✓ Client connected successfully")

        # 2. Test channel enumeration with a specific channel
        print("2. Testing channel enumeration...")
        channel_name = "jcexclusive"
        chat_id = -1002436706028  # From config.toml

        try:
            # Create a simple progress display mock
            class MockProgress:
                def __init__(self):
                    pass

                def log(self, msg):
                    print(f"   Progress: {msg}")

                def is_termination_requested(self):
                    return False

                def add_main_task(self, *args, **kwargs):
                    pass

                def start_main_task(self, *args, **kwargs):
                    pass

                def update_main_task(self, *args, **kwargs):
                    pass

                def complete_main_task(self, *args, **kwargs):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

            progress = MockProgress()
            termination_event = asyncio.Event()

            # Test enumeration
            result = await enumerate_media_in_channel(
                client,
                chat_id,
                limit=5,  # Small limit for testing
                channel_name=channel_name,
                incremental=True,
                progress=progress,
                termination_event=termination_event,
            )
            print(
                f"✓ Channel enumeration completed. Found {len(result.get('messages', []))} messages"
            )

        except Exception as e:
            print(f"✗ Channel enumeration failed: {e}")
            import traceback

            traceback.print_exc()

        # 3. Test database sync
        print("3. Testing database sync...")
        try:
            coordinator = FileDiscoveryCoordinator(channel_name, telegram_id=chat_id)
            discovery = await coordinator.discover_complete_file_state()
            print("✓ File discovery completed")

            sync_result = await coordinator.coordinate_sync_operations(
                discovery,
                dry_run=True,
                progress=None,  # Dry run to avoid changes
            )
            print(f"✓ Database sync test completed: {sync_result}")

        except Exception as e:
            print(f"✗ Database sync failed: {e}")
            import traceback

            traceback.print_exc()

        # Clean up
        await client.disconnect()
        print("✓ Client disconnected")

    except Exception as e:
        print(f"✗ Overall test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run with a timeout
    try:
        asyncio.run(asyncio.wait_for(test_specific_errors(), timeout=60.0))
    except TimeoutError:
        print("Test timed out after 60 seconds")
    except Exception as e:
        print(f"Test failed: {e}")
