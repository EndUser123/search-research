# Repository Visibility Guard Hook

**Implementation Date**: 2026-03-14

**Purpose**: Prevents accidental public exposure of P:\ drive repositories that may contain API keys or sensitive data.

**Status**: ✅ **LIVE** - Hook is registered and tested (21/21 tests pass)

---

## Problem Solved

Another terminal made a private repo public, potentially exposing API keys. This hook prevents that from happening again by:

1. **Blocking** P:\ drive repos from being made public
2. **Allowing** packages/ folder repos to be public (as needed)
3. **Allowing** all repos to be made private (safe operation)

---

## What It Blocks

### Commands Blocked (for P:\ drive repos)

```bash
# GitHub CLI
gh repo edit owner/repo --visibility public

# GitHub API via curl
curl -X PATCH api.github.com/repos/owner/repo -d '{"visibility":"public"}'

# GitHub API via wget
wget --method=PATCH api.github.com/repos/owner/repo --body-data='{"visibility":"public"}'

# GitHub API via PowerShell
Invoke-WebRequest -Method Patch -Uri "api.github.com/repos/owner/repo" -Body '{"visibility":"public"}'
```

### Commands Allowed

```bash
# Making repos private (safe operation)
gh repo edit owner/repo --visibility private

# packages/ folder repos can be made public
cd P:/packages/some-lib
gh repo edit owner/repo --visibility public  # Allowed

# Non-P: drives are not protected
cd C:/temp/repo
gh repo edit owner/repo --visibility public  # Allowed
```

---

## Architecture

**File**: `.claude/hooks/PreToolUse_repo_visibility_guard.py`

**Registration**:
- Hook registered in `.claude/hooks/PreToolUse.py` (line 548, Bash hooks)
- Environment variable: `REPO_VISIBILITY_GUARD_ENABLED=true` in `.claude/settings.json`

**Detection Logic**:
1. Checks if command is a Bash tool invocation
2. Detects visibility change commands using regex patterns
3. Gets current git repository path via `git rev-parse --show-toplevel`
4. Blocks if:
   - Repo is on P:\ drive (protected path)
   - NOT in packages/ folder (allowed exception)
   - Attempting to set visibility to public

**Bypass Flag**:
```bash
gh repo edit owner/repo --visibility public --allow-visibility-change
```

---

## Configuration

### Enable/Disable Hook

```bash
# Enable (default)
export REPO_VISIBILITY_GUARD_ENABLED=true

# Disable
export REPO_VISIBILITY_GUARD_ENABLED=false
```

Or set in `.claude/settings.json`:
```json
{
  "env": {
    "REPO_VISIBILITY_GUARD_ENABLED": "true"
  }
}
```

### Protected Paths

**Default protected paths** (in `PreToolUse_repo_visibility_guard.py`):
```python
PROTECTED_PATHS = [
    "P:/",  # P: drive (case-insensitive)
]

ALLOWED_PUBLIC_PATHS = [
    "P:/packages/",  # packages folder (case-insensitive)
]
```

To add more protected paths or exceptions, edit these lists in the hook file.

---

## Error Message

When the hook blocks a command, users see:

```
⛔ REPOSITORY VISIBILITY CHANGE BLOCKED

Repository: P:/my-private-repo
Command: gh repo edit --visibility public

This repository is on the P: drive, which is protected from
being made public to prevent accidental exposure of API keys
and sensitive data.

Exceptions:
• Repositories under P:/packages/ are allowed to be public
• All repositories can be made private (safe operation)

To bypass this check (use with caution):
  Add --allow-visibility-change to your command

To disable this hook:
  export REPO_VISIBILITY_GUARD_ENABLED=false
```

---

## Test Coverage

**Test file**: `.claude/hooks/tests/test_repo_visibility_guard.py`

**21 tests covering**:
- ✅ Path validation (P:\ drive protection, packages/ exceptions)
- ✅ Visibility change detection (GitHub CLI, curl, wget, PowerShell)
- ✅ Blocking logic (blocks P:\ public, allows packages/ public)
- ✅ Bypass flag functionality
- ✅ Integration tests (actual hook execution)

**Run tests**:
```bash
pytest .claude/hooks/tests/test_repo_visibility_guard.py -v
```

**Result**: All 21 tests pass (0.84s)

---

## Limitations

**What this hook DOESN'T protect against**:

1. **Web UI changes**: Hook doesn't prevent visibility changes via GitHub website
   - **Mitigation**: Use GitHub organization policy settings to restrict web UI changes

2. **GitHub Desktop app**: GUI-based visibility changes
   - **Mitigation**: Organization policy settings

3. **Other git hosting platforms**: GitLab, Bitbucket, etc.
   - **Mitigation**: Extend regex patterns to detect their CLI commands

4. **API tokens already exposed**: If API keys were already public, this hook prevents FUTURE exposure but doesn't fix past leaks
   - **Mitigation**: Rotate all exposed API keys immediately

---

## Best Practices

1. **Verify hook is working**: Run the test suite after any changes
2. **Check hook registration**: Verify hook appears in `.claude/hooks/PreToolUse.py` Bash hooks list
3. **Monitor bypass usage**: If `--allow-visibility-change` is used frequently, reconsider path rules
4. **Layer security**: This hook is ONE layer - combine with:
   - GitHub secret scanning (automatic for public repos)
   - Pre-commit hooks (gitleaks, trufflehog)
   - `.gitignore` for `.env` files
   - Environment variable management

---

## Troubleshooting

### Hook not blocking commands

**Check**:
1. Is `REPO_VISIBILITY_GUARD_ENABLED=true` in settings.json?
2. Is hook registered in PreToolUse.py Bash hooks?
3. Run tests: `pytest .claude/hooks/tests/test_repo_visibility_guard.py`
4. Check hook logs: `.claude/hooks/logs/`

### False positives (blocking legitimate commands)

**Solution**: Use bypass flag for exceptions
```bash
gh repo edit owner/repo --visibility public --allow-visibility-change
```

**Long-term**: Add path to `ALLOWED_PUBLIC_PATHS` in hook file

### Hook performance issues

**Baseline**: <100ms latency (not measured yet)

**If slow**:
1. Check if `git rev-parse --show-toplevel` is timing out
2. Consider caching repo path in session state
3. Profile with Python cProfile

---

## Related Security Measures

This hook is part of a layered security strategy:

1. **Repository Visibility Guard** (this hook) - Prevents accidental public exposure
2. **Secret Scanning Hooks** - Detects API keys, tokens, passwords in code
3. **Directory Policy** - Prevents writing to restricted paths
4. **Git Safety Enhancements** - Prevents destructive git operations

For a complete security audit, see:
- `.claude/hooks/CLAUDE.md` - Complete hook documentation
- `.claude/docs/git-safety-enhancements.md` - Git safety improvements

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2026-03-14 | Initial implementation - Created hook, tests, documentation | Claude Code (Sonnet 4.6) |
