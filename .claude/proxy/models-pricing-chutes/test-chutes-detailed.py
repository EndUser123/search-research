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

def test_chutes_endpoints():
    """Test various Chutes API endpoints"""
    load_env()

    api_key = os.getenv('CHUTES_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Test different endpoints
    endpoints = [
        ('/chutes/', 'Main chutes endpoint'),
        ('/chutes?include_public=true', 'Chutes with public models'),
        ('/users/me', 'User info'),
        ('/users/me/quotas', 'User quotas'),
        ('/models/', 'Models endpoint'),
        ('/pricing/pricing', 'Pricing info')
    ]

    for endpoint, description in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"Endpoint: {endpoint}")

        try:
            response = requests.get(f'https://api.chutes.ai{endpoint}', headers=headers, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    if 'items' in data:
                        print(f"Items count: {len(data['items'])}")
                    if 'data' in data:
                        print(f"Data keys: {list(data['data'].keys())}")
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
                    if data:
                        print(f"First item keys: {list(data[0].keys())}")
                print("✅ Success!")
            else:
                print(f"❌ Failed: {response.text[:200]}...")

        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == '__main__':
    test_chutes_endpoints()
