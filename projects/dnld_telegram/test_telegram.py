import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

# Load credentials from environment
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

print(f"API_ID: {API_ID}")
if API_HASH:
    print(
        f"API_HASH: {API_HASH[:5]}...{API_HASH[-5:]}"
    )  # Print partial hash for security
else:
    print("API_HASH: None")
print(f"SESSION_STRING length: {len(SESSION_STRING) if SESSION_STRING else 0}")


async def test_connection():
    try:
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
        await client.connect()
        print("Connected successfully!")
        if await client.is_user_authorized():
            print("Client is authorized")
        else:
            print("Client is NOT authorized")
        await client.disconnect()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
