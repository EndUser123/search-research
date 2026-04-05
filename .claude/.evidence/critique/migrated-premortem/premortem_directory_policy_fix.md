---
 Migrated from: premortem_directory_policy_fix.md
 Original location: P:\.claude\.evidence\premortem_directory_policy_fix.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: Directory Policy Relative Path Fix

**Date**: 2026-03-23
**Target**: PreToolUse_directory_policy.py relative path detection fix
**Scenario**: It's 6 months later and the fix failed. Why?

---

## Step 0: Project Constraints

From `P:\.claude\CLAUDE.md`:
- **Solo dev environment**: 75-85% reliability target
- **Hooks handle enforcement**: Document provides context
- **Fail fast**: Surface problems immediately
- **Truthfulness > agreement**: Evidence-first verification
- **No arbitrary thresholds**: Base decisions on actual signals
- **Ignoring concurrency**: Multiple terminals run simultaneously
- **Python 3.14**: Main Python version for codebase
- **Test-driven pattern**: Create test corpus before modifying patterns

## Step 0.7: Kill Criteria

- If >2 hours spent debugging regex edge cases, reconsider approach
- If >3 false positive reports from users, disable feature
- If hook adds >100ms latency to bash commands, redesign
- If test coverage drops below 80%, revert

## Step 1: Failure Scenario

It's 6 months later and:
- Files are still being written to P:/ root despite the fix
- Users report legitimate commands being blocked
- The hook was disabled due to false positives
- An alternative solution was implemented that bypassed the hook entirely

## Step 1.5: Fix Side Effects

**NEW risks introduced by the regex patterns:**
- Relative pattern `[^/\s"\';&|]+` might match command arguments instead of file paths
- Path prefixing with `working_dir` could create invalid paths if cwd changes mid-command
- Multiple patterns matching the same text could cause duplicate validation

**NEW risks introduced by os.getcwd() usage:**
- Hook behavior differs based on where command is run from
- Working directory might not match CLAUDE_PROJECT_DIR in worktrees
- Terminal isolation issues if os.getcwd() returns wrong path

## Step 2: Brainstorm Failure Causes

1. **Pattern false positives**: Relative patterns match non-file arguments (options, flags)
2. **Working directory mismatch**: `os.getcwd()` returns different path than expected in worktrees
3. **Command chaining**: `cd /tmp && echo test > file.txt` breaks working_dir detection
4. **Subshell execution**: Commands in `$(...)` or backticks have different working directory
5. **Path normalization**: `P://file.txt` double slash from path concatenation
6. **Terminal ID not propagated**: working_dir doesn't respect terminal isolation
7. **Performance regression**: 18 regex patterns + os.getcwd() on every bash command
8. **Concurrent access**: Multiple terminals running bash commands simultaneously
9. **Allowed files blocked**: Legitimate writes to allowed_config_files blocked by root check
10. **Windows path edge cases**: UNC paths, drive letter case sensitivity
11. **Git hooks interference**: Pre-commit hooks run from .git directory, not P:/
12. **Tool-specific assumptions**: Only Bash tool uses working_dir, other tools don't

## Step 2.5: Cascade Tracing (Risks ≥6)

**RISK-001: Pattern false positives (Risk 9)**
- Step 1: User runs `echo --flag > file.txt`
- Step 2: Pattern extracts `--flag` as a file path
- Step 3: Validator blocks legitimate command
- Step 4: User reports hook is broken, disables it

**RISK-002: Working directory mismatch (Risk 8)**
- Step 1: User in worktree runs `echo test > file.txt`
- Step 2: `os.getcwd()` returns worktree path, not P:/
- Step 3: Path validation fails (not in P:/ tree)
- Step 4: Legitimate write blocked, user frustrated

**RISK-003: Command chaining (Risk 7)**
- Step 1: `cd /tmp && echo test > file.txt`
- Step 2: Hook sees entire command, uses initial cwd
- Step 3: File written to /tmp, not P:/, but validation used P:/
- Step 4: Validation logic inverted, wrong decision made

**RISK-004: Performance regression (Risk 6)**
- Step 1: 18 regex patterns run on every bash command
- Step 2: `os.getcwd()` adds system call overhead
- Step 3: Commands with no file ops still pay overhead
- Step 4: User experience degrades, hook disabled for performance

## Step 2.6: AI/LLM-Specific Failures

- **LLM bypass**: AI uses Write tool directly to bypass bash validation
- **Tool confusion**: AI doesn't understand relative vs absolute path distinction
- **Hook ordering**: PreToolUse runs before path resolution, wrong context
- **State management**: No session state to track working directory changes

## Step 3: Categorization

**People/Process**:
- Kill criteria not defined before implementation
- No user testing before deploying

**Technical**:
- Pattern false positives (RISK-001)
- Working directory mismatch (RISK-002)
- Command chaining (RISK-003)
- Performance regression (RISK-004)

**External**:
- Git hooks running from different directories
- Worktree path expectations

## Step 3.5: Reference Class Forecasting

**Similar projects**: Path validation hooks in other codebases
- Base rate: 60% of path validation hooks have false positive issues
- Base rate: 40% of working directory detection fails in worktrees
- Base rate: 30% of regex-based extraction has edge cases

**This project's risks are HIGHER than baseline** because:
- Multiple complex regex patterns (18 total)
- Working directory detection in multi-terminal environment
- Windows-specific path handling

## Step 3.6: Success Theater Detection

**Potential fake metrics**:
- "Hook blocks X commands" → Doesn't measure false positives
- "Zero files at P:/ root" → Doesn't mean fix is working, could mean users gave up
- "Tests pass" → Unit tests don't cover real-world edge cases

**Real metrics needed**:
- False positive rate (legitimate commands blocked)
- User complaints about hook behavior
- Latency measurements on actual workflows

## Step 3.8: Operational Verification Required

**Claims needing evidence**:
- "Fix correctly detects relative paths" → Needs: Test corpus with real commands
- "Hook performance is acceptable" → Needs: Benchmark with typical bash commands
- "Working directory detection works" → Needs: Test in worktree environment

## Step 4: Risk Rating

| ID | Risk | Likelihood | Impact | Score |
|----|------|------------|--------|-------|
| RISK-001 | Pattern false positives | 3 | 3 | **9** |
| RISK-002 | Working directory mismatch | 3 | 3 | **9** |
| RISK-003 | Command chaining | 2 | 3 | 6 |
| RISK-004 | Performance regression | 2 | 2 | 4 |

## Step 4.5: Dependency Cascades

**RISK-001 [causes: RISK-004]**
- Pattern false positives → Users disable hook → Performance becomes irrelevant

**RISK-002 [causes: RISK-001]**
- Working directory mismatch → Wrong paths validated → False positives increase

## Step 5: Prevention (Top 3)

**1. RISK-001: Pattern false positives (Score 9)**
- Create test corpus of 100+ real bash commands from user sessions
- Add negative test cases (commands that should NOT match)
- Implement whitelist for known-safe command patterns
- **Action**: Write `test_relative_path_patterns.py` with real command corpus

**2. RISK-002: Working directory mismatch (Score 9)**
- Add worktree detection to validate working_dir
- Fall back to CLAUDE_PROJECT_DIR if cwd looks wrong
- Add telemetry to track actual cwd values seen
- **Action**: Add worktree check in `run()` function

**3. RISK-003: Command chaining (Score 6)**
- Detect `cd` commands in bash input before path extraction
- Use `CLAUDE_PROJECT_DIR` for chained commands instead of cwd
- Add test cases for command chaining scenarios
- **Action**: Implement cd command detection

## Step 6: Warning Signs

Monitor for:
- User reports of legitimate commands being blocked
- Latency complaints after hook deployment
- Files still appearing at P:/ root (fix not working)
- Hook disabled in settings.json (users gave up)

## Step 7: Adversarial Validation

Detailed findings from adversarial agents will be stored in `.evidence/` directory after execution.
