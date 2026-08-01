---
title: "DiffusionGemma direct API: reproducible HOW-TO"
created: 2026-07-22
source: session-2026-07-22
sources:
  - P:/.agents/scripts/models/dgemma_read.py
  - https://integrate.api.nvidia.com/v1/chat/completions
  - P:/.data/wiki/concepts/diffusiongemma-4-tier-integration.md
  - P:/.data/wiki/concepts/diffusiongemma-optimal-usage-dos-and-donts.md
tags: [diffusiongemma, direct-api, howto, reproducible, nvidia, nvidia-nim, urllib, recipe, verification]
summary: >
  Reproducible recipe for calling DiffusionGemma via direct
  HTTP API: endpoint, auth, request shape, three invocation modes
  (single/enhanced/batch), expected output, and a falsification test.
  Verifiable by anyone who can run curl or python.
agent: grok
host: both
cognitive_load: 2
verification: script-verified
relations:
  - target: wiki/concepts/diffusiongemma-4-tier-integration
    type: provides-how-to-for
  - target: wiki/concepts/diffusiongemma-optimal-usage-dos-and-donts
    type: provides-how-to-for
  - target: wiki/concepts/model-pool-not-chain
    type: related
---

# DiffusionGemma direct API: reproducible HOW-TO

## What "direct API" means here (and why it matters)

DiffusionGemma (`google/diffusiongemma-26b-a4b-it`) is a Google model hosted on Nvidia's NIM endpoint. Two ways to reach it:

| Path | Works? | Why |
|------|--------|-----|
| **`spawn_subagent(model="nvidia-diffusiongemma-26b")`** | ❌ Empty content | The agent framework sends parameters conflicting with thinking mode (thinking ON by default; disabling produces empty content) |
| **Direct HTTP POST** to Nvidia's OpenAI-compatible endpoint | ✅ Verified | Bypasses the framework; urllib POST with chat-completions payload returns valid content |

**Only the direct API path works.** If you cannot make a raw HTTP POST (e.g., you are inside a constrained agent framework), DiffusionGemma is unavailable to you. Use a different pool member instead.

## Prerequisites

1. **Network access** to `https://integrate.api.nvidia.com`
2. **API key** in env var `NVIDIA_API_KEY`. The script at `P:/.agents/scripts/models/dgemma_read.py` has a default key baked in for this host; for other hosts, set the env var:
   ```powershell
   $env:NVIDIA_API_KEY = "nvapi-..."
   ```
   (Get a key from NVIDIA's build page: https://build.nvidia.com/google/diffusiongemma-26b-a4b-it)
3. **Python 3.9+** with stdlib only (urllib, json, pathlib). No pip installs.

## The minimal call (proof it works)

Paste this verbatim. If it returns a non-empty summary, the endpoint is live and the prior wiki claims are reproducible.

```python
# P:/tmp/dgemma_smoke.py
import json, os, urllib.request

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
MODEL = "google/diffusiongemma-26b-a4b-it"

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "In one sentence, what is DiffusionGemma?"},
    ],
    "max_tokens": 200,
    "stream": False,
}
req = urllib.request.Request(URL, data=json.dumps(payload).encode(), method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", f"Bearer {API_KEY}")
req.add_header("Accept", "application/json")

with urllib.request.urlopen(req, timeout=60) as resp:
    body = json.loads(resp.read().decode())
    print(body["choices"][0]["message"]["content"])
```

Run: `python P:/tmp/dgemma_smoke.py`
Expected: a one-sentence answer about DiffusionGemma, returned in ~1-3 seconds.
**If you see empty output:** the thinking-mode conflict is biting; this minimal call should not trigger it, but if it does, retry — transient.

## Request shape (the contract)

```
POST https://integrate.api.nvidia.com/v1/chat/completions
Headers:
  Content-Type: application/json
  Authorization: Bearer <NVIDIA_API_KEY>
  Accept: application/json
Body (JSON):
  {
    "model": "google/diffusiongemma-26b-a4b-it",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "...

--- FILE CONTENT ---
<file text>"}
    ],
    "max_tokens": 600,        # bump for long outputs; thinking tokens are invisible but counted
    "stream": false
  }
Response: standard OpenAI chat-completions shape; content at choices[0].message.content
```

**Thinking mode:** the model emits reasoning tokens that are invisible in `content` but counted in `usage`. Keep `max_tokens` generous (600+). Do NOT attempt to disable thinking — that returns empty content (the spawn_subagent failure mode).

## Three invocation modes (use the script)

The script `P:/.agents/scripts/models/dgemma_read.py` wraps the above into three modes. **Prefer the script over copy-pasting the minimal call** — it handles batching, fan-out, merge, and JSON output.

```bash
# Single file, one pass (fastest, breadth scanning)
python P:/.agents/scripts/models/dgemma_read.py <file_path>

# Single file, multi-perspective fan-out + merge (higher quality, ~4s)
python P:/.agents/scripts/models/dgemma_read.py <file_path> --enhanced

# Multiple files in one call (256K context; 20 files ~6.5s)
python P:/.agents/scripts/models/dgemma_read.py <file1> <file2> <file3> --batch --json

# Directory of .md files
python P:/.agents/scripts/models/dgemma_read.py <dir> --batch

# Directory of SKILL.md files (skill-tree mode)
python P:/.agents/scripts/models/dgemma_read.py <dir> --batch --pattern SKILL.md

# Custom prompt
python P:/.agents/scripts/models/dgemma_read.py <file> --prompt "Extract every quoted string and its source line."
```

**When to use which:**
- **single** — one file, need it fast, breadth over depth
- **enhanced** — one file, need higher quality (3 perspectives merged); ~4s but matches ccr-ornith quality at 10x speed
- **batch** — many files; uses the 256K context to summarize N files in one call (cheapest per-file)

## Verified performance (receipts)

| Mode | Test | Result | Date |
|------|------|--------|------|
| single | T1 (1 file) | ~1-2s, accurate | 2026-07-21 |
| enhanced | T4 blind (20/20 vs ccr-ornith) | ~4s, matched ornith quality | 2026-07-21 |
| batch | 26 files in one call | ~6.5s, all 26 correct | 2026-07-21 |
| batch (multi-path) | 2 concepts, this session | 4.8s, 1 API call, both accurate | 2026-07-22 |
| batch (multi-path) | 6 concepts, this session | 3.6s, 1 API call, all 6 correct | 2026-07-22 |
| **smoke test (minimal call)** | this session | 2.0s, valid one-sentence answer | 2026-07-22 (falsification test run at page-creation) |
| **batch (multi-path)** | 2 concepts, falsification test | 1.4s, 1 API call, both correct | 2026-07-22 (falsification test run at page-creation) |
| **single (smallest skill)** | web/SKILL.md (6.2KB) | 5.0s, structured output correct | 2026-07-22 (6-skill test) |
| **single (largest skill)** | go/SKILL.md (37KB) | 5.2s, structured output correct | 2026-07-22 (6-skill test) |
| **enhanced** | handoff/SKILL.md (21KB) | 8.6s, 4 calls, [HIGH]/[MEDIUM] labels | 2026-07-22 (6-skill test) |
| **batch (6 skills, post-fix)** | tp/wiki/go/plan/handoff/web | 7.0s, 1 call, all 6 named + summarized correctly, 0 truncated | 2026-07-22 (6-skill test) |
| **dir mode (--pattern SKILL.md)** | plan/ dir | 2.8s, found + summarized the SKILL.md | 2026-07-22 |

**Testing across multiple skills found two real defects in the script (both fixed 2026-07-22):**

1. **`name` field bug:** batch output used filename stem as the name, so every SKILL.md showed up as `"name": "SKILL"` — ambiguous, can't tell skills apart. Fix: script now uses parent dir name when the filename is generic (SKILL/README/INDEX/etc.).
2. **Silent input truncation:** `max_file_chars` defaulted to 12000; files >12KB had their back halves dropped before the model saw them. 3 of 6 real skills (tp/go/handoff, 20-37KB) were silently truncated. Fix: default raised to 50000 (handles real skills; ~12K tokens, well within 256K context).

**Both fixes verified** by re-running the 6-skill batch: all 6 now show correct names, 0/6 truncated, 7.0s total. The HOW-TO's claims are now backed by actual multi-skill testing, not just the 2-concept falsification test.

Reproduce any of these: the script prints `elapsed`, `calls`, `summarized/total_files` to stderr.

## Falsification test (run this before relying on the claim)

```bash
# 1. Confirm the minimal call returns non-empty content
python P:/tmp/dgemma_smoke.py

# 2. Confirm batch mode works on real files
python P:/.agents/scripts/models/dgemma_read.py `
  "P:/.data/wiki/concepts/diffusiongemma-4-tier-integration.md" `
  "P:/.data/wiki/concepts/model-pool-not-chain.md" `
  --batch --json

# Expected: JSON with 2 summaries, elapsed ~3-7s, exit 0
# If you see "ERROR: Empty content" or a 4xx/5xx HTTP error: the claim is NOT
# reproducible in your environment. File the specifics.
```

**The claim "DiffusionGemma works via direct API" is only true if this test passes in your environment.** If it does not, report the failure and use a different pool member.

## Common failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Empty content` from spawn_subagent | Framework thinking-mode conflict | Use direct API (this page), not spawn_subagent |
| HTTP 401 | Bad/missing API key | Set `NVIDIA_API_KEY` env var |
| HTTP 429 | Rate limited (free tier, shared) | Wait; or switch to another free pool member |
| HTTP 5xx / timeout | Nvidia endpoint down | Failover to another pool member (see [[model-selection-from-pool-decision-framework]]) |
| `max_tokens` too small, truncated output | Thinking tokens eat the budget | Raise `max_tokens` to 1000+ for complex prompts |

## What this page does NOT do

- Does not claim DiffusionGemma is the **best** model for any task — only that the direct API is reproducible. Quality-vs-alternatives is a separate question (see [[model-selection-from-pool-decision-framework]]).
- Does not address multimodal use (image/audio) — untested.
- Does not address streaming — `stream: false` only.
- Does not replace `diffusiongemma-optimal-usage-dos-and-donts.md` (that page covers *when* to use it; this page covers *how*).

## Related

- `P:/.agents/scripts/models/dgemma_read.py` — the wrapper script (canonical implementation)
- [[diffusiongemma-4-tier-integration]] — *when* to use it (tier architecture); this page is *how*
- [[diffusiongemma-optimal-usage-dos-and-donts]] — sampling, thinking mode, limitations
- [[model-pool-not-chain]] — DiffusionGemma is a Code-lane pool member, not a chain position
- [[model-selection-from-pool-decision-framework]] — picking among pool members by task

## Falsifier

This page is wrong if:
- The minimal smoke test fails on a clean environment (the recipe is not actually reproducible)
- The endpoint URL or model name changes (Nvidia rebranded/retired it) — re-verify quarterly
- A simpler invocation exists that the page omits (the recipe is over-specified)

If the smoke test stops passing, update the page immediately or mark the claim refuted.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
