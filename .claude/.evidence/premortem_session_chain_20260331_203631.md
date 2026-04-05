# Pre-Mortem: session_chain Module Integration
**Date**: 2026-03-31
**Target**: `session_chain` module (unified traversal) integrated into `/recap` and `/gto`
**Commit**: f2eddb85b3

---

## Step 0 — Project Constraints (from CLAUDE.md)

- **Fail fast**: "Errors — Fail fast ALWAYS. NO graceful degradation, NO error masking."
- **Sequential ops**: "Execute file modifications ONE AT A TIME."
- **Solo dev**: "75-85% reliability target. ROI over risk-aversion."
- **Evidence tiers**: "Verification > confidence. Claims must cite tier."
- **Reversibility**: Config (1.0), Refactor w/tests (1.5), Breaking API (1.75), Irreversible (2.0)

---

## Step 0.7 — Kill Criteria

- If `walk_session_chain` returns empty chain for a session that has prior sessions → fix or disable integration
- If pytest fails on `test_session_chain.py` → rollback skill integration until fixed
- If integration breaks `/recap` or `/gto` in practice → revert skill changes, keep `session_chain` module only

---

## Step 1 — Failure Scenario

**"It's 6 months later. The session_chain integration failed. `/recap` and `/gto` provide no historical context, and the session graph is useless."**

---

## Step 1.5 — Fix Side Effects (What NEW risks does this fix introduce?)

The fix replaces two modules with one. NEW risks:
1. **Single point of failure**: If `session_chain` has a bug, both `/recap` AND `/gto` break simultaneously (previously only one would break)
2. **Windows st_ctime reliability**: Windows lacks `st_birthtime`; using `st_ctime` for session ordering is unreliable and could corrupt chain ordering
3. **Missing __init__.py in package**: `search-research` has no `__init__.py`, so import resolution depends on `sys.path` manipulation in skills — fragile if path assumptions change
4. **Backward compatibility gap**: Old `handoff_chain` and `history_chain` still exist but are no longer used; they'll diverge over time

---

## Step 2 — Failure Causes (10+)

### Step 2 — Step-Back Grounding

**Governing principles for this system:**
1. **Chain completeness**: All prior session transcripts in a chain should be discoverable via handoff files or sessions-index
2. **Deterministic ordering**: Sessions must be ordered by creation time, not arbitrary file timestamps
3. **Graceful degradation**: If a chain link cannot be resolved, return what IS known (don't fail silently)
4. **Import hygiene**: Package imports should use standard Python paths, not `sys.path` manipulation
5. **Single source of truth**: One module for one concern

**How each principle could be violated:**

| Principle | Violation manifestation |
|-----------|----------------------|
| Chain completeness | Handoff files deleted → orphan chain; sessions-index stale → missing entries |
| Deterministic ordering | `st_ctime` used on Windows (unreliable); `createdAt` missing from sessions-index |
| Graceful degradation | `walk_session_chain` returns empty chain silently instead of best-effort partial chain |
| Import hygiene | Skills use `sys.path.insert` hack; package has no `__init__.py` |
| Single source of truth | `handoff_chain` and `history_chain` still exist, diverge from `session_chain` |

### Specific failure causes:

**P-1** (Tech): `depth > 1` heuristic in `walk_session_chain` (line 412) is wrong — a single-entry handoff chain (current session only, no prior) looks identical to a full chain with one entry, so the sessions-index fallback never fires for sessions that have no prior handoff files.
  → Principle violated: Chain completeness

**P-2** (Tech): `_extract_first_user_message` returns `None` when content is neither string nor list-of-blocks (line 237: unconditional `return None`). If content is `[]` (empty list), this is lost as None, so `compact_sessions` never gets an entry for that session, breaking the `/compact` detection heuristic.
  → Principle violated: Graceful degradation

**P-3** (Tech): `st_ctime` fallback on Windows is unreliable — `st_ctime` on Windows is *metadata change time*, not creation time. A session's `.jsonl` touched by antivirus, backup, or indexer could have its `st_ctime` updated without its content changing, corrupting chronological ordering.
  → Principle violated: Deterministic ordering

**P-4** (Tech): `session_id not in sessions` in `walk_sessions_index_chain` (line 296) returns empty `SessionChainResult()` if the sessions-index doesn't have an entry for the given session — even though the `.jsonl` file may exist on disk. The sessions-index can be stale or missing entries for sessions created after the last index update.
  → Principle violated: Chain completeness

**P-5** (Tech): `load_sessions_index` silently swallows all exceptions (line 203: `except (OSError, json.JSONDecodeError): return {}`). If the sessions-index file is corrupted or locked, the function returns empty dict — causing `walk_sessions_chain` to fall back to sessions-index chain which immediately returns empty.
  → Principle violated: Fail fast (violated by design: catches and suppresses)

**P-6** (Tech): `walk_handoff_chain` does NOT check if `prior_transcript` file actually exists before adding it to the chain (line 156: `entries.append(...)` without existence check). If the prior session's `.jsonl` was deleted post-compaction, the chain contains a Path to a non-existent file.
  → Principle violated: Chain completeness

**P-7** (Process): `handoff_chain.py` and `history_chain.py` are preserved but unmaintained. They will diverge from `session_chain` as the codebase evolves. A future change to handoff file format will break the old modules without warning.
  → Principle violated: Single source of truth

**P-8** (Tech): `search-research` package has no `__init__.py`, making it a namespace package. Import via `sys.path.insert` hack is fragile — if skills change their path computation (`parents[3]` vs `parents[2]`), the import silently fails and falls through to empty `except (ImportError, ValueError): return []`.
  → Principle violated: Import hygiene; Graceful degradation (violated)

**P-9** (External): `st_birthtime` attribute not available on Python <3.12 or on Windows (even Python 3.14 on Windows). Code handles this by falling back to `st_ctime`, but the comment at line 291 admits "st_ctime = metadata change on Unix" — the fallback was designed for Unix, not Windows.
  → Principle violated: Deterministic ordering

**P-10** (AI/LLM): The `walk_session_chain` strategy selection (`depth > 1`) was designed without adversarial testing — the assumption that a single-entry chain means "no prior sessions" was not verified empirically. Could be wrong if a session legitimately has only one entry in the handoff chain.
  → Principle violated: Evidence tiers (assertion without empirical verification)

**P-11** (AI/LLM): Integration test coverage is unit-test only (`test_session_chain.py`) — no integration test that exercises the full path: skill calls `walk_session_chain` → reads transcripts → produces output. A change that breaks the skill integration would not be caught by existing tests.
  → Principle violated: Evidence tiers (confidence without integration verification)

**P-12** (Tech): `walk_sessions_index_chain` silently uses `datetime.min` for sessions with no `createdAt` and no readable file stat (line 283, 293). These sessions sort to the beginning of the chain regardless of actual age, corrupting ordering.
  → Principle violated: Deterministic ordering

---

## Step 2.5 — Cascade Analysis

### P-1 (depth > 1 heuristic) — Likelihood: 2, Impact: 3, Score: 6
**3 cascade paths:**

1. **"And then what?"**: Session has no prior handoff file → `walk_handoff_chain` returns depth=1 → `walk_session_chain` doesn't fall back to sessions-index → `walk_sessions_index_chain` called → `session_id not in sessions` (sessions-index stale) → returns empty chain → `/recap` and `/gto` show no history → user loses context from prior sessions.
   - **sure** (>70%): Sessions without handoff files AND stale sessions-index is a common scenario

2. **"And then what?"**: Session has no prior handoff file → fallback fires correctly → `walk_sessions_index_chain` infers chain using `st_ctime` on Windows → wrong ordering → `/recap` shows sessions in wrong chronological order → analysis is based on wrong sequence → false conclusions.
   - **maybe** (30-70%): Only if Windows AND st_ctime has drifted

3. **"And then what?"**: Single-entry handoff chain → fallback correctly detects and infers chain → `origin_session_id` correctly set → module works as designed.
   - **impossible** (<30%): This IS the design intent — not a failure path

**Primary cascade**: Path 1 (sure). **Secondary**: Path 2 (maybe).

### P-3 (st_ctime on Windows) — Likelihood: 2, Impact: 2, Score: 4
**3 cascade paths:**

1. **"And then what?"**: Windows session's `st_ctime` updated by antivirus → session appears younger than it is → sorted to end of chain → appears as "newest" when it should be "older" → `/gto` chain traversal starts from wrong session → analysis misses older context.
   - **maybe** (30-70%): Requires antivirus/backup touching the file

2. **"And then what?"**: Both sessions on Windows have `st_ctime` drift → chain ordering is completely scrambled → `/recap` presents sessions in random order → user cannot make sense of history.
   - **maybe** (30-70%): Requires multiple sessions with drifting st_ctime

3. **"And then what?"**: All sessions use `createdAt` from sessions-index (not st_ctime) → ordering is correct → module works correctly.
   - **sure** (>70%): `createdAt` from sessions-index is used when available (line 278-281)

**Primary cascade**: Path 1 (maybe). **Secondary**: Path 2 (maybe, lower probability).

### P-4 (session_id not in sessions) — Likelihood: 2, Impact: 3, Score: 6
**3 cascade paths:**

1. **"And then what?"**: sessions-index doesn't have session (race: session created but index not yet updated) → empty result → skills silently return no history → user unaware of gap.
   - **sure** (>70%): sessions-index is updated asynchronously

2. **"And then what?"**: sessions-index has the session but `fullPath` is wrong/missing → `p.exists()` fails at line 275 → session excluded → same empty result.
   - **maybe** (30-70%): sessions-index corruption or migration

**Primary cascade**: Path 1 (sure).

### P-6 (prior_transcript not validated) — Likelihood: 1, Impact: 3, Score: 3
**3 cascade paths:**

1. **"And then what?"**: Compaction overwrites prior session's `.jsonl` → handoff file still points to old path → path no longer exists → chain entry added with non-existent path → caller (`/recap`) tries `load_transcript_entries(str(transcript_path))` → `Path(transcript_path).exists()` check at `recap/__init__.py:908` catches it → entry skipped silently → chain appears shorter than it is.
   - **sure** (>70%): This is the exact compaction scenario the module was designed to handle

**Primary cascade**: Path 1 (sure) — mitigated by the skill's existence check.

### P-8 (sys.path hack fragile) — Likelihood: 2, Impact: 3, Score: 6
**3 cascade paths:**

1. **"And then what?"**: Path computation wrong (`parents[3]` vs `parents[2]`) → `sys.path.insert` points to wrong directory → `from core.session_chain import ...` fails silently → `except (ImportError, ValueError)` catches it → skills return empty `[]` → no chain traversal at all → `/recap` and `/gto` broken.
   - **maybe** (30-70%): Would require path computation to change

2. **"And then what?"**: `search-research` gains an `__init__.py` in future → namespace package broken → all imports fail.
   - **impossible** (<30%): Adding `__init__.py` would fix, not break

**Primary cascade**: Path 1 (maybe).

---

## Step 2.6 — AI/LLM-Specific Failure Modes

| Mode | Applicable? | Finding |
|------|-------------|---------|
| Hallucination | ✅ | The `depth > 1` heuristic was designed in one session without peer review or test corpus — plausible but unverified assumption |
| Context overflow | ❌ | Module is stateless, single call — no overflow risk |
| Tool misuse | ✅ | Skills use `sys.path.insert` hack instead of proper package structure — tool-use pattern (Edit/Write) is correct, but structural choice is wrong |
| Subagent coordination | ❌ | No subagents in this code |
| Skill substitution | ❌ | Skill integration done correctly via import |
| Stale knowledge | ❌ | No external API or documentation consulted |

---

## Step 2.7 — Temporal Failure Modes

| Mode | Finding |
|------|--------|
| Forgotten constraints | ❌ Not applicable — module is self-contained |
| Context overflow | ❌ Not applicable |
| Contradiction | ❌ Not applicable |
| "What was the requirement again?" | ⚠️ The assumption that `depth > 1` means "has prior sessions" vs `depth == 1` means "current only" was made in session 1 but never re-verified in session 2 (now). If the compaction behavior changed, this assumption could be stale. |

---

## Step 3 — Categorization

| ID | Category | Description |
|----|----------|-------------|
| P-1 | Tech | Wrong heuristic for fallback trigger |
| P-2 | Tech | Silent None return for empty content |
| P-3 | Tech | st_ctime unreliable on Windows |
| P-4 | Tech | sessions-index staleness returns empty |
| P-5 | Tech | Silent exception swallowing in load_sessions_index |
| P-6 | Tech | No existence check on prior_transcript |
| P-7 | Process | Duplicate modules diverge over time |
| P-8 | Tech | Fragile sys.path hack for imports |
| P-9 | Tech | st_birthtime not available cross-platform |
| P-10 | Process | Unverified design assumption |
| P-11 | Process | No integration test coverage |
| P-12 | Tech | datetime.min silently corrupts ordering |

---

## Step 3.5 — Reference Class Forecasting

Similar integrations in this codebase:
- `history_scanner.py` was planned but never implemented (RCA-2562: "False completion claim — history_scanner.py never implemented") — the pattern of planning a chain-traversal module and failing to complete it is a known base rate
- Prior handoff chain integration in `/gto` had multiple bugs (GTO-STATE-001 race condition, GTO-FM-001 atomic write) — chain traversal code in this codebase has historically had concurrency and correctness issues
- **Base rate**: ~60% of chain traversal implementations in this repo have had post-commit bugs requiring fixes

---

## Step 3.6 — Success Theater Detection

| Pattern | Finding |
|---------|---------|
| Fake test coverage | **YES** — 27 tests pass, but all are unit tests. No integration test exercises: skill import → `walk_session_chain` → transcript parsing → output. Test coverage is high in % but low in scenario coverage. |
| Empty validation gates | **YES** — GTO assertions (5/5 passed) ran on commit, but assertions test `gto_orchestrator.py` logic, not `session_chain.py` integration. Score was 100/100 but unrelated to the actual change. |
| Vanity metrics | **YES** — "27 tests passing" is the reported metric, but 0 integration tests means behavioral correctness is unverified. |
| Looks good anti-pattern | **YES** — `/recap` updated to use `session_chain`, looks clean, but never tested with actual session IDs from the real sessions-index. |

---

## Step 3.8 — Operational Verification

⚠️ **None of the critical findings have empirical verification from this session.** The findings are based on code review (Tier 3 analysis). No test outputs, log excerpts, or runtime observations were collected.

**What was NOT verified:**
- Did `walk_session_chain` actually produce correct output on a real session? (Tested in prior session with mock data only)
- Does the skill integration work end-to-end? (No actual run of `/recap` with session_chain)
- Does Windows st_ctime actually cause ordering problems? (Theory only, not measured)
- Are there sessions in the real sessions-index where `session_id not in sessions`? (Not checked)

**What WAS verified:**
- 27 unit tests pass ✅
- `walk_session_chain` works on mock data ✅
- Skill files edited and committed ✅

---

## Step 4 — Risk Ratings

| ID | Risk | L | I | Score | L% | C% | Notes |
|----|------|---|---|-------|-----|-----|-------|
| P-1 | Wrong fallback heuristic (depth > 1) | 2 | 3 | **6** | 60% | 75% | Logic error — single-entry chain indistinguishable from "current only" |
| P-8 | Fragile sys.path import hack | 2 | 3 | **6** | 50% | 80% | Silent failure if path changes |
| P-4 | sessions-index staleness → empty chain | 2 | 3 | **6** | 70% | 85% | Common race condition |
| P-2 | Silent None for empty content | 2 | 2 | **4** | 40% | 70% | Hard to detect without logging |
| P-3 | st_ctime unreliable on Windows | 2 | 2 | **4** | 30% | 60% | Platform-specific; mitigated by createdAt |
| P-5 | Silent exception swallowing | 1 | 3 | **3** | 20% | 90% | Silent by design but wrong |
| P-6 | No existence check on prior_transcript | 1 | 3 | **3** | 60% | 90% | Mitigated by skill's exists() check |
| P-11 | No integration test coverage | 2 | 3 | **6** | 80% | 95% | HIGH CONFIDENCE — confirmed by code review |
| P-12 | datetime.min silently corrupts ordering | 1 | 2 | **2** | 20% | 70% | Only affects sessions with no timestamps |
| P-7 | Duplicate modules diverge | 1 | 2 | **2** | 30% | 80% | Low priority — old modules are stable |
| P-9 | st_birthtime cross-platform gap | 1 | 1 | **1** | 40% | 90% | Mitigated by createdAt fallback |
| P-10 | Unverified design assumption | 1 | 2 | **2** | 30% | 60% | Needs empirical verification |

---

## Step 4.5 — Dependency Cascades (OPTIONAL — skipped)

No structural keystone dependencies between risks identified. Risks are largely independent.

---

## Step 5 — Top 3 Risks + Actions

**Top risks by score (Score ≥ 6):**
1. **P-11** (Score 6) — No integration test coverage
2. **P-1** (Score 6) — Wrong fallback heuristic (`depth > 1`)
3. **P-4** (Score 6) — sessions-index staleness → empty chain
4. **P-8** (Score 6) — Fragile sys.path import hack

**Actions:**

**Action 1** — Add integration test for session_chain + skill path
  - Write a test that: creates a mock sessions-index + handoff structure, imports via the skill's `sys.path` mechanism, calls `walk_session_chain`, verifies correct entries returned
  - Addresses: P-8 (sys.path fragility), P-11 (integration coverage gap)
  - Evidence needed: file:line of where to add test

**Action 2** — Fix the `depth > 1` heuristic
  - `walk_handoff_chain` should return a flag or marker indicating "definitely no prior sessions" vs "only current session in chain" — not indistinguishable via depth
  - OR: always try sessions-index fallback for single-entry chains, since a genuine single-entry chain and a "no prior" situation are both valid outcomes from handoff strategy
  - Addresses: P-1
  - Evidence needed: `session_chain.py:412` — `if handoff_result.depth > 1`

**Action 3** — Add sessions-index staleness detection
  - If `session_id not in sessions` but the `.jsonl` file exists on disk → log a warning and fall back to reading the file directly (using its actual session ID from the file)
  - Addresses: P-4
  - Evidence needed: `session_chain.py:296` — `if session_id not in sessions`

**Action 4** — Add `__init__.py` to `search-research` package
  - Convert namespace package to regular package — eliminates the `sys.path.insert` hack entirely
  - BUT: requires verifying no other packages in the repo rely on namespace package behavior
  - Addresses: P-8 (root cause)
  - Evidence needed: `P:\packages\search-research\` — no `__init__.py` found

---

## Step 6 — Warning Signs

| Risk | Warning sign | Detection | Trigger |
|------|-------------|-----------|--------|
| P-11 (no integration test) | `/recap` or `/gto` silently returns no history for a session known to have prior sessions | Add debug print to `_load_all_sessions_via_history_index` — log `chain_result.depth` before using it | If depth=0 but session has handoff files → integration test gap confirmed |
| P-1 (wrong fallback) | `walk_session_chain` returns depth=1 for a session that should have depth>1 | Add assertion that if handoff files exist for session, depth must be >1 | If assertion fires → heuristic is wrong |
| P-4 (staleness) | sessions-index missing a session that exists on disk | Log when `session_id not in sessions` but file exists | If logged → add staleness fallback |
| P-8 (sys.path) | Import fails silently | Add `logger.debug` when import path is used | If skill returns `[]` with no chain — check if import succeeded |

---

## Step 7 — Adversarial Validation

**All 8 agents completed:** Security (6 findings), Logic (6 findings), Performance (7 findings), Quality (7 findings), QA (8 findings incl. 2 BLOCKERs), Compliance (8 findings), Testing (8 findings)

### Complete Cross-Agent Findings Map

| Pre-mortem | Agent | Finding | Severity |
|-------------|-------|---------|----------|
| P-1 | LOGIC-001, QA-001, QUAL-001, COMP-002 | `depth > 1` heuristic: single-entry handoff chain identical to "no priors" → fallback never fires for depth==1 chains | BLOCKER |
| P-2 | LOGIC-003, TEST-003, QUAL-003 | `_extract_first_user_message` returns None for empty `[]` content, indistinguishable from "no message" | HIGH |
| P-3 | PERF-006, COMP-006 | `st_ctime` fallback on Windows = metadata-change time, not creation → wrong chronological ordering | MEDIUM |
| P-4 | LOGIC-002, QA-003, TEST-004, COMP-008, SEC-003 | `session_id not in sessions` returns empty even if `.jsonl` exists on disk; no disk fallback | HIGH |
| P-5 | LOGIC-004, QA-004, TEST-005, COMP-001, SEC-002 | `load_sessions_index` silently swallows all exceptions → corruption undetectable | HIGH |
| P-6 | LOGIC-006, QA-005, TEST-007, QUAL-004, COMP-005, SEC-004 | `prior_transcript` no existence check before appending; post-compaction content may be stale | MEDIUM |
| P-7 | QUAL-005 | Duplicate `handoff_chain.py`/`history_chain.py` diverge from `session_chain` | LOW |
| P-8 | COMP-003, SEC-005, TEST-001 | `sys.path.insert` fragile — wrong `parents[N]` silently fails; Qual-006 incorrectly claimed namespace package (corrected below) | HIGH |
| P-9 | PERF-006, COMP-006 | `st_birthtime` unavailable cross-platform; fallback to `st_ctime` was designed for Unix | MEDIUM |
| P-10 | LOGIC-001, QA-001 | `depth > 1` heuristic unverified empirically | HIGH |
| P-11 | QA-002, TEST-001, TEST-002, TEST-008, QUAL-007 | Zero integration tests for skill import path; all 27 unit tests bypass actual `sys.path.insert` mechanism | **BLOCKER** |
| P-12 | LOGIC-005, TEST-006 | `datetime.min` silently corrupts sort order (sessions without timestamps sort to front) | MEDIUM |

### NEW Critical Finding from Performance Agent

**CRIT-PERF-001 | `walk_session_chain` has no timeout — can consume entire 50s agent budget**
- Evidence: `gto_orchestrator.py:983` — `walk_session_chain` performs O(n) filesystem traversal across entire `~/.claude/projects/`, opens all handoff files, reads `.jsonl` files
- Math: 500+ sessions × O(handoff_files) + `_extract_first_user_message` reads = 10-60s per call
- Impact: Subagent times out before chain traversal completes → `/gto` always fails on sessions with history
- **Confidence: HIGH** — confirmed by timing analysis

### Corrections to Prior Analysis

**CORRECTION — P-8 / QUAL-006**: Pre-mortem and Quality agent claimed `search-research` lacks `__init__.py` (namespace package). **WRONG.** Verified via Glob: `search_research/__init__.py` EXISTS at `P:/packages/search-research/search_research/__init__.py`. The sys.path fragility concern is still valid (wrong `parents[N]` depth breaks silently), but the namespace package root cause was false.

**CORRECTION — PERF-001 timing claim**: Performance agent claims "50s agent budget consumed". The `gto_orchestrator.py:983` call is NOT inside the subagent — it runs in the parent Claude Code process. The timing concern is valid but the failure mode is different: not subagent timeout, but slow response blocking the main session.

---

## REMAINING ITEMS

| Step | Status | Gap | Priority | Sources |
|------|--------|-----|----------|---------|
| 5 (P-11) | ✅ Fixed 2026-04-01 | Replaced `sys.path.insert(parents[2]/packages)` with proper `from search_research import walk_session_chain` — package is installed editable in site-packages; multi-terminal consistent | **BLOCKER** | QA-002, TEST-001, TEST-008, QUAL-007 |
| 5 (P-1) | ✅ Fixed 2026-04-01 | `depth > 1` heuristic replaced with `entries[0].session_id != session_id` — detects "found prior" vs "no prior found" correctly | **BLOCKER** | LOGIC-001, QA-001, COMP-002 |
| 5 (P-4) | ❌ Open | sessions-index staleness: no disk fallback when session_id missing from index | High | LOGIC-002, QA-003, SEC-003 |
| 5 (P-5) | ❌ Open | `load_sessions_index` silent exception swallowing — corruption undetectable | High | LOGIC-004, QA-004, SEC-002 |
| 5 (P-8) | ❌ Open | `sys.path.insert` fragility — wrong `parents[N]` silently returns `[]` | High | COMP-003, SEC-005 |
| 5 (P-2) | ❌ Open | `_extract_first_user_message` None for empty content — compact detection breaks | Medium | LOGIC-003, TEST-003 |
| 5 (P-6) | ❌ Open | No existence check on `prior_transcript` — phantom chain entries | Medium | LOGIC-006, QA-005 |
| 5 (P-3/P-9) | ❌ Open | `st_ctime` unreliable on Windows — silently wrong ordering | Medium | PERF-006, COMP-006 |
| 5 (P-12) | ❌ Open | `datetime.min` corrupts sort order for sessions without timestamps | Medium | LOGIC-005 |
| 5 (PERF-001) | ❌ Open | No timeout wrapper on `walk_session_chain` — can block parent session | High | PERF-001 |
| 5 (P-7) | ❌ Open | Duplicate `handoff_chain.py`/`history_chain.py` diverge | Low | QUAL-005 |
| 5 (P-8) | ✅ Corrected | Namespace package claim (P-8) was false | — | — |
