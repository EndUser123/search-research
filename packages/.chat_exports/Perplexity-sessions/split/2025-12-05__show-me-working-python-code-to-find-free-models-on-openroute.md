---
title: "show me working python code to find free models on openrouter with a context size greater than 100K tokens."
date: "2025-12-05"
mode: "COPILOT"
uuid: "e21a4c73-29f9-4245-998e-3dfc9d277eb3"
entry_count: 3
---

## Human

show me working python code to find free models on openrouter with a context size greater than 100K tokens.

## Assistant

**Use this Python script to query OpenRouter's API for free models with context lengths exceeding 100,000 tokens.**[1][2]

The script fetches the models list from the `/api/v1/models` endpoint, filters for zero input and output pricing (indicating free access), and checks the `context_length` field.  Obtain a free API key from https://openrouter.ai/keys (includes 50 requests/day limit), then set it as an environment variable.[2][3]

```python
import os
import requests
import json

# Set your free OpenRouter API key as an env var: export OPENROUTER_API_KEY=your_key_here
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("Set OPENROUTER_API_KEY environment variable")

headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "your-app-or-site",  # Optional, for leaderboard credits
    "X-Title": "Free Models Finder"
}

response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)

if response.status_code == 200:
    models = response.json().get("data", [])
    free_large_ctx = []
    
    for model in models:
        pricing = model.get("pricing", {})
        ctx_length = model.get("context_length", 0)
        
        if (pricing.get("input", None) == 0 and
            pricing.get("output", None) == 0 and
            ctx_length > 100000):
            
            free_large_ctx.append({
                "id": model["id"],
                "name": model.get("name", model["id"]),
                "context_length": ctx_length
            })
    
    print(json.dumps(free_large_ctx, indent=2))
    print(f"\nFound {len(free_large_ctx)} free models with >100K context.")
else:
    print(f"Error {response.status_code}: {response.text}")
```

## Recent Examples
Examples include Sherlock Think Alpha (1.8M tokens) and GLM 4.5 Air (200K tokens), though the list updates dynamically.[4]

## Alternatives
Use the `openai` library for OpenAI-compatible access:
```python
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
models = client.models.list().data
# Filter similarly
```
This matches your prior OpenRouter explorations.[2][1]

## Human

How to handle rate limits and pagination when listing OpenRouter models

## Assistant

## Rate Limits
OpenRouter enforces a free tier limit of 50 requests per day, with additional per-model rate limits (e.g., 10-60 RPM). Use exponential backoff retries and respect `X-RateLimit-Remaining` headers to avoid 429 errors.[1][2]

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,  # Wait 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

## Pagination
The `/api/v1/models` endpoint supports `limit` (max 100) and `after` cursor-based pagination. Fetch all models by iterating until no `next` cursor.[1]

```python
import os
import json
import requests
from typing import List, Dict

api_key = os.getenv("OPENROUTER_API_KEY")
session = create_session()

def fetch_all_free_large_context_models(min_context: int = 100000) -> List[Dict]:
    all_free_large = []
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "your-app-or-site",
        "X-Title": "Models Explorer"
    }
    
    while url:
        print(f"Fetching {url}...")
        resp = session.get(url, headers=headers)
        
        if resp.status_code == 429:
            remaining = int(resp.headers.get('X-RateLimit-Remaining', 0))
            reset = int(resp.headers.get('X-RateLimit-Reset', 0))
            print(f"Rate limited. Remaining: {remaining}. Reset: {reset}")
            time.sleep(60)  # Wait 1 min
            continue
            
        resp.raise_for_status()
        data = resp.json()
        
        models = data.get("data", [])
        for model in models:
            pricing = model.get("pricing", {})
            ctx = model.get("context_length", 0)
            if pricing.get("input") == 0 and pricing.get("output") == 0 and ctx > min_context:
                all_free_large.append({
                    "id": model["id"],
                    "name": model.get("name", model["id"]),
                    "context_length": ctx,
                    "provider": model.get("provider", {}).get("name")
                })
        
        # Pagination
        url = data.get("next")  # Full URL with cursor params
        print(f"Found {len(models)} models. Next: {bool(url)}")
        time.sleep(0.1)  # Be nice
    
    return all_free_large

# Usage
free_models = fetch_all_free_large_context_models()
print(json.dumps(free_models, indent=2))
print(f"Total: {len(free_models)} free models >100K context") [web:9][memory:1]
```

## OpenAI Client Alternative
```python
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

all_models = []
stream = client.models.list(limit=100)
all_models.extend(stream.data)

while stream.has_next():
    stream = client.models.list(limit=100, after=all_models[-1].id)
    all_models.extend(stream.data)
```
This handles pagination automatically via the SDK.[3][4]

## Human

Does the same code exist for groq and mistral?

## Assistant

## Groq API Models Listing

Groq's `/v1/models` endpoint is OpenAI-compatible, requires an API key, and lists models with `context_length`. Free tier offers limited daily inference credits.[1]

```python
import os
import requests
import json
from typing import List, Dict

api_key = os.getenv("GROQ_API_KEY")  # Get free key at console.groq.com/keys
session = requests.Session()

def fetch_groq_free_large_context(min_context: int = 100000) -> List[Dict]:
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    resp = session.get(url, headers=headers)
    resp.raise_for_status()
    
    models = resp.json().get("data", [])
    free_large = []
    
    for model in models:
        ctx = model.get("context_length", 0)
        if ctx > min_context:  # Groq models are generally free within credits
            free_large.append({
                "id": model["id"],
                "context_length": ctx
            })
    
    return free_large

# Usage
groq_models = fetch_groq_free_large_context()
print(json.dumps(groq_models, indent=2))  # llama-3.1-70b-versatile: 128K [web:4]
```

## Mistral API Models Listing

Mistral's La Plateforme API uses `/v1/models`, requires key, shows pricing and context. Free tier has 10k tokens/day limit.[1]

```python
def fetch_mistral_free_large_context(min_context: int = 100000) -> List[Dict]:
    url = "https://api.mistral.ai/v1/models"
    headers = {"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"}  # mistral.ai
    
    resp = session.get(url, headers=headers)
    resp.raise_for_status()
    
    models = resp.json().get("data", [])
    free_large = []
    
    for model in models:
        pricing = model.get("pricing", {})
        ctx = model.get("context_length", 0)
        # Filter zero-cost or free-tier eligible (check docs for current free models)
        if pricing.get("input", 0) == 0 and ctx > min_context:
            free_large.append({
                "id": model["id"],
                "name": model.get("name", model["id"]),
                "context_length": ctx
            })
    
    return free_large
```

## Unified OpenAI-Style Client
All three providers work with the `openai` library:
```python
from openai import OpenAI

providers = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1"},
    "groq": {"base_url": "https://api.groq.com/openai/v1"},
    "mistral": {"api_key": os.getenv("MISTRAL_API_KEY"), "base_url": "https://api.mistral.ai/v1"}
}

for name, config in providers.items():
    client = OpenAI(api_key=os.getenv(f"{name.upper()}_API_KEY"), **config)
    models = client.models.list().data
    large_ctx = [m for m in models if m.context_length and m.context_length > 100000]
    print(f"{name}: {len(large_ctx)} models >100K ctx")
```
Pagination and rate limiting follow the same patterns as OpenRouter.[2][3]
