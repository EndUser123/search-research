---
title: "SDLC proactive prevention techniques beyond our current pipeline"
created: 2026-07-29
source: session-019fa94d (/www research — what else do people do to prevent problems)
sources:
  - https://github.com/pre-commit/pre-commit-hooks
  - https://bandit.readthedocs.io/
  - https://semgrep.dev/
  - https://github.com/radon-project/radon
  - https://github.com/nedbat/coveragepy
  - https://github.com/beartype/beartype
  - https://pypi.org/project/pip-audit/
  - https://github.com/pycqa/diff-cover
  - https://syrupy.readthedocs.io/
  - https://pylint.readthedocs.io/en/latest/messages/refactor/cyclic-import.html
tags: [verification, prevention, proactive, pipeline, bandit, radon, pip-audit, diff-cover, beartype, coverage, complexity, security, sdlc, check]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  Maps the full landscape of proactive SDLC prevention techniques against
  what our fleet already has. Our /check pipeline has 5 deterministic layers
  (ruff, pyright, pylint, trace_check, vulture) but zero security scanning,
  zero complexity analysis, zero coverage gating, zero dependency auditing,
  zero runtime type checking, and zero import cycle detection. The research
  identifies 6 techniques with the highest ROI for an AI-agent-maintained
  Python codebase: bandit (security), radon (complexity), pip-audit (deps),
  diff-cover (new-line coverage gate), pylint cyclic-import (import cycles),
  and branch coverage. These are additive to /check Step 0.9 and prevent
  the classes of problems that cause the most user-facing pain.
relations:
  - target: wiki/concepts/code-verification-pipeline-gaps.md
    type: extends
  - target: wiki/concepts/dead-code-detection-workflow.md
    type: complements
  - target: wiki/concepts/auto-test-stop-hooks-and-property-based-testing.md
    type: complements
  - target: wiki/concepts/automated-code-quality-enforcement.md
    type: extends
  - target: wiki/concepts/textual-tui-pitfall-checklist.md
    type: related
---

# SDLC proactive prevention techniques beyond our current pipeline

## Decision context

**Why this research was needed:** after wiring trace_check.py and pylint into
`/check` Step 0.9, the operator asked: what ELSE do people do to proactively
prevent problems in their SDLC? The goal is to prevent the classes of bugs
that cause user-facing pain — the "user swearing at the computer" problem.

**What this research changed:** identifies 6 concrete gaps in our pipeline
that map to specific AI-agent failure modes, with tiered recommendations
for wiring them into `/check` and `/review`.

## Our current pipeline (5 layers)

| Layer | Tool | What it catches | Status |
|-------|------|----------------|--------|
| Fast lint | ruff E,F | syntax, undefined names, unused imports | ✅ Active |
| Type checking | pyright | type errors, undefined attributes | ✅ Active (cross-workspace fixed) |
| Deep inference | pylint --errors-only | E1101 no-member, import errors | ✅ Active |
| Definition completeness | trace_check.py | called-but-undefined `self.*` methods | ✅ Active |
| Dead code | vulture | unused functions/methods/classes | ✅ Advisory |
| AI review | /review specialists | logic, context, cross-file | ✅ Active |
| Runtime test | pytest | behavior verification | ✅ Active |

## The gaps — what we DON'T have

### Gap 1: Security scanning (bandit / semgrep) — HIGHEST ROI

We have **zero security scanning**. AI agents write code with `shell=True`,
`eval()`, `subprocess` with user input, `pickle.loads()` on untrusted data,
hardcoded passwords, and weak crypto (`random` instead of `secrets`).

**Bandit** (`pip install bandit`) catches all of these in <5s with zero config:
```bash
bandit -r <files> -ll -x tests/  # -ll = low severity, -x = exclude tests
```

**Semgrep** adds framework-aware patterns (Django SQL injection, Flask XSS):
```bash
semgrep scan --config p/python --config p/owasp-top-ten
```

**Practitioner signal [PRACTITIONER]:** Reddit r/Python consensus: bandit is
the minimum SAST floor for Python. ExperiencedDevs: "you'd be surprised how
many production incidents come from the exact patterns bandit flags."

**Recommendation:** add `bandit -ll` to `/check` Step 0.9 as a 6th deterministic
layer. Advisory first; if FP rate is manageable, promote to blocking. Semgrep
in CI/pre-push, not per-turn (slower, needs ruleset download).

**Host invariant check:** bandit runs offline, pure Python, no network. ✅

### Gap 2: Complexity analysis (radon) — HIGH ROI

We have **zero complexity gating**. AI agents produce overly complex functions
that become unmaintainable bug magnets. The `_copy_with_progress` method in KSC
hit 15+ cyclomatic complexity before refactoring.

**radon** (`pip install radon`) computes cyclomatic complexity, Halstead metrics,
and maintainability index:
```bash
radon cc -s -n C <files>  # -n C = only show complexity grade C or worse (>10)
```

**Recommendation:** add `radon cc -n C` to `/check` Step 0.9 as advisory.
Functions above complexity 10 get flagged for the verifier to spot-check.
This catches the "the agent added one more if/else and now nobody can
reason about this function" pattern.

### Gap 3: Dependency auditing (pip-audit) — HIGH ROI

We have **zero dependency vulnerability scanning**. AI agents add dependencies
freely (`pip install` as part of "make it work") without checking CVEs.

**pip-audit** (`pip install pip-audit`) checks installed packages against the
PyPA Advisory Database:
```bash
pip-audit -r requirements.txt  # or scan current environment
```

**Recommendation:** add to `/check` Step 0.9 as advisory when a
`requirements.txt` or `pyproject.toml` is in scope. Not blocking (too many
transitive false positives), but surface as `dependency_advisory` for the
verifier. Could be blocking in a pre-push hook.

**Host invariant check:** pip-audit requires PyPI API access (network). Run in
`/check` (execute mode), NOT in Stop hooks (which need to be fast/offline). ✅

### Gap 4: New-line coverage gating (diff-cover) — MEDIUM-HIGH ROI

We have **zero coverage gating**. Tests exist (17 in KSC, 6+ in trace_check),
but we never gate on whether new/changed lines are tested. The `_mark_row`
incident: 5 callers of a deleted method, none exercised by tests.

**diff-cover** (`pip install diff-cover`) gates coverage on only the diff:
```bash
pytest --cov=<pkg> --cov-report=xml
diff-cover coverage.xml --fail-under=80  # only new/changed lines
```

**Why diff-cover over --cov-fail-under:** diff-cover only requires coverage on
NEW or MODIFIED lines. This prevents coverage backsliding without forcing an
immediate catch-up on all legacy uncovered code. The gate is achievable from
day one.

**Recommendation:** add to `/check` Step 0.9 when `--cov` output is available.
Wire diff-cover as advisory first; promote to blocking once baseline is set.

### Gap 5: Import cycle detection (pylint R0401) — MEDIUM ROI

We run `pylint --errors-only`, which **suppresses R0401 (cyclic-import)**
because it's a refactoring check, not an error. AI agents frequently create
import cycles when reorganizing modules or adding cross-imports.

**Fix:** extend our pylint invocation:
```bash
pylint --errors-only --enable=cyclic-import <files>
```

**Recommendation:** add `--enable=cyclic-import` to the existing pylint layer
in `/check` Step 0.9. Zero additional tooling — just a flag change.

### Gap 6: Branch coverage (--cov-branch) — MEDIUM ROI

We run pytest but **without branch coverage**. Line coverage hides untested
`except` blocks — the exact pattern where AI-agent bugs hide. The KSC atomic
copy failure path (`except Exception` cleanup) was never tested until it
failed at runtime.

```bash
pytest --cov=<pkg> --cov-branch --cov-report=term-missing
```

**Recommendation:** add `--cov-branch` to test runs in `/check`. Surface
uncovered branches as `coverage_gaps` in the evidence packet for the verifier.

## Runtime type checking (beartype) — APPLICATION-LEVEL, NOT SKILL-LEVEL

**beartype** adds O(1) ~1μs runtime type checking to every annotated function
via a single import in `__init__.py`:
```python
from beartype import beartype; beartype_this_package()
```

**Why this is Tier 2 (not /check):** beartype is a code-level decision per
package, not a fleet-wide deterministic check. It catches type errors pyright
misses (dynamic dispatch, runtime values from JSON/files). Recommend for KSC
and skill scripts that parse external data, but it's not a `/check` layer.

**Host invariant check:** zero-cost overhead claim from the library author.
[INFERENCE] — not measured on our codebase. Test on one package before
fleet-wide adoption.

## What NOT to add (overkill for our fleet)

| Technique | Why not |
|-----------|---------|
| **Pact contract testing** | We don't have microservices with consumer/provider splits |
| **Atheris fuzzing** | High effort, narrow payoff for our code types (TUI apps, skill scripts) |
| **OSS-Fuzz** | We're not an OSS project with critical parsers |
| **Schemathesis** | We don't have REST APIs to fuzz |
| **Commitizen** | We have auto-commit; conventional commits are nice-to-have, not prevention |
| **Golden Master for legacy** | We don't have enough legacy to justify the setup cost |

## Disconfirmation pass

**Evidence AGAINST adding more checks:**
- False positive fatigue: if bandit/radon produce >5 FPs per run, operators
  learn to ignore them. Mitigation: `bandit -ll` (low-only), `radon -n C`
  (complexity C+), advisory-first promotion path.
- Pipeline latency: each layer adds 2-5s. Current 5-layer pre-check takes
  ~10-15s. Adding 3 more (bandit + radon + pip-audit) adds ~10-15s. Total
  ~25-30s — acceptable given it replaces 200-350s of LLM verifier time.
- Pylint --errors-only + --enable=cyclic-import: R0401 can false-positive on
  lazy imports (import inside function). This is a known pylint limitation;
  the false positive is acceptable as a spot-check prompt.

**Disconfirmation result:** no refuting evidence found. The techniques are
standard Python ecosystem practice. The risk is in FP management, not in
the techniques themselves.

**Wiki contradiction check:** existing [[code-verification-pipeline-gaps]]
recommends "no new skill needed, improve deterministic layers." This concept
extends that recommendation with 6 more deterministic layers — consistent,
not contradictory.

## Host invariant check (Round 3.5)

| Recommended technique | Network? | Writes state? | Multi-agent safe? |
|----------------------|----------|---------------|-------------------|
| bandit -ll | No | No | ✅ Read-only on changed files |
| radon cc -n C | No | No | ✅ Read-only |
| pip-audit | Yes (PyPI) | No | ✅ Read-only (run in /check, not Stop hook) |
| diff-cover | No | No | ✅ Read-only (reads coverage.xml + git diff) |
| pylint --enable=cyclic-import | No | No | ✅ Read-only |
| --cov-branch | No | Writes coverage.xml | ✅ Per-run-dir artifact |

No host invariant violations. All tools run on changed files only, produce
no shared state, and don't conflict with concurrent sessions.

## Recommended implementation tiers

### Tier 1 — wire into /check Step 0.9 NOW (highest ROI, lowest effort)

| # | Technique | Command | Effort | Prevents |
|---|-----------|---------|--------|----------|
| 1 | Security scan | `bandit -r @pyFiles -ll -x tests/` | 1 layer in Step 0.9 | shell=True, eval, weak crypto, hardcoded secrets |
| 2 | Complexity | `radon cc -s -n C @pyFiles` | 1 layer in Step 0.9 | unmaintainable functions, bug magnets |
| 3 | Import cycles | add `--enable=cyclic-import` to pylint | 1 flag change | circular imports from agent reorgs |

### Tier 2 — wire into /check Step 0.9 as advisory (medium effort)

| # | Technique | Command | Effort | Prevents |
|---|-----------|---------|--------|----------|
| 4 | Dep auditing | `pip-audit -r requirements.txt` | 1 layer (conditional on req file in scope) | vulnerable dependencies |
| 5 | Coverage gate | `diff-cover coverage.xml --fail-under=80` | Requires --cov wiring | untested changes |
| 6 | Branch coverage | add `--cov-branch` to pytest | 1 flag change | untested error paths |

### Tier 3 — application-level (per-package, not fleet-wide)

| # | Technique | Where | Prevents |
|---|-----------|-------|----------|
| 7 | beartype | package __init__.py | runtime type errors |
| 8 | Pydantic validation | config I/O boundaries | config drift, schema violations |
| 9 | syrupy snapshots | TUI app tests | visual/output regressions |

## What this means for /check, /review, /refactor, /go

| Skill | Change | Priority |
|-------|--------|----------|
| `/check` Step 0.9 | Add bandit + radon + cyclic-import (Tier 1) | **NOW** |
| `/check` Step 0.9 | Add pip-audit + diff-cover + --cov-branch (Tier 2) | Next session |
| `/check` Step 0.9 layers table | Expand from 5 to 8-11 layers | With Tier 1 |
| `/review` specialist prompts | Add "check security (bandit), complexity (radon)" | With Tier 1 |
| `/refactor` seam close gate | Add complexity check (don't increase CC) | With Tier 1 |
| `/go` | No change — delegates to /check + /review | — |

## Falsifier

This concept is wrong if:
- bandit produces >5 FPs per run on our codebase → drop to `-l` (low-only)
  or skip and use Semgrep with a custom ruleset instead
- radon CC threshold of C (10) is too low → adjust to B (5) or D (15)
- pip-audit has too many transitive false positives → gate to direct deps only
- diff-cover can't parse our multi-root git structure → fall back to
  `--cov-fail-under` with a per-package threshold
- The added pipeline latency (>25s total) makes /check feel slow → profile
  and parallelize the deterministic layers (they're independent)

## Sources

- [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) — repo hygiene hooks
- [Bandit](https://bandit.readthedocs.io/) — Python SAST
- [Semgrep](https://semgrep.dev/) — multi-language SAST with custom rules
- [radon](https://github.com/radon-project/radon) — complexity metrics
- [coverage.py](https://github.com/nedbat/coveragepy) — branch coverage
- [diff-cover](https://github.com/pycqa/diff-cover) — diff-scoped coverage gate
- [beartype](https://github.com/beartype/beartype) — runtime type checking
- [pip-audit](https://pypi.org/project/pip-audit/) — dependency vulnerability scanning
- [syrupy](https://syrupy.readthedocs.io/) — snapshot testing
- [pylint cyclic-import](https://pylint.readthedocs.io/en/latest/messages/refactor/cyclic-import.html) — R0401
- Reddit r/Python, r/ExperiencedDevs — practitioner consensus on prevention stack

## Related

- [[code-verification-pipeline-gaps]] — the original tool-to-bug-class map this extends
- [[dead-code-detection-workflow]] — vulture (already wired)
- [[auto-test-stop-hooks-and-property-based-testing]] — PBT + mutation testing (documented, not wired)
- [[automated-code-quality-enforcement]] — broader enforcement patterns
- [[textual-tui-pitfall-checklist]] — framework-specific prevention
