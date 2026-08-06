---
title: "Parallel subagent wait-all-before-conclude gate"
created: 2026-07-26
source: session-2026-07-26
sources:
  - internal: session 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9 — first /www run on operator-modeling where disconfirmation subagent completed after concept was already persisted
tags: [parallel-subagents, wait-all, orchestration-discipline, anti-premature-conclusion, fan-out, skills]
agent: grok
host: both
cognitive_load: 2
verification: local-only
summary: >
  When an orchestrator skill (/www, /risk, /aar, /dream, /debrief) dispatches
  N background subagents via spawn_subagent(background=true), NO durable artifact
  (wiki write, ledger entry, commit, run directory, conclusion in the response)
  may be emitted until get_command_or_subagent_output with ALL N task IDs returns
  every task as completed or explicitly failed. "Task not found" is a mechanical
  error in the orchestrator, not a signal to proceed.
relations:
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: related
  - target: wiki/concepts/inference-chains-bare-numbers-destructive-write.md
    type: refines
---

# Parallel subagent wait-all-before-conclude gate

## The rule (canonical)

When an orchestrator skill has dispatched N background subagents via `spawn_subagent(background=true)`:

1. **No durable artifact may be emitted** — wiki write, ledger entry, commit, run directory, persistent state file, **or a conclusion stated as fact in the response** — until `get_command_or_subagent_output(task_ids=[all-N-ids], timeout_ms=<positive>)` returns ALL N tasks as `completed` or explicitly failed.
2. **"Task not found" recovery protocol (revised 2026-07-31 after two false-negative incidents — original protocol was too strict):**
   - **Mode 1 (typo):** ID doesn't match any `spawn_subagent` return in the transcript → re-read the return value, recover the correct ID, re-issue the wait.
   - **Mode 2 (backend lag):** ID is correct but lookup returns "not found" → retry once with `timeout_ms=30000`. The backend lookup may be lagging behind the subagent lifecycle.
   - **Mode 3 (genuine loss):** Still "not found" after retry → proceed with either (a) a **parallel re-spawn** to maintain quality (preferred), or (b) a serial fallback **labeled as degraded**. Do NOT block indefinitely.
   - **When the original arrives (all modes):** fold its findings in. The original is **never discarded**.
3. **Re-spawning is now permitted in Mode 3** (revised from the original "never re-spawn" rule). The original "never re-spawn" rule was written from a single incident (2026-07-26) and proved too strict — it forced serial fallback that degraded quality in sessions 2026-07-26 and 2026-07-31. The revised protocol preserves the core insight (original findings are always folded in) while removing the quality penalty.
4. **Persistence-before-completion is the canonical failure.** If the orchestrator catches itself about to emit a conclusion while any task is still pending, the correct action is: WAIT LONGER. Re-issue `get_command_or_subagent_output` with a longer `timeout_ms`. State in the response: "waiting for N outstanding subagents before concluding." If the wait itself times out, either (a) escalate to the user "subagent X is taking >Y min; proceed with partial data?" or (b) continue waiting — but never silently emit conclusions.

## Why this rule exists

**Reference failure (2026-07-26):** a `/www` run on operator-modeling dispatched 5 parallel research subagents + 1 discovery + 1 disconfirmation. The orchestrator issued `get_command_or_subagent_output` with two task IDs (discovery + disconfirmation); one ID was mistyped and returned "task not found." The orchestrator interpreted "not found" as "failed/disappeared" rather than "your wait call is malformed," re-spawned the disconfirmation subagent, waited for the re-spawn, and persisted the wiki concept + commits based on its output. The original disconfirmation subagent completed ~2 minutes later with **three additional peer-reviewed sources** (P-DPO OpenReview 132 cit, Qian 2021 66 cit, MIT/Penn State ACM CHI 2026) that materially strengthened the disconfirmation. The orchestrator had to patch the wiki concept in a follow-up turn.

**The cost:** ~30 minutes of operator attention, two extra commits, a patched concept, and reduced confidence in the first persist. All avoidable if the orchestrator had treated "task not found" as a malformed-wait signal rather than a task-completion signal.

**Root cause:** there was no explicit rule that "all dispatched subagents must return before persistence." The implicit norm ("of course you wait") did not fire under context momentum and the social-pressure-feeling of "I should produce a response now." Structural rules fire reliably under pressure; implicit norms do not.

## Why this matters beyond the single incident

This rule sits at the intersection of three existing failure classes already documented in the wiki:

1. **Closure pressure / premature conclusion.** The same family as `reactive-pattern-matching-and-closure-pressure` and `narrative-sufficiency-is-not-verification`. The orchestrator reaches a point where "I have enough to ship" feels true, and the missing subagent is treated as background noise rather than missing evidence.
2. **Deferred persistence.** `~/.grok/AGENTS.md` § "No deferred persistence" already requires that stated intent to write produce a write in the same turn. This rule is the inverse: do NOT write prematurely when more data is incoming. The two together bracket the write window — write when intended, but not before evidence is complete.
3. **Inference chains / bare numbers / destructive write.** `[[inference-chains-bare-numbers-destructive-write]]` is the broader discipline of not acting on inference when verification is available. A partial-subagent conclusion IS acting on inference — "the missing subagent probably doesn't change the answer" is itself an unverified claim.

**The class of failure this catches that the existing rules do not:** all three existing rules are about *what to write* (with receipts, not as inference). This rule is about *when to write* — a temporal gate, not a content gate. Without it, an orchestrator can satisfy every content rule (receipts, evidence tiers, falsifier) and still ship prematurely because it shipped before all evidence arrived.

## How to apply

### For orchestrator skills (/www, /risk, /aar, /dream, /debrief)

Add a single rule near the parallel-dispatch section:

> **Wait-all-before-conclude gate (mandatory):** before emitting any durable artifact OR a conclusion stated as fact in the response, issue `get_command_or_subagent_output(task_ids=[every-dispatched-id], timeout_ms=<positive>)` and require every task to be `completed` or explicitly failed. "Task not found" is a mechanical error — re-read the `spawn_subagent` return to recover the correct ID and re-issue the wait. Do NOT re-spawn duplicates to work around a malformed wait; the original is still running. See [[parallel-subagent-wait-all-gate]].

### For the orchestrator model (always-on, not just inside skills)

Two related invariants already in AGENTS.md:
- "No deferred persistence" — stated intent to write must produce a write in the same turn
- "Claims require receipts" — a causal claim without a receipt does not ship as fact

**This rule extends them:** stated intent to dispatch N subagents requires waiting for all N before any of: (a) persisting based on partial results, (b) shipping a conclusion as fact, (c) stating "research complete." A partial-result conclusion must be labeled as such: "conclusion based on N-1 of N dispatched subagents; subagent X is still running and its output may revise this."

## Failure modes the rule prevents

| Failure mode | Without the rule | With the rule |
|---|---|---|
| Typo in task ID | Silently treated as "task done/failed"; conclusion emitted on partial data | Wait call rejected; orchestrator re-reads spawn_subagent output to recover ID |
| Re-spawn of duplicate | Original completes later with stronger evidence; orchestrator must patch | Forbidden; orchestrator waits for original or kills it explicitly |
| Partial-result persistence | Wiki concept / commit written based on N-1 of N subagents | Forbidden; persistence deferred until all N return |
| Closure-pressure conclude-now | "I should produce a response now" overrides wait discipline | Structural rule fires; orchestrator emits "waiting for N outstanding subagents" instead of concluding |
| Lost ID through compaction | Orchestrator forgets which subagents are pending; emits conclusion | Orchestrator re-reads recent turn's `spawn_subagent` returns to recover IDs before any conclusion |

## Falsifier

This rule is wrong if, within 6 months:

- **Wait times become intolerable.** If subagents routinely take 5+ minutes and the operator is complaining about latency, the rule is too strict. Fix: allow the orchestrator to surface "still waiting on X" and let the operator decide whether to proceed with partial data (operator override).
- **The rule never catches a real partial-persistence event.** If no instance of "task not found" or "still pending at persistence time" recurs in 6 months, the rule is defensive overhead. Fix: retire.
- **The rule blocks legitimate kill-and-retry.** If a subagent is genuinely stuck (not slow — stuck), the operator should be able to kill it explicitly via `kill_command_or_subagent` and proceed. The rule allows this; falsifier is whether the rule's "no re-spawn" clause gets in the way of legitimate abandonment.

## Related

- [[inference-chains-bare-numbers-destructive-write]] — the broader discipline of not acting on inference when verification is available
- [[agent-failure-modes-2026]] — the taxonomy this failure belongs to
- [[llm-handoff-best-practices]] — handoff/persistence discipline this extends
- `~/.grok/AGENTS.md` § "No deferred persistence" and § "Claims require receipts" — the always-loaded invariants this rule extends

## Sources

- Session 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9 (2026-07-26) — direct observation of the failure mode that produced this rule
- `~/.grok/skills/www/SKILL.md` § "Parallel subagent dispatch (for broad topics)" — the section where the failure occurred

## Receipts (mechanism claims)

- **"5 parallel research subagents + 1 discovery + 1 disconfirmation dispatched":** receipt — the `spawn_subagent` calls earlier in this session (subagent IDs `019f9f55-393d-...`, `-393e-...`, `-393f-...` ×2, `-3940-...` for research; `019f9f59-43db-7402-...` for discovery; `019f9f59-43db-7402-bd4e-f42425132ffb` for disconfirmation).
- **"One task ID was mistyped and returned 'task not found'":** receipt — the `get_command_or_subagent_output(task_ids=["019f9f59-43db-7402-bd4e-f419e8457ade", "019f9f59-4242-5132-ffb-disconfirm"])` call returned `Task 019f9f59-4242-5132-ffb-disconfirm not found`. The ID I used was a hand-typed truncation, not the actual returned ID.
- **"Original disconfirmation subagent completed ~2 minutes later with three additional peer-reviewed sources":** receipt — the system-reminder arrived at the start of this turn reporting `019f9f59-43db-7402-bd4e-f42425132ffb` completed with duration 155.9s, and `get_command_or_subagent_output` on it returned the three sources (P-DPO OpenReview, Qian 2021, MIT CHI 2026 Jain et al.).
- **"The wiki concept had to be patched":** receipt — the second commit `39244cc` in this session ("docs(wiki): user-modeling concept disconfirmation upgrade") was the patch.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
