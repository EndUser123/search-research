import json
import os
from datetime import datetime

import requests


def get_chutes_models():
    """
    Fetch all public Chutes models from the API.
    Returns a list of models with metadata including usage stats.
    """
    api_key = os.getenv('CHUTES_API_KEY')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Fetch models - sorted by usage descending
    url = 'https://api.chutes.ai/chutes/'
    params = {
        'include_public': 'true',
        'include_schemas': 'false',
        'limit': 10000,
        'page': 0
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Chutes models: {e}")
        return None

def get_chutes_pricing():
    """
    Fetch current Chutes compute unit pricing.
    Returns pricing information including cost per unit.
    """
    api_key = os.getenv('CHUTES_API_KEY')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.chutes.ai/pricing/pricing'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Chutes pricing: {e}")
        return None

def list_chutes_models_with_costs():
    """
    Main function: list all Chutes models with their costs and usage.
    """
    models_data = get_chutes_models()
    pricing_data = get_chutes_pricing()

    if not models_data:
        print("Failed to fetch models.")
        return

    print("\n" + "="*80)
    print("CHUTES MODELS & PRICING")
    print("="*80)

    items = models_data.get('items', [])

    if not items:
        print("No models found.")
        return

    print(f"\nTotal models available: {len(items)}\n")
    print(f"{'Model Name':<40} {'Creator':<20} {'Usage Count':<12}")
    print("-" * 80)

    for idx, model in enumerate(items[:25], 1):  # Show top 25 by usage
        name = model.get('name', 'N/A')
        creator = model.get('creator', 'N/A')
        usage_count = model.get('usage_count', 0)

        print(f"{name:<40} {creator:<20} {usage_count:<12}")

    if len(items) > 25:
        print(f"\n... and {len(items) - 25} more models")

    # Print pricing info if available
    if pricing_data:
        print("\n" + "="*80)
        print("PRICING INFO")
        print("="*80)
        print(json.dumps(pricing_data, indent=2))

    print("\n" + "="*80)
    print(f"Last updated: {datetime.now().isoformat()}")
    print("="*80)

if __name__ == '__main__':
    list_chutes_models_with_costs()
