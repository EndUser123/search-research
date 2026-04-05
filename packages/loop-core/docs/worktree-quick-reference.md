# Git Worktrees + /ralph-loop: Quick Reference

Fast-path commands for multi-terminal Ralph Loop workflows.

## Setup Commands

### Create Worktrees
```bash
# From main repository
git worktree add ../repo-feature-auth feature/auth-loop
git worktree add ../repo-feature-api feature/api-loop
git worktree add ../repo-bugfix-123 fix/bug-123

# List worktrees
git worktree list
```

### Create Terminal-Specific Plans
```bash
# In each worktree, create plan.{terminal_id}.md
# Example: plan.console_abc123.md

cat > plan.console_abc123.md << 'EOF'
# Feature: My Feature

## RALPH_STATUS
- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks
- [ ] TASK-001 First task
- [ ] TASK-002 Second task
- [ ] TASK-003 Third task
EOF
```

## Run Commands

### Start Loops (Parallel Terminals)
```bash
# Terminal 1
cd ../repo-feature-auth
export CLAUDE_TERMINAL_ID=console_auth
/ralph-loop

# Terminal 2 (simultaneous)
cd ../repo-feature-api
export CLAUDE_TERMINAL_ID=console_api
/ralph-loop

# Terminal 3 (simultaneous)
cd ../repo-bugfix-123
export CLAUDE_TERMINAL_ID=console_bugfix
/ralph-loop
```

## Monitor Commands

### Check Loop State
```bash
# Check loop state
cat ~/.claude/state/terminals/console_auth/loop_state.json

# Watch loop progress
watch -n 5 'cat ~/.claude/state/terminals/console_auth/loop_state.json'

# View decision logs
tail -f ~/.claude/state/terminals/console_auth/logs/decision.log
```

### Check All Loops
```bash
# Find all loop states
find ~/.claude/state/terminals/ -name loop_state.json

# Check exit status
find ~/.claude/state/terminals/ -name loop_state.json -exec grep -l "exit_reason" {} \;
```

## Merge Commands

### Merge Completed Work
```bash
# From main repository
cd /path/to/main/repo

# Merge branches
git merge feature/auth-loop --no-ff -m "feat: Authentication (ralph-loop)"
git merge feature/api-loop --no-ff -m "feat: API v2 (ralph-loop)"
git merge fix/bug-123 --no-ff -m "fix: Bug #123 (ralph-loop)"
```

### Cleanup Worktrees
```bash
# Remove worktrees
git worktree remove ../repo-feature-auth
git worktree remove ../repo-feature-api
git worktree remove ../repo-bugfix-123

# Delete merged branches
git branch -d feature/auth-loop
git branch -d feature/api-loop
git branch -d fix/bug-123

# Cleanup terminal state
rm -rf ~/.claude/state/terminals/console_auth
rm -rf ~/.claude/state/terminals/console_api
rm -rf ~/.claude/state/terminals/console_bugfix
```

## Troubleshooting Commands

### Fix Plan Not Found
```bash
# Check terminal ID
python -c "from scripts.terminal_detection import get_terminal_id; print(get_terminal_id())"

# Use explicit path
/ralph-loop path/to/plan.md
```

### Clear Stale State
```bash
# Clear terminal state
rm -rf ~/.claude/state/terminals/console_auth/

# Restart loop
/ralph-loop
```

### Fix Worktree Conflicts
```bash
# Force remove worktree
git worktree remove -f ../repo-feature-auth

# Remove directory
rm -rf ../repo-feature-auth

# Recreate worktree
git worktree add ../repo-feature-auth feature/auth-loop
```

### Manual Exit Signal
```bash
# Edit plan file to set exit signal
# In plan.{terminal_id}.md:
# EXIT_SIGNAL: true
```

## Verification Commands

### Verify Loop Exit
```bash
# Check exit reason
cat ~/.claude/state/terminals/console_auth/loop_state.json | grep "exit_reason"

# Expected: "exit_reason": "all_conditions_met"
```

### Review Changes
```bash
# In worktree, review changes
cd ../repo-feature-auth
git diff main...HEAD

# View commit log
git log main..HEAD
```

### Pre-Merge Checklist
```bash
# 1. Verify loop exit
cat ~/.claude/state/terminals/console_auth/loop_state.json | grep "exit_reason"

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

## Common Patterns

### Pattern 1: Parallel Features
```bash
git worktree add ../repo-feature-a feature/a
git worktree add ../repo-feature-b feature/b

# Terminal 1: cd ../repo-feature-a && /ralph-loop
# Terminal 2: cd ../repo-feature-b && /ralph-loop
```

### Pattern 2: Bug Sprint
```bash
git worktree add ../repo-bug-101 fix/bug-101
git worktree add ../repo-bug-102 fix/bug-102
git worktree add ../repo-bug-103 fix/bug-103

# Run loops in parallel for each bug
```

### Pattern 3: Testing Isolation
```bash
git worktree add ../repo-test-integration test/integration

cd ../repo-test-integration
cat > plan.console_tester.md << 'EOF'
# Test Suite: Integration Tests
## Tasks
- [ ] TASK-001 Run all integration tests
- [ ] TASK-002 Fix failing tests
- [ ] TASK-003 Verify coverage > 80%
EOF

/ralph-loop
```

## Tips

1. **Use descriptive branch names**: `feature/auth-oauth2-loop`, not `feature-a`
2. **Keep plans in worktree root**: `repo-feature-auth/plan.console_abc123.md`
3. **Clean up after merge**: Remove worktrees and terminal state
4. **Use structured commit messages**: Include terminal ID and completion stats
5. **Monitor loops**: Use `watch` to track progress in real-time

## Full Documentation

See **[ralph-worktrees.md](ralph-worktrees.md)** for complete guide with troubleshooting and advanced patterns.
