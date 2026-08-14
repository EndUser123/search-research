---
title: "For the NVIDIA developer access, you get API access and a rate or quota. How does that rate limit work, and when does it"
date: "2026-02-02"
mode: "CONCISE"
uuid: "07ed116b-6e0b-4e53-900f-2a5a674fe0ae"
entry_count: 3
---

## Human

For the NVIDIA developer access, you get API access and a rate or quota. How does that rate limit work, and when does it refresh?

## Assistant

**NVIDIA developer access through the NVIDIA API Catalog for NIM provides trial API access with rate limits.** 

## Rate Limit Details
The primary rate limit for the NVIDIA NIM API trial is 40 requests per minute per model. NVIDIA does not publicly publish additional limits like token quotas or context windows, as these apply only to the trial experience. Exceeding the limit results in HTTP 429 errors, and users should implement backoff strategies.[1][2][3]

## Refresh Mechanism
The limit refreshes every minute, consistent with the per-minute window structure (e.g., 40 requests allowed within each rolling 60-second period). No daily or hourly quotas are explicitly mentioned in available sources, though congestion may cause additional throttling.[2][1]

## Usage Notes
For production or unlimited access, NVIDIA recommends NVIDIA AI Enterprise, hosted providers like Together.ai, or self-deployment of NIM microservices. Check the API catalog at build.nvidia.com after logging in for any user-specific indicators, such as rate limit status icons.[4][1][2]

## Human

I thought you had like 1000 quota or 5000 quota, but I don't see how it renews, like if it's every month, etc.

## Assistant

**NVIDIA NIM API Catalog provides a total trial quota of 5000 free API credits, starting with 1000 upon signup.** Users can request an additional 4000 credits via their profile, often requiring a business email for a 90-day NVIDIA AI Enterprise license.[1][2]

## Credit Allocation
New accounts receive 1000 API credits immediately after signup and phone verification. The "Request More" option unlocks up to 4000 extra credits, bringing the total to 5000 for trial use.[3][4][1]

## Renewal and Expiration
Credits do not renew monthly or periodically; they are a one-time trial allocation that depletes with usage until exhausted. Once used up, access ends unless switching to self-hosted NIM (free for development under NVIDIA Developer Program) or paid options like hosted NIM microservices.[2][1]

## Additional Limits
A separate rate limit of 40 requests per minute applies alongside credits, refreshing every minute. Exact credit consumption per request varies by model and usage (e.g., input/output tokens), viewable in the build.nvidia.com dashboard after login.[5][1][3]

## Human

How to self-host NIM microservices for free development

## Assistant

**Self-hosting NVIDIA NIM microservices for free development requires joining the NVIDIA Developer Program and using Docker on NVIDIA GPU hardware.** This provides unlimited prototyping on up to 16 GPUs across two nodes, with standard OpenAI-compatible APIs exposed on port 8000.[1][2][3]

## Prerequisites
Join the free NVIDIA Developer Program via build.nvidia.com: select a model, go to the Deploy tab, click Get API Key, and sign in with a personal email. Ensure Linux (Ubuntu 22.04+ recommended), NVIDIA drivers >= R580, NVIDIA Container Toolkit >= 1.16.1, and Docker installed; test with `docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi`.[2][3]

## Generate API Key
Visit https://build.nvidia.com, pick a model (e.g., meta/llama-3.1-8b-instruct), select Deploy > Get API Key, generate and copy your NGC Personal API key (select NGC Catalog entitlements).[2][3] Export it: `export NGC_API_KEY=your_key_value` and authenticate Docker: `echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin`.[3]

## Deployment Steps
List available NIMs: `ngc registry image list nvcr.io/nim/*` to get repository (e.g., nim/meta/llama-3.1-8b-instruct) and tag (e.g., latest).[3]

Set variables:
```
export CONTAINER_NAME=llama-nim
export Repository=nim/meta/llama-3.1-8b-instruct
export TAG=latest
export IMG_NAME="nvcr.io/$Repository:$TAG"
export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p "$LOCAL_NIM_CACHE" && chmod -R a+w "$LOCAL_NIM_CACHE"
```

Run the container:
```
docker run -it --rm --name=$CONTAINER_NAME \
  --runtime=nvidia --gpus all --shm-size=16GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
  -u $(id -u) -p 8000:8000 \
  $IMG_NAME
```
The container downloads models on first run and starts the server.[4][3]

## Testing and Usage
Verify readiness: `curl http://0.0.0.0:8000/v1/health/ready` (200 OK). List models: `curl http://0.0.0.0:8000/v1/models`. Test chat: `curl -X POST 'http://0.0.0.0:8000/v1/chat/completions' -H 'Content-Type: application/json' -d '{"model": "meta/llama-3.1-8b-instruct", "messages": [{"role":"user","content":"Hello"}]}'`.[3]

## Notes
Stop with `docker stop $CONTAINER_NAME`. For Kubernetes, multi-node, air-gapped, or Hugging Face models, see docs.nvidia.com/nim/large-language-models/latest/deployment-guide.html. Production requires NVIDIA AI Enterprise license.[5][6][7]
