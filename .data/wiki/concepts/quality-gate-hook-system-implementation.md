---
title: "Quality Gate Hook System — Working Implementation"
created: 2026-07-23
source: session-2026-07-22
tags: [hooks, enforcement, quality-gate, stop-hook, posttooluse, verification, grok-build, implementation]
summary: >
  A four-file hook system that prevents the agent from claiming "done" on code
  changes without running verification. PostToolUse nudge detects test
  suites and writes file-specific hints. Stop gate blocks completion when
  claim + code modification + no verification all fire. SessionStart/End
  manages state lifecycle. Through 2 critique rounds and 1 review (43 findings,
  8 P0+P1 fixed). The hook caught the agent in real time during its own
  development, proving the enforcement is real.
agent: grok
host: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: implements
  - target: wiki/concepts/grok-build-stop-hook-agent-text
    type: refines
  - target: wiki/concepts/skill-enforcement-layers
    type: implements
  - target: wiki/concepts/challenge-triggered-verification-implementations
    type: related
---

## Summary

A working quality gate hook system at `~/.grok/hooks/` that mechanically
prevents unverified code completion claims. Built on 2026-07-22, refined
through 2 `/tp` critiques and 1 `/review` (43 total findings, 8 P0+P1
fixed). The hook caught its own developer mid-session — proving the
enforcement is structural, not behavioral.

## Architecture: four files, four events

```
~/.grok/hooks/
├── quality-gate.json              # Hook registration (4 events)
├── scripts/
│   ├── quality_gate.py            # Stop gate (~400 lines)
│   ├── quality_nudge.py           # PostToolUse nudge (~140 lines)
│   └── quality_cleanup.py         # SessionStart/End cleanup (~100 lines)
└── state/                         # Per-session state files (auto-cleaned)
```

| Event | Script | Purpose | Can block? |
|---|---|---|---|
| PostToolUse | quality_nudge.py | After code write: detect test suite, write file-specific hint to JSONL | No |
| Stop | quality_gate.py | At completion: block if claim + code modified + no verification | Yes |
| SessionStart | quality_cleanup.py | Sweep stale state files >24h old (startup only) | No |
| SessionEnd | quality_cleanup.py | Delete this session's state files | No |

## How the Stop gate works

Three signals, all must be true to block:

1. **Claim detection** from `lastAssistantMessage` — phrase-based regex
   matching "done", "fixed", "shipped", "tests passed", "is ready", etc.
   Negation-aware: "not done yet", "aren't finished", "isn't ready" all
   suppress the claim.

2. **Code modification** from transcript scan — iterates `entry["tool_calls"]`
   (NOT `entry["content"]` — that was a v1/v2 bug that took 2 critique
   rounds to catch) looking for `search_replace`/`write` to files with
   code extensions (`.py`, `.ps1`, `.sh`, `.js`, `.ts`, etc.).

3. **Verification detection** from transcript scan — checks for pytest,
   pyright, ruff, mypy, Invoke-Pester, `[Parser]::ParseFile`, test-named
   scripts, and `python -c` with verification keywords (`ast.parse`,
   `compile`, `unittest`).

Block fires only when: claim_made AND code_modified AND NOT verification_ran.

## Key design decisions (learned from bugs)

### `tool_calls` not `content`

Grok Build's `chat_history.jsonl` puts tool calls in a top-level
`tool_calls` array, NOT inside `content` (which is a string). The v1
and v2 plans both iterated `content` looking for tool calls — the gate
never fired. This was caught only when a subagent ran test code against
the real JSONL. Documented in [[grok-build-stop-hook-agent-text]].

### 2nd-pass checks current scan window only

On `stopHookActive=True` (agent was already blocked once), the gate
checks only what happened *since the last block* — not cumulative flags.
This is the hexisteme pattern from [[challenge-triggered-verification-implementations]].
If the agent ran verification → allow. If the agent dropped claim words → allow.
If the agent wrote more code without verifying → block again.

### Verification patterns are narrowed (not any execution)

Early versions accepted `python script.py` and `python -c` as verification.
This was trivially bypassable (`python -c "print('ok')"`). Now narrowed:
direct execution only counts when the filename contains test/verify/check/lint,
or when `python -c` contains `ast.parse`/`compile`/`pytest`/`unittest`.

### Nudge state cleaned up on allow-paths only

The PostToolUse nudge file is preserved when the gate blocks (so file
hints survive across passes) and deleted when the gate allows through.
SessionEnd cleanup is the backup for crashed sessions.

### Compaction-safe cursor

The state file tracks `(mtime, size, last_line)`. If the transcript
shrinks (compaction rewrote it), the cursor resets to scan fresh.

### Time-windowed verification freshness

If code was modified AFTER verification ran (detected via linear transcript
scan), the verification is stale and the gate blocks. Also: modifications
older than 10 minutes trigger staleness regardless of ordering.

## State lifecycle

| State file | Written by | Read by | Cleaned up by |
|---|---|---|---|
| `quality-gate-<session>.json` | Stop gate (cursor) | Stop gate | SessionEnd + SessionStart sweep |
| `quality-nudge-<session>.jsonl` | PostToolUse nudge | Stop gate (file hints) | Stop gate (on allow) + SessionEnd |
| `quality-gate-<session>.log` | Stop gate (trace) | Human/agent debugging | SessionEnd |
| `quality-cleanup-debug.log` | Cleanup script | Human debugging | Never (known limitation) |

## Known limitations (from `/review` P2 items)

- CODE_EXTENSIONS excludes C/C++/C#/Swift/Kotlin (hardcoded)
- No shared module — constants duplicated across 3 files
- Nudge file grows unbounded within a session (no cap)
- UUID regex is lowercase-only (`[0-9a-f-]`, missing A-F)
- Negation check is global, not windowed (Finding 7 from review)
- No configurability (hardcoded thresholds, no config file)
- First-fire transcript scan has no line cap (could exceed 60s on huge transcripts)
- `quality-cleanup-debug.log` never rotated

## What this does NOT catch (the three-layer model)

This hook is **Layer 1** of a three-layer verification strategy:

1. **Stop hook** (this system) — forces verification to run at all ✅
2. **Skill step** (future) — forces ground-truth inspection before coding ❌
3. **Testing strategy** (future) — ensures verification is meaningful ❌

Layer 1 catches "agent claimed done without running anything." Layer 2
catches "agent wrote code from assumptions without reading real data."
Layer 3 catches "agent ran tests but the tests don't actually test the
right thing." Each layer is independent.

## Proven in production

The hook caught its own developer (me) mid-session:
- First catch: wrote `test_gate2.py`, said "Done." → blocked
- Second catch: modified hook files after verification → time-window stale
- Third catch: kept claiming completion in loop responses → 2nd-pass blocked

Each catch was the correct behavior for the signal detected.

## Sources

- Implementation files: `~/.grok/hooks/`
- `/review` findings: `P:\.artifacts\console_c0d59c27-a0ec-424a-b5d6-cb19\grok-review\hook-system\20260722-232548-076\FINDINGS.md`
- Plan (v3): session plan file
- Research: [[challenge-triggered-verification-implementations]], [[mandatory-step-enforcement-code-over-prose]], [[skill-enforcement-layers]], [[grok-build-stop-hook-agent-text]]

## Related

- [[mandatory-step-enforcement-code-over-prose]]@implements
- [[grok-build-stop-hook-agent-text]]@refines
- [[skill-enforcement-layers]]@implements
- [[challenge-triggered-verification-implementations]]@related
- [[verification-before-completion-principle]]@related

## Auto-related

- [[exemption-logic-as-conflict-signal]]
- [[i'm-going-to-create-a-hook-to-enforce-discovery-be]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
