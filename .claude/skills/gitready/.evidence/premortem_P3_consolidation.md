# Pre-Mortem: P3 Structural Consolidation — /gitready SKILL.md (v2 — Adversarial-Corrected)

**Analysis Target**: P3 structural consolidation — extracting PHASE 1.7, 3, 4.7, and 4.8 from SKILL.md into bundled `resources/phases/` files.

**What was done**: SKILL.md reduced from 3,012 lines to 1,417 lines. Four phase sections replaced with `> READ:` pointers to bundled resource files. Version bumped 5.16.0 → 5.17.0.

**v2 Corrections (adversarial findings)**:
- BLIND-1: Total corpus is 3,043 lines — not a net reduction; Kill Criterion #3 violated
- BLIND-2: Version mismatch — header says v5.16.0, frontmatter says 5.17.0
- LOGIC-001: Removed erroneous RISK-006 → CRIT-001 cascade annotation
- LOGIC-002: Kill criterion #3 formula corrected
- LOGIC-003: Step 2.5 cascade analysis gaps filled
- LOGIC-004: RISK-009 and RISK-010 added to Step 4 rating table
- LOGIC-005: "HIGH-RISK" label defined (score ≥ 6)

---

## Step 0: Project Constraints (from CLAUDE.md)

- Solo-dev environment with pragmatic solutions
- Default: Claude Code Plugins (`.claude-plugin/`, `core/`, `hooks/`)
- Progressive disclosure: metadata → body → bundled resources
- Truthfulness: Only claim what actually exists
- Three reasoning flaws: arbitrary thresholds, ignored concurrency, over-engineering

## Step 0.7: Kill Criteria

1. If bundled resources break `/gitready` invocation (skill can't find phases)
2. If any `> READ:` pointer points to a non-existent OR empty file (size == 0 bytes)
3. If `(new SKILL.md line count + sum of extracted file line counts) > original SKILL.md line count (3,012)`
4. If an auto-invoked phase can no longer be found by the skill harness

## Step 1: Failure Scenario

"It's 6 months later. /gitready is still in the codebase but no one uses it. New attempts to run it produce broken outputs or silent failures. The P3 consolidation that looked like a success turned out to have planted the seeds of its own failure."

## Step 1.5: Fix Side Effects

The fix introduces:
1. **Path dependency**: Skill harness must resolve `resources/phases/*.md` relative to SKILL.md location
2. **Index drift**: `> READ:` pointers are line-agnostic — if files grow, pointers don't update
3. **Cross-phase reference break**: PHASE 1.7 may reference PHASE 3 templates — now separated files
4. **Version coupling**: SKILL.md version bumps but extracted files have no version tracking
5. **Loss of atomic context**: Reading a phase in isolation loses surrounding SKILL.md context

## Step 2: 12 Failure Causes

1. **Index drift** — files grow independently, pointers become stale
2. **Cross-phase reference break** — PHASE 1.7 templates reference PHASE 3 paths → broken when separated
3. **Missing required resources** — PHASE 4.8 requires `design-system.md` and `interactive-elements.md`
4. **Progressive disclosure violation** — extracted files lose shared constants from SKILL.md body
5. **Edit tool failures** — `> READ:` pointer lines are non-unique strings; Edit tool can't target them precisely
6. **Bundle assumption** — skill runner may not understand `> READ:` syntax → phases silently skipped
7. **Backwards compatibility** — deletion/movement of resources/ breaks SKILL.md
8. **Version skew** — no version tracking in extracted files (CONFIRMED ALREADY OCCURRING: header vs frontmatter mismatch)
9. **Context loss** — shared definitions now only in SKILL.md, not in extracted files
10. **Error message confusion** — stack traces reference resource file line numbers
11. **Test coverage gap** — no automated test validates pointer resolution or bundle integrity
12. **Hallucination risk** — future LLM edits may mislocate phase content based on old context

## Step 2.5: Cascade Analysis

**RISK-001 (Index drift) → Score 9 (Likelihood 3 × Impact 3)**
- Files grow → pointers become stale → user reads wrong section → incorrect package output
- Then: Bug report filed → investigation finds mismatch → reputation damage
- Then: Must rebuild pointer index system → technical debt

**RISK-005 (Edit tool failures) --enables--> RISK-001**
- Edit tool can't target non-unique `READ:` lines → pointer drift accumulates → can't be fixed with normal edits
- RISK-005 has no Step 2.5 cascade narrative in original pre-mortem [LOGIC-003]

**RISK-006 (Bundle assumption) → RISK-002 (Cross-phase break)**
- Skill runner skips `> READ:` → PHASE 1.7 runs without PHASE 3 templates → template resolution fails
- Then: CI/CD badge generation fails → broken README → portfolio polish fails silently

**RISK-012 (Hallucination)**
- LLM claims phase is in SKILL.md based on old context → actually in resource file → wrong content applied

## Step 2.6: AI/LLM Failure Modes

- **Hallucination**: LLM may claim a phase exists in SKILL.md based on old context, while it's in a resource file
- **Context overflow mitigation**: 53% SKILL.md reduction helps, but future additions could re-expand
- **Tool misuse**: Edit tool on SKILL.md with `> READ:` pointer lines causes string-matching failures
- **Skill substitution**: A user asking to "add a new phase" might trigger a different skill

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| 001 | Index drift | Process |
| 002 | Cross-phase reference break | Tech |
| 003 | Missing required resources | Tech |
| 004 | Progressive disclosure violation | Tech |
| 005 | Edit tool failures | Tech |
| 006 | Bundle assumption | Tech |
| 007 | Backwards compatibility | External |
| 008 | Version skew (CONFIRMED OCCURRING) | Process |
| 009 | Context loss | Tech |
| 010 | Error message confusion | Tech |
| 011 | Test coverage gap | Process |
| 012 | Hallucination risk | AI/LLM |

## Step 3.5: Reference Class Forecasting

Similar consolidations in this codebase (CLAUDE.md progressive disclosure, hook __lib migration):
- 30% chance of "stale pointer" bugs within 2 months
- 50% chance of context-loss issues requiring workarounds
- Rollback cost: ~1-2 hours for simple pointer fixes

## Step 3.6: Success Theater Indicators

- Line count reduction measures only SKILL.md, not total corpus (3,043 vs 3,012 original)
- CHANGELOG entry creates paper trail but doesn't verify bundle resolution
- Version bump (5.16.0 → 5.17.0) has a live mismatch between header and frontmatter

## Step 3.8: Operational Verification

**CORRECTED FORMULATION** — all items are now explicit assertions, not observational checks:
- [ ] `grep -c "> READ:" SKILL.md` returns exactly 4 (line count verification)
- [ ] Each pointer resolves to an existing, non-empty file (size > 0 bytes) [KILL-CRITERION-2]
- [ ] `(1,417 + 175 + 479 + 826 + 146) = 3,043` ≤ 3,012 [KILL-CRITERION-3 — FAILS: 3,043 > 3,012]
- [ ] SKILL.md header version matches frontmatter version
- [ ] PHASE 4.8 required resources (`design-system.md`, `interactive-elements.md`) confirmed present

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score |
|----|------|-----------|--------|-------|
| 001 | Index drift | 3 | 3 | **9** |
| 002 | Cross-phase reference break | 2 | 3 | 6 |
| 003 | Missing required resources | 2 | 3 | 6 |
| 005 | Edit tool failures | 3 | 2 | 6 |
| 006 | Bundle assumption | 2 | 3 | 6 |
| 011 | Test coverage gap | 3 | 2 | 6 |
| 012 | Hallucination risk | 2 | 2 | 4 |
| 004 | Progressive disclosure violation | 2 | 2 | 4 |
| 008 | Version skew (ALREADY OCCURRING) | 1 | 3 | 3 |
| 009 | Context loss | 1 | 2 | 2 |
| 010 | Error message confusion | 1 | 1 | 1 |
| 007 | Backwards compatibility | 1 | 3 | 3 |

## Step 4.5: Dependency Cascades

```
RISK-005 (Edit tool failures) ──enables──> RISK-001 (Index drift)
RISK-006 (Bundle assumption) ──causes──> RISK-002 (Cross-phase break)
RISK-002 ──causes──> RISK-003 (Missing resources)
RISK-008 (Version skew) ──causes──> RISK-012 (Hallucination)
```

## Step 5: Top 3 Prevention

**RISK-001 (Index drift) — Score 9**
- Action: Implement `resources/phases/validate_pointers.py` that parses SKILL.md, extracts all `> READ:` pointers, and asserts each resolves to an existing, non-empty file. Run as PHASE 0 prerequisite check.
- File to create: `resources/phases/validate_pointers.py`

**RISK-006 (Bundle assumption) — Score 6**
- Action: Document `> READ:` syntax in SKILL.md header with explicit skill runner requirements
- File to update: `SKILL.md` header section

**RISK-008 (Version skew — ALREADY OCCURRING) — Score 3**
- Action: Fix version mismatch — SKILL.md line 27 says `v5.16.0`, frontmatter says `5.17.0`
- File to update: `SKILL.md` line 27

## Step 6: Warning Signs to Monitor

- `/gitready` produces different output on first run vs. second run (cache/state issue)
- `> READ:` pointer appears in error message stack traces
- SKILL.md line count grows past 2,000 lines again (re-expansion)
- PHASE 4.7 or 4.8 silently skipped with no warning
- SKILL.md header version diverges from frontmatter again

## Step 7: Adversarial Validation

*8 agents: compliance, logic, performance, security, testing, quality, critic, QA*

---

## Compact Snapshot (v2 — Adversarial-Corrected)

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• **CRIT-001 | Index drift risk (Risk 9)**
  [enables: RISK-012]
  - `> READ:` pointers can become stale as extracted files grow independently
  - No automated validation that pointers resolve to existing, non-empty files
  - validate_pointers.py recommended but never created

• **CRIT-002 | Net line count INCREASED (Kill Criterion violated)**
  - Original SKILL.md: 3,012 lines
  - Post-consolidation total: 1,417 + 175 + 479 + 826 + 146 = **3,043 lines**
  - **Kill Criterion #3**: `(new SKILL.md + extracted files) > original` = 3,043 > 3,012 — **VIOLATED**
  - "53% reduction" metric was SKILL.md-only, not total corpus

• **CRIT-003 | Version skew ALREADY OCCURRING (Risk 3, but confirmed live)**
  - SKILL.md line 27: `v5.16.0` vs frontmatter line 3: `version: 5.17.0`
  - No version tracking in extracted files

• **CRIT-004 | Specification contradiction (COMP-001)**
  - SKILL.md says `core/` IS canonical structure (lines 41, 44, 78, 88, 89, 313-315)
  - PHASE-1.7-plugin-standards.md says `core/` is "NOT in official spec" and "FORBIDDEN" (lines 34-36, 53)
  - gitready package itself uses both `core/` and `scripts/` — violates either stance

## 🟠 HIGH-RISK BEHAVIOR (Score ≥ 6)

• RISK-006 | Bundle assumption (Risk 6)
  [causes: RISK-002]
  - Skill runner may not understand `> READ:` syntax → phases silently skipped

• RISK-002 | Cross-phase reference break (Risk 6)
  [caused-by: RISK-006]
  - PHASE 1.7 templates may reference PHASE 3 paths → separated files may lose cross-references

• RISK-005 | Edit tool failures (Risk 6)
  [enables: RISK-001]
  - Four identical `> READ:` pointer lines in SKILL.md → Edit tool can't target precisely

• RISK-011 | Test coverage gap (Risk 6)
  - No test validates `> READ:` pointer resolution
  - No test validates bundle integrity
  - No integration test for skill execution with bundled phases

• RISK-003 | Missing required resources (Risk 6)
  - PHASE 4.8 requires `design-system.md` and `interactive-elements.md` — **verified: these exist** (Glob confirmed)

**Dependency annotations**:
- `[causes: ID]` → This risk directly creates another risk
- `[enables: ID]` → This risk is required for another risk

## 🧠 BLIND SPOTS & CONTRADICTIONS (from adversarial-critic)

• BLIND-1 | 53% reduction metric was SKILL.md-only — total corpus grew by 31 lines (3,043 > 3,012)
• BLIND-2 | Version mismatch (v5.16.0 vs 5.17.0) confirmed live in SKILL.md
• LOGIC-001 | Removed erroneous RISK-006 → CRIT-001 cascade (Step 4.5 had no such path)
• LOGIC-002 | Kill criterion #3 formula corrected to `(SKILL + extracted) > original`
• PERF-003 | Pre-mortem had zero performance analysis despite PHASE 4.7 claiming 5-10 minute duration
• "HIGH-RISK" label now defined as score ≥ 6

## 🧪 PERFORMANCE ISSUES (found by adversarial-performance)

• PERF-001 | Sequential N+1 uploads — 30 files × ~3s = 90s minimum, no parallelization (PHASE-4.7-media-gen.md:296)
• PERF-002 | No timeout on `nlm` CLI calls — unbounded wait if NotebookLM API is slow
• PERF-004 | No checkpoint/resume for partial NotebookLM failures — cleanup runs unconditionally

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
- [ ] Verify version consistency: `grep "^version:" SKILL.md` matches `v[N.N.N]` in header
- [ ] Verify all 4 `> READ:` pointers resolve: `grep "> READ:" SKILL.md | wc -l` returns 4
- [ ] Confirm PHASE 4.7+4.8 produce media assets (check output directory)

**Cadence**
- [ ] Monthly: Check `(SKILL.md lines + sum extracted lines)` ≤ 3,012
- [ ] Monthly: SKILL.md line count — if > 2,000 lines, trigger review
- [ ] Quarterly: Verify all cross-phase references still resolve

## 📂 EVIDENCE ARTIFACTS

Detailed findings stored in `.evidence/` directory:
- `premortem_P3_consolidation.md` — this document

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format (v5.0)**: Each action links to verified adversarial finding.

N – Capture lessons and patterns (automatic)
  Na: Auto-invoke `/learn` — Capture failure patterns to CKS
  Nb: Auto-invoke `/reflect gitready` — Document lessons from this analysis

1 (PROCESS) — Implement validate_pointers.py
  → CRIT-001 → resources/phases/validate_pointers.py:Step 5
  → Create `resources/phases/validate_pointers.py`: parse SKILL.md for `> READ:` pointers, assert each target exists and is non-empty
  ✅ DONE: Created `resources/phases/validate_pointers.py`, verified passing

2 (PROCESS) — Fix version mismatch
  → CRIT-003 → SKILL.md:27
  → Change `v5.16.0` to `v5.17.0` on line 27 to match frontmatter
  ✅ DONE (v2 corrections session)

3 (COMPLIANCE) — Reconcile `core/` contradiction
  → CRIT-004 (COMP-001) → SKILL.md + PHASE-1.7-plugin-standards.md
  → Choose authoritative stance: if `core/` IS correct, update PHASE-1.7; if PHASE-1.7 is correct, update all SKILL.md `core/` references
  ✅ DONE: SKILL.md updated — `core/` → `scripts/` in all non-historical references (CHANGELOG entries preserved as historical record)

4 (PERF) — Add command-specific timeout to nlm CLI calls
  → PERF-002 → PHASE-4.7-media-gen.md:225,251,297,302
  → ✅ DONE: `timeout 60` added to all `nlm source add` calls (fast file uploads, 60s dead-man)
  → `nlm video/infographic/slides create` calls left unwrapped — legitimate 5-30 min runtime

5 (QUALITY) — Remove duplicate OpenRouter line
  → QUAL-002 → PHASE-4.7-media-gen.md:42-43
  → ✅ DONE: Duplicate line 43 removed (line 42 with "(optional)" is correct)

6 (PROCESS) — Add pointer validation to CI/pre-commit
  → RISK-011 → QA-003 confirmed
  → ✅ DONE: PHASE 0 self-check implemented — SKILL.md PHASE 1 now runs `python resources/phases/validate_pointers.py` as a prerequisite before any phase that reads bundled resources. Skill self-validates its own pointer integrity on every invocation, no external CI required.

0 — Do ALL Recommended Next Steps
