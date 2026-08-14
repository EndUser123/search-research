---
title: "how can I use find out what openrouter models are avilable for free, wtih their context window size."
date: "2025-12-05"
mode: "COPILOT"
uuid: "072696dc-f9dd-4e96-84dc-2e30a350a287"
entry_count: 2
---

## Human

how can I use find out what openrouter models are avilable for free, wtih their context window size.

## Assistant

## Finding Free OpenRouter Models

Visit the OpenRouter models page at https://openrouter.ai/models, apply the filter `max_price=0` for free models, and sort by `context-high-to-low` to view them ordered by context window size; each listing includes the model's context length, provider, and free variant indicator.[1][2][3]

## Key Free Models and Context Windows

Free models have daily rate limits (50 requests unless credits purchased), making them suitable for testing rather than production.[4][5]

Examples include:
- Sherlock Think Alpha and Dash Alpha: 1.8 million tokens (free during alpha).[6]
- GLM 4.5 Air: 200K tokens.[7]
- Grok 4.1 Fast, DeepSeek R1T2 Chimera, KAT-Coder-Pro V1: Listed as free with context details on the filtered page.[8]

## Programmatic Access

Use OpenRouter's API to query models programmatically; free variants are marked and include context specs in model metadata. Free tier details are in the FAQ and docs.[5][9]

## Human

please show me the python code to Use OpenRouter's API to query models programmatically

## Assistant

To query OpenRouter models programmatically via their OpenAI-compatible API, use a GET request to `https://openrouter.ai/api/v1/models` with your API key in the Authorization header.[1]

## Python Code Example

```python
import os
import requests
import json

api_key = os.getenv("OPENROUTER_API_KEY")  # Set your free tier API key as env var
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)

if response.status_code == 200:
    models = response.json()["data"]
    
    # Filter for free models (input/output price == 0) and show ID + context length
    free_models = []
    for model in models:
        pricing = model.get("pricing", {})
        if pricing.get("input") == 0 and pricing.get("output") == 0:
            ctx_len = model.get("context_length", "N/A")
            free_models.append({"id": model["id"], "context_length": ctx_len})
    
    print(json.dumps(free_models, indent=2))
else:
    print(f"Error: {response.status_code}")
```

This code fetches all models, filters free ones (zero input/output pricing), and prints their IDs with context window sizes.[2][1]

## OpenAI Client Alternative

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

models = client.models.list()
# Process models.data similarly, filtering on pricing.input == 0 etc.
```

Sign up at openrouter.ai for a free API key (50 req/day limit); the response includes pricing and context_length fields for filtering.[3][4][1]
