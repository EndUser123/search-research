---
title: "did we develop code to enumerate chutes llm providers models?"
date: "2025-12-20"
mode: "COPILOT"
uuid: "e51f6d1a-2ff6-40ce-800c-3752bba3cb47"
entry_count: 2
---

## Human

did we develop code to enumerate chutes llm providers models?

## Assistant

Yes, there is code in your setup that effectively enumerates Chutes LLM provider models, but it is currently driven by a static model list rather than a live “list models” API call.[1]

## Where enumeration happens

- The unified LiteLLM proxy uses a YAML model list that includes both OpenRouter and **Chutes** routes, so all Chutes models are declared there.[1]
- `cc_menu.ps1` reads that unified config and presents the models under a `PROVIDER: CHUTES` section with numbered entries, which gives you a menu-based enumeration of available Chutes models.[2][1]

## Related helper scripts

- `cc_speed_test.ps1` reuses the same model list and prints latency results grouped by provider, including all Chutes routes, which is another form of enumeration.[2]
- The quota checker (`api_quota_checker.py`) is provider-aware (OpenRouter vs Chutes) but focuses on usage/credits, not on listing models beyond what is defined in the YAML.[3]

## What does *not* exist yet

- There is no Python or PowerShell code that calls a Chutes “list models” endpoint to dynamically discover all models at runtime; everything for Chutes is still based on the static LiteLLM config.[3]

If you want, the next step can be to add a small Python helper that calls a Chutes models endpoint (if exposed) and regenerates the Chutes section of your LiteLLM model list automatically.

## Human

I really thought there was.  Please research what the chutes code would be to list the models and their costs.

## Assistant

Perfect—I found it. Here's the Chutes API code to list models and their costs:

## Key Findings

From the research, the **Chutes list models endpoint** is:

```
GET https://api.chutes.ai/chutes/?include_public=true&include_schemas=false&limit=10000
```

**With authentication:**
```
GET https://api.chutes.ai/chutes/?include_public=true&include_schemas=false&limit=10000
Authorization: Bearer $CHUTES_API_KEY
```


***

## Python Code to Enumerate Chutes Models & Costs

Here's a complete Python script to fetch Chutes models and pricing:

```python
import requests
import os
import json
from datetime import datetime

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
```

***

## Bash/cURL One-Liners

If you just want quick outputs without Python:

**List model names only (no auth required):**
```bash
curl -s "https://api.chutes.ai/chutes/?include_public=true&include_schemas=false&limit=10000" | jq -r '.items[].name'
```

**With auth (API key):**
```bash
curl -s "https://api.chutes.ai/chutes/?include_public=true&include_schemas=false&limit=10000" \
  -H "Authorization: Bearer $CHUTES_API_KEY" | jq -r '.items[] | "\(.name) - by \(.creator) (usage: \(.usage_count))"'
```

**Get pricing:**
```bash
curl -s "https://api.chutes.ai/pricing/pricing" \
  -H "Authorization: Bearer $CHUTES_API_KEY" | jq '.'
```

***

## What's Returned

The `/chutes/` endpoint returns:
- `items[]` — array of model/chute objects
  - `name` — model name  
  - `creator` — who deployed it  
  - `usage_count` — how many times it's been invoked (sorted descending)  
  - Other fields: `id`, `public`, `description`, etc.

The `/pricing/pricing` endpoint returns compute unit costs (how much it costs per unit of inference).

***

**Would you like me to integrate this into a PowerShell script that updates your LiteLLM model list dynamically?** That way `cc_menu.ps1` could always show the latest Chutes offerings.
