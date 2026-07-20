# CCR Routing & MiniMax Quota Burn — Handoff (2026-07-19)

Authoritative investigation of where 5h of MiniMax tokens went, the routing
chain that produced them, and the staged fix awaiting promotion.

## TL;DR

- 5h burn: **221 MiniMax requests / 47.4M tokens**, distributed across 3
  session_ids. Source of truth: `P:/.claude/state/ccr-route-log.jsonl`
  (`backend_provider` + `backend_model` per row).
- The bleed: `DEEPSEEK_TOOL_SAFE_FALLBACK = "minimax,MiniMax-M3[1m]"` at
  `P:/.claude/provider-configs/ccr-custom-router.js:86`. When
  opencode-go + deepseek-v4-flash hits tool-history compat, the only
  safety net is MiniMax.
- **Staged fix (NOT YET PROMOTED):**
  `P:/.staging/ccr-custom-router.js` — single-line change: the
  fallback constant is now `"opencode-go,mimo-v2.5"` (mimo is a
  different model family and does not hit the same tool-history
  compat issue). Parses clean (`node -c` exit 0). The broken ladder
  iteration was abandoned because the compat check is model-independent.

## Verified CCR routing authority map (read directly from source)

Architecture (`ccr-admission-proxy.js:1-24`, `cc-ccr.ps1:1-22`):
```
Claude Code → admission-proxy :3458 → CCR :3456 → external providers
                ↓                    ↓
          ccr-request-ledger.sqlite   ccr-route-log.jsonl  ← routing decision
```

| artifact | classification | purpose |
|---|---|---|
| `P:/.claude/provider-configs/cc-ccr.ps1` | canonical source | launcher; sets `ANTHROPIC_BASE_URL=http://127.0.0.1:<ccrPort>` |
| `P:/.claude/provider-configs/ccr-admission-proxy.js` | canonical source (observability) | Node http server :3458; writes the SQLite ledger; does **not** gate forwarding |
| `P:/.claude/provider-configs/ccr-custom-router.js` | canonical source (per-request routing) | the routing decision; line 86 holds the legacy fallback constant |
| `P:/.claude/provider-configs/ccr-route-metadata.js` | canonical source (route metadata) | 9 verified routes; context limits per route |
| `P:/.claude/state/ccr-route-log.jsonl` | runtime state (canonical log) | **per-request `backend_provider` + `backend_model`**; 13.8 MB / 23,314 rows |
| `P:/.claude/state/ccr-request-ledger.sqlite` | runtime state | admitted/attempted; **no** upstream provider |

## Known routes (from `ccr-route-metadata.js`)

- `zai,glm-5.2`
- `opencode-go,deepseek-v4-flash`  ← currently failing for tool-history compat
- `opencode-go,mimo-v2.5`  ← new fallback (different family)
- `minimax,MiniMax-M3[1m]`  ← previous fallback (the bleed)
- `nvidia-free,nvidia/nemotron-3-ultra-550b-a55b`
- `nvidia-free,nvidia/nemotron-3-super-120b-a12b`
- `opencode-zen-free,opencode/minimax-m3-free`
- `grok-subscription,grok-4.5`

## 5h attribution (verified)

| session_id | MiniMax reqs | tokens | tiers | dominant reason |
|---|---:|---:|---|---|
| `unknown` (background hook traffic) | 149 | 32.8M | local:67, sonnet:11, opus:6, None:65 | over-ctx → opencode-go → minimax fallback |
| **`508c2e10-8e72-4307-87e1-6cf56973c741` (this session)** | **45** | **8.9M** | local:39, sonnet:6 | over-ctx → opencode-go → minimax fallback |
| `45504861-e019-4c69-a420-34761e7d303e` | 27 | 5.7M | local:25, sonnet:2 | over-ctx → opencode-go → minimax fallback |
| **total** | **221** | **47.4M** | | |

## Promote + validate (cold-start)

1. Replace live with staged: `cp P:/.staging/ccr-custom-router.js P:/.claude/provider-configs/ccr-custom-router.js`
2. Restart CCR: `. P:\.claude\provider-configs\cc-ccr.ps1 -Restart`
3. Re-run the JSONL attribution query for the next 5h window. If `minimax` count drops significantly, the fix worked. The verification query:

```python
import json, collections
from datetime import datetime, timezone, timedelta
cutoff = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
prov = collections.Counter()
with open(r"P:/.claude/state/ccr-route-log.jsonl", encoding='utf-8') as f:
    for line in f:
        o = json.loads(line)
        if o.get('ts','') >= cutoff:
            prov[o.get('backend_provider','?')] += 1
print(prov)
```

## Notes

- Don't conflate `ccr-request-ledger.sqlite`'s `model` column with the
  destination — it is the *requested* alias. The destination lives in
  `ccr-route-log.jsonl`.
- The "unknown" session bucket (149 reqs) is hook-driven LLM evals
  (semantic_critic, anti_dodge_judge, cks_quality_gate, etc.) running
  in subprocess contexts that don't set a session_id. Cost-aware hook
  gating is a separate workstream — not addressed here.

## Related workstream tasks in the shared task list

- #1475 CCR routing attribution: MiniMax 5h burn investigated
- #1476 CCR router fix: extend fallback ladder beyond MiniMax (now: direct route to mimo)
- #1477 mm-quota: Layer 3 has no real call log (negative finding)
- #1478 Self-correction: context-pressure reminder reflex
- #1479 path_errors_*.jsonl filename cascade root cause (untraced)
- #1474 discovery_audit.py: scanner leak fixed (live)
- #1473 Task-list cleanup: delete 254 closed tasks
- #1481 Cleanup: rename + dedupe path_errors_*.jsonl cascade files (11+ GB reclaim)