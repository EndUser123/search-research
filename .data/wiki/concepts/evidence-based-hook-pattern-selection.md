---
title: "Evidence-based hook pattern selection — scan incidence before building detection"
created: 2026-08-09
source: session-2026-08-09 (R002 zero-incidence finding from 2,496-session scan)
tags: [hooks, evidence-first, pattern-selection, detection, false-positive, code-pattern, methodology, measurement]
summary: >
  Before building a detection hook for a "known failure pattern," scan
  historical session data for the pattern's actual incidence rate. A pattern
  documented in the wiki as a failure mode may have zero real-world occurrence
  because existing prose rules already prevent it. Building a hook for a
  zero-incidence pattern is dead weight: it adds latency and maintenance burden
  with zero catch rate. The evidence scan takes seconds (grep chat_history.jsonl)
  and prevents investing design and implementation effort on phantom problems.
  This is the same principle as [[obligation-enforcement-vs-justification-detection]]:
  check the evidence before proposing, not after.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Session 019fdf3d (2026-08-09): R002 (missing encoding) proposed from wiki concept without incidence check; 2,496-session scan showed zero incidence. R001 (backslash paths) showed 625 write-tool calls with the pattern.
relations:
  - target: wiki/concepts/obligation-enforcement-vs-justification-detection.md
    type: complements — that concept covers WHY prose-semantic gates fail; this covers HOW to decide whether to build a hook at all
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related — both are evidence-first disciplines against plausible-but-unverified proposals
  - target: wiki/concepts/lexical-vs-semantic-verification-gap.md
    type: related — both are about checking the right layer before trusting a signal
  - target: wiki/concepts/narrative-as-signal-anti-dismissal-rule.md
    type: related — plausible narratives (including "this pattern is worth hooking") are signals to investigate, not conclusions
  - target: wiki/concepts/knowledge-capture-cant-afford-to-lose.md
    type: related — the capture principle "when in doubt, capture" has a mirror: "when in doubt, measure before building"
---

# Evidence-based hook pattern selection

## Decision context

**The problem:** during session 019fdf3d, a code-pattern-checking hook was designed with two initial patterns (R001 backslash paths, R002 missing encoding). R002 was proposed because the wiki documents the encoding hazard and AGENTS.md has a prose rule for it. The pattern is real, mechanically detectable, and could cause silent corruption. All true.

**What wasn't checked:** whether agents actually make this mistake. The operator asked: "Why are we doing a 14-day waiting period? Can you look at historical session data?"

The scan of 2,496 Grok sessions and 8 Claude session files found **zero** occurrences of `open()` without `encoding=`. The AGENTS.md prose rule was working. R002 was dead weight — a hook for a problem that doesn't occur.

## The principle

**Before building a detection hook for a "known failure pattern," measure the pattern's actual incidence rate in historical session data.** The measurement is cheap (grep `chat_history.jsonl` across sessions). The cost of not measuring is investing design and implementation effort on phantom problems, then calibrating shadow periods for firing rates that don't exist.

This is the same evidence-first principle the session was diagnosing in the equivalence-bypass gate: the gate detected justification language without checking whether the obligation was actually unmet ([[obligation-enforcement-vs-justification-detection]]). Here, I proposed a hook pattern without checking whether the pattern actually occurs. The /narrative-as-signal-anti-dismissal-rule applies: "this pattern is worth hooking" was a plausible narrative, not a verified finding.

## Worked example

```
Proposed pattern: R002 — detect open() without encoding="utf-8"
Evidence basis:   wiki documents the hazard; AGENTS.md has a prose rule

Incidence scan:
  python scan: 2,496 Grok sessions → 0 occurrences
  python scan: 8 Claude session files → 0 occurrences

Conclusion: the prose rule is working. Zero incidence = no evidence base for a hook.
Action: drop R002. Add it only if a real incident occurs.
```

Contrast with R001 (backslash paths): 625 write-tool calls contained the pattern across 2,496 sessions. High incidence, unambiguous harm, clear evidence base. Ship it.

## What this means for our workspace

1. **Every proposed hook pattern must include an incidence scan before implementation.** The scan greps `chat_history.jsonl` files for the pattern in write-tool calls (not prose mentions — the pattern must appear in `new_string` of `search_replace` or `write` tool inputs).

2. **Zero-incidence patterns are not hooks.** They may become hooks later if incidence appears, but building them speculatively adds latency and maintenance burden with zero catch rate.

3. **The incidence scan also calibrates the shadow period.** If a pattern fires 625 times across 2,496 sessions (~25%), no shadow is needed — there's enough data. If it fires 5 times (~0.2%), a 14-day shadow won't produce statistically meaningful data. The shadow period should be proportional to the inverse of the incidence rate.

4. **This applies to all detection mechanisms, not just PreToolUse hooks.** Stop hooks, PostToolUse hooks, and advisory scanners all have the same false-positive and dead-weight costs. Measure before building. The [[knowledge-capture-cant-afford-to-lose]] principle says "when in doubt, capture" — the mirror is "when in doubt about whether to build, measure."

## Falsifier

This principle is wrong if:
- A pattern with zero historical incidence suddenly appears at high rate after a model upgrade or workflow change. The historical scan would have shown zero, but the pattern would be real. Mitigation: re-scan after major model/workflow changes.
- The incidence scan produces false negatives because the regex doesn't match all forms of the pattern. Mitigation: validate the scan regex against known-positive examples before trusting zero results.
- The prose rule that was preventing the pattern gets removed or weakened, and the pattern re-emerges. Mitigation: if the prose rule is removed, add the hook proactively.

## Receipts

- **R002 zero-incidence finding:** session 019fdf3d, scan of 2,496 Grok sessions + 8 Claude session files, run via PowerShell grep of `chat_history.jsonl`. Command output: "Sessions with open() without encoding: 0" (Grok), "Files with open() and no encoding= anywhere: 0" (Claude).
- **R001 high-incidence finding:** same scan, "Write-tool calls containing backslash path in new_string: 625" across 2,496 sessions.
- **The proposal-without-evidence pattern:** session 019fdf3d, R002 was proposed from `inference-in-code-blind-spot.md` wiki concept without incidence check. Operator correction: "Why did we even come up with this idea then, for it?"

## Auto-related

- [[skill-catalog]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]

