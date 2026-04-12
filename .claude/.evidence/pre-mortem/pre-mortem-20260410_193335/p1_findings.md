## Triage Classification
skill — A Claude Code git sync skill (sync.py) with destructive git guard fix

## Dispatched Specialists
- adversarial-logic: Logic correctness of guard filtering and fallback code paths
- adversarial-io-validation: Path validation, subprocess calls, environment assumptions
- adversarial-security: Severity classification, destructive operation coverage gaps
- adversarial-quality: Code maintainability, test coverage, structural mismatches

## Specialist Findings Summary

### adversarial-logic
**Domain:** Guard logic, severity filtering, fallback code paths
**Key findings:**
- [BLOCKER] Severity filter at line 181 only blocks CRITICAL, not HIGH — `git clean -fd` and `git stash drop` bypass the guard
- [MEDIUM] Fallback dict structure incompatible with DangerOp dataclass attribute access — would crash with AttributeError if triggered

### adversarial-security
**Domain:** Severity classification, destructive operation coverage
**Key findings:**
- [CRITICAL] Same severity gap (SEC-001): only CRITICAL blocked, leaving HIGH destructive ops unguarded
- [HIGH] clean severity=HIGH should be CRITICAL — permanent untracked file deletion equivalent to reset --hard (SEC-002)
- [HIGH] stash drop/clear severity=HIGH should be CRITICAL — permanent stash deletion (SEC-003)
- [MEDIUM] Hook adds pull/rebase at MEDIUM not in shared config — creates hook vs skill protection gaps (SEC-004)

### adversarial-io-validation
**Domain:** Path validation, subprocess execution, environment assumptions
**Key findings:**
- [HIGH] Same severity gap: clean -fXd passes guard because it's HIGH not CRITICAL (IO-001)
- [MEDIUM] No fallback return for unclassified operations in _check_destructive_git (IO-002)
- [MEDIUM] Fallback has structural mismatch — dict values vs dataclass attribute access (IO-003)
- [LOW] MAIN_ROOT path not validated to exist before rglob (IO-004)
- [LOW] git rev-list assumes remote/branch exist without validation (IO-005)

### adversarial-quality
**Domain:** Maintainability, test coverage, code quality
**Key findings:**
- [HIGH] Only CRITICAL blocked by guard, HIGH ignored — destructive ops bypass (QUAL-001)
- [MEDIUM] Fallback data structure mismatch — unreachable but broken by design (QUAL-002)
- [LOW] Bare `except ImportError:` swallows failures silently (QUAL-003)
- [LOW] No test coverage for _check_destructive_git guard (QUAL-004)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [CRITICAL] (source: adversarial-logic, adversarial-security, adversarial-io-validation, adversarial-quality) — **Severity filter mismatch**: `sync.py:181` checks `danger["severity"] == "CRITICAL"` but `git clean -fd` and `git stash drop/clear` are classified `severity="HIGH"` in `git_guard_config.py`. These HIGH-severity destructive operations bypass the skill-level guard entirely. The `_check_destructive_git()` detects them correctly but the enforcement at line 181 ignores them.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-logic, adversarial-quality) — **Fallback incompatible with DangerOp dataclass**: `sync.py:32-36` defines fallback as dict with `{"danger_flags": ("--hard",), "severity": "CRITICAL"}` but `_check_destructive_git()` at lines 136-137 accesses `op.danger_flags` and `op.danger_subcommands` as dataclass attributes. If the import fails, the fallback activates but immediately crashes with `AttributeError: 'dict' object has no attribute 'danger_flags'`.
2.2. [MEDIUM] (source: adversarial-security) — **Hook adds operations not in shared config**: `PreToolUse_destructive_git_guard.py` adds `pull` and `rebase` at MEDIUM severity, not present in shared `DESTRUCTIVE_GIT_OPS`. The skill only references shared config, so hook-specific additions are not blocked by skill guard.
2.3. [LOW] (source: adversarial-io-validation) — **Path constants not validated**: `MAIN_ROOT = Path("P:/")` at `sync.py:60` is not checked to exist before `rglob('.git')`. Silent empty result if drive unmounted.

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-quality) — **No test coverage for destructive git guard**: `_check_destructive_git()` and the `run()` blocking logic have no unit tests. Future changes could re-introduce the gap without detection. Tests already exist at `P:/.claude/skills/git/tests/test_destructive_git_guard.py` — confirm they cover HIGH severity blocking.
3.2. [MEDIUM] (source: adversarial-io-validation) — **Missing fallback return for unclassified ops**: `_check_destructive_git()` returns `None` when subcommand is in `DESTRUCTIVE_GIT_OPS` but flags don't match. Should return the op info so caller can log unknown dangerous operations.

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-io-validation) — **git rev-list assumes remote/branch exist**: `get_repo_status()` at `sync.py:366` calls `git rev-list --count origin/{branch}..HEAD` without checking if remote branch still exists. Silent failure returns (True, 0) even when local has commits.
4.2. [LOW] (source: adversarial-quality) — **Bare except ImportError**: Line 30 catches all ImportError silently. A more specific exception or logging would help diagnose if git_guard_config.py has issues.

### Concrete Recommendations
5.1. [HIGH] (source: all specialists) — Change `sync.py:181` severity check from `== "CRITICAL"` to `in ("CRITICAL", "HIGH")`. This is the primary fix for the severity gap.
5.2. [MEDIUM] (source: adversarial-logic, adversarial-quality) — Remove the broken fallback at lines 32-36 since it's unreachable when the import succeeds and structurally broken if triggered. Add `assert hasattr(DESTRUCTIVE_GIT_OPS["reset"], "danger_flags")` after import to fail fast if config structure changes.
5.3. [MEDIUM] (source: adversarial-security) — Consider upgrading `clean` and `stash` severity from HIGH to CRITICAL in `git_guard_config.py` to match `reset --hard`. Both operations cause permanent data loss equivalent to reset --hard.
5.4. [LOW] (source: adversarial-io-validation) — Add existence check for `MAIN_ROOT` before rglob: `if not MAIN_ROOT.exists(): print("ERROR: P:/ drive not accessible"); sys.exit(1)`

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-logic) — Is severity-based filtering intentional? Was only CRITICAL meant to be blocked by design? If so, HIGH operations like `git clean -fd` were knowingly allowed through — but the PreToolUse hook already handles those at the Bash level.
6.2. [LOW] (source: adversarial-io-validation) — What is expected behavior when MAIN_ROOT doesn't exist — hard error or silent skip?
