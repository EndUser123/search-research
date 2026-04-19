<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Do you think this outcome is optimal?  Any gaps or opportunities?

"Here's part of an earlier conversation: "Great question. Here's a practical progression from rough code to portfolio-quality public repo:
Phase 1: Make It Work
Fix all known bugs — get tests passing, resolve edge cases
Add basic tests — unit tests for core logic, integration tests for workflows
Pin dependencies — lock file (uv.lock, package-lock.json, etc.) so builds are reproducible
Phase 2: Make It Right
Code review pass — clean up dead code, inconsistent naming, leftover debug prints
Type hints / type checking — mypy (Python) or strict TypeScript config
Linting \& formatting — ruff (Python) or eslint/prettier (TS/JS), enforced via config
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

It’s a strong outcome, but there are a few clear opportunities to tighten the model and naming, especially given how opinionated your environment already is.[^1_1][^1_2]

## Is this “optimal”?

The 4-phase, gated, loop-until-clean progression is very aligned with modern quality-gate thinking: each phase has explicit criteria, and you don’t advance until those are satisfied.[^1_2][^1_1]
It also fits well within the broader idea of a “pipeline” as a sequenced series of quality and validation stages, without overclaiming full SDLC coverage.[^1_3][^1_4][^1_5]

So conceptually, it’s close to optimal for “code maturation” (rough → publishable) rather than the entire lifecycle.[^1_6][^1_7][^1_4]

## Naming and conceptual framing gaps

- “Code Maturation Pipeline” is accurate, but you might want something that hints at quality gates, since that’s what you’re really doing (gated promotion between phases).[^1_8][^1_1][^1_2]
- Candidates that align with established terminology:
    - “Quality Gate Pipeline” (emphasizes halt-on-failure stages).[^1_1][^1_8][^1_2]
    - “Promotion Pipeline” or “Code Promotion Pipeline” (suggests moving code between quality tiers).[^1_9][^1_4]
- The /e1..4 names are implementation details; conceptually, you could frame this as a single “promotion pipeline” with four gate-bands: Build, Review, Validate, Publish.[^1_4][^1_1]


## Structural opportunities

1. Make gates first-class, not just phases
Right now you’ve got phases with implicit “loop until clean” behavior; you could formalize these as explicit quality gates with thresholds per gate (e.g., no critical issues, >= X% coverage, etc.), which is consistent with how quality gates are usually defined and enforced in CI.[^1_8][^1_2][^1_1]
2. Separate “analysis primitives” from “pipelines”
You’re already leaning this way: /review as pure analysis, /validate as a pipeline that calls it. That’s exactly the “pipeline-as-code composed from reusable tasks” pattern people use to avoid duplication.[^1_10][^1_11][^1_7][^1_3]
Ensuring /e1..4 are thin orchestrators over shared primitives will keep you from recreating the multi-skill duplication you just cleaned up.[^1_10][^1_9][^1_3]
3. Explicit depth/profiles early
You’ve already designed depth flags for /validate (quick/standard/full); consider matching that across the whole chain so /e1..4 can run in:
    - scan mode (analysis only),
    - local-dev mode (fast checks),
    - gate mode (full, blocking).[^1_12][^1_13][^1_7]

## UX and workflow gaps

- Single entrypoint meta-skill
Dev-UX wise, having one canonical “/promote” (or similar) that walks the repo through e1→e4 with resumable state would better match how CI/CD pipelines expose a single definition with multiple stages.[^1_3][^1_4][^1_10]
- Context-aware strictness
Quality-gate best practices often recommend stricter rules for new/changed code and progressive tightening over time (e.g., “no new criticals, coverage on new code can’t drop”).[^1_14][^1_1][^1_8]
You could mirror that by:
    - Treating “legacy” vs “touched in this session” differently.
    - Letting /e3 or /e4 enforce stricter gates on diff-only.


## Non-destructive implementation thoughts

Using /e1..4 as a non-destructive, experimental pipeline alongside the existing skills is a solid pattern; it’s similar to how teams stand up “golden pipelines” or template pipelines while keeping legacy ones intact.[^1_7][^1_9][^1_4]
Once you’re happy with behavior, you can either:

- alias /build,/review,/validate,/publish to /e1..4, or
- keep /e* as “opinionated paved road” variants while legacy skills remain low-level primitives.[^1_9][^1_4]

If you want, I can propose concrete names and gate criteria for /e1–/e4 that make these quality gates explicit (e.g., exact thresholds and exit conditions per phase).
<span style="display:none">[^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://testrigor.com/blog/software-quality-gates/

[^1_2]: https://www.perforce.com/blog/sca/what-quality-gates

[^1_3]: https://teamhub.com/blog/understanding-pipeline-as-code-in-software-development/

[^1_4]: https://github.com/resources/articles/pipeline

[^1_5]: https://www.reddit.com/r/learnprogramming/comments/ueh9h6/what_exactly_is_a_pipeline/

[^1_6]: https://fastercapital.com/topics/understanding-pipeline-maturity.html/1

[^1_7]: https://www.blazemeter.com/blog/ci-cd-best-practices-improve-code-quality

[^1_8]: https://debugg.ai/resources/best-code-quality-gates-tools-for-developers-2024

[^1_9]: https://www.harness.io/harness-devops-academy/scaling-ci-cd-templates-the-pipeline-reuse-maturity-model

[^1_10]: https://about.gitlab.com/topics/ci-cd/pipeline-as-code/

[^1_11]: https://www.techtarget.com/searchsoftwarequality/definition/pipeline-as-code

[^1_12]: https://codefresh.io/learn/ci-cd/7-ci-cd-concepts-you-must-know/

[^1_13]: https://www.wondermentapps.com/blog/ci-cd-pipeline-best-practices/

[^1_14]: https://www.reddit.com/r/devops/comments/1onb20l/how_are_you_enforcing_codequality_gates/

[^1_15]: https://www.reddit.com/r/devops/comments/12m0e88/cicd_good_practices_should_the_cicd_pipeline/


---

# yes please

Here’s a concrete, opinionated spec for /e1–/e4 with explicit names and gate criteria. Thresholds are chosen to match common “quality gate” practice (and you can tune them per repo).[^2_1][^2_2][^2_3][^2_4]

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
    - Line coverage on changed files ≥ 70%.[^2_2][^2_3][^2_5][^2_6]
- No “blocking” runtime failures (crash at startup, missing config).

**Diff-aware rule (optional but recommended):**

- Do not enforce global project coverage here; only enforce on changed files so you don’t get blocked by legacy.[^2_7][^2_4][^2_8]

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
    - Cyclomatic complexity per function ≤ 10 for new/changed functions (with allowlist for generated or legacy hotspots).[^2_3][^2_9][^2_2]
    - Duplication in new/changed code ≤ 3% of that diff.[^2_2]
- Review findings:
    - 0 CRITICAL and 0 HIGH severity findings from /review.[^2_10][^2_1][^2_2]
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
    - All required test suites pass (unit + integration + regression where configured).[^2_9][^2_2]
- Coverage:
    - Overall project coverage ≥ configurable baseline (start from current, then gradually move toward 70–80%).[^2_5][^2_3][^2_2]
    - Coverage on changed code ≥ 80–90% (stricter than /e1).[^2_4][^2_3][^2_2]
- Security:
    - 0 HIGH/CRITICAL security vulnerabilities in code or dependencies.[^2_1][^2_10][^2_2]
    - 0 secrets detected in repo (or all real positives removed/rotated).
- Compliance:
    - Type checking passes (no errors in strict mode for new/changed code).
    - No license policy violations from dependency scan (if you track this).[^2_2]

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
    - README contains: problem statement, quickstart, usage examples, and basic architecture overview.[^2_5][^2_2]
    - LICENSE present and from approved set (MIT, Apache-2.0, etc.).
    - CONTRIBUTING or “How to work on this” section present for non-trivial repos.
- CI/CD:
    - Default branch protected by CI that:
        - Runs /e1–/e3 equivalents.
        - Fails build on any blocking gate (tests, security, coverage-on-new-code, critical review issues).[^2_11][^2_1][^2_2]
- Release hygiene:
    - Semantic version tag for latest “green” state.
    - CHANGELOG entry for that release (even minimal).
- Repo state:
    - No uncommitted changes or untracked files needed for a green run.
    - No local-only configuration required beyond documented env vars.

***

## How these gates interact

- /e1–/e4 are **promotion gates**: you only move forward when the current gate is satisfied; you can always re-run a lower gate after changes.
- All gates should treat “new/changed code” more strictly than legacy code: this is the de-facto best practice for evolving large codebases without boiling the ocean.[^2_8][^2_7][^2_4]
- You can expose a meta-skill like `/promote` that:
    - Detects current “max passed gate” for the branch.
    - Runs the next gate and loops until green or user stops.

If you share one concrete repo profile (size, language, current coverage), I can tune these thresholds into a config stub you can drop into the meta-skill or a central `quality-gates.yaml`.
<span style="display:none">[^2_12][^2_13][^2_14][^2_15]</span>

<div align="center">⁂</div>

[^2_1]: https://docs.sonarsource.com/sonarqube-server/10.7/instance-administration/analysis-functions/quality-gates

[^2_2]: https://www.propelcode.ai/blog/continuous-integration-code-quality-gates-setup-guide

[^2_3]: https://dev.to/sophielane/how-to-use-coverlet-coverage-thresholds-to-enforce-better-testing-standards-3pec

[^2_4]: https://docs.sealights.io/knowledgebase/settings/quality-gates

[^2_5]: https://www.graphite.com/guides/code-coverage-best-practices

[^2_6]: https://graphite.com/guides/code-coverage-best-practices

[^2_7]: https://community.sonarsource.com/t/quality-gate-metric-for-coverage-on-new-code-not-failing-short-lived-branch/9909

[^2_8]: https://www.ben-morris.com/does-code-quality-matter-using-sonarqube-with-legacy-code-bases/

[^2_9]: https://www.ranorex.com/blog/test-coverage/

[^2_10]: https://experienceleague.adobe.com/en/docs/experience-manager-cloud-manager/content/using/code-quality-testing

[^2_11]: https://www.jetbrains.com/help/qodana/quality-gate.html

[^2_12]: https://www.reddit.com/r/devops/comments/1onb20l/how_are_you_enforcing_codequality_gates/

[^2_13]: https://stackoverflow.com/questions/41385327/configure-sonarqube-quality-gate-threshold-for-new-issues-rather-than-increase-i

[^2_14]: https://community.sonarsource.com/t/quality-gate-not-breaking-on-low-coverage-score/7943

[^2_15]: https://softjourn.com/insights/legacy-system-modernization-approaches


---

# Recommended cyclomatic complexity limits for quality gates

Most teams set fairly conservative limits; 10 per function is the usual “good default,” with some nuance by context.[^3_1][^3_2][^3_3][^3_4][^3_5]

## Commonly recommended thresholds

- 1–10: Simple and easy to test; generally considered the ideal range.[^3_6][^3_5][^3_1]
- 11–20: Moderately/quite complex; acceptable with care but a refactoring candidate.[^3_5][^3_1][^3_6]
- 21–50: High risk; hard to test and maintain, usually flagged for refactor.[^3_1][^3_6][^3_5]
- >50: Very complex/“untestable”; almost always considered problematic.[^3_4][^3_6][^3_5][^3_1]

McCabe’s original guidance and later summaries (e.g., ReSharper, Code Complete) point to 10 as a reasonable upper bound for most modules, with 15 as a possible relaxed limit for mature teams willing to invest more in testing.[^3_7][^3_4][^3_5]

## Practical quality-gate settings

For a modern quality gate, a good starting policy is:

- New or changed code:
    - Hard limit: CC ≤ 10 per function/method (gate fails above this).[^3_2][^3_5][^3_1]
    - Warning band: 6–10 flagged but allowed; >10 requires refactor or explicit justification.[^3_2][^3_5]
- Legacy code:
    - No hard break on existing high CC; instead:
        - Refuse *increases* in CC on legacy hot spots.
        - Require reductions when touching very high complexity areas (e.g., CC ≥ 20).[^3_8][^3_9][^3_4]
- Critical/safety-critical code:
    - Stricter: target 5–7 max per function where feasible.[^3_10][^3_4][^3_2]

This gives you a firm 10-for-new-code gate, keeps you from being blocked by old mess, and nudges complexity down over time.
<span style="display:none">[^3_11][^3_12][^3_13][^3_14][^3_15]</span>

<div align="center">⁂</div>

[^3_1]: https://axify.io/blog/cyclomatic-complexity

[^3_2]: https://linearb.io/blog/cyclomatic-complexity

[^3_3]: https://docs.legato.io/18_08/ccodingStdsComplexity.html

[^3_4]: https://blog.feabhas.com/2018/07/code-quality-cyclomatic-complexity/

[^3_5]: https://github.com/JetBrains/resharper-cyclomatic-complexity/blob/master/docs/ThresholdGuidance.md

[^3_6]: https://stackoverflow.com/questions/1364946/what-is-the-highest-cyclomatic-complexity-of-any-function-you-maintain-and-how

[^3_7]: https://en.wikipedia.org/wiki/Cyclomatic_complexity

[^3_8]: https://www.in-com.com/blog/cyclomatic-complexity/

[^3_9]: https://xebia.com/blog/using-metrics-to-find-the-pain-points-in-a-legacy-codebase/

[^3_10]: https://www.sonarsource.com/resources/library/cyclomatic-complexity/

[^3_11]: https://www.eevblog.com/forum/programming/cyclomatic-complexity/

[^3_12]: https://community.sonarsource.com/t/difference-between-cognitive-cyclomatic-complexity-quality-gate-and-rule/25558

[^3_13]: https://www.swarmia.com/blog/complexity-in-developer-productivity/

[^3_14]: https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity?view=vs-2022

[^3_15]: https://getdx.com/blog/cyclomatic-complexity/


---

# How to reduce cyclomatic complexity in code

Cyclomatic vs cognitive complexity differences
Tools to measure and enforce complexity thresholds
Refactoring strategies for high cyclomatic complexity functions
Quality gate settings for cognitive complexity limits

Here’s a concise, opinionated set of answers you can lift straight into gate specs and refactor playbooks.

***

## How to reduce cyclomatic complexity

Most effective, language-agnostic moves:[^4_1][^4_2][^4_3][^4_4]

- Extract smaller functions
    - Split large, multi-responsibility functions into single-purpose helpers.
- Flatten control flow
    - Replace nested `if/else`/`switch` ladders with guard clauses, early returns, or lookup tables.[^4_2][^4_5][^4_1]
- Remove duplication
    - Consolidate duplicated branches into shared helpers or strategy/template patterns.[^4_4][^4_1]
- Use polymorphism / strategy
    - Replace big type/flag `switch` blocks with polymorphic dispatch or strategy objects.[^4_3]
- Isolate special cases
    - Move rare or edge-case logic into separate code paths or handlers.

All of this is safest if you start with tests (or add them), then refactor while re-running tests and complexity metrics.[^4_6][^4_7]

***

## Cyclomatic vs cognitive complexity

Core differences:[^4_8][^4_9][^4_10]

- Cyclomatic complexity
    - What it measures: number of linearly independent control-flow paths (branch/loop count).
    - Focus: test effort and structural risk (how many paths to test).
    - Calculation: count decision points (`if`, `for`, `while`, `case`, etc.) plus 1.[^4_7][^4_11][^4_12]
- Cognitive complexity
    - What it measures: mental effort required to understand the code.
    - Focus: readability and comprehension cost (nesting, convoluted flow, boolean soup).
    - Calculation: penalizes nesting depth, complex boolean expressions, jumps, but does *not* penalize simple sequence or some structural patterns that don’t add mental load.[^4_9][^4_10][^4_8]

High cyclomatic complexity ≈ many paths; high cognitive complexity ≈ hard-to-think-about logic, even if structural path count is small.[^4_11][^4_9]

***

## Tools to measure and enforce thresholds

Representative tools you can wire into gates:[^4_13][^4_14][^4_15][^4_16][^4_17]

- General / multi-language
    - SonarQube / SonarCloud: cyclomatic and cognitive complexity, project and method level, quality gates.[^4_18][^4_16]
    - JetBrains IDEs (ReSharper, Rider, IntelliJ): per-method cyclomatic complexity, with guidance docs and thresholds.[^4_17][^4_19]
    - GeneSE complexity: CLI and library for cyclomatic and cognitive complexity across languages.[^4_13]
- Language-specific examples
    - Java / .NET: Visual Studio Code Metrics, ReSharper, Sonar plugins.[^4_19][^4_17]
    - JavaScript/TypeScript: ESLint plugins for complexity; cognitive complexity rules exist in various rule sets.[^4_9][^4_11]
    - Python: radon (cyclomatic, MI), xenon (threshold enforcement).[^4_14][^4_15]
- Enforcement pattern
    - Run complexity analysis in CI.
    - Fail the build when function/file/project metrics exceed configured limits (see gates below).[^4_15][^4_16]

***

## Refactoring strategies for high-CC functions

For a function with CC in the 20–50+ range, typical moves:[^4_1][^4_2][^4_3][^4_4]

- Decompose by responsibility
    - Identify distinct phases in the function (validation, transformation, IO, reporting) and extract them into separate functions or classes.
- Replace condition ladders
    - Map “input → behavior” with a table or dictionary instead of long `if/elif` chains; or use polymorphic classes/strategies.[^4_5][^4_3][^4_14]
- Remove nested conditionals
    - Use early returns/guards, meaningfully named boolean helpers, or separate validator functions to get back to flat, linear logic.[^4_2][^4_3]
- Split big boolean expressions
    - Break complex conditions into named intermediate variables or helper functions for each rule.[^4_3][^4_9]
- Separate error handling from core logic
    - Move “plumbing” (logging, retries, error wrapping) into decorators/middleware so the core function is straightforward.

Algorithmically, your loop can be: add tests → measure CC → refactor a small piece → re-run tests + metric → repeat until under threshold.[^4_6][^4_7]

***

## Quality gate settings for cognitive complexity

There’s less universal consensus than for cyclomatic, but common patterns (often via Sonar rules) look like:[^4_10][^4_16][^4_18][^4_9]

- Per-method limits
    - Cognitive complexity per method ≤ 15 is a common rule-of-thumb; SonarQube examples use 15 as a “too high” default for Java methods.[^4_18]
    - Some teams use 10–12 as the “preferable” range for new code, with 15 as hard upper bound.[^4_16][^4_9]
- Gate strategy
    - New/changed code:
        - Hard fail if cognitive complexity > 15 for any new/modified method.
        - Warning band (e.g., 10–15) that requires justification or tech-debt tracking.
    - Legacy code:
        - Don’t fail the build solely on old high cognitive complexity; instead fail on *increases* and require improvement when touching those methods.[^4_20][^4_11][^4_9]
    - Project-level:
        - Use total cognitive complexity mainly as a reporting/triage metric, not as a hard gate, since it scales with size.[^4_10]

Combining both, a reasonable default for your gates:

- Cyclomatic complexity (new/changed):
    - Soft band: 6–10; hard cap: 10–12.
- Cognitive complexity (new/changed):
    - Soft band: 8–15; hard cap: 15.

That gives you a structurally simple, mentally tractable target surface without blocking on existing legacy hotspots.
<span style="display:none">[^4_21]</span>

<div align="center">⁂</div>

[^4_1]: https://linearb.io/blog/reduce-cyclomatic-complexity

[^4_2]: https://typoapp.io/blog/reduce-cyclomatic-complexity

[^4_3]: https://www.hackerone.com/blog/unraveling-cyclomatic-complexity-guide-simplifying-your-code

[^4_4]: https://www.axelerant.com/blog/reducing-cyclomatic-complexity-and-npath-complexity-steps-for-refactoring

[^4_5]: https://www.danylkoweb.com/Blog/minimizing-cyclomatic-complexity-with-pattern-matching-SR

[^4_6]: https://stackoverflow.com/questions/40218530/how-to-reduce-cyclomatic-complexity-by-refactoring-the-code

[^4_7]: https://jellyfish.co/library/cyclomatic-complexity/

[^4_8]: https://www.graphapp.ai/blog/cyclomatic-complexity-vs-cognitive-complexity-a-comparative-analysis

[^4_9]: https://getdx.com/blog/cognitive-complexity/

[^4_10]: https://www.graphapp.ai/blog/cyclomatic-complexity-vs-cognitive-complexity-key-differences-explained

[^4_11]: https://linearb.io/blog/cyclomatic-complexity

[^4_12]: https://en.wikipedia.org/wiki/Cyclomatic_complexity

[^4_13]: https://github.com/geneseframework/complexity

[^4_14]: https://axify.io/blog/cyclomatic-complexity

[^4_15]: https://www.in-com.com/blog/cyclomatic-complexity/

[^4_16]: https://www.sonarsource.com/resources/library/cyclomatic-complexity/

[^4_17]: https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity?view=vs-2022

[^4_18]: https://community.sonarsource.com/t/difference-between-cognitive-cyclomatic-complexity-quality-gate-and-rule/25558

[^4_19]: https://github.com/JetBrains/resharper-cyclomatic-complexity/blob/master/docs/ThresholdGuidance.md

[^4_20]: https://www.ben-morris.com/does-code-quality-matter-using-sonarqube-with-legacy-code-bases/

[^4_21]: https://stackoverflow.com/questions/28549244/refactoring-java-method-to-reduce-cyclomatic-complexity


---

# Best tools to measure cyclomatic complexity

Here are solid, broadly used tools you can plug into gates and CI for cyclomatic complexity.[^5_1][^5_2][^5_3][^5_4]

***

## Multi-language / platform tools

- SonarQube / SonarCloud
    - Measures cyclomatic and cognitive complexity across 30+ languages, exposes per-function metrics, and lets you define quality gates (e.g., max complexity per method, total complexity).[^5_5][^5_3][^5_6]
    - Good for central dashboards and “break the build if new code exceeds X” policies.
- Lizard
    - CLI and library that computes cyclomatic complexity for many languages (C/C++, Java, Python, JavaScript, etc.) and is easy to script into CI.[^5_7][^5_8]
    - Outputs per-function metrics and can be used to enforce thresholds in a custom gate.
- SourceMonitor / Metrix++ / similar
    - Desktop/CLI tools that compute complexity and other metrics across multiple languages, often used in legacy code surveys and periodic reports.[^5_9][^5_2][^5_4]

***

## Language- and ecosystem-specific tools

- .NET / C\# / C++
    - Visual Studio Code Metrics: built-in cyclomatic complexity metric per method, integrated into the IDE and reports.[^5_10]
    - ReSharper / Rider: per-method complexity highlighting and threshold guidance.[^5_11]
- Java
    - SonarQube plugins (usual choice), plus IDE plugins that show per-method complexity and can enforce limits via inspections.[^5_3][^5_6]
- JavaScript / TypeScript
    - ESLint `complexity` rule and related rules for nesting, parameters, etc., to gate max complexity in CI.[^5_4][^5_9]
    - Some static analysis platforms (e.g., CodeClimate, Sonar) expose JS complexity in dashboards.[^5_1][^5_4]
- Python
    - radon: computes cyclomatic complexity and maintainability index from the CLI or Python API.[^5_12][^5_13]
    - xenon: enforces radon-based thresholds, exiting with non-zero status when complexity exceeds configured limits.[^5_13]

***

## How to enforce in quality gates

- Run the chosen tool in CI as a separate step.
- Parse per-function scores and fail the build when:
    - Any new/changed function exceeds your complexity cap (e.g., 10–12).
    - Or total complexity in touched files increases beyond a tolerance.
- SonarQube, ESLint, and xenon can all be configured to do this directly; Lizard/radon require a thin wrapper script that interprets their output and decides pass/fail.[^5_2][^5_6][^5_4][^5_13]
<span style="display:none">[^5_14][^5_15][^5_16][^5_17][^5_18]</span>

<div align="center">⁂</div>

[^5_1]: https://cycode.com/blog/top-10-code-analysis-tools/

[^5_2]: https://www.in-com.com/blog/how-to-identify-and-reduce-cyclomatic-complexity-using-static-analysis/

[^5_3]: https://brainhub.eu/library/measuring-cyclomatic-complexity

[^5_4]: https://daily.dev/blog/7-code-complexity-metrics-developers-must-track

[^5_5]: https://blog.devgenius.io/sonarqube-cognitive-complexity-265640dbad3e?gi=8b94395dc367

[^5_6]: https://www.sonarsource.com/resources/library/cyclomatic-complexity/

[^5_7]: https://github.com/terryyin/lizard

[^5_8]: https://pypi.org/project/lizard/

[^5_9]: https://stackoverflow.com/questions/100645/calculate-cyclomatic-complexity-for-javascript

[^5_10]: https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity?view=visualstudio

[^5_11]: https://github.com/JetBrains/resharper-cyclomatic-complexity/blob/master/docs/ThresholdGuidance.md

[^5_12]: https://axify.io/blog/cyclomatic-complexity

[^5_13]: https://www.in-com.com/blog/cyclomatic-complexity/

[^5_14]: https://www.shadecoder.com/ja/topics/cyclomatic-complexity-a-comprehensive-guide-for-2025

[^5_15]: https://www.reddit.com/r/programmingtools/comments/1j7ufq2/best_static_code_analysis_tools_for_2025_compared/

[^5_16]: https://www.linkedin.com/pulse/improving-code-quality-reducing-complexity-1-zeeshan-adil

[^5_17]: https://jellyfish.co/library/cyclomatic-complexity/

[^5_18]: https://www.youtube.com/watch?v=DzDETVRpqMk


---

# propose a single skill name, that invokes the pipeline, and halts if a phase isn't good.  If a phase is good, it proceeds to the next.  It should record phase assessment quality, and the next time we use the pipeline it won't rerun a good phase, if the hash for the target system hasn't changed.  It needs to be multi terminal friendly, for claude code on windows 11, and not get tricked by context bleed or stale data.  we should be able to pick up the work in another terminal on another day without needing to redo work.  We probably need to include the version of the pipeline or phases, so that if we update part of it, the old state/phase data would be invalidated.  Does that make sense?  Are we forgetting anything?

Yes, it makes sense, and you’re hitting the right concerns (hashing, versioning, multi-terminal, stale state). Here’s an opinionated proposal and a quick checklist of “don’t forgets.”[^6_1][^6_2][^6_3]

***

## Skill name and behavior

**Skill name:** `/promote`

**Behavior:**

- Runs your 4-phase pipeline as ordered gates: e1 → e2 → e3 → e4.
- For each phase:
    - Compute a **target hash** for the system under test (e.g., Git tree hash of the repo, plus optional config inputs).[^6_2]
    - Look up persisted state: `(repo_id, branch, phase_id, pipeline_version, hash)` → last result.
    - If there is a **matching successful record**, skip the phase.
    - Otherwise, execute that phase’s skill, record result (pass/fail + metrics), and:
        - On **pass**: continue to next phase.
        - On **fail**: halt `/promote` immediately and report which gate failed and why.[^6_1]

This gives you a true **promotion gate** skill with caching based on content hash + pipeline version.[^6_2][^6_1]

***

## State model and versioning

Persist (in a simple JSON/SQLite/kv store in your `.claude` area) a record per phase:

- Keys:
    - `pipeline_id = "promote"`
    - `pipeline_version = "1.0.0"` (bumped when you change phase logic).
    - `phase_id ∈ {e1_build, e2_review, e3_validate, e4_publish}`
    - `repo_id` (e.g., canonical path or a stable UUID per repo).
    - `branch` (or ref) name.
    - `target_hash` (Git tree hash or your own content hash).[^6_2]
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

To keep this robust across terminals and days:[^6_4][^6_5][^6_3]

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
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_6][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://www.propelcode.ai/blog/continuous-integration-code-quality-gates-setup-guide

[^6_2]: https://www.reddit.com/r/devops/comments/ua3fji/speeding_up_cicd_pipelines_with_checksums/

[^6_3]: https://www.tencentcloud.com/techpedia/125877

[^6_4]: https://www.reddit.com/r/Terraform/comments/ypsloz/how_are_workspaces_used_across_multiple_teams/

[^6_5]: https://stackoverflow.com/questions/56433841/multiple-developers-workflow-with-shared-terraform-codebase

[^6_6]: https://learn.microsoft.com/en-us/azure/devops/organizations/settings/naming-restrictions?view=azure-devops

[^6_7]: https://mdtproductdevelopement-enablement-pnps-dev.azurewebsites.net/Tools/Azure/Azure-Repos-and-Pipelines/Pipelines-Management/Pipeline-Naming-and-Organization/

[^6_8]: https://stackoverflow.com/questions/60386031/in-azure-devops-release-pipeline-how-to-promote-the-latest-version-to-a-stage-to

[^6_9]: https://decovar.dev/blog/2021/07/21/azure-devops-artifacts-promotion/

[^6_10]: https://help.salesforce.com/apex/HTViewHelpDoc?id=devops_center_work_items_promote.htm

[^6_11]: https://www.reddit.com/r/devops/comments/1ci9kco/question_on_infrastructureascode_how_do_you/

[^6_12]: https://www.reddit.com/r/azuredevops/comments/fskotd/naming_convention_repos_and_pipelines/

[^6_13]: https://www.usenix.org/system/files/usenixsecurity23-katzman.pdf

[^6_14]: https://www.reddit.com/r/devops/comments/1exqlkq/deployment_promotion_with_dns_names/

[^6_15]: https://www.zigpoll.com/content/can-you-provide-the-best-practices-a-technical-lead-should-follow-when-improving-frontend-deployment-pipelines-for-faster-and-more-reliable-releases


---

# What additional features should we consider for our promote pipeline?

A few high‑leverage features come to mind that fit what you’ve described and make `/promote` feel “first-class” rather than just a thin orchestrator.[^7_1][^7_2][^7_3]

***

## 1. Artifacted evidence per phase

Store not just pass/fail, but **artifacts** for each phase:

- Structured JSON: coverage, complexity, issue counts, security findings, gate thresholds used.
- Human report: concise markdown summary (`.claude/promote/e2_review-report.md`).

This gives you:

- Diffable history between runs.
- A way to surface metrics and trend them without re-running the phase.[^7_2][^7_1]

***

## 2. Profiles, policies, and approvals

Introduce a lightweight policy system:

- Profiles: `dev`, `ci`, `release` with different thresholds and which phases are required.
- Manual approval hooks:
    - Optional “human gate” before / after certain phases for regulated or risky changes.[^7_4][^7_3][^7_2]

This lets `/promote` run in:

- **Local-dev mode**: fast, possibly skipping heavy phases.
- **Enforcement mode**: used by CI or pre-merge, with stricter gates and optional approvals.

***

## 3. Incremental and diff‑aware analysis

Go beyond a simple tree hash:

- Diff-based focus:
    - Prioritize analyzers on changed files/functions; treat legacy separately.
- Incremental static analysis:
    - Keep summaries so later runs can reuse results when only a small subset of files changed.[^7_5][^7_6][^7_7]

This keeps phases fast enough that you won’t be tempted to bypass them.

***

## 4. Policy‑as‑code config

Let repos declare their own gate config:

- `promote.config.(yaml|json)` checked into the repo with:
    - Complexity caps, coverage targets, allowed licenses, security severity thresholds, etc.[^7_8][^7_1]
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
    - Track `branch` and optionally `pr_number` or `session_id` so multiple efforts on the same repo don’t stomp each other’s state.[^7_9][^7_10]
- Safety checks:
    - Refuse to run if repo is in a detached HEAD or ambiguous state, unless `--force`.

***

## 6. Degradation and fallback behavior

When something goes wrong (tool missing, metric not available):

- Clear error modes:
    - Distinguish “gate failed” vs “pipeline misconfigured or tool missing”.
- Graceful fallback:
    - For example, if a performance tool isn’t installed, mark that sub-gate as “not evaluated” but don’t silently treat it as a pass.[^7_1][^7_2]

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
    - Phase ID in exit code or in a small JSON block so a GitHub Action/Azure pipeline can mark the right check as failed.[^7_11][^7_12][^7_2]
- Single‑artifact principle:
    - Optionally emit a “validated artifact descriptor” (commit hash, build ID, test/scan summaries), so CI/CD can promote *that* artifact instead of rebuilding.[^7_13][^7_3][^7_4]

***

You’ve already covered the hard bits (hashing, versioning, multi-terminal state). The big “don’t forgets” beyond that are: **policy-as-code**, **incremental/diff-awareness**, and **rich evidence artifacts** so the pipeline is both enforceable and explainable.
<span style="display:none">[^7_14][^7_15][^7_16][^7_17][^7_18]</span>

<div align="center">⁂</div>

[^7_1]: https://zetcode.com/terms-testing/quality-gate/

[^7_2]: https://www.infoq.com/articles/pipeline-quality-gates/

[^7_3]: https://www.devopstraininginstitute.com/blog/10-cicd-quality-gates-for-production-level-reliability

[^7_4]: https://www.reddit.com/r/devops/comments/1hs54fn/single_cicd_pipeline_with_promotion_between/

[^7_5]: https://www3.cs.stonybrook.edu/~stoller/papers/TOPLAS98.pdf

[^7_6]: https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2025.28

[^7_7]: https://www.reddit.com/r/devops/comments/ua3fji/speeding_up_cicd_pipelines_with_checksums/

[^7_8]: https://www.teamazing.com/quality-gates/

[^7_9]: https://www.reddit.com/r/Terraform/comments/ypsloz/how_are_workspaces_used_across_multiple_teams/

[^7_10]: https://stackoverflow.com/questions/56433841/multiple-developers-workflow-with-shared-terraform-codebase

[^7_11]: https://about.gitlab.com/blog/ultimate-guide-to-ci-cd-fundamentals-to-advanced-implementation/

[^7_12]: https://learn.microsoft.com/en-us/azure/devops/pipelines/architectures/devops-pipelines-baseline-architecture?view=azure-devops

[^7_13]: https://octopus.com/blog/fast-tracking-code-promotion-in-your-ci-cd-pipeline

[^7_14]: https://dev.to/gauri1504/advanced-cicd-pipeline-configuration-strategies-4mjh

[^7_15]: https://www.youtube.com/watch?v=S2ZNKu4IrdE

[^7_16]: https://www.reddit.com/r/devops/comments/11e6tdl/what_is_your_preferred_method_for_promoting_to/

[^7_17]: https://vercel.com/blog/isr-a-flexible-way-to-cache-dynamic-content

[^7_18]: https://www.youtube.com/watch?v=UC-sDyfTemc


---

# 1.  Yes good idea

2. feels like enterprise bloat
3. git has been problematic in our multi terminal environment.  How do you suggest making it not a problem?
4. good idea.
5. OK
6. Very good idea.
7. Yes ok.
8. Good idea.

We'd keep the data at the root of the feature or repo?  maybe referenced as part of a readme.md tree?  What do you suggest?

Short answer: yes, keep it near the feature/repo, but I’d split *state* and *human docs* rather than stuffing everything into README.

***

## 1) Making Git not a problem in multi‑terminal

To avoid Git weirdness across terminals/worktrees on Windows 11:[^8_1][^8_2][^8_3]

- Treat each *worktree directory* as the unit of identity
    - Never assume “CWD = repo”; use `git rev-parse --show-toplevel` and `--git-dir` to resolve the real root for that worktree.[^8_3][^8_1]
- Don’t cache by branch name alone
    - Use `(git_dir, worktree_root, HEAD commit, tree hash)` as the identity for a run, so multiple terminals on the same worktree naturally see the same state, but different worktrees don’t collide.[^8_4][^8_1][^8_3]
- Handle detached / dirty state explicitly
    - If `HEAD` is detached or the index is dirty, you either:
        - refuse to cache, or
        - include “dirty hash” (e.g., hash of tracked+untracked files) in the key so staged-but-uncommitted changes are treated as distinct targets.[^8_2][^8_1]

That way, multiple terminals pointing at the same worktree share state; multiple worktrees (or branches) naturally separate.

***

## 2) Where to keep the data

I’d separate *machine-owned state* from *human-facing docs*:

### a) Machine state (for `/promote` internals)

- Location: **outside the repo**, per-user, per-machine, e.g.:
    - `%USERPROFILE%\.claude\promote\state.db`
- Keys include `repo_root` and `worktree_root`, so you can still distinguish repos and worktrees.[^8_5][^8_6]
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
    - At repo root `README.md`, add a short **“Quality \& Promotion”** section with a link into `promote/README.md`.
    - That keeps the top-level README lean but discoverable, and keeps pipeline detail in its own tree.[^8_6]

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
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_7][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://www.datacamp.com/tutorial/git-worktree-tutorial

[^8_2]: https://www.datacamp.com/es/tutorial/git-worktree-tutorial

[^8_3]: https://www.meziantou.net/git-worktree-managing-multiple-working-directories.htm

[^8_4]: https://www.reddit.com/r/git/comments/lfv8yp/the_correct_way_to_do_this_in_git_work_on/

[^8_5]: https://aws.amazon.com/blogs/devops/best-practices-for-managing-terraform-state-files-in-aws-ci-cd-pipeline/

[^8_6]: https://www.env0.com/blog/terraform-best-practices-state-management-reusability-security-and-beyond

[^8_7]: https://github.com/FareedKhan-dev/git-workflow-guide

[^8_8]: https://www.reddit.com/r/Linear/comments/1ohi9rd/lit_manage_your_linear_issues_without_ever/

[^8_9]: https://www.gitkraken.com/blog/multi-repo-management-hurdles-and-solutions

[^8_10]: https://stackoverflow.com/questions/14865283/proper-git-workflow-scheme-with-multiple-developers-working-on-same-task

[^8_11]: https://stackoverflow.com/questions/39926386/github-workflow-issue-how-to-work-with-multiple-developers-on-github

[^8_12]: https://www.reddit.com/r/Terraform/comments/1450vs3/a_question_around_storing_remote_state_or_local/

[^8_13]: https://www.reddit.com/r/learnprogramming/comments/qsl2qi/confused_by_git_branch_workflow/

[^8_14]: https://georgestocker.com/2020/03/04/please-stop-recommending-git-flow/

[^8_15]: https://dev.to/softheartengineer/how-to-work-on-multiple-branches-using-git-worktree-command-4pam


---

# are there repos or socials that have insightful value to consider adding?

Yes, there are a few high-signal repos and people worth “pinning” as reference points for this whole promote/quality-gate story.[^9_1][^9_2]

## Reference repos to study

- Sonar example projects
    - `sonarcloud_examples` shows how to wire real projects into quality gates (metrics, gate status, GitHub Actions).[^9_3]
    - Good for seeing practical gate configs and how they surface complexity, coverage, smells, etc., in CI.
- Cognitive + cyclomatic complexity tooling
    - `geneseframework/complexity` – computes both cyclomatic and cognitive complexity, with configurable thresholds and HTML reports.[^9_4]
    - `Melevir/flake8-cognitive-complexity` – focused example of enforcing cognitive complexity in Python via flake8.[^9_5]
    - `uudashr/gocognit` – clean, single-purpose cognitive complexity tool for Go.[^9_6]
- SonarQube quality-gate discussions
    - SonarSource community threads on “cognitive vs cyclomatic complexity quality gates” give concrete gate settings and lessons learned in production.[^9_7][^9_8][^9_9]

You can mine these for: threshold defaults, how they present complexity in reports, and how they structure project-level configs.

## Articles / blogs worth folding into your mental model

- “10 CI/CD Quality Gates for Production-Level Reliability”
    - Very aligned with your gate-based promote idea; covers static analysis, tests, security, artifact integrity, performance, observability as first-class gates.[^9_1]
- “CI/CD: Automating Quality Gates”
    - Focuses on using containers, parallelism, and enforced gates as the backbone of a real pipeline (not just local scripts).[^9_2]
- Sonar’s complexity guide + docs
    - The Sonar complexity resources plus their GitHub/SonarCloud examples are a good reference for how to present complexity and gate status to humans.[^9_10][^9_11][^9_3]


## Social / people to watch (concept level)

Rather than specific influencers, the most directly relevant “social” sources here are:

- SonarSource community and blog
    - Ongoing discussions on cognitive complexity, gate tuning, and how they balance “new code vs legacy” in quality gates.[^9_8][^9_9][^9_7]
- GitHub / CI blogs on org-wide CI templates and governance
    - Show how people build reusable promotion/quality-gate pipelines and policy-as-code for Actions.[^9_12][^9_1]

If you want, I can pull a handful of specific gate configs (complexity, coverage, severity thresholds) from these repos and threads and translate them into a `promote/config.yaml` template you can drop into your own projects.
<span style="display:none">[^9_13][^9_14][^9_15][^9_16]</span>

<div align="center">⁂</div>

[^9_1]: https://www.devopstraininginstitute.com/blog/10-cicd-quality-gates-for-production-level-reliability

[^9_2]: https://www.dhirajdas.dev/blog/ci-cd-automating-quality-gates

[^9_3]: https://github.com/SonarSource/sonarcloud_examples

[^9_4]: https://github.com/geneseframework/complexity

[^9_5]: https://github.com/Melevir/flake8-cognitive-complexity

[^9_6]: https://github.com/uudashr/gocognit

[^9_7]: https://community.sonarsource.com/t/difference-between-cognitive-cyclomatic-complexity-quality-gate-and-rule/25558

[^9_8]: https://community.sonarsource.com/t/difference-between-cognitive-cyclomatic-complexity-quality-gate-and-rule/25558/2

[^9_9]: https://samirbehara.com/2018/08/20/sonarqube-issues-with-cyclomatic-complexity-metrics/

[^9_10]: https://docs.sonarsource.com/sonarqube-cloud/getting-started/github

[^9_11]: https://www.sonarsource.com/resources/library/cyclomatic-complexity/

[^9_12]: https://github.blog/enterprise-software/devops/building-organization-wide-governance-and-re-use-for-ci-cd-and-automation-with-github-actions/

[^9_13]: https://github.com/topics/cognitive-complexity

[^9_14]: https://www.reddit.com/r/devops/comments/qdqjc8/cyclomatic_complexity_analysis_on_code_reviews/

[^9_15]: https://github.com/LorenzoBettini/sonarqube-example

[^9_16]: https://www.embedded.com/breaking-the-ci-cd-bottleneck-scaling-embedded-devops-with-containers-and-automation/


---

# Yes please, whatever you think would be valuable.

Here’s a concrete `promote/config.yaml` you can use as a starting point, with values chosen to match common quality-gate practice and the complexity discussions we’ve looked at.[^10_1][^10_2][^10_3][^10_4][^10_5][^10_6][^10_7]

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

- `/promote` reads this file, validates it, and includes its hash in the cache key so changing thresholds or tools invalidates stale phase results.[^10_2][^10_8][^10_9]
- Your per-phase skills (e1–e4) just consume the relevant section (coverage, cyclomatic, cognitive, etc.) when deciding pass/fail.
- You can tune `profiles` per repo, but the defaults above should be sane for most Python/TS-heavy projects.

<div align="center">⁂</div>

[^10_1]: https://docs.sonarsource.com/sonarqube-server/10.7/instance-administration/analysis-functions/quality-gates

[^10_2]: https://www.propelcode.ai/blog/continuous-integration-code-quality-gates-setup-guide

[^10_3]: https://www.graphite.com/guides/code-coverage-best-practices

[^10_4]: https://axify.io/blog/cyclomatic-complexity

[^10_5]: https://community.sonarsource.com/t/difference-between-cognitive-cyclomatic-complexity-quality-gate-and-rule/25558

[^10_6]: https://www.sonarsource.com/resources/library/cyclomatic-complexity/

[^10_7]: https://www.devopstraininginstitute.com/blog/10-cicd-quality-gates-for-production-level-reliability

[^10_8]: https://www.reddit.com/r/devops/comments/ua3fji/speeding_up_cicd_pipelines_with_checksums/

[^10_9]: https://zetcode.com/terms-testing/quality-gate/


---

# can we use /p for the pipeline?

Yes, `/p` is fine, with one caveat: treat it as a **thin alias** rather than the canonical name.

### Recommended pattern

- Canonical skill name: `/promote`
- Short alias: `/p` → invokes `/promote` with same arguments.

This gives you:

- Discoverability and clarity in docs (`/promote --profile=standard`).[^11_1][^11_2][^11_3]
- Speed in daily use (`/p` from any terminal), just like `g` for `git` or other short aliases.[^11_4][^11_2][^11_5]

As long as `/p` is just a front-end alias and not a separate implementation, you avoid confusion and keep your pipeline semantics in one place.
<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_6][^11_7][^11_8][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://clig.dev

[^11_2]: https://nih.ar/cli_aliases

[^11_3]: https://www.linuxjournal.com/content/boost-productivity-custom-command-shortcuts-using-linux-aliases

[^11_4]: https://www.reddit.com/r/linux/comments/1g8cyrd/any_aliass_i_should_make_for_less_typing/

[^11_5]: https://www.reddit.com/r/programming/comments/b0o6z/short_but_sweet_shell_aliases_and_global_aliases/

[^11_6]: https://news.ycombinator.com/item?id=29611317

[^11_7]: http://www.catb.org/~esr/writings/taoup/html/ch10s05.html

[^11_8]: https://stackoverflow.com/questions/18873933/new-command-line-tool-unique-name

[^11_9]: https://github.com/kriomant/pipec

[^11_10]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_pipelines?view=powershell-7.5

[^11_11]: https://www.reddit.com/r/linuxquestions/comments/kdgjef/is_it_generally_bad_to_have/

[^11_12]: https://dev.to/svhl/the-better-way-to-shorten-linux-commands-its-not-alias-17f6

[^11_13]: https://pipelight.dev/guide/cli.html

[^11_14]: https://www.reddit.com/r/bash/comments/10kxidg/bash_aliases_best_practice/

[^11_15]: https://opensource.com/article/18/8/time-saving-command-line-aliases

