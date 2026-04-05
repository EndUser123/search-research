# Statusline System

Real-time status display for Claude Code terminal sessions.

## Overview

| Component | Path | Lines |
|-----------|------|-------|
| Statusline | `P:/.claude/statusline.py` | 222 |
| Statusline (PS) | `P:/.claude/statusline.ps1` | 323 |
| Notification Queue | `P:/.claude/hooks/notification_queue.py` | 168 |
| BUC Command | `P:/.claude/skills/buc.py` | 22 |

The statusline is an external process that:
1. Reads JSON from stdin (session context from Claude Code)
2. Queries git, notifications, and system state
3. Outputs a single-line status string

## Display Format

```
[🔔] | 🤖 Opus 4.5 📂 dirname | 🌿 branch 💾 3 | 🟢 150k/200k | ⌛ 4:23 15:31
[🔔] | 🤖 Opus 4.5 📂 worktrees | 🌳 experiment-xyz [wt] 💾 2 | 🟢 150k/200k | ⌛ 4:23 15:31
```

| Component | Format | Description |
|-----------|--------|-------------|
| Notifications | 🔔 | Prefix shown when notifications exist |
| Settings Drift | ⚙️ | Settings.json modified after session started |
| Model | 🤖 {name} | Opus 4.5, Sonnet, Haiku (GLM variant for z.ai) |
| Directory | 📂 {name} | Current folder, or P:/C: for drive roots |
| Git | 🌿 branch 🌳 branch [wt] 💾 N | 🌿=main worktree, 🌳=git worktree, [wt]=worktree mode, 💾=dirty count |
| Context | 🟢🟡🟠🔴🔥 Nk/Mk | Token remaining (emoji based on amount) |
| Rate Limit | ⌛ H:MM | z.ai 5-hour window remaining |
| Session Start | H:MM or M/d H:MM | Time when CC session started |

### Token Context Indicators

| Emoji | Remaining | Status |
|-------|-----------|--------|
| 🟢 | ≥150k | Plenty |
| 🟡 | ≥100k | OK |
| 🟠 | ≥50k | Low |
| 🔴 | <50k | Critical |
| 🔥 | Very low | Emergency |

### Settings Drift Indicator

The ⚙️ appears when `.claude/settings.json` has been modified **after the current terminal started**.

**How it works:**
- Each terminal stores its startup timestamp in `%TEMP%\cc_settings_mtime_<terminal_id>.txt`
- The SessionStart hook writes this file using `CLAUDE_TERMINAL_ID` for per-terminal tracking
- On each refresh, the statusline compares settings.json mtime to the terminal's start timestamp
- If settings mtime > terminal start time, ⚙️ is displayed

**Per-terminal behavior:**
- Terminal A restarts → Only Terminal A's gear clears (Terminal B keeps its gear if settings were modified during its session)
- Each terminal has independent tracking via `CLAUDE_TERMINAL_ID` or `WT_SESSION_ID`

**Common causes:**
- Another terminal modified settings
- Manual edits to settings.json
- Config changed via UI/external tool

**To clear a stuck indicator:**
```powershell
# Delete this terminal's tracker (replaces with current timestamp on next refresh)
Remove-Item "$env:TEMP\cc_settings_mtime_<terminal_id>.txt" -Force

# Or delete all trackers (forces all terminals to re-initialize)
Remove-Item "$env:TEMP\cc_settings_mtime_*" -Force
```

### Session Start Time Display

The session start time appears at the end of the statusline (e.g., `15:31` or `1/9 15:31`).

**How it works:**
- `SessionStart_capture_settings.py` hook runs when CC starts
- Writes current Unix timestamp to `%TEMP%\cc_session_start.txt` (shared file)
- Statusline reads this file and formats the time
- **Today**: Shows `H:MM` format (e.g., `15:31`)
- **Different day**: Shows `M/d H:MM` format (e.g., `1/9 15:31`)

**Why a shared file?** The SessionStart hook runs in CC's Python process with one PID, but the statusline runs in a PowerShell subprocess with a different PID. Per-terminal PID-based files wouldn't match between the two processes. The shared `cc_session_start.txt` file bridges this gap.

**Files involved:**
- Hook: `P:/.claude/hooks/SessionStart_capture_settings.py`
- Statusline function: `P:/.claude/statusline.ps1` (Get-SessionStartTime)
- Registered in: `P:/.claude/settings.json` under `hooks.SessionStart` array

## Notification System

### Queue File
`~/.claude/notifications.json`

### Notification Schema

```json
{
  "type": "duf|commit|lesson|warning|info|doc_staleness|brainstorm",
  "message": "Display text",
  "timestamp": "2025-01-04T12:34:56Z",
  "source": "commit_reminder|retrospective|session_end|auto_learn|poka_yoke|doc_staleness",
  "priority": 0|1|2,
  "session_id": "uuid-or-terminal-id"
}
```

| Field | Values | Notes |
|-------|--------|-------|
| `type` | `duf`, `brainstorm`, `warning`, `doc_staleness`, `commit`, `info` | Maps to emoji in statusline |
| `priority` | `0`=low, `1`=normal, `2`=high | Sort order (desc) |
| `session_id` | UUID, `terminal_id`, or `""` | Empty = global (all terminals) |

### Notification Types Reference

| Emoji | Type | Source | Trigger | Command |
|-------|------|--------|---------|---------|
| 🔔 | `duf` | `session_end` | Session ends **with uncommitted git changes** | `/r` to clear |
| 💡 | `brainstorm` | `session_end` | Session ends **with uncommitted git changes** | `/brainstorm` to clear |
| 📚 | `doc_staleness` | `doc_staleness` | Project docs outdated | Update docs |
| 🚨 | `warning` | `poka_yoke` | Edit failure or loop detected | `/r` to clear |
| ⚙️ | (n/a) | Settings drift | settings.json modified | Refresh session |

**Priority Behavior:**

- **Poka-yoke (🚨) takes over statusline**: When a `warning`/`poka_yoke` notification exists, it REPLACES the entire statusline with the alarm message. This is intentional - edit failures and loop detection are critical issues that require immediate attention. All other emojis are hidden until the poka-yoke is cleared.
- **Other notifications**: When no poka-yoke is active, duf (🔔), brainstorm (💡), and doc_staleness (📚) emojis are shown together in the prefix.

**Details:**

- **DUF (🔔)**: "Did You Forget?" - shown when session ends **with uncommitted git changes**, prompts user to review what might have been missed. If you commit before closing CC, no DUF emoji appears (clean state = no reminder needed).
- **Brainstorm (💡)**: Session ended with uncommitted changes, prompts user to run `/brainstorm` for opportunity analysis. Same git requirement as DUF.
- **Edit Failure (🚨)**: Triggered when Edit/Write fails ("String to replace not found"). Message includes "Run: /r"
- **Loop Detection (🚨)**: Same file edited 3+ times in 3 minutes. STOP and run `/r`
- **Doc Staleness (📚)**: Triggered on completion keywords ("done", "complete", "finished") when docs haven't been updated recently

### API

```python
from notification_queue import add_notification, clear_by_type

# Add a notification
add_notification(
    notification_type="commit",
    message="🤔 BEFORE YOU COMMIT - Did we test?",
    source="commit_reminder",
    priority=1,
    session_id=""  # Empty = global
)

# Clear by type (and optionally source)
cleared = clear_by_type("commit", source="commit_reminder")
```

## Troubleshooting

### Notifications Not Appearing

If emoji notifications don't appear in the statusline after session end:

1. **Check git status:**
   ```bash
   # DUF and brainstorm only appear if there are uncommitted changes
   git status --porcelain
   ```
   If output is empty, this is **expected behavior** - no notifications are added when git is clean.

2. **Check notification file:**
   ```bash
   # View all notifications with sources
   cat ~/.claude/notifications.json
   ```

3. **Enable debug logging:**
   ```bash
   # Run Stop_router with debug output
   ROUTER_DEBUG=1 echo '{}' | python P:/.claude/hooks/Stop_router.py
   ```

4. **Common issues:**
   - Git is clean (no uncommitted changes): DUF/brainstorm won't trigger - this is intentional
   - `Stop_router.py` not executing: Check `settings.json` hooks configuration
   - Import path error: Notification module may have moved or has syntax errors
   - Finally block skipped: Process killed with `os._exit()` instead of `sys.exit()`

## Session Filtering

The statusline filters notifications by `session_id`:

```python
notifications = [
    n for n in all_notifications
    if n.get("session_id", "") == ""  # Global
    or n.get("session_id", "") == current_session_id  # This session
]
```

- **Global notifications** (`session_id = ""`): Show in all terminals
- **Session notifications**: Show only in the terminal that created them

## Fleet Monitoring

Lock-free multi-terminal awareness using file-per-process strategy.

### Fleet Directory
`%TEMP%\cc_fleet\`

### Heartbeat Schema

Each terminal writes to its own PID file:
```
%TEMP%\cc_fleet\pid_12345.json
```

```json
{
  "pid": 12345,
  "session_id": "uuid-or-empty",
  "model": "Opus 4.5",
  "directory": "project-name",
  "branch": "main",
  "status": "active|error",
  "last_seen": 1735954496
}
```

| Field | Description |
|-------|-------------|
| `pid` | Process ID (used for filename) |
| `last_seen` | Unix timestamp - updated each statusline refresh |
| `status` | `"active"` or `"error"` (future: detect crashed sessions) |

### TTL and Cleanup

- **HEARTBEAT_TTL**: 30 seconds
- Terminals with `last_seen` older than TTL are considered dead
- Stale files are automatically removed on read

### Display Format

| Component | Format | Description |
|-----------|--------|-------------|
| Fleet count | 👥 N | Number of active terminals (only shown if N > 1) |
| Errors | 🆘 N | Number of terminals in error state |

**Example output:**
```
👥3 │ 🔔 │ 🤖 Opus 4.5 📂 project │ 🌿 main 💾 2
```

### Architecture Benefits

| Pattern | Benefit |
|---------|---------|
| File-per-process | No locks needed - each terminal writes to its own file |
| Read-all strategy | Simple O(N) scan of directory |
| TTL-based cleanup | No coordination for cleanup - stale files expire naturally |
| Prefix display | Global fleet info on left, local status on right |

## Integration Points

| Component | Path | Purpose |
|-----------|------|---------|
| Commit Reminder | `hooks/UserPromptSubmit_commit_reminder.py` | Adds 🔔 before commits |
| Poka-Yoke | `hooks/poka-yoke.py` | Adds 🔔 on edit failure/loop |
| Doc Staleness | `hooks/UserPromptSubmit_doc_staleness.py` | Adds 📚 when docs outdated |
| Retro | `hooks/UserPromptSubmit_retrospective.py` | Extracts lessons and ingests to CKS |
| Clear Command | `commands/buc.py` | User-initiated `/buc` clears commit notifications |
| Statusline | `statusline.py` / `statusline.ps1` | Displays all components |

### `/buc` Command

Broad Aware Check - clears commit reminders after user confirms they checked.

```bash
/buc
# Output: ✓ Cleared 1 'commit' notification(s)
```

## Standards

### Error Handling
- **Silent failure**: Never crash the statusline
- All file operations wrapped in try/except
- Git commands have 2-second timeout

### Performance
- Git commands run in parallel where possible
- Subprocess uses `CREATE_NO_WINDOW` on Windows (no popup)
- Caches expensive operations (rate limit window)

### Sorting
- Notifications: Priority (desc) → Timestamp (asc)
- Oldest high-priority notification shows first

### Debug Output
Statusline writes debug files for troubleshooting:
- `~/.claude/model_debug.json` - Model data from last update
- `~/.claude/context_debug.json` - Full context from last update

## PowerShell Implementation

**File**: `P:/.claude/statusline.ps1`

Alternative to `statusline.py` with:
- Same input format (JSON via stdin)
- Same output format
- Same notification queue integration
- **Benefit**: Less flicker on Windows

### Requirements
- **PowerShell 7+**: Uses `pwsh.exe` (not `powershell.exe` which is 5.1)
- Requires UTF-8 console encoding

### Configuration
Configure Claude Code settings to use:
```
statusline: pwsh -File "P:/.claude/statusline.ps1"
```

Both implementations are functionally identical and interchangeable.
