---
title: "DONE-trigger fires on artifact creation, not integration — chronic 4-recurrence harvest pattern"
created: 2026-08-02
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (chronic harvest sweep)
tags: [chronic-pattern, harvest, completion-discipline, integration-vs-creation, self-deception, lifecycle-skills, agentic-sdlc]
summary: >
  The agent declares work "done" the moment an artifact (file, concept, handoff)
  is written to disk — not when it is wired in, traced, or verified to be doing
  its job downstream. The harvest scan flagged this as a chronic 4-recurrence
  pattern (top-aging item 2026-08-02). This concept captures the failure mode
  and a structural test: "what would I do differently if the artifact didn't
  exist yet?" — if the answer is "nothing," the artifact is not yet done.
agent: grok
host: grok
cognitive_load: 2
verification: observed
tier: hot
half_life_days: 90
sources:
  - P:/.data/harvest/events/ (4+ DONE-trigger recurrences, 2026-07-26 through 2026-08-02)
  - P:/.data/wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md (same instance class)
  - P:/.data/wiki/concepts/trace-skill-execution-gap-critical-code-uncaught.md (instance: 9 edits, 0 traces)
  - P:/.data/wiki/concepts/lifecycle-skill-invocation-gap-parent-sibling-coverage.md
  - Session 019fa8f8 critical-code-trace report (wf_019fc0c81)
relations:
  - target: wiki/concepts/right-but-insufficient-hidden-output-quality-failure.md
    type: extends — that concept covers output that is right but insufficient; this covers completion that is artifact-present but integration-absent
  - target: wiki/concepts/structural-enforcement-for-skipped-rules-grok-build-2026.md
    type: related — both are rules-skipped-under-load; the difference is "rule skipped" (compliance) vs "completion declared prematurely" (judgment)
  - target: wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md
    type: example — hook scripts written but fail-open behavior never traced
  - target: wiki/concepts/trace-skill-execution-gap-critical-code-uncaught.md
    type: example — PreToolUse_spawn_model_gate.py edited 9x, 0 traces
  - target: wiki/concepts/operator-correction-as-highest-density-signal.md
    type: extends — operator-correction density is the detection signal; this concept is the underlying failure mode
  - target: wiki/concepts/chronic-workspace-health-debt-inventory-2026-08-01.md
    type: applies — the workspace's integration-verification scanners (hooks_audit, index_skills) are the structural defense
---

# DONE-trigger fires on artifact creation, not integration

## Decision context

**The problem:** the harvest scan on 2026-08-02 surfaced a chronic pattern
flagged as a top-aging item: "DONE-trigger fires on artifact creation not
integration — 4 recurrences" (alongside "PostToolUse auto-verify — 10 recurrences"
and "Code-output passthrough — 6 recurrences"). Across multiple sessions,
the agent commits a file, writes a wiki concept, or ships a handoff, then
declares the work done — even when the artifact has not been wired into
its downstream consumer, has not been traced, has not been tested, or
has not been observed firing.

The artifact exists. The work is not yet done. But the model treats
"file on disk" as completion because the file-write is the most concrete
action in the loop, and concrete actions feel like completion.

This is distinct from **right-but-insufficient output** ([[right-but-insufficient-hidden-output-quality-failure]])
where the artifact exists and is technically correct but missing sufficiency
layers — the artifact here is more likely to be **unfinished at the integration
level** (a hook script exists but its registration is broken; a wiki concept
exists but no other concept links to it; a code path is implemented but no
test covers it).

## Why this is chronic, not session-specific

The harvest scan shows 4+ distinct recurrences over 7 days, across multiple
session IDs and skill invocations. That makes it chronic by the
[[structural-enforcement-for-skipped-rules-grok-build-2026]] threshold (≥2
recurrences in 7 days). The instances span:

- **Hooks that exist but are not registered.** `snapshot_PreCompact.py` was
  a registered-via-hooks.json (not via `__lib/router.py`) drift; the file
  existed, looked done, and was silently not firing. Caught only by
  `hooks_audit.py` per [[chronic-workspace-health-debt-inventory-2026-08-01]].
- **Wiki concepts written but not cross-linked.** The auto-link step runs
  after every write, but a concept can be left dangling (no inbound links)
  and still feel "complete." The post-write gap detection (added 2026-08-02)
  surfaces these, but only when explicitly invoked.
- **Code paths that are written but not traced.** PreToolUse_spawn_model_gate.py
  was edited 9x across events 679-695 of session 019fa8f8 with zero trace
  reports. The edits produced file diffs, the file diffs felt like progress,
  the agent moved on. The trace gap is documented in
  [[trace-skill-execution-gap-critical-code-uncaught]].
- **Skills that exist in the catalog but are not invocable.** 237 of 657
  skills are marked disabled in `~/.grok/config.toml` — the catalog entry
  is "complete" but the skill is unreachable. Caught by `index_skills.py`.
  The same pattern is documented in [[chronic-workspace-health-debt-inventory-2026-08-01]].

In each case, the artifact's existence is the trigger; the artifact's
downstream function is what was supposed to be the trigger.

## Why the artifact-create action feels like completion

This is a closure-pressure failure mode with a specific mechanism:

1. **The file-write is a concrete, observable action.** "I just wrote
   `~/.grok/hooks/scripts/PreToolUse_spawn_model_gate.py`" is a statement
   the model can make with high confidence — it ran the tool, the tool
   returned success, the file exists.
2. **The downstream function is abstract and probabilistic.** "The gate
   now blocks serde-broken spawns" requires reasoning about the system at
   runtime, the registry contents, the spawn call sites, and the failure
   modes. That reasoning is harder to ground in a tool call.
3. **The concrete action is preferred over the abstract one.** Under
   session pressure (or any pressure), the model reaches for the
   confidence it can claim. "I wrote it" is confidence; "it works" is
   inference.

The harvest event log, with 4+ distinct DONE-trigger events across the
window, indicates this is a session-arc pattern rather than a one-shot
mistake. After 30+ turns of writing, the agent's DONE-trigger fires on
"wrote artifact N" rather than "verified artifact N is doing its job."

## The structural test

A simple check that catches the pattern at the moment of declaration:

> **"If the artifact did not exist yet, what would I do next?"**
> - If the answer is "I'd verify it's needed and write it" — the
>   artifact is not yet done (you've been treating writing as the
>   deliverable, but the deliverable is the integration).
> - If the answer is "I'd test it" — the artifact is not yet done
>   (the test is the deliverable, not the file).
> - If the answer is "I'd wire it up" — the artifact is not yet done
>   (the wiring is the deliverable).
> - If the answer is "nothing, it would be complete" — the artifact
>   is genuinely done.

The test forces the agent to separate the *existence* claim from the
*function* claim. The pattern is detected when the existence claim is
strong but the function claim is missing.

## Receipts

The mechanism claims in this concept are grounded in observed evidence, not
inference. Each claim has a specific implementation or artifact reference:

- **"4+ DONE-trigger recurrences over 7 days"** — `P:/.data/harvest/events/`
  directory (event JSON files timestamped 2026-07-26 through 2026-08-02);
  the harvest CLI counts DONE-trigger events as a separate category in
  `harvest.py:count_done_triggers()`. Receipt: scan-handoffs output
  captured in session 019fa8f8 transcript.
- **"Hooks exist but are not registered"** — `hooks_audit.py:REGISTRATION`
  bucket, specifically the 1-file drift on `snapshot_PreCompact.py`. The
  scanner walks `~/.claude/hooks/*.json` and `packages/.claude-marketplace/
  plugins/*/hooks/*.json`, then asserts the registration chain goes through
  `__lib/router.py`. Receipt: chronic-workspace-health-debt-inventory-2026-08-01.md §A.
- **"Code paths written but not traced"** — `trace-skill-execution-gap-critical-code-uncaught.md`
  documents the 9-edit, 0-trace instance on `~/.grok/hooks/PreToolUse_spawn_model_gate.py`
  across events 679-695 of session 019fa8f8. The pre-close-report for
  `wf_019fc0c81` flagged `critical-code-trace [fail]` with `agentFilesTouched=228`
  and `agentLinesAdded=64723`.
- **"237 of 657 skills disabled"** — `P:/.data/wiki/scripts/index_skills.py:compute_plugin_state()`
  parses `~/.grok/config.toml [plugins].disabled` and intersects with the
  catalog. Receipt: chronic-workspace-health-debt-inventory-2026-08-01.md §B.

## Falsifier

This concept is wrong if:
- A future session shows the agent consistently treats integration
  verification (not artifact creation) as the DONE-trigger — without
  the explicit test. The test is the scaffold, not the cure; the cure
  is the model learning to ask "what is the deliverable?" before
  "what is the artifact?"
- The 4-recurrence pattern does not reproduce in the next harvest scan.
- "Artifact creation" is the deliverable by design (a one-line rule
  whose function is its presence) — in that case the test produces
  "nothing, it would be complete" and the concept is moot.

## What this means for our workspace

1. **The post-write gap detection (added 2026-08-02 to /wiki) is one
   structural defense.** It surfaces dangling wikilinks, tag-cluster
   gaps, and stale references. But it only fires on `/wiki` writes, not
   on every file write. The agent should run it after writing ANY
   durable artifact, not just wiki concepts.
2. **`hooks_audit.py` and `index_skills.py` are the workspace's
   integration verifiers.** The [[chronic-workspace-health-debt-inventory-2026-08-01]]
   concept shows what they catch (REGISTRATION drift, SYNTAX errors,
   DANGLING_PATHS, STATE_GC, duplicate skills, orphan references).
   These scanners are the integration test for the "write" action.
   A session that writes hooks, plugins, or skills without re-running
   these scanners has triggered the DONE-on-create pattern.
3. **/trace is the integration test for critical code.** The
   [[trace-skill-execution-gap-critical-code-uncaught]] concept documents
   the recurring failure to trace. Critical code (anything in
   `~/.grok/hooks/`, `~/.grok/hooks/scripts/`, `P:/.claude/hooks/`, or
   anything tagged `verification-receipt`-adjacent) requires a trace
   before the session can claim completion. The `pre-close-report.md`
   critical-code-trace gate is the structural enforcement.
4. **A /wiki-written concept is not done until it is referenced by at
   least one other concept or handoff.** This is the litmus test for
   wiki concepts specifically. The post-write gap detection already
   catches dangling wikilinks; the next step is a minimum-link-count
   threshold (≥1 inbound link) for new concepts.
5. **The structural test ("what would I do differently if the artifact
   didn't exist yet?") should be added to the meta-checkpoint gate**
   in `/close` (per the "Did I audit my own output?" question). Asking
   the question at the moment of completion-claim is the cheapest
   place to catch the pattern.

## Sources

- `P:/.data/harvest/events/` — 4+ DONE-trigger recurrences over 7 days
- `P:/.data/wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md` — instance: hook scripts written but not traced
- `P:/.data/wiki/concepts/trace-skill-execution-gap-critical-code-uncaught.md` — instance: 9 edits, 0 traces
- Session 019fa8f8 critical-code-trace report (wf_019fc0c81) — Phase 3 timing
- `P:/.data/wiki/concepts/chronic-workspace-health-debt-inventory-2026-08-01.md` — workspace-state inventory
- `P:/.data/wiki/concepts/structural-enforcement-for-skipped-rules-grok-build-2026.md` — chronicity threshold
- `P:/.data/wiki/concepts/operator-correction-as-highest-density-signal.md` — detection signal

## Auto-related

- [[skill-catalog]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[inline-conditional-over-dispatch-for-skill-design]]
- [[user-modeling-for-agentic-clis]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]

