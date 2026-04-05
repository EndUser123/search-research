---
 Migrated from: premortem_gto_project_root_removal_20260402_083105.md
 Original location: P:\.claude\.evidence\premortem_gto_project_root_removal_20260402_083105.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: GTO `--project-root` Removal + Test Import Fixes

**Date:** 2026-04-02
**Target:** GTO v3.4→v3.6 — `--project-root` CLI removal + `arch/tests/test_persistence.py` import path fixes
**Analyst:** Claude Code (solo dev)

---

## Step 0 — Project Constraints (CLAUDE.md)

- **Solo dev context**: ROI over risk-aversion, pragmatic solutions
- **Sequential file operations**: Execute modifications ONE AT A TIME — race conditions from parallel Edit/Write
- **Verification before claiming**: Unverified absence claims prohibited; re-verify before asserting
- **Terminal isolation**: Each terminal has isolated state
- **Contract discipline**: explicit input/output schema, required fields, source of truth, freshness/invalidation, isolation boundary
- **Python dev**: Always add type hints, use pytest

---

## Step 0.7 — Kill Criteria

- If >60min of analysis time, stop and surface current findings
- If adversarial agent dispatch fails (3+ agents error), abort Phase 2
- If evidence file write fails (disk space, permissions), abort

---

## Step 1 — Failure Scenario

**"It's 6 months later and GTO is producing non-deterministic gap analysis. Users get wildly different results depending on how they invoke GTO — with `--project-root`, without it, from different terminals. The `--project-root` removal caused silent behavioral regressions that went undetected."**

---

## Step 1.5 — Fix Side Effects

### Change 1: `--project-root` removal from GTO CLI
- **NEW**: GTO now **always** relies on session context auto-detection — no override possible
- **NEW**: Users who depended on `--project-root` have no migration path
- **NEW**: GTO answers "what's broken in X?" where X is auto-detected, which may differ from user intent

### Change 2: `skill.persistence` → `arch.persistence` import fix
- **NEW**: Tests now correctly mock `arch.persistence` module
- **NEW**: Test isolation improved — tests no longer depend on implicit `skill.persistence` module

---

## Step 2 — Brainstorm Causes (Multi-Perspective)

### People
1. **P1**: Dev removed `--project-root` but didn't add deprecation notice or changelog entry — users unaware
2. **P2**: Dev didn't run GTO assertions after removal to verify behavior unchanged for auto-detected targets

### Process
3. **P3**: No integration test verifies auto-detection priority ordering works correctly
4. **P4**: Changelog entry missing for v3.4 removal (CLAUDE.md constitutional rule: keep CHANGELOG for breaking changes)

### Tech
5. **T1**: Session context auto-detection fails silently when transcript is missing/empty → defaults to `cwd` which may be wrong target
6. **T2**: `sys.path` manipulation in `test_persistence.py` could bleed into other test modules if tests run in wrong order
7. **T3**: Multi-terminal GTO invocations share state file (`.evidence/gto-state-*.json`) with same terminal_id → collision risk

### External
8. **E1**: IDE integration tests use different working directory than CLI, causing auto-detection to pick different targets

---

## Step 2.6 — AI/LLM Failure Modes
- LLM context overflow causes session context to be silently discarded → wrong target auto-detected
- Handoff chain breaks between compaction boundaries, losing auto-detection signal

---

## Step 2.7 — Temporal Failure Modes
- "What was the target again?" — session context stale after compaction, GTO picks `cwd` as fallback
- Earlier GTO run's state file (`.evidence/gto-state-*.json`) incorrectly read as current session's context

---

## Step 2.8 — Contract/Interruption Failure Modes
- Resume artifact partial but treated as complete — assertions pass but gap list is incomplete
- Producer (GTO) wrote gap list but consumer (skill mapper) never validated recommendations
- Contract Authority Packet exists at producer but consumer doesn't read it

---

## Step 3 — Categorization

| ID | Category | Root Cause |
|----|----------|------------|
| P1 | People | Missing deprecation notice |
| P2 | People | No post-removal verification |
| P3 | Process | No auto-detection priority test |
| P4 | Process | Missing changelog entry |
| T1 | Tech | Auto-detection silent fallback |
| T2 | Tech | sys.path test isolation |
| T3 | Tech | Multi-terminal state collision |
| E1 | External | IDE vs CLI working directory |

---

## Step 3.5 — Reference Class

Historical: TASK-2275 (pid reuse caused 10,700 empty state directories) — same pattern as T3 (terminal_id reuse across sessions).

---

## Step 3.6 — Success Theater
- "13/13 tests pass" proves test import fixes work — doesn't prove auto-detection fallback works correctly
- "GTO runs successfully" without `--project-root` proves nothing about correct target selection

---

## Step 3.8 — Operational Verification

- **T1**: `gto_orchestrator.py` — `run()` method uses `cwd` as fallback when session context is empty; need to verify that path actually leads to valid target
- **T3**: Multi-terminal state — `get_state_path()` in orchestrator uses `terminal_id`; need to verify `terminal_id` uniqueness across terminals
- **P3**: Auto-detection priority — no test corpus verifies that "recent file edits" correctly selects target over "last resort cwd"

---

## Step 4 — Risk Ratings

| ID | Risk | L | I | Score | Conf |
|----|------|---|---|-------|------|
| P1 | Missing deprecation for `--project-root` | 3 | 2 | 6 | HIGH |
| T1 | Auto-detection silent fallback to cwd | 2 | 3 | 6 | MED |
| T3 | Multi-terminal state collision | 2 | 3 | 6 | MED |
| P3 | No auto-detection priority test | 2 | 2 | 4 | MED |
| P4 | Missing changelog entry | 2 | 1 | 2 | HIGH |
| T2 | sys.path test bleed | 1 | 2 | 2 | LOW |
| E1 | IDE vs CLI directory mismatch | 1 | 2 | 2 | LOW |

---

## Step 4.5 — Dependency Cascades

- **T1** [causes]: T3 — if auto-detection silently falls back to `cwd`, and `cwd` is same across terminals, state collision more likely
- **P1** [causes]: P4 — no deprecation means no changelog, no way to trace removal

---

## Step 5 — Top Prevention Actions

1. **P1 → Add deprecation notice to SKILL.md**: Document `--project-root` removal and auto-detection as replacement
2. **T1 → Add auto-detection validation**: GTO should emit warning when falling back to `cwd`
3. **T3 → Verify terminal_id uniqueness**: Check `get_state_path()` handles concurrent access correctly

---

## Step 6 — Warning Signs

- GTO output mentions "analyzing `{cwd}`" when user expected different target → auto-detection failed
- Error: "State file locked" or JSON parse errors on `.evidence/gto-state-*.json` → terminal_id collision
- User report: "GTO gave different results in Terminal B vs Terminal A" → state collision

---

## Step 7 — Adversarial Validation

### Phase 1 Artifacts

Target analysis file: `P:/.claude/.evidence/premortem_gto_project_root_removal_20260402_083105.md`

---

## ✅ RECOMMENDED NEXT STEPS

### BLOCKING BEFORE IMPLEMENTATION

**RISK-P1** - Missing deprecation notice for `--project-root` removal
  Type: ROOT-CAUSE FIX
  Owner: `/planning`
  Blocking: yes
  Survives compaction: yes
  Why: Users who relied on `--project-root` have no migration path. Silent breakage is worse than documented removal.
  Prevention action:
  Add deprecation notice to SKILL.md documenting: (1) `--project-root` removed in v3.4, (2) auto-detection is the replacement, (3) session context priority order.
  Proof action:
  Read SKILL.md and verify deprecation notice exists with v3.4 removal note.

**RISK-T1** - Auto-detection silent fallback to `cwd` with no validity check
  Type: ROOT-CAUSE FIX
  Owner: `/arch`
  Blocking: yes
  Survives compaction: yes
  Why: GTO could analyze an invalid/non-Claude directory silently when session context is stale.
  Prevention action:
  Add target validity check in `gto_orchestrator.py`: verify `.claude` directory or `CLAUDE.md` exists before analyzing. Emit warning when falling back to `cwd`.
  Proof action:
  Run GTO from `/tmp` (non-Claude dir) — should emit warning, not silent analysis.

**RISK-T3** - Terminal ID collision across concurrent GTO invocations
  Type: ROOT-CAUSE FIX
  Owner: `/verify`
  Blocking: yes
  Survives compaction: yes
  Why: Second-level timestamp precision + hostname-pid in `gto_orchestrator.py:164` causes state collision when multiple GTO runs start in same second. Confirmed by consensus (3 agents: quality, security, testing).
  Prevention action:
  Unify terminal_id algorithm across `gto_orchestrator.py`, `state_manager.py`, and `gto_assertions.py`. Add sub-second precision or random component.
  Proof action:
  Run two GTO instances simultaneously — verify separate state files created (no collision).

**RISK-T4** - Sequential correctness agent dispatch (900s worst-case timeout)
  Type: SYMPTOM PATCH
  Owner: `/planning`
  Blocking: no
  Survives compaction: yes
  Why: 3 × 300s sequential timeouts = 900s worst case for correctness mode.
  Prevention action:
  Evaluate parallel dispatch for correctness agents or add `--no-correctness` as default with explicit opt-in.
  Proof action:
  Time correctness mode on a small target — should complete in <60s if sequential, <30s if parallel.

### BLOCKING BEFORE VERIFIED

**RISK-T2** - GTO assertions CLI not tested after `--project-root` removal
  Type: PROOF / CERTIFICATION
  Owner: `/verify`
  Blocking: yes
  Depends on: `RISK-P1`
  Survives compaction: yes
  Why: `evals/gto_assertions.py` has its own terminal_id logic copy. Changes to orchestrator don't propagate. Assertions could validate wrong state.
  Prevention action:
  None. This is a verification obligation.
  Proof action:
  Run `python gto_assertions.py` after a GTO run — verify it correctly identifies the state directory used.

**RISK-T5** - StateManager.append_history() TOCTOU not fully mitigated
  Type: PROOF / CERTIFICATION
  Owner: `/verify`
  Blocking: yes
  Survives compaction: yes
  Why: Lock on `.history.lock` is advisory on FAT32/network shares. JSONL corruption under concurrent writes is possible.
  Prevention action:
  None. This is a verification obligation.
  Proof action:
  Concurrent append_history() from 2 processes — verify JSONL integrity (no partial lines, no corruption).

### HARDENING / FOLLOW-UP

**RISK-B1** - Blind spot: StateManager uses different terminal_id algorithm than orchestrator
  Type: ROOT-CAUSE FIX
  Owner: `/arch`
  Blocking: no
  Survives compaction: yes
  Why: `state_manager.py:113-129` uses `hostname+pid` while `gto_orchestrator.py:164` uses `PID+timestamp`. Container environments with identical hostname get collision.
  Prevention action:
  Audit all terminal_id generation sites — unify to single algorithm with container-aware fallback.
  Proof action:
  Read state_manager.py and gto_orchestrator.py — verify same algorithm.

**RISK-B2** - sys.path manipulation without cleanup in test files
  Type: ROOT-CAUSE FIX
  Owner: `/qa`
  Blocking: no
  Survives compaction: no
  Why: `test_persistence.py:19` and `test_state_manager.py:8` insert paths without cleanup. pytest can leave stale entries.
  Prevention action:
  Use `pytest fixtures` with `tmp_path` or `monkeypatch` for sys.path changes, ensure cleanup.
  Proof action:
  Run full pytest suite, verify no sys.path pollution between test files.

**RISK-B3** - QA blind spot: No test for auto-detection priority ordering
  Type: ROOT-CAUSE FIX
  Owner: `/testing`
  Blocking: no
  Survives compaction: yes
  Why: No test corpus verifies "recent file edits" > "cwd" priority. Could silently reverse.
  Prevention action:
  Create test with known recent edit file — verify GTO picks that project over cwd.
  Proof action:
  Run test — verify auto-detection priority ordering works as documented.

0 — Do ALL Blocking Steps First
