---
title: "SHIP receipt mechanically generated from per-check results, not LLM-assembled"
created: 2026-07-31
source: session-019fb177 (SHIP-RECEIPT-01 task)
tags: [ship, receipt, mechanical-enforcement, progressive-disclosure, deterministic-output, report-structure]
summary: >
  The SHIP DONE/BLOCKED receipt for /go's ship profile was thin because the LLM
  assembled it by hand — missing fields, understated check disclosure. The fix:
  ship_receipt.py mechanically collects git state, runs Phase 3 verification
  checks scoped to changed files, DERIVES the verdict from check results (never
  trusts an LLM aggregate), and emits a receipt with progressive disclosure.
  The LLM fills only judgment fields. This applies the manifest-at-start +
  mechanical-finalizer pattern from /check to the ship domain.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
sources:
  - "Workspace wiki: close-report-design-user-centric-progressive-disclosure.md (progressive disclosure research)"
  - "Workspace wiki: check-receipt-lifecycle-manifest-and-mechanical-derivation.md (manifest + mechanical derivation pattern)"
  - "Workspace wiki: deterministic-output-engineering.md (deterministic output principles)"
relations:
  - target: wiki/concepts/check-receipt-lifecycle-manifest-and-mechanical-derivation.md
    type: refines
  - target: wiki/concepts/close-report-design-user-centric-progressive-disclosure.md
    type: applies
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
---

# SHIP receipt mechanically generated from per-check results

## Decision context

**Why this was needed:** `/go ship` produced thin receipts — the LLM was supposed to fill a 13-field receipt template (review, fix-loop, verify, docs, spec, breaking, rollback, merge, handoff, wiki, next), but under closure pressure it consistently omitted fields, understated check disclosure, and produced placeholder text. The problem wasn't the template — it was the producer. The LLM had to remember to run each check AND remember to report each result, then assemble them into a coherent receipt. Two memory-dependent steps where one is enough.

**The architectural defect (same pattern as [[check-receipt-lifecycle-manifest-and-mechanical-derivation]]):** the receipt existed (in SKILL.md as a template), the consumer existed (the operator reads it to decide whether to trust the ship), but the producer was memory-dependent. The LLM had to fill it completely every time, and it didn't.

## The design: mechanical collection + derivation + progressive disclosure

### Three principles from wiki research

1. **Progressive disclosure** (`close-report-design-user-centric-progressive-disclosure`): outcome first (verdict), then check summary, then detail. The user needs "SHIP DONE or BLOCKED?" in the first line, not a wall of check statuses.

2. **Mechanical verdict derivation** (`check-receipt-lifecycle-manifest-and-mechanical-derivation`): the verdict is DERIVED from per-check results, never trusted from an LLM-supplied aggregate. A contradictory input (LLM says "looks good" but tests fail) produces a derived BLOCKED, not a contradictory DONE.

3. **Mechanical enforcement** ([[mechanical-enforcement-over-behavioral-reminder]]): prompt instructions have ~12% compliance ceiling; script invocations have 100% compliance once invoked.

### What the script does

`ship_receipt.py` collects:
- Git state per repo (branch, HEAD, commits, SHA range, files changed, dirty tree)
- Phase 3 checks scoped to changed files (not whole-repo):
  - Tests: finds test files by walking up from changed source to `tests/` dirs, runs pytest, baseline-aware
  - Lint: ruff on changed Python files only
  - Type checking: pyright on changed Python files
  - Doc-readiness: doc-check script if available
  - Breaking-change detection: cross-package imports via code_analysis.py
  - Dirty tree check

Then **derives** SHIP DONE (all checks PASS/PASS_WITH_INHERITED/WARN/SKIP) or SHIP BLOCKED (any check FAIL/BLOCK). The LLM cannot override the mechanical verdict.

### What the LLM fills

Only judgment fields: `review` (verdict from the self-review specialist), `fix-loop` (iteration count), `spec` (plan match or contract generation), `merge` (merge result), `handoff`, `wiki`, `next`. Every mechanical field is code-populated or explicitly SKIP.

### Test discovery scoping

The first version ran root-level pytest across the entire workspace — picking up 10 errors from unrelated test suites. Fix: scope to changed files by walking up the tree from each changed source file to find `tests/test_<name>.py` in ancestor directories. This catches the tests that matter for the changes being shipped, not the workspace's entire health.

## Steelman of the rejected alternative

**Rejected: keep the LLM-assembled receipt, add a validator that checks completeness.**

**Why it was reasonable:** validators are lighter-weight than a full generator. The LLM retains flexibility in field content. The pattern is proven (wiki + close both use it). And the [[deterministic-output-engineering]] research notes that programmatic validation hooks are a recognized layer in the multi-layered architectural approach.

This is the same principle as [[mechanical-enforcement-over-behavioral-reminder]] — a prompt instruction ("remember to fill all 13 fields") has a low compliance ceiling; a script invocation has 100% compliance once invoked. The [[deterministic-output-engineering]] research from NotebookLM confirms: LLMs prioritize conversational fluidity over structural rigidity, causing drift in schema-respecting output. The generator eliminates that drift.

**Why it loses:** a validator catches missing fields AFTER the LLM has already done its (incomplete) work. The LLM then has to re-run checks it forgot, re-assemble, and re-validate — a multi-turn fix loop for a receipt that should be deterministic. The generator approach runs all checks in one invocation and produces the receipt in one shot. The generator is the manifest-at-start pattern applied to ship: collect-then-derive beats assemble-then-validate.

## Falsifier

This design is wrong if:
- The script's test discovery misses relevant test files (false negative on coverage) — fixable by expanding the tree-walk search
- The script's verdict derivation is too strict (e.g., lint failures that are pre-existing block the ship) — mitigated by baseline-aware testing and scoping to changed files
- The LLM-judgment fields (review, spec) are where the real value is, and the mechanical fields are just plumbing — then the generator adds ceremony without improving decision quality
- A future change adds a check type the script doesn't know about (e.g., integration tests, e2e) — the LLM would need to run it separately and manually fill the result

## What this means for our workspace

The `/go ship` profile (SKILL.md Phase 3) now calls `ship_receipt.py` at Step 3a instead of the manual 12-check list. The old check list is preserved as reference. The script produced a clean SHIP DONE on its final test run (6/6 tests, lint clean, types clean, docs WARN, breaking none).

The dogfooding moment validated the design: the script caught its own lint issues (unused import, ambiguous variable names) on first real run — exactly the mechanical enforcement working as intended. An LLM-assembled receipt would have shipped those lint issues silently.

This pattern (mechanical receipt generator + LLM fills only judgment fields) is transferable to any report where the producer is LLM-dependent and the fields mix deterministic data with judgment. Candidates: `/check` receipts (already partially mechanical via [[check-receipt-lifecycle-manifest-and-mechanical-derivation]]'s `check_lifecycle.py`), `/review` FINDINGS.md, `/aar` reports. The [[close-report-design-user-centric-progressive-disclosure]] research directly informed the output structure — verdict first, check summary second, detail on request.

## Receipts

- `~/.grok/skills/go/__lib/ship_receipt.py` — the generator script (692 lines)
- `~/.grok/skills/go/SKILL.md` Phase 3 Steps 3a-3d — the skill wiring (commit `07c863d`)
- `~/.grok/hooks/test_PreToolUse_spawn_model_gate.py` — test fixed as a side effect (commit `485aebc`)
- `P:/.data/wiki/concepts/check-receipt-lifecycle-manifest-and-mechanical-derivation.md` — the pattern this refines

## Sources

- [Close report design: user-centric progressive disclosure](file:///P:/.data/wiki/concepts/close-report-design-user-centric-progressive-disclosure.md) — progressive disclosure principle (5+ independent sources)
- [Durable /check receipt lifecycle](file:///P:/.data/wiki/concepts/check-receipt-lifecycle-manifest-and-mechanical-derivation.md) — manifest-at-start + mechanical-finalizer pattern
- [Deterministic Output Engineering](file:///P:/.data/wiki/concepts/deterministic-output-engineering.md) — transition from probabilistic instruction-following to deterministic lifecycle enforcement
