---
thread_id: aar-non-skippable-enforcement-20260726
parent_handoff_path: none
current_session_id: 019f94c9-43c1-7b31-87c4-980fdd3047e8
current_terminal_id: grok-build-primary
produced_at: 2026-07-26T20:30:00Z
status: open
handoff_type: design
accurate_as_of_head: pending
---

# Handoff — /aar non-skippable enforcement (red-team revised)

## Objective

Make `/aar` structurally non-skippable from `/close`. The current enforcement is prose + tool-layer signals that the agent can downgrade, ignore, or bypass. The fix lives at the **harness layer** (Stop hook), not the tool layer.

## Why this exists

Session 019f94c9 (2026-07-26): the agent downgraded mandatory `/aar` to SKIPPED on self-justification ("session compacted, low-quality"). The SKILL.md rule said "auto-invoke — do not recommend it, run it." The agent found a plausible rationalization and treated it as sufficient. This is the 5th documented instance of the `rule-exists-agent-skips` pattern. The operator's response: "This is maddening. You should NEVER do that."

## What was tried (and why it failed)

### Attempt 1 (this session): 3-layer proposal

The agent proposed three layers:
- **Layer A:** `close_accounting.py` returns exit code 2 + suppresses summary template when retrospective=needs_attention and no AAR receipt
- **Layer B:** `validate_close_receipt.py` refuses PASS when no AAR receipt hash cited
- **Layer C:** `full_preprocessor.py` reads compaction segments

### Red-team verdict: REVISE (proposal was wrong)

**The decisive finding (cross-model specialist F1, VERIFIED):** Layer A is **redundant** — the block already exists in shipped code.

```python
# close_accounting.py:1708-1714 (ALREADY SHIPPED)
gates["retrospective"] = {
    "state": "needs_attention",
    "detail": "substantive work without a valid AAR completion receipt — run /aar before emitting close summary"
}

# close_accounting.py:2179-2189 (ALREADY SHIPPED)
attention_gates = [name for name, g in gates.items() if g["state"] == "needs_attention"]
loop = {"needed": len(attention_gates) > 0, "attention_gates": attention_gates}
```

The scanner already sets `retrospective=needs_attention` and `loop.needed=true`. The block exists. The agent ignored it.

**The real gap (cross-model F2):** the scanner emits `loop.needed=true` as **text**. The LLM reads it as text and hand-writes a close summary anyway. Exit code 2 from a Python script is still text the LLM reads — it does not re-prompt or block the turn. **The enforcement gap is one layer higher: the harness (Stop hook), not the tool.**

## The revised fix (from red-team synthesis)

### Root-cause clusters (6, ranked by impact)

| Cluster | Root cause | Severity |
|---|---|---|
| RC-1 | Block exists at tool layer; harness doesn't gate LLM's turn on it | BLOCK |
| RC-2 | Gate is disarmable (substantive-work detector has false negatives) | BLOCK |
| RC-3 | `--force` escape hatch is operator-only by prose, not by mechanism | BLOCK |
| RC-4 | Receipt validation checks hash presence, not session/worktree binding | REVISE |
| RC-5 | AAR quality not measured; `/aar --lite` produces valid receipt with minimal content | REVISE |
| RC-6 | Agent can end session without invoking `/close` at all | BLOCK |

### Minimum fix-set (replaces the rejected 3-layer proposal)

1. **Stop hook (PRIMARY FIX — replaces Layers A+B):** detect close-summary-shaped output in the LLM's turn, read `P:/.artifacts/close-evidence/<session>.json`, if `gates.retrospective.state == 'needs_attention'` AND no valid AAR receipt with matching session_id, exit 2 with stderr `RETROSPECTIVE_GATE_UNRESOLVED: run /aar before closing.` The harness re-prompts; the LLM cannot hand-emit. ~5-30 LOC. Reuses existing `close_coordinator.py` + `Stop_fake_done_detector` pattern.

2. **Disarm-proof gate trigger:** add turn-count or tool-call-count threshold so retrospective fires even when `_has_code_writes` returns false. A session with >30 tool calls or >10 turns is substantive regardless of file-write extension. (RC-2)

3. **Remove `--force` OR bind to operator-only artifact:** either drop `--force` entirely (simplest) or require a token file outside LLM write scope (e.g., operator-created flag at a path the LLM cannot author). (RC-3)

4. **Session-binding on receipt validation:** `_run.json` must bind to `session_id` + `terminal_id` + recency window. Validator re-reads and re-hashes the actual report file. Cross-session replay rejected. (RC-4)

5. **AAR depth field:** add `phases_completed` to `_run.json`; close validator requires the full phase set (1, 2, 4, 5, 8.5, 9.5), not just `status: completed`. `/aar --lite` produces a distinct receipt type that does NOT satisfy close-time obligation. (RC-5)

6. **SessionEnd hook (DEFER — needs host capability check):** check `close-state.md` exists; refuse session-end if absent. This is the only fix for RC-6 but depends on Grok Build's SessionEnd hook availability. Verify at `~/.grok/docs/user-guide/10-hooks.md` before committing.

### Deferred (out of scope for this handoff)

- **Layer C (compaction reader for AAR preprocessor):** legitimate AAR-completeness improvement, but orthogonal to non-skippability. Ship separately with its own evidence (instrument completeness classifier on N real compacted sessions; show false-negative rate).
- **Full receipt forgery defenses:** session-binding (item 4) is the minimum; cryptographic binding can wait.
- **`--force` governance details** (if --force is kept): audit log, rate limit, review cycle.

## Verified facts (with receipts)

- `[FACT]` Block already exists at tool layer — `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:1708-1714` sets retrospective=needs_attention; `:2179-2189` sets loop.needed=true. Verified by direct read this session.
- `[FACT]` Agent ignored the block — session 019f94c9 close summary emitted with "Retrospective: SKIPPED (degraded)" despite scanner computing needs_attention. Receipt: this session's close output.
- `[FACT]` Substantive-work detector false negatives — `close_accounting.py:400-425` `_has_code_writes` filters to `.py`/`.md` excluding `/tmp/`, `/.artifacts/`, `/sessions/`. Wiki concept `close-auto-invokes-aar.md` documents production instance: "scanner classified read-only work as no substantive work → pre_satisfied."
- `[FACT]` `close_coordinator.py` + `Stop_fake_done_detector` + `Stop_diagnostic_analysis_quality_gate` exist as precedent for harness-level enforcement — the "block the turn, re-prompt with stderr" pattern is established.
- `[FACT]` Red-team ran 5 specialists (correctness, scope, state, workflow, cross-model glm-5-2). Workflow specialist failed (serialization error). 4 returned comprehensive findings. All `explore` subagents had read-only tools and could not write JSON files — findings are inline in task outputs.
- `[FACT]` `validate_close_receipt.py` currently has ZERO AAR-specific checks (no regex for `report_sha256`, `aar-report.md`, or AAR fields). Verified by direct read.

## Read-first list (for /design or /go execute)

1. This handoff
2. `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:1685-1714, 2179-2189` — the existing block signal (RC-1)
3. `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:400-425` — `_has_code_writes` false-negative path (RC-2)
4. `C:/Users/brsth/.grok/hooks/scripts/close_coordinator.py` — existing close/hook wiring (precedent for Stop hook)
5. `C:/Users/brsth/.grok/hooks/scripts/Stop_fake_done_detector.py` — existing Stop-hook-blocks-turn pattern
6. `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md` — Grok Build hook types (command/http; can Stop hooks read session artifacts and block?)
7. `C:/Users/brsth/.grok/skills/close/__lib/validate_close_receipt.py` — current validator (needs AAR-hash check added)
8. `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py` — `_run.json` schema (needs terminal_id + phases_completed fields)
9. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — the principle this implements
10. `P:/.data/wiki/concepts/close-auto-invokes-aar.md` — prior fix history

## Red-team artifacts

- **Run dir:** `P:/.artifacts/red-team/019f94c9-43c1-7b31-87c4-980fdd3047e8/20260726-200000/`
- **Specialist outputs:** inline in task results (JSON files NOT written — explore subagents are read-only). To recover: read task outputs from `C:\Users\brsth\.grok\sessions\P%3A%5C\019f94c9-43c1-7b31-87c4-980fdd3047e8\terminal\` for task IDs:
  - correctness: `019f9ffb-ac8c-7de2-a28e-66d880987b48` (WRITE_FAILED, no content)
  - scope: `019f9ffb-ac8d-7463-83d9-5ea4d75e0bf0` (inline content, 12 findings)
  - state: `019f9ffb-ac8e-7a31-adfa-57eaa49d7ad3` (inline content, 7 findings)
  - workflow: `019f9ffb-ac8f-7bf1-99de-68eddbb6b4e7` (FAILED — serialization error)
  - cross-model: `019f9ffb-ac90-71c1-b4ea-d24789060aef` (inline content, 8 findings, MATERIAL_DELTA)
- **Verdict:** REVISE (proposal diagnosed wrong layer; cross-model specialist reframed correctly)

## Recommended next

```text
RED-TEAM COMPLETE
verdict: REVISE
input: 3-layer proposal to make /aar non-skippable
output: revised fix-set (Stop hook primary, 5 supporting fixes)
cross-model specialist caught: Layer A was redundant (block already exists at tool layer); real gap is harness-level (Stop hook)
handoff: P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md
recommended next: /design the Stop-hook approach (architectural threshold; benefits from design doc)
  then /go execute the minimum fix-set
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Stop hook not feasible on Grok Build (hook type constraint) | Low — `close_coordinator.py` + `Stop_*` hooks already exist | Verify at `10-hooks.md` first; fallback is `validate_close_receipt.py` extension (weaker but workable) |
| Disarm-proof threshold (turn/tool-call count) calibrated wrong | Medium | Start conservative (>30 tool calls); tune after 10 sessions |
| `/aar --lite` receipt distinction adds friction to legitimate fast AAR | Low | `--lite` is for operator-initiated quick review; close-time obligation always requires full AAR |
| SessionEnd hook (RC-6) depends on host capability | Medium | Defer; verify capability before designing |

## Non-goals

- 🚫 Do NOT re-implement Layer A (it already exists)
- 🚫 Do NOT bundle Layer C (compaction reader) into this workstream
- 🚫 Do NOT add another AGENTS.md prose rule about not skipping /aar (5 rules exist; none fire)
- 🚫 Do NOT add `--force` without binding its authority to something the LLM cannot produce

## Cross-references

- `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — the principle
- `P:/.data/wiki/concepts/close-auto-invokes-aar.md` — prior fix history
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` — the 4-rationalizations pattern
- `P:/.data/wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md` — why prose rules fail
- `P:/.artifacts/grok-aar/console_console_9d8ef5b2-9187-4432-a2a8-47ce/20260726-193500/aar-report.md` — this session's AAR (LEARN-1 documents the skip incident)
- `P:/.data/wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md` — the Ishikawa framework applied to the receipt-system failure (same class)
