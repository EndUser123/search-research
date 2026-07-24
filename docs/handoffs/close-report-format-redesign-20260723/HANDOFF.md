---
thread_id: e2b7c9a1-4f3d-8a2e-b6c1-5d4e7f901a23
parent_handoff_path: P:\docs\handoffs\session-observations-20260718-019f76e8\HANDOFF.md
current_session_id: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
current_terminal_id: console_019f76e8
produced_at: 2026-07-23T22:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: (uncommitted — ~/.grok changes are not tracked)
---

## Objective

Redesign /close output format by fixing the root cause: the ambiguous word
"template" in the original architecture spec caused both the scanner code
and the SKILL.md to claim format ownership, with no contract defining the
boundary between data and format.

## Status

OPEN — root cause identified and verified by /tp fresh-lens critique (glm-5-2).
Plan written at `C:\Users\brsth\.grok\sessions\P%3A%5C\019f76e8-eae4-7cc1-9c70-2fe3729812f1\plan.md`.
Not implemented.

## Root cause chain (verified)

```
L1 SYMPTOM:        /close output is unreadable
L2 IMMEDIATE:      LLM receives two competing templates (generate_summary() Template A
                   vs SKILL.md Step 4 Template B) and reconciles in real time
L3 PROXIMATE:      Templates diverge because they're edited independently across sessions
                   with no synchronization
L4 SYSTEMIC:       No contract or enforcement mechanism binds scanner output to SKILL.md
                   format definition — no test, no workflow treats them as coupled
L5 ARCHITECTURAL:  Scanner code and SKILL.md are treated as independent concerns (code vs
                   prose) with no integration layer between the boundaries
L6 ROOT CAUSE:     The original design ("scanner thinks; LLM judges") told the scanner to
                   emit a "summary template" — but "template" conflated DATA (counts, gate
                   states, evidence) with FORMAT (section headers, field order, structure).
                   Both layers interpreted "template" as including format ownership. The
                   boundary between data and format was never drawn.
L7 WHY PLANS FAILED: Every prior plan (close-scanner-architecture-20260722,
                   close-v6-deferred-design-findings-20260722, today's plan) inherited the
                   same blind spot: they accepted the scanner's role as "template emitter"
                   and tried to fix format WITHIN that role, rather than questioning whether
                   the scanner should emit format at all.
```

**Root cause (L6):** The ambiguous word "template" caused dual format ownership with no contract defining the boundary.

## Producing context

- Session: 019f76e8 (2026-07-18 to 2026-07-23, multi-restart)
- The operator said "I'm pretty far from good" about the current /close output
- /tp fresh-lens critique (glm-5-2) caught the dual-ownership root cause that
  same-agent analysis missed across multiple sessions. The subagent read both
  `generate_summary()` and SKILL.md Step 4, saw the divergence, and identified
  that the plan's scope (code-only) was wrong for a coupling problem.
- Subagent ID: 019f90e3-a3de-7d80-8fed-11c0d222f897

## Read-first list

1. `C:\Users\brsth\.grok\sessions\P%3A%5C\019f76e8-eae4-7cc1-9c70-2fe3729812f1\plan.md`
   — the revised plan with the root cause fix
2. `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py` — the scanner.
   Key functions:
   - `generate_summary()` (L1266-1322) — DELETE THIS. Source of Template A drift.
   - `_format_compact()` (L1490-1600) — REWRITE as worklist-only output
   - `resolve_gates()` — DO NOT CHANGE
   - `scan_all()` — DO NOT CHANGE
3. `C:\Users\brsth\.grok\skills\close\SKILL.md` — Step 4 (L240-290) defines
   Template B. REWRITE to own the full output format.
4. Prior handoffs on /close format failures:
   - `close-scanner-architecture-and-root-causes-20260722`
   - `close-v6-deferred-design-findings-20260722`
   - `tp-model-pool-not-inline-fallback-20260722` (L159: close gate fixes)

## What to implement

### Part 1: Delete format ownership from the scanner

**Delete `generate_summary()`** (L1266-1322). This function emits `<LLM: ...>`
template lines — it's the source of Template A. The scanner should not be in
the business of defining output format.

**Rewrite `_format_compact()`** to produce only Phase 1 (worklist):

```
CLOSE SCAN: 2026-07-23 | session 019f76e8 | 13 gates checked

  ✓ 8 gates satisfied

  ACTION NEEDED (3):
  1. retrospective   No AAR artifact for this session
                     → run /aar, or defer to next session
  2. verify          Code modified but scanner detected no test run
                     → confirm tests in conversation, or run them now
  3. temp_files      312 files (13 MB) in P:/tmp/ — at risk of OS reaping
                     → classify as disposable or preserve durable ones

  ADVISORY (2):
  • background_tasks  Check for orphaned spawn_subagent tasks
  • decisions         Identify decisions to promote to wiki/ADR

  EVIDENCE:
  Handoffs: 5 (4 open)  |  Commits: 167  |  Wiki: 10 concepts
  Uncommitted: 26 files from other sessions
```

Translation rules:
- `needs_attention` → "ACTION NEEDED" (numbered, with resolution hint)
- `needs_llm_check` → "ADVISORY" (bullet list)
- `pre_satisfied`/`skip` → counted as satisfied (not listed individually)
- Gate state names NEVER appear in output — translate to human language
- No `<LLM: ...>` placeholders — the worklist structure IS the instruction

**Remove `summary_lines` parameter** from `format_output()` and `_format_compact()`.
The scanner no longer emits summary template lines.

**Add enforcement test:** assert scanner output contains no `<LLM:` text and no
section headers from the SKILL.md format (SHIPPED, PARTIAL, etc.). This prevents
future regression of the boundary.

### Part 2: Give SKILL.md sole ownership of the output format

**Rewrite Step 4** to define the full Phase 2 format (the operator-facing summary):

```
SESSION CLOSED: <date> <session-id-short>

SHIPPED:
  • <what was completed this session>

PARTIAL:
  • <what was partially done, with what remains>

NOT STARTED:
  • <what was planned but not attempted>

ACTIONS TAKEN: <Tier-1 actions performed during close, or "none">
PERSISTENCE: <all work committed/durable | N items at risk>
VERIFY: <PASS | GAP: specifics | deferred>
DECISIONS PROMOTED: <list | none: reason>
RETROSPECTIVE: <aar run | deferred: reason>

NEXT SESSION:
  1. <highest priority next action>
  2. <second priority>
```

Every section is mandatory. Empty sections say "none." This preserves the four
audit fields the glm-5-2 critique identified as critical:
- ACTIONS TAKEN — operator visibility into autonomous Tier-1 behavior
- DECISIONS PROMOTED — operator visibility into auto-promoted wiki concepts
- VERIFY — structural enforcement of the receipt check (2026-07-22 incident fix)
- RETROSPECTIVE — whether /aar was run or deferred

**Update Step 4.1 (receipt check)** to reference the new section names.

**Collapse gate-specific guidance** (currently ~130 lines) to the tier system
+ edge cases. The Phase 1 worklist resolution hints make much of this redundant.

### Part 3: Tests

Update `test_new_features.py` format assertion tests to match the new worklist.
Add boundary enforcement test (no format leakage from scanner).

### What NOT to change

- `resolve_gates()` — gate logic is correct
- `compute_loop()` — loop decision logic is correct
- `scan_all()` — scanning is correct
- Evidence dataclass — structural, not presentation
- `--format json` — still emits full structured output (programmatic consumers)
- `--format summary` (detailed) — keep for debugging

## Why this plan won't fail like the prior ones

| Prior plan failure mode | This plan's defense |
|---|---|
| Scoped to code only → SKILL.md drifts | Both files edited together in one atomic change |
| Accepted scanner as "template emitter" | Deletes `generate_summary()` — removes the claim |
| No boundary between data and format | Boundary explicitly drawn: scanner = data, SKILL.md = format |
| No enforcement | Test asserts no format leakage from scanner |
| Dropped audit fields | All 4 audit fields are mandatory sections, not optional |

## Falsifier

If the next /close run still produces messy output after this change, the root
cause diagnosis was wrong — the problem isn't template drift / format ownership
ambiguity but something else entirely (e.g., the LLM ignoring SKILL.md instructions
regardless of format ownership, or the Evidence refactor breaking the pipeline).

## Other outstanding streams

- **AAR SKILL.md lean-core reduction** (838→600) — handoff at
  `aar-skill-lean-core-reduction-20260723`
- **Red-team RC items** (RC-1/RC-2/RC-5) — synthesis at
  `P:/.artifacts/red-team/019f907b.../synthesis.md`
- **STOP-03** (PreToolUse gate) — handoff at `stop-hook-challenge-gate-20260723`
- **CVG-02** (SYCOPHANCY.md, 10 min)
- **/aar against this session's transcript** — deferred to fresh session
