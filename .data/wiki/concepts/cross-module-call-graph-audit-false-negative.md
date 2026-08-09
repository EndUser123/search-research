---
title: "Cross-module call-graph audit false-negative"
concept_type: "anti-pattern"
created: 2026-07-27
agent: grok
host: both
cognitive_load: 2
verification: session-verified
sources:
  - session 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e (2026-07-27 /go hermeticity refactor)
tags: [hermeticity, audit, call-graph, transitive, hardcoded-path, false-negative, anti-pattern, testing, refactoring]
summary: >
  When verifying a refactor that propagates a configuration parameter (cfg,
  options, settings) through a codebase, an AST audit scoped to ONE module
  produces a false "all paths configured" verdict whenever the production
  call graph reaches a SIBLING module via import. The audit reports zero
  function-body references to module-level constants in module A, while
  module B (imported by A) still reads the same constants directly. The
  escape is only visible when the audit covers the transitive call graph,
  not just the file under edit. This is the module-level analog of the
  multi-repo false-negative pattern and produces the same class of
  "verification theater" failure: a passing check that proves nothing.
relations:
  - target: wiki/concepts/single-repo-verification-false-negative-on-multi-repo-workspace.md
    type: complements — that concept covers cross-repo git history; this covers cross-module call graphs. Same failure class, different layer.
  - target: wiki/concepts/narrative-as-signal
    type: related — the "AST audit clean" narrative substitutes for actual transitive verification
  - target: wiki/concepts/subprocess-as-degradation-boundary
    type: related — both are about hidden coupling at module boundaries
---

# Cross-module call-graph audit false-negative

## Decision context

**Why this knowledge was needed:** during a `/close` hermeticity refactor
(Workstream B, session 019fa111, 2026-07-27), the operator issued two
consecutive `needs_fix` verdicts on work I had declared `ready_for_review`.
Both caught the same failure class: I ran an AST audit on
`close_accounting.py`, reported "zero function-body references to module-level
constants — clean," and shipped. The operator then proved the production call
graph escaped into `continuation_coverage.py` (imported by `close_accounting`)
which still read `WORKSPACE`, `ARTIFACTS_DIR`, `HANDOFFS_DIR`, `GROK_SESSIONS`
directly and wrote a ledger to the real `P:/.artifacts/` — defeating both
the hermeticity claim and the `--no-mutate` flag.

The first `needs_fix` was on the same defect class as the second, separated
by one refactor iteration. The pattern: an audit scoped to the file under
edit cannot see escapes in the files it imports.

## The anti-pattern

```
refactor target: module_a.py (propagate cfg parameter)
audit scope:    AST(module_a.py) — "zero globals in function bodies"
verifier:       "all production paths configured"
reality:        module_a imports module_b
                module_b still reads WORKSPACE / ARTIFACTS_DIR directly
                module_a.something() -> module_b.something() -> global path
escape:         module_b writes a file to P:/.artifacts/ under --no-mutate
```

The audit is not wrong about what it measured; it is wrong about what it
claimed. "Zero globals in module_a's function bodies" is true.
"All production paths configured" is false. The verifier conflated the two.

## Observable signature

```
refactorer:   "AST audit confirms zero function-body references to module globals"
operator:     "needs_fix — module_b.py still uses WORKSPACE at line N"
              (operator ran the actual scanner and observed a leaked file
               at P:/.artifacts/continuation-coverage-hermetic.json)
refactorer:   (silently re-audits module_b; finds the escape)
```

The signature is asymmetric: the refactorer's audit passes; the operator's
runtime test fails. The audit's scope was the file under edit; the runtime
test's scope was the actual call graph.

## Why this is dangerous

1. **It produces false hermeticity claims.** A `--no-mutate` flag that
   passes its own audit while still writing files is worse than no flag —
   it actively misleads tests that depend on it.

2. **The failure compounds across refactor iterations.** Each iteration
   that declares `ready_for_review` based on a single-module audit burns
   one operator review cycle. In session 019fa111, this consumed two
   full iterations before the cross-module audit was performed.

3. **It is the module-level analog of the multi-repo false-negative** ([[single-repo-verification-false-negative-on-multi-repo-workspace]]).
   Same structural failure: the verifier's scope is narrower than the
   thing being verified. The fix is the same shape: enumerate ALL
   reachable modules/repos, not just the one under edit. This is itself
   an instance of evidence-scope-discipline — the receipt proves only
   the scope it covers, not the scope of the claim.

4. **AST audits are particularly prone to this** because they are easy
   to write and produce satisfying "zero remaining" output. The ease of
   the audit is inversely correlated with its coverage. This inverts the
   principle behind [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]:
   the easy path (single-file AST scan) produces a false-positive "clean"
   verdict, while the hard path (cross-module transitive audit) produces
   the actually-correct verdict.

## The structural fix

**Cross-module transitive call-graph audit, not single-module AST scan.**

For a refactor that propagates `cfg` (or any parameter) through a codebase:

1. **Enumerate the import graph.** For Python: parse imports, walk the
   `import X from Y` statements reachable from the entry point.
2. **For each reachable module, scan for the same defect class** (globals
   reads, hardcoded paths, mutation operations).
3. **Classify each reference** as: correctly configured (function takes
   cfg), production-default-only (module-level constant, overridable),
   blocking hardcoded escape (hardcoded inside function body, no override),
   or intentionally out of scope (proven unreachable).
4. **Report all blocking escapes**, not just the ones in the file under
   edit.

A reference implementation is at `P:/tmp/cross_module_audit.py` (this
session). It scans `close/__lib/*.py` for globals references and mutation
operations, then classifies each. The audit takes ~1 second and caught
the continuation_coverage escape that the single-module audit missed.

For larger codebases, the audit should integrate with the import graph
(`ast.parse` + `ast.Import` / `ast.ImportFrom` walking) rather than
scanning a fixed directory.

## When this fires

Apply cross-module audit whenever:
- A refactor propagates a configuration parameter through a codebase
- A hermeticity / isolation claim is being made
- A `--no-mutate` / read-only / no-side-effect claim is being made
- An audit produces a "zero remaining" verdict that feels too clean

**Skip cross-module audit** when:
- The change is scoped to a single function with no new imports
- The module under edit has no callers that pass through to other modules
- The change is doc-only or test-only

## Falsifier

This pattern is wrong if a single-module AST audit is sufficient to catch
every hardcoded-path escape in every refactor. Empirical check (session
019fa111, 2026-07-27): one refactor produced two false `ready_for_review`
verdicts because the audit missed escapes in two sibling modules
(`continuation_coverage.py`, `friction_detector.py`). Pattern confirmed.

### Iteration trigger (concept health check)

This concept is not just documentation — it is a **predictor**. It predicts
that future config-propagation refactors will catch sibling-module escapes
if a cross-module transitive audit is performed before declaring
`ready_for_review`.

**The success criterion:** if a future refactor (after 2026-07-27) produces
a third instance of this failure class — i.e., the operator catches a
sibling-module escape that a single-module AST audit missed — the concept
has failed as a prevention mechanism and needs iteration. The minimum
iteration is to promote `P:/tmp/cross_module_audit.py` from a one-off
script to a structural pre-flight check at `P:/.agents/scripts/`, so
future refactors run it mechanically rather than relying on the model to
remember the concept exists.

**Concept health status (as of 2026-07-27):** pattern instances observed
= 2 (both in session 019fa111). Prevention mechanism = documentation only
(this concept page). Iteration threshold = 1 future instance.

## Reference incident

**Session 019fa111 (2026-07-27), iterations 2 and 3 of the Workstream B
hermeticity refactor:**

- **Iteration 2:** `close_accounting.py` was refactored to propagate
  `Config` to all 22 scanner functions. AST audit on
  `close_accounting.py` returned "zero function-body references to
  module-level constants." Verdict: `ready_for_review`. Operator
  rebuttal: `scan_all()` calls `scan_continuation_coverage()` from
  `continuation_coverage.py`, which still uses globals and unconditionally
  writes a ledger. Leaked file: `P:/.artifacts/continuation-coverage-hermetic.json`.

- **Iteration 3 (the fix):** `continuation_coverage.py` got its own local
  `ContCovConfig` dataclass; `close_accounting.scan_all` adapts its
  `Config` to `ContCovConfig` at the call site. `friction_detector.py`'s
  `detect_friction` got a `workspace` parameter for the encoded_cwd.
  Cross-module audit (`P:/tmp/cross_module_audit.py`) confirmed zero
  remaining escapes in the production call graph. The strengthened
  hermetic test (snapshot before/after of ALL write destinations, not
  just the test-configured dir) verified zero writes.

## Relation to existing rules

- **AGENTS.md § "Search Topology"** — establishes the multi-root search
  principle for files. This concept extends it to the import graph: when
  auditing a refactor, walk the imports, not just the file under edit.
- **AGENTS.md § "Claims require receipts; narrative sufficiency is not
  verification"** — the "AST audit clean" narrative is itself a
  narrative-as-signal failure (plausible conclusion substituting for
  transitive verification).
- [[single-repo-verification-false-negative-on-multi-repo-workspace]] —
  the cross-repo analog. Same failure class, different layer.

## Prevention

Two layers, applied together:

1. **Behavioral (this concept).** When auditing a refactor that propagates
   a parameter, enumerate ALL reachable modules via the import graph, not
   just the file under edit. The `P:/tmp/cross_module_audit.py` script is
   a starting point; candidate for promotion to `P:/.agents/scripts/`.

2. **Testing (the strengthened hermetic test pattern).** A hermetic test
   must snapshot ALL possible write destinations before/after, not just
   the test-configured directory. The original hermetic test passed while
   the production path leaked a file into the real `P:/.artifacts/`
   because the test only checked that the test-configured artifacts dir
   was empty. Snapshot-based testing catches cross-module escapes that
   AST audits miss.

## Receipts

- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:37` — `from continuation_coverage import scan_continuation_coverage` (the import that the single-module audit could not see)
- `C:/Users/brsth/.grok/skills/close/__lib/continuation_coverage.py:31-34` — module-level `WORKSPACE`/`ARTIFACTS_DIR`/`HANDOFFS_DIR`/`GROK_SESSIONS` (the escaped globals)
- `C:/Users/brsth/.grok/skills/close/__lib/continuation_coverage.py:825-833` — `save_ledger` writing to global `ARTIFACTS_DIR` (the leak)
- `P:/.artifacts/continuation-coverage-hermetic.json` (536 bytes, mtime 2026-07-27) — the leaked file, kept as test-created residue per operator directive
- `P:/tmp/cross_module_audit.py` — the cross-module audit script that catches this class of escape
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
