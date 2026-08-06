---
title: "Grok quota dashboard: Gemini dedup, sort order, Claude+OSS, and check_grok() billing endpoint"
current_session_id: 019fd698-f697-7212-af73-19143fd58dcd
produced_at: 2026-08-06T09:00:00Z
last_updated_at: 2026-08-06T09:00:00Z
status: open
accurate_as_of_head: c526502
source_transcript: ~/.grok/sessions/P%3A%5C/019fd698-f697-7212-af73-19143fd58dcd/chat_history.jsonl
assigned_to: grok
assigned_at: 2026-08-06T09:00:00Z
assigned_by: operator
---

# Handoff: Grok quota dashboard fixes + check_grok()

## Goal

Fix display issues in the fleet quota dashboard (`fleet_quota.py`) and add
Grok Build weekly quota tracking via a reverse-engineered gRPC-web billing
endpoint.

## 1. Operator's verbatim request

> "Why isn't grok measured for quota use? why is gemini listed twice? How would you fix these?"

Then followed by:

> "except that there is a quota per week."

And:

> "/www everything worth reading and related. /tp what's the best implementation? /go do it"

## 2. What was done

### Completed (6 commits, c3320fe through 9e1154a)

| Commit | Change |
|--------|--------|
| `c3320fe` | Gemini window label dedup — `parse_opencode_quota()` passes `raw_window` field, `render_dashboard()` appends it to labels |
| `2b717b8` | Bar alignment — `W_WIN` 14→17 to accommodate "Claude+OSS weekly" |
| `8a9ac76` | Logical sort order — `_sort_key` groups by family (Gemini→Claude→Claude+OSS), then window (5h→weekly) |
| `0c79356` | Claude+GPT→Claude+OSS rename (pool covers Opus+Sonnet+GPT-OSS, not GPT generally) |
| `3e4e289` | `check_grok()` — gRPC-web billing endpoint query + wiring into dashboard |
| `9e1154a` | Style fix — expand compact protobuf parser to proper multi-line (E702/E701) |

### Wiki concept written

- `P:/.data/wiki/concepts/grok-build-grpc-web-billing-endpoint.md` — documents the gRPC-web endpoint, protobuf parsing, three xAI quota surfaces, and prior art

### Verification completed

- `/check` PASS (33/33 tests, all 9 checklist items verified by independent subagent)
- `/review` needs_attention (2 actionable bugs found, 1 critical design note)

## 3. Key decisions

### Gemini dedup approach
opencode-quota returns two entries per Gemini account (5h + Weekly windows) with identical names. Decision: pass the `raw_window` field through and append it to the display label. Alternative rejected: filtering to one window (loses information).

### Claude+OSS label accuracy
The raw pool name "Claude and GPT models" is misleading — it covers Claude Opus, Claude Sonnet, and GPT-OSS (not GPT generally). Decision: abbreviate to "Claude+OSS." Alternative rejected: keeping "Claude+GPT" (inaccurate per operator).

### check_grok() implementation path
Three xAI quota surfaces exist: (1) public API tier-based RPS/TPM, (2) consumer app weekly pool, (3) Grok Build same weekly pool. The gRPC-web billing endpoint at `grok.com/grok_api_v2.GrokBuildBilling/GetGrokCreditsConfig` is the only programmatic path for #3. Uses bearer token from `~/.grok/auth.json`. Requires IPv4 forcing + browser-like headers (Cloudflare).

## 4. Evidence

- **Live dashboard output:** Grok Build shows 80% remaining, 20% pool used, resets Thu 08:24 (168h cycle)
- **gRPC-web response:** HTTP 200, 120 bytes, protobuf with field 1 float32=20.0%, field 5 timestamp=1786026280
- **Tests:** 33/33 pass (`python -m pytest test_fleet_quota.py -v`)
- **AST parse:** clean
- **Review artifacts:** `file:///P:/.artifacts/console_a8dfe293-484b-49d1-8c12-b6d7/grok-review/local/20260806-085229/FINDINGS.md`
- **Check artifacts:** `file:///P:/.artifacts/console_a8dfe293-484b-49d1-8c12-b6d7/grok-check/20260806-083346-072/check-state.md`

## 5. Open items (from /review)

### SEC-6 — Bug: AttributeError crash if email field is null
**Line:** 770 of `fleet_quota.py`
**Issue:** `auth[oidc_key].get("email", "?")` returns `None` if JSON has `"email": null`. Later `email.split('@')` crashes.
**Fix:** `email = auth[oidc_key].get("email") or "?"`
**Effort:** 1 line

### SEC-7 — Bug: malformed gRPC response produces false "100% remaining"
**Line:** 662, 766 of `fleet_quota.py`
**Issue:** Truncated response → `used_pct` defaults to 0.0 → false 100% remaining in cache → spawn gate could unblock a model that should stay gated.
**Fix:** Validate `msg_len <= len(raw) - 5`. If `used_pct is None` after parsing, return `pct: None` (show "?" on dashboard).
**Effort:** ~5 lines

### SEC-1 — Critical (design): socket monkey-patch not thread-safe
**Line:** 628 of `fleet_quota.py`
**Issue:** `socket.getaddrinfo` monkey-patch is process-global. If hooks call check_grok() concurrently, the original can be permanently lost.
**Fix:** Use `threading.RLock` guard or custom HTTPS handler. Not urgent for single-threaded `quota` alias use.
**Effort:** ~20 lines

### CORR-1 — Nit: dead `_FAMILY_ORDER` dict
**Line:** ~1118 of `fleet_quota.py`
**Fix:** Delete the unused dict.

### CORR-2 — Suggestion: hoist sort constants
**Line:** ~1116 of `fleet_quota.py`
**Fix:** Move `_WIN_ORDER` and `_sort_key` to module scope.

## 6. Next steps (for a fresh session)

1. **Fix SEC-6** (1 line) — `email = auth[oidc_key].get("email") or "?"`
2. **Fix SEC-7** (~5 lines) — validate msg_len + return None for missing used_pct
3. **Fix SEC-1** (~20 lines, optional) — add threading lock to socket monkey-patch
4. **Clean up CORR-1 + CORR-2** — delete dead dict, hoist constants
5. **Update `P:/.data/wiki/concepts/provider-quota-usage-api-reference.md`** — add the gRPC-web endpoint as an alternative to opencode-quota for xAI

## 7. Read first (for a fresh session)

- `~/.grok/skills/model-quota/scripts/fleet_quota.py` — the file being modified
- `P:/.data/wiki/concepts/grok-build-grpc-web-billing-endpoint.md` — the technique
- `P:/.data/wiki/concepts/provider-quota-usage-api-reference.md` — the broader quota API landscape

## 8. Cross-reference couplings

- `fleet_quota.py` `write_quota_cache()` → feeds `PreToolUse_spawn_model_gate.py` hook (reads cache to block near-limited providers)
- `fleet_quota.py` `check_grok()` → reads `~/.grok/auth.json` (same token grok CLI uses)
- `P:/.data/wiki/concepts/cohere-api-integration-rate-limit-tracking.md` — same pattern (response-header probe for provider without management API)

## Other outstanding streams

None — this was a single-stream session focused on the quota dashboard.

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-08-06 | grok (019fd698) | Initial handoff — all work done, 2 review bugs open |
