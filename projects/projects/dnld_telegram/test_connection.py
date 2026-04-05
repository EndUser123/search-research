import asyncio
from pathlib import Path

from dotenv import load_dotenv
from src.dnld_telegram.download.client import get_client, validate_credentials


async def test_telegram_connection_and_channels():
    """Test Telegram connection and channel access"""
    # Load environment variables
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    load_dotenv(env_path)

    print("=== Testing Telegram Connection ===")

    try:
        # Validate credentials
        api_id, api_hash, session_string = validate_credentials()
        print("✓ Credentials validated")

        # Create and connect client
        client = await get_client(api_id, api_hash, session_string)
        print("✓ Client connected")

        # Test authorization
        if await client.is_user_authorized():
            print("✓ Client is authorized")
        else:
            print("✗ Client is NOT authorized")
            return

        # Test access to one of the channels from config.toml
        # jcexclusive = -1002436706028
        channel_id = -1002436706028

        try:
            print(f"Testing access to channel {channel_id}...")
            entity = await client.get_entity(channel_id)
            print(f"✓ Successfully accessed channel: {entity.title}")
        except Exception as e:
            print(f"✗ Failed to access channel {channel_id}: {e}")

        # Try to get messages from the channel
        try:
            print("Testing message retrieval...")
            messages = await client.get_messages(channel_id, limit=1)
            print(f"✓ Successfully retrieved {len(messages)} messages")
        except Exception as e:
            print(f"✗ Failed to retrieve messages: {e}")

        await client.disconnect()
        print("✓ Client disconnected")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_telegram_connection_and_channels())
