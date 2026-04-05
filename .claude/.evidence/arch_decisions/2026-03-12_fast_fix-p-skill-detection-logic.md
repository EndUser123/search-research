# Architecture Decision: Fix /p Detection Logic for Pure Skills

**Date:** 2026-03-12
**Template:** fast
**Intent Type:** DEFAULT (bug fix)

---

## Decision Statement

Reorder the `/p` skill's target type classification logic (Step 2) to check **test status before project type**, ensuring pure skills with passing tests route to P2 (Review) instead of unnecessarily running P0-Skill validation.

**Root Cause:** Lines 409-415 in `P:/.claude/skills/p/SKILL.md` prioritize "SKILL.md exists in root" as the first check, causing ALL pure skills to route to P0-Skill regardless of whether tests pass or scaffold is complete.

---

## Options

**Option A:** Reorder classification logic — test status first, then project type

- **Pro:** Correctly routes skills with passing tests directly to P2 (Review), skipping redundant P0-SKILL validation
- **Pro:** Aligns with documented behavior in Detection Table where "Tests pass, never reviewed" → P2
- **Pro:** P0-SKILL only runs when scaffold is actually missing (incomplete frontmatter, missing tests/)
- **Con:** Changes evaluation order (currently type-first, becomes status-first)
- **Differs on:** Evaluation priority (type-first vs status-first)

**Option B:** Add conditional check inside P0-SKILL to skip if tests pass

- **Pro:** Minimal change to classification logic
- **Pro:** Keeps P0-SKILL as the entry point for all skills
- **Con:** P0-SKILL becomes a "router" phase that immediately exits, adding unnecessary step
- **Con:** Violates principle: phases should do their declared work, not route to other phases
- **Differs on:** Phase responsibility (router vs worker)

---

## Recommendation

**Option A** is better — test status is a higher-priority signal than project type. The Detection Table (lines 247-248) already documents that test status determines phase ("Tests failing → P1", "Tests pass, never reviewed → P2"). The classification logic (lines 409-415) contradicts this by checking project type first.

---

## Implementation

**Before (lines 407-415):**
```markdown
**First, classify target type:**

Check for these signals (in priority order):
1. **SKILL.md exists in root** → Pure skill → Run P0-Skill (skill-specific validation)
2. **pyproject.toml exists AND skill/SKILL.md exists** → Dual-nature package → Run package pipeline + skill metadata check
3. **pyproject.toml exists** → Python package → Run package pipeline (P1-P6)
4. **package.json exists** → Node package → Run package pipeline (P1-P6)
5. **go.mod exists** → Go module → Run package pipeline (P1-P6)
6. **None of the above** → Unknown/empty → Run P0 (Scaffold)
```

**After (lines 407-427):**
```markdown
**First, check test status (applies to all targets):**

Check for these signals (in priority order):
1. **No tests or tests failing** → Run P1 (Build)
2. **Tests pass, no review marker files** → Run P2 (Review)
3. **Tests pass, review markers exist, files changed since review** → Run P2 (Re-review)
4. **Tests pass, reviewed, no validation marker files** → Run P3 (Validate)

**Then, classify target type only if test status is unknown:**

Check for these signals (in priority order):
1. **SKILL.md exists in root (no pyproject.toml)** → Pure skill → Run P0-Skill (scaffold validation ONLY if missing tests/, incomplete frontmatter)
2. **pyproject.toml exists AND skill/SKILL.md exists** → Dual-nature package → Run package pipeline + skill metadata check
3. **pyproject.toml exists** → Python package → Run package pipeline (P1-P6)
4. **package.json exists** → Node package → Run package pipeline (P1-P6)
5. **go.mod exists** → Go module → Run package pipeline (P1-P6)
6. **None of the above** → Unknown/empty → Run P0 (Scaffold)

**Pure skill routing clarification:**
- If SKILL.md exists + tests pass + scaffold complete → Run P2 (Review), NOT P0-Skill
- If SKILL.md exists + scaffold incomplete (missing tests/, incomplete frontmatter) → Run P0-Skill
```

**Rollback:** Restore original lines 407-415 if the reordering causes regressions.

---

## Quick Ramifications

- **Breaks:** Nothing — this fixes a logic bug where pure skills with passing tests incorrectly route to P0-SKILL
- **Edge cases:** Pure skills without tests correctly route to P1 (Build) → P0-SKILL → P2
- **Constraints:** None — pure text change to documentation, no code execution

---

## Confidence

**Confidence: 95%** — The Detection Table (lines 247-248) explicitly documents "Tests pass, never reviewed → P2", but the implementation (lines 409-415) contradicts this by checking project type before test status. This is a documentation-implementation mismatch that the fix resolves.

**Evidence basis:**
- Line 243: "Has SKILL.md in root (no pyproject.toml) | P0-Skill" — current behavior
- Line 248: "Tests pass, never reviewed | P2 (Review)" — documented but unreachable for skills
- Lines 409-415: Classification logic prioritizes type over status
- Actual behavior observed: `/code` skill (395 passing tests) routed to P0-SKILL instead of P2

---

## Adversarial Self-Review

**Weakest assumption:** Reordering test status before project type won't break package detection.

**If wrong:** Packages might incorrectly route to P0 (Scaffold) instead of P1-P6, breaking the pipeline for all Python/Node/Go projects.

**Mitigation:** The reordering only affects the INITIAL classification. Test status checks are mutually exclusive with project type checks:
- Test status (lines 1-4): Apply to ALL targets, exit immediately if match
- Project type (lines 1-6): Only checked if test status is "unknown" (no tests directory)
- Packages with `pyproject.toml` will still match type check (line 3) since they have tests/

---

**Persisted:** 2026-03-12
**File:** `P:/.claude/arch_decisions/2026-03-12_fast_fix-p-skill-detection-logic.md`
