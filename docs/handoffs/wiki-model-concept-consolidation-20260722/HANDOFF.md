---
thread_id: 422cb93d-fdcf-4d7b-b97d-5f70573f540e
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console
produced_at: 2026-07-22T15:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
assigned_to: unassigned
---

# Handoff: Consolidate model wiki concepts + fix stale claims

## 1. Objective

Multiple model-related wiki concepts were written this session. Some contain superseded data or overlap. Consolidate into a coherent set with verified data only.

## 2. Status

**Not started.**

## 3. The problem

We now have ~10 model-related wiki concepts. Some supersede each other but aren't marked. Some contain claims that were later disproven by testing.

## 4. Concepts to review

| Concept | Status | Action needed |
|---------|--------|---------------|
| `model-pool-not-chain` | Current | Keep — core principle |
| `model-fleet-provider-pools` | Current, updated multiple times | Keep — primary operational reference. Contains delegation gate. |
| `model-lanes-vs-roles` | Updated (chain→pool) but still has old fleet table | **Update**: fleet table doesn't list Gemma 4 31B as primary |
| `model-selection-from-pool-decision-framework` | Written by another LLM | Keep — complementary to fleet-provider-pools |
| `gemini-billing-tiers-actual-rate-limits-2026-07-22` | Current | Keep — verified rate limits |
| `gemini-gemma-quota-rate-limits-2026-07-22` | **SUPERSEDED** | Already marked superseded; verify the note is there |
| `dgemma-gemini-flash-operational-tests-2026-07-22` | Current | Keep — verified test results |
| `operationalizing-gemma-models-2026-07-22` | Current | Keep — practical guide |
| `agy-vs-direct-api-complementary-value` | Current | Keep |
| `gemini-api-vs-agy-cli` | Current | Keep |

## 5. Specific fixes needed

1. `model-lanes-vs-roles.md` — update fleet table to list Gemma 4 31B as Code pool primary (14,400 RPD, 30 RPM, 16K TPM); remove or label `[UNMEASURED]` claims about ccr-ornith speed
2. `model-fleet-provider-pools.md` — verify the `model-selection-from-pool-decision-framework` cross-link is bidirectional
3. Any remaining "42x faster" or "instant" or "free" claims in other concepts → fix to verified values
4. `compensating-for-weaker-models-ensemble-multi-pass.md` — may need update with ensemble test results from this session (ensemble is 1.4x slower, better coverage, needs retry logic)

## 6. Non-blocking

This is consolidation/cleanup, not blocking any operational work. Do when the model concepts are stable (after spawn_subagent tests resolve).
