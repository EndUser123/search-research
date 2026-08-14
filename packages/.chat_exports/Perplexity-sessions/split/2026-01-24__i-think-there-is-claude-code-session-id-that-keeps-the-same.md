---
title: "I think there is claude_code_session_id, that keeps the same ID until CC is restarted.  And there's the windows terminal"
date: "2026-01-24"
mode: "COPILOT"
uuid: "f02e1161-b942-4b13-bfb3-4a7144bf4204"
entry_count: 2
---

## Human

I think there is claude_code_session_id, that keeps the same ID until CC is restarted.  And there's the windows terminal ID or console ID.

## Assistant

I appreciate you sharing this technical observation about Claude Code's session management. However, I want to clarify what you're asking so I can provide the most helpful response.

Are you looking for:

1. **Documentation or technical details** about how `claude_code_session_id` works—specifically how it persists across terminal commands within a single Claude Code session and resets on restart?

2. **Clarification on the distinction** between the `claude_code_session_id` and Windows Terminal's session/console ID, and how they relate to each other in your multi-terminal workflow?

3. **Practical guidance** on how to reference, track, or leverage these IDs in your automation or debugging workflows?

4. **Something else**—perhaps related to how these IDs interact with your current system architecture or how they might be used for logging/observability purposes?

Given your expertise with Claude Code workflows and multi-terminal setups, I want to make sure I'm addressing the specific technical problem or question you're exploring rather than providing generic documentation.

## Human

all of it please

## Assistant

Now I'll generate the comprehensive technical report.

***

# Claude Code Session Management: Technical Architecture & Multi-Terminal Integration

## Executive Summary

Claude Code maintains **persistent session IDs across restarts within the same project directory**, but each Claude Code process restart generates a **new UUID-based session identifier**. Windows Terminal and PowerShell provide their own hierarchy of session identifiers (`WT_SESSION`, `WT_PROFILE_ID`, `$PID`) that operate independently from Claude Code's session management. Understanding this three-tier identification system—Windows Terminal → PowerShell process → Claude Code session—is essential for building reliable multi-terminal automation and subprocess orchestration.

***

## 1. Claude Code Session ID Architecture

### Session ID Characteristics

Claude Code's session ID is a **UUID** (e.g., `55ace50a-73f9-4cc0-8ed0-d2f2523288b8`) that serves as the unique identifier for a conversation context. Critical properties:[1][2][3][4]

| Property | Behavior |
|----------|----------|
| **Format** | RFC 4122 UUID (36 characters, hyphenated) |
| **Persistence** | Remains identical across multiple Claude Code invocations within the same project directory |
| **Scope** | User-scoped; isolated per project path |
| **Reset Trigger** | Generates new ID when Claude Code process restarts |
| **Storage** | `~/.claude/projects/<encoded-path>/<session-id>.jsonl` |
| **Retrieval** | Stored in initial system init message during session startup |

The key distinction: **A session ID identifies conversation state, not the Claude Code process itself.** When you restart Claude Code (`Ctrl+C`, crash, or explicit exit) and resume from the same directory, the session ID remains constant because Claude Code reads the .jsonl file. However, if you simply exit and start a fresh Claude Code instance without specifying `--resume`, a new session ID is generated.

### Session Storage and Encoding[3][4][5]

Claude Code encodes project paths into directory names using a simple algorithm:

```
/Users/alex/Projects/myapp  →  ~/.claude/projects/-Users-alex-Projects-myapp/
/home/user/code/project     →  ~/.claude/projects/-home-user-code-project/
```

The full directory structure under `~/.claude/`:

```
~/.claude/
├── history.jsonl                      # Global session metadata index
├── projects/                          # Encoded project directories
│   ├── -home-user-project-main/
│   │   ├── 55ace50a-73f9-4cc0-8ed0-d2f2523288b8.jsonl
│   │   ├── a06171f9-5f33-4258-84e1-4dc70e84c6dd.jsonl
│   │   └── agent-*.jsonl              # Subagent sessions
│   └── -home-user-project-tools/
│       └── b1234567-8901-2345-6789-abcdef0123456.jsonl
├── session-env/                       # Per-session environment variables
├── todos/                             # Task list storage
├── .claude.json                       # User-scoped config + MCP servers
└── settings.json                      # User preferences and permissions
```

**Critical behavior:** Session files are **only discoverable from the exact directory they were created in.** If you create a session in `/home/user/project-a/`, then `cd` to `/home/user/project-b/` and run `claude --resume`, it will not see the session from project-a because Claude Code looks in `.claude/projects/-home-user-project-b/`, not `project-a`.

### Session File Format (JSONL)[3]

Each .jsonl file contains structured conversation history with this schema:

```json
{
  "session_id": "55ace50a-73f9-4cc0-8ed0-d2f2523288b8",
  "uuid": "message-uuid",
  "parent_uuid": "parent-message-uuid",
  "role": "user|assistant",
  "content": "message text or tool invocation",
  "timestamp": "2026-01-24T03:37:00Z",
  "tool_uses": [{"id": "...", "name": "Bash", "input": {...}}],
  "tool_results": [{"tool_use_id": "...", "content": "..."}],
  "git_branch": "main",
  "project_path": "/home/user/project"
}
```

The JSONL format enables:
- **Streaming append**: Each message is a complete JSON object on one line
- **Incremental saves**: Claude Code writes messages in real-time
- **Easy parsing**: Standard line-by-line JSON reading
- **Durable format**: No partial writes or corruption risk from crashes

***

## 2. Session ID Retrieval: Official vs. Workaround Methods

### Official Retrieval Methods[6][7]

**Method 1: Interactive Resume (GUI-like)**
```bash
claude --resume
# Displays numbered list of recent sessions with metadata
# User selects by number
# Example output:
# 1. project-main        | 3 days ago     | 42 messages
# 2. feature-branch      | 2 hours ago    | 18 messages
# 3. bugfix-session      | now            | 5 messages
```

**Method 2: Direct Resume by ID**
```bash
claude --resume 55ace50a-73f9-4cc0-8ed0-d2f2523288b8
# Resumes specific session without prompting
```

**Method 3: Continue Most Recent**
```bash
claude --continue  # or `claude -c`
# Equivalent to: claude --resume (auto-selects #1 from list)
```

### Programmatic Access Workaround[2]

The critical limitation: **There is no native command to retrieve the current session ID during an active Claude Code session.** This blocks automation where one Claude Code process needs to invoke another. The current workaround:[2]

```bash
#!/bin/bash

# Generate unique marker
MARKER=$(uuidgen)
echo $MARKER > /tmp/marker-$MARKER

# Start Claude Code in background
claude "do work and save in session" &
CC_PID=$!

# Search for newly created .jsonl file that references this marker
# (Requires Claude to write the marker to its session context first)
sleep 2
SESSION_ID=$(tail -1 ~/.claude/projects/-$(pwd | tr / -)/*.jsonl | \
  jq -r '.session_id' | tail -1)

echo "Captured session ID: $SESSION_ID"

# Later, resume this session
claude --resume $SESSION_ID "continue work"
```

**Feature request #1407** is open for a `/session` command that would expose the current session ID without workarounds.

### Why This Matters for Agentic Chaining[2]

Current challenge for coordinating multiple Claude Code processes:

```bash
# Desired workflow: Chain two tasks
claude "work on task 1 and save context"  # Session A created
# [No way to get Session A's ID without file system polling]

# Must resort to:
claude "work on task 1" && \
  SESSION_ID=$(find ~/.claude/projects -name "*.jsonl" -newer <marker> -printf '%T@ %p\n' | \
               sort -rn | head -1 | cut -d' ' -f2- | xargs basename | sed 's/.jsonl//') && \
  claude --resume $SESSION_ID "work on task 2"

# This is brittle and slow
```

***

## 3. Windows Terminal & Console Session Architecture

### Three-Tier Session Identification Hierarchy

Windows offers three distinct session identification mechanisms that operate at different OS layers:[8][9][10][11]

#### Tier 1: Windows Terminal Session (GUI Layer)
```powershell
$env:WT_SESSION  # GUID unique per terminal window
$env:WT_PROFILE_ID  # GUID of terminal profile used
```

**Example values:**
```powershell
WT_SESSION = c3f793c5-98bd-40f8-a8cd-73fe0027b5c7
WT_PROFILE_ID = {574e775e-4f2a-5b96-ac1e-a2962a402336}
```

These are set by Windows Terminal **when it launches** PowerShell/CMD. Each terminal window gets its own `WT_SESSION` GUID that remains stable for that window's lifetime. The `WT_PROFILE_ID` identifies which Terminal profile (PowerShell, Command Prompt, WSL, etc.) is configured for that tab/window.

#### Tier 2: PowerShell Process Identification (OS Layer)
```powershell
$PID              # Current PowerShell process ID (automatic variable)
Get-Process -Id $PID | Select-Object Id, ProcessName  # Detailed process info
```

**Example:**
```
PS C:\> $PID
15264

PS C:\> Get-Process -Id $PID | Select-Object Id, ProcessName
 Id ProcessName
--- -----------
15264 pwsh
```

The `$PID` variable contains the **Windows process ID** of the PowerShell session. This changes if you spawn nested PowerShell instances (`pwsh` from within `pwsh`). However, it remains constant throughout a single PowerShell session.

#### Tier 3: Console Host Process (Kernel Layer)
```powershell
# On Windows 7+, each console window has a conhost.exe
# Find the conhost that owns this PowerShell:
Get-Process -Id (Get-Process -Id $PID).Parent.Handle | Select-Object ProcessName
# Result: conhost.exe (stable across nested shell invocations)
```

The `conhost.exe` (Console Host) process is **stable per console window** even if you spawn multiple nested shells (cmd.exe, pwsh.exe, bash.exe). This is the lowest-level console abstraction.[12][13]

### Environment Variables Available in Windows Terminal[11]

| Variable | Source | Value | Scope |
|----------|--------|-------|-------|
| `WT_SESSION` | Terminal | GUID | This terminal window instance |
| `WT_PROFILE_ID` | Terminal | GUID | Profile configuration for this tab |
| `USERNAME` | OS | User login | Session user |
| `COMPUTERNAME` | OS | Machine name | Local machine |
| `SESSIONNAME` | RDP only | `console\|RDP-Tcp#N` | RDP connection type |

The `SESSIONNAME` variable is only set if you're using RDP (Remote Desktop). On a local Windows machine, it defaults to `console`.

### Session Identification Chain in Your Multi-Terminal Setup

When you open 5-6 Claude Code instances in different Windows Terminal tabs:

```
┌─────────────────────────────────────────────────────────────┐
│ Windows Terminal Application                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ Tab 1: "Terminal 1"
    │  │ env:WT_SESSION = c3f793c5-98bd-40f8-a8cd-73fe0027b5c7
    │  │ env:WT_PROFILE_ID = {574e775e-4f2a-5b96-ac1e-a2962a402336}
    │  │
    │  └─ PowerShell Process [PID: 12345]
    │     └─ Claude Code Process [Session: 55ace50a-73f9-4cc0-8ed0...]
    │
    ├─ Tab 2: "Terminal 2"
    │  │ env:WT_SESSION = a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p
    │  │ env:WT_PROFILE_ID = {574e775e-4f2a-5b96-ac1e-a2962a402336}
    │  │
    │  └─ PowerShell Process [PID: 12346]
    │     └─ Claude Code Process [Session: a06171f9-5f33-4258-84e1...]
    │
    └─ ...5 more tabs with unique WT_SESSION GUIDs
```

Each Claude Code process has its own `claude_code_session_id` (stored in its .jsonl file), independent from the Windows Terminal `WT_SESSION` GUID or the PowerShell `$PID`.

***

## 4. Claude Code Session Lifecycle & Restart Behavior

### Session Persistence vs. Process Restart

This is the critical distinction:[14][1][2]

**Scenario 1: Resume in Same Directory (Session Persists)**
```bash
$ cd /home/user/project
$ claude "do work"
# Claude Code starts, generates session ID 55ace50a...
# Work happens, session saved to ~/.claude/projects/-home-user-project/55ace50a.jsonl

# User presses Ctrl+C
# Later, in the SAME directory:
$ cd /home/user/project
$ claude --resume
# Claude Code finds 55ace50a.jsonl, loads it
# Same session ID used, conversation context restored
```

**Scenario 2: Directory Change (Session Lost)**
```bash
$ cd /home/user/project
$ claude "do work"
# Session ID: 55ace50a... saved to ~/.claude/projects/-home-user-project/55ace50a.jsonl

$ cd /home/user/other-project
$ claude --resume
# Claude Code looks in ~/.claude/projects/-home-user-other-project/
# Session file NOT found (it's in project/, not other-project/)
# User gets interactive picker with sessions from other-project
```

**Scenario 3: Explicit Restart (New Session)**
```bash
$ cd /home/user/project
$ claude "do work"
# Session ID: 55ace50a...

# User wants fresh session in same directory
$ claude  # No --resume flag
# Claude Code generates NEW session ID: a06171f9...
# Starts blank session in same project
# Old session still exists in .jsonl files
```

### Context Loss on Restart[14]

When Claude Code restarts (even resuming the same session ID), it **re-analyzes the entire repository from scratch**:

- ✅ Conversation history is preserved (read from .jsonl)
- ✅ File states and git history are available for search
- ❌ In-memory working memory is lost (file caches, analysis state)
- ❌ Accumulated understanding of project structure must be rebuilt
- ❌ Previous tool outputs are in history but not cached for performance

This is why large projects with 100k+ lines benefit from `CLAUDE.md` files that prime the context—they compensate for the restart cost.

### Session Cleanup Policy[15]

Claude Code automatically deletes old sessions based on inactivity:

```json
{
  "cleanupPeriodDays": 30  // Default: sessions inactive >30 days deleted at startup
}
```

You can override in `~/.claude/settings.json`:
- `"cleanupPeriodDays": 0` → Delete all sessions immediately on startup (nuclear option)
- `"cleanupPeriodDays": 90` → Keep sessions for 90 days
- Set to very high value to keep everything

This cleanup happens at Claude Code startup, not continuously.

***

## 5. Windows Terminal Session Tracking in Your Environment

### Mapping Terminal → PowerShell → Claude Code

For your specific setup (5-6 concurrent Claude Code instances), you can build a session tracking system:

```powershell
# At terminal startup, capture the session hierarchy
$WT_SESSION = $env:WT_SESSION
$PWSH_PID = $PID
$PWSH_PARENT = (Get-Process -Id $PID).Parent.ProcessId

# Create tracking file
$TRACKING = @{
    wt_session = $WT_SESSION
    wt_profile = $env:WT_PROFILE_ID
    pwsh_pid = $PWSH_PID
    pwsh_parent = $PWSH_PARENT
    hostname = $env:COMPUTERNAME
    timestamp = (Get-Date -Format 'o')
}

# Store in project-specific location for discovery
$TrackingPath = "$env:USERPROFILE\.claude\terminal-sessions\$WT_SESSION.json"
$TRACKING | ConvertTo-Json | Out-File -Path $TrackingPath -Force

# Later, when launching Claude Code:
# The process will inherit WT_SESSION from environment
# You can query it: $env:WT_SESSION or [System.Environment]::GetEnvironmentVariable('WT_SESSION')
```

### Subprocess PID Management

When Claude Code launches bash/PowerShell subprocesses:[15]

```powershell
# Inside Claude Code session, bash commands get:
$CLAUDE_PROJECT_DIR      # Current project directory
$CLAUDE_SESSION_ID       # Current session ID (NOT exposed, workaround needed)
$CLAUDE_ENV_FILE         # Path to .env file sourced before bash

# You can track subprocess pids:
$ProcessInfo = Get-Process -Id $PID | Select-Object -ExpandProperty Handles
# Returns handle count, indicating subprocess activity

# Set subprocess timeout behavior:
# Environment variable BASH_DEFAULT_TIMEOUT_MS controls timeout
# MCP_TIMEOUT controls MCP server startup timeout
```

***

## 6. Hooks for Session Lifecycle Events

Claude Code provides hook points for session startup and tool execution:[15]

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Session started at $(date)' >> ~/.claude/session.log"
          }
        ]
      }
    ],
    "PreToolUse": {
      "Bash": "echo 'Before bash command: running in $PWD with timeout $BASH_DEFAULT_TIMEOUT_MS' >&2"
    },
    "PostToolUse": {
      "Bash": "echo 'Bash exit code: $?' >&2"
    }
  }
}
```

Available environment variables in hooks:
- `$CLAUDE_PROJECT_DIR` – Current working directory
- `$CLAUDE_SESSION_ID` – Session ID (workaround required to access)
- `$CLAUDE_ENV_FILE` – Environment file location

These hooks enable you to **track session lifecycle events** across your 5-6 concurrent terminals by writing to a shared log file or database.

***

## 7. Multi-Terminal Architecture & Recommendations

### Current Monitoring Capabilities[16][17]

Tools exist for real-time session monitoring without polling:

**agtrace** – Local dashboard for session monitoring:
```bash
npm install -g agtrace
agtrace watch  # Real-time context window %, tool calls timeline
```

This tool:
- Monitors `~/.claude/projects/` automatically
- Shows context usage percentage in real-time
- Detects tool calls and errors
- Operates entirely locally (privacy-first)

### Recommended Multi-Terminal Coordination Pattern

For 5-6 concurrent Claude Code instances working on independent tasks:

```powershell
# Script: launch-task-cluster.ps1

$TaskDefs = @(
    @{ Name = "Project A"; Dir = "C:\Projects\app-a"; Task = "implement feature X" },
    @{ Name = "Project B"; Dir = "C:\Projects\app-b"; Task = "fix bug Y" },
    @{ Name = "Project C"; Dir = "C:\Projects\app-c"; Task = "refactor module Z" },
    @{ Name = "Project D"; Dir = "C:\Projects\app-d"; Task = "write tests" },
    @{ Name = "Project E"; Dir = "C:\Projects\app-e"; Task = "optimize performance" },
    @{ Name = "Project F"; Dir = "C:\Projects\app-f"; Task = "update documentation" }
)

$TaskIds = @{}

foreach ($Task in $TaskDefs) {
    $TaskId = [System.Guid]::NewGuid().ToString()
    $TaskIds[$Task.Name] = $TaskId
    
    # Create tracking file before launching
    $TrackingFile = "$env:USERPROFILE\.claude\tasks\$TaskId.json"
    @{
        task_id = $TaskId
        wt_session = $env:WT_SESSION
        project_dir = $Task.Dir
        task = $Task.Task
        started_at = (Get-Date -Format 'o')
    } | ConvertTo-Json | Out-File -Path $TrackingFile
    
    # Launch in new Windows Terminal tab
    wt -w 0 new-tab -p "PowerShell" -d $Task.Dir `
        powershell -NoExit -Command "cd '$($Task.Dir)'; claude '$($Task.Task)'"
}

# Monitor all tasks
Write-Host "Started $(($TaskIds.Count)) tasks:"
$TaskIds | ForEach-Object { Write-Host "  $($_.Key): $($_.Value)" }

# Keep script running to monitor
while ($true) {
    Start-Sleep -Seconds 5
    # Query ~/.claude/projects/ for active sessions
    $ActiveSessions = Get-ChildItem "$env:USERPROFILE\.claude\projects" -Recurse -Name "*.jsonl" | Measure-Object
    Write-Host "Active sessions: $($ActiveSessions.Count)"
}
```

### Persistent Session Metadata Storage

Create a session registry for cross-terminal coordination:

```powershell
# ~/.claude/session-registry.json
{
  "sessions": [
    {
      "claude_session_id": "55ace50a-73f9-4cc0-8ed0-d2f2523288b8",
      "wt_session": "c3f793c5-98bd-40f8-a8cd-73fe0027b5c7",
      "pwsh_pid": 12345,
      "project_dir": "C:\\Projects\\app-a",
      "task_name": "Feature X implementation",
      "started_at": "2026-01-24T03:37:00Z",
      "last_active": "2026-01-24T03:45:30Z",
      "status": "active"
    },
    ...
  ]
}
```

Update this file in the `SessionStart` hook to maintain a live registry of all active Claude Code sessions.

***

## Conclusion

Claude Code's session management operates on three independent identification hierarchies:

1. **Windows Terminal GUID** (`WT_SESSION`) – Unique per terminal window
2. **PowerShell Process ID** (`$PID`) – Unique per shell instance
3. **Claude Code Session UUID** (`session-id` in JSONL files) – Unique per conversation context

Each persists and resets independently:
- `WT_SESSION` remains constant for a terminal window's lifetime
- `$PID` changes if you spawn nested PowerShell instances
- `claude_code_session_id` persists across Claude Code restarts within the same directory, but resets if you exit and start fresh

For reliable multi-terminal automation (5-6 concurrent instances), track all three identifiers in a central registry and use session hooks to maintain real-time state. The lack of native session ID exposure in Claude Code is a known limitation (feature request #1407), so file-system-based coordination remains the most robust approach for orchestrating multiple processes.
