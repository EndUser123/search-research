---
thread_id: 4c87727d-6900-4c4f-b470-736b449caefb
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console
produced_at: 2026-07-22T15:00:00Z
status: CLOSED
handoff_type: implementation
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
assigned_to: unassigned
---

# Handoff: Update /go wave table with verified pool data

## 1. Objective

Update the `/go` skill spawn recipe to reflect the verified model pool data from this session's testing: Gemma 4 31B as Code pool primary, corrected rate limits, delegation gate.

## 2. Status

**Blocked on spawn_subagent test results.**

The wave table currently lists pool members that were updated to pool notation (not chain) this session, but the specific model assignments need updating after we know which models work via spawn_subagent.

## 3. What's already done

- `/go` wave table converted from chain notation to pool notation ✅
- `/go` spawn example updated to show pool selection logic ✅
- "Primary/Escalate" columns renamed to "Free pool members/Escalation tier" ✅
- `/go` `architectural` profile added with alternatives gate ✅
- AGENTS.md alternatives-before-implementation rule added ✅

## 4. What's pending

| Task | Blocked on |
|------|-----------|
| Add `gemma-4-31b-it` as Code pool primary | spawn_subagent test (does it work via Grok dispatch?) |
| Add `nvidia-diffusiongemma-26b` as Code pool member (not just direct API) | spawn_subagent test + NVIDIA validator fix |
| Update `/go` context-fit section with verified latency data | Nothing — can do now |
| Update `/go` wave table with verified rate limits (Gemma 14,400 RPD, DGemma no cap) | Nothing — can do now |
| Update `model-lanes-vs-roles.md` fleet table with Gemma 4 31B verified data | Nothing — can do now |

## 5. Verified data to incorporate

| Model | Quality | Latency p50 | RPD | RPM | Context | Dispatch |
|-------|---------|-------------|-----|-----|---------|----------|
| Gemma 4 31B | 7/7, 3/3, 1.0 recall | 7.6s | 14,400 | 30 | 131K | `[UNTESTED post-config-fix]` |
| DiffusionGemma | 7/7, 3/3, 0.87 recall | 3.9s | No cap | ~40 | 262K | Direct API only (NVIDIA validator bug) |
| Gemini 3.5 Flash-Lite | 7/7, 3/3, 1.0 recall | 0.9s | 500 | 15 | 1M | `[UNTESTED]` |
| ccr-ornith | `[UNTESTED]` | `[UNMEASURED]` | Unlimited | — | 65K | Works |

## 6. References

- `P:/tmp/model-test-results.json` — full raw results
- `P:/.data/wiki/concepts/operationalizing-gemma-models-2026-07-22.md` — operationalization guide
- `P:/.data/wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22.md` — test results
- `P:/.data/wiki/concepts/gemini-billing-tiers-actual-rate-limits-2026-07-22.md` — rate limits
- `P:/.data/wiki/concepts/model-pool-not-chain.md` — pool concept
- `P:/.data/wiki/concepts/model-fleet-provider-pools.md` — fleet inventory + delegation gate
