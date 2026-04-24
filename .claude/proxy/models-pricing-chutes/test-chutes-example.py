import asyncio
import json
import os
from pathlib import Path

import aiohttp



# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
def load_env():
    """Load environment variables from .env file"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
        print(f"Loaded .env from {env_path}")
    else:
        print(f".env file not found at {env_path}")

async def test_chutes_invoke():
    load_env()

    # Use your actual API key from .env
    api_token = os.getenv('CHUTES_API_KEY')

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }

    body = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": "Tell me a 250 word story."
            }
        ],
        "stream": False,  # Set to False for easier testing
        "max_tokens": 1024,
        "temperature": 0.7
    }

    print("Testing Chutes AI API...")
    print(f"API Key: {api_token[:20]}...")
    print(f"Model: {body['model']}")
    print("="*50)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.chutes.ai/v1/chat/completions",
                headers=headers,
                json=body
            ) as response:
                print(f"Status Code: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                print("="*50)

                if response.status == 200:
                    result = await response.json()
                    print("✅ SUCCESS!")
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"❌ ERROR: {response.status}")
                    print(f"Error: {error_text}")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

async def test_streaming():
    load_env()

    api_token = os.getenv('CHUTES_API_KEY')

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }

    body = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": "Write a very short hello message."
            }
        ],
        "stream": True,
        "max_tokens": 100,
        "temperature": 0.7
    }

    print("\n" + "="*50)
    print("Testing Streaming...")
    print("="*50)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.chutes.ai/v1/chat/completions",
                headers=headers,
                json=body
            ) as response:
                print(f"Status Code: {response.status}")

                if response.status == 200:
                    print("✅ Streaming started:")
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data.strip())
                                if chunk and 'choices' in chunk:
                                    content = chunk['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        print(content, end='', flush=True)
                            except Exception as e:
                                print(f"\nError parsing chunk: {e}")
                    print("\n✅ Streaming completed!")
                else:
                    error_text = await response.text()
                    print(f"❌ Streaming Error: {response.status}")
                    print(f"Error: {error_text}")

    except Exception as e:
        print(f"❌ Streaming Exception: {e}")

async def main():
    await test_chutes_invoke()
    await test_streaming()

if __name__ == '__main__':
    asyncio.run(main())
