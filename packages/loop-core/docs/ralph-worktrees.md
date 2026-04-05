# Ralph Loop + Git Worktrees: Multi-Terminal Workflow

This guide documents the recommended pattern for running multiple `/ralph-loop` instances in parallel using git worktrees for complete isolation.

## Overview

**Problem**: Running multiple autonomous loops in different terminals on the same codebase can cause:
- Git conflicts from concurrent operations
- State pollution between loops
- Difficulty merging divergent work

**Solution**: Git worktrees + per-terminal plans + isolated state
- Each terminal gets its own working directory (worktree)
- Each worktree runs `/ralph-loop` with terminal-specific plans
- Merge changes back to main branch after loops complete

## Architecture

```
repository/
├── main/                    # Primary working tree (your normal workspace)
├── worktree-feature-auth/   # Worktree for authentication loop
├── worktree-feature-api/    # Worktree for API loop
└── worktree-bugfix-123/     # Worktree for bug fix loop
```

Each worktree:
- Has its own git working directory (isolated files)
- Shares the same `.git` database (efficient storage)
- Can have its own branch (isolated commits)
- Uses per-terminal state in `~/.claude/state/terminals/<terminal_id>/`

## Prerequisites

- TASK-012 completed (per-terminal state isolation)
- `/ralph-loop` skill installed
- Git worktree support (Git 2.17+)

## Quick Start

### 1. Create Worktrees for Each Loop

```bash
# From your main repository directory
cd /path/to/your/repository

# Create worktree for feature branch
git worktree add ../repo-feature-auth feature/auth-loop
git worktree add ../repo-feature-api feature/api-loop
git worktree add ../repo-bugfix-123 fix/bug-123

# Verify worktrees
git worktree list
```

**Output:**
```
/path/to/repo              abc1234 [main]
/path/to/repo-feature-auth def5678 [feature/auth-loop]
/path/to/repo-feature-api  ghi9012 [feature/api-loop]
/path/to/repo-bugfix-123   jkl3456 [fix/bug-123]
```

### 2. Create Terminal-Specific Plans

In **each worktree**, create a terminal-specific plan:

```bash
# Terminal 1: In repo-feature-auth worktree
cd ../repo-feature-auth

# Create plan for this terminal
cat > plan.console_abc123.md << 'EOF'
# Feature: Authentication System

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design user schema and migration
- [ ] TASK-002 Implement password hashing
- [ ] TASK-003 Create login endpoint
- [ ] TASK-004 Add JWT token handling
- [ ] TASK-005 Write integration tests
- [ ] TASK-006 Verify all tests pass
EOF
```

```bash
# Terminal 2: In repo-feature-api worktree
cd ../repo-feature-api

# Create plan for this terminal
cat > plan.console_xyz789.md << 'EOF'
# Feature: REST API v2

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design API endpoints
- [ ] TASK-002 Implement request validation
- [ ] TASK-003 Add rate limiting
- [ ] TASK-004 Write API tests
- [ ] TASK-005 Verify documentation
EOF
```

```bash
# Terminal 3: In repo-bugfix-123 worktree
cd ../repo-bugfix-123

# Create plan for this terminal
cat > plan.console_def456.md << 'EOF'
# Bug Fix: Navigation Menu Issue #123

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Reproduce navigation bug
- [ ] TASK-002 Identify root cause
- [ ] TASK-003 Implement fix
- [ ] TASK-004 Add regression test
- [ ] TASK-005 Verify fix in browser
EOF
```

### 3. Run /ralph-loop in Each Terminal

Open a separate terminal for each worktree:

```bash
# Terminal 1
cd /path/to/repo-feature-auth
/ralph-loop

# Terminal 2 (simultaneous)
cd /path/to/repo-feature-api
/ralph-loop

# Terminal 3 (simultaneous)
cd /path/to/repo-bugfix-123
/ralph-loop
```

Each terminal will:
1. Auto-detect its terminal ID
2. Find its `plan.{terminal_id}.md` file
3. Run autonomous loop until exit conditions met
4. Save state to `~/.claude/state/terminals/<terminal_id>/`

### 4. Merge Completed Work

After loops exit, merge branches back to main:

```bash
# From main repository
cd /path/to/repo

# Merge feature/auth-loop
git merge feature/auth-loop --no-ff -m "feat: Add authentication system (ralph-loop)"

# Merge feature/api-loop
git merge feature/api-loop --no-ff -m "feat: Add REST API v2 (ralph-loop)"

# Merge fix/bug-123
git merge fix/bug-123 --no-ff -m "fix: Navigation menu issue #123 (ralph-loop)"
```

### 5. Clean Up Worktrees

```bash
# Remove worktrees after merging
git worktree remove ../repo-feature-auth
git worktree remove ../repo-feature-api
git worktree remove ../repo-bugfix-123

# Verify cleanup
git worktree list
```

## Detailed Workflow

### Phase 1: Setup

#### 1.1 Create Branches

```bash
# Create branches for each loop
git checkout -b feature/auth-loop
git checkout -b feature/api-loop
git checkout -b fix/bugfix-123

# Return to main
git checkout main
```

#### 1.2 Create Worktrees

```bash
# Create worktrees from branches
git worktree add ../repo-auth feature/auth-loop
git worktree add ../repo-api feature/api-loop
git worktree add ../repo-bugfix fix/bugfix-123
```

#### 1.3 Configure Loop Policy (Optional)

Create `.claude/loop/config.yaml` in each worktree:

```yaml
# .claude/loop/config.yaml
exit_policy:
  min_completion_indicators: 2
  require_exit_signal: true
  require_all_tasks_complete: false
  require_verification_pass: false

observability:
  log_iterations: true
  save_reports: true
```

### Phase 2: Execution

#### 2.1 Terminal Identification

Each terminal gets a unique ID from environment:

```python
# Terminal ID detection (automatic)
# Windows: %USERNAME%_%SESSION% (e.g., brsth_1)
# Linux/Mac: $USER_$TERM_SESSION_ID (e.g., user_abc123)
```

#### 2.2 Plan Resolution

`/ralph-loop` searches for plans in priority order:

1. **Explicit path**: `/ralph-loop path/to/plan.md`
2. **Default location**: `.claude/loop/plan.md`
3. **Per-terminal**: `plan.{terminal_id}.md`
4. **Root fallback**: `plan.md`

#### 2.3 State Isolation

Each terminal's state is stored separately:

```
~/.claude/state/terminals/
├── console_abc123/
│   ├── loop_state.json       # Loop state for auth feature
│   ├── loop_metrics.json     # Performance metrics
│   └── logs/
│       └── decision.log      # Decision log
├── console_xyz789/
│   ├── loop_state.json       # Loop state for API feature
│   └── ...
└── console_def456/
    └── ...                   # Loop state for bug fix
```

#### 2.4 Monitoring Loops

Monitor loop progress in real-time:

```bash
# Watch loop state (Terminal 1)
watch -n 5 'cat ~/.claude/state/terminals/console_abc123/loop_state.json'

# Watch loop state (Terminal 2)
watch -n 5 'cat ~/.claude/state/terminals/console_xyz789/loop_state.json'

# View decision logs
tail -f ~/.claude/state/terminals/console_abc123/logs/decision.log
```

### Phase 3: Completion

#### 3.1 Verify Loop Exit

Check that loops exited cleanly:

```bash
# Check loop state
cat ~/.claude/state/terminals/console_abc123/loop_state.json

# Look for:
# - "exit_reason": "all_conditions_met"
# - "completion_indicators": 2
# - "EXIT_SIGNAL": true
```

#### 3.2 Review Changes

Review changes in each worktree:

```bash
# In repo-auth worktree
cd ../repo-auth
git diff main...HEAD

# In repo-api worktree
cd ../repo-api
git diff main...HEAD
```

#### 3.3 Merge Strategy

Use `--no-ff` to preserve loop history:

```bash
# From main repository
cd /path/to/repo

# Merge with merge commit (preserves loop history)
git merge feature/auth-loop --no-ff -m "feat: Authentication system

Implemented via /ralph-loop with terminal ID: console_abc123
Plan: plan.console_abc123.md
Completion: 6/6 tasks
Exit: EXIT_SIGNAL + 2 completion indicators
"
```

## Advanced Patterns

### Pattern 1: Parallel Feature Development

**Use case**: Multiple features developed simultaneously

```bash
# Create worktrees
git worktree add ../repo-user-auth feature/user-auth
git worktree add ../repo-admin-panel feature/admin-panel
git worktree add ../repo-api-client feature/api-client

# Run loops in parallel
# Terminal 1: cd ../repo-user-auth && /ralph-loop
# Terminal 2: cd ../repo-admin-panel && /ralph-loop
# Terminal 3: cd ../repo-api-client && /ralph-loop
```

**Benefits**:
- Zero git conflicts
- Isolated development state
- Independent loop execution
- Clean merge history

### Pattern 2: Bug Sprint

**Use case**: Fix multiple bugs in parallel

```bash
# Create worktrees for each bug
git worktree add ../repo-bug-101 fix/bug-101
git worktree add ../repo-bug-102 fix/bug-102
git worktree add ../repo-bug-103 fix/bug-103

# Each worktree has a focused plan
# repo-bug-101/plan.console_abc123.md: Fix navigation
# repo-bug-102/plan.console_xyz789.md: Fix login
# repo-bug-103/plan.console_def456.md: Fix checkout
```

### Pattern 3: Refactor + Feature

**Use case**: Refactor while adding new features

```bash
# Main worktree: Refactor
cd /path/to/repo
git checkout -b refactor/database
# Run /ralph-loop with refactor plan

# Second worktree: New feature (depends on refactor)
git worktree add ../repo-new-feature feature/new-feature
# Run /ralph-loop after refactor completes
```

### Pattern 4: Testing Isolation

**Use case**: Run test loops in isolation

```bash
# Create worktree for testing
git worktree add ../repo-test-integration test/integration-suite

# In worktree, create test-focused plan
cat > plan.console_tester.md << 'EOF'
# Test Suite: Integration Tests

## Tasks
- [ ] TASK-001 Run all integration tests
- [ ] TASK-002 Fix failing tests
- [ ] TASK-003 Verify coverage > 80%
- [ ] TASK-004 Update test documentation
EOF

# Run test loop
cd ../repo-test-integration
/ralph-loop
```

## Troubleshooting

### Issue: Plan Not Found

**Symptom**: `/ralph-loop` reports "No plan file found"

**Diagnosis**: Terminal ID mismatch or plan missing

**Solution**:

```bash
# Check terminal ID
python -c "from scripts.terminal_detection import get_terminal_id; print(get_terminal_id())"

# Create plan with correct terminal ID
cat > plan.console_abc123.md << 'EOF'
# Plan
## Tasks
- [ ] TASK-001 Example task
EOF

# Or use explicit path
/ralph-loop path/to/plan.md
```

### Issue: State Pollution

**Symptom**: Loop state from previous run interfering

**Diagnosis**: Stale state in `~/.claude/state/terminals/<terminal_id>/`

**Solution**:

```bash
# Clear terminal state
rm -rf ~/.claude/state/terminals/console_abc123/

# Restart loop
/ralph-loop
```

### Issue: Git Merge Conflicts

**Symptom**: Conflicts when merging worktree branches

**Diagnosis**: Overlapping file changes in different worktrees

**Solution**:

```bash
# Use strategy option for conflicts
git merge feature/auth-loop -X theirs --no-ff

# Or resolve conflicts manually
git merge feature/auth-loop --no-ff
# Resolve conflicts
git add .
git commit -m "feat: Authentication system (conflicts resolved)"
```

### Issue: Worktree Already Exists

**Symptom**: `git worktree add` fails with "worktree already exists"

**Diagnosis**: Worktree directory not properly cleaned up

**Solution**:

```bash
# Force remove worktree
git worktree remove -f ../repo-feature-auth

# Remove directory if it still exists
rm -rf ../repo-feature-auth

# Recreate worktree
git worktree add ../repo-feature-auth feature/auth-loop
```

### Issue: Loop Hangs

**Symptom**: `/ralph-loop` doesn't exit

**Diagnosis**: Exit conditions not met, infinite loop

**Solution**:

```bash
# Check loop state
cat ~/.claude/state/terminals/console_abc123/loop_state.json

# Manually set EXIT_SIGNAL
# Edit plan.{terminal_id}.md:
# EXIT_SIGNAL: true

# Or kill loop process
# Ctrl+C or kill from another terminal
```

### Issue: Terminal ID Collision

**Symptom**: Two terminals get same ID

**Diagnosis**: Environment variables not unique

**Solution**:

```bash
# Manually set terminal ID
export CLAUDE_TERMINAL_ID="terminal_1"

# Run loop
/ralph-loop

# Or use explicit plan paths
/ralph-loop plan-feature-a.md
/ralph-loop plan-feature-b.md
```

## Best Practices

### 1. Branch Naming

Use descriptive branch names:

```bash
# Good
feature/auth-oauth2-loop
fix/navigation-bug-123-loop
refactor/database-migration-loop

# Avoid
feature-a
fix-b
test-1
```

### 2. Plan Organization

Keep plans in worktree root:

```bash
# Good
repo-feature-auth/plan.console_abc123.md

# Works but less convenient
repo-feature-auth/.claude/loop/plan.md
repo-feature-auth/docs/plans/auth.md
```

### 3. State Management

Clean up state after successful merges:

```bash
# After merging branch
git branch -d feature/auth-loop

# Clean up terminal state
rm -rf ~/.claude/state/terminals/console_abc123/

# Remove worktree
git worktree remove ../repo-feature-auth
```

### 4. Commit Messages

Use structured commit messages:

```bash
git merge feature/auth-loop --no-ff -m "feat: OAuth2 authentication

Implemented via /ralph-loop (terminal: console_abc123)

Plan: plan.console_abc123.md
Tasks: 6/6 complete
Exit: EXIT_SIGNAL + 2 completion indicators

Changes:
- Add user schema and migrations
- Implement password hashing with bcrypt
- Create login endpoint with JWT
- Add token refresh mechanism
- Write integration tests
- Achieve 85% test coverage
"
```

### 5. Monitoring

Monitor loop health:

```bash
# Check all loop states
find ~/.claude/state/terminals/ -name loop_state.json -exec echo "==== {} ====" \; -exec cat {} \;

# Check for stuck loops
find ~/.claude/state/terminals/ -name loop_state.json -exec grep -l '"iteration": 100' {} \;
```

## Integration with CI/CD

### Pre-Merge Checklist

Before merging loop branches:

```bash
# 1. Verify loop exited cleanly
cat ~/.claude/state/terminals/console_abc123/loop_state.json | grep "exit_reason"

# 2. Run tests
pytest tests/ -v --cov

# 3. Check coverage
coverage report | grep TOTAL

# 4. Linting
ruff check .
mypy .

# 5. Verify no merge conflicts
git merge main --no-commit --no-ff
git merge --abort
```

### Automated Merge Script

```bash
#!/bin/bash
# merge-loop-branch.sh

set -e

BRANCH=$1
TERMINAL_ID=$2

echo "Merging $BRANCH (terminal: $TERMINAL_ID)"

# Verify loop exit
if ! grep -q '"exit_reason": "all_conditions_met"' ~/.claude/state/terminals/$TERMINAL_ID/loop_state.json; then
    echo "Error: Loop did not exit cleanly"
    exit 1
fi

# Run tests
pytest tests/ -v --cov

# Merge branch
git checkout main
git merge $BRANCH --no-ff -m "feat: Merge $BRANCH (terminal: $TERMINAL_ID)"

# Cleanup
git branch -d $BRANCH
rm -rf ~/.claude/state/terminals/$TERMINAL_ID/

echo "Merge complete"
```

Usage:

```bash
./merge-loop-branch.sh feature/auth-loop console_abc123
./merge-loop-branch.sh feature/api-loop console_xyz789
```

## Performance Considerations

### Disk Usage

Worktrees share `.git` database but duplicate working files:

```bash
# Check disk usage
du -sh ../repo-*
du -sh .git

# Typical usage:
# repo-feature-auth: 50M  (working files)
# repo-feature-api: 50M   (working files)
# .git: 200M              (shared git database)
# Total: 300M (vs 400M for full clones)
```

### Loop Performance

Parallel loops don't significantly impact performance:

- **CPU**: Each loop uses one Claude API call per task
- **I/O**: Terminal state is isolated (no contention)
- **Git**: Worktrees don't interfere (separate working directories)

### Resource Limits

For resource-constrained systems:

```bash
# Limit concurrent loops
# Run 2 loops at a time instead of 4

# Monitor memory usage
watch -n 5 'ps aux | grep -E "python|claude" | head -10'

# Clean up old state
find ~/.claude/state/terminals/ -mtime +7 -exec rm -rf {} \;
```

## Alternatives

### Alternative 1: Single Terminal, Sequential Loops

```bash
# Run loops sequentially in same terminal
/ralph-loop plan-feature-a.md
/ralph-loop plan-feature-b.md
/ralph-loop plan-feature-c.md
```

**Pros**: Simpler setup
**Cons**: Slower (sequential execution)

### Alternative 2: Single Worktree, Multiple Plans

```bash
# Use explicit plan paths
/ralph-loop plan-feature-a.md
# (in different terminal)
/ralph-loop plan-feature-b.md
# (in different terminal)
/ralph-loop plan-feature-c.md
```

**Pros**: No worktree overhead
**Cons**: Potential git conflicts

### Alternative 3: Docker Containers

```bash
# Run each loop in Docker container
docker run -v $(pwd):/work -it claude-loop /ralph-loop
```

**Pros**: Complete isolation
**Cons**: Complex setup, resource overhead

## Summary

Git worktrees + `/ralph-loop` provides:

✅ **Complete isolation** (no git conflicts)
✅ **Parallel execution** (faster development)
✅ **Clean merges** (preserved history)
✅ **Scalable workflow** (unlimited terminals)
✅ **Zero coordination** (independent loops)

**Recommended for**:
- Multi-feature development
- Bug sprints
- Parallel refactoring
- Testing isolation
- Team collaboration

## References

- **Git Worktree Documentation**: https://git-scm.com/docs/git-worktree
- **/ralph-loop Skill**: `P:/packages/loop-code/skills/ralph-loop/SKILL.md`
- **/loop-code Skill**: `P:/packages/loop-code/skills/loop-code/SKILL.md`
- **Loop Architecture**: `P:/packages/loop-code/ARCHITECTURE.md`
- **Usage Examples**: `P:/packages/loop-code/USAGE_EXAMPLES.md`

## Tags

ralph-loop, git-worktree, multi-terminal, parallel-development, workflow, isolation
