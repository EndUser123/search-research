# Pre-Mortem: /critique Multi-Terminal Isolation Fix
**Date:** 2026-04-02
**Target:** Multi-terminal isolation fix — specialist outputs redirected from global `P:/.claude/plans/adversarial/` to session-scoped `P:/{session_dir}/specialists/`

## Step 0 — Project Constraints (CLAUDE.md)
- Terminal isolation: Each terminal has isolated state
- Stale data immunity: State changes must propagate
- Contract discipline: explicit input/output schema, required fields, source of truth, freshness/invalidation, isolation boundary
- Fail fast, surface problems immediately

## Step 0.7 — Kill Criteria
- If 2+ concurrent terminals produce interleaved sessions.json writes → abandon sessions.json, use timestamp-only session discovery
- If specialists/ JSONs are corrupted on resume → delete session, start fresh
- If Phase 2 glob finds 0 specialist files → fail with explicit error, don't proceed with empty consolidation

## Step 1 — Failure Scenario
**"It's 6 months later and /critique is producing cross-terminal contamination. Terminal B sees Terminal A's findings in its Phase 2 output."**

## Step 1.5 — Fix Side Effects
- `get_specialists_dir()` auto-creates the directory — no side effect
- p2_meta_critique uses `*.json` glob — safe on Windows (PowerShell/cmd glob works)
- Old sessions with no `specialists/` subdir: p2 will glob 0 files → risk of empty consolidation

## Step 2 — Failure Causes

### Tech Failure Modes
1. **`sessions.json` TOCTOU on Windows** — `_save_registry` uses `os.replace()` which is atomic on POSIX but best-effort on Windows (not guaranteed atomic rename). Concurrent `_save_registry` calls can corrupt sessions.json. [Governing principle: Atomic writes required for shared mutable state]
2. **`_get_terminal_id()` changes after compaction** — If skill_guard's `detect_terminal_id()` returns different values across compactions within the same terminal session, `find_or_create_session()` won't find its registry entry and creates a new session, orphaning the old one. [Governing principle: Identity must be stable across session compaction]
3. **`{session_dir}` not substituted in dispatch template** — If orchestrator fails to substitute `{session_dir}` from session_dir path into the Task description, agents write to literal `P:/{session_dir}/specialists/` which is not a valid path. [Governing principle: Path variables must be resolved before dispatch]
4. **Phase 2 glob skips on partial specialist output** — After compaction at Phase 1, only some specialists' JSONs are written. p2_meta_critique glob finds them (e.g. 2/4) and proceeds with incomplete data. [Governing principle: Consumer must validate producer completeness before proceeding]
5. **`sessions.json` deleted by old-session cleanup during active session** — `cleanup_old_sessions()` runs opportunistically in `find_or_create_session()` and could remove an active session's registry entry if its directory is old enough. [Governing principle: Active sessions must not be cleaned up]
6. **Old session with no `specialists/` subdirectory** — Sessions created before this fix have no `specialists/` dir. p2_meta_critique glob finds 0 files → empty consolidation silently passes.

### Process Failure Modes
7. **Idempotency check uses file existence not content validity** — Step 3 checks "contains valid JSON" but doesn't validate the JSON is complete (has all expected fields). Partial JSON passes the check.
8. **No phase-completion marker** — No file marks "Phase 1 is fully complete." Resume relies on all specialist JSONs being present, which is fragile.

## Step 2.5 — Cascade Analysis

**Risk 1 (sessions.json TOCTOU)**: sure cascade: Two terminals write simultaneously → sessions.json corrupted → both terminals get `{}` from `_load_registry` → both create new sessions → old sessions orphaned → data loss.
**Risk 5 (cleanup removes active session)**: maybe cascade: Active session's directory is 8+ days old (user ran /critique, then didn't use it for a week) → cleanup removes it → next /critique finds no registry entry → new session created → previous work lost.

## Step 2.6 — AI/LLM Failure Modes
- LLM skips idempotency check if it "remembers" already running Phase 1 (temporal context overflow)
- LLM consolidates findings from a previous terminal's session because `{session_dir}` variable resolved to wrong session path

## Step 2.7 — Temporal Failure Modes
- "Did we finish Phase 1?" — LLM's conversation context doesn't track phase state; must rely on file existence

## Step 2.8 — Interruption/Handoff Failure Modes
- Compact between specialist write completing and p1_findings.md written → p1_findings.md exists but specialist JSONs are partial → p2 proceeds with incomplete data
- Consumer (p2) expects all specialist types listed in p2_meta_critique hardcoded list, but p1 dispatches a dynamic set → missing inputs silently ignored

## Step 3 — Categorization
- P1/TECH: sessions.json TOCTOU
- P2/PROCESS: no phase-completion marker
- P3/TECH: `{session_dir}` substitution failure
- P4/PROCESS: partial JSON passes idempotency check
- P5/TECH: cleanup removes active session
- P6/PROCESS: old sessions lack specialists/ dir

## Step 3.5 — Reference Class
Historical: skill_guard's terminal detection fallback was fixed because pid reuse caused 10,700 empty directories (TASK-2275). This is the same pattern — pid-based identity is unstable.

## Step 3.6 — Success Theater
- "23 tests pass" proves nothing about multi-terminal correctness — tests run single-threaded in-process
- Idempotency check "works" because test writes to temp dir, not shared sessions.json

## Step 3.8 — Operational Verification
- Risk 1: sessions.json TOCTOU — no test covers concurrent `_save_registry` from 2 processes
- Risk 5: Active session cleanup — `cleanup_old_sessions()` has no "active" flag check, just mtime-based
- Risk 6: Old session compatibility — never tested with pre-fix sessions

## Step 4 — Risk Ratings
| ID | Risk | L | I | Score | Conf |
|----|------|---|---|-------|-------|
| 1 | sessions.json TOCTOU corruption | 3 | 3 | 9 | HIGH |
| 2 | terminal_id changes across compaction | 2 | 3 | 6 | MED |
| 3 | {session_dir} not substituted | 2 | 3 | 6 | MED |
| 4 | Phase 2 proceeds with partial JSON | 3 | 2 | 6 | MED |
| 5 | Cleanup removes active session | 2 | 3 | 6 | MED |
| 6 | Old sessions lack specialists/ dir | 2 | 2 | 4 | HIGH |

## Step 5 — Prevent Top 3
See RNS below.
