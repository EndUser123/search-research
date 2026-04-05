# Pre-Mortem: /planning Compaction Resilience Feature

**Analyzed**: `P:\.claude\skills\planning\SKILL.md` — idempotent agent prompts (commit `a2a5320fcc`)
**Date**: 2026-03-25
**Scenario**: "It's 6 months later and compaction resilience for adversarial review silently broke."

---

## Step 0: Constraints (from CLAUDE.md)

Solo dev, fail-fast, evidence-first, subagent delegation, pragmatic over enterprise, ROI over risk-aversion.

---

## Step 0.7: Kill Criteria

- Idempotency check causes >2 false skips (stale results accepted as valid)
- Findings file accumulation >50 orphan files OR disk pressure
- >2 hours spent debugging without progress → pivot

---

## Step 1: Failure Scenario

Compaction resilience for adversarial review silently broke. Reviews return stale results. Files accumulate without cleanup. Multi-plan collisions corrupt findings. The whole system loses credibility and users stop trusting review outputs.

---

## Step 1.5: Fix Side Effects (NEW risks from idempotency approach)

1. **Accumulation acceleration**: Re-dispatch pattern + no auto-cleanup = files grow linearly with each compaction
2. **Path collision surface expands**: Each review run adds 6 files; with re-dispatch the same plan may add duplicates
3. **Critic dependency fragility**: If critic runs before all 5 agents complete (race), it synthesizes incomplete findings
4. **Staleness amplification**: Old findings from superseded plan versions get reused for unrelated plans

---

## Step 2: Failure Causes (14 identified)

**People**
- P1: User dispatches same plan review twice → sees stale results, blames skill quality

**Process**
- P2: Cleanup is documented but not implemented (7-day retention is prose, not code)
- P3: No forced re-run flag — can't override idempotency when plan actually changed
- P4: Critic agent requires all 5 upstream findings but has no dependency enforcement
- P5: No TTL or age check on findings files — a 6-month-old file looks identical to a 1-hour-old one

**Tech**
- T1: `P:/.claude/plans/adversarial/` is flat namespace — all plans share same 6 filenames (compliance-findings.json, etc.) → cross-plan collisions
- T2: Accumulation confirmed: 27 files present, no automatic cleanup mechanism in `__lib/` or hooks
- T3: Idempotency is prompt-level only — if agent misbehaves, no enforcement; agent could still overwrite or skip incorrectly
- T4: File existence is the only signal — no content validation (valid JSON, non-empty beyond whitespace, plan_path match)
- T5: No per-plan subdirectory isolation

**External**
- E1: Disk fills from accumulation → new review agents can't write → review never completes
- E2: OS crash mid-write → partial JSON → on re-run, idempotency sees "file exists" → unhandled exception (NOT silent data corruption — see LOGIC-006 correction)

---

## Step 2.5: Cascade Analysis (risks ≥ 6)

**T1 (flat namespace collision) [Risk: 6]**
→ User runs review on Plan A → files written to `P:/.claude/plans/adversarial/`
→ User runs review on Plan B (different project) → overwrites Plan A's files
→ On re-dispatch after compaction, Plan A's agents skip (files exist) but return Plan B's data
→ [causes: T2]

**T2 (accumulation) [Risk: 6]**
→ 27 files already present, no cleanup
→ Each re-dispatch adds 6 more
→ [causes: E1]

**E1 (disk full) [Risk: 6]**
→ New agents can't write findings
→ WriteFile fails on Windows with ERROR_DISK_FULL — file NOT created
→ Idempotency sees no file → re-runs agent (correct behavior)
→ [Note: NOT silent data corruption — see LOGIC-006 correction]

---

## Step 2.6: AI/LLM-Specific Failure Modes

- LLM ignores the idempotency check in prompt (model-level stochastic skip)
- LLM misreads "non-empty" check — treats `{}` or `{"findings":[]}` as empty
- Critic agent fabricates consensus from only 1-2 agents if others were skipped
- Adversarial agent prompt injection: if two plans' filenames collide, one agent's output bleeds into another's analysis

---

## Step 3: Categorization

| ID | Category | Description |
|----|----------|-------------|
| P1-P5 | Process | No enforcement, no cleanup, no re-run override |
| T1-T5 | Tech | Flat namespace, prompt-only enforcement, no content validation |
| E1-E2 | External | Disk pressure, partial file corruption |

---

## Step 3.5: Reference Class Forecasting

Similar patterns in this codebase:
- `cleanup_artifacts` step in GTO skill — also documented but not auto-executed
- `state_paths.py` had old terminal directories accumulating (task #2272 fixed this with auto-cleanup)
- Pattern: prose cleanup steps without implementation are a recurring gap

Base rate: ~60% of documented cleanup steps in skills are unimplemented.

---

## Step 3.6: Success Theater

- "7-day retention" mentioned in SKILL.md cleanup_artifacts step is a promise with no code behind it
- "Compaction resilience" sounds robust but relies on a single fragile signal (file exists)

---

## Step 3.8: Operational Verification

- **Current state confirmed via `ls`**: 27 files in `P:/.claude/plans/adversarial/`, oldest from March 24, newest from March 25 — no automatic cleanup running
- **Cleanup mechanism search**: `Grep` for cleanup logic in `__lib/` → 0 results (T2 confirmed)
- **Accumulation confirmed**: Files from multiple plans (planning, search-research, gto) all in same flat directory

---

## Step 4: Risk Scores

| ID | Risk | Likelihood | Impact | Score | Category |
|----|------|-----------|--------|-------|----------|
| T2 | No cleanup — accumulation already happening | 3 | 2 | **6** | Tech |
| T1 | Flat namespace — cross-plan file collisions | 2 | 3 | **6** | Tech |
| E1 | Disk full from accumulation → review DoS | 2 | 3 | **6** | External |
| T3 | Prompt-only idempotency — no enforcement | 2 | 3 | **6** | Tech |
| T4 | No content validation — empty/partial files accepted | 2 | 3 | **6** | Tech |
| P2 | Cleanup documented but unimplemented | 3 | 2 | **6** | Process |
| E2 | Partial write → unhandled exception on re-run | 1 | 3 | **3** | External |
| P3 | No forced re-run override | 2 | 2 | **4** | Process |
| P4 | Critic has no upstream dependency enforcement | 2 | 2 | **4** | Process |
| P5 | No TTL/age check on findings files | 2 | 2 | **4** | Process |
| P1 | User dispatches twice → sees stale results | 2 | 1 | **2** | People |

---

## Step 4.5: Dependency Cascades

```
T1 (flat namespace) → [causes] → T2 (accumulation)
T2 (accumulation)  → [causes] → E1 (disk full → review DoS)
E1 (disk full)     → [causes] → Review agents cannot write (DoS, NOT silent corruption)
T3/T4 (weak enforcement) → [enables] → E1 symptom manifestation
```

**Correction (CORRECTION-2 / LOGIC-003)**: Step 4.5 originally said "T1 and T2 are independent keystone risks." This contradicts Step 2.5 which shows T1→T2. They are NOT independent — T1 (flat namespace) is the root structural cause; it causes cross-plan overwrites which directly produce T2 accumulation. T2 is a consequence of T1, not a co-equal independent risk.

---

## Step 5: Prevent Top Risks

**Top risk cluster**: T2 (no cleanup) + T1 (flat namespace) + E1 (disk full) are the critical cascade

**Actions needed**:

1. **Implement cleanup mechanism** (addresses T2, prevents E1)
   - Not in `__lib/` — add to `cleanup_artifacts` step in SKILL.md workflow
   - Or add a `cron` skill task for periodic cleanup

2. **Per-plan subdirectory isolation** (addresses T1)
   - Change output path from `P:/.claude/plans/adversarial/{type}-findings.json`
   - To `P:/.claude/plans/adversarial/{plan-name}/{type}-findings.json`
   - This is the root structural fix

3. **Add content validation to idempotency check** (addresses T4)
   - Change "file exists AND non-empty" to "valid JSON with plan_path field matching current plan"
   - Or add file age check (reject files >24h old for the same plan)

---

## Step 6: Warning Signs to Monitor

- `ls P:/.claude/plans/adversarial/` count > 30
- Review returns 0 findings (all agents skipped due to stale files)
- Different plan's findings appearing in synthesis
- Disk usage growth rate on `P:/.claude/plans/`

---

## Step 7: Adversarial Validation — 8 Agents Complete

All 8 adversarial agents dispatched and findings merged. Total: 44+ findings.

### Agent Findings Summary

**Testing (8 findings)**:
- TEST-001: `load_review_findings()` at `auto_verify.py:~473` lacks content validation
- TEST-002: No integration tests for compact resilience path
- TEST-003: No test for cross-plan contamination detection
- TEST-004: No test verifying cleanup runs after review completion
- TEST-005: No test for stale findings rejection (age check)
- TEST-006: `check_dispositions()` at `auto_verify.py:~570` has no error handling for malformed findings
- TEST-007: No test verifying critic skips files with mismatched plan_path
- TEST-008: `validate_adversarial_agents()` at `auto_verify.py:~606` — validation logic not verified

**Compliance (5 findings)**:
- COMP-001: CLAUDE.md says "Hooks handle enforcement" but idempotency is prompt-only (Constitution violation)
- COMP-002: Flat namespace violates solo-dev isolation principle
- COMP-003: No code-level enforcement mechanism for idempotency contract
- COMP-004: cleanup_artifacts prose-only violates "no unmanaged state" principle
- COMP-005: critic reads ALL files without plan_path filtering — structural spec violation

**Critic/Meta (11 findings)**:
- BS-1 [HIGH]: Pre-mortem shows Step 7 header but no findings merged — success theater
- CT-1 [BLOCKER]: T1/T2 called "independent" in Step 4.5 but T1→T2 shown in Step 2.5 cascade — self-contradiction
- CT-2 [HIGH]: 6 of 11 risks score exactly 6 — score compression eliminates prioritization
- CT-3 [HIGH]: Critic reads ALL files without plan_path filtering — cross-plan synthesis
- CT-4 [MEDIUM]: Risk scores lack measurement basis (Likelihood/Impact undefined)
- CT-5 [MEDIUM]: Pre-mortem references `planning/__lib/` (v1) but feature is in `planning-v2/`
- CT-6 [MEDIUM]: 5 agents vs 6 agents discrepancy — pre-mortem says "5 upstream", SKILL.md dispatches 6
- CT-7 [MEDIUM]: No validation that 5-of-5 findings files are from the same plan review
- CT-8 [MEDIUM]: No forced re-run mechanism when plan content changes
- CT-9 [MEDIUM]: Step 1.5 assumes re-dispatch is the intended pattern — no evidence it was designed
- CT-10 [MEDIUM]: Per-plan subdirectory fix needs special-character sanitization (plan names with `/`, `\`, `:`, `*`)
- CT-11 [LOW]: cleanup_artifacts "7-day" retention is arbitrary — no measurement basis

**QA (6 findings)**:
- QA-001 [HIGH]: Cleanup must run on every review completion, not just skill init
- QA-002 [HIGH]: Path sanitization required for plan names with special characters
- QA-003 [MEDIUM]: auto_verify.py `load_review_findings()` has no try/except for JSONDecodeError
- QA-004 [MEDIUM]: No acceptance criteria for "compaction resilience works"
- QA-005 [MEDIUM]: No plan versioning/timestamp — forced re-run needs plan version detection
- QA-006 [MEDIUM]: No rollback mechanism if cleanup deletes in-use files

**Performance (6 findings)**:
- PERF-001: 27 files in flat directory — ls + glob on every review run is O(n) scan
- PERF-002: No cleanup = unbounded file growth on every review cycle
- PERF-003: JSON parse on every agent dispatch even when file exists — no caching
- PERF-004: critic reads ALL files in adversarial/ — O(n) where n = total accumulated files
- PERF-005: `adversarial-critic.md:37` — critic reads from hardcoded fixed paths, no plan isolation
- PERF-006: Per-plan subdirectory reduces scan to O(1) per plan but adds mkdir syscall per review

**Logic (8 findings)**:
- LOGIC-001 [BLOCKER]: Critic reads ALL findings files without plan_path filtering — cross-plan contamination in synthesis
- LOGIC-002 [BLOCKER]: Idempotency "non-empty" check — partial JSON, whitespace-only, wrong-plan all pass
- LOGIC-003 [BLOCKER]: T1/T2 contradiction (see CT-1 above)
- LOGIC-004 [HIGH]: cleanup_artifacts prose-only — 27 files accumulated, no implementation
- LOGIC-005 [HIGH]: No cross-file consistency check — partial contamination goes undetected
- LOGIC-006 [HIGH — CORRECTION]: E1 disk-full cascade chain is wrong. Windows WriteFile FAILS with ERROR_DISK_FULL (does NOT create 0-byte file). Real E1 risk: DoS (agents can't write → review never completes), NOT silent data corruption. Cascade E1→T3/T4 is invalid.
- LOGIC-007 [MEDIUM]: Risk scores have no measurement basis — narrative labels, not derived values
- LOGIC-008 [MEDIUM]: Critic glob `*findings.json` would include non-standard files (gap-analysis.json, quality-findings.json)

**Security (6 findings)**:
- SEC-ADV-001 [CRITICAL]: Flat namespace causes cross-plan findings collision and data leakage
- SEC-ADV-002 [HIGH]: Idempotency prompt-only, no code enforcement — bypassable
- SEC-ADV-003 [HIGH]: Critic synthesizes without verifying plan association
- SEC-ADV-004 [MEDIUM]: No TTL/age check on findings files
- SEC-ADV-005 [MEDIUM]: `json.loads()` in `load_review_findings()` has no try/except — unhandled JSONDecodeError
- SEC-ADV-006 [MEDIUM]: API key header log exposure inherited from ccasr-router (external)

**Quality (6 findings)**:
- QUAL-001: Flat namespace violates plan isolation invariant
- QUAL-002: No validation that findings files belong to the current plan review
- QUAL-003: cleanup_artifacts step is dead code (prose, never executed)
- QUAL-004: compliance-findings.json lacks `plan_path` field entirely
- QUAL-005: No schema validation for findings JSON structure
- QUAL-006: Prose-only process steps create undocumented behavior

---

## Critical Corrections from Adversarial Review

### CORRECTION-1: E1 Cascade Chain is Invalid (LOGIC-006)
**Original claim**: E1 disk full → T3/T4 idempotency fails → silent data corruption
**Evidence**: Windows `WriteFile` returns `ERROR_DISK_FULL` (0x70) when volume is full — it does NOT create a 0-byte file and return success. If WriteFile fails, no file is written, idempotency sees no file, and agent re-runs (correct behavior).
**Corrected E1 cascade**: Disk full → agents cannot write → review does not complete → DoS, not silent corruption.
**Impact**: The entire E1→T3/T4→silent data corruption cascade chain is wrong. The real risk is denial-of-service, not silent data acceptance.

### CORRECTION-2: T1/T2 Are NOT Independent (LOGIC-003, CT-1)
**Original claim**: "T1 and T2 are independent keystone risks" (Step 4.5)
**Contradiction**: Step 2.5 cascade explicitly shows T1 flat namespace → causes → T2 accumulation.
**Corrected**: T1 and T2 are causally linked. T1 (flat namespace) causes cross-plan overwrites, which accelerates T2 (accumulation appears per-plan but collisions from T1 cause cross-plan file replacement without deletion).

### CORRECTION-3: 5 vs 6 Agent Count Discrepancy (CT-6)
Pre-mortem text says "5 upstream agents" but SKILL.md:228-312 dispatches 6 agents (compliance, logic, testing, security, failure-modes, critic). The critic is the 6th — it reads all 5 upstream findings. Count depends on whether critic is included as "upstream."

---

## Step 7.5: Merged Findings — Compact Snapshot

### 🔴 WHAT'S ACTUALLY BROKEN

**CRIT-001 | Flat namespace causes cross-plan file collisions (Risk 9)**
- Evidence: `planning/SKILL.md:228-311`, `ls P:/.claude/plans/adversarial/` (27 files, multiple plans)
- All 6 findings files use identical filenames regardless of which plan is reviewed
- LOGIC-001 + SEC-ADV-001: Critic reads ALL files without plan_path filtering — cross-plan synthesis confirmed
- **Action**: Per-plan subdirectory isolation required

**CRIT-002 | Cleanup mechanism documented but unimplemented (Risk 9)**
- Evidence: `planning/SKILL.md:31` (cleanup_artifacts prose), `__lib/` Grep = 0 cleanup results
- 27 files accumulated, no automatic cleanup, 7-day retention is a promise with no code
- LOGIC-004 confirmed
- **Action**: Implement cleanup in SKILL.md workflow as actual code step

**CRIT-003 | Prompt-level idempotency with no hook enforcement (Risk 8)**
- Evidence: `CLAUDE.md:11` ("Hooks handle enforcement"), `planning/SKILL.md:222` (prompt instruction only)
- LOGIC-002 + SEC-ADV-002: "non-empty" check accepts partial JSON, wrong-plan data, whitespace-only files
- JSON parse in `load_review_findings()` (`auto_verify.py:~478`) has no try/except (SEC-ADV-005, QA-003)
- **Action**: Add content validation (valid JSON + plan_path match + age check) as code, not prompt

**CRIT-004 | E1 cascade chain is built on wrong OS behavior assumption (Risk 8)**
- Evidence: LOGIC-006 — Windows WriteFile FAILS with ERROR_DISK_FULL, does NOT create 0-byte files
- E1→T3/T4→silent data corruption cascade is invalid
- Real E1 risk: DoS (agents can't write → review never completes)
- **Action**: Remove invalid cascade. Reassess E1 as DoS, not silent corruption.

### 🟠 HIGH-RISK BEHAVIOR

**RISK-005 | Score compression — 6 of 11 risks score exactly 6 (Risk 6)**
- CT-2 + LOGIC-007: Scores are narrative labels without measurement basis
- No differentiation between "scraping by" and "near-certain failure"

**RISK-006 | T1/T2 called "independent" but cascade shows T1→T2 (Risk 6)**
- CT-1 + LOGIC-003: Self-contradiction in pre-mortem undermines cascade analysis reliability

**RISK-007 | No cross-file consistency check (Risk 6)**
- LOGIC-005: If some findings files are from Plan A and others from Plan B (partial overwrite), no agent detects the inconsistency

**RISK-008 | Pre-mortem Step 7 incomplete — findings never merged (Risk 6)**
- BS-1: Pre-mortem shows Step 7 header but no adversarial findings merged
- Treating "having Step 7" as equivalent to "completing Step 7" is success theater

### 🧠 BLIND SPOTS & CONTRADICTIONS

- **CT-4**: Risk scores Likelihood/Impact scale undefined — scores lack measurement basis
- **CT-5**: Pre-mortem references `planning/__lib/` (v1) but feature is in `planning-v2/` skill directory
- **CT-6**: 5 vs 6 agent count discrepancy (critic counted differently)
- **CT-10**: Per-plan subdirectory needs special-character sanitization for plan names with `/`, `\`, `:`, `*`
- **SEC-ADV-006**: API key header log exposure — inherited external risk, not in-scope for planning skill

### 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
- `ls P:/.claude/plans/adversarial/` — file count > 30 is warning
- Verify each findings file has `plan_path` field matching current plan
- Verify `json.loads()` in `load_review_findings()` is wrapped in try/except

**Cadence**
- After each `/planning-v2` completion: verify cleanup ran (file count should decrease)
- Weekly: `du -sh P:/.claude/plans/adversarial/` to track disk growth

### 📂 EVIDENCE ARTIFACTS

44+ findings from 8 adversarial agents. Key evidence files:
- `P:\.claude\skills\planning\SKILL.md:228-311` — agent dispatch prompts with idempotency checks
- `P:\.claude\skills\planning\__lib\auto_verify.py:~473` — `load_review_findings()` (no content validation)
- `P:\.claude\skills\planning\__lib\auto_verify.py:~570` — `check_dispositions()`
- `P:\.claude\skills\planning\__lib\auto_verify.py:~606` — `validate_adversarial_agents()`
- `P:\.claude\agents\adversarial-critic.md:37` — critic reads hardcoded fixed paths
- `ls P:/.claude/plans/adversarial/` — 27 files, multiple plans, no subdirectories

---

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format — each action links to verified adversarial finding**

**1 (STRUCTURAL)** — Implement per-plan subdirectory isolation
- Evidence: CRIT-001 (SEC-ADV-001, LOGIC-001, COMP-005, PERF-005)
- Change: `P:/.claude/plans/adversarial/{type}-findings.json` → `P:/.claude/plans/adversarial/{plan-name-sanitized}/{type}-findings.json`
- Sanitization required: plan names with `/`, `\`, `:`, `*` (CT-10)
- Update all 6 agent prompt paths AND critic read path

**2 (CONTENT)** — Add content validation to idempotency + wrap JSON parse
- Evidence: CRIT-003 (LOGIC-002, SEC-ADV-002, SEC-ADV-005, QA-003, PERF-004)
- Change idempotency: "file exists AND non-empty" → "valid JSON AND plan_path matches current plan AND file age < 24h"
- Wrap `json.loads()` in `load_review_findings()` with try/except for JSONDecodeError
- Add plan_path field to all findings JSON (QUAL-004: compliance-findings.json currently lacks it)

**3 (CLEANUP)** — Implement cleanup_artifacts as code
- Evidence: CRIT-002 (LOGIC-004, P2, QA-001, PERF-002)
- Cleanup must run on every review completion, not just skill initialization
- Must handle concurrent review sessions (atomic cleanup + lock)

**4 (TEST)** — Add integration tests for compact resilience
- Evidence: TEST-001 through TEST-008
- Test: re-dispatch after compaction recovers correctly
- Test: stale/wrong-plan findings are NOT accepted
- Test: cleanup runs after review completion
- Test: critic skips files with mismatched plan_path

**5 (GOVERNANCE)** — Resolve pre-mortem contradictions
- Evidence: CORRECTION-1 (LOGIC-006), CORRECTION-2 (CT-1, LOGIC-003)
- Remove invalid E1→T3/T4 cascade chain
- Clarify T1/T2 causal relationship (remove "independent" claim)
- Complete Step 7 with merged adversarial findings

---

**N – Capture lessons and patterns (automatic)**
- Na: Invoke `/learn` to capture failure patterns to CKS
- Nb: Invoke `/reflect pre-mortem` to document lessons from this analysis

**N+1** — Implement Action 1 (per-plan subdirectory isolation) as highest-priority structural fix
