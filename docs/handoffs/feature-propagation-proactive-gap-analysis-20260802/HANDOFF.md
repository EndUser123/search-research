---
thread_id: feature-propagation-proactive-gap-analysis-20260802
parent_handoff_path: none
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
current_terminal_id: grok-build-terminal
produced_at: 2026-08-02T20:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 992b8d5
---

# Feature propagation + proactive gap analysis

## Objective

Investigate why the agent consistently ships features without propagating them to consumers, and surfaces findings without proactively identifying system-level gaps. The pattern recurs across sessions: the agent builds something, stops, and only connects it to the broader system when the operator asks.

## Problem instances from this session chain

1. **Ranked harvest built but not wired.** The agent built `harvest show --ranked` (leverage scoring) but didn't think about which skills should consume the ranked output. The operator asked "what other skills should it be added to?" — the gap the agent should have surfaced.

2. **Harvest items without handoffs.** 12 of 20 harvest items had no execution path. The agent didn't notice this structural gap until the operator asked "do the harvest items have handoff files?"

3. **Operator's "wouldn't you maintain it?" missed as a redirect.** The operator was telling the agent its rejection reasoning was wrong. The agent answered literally instead of recognizing the pragmatic intent.

4. **Operator's "are you considering [time pressure] systematically?" was the catalyst.** The agent had built cost-of-inaction as a field but never used it as a sorting function. The operator saw the systematization gap the agent missed.

## Root cause

The agent operates in "build mode" — finish the immediate task, commit, move on. It doesn't run a "consumer check" after shipping: "who needs this output, and are they wired to receive it?" This is the same pattern as the producer-consumer drift documented in `[[skip-write-only-computation-over-cache-or-budget]]` — the producer ships but doesn't verify consumers exist.

## Proposed approach

### Option A: Add a "consumer check" step to /go and /handoff

After shipping any feature, the agent asks: "What consumes this output? Are those consumers wired?" This is a behavioral rule — same structural weakness as the verify-after-commit rule.

### Option B: Add a "propagation check" to /tp improve

The /tp improve analysis already asks "what improvements are possible?" Add a standing question: "Did this session ship any feature whose output isn't consumed by downstream skills?" This catches the gap at session review time, not at ship time.

### Option C: Structural — add "provides" and "consumes" frontmatter validation

The skill graph already has `provides` and `consumes` frontmatter. When a new capability is provided, validate that at least one other skill consumes it (or document why it's standalone). This is the structural fix but requires extending the capabilities graph validator.

## Acceptance criteria

1. After shipping a feature that produces output other skills could use, the agent proactively surfaces: "This output should be consumed by [skills]. Wire them?"
2. After building a data store (harvest, wiki, tasks), the agent proactively surfaces: "N% of items have no execution path. Close the gap?"
3. The pattern is detected in /tp improve as a recurring dimension, not just one-off findings

## Read-first list

1. `P:/.data/wiki/concepts/skip-write-only-computation-over-cache-or-budget.md` — the producer-consumer drift pattern
2. `P:/.data/wiki/concepts/inter-skill-output-bridges-and-temporal-surfacing-layers.md` — inter-skill composition patterns
3. `~/.grok/skills/go/SKILL.md` — Step 0 (where /go's harvest check was added)

## Falsifier

This approach is wrong if the "consumer check" produces too many false positives (fires on features that are genuinely standalone) or if the behavioral approach (A/B) doesn't fire reliably under session pressure.
