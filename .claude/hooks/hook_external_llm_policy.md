# Hook External LLM API Policy

**Rule:** Hooks MAY call external LLMs via direct HTTP or SDK when all four safeguards below are met. Raw HTTP calls to arbitrary third-party APIs without fail-open remain prohibited.

## Approved Pattern 1: Direct MiniMax via requests

MiniMax exposes an Anthropic-compatible API at `https://api.minimax.io/anthropic/v1/messages`. Auth uses `Authorization: Bearer {key}` (NOT `x-api-key`). Key loaded from `MINIMAX_API_KEY` env var or `P:/.env`.

```python
# ✅ Direct MiniMax call inside a hook — all four safeguards present
import os
import requests
from pathlib import Path

def _load_minimax_key() -> str | None:
    key = os.environ.get("MINIMAX_API_KEY", "").strip().strip('"')
    if key:
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MINIMAX_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None

def call_minimax(system_prompt: str, user_prompt: str, model: str = "MiniMax-M2.7") -> str | None:
    api_key = _load_minimax_key()
    if not api_key:
        return None  # fail-open: no key

    try:
        resp = requests.post(
            "https://api.minimax.io/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": 196608,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        return text.strip() or None
    except Exception:
        return None  # fail-open — never block on LLM failure
```

## Approved Pattern 2: Mistral via mistralai SDK

Mistral uses the `mistralai` Python package. Auth via `MISTRAL_API_KEY` env var or `P:/.env`.

```python
# ✅ Mistral call inside a hook — all four safeguards present
import os
from pathlib import Path

def _load_mistral_key() -> str | None:
    key = os.environ.get("MISTRAL_API_KEY", "").strip().strip('"')
    if key:
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MISTRAL_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None

def call_mistral(system_prompt: str, user_prompt: str, model: str = "mistral-medium-3.5") -> str | None:
    api_key = _load_mistral_key()
    if not api_key:
        return None  # fail-open: no key

    try:
        from mistralai.client import Mistral
        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            reasoning_effort="high",
            timeout_ms=10000,
        )
        if not response or not response.choices:
            return None
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception:
        return None  # fail-open — never block on LLM failure
```

## Parallel Dual-LLM Pattern

`Stop_semantic_critic.py` calls **both** LLMs in parallel via `ThreadPoolExecutor`. Combination logic:

| MiniMax | Mistral | Result |
|---------|---------|--------|
| ok=true | ok=true | ok=true (agree on pass) |
| ok=false | ok=true | ok=false (conservative — any flag wins) |
| ok=true | ok=false | ok=false (conservative — any flag wins) |
| ok=false | ok=false | ok=false (both flag issues) |
| None | result | Use Mistral result |
| result | None | Use MiniMax result |
| None | None | None — fail-open, never blocks |

## Key Details

### MiniMax
- **Auth header**: `Authorization: Bearer {key}` — MiniMax uses Bearer auth, not the Anthropic SDK's `x-api-key`. Using the Anthropic SDK produces 401 errors.
- **Key in .env**: Values have literal double quotes — always `.strip('"')`.
- **Response format**: Anthropic Messages shape with `content` array containing `thinking` and `text` blocks. Extract only `text` blocks.
- **Model**: `MiniMax-M2.7` (204,800 token context, ~60 tps output).
- **max_tokens**: Set to 196,608 (model's max output token limit).
- **Cost**: $0 marginal cost on token plan.

### Mistral
- **Auth**: `mistralai.client.Mistral(api_key=key)` — uses `Authorization: Bearer` internally.
- **Key in .env**: Same quote stripping as MiniMax.
- **Response format**: `response.choices[0].message.content` — plain string.
- **Model**: `mistral-medium-3.5` with `reasoning_effort="high"` for deep analysis.
- **Rate limit**: Free tier = 1 req/sec.
- **Cost**: Free tier available.

## Four Mandatory Safeguards

Regardless of transport, all LLM-calling hooks must implement:

1. **Fail-open on any error** — timeout, transport failure, parse error, or empty response returns `None`, never blocks the user workflow
2. **Per-session invocation cap** — e.g., `SEMANTIC_CRITIC_CAP` (default 5) prevents runaway LLM calls within a single session
3. **Hard timeout** — 10s maximum; return `None` on timeout rather than blocking
4. **Quality gate classification** — LLM-calling hooks must be classified as `"quality"` gates in `GATE_CLASSES`, so they are suppressed on control/exploration turns where the cost is unjustified

## Production Reference

`Stop_semantic_critic.py` is the production reference implementation using the parallel dual-LLM pattern (MiniMax + Mistral).

## Prohibited Patterns

```python
# ❌ Anthropic SDK for MiniMax (sends x-api-key header, MiniMax expects Authorization: Bearer)
import anthropic
client = anthropic.Anthropic(api_key=key, base_url="https://api.minimax.io/anthropic")

# ❌ Raw HTTP to arbitrary APIs (no fail-open, no cap, no timeout)
import requests
response = requests.get("https://api.example.com/...")

# ❌ "Graceful degradation" that silently drops captured data
try:
    summary = call_external_api(transcript)
except Exception:
    summary = None  # NOT graceful — you just lost the data with no audit trail
```

## Decision Rule

If a hook needs semantic analysis that regex cannot provide (ambiguity resolution, contextual classification), use the parallel dual-LLM pattern with all four safeguards. If local artifact data suffices, prefer that — it's faster and has zero failure surface.
