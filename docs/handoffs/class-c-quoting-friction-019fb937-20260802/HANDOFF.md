---
thread_id: class-c-quoting-friction-019fb937
parent_handoff_path: P:/docs/handoffs/hook-timeout-root-cause-and-deferred-work-20260801/HANDOFF.md
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
parent_session: 019fb937-b03e-7f80-a4b0-68afdb7da38d
current_terminal_id: 311cd4b1-2bf4-47ec-8abd-7530e971493c
produced_at: 2026-08-02T05:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 963c0aff7cb1f5a5ecd83a76e1844b1890049218
---

# Handoff: Class C quoting friction enforcement

## Objective

Reduce inline `python -c` failures by enforcing temp-file usage for multi-line Python payloads.

## Status

OPEN — 11 Class C quoting failures observed this session; no enforcement improvement implemented yet.

## Producing context

- Session: `019fb937-b03e-7f80-a4b0-68afdb7da38d` (2026-07-31 → 2026-08-02)
- Terminal: 311cd4b1-2bf4-47ec-8abd-7530e971493c
- Host: grok (Grok Build)

## Read-first list

1. `~/.grok/AGENTS.md` § "Class C: shell quoting" — the existing rule
2. `P:/.data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md` — the systemic pattern
3. `C:/Users/brsth/.grok/hooks/quality-gate.json` — the hook registration

## Verified facts

- [FACT] 11 Class C quoting failures occurred this session from inline `python -c` probes (source: transcript scan)
- [FACT] 10 were Traceback errors, 1 was a SyntaxError (source: transcript scan)
- [FACT] The existing AGENTS.md rule says "for multi-line or nested-quote shell payloads, write to a temp file and invoke against the file" (source: AGENTS.md § Class C)
- [FACT] The rule is not being followed — operators continue to use inline `python -c` for multi-line payloads
- [FACT] The existing rule has been in AGENTS.md since session 019f9f4f (2026-07-26) — 6+ sessions of non-compliance

## Current state

- The rule exists in AGENTS.md but compliance is low
- No mechanical enforcement (hook) exists to detect or prevent the violation
- The rule is a behavioral guideline, not a enforced constraint

## Task packets

### TP-02a: Strengthen AGENTS.md Class C rule

- **id:** CC-01
- **goal:** Add concrete examples and consequences to the Class C quoting rule
- **in scope:** `~/.grok/AGENTS.md` § "Class C: shell quoting"
- **out of scope:** New hooks or scripts
- **acceptance:** The rule includes at least 2 concrete examples of correct vs incorrect usage
- **falsifier:** Same number of Class C failures in next session (no behavior change)
- **verification level required:** STATIC_INSPECTION

### TP-02b: Add PreToolUse hook for multi-line python -c detection

- **id:** CC-02
- **goal:** Add a PreToolUse hook that detects multi-line `python -c` in run_terminal_command and warns/blocks
- **in scope:** `~/.grok/hooks/PreToolUse_class_c_quoting.py`
- **out of scope:** Single-line `python -c` (acceptable risk)
- **acceptance:** Hook fires on multi-line `python -c` with >1 statement; operator can override with `--force`
- **falsifier:** >3 inline `python -c` multi-statement failures in a future session despite the hook
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 2 hours (implementation + test)

### TP-02c: Both (belt and suspenders)

- **id:** CC-03
- **goal:** Implement both the strengthened rule (CC-01) and the detection hook (CC-02)
- **in scope:** Both CC-01 and CC-02
- **acceptance:** Both the rule and hook are in place; compliance improves
- **falsifier:** Same or higher failure rate in next session
- **verification level required:** LIVE_BEHAVIOR
- **Leading option:** CC-03 (both) — the rule is cheap, the hook is reliable

## Open decisions

### OD-01: Class C enforcement mechanism

- **Question:** Should the Class C quoting fix be a behavioral rule (strengthened AGENTS.md) or a mechanical hook?
- **Options:** (1) Stronger AGENTS.md rule with examples [low cost, ~50% compliance ceiling] (2) PreToolUse hook that detects multi-line `python -c` and warns [mechanical, higher compliance] (3) Both [belt and suspenders]
- **Selection criterion:** compliance rate vs implementation cost
- **Currently leads:** Option 3 (both) — the rule is cheap, the hook is reliable
- **What would change it:** if the existing rule's compliance is actually high and this session was an anomaly

## Hard constraints

- The hook must not break existing workflows
- The hook must allow override for legitimate single-line `python -c` usage
- The rule must be clear enough that a cold-start reader understands the requirement

## Cross-reference couplings

- `~/.grok/AGENTS.md` → contains the existing Class C quoting rule
- `P:/.data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md` → describes the systemic pattern of analysis without action
- `C:/Users/brsth/.grok/hooks/quality-gate.json` → hook registration file

## Resumption protocol

1. Decide on enforcement mechanism (OD-01)
2. If Option 3 (both): implement CC-01 (strengthen rule) and CC-02 (add hook)
3. Verify the hook fires correctly on multi-line `python -c`
4. Monitor failure count in next session

## Suggested next invocation

```
/go CC-01 — strengthen the AGENTS.md Class C quoting rule with examples
/go CC-02 — add PreToolUse hook for multi-line python -c detection
```

## Last user message (verbatim)

> "Please use the handoff skill"

## Epistemic labels per claim

- [FACT] 11 Class C quoting failures — sourced from transcript scan
- [FACT] The rule exists in AGENTS.md — sourced from reading AGENTS.md
- [INFERENCE] Compliance is low — based on 11 failures in one session vs the rule existing for 6+ sessions
- [INFERENCE] Option 3 (both) is leading — based on the cost/compliance tradeoff analysis

---

## Revision 1 — 20260802T051500Z (session 019fb937-b03e-7f80-a4b0-68afdb7da38d)

**Trigger:** auto-update — HEAD drifted from 448e0b3 to 963c0af (3 new commits since handoff was written).

**What changed since the original:**
- 3 new commits landed: capture rhai workflow launch-time snapshot staleness pattern (963c0af), run-everything-explicitly pattern documented (9516871), close-runner Windows-path JSON-stringification bug wiki concept (0f2472c)
- accurate_as_of_head bumped to 963c0af

**Updated evidence:**
- git rev-parse HEAD → 963c0aff7cb1f5a5ecd83a76e1844b1890049218

**Status update:** unchanged — additional evidence only

**New open items:** none

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:00 | 019fb937... | created |
