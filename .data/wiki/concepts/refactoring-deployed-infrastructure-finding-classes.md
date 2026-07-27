---
title: "Refactoring deployed infrastructure: 4 finding classes for the refactor skill"
created: 2026-07-27
source: session-2026-07-27 (/www research on refactor skill improvements)
tags: [refactoring, deployed-infrastructure, sdlc, refactor-skill, source-deployed-divergence, dead-code, constant-drift, execution-order, skill-improvement]
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
summary: >
  Four finding classes uncovered during Phase 3 hook refactoring that the
  /refactor skill doesn't mechanically detect: (1) source-to-deployed
  divergence risk, (2) dead code discovery after optimization, (3) shared
  constant drift across hook files, (4) execution-order risk within priority
  classes. Each maps to established refactoring practice (deployment validation,
  seam identification, DRY detection, safe sequencing). The improvements are
  additive grep-based detection steps, not new analysis phases. Connects to
  [[coupling-inventory-as-mandatory-design-section]], [[hook-evidence-collection-cost-vs-timeout-tradeoff]],
  and [[skip-write-only-computation-over-cache-or-budget]].
sources:
  - https://medium.com/trendyol-tech/validating-deployments-for-production-safety-22d4f346419b (Trendyol, 2025)
  - https://www.hashicorp.com/en/blog/patterns-to-refactor-infrastructure-as-code-for-compliance (HashiCorp, 2025)
  - https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/ (Feathers summary)
  - https://evilmartians.com/chronicles/lefthook-refactoring-the-git-hooks-automation-tool-back-into-shape (Evil Martians, 2022)
  - https://medium.com/@erwindev/refactoring-with-confidence-how-to-restructure-code-without-breaking-everything-3fe1b7f4dcd1 (Hermanto, 2026)
relations:
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: extends
  - target: wiki/concepts/skip-write-only-computation-over-cache-or-budget.md
    type: related
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: related
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
---

# Refactoring deployed infrastructure: 4 finding classes for the refactor skill

## Decision context

**Why this research was needed:** during Phase 3 hook refactoring (session 019fa23d), a `/tp review` of the refactor plan caught three issues the plan missed: (1) no deployment verification step (source worktree ≠ deployed hooks), (2) wrong execution order (highest-risk seam first), (3) no verification that shared constants were actually identical before extracting. A fourth class (dead code) was discovered during the hook timeout investigation. The operator asked: what improvements would the refactor skill and SDLC work benefit from?

**What alternatives were explored:** full CI/CD pipeline for hooks (rejected — solo workspace, manual deployment is fine), automated dead-code tools like vulture/pyflakes (rejected — noisy on dynamic imports), more planning ceremony (rejected — disconfirmation research warns analysis paralysis kills progress).

## The 4 finding classes

### Class 1: Source-to-deployed divergence

**The problem:** the refactor skill assumes one write root (worktree or main). But deployed infrastructure (hooks, scripts, config) has TWO copies that must stay in sync: source (worktree/repo) and deployed (live path). A refactor that passes tests in the worktree but isn't propagated creates silent divergence.

**Session evidence:** the `verification_receipt_writer.py` fix was applied to BOTH source and deployed, but the refactor plan's verify commands only test the source worktree. If the deployed copy diverges (e.g., a sibling session edited it), the tests pass but the live hook is broken.

**Established practice:** Trendyol's OAT validation and HashiCorp's IaC compliance patterns treat deployment validation as separate from code validation. After refactoring, verify the DEPLOYED artifact, not just the source.

**Skill improvement:** add a `deployment_target` field to `seams.json`. When present, each seam's verify step includes: (1) copy source→deployed, (2) hash-verify, (3) smoke-test the deployed artifact. This is distinct from `verify_commands` (which run against source/worktree).

### Class 2: Dead code discovery after optimization

**The problem:** the refactor skill's inventory step doesn't systematically check for dead code. The session discovered `_resolve_path_identities` was dead AFTER profiling around it — the optimization should have started with a reader-grep.

**Session evidence:** the function had zero callers but consumed 21s per hook invocation. The refactor skill's coupling analysis (Step 4.1) looks at imports but not at function-level call sites.

**Established practice:** Michael Feathers' "Working Effectively with Legacy Code" emphasizes identifying seams. Dead code is an anti-seam: behavior CAN'T change because nothing calls it. The inventory should flag these.

**Skill improvement:** add dead-code detection to Step 4.1: for each function in scope, grep for callers. Functions with zero callers (outside their own definition and tests) get flagged as `class: P2, delete_or_close`.

### Class 3: Shared constant drift

**The problem:** three hook files independently define identical `CODE_EXTENSIONS`. Any update to one without the others creates silent disagreement about what counts as "code modified."

**Session evidence:** `quality_gate.py:32`, `quality_nudge.py:23`, `verification_receipt_writer.py:92` — all identical sets. The refactor skill found this via coupling analysis but has no explicit constant-drift detection pattern.

**Established practice:** Evil Martians' Lefthook refactoring article documents the same pattern in git hook tools. Solution: extract to shared module.

**Skill improvement:** add constant-drift detection to Step 4.1: grep for `^[A-Z_]+\s*=` patterns across files in scope. Same constant name in ≥2 files → flag as `class: P1, delete_or_close: duplicate definitions`. This is the structural fix for DRY violations that the [[coupling-inventory-as-mandatory-design-section]] concept already documents but the refactor skill doesn't mechanically detect. The detection is precise: module-level constant names are exact-match, so false positives are near-zero.

### Class 4: Execution-order risk

**The problem:** the refactor skill ranks seams P0→P4 (integrity priority) but doesn't consider risk-of-change within the same priority class. The plan had the highest-risk seam (A1: shared constants, modifies imports in 4 files including load-bearing `quality_gate.py`) FIRST.

**Session evidence:** the `/tp review` caught this — the plan should have started with B2 (trivial deletion, zero risk) before A1 (structural change, highest risk).

**Established practice:** "Refactoring with Confidence" (Hermanto 2026) and tembo.io both recommend: "start with low-risk areas and expand as your team gains confidence." The disconfirmation research warns about analysis paralysis — but the fix is better ordering, not less planning.

**Skill improvement:** add a secondary sort key within priority classes: `risk_of_change` (S/M/L). When two seams are both P2, the S-risk one executes first. Risk assessment: S = pure deletion/additive (no existing path modified); M = import path or signature change; L = behavioral logic change in load-bearing path. This mirrors the [[skip-write-only-computation-over-cache-or-budget]] principle: audit before acting, and act in the order that builds confidence.

## What this means for our workspace

The `/refactor` skill gains 4 additive detection steps (no restructuring):

1. **`deployment_target` field** in seams.json + deployment verification in Step 6
2. **Dead-code detector** in Step 4.1 (grep for callers per function)
3. **Constant-drift detector** in Step 4.1 (grep for `^[A-Z_]+\s*=` across files)
4. **Risk-of-change secondary sort** within priority classes in Step 4.2

Each is a few lines of grep + classification logic. None adds an analysis phase. The improvements follow the [[compound-skill-improvement-patterns]] model: mechanical detection catches what model recall misses. The constant-drift detector is the highest-precision addition (exact name match across files has near-zero false positives). The dead-code detector is the highest-value addition (it would have caught the 21s timeout before profiling). The deployment-target field is the highest-risk-reduction addition (it prevents the source≠deployed silent divergence that caused the Phase 3 acceptance ambiguity). The risk-of-change sort is the lowest-cost addition (one secondary sort key) but prevents the execution-order error that the `/tp review` caught.

## Implications

The 4 improvements transform the refactor skill from a plan-and-execute tool into a detect-and-plan tool. The current skill relies on the model noticing structural problems during inventory. The improved skill mechanically surfaces them via grep patterns, then the model evaluates severity and execution order. This is the same pattern as `/tp session`'s Step 0 transcript scan and `/why`'s Step 0.5 wiki query — mechanical detection feeding into model judgment. The pattern is documented in [[visible-output-contracts-for-behavioral-skill-steps]]: the detection step produces visible evidence, the model interprets it.

The deployment-target field is the most workspace-specific improvement — it only applies to deployed infrastructure (hooks, scripts). But the other three (dead-code, constant-drift, risk-of-change sort) apply to any Python codebase. They could be extracted into a shared `refactor_detectors.py` utility that `/refactor`, `/review`, and `/check` all call.

## Falsifier

These improvements are wrong if:
- **The grep-based detection is too noisy** (flags too many false positives). Mitigation: start with the constant-drift detector (highest precision — exact name match across files). Add dead-code detection only if constant-drift proves useful.
- **The deployment_target field is never used** (no seams actually have deployed copies). Mitigation: the Phase 3 hooks always have this property; any hook refactor will use it.
- **The risk-of-change sort reorders seams incorrectly** (puts a low-risk-but-important seam after a high-risk-but-trivial one). Mitigation: the sort is WITHIN priority class only — P0 always comes before P1 regardless of risk.

## Sources

- [Trendyol: Validating Deployments for Production Safety](https://medium.com/trendyol-tech/validating-deployments-for-production-safety-22d4f346419b) (Trendyol, 2025) — deployment validation as a separate step from code validation
- [HashiCorp: Patterns to Refactor IaC for Compliance](https://www.hashicorp.com/en/blog/patterns-to-refactor-infrastructure-as-code-for-compliance) (HashiCorp, 2025) — compliance patterns for infrastructure refactoring
- [Understand Legacy Code: Key Points of Working Effectively with Legacy Code](https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/) (Feathers summary) — seam identification and dependency breaking
- [Evil Martians: Lefthook Refactoring](https://evilmartians.com/chronicles/lefthook-refactoring-the-git-hooks-automation-tool-back-into-shape) (2022) — refactoring git hook tools, shared constant extraction
- [Hermanto: Refactoring with Confidence](https://medium.com/@erwindev/refactoring-with-confidence-how-to-restructure-code-without-breaking-everything-3fe1b7f4dcd1) (2026) — safe sequencing, start with low-risk areas

## Receipts

- **"CODE_EXTENSIONS duplicated in 3 files":** receipt — `Select-String -Path "C:/Users/brsth/.grok/hooks/scripts/*.py" -Pattern "^CODE_EXTENSIONS\s*="` returned 3 hits (quality_gate.py:32, quality_nudge.py:23, verification_receipt_writer.py:92), this session.
- **"_resolve_path_identities has zero callers":** receipt — `rg "_resolve_path_identities" P:/worktrees/dotgrok-phase3/hooks/scripts/*.py` returned 4 hits (all in the writer: def + comment refs), zero call sites. Verified by /review specialist (57 tool calls).
- **"Plan had highest-risk seam first":** receipt — `/tp review` of PLAN.md found A1 (shared constants, 4 files, load-bearing) ordered before B2 (dead code, 1 file, zero risk), this session.
