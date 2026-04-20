# Review Bundle: cc-skills-sdlc — tdd_v3.2

**Generated:** 2026-04-20
**Scope:** `P:/packages/cc-skills-sdlc/skills/tdd_v3.2`
**File Count:** 18 files (2-agent parallel scan)
**Execution Mode:** 2-agents (Explorer + Core Reader/Config)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated:** 2026-04-20
- **Scope:** `P:/packages/cc-skills-sdlc/skills/tdd_v3.2`
- **File Count:** 18 files
- **Execution Mode:** 2-agents

### Domain & Purpose

`tdd_v3.2` is a strict Test-Driven Development protocol skill for Claude Code. All test execution routes through `run_phase.py` which produces HMAC-signed receipts. The standalone validator checks receipt signatures, log integrity, temporal ordering, and exit codes. The skill operates in three modes (feature, bugfix, refactor) and is designed for Windows 11 optimization with O(1) active session tracking.

### Scale Metrics

| Metric | Value |
|--------|-------|
| Total files | 18 |
| Python files | 8 |
| Test files | 4 |
| Reference docs | 5 |
| Major subsystems | 5 (session, run_phase, validate, gap_loader, evidence) |
| Workflow phases | 7 (DISCOVER → RED → GREEN → REFACTOR → VERIFY → REGRESSION → CLOSURE) |
| Enforcement | strict (advisory hooks, mandatory protocol) |

### Environment

- **OS:** Windows 11 Pro (assumed from skill design)
- **Shell:** Bash (Git Bash)
- **Primary Language:** Python 3.12+
- **Package Managers:** None (no requirements.txt)
- **Test Runners:** Auto-detected: `pytest`, `npx jest`, `npx vitest`, `go test`, `cargo test`, `npm test`

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /tdd [mode] "description"
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  generate_context.py — Session Initialization              │
│  ├─ Clean stale runs (>3600s)                            │
│  ├─ Detect test framework (pytest/jest/vitest/go/cargo)  │
│  ├─ Create session.json with HMAC secret (32-byte hex)   │
│  ├─ Write .active_run pointer (O(1) active check)        │
│  └─ Print SOP + workspace symbols                         │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  run_phase.py — Test Execution Wrapper (all phases)      │
│  ├─ Validate phase transition (state machine)            │
│  ├─ Validate CWD within session tree (monorepo support)  │
│  ├─ Execute test command via subprocess.run()            │
│  ├─ Write stdout/stderr logs                             │
│  ├─ Compute SHA256 hashes of logs                        │
│  ├─ Build PhaseReceipt, HMAC-sign with session secret    │
│  └─ Advance session.phase monotonically                  │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  validate_tdd.py — TDD Cycle Validator                    │
│  ├─ HMAC signature verification (timing-safe)            │
│  ├─ Log SHA256 hash verification (tampering detection)    │
│  ├─ RED must fail (exit_code ≠ 0, failure pattern)     │
│  ├─ GREEN must pass (exit_code = 0, pass pattern)       │
│  ├─ Temporal ordering (GREEN ≥ RED timestamps)          │
│  ├─ Distinctness (RED ≠ GREEN stdout)                    │
│  └─ REFACTOR (if claimed): receipt + pass + distinct    │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  Hooks (external to skill directory)                     │
│  ├─ preflight_require_tdd.py  — pre_prompt, blocks     │
│  └─ stop_if_tdd_unverified.py — pre_response, blocks    │
└──────────────────────────────────────────────────────────┘
```

### Phase State Machine

```
Phase transitions (enforced by run_phase.py):
  init → red → green → refactor → validated

Allowed transitions:
  RED     ← init
  GREEN   ← red
  REFACTOR ← green

_MAX_RETRIES = 3 (validate_tdd.py)
_STALE_THRESHOLD = 3600 seconds (generate_context.py)
```

---

## 3. EXECUTION AND DATA FLOW

### Mode: feature / bugfix / refactor

**Shared SOP (all modes):**
1. DISCOVER — Read source, check `/t` gaps
2. RED — Write failing tests via `run_phase.py --phase red`
3. GREEN — Minimal implementation via `run_phase.py --phase green`
4. REFACTOR — Optional cleanup via `run_phase.py --phase refactor`
5. VERIFY — Mandatory integration validation
6. REGRESSION — Targeted tests after VERIFY
7. CLOSURE — Bug-fix only: grep for similar patterns

**Bug-fix additions:**
- YAGNI constraint enforced
- Data vs logic distinction
- Closure protocol: grep for similar bugs

### State Stores

| Store | Location | Purpose |
|-------|----------|---------|
| Session state | `.claude-state/tdd/{run_id}/session.json` | HMAC secret, phase, mode, retries |
| Phase receipts | `.claude-state/tdd/{run_id}/{phase}_receipt.json` | HMAC-signed, log hashes |
| Log files | `.claude-state/tdd/{run_id}/{phase}.stdout.log`, `.stderr.log` | Raw output (referenced by receipts) |
| Active pointer | `.claude-state/tdd/.active_run` | O(1) active session check |
| Evidence | `.evidence/` | 7-day retention, `TASK-{id}_{PHASE}_{timestamp}.md` |
| Gap files | `.claude/state/test_gaps/{terminal_id}_gaps_READY.json` | `/t` discovery output |
| Validated flag | `.claude-state/tdd/{run_id}/validated.json` | Written on success |

### Error Handling

- **Max retries:** 3 — after 3rd failure, validator prints "HARD STOP: ask user for help"
- **Stale runs:** Auto-deleted if older than 3600s on next session init
- **Corrupt gap files:** Renamed to `*_CONSUMED.json` on consumption failure
- **CWD constraint:** Enforced via `is_relative_to()` (Python 3.9+) — tests must run within session tree

---

## 4. COMPONENT INVENTORY

### Core Logic

#### `generate_context.py`
- **Role:** Session initialization entry point
- **Key functions:**
  - `_clean_stale_runs()` — Delete runs > STALE_THRESHOLD_SECONDS
  - `_get_active_run() → str | None` — O(1) active session via pointer file
  - `_detect_test_command(root_dir) → str` — Auto-detect framework
  - `_scan_python(path) → List[str]` — AST parse for FunctionDef/ClassDef names
  - `_scan_js_ts(path) → List[str]` — Regex scan for JS/TS exports
  - `_scan_go(path) → List[str]` — Regex scan for func declarations
  - `_get_workspace_summary(root_dir, max_depth=3) → str`
- **Outputs:** `session.json`, `.active_run` pointer
- **Constants:** `STATE_ROOT = .claude-state/tdd`, `STALE_THRESHOLD_SECONDS = 3600`

#### `run_phase.py`
- **Role:** Mandatory test execution wrapper for all phases
- **Key class/functions:**
  - `_now_iso() → str` — UTC timestamp
  - `_sha256_file(path) → str` — Chunked file hash (8192 bytes)
  - Phase state machine via `_ALLOWED_TRANSITIONS` dict
- **Inputs:** `--run-id`, `--phase`, `--override-cmd`, `--timeout` (default 120s)
- **Outputs:** `{phase}_receipt.json`, `{phase}.stdout.log`, `{phase}.stderr.log`
- **Critical constraint:** All test execution MUST go through this script (never direct subprocess)

#### `validate_tdd.py`
- **Role:** HMAC-verified TDD cycle validation
- **Key functions:**
  - `_sha256_file(path) → str`
  - `_output_shows_failure(text) → bool` — Uses `_FAIL_PATTERN` regex
  - `_output_shows_pass(text) → bool` — Pass pattern + residual failure check
  - `_parse_iso(ts) → datetime`
- **Validation checks (11 total):**
  1. Receipt existence + HMAC signature
  2. Log SHA256 hash verification
  3. RED exit_code ≠ 0
  4. RED stdout matches failure pattern
  5. RED stdout ≥ 3 lines
  6. GREEN exit_code = 0
  7. GREEN stdout matches pass pattern
  8. GREEN stdout ≥ 3 lines
  9. Temporal ordering (GREEN ≥ RED timestamps)
  10. Distinctness (RED ≠ GREEN stdout)
  11. REFACTOR (if claimed): receipt exists, pass, distinct from GREEN
- **Failure patterns detected:**
  ```
  \d+ failed, FAILED \S+, ERRORS? collecting, AssertionError,
  assert .+==, FAIL:\s+, ---\s+FAIL, panic:\s+
  ```
- **Constants:** `MAX_RETRIES = 3`

#### `session_models.py`
- **Role:** Pydantic data models for all TDD artifacts
- **Key models:**
  - `SessionState` — run_id, mode, task, cwd, test_command, phase, hmac_secret, started_at, retries
  - `PhaseReceipt` — phase, run_id, test_command, exit_code, timestamps, stdout/stderr paths+hashes, signature
  - `TddEvidence` — metadata, target_component, expected_behavior, modified files, PhaseReceiptRefs
  - `PhaseReceiptRef` — reference to receipt without embedding logs
  - `RunMetadata` — run_id, mode, task, cwd, test_command, started_at
- **Critical method:** `PhaseReceipt.compute_signature(secret)` / `verify_signature(secret)` — HMAC-SHA256 with timing-safe comparison

#### `gap_loader.py`
- **Role:** Integration with `/t` discovery; loads test gaps
- **Key function:** `load_test_gaps(project_root) → dict | None`
- **Inputs:** Terminal-scoped gap file or global fallback
- **Gap file locations:**
  - Terminal-scoped: `.claude/state/test_gaps/{terminal_id}_gaps_READY.json`
  - Global: `.claude/state/test_gaps/_READY.json`
- **Behavior:** Atomic rename to `*_CONSUMED.json` on successful load
- **Output:** `format_gap_summary(gap_data) → str` for DISCOVER phase

### Utilities / Helpers

| File | Purpose |
|------|---------|
| `test_task_021_verification.py` | TASK-021 EvidenceManager integration test |
| `tests/conftest.py` | Pytest fixtures: `mock_time`, `frozen_time`, `fast_time`, `fast_datetime` (freezegun-based, optional) |

### Hooks (External)

| Hook | Trigger | File | Purpose |
|------|---------|------|---------|
| `preflight_require_tdd.py` | pre_prompt | `.claude/hooks/` | Block prompt if TDD session not initialized |
| `stop_if_tdd_unverified.py` | pre_response | `.claude/hooks/` | Block response if TDD cycle not validated |

### Reference Documents

| File | Purpose |
|------|---------|
| `references/discovery-and-regression.md` | DISCOVER/REGRESSION phase docs |
| `references/evidence-collection.md` | Evidence tracking, 7-day cleanup, artifact format |
| `references/parallel-delegation.md` | PARALLEL FIRST rule, subagent patterns |
| `references/verify-phase.md` | VERIFY mandatory integration validation |
| `references/workflow-variants.md` | Bug-fix YAGNI constraint, data vs logic guidance |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **HMAC-signed receipts** — Each phase produces a cryptographically signed receipt; validator verifies signature and log hash integrity
2. **Receipts reference logs** — Evidence does NOT embed raw logs; only receipt path references
3. **Monotonic phase advancement** — Phase transitions stored in session.json, enforced by run_phase.py state machine
4. **No global locks** — Windows-compatible localized retry tracking
5. **O(1) active session check** — `.active_run` pointer file, not directory scan
6. **Stale run cleanup** — Runs older than 3600s auto-deleted on session init
7. **CWD sub-path enforcement** — Monorepo support via `is_relative_to()` check

### Technology Constraints

- **Python 3.9+** for `is_relative_to()` support
- **pydantic** for data models (session_models.py)
- **freezegun** optional for time mocking tests
- **No dedicated TDD test files** — tests exist but validate integration with `/code` EvidenceManager
- **No per-skill requirements.txt** — dependencies managed at package level

### Things That MUST NOT Change

| Rule | Why |
|------|-----|
| All test execution via `run_phase.py` | Guarantees HMAC-signed receipts for every phase |
| RED must fail (exit_code ≠ 0) | Proves test captures expected failure |
| GREEN must pass (exit_code = 0) | Proves minimal implementation satisfies test |
| HMAC secret per session | Ensures receipt integrity and non-repudiation |
| Receipts reference logs (not embed) | Prevents transcript bloat; enables detached verification |
| 3-retry max | Prevents infinite validation loops |
| O(1) active session via pointer file | Avoids directory scan on every invocation |

---

## 6. KNOWN ISSUES

*(Documented in source or migration plan)*

| Issue | Impact | Workaround |
|-------|--------|-----------|
| RED phase module not yet available | `test_task_021_verification.py` fails because `lib.evidence_writer` doesn't exist in RED phase | Tests use `EVIDENCE_TRACKING_AVAILABLE` skip flag |
| freezegun optional | Time mocking tests skip if not installed | Install freezegun for full test coverage |
| CWD sub-path enforcement | Cannot run tests from outside session tree | Run from within session CWD |
| 3-retry limit is per-session | Long debugging sessions may exhaust retries | Start new session |
| No cross-process cache invalidation | Original issue (doc: twinkly-soaring-sunbeam.md) was fixed via terminal isolation | — |
| Test naming validator strict | Non-standard test file names rejected by `paths_must_look_like_test_files` | Use standard naming: `test_*.py`, `*_test.py`, `*.test.ts`, etc. |

---

## 7. INTEGRATION POINTS

### Skill Invocation

**Slash command:** `/tdd [mode] "description"` where mode ∈ {`feature`, `bugfix`, `refactor`}

**Modes:**
- `feature` — Standard RED/GREEN/REFACTOR flow
- `bugfix` — YAGNI constraint, data vs logic guidance, closure protocol
- `refactor` — REFACTOR phase enforced if `files_refactored` claimed

### Integration with `/code`

- Evidence written to `.evidence/` directory (7-day retention)
- Artifact naming: `TASK-{id}_{PHASE}_{timestamp}.md`
- API: `generate_evidence_artifact()`, `cleanup_old_evidence()`, `is_evidence_tracking_enabled()`

### Integration with `/t` (Discovery)

- Gap file location: `.claude/state/test_gaps/{terminal_id}_gaps_READY.json`
- `gap_loader.py` consumes gap data during DISCOVER phase
- Gap data includes: target, gaps, test_types, coverage_percent, total_tests

### Auto-Detected Test Frameworks

| Framework | Detection | Command |
|-----------|-----------|---------|
| pytest | `pytest.ini`, `setup.cfg`, `pyproject.toml`, `conftest.py` | `pytest` |
| jest | `jest.config.js`, `jest.config.ts` | `npx jest` |
| vitest | `vitest.config.ts` | `npx vitest run` |
| go | `go.mod` | `go test ./...` |
| cargo | `Cargo.toml` | `cargo test` |
| npm | `package.json` test script | `npm test` |
| default | — | `pytest` |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `WT_SESSION` | Windows Terminal session ID (primary terminal identifier) |
| `TERM` | Fallback terminal identifier |
| `TDD_EVIDENCE_TRACKING_ENABLED` | Enable evidence tracking (test only) |

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

#### generate_context.py (Session Init)

| Step | Reads | Writes | Constraint |
|------|-------|--------|-----------|
| 1 | — | `session.json` | HMAC secret generated via `secrets.token_hex(32)` |
| 2 | — | `.active_run` | Atomic write via temp + replace |
| 3 | workspace | workspace summary (stdout) | Max depth=3, skips venv/__pycache__/node_modules |

#### run_phase.py (Per Phase: RED, GREEN, REFACTOR)

| Step | Reads | Writes | Constraint |
|------|-------|--------|-----------|
| 1 | `session.json` | — | Validates phase transition allowed |
| 2 | CWD | — | CWD must be sub-path of session root |
| 3 | test command | subprocess output | timeout=120s default |
| 4 | — | `{phase}.stdout.log`, `{phase}.stderr.log` | SHA256 computed |
| 5 | — | `{phase}_receipt.json` | HMAC-SHA256 signed |
| 6 | — | `session.json` (updated phase) | Monotonic advancement only |

#### validate_tdd.py (Post-Cycle)

| Step | Reads | Writes | Constraint |
|------|-------|--------|-----------|
| 1 | `{phase}_receipt.json` | — | HMAC verification |
| 2 | `{phase}.stdout.log` | — | SHA256 verification |
| 3 | RED stdout | — | Must show failure pattern |
| 4 | GREEN stdout | — | Must show pass pattern |
| 5 | timestamps | — | Temporal ordering enforced |
| 6 | — | `validated.json` | On success only |
| 7 | — | `session.json` (phase=validated) | On success only |

### Quality Gates

| Gate | Trigger | Checks | Does NOT Check |
|------|---------|--------|----------------|
| `preflight_require_tdd.py` | pre_prompt | TDD session initialized (session.json exists) | Whether session is stale |
| `stop_if_tdd_unverified.py` | pre_response | `validated.json` exists | Whether validation was correct |
| `validate_tdd.py` | Manual or hook call | 11 validation checks | Content of test assertions |

---

## 9. AGENT DISPATCH DEFINITIONS

This skill does not dispatch parallel agents. It is a single-user TDD protocol with local subprocess execution only.

**Sub-agent patterns documented in `references/parallel-delegation.md`:**
- PARALLEL FIRST rule: independent tasks launch all subagents in parallel
- RED: one `tdd-test-writer` per test case
- GREEN: one `tdd-implementer` per implementation task
- REFACTOR: one `tdd-refactorer` per cleanup task

These are documented patterns for human/agent coordination, not implemented agent dispatches within this skill.

---

## 10. FAILURE SCENARIOS

### F1: RED phase exit code is 0

**Trigger:** Test suite passes when it should fail (test doesn't assert expected failure)

**Propagation:** `validate_tdd.py` check #3 (`RED exit_code must be non-zero`) fails → validation fails

**Detection:** Validator prints "RED must fail but exit code was 0"

**Actual vs expected:** Expected: RED fails. Actual: RED passed.

**Root cause:** User wrote a test that doesn't actually fail, or implementation was pre-written

---

### F2: GREEN phase exit code is non-zero

**Trigger:** Implementation doesn't satisfy the test

**Propagation:** `validate_tdd.py` check #6 (`GREEN exit_code must be zero`) fails → validation fails

**Detection:** Validator prints numbered errors, increments `session.retries`

**Actual vs expected:** Expected: GREEN passes. Actual: GREEN fails.

**Root cause:** Implementation is insufficient or test is incorrect

---

### F3: Log tampering after phase completion

**Trigger:** User modifies log file after `run_phase.py` writes it

**Propagation:** `validate_tdd.py` check #2 (SHA256 verification) fails

**Detection:** "Log hash mismatch for {phase} stdout"

**Actual vs expected:** Expected: log hash matches receipt. Actual: log hash differs.

**Root cause:** HMAC receipt signs the hash, not the log content — hash mismatch proves tampering

---

### F4: HMAC receipt forgery

**Trigger:** Attacker creates fake receipt with valid signature

**Propagation:** `validate_tdd.py` check #1 (HMAC signature) fails

**Detection:** `hmac.compare_digest` timing-safe comparison returns False

**Actual vs expected:** Expected: valid HMAC. Actual: forged HMAC.

**Root cause:** HMAC secret is session-scoped; attacker doesn't have access to `session.json`

---

### F5: Stale session blocking new session

**Trigger:** User starts `/tdd`, then leaves it idle >3600s, then tries to start new session

**Propagation:** `generate_context.py` `_clean_stale_runs()` deletes old run dir → new session starts clean

**Detection:** Old `.active_run` pointer removed on new session init

**Actual vs expected:** Expected: new session starts. Actual: old session cleaned.

**Root cause:** Stale threshold is intentional cleanup mechanism

---

### F6: Validation retry exhaustion

**Trigger:** Three consecutive validation failures

**Propagation:** `validate_tdd.py` increments `session.retries`, after 3rd: prints "HARD STOP: ask user for help", exits

**Detection:** User sees "HARD STOP" message

**Actual vs expected:** Expected: retry indefinitely. Actual: 3-retry limit enforced.

**Root cause:** `MAX_RETRIES = 3` is intentional to prevent infinite loops

---

## 11. APPENDIX: KEY CONSTANTS

| Constant | Value | Location |
|----------|-------|----------|
| `MAX_RETRIES` | 3 | `validate_tdd.py:21` |
| `STALE_THRESHOLD_SECONDS` | 3600 | `generate_context.py:26` |
| `default timeout` | 120 seconds | `run_phase.py:64` |
| `HMAC secret length` | 32 bytes (64 hex chars) | `generate_context.py:199` |
| `max workspace depth` | 3 | `generate_context.py:147` |
| `stdout chunk size` | 8192 bytes | All `_sha256_file()` functions |
| Evidence retention | 7 days | `references/evidence-collection.md` |
| Phase receipt fields | 11 fields | `PhaseReceipt` Pydantic model |
| Test naming patterns | 12 patterns | `paths_must_look_like_test_files` validator |

---

## COMPARISON: tdd_v3.2 vs code_v3.0 Evidence

| Aspect | tdd_v3.2 | code_v3.0 EvidenceManager |
|--------|-----------|--------------------------|
| **Receipt signing** | HMAC-SHA256 per phase | None (hash-based) |
| **Evidence model** | `TddEvidence` (Pydantic) | `can_mark_done()`, `mark_done()` |
| **Log storage** | Separate `.log` files referenced by receipt | Inline in evidence ledger |
| **Validation** | 11 deterministic checks | `can_mark_done()` tuple check |
| **Phase isolation** | Receipt per phase | Single ledger per task |
| **Timestamps** | ISO8601 in receipts | datetime in ledger |
| **Tool gating** | Hooks (preflight + pre_response) | PostToolUse breadcrumb |
| **State scope** | Per-run directory | Per terminal |
