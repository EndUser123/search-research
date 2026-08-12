---
title: "Refactoring skill landscape — what /refactor is missing (2026 research)"
date_created: 2026-08-12
tags: [www-synced, reference, refactoring, best-practices, code-quality, llm-agent]
confidence: HIGH
verification_tier: 1
sources:
  - "github.com/mickeyyaya/refactoring-skills (70 skills, 66 Fowler techniques, MIT)"
  - "github.com/MuhiminOsim/code-refactoring-skill (safety tiers, Moving Invariant, MIT)"
  - "dev.to/moksh: AI Code Refactoring Tools in 2026 (CodeScene ACE, tool comparison)"
  - "arxiv.org/abs/2507.03536: ACE paper (validates refactoring improves code health)"
  - "github.com/sourcegraph/awesome-code-ai (curated AI coding tool list)"
---

# Refactoring skill landscape — what /refactor is missing

## Workspace observations (Phase 1a)

1. Our /refactor already has seam-based serial discipline, comprehensive mechanical analysis (code_analysis.py), and the newly-added Step 4.1.2 best-practices grounding.
2. The /tp review found the systemic gap: all artifacts trust agent-authored output without verification.
3. Prior wiki concepts validate our seam approach against industry baseline but identified specific gaps (dead-code detection, constant-drift detection — both since added).

## What we're missing (ranked by impact)

### 1. Named code-smell catalog (HIGH)

**What others do:** refactoring.guru catalogs 23 code smells across 5 families (Bloat, OO Abusers, Change Preventers, Dispensables, Couplers). The mickeyyaya/refactoring-skills repo maps each smell to fix techniques with risk/difficulty ratings. MuhiminOsim/code-refactoring-skill adds a 6th family (Architectural Violations: Fat Controller, UI with Business Logic, Anemic Domain Model, Layer Violation).

**Our gap:** Our code_analysis.py detects architecture smells (cyclic deps, god components) and complexity hotspots but doesn't use the standard smell vocabulary. When we say "P2: God component (fan-in ≥5 AND fan-out ≥5)," a human reviewer thinks in terms of "God Class smell." The named vocabulary matters because it maps to known fix techniques.

**Recommendation:** Add a smell-to-technique mapping table to Step 4.1. Each finding from code_analysis.py gets mapped to a named smell + the standard fix technique. This gives the operator a recognizable vocabulary and the executor a proven playbook.

### 2. Measure-before-after validation (HIGH)

**What others do:** CodeScene ACE (the standout tool from the dev.to comparison) validates that a suggested refactoring *actually improves* the code health score before surfacing it. "Every other tool generates a suggestion and hopes it is better. CodeScene runs the suggestion through a measurement pipeline and only shows it if the metrics confirm improvement." AI-generated refactorings boosted CodeScene's code health metric by 68-79% while compiling successfully 99% of the time.

**Our gap:** Our /refactor verifies tests pass after each seam (Step 6) and checks complexity didn't increase (radon cc grade check). But we don't measure whether the refactor *actually improved* the targeted metric. We can know "tests pass" and "complexity didn't get worse" without knowing "the refactor achieved its goal."

**Recommendation:** Add a Step 6 "measure delta" sub-step: before implementing a seam, record the baseline metric (complexity grade, coupling score, duplication count). After implementing, re-measure. If the metric didn't improve, the seam is flagged as `no_improvement` — the refactor was behavior-preserving but didn't achieve its structural goal.

### 3. Red/yellow line safety tiers (MEDIUM)

**What others do:** MuhiminOsim/code-refactoring-skill has explicit tiers:
- **Red Lines (stop and ask before ANY change):** public API changes, serialization format changes, concurrency behavior changes, error contract changes, files with no test coverage, files with recent concurrent edits, moving code with side effects, introducing a new architectural layer, moving code in a transaction boundary, **agentic hallucinations** (guessing file paths/symbol names/test failures instead of verifying)
- **Yellow Lines (warn, require confirmation):** renaming symbols with >20 call sites, splitting classes used in >5 modules, changing parameter order with >10 callers, inlining functions in multiple files

**Our gap:** Our /refactor has "auto-execute constraints" (P0-P2 only, evidence required) but doesn't enumerate specific categories of dangerous changes. The "irreversible risk (data wipe, untested public API break) → one short confirm" is too generic.

**Recommendation:** Add a red-line/yellow-line table to Step 6. The agentic-hallucination red line is particularly valuable — it's LLM-specific and directly relevant to our trust-the-agent pattern.

### 4. The Moving Invariant for architectural refactoring (MEDIUM)

**What others do:** MuhiminOsim names the pattern explicitly: "Never change logic AND location in the same step." Every architectural move follows: **Introduce → Redirect → Remove**, with tests passing after each sub-step. "Code-level refactoring touches 1-3 files and has a small blast radius. Architectural refactoring is multi-file by definition, moves logic across layer boundaries, and can produce behavioral differences even when the code looks identical."

**Our gap:** Our /refactor mentions "no dual-write without exit + tests" but doesn't name the Introduce → Redirect → Remove pattern. The 3-sub-step discipline is important because it makes each step independently verifiable.

**Recommendation:** Add the Moving Invariant + Introduce → Redirect → Remove pattern to Step 6.4 for seams with `category: "architecture_smell"`.

### 5. Rollback protocol (MEDIUM)

**What others do:** MuhiminOsim has an explicit rollback protocol: "On any test failure after an edit: (1) Revert the edit immediately, (2) State exactly which test failed and with which error, (3) Diagnose root cause, (4) Propose a safer decomposition. The skill never fixes forward."

**Our gap:** Our /refactor says "On verify fail: `blocked`; do not advance walk." But it doesn't mandate revert + diagnose + re-approach. The agent can leave the broken edit in place and move to a different seam.

**Recommendation:** Add a rollback protocol to Step 6: on verify fail, revert the edit, diagnose, and either re-approach with a safer decomposition or mark the seam as blocked with root cause.

### 6. Lazy-loading reference structure (LOW)

**What others do:** Both repos separate technique catalogs into multiple files loaded on demand. MuhiminOsim: "A single 60-operation reference would consume too much context. The decision tree in SKILL.md routes to exactly the catalog file needed." The skill specifies lazy-loading: agents locate sections via targeted searches and load only specific line-ranges rather than reading whole reference guides.

**Our gap:** Our /refactor is a single 720-line SKILL.md (now 800+ with 4.1.2). It loads fully every time.

**Recommendation:** Low priority — our skill works. But if it grows further, consider splitting the catalog (smells, techniques, safety model) into reference files like the repos do.

### 7. Agentic hallucination as an explicit red line (MEDIUM — LLM-specific)

**What others do:** MuhiminOsim lists "Agentic Hallucinations: Guessing file paths, symbol names, or test failures instead of verifying via active tool executions" as a red line. This is directly relevant to the trust-the-agent pattern our /tp review identified.

**Our gap:** Our /refactor has evidence bars (P0/P1 require tool-read evidence) but doesn't explicitly call out hallucination as a stop condition. The evidence bar is about *class* (P0/P1 need more evidence); the hallucination red line is about *type* (any claim about a file/symbol/test must be tool-verified, regardless of class).

**Recommendation:** Add to the red-line table from recommendation #3.

## Repos worth studying

| Repo | Stars | What it has | Why study it |
|------|-------|-------------|-------------|
| `mickeyyaya/refactoring-skills` | growing | 70 skills, 66 Fowler techniques, 23 code smells, 6 language profiles, multi-platform installer | The most comprehensive refactoring skill library; our smell catalog gap is fully covered here |
| `MuhiminOsim/code-refactoring-skill` | growing | Safety model (red/yellow lines, rollback protocol, Moving Invariant), 5-phase process, 70+ operations, 13 agent adapters | Best safety model of any refactoring skill we've seen; the agentic-hallucination red line is unique |
| `sourcegraph/awesome-code-ai` | high | Curated list of AI coding tools (assistants, completions, refactoring) | Reference for discovering new tools and patterns |
| `CodeScene/ace` (arxiv paper) | paper | Validates refactoring improves code health metric before surfacing | The measure-before-after pattern; the only tool that validates improvement, not just correctness |
| `chrisallenlane/claude-swe-workflows` | growing | SWE workflow skills including refactor | Alternative skill design for comparison |

## What we already have that others don't

Our /refactor has capabilities most public skills lack:
- **Seam-based serial discipline** — one closed structural cut at a time, with evidence bar and verify gate
- **Multi-terminal isolation** — worktree + safe-git + stale-data immunity
- **Step 4.1.2 best-practices grounding** — wiki + context7 + external (no public skill has this)
- **code_analysis.py** — AST-based cross-file analysis (most skills use grep only)
- **Integrity-first ranking (P0-P3)** — severity-based, not just smell-type-based

These are genuine differentiators. The gap is in the vocabulary (smell catalog), measurement (before/after delta), and safety model (red/yellow lines).

## Do's and don'ts

**DO:**
- Add a named smell-to-technique mapping to Step 4.1 (from refactoring.guru taxonomy)
- Add measure-before-after to Step 6 (record baseline metric, re-measure after, flag no_improvement)
- Add red/yellow line safety tiers to Step 6 (from MuhiminOsim, including agentic hallucination)
- Add Introduce → Redirect → Remove pattern for architectural seams
- Add rollback protocol (revert + diagnose + re-approach on verify fail)

**DON'T:**
- Don't replace code_analysis.py with grep-only smell detection — our AST analysis is more precise
- Don't split into 70 skills like mickeyyaya — our single-skill approach is more maintainable for our fleet
- Don't adopt CodeScene's commercial metric — use radon cc + our own coupling scores
- Don't add every Fowler technique — our executor (/go) handles implementation; /refactor plans

## Cross-references

- [[refactor-as-comprehensive-optimization-analyzer]] — what "comprehensive" means
- [[refactoring-discipline-tdd-parallel-seams-verification-gates]] — validates our seam approach
- [[refactoring-deployed-infrastructure-finding-classes]] — dead-code + constant-drift detection
- [[raising-coding-best-practices-in-ai-agents]] — coupling inventory
- [[close-py-gate-resolution-gaming]] — the trust-the-agent pattern this research reinforces
