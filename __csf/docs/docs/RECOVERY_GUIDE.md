# Recovery Guide: Auto-Backup and Intent Validation

## What Happened?

If a file got deleted or modified unexpectedly, this guide helps you recover it.

### Two-Layer Safety System

**Layer 1: Prevention (Intent Validation)**
- Blocks destructive operations when user intent cannot be verified
- Example: You didn't ask to delete, but LLM tries `rm file.txt` → BLOCKED

**Layer 2: Recovery (Auto-Backup)**
- Creates git commit after successful destructive operations
- Example: You authorized delete, file is gone → Git commit created for recovery

## How to Recover

### Option 1: View Recent Commits (Safest First)

```bash
# See all recent commits including auto-backups
git log --oneline -20

# Or see all operations (including branch deletes)
git reflog
```

### Option 2: Restore Single File

```bash
# Restore file to its previous state
git checkout HEAD~1 -- path/to/file

# Or view what it was before deletion
git show HEAD~1:path/to/file > backup.txt
```

### Option 3: Restore Entire Worktree State

```bash
# Go back to before the operation
git reset --hard HEAD~1

# Warning: This loses any uncommitted changes!
```

### Option 4: Find Deleted Branch

If a git branch was deleted:

```bash
# See deleted refs
git reflog

# Recreate branch from reflog
git checkout -b branch-name <SHA-from-reflog>
```

### Option 5: Undo Git Reset

If you used `git reset --hard` and want to undo:

```bash
# Reset reset via reflog
git reflog
git reset --hard <SHA-before-reset>
```

## Real-World Recovery Scenarios

### Scenario: LLM Deleted File Without Asking

```bash
# 1. Check recent commits
git log --oneline -5

# You might see:
# abc1234 auto-backup: Delete 2026-01-23T12:00:00
# def5678 Some previous commit

# 2. Restore the file
git show abc1234:path/to/file > path/to/file

# 3. Verify restoration
cat path/to/file
```

### Scenario: Git Reset Gone Wrong

```bash
# 1. Find the commit before reset
git reflog

# 2. Reset back to that commit
git reset --hard <SHA-before-reset>

# 3. Verify files are back
git status
```

### Scenario: Accidentally Deleted Branch

```bash
# 1. Find where branch was deleted
git reflog | grep branch-name

# 2. Recreate from that point
git checkout -b branch-name <SHA>

# 3. Verify
git log --oneline
```

## How to Prevent Future Issues

### Adjust Confidence Thresholds

If intent validation is blocking legitimate operations, edit `P:\.claude\settings.toml`:

```toml
[intent_validation]
block_threshold = 50    # Higher = blocks more (safer)
prompt_threshold = 75  # More prompting = safer
```

- **Lower thresholds** = Less blocking (faster, but riskier)
- **Higher thresholds** = More blocking (safer, but more prompts)

### Monitor Auto-Backup Commits

```bash
# See all auto-backup commits
git log --oneline --grep="auto-backup"
```

If too noisy, you can disable auto-backup:

```toml
[auto_backup]
enabled = false
```

### Review Signal Keywords

If intent validation blocked legitimate operations, add your own signals:

```toml
[destructive_signals.explicit]
# Add your own phrases
"nuke", "obliterate", "purge"
```

## Troubleshooting

### Q: Can I undo the recovery?

A: Yes. `git reflog` shows all operations. You can reset to any point.

```bash
git reflog
git reset --hard <any-SHA>
```

### Q: Will auto-backup cause too many commits?

A: Only created after actual destructive operations. You can squash them later:

```bash
# Squash last N auto-backup commits
git rebase -i HEAD~N
```

### Q: What if the file is lost after recovery?

A: It's in git. You can always recover from any prior commit:

```bash
# Find the commit where file existed
git log --all --full-history -- path/to/file

# Checkout from that commit
git checkout <commit-SHA> -- path/to/file
```

### Q: How do I know what was deleted?

A: Check the commit message and diff:

```bash
# See what changed in the backup commit
git show HEAD~1 --stat

# See the actual content that was removed
git show HEAD~1:path/to/deleted-file
```

### Q: Can I disable intent validation?

A: Yes, if you find it too restrictive:

```toml
[intent_validation]
enabled = false
```

Or temporarily:

```bash
export INTENT_VALIDATION_ENABLED="false"
```

## Quick Reference

| Action | Command |
|--------|---------|
| View recent commits | `git log --oneline -20` |
| View all operations | `git reflog` |
| Restore single file | `git checkout HEAD~1 -- path/to/file` |
| Undo reset | `git reset --hard <SHA-before-reset>` |
| Disable intent validation | Edit `settings.toml`: `enabled = false` |
| Enable debug mode | Edit `settings.toml`: `debug_mode = true` |

## FAQ

**Q: Can intent validation make mistakes?**
A: Yes, that's why Layer 2 (auto-backup) exists. If Layer 1 allows something it shouldn't, Layer 2 provides recovery.

**Q: What if both layers fail?**
A: `git reflog` is the ultimate fallback. It records all ref movements for 90+ days.

**Q: How do I know if a recovery commit exists?**
A: Look for "auto-backup" in commit messages:
```bash
git log --oneline --grep="auto-backup"
```

**Q: Can I customize the commit message format?**
A: Yes, edit `settings.toml`:
```toml
[auto_backup]
commit_message_prefix = "my-backup"
```

**Q: What if multiple terminals run simultaneously?**
A: Each terminal creates its own commits. Git handles concurrent operations safely. No conflicts expected.
