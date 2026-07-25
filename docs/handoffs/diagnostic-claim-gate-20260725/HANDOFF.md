---
current_session_id: 019f94c9-43c1-7b31-87c4-980fdd3047e8
current_terminal_id: console_9d8ef5b2-9187-4432-a2a8-47ce59cfe35f
thread_id: diagnostic-claim-gate-20260725
parent_handoff_path: none
produced_at: 2026-07-25T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 0cd4e53
---

# Diagnostic claim gate — pre-execution checklist for causal claims made during investigation

## Objective (one sentence)

Design and implement a structural mechanism that prevents the LLM from acting on diagnostic claims (e.g., "the hooks are not registered because the evaluation summaries show zeros") without first verifying the claim against direct evidence.

## Problem

The workspace implements 4 of 5 external approaches to preventing premature closure (verifiable records, differential diagnosis, agreement-bias detection, separation of verification). The gap is approach 1: **a pre-execution checklist applied to diagnostic claims made mid-session during investigation, not just design decisions or session completion.**

The failure instance: the agent observed evaluation summaries showing `completion_attempts: 0` and `hook_registration_status: not_registered`, concluded "the hooks are not registered," and acted on that conclusion (registered the receipt writer in `quality-gate.json`). The conclusion was wrong — the hooks were already firing via `verification-receipts.json` (31 receipt files in one session). The agent didn't check the raw evidence (one `ls` of the receipt directory) because the narrative closed before it formed.

**Root cause (multi-dimensional):**
1. **MEASUREMENT**: `hook_registration_status` is derived from a config-path check that doesn't match Grok Build's glob-based hook discovery
2. **SCHEMA**: `completion_attempts: 0` looks identical whether the hooks didn't fire OR fired with no completion claims to evaluate
3. **SAMPLING**: the agent sampled 5 most-recent evaluation summaries (all subagent sessions with naturally-zero claims)
4. **BEHAVIOR**: the agent treated the plausible narrative as sufficient without checking raw evidence

Dimensions 1-3 are structural (fixable in code). Dimension 4 is behavioral (probabilistic mitigation only).

## What was done this session

### Shipped
- Wiki concept documenting the 5 external approaches and the gap: `P:/.data/wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md`
- Receipt writer registered in `quality-gate.json` (commit `3609e5a`) — redundant with the already-working `verification-receipts.json` but harmless
- Handoffs updated to reflect the true state: `multi-terminal-auto-commit-20260725/HANDOFF.md` and `tp-rewrite-20260725/HANDOFF.md`
- Multi-dimensional root cause analysis completed (measurement, schema, sampling, behavioral)
- Root cause analysis methodology identified: Ishikawa/fishbone for fan-out across dimensions (mechanical/behavioral/process/environmental), Five Whys for linear chain when single-cause

### Discovered (not yet fixed)
- **Evaluation script bug**: `receipt_shadow_evaluation.py` reports `hook_registration_status: not_registered` because it checks a different registration path than Grok Build's glob discovery uses. The hooks ARE registered and firing — the evaluation just doesn't recognize them.
- **Schema gap**: no `shadow_entries_total` or `receipts_written_total` field to distinguish "hooks fired but no claims" from "hooks didn't fire"

## Status

OPEN — design and implementation needed.

## Next steps

1. **Fix the evaluation script's registration detection** (`receipt_shadow_evaluation.py`) — make `hook_registration_status` check whether receipt files exist in the state directory, not whether a config path matches. This is the cheapest structural fix.

2. **Add observability fields to the evaluation summary schema** — `shadow_entries_total`, `receipts_written_total`. This makes "no data" distinguishable from "data exists but no claims."

3. **Design the diagnostic claim gate** — the pre-execution checklist for causal claims. Options from research:
   - **Jang-woo's approach**: `unknown` items block execution. Applied to diagnostics: before acting on "X is true because Y," require naming the evidence (receipt) for X and what evidence would refute X.
   - **Ishikawa fan-out**: before committing to a single causal chain, require naming at least 2 other dimensions (mechanical, measurement, process, behavioral) that could explain the observation.
   - **Receipt rule extension**: the existing AGENTS.md receipt rule targets causal claims about runtime behavior. Extend it to target diagnostic claims about system state ("hooks not registered" is a diagnostic claim about system state, not a causal claim about runtime behavior — the receipt rule as written doesn't clearly cover it).

4. **Implement the gate** — likely as a SKILL.md rule in a skill the agent uses during investigation (e.g., `/check`, `/aar`, or a new diagnostic-claim gate). NOT a hook — the gate needs to fire on the agent's own reasoning, which a hook cannot inspect.

5. **Evaluate shadow data** — now that the receipt writer is confirmed working (31 receipts in session `019f96f5`), accumulate 20+ sessions and evaluate agreement rate for the receipt system promotion decision.

## Read-first list

1. `P:/.data/wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md` — the 5 external approaches + gap analysis
2. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` — our root-cause diagnosis of the behavioral pattern
3. `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` — the parent pattern with 8 disguises
4. `P:/.data/wiki/concepts/problem-first-systems-decomposition.md` — the methodology that prevents jumping to solutions
5. `P:/docs/handoffs/multi-terminal-auto-commit-20260725/HANDOFF.md` — the receipt system handoff (updated with true state)
6. `https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632` — Jang-woo's pre-execution checklist (external)

## Key decisions and rationale

- **Multi-dimensional root cause analysis over Five Whys**: the receipt-system failure had 4 contributing dimensions. A linear "why" chain would have found one and missed the others. Ishikawa fan-out is the right tool for multi-causal failures.
- **Structural fixes over behavioral fixes**: the evaluation script bug (dimension 1) and schema gap (dimension 2) are structural and permanent. The behavioral pattern (dimension 4) can only be probabilistically mitigated. Fix structural causes first; behavioral mitigation is the fallback.
- **Receipt rule extension, not new rule**: the existing receipt rule already targets causal claims. The gap is scope — it covers runtime-behavior claims but not system-state diagnostic claims. Extending is cleaner than creating a parallel rule.

## Open questions

1. **Where does the diagnostic claim gate live?** Options: (a) AGENTS.md rule (behavioral, fires probabilistically), (b) a skill step in `/check` or `/aar` (structural within skill scope), (c) a new skill for diagnostic investigation. Recommendation: start with (a) + (b) — AGENTS.md for the rule text, `/check` Phase A for the structural enforcement (verifiers check whether the agent's diagnostic claims have receipts).

2. **How to handle the "checklist completeness" problem** (Jang-woo's acknowledged limitation)? The gate works only if the agent knows what to check. In the receipt-system case, the thing to check was "are receipt files being written?" — a question the agent didn't think to ask. No gate can force the agent to ask the right question if it doesn't know the question exists.

3. **Should the evaluation script be fixed now or batched with other receipt-system work?** The fix is cheap (~30 min) but the receipt system has other open work (promotion decision, F4 caching). Batching vs. shipping independently.

## What's verified (with receipts)

- [FACT] Receipt files exist with real data: 31 `.json` files in `quality-receipts-019f96f5-dc4a-79d0-9e17-396f2a582186/`, each containing verification commands, exit codes, file fingerprints, git blob OIDs. Receipt: `Get-ChildItem` output showing file names + sizes + timestamps.
- [FACT] Shadow comparison logs have real entries: 12 entries in `quality-shadow-019f9488-2a86-7bf1-ae6f-eeb341ec7095.jsonl` with `old_gate_decision`, `receipt_gate_decision`, latency metrics. Receipt: `Get-Content -Tail 3` showing JSON entries.
- [FACT] Evaluation summaries show `hook_registration_status: not_registered` despite hooks firing. Receipt: `Get-Content` of 5 evaluation summary JSONs all showing `not_registered` + `completion_attempts: 0`.
- [FACT] The receipt writer was already loaded via `verification-receipts.json` before my `quality-gate.json` edit. Receipt: `verification-receipts.json` exists with PreToolUse + PostToolUse hook entries pointing at `verification_receipt_writer.py`.

## Last user message (verbatim)

> "What's the problem? What's the cause of the problem? What's the causal chain to the root cause?"

(Then, after I provided the chain, the user asked me to research how others address this pattern, then asked for a handoff.)

## Other outstanding streams

- **Receipt system promotion**: needs 20+ sessions of shadow data (now accumulating), then evaluation of agreement rate. Blocked on data accumulation.
- **/check orchestrator implementation**: design approved (1380 lines), not implemented. 4 PRs planned. See `P:/docs/designs/2026-07-25-check-orchestrator-design.md`.
- **Static analysis gate**: design produced, critical friend returned REVISE (3 unverified premises). See `P:/docs/design/2026-07-25-static-analysis-gate/DESIGN.md`. Needs falsifier runs before PR 4.
- **Handoff cleanup**: 80+ handoffs, many stale.
