---
thread_id: 019fa8f8-stop-hook-verification
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-07-31T19:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 2f95b53
---

# Handoff: Stop hook verification — auto-run ruff+py_compile on modified files before claiming completion

## 1. Objective

Find a way to make the Stop hook's verification receipt check pass automatically — so ruff + py_compile run on modified files without the agent having to manually remember and the operator seeing constant Stop blocks.

## 2. Status

OPEN — not started.

## 3. Producing context

The Stop hook checks that modified files have a covering verification receipt. When the agent modifies files (even small fixes like removing an unused import) and claims completion without re-running verification, the hook blocks with "NO_COVERING_RECEIPT." This happened repeatedly this session — 10+ times. Each block costs a round-trip.

The problem: the agent runs `ruff check` and `py_compile` during implementation, but then makes small follow-up edits (lint fixes, format changes) that invalidate the previous receipt. The hook correctly catches the stale receipt, but the agent doesn't re-verify after every tiny edit.

## 4. Read-first list

1. `~/.grok/hooks/scripts/verification_receipts.py` — the hook that checks receipts
2. `~/.grok/hooks/scripts/quality_gate.py` — the quality gate that wraps verification
3. `~/.grok/AGENTS.md` § "Verification receipt scope-binding" — the Stop hook contract
4. `~/.grok/skills/model-quota/scripts/fleet_quota.py` — a file that was modified multiple times this session, triggering repeated blocks

## 5. Verified facts

- [FACT] Stop hook blocks when modified files don't have covering receipts (observed 10+ times this session)
- [FACT] The receipt check is file-fingerprint based — it hashes file content and compares against the last verification
- [FACT] ruff + py_compile are the approved verifiers for .py files
- [FACT] The agent must run verifiers with explicit file paths (not just `ruff check .`)
- [FACT] The hook fires on Stop — the last action before the agent would present results to the operator

## 6. Current state

Three approaches to investigate:

1. **PreStop hook that auto-runs ruff + py_compile on modified files.** When the agent says "done," a PreStop hook scans for modified .py files since last verification and runs ruff + py_compile automatically. If they pass, the receipt is updated. If they fail, the block fires with the actual error (not just "stale receipt"). This would eliminate the vast majority of blocks.

2. **PostToolUse hook on search_replace/write that auto-runs verification.** After every file edit, run ruff + py_compile on that file immediately. The receipt is always current. Cost: slight latency on every edit (~200ms per file for ruff). Benefit: never see a Stop block again for code files.

3. **AGENTS.md rule with behavioral enforcement.** Tell the agent to always run `ruff check <file> && python -m py_compile <file>` after the final edit to each file. This is the current approach — it doesn't work because the agent forgets under closure pressure.

## 7. Task packets

### FIX-VERIFY-01: Investigate PreStop auto-verification
- **goal:** determine if a PreStop hook can auto-run ruff + py_compile on modified files and update the receipt before the Stop check fires
- **in scope:** PreStop hook event, verification_receipts.py receipt mechanism
- **out of scope:** changing the Stop hook's blocking behavior
- **files / anchors:** `~/.grok/hooks/scripts/verification_receipts.py`, `~/.grok/docs/user-guide/10-hooks.md`
- **acceptance:** a concrete recommendation: (a) PreStop auto-verify is viable, or (b) PostToolUse auto-verify is better, or (c) neither works and the agent must manually verify
- **falsifier:** if the hook chain order doesn't allow PreStop to run before Stop verification
- **verification level required:** STATIC_INSPECTION
- **estimate:** 30 min

### FIX-VERIFY-02: Implement auto-verification hook
- **goal:** implement the chosen approach so modified .py files are auto-verified
- **in scope:** new hook script + JSON registration
- **out of scope:** changing which verifiers are used
- **files / anchors:** `~/.grok/hooks/` (new file)
- **acceptance:** after editing a .py file and claiming completion, the Stop hook does NOT block with NO_COVERING_RECEIPT — the receipt is already fresh
- **falsifier:** if the Stop hook still blocks despite the auto-verify running
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 45 min
- **depends on:** FIX-VERIFY-01

## 8. Open decisions

- PreStop vs PostToolUse: which hook event fires at the right time?
- Should auto-verify also handle .md files (which don't need py_compile)?
- Performance impact: is ~200ms per edit acceptable?

## 9. Hard constraints

- Do NOT change the Stop hook's blocking behavior — it's correct
- Do NOT disable the verification receipt system — it catches real bugs
- The fix should reduce blocks, not eliminate verification

## 10. Cross-reference couplings

- `~/.grok/AGENTS.md` § "Verification receipt scope-binding" — the contract this work serves
- `~/.grok/hooks/scripts/verification_receipts.py` — the receipt mechanism

## 11. Other outstanding streams

- Red-team /design skill → `P:/docs/handoffs/design-skill-red-team-20260730/HANDOFF.md`
- /www Phase 2b enforcement → `P:/docs/handoffs/www-phase2b-enforcement-20260731/HANDOFF.md`

## 12. Explicit non-goals

- Do NOT change which verifiers are approved (ruff + py_compile for .py)
- Do NOT change the receipt format or storage mechanism

## 13. Resumption protocol

1. Read verification_receipts.py to understand receipt mechanism
2. Check if PreStop fires before Stop verification in Grok Build hook chain
3. Implement auto-verify hook (PreStop or PostToolUse)
4. Test: edit a .py file, claim completion, verify no Stop block

## 14. Suggested next invocation

```
/go implement auto-verification hook for Stop hook receipt — run ruff + py_compile on modified .py files before Stop check fires. See P:/docs/handoffs/stop-hook-auto-verification-20260731/HANDOFF.md
```

## 15. Last user message (verbatim)

> "let's try to find a way to do these verification steps by default so we don't have to see the stop block all the time"

## 16. Epistemic labels

- Stop hook blocking repeatedly: [FACT] — observed 10+ times this session
- PreStop/PostToolUse as solution: [INFERENCE] — need to verify hook chain order
- Performance impact of auto-verify: [UNKNOWN] — not measured
