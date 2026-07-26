---
thread_id: aar-non-skippable-enforcement-20260726
parent_handoff_path: P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md
current_session_id: 019f94c9-43c1-7b31-87c4-980fdd3047e8
current_terminal_id: grok-build-primary
produced_at: 2026-07-26T21:35:00Z
status: open
handoff_type: design
accurate_as_of_head: pending
---

# Handoff — /aar non-skippable enforcement: design doc + Stop-hook BLOCK + scanner/validator reframe

## Objective

Make `/aar` structurally non-skippable from `/close`. This handoff supersedes the prior red-team handoff (`P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md`) with the full design cycle results: the design doc is valid as a requirements document, but the Stop-hook implementation mechanism has a fatal flaw. The correct mechanism is the scanner/validator layer.

**A design document EXISTS at:** `C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\grok-design-doc-47a92cea.md` (99 KB). **Read it as the requirements document. Do NOT implement the Stop-hook mechanism as designed — it is BLOCK'd.**

## What happened this session (the full arc)

1. **Operator asked how to make /aar NEVER skipped.** I proposed a 3-layer fix (exit code 2 + validator + compaction reader).
2. **Red-team (5 specialists, cross-model GLM)** found Layer A was REDUNDANT — the block already exists at the tool layer (`close_accounting.py:1708-1714`). The real gap is the harness doesn't gate the LLM's turn on the block signal. Red-team recommended a Stop hook.
3. **`/design` produced a 99 KB design doc** (writer → reviewer 60 findings → revise 53 fixed → consistency sweep 17 stale refs fixed). Reviewer caught 6 critical implementation bugs (all fixed). Design passed implementability review.
4. **Critical friend (GLM cross-model) BLOCK'd the design** with a fatal flaw: Stop hooks fire on EVERY turn-end, not just /close turns. The design's own acceptance criteria confirm: `echo '{"sessionId": "test-001"}' | python close_compliance_stop.py` exits 2 in enforce mode without a ledger — meaning the agent cannot end ANY turn until /close has run.
5. **BLOCK verified by me** against the design doc's own code and acceptance criteria. The granularity mismatch (per-turn Stop event vs per-session-close obligation) is not fixable within the Stop-hook layer.

## The design doc is valuable as a REQUIREMENTS document

The 99 KB design doc at `C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\grok-design-doc-47a92cea.md` contains:

- **6 root-cause closures** (RC-1 through RC-6) — all valid regardless of implementation mechanism
- **Forgery threat model** — pre-write attack (agent writes _run.json before scanner runs), cross-session receipt replay, hash forgery — all valid threats
- **Threshold justifications** — TOOL_CALL_THRESHOLD=5, HIGH_SUBSTANCE thresholds — valid for the disarm-proof gate trigger
- **Session-binding requirements** — `_run.json` must bind to session_id + terminal_id + recency — valid
- **AAR depth field requirement** — distinguish full AAR from --lite — valid
- **Coupling & Code-Smell Inventory** — DRY violations, parameter counts, touch-point analysis on the modules to be changed

**Use the design doc for WHAT needs to be fixed. Use the scanner/validator reframe below for HOW.**

## The fatal flaw (why the Stop hook doesn't work)

**Stop hooks fire on every turn-end** (`~/.grok/docs/user-guide/10-hooks.md:148-149`: "A matcher on Stop or UserPromptSubmit is ignored with a warning (those events always fire)"). The design's hook treats "no close-evidence ledger" as a BLOCK condition. But no ledger exists until /close runs. Therefore:

- Agent answers a question → turn ends → Stop fires → no ledger → **BLOCK** (session-breaking)
- Agent runs /close → scanner runs → ledger exists → retrospective unresolved → **BLOCK** (intended behavior)

The design's OQ-5 frames no-ledger as intentional ("catch cases where /close was never invoked") but doesn't address the consequence: the agent literally cannot end any turn without first running /close.

The 1-line fix (no-ledger → ALLOW) makes the hook workable but opens the exact bypass the design was trying to close (agent ends session without invoking /close at all — RC-6, unsolved).

## The scanner/validator reframe (what the next session should build)

**Granularity match:** the scanner/validator layer fires per-/close-invocation, not per-turn. This is the correct granularity by construction.

**What already exists (verified):**
- `close_accounting.py:1708-1714` already sets `retrospective.state = "needs_attention"` when substantive work happened without AAR receipt
- `close_accounting.py:2179-2189` already computes `loop.needed = len(attention_gates) > 0`
- `close_accounting.py` already emits the summary template

**What's missing (the ~15-line fix the critical friend recommended):**
1. **Scanner refuses to emit summary template** when `retrospective.state == "needs_attention"` and no valid AAR receipt exists. Currently the scanner emits the template anyway and the LLM fills in judgment fields. Change: return exit 2 + a one-line stderr `RETROSPECTIVE_BLOCK: run /aar before /close` instead of the template. The LLM has no template to fill — there's literally nothing to hand-write from.
2. **Validator adds AAR-hash check** to `validate_close_receipt.py`. Currently zero AAR-specific checks exist. Add: if the close-evidence ledger shows `retrospective.state == "needs_attention"`, require an AAR receipt hash that binds to session_id + matches the actual report file hash.
3. **Disarm-proof gate trigger** (from design doc RC-2): extend `_has_code_writes` to also fire on tool-call count ≥5 or handoff count ≥1, so research-heavy sessions with few file writes still trigger retrospective.

**What the scanner/validator approach does NOT solve (acknowledged gaps):**
- RC-6 (agent ends session without invoking /close) — requires SessionEnd hook, which has the same per-turn granularity problem unless it only fires on actual session termination (distinct from per-turn Stop). Verify SessionEnd hook semantics at `10-hooks.md` before designing.
- The agent can still hand-write a close summary in prose without invoking the scanner at all. The scanner/validator approach makes this harder (no template to work from) but not impossible. The ultimate fix for this is a Stop hook that detects close-summary-shaped output — but that's a detection problem, not a simple gate.

## Critical friend's constructive path (from the critique)

The critical friend (`C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\grok-design-critique-47a92cea.md`) recommended:

1. **Unbundle AAR Phase 8.5's mechanical safety checks** (the high-ROI value: uncommitted work audit, unhanded-off workstream detection, dangling intent scan, stale dirty files) from retrospective reflection (the thing the agent will always hollow out)
2. **Enforce the mechanical checks directly** at the scanner layer — these are deterministic and don't require a full AAR
3. **Keep retrospective reflection as a softer obligation** — the /aar --lite mode is acceptable for low-substance sessions; the mechanical checks are what matter

This separates "mechanical value" (high ROI, enforceable, deterministic) from "retrospective reflection" (the thing the agent will rationalize past). The scanner can enforce mechanical checks structurally; retrospective remains advisory.

## Read-first list (for the next session)

1. **This handoff** — the reframe
2. **The design doc** at `C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\grok-design-doc-47a92cea.md` — read as REQUIREMENTS (6 RC closures, threat model, thresholds). Skip the Stop-hook implementation sections.
3. **The critical friend critique** at `C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\grok-design-critique-47a92cea.md` — the constructive path
4. **The prior red-team handoff** at `P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md` — the red-team synthesis (6 root-cause clusters, revised fix-set)
5. `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:1685-1714, 2179-2189` — the existing block signal
6. `C:/Users/brsth/.grok/skills/close/__lib/validate_close_receipt.py` — current validator (needs AAR-hash check)
7. `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py` — `_run.json` schema (needs session binding + mode field)
8. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — the principle
9. `P:/.data/wiki/concepts/close-auto-invokes-aar.md` — prior fix history
10. `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md` — hook types (Stop fires per-turn; SessionEnd semantics need verification)

## Design artifacts (all in `C:\Users\brsth\AppData\Local\Temp\grok-design-47a92cea\`)

| File | Size | What it is |
|---|---|---|
| `grok-design-doc-47a92cea.md` | 99 KB | Design doc (valid as requirements; BLOCK'd as Stop-hook implementation) |
| `grok-design-review-47a92cea.md` | 77 KB | Reviewer findings (60 findings, all addressed) |
| `grok-design-summary-47a92cea.md` | 11 KB | Writer summary |
| `grok-design-critique-47a92cea.md` | — | Critical friend BLOCK (fatal flaw + constructive path) |

**NOTE:** These are in the OS temp directory and will be reaped. If the next session needs them, copy to `P:/docs/designs/2026-07-26-aar-non-skippable/` first. The design doc's requirements sections (RC closures, threat model, thresholds) are the durable value.

## Recommended next

```text
DESIGN BLOCKED — Stop-hook approach has fatal granularity flaw
reframe: scanner/validator layer (granularity matches: per-/close-invocation)
requirements document: the 99 KB design doc (6 RC closures + threat model)
critical friend constructive path: unbundle AAR Phase 8.5 mechanical checks from retrospective reflection
handoff: P:/docs/handoffs/aar-non-skippable-enforcement-20260726-design-blocked/HANDOFF.md
recommended next: fresh session implements the scanner/validator approach (~15-30 LOC)
  1. scanner refuses to emit template when retrospective=needs_attention (exit 2 + stderr)
  2. validator adds AAR-hash check with session binding
  3. disarm-proof gate trigger (tool-call-count threshold)
  4. optionally: unbundle AAR Phase 8.5 mechanical checks as direct scanner enforcement
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Scanner/validator approach still bypassable (agent hand-writes close summary without invoking scanner) | Medium | Harder than Stop hook (no template to work from) but not impossible. Detection of close-summary-shaped output in a Stop hook is the ultimate fix — but that's a detection problem, not a simple gate |
| RC-6 (session end without /close) unsolved | High | Acknowledged gap. Requires SessionEnd hook (distinct from Stop). Verify SessionEnd semantics first |
| Design doc temp files reaped before next session reads them | Medium | Copy to `P:/docs/designs/2026-07-26-aar-non-skippable/` at start of next session (path listed in read-first) |
| Agent rationalizes past scanner/validator approach too | Medium | Same class as all prior failures. The scanner/validator approach is structurally stronger than prose rules (no template = no close summary) but not immune to creative bypass |

## Cross-references

- `P:/docs/handoffs/aar-non-skippable-enforcement-20260726/HANDOFF.md` — prior red-team handoff (superseded by this one for implementation guidance, but the red-team synthesis is still valid)
- `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — the principle
- `P:/.data/wiki/concepts/close-auto-invokes-aar.md` — prior fix history
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` — the 4-rationalizations pattern
- `P:/.artifacts/grok-aar/console_console_9d8ef5b2-9187-4432-a2a8-47ce/20260726-193500/aar-report.md` — this session's AAR (LEARN-1 documents the skip incident)

## Non-goals

- 🚫 Do NOT implement the Stop-hook approach as designed — it has a fatal granularity flaw
- 🚫 Do NOT re-derive the 6 RC closures — they're in the design doc and valid
- 🚫 Do NOT re-run the red-team — the 5-specialist synthesis is in the prior handoff
- 🚫 Do NOT add another AGENTS.md prose rule about not skipping /aar — 5 rules exist; none fire
