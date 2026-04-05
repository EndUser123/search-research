# Review Bundle: Git Safety & Operations Infrastructure

**Generated**: 2026-03-07 17:47 UTC
**Scope**: Git-related hooks and utilities in `P:/.claude/hooks/`
**File Count**: 5 core files (4 active + 1 archived)
**Execution Mode**: Single-agent (small scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **System**: Git Safety & Operations Infrastructure
- **Location**: `P:/.claude/hooks/`
- **Components**: 3 PreToolUse hooks + 1 helper library
- **Status**: Production-active

### Domain & Purpose
The git hooks system provides safety guards and automation for git operations within Claude Code workflows. It prevents accidental data loss, catches common omissions before commits, and provides in-process git operations to avoid subprocess overhead.

### Scale Metrics
- **LOC**: ~1,300 lines across 5 files
- **Subsystems**: 3 PreToolUse hooks + 1 Stop/PostToolUse hook + 1 shared library
- **Deployment scope**: Hooks directory, loaded by Claude Code on session start
- **Change frequency**: Medium (periodic safety enhancements)

### Your Environment
- **OS and shell**: Windows 11, Git Bash (MSYS2)
- **Primary languages and frameworks**: Python 3.14+, subprocess, GitPython (optional)
- **Package managers and build tools**: pip, uv
- **Databases or external services**: Git (local repos), optional GitPython library

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Session                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
    ┌────────────────┐
    │  Hook Events   │
    └────────┬───────┘
             │
      ┌──────┴──────┬──────────────────────┬──────────────┐
      │             │                      │              │
      ▼             ▼                      ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌──────────────┐
│   Git       │ │  Destructive │ │    Git Helper    │ │ Auto-Commit  │
│   Safety    │ │    Guard     │ │   (Library)      │ │              │
│ (PreToolUse)│ │ (PreToolUse) │ │   (Library)      │ │ (Stop/Post)  │
└─────────────┘ └──────────────┘ └──────────────────┘ └──────────────┘
      │                     │                   │              │
      ▼                     ▼                   ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌──────────────┐
│ Checks for  │ │ Blocks       │ │ In-process git   │ │ Auto-commit │
│ forgotten   │ │ dangerous    │ │ operations       │ │ on session  │
│ files       │ │ commands     │ │ (GitPython/       │ │ end         │
│ (advisory)  │ │ (--hard, etc) │ │  subprocess)     │ │              │
└─────────────┘ └──────────────┘ └──────────────────┘ └──────────────┘
```

### Component Details

#### PreToolUse_git_safety.py
- **Purpose**: Advisory hook that catches common omissions before git commits
- **Trigger**: `git commit`, `git merge`, `sl commit` commands
- **Behavior**: Non-blocking (returns info, asks "did we forget anything?")
- **Files**:
  - Staged files with forgettable patterns (config, docs, env files)
  - Modified files not staged (did you forget to add?)
  - Untracked test files
  - Suspicious files (secrets, large files, build artifacts)
- **Special**: Cleans up stale `.git/index.lock` files before running git commands

#### PreToolUse_destructive_git_guard.py
- **Purpose**: Blocks dangerous git operations requiring explicit confirmation
- **Trigger**: Commands with danger flags (`git reset --hard`, `git clean -fd`, etc.)
- **Behavior**: Blocking (requires `--i-understand-irreversible` flag)
- **Protected Operations**:
  - `git reset --hard` (CRITICAL)
  - `git clean -f*` (HIGH)
  - `git stash drop/clear` (HIGH)
  - `git rebase --onto` (MEDIUM)
- **Safety**: Shows affected files, requires explicit approval flag

#### __lib/git_helper.py
- **Purpose**: Shared library for in-process git operations
- **Benefits**:
  - 2-5x faster than subprocess (no process spawn overhead)
  - No process contention with multiple terminals
  - Direct Python object access to git state
  - Graceful fallback to subprocess if GitPython unavailable
- **API**:
  - `GitHelper(cwd)`: Main class
  - `is_git_repo()`: Check if directory is git repo
  - `has_uncommitted_changes()`: Check dirty state
  - `is_worktree()`: Detect worktree vs main repo
  - `add()`, `commit()`, `push()`: Git operations
  - `status()`, `rev_parse()`: Git introspection

#### auto_commit_hook.py (471 lines)
**Location**: `.claude/hooks/auto_commit_hook.py`

**Purpose**: Automatically commit and push uncommitted changes when Claude Code session ends

**Trigger**: Session end (via Stop/PostToolUse hooks)

**Behavior**:
- Scans multiple repos (main P:/ + package subdirectories)
- Commits to each repo independently (failure in one doesn't block others)
- Generates intelligent commit messages:
  1. **Semantic commit parser** (if available): Generates conventional commit format
  2. **Change analyzer** (fallback): Analyzes diffs for notable changes
  3. **Default**: "auto-commit: session end"
- Updates CHANGELOG.md before committing if notable changes detected
- **Special handling for worktrees**:
  - Commits locally (no auto-push)
  - Prevents experimental/broken code from reaching origin/main
  - Manual push via `/git-sync` when ready
- **Main worktree**: Auto-commits AND auto-pushes

**Key Functions**:
- `auto_commit_all()`: Find all repos with uncommitted changes and commit them
- `auto_commit(cwd)`: Commit changes in a single repository
- `find_repos_with_changes()`: Scan P:/ + packages/ for repos with uncommitted changes
- `has_uncommitted_changes()`: Check git status for dirty state
- `is_git_repo()`: Verify directory is git repository
- `is_worktree()`: Detect if in worktree vs main repo
- `analyze_opportunities()`: Log optimization opportunities from commit

**Integration Points**:
- Uses `commit_message_parser.py` for semantic commit messages
- Uses `change_analyzer.py` for change analysis and CHANGELOG updates
- Uses `notification_queue.py` for DUF reminders (now decoupled)
- Uses `GitHelper` library (if available) for faster operations

**Dependencies** (optional):
- `GitHelper` library (preferred for speed, falls back to subprocess)
- `commit_message_parser` module (for semantic commits)
- `change_analyzer` module (for intelligent commit messages)

**Responsibility**: Prevent work loss by auto-committing on session end

**Inputs**: Session end event (Stop/PostToolUse hook)
**Outputs**: Git commits to all repos with uncommitted changes

**Known Limitations**:
- GitHelper disabled for subdirectories (fails in `.claude/hooks/`)
- Only commits to repos with `.git` directory (no shallow clones)
- Requires git to be installed and available in PATH
- Push failures logged but don't block local commits
- CHANGELOG updates only happen in repos with `.claude/hooks/CHANGELOG.md`

#### _archive/PostToolUse_git_state_verifier.py (Archived)
- **Purpose**: Ran after `/compact` to inject actual git state into context
- **Status**: Not currently active (in archive)
- **Feature**: Prevented summary hallucinations by verifying actual vs claimed commits

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### Auto-Commit Flow (Session End)
```
Claude Code session ends
         ↓
Stop/PostToolUse event triggered
         ↓
auto_commit_hook.main()
         ↓
find_repos_with_changes()
         ↓
  ┌─────┴─────┐
  │           │
  ▼           ▼
Package    Main Repo
Repos      (P:/)
  │           │
  └─────┬─────┘
       │
       ▼
  For each repo:
       │
       ├─► has_uncommitted_changes()?
       │         ├─ Yes → Continue
       │         └─ No  → Skip
       │
       ├─► is_worktree()?
       │         ├─ Yes → Commit only (NO push)
       │         └─ No  → Commit + push
       │
       ├─► git add -A
       │
       ├─► Generate commit message:
       │   ├─► commit_message_parser() [semantic]
       │   ├─► change_analyzer() [intelligent]
       │   └─► Default "auto-commit: session end"
       │
       ├─► Update CHANGELOG.md (if notable)
       │
       ├─► git commit -m "<message>"
       │
       └─► git push (if not worktree)
```

#### Git Safety Advisory Flow
```
User runs: git commit -m "message"
         ↓
PreToolUse event triggered
         ↓
PreToolUse_git_safety.main()
         ↓
ensure_fresh_index()  [Clean stale index.lock files]
         ↓
get_git_status()  [Run git status commands]
         ↓
check_forgettables()  [Check for .env, README, etc.]
         ↓
check_suspicious()  [Check for secrets, large files]
         ↓
check_untracked_tests()  [Check for test files]
         ↓
Return JSON with advisory message (non-blocking)
         ↓
Claude sees message, can choose to add files or proceed
```

#### Destructive Operation Guard Flow
```
User runs: git reset --hard HEAD
         ↓
PreToolUse event triggered
         ↓
PreToolUse_destructive_git_guard.run()
         ↓
check_bash_command()  [Detect destructive operation]
         ↓
get_affected_files()  [Show what will be lost]
         ↓
Check for --i-understand-irreversible flag
         ↓
    ├─ Flag present → Allow (exit 0)
    │
    └─ Flag missing → Block with detailed warning (exit 2)
```

### State Management
- **State stores**: Git working directory, index, staged changes
- **Ownership**: Git repository (managed by git, not hooks)
- **Isolation boundaries**: Each hook runs independently, no shared state between hooks
- **Consistency model**: Hooks read git state but don't modify it (except `ensure_fresh_index` cleanup)

### Error Handling
- **Fail-open policy**: If git commands fail, hooks default to allow (don't block legitimate work)
- **Stale lock cleanup**: `ensure_fresh_index()` removes `.git/index.lock` files older than 30 seconds if empty
- **Subprocess fallback**: `git_helper.py` falls back to subprocess if GitPython unavailable
- **Timeout protection**: All git commands have 10-30 second timeouts

---

## 4. COMPONENT INVENTORY

### Core Logic

#### auto_commit_hook.py (471 lines)
**Location**: `.claude/hooks/auto_commit_hook.py`

**Key Functions**:
- `auto_commit_all()`: Find and commit to all repos with uncommitted changes
- `auto_commit(cwd)`: Commit to single repo with intelligent message
- `find_repos_with_changes()`: Scan main + package repos for uncommitted changes
- `has_uncommitted_changes()`: Check git status --porcelain for dirty state
- `is_git_repo()`: Verify .git directory exists
- `is_worktree()`: Detect if .git is a file (worktree indicator)
- `analyze_opportunities()`: Log opportunities from committed changes

**Commit Message Generation**:
1. Semantic parser (conventional commits: "feat:", "fix:", "chore:")
2. Change analyzer (intelligent analysis of diffs)
3. Default: "auto-commit: session end"

**Responsibility**: Auto-commit uncommitted work on session end to prevent data loss

**Inputs**: Session end trigger (Stop/PostToolUse hook event)
**Outputs**: Git commits to multiple repos, status messages

**Known Limitations**:
- GitPython disabled in subdirectories (uses subprocess fallback)
- Only scans immediate package subdirectories (not nested package repos)
- Push failures don't block local commits
- CHANGELOG updates only work in repos with `.claude/hooks/CHANGELOG.md`

---

#### PreToolUse_git_safety.py (338 lines)
**Location**: `.claude/hooks/PreToolUse_git_safety.py`

**Key Functions**:
- `ensure_fresh_index()`: Remove stale `.git/index.lock` files (main + worktrees)
- `get_git_status()`: Run git commands to get staged/modified/untracked files
- `check_forgettables()`: Match files against FORGETTABLE_PATTERNS
- `check_suspicious()`: Match files against SUSPICIOUS_PATTERNS
- `check_untracked_tests()`: Find untracked test files
- `main()`: Hook entry point, orchestrates checks

**Patterns Detected**:
- **Config files**: `.env`, `pytest.ini`, `pyproject.toml`, `package.json`, `.gitignore`
- **Documentation**: `README.md`, `CHANGELOG.md`, `docs/`
- **Suspicious categories**:
  - Secrets: `.env`, `.key`, `.pem`, `credentials.json`
  - Large files: `.png`, `.jpg`, `.zip`, `.db`, `.sqlite`
  - Build artifacts: `node_modules/`, `__pycache__/`, `.pyc`, `.dll`, `.exe`

**Responsibility**: Catch common omissions before commits, provide advisory feedback

**Inputs**: PreToolUse hook event (tool_name, tool_input, command)
**Outputs**: JSON with `allowed: true`, branch info, staged/modified/untracked counts, check results, advisory message

**Known Limitations**:
- Only checks git commit/merge commands (not other git operations)
- Pattern matching is simple substring matching (may have false positives)
- Limited to 5 modified files in output (truncates for display)
- Requires git to be installed and available in PATH

#### PreToolUse_destructive_git_guard.py (233 lines)
**Location**: `.claude/hooks/PreToolUse_destructive_git_guard.py`

**Key Functions**:
- `check_bash_command()`: Parse git command, detect destructive operations
- `get_affected_files()`: Run `git status --porcelain` to get affected files
- `main()`: Hook entry point (subprocess mode)
- `run()`: In-process entry point for PreToolUse router

**Protected Operations**:
```python
DESTRUCTIVE_OPS = {
    "reset": {"danger_flags": ["--hard"], "severity": "CRITICAL"},
    "clean": {"danger_flags": ["-f", "-fd", "-fXd"], "severity": "HIGH"},
    "stash": {"danger_subcommands": {"drop", "clear"}, "severity": "HIGH"},
    "rebase": {"danger_flags": ["--onto"], "severity": "MEDIUM"}
}
```

**Responsibility**: Block destructive git operations without explicit confirmation

**Inputs**: PreToolUse hook event (tool_name, tool_input, command)
**Outputs**: Block decision with detailed warning, or allow (exit 0)

**Known Limitations**:
- Only protects specific dangerous flag combinations
- Scope validation (`-- <path>`) only warns, doesn't block
- Requires manual flag `--i-understand-irreversible` to override

### Utilities/Helpers

#### auto_commit_hook.py (471 lines)
**Location**: `.claude/hooks/auto_commit_hook.py`

**Key Functions**:
- `auto_commit_all()`: Find and commit to all repos with uncommitted changes
- `auto_commit(cwd)`: Commit to single repo with intelligent message
- `find_repos_with_changes()`: Scan main + package repos for uncommitted changes
- `has_uncommitted_changes()`: Check git status --porcelain for dirty state
- `is_git_repo()`: Verify .git directory exists
- `is_worktree()`: Detect if .git is a file (worktree indicator)
- `analyze_opportunities()`: Log opportunities from committed changes
- `run_git_command()`: Fallback subprocess git when GitHelper unavailable

**Commit Message Generation Priority**:
1. `commit_message_parser.generate_semantic_commit_message()` - Semantic/conventional commits
2. `change_analyzer.analyze_changes()` - Change analysis with notable detection
3. Default messages - "auto-commit: session end" or "auto-commit: merge resolution"

**Special Behaviors**:
- **Package repos**: Committed BEFORE main repo (hooks finalized last)
- **Worktrees**: Commit only, NO push (prevents experimental code on origin/main)
- **Main worktree**: Commit AND push
- **CHANGELOG updates**: Staged and committed before main commit if notable changes
- **Merge conflicts**: Use special merge message ("auto-commit: merge resolution")
- **Error isolation**: Failure in one repo doesn't block others

**Responsibility**: Auto-commit uncommitted work on session end to prevent data loss

**Inputs**: Session end trigger (Stop/PostToolUse hook event)
**Outputs**: Git commits to multiple repos, status messages

**Known Limitations**:
- GitPython disabled in subdirectories (uses subprocess fallback)
- Only scans immediate package subdirectories (not nested package repos)
- Push failures don't block local commits (may cause sync issues)
- CHANGELOG updates only work in repos with `.claude/hooks/CHANGELOG.md`
- Requires manual intervention if push fails (local commit succeeds but push doesn't)

---

#### __lib/git_helper.py (257 lines)
**Location**: `.claude/hooks/__lib/git_helper.py`

**Key Classes**:
- `GitHelper`: Main class for in-process git operations

**Key Methods**:
- `is_git_repo()`: Check if cwd is git repository
- `has_uncommitted_changes()`: Check dirty state (untracked_files=True)
- `is_worktree()`: Detect if in worktree vs main repo
- `add(args)`: Stage files (supports `-A`, `-u`, or specific files)
- `commit(message, allow_empty)`: Create commit
- `push(args)`: Push to remote
- `status()`: Get `git status --porcelain` output
- `rev_parse(args)`: Run git rev-parse

**Responsibility**: Provide fast in-process git operations with graceful fallback

**Dependencies**:
- Optional: `gitpython` package (2-5x faster if available)
- Fallback: subprocess to git CLI

**Known Limitations**:
- GitPython is optional but not required
- Fallback subprocess mode used if GitPython unavailable
- Limited to basic git operations (add, commit, push, status, rev-parse)

### Infrastructure

#### _archive/PostToolUse_git_state_verifier.py
**Location**: `.claude/hooks/_archive/PostToolUse_git_state_verifier.py`

**Status**: **ARCHIVED** - Not currently active

**Original Purpose**: Run after `/compact` to verify actual git state vs summary claims

**Why Archived**: Superseded by other verification mechanisms, not integrated into current workflow

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Safety first**: Hooks should prevent accidental data loss
2. **Advisory over blocking**: Prefer warnings over hard blocks where possible
3. **Explicit confirmation**: Dangerous operations require explicit opt-in
4. **Performance**: Use in-process operations when available (GitPython)

### Technology Constraints
- **Python 3.14+**: Hooks use modern Python syntax
- **No external dependencies**: GitPython is optional, hooks work with subprocess fallback
- **Platform support**: Windows (Git Bash/MSYS2) primary target
- **Git version**: Compatible with git 2.30+

### Performance SLAs
- **Hook latency**: < 100ms for in-process checks, < 1s for subprocess git commands
- **Lock cleanup**: Remove stale locks within 30 seconds
- **Timeout protection**: All git commands timeout after 10-30 seconds

### Things That Must NOT Change
1. **Blocking behavior**: `destructive_git_guard` MUST block operations without `--i-understand-irreversible` flag
2. **Advisory nature**: `git_safety` hook MUST remain non-blocking (informational only)
3. **Fail-open policy**: If git commands fail, hooks MUST default to allow (don't block legitimate work)
4. **Backward compatibility**: Hooks MUST work with subprocess fallback if GitPython unavailable

---

## 6. KNOWN ISSUES

### Issue 1: Auto-commit Push Failures
**Scenario**: Auto-commit creates local commits but push fails (network, auth, remote down)
**Expected**: Push succeeds or hook blocks with error
**Actual**: Hook logs error to stderr but allows session to end (local commits remain)
**Impact**: HIGH - Work is committed locally but not pushed to remote, may cause sync issues
**Current Workaround**: Manual `git push` after session ends
**Status**: ⚠️ ACCEPTABLE - Local commits preserve work, push can be manual

### Issue 2: GitHelper Disabled in Subdirectories
**Scenario**: Auto-commit hook runs from `.claude/hooks/` (subdirectory of P:/)
**Expected**: GitHelper should work in subdirectories
**Actual**: GitPython requires repo root, fails in subdirectories (line 13-16)
**Impact**: MEDIUM - Falls back to subprocess (slower, 2-5x overhead)
**Current Workaround**: Automatic fallback to subprocess implemented
**Status**: ✅ MITIGATED - Graceful fallback in place

### Issue 3: Stale .git/index.lock Causes "Another git process running" Errors
**Scenario**: When git processes are killed mid-operation, stale `.git/index.lock` files remain
**Expected**: Hooks should detect and clean stale locks
**Actual**: `ensure_fresh_index()` function implemented (lines 73-138) to handle this
**Impact**: HIGH - Blocks all git operations until manually cleaned
**Current Workaround**: Function automatically removes stale locks > 30 seconds old if empty (0 bytes)
**Status**: ✅ RESOLVED - Implemented in `PreToolUse_git_safety.py`

### Issue 2: Pattern Matching False Positives
**Scenario**: Files like `schema.json` or `database.py` match "suspicious" patterns
**Expected**: Should recognize safe patterns (test, mock, fixture, fake, schema, database)
**Actual**: `SAFE_PATTERNS` list (line 67-70) filters these out
**Impact**: MEDIUM - Reduces noise in warnings
**Current Workaround**: Add file paths to SAFE_PATTERNS if needed
**Status**: ✅ MITIGATED - Safe pattern filtering implemented

### Issue 3: Truncated Output for Modified Files
**Scenario**: More than 5 modified files in git status
**Expected**: Show all modified files
**Actual**: Only shows first 5 files (line 306: `status["modified_files"][:5]`)
**Impact**: LOW - UI limitation, not data loss
**Current Workaround**: None needed, advisory only
**Status**: ✅ ACCEPTABLE - Truncation intentional for display

### Issue 4: Package Repo Scan Depth
**Scenario**: Nested package repos (packages/category/pkgname/.git)
**Expected**: Auto-commit should find and commit to nested repos
**Actual**: Only scans `packages/*` immediate subdirectories (line 306-311)
**Impact**: LOW - Current setup uses flat package structure
**Current Workaround**: None needed for current architecture
**Status**: ✅ ACCEPTABLE - Matches current project structure

### Issue 5: Worktree Lock Detection Priority
**Scenario**: Multiple worktrees with stale locks
**Expected**: Current worktree lock cleaned first (highest priority)
**Actual**: Lines 97-111 insert current worktree lock at beginning of list
**Impact**: MEDIUM - Ensures current terminal's git operations work first
**Current Workaround**: Automatic (no user action needed)
**Status**: ✅ RESOLVED - Worktree priority implemented

---

## 7. INTEGRATION POINTS

### Adding New Git Safety Checks
**Location**: `PreToolUse_git_safety.py`

**Pattern**:
```python
# Add new pattern to FORGETTABLE_PATTERNS or SUSPICIOUS_PATTERNS
FORGETTABLE_PATTERNS = [
    "existing_pattern",
    "your_new_pattern",  # Add here
]

# No code changes needed - check_forgettables() automatically uses it
```

**Invocation**: Automatically runs before every `git commit` command

### Adding New Destructive Operation Guards
**Location**: `PreToolUse_destructive_git_guard.py`

**Pattern**:
```python
DESTRUCTIVE_OPS = {
    "existing_op": {...},
    "your_new_op": {
        "danger_flags": ["--dangerous-flag"],
        "description": "What this does",
        "severity": "CRITICAL|HIGH|MEDIUM"
    }
}
```

**Invocation**: Automatically runs before matching git commands

### Using GitHelper in Other Hooks
**Location**: Any hook file in `.claude/hooks/`

**Pattern**:
```python
from __lib.git_helper import create_git_helper

git = create_git_helper(Path.cwd())
if git.has_uncommitted_changes():
    git.add(["-A"])
    git.commit("auto-commit: session end")
```

**Data Exchange**: Returns boolean success/failure, raises exceptions on errors

**Output/Exit Code**: No exit codes (Python API), returns `True`/`False` for operations

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample 1: Auto-Commit on Session End
```
[auto-commit] Committed to packages/debugRCA
[auto-commit] Committed to .
[auto-commit] All repos committed and pushed
```

### Sample 2: Auto-Commit with Worktree (No Push)
```
[auto-commit] Committed to . (worktree)
[auto-commit] Changes committed locally (push disabled in worktree)
```

### Sample 3: Git Safety Advisory Triggered

### Sample 1: Git Safety Advisory Triggered
```json
{
  "allowed": true,
  "branch": "main",
  "staged_count": 3,
  "modified_count": 1,
  "untracked_count": 2,
  "checks": {
    "Staged": {
      "env": [".env"]
    },
    "Modified (not staged)": ["src/main.py"],
    "Untracked tests": ["test_new_feature.py"]
  },
  "message": "\n🤔 Did we forget anything?\n----------------------------------------\n\n  env:\n    - .env\n\n  Modified (not staged):\n    - src/main.py\n\n  Untracked tests:\n    - test_new_feature.py\n\n----------------------------------------\nReview these before committing. If everything looks good, proceed.\n"
}
```

### Sample 2: Destructive Operation Blocked
```
======================================================================
☢️ DESTRUCTIVE GIT OPERATION DETECTED
======================================================================

Command: git reset --hard HEAD
Severity: CRITICAL
Impact: Discard all uncommitted changes in working directory

======================================================================
FILES THAT WILL BE AFFECTED:
======================================================================
  M  src/download/batch_downloader.py
  M  src/api/client.py
  ??  test_temp.py

======================================================================
CRITICAL: This operation cannot be undone!
======================================================================

To proceed, you MUST:
1. Confirm you understand what will be deleted
2. Specify the scope (e.g., "only files related to task X")
3. Use explicit approval flag: --i-understand-irreversible

Example safe usage:
  git reset --hard 7d0011fd4e -- -- src/yt_fts/download/batch_downloader.py

If you need to reset everything, run:
  echo "RECOVERY_CODE: DESTROY_ALL" | git reset --hard

❌ BLOCKED: Missing explicit approval flag --i-understand-irreversible
Add this flag to confirm you understand this operation cannot be undone.
```

### Sample 3: Stale Lock Cleanup (from debugRCA session)
**Context**: This morning's git problems were caused by stale `.git/index.lock` files
**Fix Applied**: `ensure_fresh_index()` function automatically cleaned these up
**Result**: Git operations resumed working without manual intervention

---

## END OF BUNDLE

**Next Steps**:
1. Review the git safety patterns in `FORGETTABLE_PATTERNS` and `SUSPICIOUS_PATTERNS`
2. Consider adding project-specific patterns to these lists
3. Test the destructive operation guard with `git reset --hard` (with test files only)
4. Verify GitPython is installed for 2-5x performance improvement

**Contact**: See `.claude/hooks/CLAUDE.md` for hook architecture documentation
