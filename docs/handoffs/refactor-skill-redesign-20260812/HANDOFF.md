# HANDOFF: Redesign /refactor skill

## Field 1 — Goal

Redesign `/refactor` to close the 7 gaps identified in the best-practices landscape research (`P:/.data/wiki/concepts/refactoring-skill-landscape-2026.md`), incorporating patterns from the top refactoring skill repos (mickeyyaya/refactoring-skills, MuhiminOsim/code-refactoring-skill, CodeScene ACE).

## Field 2 — Status

needs-revision (P0 findings from /tp review addressed below — Rev 2)

## Field 3 — Scope

The `/refactor` skill at `C:\Users\brsth\.grok\skills\refactor\SKILL.md` needs 6 additive enhancements. Each can be implemented as a separate commit, but they build on each other sequentially (not fully independent). **Step 6 is explicitly on the table for restructuring** (Enhancements 4 and 5 modify Step 6 sub-steps). Steps 1-5 and 7-9 are not restructured.

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

#### Enhancement 1: Named code-smell catalog (HIGH — revised)

**Source:** refactoring.guru taxonomy (23 smells), mickeyyaya/refactoring-skills (66 techniques), MuhiminOsim/code-refactoring-skill (30+ smells in 6 families).

**Location:** Step 4.1, after code_analysis.py produces findings.

**P0 fix (Rev 2):** code_analysis.py only emits 5 finding categories today (complexity_hotspot, duplication, test_gap, dead_code, architecture_smell with 2 types). The full 24-smell catalog is forward-looking — 22 of 24 smells have no current detector. Ship ONLY the mappings that code_analysis.py actually emits:

| code_analysis.py finding | Named smell |
|---|---|
| complexity_hotspot (radon grade C+) | Long Method |
| duplication (AST-based) | Duplicate Code |
| god_component (fan-in ≥5 AND fan-out ≥5) | Large Class / God Object |
| dead_code (vulture ≥60%) | Dead Code |
| test_gap | (no smell mapping — it's a process gap, not a code smell) |

List the remaining 19 smells in `references/smell-catalog.md` under a "Future detectors" section. Don't ship a hollow vocabulary.

**Schema note (P0 fix):** Do NOT change `evidence_kind` from a flat string enum to a sub-field. Add `smell_type` as a **separate optional field** on each seam, defaulting to null. This is backward-compatible with existing seams.json files.

#### Enhancement 2: Measure-before-after validation (HIGH — revised)

**Source:** CodeScene ACE (arxiv 2507.03536) — "validates that a suggested refactoring actually improves the code health score before surfacing it."

**Location:** Step 6, after verify (step 6.6).

**P0 fix (Rev 2):** The binary `no_improvement` flag was too simplistic — refactoring a god module into smaller ones can reduce original fan-out while increasing fan-in at the new coordinator. Replace with **multivariate measurement**:

1. Before implementing, record baseline: radon cc grade, fan-in, fan-out, duplication count
2. After implementing, re-measure all metrics
3. Record before/after in PROGRESS.md as a **delta table**, not a binary flag
4. Flag `no_improvement` ONLY when ALL metrics worsened or stayed flat AND no trade-off is documented
5. When metrics trade off (e.g., complexity↓ coupling↑), document the trade-off explicitly in the seam's `notes` field

**Metric definitions:** use radon cc (complexity) + code_analysis.py fan-in/fan-out (coupling) + AST-based duplication count. Do not adopt CodeScene's commercial CodeHealth metric.

#### Enhancement 3: Red/yellow line safety tiers (MEDIUM — revised)

**Source:** MuhiminOsim/code-refactoring-skill safety model.

**Location:** Step 6, before "Implement" (6.4).

**P0 fix (Rev 2):** The original "Files with no test coverage" red line deadlocked the P3 test-gap fix loop (P3 says "add characterization test" but the red line says "stop if no coverage"). Reword to: **"Files with no test coverage AND no characterization plan — stop. Files with no coverage but a characterization test IS the seam — proceed."**

**Red Lines (stop and ask before ANY change):**
- Public API changes (exported symbols, function signatures, module paths)
- Serialization format changes (JSON keys, database columns, proto fields)
- Concurrency behavior changes (lock ordering, async boundaries)
- Error contract changes (types thrown, messages matched by callers)
- **Files with no test coverage AND the seam is NOT the characterization test**
- Files with recent concurrent edits (check `git log --since="1 hour ago"`)
- Moving code with side effects (emails, payments, queues) between layers
- Introducing a new architectural layer where none existed
- Moving code that participates in a transaction boundary
- **Agentic hallucination:** claiming file paths/symbol names/test results without tool-verified evidence

**Yellow Lines (warn, require confirmation):**
- Renaming a symbol with >20 call sites
- Splitting a class used in >5 modules
- Changing parameter order with >10 callers
- Inlining a function present in multiple files

**Threshold note:** the >20 call sites / >5 modules thresholds should be calibrated against the workspace's actual symbol fan-in distribution (from code_analysis.py). For packages with naturally high fan-in (like yt-is), raise the threshold; for small utility packages, lower it.

#### Enhancement 4: Moving Invariant for architectural seams (MEDIUM — revised)

**Source:** MuhiminOsim/code-refactoring-skill §8.

**Location:** Step 6.4, conditional on `category: "architecture_smell"`.

**P0 fix (Rev 2):** The original proposal didn't reconcile with the existing walk budget (3 seams) or the existing P0 example. Clarify:

- **Introduce → Redirect → Remove counts as 3 sub-steps within 1 seam** (not 3 seams against budget). The seam is one architectural change; the 3 sub-steps are verify checkpoints within that seam.
- The existing "fail-closed mapping" P0 example (SKILL.md lines 497-510) changes logic AND removes a code path in one seam. This is a **code-level refactor** (not architectural), so the Moving Invariant doesn't apply to it. The Invariant only applies to `category: "architecture_smell"` seams where code moves across layer boundaries.
- **The Moving Invariant:** "Never change logic AND location in the same step." Every architectural move follows: **Introduce** (create new structure, old untouched, tests pass) → **Redirect** (migrate callers one at a time, tests pass after each) → **Remove** (delete old structure only after all callers redirected, tests pass).

Each sub-step is a separate verify checkpoint, but all 3 sub-steps are within the single seam's scope.

#### Enhancement 5: Rollback protocol (MEDIUM — revised)

**Source:** MuhiminOsim/code-refactoring-skill rollback protocol.

**Location:** Step 6, replace "On verify fail: `blocked`; do not advance walk."

**P0 fix (Rev 2):** The original `git checkout -- <file>` doesn't work after commit-per-seam (the bad edit is committed; checkout reverts to HEAD which includes it). And "do NOT fix forward" is wrong for trivial root causes. Revised protocol:

1. **Revert the edit:**
   - Uncommitted: `git checkout -- <file>` in the worktree
   - Committed (commit-per-seam mode): `git revert HEAD --no-edit` (creates a follow-up commit, never rewrites history — operator-consistent)
2. **State exactly which test failed** and with which error
3. **Diagnose root cause** — why did the refactor break the test?
4. **Choose recovery path:**
   - **Trivial root cause** (typo, missing import, wrong variable name): **fix forward** — apply the one-line fix and re-verify
   - **Architectural root cause** (wrong decomposition, missing dependency): **re-approach** — propose a safer decomposition
5. Record the revert + diagnosis + recovery in PROGRESS.md

#### Enhancement 6: Agentic hallucination red line (MEDIUM — subsumed by Enhancement 3)

This is the LLM-specific red line from Enhancement 3. Already included as the last item in the red-line table. No separate implementation needed.

#### Enhancement 7: Step 4.1.2 gaming-vector fix (MEDIUM — revised)

**Source:** /tp review of this session — Step 4.1.2 has gaming vectors (no validator checks that wiki grep ran, no citation backcheck).

**P0 fix (Rev 2):** The original Test-Path check catches dangling references but not fabricated findings. The agent can cite 5 real concepts by path without actually reading them. Replace with **content-backed cross-reference**:

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
   If this file is missing, the plan CANNOT advance to Step 4.2 (ranking).

2. **Content-backed citation check (not just existence):** for each finding with `evidence_kind: "wiki_best_practice"`, grep the cited concept body for a keyword from the finding's title. If the finding is "Missing .catch on async handlers" and the cited concept is `chrome-acp-library-stack-and-best-practices-2026.md`, grep for "catch" or "async" in the concept. If the keyword doesn't appear, the citation is irrelevant — flag as `citation_mismatch`.

3. **Provenance cross-check for context7:** the audit file records context7 library IDs. If the agent's finding cites a context7 result but the audit file shows no context7 query for that library, the finding is fabricated.

**`--lite` propagation:** `--lite` mode skips external research (Source 3) but the audit file is still mandatory for Sources 1-2. A `--lite` run with no audit file cannot advance to Step 4.2.

## Field 5 — Done criteria

- [ ] Enhancement 1: Named smell catalog with only the 4-5 mappings code_analysis.py emits today + `references/smell-catalog.md` with future detectors section
- [ ] Enhancement 2: Measure-before-after (Step 6.5) with multivariate delta table in PROGRESS.md
- [ ] Enhancement 3: Red/yellow line safety tiers with deadlock-free "no coverage" wording
- [ ] Enhancement 4: Moving Invariant + Introduce → Redirect → Remove (1 seam, 3 sub-steps, architecture_smell only)
- [ ] Enhancement 5: Rollback protocol with `git revert HEAD` for commit-per-seam + fix-forward for trivial causes
- [ ] Enhancement 7: `best_practices_audit.json` side-effect + content-backed citation check + `--lite` propagation
- [ ] All changes pass `/skill-dev measure refactor` static checks
- [ ] Runtime test-fire: run `/refactor --lite` against a fixture package, confirm seams.json produced + audit file written
- [ ] Test fixture created under `C:/Users/brsth/.grok/skills/refactor/tests/` with one known-smell package
- [ ] Skill version bumped in frontmatter

## Field 6 — Constraints

- **Don't restructure Steps 1-5 and 7-9.** Step 6 IS on the table (Enhancements 4 and 5 modify Step 6 sub-steps).
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
