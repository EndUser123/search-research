# Git Context Integration for /gto

## Purpose

/gto automatically enhances gap analysis with git state awareness when a `.git/` directory is detected in the working directory. This requires no configuration and works safely in multi-terminal environments.

## How It Works

When git repository is detected, /gto automatically:

1. **Detects current branch**: Shows active branch name
2. **Checks dirty state**: Identifies uncommitted changes
3. **Analyzes recent commits**: Last 10 commits with full metadata
4. **Tracks modified files**: All modified files (staged + unstaged + untracked)
5. **Classifies commit patterns**: Categorizes commits by type
6. **Measures activity level**: HIGH (10+ commits), MEDIUM (5-9), LOW (0-4)
7. **Detects patterns**: Identifies dominant development patterns

## Multi-Terminal Safety

Git repository is the **shared source of truth** across terminals:
- ✅ All reads are fresh (no caching)
- ✅ Ensures stale-data immunity
- ✅ Multiple terminals can run /gto simultaneously without state conflicts
- ✅ No file-based state that can diverge between terminals

## Git Analysis Features

### Current Branch + Dirty State
```markdown
### Git Context
- Branch: main (dirty: 3 modified files)
```

### Recent Commits Analysis
- **Last 10 commits** with full metadata:
  - Author
  - Timestamp (ISO format)
  - Commit message (subject line)
  - Files changed
  - Insertions/deletions

### Modified Files Tracking
All modified files across:
- **Staged**: Files added to git index
- **Unstaged**: Files modified but not staged
- **Untracked**: New files not yet added to git

### Commit Pattern Detection

**Commit Types**:
- **FEATURE**: New features, functionality additions
- **REFACTOR**: Code restructuring without behavior change
- **BUGFIX**: Bug fixes, error corrections
- **TEST**: Test additions, modifications
- **DOCUMENTATION**: Doc changes, README updates
- **MERGER**: Merge commits
- **OTHER**: Unclassified commits

**Development Activity Levels**:
- **HIGH**: 10+ commits (active development)
- **MEDIUM**: 5-9 commits (moderate activity)
- **LOW**: 0-4 commits (light activity)

### Pattern Detection

Identifies dominant patterns like:
- **"Feature development focus"**: Mostly FEATURE commits
- **"Bug fixing focus"**: Mostly BUGFIX commits
- **"Active refactoring"**: Mostly REFACTOR commits
- **"Test development activity"**: Mostly TEST commits

## Example Output

```markdown
### Git Context
- Branch: main (dirty: 3 modified files)
- Recent commits: 10 (FEATURE focus detected)
- Activity: HIGH
- Modified: src/git_context.py, SKILL.md, tests/test_git.py
- Commit types: 4 FEATURE, 3 REFACTOR, 2 BUGFIX, 1 TEST
```

## Usage

**Automatic activation**: Git context is automatically included when:
- `.git/` directory exists in working directory
- No flags or configuration required

**Manual invocation**: Just run `/gto` as usual
```bash
/gto                # Compact mode with git context
/gto -v             # Verbose mode with git context
```

## Integration with Gap Analysis

Git context enhances /gto's gap detection:

### Cleanup Detection
- **Uncommitted changes**: Flags work that needs committing
- **Stale branches**: Suggests branch cleanup
- **Merge conflicts**: Detects unresolved merge state

### Broken Windows Detection
- **Modified files**: Shows partial work in progress
- **Commit gaps**: Detects streaks without commits (potential untracked work)

### Context State
- **Branch state**: Shows current branch and whether it's clean/dirty
- **Recent work**: Summarizes last 10 commits for context

### Detached HEAD Detection (CRITICAL)

**What it is**: Working directly on a commit SHA instead of a branch. Commits made on detached HEAD are **orphaned** and can be garbage collected.

**Detection command**:
```bash
git symbolic-ref -q HEAD
# Returns non-zero exit code when detached
# Returns "refs/heads/<branch>" when on a branch
```

**Output enhancement**:
```markdown
### Git Context
- ⚠️ DETACHED HEAD (commit 39a0ce1) — CREATE BRANCH NOW
- Or run: git checkout -b <branch-name>
```

**When detected**: ALWAYS flag as Critical severity - work is at risk of being lost

### Orphaned Commit Detection (CRITICAL)

**What it is**: A commit that exists but is not reachable from any branch ref. These commits will eventually be garbage collected.

**Detection command**:
```bash
git branch --contains HEAD
# If empty output or "no branch", commit is orphaned
```

**Example scenario** (from actual session):
```
HEAD detached from cleanup-pre-task-019-20260316-225720
Commit: 39a0ce1014 feat(testing): add CONVENTION claim type + integration boundary hardening
git branch --contains HEAD → (empty - commit is orphaned!)
```

**Output enhancement**:
```markdown
### Git Context
- ⚠️ ORPHANED COMMIT: 39a0ce1014 not on any branch
- Immediate action: git branch <name> OR git checkout -b <name>
- Risk: Commit will be garbage collected and lost
```

### Pre-existing Test Failure Detection

**What it is**: Session ends with acknowledgment of broken tests that weren't fixed.

**Detection signals in chat**:
- "X pre-existing failures"
- "unchanged from before this session"
- "tests that use <deleted code>"
- Test output showing FAILED with "(unchanged from before)"

**Output enhancement**:
```markdown
### Git Context
- 🟡 Pre-existing test failures: 24 tests failing (TestPathNormalization, TestEntityMatching, etc.)
- These reference deleted code from "Phase 2 refactor" - needs ticket or fix
```

**Severity**: Medium - should be documented/fixed, not left as hidden debt

## Technical Implementation

### Git Commands Used

```bash
# Get current branch
git rev-parse --abbrev-ref HEAD

# Check dirty state
git status --porcelain

# Get recent commits
git log -10 --pretty=format:'%H|%an|%ai|%s' --name-status

# Get modified files
git status --porcelain

# Detached HEAD detection (CRITICAL)
git symbolic-ref -q HEAD
# Returns non-zero exit code when detached

# Orphaned commit detection (CRITICAL)
git branch --contains HEAD
# Empty output = commit not on any branch
```

### Performance

- **Typical execution**: < 1 second for 10 commits
- **Large repos**: May take 2-3 seconds for 1000+ commits
- **No caching**: Always fresh data from git repository
- **Multi-terminal safe**: No shared state files

## Error Handling

### Not a Git Repository
- Gracefully degrades: No git context section in output
- No error messages: Silently skips git analysis
- Continues with chat-only analysis

### Git Command Failures
- Individual git command failures don't crash /gto
- Missing git context sections show warning: "(git analysis failed)"
- Continues with remaining analysis

## Future Enhancements

Potential improvements (not currently implemented):

- **Stale branch detection**: List branches not merged in > 30 days
- **Commit message quality**: Check for conventional compliance
- **Code churn metrics**: Track files with most changes
- **Contributor analysis**: Show commit distribution by author
- **Release tracking**: Detect version tags and release patterns

## Version: 1.1

Last updated: 2026-03-17

**Changes in 1.1**:
- Added detached HEAD detection (Critical severity)
- Added orphaned commit detection (Critical severity)
- Added pre-existing test failure detection (Medium severity)
- Updated git commands reference with new detection commands

## Related Skills

- **/git**: Git operations (sync, worktree, conflict resolution)
- **/github-ready**: PR workflow and commit validation
- **/ship**: Deploy readiness with git state checks

## Version: 1.0

Last updated: 2026-03-15
