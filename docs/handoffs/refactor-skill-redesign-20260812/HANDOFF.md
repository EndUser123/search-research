# HANDOFF: Redesign /refactor skill

## Field 1 — Goal

Redesign `/refactor` to close the 7 gaps identified in the best-practices landscape research (`P:/.data/wiki/concepts/refactoring-skill-landscape-2026.md`), incorporating patterns from the top refactoring skill repos (mickeyyaya/refactoring-skills, MuhiminOsim/code-refactoring-skill, CodeScene ACE).

## Field 2 — Status

ready-to-implement

## Field 3 — Scope

The `/refactor` skill at `C:\Users\brsth\.grok\skills\refactor\SKILL.md` needs 7 additive enhancements (no restructuring of existing steps). Each is independent — they can be implemented as separate commits.

## Field 4 — Context

### What we already have (don't break these)

Our /refactor already has capabilities most public refactoring skills lack:
- **Seam-based serial discipline** — one closed structural cut at a time (Step 6)
- **Multi-terminal isolation** — worktree + safe-git + stale-data immunity (Steps 5, 8)
- **Step 4.1.2 best-practices grounding** — wiki + context7 + external (added this session, commit 1001e15)
- **code_analysis.py** — AST-based cross-file analysis (Step 4.1)
- **Integrity-first ranking (P0-P3)** — severity-based (Step 4.2)

### The 7 gaps to close (from `refactoring-skill-landscape-2026.md`)

Each gap has a concrete source, a specific location in SKILL.md, and a bounded change.

#### Enhancement 1: Named code-smell catalog (HIGH)

**Source:** refactoring.guru taxonomy (23 smells), mickeyyaya/refactoring-skills (66 techniques), MuhiminOsim/code-refactoring-skill (30+ smells in 6 families).

**Location:** Step 4.1, after code_analysis.py produces findings.

**Change:** Add a smell-to-technique mapping table. Each code_analysis.py finding gets mapped to a named smell from the standard taxonomy. The mapping gives the operator a recognizable vocabulary and the executor a proven fix playbook.

**Smell families to add:**
- Bloat: Long Method, Large Class, Long Parameter List, Data Clumps, Primitive Obsession
- OO Abusers: Switch on Type, Temporary Field, Refused Bequest
- Change Preventers: Divergent Change, Shotgun Surgery, Parallel Inheritance Hierarchies
- Dispensables: Duplicate Code, Dead Code, Lazy Class, Speculative Generality
- Couplers: Feature Envy, Inappropriate Intimacy, Message Chains, Middle Man
- Architectural: Fat Controller, UI with Business Logic, Anemic Domain Model, Layer Violation

**Format:** Add to `evidence_kind` field a `smell_type` sub-field mapping each finding to a named smell. Add a reference file `references/smell-catalog.md` with the full catalog + fix techniques.

#### Enhancement 2: Measure-before-after validation (HIGH)

**Source:** CodeScene ACE (arxiv 2507.03536) — "validates that a suggested refactoring actually improves the code health score before surfacing it."

**Location:** Step 6, after verify (step 6.6).

**Change:** Add a Step 6.5 "measure delta" sub-step:
1. Before implementing a seam, record baseline metrics: `radon cc` complexity grade, coupling score (fan-in/fan-out from code_analysis.py), duplication count
2. After implementing, re-measure the same metrics on the affected files
3. If the targeted metric didn't improve, flag the seam as `no_improvement` — behavior-preserving but structurally ineffective
4. Record before/after in PROGRESS.md per seam

**Why:** Currently we verify tests pass and complexity didn't increase. But we don't verify the refactor *achieved its goal*. A seam can be "tests pass, complexity stable" while being structurally pointless.

#### Enhancement 3: Red/yellow line safety tiers (MEDIUM)

**Source:** MuhiminOsim/code-refactoring-skill safety model.

**Location:** Step 6, before "Implement" (6.4).

**Change:** Add a red-line/yellow-line table:

**Red Lines (stop and ask before ANY change):**
- Public API changes (exported symbols, function signatures, module paths)
- Serialization format changes (JSON keys, database columns, proto fields)
- Concurrency behavior changes (lock ordering, async boundaries)
- Error contract changes (types thrown, messages matched by callers)
- Files with no test coverage
- Files with recent concurrent edits (check `git log --since="1 hour ago"`)
- Moving code with side effects (emails, payments, queues) between layers
- Introducing a new architectural layer where none existed
- Moving code that participates in a transaction boundary
- **Agentic hallucination:** guessing file paths, symbol names, or test failures instead of verifying via tool calls

**Yellow Lines (warn, require confirmation):**
- Renaming a symbol with >20 call sites
- Splitting a class used in >5 modules
- Changing parameter order with >10 callers
- Inlining a function present in multiple files

#### Enhancement 4: Moving Invariant for architectural seams (MEDIUM)

**Source:** MuhiminOsim/code-refactoring-skill §8.

**Location:** Step 6.4, conditional on `category: "architecture_smell"`.

**Change:** Add the Moving Invariant rule: "Never change logic AND location in the same step." For architectural seams, the implementation follows the **Introduce → Redirect → Remove** pattern with tests passing after each sub-step:

1. **Introduce** — create the new structure (new module, new interface, new layer) without changing any callers. Tests must still pass (the old path is untouched).
2. **Redirect** — migrate callers to the new structure, one caller at a time. Tests pass after each migration.
3. **Remove** — delete the old structure only after all callers are redirected. Tests must pass.

Each sub-step is a separate verify checkpoint, not a single seam.

#### Enhancement 5: Rollback protocol (MEDIUM)

**Source:** MuhiminOsim/code-refactoring-skill rollback protocol.

**Location:** Step 6, replace "On verify fail: `blocked`; do not advance walk."

**Change:** Replace with explicit rollback protocol:
1. **Revert the edit immediately** (`git checkout -- <file>` in the worktree)
2. **State exactly which test failed** and with which error
3. **Diagnose root cause** — why did the refactor break the test?
4. **Propose a safer decomposition** — either a smaller seam or a different approach
5. Do NOT fix forward. A refactoring that breaks a test is reverted, diagnosed, and re-approached safely.

#### Enhancement 6: Agentic hallucination red line (MEDIUM — subsumed by Enhancement 3)

This is the LLM-specific red line from Enhancement 3. Already included as the last item in the red-line table. No separate implementation needed.

#### Enhancement 7: Step 4.1.2 gaming-vector fix (MEDIUM)

**Source:** /tp review of this session — Step 4.1.2 has gaming vectors (no validator checks that wiki grep ran, no citation backcheck).

**Location:** Step 4.1.2.

**Change:** Add two structural enforcement mechanisms:

1. **Side-effect artifact:** Step 4.1.2 MUST write a `best_practices_audit.json` to `$runDir` recording:
   ```json
   {
     "wiki_concepts_read": ["concept-1.md", "concept-2.md"],
     "context7_queries": [{"library": "WXT", "result_size_kb": 45}],
     "external_searches": [{"query": "...", "results_count": 5}],
     "sources_found": true,
     "timestamp": "<iso>"
   }
   ```
   If this file is missing, the plan CANNOT advance to Step 4.2 (ranking). This prevents the "no grounding sources found" escape hatch from being used without actually checking.

2. **Citation backcheck (lightweight):** for each finding with `evidence_kind: "wiki_best_practice"`, verify the cited concept path exists. This is a `Test-Path` check, not a content check — it catches fabricated citations without being expensive.

## Field 5 — Done criteria

- [ ] Enhancement 1: Named smell catalog added to Step 4.1 with `references/smell-catalog.md`
- [ ] Enhancement 2: Measure-before-after (Step 6.5) with baseline recording in PROGRESS.md
- [ ] Enhancement 3: Red/yellow line safety tiers table added to Step 6
- [ ] Enhancement 4: Moving Invariant + Introduce → Redirect → Remove pattern for architecture seams
- [ ] Enhancement 5: Rollback protocol replacing "blocked, don't advance"
- [ ] Enhancement 7: `best_practices_audit.json` side-effect artifact + citation backcheck in Step 4.1.2
- [ ] All changes pass `/skill-dev measure refactor` static checks
- [ ] Skill version bumped in frontmatter

## Field 6 — Constraints

- **Don't restructure existing steps.** All 7 enhancements are additive to existing steps.
- **Don't replace code_analysis.py.** Our AST analysis is more precise than grep-only smell detection.
- **Don't split into multiple skills.** Our single-skill approach is more maintainable for our fleet.
- **Don't adopt CodeScene's commercial metric.** Use radon cc + our own coupling scores.
- **Don't add every Fowler technique.** Our executor (/go) handles implementation; /refactor plans.
- **File location:** `C:\Users\brsth\.grok\skills\refactor\SKILL.md` (user scope, not workspace scope).
- **Test after changes:** run `/skill-dev measure refactor` to verify the changed skill passes static checks.

## Field 7 — Evidence

- **Landscape research:** `P:/.data/wiki/concepts/refactoring-skill-landscape-2026.md` (commit 5f95b68)
- **Step 4.1.2 (already shipped):** `C:\Users\brsth\.grok\skills\refactor\SKILL.md` Step 4.1.2 (commit 1001e15)
- **Step 4.1.2 gaming vectors:** /tp review subagent findings (subagent 019ff609)
- **Prior refactor research:** `P:/.data/wiki/concepts/refactor-as-comprehensive-optimization-analyzer.md`
- **Prior TDD validation:** `P:/.data/wiki/concepts/refactoring-discipline-tdd-parallel-seams-verification-gates.md`
- **Trust-the-agent pattern:** `P:/.data/wiki/concepts/close-py-gate-resolution-gaming.md`

## Field 8 — Verbatim last user message

"/handoff to redesign '/refactor'."

## Field 9 — Cross-reference couplings

- `[[refactoring-skill-landscape-2026]]` — the research driving this redesign
- `[[refactor-as-comprehensive-optimization-analyzer]]` — prior research on what "comprehensive" means
- `[[refactoring-discipline-tdd-parallel-seams-verification-gates]]` — validates seam approach
- `[[refactoring-deployed-infrastructure-finding-classes]]` — dead-code + constant-drift detection (already added)
- `[[close-py-gate-resolution-gaming]]` — trust-the-agent pattern (Enhancement 7 addresses this)
- `[[coupling-inventory-as-mandatory-design-section]]` — coupling inventory pattern

---

produced_at: 2026-08-12T12:50:00Z
current_session_id: 019fee39-abb7-7490-a66a-e2cd7df5600a
accurate_as_of_head: 5f95b68
head: OK
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019fee39-abb7-7490-a66a-e2cd7df5600a
