---
title: "chutes.ai cookbook"
date: "2025-12-11"
mode: "CONCISE"
uuid: "0eb9f92b-040f-44d2-bed2-653b46eb22de"
entry_count: 4
---

## Human

chutes.ai cookbook

## Assistant

Chutes.ai is a serverless AI compute platform for deploying and scaling open-source models via "chutes," which are containerized AI applications with OpenAI-compatible APIs.[1][9]

## Core Features
Chutes supports rapid deployment of custom AI apps using Docker images, VLLM for inference, and GPU acceleration on a decentralized network. Users build images with commands like `chutes build`, deploy via CLI or API, and access endpoints for chat completions, streaming, and custom functions decorated with `@chute.cord()`. Pay-per-use billing applies only during active inference.[2][3]

## Documentation Guides
The platform's docs include quickstarts for first deployments, custom chute creation (e.g., sentiment analysis with transformers), error handling, and integrations like Vercel AI SDK. Examples cover audio processing, batch jobs, and multi-model analysis, all with Python/TypeScript code snippets.[6][7][1]

## SDK and CLI Usage
Install via `pip install chutes`, register with Bittensor wallet, create API keys (`chutes keys create`), and share chutes across users. Local dev mode (`chutes run --dev`) enables testing before production pushes. GitHub repo at chutesai/chutes provides full SDK source.[3][2]

## Human

I'm looking for python information on how to use the api.

## Assistant

To use the Chutes.ai API in Python, install the SDK with `pip install chutes`, set up authentication via Bittensor wallet and API keys (`chutes keys create`), then interact with deployed chute endpoints using standard HTTP clients like `aiohttp` for OpenAI-compatible calls.[1]

## Client-Side API Calls
Deployed chutes expose REST endpoints like `/v1/chat/completions`. Send POST requests with JSON payloads specifying the model, messages, `max_tokens`, and `temperature`. Responses return generated completions in standard OpenAI format.[2]

Example async Python code for chat completions:

```python
import asyncio
import aiohttp
import json

async def chat_with_chute():
    url = "https://your-username-my-first-chute.chutes.ai/v1/chat/completions"
    payload = {
        "model": "unsloth/Llama-3.2-1B-Instruct",
        "messages": [{"role": "user", "content": "Hello! How are you today?"}],
        "max_tokens": 100,
        "temperature": 0.7
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            print(json.dumps(result, indent=2))

asyncio.run(chat_with_chute())
```

This supports streaming, tool calling, and custom endpoints via `@chute.cord()` decorators in chute definitions.[2]

## SDK for Building/Deploying
Use the Python SDK to create chutes programmatically, e.g., `build_vllm_chute()` for VLLM-based inference servers. Build images (`chutes build`), deploy (`chutes deploy`), and test locally (`chutes run --dev`). Full CLI/SDK reference covers listing chutes, logs, and management.[2]

## Human

How do I query how much quota I've used?

## Assistant

You can query quota and usage via the Chutes Users API, which exposes endpoints for “my quotas” and per‑chute quota usage.[1]

## High-level options

- In‑app: On paid tiers, current daily quota usage is visible in the top‑right of the dashboard and API panel.[2]
- VS Code: The “Chutes.ai Quota Monitor” extension shows your current daily quota in the status bar using the same API.[3]

## API endpoints

Chutes exposes user and chute quota endpoints under the Users API:[1]

- **My quotas (current user)**:  
  - Endpoint: `GET /users/me/quotas` (path name may appear as “My Quotas” in docs)  
  - Returns your active quota limits and current usage across resources.[1]

- **Chute quota usage (per chute)**:  
  - Endpoint: `GET /users/me/quota_usage/{chute_id}`  
  - Parameter: `chute_id` (string, required)  
  - Returns current usage for that specific chute (e.g., tokens, requests, or GPU time depending on chute type).[1]

Both require authentication via your API key using the `Authorization` header (same pattern as other Chutes API calls).[4]

### Minimal Python example

```python
import aiohttp
import asyncio

API_KEY = "cpk_your_api_key"
BASE_URL = "https://api.chutes.ai"

headers = {
    "Authorization": f"Bearer {API_KEY}",
}

async def get_my_quotas():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{BASE_URL}/users/me/quotas") as resp:
            resp.raise_for_status()
            return await resp.json()

async def get_chute_quota_usage(chute_id: str):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            f"{BASE_URL}/users/me/quota_usage/{chute_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

async def main():
    my_quotas = await get_my_quotas()
    print("My quotas:", my_quotas)

    usage = await get_chute_quota_usage("your-chute-id")
    print("Chute usage:", usage)

asyncio.run(main())
```

This pattern matches the documented quota endpoints and the way the VS Code quota monitor integrates with Chutes.[3][4][1]

## Human

How to call the Chutes API endpoint for quota usage

## Assistant

To call the Chutes quota‑usage endpoint, send an authenticated GET request to the Users API “my quotas” or “quota usage by chute” paths with your Chutes API key in the `Authorization` header.[1][2]

## Key endpoint and auth

- Base URL: `https://api.chutes.ai` (same as other Chutes control‑plane APIs).[2]
- Auth: `Authorization: Bearer <YOUR_API_KEY>` using a Chutes API key created in your account settings or via CLI.[2]
- Main quota endpoint (current user, all quotas):  
  - `GET /users/me/quotas` returns your current limits and usage.[1]
- Per‑chute quota usage (if available in your account):  
  - `GET /users/me/quota_usage/{chute_id}` where `chute_id` is the ID of the chute you want to inspect.[1]

Both endpoints are read‑only and follow standard JSON responses with fields for limits and current usage.[1]

## Python example with `requests`

```python
import os
import requests

API_KEY = os.environ.get("CHUTES_API_KEY")  # or hardcode for testing
BASE_URL = "https://api.chutes.ai"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

def get_my_quotas():
    url = f"{BASE_URL}/users/me/quotas"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_chute_quota_usage(chute_id: str):
    url = f"{BASE_URL}/users/me/quota_usage/{chute_id}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    print("My quotas:")
    print(get_my_quotas())

    # Replace with your actual chute ID from the dashboard or CLI
    chute_id = "your-chute-id"
    print(f"\nQuota usage for chute {chute_id}:")
    print(get_chute_quota_usage(chute_id))
```

This pattern matches the documented Users API quota endpoints and uses the same auth mechanism as other Chutes control‑plane calls.[2][1]
