# Cognitive Steering Framework (CSF) — Hooks

> **Ground Truth**: This directory implements **structural enforcement hooks** for the Cognitive Steering Framework. These hooks implement deterministic blocking where advisory documentation fails.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Platform Reference: Claude Code Hooks](#platform-reference-claude-code-hooks)
3. [CSF Hooks Catalog](#csf-hooks-catalog)
4. [Configuration](#configuration)
5. [Hook Detection Patterns & TAV Standard](docs/HOOK_DETECTION_PATTERNS.md)
6. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Daemon Architecture](#two-daemon-architecture)
8. [Resources](#resources)

---

## Quick Start

```bash
# Check hook status
python P:\.claude\hooks\shared_utils.py status

# Clear state for new session
python P:\.claude\hooks\shared_utils.py new-session

# View recent logs
python P:\.claude\hooks\shared_utils.py logs --limit 50
```

---

## First Time Setup

If you're setting up a new environment or starting fresh:

```bash
# 1. Initialize competence tracking baseline
python P:\.claude\skills\_tools\competence_health_check.py

# 2. Run full health check to verify system
python P:\.claude\skills\_tools\main_health.py

# 3. Review hook documentation
cat P:\.claude\hooks\CLAUDE.md
```

**Competence Tracking**: The competence layer monitors skill execution and performance. Initialize once to establish baseline (0 checks recorded), then it tracks automatically with `/main` health checks.

---

## Platform Reference: Claude Code Hooks

Claude Code hooks are shell commands that execute at specific points in the AI agent's lifecycle. They provide **deterministic control**—guaranteed behavior, not probabilistic suggestions.

### Hook Events Lifecycle

| Event              | Trigger                   | Capability                                      |
| ------------------ | ------------------------- | ----------------------------------------------- |
| `SessionStart`     | CLI session begins        | Initialize context, restore state               |
| `UserPromptSubmit` | Before prompt processing  | Inject context, validate input, detect concerns |
| `PreToolUse`       | Before tool execution     | **Gate/Block** actions, enforce prerequisites   |
| `PostToolUse`      | After tool completes      | Analyze output, detect failures, auto-format    |
| `Notification`     | System notification       | External alerts (Slack, ntfy, Discord)          |
| `PreCompact`       | Before context compaction | Capture timeline, save critical state           |
| `Stop`             | Agent response complete   | Validate success claims, enforce verification   |
| `SubagentStop`     | Subagent completes        | Evaluate subagent task completion               |
| `SessionEnd`       | CLI session ends          | Cleanup, statistics, logging                    |

### Hook Types

Claude Code supports **five hook handler types**:

| Type | Value | Mechanism | Best For | Default Timeout |
|------|-------|-----------|----------|-----------------|
| **`command`** | `"command"` | Runs shell script/binary, receives JSON via stdin | Deterministic logic, file checks, Git operations | 600s |
| **`http`** | `"http"` | Sends JSON as HTTP POST to URL | External services, webhooks | — |
| **`mcp_tool`** | `"mcp_tool"` | Calls tool on connected MCP server | MCP-integrated scanners | — |
| **`prompt`** | `"prompt"` | LLM evaluates a prompt (single-turn) | Context-heavy judgment, semantic analysis | 30s |
| **`agent`** | `"agent"` | Spawns subagent to verify conditions (experimental) | Multi-step verification | 60s |

**Example `settings.json` configuration:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "matcher": "Write|Edit",
        "command": "python .claude/hooks/investigation_gate.py"
      },
      {
        "type": "prompt",
        "matcher": "Bash",
        "prompt": "Block if this command could delete system files or user data."
      },
      {
        "type": "http",
        "url": "http://localhost:8080/hooks/pre-tool-use",
        "headers": { "Authorization": "Bearer $TOKEN" },
        "allowedEnvVars": ["TOKEN"]
      },
      {
        "type": "mcp_tool",
        "server": "security_server",
        "tool": "scan_file",
        "input": { "path": "${tool_input.file_path}" }
      },
      {
        "type": "agent",
        "prompt": "Verify tests pass before deployment. $ARGUMENTS",
        "model": "sonnet",
        "timeout": 60
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "matcher": "Write",
        "command": "prettier --write $CLAUDE_FILE_PATH"
      }
    ]
  }
}
```

**$ARGUMENTS**: Available in `prompt` and `agent` hooks only — NOT in `command` hooks. Use stdin JSON parsing for command hooks.

**Exit codes**: Exit 0 = success (stdout parsed), Exit 2 = blocking error (stderr fed back), other = non-blocking warning.

**Async hooks**: Use `async: true` for non-blocking background execution, or `asyncRewake: true` to have Claude resume when the hook completes.

**Common fields**: `type` (required), `if` (permission filter), `timeout` (override default), `statusMessage` (spinner text), `once` (run once per session).

### Input/Output Protocol

| Event              | Input (stdin)                                       | Output (stdout)                       |
| ------------------ | --------------------------------------------------- | ------------------------------------- |
| `UserPromptSubmit` | `{"prompt": "..."}`                                 | **Raw text** (injected into context)  |
| `PreToolUse`       | `{"tool_name": "...", "tool_input": {...}}`         | `{"continue": bool, "reason": "..."}` |
| `PostToolUse`      | `{"tool_name": "...", "tool_response": {...}}`      | `{"warning": "..."}` or `{}`          |
| `Stop`             | `{"transcript_path": "...", "conversation": [...]}` | `{"allow": bool, "reason": "..."}`    |

> **See also:** [PROTOCOL.md](file:///P:/.claude/hooks/PROTOCOL.md) for complete I/O specifications.

---

## Unified Semantic Daemon

**Overview:** The Unified Semantic Daemon provides fast semantic search for CKS (Constitutional Knowledge System) and CHS (Chat History Search) via Windows named pipes.

**Location:** `P:\__csf\src\daemons\unified_semantic_daemon.py`

**Hook Integration:** `/search` starts the daemon lazily via `DaemonClient(auto_start=True)` in the unified search router.

### Key Features

| Feature | Description |
|---------|-------------|
| **Named pipe IPC** | `\\.\pipe\csf_nip_semantic` for fast communication |
| **Multi-terminal safe** | Windows Named Mutex (`Global\CSF_NIP_SemanticDaemon_Startup`) prevents race conditions |
| **Zombie daemon cleanup** | Aggressive cleanup kills stale daemons, preserves canonical one |
| **Dynamic pipe names** | Each daemon instance uses unique pipe name to avoid Windows stale handle issues |
| **Auto-start** | Daemon starts lazily on first `/search` |
| **CKS search** | Semantic search across memories, patterns, code, knowledge |
| **CHS search** | Chat history search with async indexing |

### Daemon Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 /search Invocation                           │
│  unified_router.py -> DaemonClient(auto_start=True)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Unified Semantic Daemon                         │
│  P:\__csf\src\daemons\unified_semantic_daemon.py             │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ CKS Backend │  │ CHS Backend │  │ Named Pipe  │         │
│  │ (FAISS)     │  │ (SQLite)    │  │ IPC Server  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    \\.\pipe\csf_nip_semantic
```

### Usage from Hooks

```python
# Example: Hook querying CKS for relevant patterns
from __csf.src.daemons.daemon_client import DaemonClient

client = DaemonClient(auto_start=False)  # Hook doesn't auto-start
results = client.search("cks", "architecture directive", limit=3)

# Returns: {"status": "success", "results": [...], "backend": "cks", ...}
```

### Configuration

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `SEMANTIC_DAEMON_ENABLED` | `true` | Enable/disable auto-start |
| `SEMANTIC_DAEMON_PIPE` | `\\.\pipe\csf_nip_semantic` | Named pipe name |

### Search-Triggered Startup Behavior

1. **Startup check**: `/search` checks daemon availability through discovery/pipe.
2. **Spawn if missing**: Client auto-start launches daemon detached (`pythonw.exe` on Windows).
3. **Discovery handshake**: Daemon publishes discovery metadata.
4. **Multi-terminal reuse**: Other terminals connect to the same daemon via discovery + named pipe.
5. **Fallback**: If daemon fails, search path falls back to direct backend calls.

**Multi-terminal safety**: Multiple terminals can start simultaneously - the mutex ensures only one daemon is spawned, and aggressive cleanup removes any duplicate daemons from previous crashes.

### Troubleshooting

**Symptom**: "Daemon fallback" message on session start

**Cause**: `pywin32` not installed or daemon script missing

**Solution**:
```bash
pip install pywin32
# Verify daemon exists at: P:\__csf\src\daemons\unified_semantic_daemon.py
```

**Symptom**: "Pipe not ready within timeout"

**Cause**: Daemon crashed during startup

**Solution**: Check `P:\__csf\data\semantic_daemon.log` for errors

---

## Two-Daemon Architecture

**Overview:** The two-daemon architecture enables multiple specialized background services to run concurrently without interference.

**Location:** `P:\.claude\hooks\dreaming_daemon.py`, `config/daemon_config.py`

**Documentation:** See `TWO_DAEMON_ARCHITECTURE.md` for complete guide.

### Key Features

| Feature | Description |
|---------|-------------|
| **Type-specific mutexes** | Each daemon type has exclusive Windows named mutex |
| **Separate state files** | PID, state, and log files per daemon type |
| **Concurrent execution** | Dreaming and search daemons run simultaneously |
| **Backward compatible** | Default `--daemon-type` is "dreaming" |
| **Configurable** | Add new daemon types via `DAEMON_TYPES` config |

### Daemon Types

| Daemon | Mutex | Purpose |
|--------|-------|---------|
| **Dreaming** | `Global\ClaudeInsightDaemon` | Analyzes principle-events.jsonl to generate insights |
| **Search** (planned) | `Global\ClaudeSearchDaemon` | Manages search operations and indexing |

### Quick Start

```bash
# Start dreaming daemon (default)
python dreaming-daemon.py

# Start dreaming daemon explicitly
python dreaming-daemon.py --daemon-type dreaming

# Start search daemon (when implemented)
python dreaming-daemon.py --daemon-type search
```

**Auto-start:** The `SessionStart_dreaming_daemon.py` hook automatically starts the dreaming daemon when a Claude Code session begins.

**File Locations:**
- Config: `config/daemon_config.py`
- PID files: `state/{daemon_type}-daemon.pid`
- State files: `state/{daemon_type}-daemon-state.json`
- Log files: `logs/{daemon_type}-daemon.log`

**See Also:** `TWO_DAEMON_ARCHITECTURE.md` for comprehensive documentation, troubleshooting, and implementation details.

---

## Library Code Protection System

**Overview:** API breakage detection for `__lib/` library files using characterization-based validation.

**Location:** `P:\.claude\hooks\__lib\`

**Hook Integration:** `PostToolUse_lib_protection_gate.py` validates edits after completion

### Key Features

| Feature | Description |
|---------|-------------|
| **Pre-edit characterization** | Captures AST signatures, imports, call graphs, SHA256 |
| **Post-edit validation** | Compares signatures for breaking changes |
| **Caller impact analysis** | Uses call graph to identify affected callers |
| **Auto-test generation** | Creates characterization tests from captured data |
| **Terminal isolation** | State scoped per terminal to prevent cross-bleed |

### Protection Architecture

```
Pre-Edit Phase                      Post-Edit Phase
┌─────────────────────┐           ┌─────────────────────┐
│  Characterization    │           │  Validation &        │
│  Capture            │           │  Comparison         │
├─────────────────────┤           ├─────────────────────┤
│ • Function sigs      │   EDIT    │ • Signature diff     │
│ • Class definitions  │ ────────▶ │ • Import removal     │
│ • Import deps        │           │ • Caller mapping     │
│ • Call graph         │           │ • Remediation        │
└─────────────────────┘           └─────────────────────┘
            │                              │
            ▼                              ▼
    ┌───────────────┐              ┌──────────────────┐
    │ State Manager │              │ Allow/Block       │
    │ (.state/ dir) │              │ + Report          │
    └───────────────┘              └──────────────────┘
```

### Breaking Change Types Detected

| Type | Severity | Example |
|------|----------|---------|
| **Function removed** | CRITICAL | Function deleted without deprecation |
| **Signature changed** | CRITICAL | Required parameter added/removed |
| **Import removed** | WARNING | External dependency removed |
| **Method removed** | CRITICAL | Class method deleted |
| **Property removed** | CRITICAL | @property deleted |

### Safe Changes (Not Flagged)

- Adding optional parameters (with defaults)
- Adding new functions/methods
- Adding new classes
- Import additions

### Configuration

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `LIB_PROTECTION_ENABLED` | `false` | Enable lib protection system |
| `LIB_PROTECTION_STRICT` | `false` | Block (true) vs warn-only (false) |

### Usage Example

```bash
# Enable library protection
export LIB_PROTECTION_ENABLED="true"

# Edit a __lib file
# PostToolUse hook automatically:
# 1. Captures pre-edit characterization (first edit)
# 2. Captures post-edit characterization
# 3. Compares for breaking changes
# 4. Warns or blocks if issues found
```

### Block Message Format

```
❌ LIBRARY CODE VALIDATION FAILED

File: P:\.claude\hooks\__lib\session_manager.py

BREAKING CHANGES DETECTED:

1. [CRITICAL] Function Signature Changed
   Function: get_current_session_id()
   Before: () -> str
   After: (terminal_id: str) -> str

   Impact: 2 callers will break
   - P:\.claude\hooks\SessionStart_initializer.py:42
   - P:\.claude\hooks\SessionStart_handoff_restore.py:15

   Fix: Keep original signature, create new function:
   def get_current_session_id() -> str:
       return get_current_session_id_for_terminal(get_terminal_id())

RECOMMENDATION:
Revert changes and follow safe refactoring pattern:
1. Add new function with new signature
2. Update callers incrementally
3. Deprecate old function
4. Remove after all callers migrated
```

### State Storage

```
P:\.claude\hooks\__lib\.state/
├── characterization/
│   ├── session_manager.json       # Pre-edit capture
│   └── task_identity_manager.json
├── call_graphs/
│   └── *.dot files                # GraphViz export
└── test_snapshots/
    └── *.json files                # Behavior snapshots
```

### Module Files

| File | Purpose |
|------|---------|
| `characterization_engine.py` | AST parsing, signature extraction, call graph building |
| `api_breakage_detector.py` | Compare pre/post characterizations, detect breakages |
| `protection_state.py` | Save/load characterizations with terminal isolation |
| `test_generator.py` | Auto-generate characterization tests |
| `PostToolUse_lib_protection_gate.py` | Hook orchestrating validation pipeline |

---

## Handoff System

**Overview:** Session restoration after transcript compaction with SHA256-validated handoffs and terminal-scoped isolation.

**Location:** `P:/packages/handoff/` (Python package)

**Hook Integration:**
- `PreCompact_handoff_capture.py` — Captures handoff before compaction
- `SessionStart_handoff_restore.py` — Restores handoff on session start

### Key Features

| Feature | Description |
|---------|-------------|
| **SHA256 validation** | Prevents handoff corruption |
| **Terminal-scoped** | `{task_name}__{terminal_id}__v{version}.json` |
| **7-day cleanup** | Auto-deletes stale handoffs |
| **45-min timeout** | Releases stuck tasks in `in_progress` |
| **Version tracking** | Rolling version with "latest" alias |
| **Transcript reference** | Links to compacted session for review |

### Handoff Payload

```python
@dataclass
class HandoffPayload:
    task_name: str                    # Task identifier
    task_type: TaskType               # FORMAL, ADHOC_COMMAND, ADHOC_SESSION
    terminal_id: str                  # Terminal isolation
    progress_percent: int             # 0-100
    blocker: str | None               # Current blocker
    next_steps: str                   # What to do next
    command_context: CommandContext   # For ad-hoc commands
    git_branch: str | None            # Current branch
    active_files: list[str]           # Files modified
    transcript_path: str | None       # Reference to compacted session
    handover: dict[str, Any] | None   # HOD handover data
```

### Handoff Architecture

```
PreCompact Hook (before compaction)
├── TaskIdentityManager determines task name
├── Extracts: progress, blocker, next_steps, handover
├── Stores: handoff in task metadata
└── Writes: restore_pending__{terminal_id}.json marker

SessionStart Hook (after compaction)
├── Reads: restore_pending__{terminal_id}.json marker
├── Loads: handoff from task metadata
├── Validates: SHA256 checksum
└── Builds: restoration prompt for user
```

### Storage Structure

```
.claude/
└── state/
    └── restore_pending__{terminal_id}.json         # Recovery marker
```

Note: Handoff data is stored in task tracker metadata, not in a separate checkpoints directory.

### Usage

**Automatic:** Handoffs are captured automatically before compaction and restored on next session start.

### Related Files

| File | Purpose |
|------|---------|
| `packages/handoff/src/handoff/` | Handoff package (core logic) |
| `PreCompact_handoff_capture.py` | Pre-compaction capture hook |
| `SessionStart_handoff_restore.py` | Post-compaction restore hook |

---

## CSF Hooks Catalog

> **Complete Hook Inventory** (from `settings.json` registration)

These hooks address specific failure modes identified from transcript analysis. Organized by event type for quick reference.

### Hook Summary by Event Type

Detailed architectural patterns for these hooks (Regex, TAV, AST, etc.) are documented in [docs/HOOK_DETECTION_PATTERNS.md](docs/HOOK_DETECTION_PATTERNS.md).

| Event | Hook Count | Purpose |
|-------|-----------|---------|
| **SessionStart** | 2 | Initialize context, load decision history |
| **UserPromptSubmit** | 4 | Context injection, skill routing, task detection |
| **PreToolUse** | 15 | Gate/block actions, enforce prerequisites |
| **PostToolUse** | 24 | Analyze output, detect failures, auto-format, TDD-95 |
| **Stop** | 10 | Validate claims, enforce verification |
| **PreCompact** | 1 | Capture checkpoint before compaction |
| **Notification** | 1 | Voice notifications |
| **Total** | **57** | Complete enforcement coverage |

---

### Complete Hook Registry

#### SessionStart Hooks (1 router, 7 sub-hooks)

| Hook | Timeout | Purpose |
|------|---------|---------|
| `SessionStart.py` | 30s | **Main router** - orchestrates setup sequence |
| `SessionStart_terminal_id.py` | 5s | Set CLAUDE_TERMINAL_ID for multi-terminal safety |
| `SessionStart_hook_health_check.py` | 5s | Validate hooked hook files |
| `SessionStart_handoff_restore.py` | 5s | Restore session state after compaction |
| `/search` daemon auto-start (unified router) | n/a | **Lazily starts semantic daemon via `DaemonClient(auto_start=True)`** |
| `SessionStart_task_identity.py` | 2s | Display current task context |
| `SessionStart_timeline.py` | 2s | Show session timeline |
| `SessionStart_constraint_display.py` | 2s | Show active constraints |

**Multi-terminal safety**: SessionStart uses Windows Named Mutex for daemon startup and terminal ID detection to prevent race conditions when multiple Claude Code sessions start simultaneously.

#### UserPromptSubmit Hooks (5)

| Hook | Timeout | Purpose |
|------|---------|---------|
| `UserPromptSubmit.py` | 15s | **Main router** - orchestrates setup sequence |
| `prompt_enhancement.py` | 5s | **Soft-forced-eval** - ambiguity detection, clarification questions |
| `post_compact_reminder.py` | 2s | Remind about post-compaction restoration |
| `UserPromptSubmit_skill_router.py` | 5s | Auto-suggest relevant skills based on patterns |
| `UserPromptSubmit/task_detector.py` | 5s | Detect and track task context |
#### UserPromptSubmit Hooks (6) - Registry Pattern

| Hook | Priority | Timeout | Purpose |
|------|----------|---------|---------|
| `competence_injector.py` | 7.0 | 5s | **Competence Layer** - Inject task-type templates (5-step lifecycle, anti-avoidance, reasoning checklist) |
| `prompt_enhancement.py` | 8.0 | 5s | **Soft-forced-eval** - Ambiguity detection, clarification questions via lightweight heuristics |
| `skill_enforcer.py` | 10.0 | 2s | Gate skill execution (general enforcement) |
| `plan_injector.py` | 10.1 | 3s | Inject planning mode context for architecture tasks |
| `diagnostic_guard.py` | 10.2 | 5s | Detect diagnostic loops and suggest systematic approaches |
| `unified_injector.py` | 11.0 | 3s | **Solo dev context**, goal anchor, falsification injection (latest) |

**Registry**: All hooks registered via `@register_hook()` decorator in `registry.py`. Lower priority = earlier execution.

**Legacy**: `UserPromptSubmit.py` main router orchestrates backward-compatible setup before registry hooks run.

#### PreToolUse Hooks (15)

| Hook | Matcher | Timeout | Purpose |
|------|---------|---------|---------|
| `PreToolUse_hook_protection_gate.py` | Write/Edit/MultiEdit/Update | 5s | Prevent breaking changes to hook files |
| `PreToolUse_file_lock.py` | Write/Edit/MultiEdit/Update | 2s | File locking for concurrent access |
| `PreToolUse_syntax_gate.py` | Write/Edit/MultiEdit | 2s | Validate syntax before edits |
| `PreToolUse_write_router.py` | Write/Edit/MultiEdit | 8s | Route write operations to validators |
| `skill_enforcement_gate.py` | Bash/Glob/Grep/Write/Edit/Task/WebFetch | 2s | Gate skill execution (general) |
| `PreToolUse/PreToolUse_skill_pattern_gate.py` | Bash/Task | 3s | **Skill Enforcement v3.2: Parallel regex + daemon validation** |
| `pretooluse_tdd_gate.py` | Write/Edit/MultiEdit | 3s | Enforce TDD before code edits |
| `PreToolUse_tdd95_gate.py` | Write/Edit/MultiEdit | 3s | **TDD-95 gate - evidence-based TDD enforcement with auto-scaffold** |
| `shell_complexity_gate.py` | Bash | 3s | Block overly complex shell commands |
| `unparseable_command_gate.py` | Bash | 2s | Block `python -c`, `eval()`, injection risks |
| `recursive_failure_detector.py` | Bash | 3s | Detect Catch-22 loops |
| `PreToolUse_bash_router.py` | Bash | 5s | Route bash commands to validators |
| `pre_generation_registry.py` | Read/Glob/Grep/WebFetch | 1s | Pre-generation library-first check |
| `path_resolution_orchestrator.py` | Write/Edit/Bash | 5s | Path protection, block symlink creation |
| `semantic_file_router.py` | Write/Edit/Bash | 2s | Semantic file routing |

#### PostToolUse Hooks (24)

| Hook | Matcher | Timeout | Purpose |
|------|---------|---------|---------|
| `evidence_tracker.py` | * | 3s | Track execution evidence |
| `PostToolUse_file_lock.py` | Write/Edit/MultiEdit/Update | 2s | Release file locks |
| `PostToolUse_code_verification_gate.py` | Write/Edit | 3s | Verify code after edits |
| `PostToolUse_hook_protection_gate.py` | Write/Edit | 5s | Validate hook edits post-completion |
| `PostToolUse_lint_router.py` | Write/Edit | 10s | Auto-format files (ruff, prettier) |
| `PostToolUse_router.py` | * | 8s | In-process router (19 hooks: monitoring, change propagation, outcome validation, error attribution) |
| `repositories/doc_cks_ingester.py` | Write/Edit | 15s | Ingest documentation to CKS |
| `PostToolUse_task_tracker.py` | TaskCreate/Update/List | 3s | Track TaskCreate/Update/List calls |
| `PostToolUse_file_activity_tracker.py` | Read/Edit/Write/Grep/Glob/Bash | 2s | Track file activity patterns |
| `PostToolUse_speculation_detector.py` | Read/Grep/Glob | 2s | Detect speculation without tools |
| `inherited_choice_validator.py` | Read/Grep/Glob | 2s | Detect inherited choice patterns |
| `PostToolUse_write_router.py` | Edit/Write/MultiEdit | 8s | Route writes to verification |
| `PostToolUse_falsification_assessor.py` | Edit/Write/Bash/Read/Grep | 2s | Assess falsification risk |
| `session_change_tracker.py` | Edit/Write | 2s | Track session changes |
| `auto_cks_storage.py` | Edit/Write | 1s | Auto-store to CKS |
| `PostToolUse_tdd_state.py` | Bash/WebFetch/Read/Glob/Write/Edit | 2s | Track TDD state |
| `PostToolUse_tdd95_autoscaffold.py` | Write/Edit/MultiEdit | 5s | **TDD-95 auto-scaffold - automatic test creation** |
| `PostToolUse_tdd95_runner.py` | Bash | 3s | **TDD-95 runner - test result tracking** |
| `PostToolUse_truth_validator.py` | Edit/Write/Bash | 2s | Validate truth claims |
| `strategy_escalation_tracker.py` | Edit/Write/Bash | 2s | Track strategy escalation |
| `PostToolUse_p2_filter_gate.py` | Skill | 3s | **P2 Filter Gate** - Enforce 4-layer filtering for adversarial review findings |
| `PostToolUse_task_router.py` | Task | 5s | Route Task tool operations |
| `skill_enforcement_gate.py` | Skill | 1s | Track skill execution state |
| `skills/v/hooks/PostToolUse_v_init.py` | Skill | 2s | Initialize /v skill tracking |
| `PostToolUse_next_command_suggester.py` | Skill | 3s | Suggest next commands |
| `observable_effect_verifier.py` | Edit/Write | 5s | **Observable Effect Verification (SEV)** - Verify expected side effects from code changes (e.g., logging FileHandler → log files) |

#### Stop Hooks (11)

| Hook | Timeout | Purpose |
|------|---------|---------|
| `verify_claims_transcript.py` | 15s | Verify claims against transcript |
| `Stop_cks_decision_capture.py` | 5s | Capture decisions to CKS |
| `speculation_gate.py` | 3s | **Block error claims without verification** |
| `Stop/contract_validator.py` | 5s | Validate contract compliance |
| `architecture_evidence_gate.py` | 5s | **Block architecture proposals without evidence** |
| `StopHook_cross_validator.py` | 5s | **Enforce empirical verification for "fixed" claims** |
| `StopHook_unverified_stance.py` | 5s | **Detect skeptical language without verification evidence** (anti-sycophancy: "that sounds high", "let me verify" without actual verification) |
| `skill-guard plugin: StopHook_skill_execution_gate.py` | 5s | **Skill Enforcement v3.2: Late violation safety net** (plugin-hosted; local delegator wrapper deleted) |
| `Stop_router.py` | 5s | Route to validation sub-hooks |
| `assumption_audit_v2.py` | 10s | **Audit retrospective claims without evidence (session/terminal-filtered tool evidence)** |
| `auto_commit_hook.py` | 10s | Auto-commit successful changes |

Stop pipeline runtime controls:
- `STOP_BLOCK_DEDUPE_TTL_SECONDS` (default `20`) suppresses repeated identical Stop blocks in rapid loops.
- `EMPIRICAL_OBSERVATION_CACHE_TTL_SECONDS` (default `1800`) keeps turn/session observation memory for path-grounding checks.
- `STOP_POST_BLOCK_GUARD_TTL_SECONDS` (default `1800`) requires a fresh observation tool call after evidence-related Stop blocks before allowing another diagnostic response.
- `ARCHITECTURE_EVIDENCE_GATE_ENABLED` (default `true`) enables conditional architecture blocking (hard block with zero observation tools; warning mode when observations exist but assumptions remain unverified).

#### PreCompact Hooks (1)

| Hook | Timeout | Purpose |
|------|---------|---------|
| `PreCompact_handoff_capture.py` | 10s | Capture handoff before compaction |

#### Notification Hooks (1)

| Hook | Timeout | Purpose |
|------|---------|---------|
| `voice_notifications.ps1` | 3s | Voice notifications |

---

### Core Constitutional Hooks

These hooks address specific failure modes identified from transcript analysis:

| Failure Mode           | Hook                       | Event              | Purpose                                   |
| ---------------------- | -------------------------- | ------------------ | ----------------------------------------- |
| **Skill substitution** | **Skill Enforcement v3.2** | **PreToolUse + Stop** | **Parallel regex + daemon validation, blocks invalid tool usage** |
| **Secret leakage**     | **Secret Scanner**         | **PreToolUse**     | **Blocks writes containing secrets, API keys, credentials** |
| **Credential exposure**| **Credential Filter**      | **PreToolUse**     | **Blocks Bash commands with exposed credentials** |
| **Output redaction**   | **Output Sanitizer**       | **PostToolUse**    | **Redacts secrets from tool output before display** |
| **Runaway sessions**  | **Runaway Session Detector**| **Stop**           | **Detects infinite loops, excessive tool thrashing** |
| **Meta-conversation filter** | **Cross-Validator** | **Stop** | **Exempts process self-talk from verification (e.g., "I didn't use TDD")** |
| Goal displacement      | Task Tracker               | `PostToolUse`      | Maintains ground truth about active task   |
| Goal drift             | *(removed — zero blocks in production)* | — | — |
| Overcomplication loop  | Investigation Gate         | `PreToolUse`       | Blocks writes until target module is read |
| Cascading fix failures | Failure Escalation        | `PostToolUse`      | Forces reassessment after N failures      |
| Zombie code            | Change Propagation        | `PostToolUse`      | Enforces cache clear + reference check    |
| Dismissing concerns    | Concern Detection         | `UserPromptSubmit` | Injects investigation mandate             |
| Unverified claims      | Success Validator         | `Stop`             | Blocks success claims without evidence    |
| Unverified fixes      | Cross Validator           | `Stop`             | Enforces empirical verification           |
| Error explanations     | Speculation Gate          | `Stop`             | Blocks error claims without verification  |
| Mechanical parroting   | Reality Check             | `Stop`             | Detects unverified code references        |
| Incomplete removal     | Reality Check             | `Stop`             | Detects orphaned/dead code                |
| Unparseable commands   | Unparseable Command Gate | `PreToolUse`       | Blocks `python -c`, `eval()`, injection risks |
| Hook edits without test| Hook Edit Gate             | `PreToolUse`       | Requires testing before editing hooks     |
| **Lib API breakages**  | **Lib Protection Gate**     | **`PostToolUse`**  | **Detects breaking changes in `__lib/` files** |
| Type errors            | Compilation Gate           | `PreToolUse`       | Runs type checkers before commits         |
| Symlink escapes        | Path Resolution Orchestrator | `PreToolUse`    | Blocks symlink creation (mklink, ln -s)   |
| Post-hoc attribution   | Overconfidence Detector   | `Stop`             | Detects causal claims without traced evidence |
| Sycophantic agreement  | Sycophancy Agreement      | `Stop`             | Detects unwarranted agreement patterns    |
| Work avoidance         | Lazy Closure Detector     | `Stop`             | Detects lazy fix language, premature offers |
| Tool thrashing         | Tool Thrashing Tracker    | `PostToolUse`      | Detects panic searching (repeated reads)  |
| Format inconsistency   | Lint Router               | `PostToolUse`      | Auto-formats files after edits            |
| Response mismatch      | Behavioral Quality Gate   | `Stop`             | Validates response matches question type  |
| Skill selection        | Skill Router               | `UserPromptSubmit` | Auto-suggests skills based on patterns    |
| Session confusion      | Session Manager            | `PostToolUse`      | Tracks tasks across sessions/terminals    |
| CKS query delay        | CKS Model Pre-Load        | `SessionStart`     | Pre-loads embedding model for fast CKS   |
| **Speculation w/o tools** | **Investigation Required** | **`Stop`**       | **Self-prompt when diagnostic Q answered without investigation** |
| **Unsubstantiated claims** | **Investigation Validator** | **`Stop`**     | **Blocks claims that exceed investigation ledger** |
| **Historical fabrication** | **Stop_historical_claims_gate** | **`Stop`**     | **Blocks fabricated past actions and fake state-transition narratives** |

### 1. Hook Protection System (`PreToolUse` + `PostToolUse`)

**Files:** `PreToolUse_hook_protection_gate.py`, `PostToolUse_hook_protection_gate.py`
**Docs:** See Library Code Protection System above

**Prevents accidental breaking changes** to hook and `__lib/` files through characterization-based validation.

- **Pre-edit**: Analyzes planned changes for breaking API modifications
- **Post-edit**: Captures before/after characterization, compares signatures
- **State storage**: Terminal-scoped state with file locking

**Environment variables:**
```bash
HOOK_PROTECTION_ENABLED=false     # Enable hook protection validation
HOOK_PROTECTION_BLOCKING=false    # Block mode in PreToolUse
INVESTIGATION_LEDGER_ENABLED=false # Enable investigation tracking
CONFIDENCE_VALIDATOR_ENABLED=false # Enable confidence ceiling validation
```

### 2. Skill Enforcement v3.2 (`UserPromptSubmit` + `PreToolUse` + `PostToolUse` + `Stop`)

**Files:**
- `PreToolUse/PreToolUse_skill_pattern_gate.py` (PRIMARY)
- `skill_enforcement_gate.py` (general gate)
- `posttooluse/v_state_tracker_hook.py` (state tracking)
- `skill-guard plugin: StopHook_skill_execution_gate.py` (SAFETY NET)

**Plan:** [skill_execution_enforcement_v3.2.md](skill_execution_enforcement_v3.2.md)

**Prevents skill substitution** — LLM loading skill documentation then providing its own analysis instead of executing the skill's designated workflow.

**v3.2 Architecture:**
- **PreToolUse** (PRIMARY): Parallel regex + daemon semantic validation, blocks before tool execution
- **State management**: Terminal-isolated state with extended schema (`hint`, `intent_enabled`)
- **PostToolUse** (TRACKING): Records skill execution state for Stop hook consumption
- **Stop hook** (SAFETY NET): Late violation logging, indicates PreToolUse failure

**Registry controls execution requirements:**
```python
SKILL_EXECUTION_REGISTRY = {
    "rca": {
        "tools": ["Bash", "Task"],
        "pattern": r"src\.rca|SimpleRCAEngine|RCAEngine|EnhancementRouter",
        "hint": "Use /rca via src.rca imports",
        "intent_enabled": True,  # Use daemon semantic validation
    },
    # ... other skills
}
```

**Decision matrix (6 combinations):**
| Regex | Daemon | Decision |
|-------|--------|----------|
| True | True | ALLOW (pass) |
| True | False | ALLOW (regex wins, log disagreement) |
| False | True | BLOCK (daemon caught semantic match) |
| False | False | BLOCK with hint |
| True | Error | ALLOW (daemon down, regex sufficient) |
| False | Error | BLOCK with hint |

**Environment variables:**
```bash
SKILL_PATTERN_ENFORCEMENT_ENABLED=true    # Enable PreToolUse pattern check
SKILL_INTENT_DAEMON_ENABLED=true         # Enable daemon semantic layer
SKILL_EXECUTION_GATE_ENABLED=true         # Enable Stop hook safety net
```

**Investigation tools whitelist:** Read, Grep, Glob, AskUserQuestion, Skill — always allowed for understanding the problem.

### 3. TDD Enforcement (`PreToolUse` + `PostToolUse`)

**Legacy TDD System:**
- `pretooluse_tdd_gate.py` (PreToolUse blocking)
- `PostToolUse_tdd_state.py` (state tracking)

**TDD-95 System (Recommended):**
- `PreToolUse_tdd95_gate.py` (evidence-based gate)
- `PostToolUse_tdd95_autoscaffold.py` (auto-scaffold)
- `PostToolUse_tdd95_runner.py` (test result tracking)
- `tdd95_core.py` (core module with state management)
- `critical_hooks.json` (critical hooks manifest)

**Enforces Test-Driven Development** for code modifications with 95% adoption target.

**TDD-95 Architecture:**
- **5-state machine**: NONE → TEST_EXISTS → FAILING → PASSING → COMPLETE
- **Evidence-based gating**: Smart detection vs. complex state tracking
- **Auto-scaffolding**: Creates test stubs when implementation files lack tests
- **Multi-terminal safe**: Per-terminal state + global index coordination
- **Windows-safe**: pathlib.Path everywhere, POSIX storage for JSON
- **Critical hooks enforcement**: Stricter requirements for safety-critical hooks

**Configuration via `settings.json`:**
```json
"tdd95": {
  "enabled": true,
  "enforcement_mode": "smart",
  "autoscaffold": {
    "enabled": true,
    "template": "minimal"
  },
  "gate": {
    "check_test_exists": true,
    "check_test_recency_minutes": 10,
    "block_on_missing": "scaffold",
    "block_on_stale": "suggest"
  },
  "tiers": {
    "TIER0": {"files": ["**/*.py", "**/*.ts"], "action": "scaffold"},
    "TIER1": {"files": ["src/**", "lib/**"], "action": "scaffold"}
  },
  "critical_hooks": {
    "enabled": true,
    "manifest_path": "P:/.claude/hooks/critical_hooks.json"
  }
}
```

**State location:** `.claude/state/tdd95/{terminal_id}/` + `global.json`

**Documentation:** `tests/TDD_95_IMPLEMENTATION.md` (complete guide)

### 4. Task Detection & Tracking (`UserPromptSubmit` + `PostToolUse`)

**Files:**
- `UserPromptSubmit/task_detector.py` (UserPromptSubmit detection)
- `PostToolUse_task_tracker.py` (PostToolUse tracking)
- `PostToolUse_task_router.py` (Task tool routing)

**Prevents goal displacement** by maintaining ground truth about the active task.

- Automatically detects tasks from user prompts
- Tracks TaskCreate/TaskUpdate/TaskList calls
- Multi-terminal safety with session-based state

**State location:** `.claude/state/task_tracker/`

**Environment variables:**
```bash
TASK_DETECTOR_ENABLED=true         # Enable task detection
TASK_TRACKER_ENABLED=true          # Enable task tracking
TASK_STATE_DIR=.claude/state/task_tracker/
```

### 6. Evidence & Claim Tracking (`PostToolUse` + `Stop`)

**Files:**
- `evidence_tracker.py` (PostToolUse evidence tracking)
- `PostToolUse_falsification_assessor.py` (falsification risk)
- `verify_claims_transcript.py` (Stop claim verification)
- `assumption_audit_v2.py` (Stop retrospective audit)

**Tracks execution evidence and validates claims** against what was actually done.

- **PostToolUse**: Tracks tool execution, evidence collection, falsification risk
- **Stop**: Verifies claims against transcript, audits retrospective claims

**Environment variables:**
```bash
ASSUMPTION_AUDIT_V2_ENABLED=true           # Enable assumption audit
CLAIM_SCOPE_CHECK_ENABLED=true             # Enable claim scope checking
CLAIM_COVERAGE_THRESHOLD=0.5               # Minimum claim coverage
HISTORICAL_CLAIMS_GATE_ENABLED=true        # Enable historical claims gate
EMPIRICAL_CLAIMS_PRECHECK_ENABLED=true     # Inject Observed/Inferred/Unknown precheck
```

### 7. File System Operations (`PreToolUse` + `PostToolUse`)

**Files:**
- `PreToolUse_file_lock.py` (PreToolUse locking)
- `PostToolUse_file_lock.py` (PostToolUse release)
- `PostToolUse_file_activity_tracker.py` (activity tracking)
- `PostToolUse_write_router.py` (write routing)
- `PreToolUse_write_router.py` (write routing)
- `path_resolution_orchestrator.py` (path protection)

**Manages file operations** with locking, routing, and protection.

- **PreToolUse**: Acquire file locks, route writes, protect paths
- **PostToolUse**: Release locks, track activity, route verification

**Key features:**
- Cross-platform file locking for concurrent access
- Path protection (blocks symlink creation)
- Activity tracking for tool thrashing detection

### 8. Code Quality & Validation (`PreToolUse` + `PostToolUse`)

**Files:**
- `PreToolUse_syntax_gate.py` (syntax validation)
- `PostToolUse_code_verification_gate.py` (code verification)
- `PostToolUse_lint_router.py` (auto-formatting)

**Ensures code quality** through syntax validation, verification, and auto-formatting.

**Lint Router supports:**
- Python: `ruff check --fix`
- TypeScript/JavaScript: `prettier --write`
- JSON/YAML/Markdown: `prettier --write`

**Environment variables:**
```bash
LINT_ROUTER_ENABLED=true               # Enable lint router
LINT_ROUTER_AUTO=ruff,prettier         # Which linters to run
```

### 9. Shell Command Safety (`PreToolUse` + `PostToolUse`)

**Files:**
- `shell_complexity_gate.py` (complexity check)
- `unparseable_command_gate.py` (injection protection)
- `recursive_failure_detector.py` (Catch-22 detection)
- `PreToolUse_bash_router.py` (bash routing)
- `posttooluse/outcome_validator_hook.py` (in-process, outcome validation)
- `posttooluse/error_attribution_hook.py` (in-process, error attribution)

**Protects against dangerous shell commands** and infinite loops.

- **PreToolUse**: Block complex commands, injection risks, detect loops
- **PostToolUse**: Outcome validation and error attribution (in-process via router)

**Security hard blocks:**
- `eval()`, `exec()`, complex `$()` substitution (injection risks)

**Warn-mode patterns:**
- complex shell composition (`shell_complexity_gate.py`)
- opaque `python -c` config/file mutation when `UNPARSEABLE_MUTATION_MODE=warn`

**Config:**
```bash
UNPARSEABLE_MUTATION_MODE=warn   # warn|block for opaque python -c mutations
```

- Overly complex commands (complexity threshold)
- Recursive failure patterns (Catch-22 loops)

**Scoped bypass:**
```bash
ALLOW_VDATE_VALIDATION=1 python -c "import ast; ast.parse(open('file.py').read())"
```

### 10. Investigation & Speculation Detection (`PostToolUse` + `Stop`)

**Files:**
- `pre_generation_registry.py` (library-first check)
- `PostToolUse_speculation_detector.py` (speculation detection)
- `inherited_choice_validator.py` (inherited choice detection)
- `speculation_gate.py` (Stop speculation blocking)

**Prevents speculation without investigation** and detects inherited choice patterns.

- **PreToolUse**: Library-first check before generation
- **PostToolUse**: Detect speculation, inherited choices
- **Stop**: Block error claims without verification

**Environment variables:**
```bash
PRE_GENERATION_REGISTRY_ENABLED=true       # Enable library-first mode
INVESTIGATION_REQUIRED_ENABLED=true         # Require investigation for diagnostics
INVESTIGATION_LEDGER_ENABLED=true          # Track investigation evidence
```

### 11. Change Propagation & Validation (`PostToolUse`)

**Files:**
- `posttooluse/change_propagation_hook.py` (in-process, change propagation)
- `posttooluse/truth_validator_hook.py` (in-process, truth validation)
- `posttooluse/strategy_escalation_hook.py` (in-process, escalation tracking)

**Ensures changes propagate correctly** and validates truth claims. All run in-process via PostToolUse_router.py.

- Enforces cache clear + reference check after structural changes
- Validates truth claims against evidence
- Tracks strategy escalation patterns

### 12. Prompt Enhancement (`UserPromptSubmit`)

**File:** `UserPromptSubmit/prompt_enhancement.py`

**Layer 1 of three-layer prompt enhancement architecture** - detects ambiguous prompts and injects clarification questions.

**Key Features:**
- **Ambiguity Detection**: Pattern-based detection for unclear antecedents ("fix it"), missing specifics ("implement this"), ambiguous improvements ("make it better"), too brief prompts (≤2 words)
- **Domain Detection**: Security, testing, database, frontend domains via path hints and keyword matching
- **Complexity Assessment**: Word count-based (simple ≤10, moderate 10-30, complex 30-60, expert 60+)
- **Clarification Injection**: Targeted questions based on ambiguity type
- **Fail-Open**: Errors never block sessions

**Routing Logic:**
| Complexity | Ambiguous | Action |
|------------|-----------|--------|
| Simple (≤10 words) | No | PASS - no injection |
| Simple (≤10 words) | Yes | CLARIFICATION - ask questions |
| Moderate+ (10+ words) | No | GUIDANCE - domain-specific context |
| Moderate+ (10+ words) | Yes | CLARIFICATION - ask questions |

**Ambiguity Patterns:**
| Pattern | Example | Reason |
|---------|---------|--------|
| `^(fix|check|test|debug)\s+(it|this|that|them)` | "fix it" | unclear_antecedent |
| `^(implement|add|create|write|build)\s+(this|it|that)$` | "implement this" | missing_specifics |
| `^(make|optimize|improve)\s+(it|this)\s+(better|faster)$` | "make it better" | ambiguous_improvement |
| `^(optimize|improve|enhance)\s+(this|it)$` | "optimize this" | ambiguous_improvement |
| `^(ok|help|fix)$` | "help" | too_brief (≤2 words) |

**Environment Variables:**
```bash
PROMPT_ENHANCEMENT_ENABLED=true    # Enable/disable hook (default: true)
PROMPT_ENHANCEMENT_DEBUG=false     # Enable debug logging (default: false)
```

**Prompt Choice State Module:**

| File | Purpose |
|------|---------|
| `__lib/prompt_choice_state.py` | Manages state for prompt enhancement choice system |

**Key Functions:**
| Function | Purpose |
|----------|---------|
| `save_prompt_choice(original, enhanced, injection)` | Store both prompts and the injection |
| `get_pending_choice()` | Get pending prompt choice if exists |
| `clear_prompt_choice()` | Clear the prompt choice state |
| `get_chosen_prompt()` | Get the user's chosen prompt based on their response |
| `detect_choice_from_message(message)` | Detect user's choice from their message |

**State Storage:**
- Location: `P:/.claude/state/prompt_choice/`
- File format: `{terminal_id}.json`
- Timeout: 300 seconds (5 minutes)

**Testing:**
```bash
# Run unit tests
cd P:/.claude/hooks/UserPromptSubmit/tests
pytest test_prompt_enhancement.py -v
```

**Design Document:** `P:/__csf/reviews/prompt_enhancement_bridge_design.md`

### 13. CKS Integration (`PostToolUse` + `Stop` + `UserPromptSubmit`)

**Files:**
- `repositories/doc_cks_ingester.py` (doc ingestion)
- `auto_cks_storage.py` (auto-storage)
- `Stop_cks_decision_capture.py` (decision capture)
- `SessionStart_cks_decision_load.py` (decision load)

**Integrates with Constitutional Knowledge System** for learning and retrieval.

- **PostToolUse**: Ingest documentation, auto-store solutions
- **Stop**: Capture decisions for future reference
- **SessionStart**: Load decision history for context

**Configuration via `settings.json`:**
```json
"cks_integration": {
  "enabled": true,
  "memory_config": {
    "max_memories": 5,
    "similarity_threshold": 0.7,
    "context_length_limit": 1500
  }
}
```

### 14. Session Management (`PostToolUse` + `SessionStart`)

**Files:**
- `session_change_tracker.py` (change tracking)
- `SessionStart_router.py` (initialization routing)

**Manages logical work sessions** across terminals and compaction.

- Tracks session changes for continuity
- Initializes session context on start

**State location:** `.claude/state/session_manager/`

### 15. Skill Routing (`UserPromptSubmit` + `PostToolUse`)

**Files:**
- `UserPromptSubmit_skill_router.py` (routing)
- `PostToolUse_next_command_suggester.py` (next command)

**Auto-selects and suggests skills** based on prompt pattern matching.

**Pattern mappings:**
- `debug`, `error`, `broken` → `/rca`
- `test`, `spec` → `/tdd`
- `validat`, `review` → `/p --phase=6` (security), `/p --phase=5` (certify)
- `implement`, `build` → `/p --phase=1`
- `research` → `/research`

### 16. Semantic File Routing (`PreToolUse`)

**File:** `semantic_file_router.py`

**Routes file operations** based on semantic analysis.

### 17. System Monitoring (`PostToolUse` + `SessionStart`)

**Files:**
- `PostToolUse_router.py` (routing)
- `PostToolUse_system2.py` (monitoring v2)
- `failure_recorder.py` (failure recording)

**Monitors system behavior** and records failures for escalation.

- Routes to monitoring sub-hooks
- Records failures for pattern analysis
- System health monitoring

### 18. Context & Compaction (`UserPromptSubmit` + `PreCompact`)

**Files:**
- `post_compact_reminder.py` (post-compaction reminder)
- `PreCompact_handoff_capture.py` (handoff capture)

**Manages context across compaction** with handoff/restore system.

**Handoff system features:**
- SHA256 validation
- Terminal-scoped isolation
- 7-day auto-cleanup
- 45-min stuck task timeout

### 20. Architecture & Evidence (`Stop`)

**Files:**
- `architecture_evidence_gate.py` (evidence gate)

**Blocks architecture proposals without evidence** (CLAUDE.md: vague_directive_gate).

### 21. Cross-Validation (`Stop`)

**File:** `StopHook_cross_validator.py`

**Enforces empirical verification** for "fixed" claims and hook edits.

**Research basis:** Cross-Validation / Self-Verification (Duke, MIT CSAIL)

**Meta-Conversation Exemption (2026-02-12):**
- Process/self-report statements skip verification: "I did not use TDD", "I only ran py_compile", "I created X, modified Y"
- External claims still require evidence: "The fix works", "Tests passed", "Hook returns {'ok': true}"

**Gate logic:**
```python
is_meta = is_meta_conversation(transcript) or is_self_referential(response)
has_external_claim = matches_external_claim_pattern(response)

if is_meta and not has_external_claim:
    # Skip verification - process description only
    allow()
# Otherwise: Run cross-validation
```

**Environment variables:**
```bash
CROSS_VALIDATION_HOOK_ENABLED=false    # Block "fixed" claims without verification
CROSS_VALIDATION_VERBOSE=false         # Warnings only (true) or block (false)
```

**Shared helper:** `__lib/shared_helpers.py` provides `is_self_referential()` with process/self-report patterns.

### 22. Auto-Commit (`Stop`)

**File:** `auto_commit_hook.py`

**Auto-commits successful changes** after validation passes.

### 23. Voice Notifications (`Notification`)

**File:** `voice_notifications.ps1`

**Provides voice notifications** for system events.

### 24. Overcomplication Loop Prevention (`PreToolUse`)

**File:** `PreToolUse_investigation_gate.py` (documented in CLAUDE.md)

**Blocks code modifications** that bypass investigation.

### 25. Goal Drift Detection — REMOVED

Removed: LLM prompt hook that checked alignment on every Edit/Write/Bash/Task call.
Zero blocks recorded in production. 8s timeout per call was pure overhead.

**Key design:**
- No API key needed (uses Claude Code's built-in Haiku)
- No external dependencies
- Semantic understanding vs pattern matching

### 26. Investigation Gate (`PreToolUse`)

**File:** `PreToolUse_investigation_gate.py`

Blocks code modifications that bypass investigation.

- Tracks all file reads in session
- Before write operations, checks if target was investigated
- Blocks writes with insufficient read coverage

**Bypass declarations:**

- `"Investigation complete: [summary]"`
- `"Greenfield: [reason this is new code]"`

```bash
CSF_INVESTIGATION_GATE=1          # Enable/disable
CSF_MIN_READS_BEFORE_WRITE=1      # Minimum related files to read
```

### 27. Failure Escalation (`PostToolUse`)

**File:** `PostToolUse_failure_escalation.py`

Forces architectural reassessment after consecutive failures.

- Detects failure patterns in tool output
- Counts consecutive failed fix attempts
- After N failures, blocks further tool use

**Bypass:** `"Reassessment complete: [what you now understand differently]"`

```bash
CSF_FAILURE_ESCALATION=1          # Enable/disable
CSF_MAX_CONSECUTIVE_FAILURES=2    # Failures before block
CSF_ESCALATION_COOLDOWN=30        # Auto-unblock after N minutes
```

### 28. Concern Detection (`UserPromptSubmit`)

**File:** `UserPromptSubmit_concern_detection.py`

Detects user frustration and forces investigation before response.

**Detected signals:**

- Logic concerns: "doesn't make sense", "that's wrong"
- Frustration: strong language, repeat complaints
- Data concerns: "inconsistent", "missing N items"
- Regression: "used to work", "broke something"

```bash
CSF_CONCERN_DETECTION=1           # Enable/disable
```

### 29. Change Propagation (`PostToolUse`)

**File:** `PostToolUse_change_propagation.py`

Enforces cache clearing and duplicate detection after structural changes.

**Required verifications:**

- `grep_references`: Search for calls to removed code
- `cache_clear`: Delete `__pycache__` and `.pyc` files
- `execution_test`: Run code using changed functionality
- `registry_check`: Search for filename in configs

```bash
CSF_CHANGE_PROPAGATION=1          # Enable/disable
```

### 30. Success Validator (`Stop`)

**File:** `StopHook_success_validator.py`

Prevents success claims without verification evidence.

- Scans final response for completion claims
- Checks for execution evidence
- Cross-references outstanding requirements from other hooks

```bash
CSF_SUCCESS_VALIDATOR=1           # Enable/disable
CSF_SUCCESS_VALIDATOR_MODE=warn   # "warn" or "block"
```

### 31. Reality Check Validator (`Stop`)

**File:** `StopHook_reality_check.py`

Detects two failure modes:

1. **Mechanical parroting** — Quoting what code "checks for" without verifying targets exist
2. **Incomplete solutions** — Removing functionality but leaving orphaned interfaces

**Detected patterns:**

- "The code checks for X" without verification that X exists
- Platform mismatches (`.sh` on Windows, `.bat` on Linux)
- "Removed X" but leaving related flags/imports/help text
- "--debug flag exists but doesn't do anything"

```bash
CSF_REALITY_CHECK=1               # Enable/disable
CSF_REALITY_CHECK_MODE=warn       # "warn" or "block"
```

### 32. Overconfidence Detector (`Stop`)

**Runtime:** `Stop.py` in-process gate (`anti_sycophancy_quality`)
**Module:** `anti_sycophancy/overconfidence_detector.py`
**Docs:** [docs/overconfidence_detector.md](file:///P:/.claude/hooks/docs/overconfidence_detector.md)

Detects and challenges claims made without traced evidence, particularly **post-hoc attribution errors** where Claude observes an outcome during testing and incorrectly infers causation.

**Detected patterns:**

| Pattern Type | Examples | Issue |
|--------------|----------|-------|
| Root cause claims | "the root cause is", "this explains why" | Causal assertion without traced evidence |
| Outcome attribution | "correctly blocked", "handled by", "triggered by" | Correlation ≠ causation |
| Certainty markers | "definitely", "certainly", "clearly shows" | Overconfident language |
| Unqualified conclusions | "proves that", "demonstrates" | Missing evidence tier |

**Example failure mode:**
```
Testing /v hooks → command blocked → "The /v skill hooks correctly blocked..."
WRONG: Actually blocked by unparseable_command_gate.py (different hook)
```

**Mechanism:**
1. Scans response for attribution/confidence patterns
2. Generates self-prompt asking for verification
3. Logs to audit trail for `/hook-audit` review

**Modes:**
- **Soft (default):** Injects self-prompt for reflection
- **Hard:** Blocks response until claim is qualified

```bash
OVERCONFIDENCE_DETECTOR_ENABLED=true   # Enable/disable
OVERCONFIDENCE_DETECTOR_BLOCK=false    # Soft mode (inject prompt)
OVERCONFIDENCE_DETECTOR_BLOCK=true     # Hard mode (block response)
```

### 33. Sycophancy Agreement Detector (`Stop`)

**File:** `StopHook_sycophancy_agreement.py`

Detects unwarranted agreement patterns where Claude agrees without evidence.

- Catches "you're right" without verification
- Detects "I agree" without supporting reasoning
- Flags excessive validation language

```bash
SYCOPHANCY_AGREEMENT_ENABLED=true   # Enable/disable
```

### 34. Lazy Closure Detector (`Stop`)

**Runtime:** `Stop.py` in-process gate (`anti_sycophancy_quality`)
**Module:** `anti_sycophancy/lazy_closure_detector.py`

Detects work avoidance and premature task closure patterns.

**Detected patterns:**

| Pattern Type | Examples | Issue |
|--------------|----------|-------|
| Lazy justification | "is appropriate", "looks good", "no issues" | Claims without evidence |
| Assumed mechanism | "built-in verification", "automatically handles" | Unverified capability claims |
| Work avoidance | "administrative acknowledgment", "just a formality" | Framing closure as trivial |
| Assumed compliance | "agents follow X", "workflow ensures" | Compliance without verification |
| **Lazy fix** | "quick fix", "5-line edit", "workaround", "bypass" | Patches over root cause |
| **Premature offer** | "Want me to do it?", "Should I implement?" | Offering before understanding |

**Mechanism:**
1. Word-boundary regex detects patterns
2. Checks for evidence markers that make patterns acceptable
3. Generates self-prompt for LLM self-correction

```bash
LAZY_CLOSURE_DETECTOR_ENABLED=true   # Enable/disable
```

### 35. Tool Thrashing Tracker (`PostToolUse`)

**File:** `posttooluse/tool_thrashing_tracker.py`

Detects repeated reads of the same file within a turn—"panic searching" without synthesis.

**What counts as thrashing:**
- Same file read multiple times with overlapping line ranges
- No output/synthesis between reads

**What doesn't count:**
- Pagination (non-overlapping ranges)
- Re-reading after making changes (verification)
- Reading same file in different turns

**State:** Written to `.state/turn_tool_usage.json` for Stop hook consumption.
**Reset:** State cleared on each new user message (UserPromptSubmit).

```bash
TOOL_THRASHING_TRACKER_ENABLED=true   # Enable/disable
```

### 36. Behavioral Quality Gate (`Stop`)

**File:** `StopHook_behavioral_quality_gate.py`

Unified response quality validation covering multiple behavioral gaps.

**Checks performed:**

| Check | Source | Action |
|-------|--------|--------|
| Lazy-fix language | `lazy_closure_detector` | Flag with self-prompt |
| Premature offer | Pattern + Investigation Gate state | Block if gate not satisfied |
| Tool thrashing | Turn state from tracker | Inject warning |
| Question-type mismatch | Heuristic classifier | Flag if response doesn't match |

**Question-type classification:**
- **Binary:** Short questions starting with "did", "is", "was", etc. → expects YES/NO near start
- **Root cause:** Contains "why", "root cause", "what happened" → expects causal explanation
- **Open-ended:** Everything else → flexible response

**Self-prompt examples:**
```
⚠️ LAZY FIX DETECTED: 'quick fix'
→ Does this address root cause or just patch symptoms?

⚠️ TOOL THRASHING: Read same file multiple times: file.py
→ Synthesize findings before re-reading.

⚠️ RESPONSE MISMATCH: Binary question expects YES/NO near start
→ Answer the actual question first, then elaborate.
```

```bash
BEHAVIORAL_QUALITY_GATE_ENABLED=true   # Enable/disable
```

### 37. Symlink Blocking (`PreToolUse`)

**Files:** `path_resolution_orchestrator.py`, `deny_root_write.py`

Blocks symlink creation commands in the workspace.

**Blocked commands:**
- Windows: `mklink`
- Unix: `ln -s`, `ln`
- PowerShell: `New-Item -ItemType SymbolicLink`

**Rationale:** Symlinks are fragile, violate path protection policies, and create security concerns.

**Error message:**
```
SYMLINK NOT ALLOWED

Symlinks are not allowed in this workspace.

If you need to reference another location, use the actual path or configure the application to use the desired location directly.
```

### 38. CKS Model Pre-Load (`SessionStart`)

**File:** `SessionStart_cks_preload.py`

Pre-loads sentence transformer model for fast CKS (Constitutional Knowledge System) queries.

**Performance:**
- First session: Download from HuggingFace (~6.8s)
- Subsequent sessions: Load from local cache (~0.5s)

**Cache location:** `P:\.model_cache\`

**Multi-terminal safety:** File-based lock prevents concurrent downloads.

**Environment variables (set in `settings.json`):**
```json
"env": {
  "SENTENCE_TRANSFORMERS_HOME": "P:\\.model_cache",
  "TRANSFORMERS_CACHE": "P:\\.model_cache\\transformers",
  "HF_HOME": "P:\\.model_cache"
}
```

**Graceful degradation:** If CKS fails to load, hooks continue working without auto-retrieval.

### 39. Task Tracker (`PostToolUse`)

**File:** `PostToolUse_task_tracker.py`
**Library:** `__lib/session_manager.py`

Tracks TaskCreate/TaskUpdate/TaskList calls for session-based task coordination with enhanced context capture.

**Multi-terminal safety:**
- Session ID = Logical work unit (persists across terminals and /clear)
- Terminal ID = Physical instance (collision safety only)
- Re-entrancy guard prevents infinite loops

**Features:**
- Groups tasks by session_id (primary key)
- Tracks terminal_id for collision safety
- File-based persistence survives compaction
- Syncs tasks across sessions via TaskList
- **Enhanced task context capture:**
  - `description` - from TaskCreate input (what the task is about)
  - `files_referenced` - last 5 files accessed via Read/Edit/Grep (related files)
  - `session_timestamp` - ISO8601 timestamp for temporal context

**Task metadata structure:**
```json
{
  "id": "task_1",
  "subject": "Fix authentication bug",
  "description": "Fix process_prompt() in auth.py to handle null tokens",
  "files_referenced": ["P:/src/auth.py", "P:/tests/test_auth.py"],
  "session_timestamp": "2026-02-06T10:00:00+00:00",
  "status": "pending",
  "created_at": 1738838400.0,
  "session_id": "session_123",
  "terminal_id": "env_abc123"
}
```

**State location:** `.claude/state/task_tracker/`

```bash
TASK_TRACKER_ENABLED=true              # Enable/disable (default: true)
TASK_STATE_DIR=.claude/state/task_tracker/  # State directory
```

### 40. Lint Router (`PostToolUse`)

**File:** `PostToolUse_lint_router.py`

Auto-formats files after edits using language-specific linters.

**Supported languages:**
- Python: `ruff check --fix`
- TypeScript/JavaScript: `prettier --write`
- JSON/YAML/Markdown: `prettier --write`

**Multi-terminal safety:** Re-entrancy guard via marker file.

```bash
LINT_ROUTER_ENABLED=true               # Enable/disable (default: true)
LINT_ROUTER_AUTO=ruff,prettier         # Which linters to run
```

### 19. Compilation Gate (`PreToolUse`)

**File:** `PreToolUse_compilation_gate.py`

Runs language-specific type checkers before commit operations.

**Checks:**
- Python: `mypy .` (if pyproject.toml/mypy.ini exists)
- TypeScript: `tsc --noEmit` (if tsconfig.json exists)

**Opt-in via environment variables:**
```bash
MYPY_CHECK_ENABLED=true                # Enable Python type checking
TS_CHECK_ENABLED=true                  # Enable TypeScript type checking
STRICT_MODE=false                      # Block on failures (default: warnings only)
```

### 20. Hook Edit Gate (`PreToolUse`)

**File:** `PreToolUse_hook_edit_gate.py`

Requires testing before editing hook files.

**Protected paths:** `.claude/hooks/**/*.py`

**Enforcement:**
- Blocks Edit/Write on hook files
- Requires test execution first (pytest, python test)
- Graceful degradation if tests unavailable

```bash
HOOK_EDIT_VERIFICATION_ENABLED=true    # Require testing before hook edits
```

### 21. Cross Validator (`Stop`)

**File:** `StopHook_cross_validator.py`

Enforces empirical verification for claims and hook edits.

**Blocks:**
- "fixed" claims without verification
- Hook edits without testing evidence

**Research basis:** Cross-Validation / Self-Verification (Duke, MIT CSAIL)

**Session isolation:** Terminal-specific state directories prevent cross-terminal bleed.

```bash
CROSS_VALIDATION_HOOK_ENABLED=false    # Block "fixed" claims without verification
CROSS_VALIDATION_VERBOSE=false         # Warnings only (true) or block (false)
HOOK_EDIT_VERIFICATION_ENABLED=false   # Require testing before editing hooks
```

### Meta-Conversation Detection

**Shared helper:** `__lib/shared_helpers.py`

**Functions:**
- `is_meta_conversation(transcript)` — Detects user meta-questions ("why did you...", "what was your thinking...")
- `is_self_referential(response)` — Detects LLM self-referential patterns

**Self-referential patterns (as of 2026-02-12):**
| Pattern Type | Examples |
|--------------|-------------|
| Process/TDD | "I did not use TDD", "I only ran py_compile", "I didn't write tests first" |
| File operations | "I created shared_helpers.py", "I modified three hooks" |
| Apologies | "I apologize", "sorry", "my mistake" |
| Reasoning | "I did this because", "my reasoning was", "the reason I..." |
| Admission | "I misread", "I misunderstood", "I misremembered" |

**External claim patterns (require verification):**
- "The fix works", "tests passed", "hook returns {'ok': true}"
- "File is at C:\path", "bug is in line 42", "issue is fixed"

### 22. Skill Router (`UserPromptSubmit`)

**File:** `UserPromptSubmit_skill_router.py`

Auto-selects and suggests skills based on prompt pattern matching.

**Pattern mappings:**
- `debug`, `error`, `broken` → `/rca`
- `test`, `spec` → `/tdd`
- `validat`, `review` → `/p --phase=6` (security), `/p --phase=5` (certify)
- `implement`, `build` → `/p --phase=1`
- `research` → `/research`

**Opt-in:** Requires `@tags` or explicit patterns.

```bash
SKILL_ROUTER_ENABLED=false             # Enable/disable (default: false - opt-in)
SKILL_ROUTER_VERBOSE=false             # Show all matched skills (default: top match only)
```

### 23. Session Management System

**Library:** `__lib/session_manager.py`
**Skill:** `/session`

Manages logical work sessions across terminals and compaction.

**Session architecture:**
- Session ID = Logical work unit (persists across terminals and /clear)
- Terminal ID = Physical instance (collision safety only)

**Commands:**
- `/session` - List all sessions
- `/session <name>` - Create new session
- `/session rename <name>` - Rename current
- `/session switch <id>` - Switch sessions
- `/session claim <task-id>` - Claim task for current session

**State location:** `.claude/state/session_manager/`
**Current session:** `.claude/hooks/current_session.json`

### 24. Validation Cache

**Library:** `__lib/validation_cache.py`

SHA256-based caching for validation results to avoid redundant checks.

**Performance targets:**
- TDD test file discovery: ~50ms → ~5ms
- Path validation: ~30ms → ~2ms
- Pattern matching: ~20ms → ~1ms

**Multi-terminal safety:** Cache keys include terminal_id, cwd, tool version, config hash.

**TTL:** 5 minutes (stale data acceptable for validation)

```python
from validation_cache import ValidationCache

cache = ValidationCache(operation="tdd_test_discovery", version="1.0")
result = cache.get(lambda: expensive_operation())
```

### 25. Investigation Ledger System (`PostToolUse` + `Stop`)

**Directory:** `investigation-ledger/`
**Docs:** [investigation-ledger/README.md](file:///P:/.claude/hooks/investigation-ledger/README.md)

Two-layer defense against speculation without investigation.

**Architecture:**
```
PostToolUse → InvestigationTracker → session_ledger.json
                                            ↓
Stop → StopHook_investigation_required → "Did you investigate?" (self-prompt)
Stop → Stop_investigation_validator → "Do claims match ledger?" (block)
```

**Layer 1: Investigation Required** (`StopHook_investigation_required.py`)

Detects when LLM answers diagnostic questions without using investigation tools.

- **Trigger:** Diagnostic question + No tools used + Substantial response
- **Action:** Injects self-assessment prompt (WARN, non-blocking)
- **Principle:** "The LLM knows if it investigated or speculated"

```bash
INVESTIGATION_REQUIRED_ENABLED=true   # Enable/disable
```

**Layer 2: Investigation Validator** (`investigation-ledger/Stop_investigation_validator.py`)

Validates claims against what was actually investigated.

- **Trigger:** Response contains claims about system behavior
- **Action:** Blocks if claims exceed investigation evidence (CRITICAL)
- **Principle:** "Confidence cannot exceed evidence tier ceiling"

```bash
INVESTIGATION_LEDGER_ENABLED=true     # Enable/disable
```

**Evidence Tiers:**

| Tier | Ceiling | Requirement |
|------|---------|-------------|
| 1 | 95% | 3+ files read + successful execution |
| 3 | 75% | 2+ files read OR (1 file + 2 searches) |
| 4 | 50% | 1 file read OR 1 search |
| None | 0% | No investigation |

**Key design:**
- Structural detection (tool usage) is binary and reliable
- Pattern-based detection is fragile - minimized
- LLM self-assessment via direct questions works well for Stop hooks

---

## Configuration

### Environment Variables

```bash
# Core paths (from settings.json)
export CSF_STATE_DIR=".claude/state"
export CSF_HOOK_DEBUG=1

# Parallel hooks
export PARALLEL_HOOKS_ENABLED=1

# Session management
export SESSION_REVERSION_INPROCESS=1

# Skill Enforcement v3.2
export SKILL_ENFORCEMENT_INPROCESS=1
export SKILL_PATTERN_ENFORCEMENT_ENABLED=true
export SKILL_INTENT_DAEMON_ENABLED=true
export SKILL_EXECUTION_GATE_ENABLED=true

# Execution Orchestrator
export EXEC_ORCHESTRATOR_INPROCESS=1

# TDD Enforcement
export TDD_ENFORCEMENT_MODE="enforced"

# Task Detection
export TASK_DETECTOR_ENABLED="true"

# Prompt Enhancement
export PROMPT_ENHANCEMENT_ENABLED="true"
export PROMPT_ENHANCEMENT_DEBUG="false"

# Overconfidence Detection
export OVERCONFIDENCE_DETECTOR_ENABLED="true"
export OVERCONFIDENCE_DETECTOR_BLOCK="false"

# Lazy Closure Detection
export LAZY_CLOSURE_DETECTOR_ENABLED="true"

# Investigation & Evidence
export INVESTIGATION_LEDGER_ENABLED="true"
export INVESTIGATION_REQUIRED_ENABLED="true"

# Assumption Audit
export ASSUMPTION_AUDIT_V2_ENABLED="true"
export TEST_ASSUMPTION_AUDIT_METHOD="loose"
export TEST_ASSUMPTION_AUDIT_MODE="block"

# Claim Scope
export CLAIM_SCOPE_CHECK_ENABLED="true"
export CLAIM_COVERAGE_THRESHOLD="0.5"

# Historical Claims
export HISTORICAL_CLAIMS_GATE_ENABLED="true"

# Cross Validation
export CROSS_VALIDATION_HOOK_ENABLED="false"
export CROSS_VALIDATION_VERBOSE="false"
export HOOK_EDIT_VERIFICATION_ENABLED="false"

# Hook Protection
export HOOK_PROTECTION_ENABLED="false"
export HOOK_PROTECTION_BLOCKING="false"
export CONFIDENCE_VALIDATOR_ENABLED="false"

# Pre-Generation Registry (Library-First)
export PRE_GENERATION_REGISTRY_ENABLED="true"
export PRE_GENERATION_MAX_SUGGESTIONS=5
export PRE_GENERATION_PERFORMANCE_TARGET_MS=500
export PRE_GENERATION_LIBRARY_FIRST_MODE="strict"

# CKS Integration
export CKS_INTEGRATION_ENABLED="true"
export CKS_MAX_MEMORIES="5"
export CKS_SIMILARITY_THRESHOLD="0.4"
export CKS_CONTEXT_LENGTH_LIMIT="1500"
export CKS_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# Success Validator
export CSF_SUCCESS_VALIDATOR_MODE="block"

# Global Bypass
export CONSTITUTIONAL_HOOKS_BYPASS="0"
```

### Disable a Hook Temporarily

```bash
# Via environment
export CSF_INVESTIGATION_GATE=0

# Via file rename
mv PreToolUse_investigation_gate.py PreToolUse_investigation_gate.py.off
```

### Bypass All Constitutional Hooks

```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

### Allowed External Paths

The `PreToolUse_directory_policy.py` hook allows whitelisting external paths (outside `P:/`) for development operations. This is configured in `config/directory_policy.json`:

```json
"allowed_external_paths": {
  "description": "External paths (outside P:/) allowed for development operations",
  "patterns": [
    "*/site-packages/*.pth",           # Python package config
    "*/.claude/plans/*",               # Claude Code plan files (any user)
    "c:/users/*/.claude/plans/*",      # Claude Code plan files (Windows)
    "p:/standalone/*"                  # Standalone packages
  ],
  "exact_paths": [
    "C:/Users/brsth/.claude/projects/",  # Auto memory directory
    "C:/Users/brsth/.gemini/antigravity/brain/"
  ]
}
```

**Implementation note (2026-02-06):**
- External path whitelist is now sourced **exclusively** from `directory_policy.json`
- The `DirectoryPolicy.get_allowed_external_paths()` method loads both `patterns` (wildcards) and `exact_paths`
- `check_external_path_consent()` in `deny_root_write.py` uses the policy (no hardcoded constants)
- Single source of truth prevents drift between config and code

**To add new external paths:**
1. Edit `P:\.claude\hooks\config\directory_policy.json`
2. For exact paths: Add to `allowed_external_paths.exact_paths` array
3. For wildcard patterns: Add to `allowed_external_paths.patterns` array
4. Patterns use `fnmatch` glob syntax (case-insensitive)

### Scoped Bypass (Operation-Specific)

**Unlike global bypass**, scoped bypasses allow specific operations while maintaining security logging and audit trails.

**Available bypass variables:**

| Variable | Purpose | Example Usage |
|----------|---------|---------------|
| `ALLOW_VDATE_VALIDATION=1` | Allow vdate validation commands | `ALLOW_VDATE_VALIDATION=1 python -m src.commands.vdate file.py` |
| `ALLOW_BUILD_VALIDATION=1` | Allow build validation commands | `ALLOW_BUILD_VALIDATION=1 python -m build.validate` |

**How it works:**

1. Hook detects blocked operation (e.g., `python -c` for validation)
2. Checks if scoped bypass is enabled for that operation type
3. If bypassed: logs operation to audit trail and allows execution
4. If not bypassed: blocks as normal

**Audit logging:**

All scoped bypass usage is logged to `logs/constructional_blocks.jsonl` with:
- Timestamp
- Operation type
- Which bypass variable was triggered
- Command that was allowed

**Benefits over global bypass:**

- **Targeted**: Only affects specific operations, not entire hook system
- **Auditable**: Every bypass is logged for review
- **Composable**: Multiple tools can have their own bypass variables
- **Temporary**: Easy to enable/disable per operation

**Example:**

```bash
# Without bypass - blocked
python -c "import ast; ast.parse(open('file.py').read())"
# → BLOCKED by unparseable_command_gate.py

# With scoped bypass - allowed and logged
ALLOW_VDATE_VALIDATION=1 python -c "import ast; ast.parse(open('file.py').read())"
# → ALLOWED (logged to constructional_blocks.jsonl)
```

---

## Logging and Analysis

Constitutional hooks log blocks/warnings for periodic review. Multiple log files track different aspects of hook behavior.

### Structured Hook Logging (v3.0)

**Overview:** SQLite-based logging with WAL mode for concurrent multi-terminal access. Eliminates lock contention errors that occurred with JSONL-based logging.

**Implementation:** `cc_diagnostic_logger.py` with thread-local SQLite connections and WAL mode.

**Database:** `logs/diagnostics/diagnostics.db`

**Schema:**
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `context` | Prompt tracking | prompt_preview, prompt_length, claude_md_present |
| `hooks` | Hook invocations | hook_name, event_type, action, execution_time_ms |
| `tools` | Tool call logs | tool_name, tool_input, success, duration_ms |
| `assumptions` | Assumption detection | assumption_type, assumption, verified |
| `errors` | Error logging | error_type, error_message, stack_trace |

**CLI usage:**
```bash
# View recent logs
python P:/.claude/hooks/cc_diagnostic_logger.py recent --type hooks --count 10

# Session summary
python P:/.claude/hooks/cc_diagnostic_logger.py summary

# Database status
python P:/.claude/hooks/cc_diagnostic_logger.py status

# Clear all logs
python P:/.claude/hooks/cc_diagnostic_logger.py clear
```

**Concurrent access:** WAL mode enables multiple terminals to write simultaneously without lock contention.

**See:** `docs/LOGGING_STANDARD.md` for schema documentation

### Hook Audit Skill (Recommended)

```bash
# Full compliance dashboard
/hook-audit

# Specific analysis
/hook-audit blocks        # Blocking events
/hook-audit assumptions   # Assumption audit compliance  
/hook-audit attribution   # Error attribution compliance
/hook-audit escalation    # Phase 2 recommendations
/hook-audit health        # Hook system health

# Custom time range
/hook-audit --days 14

# Terminal filtering (v2.1)
/hook-audit --terminal    # Current terminal only
/hook-audit --all         # Per-terminal breakdown
```

### Analysis Scripts

```bash
cd P:\.claude\hooks

# Unified dashboard
python hook_audit_dashboard.py

# Specific systems
python analyze_blocks.py              # Hook blocking events
python analyze_error_attribution.py   # Error source injections
python analyze_audit_compliance.py    # Assumption audit compliance
python analyze_hooks.py               # General hook metrics

# Terminal-filtered analysis (v2.1)
python analyze_assumption_audit.py --terminal  # Current terminal only
python analyze_assumption_audit.py --all       # Per-terminal breakdown
```

### Terminal Isolation (v2.1)

When running multiple Claude Code instances, logs can get mixed. Terminal isolation prevents cross-contamination.

**Key files:**
- `terminal_detection.py` — Core detection logic, normalization, diagnostics
- `SessionStart_terminal_id.py` — Sets CLAUDE_TERMINAL_ID env var at session start

**Normalized ID format:** `{source}_{raw_id}`

| Source | Example | When Used |
|--------|---------|-----------|
| `env_` | `env_58fe0386-...` | From CLAUDE_TERMINAL_ID env var |
| `tempfile_` | `tempfile_58a8e5f3-...` | From temp file (legacy) |
| `console_` | `console_1a2b3c` | From Windows ConsoleHost handle |
| `fallback_` | `fallback_1` | When nothing detected |

**Terminal-scoped state files:**
- `state/pending_assumption_audit_{hash}.json` — Per-terminal compliance tracking

**Session/terminal context pinning (v2.2):**
- `Stop_router.py` and `PostToolUse_router.py` set `CLAUDE_SESSION_ID` when `session_id` is present in hook input.
- Existing `CLAUDE_TERMINAL_ID` is preserved; if missing, routers derive `session_{session_id}` as a stable fallback key.
- `tool_sequence_manager.load_tool_sequence_filtered()` is used by `assumption_audit_v2.py` to filter evidence by current session + terminal.
- Tool sequence entries now include `session_id` and `terminal_id` to support scoped reads.

**Diagnostic:**
```python
from terminal_detection import get_terminal_id_diagnostic
import json
print(json.dumps(get_terminal_id_diagnostic(), indent=2))
```

**See:** `docs/TERMINAL_ISOLATION.md` for full documentation.

### Log Files

| Log | Path | Purpose |
|-----|------|---------|
| Diagnostics (SQLite) | `logs/diagnostics/diagnostics.db` | Hook invocations, tool calls, context, assumptions, errors |
| Error Attribution | `P:/.claude/logs/error_attribution.jsonl` | Error source injections |
| Blocks | `logs/constructional_blocks.jsonl` | Hook blocking events |
| Enforcement | `logs/block_enforcement.jsonl` | Hard blocks (exit 2) |
| Assumption Audit | `logs/test_assumption_audit.jsonl` | Audit triggers + compliance |
| Absence Claims | `logs/absence_claim_gate.jsonl` | "Nothing found" claims |
| Subagent | `logs/subagent_enforcer.jsonl` | Subagent enforcement |

**Note:** The diagnostic database uses SQLite with WAL mode for concurrent multi-terminal access. Use `cc_diagnostic_logger.py` CLI to query.

### Weekly Analysis

```bash
cd P:\.claude\hooks
python analyze_blocks.py
```

**Output:**

- Block counts by hook and reason
- Recent blocked commands
- Suggestions for SAFE_PATTERNS adjustments
- Review reminder when threshold exceeded

### Mark Review Complete

```bash
python analyze_blocks.py --mark-reviewed
```

Sets weekly review timer. Next review due in 7 days.

### Log Filtering

Test commands are automatically excluded from logging:

- Pytest environment (`PYTEST_CURRENT_TEST`)
- Test probes (`eval("evil")`, `exec("evil")`, test file writes)

---

## Usage Examples

### Before/After: Overcomplication Loop

**Without hooks:**

```
User: how do I set worker count?
AI: [proposes complex manual workarounds]
AI: [proposes more workarounds]
AI: [finally mentions existing command after 4 exchanges]
```

**With Investigation Gate:**

```
User: how do I set worker count?
🛑 [blocked from proposing code until checking existing commands]
AI: [reads yt --help, batch_download.py]
AI: "The existing batch-download command handles this."
```

### Before/After: Cascading Failures

**Without hooks:**

```
AI: [Fix #1] → Fails
AI: [Fix #2] → Fails
AI: [Fix #3] → Fails
AI: [Fix #4] → Finally works (after 30 minutes)
```

**With Failure Escalation:**

```
AI: [Fix #1] → Fails
⚠️ Fix attempt failed (1/2)
AI: [Fix #2] → Fails
🛑 FAILURE ESCALATION TRIGGERED
AI: "Reassessment complete: The issue is SQLite connection-level
    locking, not Python thread locking."
AI: [Fix with correct understanding]
```

---

## Troubleshooting

### Hook Not Loading

```bash
# Check syntax
python -m py_compile P:\.claude\hooks\<hook>.py

# Check registration
grep "<hook>" P:\.claude\settings.json
```

### Common Errors

| Error                   | Cause                     | Fix                               |
| ----------------------- | ------------------------- | --------------------------------- |
| "unterminated f-string" | Literal newline in string | Use `\n` escape sequence          |
| Hook exits with code 2  | Wrong blocking method     | Use `{"continue": false}`, exit 0 |
| `tool_output` not found | Wrong field name          | Use `tool_response` field         |
| JSONDecodeError         | Malformed JSON input      | Protected by hook_runner (see below) |
| "SessionStart:startup hook error" | Node.js DEP0190 warnings | Add `--no-deprecation` flag (see below) |

### Plugin Hook stderr Warnings (Node.js DEP0190)

**Symptom**: "SessionStart:startup hook error" on session start despite hooks working correctly

**Cause**: Node.js v24 writes DEP0190 deprecation warnings to stderr. Claude Code treats ANY stderr as a "hook error" even when hooks succeed.

**Fix**: Add `--no-deprecation` flag to all `node` commands in plugin `hooks.json` files:

```bash
# Before (causes error):
"command": "node \"${CLAUDE_PLUGIN_ROOT}/scripts/script.js\" 2>/dev/null"

# After (no stderr):
"command": "node --no-deprecation \"${CLAUDE_PLUGIN_ROOT}/scripts/script.js\" 2>/dev/null"
```

**Affected plugins**:
- `claude-mem` (marketplaces/thedotmack/plugin/hooks/hooks.json)
- Any plugin using Node.js hooks

**Verification**:
```bash
# Test without flag - produces DEP0190 warning
node "path/to/script.js" 2>&1

# Test with flag - no stderr
node --no-deprecation "path/to/script.js" 2>&1
```

**Note**: The `2>/dev/null` redirection alone is insufficient because the deprecation warning comes from Node.js itself at startup, before shell redirection takes full effect.

### JSON Input Validation (hook_runner.py)

The `hook_runner.py` wrapper validates JSON input from Claude Code before passing it to hooks. This protects all hooks from malformed JSON (e.g., unescaped backslashes in Windows paths).

**Behavior:**
- Invalid JSON → replaced with `{}` (empty object)
- Hook executes without crashing
- No error logged (graceful degradation)

**Why this matters:** Claude Code sometimes passes tool results containing unescaped backslashes (Windows paths, escape sequences in error messages). Without validation, `json.loads()` fails and hooks crash.

**Defense in depth:** Individual hooks can still add their own try/except around `json.loads()` for additional safety.

---

## Modern Community Patterns

Best practices from the Claude Code community:

| Pattern                      | Description                                                                              |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| **UV Single-File Scripts**   | Use `# /// script` metadata for self-contained dependencies                              |
| **Typed Frameworks**         | [johnlindquist/claude-hooks](https://github.com/johnlindquist/claude-hooks) (TypeScript) |
| **Git Checkpointing**        | Auto-stash in `PostToolUse` for instant rollback                                         |
| **Shadow Mode**              | Run hooks in "log-only" before enabling blocking                                         |
| **Notification Integration** | Pipe to ntfy.sh, Slack, or Discord                                                       |

---

## Resources

- **[Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery)** — Comprehensive hook patterns
- **[Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code)** — Curated community list
- **[Local Protocol](file:///P:/.claude/hooks/PROTOCOL.md)** — I/O specifications for this workspace
- **[Hook Sitrep](file:///P:/.claude/hooks/HOOK_FIXES_SITREP.md)** — Current status and fixes

---

## Evidence & Confidence

| Hook                    | Evidence Tier          | Confidence |
| ----------------------- | ---------------------- | ---------- |
| Skill Enforcement       | 2 (empirical testing)  | 85%        |
| *(Drift Detector — removed)* | — | — |
| Investigation Gate      | 3 (logical derivation) | 75%        |
| Failure Escalation      | 3 (logical derivation) | 70%        |
| Change Propagation      | 3 (pattern analysis)   | 75%        |
| Concern Detection       | 3 (pattern analysis)   | 70%        |
| Success Validator       | 4 (untested)           | 50%        |
| Reality Check           | 3 (pattern analysis)   | 70%        |
| Overconfidence Detector | 2 (empirical testing)  | 80%        |
| Sycophancy Agreement    | 3 (pattern analysis)   | 70%        |
| Speculation Gate        | 2 (empirical testing)  | 80%        |

---

## Limitations

1. **Pattern-based detection** — May miss novel failure patterns
2. **State persistence** — Requires file system access between calls
3. **False positives** — May block legitimate quick fixes
4. **Escape hatches** — Declarations can be made without genuine understanding
5. **Prompt hooks run every time** — No throttling for `type: "prompt"` hooks (Drift Detector removed for this reason)

---

_Last updated: 2026-02-12 | Framework: Cognitive Steering Framework (CSF)_

---

## Changelog

### 2026-02-05: Comprehensive Hook Catalog Update
- Added complete hook inventory (60 hooks) from settings.json
- Organized hooks by event type (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, PreCompact, Notification)
- Updated environment variables section with all settings from settings.json
- Added comprehensive documentation for Skill Enforcement v3.2 with PostToolUse tracking
- Added TDD Enforcement documentation
- Added Contract System documentation
- Added Task Detection & Tracking documentation
- Added Evidence & Claim Tracking documentation
- Added File System Operations documentation
- Added Code Quality & Validation documentation
- Added Shell Command Safety documentation
- Added Investigation & Speculation Detection documentation
- Added CKS Integration documentation
- Added Session Management documentation
- Added Skill Routing documentation
- Added System Monitoring documentation
- Added /v Skill Tracking documentation
- Added Context & Compaction documentation
- Fixed Hook JSON validation error in assumption_audit_v2.py (decision value mapping: "allow" → "approve")

See [CHANGELOG.md](CHANGELOG.md) for detailed migration history.

### 2026-02-12: Meta-Conversation Gate Enhancement
- **Enhanced** `is_self_referential()` in `__lib/shared_helpers.py` with process/self-report patterns:
  - TDD/process: "I did not use TDD", "I only ran py_compile"
  - File operations: "I created X", "I modified Y hooks"
  - Testing status: "I haven't written tests yet", "no tests yet"
- **Updated** `StopHook_cross_validator.py` gate logic:
  - Now distinguishes meta-conversation from external claims
  - Process descriptions skip verification (e.g., "I didn't use TDD")
  - External claims still require evidence (e.g., "The fix works")
  - Added EXTERNAL_CLAIM_PATTERNS for verification triggers
- **Updated** documentation: HOOKS_BEHAVIOR_GRAPH.md, README.md
- **Rationale**: Prevent false blocks when user asks about implementation process
