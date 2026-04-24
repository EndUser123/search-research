import os
from pathlib import Path

import requests



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

def test_chutes_api():
    """Test Chutes API connection"""
    load_env()

    api_key = os.getenv('CHUTES_API_KEY')
    print(f"CHUTES_API_KEY found: {bool(api_key)}")
    if api_key:
        print(f"Key starts with: {api_key[:10]}...")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Test simple API call
    try:
        response = requests.get('https://api.chutes.ai/chutes/', headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            items = data.get('items', [])
            print(f"Found {len(items)} models")

            # Show first few models
            for i, model in enumerate(items[:5], 1):
                name = model.get('name', 'N/A')
                creator = model.get('creator', 'N/A')
                usage = model.get('usage_count', 0)
                print(f"{i}. {name} by {creator} (usage: {usage})")

        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == '__main__':
    test_chutes_api()
