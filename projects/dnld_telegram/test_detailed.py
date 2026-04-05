import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from src.dnld_telegram.download.client import get_client, validate_credentials

# Load environment variables first (find .env in project root)
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
load_dotenv(env_path)

print(f"Project root: {project_root}")
print(f"Env path: {env_path}")
print(f"Env file exists: {env_path.exists()}")

# Print environment variables
print(f"API_ID from env: {os.getenv('TELEGRAM_API_ID')}")
print(f"API_HASH from env: {os.getenv('TELEGRAM_API_HASH')}")
print(
    f"SESSION_STRING from env: {os.getenv('TELEGRAM_SESSION_STRING')[:10] if os.getenv('TELEGRAM_SESSION_STRING') else None}..."
)


async def test():
    try:
        # Validate and load credentials
        api_id, api_hash, session_string = validate_credentials()
        print(f"Validated credentials - API_ID: {api_id}")

        # Create the client and connect
        client = await get_client(api_id, api_hash, session_string)
        print("Client created successfully")

        # Test if client is authorized
        if await client.is_user_authorized():
            print("Client is authorized")
        else:
            print("Client is NOT authorized")

        await client.disconnect()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
