# Configuration Guide: Intent Validation + Auto-Backup

## Quick Start

Intent validation is preconfigured with conservative defaults. No action needed—it just works.

For advanced tuning, edit `P:\.claude\settings.toml`.

## Understanding Thresholds

### Confidence Scoring (0-100%)

Each destructive operation gets a confidence score based on:

| Source | Points | Example |
|--------|--------|---------|
| **Base score** | Varies by severity | Critical: 0%, High: 10%, Medium: 30% |
| **Destructive signal** | +30 | User says "delete", "remove", "nuke" |
| **File name match** | +50 | User mentions specific file being deleted |
| **Approval signal** | +20 | User says "yes", "proceed", "do it" |
| **Context signal** | +10 | User says "as I asked", "obviously" |

**Score cap:** 100% (can't exceed maximum)

### Block vs Prompt vs Allow

```
Confidence < block_threshold (40%)
  → BLOCK operation
  → User sees: "Cannot verify user authorization for destructive operation"

Confidence in [40%, 70%)
  → PROMPT user
  → User sees: "Destructive operation detected. Please confirm."

Confidence >= prompt_threshold (70%)
  → ALLOW operation
  → No interruption
```

## Tuning for Your Workflow

### Conservative (More Blocking, Safer)

Use if you want maximum safety and don't mind frequent prompts:

```toml
[intent_validation]
enabled = true
block_threshold = 50    # Higher threshold
prompt_threshold = 80   # More prompting
message_count = 3       # Search fewer messages (older intent expires faster)
```

**Effect:**
- More operations will prompt for confirmation
- Requires stronger evidence before allowing destructive operations
- Safer but more interruptions

### Aggressive (Less Blocking, Faster)

Use if you trust your intent naming and want fewer interruptions:

```toml
[intent_validation]
enabled = true
block_threshold = 30    # Lower threshold
prompt_threshold = 60   # Less prompting
message_count = 10      # Search more messages
```

**Effect:**
- Fewer prompts and interruptions
- Allows operations with weaker evidence
- Faster but less safe

### Balanced (Default)

The recommended middle ground:

```toml
[intent_validation]
enabled = true
block_threshold = 40
prompt_threshold = 70
message_count = 5
```

## Signal Keywords

Edit the signal lists to match your language and workflow:

```toml
[destructive_signals]
# User explicitly wants to destroy something
explicit = [
    "delete", "remove", "erase", "overwrite", "wipe", "clear",
    "destroy", "nuke", "start over", "begin from scratch",
    "clean up", "cleanup", "discard", "throw away", "tear down",
    "reset", "revert", "rollback",
]

# User confirms after being warned
approval = [
    "yes", "proceed", "confirmed", "go ahead", "do it",
    "approve", "understood", "fine", "ok", "okay", "alright", "right",
    "correct", "confirmed",
]

# User implies intent from context
context = [
    "i asked you to", "remember when", "as i said",
    "of course", "obviously", "naturally",
]

# User cancels prior request (OVERRIDES approval)
negative = [
    "cancel", "stop", "abort", "don't", "no", "wait",
    "never mind", "actually", "hold on", "scratch that",
]
```

**Matching:** All keywords are lowercase. Content is lowercased before matching, so case doesn't matter.

### Adding Your Own Signals

If you use custom phrases for destructive actions:

```toml
[destructive_signals.explicit]
# Add project-specific signals
"obliterate", "annihilate", "purge", "strip"
```

## Auto-Backup Configuration

```toml
[auto_backup]
enabled = true                    # Disable if too noisy
commit_message_prefix = "auto-backup"
```

### When to Disable Auto-Backup

Disable if:
- Too many commits cluttering history
- You prefer manual git practices
- Working in a repo where auto-commits are problematic

**Note:** Recovery is still possible via `git reflog` even when disabled.

## Environment Variable Overrides

For one-off changes without editing config:

```bash
# Disable intent validation for this session
export INTENT_VALIDATION_ENABLED="false"

# Increase block threshold
export INTENT_VALIDATION_BLOCK_THRESHOLD="50"

# Enable debug logging
export INTENT_VALIDATION_DEBUG_MODE="true"
```

## Operation Severity Levels

### Critical (Requires 70% confidence)

Operations that are difficult or impossible to recover:

- `rm -rf` - Recursive force delete
- `git reset --hard` - Hard reset (loses uncommitted work)
- `git clean -fdx` - Remove all untracked files
- `git push --force` - Rewrite remote history
- `DROP DATABASE` - Destroy entire database
- `TRUNCATE` - Wipe all table data

### High (Requires 40-70% confidence)

Destructive but potentially recoverable:

- `rm` - Delete files
- `git reset` - Reset to previous commit
- `> file` - Truncate file with redirect
- `DELETE FROM` - SQL delete (all rows)

### Medium (Requires 40% confidence)

Operations that might destroy data:

- `>> file` - Append (could overwrite if redirected)
- `sed` - Stream editor (can delete lines)

## Debugging

### Enable Debug Mode

```toml
[intent_validation]
debug_mode = true
```

Or via environment:

```bash
export INTENT_VALIDATION_DEBUG_MODE="true"
```

### What Debug Shows

When enabled, you'll see in stderr:

```
[intent_validation] Operation detected: Bash (severity: critical)
[intent_validation] Found 5 user messages
[intent_validation] Confidence: 85% - File 'temp.txt' mentioned with destructive signal 'delete'
[intent_validation] Decision: allow
```

### Troubleshooting Blocked Operations

If an operation is blocked unexpectedly:

1. **Check debug output** - What confidence was calculated?
2. **Review your recent messages** - Was intent actually expressed?
3. **Check signal keywords** - Do your phrases match the config?
4. **Consider thresholds** - Are thresholds too conservative?

Example:

```
[intent_validation] Confidence: 30% - No explicit intent signals found
[intent_validation] Decision: deny
```

**Solution:** Add explicit intent: "Yes, delete the temp files"

## Performance

| Factor | Impact | Typical Values |
|--------|--------|---------------|
| Transcript parsing | ~10-30ms | 1000 JSONL lines |
| Confidence calculation | ~1ms | Keyword matching |
| Git commit (backup) | ~100-300ms | Depends on repo size |
| **Total latency** | **~50-150ms** | **Per operation** |

### Optimization Tips

If latency is noticeable:

1. **Reduce message count:**
   ```toml
   message_count = 3  # Instead of 5
   ```

2. **Disable debug mode:**
   ```toml
   debug_mode = false
   ```

3. **Check git performance:**
   ```bash
   # Auto-backup might be slow if git is slow
   time git status  # Test git speed
   ```

## Per-Operation Configuration

**Phase 1 limitation:** All operations share the same thresholds.

**Phase 2 will support:**
- Different thresholds per operation type
- File-specific rules
- Directory-based exceptions

## Resetting to Defaults

If you've made changes and want to revert:

### Option 1: Delete settings.toml

```bash
rm P:\.claude\settings.toml
```

Hooks will use hardcoded defaults.

### Option 2: Override section

```toml
[intent_validation]
enabled = false  # Disable entirely
```

### Option 3: Restore defaults

```toml
[intent_validation]
# Restore default values
block_threshold = 40
prompt_threshold = 70
message_count = 5
debug_mode = false
```

## Multi-Instance Considerations

If running multiple Claude Code instances (terminals/worktrees):

1. **Shared config:** All instances read the same `settings.toml`
2. **Independent transcripts:** Each instance has its own session file
3. **Concurrent backups:** Each creates its own git commits (safe)

**Conflict resolution:** Git handles concurrent commits automatically. No special handling needed.

## FAQ

**Q: How do I disable intent validation?**
A: Set `enabled = false` in `[intent_validation]` section.

**Q: Can I have different thresholds for different operations?**
A: Not in Phase 1. Phase 2 will support per-operation config.

**Q: What if auto-backup is too noisy?**
A: Set `[auto_backup] enabled = false`. Recovery is still possible via git reflog.

**Q: How do I reset to defaults?**
A: Delete `P:\.claude\settings.toml` or set `enabled = false`.

**Q: Can multiple users have different configurations?**
A: Yes - commit `.toml` to repo for shared settings, each user can override with environment variables.

**Q: What's the difference between block and prompt?**
A: Block = operation fails, you must change your approach. Prompt = operation waits for your confirmation.

**Q: How do I know which signals matched?**
A: Enable debug_mode to see which signals were found and why.
