---
title: or-ling-3-flash-free persistent rate-limit under parallel load
thread_id: or-ling-rate-limit-parallel-load-20260802
created: 2026-08-02
status: OPEN — investigation needed
priority: MEDIUM
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: grok
last_updated_at: 2026-08-02T00:30:00Z
---

# Handoff: or-ling-3-flash-free persistent rate-limit under parallel load

## Problem

`or-ling-3-flash-free` (OpenRouter) consistently fails with 429 rate-limit errors when used for 2+ concurrent spawns. This hit in both close-check live runs:

- **Run 1:** 3 of 5 Phase 3 remediation agents failed with 429 (all on or-ling)
- **Run 2:** friction subagent failed (429 on or-ling)
- **This session's /tp spawn attempts:** or-ling ran 375s with 53 tool calls before being killed

The provider-diverse defaults fix (FREE_A=minimax, FREE_B=or-ling, FREE_C=minimax) reduced but did not eliminate the problem — or-ling still gets 2 concurrent slots, which is enough to trigger the rate limit under parallel() dispatch.

## Root cause (from tool-fallbacks.md line 65)

> `or-ling-3-flash-free` (parallel dispatch) | 429 rate limit after 3+ concurrent agents (OpenRouter 20 RPM shared across all free-model calls). 4 of 7 agents failed in session 2026-08-01.

The 20 RPM limit is shared across ALL free-model calls on OpenRouter, not just or-ling. If another session is also using OpenRouter free models concurrently, the combined rate exceeds 20 RPM even with only 2 agents per session.

## Options for next session

1. **Reduce or-ling parallel_safe_count from 2 to 1** in fleet-models.json — prevents the workflow from assigning 2 concurrent agents to OpenRouter
2. **Replace or-ling as a default with a third provider** (NVIDIA NIM is free and has higher RPM — we proved nim-openai-gpt-oss-20b works via spawn)
3. **Add a per-provider concurrency tracker** to the spawn gate that counts in-flight spawns per provider and blocks when the limit is reached (architectural — belongs in the model-error-classification handoff)
4. **Use pick_model.py --count to get 3 diverse providers every time** and never reuse the same provider for 2 agents (the intended fix, but requires the args to actually land in the workflow)

## Acceptance criteria

- [ ] Choose an option (1-4 above)
- [ ] Implement the fix
- [ ] Verify with a close-check run that no 429 errors occur on OpenRouter

## Related

- `P:/docs/handoffs/model-error-classification-architecture-20260801/HANDOFF.md` — item 2 (model-scoped cooldowns) would help here
- `P:/.data/wiki/concepts/tool-fallbacks.md` — or-ling entry in spawn_subagent limitations table
- `P:/.data/wiki/concepts/agent-consolidation-in-parallel-workflows.md` — max 2-3 concurrent per free-tier provider
