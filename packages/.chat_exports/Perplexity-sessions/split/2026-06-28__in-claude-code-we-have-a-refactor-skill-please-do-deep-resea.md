---
title: "In claude code, we have a refactor skill. please do deep research so that we can make our /refactor plugin/skill the bes"
date: "2026-06-28"
mode: "COPILOT"
uuid: "91a06d0f-a4d6-4e2e-9f55-585f098f7514"
entry_count: 1
---

## Human

In claude code, we have a refactor skill. please do deep research so that we can make our /refactor plugin/skill the best it can be, with the best and happiest outcomes. I don't mind radical refactoring of the plugin/skill if there's a positive ROI. after the /refactor command is used and 100% finished, I do want output that can be professionally published on github and used as exemplar resume material. I've attached a long chat, with a short segment about /refactor and it shows how ignorant the target LLM is. I've also attached the /refactor files and other LLMs research.  Can you make it better?

## Assistant

---
name: refactor
description: Multi-file refactoring orchestrator for Claude Code. Discovers structural debt (cyclomatic complexity P0≥30, P1≥15, P2≥8), cross-file DRY violations, circular imports, and god-modules via parallel agent discovery. Produces constitutional-filtered, dependency-ordered plans. Executes approved batches in isolated git worktrees with LibCST-based AST transforms. Mandates characterization tests (RED→GREEN) before any edit. Emits GitHub-ready commits, PR description, CHANGELOG entry, health-score metrics, and resume bullets upon completion. Use --dry-run to stop after plan, --continue to resume from prior artifacts, --worktree to force isolated execution.
***

# refactor — Multi-File Refactoring Orchestrator

> **Contract first, then execution.** Read this skill fully before invoking any tool.

## What This Skill Does

`refactor` turns large-scale, multi-file structural debt into safe, observable, publishable changes. It is not a diff reviewer and not a single-file formatter. Its value lives entirely in cross-file analysis — DRY violations split across four files, circular imports invisible at file scope, god-modules accumulating unrelated concerns — and in providing the safety scaffold (worktrees, characterization tests, rollback tags) that makes executing those findings trustworthy.

**End state after a completed run:**
- A merged feature branch with atomic, reviewable commits
- A PR description, CHANGELOG entry, health-score delta, and resume bullets
- All tests green, lint clean, type-check passing
- A session artifact bundle suitable for public GitHub publication

## Phases

```
PREFLIGHT → DISCOVER → DEDUPLICATE → CLASSIFY → PRIORITIZE → FILTER → PLAN
  → [approval checkpoint] → WORKTREE → RED → REFACTOR → GREEN → REGRESSION
  → DELETION-METRIC → PUBLISH
```

`--dry-run` halts after PLAN and writes `findings.json` + `plan.json` to the artifacts dir.  
`--continue` resumes from existing artifacts, skipping DISCOVER through PLAN.  
`--worktree` forces isolated git worktree execution even for single-file findings.

## Invocation

```bash
refactor <path>                    # Full run on directory or file
refactor <path> --dry-run          # Discovery + plan only, no edits
refactor <path> --focus security   # Tune agent focus lens
refactor <path> --focus duplication
refactor <path> --focus complexity
refactor <path> --cc-threshold 20  # Override cyclomatic complexity threshold
refactor <path> --incremental      # Resume across sessions, terminal-isolated state
refactor continue                  # Resume from prior session artifacts
```

## Priority Thresholds

| Priority | CC Threshold | Action |
|----------|-------------|--------|
| P0 | ≥ 30 | Block — must fix before any new feature work |
| P1 | ≥ 15 | Scheduled — address in current sprint |
| P2 | ≥ 8  | Queued — next available session |
| P3 | < 8  | Logged — fix opportunistically |

Health Score: `100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)`, clamped to              ← Adversarial plan review (score < 7/10 → revise)
  synthesizefindings.py       ← Health Score: 100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)
  worstfinding.py             ← Worst-finding triage helper
  runscan.py                  ← CLI entry point for complexity pre-scan
  scant.py                    ← Scan + triage shortcut

hooks/
  PreToolUse.refactor-gate.py       ← Phase-gating: blocks tools not in current phase
  PostToolUse.refactor-transition.py← Phase advance on machine-readable evidence artifacts
  PostToolUse.refactor-validator.py ← Validates artifact existence after phase tools
  Stop.refactor-verifier.py         ← Blocks STOP if required steps incomplete
  statemanagerrefactor.py           ← Phase state: PREFLIGHT→DISCOVER→PLANNING→EXECUTION
  ledgerappend.py                   ← Append-only execution ledger (JSONL)

tests/
  test_synthesizefindings.py  ← Health score, dedup, severity grouping
  test_attach_synthesis.py    ← Plan attachment and synthesis integration
```

### What Is Real vs. Aspirational

The following **exist and work**:
- `scripts/astrefactorhelpers.py` — LibCST `RenameAttribute`, `RemoveUnusedImport`, `ExtractMethodTransformer`, `diffsources()`
- `scripts/complexityscanner.py` — CC scoring with P-level thresholds
- `scripts/deduplicate.py` — canonical finding deduplication
- `scripts/evidencecollector.py` — RED/GREEN phase evidence
- `scripts/refactorplan.py` — plan generation (priority-sequential ordering; dependency topo-sort is pending)
- `scripts/synthesizefindings.py` — Health Score computation
- All 6 hook files in `hooks/`
- Both test modules in `tests/`

The following are **pending** (designed, not yet wired — see CHANGELOG):
- `changeset.files[]` multi-file schema on findings
- Import-graph dependency ordering in `refactorplan.py`
- Worktree-based isolated execution
- Publication artifact generation (commit message, PR description, CHANGELOG, resume bullets)
- `scripts/statemanagerrefactor.py --diagnose` flag
- 8-agent comprehensive mode

---

## Priority Thresholds

| Priority | Cyclomatic Complexity | Meaning |
|----------|-----------------------|---------|
| P0 | ≥ 30 | Block — structural emergency |
| P1 | ≥ 15 | Schedule — current sprint |
| P2 | ≥ 8  | Queue — next session |
| P3 | < 8  | Log — opportunistic |

**Health Score** = `100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)`, clamped to [0, 100]
