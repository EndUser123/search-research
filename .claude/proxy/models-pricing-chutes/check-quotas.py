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

def check_chutes_account():
    """Check detailed Chutes account information"""
    load_env()

    api_key = os.getenv('CHUTES_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    print("="*80)
    print("CHUTES ACCOUNT DETAILS")
    print("="*80)

    # Get user info
    try:
        response = requests.get('https://api.chutes.ai/users/me', headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print(f"Username: {user_data.get('username', 'N/A')}")
            print(f"User ID: {user_data.get('user_id', 'N/A')}")
            print(f"Balance: {user_data.get('balance', 'N/A')}")
            print(f"Permissions: {user_data.get('permissions_bitmask', 'N/A')}")
            print(f"Created: {user_data.get('created_at', 'N/A')}")
        else:
            print(f"User info failed: {response.status_code}")
    except Exception as e:
        print(f"User info error: {e}")

    print("\n" + "="*80)
    print("QUOTAS")
    print("="*80)

    # Get quotas
    try:
        response = requests.get('https://api.chutes.ai/users/me/quotas', headers=headers, timeout=10)
        if response.status_code == 200:
            quotas = response.json()
            print(f"Number of quotas: {len(quotas)}")

            for i, quota in enumerate(quotas, 1):
                print(f"\nQuota {i}:")
                print(f"  Chute ID: {quota.get('chute_id', 'N/A')}")
                print(f"  Is Default: {quota.get('is_default', 'N/A')}")
                print(f"  Quota: {quota.get('quota', 'N/A')}")
                print(f"  Updated: {quota.get('updated_at', 'N/A')}")
                print(f"  Payment Refresh: {quota.get('payment_refresh_date', 'N/A')}")
        else:
            print(f"Quotas failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Quotas error: {e}")

    print("\n" + "="*80)
    print("CHUTES (MODELS)")
    print("="*80)

    # Try without public models
    try:
        response = requests.get('https://api.chutes.ai/chutes/', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            items = data.get('items', [])
            print(f"Total chutes: {total}")
            print(f"Items returned: {len(items)}")

            if items:
                for item in items:
                    print(f"  - {item.get('name', 'N/A')} (ID: {item.get('id', 'N/A')})")
            else:
                print("  No chutes found")
        else:
            print(f"Chutes failed: {response.status_code}")
    except Exception as e:
        print(f"Chutes error: {e}")

if __name__ == '__main__':
    check_chutes_account()
