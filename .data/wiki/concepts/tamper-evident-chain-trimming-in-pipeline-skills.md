---
title: Tamper-evident chain trimming in pipeline skills
type: concept
tags: [pipeline, anti-fabrication, chain, ship-py, close-py, shared-module]
confidence: high
evidence_tier: observed
verified: true
created: 2026-08-12
---

# Tamper-evident chain trimming in pipeline skills

## Problem

Ship-py and close-py both use a tamper-evident transition chain to detect specification gaming (agents writing state directly instead of through `save_state`). The chain is a linked list of SHA-256 hash entries capped at 20 entries (`chain[-20:]`). When the cap is exceeded, the genesis entry is trimmed from the front.

The validation logic originally assumed entry 0 always starts from genesis. After 20+ `save_state` calls, the genesis entry was trimmed, but validation still expected `prior_hash == "genesis"` at entry 0 — producing a false-positive `chain_broken` error that blocked the pipeline.

## Solution

Three-layer fix:

1. **Trim flag**: `save_state` sets `_chain_trimmed = True` when trimming occurs, signaling to validation that the genesis entry may be absent.

2. **Anti-gaming hash**: When trimming, store a derived hash binding the session to the cumulative trim count: `_chain_trimmed_hash = sha256(f"{session_id}:trimmed:{count}")`. Validation verifies this hash before trusting the trimmed boundary. Without it, an attacker could set `_chain_trimmed = True` with any `prior_hash`.

3. **Shared module**: The chain logic lives in `~/.grok/lib/pipeline_chain.py` — imported by both ship-py and close-py. This eliminates the copy-paste duplication that caused the original bug (ship-py was fixed, close-py wasn't, because they were independent copies).

## Anti-gaming properties

The chain is described as "not cryptographically unforgeable" — the agent has access to `hashlib`. The trim hash is a **consistency check**, not a cryptographic seal. It prevents accidental gaming (sloppy writes that set the flag without the matching hash) but not deliberate forgery by an agent that knows the derivation formula. This is the same trust level as the original chain design.

## Key files

- `~/.grok/lib/pipeline_chain.py` — shared `append_chain_entry()` + `validate_chain()`
- `skills/ship-py/__lib/phases/_shared.py` — delegates to shared module
- `skills/close-py/__lib/phases/_shared.py` — delegates to shared module
- `skills/ship-py/tests/test_chain_trimming.py` — 6 regression tests
- `skills/close-py/tests/test_chain_trimming.py` — 6 regression tests

## Reference incident

Session 019fee63 (2026-08-12): ship-py pipeline blocked by false-positive `chain_broken` after 20+ save_state calls. Root cause: chain trimming removed genesis entry, validation didn't account for it. Same bug existed in close-py (independent copy). Fixed in both, then extracted to shared module.
