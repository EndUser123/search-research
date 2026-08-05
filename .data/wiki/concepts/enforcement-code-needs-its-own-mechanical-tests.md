---
title: "Enforcement code needs its own mechanical tests — the meta-enforcement gap"
created: 2026-08-05
source: session-20260804
tags: [enforcement, testing, scanners, quality-gates, meta-pattern, mechanical-enforcement]
summary: >
  Mechanical enforcement code (scanners, gates, validators, receipt-checkers) is
  itself code that can regress silently. When enforcement code has zero test
  coverage, a future edit that breaks detection logic goes unnoticed — the gate
  continues to "pass" or "block" but for the wrong reasons. The pattern: every
  session that adds new enforcement code should also add at least one test per
  enforcement function. The meta-rule: enforcement code is a special case of
  executable artifact that needs execution receipts (test runs) before it's
  trusted, not just inspection receipts (code reads).
agent: grok
host: both
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/mechanical-enforcement-of-llm-skill-steps-2026.md
    type: extends
  - target: wiki/concepts/declarative-quality-gates-skills-declare-evidence.md
    type: extends
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
---

# Enforcement code needs its own mechanical tests

## Decision context

**The problem:** session 019fca0e added two significant enforcement code blocks:
`check_skill_receipts()` in ship_receipt.py (session-scoped receipt file
verification) and Checks 7-8 in script_scan.py (LLM-fillable detection + craft
quality). Both are mechanical enforcement — code that gates SHIP DONE or emits
findings. A specialist review at ship time found that **neither has any test
coverage**. The session's entire theme was moving from prose enforcement
(~12% activation) to mechanical enforcement (~100% activation). But the
mechanical enforcement code itself is unverified — a regression in
`check_skill_receipts()` that silently returns MISSING for all inputs would
make the gate useless, and no test would catch it.

**The meta-pattern:** enforcement code is a trusted computing base. When it
fails silently, every downstream consumer inherits the failure without knowing.
The "who watches the watchers" problem applies directly: the scanner scans
skills, but nothing scans the scanner.

## Key findings

### Enforcement code has different failure modes than application code

Application code fails visibly — the feature doesn't work, tests catch it.
Enforcement code fails invisibly — the gate still produces a verdict, but the
verdict is based on broken logic. The failure is silent because:

1. **Fail-open defaults:** `verify_specialist_spawn()` returns `(True, ...)` when
   the transcript can't be found (ship_receipt.py:1130). The gate "passes" but
   the verification never happened. This is the most dangerous failure mode —
   the gate reports success while being non-functional.

2. **Heuristic degradation:** `script_scan.py` Check 4 uses `"R" in body_str` to
   detect rename handling, but `body_str` is an AST dump containing English text
   — virtually every file has an uppercase R somewhere. The heuristic is
   effectively dead code, but it produces no error.

3. **Encoding mismatches:** `verify_specialist_spawn()` tries two session path
   encodings but doesn't know which one Grok Build uses. If neither matches,
   the lookup fails silently and (combined with fail-open) the gate is bypassed.

### The minimum viable test set for enforcement code

Each enforcement function needs at least these test cases:

| Test case | What it catches |
|-----------|----------------|
| Positive match (should detect/pass) | Gate never fires |
| Negative match (should not detect/block) | Gate always fires |
| Edge case (empty input, missing files) | Crash on valid input |
| Fail-open check (enforcement bypass when input unavailable) | Silent security bypass |
| Session scoping (cross-session contamination) | Cross-session contamination |

### Connection to existing enforcement concepts

This extends [[mechanical-enforcement-of-llm-skill-steps-2026]] — that concept
establishes that mechanical enforcement is better than prose rules. This
concept adds: mechanical enforcement code is itself subject to the same
quality bar. An untested scanner is prose enforcement with extra steps — it
*looks* mechanical but degrades silently.

It also extends [[declarative-quality-gates-skills-declare-evidence]] — that
concept establishes that skills should declare evidence artifacts. This concept
adds: the code that checks for evidence artifacts should itself have evidence
(tests) demonstrating it works.

## What this means for our workspace

1. **Immediate gap:** `check_skill_receipts()` and `script_scan.py` Checks 7-8
   have zero tests. These were added in session 019fca0e. A regression in either
   would not be caught by `pytest tests/`.

2. **Standing rule:** when adding new enforcement code (scanner check, receipt
   checker, gate function), add at least one test in the same commit. The test
   is part of the enforcement, not a nice-to-have.

3. **Fail-closed principle:** enforcement gates must fail closed (BLOCK) when
   their inputs are unavailable, not fail open (PASS). `verify_specialist_spawn()`
   currently fails open — this is a bug, not a design choice. The fix is to
   return `(False, "transcript not found")` and provide a separate
   `--no-transcript-verify` escape hatch for explicit operator override.

4. **Scanner self-test:** running `/skill-dev` on `/skill-dev` (the scanner
   self-improvement loop from this session) is valuable but insufficient — it
   catches structural issues (Check 8 not scanner-enforced) but not logic bugs
   (Check 4 heuristic degradation). Unit tests catch logic bugs.

## Falsifier

This concept is wrong if:
- Enforcement code is simple enough that inspection is sufficient (trivial
  functions with no branching don't need tests)
- The fail-open behavior in `verify_specialist_spawn()` is intentional (operator
  preference for "ship even when transcript is missing" rather than a bug)
- Test coverage for enforcement code is already addressed by the existing
  test suite (check: `pytest tests/ -k receipt` should find tests for
  `check_skill_receipts` — if it does, this concept's premise is wrong)

## Receipts

- `~/.grok/skills/ship/__lib/ship_receipt.py:1130,1135` — `verify_specialist_spawn()` fail-open: returns `(True, ...)` when transcript not found (inspected by specialist subagent 019fd0ba, 2026-08-05)
- `~/.grok/skills/ship/__lib/ship_receipt.py:715-820` — `check_skill_receipts()`: zero test coverage; function does session-scoped JSON matching + stub detection (inspected by specialist subagent)
- `~/.grok/skills/skill-dev/__lib/script_scan.py:280` — Check 4 `"R" in body_str` heuristic: trivially True due to AST node names containing uppercase R (inspected by specialist subagent)
- `~/.grok/skills/ship/tests/test_ship_receipt.py` — test file exists with 41 tests but `check_skill_receipts` not in import list (inspected by specialist subagent)
- `~/.grok/skills/skill-dev/__lib/script_scan.py` (whole file) — no `tests/` directory exists for skill-dev scanner (verified via `list_dir`)

## Sources

- Session 019fca0e specialist review (explore subagent 019fd0ba, 2026-08-05) — 7 bugs, 9 risks found in ship_receipt.py and script_scan.py
- [[mechanical-enforcement-of-llm-skill-steps-2026]] — prior concept establishing mechanical > prose enforcement
- [[declarative-quality-gates-skills-declare-evidence]] — prior concept establishing artifact-based evidence

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[codebase-knowledge-graph-mapping]]
- [[claude-code-hooks]]

