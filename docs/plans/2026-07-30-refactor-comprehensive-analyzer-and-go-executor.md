# Plan: /refactor as Comprehensive Analyzer + /go as Expert Executor + Durable PowerShell Quoting Fix

Created: 2026-07-30
Source: /www research sessions 2026-07-30 (two wiki concepts produced)
Status: ready_for_review

## Goal

Transform `/refactor` from a seam-extraction-only tool into a comprehensive cross-file/architecture-level optimization analyzer, confirm `/go` as the expert executor, and durably solve the PowerShell quoting failure mode that wastes subagent budgets.

## Decision context

Three research runs in this session produced two wiki concepts:
- `refactoring-discipline-tdd-parallel-seams-verification-gates.md` — TDD discipline validation, parallel seam safety, verification gate gaps
- `refactor-as-comprehensive-optimization-analyzer.md` — the planner-executor split, the "analyze everything" taxonomy (8 debt categories, 6 architecture smells, Fowler's 152 refactorings), and the tool stack

Key findings driving this plan:
1. `/refactor`'s "when practical" TDD is domain-correct (characterization tests, not red-first) — no change needed
2. Parallel seam execution is safe when DSM-verified independent — add parallelism detection
3. `/refactor` covers ~30% of the full optimization taxonomy — 4 new analysis dimensions needed
4. The planner-executor split is externally validated (5/5 sources)
5. PowerShell quoting via inline `python -c` is a chronic failure — solved by moving code to files

## Governing invariants

- `/refactor` is **read-only** in analysis mode (no product writes during analysis)
- Anti-recursion: `/refactor` does NOT call `/go`; `/go` delegates TO `/refactor` and then executes
- Multi-terminal isolation: worktree + branch for any execution (owned by `/go`)
- Stale-data immunity: re-read before edit (owned by both skills)
- File conventions: shared scripts → `P:/.agents/scripts/`; skill scripts → `~/.grok/skills/<skill>/__lib/`

---

## Track A: /refactor deepening — the comprehensive analyzer

### Task A1: Create dependency graph analysis step
- [ ] Add `pydeps` and/or `tach` to `/refactor` Step 4.1 (inventory)
- [ ] Dependency graph output: circular imports, module-level fan-in/fan-out
- [ ] Architecture smell detection: cyclic dependency, god component (module-level)
- [ ] Output findings as `category: "architecture_smell"` in seams.json
- **Verification:** `python -m pydeps P:/packages/yt-is --show-cycles --max-bacon=2 -o P:/tmp/pydeps_test.dot` succeeds and produces a graph
- **Depends on:** nothing

### Task A2: Add cross-file duplication detection
- [ ] Evaluate PyChase vs python-repetition-hunter vs CPD (PMD) for our codebase
- [ ] Add the chosen tool to `/refactor` Step 4.1
- [ ] Detection: functions/blocks with >80% similarity across files → `category: "duplication"` findings
- [ ] This is the structural DRY detector that [[coupling-inventory-as-mandatory-design-section]] calls for but `/refactor` doesn't mechanically detect
- **Verification:** chosen tool runs on `P:/packages/yt-is` and produces duplication report
- **Depends on:** nothing

### Task A3: Add test gap / coverage analysis
- [ ] Add `pytest --cov` analysis to `/refactor` Step 4.1
- [ ] For each module/function with 0% or <50% coverage: flag as `category: "test_gap"`
- [ ] For L-risk seams touching untested code: require characterization tests before execution (recommendation in seams.json, enforced by `/go` before executing that seam)
- [ ] This implements the "identification of characterization tests" capability the operator specified
- **Verification:** `python -m pytest P:/packages/yt-is/tests/ --cov=P:/packages/yt-is --cov-report=term-missing` succeeds and produces coverage report
- **Depends on:** nothing

### Task A4: Add touch-point / shotgun-surgery detection
- [ ] Analyze git history for files changed together per commit
- [ ] Files that change together >60% of the time are coupled → `category: "coupling"` finding
- [ ] This catches the "shotgun surgery" smell that coupling thresholds alone miss (they measure static coupling; this measures dynamic coupling)
- **Verification:** git history analysis script runs on last 50 commits and produces co-change report
- **Depends on:** nothing

### Task A5: Evolve seams.json schema
- [ ] Add `analysis_type: "comprehensive"` field
- [ ] Add `category` field to findings: `"code_smell" | "architecture_smell" | "duplication" | "test_gap" | "coupling"`
- [ ] Add `dependency_graph_path` field pointing to pydeps/tach output
- [ ] Add `test_coverage_summary` field
- [ ] Keep backward compatibility: existing seams with no `category` default to `"code_smell"`
- [ ] The richer artifact enables `/go` to do DSM-based parallel decomposition
- **Verification:** existing seams.json files parse correctly with the new schema; new findings appear with correct categories
- **Depends on:** A1, A2, A3, A4 (all feed into the schema)

### Task A6: Update /refactor SKILL.md
- [ ] Rename Step 4.1 from "Inventory" to "Comprehensive Analysis"
- [ ] Add sub-steps for each analysis dimension (4.1a dead-code/constant-drift, 4.1b dependency graph, 4.1c duplication, 4.1d test gaps, 4.1e touch-points)
- [ ] Add parallelism detection: when seams.json has ≥3 independent findings, emit "Parallelizable: run via `/go execute <plan>` for parallel fan-out"
- [ ] Update Step 4.2 ranking to include architecture smells (cycles = P1, god components = P1)
- [ ] Update the "Recommended next" table: analysis complete → recommend `/go execute <plan>` (not `/check`)
- [ ] Make execute mode in /refactor a thin delegation: `/refactor execute` → "Use `/go execute <seams.json>` instead. /refactor is the analyzer; /go is the executor."
- **Verification:** `/refactor yt-is` (plan mode) produces a comprehensive analysis with architecture findings; `/refactor execute` routes to /go
- **Depends on:** A1, A2, A3, A4, A5

### Task A7: Update /refactor developer-preferences section
- [ ] Add the comprehensive analysis scope statement: "DRY, SoC, complexity, coupling, test gaps, architecture smells, cross-file patterns"
- [ ] Add the planner-executor framing: "/refactor analyzes; /go executes"
- **Verification:** text present in SKILL.md header
- **Depends on:** A6

---

## Track B: /go executor updates

### Task B1: Update /go refactor profile to consume evolved seams.json
- [ ] Update the `refactor` profile recipe in `/go` Step 4 to consume `analysis_type: "comprehensive"` seams.json
- [ ] When seams.json has ≥3 findings with `depends_on: []` and no shared files: auto-enable H4 parallel fan-out
- [ ] Before executing any seam touching test_gap code: verify characterization tests exist (block if missing)
- [ ] DSM decomposition: use `dependency_graph_path` to verify no semantic conflicts between parallel seams
- **Verification:** `/go execute <comprehensive-seams.json>` correctly parallelizes independent findings
- **Depends on:** A5

### Task B2: Update /go H4 subagent spawn template (PowerShell quoting fix)
- [ ] Add to the spawn template: "For web research, use `python P:/.agents/scripts/ddgs_search.py \"<query>\" --max <N>`. NEVER use inline `python -c` with nested quotes — it fails on Windows PowerShell."
- [ ] Add to the spawn template: "For any Python that needs to run: write a temp `.py` script to `P:/tmp/` first, then execute it. Never embed multi-line Python in `python -c`."
- [ ] This is the durable enforcement of the Class C quoting rule at the subagent dispatch layer
- **Verification:** spawned subagent uses ddgs_search.py instead of inline python -c
- **Depends on:** C1 (the script must exist first)

### Task B3: Update /go refactor delegation text
- [ ] Update the `refactor` profile to state: "/refactor produces the optimization plan (comprehensive analysis + seams.json). /go executes it."
- [ ] Update anti-recursion text: "/refactor is strictly read-only analysis. If `/refactor execute` is invoked, route to `/go execute`."
- **Verification:** text present in /go SKILL.md refactor profile
- **Depends on:** A6

---

## Track C: Durable PowerShell quoting fix

### Task C1: ddgs_search.py shared script ✅ DONE
- [x] Created `P:/.agents/scripts/ddgs_search.py`
- [x] Verified: JSON output, `--site`, `--text`, `--max` all work
- [x] Standalone: no workspace module imports, just stdlib + ddgs

### Task C2: Update /www SKILL.md to reference ddgs_search.py
- [ ] Replace the inline `python -c "from ddgs import DDGS..."` examples in Phase 2 and Phase 2b with `python P:/.agents/scripts/ddgs_search.py "<query>" --max <N>`
- [ ] Replace the `/tmp/www_*.py` temp-script pattern with a note: "For DDG searches, use the shared `ddgs_search.py` script. For other Python, write to `P:/tmp/` and execute."
- [ ] Update the subagent dispatch prompt template to include: "Use `python P:/.agents/scripts/ddgs_search.py \"<query>\"` for all DDG searches."
- **Verification:** /www SKILL.md has no inline `python -c` DDG patterns
- **Depends on:** C1 ✅

### Task C3: Capture the pattern as a wiki concept
- [ ] Write `P:/.data/wiki/concepts/subagent-shell-quoting-durable-fix.md`
- [ ] Document: the failure mode (inline `python -c` with nested quotes fails on PowerShell), the fix (shared script files), the precedent (378s wasted on session 019fb3a8), the generalization (any Python subagents run should be files, not inline)
- [ ] Cross-link to [[shell-quoting-and-non-persisting-edits]] and AGENTS.md § Class C quoting
- **Verification:** wiki concept exists, ≥40 lines, has falsifier
- **Depends on:** C1 ✅

### Task C4: Add ddgs_search.py to version_check.py dependency list
- [ ] Ensure `ddgs` package is checked by `python P:/.agents/scripts/version_check.py`
- [ ] (Already checked — `version_check.py` line 52/58 already has `ddgs` as a DepSpec)
- **Verification:** `python P:/.agents/scripts/version_check.py ddgs` returns OK
- **Depends on:** nothing

---

## Track D: Integration testing

### Task D1: End-to-end test — /refactor analysis → /go execution
- [ ] Run `/refactor <small-package>` in analysis mode
- [ ] Verify: PLAN.md + seams.json contain architecture findings + duplication + test gaps
- [ ] Run `/go execute <seams.json>`
- [ ] Verify: independent findings execute in parallel (if applicable); per-finding verification passes
- **Verification:** full pipeline works end-to-end on a real package
- **Depends on:** A6, B1

### Task D2: End-to-end test — PowerShell quoting fix
- [ ] Spawn a research subagent with the updated template
- [ ] Verify: subagent uses `python P:/.agents/scripts/ddgs_search.py` instead of inline `python -c`
- [ ] Verify: zero quoting failures, search completes in <30s
- **Verification:** subagent output contains structured search results from ddgs_search.py
- **Depends on:** B2, C2

---

## Execution order (dependency-aware)

```
Phase 1 (parallel):
  C1 ✅ → C2, C3 (PowerShell quoting fix — immediate value)
  A1, A2, A3, A4 (analysis dimensions — independent)

Phase 2 (after Phase 1):
  A5 (seams.json schema — needs all analysis dimensions)
  B2 (spawn template — needs C1)

Phase 3 (after Phase 2):
  A6 (/refactor SKILL.md — needs A5)
  A7 (preferences — needs A6)

Phase 4 (after Phase 3):
  B1 (/go refactor profile — needs A5)
  B3 (delegation text — needs A6)

Phase 5 (after Phase 4):
  D1 (end-to-end pipeline test)
  D2 (end-to-end quoting test)
```

## Acceptance criteria

1. `/refactor <package>` produces comprehensive analysis covering code smells + architecture smells + duplication + test gaps + coupling (not just seam extraction)
2. `/go execute <seams.json>` correctly parallelizes independent findings with worktree isolation
3. `/go execute` blocks on seams touching untested code until characterization tests are identified
4. Subagents dispatched by `/go` or `/www` use `ddgs_search.py` instead of inline `python -c` — zero quoting failures
5. The anti-recursion rule is clean: `/refactor` is read-only analysis; `/go` is the only executor

## Falsifier

This plan is wrong if:
- Architecture smell detection produces too much noise for our package sizes (most <50 files) → drop A1, keep the other analysis dimensions
- The planner-executor split introduces handoff friction in practice → re-integrate execution into `/refactor` for single-seam cases
- `pydeps`/`tach` don't work reliably on Windows multi-root workspaces → fall back to AST-based import scanning
