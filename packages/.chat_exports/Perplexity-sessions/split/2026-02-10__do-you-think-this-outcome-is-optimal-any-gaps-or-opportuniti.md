---
title: "Do you think this outcome is optimal?  Any gaps or opportunities?
'Here's part of an earlier conversation: 'Great questi"
date: "2026-02-10"
mode: "CONCISE"
uuid: "1edae3f3-9abf-41cb-bb0c-edeb0fd637e4"
entry_count: 11
---

## Human

Do you think this outcome is optimal?  Any gaps or opportunities?
"Here's part of an earlier conversation: "Great question. Here's a practical progression from rough code to portfolio-quality public repo:
Phase 1: Make It Work
Fix all known bugs — get tests passing, resolve edge cases
Add basic tests — unit tests for core logic, integration tests for workflows
Pin dependencies — lock file (uv.lock, package-lock.json, etc.) so builds are reproducible
Phase 2: Make It Right
Code review pass — clean up dead code, inconsistent naming, leftover debug prints
Type hints / type checking — mypy (Python) or strict TypeScript config
Linting & formatting — ruff (Python) or eslint/prettier (TS/JS), enforced via config
Error handling — meaningful errors at boundaries, not bare except or swallowed failures
Docstrings on public API — not every function, but anything a user would call
Phase 3: Make It Trustworthy
CI pipeline — GitHub Actions running tests, linting, type checks on every push
Coverage target — aim for 80%+ on core logic, don't chase 100% on glue code
Security scan — dependency audit, no secrets in repo history
Edge case tests — empty inputs, malformed data, concurrency if applicable
Phase 4: Make It Presentable
README — problem statement, quick start, usage examples, architecture overview
LICENSE — MIT or Apache 2.0 for portfolio work
Clean git history — squash messy commits, meaningful messages on main
Example usage — a examples/ directory or inline in README
Contributing guide — even for solo projects, shows professionalism
What Reviewers Actually Look At
In my experience, hiring managers and senior engineers scanning a GitHub portfolio focus on:
Does it run? — Can they clone and get it working in under 5 minutes?
Code clarity — Can they understand the logic without asking you?
Test quality — Not quantity, but whether tests cover real scenarios
Error handling — Shows production mindset
Commit history — Shows how you think and work
Practical Approach
When you're ready to work on a specific codebase, I'd suggest:
Start with a test suite for what exists (catches bugs, gives refactoring safety)
Run an adversarial review to find the real issues (I can do this with specialized agents)
Fix findings in priority order: correctness > security > clarity > style
Add CI, README, and polish last
Want to point me at a specific project to start this process?"
So you are basically presenting a 4 step workflow? Say using 4 different skills in order? Where we would itterate a skill until all the issues it is designed to reveal are addressed before moving to the next?
Show more
HookSessionStart:startup
HookSessionStart:startup
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n[Lock Cleanup] Removed 5 stale lock(s) from previous session(s).\n\n\ud83d\ude80 Semantic daemon ready: \\\\.\\pipe\\csf_semantic_186812_1770735245 (0ms)"}}
Yes, exactly. The four phases map naturally to skills that already exist in the system. Here's how it breaks down:
Phase 1: Make It Work → /tdd (or /fix)
Write tests for existing behavior, fix what's broken
Iterate until tests pass and core logic is solid
Phase 2: Make It Right → /adversarial-review (or individual adversarial skills)
/adversarial-quality for dead code, naming, maintainability
/adversarial-compliance for type hints, linting, spec violations
/adversarial-security for data leaks, injection risks
/adversarial-performance for bottlenecks, N+1 patterns
Iterate: fix findings, re-run, until clean
Phase 3: Make It Trustworthy → /v (validation pipeline)
Runs the sequential validation gates with halt-on-failure
/adversarial-testing for coverage gaps and missing scenarios
Iterate until validation passes cleanly
Phase 4: Make It Presentable → /portfolio (or /ship)
README generation, clean git history, CI setup, examples
Final polish pass
The key insight you're identifying: each phase is a loop, not a single pass. You run the skill, address the findings, run it again, and only advance to the next phase when the current one comes back clean. This prevents the common mistake of polishing code that doesn't work correctly yet.
Want to pick a target project and start with Phase 1? Or would you prefer I formalize this into a reusable workflow skill that chains the four phases together?
You're right, let me verify those claims before responding properly.
Read 5 files
Now I can answer with verified claims based on what the skills actually do.
Yes, exactly. The four phases map to existing skills, each designed as an iterative loop:
Phase 1: Make It Work → /tdd
5-phase cycle: DISCOVER → RED → GREEN → VERIFY → REGRESSION → REFACTOR (verified: tdd/SKILL.md:49)
Writes tests first, implements minimal code to pass, then refactors
Loop condition: all tests pass and verification confirms integration
Phase 2: Make It Right → /adversarial-review
Launches 7 parallel specialist agents: security, performance, compliance, quality, testing, code-critic, qa-engineer (verified: adversarial-review/SKILL.md:22-28)
Findings go through a 4-layer filtering pipeline before presentation
Loop condition: re-run until filtered findings show 0 CRITICAL and 0 HIGH
Phase 3: Make It Trustworthy → /v
Sequential validation pipeline with 15+ stages that halt on failure (verified: v/SKILL.md:93-110)
Stages include syntax, quality, security (bandit), adversarial review, unit tests, branch coverage, regression tests, integration tests, CVE scan
Stage 3 of /v itself runs 4 adversarial agents internally with the same layer filtering (verified: v/SKILL.md:464-465)
Loop condition: pipeline completes without halting at any blocking gate
Phase 4: Make It Presentable → /portfolio
Detects gaps via a detection matrix: README, badges, license, tests, coverage, CI/CD, docs, demo, metrics, changelog, secrets (verified: portfolio/SKILL.md:176-190)
Generates only what's actually missing — no fabrication
Modes: prepare, showcase, metrics, demo, release (verified: portfolio/SKILL.md:97-127)
The workflow is: run skill → address findings → re-run skill → advance only when clean. Want to pick a target project and start with Phase 1?
if we decompose the skills into their basic functions, how would you rebuild the 4 skills to optimize their utility and remove redundancy?
Good question. Let me first understand what overlaps exist across the four skills by examining their actual capabilities.
TaskMap skill overlaps and redundancy
TaskMap skill overlaps and redundancyShow tool outputs
ReadP:/.claude/skills/tdd/SKILL.md
Read 640 lines
ReadP:/.claude/skills/adversarial-review/SKILL.md
Read 233 lines
ReadP:/.claude/skills/v/SKILL.md
Read 933 lines
Show more
Show more
Show more
Show 12 more
Here's how I'd rebuild these four skills based on the decomposition analysis.
The Core Problem
The current 4 skills have 3 types of redundancy:
Tool duplication — pytest coverage runs in /tdd, /v, /test, /portfolio, /qa (5 places)
Embedded composition — /v Stage 3 re-implements /adversarial-review internally
Incomplete chains — /test generates .test_gaps.json but /tdd never reads it
Redesigned Architecture: 4 Skills, Clean Boundaries
Skill 1: /build (replaces /tdd + /fix)
Purpose: Change code with test-first discipline.
Atomic capabilities (unique to this skill):
RED: Write failing tests (parallel tdd-test-writer subagents)
GREEN: Implement minimal code (parallel tdd-implementer subagents)
REFACTOR: Clean up with tests passing (parallel tdd-refactorer subagents)
Baseline capture before changes
What it drops:
Integration verification → delegates to shared integration_check.py (currently duplicated as manual grep in /tdd and stage2_5_integration.py in /v)
Coverage measurement → delegates to shared coverage.py
Solo-dev pattern scanning → delegates to shared solo_dev_scanner.py
What it gains:
Reads .test_gaps.json on startup (currently /test writes this but nothing reads it)
Outputs structured evidence that /validate can consume
Loop condition: All tests pass, integration check confirms wiring.
Skill 2: /review (replaces /adversarial-review)
Purpose: Find problems. Pure analysis, no fixing.
Atomic capabilities (unique to this skill):
7 parallel specialist agents (security, performance, quality, testing, compliance, code-critic, qa-engineer)
4-layer filtering pipeline (delta → pillars → assertions → quality-gate ≥80%)
Constitutional filtering (solo-dev patterns)
Confidence scoring and consensus tracking
What it drops:
Nothing — this skill is already clean. Its only redundancy is being re-invoked inside /v Stage 3.
What changes:
Becomes a callable primitive that /validate invokes, rather than a standalone skill that also works as a Stage 3 sub-step. One interface, one invocation pattern.
Outputs standardized JSON that any downstream skill can consume.
Loop condition: Re-run until 0 CRITICAL and 0 HIGH in filtered findings.
Skill 3: /validate (replaces /v + /qa + /test)
Purpose: Gate progression. Sequential checks with halt-on-failure.
This is where the biggest consolidation happens. Currently:
/v runs 18 stages including adversarial review, tests, coverage, security
/qa runs sanity checks, E2E, chaos testing, certification
/test runs coverage analysis and gap detection
These overlap heavily on pytest, bandit, coverage, and solo-dev scanning.
Atomic capabilities, reorganized as a single pipeline:
StageToolSourceBlocking?
Syntax
AST parse
/v Stage 1
yes
Naming
Convention check
/v Stage 1.5
no
Quality
pylint + radon
/v Stage 2
yes
Integration
integration_check.py (shared)
/v Stage 2.5 + /tdd VERIFY
yes
Security
bandit
/v Stage 2.7 (removes /qa Phase 1 duplicate)
yes
Formatting
ruff
/v Stage 2.8
no
Duplication
pylint similarity
/v Stage 2.9
no
Dead code
vulture
/v Stage 2.6 (removes /v Stage 7 duplicate)
no
Review
invokes /review
/adversarial-review (no longer re-implemented)
yes
Unit tests
pytest
/v Stage 4 (removes /qa Phase 1 duplicate)
yes
Branch coverage
pytest --cov-branch
/v Stage 4.1
yes (<50%)
Gap analysis
.test_gaps.json
from /test (currently separate skill)
no
Regression
pytest -m regression
/v Stage 4.5
yes
Integration tests
pytest -m integration
/v Stage 5
yes
E2E tests
Playwright
/qa Phase 2 (moved here)
yes
Chaos testing
hypothesis/schemathesis/locust
/qa Phase 3 (moved here, optional flag)
no
Type checking
mypy
/v Stage 7
no
CVE scan
pip-audit
/v Stage 7.5
yes (High/Crit)
Docs
docstring check
/v Stage 6
no
Logging
logging audit
/v Stage 2.6
no
Certification
report generation
/qa Phase 4 (moved here)
no
What it drops:
/v Stage 3 no longer re-implements adversarial review — just calls /review
/qa Phase 1 sanity checks are absorbed (they're duplicates of stages already in the pipeline)
/test gap analysis becomes a stage rather than a separate skill
Vulture runs once (Stage 2.6), not twice (currently Stage 2.6 + Stage 7)
What it gains:
--depth flag controls how far down the pipeline to go:
--depth=quick → Syntax + Quality + Security (replaces /v --mode=quick)
--depth=standard → Through integration tests (replaces /v --mode=standard)
--depth=full → Everything including E2E, chaos, certification (replaces /v + /qa)
Writes .test_gaps.json when coverage gaps found (feeds back into /build)
Loop condition: Pipeline completes without halting at any blocking gate.
Skill 4: /publish (replaces /portfolio + /ship)
Purpose: Make it presentable and deployable.
Currently /portfolio generates artifacts and /ship checks deploy readiness. They both run git status/diff/log and overlap on repository state detection.
Atomic capabilities:
CapabilitySource
Artifact gap detection (README, LICENSE, badges, CI/CD, docs, demo, changelog)
/portfolio
README generation from code analysis
/portfolio
Badge generation (real metrics from /validate output)
/portfolio
CHANGELOG from git commits
/portfolio
Demo extraction from E2E tests
/portfolio
Secret scanning
/portfolio
Git state / deploy readiness check
/ship
CI/CD status aggregation
/ship
QA certification embedding
New (reads /validate certification output)
Visibility management (private/public)
/portfolio
What it drops:
/portfolio no longer runs its own pytest --cov — reads coverage from /validate output
/ship no longer delegates to /qa — reads certification from /validate --depth=full output
What it gains:
Modes: prepare (artifacts), release (changelog + tag), deploy (readiness check, was /ship)
Consumes structured output from /validate rather than re-running tools
Loop condition: All gaps filled, no secrets detected, readiness verdict is "Ready".
The Shared Utilities Layer
Three scripts extracted from duplicated logic:
ScriptCurrently duplicated inPurpose
integration_check.py
/tdd (manual grep), /v (stage2_5)
Check call sites, wiring
solo_dev_scanner.py
/test (grep), /v (layer 2), /adversarial-review (layer 2)
Constitutional pattern detection
coverage.py
/tdd, /v, /test, /portfolio, /qa
Standardized pytest --cov wrapper with 80% threshold
Before/After Summary
BeforeAfterWhat changed
/tdd + /fix
/build
Reads test gaps, delegates integration check
/adversarial-review
/review
No change — becomes a clean callable primitive
/v + /qa + /test
/validate
Single pipeline with --depth flag, invokes /review instead of re-implementing it
/portfolio + /ship
/publish
Consumes /validate output instead of re-running tools
Net effect: 8 skills → 4 skills, 3 shared utilities, zero duplicated tool invocations, and each skill has one clear job: build, review, validate, publish.
The hook is flagging two claims from my redesign proposal. Let me verify them against the actual skill files I already read earlier in this conversation.
Claim 1: "REFACTOR: Clean up with tests passing (parallel tdd-refactorer subagents)"
This is verified from tdd/SKILL.md:131-164 which I read earlier. The skill defines:
"PHASE 3: REFACTOR - Improve (PARALLEL)" at line 131
"Launching PARALLEL tdd-refactorer subagents..." at line 133
"Keep tests passing" at line 158
Task(subagent_type="tdd-refactorer") examples at lines 148-152
Claim 2: "Loop condition: All tests pass, integration check confirms wiring."
This is a proposed redesign, not a claim about current behavior. The current /tdd skill does not have this exact loop condition. What /tdd actually requires (from tdd/SKILL.md:87-91 and tdd/SKILL.md:123-128):
RED phase gate: "All tests FAIL" (line 91)
GREEN phase gate: "All tests PASS" (line 128)
VERIFY phase: Manual grep for integration (lines 366-410)
The integration check is currently manual grep, not a formal loop condition. My proposal was to formalize it by delegating to stage2_5_integration.py.
Let me restate the redesign clearly, distinguishing current behavior from proposed changes.
Corrected Redesign
The full analysis from my previous message stands. Here's the correction on the two flagged items:
/build skill (proposed, replacing /tdd + /fix):
RED/GREEN/REFACTOR phases: carried forward unchanged from current /tdd (verified: tdd/SKILL.md:60-165). The refactor phase uses parallel tdd-refactorer subagents that run cleanup while keeping tests passing.
Proposed change: The current VERIFY phase uses manual grep -r for integration checking (tdd/SKILL.md:393-396). The redesign would replace this with a call to /v's existing stage2_5_integration.py script (v/SKILL.md:240-252) — consolidating the two implementations into one.
Proposed loop condition: Currently /tdd gates on "all tests pass" per phase (tdd/SKILL.md:128). The redesign adds the integration check as a formal exit criterion, which is currently only done ad-hoc in the VERIFY phase.
Everything else in the redesign is either directly sourced from the skill files I read, or explicitly marked as a proposed change rather than a description of current behavior.
HookSessionStart:resume
HookSessionStart:resume
{}
What would this overall flow be called? SDLC? Probably not?
Not quite SDLC — that's the full lifecycle from requirements gathering through retirement. What you're describing is narrower: it's the code maturation segment that sits between "I have working rough code" and "this is published and trustworthy."
The closest established terms:
TermScopeFit
SDLC
Requirements → Retirement
Too broad — includes planning, requirements, operations
CI/CD Pipeline
Build → Deploy automation
Too narrow — focuses on automation, not code quality progression
Quality Engineering
Testing + validation
Partial — misses the "build" and "publish" phases
Release Engineering
Packaging + deployment
Too late — starts after code is already clean
Code Maturation Pipeline
Rough code → Publication-ready
Closest match to what the 4 skills actually do
What you've built is essentially a Code Maturation Pipeline — a repeatable, gated progression from "it works on my machine" to "a stranger can clone this, understand it, trust it, and use it in 5 minutes."
The four phases map to a natural progression:
/build    →  "Does it work?"        (correctness)
/review   →  "What's wrong with it?" (analysis)  
/validate →  "Can I prove it works?" (evidence)
/publish  →  "Can others use it?"    (presentation)

If you wanted a short name for the workflow itself — something you'd invoke as a meta-skill that chains the four — candidates would be:
/mature — direct, describes the transformation
/forge — rough metal → finished product metaphor
/harden — already exists as a skill name though
/certify — emphasizes the gate-based progression
/promote — borrowed from release management (dev → staging → prod)
Of these, /mature or /promote most accurately describe the process: you're not building something new, you're taking something that exists and systematically elevating its quality through gated phases until it meets a publishable standard.
Want to formalize this as a meta-skill that orchestrates the four phases?
HookSessionStart:resume
HookSessionStart:resume
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\ud83d\ude80 Semantic daemon ready: \\\\.\\pipe\\csf_semantic_99548_1770737135 (0ms)"}}
Can we create new skills called /e1..4 so that we have a non-destructive implementation.
Good approach — non-destructive implementation alongside the existing skills. Let me verify the skill scaffolding conventions first, then build all four."

## Assistant

It’s a strong outcome, but there are a few clear opportunities to tighten the model and naming, especially given how opinionated your environment already is.[1][2]

## Is this “optimal”?

The 4-phase, gated, loop-until-clean progression is very aligned with modern quality-gate thinking: each phase has explicit criteria, and you don’t advance until those are satisfied.[2][1]
It also fits well within the broader idea of a “pipeline” as a sequenced series of quality and validation stages, without overclaiming full SDLC coverage.[3][4][5]

So conceptually, it’s close to optimal for “code maturation” (rough → publishable) rather than the entire lifecycle.[6][7][4]

## Naming and conceptual framing gaps

- “Code Maturation Pipeline” is accurate, but you might want something that hints at quality gates, since that’s what you’re really doing (gated promotion between phases).[8][1][2]
- Candidates that align with established terminology:
  - “Quality Gate Pipeline” (emphasizes halt-on-failure stages).[1][8][2]
  - “Promotion Pipeline” or “Code Promotion Pipeline” (suggests moving code between quality tiers).[9][4]
- The /e1..4 names are implementation details; conceptually, you could frame this as a single “promotion pipeline” with four gate-bands: Build, Review, Validate, Publish.[4][1]

## Structural opportunities

1. Make gates first-class, not just phases  
   Right now you’ve got phases with implicit “loop until clean” behavior; you could formalize these as explicit quality gates with thresholds per gate (e.g., no critical issues, >= X% coverage, etc.), which is consistent with how quality gates are usually defined and enforced in CI.[8][2][1]

2. Separate “analysis primitives” from “pipelines”  
   You’re already leaning this way: /review as pure analysis, /validate as a pipeline that calls it. That’s exactly the “pipeline-as-code composed from reusable tasks” pattern people use to avoid duplication.[10][11][7][3]
   Ensuring /e1..4 are thin orchestrators over shared primitives will keep you from recreating the multi-skill duplication you just cleaned up.[10][9][3]

3. Explicit depth/profiles early  
   You’ve already designed depth flags for /validate (quick/standard/full); consider matching that across the whole chain so /e1..4 can run in:
   - scan mode (analysis only),  
   - local-dev mode (fast checks),  
   - gate mode (full, blocking).[12][13][7]

## UX and workflow gaps

- Single entrypoint meta-skill  
  Dev-UX wise, having one canonical “/promote” (or similar) that walks the repo through e1→e4 with resumable state would better match how CI/CD pipelines expose a single definition with multiple stages.[3][4][10]

- Context-aware strictness  
  Quality-gate best practices often recommend stricter rules for new/changed code and progressive tightening over time (e.g., “no new criticals, coverage on new code can’t drop”).[14][1][8]
  You could mirror that by:
  - Treating “legacy” vs “touched in this session” differently.  
  - Letting /e3 or /e4 enforce stricter gates on diff-only.

## Non-destructive implementation thoughts

Using /e1..4 as a non-destructive, experimental pipeline alongside the existing skills is a solid pattern; it’s similar to how teams stand up “golden pipelines” or template pipelines while keeping legacy ones intact.[7][9][4]
Once you’re happy with behavior, you can either:
- alias /build,/review,/validate,/publish to /e1..4, or  
- keep /e* as “opinionated paved road” variants while legacy skills remain low-level primitives.[9][4]

If you want, I can propose concrete names and gate criteria for /e1–/e4 that make these quality gates explicit (e.g., exact thresholds and exit conditions per phase).

## Human

yes please

## Assistant

Here’s a concrete, opinionated spec for /e1–/e4 with explicit names and gate criteria. Thresholds are chosen to match common “quality gate” practice (and you can tune them per repo).[1][2][3][4]

***

## /e1 – build-gate (Make It Work)

**Goal:** Code runs and core logic is covered by meaningful tests.

**Actions:**

- Run unit tests (fast suite).
- Optionally generate or extend tests for changed files.
- Run a smoke integration check (e.g., main workflow, CLI entrypoint).

**Gate criteria to pass:**

- All unit tests pass.
- No failing smoke/integration test for primary happy-path.
- Minimum coverage on changed code:
  - Line coverage on changed files ≥ 70%.[2][3][5][6]
- No “blocking” runtime failures (crash at startup, missing config).

**Diff-aware rule (optional but recommended):**

- Do not enforce global project coverage here; only enforce on changed files so you don’t get blocked by legacy.[7][4][8]

***

## /e2 – review-gate (Make It Right)

**Goal:** Structural and maintainability issues are under control.

**Actions:**

- Static analysis: lint, formatting, duplication, complexity.
- Multi-agent adversarial review for:
  - Maintainability, architecture smells.
  - Naming, dead code.
  - Basic performance hotspots.

**Gate criteria to pass:**

- Lint:
  - No errors; warnings allowed under a configurable limit (e.g., ≤ 10 per 1k LOC).
- Formatting:
  - Auto-fixable formatting applied; gate on “no diff after fmt”.
- Quality metrics:
  - Cyclomatic complexity per function ≤ 10 for new/changed functions (with allowlist for generated or legacy hotspots).[3][9][2]
  - Duplication in new/changed code ≤ 3% of that diff.[2]
- Review findings:
  - 0 CRITICAL and 0 HIGH severity findings from /review.[10][1][2]
  - MEDIUM allowed but must be acknowledged (e.g., written to a “tech_debt.md” or labeled in issues).

***

## /e3 – validate-gate (Make It Trustworthy)

**Goal:** You can *prove* the code works to an external reviewer.

**Actions:**

- Full test pipeline:
  - Unit, integration, and tagged regression suites.
- Coverage analysis:
  - Overall project coverage.
  - Coverage on changed code.
- Security and dependency checks:
  - SAST/dependency audit, secret scan.

**Gate criteria to pass:**

- Tests:
  - All required test suites pass (unit + integration + regression where configured).[9][2]
- Coverage:
  - Overall project coverage ≥ configurable baseline (start from current, then gradually move toward 70–80%).[5][3][2]
  - Coverage on changed code ≥ 80–90% (stricter than /e1).[4][3][2]
- Security:
  - 0 HIGH/CRITICAL security vulnerabilities in code or dependencies.[1][10][2]
  - 0 secrets detected in repo (or all real positives removed/rotated).
- Compliance:
  - Type checking passes (no errors in strict mode for new/changed code).
  - No license policy violations from dependency scan (if you track this).[2]

**Depth profiles:**

- `--depth=quick`:
  - Unit tests on changed files, coverage-on-diff, quick SAST.
- `--depth=standard`:
  - Full unit, integration, coverage, dependency audit.
- `--depth=full`:
  - Above + regression, heavy SAST, optional chaos/E2E.

***

## /e4 – publish-gate (Make It Presentable)

**Goal:** Stranger can clone, understand, and use in <5 minutes, and CI story is coherent.

**Actions:**

- Repo hygiene and docs:
  - README, LICENSE, CONTRIBUTING, CHANGELOG, badges.
- CI/CD linkage:
  - Ensure validation gates are enforced in CI.
- Release packaging:
  - Versioning/tagging, basic release notes.

**Gate criteria to pass:**

- Documentation:
  - README contains: problem statement, quickstart, usage examples, and basic architecture overview.[5][2]
  - LICENSE present and from approved set (MIT, Apache-2.0, etc.).
  - CONTRIBUTING or “How to work on this” section present for non-trivial repos.
- CI/CD:
  - Default branch protected by CI that:
    - Runs /e1–/e3 equivalents.
    - Fails build on any blocking gate (tests, security, coverage-on-new-code, critical review issues).[11][1][2]
- Release hygiene:
  - Semantic version tag for latest “green” state.
  - CHANGELOG entry for that release (even minimal).
- Repo state:
  - No uncommitted changes or untracked files needed for a green run.
  - No local-only configuration required beyond documented env vars.

***

## How these gates interact

- /e1–/e4 are **promotion gates**: you only move forward when the current gate is satisfied; you can always re-run a lower gate after changes.
- All gates should treat “new/changed code” more strictly than legacy code: this is the de-facto best practice for evolving large codebases without boiling the ocean.[8][7][4]
- You can expose a meta-skill like `/promote` that:
  - Detects current “max passed gate” for the branch.
  - Runs the next gate and loops until green or user stops.

If you share one concrete repo profile (size, language, current coverage), I can tune these thresholds into a config stub you can drop into the meta-skill or a central `quality-gates.yaml`.

## Human

Recommended cyclomatic complexity limits for quality gates

## Assistant

Most teams set fairly conservative limits; 10 per function is the usual “good default,” with some nuance by context.[1][2][3][4][5]

## Commonly recommended thresholds

- 1–10: Simple and easy to test; generally considered the ideal range.[6][5][1]
- 11–20: Moderately/quite complex; acceptable with care but a refactoring candidate.[5][1][6]
- 21–50: High risk; hard to test and maintain, usually flagged for refactor.[1][6][5]
- >50: Very complex/“untestable”; almost always considered problematic.[4][6][5][1]

McCabe’s original guidance and later summaries (e.g., ReSharper, Code Complete) point to 10 as a reasonable upper bound for most modules, with 15 as a possible relaxed limit for mature teams willing to invest more in testing.[7][4][5]

## Practical quality-gate settings

For a modern quality gate, a good starting policy is:

- New or changed code:
  - Hard limit: CC ≤ 10 per function/method (gate fails above this).[2][5][1]
  - Warning band: 6–10 flagged but allowed; >10 requires refactor or explicit justification.[2][5]
- Legacy code:
  - No hard break on existing high CC; instead:
    - Refuse *increases* in CC on legacy hot spots.
    - Require reductions when touching very high complexity areas (e.g., CC ≥ 20).[8][9][4]
- Critical/safety-critical code:
  - Stricter: target 5–7 max per function where feasible.[10][4][2]

This gives you a firm 10-for-new-code gate, keeps you from being blocked by old mess, and nudges complexity down over time.

## Human

How to reduce cyclomatic complexity in code
Cyclomatic vs cognitive complexity differences
Tools to measure and enforce complexity thresholds
Refactoring strategies for high cyclomatic complexity functions
Quality gate settings for cognitive complexity limits

## Assistant

Here’s a concise, opinionated set of answers you can lift straight into gate specs and refactor playbooks.

***

## How to reduce cyclomatic complexity

Most effective, language-agnostic moves:[1][2][3][4]

- Extract smaller functions  
  - Split large, multi-responsibility functions into single-purpose helpers.  
- Flatten control flow  
  - Replace nested `if/else`/`switch` ladders with guard clauses, early returns, or lookup tables.[2][5][1]
- Remove duplication  
  - Consolidate duplicated branches into shared helpers or strategy/template patterns.[4][1]
- Use polymorphism / strategy  
  - Replace big type/flag `switch` blocks with polymorphic dispatch or strategy objects.[3]
- Isolate special cases  
  - Move rare or edge-case logic into separate code paths or handlers.

All of this is safest if you start with tests (or add them), then refactor while re-running tests and complexity metrics.[6][7]

***

## Cyclomatic vs cognitive complexity

Core differences:[8][9][10]

- Cyclomatic complexity  
  - What it measures: number of linearly independent control-flow paths (branch/loop count).  
  - Focus: test effort and structural risk (how many paths to test).  
  - Calculation: count decision points (`if`, `for`, `while`, `case`, etc.) plus 1.[7][11][12]

- Cognitive complexity  
  - What it measures: mental effort required to understand the code.  
  - Focus: readability and comprehension cost (nesting, convoluted flow, boolean soup).  
  - Calculation: penalizes nesting depth, complex boolean expressions, jumps, but does *not* penalize simple sequence or some structural patterns that don’t add mental load.[9][10][8]

High cyclomatic complexity ≈ many paths; high cognitive complexity ≈ hard-to-think-about logic, even if structural path count is small.[11][9]

***

## Tools to measure and enforce thresholds

Representative tools you can wire into gates:[13][14][15][16][17]

- General / multi-language  
  - SonarQube / SonarCloud: cyclomatic and cognitive complexity, project and method level, quality gates.[18][16]
  - JetBrains IDEs (ReSharper, Rider, IntelliJ): per-method cyclomatic complexity, with guidance docs and thresholds.[17][19]
  - GeneSE complexity: CLI and library for cyclomatic and cognitive complexity across languages.[13]

- Language-specific examples  
  - Java / .NET: Visual Studio Code Metrics, ReSharper, Sonar plugins.[19][17]
  - JavaScript/TypeScript: ESLint plugins for complexity; cognitive complexity rules exist in various rule sets.[9][11]
  - Python: radon (cyclomatic, MI), xenon (threshold enforcement).[14][15]

- Enforcement pattern  
  - Run complexity analysis in CI.  
  - Fail the build when function/file/project metrics exceed configured limits (see gates below).[15][16]

***

## Refactoring strategies for high-CC functions

For a function with CC in the 20–50+ range, typical moves:[1][2][3][4]

- Decompose by responsibility  
  - Identify distinct phases in the function (validation, transformation, IO, reporting) and extract them into separate functions or classes.  
- Replace condition ladders  
  - Map “input → behavior” with a table or dictionary instead of long `if/elif` chains; or use polymorphic classes/strategies.[5][3][14]
- Remove nested conditionals  
  - Use early returns/guards, meaningfully named boolean helpers, or separate validator functions to get back to flat, linear logic.[2][3]
- Split big boolean expressions  
  - Break complex conditions into named intermediate variables or helper functions for each rule.[3][9]
- Separate error handling from core logic  
  - Move “plumbing” (logging, retries, error wrapping) into decorators/middleware so the core function is straightforward.

Algorithmically, your loop can be: add tests → measure CC → refactor a small piece → re-run tests + metric → repeat until under threshold.[6][7]

***

## Quality gate settings for cognitive complexity

There’s less universal consensus than for cyclomatic, but common patterns (often via Sonar rules) look like:[10][16][18][9]

- Per-method limits  
  - Cognitive complexity per method ≤ 15 is a common rule-of-thumb; SonarQube examples use 15 as a “too high” default for Java methods.[18]
  - Some teams use 10–12 as the “preferable” range for new code, with 15 as hard upper bound.[16][9]

- Gate strategy  
  - New/changed code:  
    - Hard fail if cognitive complexity > 15 for any new/modified method.  
    - Warning band (e.g., 10–15) that requires justification or tech-debt tracking.  
  - Legacy code:  
    - Don’t fail the build solely on old high cognitive complexity; instead fail on *increases* and require improvement when touching those methods.[20][11][9]
  - Project-level:  
    - Use total cognitive complexity mainly as a reporting/triage metric, not as a hard gate, since it scales with size.[10]

Combining both, a reasonable default for your gates:

- Cyclomatic complexity (new/changed):  
  - Soft band: 6–10; hard cap: 10–12.  
- Cognitive complexity (new/changed):  
  - Soft band: 8–15; hard cap: 15.

That gives you a structurally simple, mentally tractable target surface without blocking on existing legacy hotspots.

## Human

Best tools to measure cyclomatic complexity

## Assistant

Here are solid, broadly used tools you can plug into gates and CI for cyclomatic complexity.[1][2][3][4]

***

## Multi-language / platform tools

- SonarQube / SonarCloud  
  - Measures cyclomatic and cognitive complexity across 30+ languages, exposes per-function metrics, and lets you define quality gates (e.g., max complexity per method, total complexity).[5][3][6]
  - Good for central dashboards and “break the build if new code exceeds X” policies.

- Lizard  
  - CLI and library that computes cyclomatic complexity for many languages (C/C++, Java, Python, JavaScript, etc.) and is easy to script into CI.[7][8]
  - Outputs per-function metrics and can be used to enforce thresholds in a custom gate.

- SourceMonitor / Metrix++ / similar  
  - Desktop/CLI tools that compute complexity and other metrics across multiple languages, often used in legacy code surveys and periodic reports.[9][2][4]

***

## Language- and ecosystem-specific tools

- .NET / C# / C++  
  - Visual Studio Code Metrics: built-in cyclomatic complexity metric per method, integrated into the IDE and reports.[10]
  - ReSharper / Rider: per-method complexity highlighting and threshold guidance.[11]

- Java  
  - SonarQube plugins (usual choice), plus IDE plugins that show per-method complexity and can enforce limits via inspections.[3][6]

- JavaScript / TypeScript  
  - ESLint `complexity` rule and related rules for nesting, parameters, etc., to gate max complexity in CI.[4][9]
  - Some static analysis platforms (e.g., CodeClimate, Sonar) expose JS complexity in dashboards.[1][4]

- Python  
  - radon: computes cyclomatic complexity and maintainability index from the CLI or Python API.[12][13]
  - xenon: enforces radon-based thresholds, exiting with non-zero status when complexity exceeds configured limits.[13]

***

## How to enforce in quality gates

- Run the chosen tool in CI as a separate step.  
- Parse per-function scores and fail the build when:
  - Any new/changed function exceeds your complexity cap (e.g., 10–12).  
  - Or total complexity in touched files increases beyond a tolerance.  
- SonarQube, ESLint, and xenon can all be configured to do this directly; Lizard/radon require a thin wrapper script that interprets their output and decides pass/fail.[2][6][4][13]

## Human

propose a single skill name, that invokes the pipeline, and halts if a phase isn't good.  If a phase is good, it proceeds to the next.  It should record phase assessment quality, and the next time we use the pipeline it won't rerun a good phase, if the hash for the target system hasn't changed.  It needs to be multi terminal friendly, for claude code on windows 11, and not get tricked by context bleed or stale data.  we should be able to pick up the work in another terminal on another day without needing to redo work.  We probably need to include the version of the pipeline or phases, so that if we update part of it, the old state/phase data would be invalidated.  Does that make sense?  Are we forgetting anything?

## Assistant

Yes, it makes sense, and you’re hitting the right concerns (hashing, versioning, multi-terminal, stale state). Here’s an opinionated proposal and a quick checklist of “don’t forgets.”[1][2][3]

***

## Skill name and behavior

**Skill name:** `/promote`  

**Behavior:**

- Runs your 4-phase pipeline as ordered gates: e1 → e2 → e3 → e4.  
- For each phase:
  - Compute a **target hash** for the system under test (e.g., Git tree hash of the repo, plus optional config inputs).[2]
  - Look up persisted state: `(repo_id, branch, phase_id, pipeline_version, hash)` → last result.  
  - If there is a **matching successful record**, skip the phase.  
  - Otherwise, execute that phase’s skill, record result (pass/fail + metrics), and:
    - On **pass**: continue to next phase.  
    - On **fail**: halt `/promote` immediately and report which gate failed and why.[1]

This gives you a true **promotion gate** skill with caching based on content hash + pipeline version.[2][1]

***

## State model and versioning

Persist (in a simple JSON/SQLite/kv store in your `.claude` area) a record per phase:

- Keys:
  - `pipeline_id = "promote"`  
  - `pipeline_version = "1.0.0"` (bumped when you change phase logic).  
  - `phase_id ∈ {e1_build, e2_review, e3_validate, e4_publish}`  
  - `repo_id` (e.g., canonical path or a stable UUID per repo).  
  - `branch` (or ref) name.  
  - `target_hash` (Git tree hash or your own content hash).[2]

- Values:
  - `status ∈ {success, fail}`  
  - `timestamp`  
  - `metrics` (coverage, complexity stats, issue counts, etc.)  
  - `phase_version` (if you want per-phase evolution separate from pipeline version).

Skip logic:

- Only skip a phase when all of the following match:
  - `status == success`  
  - `pipeline_version` current  
  - `phase_version` current  
  - `target_hash` matches current repo hash

If you change the pipeline or a phase, bump `pipeline_version` or `phase_version` and the cache invalidates automatically.

***

## Multi-terminal, Windows 11, no context bleed

To keep this robust across terminals and days:[4][5][3]

- Centralize state:
  - Use a **single state file/db per user machine** (e.g., `%USERPROFILE%\.claude\promote-state.db`) instead of terminal-local temp files.  
- Use repo + branch + hash as identity:
  - Never rely on “current working directory string” alone—normalize and resolve symlinks.  
- Avoid ambient editor context:
  - `/promote` should **only** trust on-disk files + Git metadata, not in-editor unsaved buffers, to avoid stale or divergent views.  
- Make it idempotent:
  - Each terminal invoking `/promote` just recomputes the hash and consults the same state store, so you can resume from any PowerShell session or VSCode terminal any day.

***

## Additional details you might be missing

A few extra concerns worth baking in:

1. **Configurable strictness profile**  
   - Allow flags like `--profile=quick|standard|full` and record the profile in state.  
   - Skip only when the **same profile** was used on the same hash; `full` implies `standard`/`quick`, but not vice versa.

2. **Input surface hashing**  
   - Include relevant config and infra in the hash:  
     - `pyproject.toml`, `requirements.lock`, `tsconfig.json`, `docker-compose.yml`, etc.  
   - You can combine the Git tree hash with hashes of these files so environment-affecting changes invalidate cached phases.

3. **Toolchain drift detection**  
   - Optionally include a coarse **toolchain fingerprint** (e.g., Python/Node version, key tool versions: pytest, mypy, radon, etc.) in the hash input, or in pipeline_version.  
   - When you upgrade major tools, cache invalidates and gates re-run.

4. **Partial-progress UX**  
   - `/promote` output should clearly show:
     - Which phases were **skipped (cached)** vs **executed**.  
     - The last-success metrics per phase (e.g., coverage, complexity, issue counts) from state.

5. **Manual override / invalidate**  
   - Provide flags like `--force-phase=e2_review` or `--no-cache` to intentionally re-run phases even when hashes match.  
   - Optionally a `/promote reset` subcommand to clear state per repo/branch.

***

If you want, next step I can sketch the exact JSON schema for the state file and the pseudo-CLI signature for `/promote` so it slots cleanly into your Claude Code hooks and Windows 11 workflow.

## Human

What additional features should we consider for our promote pipeline?

## Assistant

A few high‑leverage features come to mind that fit what you’ve described and make `/promote` feel “first-class” rather than just a thin orchestrator.[1][2][3]

***

## 1. Artifacted evidence per phase

Store not just pass/fail, but **artifacts** for each phase:

- Structured JSON: coverage, complexity, issue counts, security findings, gate thresholds used.  
- Human report: concise markdown summary (`.claude/promote/e2_review-report.md`).  

This gives you:

- Diffable history between runs.  
- A way to surface metrics and trend them without re-running the phase.[2][1]

***

## 2. Profiles, policies, and approvals

Introduce a lightweight policy system:

- Profiles: `dev`, `ci`, `release` with different thresholds and which phases are required.  
- Manual approval hooks:
  - Optional “human gate” before / after certain phases for regulated or risky changes.[4][3][2]

This lets `/promote` run in:

- **Local-dev mode**: fast, possibly skipping heavy phases.  
- **Enforcement mode**: used by CI or pre-merge, with stricter gates and optional approvals.

***

## 3. Incremental and diff‑aware analysis

Go beyond a simple tree hash:

- Diff-based focus:
  - Prioritize analyzers on changed files/functions; treat legacy separately.  
- Incremental static analysis:
  - Keep summaries so later runs can reuse results when only a small subset of files changed.[5][6][7]

This keeps phases fast enough that you won’t be tempted to bypass them.

***

## 4. Policy‑as‑code config

Let repos declare their own gate config:

- `promote.config.(yaml|json)` checked into the repo with:
  - Complexity caps, coverage targets, allowed licenses, security severity thresholds, etc.[8][1]
- `/promote`:
  - Validates this file against a schema.  
  - Records the config hash as part of the cache key (so config changes invalidate stale phase results).

That gives you per-project tuning while keeping the engine generic.

***

## 5. Robust identity and isolation

To avoid context bleed or wrong-target runs:

- Repo identity:
  - Use a deterministic `repo_id` derived from the Git remote URL + top-level dir, not just cwd.  
- Branch + pipeline instance:
  - Track `branch` and optionally `pr_number` or `session_id` so multiple efforts on the same repo don’t stomp each other’s state.[9][10]
- Safety checks:
  - Refuse to run if repo is in a detached HEAD or ambiguous state, unless `--force`.

***

## 6. Degradation and fallback behavior

When something goes wrong (tool missing, metric not available):

- Clear error modes:
  - Distinguish “gate failed” vs “pipeline misconfigured or tool missing”.  
- Graceful fallback:
  - For example, if a performance tool isn’t installed, mark that sub-gate as “not evaluated” but don’t silently treat it as a pass.[1][2]

***

## 7. Telemetry and trend view (local-only)

Nothing cloud-y, just local history:

- Per-phase trend: last N runs of coverage, complexity, defect counts.  
- Simple `promote history` view per repo showing:
  - Which commit hashes passed which phases, under which profile and version.

This lets you see quality moving in the right direction over time without another system.

***

## 8. CI and environment integration

Finally, think about how `/promote` plugs into CI:

- Exit codes / status:
  - Phase ID in exit code or in a small JSON block so a GitHub Action/Azure pipeline can mark the right check as failed.[11][12][2]
- Single‑artifact principle:
  - Optionally emit a “validated artifact descriptor” (commit hash, build ID, test/scan summaries), so CI/CD can promote *that* artifact instead of rebuilding.[13][3][4]

***

You’ve already covered the hard bits (hashing, versioning, multi-terminal state). The big “don’t forgets” beyond that are: **policy-as-code**, **incremental/diff-awareness**, and **rich evidence artifacts** so the pipeline is both enforceable and explainable.

## Human

1.  Yes good idea
2.  feels like enterprise bloat
3.  git has been problematic in our multi terminal environment.  How do you suggest making it not a problem?
4.  good idea.
5.  OK
6.  Very good idea.
7.  Yes ok.
8.  Good idea.

We'd keep the data at the root of the feature or repo?  maybe referenced as part of a readme.md tree?  What do you suggest?

## Assistant

Short answer: yes, keep it near the feature/repo, but I’d split *state* and *human docs* rather than stuffing everything into README.

***

## 1) Making Git not a problem in multi‑terminal

To avoid Git weirdness across terminals/worktrees on Windows 11:[1][2][3]

- Treat each *worktree directory* as the unit of identity  
  - Never assume “CWD = repo”; use `git rev-parse --show-toplevel` and `--git-dir` to resolve the real root for that worktree.[3][1]
- Don’t cache by branch name alone  
  - Use `(git_dir, worktree_root, HEAD commit, tree hash)` as the identity for a run, so multiple terminals on the same worktree naturally see the same state, but different worktrees don’t collide.[4][1][3]
- Handle detached / dirty state explicitly  
  - If `HEAD` is detached or the index is dirty, you either:
    - refuse to cache, or  
    - include “dirty hash” (e.g., hash of tracked+untracked files) in the key so staged-but-uncommitted changes are treated as distinct targets.[2][1]

That way, multiple terminals pointing at the same worktree share state; multiple worktrees (or branches) naturally separate.

***

## 2) Where to keep the data

I’d separate *machine-owned state* from *human-facing docs*:

### a) Machine state (for `/promote` internals)

- Location: **outside the repo**, per-user, per-machine, e.g.:  
  - `%USERPROFILE%\.claude\promote\state.db`  
- Keys include `repo_root` and `worktree_root`, so you can still distinguish repos and worktrees.[5][6]
- This avoids:
  - accidental commits of state,  
  - merge conflicts on state files,  
  - and lets you use the same pipeline logic across many repos without wiring anything into each one.

### b) Per-repo evidence and docs

This is what you *should* put at the root of the feature/repo:

- `promote/` directory at repo root (checked in):
  - `promote/README.md` – explains what `/promote` is for this repo, phases, and thresholds.  
  - `promote/config.yaml` – policy-as-code: coverage targets, complexity caps, which phases are enabled.  
  - `promote/reports/` – optional *committed* reports for important runs (e.g., release-grade /e3, /e4 results) if you want an auditable history.  

- README tree integration:
  - At repo root `README.md`, add a short **“Quality & Promotion”** section with a link into `promote/README.md`.  
  - That keeps the top-level README lean but discoverable, and keeps pipeline detail in its own tree.[6]

If you don’t want reports in Git history, make `promote/reports/` gitignored and let `/promote` write ephemeral Markdown/HTML there purely for local consumption.

***

## 3) Anything missing?

Given your constraints, I’d add only one more thing:

- **State schema + version in one place**  
  - Define a small schema version (`state_schema_version`) and include it in the state key/records.  
  - If you change how you encode repo IDs, hashes, or profiles, you can safely invalidate old entries without manual cleanup.

Everything else (profile bloat, enterprise-style approvals) you can skip; the core for you is:

- robust repo/worktree identity,  
- state stored outside the repo,  
- a small `promote/` tree in the repo for config + docs, linked from `README.md`.

## Human

are there repos or socials that have insightful value to consider adding?

## Assistant

Yes, there are a few high-signal repos and people worth “pinning” as reference points for this whole promote/quality-gate story.[1][2]

## Reference repos to study

- Sonar example projects  
  - `sonarcloud_examples` shows how to wire real projects into quality gates (metrics, gate status, GitHub Actions).[3]
  - Good for seeing practical gate configs and how they surface complexity, coverage, smells, etc., in CI.

- Cognitive + cyclomatic complexity tooling  
  - `geneseframework/complexity` – computes both cyclomatic and cognitive complexity, with configurable thresholds and HTML reports.[4]
  - `Melevir/flake8-cognitive-complexity` – focused example of enforcing cognitive complexity in Python via flake8.[5]
  - `uudashr/gocognit` – clean, single-purpose cognitive complexity tool for Go.[6]

- SonarQube quality-gate discussions  
  - SonarSource community threads on “cognitive vs cyclomatic complexity quality gates” give concrete gate settings and lessons learned in production.[7][8][9]

You can mine these for: threshold defaults, how they present complexity in reports, and how they structure project-level configs.

## Articles / blogs worth folding into your mental model

- “10 CI/CD Quality Gates for Production-Level Reliability”  
  - Very aligned with your gate-based promote idea; covers static analysis, tests, security, artifact integrity, performance, observability as first-class gates.[1]

- “CI/CD: Automating Quality Gates”  
  - Focuses on using containers, parallelism, and enforced gates as the backbone of a real pipeline (not just local scripts).[2]

- Sonar’s complexity guide + docs  
  - The Sonar complexity resources plus their GitHub/SonarCloud examples are a good reference for how to present complexity and gate status to humans.[10][11][3]

## Social / people to watch (concept level)

Rather than specific influencers, the most directly relevant “social” sources here are:

- SonarSource community and blog  
  - Ongoing discussions on cognitive complexity, gate tuning, and how they balance “new code vs legacy” in quality gates.[8][9][7]
- GitHub / CI blogs on org-wide CI templates and governance  
  - Show how people build reusable promotion/quality-gate pipelines and policy-as-code for Actions.[12][1]

If you want, I can pull a handful of specific gate configs (complexity, coverage, severity thresholds) from these repos and threads and translate them into a `promote/config.yaml` template you can drop into your own projects.

## Human

Yes please, whatever you think would be valuable.

## Assistant

Here’s a concrete `promote/config.yaml` you can use as a starting point, with values chosen to match common quality-gate practice and the complexity discussions we’ve looked at.[1][2][3][4][5][6][7]

```yaml
# promote/config.yaml

schema_version: 1
pipeline:
  id: promote
  version: 1.0.0

profiles:
  # Fast local feedback – good for inner loop.
  dev:
    phases: [e1_build, e2_review]
    allow_partial: true

  # Default for branches/PRs.
  standard:
    phases: [e1_build, e2_review, e3_validate]
    allow_partial: false

  # Release-grade; used before tagging or publishing.
  release:
    phases: [e1_build, e2_review, e3_validate, e4_publish]
    allow_partial: false

targets:
  # Coverage requirements
  coverage:
    # Overall project coverage target; used as baseline and for trending.
    project_min: 70          # Common “good enough” baseline.[web:19][web:23]
    # New/changed code is held to a higher bar.
    changed_min: 85          # Typical Sonar-style new-code target.[web:21][web:25]
    # Allow temporary dips when raising baselines.
    allow_regression: false

  # Cyclomatic complexity
  cyclomatic:
    # Recommended limit for new/changed functions.
    changed_max: 10          # Widely cited as a reasonable upper bound.[web:30][web:32][web:40]
    warn_band:
      min: 6
      max: 10               # 6–10 flagged but allowed; >10 fails gate.
    # Legacy functions: don’t break solely on existing high CC; do not allow increases.
    legacy:
      fail_on_increase: true
      require_reduction_above: 20  # e.g., when you touch a 30+ CC monster.[web:36][web:38][web:39]

  # Cognitive complexity
  cognitive:
    changed_max: 15          # Aligns with common Sonar defaults per method.[web:35][web:41][web:55]
    warn_band:
      min: 8
      max: 15
    legacy:
      fail_on_increase: true

  # Linting & quality
  lint:
    max_errors: 0
    max_warnings_per_kloc: 10

  duplication:
    # New/changed code duplication limit.
    changed_max_percent: 3   # Keep duplication in new code very low.[web:19]
    project_max_percent: 10  # Used for reporting/triage only.

  # Testing
  tests:
    require:
      unit: true
      integration: true
      regression: false      # Enable for critical systems.
    markers:
      regression: "regression"
      integration: "integration"

  # Security & dependencies
  security:
    max_vulnerability_severity: "MEDIUM"  # HIGH/CRITICAL fail gate.[web:16][web:19][web:28]
    allow_known_issues: false
    # If you use a dependency scanner, restrict licenses here.
    allowed_licenses: ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"]

  secrets:
    fail_on_detect: true
    allow_test_fixtures: false

  # Docs & repo hygiene (mainly for e4_publish)
  docs:
    require:
      readme: true
      license: true
      contributing: false
      changelog: true
    readme:
      sections:
        - "Problem statement"
        - "Quick start"
        - "Usage examples"
        - "Architecture overview"

  ci:
    require_branch_protection: true
    require_status_checks: true
    required_checks:
      - "promote-standard"   # e.g., CI job that runs /promote --profile=standard

hashing:
  # What to include in the content hash for caching phases.
  include:
    - "pyproject.toml"
    - "package.json"
    - "requirements*.txt"
    - "uv.lock"
    - "poetry.lock"
    - "tsconfig.json"
    - "docker-compose.yml"
    - "promote/config.yaml"

  # Whether to treat uncommitted changes as part of the hash.
  include_uncommitted: true

tools:
  # Configure the tools /promote expects to call; useful for diagnostics and versioning.
  coverage_tool: "pytest-cov"
  cyclomatic_tool: "radon"            # or "lizard"
  cognitive_tool: "flake8-cognitive-complexity"
  security_tool: "bandit"
  dependency_tool: "pip-audit"
  linter: "ruff"
  type_checker: "mypy"
```

How to use this:

- `/promote` reads this file, validates it, and includes its hash in the cache key so changing thresholds or tools invalidates stale phase results.[2][8][9]
- Your per-phase skills (e1–e4) just consume the relevant section (coverage, cyclomatic, cognitive, etc.) when deciding pass/fail.  
- You can tune `profiles` per repo, but the defaults above should be sane for most Python/TS-heavy projects.

## Human

can we use /p for the pipeline?

## Assistant

Yes, `/p` is fine, with one caveat: treat it as a **thin alias** rather than the canonical name.

### Recommended pattern

- Canonical skill name: `/promote`  
- Short alias: `/p` → invokes `/promote` with same arguments.

This gives you:

- Discoverability and clarity in docs (`/promote --profile=standard`).[1][2][3]
- Speed in daily use (`/p` from any terminal), just like `g` for `git` or other short aliases.[4][2][5]

As long as `/p` is just a front-end alias and not a separate implementation, you avoid confusion and keep your pipeline semantics in one place.
