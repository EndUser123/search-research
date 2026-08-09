---
title: "Stop-hook state-file keyword enforcement creates unbreakable agent feedback loops"
concept_type: "failure-mode"
created: 2026-08-06
source: session-019fc927 (ship-py pipeline invoked post-commit)
tags: [hook-design, stop-hook, state-file, keyword-matching, feedback-loop, ship-py, quality-gate, transferable-pattern, agent-trap]
agent: grok
host: both
cognitive_load: 2
verification: source-verified
summary: >
  When a Stop hook checks BOTH a keyword pattern in the agent's message AND a
  persistent state file, it creates a feedback loop the agent cannot escape by
  rephrasing. The keyword regex matches negative forms ("cannot complete") the
  same as positive forms ("is complete"), and the state file persists across
  turns so rephrasing doesn't help. The agent is trapped: it can't explain the
  problem without triggering the hook, and it can't satisfy the hook without
  doing work that's already been done. The only escape is programmatic state
  file modification. This extends the conversation-collapse pattern from
  [[llm-judgment-hooks]] with a state-file coupling that makes the loop
  structurally unbreakable.
relations:
  - target: wiki/concepts/llm-judgment-hooks
    type: extends
  - target: wiki/concepts/hook-regex-false-positives-pasted-terminal-output
    type: extends
  - target: wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism
    type: related
  - target: wiki/concepts/ship-pipeline-enforcement-pretooluse-phase-state-hooks
    type: related
---

# Stop-hook state-file keyword enforcement creates unbreakable agent feedback loops

## Decision context

**Why this knowledge was needed:** during session 019fc927, the operator
invoked `/ship-py` after all session work was already committed and pushed.
The pipeline's Phase 0 (detect) ran successfully and created a state file
at `P:/.artifacts/ship-py/<session-id>/state.json` with
`completed_phases: ["detect"]`. The remaining phases (review, verify,
verdict) could not produce meaningful results on already-pushed commits.
When the agent attempted to explain this to the operator — "the ship-py
pipeline cannot complete because the work is already committed" — the
quality_gate.py Stop hook blocked the message. The regex matched
"ship-py" + "complete" in the negative explanation just as it would in a
positive completion claim. The state file showed incomplete phases,
confirming the hook's suspicion. The agent was trapped in a loop until it
manually wrote `{"phase": "aborted", "verdict": "ABORTED"}` to the state
file using a shell command.

## The mechanism (source-verified)

The quality_gate.py Stop hook at lines 160-220 implements pipeline
abandonment detection with two coupled checks:

**Layer 1 — keyword pattern (line 163-164):**
```python
_SHIP_PY_CLAIM_PATTERNS = [
    re.compile(r"\bSHIP\s+DONE\b", re.IGNORECASE),
    re.compile(r"\bship[- ]py\b.*\b(?:done|complete|passed|verified)\b", re.IGNORECASE),
]
```

The second pattern matches the co-occurrence of "ship-py" and any of
"done/complete/passed/verified" anywhere in the message. It does NOT
distinguish "ship-py is complete" (positive claim) from "ship-py cannot
complete" (negative explanation). Both match the same regex.

**Layer 2 — state file check (line 191-220):**
```python
state_path = Path("P:/.artifacts/ship-py") / session_id / "state.json"
# ... reads state ...
missing = _REQUIRED_SHIP_PY_PHASES - completed
if missing:
    return f"SHIP DONE claimed but ship-py pipeline is incomplete..."
```

The state file persists across turns. Once Phase 0 writes it, every
subsequent turn where the agent mentions "ship-py" near "complete" is
blocked — regardless of whether the agent is making a positive claim or
explaining a failure.

**The feedback loop:**
1. Agent invokes `/ship-py` → Phase 0 creates state file
2. Agent realizes work is already shipped → tries to explain
3. Message contains "ship-py" + "complete" → regex matches
4. State file shows incomplete phases → hook blocks (exit 2)
5. Agent rephrases → "ship-py" must appear to explain the problem → still matches
6. No escape via rephrasing (the state file is persistent)
7. Only escape: manually write an abort state to the file

## Why this is worse than the conversation-collapse pattern

[[llm-judgment-hooks]] documents the "conversation collapse pattern" where
regex false positives cause agent retry loops. That pattern is escapable:
the agent can rephrase to avoid the trigger words, and the loop eventually
breaks when the rephrasing succeeds.

**State-file coupling makes the loop structurally unbreakable.** The agent
cannot escape by rephrasing because:
- The trigger keyword ("ship-py") must appear in the message to explain
  the problem — you can't explain a ship-py failure without naming ship-py
- The state file persists across turns — it doesn't decay or expire
- The regex matches negative forms just as readily as positive forms
- There is no programmatic API to mark the pipeline as "aborted" or
  "cannot run" — the agent had to discover the state file path and write
  raw JSON to it via shell

The only structural fix the hook message itself suggests is: "explicitly
state the pipeline cannot run (e.g., work already committed)." But doing
so triggers the very regex the hook uses to detect completion claims —
the message contains "ship-py" and "cannot run" doesn't match, but
"cannot complete" does match the pattern.

## The negative-match problem

The regex `\bship[- ]py\b.*\b(?:done|complete|passed|verified)\b` is a
co-occurrence matcher: it checks that "ship-py" and a completion word
appear in the same message, regardless of semantic relationship. This
means:

| Agent message | Matches? | Intended? |
|---|---|---|
| "ship-py is complete" | Yes | Yes — real completion claim |
| "SHIP DONE" | Yes (pattern 1) | Yes — real completion claim |
| "ship-py cannot complete" | Yes | **No** — negative explanation |
| "ship-py pipeline was unable to finish" | Yes ("finish" ≠ pattern) | No — but safe |
| "ship-py was verified by another process" | Yes | Ambiguous |

The pattern has no way to exclude negative forms. Adding "cannot" to a
negative-lookahead would help (`(?!.*\b(?:cannot|unable|won't|wasn't)\b.*\b(?:done|complete)`)
but is fragile — the agent could phrase the negative differently.

## What this means for our workspace

1. **Any Stop hook that couples keyword detection to persistent state
   files must include an escape mechanism.** The ship-py orchestrator
   needs a first-class `abort` subcommand (`ship_orchestrator.py abort
   --session-id <UUID> --reason "..."`) that writes a terminal state.
   Without it, the agent has to hack the state file manually.

2. **Regex patterns for completion claims must exclude negative/explanatory
   forms.** The co-occurrence matcher `\bship[- ]py\b.*\b(?:done|complete)\b`
   should be narrowed to require positive assertion context — e.g., require
   "ship-py" immediately followed by the completion word, or use a negative
   lookahead for "cannot/unable/failed to."

3. **The pipeline must handle the "already shipped" condition.** When
   `/ship-py` is invoked after work is committed, `cmd_detect` should
   detect that the session's commits are already at origin/main and either
   skip to a lightweight post-hoc review or exit gracefully. This prevents
   the state file from being created in the first place.

4. **Auto-commit policy creates a structural incompatibility with
   pre-commit gating pipelines.** The `/ship-py` pipeline assumes
   pre-commit invocation: "take commits from code-complete to
   verified+merged." But this workspace's auto-commit policy means work
   is committed before the operator thinks to invoke `/ship-py`. The
   pipeline needs a "retroactive review" mode that reviews the session's
   commit range rather than working-tree diffs.

5. **This pattern generalizes to any state-file-coupled Stop hook.** The
   ship-py case is one instance. Any future hook that checks "does the
   agent's message contain X?" AND "does a state file show incomplete Y?"
   will create the same trap if X can appear in failure explanations.

## Falsifier

This concept is wrong if: the quality_gate.py ship-py check is removed
entirely (no state-file-coupled keyword enforcement exists), OR the regex
is fixed to exclude negative forms and the feedback loop never recurs for
any state-file-coupled hook. The concept is also wrong if it turns out
the hook DID have an escape mechanism that the agent missed — but as of
this session, no `abort` subcommand or `cannot_run` state existed in the
orchestrator.

## Receipts

- `~/.grok/hooks/scripts/quality_gate.py:160-164` — `_SHIP_PY_CLAIM_PATTERNS` regex definitions (verified by read this session)
- `~/.grok/hooks/scripts/quality_gate.py:170-220` — `_check_ship_py_state()` function: keyword check + state file check + blocking logic (verified by read this session)
- `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — orchestrator state machine (no `abort` subcommand; phases: detect, review, verify, verdict)
- `P:/.artifacts/ship-py/019fc927-d207-7c41-a512-5e90ff0c8b91/state.json` — manually written abort state to escape the loop
- `P:/docs/handoffs/ship-pipeline-open-work-20260809/HANDOFF.md` Track C — Stop hook regex fix (consolidated from ship-py-hardening findings 10-13)

## Cross-references

- [[llm-judgment-hooks]] — the conversation-collapse pattern (6-stage retry loop); this concept extends it with state-file coupling
- [[hook-regex-false-positives-pasted-terminal-output]] — regex matching user input; this concept is the Stop-hook analog where the regex matches the agent's own output
- [[grok-build-stop-hook-patterns-and-feedback-mechanism]] — broader Stop hook patterns on this host
- [[ship-pipeline-enforcement-pretooluse-phase-state-hooks]] — related ship-pipeline enforcement design
- [[scanner-regex-scope-discipline]] — the principle of scoping regex to the right data field; the ship-py regex scopes to the full message, not the semantic intent

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-catalog]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[claude-code-hook-system-patterns]]

