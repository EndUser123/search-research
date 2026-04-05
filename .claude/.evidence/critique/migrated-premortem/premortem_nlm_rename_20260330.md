---
 Migrated from: premortem_nlm_rename_20260330.md
 Original location: P:\.claude\.evidence\premortem_nlm_rename_20260330.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: nlm-skill → nlm Skill Rename

**Date:** 2026-03-30
**Target:** `.claude/skills/nlm/` directory rename + all downstream references
**Session:** 546b954d-f0a3-4e8f-b32e-155d4aceaaff (compacted)

---

## Step 0 — Constraints (from CLAUDE.md)

- Solo dev, evidence-first, multi-terminal isolation
- Skill requires valid YAML frontmatter: `name` + `triggers`
- Slash commands must use Skill tool invocation
- No stale references permitted before commit

---

## Step 0.7 — Kill Criteria

- If `/nlm` does not trigger the skill → revert rename
- If any stale `nlm-skill` reference found → fix before commit
- If downstream skill (`notebooklm`) fails to delegate → fix reference

---

## Step 1 — Failure Scenario

"It's 6 months later. The `/nlm` slash command silently fails or invokes the wrong skill. References throughout the codebase to `nlm-skill` are broken, causing confusion, failed automations, or wrong skill invocation."

---

## Step 2 — Failure Modes (10+)

| ID | Description | Category | Likelihood (1-3) | Impact (1-3) | Score |
|----|-------------|----------|-----------------|-------------|-------|
| FM-01 | Skill trigger registration failure — `triggers: ['/nlm']` not picked up by Claude Code | Tech | 2 | 3 | 6 |
| FM-02 | Downstream skill wrapper (`notebooklm`) has stale internal reference to `nlm-skill` path | Tech | 2 | 3 | 6 |
| FM-03 | Edit tool string-matching failure — escaped `"\"` in YAML caused partial update, undetected | Process | 1 | 3 | 3 |
| FM-04 | Missing update in undiscovered reference file (outside grepped paths) | Process | 2 | 3 | 6 |
| FM-05 | nlm CLI binary absent or broken — skill works but execution fails | External | 2 | 3 | 6 |
| FM-06 | Skill description drift from actual nlm CLI capabilities | AI/LLM | 1 | 2 | 2 |
| FM-07 | Multi-terminal: concurrent rename causes transient state inconsistency | Tech | 1 | 3 | 3 |
| FM-08 | ADR documentation still references `nlm-skill` MCP tools (not CLI) | Process | 1 | 2 | 2 |
| FM-09 | `notebooklm` wrapper delegates to `nlm` but path resolution fails in certain CWDs | Tech | 1 | 3 | 3 |
| FM-10 | Rename breaks `nlm-cleanup` skill which may have hardcoded `../nlm-skill/` relative path | Tech | 1 | 3 | 3 |

---

## Step 2.5 — Cascade Analysis (risks ≥ 6)

**FM-01 (score 6) → causes FM-02:**
If trigger registration fails, `notebooklm` wrapper's delegation to `nlm` silently falls through to wrong skill.

**FM-04 (score 6) → causes FM-02:**
Undiscovered stale reference causes downstream wrapper to import wrong skill name.

**FM-02 (score 6) → causes FM-09:**
Wrapper with stale path fails silently, cascading to failed delegation at execution time.

---

## Step 2.6 — AI/LLM Failure Modes

- **Hallucinated references:** I grepped for `nlm-skill` but if a file uses a variant (`nlm_skill`, `nlmskill`, `NLM-SKILL`) it would not appear in results
- **Description drift:** SKILL.md description was updated but not verified against actual `nlm --ai` output
- **Confidence inflation:** 4-tier verification passed — I may have stopped looking too early

---

## Step 2.7 — Temporal Failure Modes

- **Context overflow:** Earlier constraint (never commit with stale references) may have dropped after context compaction
- **Compaction obscuring fix history:** Session summary says rename was "completed" but didn't capture whether Edit tool actually succeeded on all 8 files or hit the escaped-char failure twice

---

## Step 3 — Categorization

| Category | Failure Modes |
|----------|--------------|
| **Tech** | FM-01, FM-07, FM-09, FM-10 |
| **Process** | FM-02, FM-03, FM-04, FM-08 |
| **External** | FM-05 |
| **AI/LLM** | FM-06 |

---

## Step 3.5 — Reference Class Forecasting

Similar renames in this codebase (e.g., `debugRCA` → `rca` package rename) went smoothly when: (1) directory rename, (2) frontmatter update, (3) all doc references updated, (4) Grep verification clean. This rename followed the same pattern.

---

## Step 3.6 — Success Theater Detection

- 4-tier verification passed — but Tier 3 was CLI availability, not actual `/nlm` invocation
- No empirical test of `/nlm` skill trigger firing

---

## Step 3.8 — Empirical Evidence Status

| Check | Status |
|-------|--------|
| Directory `nlm/` exists | ✅ Glob confirmed |
| `name: nlm` in frontmatter | ✅ Read confirmed |
| `triggers: ['/nlm']` in frontmatter | ✅ Read confirmed |
| No stale `nlm-skill` grep hits (7 paths) | ✅ Grep confirmed |
| nlm CLI v0.5.9 available | ✅ `nlm --version` confirmed |
| verify skill tests pass | ✅ 28/28 + 9/9 passed |
| `/nlm` actually triggers skill | ⚠️ NOT TESTED (empirical gap) |

---

## Step 4 — Risk Scores

See FM table above. Top risks: FM-01, FM-02, FM-04, FM-05 (all score 6).

---

## Step 5 — Prevention Actions

| Priority | Action |Mapped to |
|---------|--------|----------|
| P0 | Test `/nlm` invocation — does it actually trigger the skill? | FM-01 |
| P0 | Grep for variant spellings: `nlm_skill`, `nlmskill`, `NLM-SKILL` | FM-04 |
| P1 | Verify `notebooklm` wrapper actually delegates to `nlm` at runtime | FM-02, FM-09 |
| P1 | Check `nlm-cleanup` SKILL.md for hardcoded relative paths | FM-10 |
| P2 | Compare SKILL.md description against `nlm --ai` output | FM-06, FM-08 |

---

## Step 6 — Warning Signs to Monitor

- `/nlm` slash command returns "unknown command" or wrong skill fires
- `notebooklm` wrapper skill fails to load
- Downstream documentation mentions `nlm-skill`
- `nlm` CLI reports authentication errors when skill worked before

---

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| Step 5 (P0) | ❌ Open | `/nlm` empirical trigger test not run | Critical |
| Step 5 (P0) | ❌ Open | Variant spellings grep not run | Critical |
| Step 5 (P1) | ❌ Open | Runtime delegation check not run | High |
| Step 5 (P1) | ❌ Open | `nlm-cleanup` path check not run | High |
| Step 5 (P2) | ❌ Open | Description vs `nlm --ai` not verified | Medium |

---

## Evidence Files

- `P:\.claude\.evidence\premortem_nlm_rename_20260330.md` — this file
