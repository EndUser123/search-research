# Flags and Usage Reference

## Usage

```
/p                    # Auto-detect and run what's needed (full file set)
/p cleanup            # Target the cleanup skill (includes ALL files in that directory)
/p /cleanup           # Same as above (skill name with or without /)
/p .claude/hooks/     # Explicit path target (any directory)
/p P:\.claude\skills\cleanup  # Explicit path to skill directory
/p package skill      # Resolve "package" skill to its directory
/p --quick            # Only check files from current session context (chat-based, no git)
/p --publish          # Halt on warnings (treat non-blocking warnings as blocking)
/p --quick --publish  # Combined: changed files only + halt on warnings
/p --evidence <path>  # Write JSON evidence to path (for batch execution)
/p --focus security   # Focus lens: emphasize security in P2 review
/p --focus complexity # Focus lens: emphasize complexity in P2+P3
/p --phase=N          # Run specific phase only (0=Scaffold, 1=Build, 2=Review, 3=Validate, 4=Publish, 5=Certify, 6=Security)
/p --reverse          # Gap analysis: run phases in reverse order (P5->P4->P3->P2->P1->P0)
/p --fix              # Auto-fix safe issues in P3 (formatting, imports, lint)
/p --fix-all          # Iterative fixing loop: run /p + /code until 0 MEDIUM+ issues remain
/p --auto-fix         # Per-phase HALT-and-retry: LLM fixes + retry until resolved (ON by default)
/p --dry-run          # Detection-only mode: report what would happen without state changes
/p --force            # Bypass exit criteria validation (EMERGENCY ONLY)
```

**Skill targeting (IMPORTANT):**
- When you provide a skill name (`cleanup`, `p`, `testing-skills`), `/p` automatically analyzes the ENTIRE skill directory
- This includes SKILL.md, scripts/, tests/, references/, assets/ -- ALL files in that skill's directory

## File Scope Modes

| Flag | File Scope | Use Case |
|------|------------|----------|
| `--quick` | Session context files only (files read/edited this session) | Fast iteration on active work |
| (default) | Full file set | Complete quality gate |
| `--publish` | Full file set + halt on warnings | Perfect for publishing |

## Analysis Modes

| Flag | Mode | Use Case |
|------|------|----------|
| `--reverse` | Gap analysis (read-only) | See what's missing to reach production |
| `--dry-run` | Detection-only (no state) | Preview what /p would do without executing |
| `--fix` | Auto-fix safe issues | Reduce friction on common P3 violations |
| `--fix-all` | Iterative fixing loop | Fix all MEDIUM+ issues automatically until convergence |
| `--auto-fix` | Per-phase HALT-and-retry | LLM fixes + retry per phase until resolved (3 attempts max, git safety net) |

## --focus Flag (Focus Lenses)

Apply a focus lens from `/analyze` to emphasize specific concerns during P2 review and P3 validation.

| Lens | Effect on P2 | Effect on P3 |
|------|-------------|-------------|
| `risk` | Pre-mortem failure mode analysis on target | Report failure modes before validation |
| `gaps` | Completeness check -- missing items, unhandled cases | Check requirements coverage |
| `opportunities` | Optimization and value identification | Report improvement opportunities |
| `security` | Prioritize security agent findings | Prioritize security stages |
| `complexity` | Flag high-CC functions during review | Lower CC threshold (>= 8 warns) |
| `duplicates` | Run duplicate detection even in quick mode | Prioritize duplication stage |
| `quality` | Emphasize quality agent, raise bar for code smells | Prioritize Pylint, Complexity stages |
| `performance` | Prioritize performance agent findings | Run with profiling awareness |
| `architecture` | Add architectural perspective to review | Add cross-module dependency check |
| `test` | Focus on test quality, coverage gaps | Prioritize unit/branch/regression stages |
| `library` | Add dependency analysis to review | Prioritize CVE + freshness stages |
| `comprehensive` | **ALL lenses** -- run every lens above | All stages elevated to blocking |

**How focus propagates:**
- `/p --focus X` passes `--focus X` to P2 when invoking it
- P2 adjusts agent priority and confidence thresholds based on the lens
- P3 stages related to the lens get elevated from non-blocking to blocking

## Phase Prerequisite Enforcement

- **P0 (Scaffold)**: No prerequisite validation - it's the entry point phase
- **P1-P5**: Hook-based enforcement prevents skipping phases via `validate_p_phase_order.py`
  - P2 requires P1 completion marker
  - P3 requires P2 completion marker
  - P4 requires P3 completion marker
  - P5 requires P4 completion marker
- **P6 (Security)**: No prerequisite validation - optional final gate

## --reverse Flag

Run phases in **reverse order** (P5 -> P4 -> P3 -> P2 -> P1 -> P0) for gap analysis.

**Behavior:**
- Runs checks in reverse order
- Reports "what's missing" rather than "what's blocking"
- Does NOT update state (read-only analysis)

**Example:**
```
User: /p --reverse src/

Reverse Pipeline: Gap Analysis
  P5 Certify: Not certified for production
  P4 Publish: Missing README.md, LICENSE
  P3 Validate: 45% coverage (need 70%)
  P2 Review: Not applicable (no review yet)
  P1 Build: Tests pass

Gap to production: 4 items missing
```

## --fix Flag

Enable **automatic fixes** for safe issues in P3 (Validate) stage.

**Scope of auto-fix (safe only):**
- Formatting (ruff format)
- Unused imports (ruff --fix)
- Lint violations (ruff --fix)

**Excluded from auto-fix:**
- Logic errors, security issues, type mismatches, architectural changes

## --fix-all Flag (Iterative Fixing Loop)

**Behavior:**
```
WHILE MEDIUM+ findings exist (max 5 iterations):
  1. /p runs detection (pytest, mypy, review, etc.)
  2. /p parses findings by severity
  3. IF MEDIUM+ findings exist:
     - /p invokes /code with SPECIFIC issues to fix
     - /code fixes ONLY those specific issues
     - Record fixes applied
  4. ELSE: EXIT LOOP - quality threshold met
  5. SAFETY: Max 5 iterations
```

**Convergence criteria:**
- 0 CRITICAL, 0 HIGH, 0 MEDIUM findings (LOW ignored)

**CRITICAL: Division of Labor**
- `/p` does detection: Identifies issues
- `/code` does fixing: Receives SPECIFIC findings from `/p`
- `/code` does NOT do detection: Only fixes what `/p` tells it to fix

## --auto-fix Flag (Per-Phase HALT-and-Retry)

Per-phase HALT-and-retry loop -- when a phase HALTs, auto-fix layer tries to fix issues, then retries. **ON by default.**

**Three-Layer Fix Approach:**

| Layer | Confidence | Fix Type | Guardrails |
|-------|------------|----------|------------|
| Layer 1 | HIGH | Imports, style, pyupgrade | No guardrails needed |
| Layer 2 | MEDIUM | LLM with findings + context | "Don't break intended functionality" |
| Layer 3 | LOW | Final LLM attempt | Full characterization + git safety net |

**Retry Loop (per phase, max 3 attempts):**
```
Attempt 1: Run phase -> if HALT -> Layer 1 fix -> retry
Attempt 2: Run phase -> if HALT -> Layer 2 LLM fix -> retry
Attempt 3: Run phase -> if HALT -> Layer 3 LLM fix -> retry -> if still HALT, report
```

**Safety net:** `git restore` available to revert any auto-fix that breaks intended functionality.

## --force Flag (EMERGENCY OVERRIDE)

Bypass exit criteria validation - allows phase completion even when automated validation fails.

**WARNING:** For EMERGENCY USE ONLY. May allow incomplete phases to report PASS.

**When to use:**
- False positive blocking
- Recovery after crash
- Manual verification done but automated validation has bugs

**Recommended workflow:**
1. Use `/p --force` to bypass validation
2. Manually verify work is complete
3. Fix the validation issue if false positive
4. Re-run without `--force` to confirm clean pipeline

## --dry-run Flag

Run **detection-only mode** without modifying state or executing phases.

**Behavior:**
- Runs full detection logic
- Reports what WOULD happen
- Does NOT write state file
- Does NOT run any phases

## Difference Between Fix Flags

- `--fix`: Auto-fixes safe formatting/import issues in P3 only
- `--fix-all`: Iterative loop across phases until convergence (0 MEDIUM+)
- `--auto-fix`: Per-phase HALT-and-retry with LLM + git safety net (ON by default)
