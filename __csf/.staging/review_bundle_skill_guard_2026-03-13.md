# Review Bundle: skill-guard System

**Generated**: 2026-03-13
**Scope**: `packages/skill-guard/` + hook integrations
**File Count**: 234 files (30 core package files + 16 tests + 188 hook integrations)
**Execution Mode**: 4 parallel agents (comprehensive analysis)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

- **System Type**: Python library (NOT a user-facing skill)
- **Primary Purpose**: Universal skill execution enforcement with breadcrumb-based verification
- **Version**: 1.0.0 (production/stable)
- **Python Support**: 3.10-3.13
- **License**: MIT

### Domain & Purpose

**skill-guard** is a backend Python library used internally by Claude Code hooks to enforce skill execution patterns. When users invoke skills (e.g., `/code`, `/package`), skill-guard ensures those skills follow their documented workflows through a breadcrumb tracking system.

**Critical for**: Ensuring skills are invoked correctly, preventing shortcut-taking, and providing self-verification capabilities for skills.

**Key distinction**: This is NOT a user-facing command. Users cannot invoke `/skill-guard`. It is a library imported by hooks.

### Scale Metrics

- **Lines of Code**: ~3,500 LOC (core package)
- **Test Coverage**: 16 test files, 10 passing, 36% coverage
- **Major Subsystems**: 3 (Auto-discovery, Breadcrumb Tracking, Enforcement)
- **Hook Integrations**: 30+ hooks import skill-guard APIs
- **Deployment Scope**: Local development environment only
- **Change Frequency**: Active development (recent security fixes in March 2026)

### Your Environment

- **OS**: Windows 11 Pro (primary), Linux-compatible
- **Languages**: Python 3.10+
- **Package Managers**: pip (editable install), pyproject.toml
- **External Dependencies**: pyyaml only
- **State Storage**: Local file system (`P:/.claude/state/`)
- **No Network Dependencies**: Fully offline operation

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INVOCATION                              │
│                   /code or /package                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              UserPromptSubmit Hook                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ process_prompt_for_breadcrumbs()                         │  │
│  │   → Detect skill invocation pattern                      │  │
│  │   → detect_terminal_id()                                 │  │
│  │   → initialize_breadcrumb_trail(skill_name)              │  │
│  │   → Write pending_command_intent state file              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PreToolUse Hook (Layer 0)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ _load_workflow_steps(skill_name)                         │  │
│  │   → Parse SKILL.md frontmatter                           │  │
│  │   → Check if workflow_steps defined                      │  │
│  │   → Block if first tool ≠ Skill                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PreToolUse Hook (Pattern Gate)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ get_skill_config(skill_name, registry)                   │  │
│  │   → discover_all_skills() [auto-discovery]               │  │
│  │   → Check allowed_first_tools from frontmatter           │  │
│  │   → Validate first tool matches pattern                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Skill Execution (via Skill tool)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PostToolUse Hook (Breadcrumb Tracker)                    │  │
│  │   → infer_step_from_tool_use(tool_name, tool_input)      │  │
│  │   → set_breadcrumb(skill_name, step_name)                │  │
│  │   → Append to JSONL log (append-only)                    │  │
│  │   → Update in-memory cache                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stop Hook (Completion Check)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ verify_breadcrumb_trail(skill_name)                      │  │
│  │   → get_enforcement_level(skill_name)                    │  │
│  │   → verify_with_enforcement()                            │  │
│  │   → MINIMAL: duration >10s, tools ≥2                     │  │
│  │   → STANDARD: + ≥2 phases + verification step            │  │
│  │   → STRICT: ALL workflow_steps must complete             │  │
│  │   → Block/warn if incomplete                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              SessionEnd/PreCompact Hooks                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ cleanup_session_breadcrumbs()                            │  │
│  │   → Remove all trails for this terminal                  │  │
│  │ cleanup_stale_breadcrumbs()                              │  │
│  │   → Remove trails >2 hours old                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. Auto-Discovery System (`skill_auto_discovery.py`)

**Purpose**: Dynamically discover all skills from `P:/.claude/skills/*/SKILL.md` without manual registration.

**Files**: `src/skill_guard/skill_auto_discovery.py`

**Key Functions**:
- `discover_all_skills(skills_dir)`: Scans SKILL.md files, extracts YAML frontmatter
- `get_skill_config(skill_name, explicit_registry)`: Returns config with 4-priority fallback
- `_parse_skill_frontmatter(skill_md)`: Parses YAML between `---` markers

**Dependencies**: Standard library only (re, pathlib, typing)

**Data Structure**:
```python
{
    "skill_name": {
        "name": "skill_name",
        "category": "development|knowledge|meta",
        "has_execution": True|False,
        "allowed_first_tools": ["Bash", "Skill"],
        "default_tools": ["Bash"]
    }
}
```

**Critical Invariants**:
- Knowledge skills (reference-only) are exempt from enforcement
- Explicit SKILL_EXECUTION_REGISTRY takes priority over frontmatter
- Category defaults applied if no frontmatter exists

#### 2. Breadcrumb Tracking System (`breadcrumb/`)

**Purpose**: Terminal-scoped workflow progress tracking with hybrid logging (cache + append-only log + JSON snapshot).

**Files**:
- `tracker.py`: Core breadcrumb operations
- `cache.py`: In-memory cache with lazy loading
- `log.py`: Append-only JSONL log
- `enforcement.py`: Tiered verification logic
- `inference.py`: Tool-to-step inference

**Key Functions**:
- `initialize_breadcrumb_trail(skill_name)`: Creates trail from workflow_steps
- `set_breadcrumb(skill_name, step_name)`: Marks step complete
- `get_breadcrumb_trail(skill_name)`: Retrieves trail with session isolation
- `verify_breadcrumb_trail(skill_name)`: Verifies completion using enforcement levels

**Trail Data Structure**:
```python
{
    "skill": str,
    "terminal_id": str,  # Multi-terminal isolation
    "initialized_at": float,
    "workflow_steps": list[str],  # From SKILL.md
    "completed_steps": list[str],
    "current_step": str | None,
    "last_updated": float,
    "tool_count": int
}
```

**Hybrid Logging Architecture**:
1. **AppendOnlyBreadcrumbLog**: JSONL audit trail (crash-safe)
2. **BreadcrumbStateCache**: In-memory cache with LRU eviction (lazy loading from log)
3. **JSON snapshot**: Backward compatibility file

**Dependencies**: `cache.py` depends on `log.py` and `terminal_detection`

**Critical Invariants**:
- Terminal-scoped state (NOT session-scoped - session_id changes during compaction)
- Path traversal protection (blocks `..` and `.`)
- Max trail age: 2 hours (configurable via MAX_TRAIL_AGE_SECONDS)
- Cache key format: `{skill_name}:terminal:{terminal_id}`

#### 3. Enforcement System (`enforcement.py`)

**Purpose**: Three-tier verification for breadcrumb completion (MINIMAL, STANDARD, STRICT).

**Files**: `src/skill_guard/breadcrumb/enforcement.py`

**Enforcement Levels**:

1. **MINIMAL** (fastest, least friction):
   - Duration > 10 seconds
   - Tool count ≥ 2
   - Use case: Simple refactoring skills

2. **STANDARD** (default, balanced):
   - MINIMAL checks
   - ≥2 workflow phases completed
   - Verification step present
   - Use case: Most skills (code review, feature development)

3. **STRICT** (maximum verification):
   - ALL workflow_steps must complete
   - Use case: Critical skills (deployment, migration)

**Key Functions**:
- `get_enforcement_level(skill_name)`: Checks env var → SKILL.md frontmatter → default
- `verify_with_enforcement(skill_name, trail, duration, tool_count)`: Main entry point

**Configuration Override**: `BREADCRUMB_ENFORCEMENT_LEVEL` environment variable

**Dependencies**: None (standalone module)

**Critical Invariants**:
- Verification keywords: "verify", "check", "validate", "test", "review"
- Environment variable overrides SKILL.md frontmatter
- Defaults to STANDARD if not specified

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### Sequence 1: Skill Invocation Flow

```
1. User types: /code implement feature X
   ↓
2. UserPromptSubmit hook triggers
   ↓
3. process_prompt_for_breadcrumbs() detects "/code" pattern
   ↓
4. detect_terminal_id() returns "console_abc123..."
   ↓
5. _load_workflow_steps("code") reads SKILL.md:
   - workflow_steps: [requirements_clarity_check, ..., done_final_certification]
   ↓
6. initialize_breadcrumb_trail("code") creates state:
   P:/.claude/state/breadcrumbs_console_abc123/code.json
   {
     "skill": "code",
     "workflow_steps": [...13 steps...],
     "completed_steps": [],
     "terminal_id": "console_abc123..."
   }
   ↓
7. Write pending_command_intent state file:
   P:/.claude/state/pending_command_intent.json
   {
     "skill": "code",
     "prompt": "/code implement feature X",
     "timestamp": "2026-03-13T..."
   }
```

#### Sequence 2: Layer 0 Enforcement (First-Tool Gating)

```
1. PreToolUse hook fires before first tool use
   ↓
2. Read pending_command_intent state file
   ↓
3. Check if workflow_steps defined for "code"
   ↓
4. IF workflow_steps exist:
      - Block if tool_name ≠ "Skill"
      - Hint: "Use /code via its documented workflow (Skill tool first)"
   ↓
5. ELSE:
      - Allow tool use (no enforcement for skills without workflow_steps)
```

#### Sequence 3: Breadcrumb Tracking During Execution

```
1. PostToolUse hook fires after each tool use
   ↓
2. infer_step_from_tool_use("Read", {"file_path": "test.py"})
   → Returns: "requirements"
   ↓
3. set_breadcrumb("code", "requirements")
   ↓
4. Update in-memory cache (BreadcrumbStateCache)
   ↓
5. Append to JSONL log:
   P:/.claude/state/breadcrumb_logs_console_abc123/code.jsonl
   {"timestamp": 1234567890.123, "event": "step_complete", "step": "requirements_clarity_check", "skill": "code"}
   ↓
6. Periodic snapshot (every 30 seconds):
   - Write all cached states to disk
   - Throttled by SNAPSHOT_INTERVAL
```

#### Sequence 4: Completion Verification

```
1. Stop hook fires when skill execution completes
   ↓
2. verify_breadcrumb_trail("code")
   ↓
3. get_breadcrumb_trail("code") retrieves trail
   ↓
4. get_enforcement_level("code") → STANDARD
   ↓
5. verify_with_enforcement("code", trail, duration=45.0, tool_count=8)
   ↓
6. Check MINIMAL requirements:
   - duration 45s > 10s ✓
   - tool_count 8 ≥ 2 ✓
   ↓
7. Check STANDARD requirements:
   - completed_steps: 8/13 ✓ (≥2 phases)
   - has_verification_step: True ✓ (done_final_certification)
   ↓
8. Return: (True, "All STANDARD requirements met")
```

### Mandatory Ordering Constraints

1. **Skill invocation → Terminal detection**: Must detect terminal ID before initializing breadcrumbs
2. **Pending intent → First tool**: Must read pending_command_intent before enforcing first-tool gate
3. **Breadcrumb init → Tool use**: Must initialize trail before setting breadcrumbs
4. **Log append → Cache update**: Must append to log before updating cache (crash safety)
5. **Verification → Completion**: Must verify breadcrumbs before allowing skill completion

### State Management

**State Stores**:
1. **In-Memory Cache**: `BreadcrumbStateCache` (LRU, max 100 entries)
2. **Append-Only Log**: JSONL files (crash-safe, rotates at 1MB)
3. **JSON Snapshots**: Backward compatibility (legacy format)
4. **Pending Intent**: `pending_command_intent.json` (Layer 0 enforcement)

**State Ownership**:
- **Breadcrumb state**: Owned by terminal (not session - changes during compaction)
- **Cache keys**: Format `{skill_name}:terminal:{terminal_id}`
- **Log files**: Terminal-scoped subdirectories (`breadcrumb_logs_{terminal_id}/`)

**Consistency Model**:
- **Write-ahead logging**: Log append happens before cache update
- **Lazy loading**: Cache loads from log on miss
- **Atomic operations**: Thread-safe with RLock
- **Eventual consistency**: Snapshots written every 30 seconds

**Isolation Boundaries**:
- **Terminal isolation**: Each terminal has separate state directory
- **Session isolation**: Verified via terminal_id (not session_id)
- **Path traversal protection**: Blocks `..` and `.` in skill names

### Error Handling

**Fail-Open vs Fail-Closed Policy**:
- **Terminal ID detection**: Fail-open (returns "" if undetectable)
- **Breadcrumb verification**: Fail-closed (blocks if incomplete in STRICT mode)
- **Frontmatter parsing**: Fail-open (returns empty dict if SKILL.md missing)
- **Log replay**: Skip malformed lines (don't crash on corruption)

**Retry Behavior**:
- **No retry logic**: All operations are synchronous and immediate
- **State cleanup**: Automatic cleanup on SessionEnd and PreCompact

**Timeout Behavior**:
- **No timeouts**: All operations are local file I/O (no network)
- **Age-based cleanup**: Trails >2 hours old are removed automatically

---

## 4. COMPONENT INVENTORY

### Core Logic Components

| Component | Path | Responsibility | Inputs | Outputs | Known Limitations |
|-----------|------|----------------|--------|---------|-------------------|
| Auto-Discovery | `skill_auto_discovery.py` | Discover skills from SKILL.md | Skills directory path | Dict of skill configs | Requires SKILL.md files to exist |
| Skill Config | `get_skill_config()` | Get skill config with fallback | Skill name, explicit registry | Config dict | 4-priority fallback complex |
| Knowledge Skills | `KNOWLEDGE_SKILLS` constant | List exempt reference skills | N/A | Set of 15 skill names | Hardcoded, requires manual updates |
| Breadcrumb Init | `initialize_breadcrumb_trail()` | Create trail from workflow_steps | Skill name | Trail state file | Requires workflow_steps in SKILL.md |
| Breadcrumb Set | `set_breadcrumb()` | Mark workflow step complete | Skill name, step name | Updated trail + log entry | Invalid step names rejected |
| Breadcrumb Get | `get_breadcrumb_trail()` | Retrieve trail with isolation | Skill name | Trail dict or None | Returns None if no trail exists |
| Breadcrumb Verify | `verify_breadcrumb_trail()` | Verify completion with tiers | Skill name | (bool, message) tuple | Enforcement level must be valid |
| Enforcement Level | `get_enforcement_level()` | Detect enforcement level | Skill name | MINIMAL/STANDARD/STRICT | Env var overrides SKILL.md |
| Tiered Verify | `verify_with_enforcement()` | Apply tier-specific checks | Skill, trail, duration, tools | (bool, message) tuple | Duration/tool counts required |
| Tool Inference | `infer_step_from_tool_use()` | Map tools to workflow steps | Tool name, tool input | Step name or None | Covers 60+ tools, not exhaustive |
| Terminal Detect | `detect_terminal_id()` | Get terminal ID for isolation | None | Terminal ID string | Returns "" if undetectable |
| Cache Manager | `BreadcrumbStateCache` | In-memory cache with lazy loading | Skill name | Trail dict or None | Max 100 entries, LRU eviction |
| Log Manager | `AppendOnlyBreadcrumbLog` | Append-only JSONL log | Entry dict | None | Rotates at 1MB threshold |

### Utilities/Helpers

| Component | Path | Responsibility | Known Limitations |
|-----------|------|----------------|-------------------|
| Terminal Detection | `utils/terminal_detection.py` | Multi-terminal ID detection | Windows-only GetConsoleWindow(), falls back to env vars |
| Path Normalization | `_normalize_id()` | Consistent terminal ID format | Assumes specific ID sources |
| State File Cleanup | `cleanup_session_breadcrumbs()` | Remove trails for terminal | Only removes for current terminal |
| Stale Cleanup | `cleanup_stale_breadcrumbs()` | Remove trails >2 hours old | Age threshold hardcoded (MAX_TRAIL_AGE_SECONDS) |
| Session Isolation | `verify_session_isolation()` | Check terminal_id matches | Only checks terminal_id (not session_id) |

### Configuration Components

| Component | Path | Responsibility | Values |
|-----------|------|----------------|--------|
| Environment Variables | System env | Global configuration override | `BREADCRUMB_ENFORCEMENT_LEVEL`, `SKILL_PATTERN_ENFORCEMENT_ENABLED`, etc. |
| SKILL.md Frontmatter | `P:/.claude/skills/*/SKILL.md` | Skill-specific configuration | `workflow_steps`, `enforcement_level`, `allowed_first_tools` |
| Constants | Module-level | Default values and thresholds | `MAX_TRAIL_AGE_SECONDS = 7200`, `MAX_CACHE_SIZE = 100`, etc. |

### Infrastructure Components

| Component | Path | Responsibility | Known Limitations |
|-----------|------|----------------|-------------------|
| State Directory | `P:/.claude/state/` | Persistent state storage | Windows-specific path (hardcoded) |
| Breadcrumb Logs | `breadcrumb_logs_{terminal_id}/` | Append-only audit trail | Terminal-scoped, no session scope |
| Breadcrumb State | `breadcrumbs_{terminal_id}/` | Trail state files | Terminal-scoped, no session scope |
| Skill Execution State | `skill_execution_{terminal_id}/` | Execution tracking | Legacy format, partially replaced |
| Hook Ledger | `.claude/hooks/__lib/hook_ledger.py` | Event-based state storage | External dependency, optional |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Enforcement Over Discovery**: Focus on ensuring correct skill usage, not just finding skills
2. **Breadcrumb-Based Tracking**: Track execution flow for verification and debugging
3. **Terminal Isolation**: Multi-terminal safety (5+ concurrent sessions)
4. **Backwards Compatibility**: Explicit SKILL_EXECUTION_REGISTRY still works
5. **Fail Clear**: Provide helpful error messages when enforcement blocks execution
6. **Explicit First**: Frontmatter declarations beat automatic detection

### Technology Constraints

1. **Python 3.10+ Only**: No support for Python <3.10
2. **Windows-First**: Terminal detection uses Windows-specific APIs (GetConsoleWindow)
3. **Local File System Only**: No network dependencies, no external APIs
4. **YAML Frontmatter Required**: SKILL.md files must have valid YAML between `---` markers
5. **State Directory Required**: `P:/.claude/state/` must exist and be writable

### Performance SLAs

- **Log Replay**: <100ms for 1000 entries
- **Memory Usage**: <10MB for 500 operations
- **Write Performance**: <10ms average per write
- **Concurrent Access**: 300 entries in <1000ms

### Things That Must NOT Change

1. **Terminal-Scoped State**: State MUST be scoped by terminal_id, not session_id (session_id changes during compaction)
2. **Append-Only Log**: Log MUST be append-only for crash safety (no in-place modifications)
3. **Path Traversal Protection**: MUST block `..` and `.` in skill names (security fix)
4. **Knowledge Skills Exemption**: Reference-only skills MUST NOT be enforced
5. **Three-Tier Enforcement**: MINIMAL/STANDARD/STRICT levels MUST remain (configurable via frontmatter)
6. **Fail-Open on Terminal Detection**: If terminal ID undetectable, return "" (don't crash)
7. **Layer 0 First-Tool Gating**: Skills with workflow_steps MUST use Skill tool first

---

## 6. KNOWN ISSUES

### Issue #1: Security Vulnerability - Path Traversal (FIXED)

**Scenario**: Malicious skill name with `..` or `.` could access arbitrary files

**Expected vs Actual**:
- Expected: Block skill names with path traversal sequences
- Actual (before fix): Allowed `../etc/passwd` as skill name

**Impact**: HIGH - Could read arbitrary files from file system

**Current Workaround**: Fixed in `tracker.py` - path traversal protection now blocks `..` and `.`

**Fix Location**: `test_tracker_fixes.py` - Issue #2

---

### Issue #2: Import Path Inconsistency (FIXED)

**Scenario**: Module imports from `utils` instead of `utils` submodule

**Expected vs Actual**:
- Expected: Import from `skill_guard.utils.terminal_detection`
- Actual (before fix): Tried fallback import, violated submodule structure

**Impact**: MEDIUM - Import failures, inconsistent behavior

**Current Workaround**: Fixed - now imports from `utils.terminal_detection` directly

**Fix Location**: `test_tracker_fixes.py` - Issue #1

---

### Issue #3: sys.path Manipulation (FIXED)

**Scenario**: Module manipulates `sys.path` on import

**Expected vs Actual**:
- Expected: No sys.path modifications
- Actual (before fix): Added parent directory to sys.path

**Impact**: MEDIUM - Side effects on import, potential conflicts

**Current Workaround**: Fixed - no sys.path manipulation

**Fix Location**: `test_tracker_fixes.py` - Issue #3

---

### Issue #4: Disk I/O on Import (FIXED)

**Scenario**: Module performs file I/O during import

**Expected vs Actual**:
- Expected: Lazy loading (I/O on first use)
- Actual (before fix): File I/O happened at import time

**Impact**: LOW - Performance degradation on import

**Current Workaround**: Fixed - now uses lazy loading via cache

**Fix Location**: `test_tracker_fixes.py` - Issue #4

---

### Issue #5: Documentation Contradiction (FIXED)

**Scenario**: MAX_TRAIL_AGE_SECONDS documented incorrectly

**Expected vs Actual**:
- Expected: Consistent documentation and code
- Actual (before fix): Docs said 3600s, code used 7200s

**Impact**: LOW - Confusion about cleanup behavior

**Current Workaround**: Fixed - documentation now matches code (7200s = 2 hours)

**Fix Location**: `test_tracker_fixes.py` - Issue #5

---

### Issue #6: Test Coverage Gap (ONGOING)

**Scenario**: Coverage at 36%, below 80% target

**Expected vs Actual**:
- Expected: >80% test coverage
- Actual: 36% coverage (10 passing tests)

**Impact**: MEDIUM - Risk of regressions in untested code

**Current Workaround**: Manual testing, regression tests in place

**Next Steps**: Increase test coverage to meet 80% target

---

### Issue #7: Windows-Specific Terminal Detection (DESIGN LIMITATION)

**Scenario**: Terminal detection fails on non-Windows platforms

**Expected vs Actual**:
- Expected: Cross-platform terminal detection
- Actual: Uses Windows-specific GetConsoleWindow() API

**Impact**: MEDIUM - Limited functionality on Linux/macOS

**Current Workaround**: Falls back to environment variables

**Design Constraint**: Windows-first development environment

---

### Issue #8: Hardcoded Knowledge Skills List (MAINTENANCE BURDEN)

**Scenario**: New knowledge skills must be manually added to KNOWLEDGE_SKILLS set

**Expected vs Actual**:
- Expected: Automatic detection of knowledge skills
- Actual: Hardcoded set of 15 skill names

**Impact**: LOW - Manual updates required when adding skills

**Current Workaround**: Manually add new knowledge skills to the set

**Future Improvement**: Auto-detect from `category: knowledge` frontmatter

---

### Issue #9: Session ID Changes During Compaction (ARCHITECTURAL CONSTRAINT)

**Scenario**: Session ID not usable for isolation (changes during compaction)

**Expected vs Actual**:
- Expected: Session-scoped state isolation
- Actual: Only terminal ID is stable (session_id changes)

**Impact**: LOW - Must use terminal_id instead of session_id

**Current Workaround**: All state is terminal-scoped, not session-scoped

**Design Rationale**: Session ID changes during context compaction, terminal ID remains stable

---

## 7. INTEGRATION POINTS

### Existing Hooks/Interfaces

**Primary Integration Hooks**:

1. **PreToolUse_skill_pattern_gate.py**
   - Imports: `get_skill_config`, `_load_workflow_steps`
   - Purpose: Universal skill enforcement (first-tool gating)
   - Invocation: Automatic on every PreToolUse event
   - Data Exchange: Reads pending_command_intent state file
   - Output: Blocks or allows tool use with hint message

2. **PreToolUse_workflow_steps_gate.py**
   - Imports: `_load_workflow_steps`
   - Purpose: Layer 0 enforcement (workflow_steps blocking)
   - Invocation: Automatic on every PreToolUse event
   - Data Exchange: Reads SKILL.md frontmatter
   - Output: Blocks if first tool ≠ Skill

3. **StopHook_breadcrumb_verifier.py**
   - Imports: `get_breadcrumb_trail`, `verify_breadcrumb_trail`
   - Purpose: Completion verification before skill exit
   - Invocation: Automatic on Stop event
   - Data Exchange: Reads breadcrumb trail, gets enforcement level
   - Output: Warning or block message

4. **UserPromptSubmit_breadcrumb_init.py**
   - Imports: `process_prompt_for_breadcrumbs`
   - Purpose: Auto-initialize breadcrumb trails on skill invocation
   - Invocation: Automatic on UserPromptSubmit event
   - Data Exchange: Parses user prompt for `/skill-name` pattern
   - Output: Initializes trail, writes pending_command_intent

5. **PostToolUse_breadcrumb_tracker.py**
   - Imports: `run` (from skill-guard package)
   - Purpose: Auto-track workflow steps from tool usage
   - Invocation: Automatic on PostToolUse event
   - Data Exchange: Tool name and input
   - Output: Updates breadcrumb trail, appends to log

6. **SessionEnd_breadcrumb_cleanup.py**
   - Imports: `cleanup_session_breadcrumbs`
   - Purpose: Clean up trails for terminal on session end
   - Invocation: Automatic on SessionEnd event
   - Data Exchange: Terminal ID
   - Output: Removes all breadcrumb state for terminal

7. **PreCompact_breadcrumb_cleanup.py**
   - Imports: `cleanup_stale_breadcrumbs`
   - Purpose: Clean up old trails (>2 hours)
   - Invocation: Automatic on PreCompact event
   - Data Exchange: None (scans all trails)
   - Output: Removes stale breadcrumb state

8. **SessionStart_task_identity.py**
   - Imports: `detect_terminal_id`
   - Purpose: Write terminal-specific state file
   - Invocation: Automatic on SessionStart event
   - Data Exchange: Terminal ID, timestamp
   - Output: Creates `terminal_{handle}.json` state file

### Invocation Model

**Automatic Hook Invocation**:
- All hooks are invoked automatically by Claude Code
- No manual invocation required
- Hooks import skill-guard modules and call functions directly

**Skill Invocation Flow**:
1. User types `/code` (or any skill name)
2. UserPromptSubmit hook detects pattern
3. PreToolUse hooks enforce first-tool gating
4. PostToolUse hooks track workflow steps
5. Stop hook verifies completion
6. SessionEnd/PreCompact hooks clean up

### Data Exchange Contracts

**Input Format** (from hooks to skill-guard):
```python
# UserPromptSubmit input
{
    "prompt": "/code implement feature X",
    "model": "claude-sonnet-4-6",
    ...
}

# PreToolUse input
{
    "tool_name": "Skill",
    "tool_input": {...},
    "pending_command_intent": {...}
}

# PostToolUse input
{
    "tool_name": "Read",
    "tool_input": {"file_path": "test.py"},
    ...
}
```

**Output Format** (from skill-guard to hooks):
```python
# Breadcrumb trail output
{
    "skill": "code",
    "workflow_steps": [...],
    "completed_steps": [...],
    "terminal_id": "console_abc123...",
    ...
}

# Verification output
(True, "All STANDARD requirements met")
# or
(False, "Incomplete: missing verification step")

# Skill config output
{
    "tools": ["Bash", "Skill"],
    "pattern": "run_heavy.py",
    "hint": "Use /code via its documented workflow",
    "discovered": True
}
```

### Output/Exit Code Expectations

**Hook Return Values**:
- **Allow**: Return empty dict or `{}` (no blocking)
- **Block**: Return `{"block": True, "reason": "..."}` (blocks tool use)
- **Warning**: Return `{"warning": "..."}` (shows warning but allows)
- **Error**: Return `{"error": "..."}` (shows error message)

**Exit Codes**:
- **Success**: 0 (operation completed)
- **Failure**: 1 (operation failed, blocked, or errored)

**No Exception Propagation**:
- skill-guard functions catch and log exceptions
- Return error messages in output dict
- Hooks handle errors gracefully (fail-open or fail-closed based on context)

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample Run 1: Complete Skill Workflow (SUCCESS)

```
# User invokes /code skill
User> /code implement feature X

# UserPromptSubmit hook initializes breadcrumb
[DEBUG] process_prompt_for_breadcrumbs: Detected skill invocation: /code
[DEBUG] detect_terminal_id: terminal_id = console_abc123...
[DEBUG] _load_workflow_steps: Loaded 13 steps from /code SKILL.md
[DEBUG] initialize_breadcrumb_trail: Created trail at P:/.claude/state/breadcrumbs_console_abc123/code.json
[INFO] Wrote pending_command_intent: {"skill": "code", "prompt": "/code implement feature X"}

# PreToolUse hook enforces first-tool gating (Layer 0)
[DEBUG] PreToolUse_workflow_steps_gate: workflow_steps defined for /code
[DEBUG] PreToolUse_workflow_steps_gate: First tool = Skill ✓

# Skill execution begins (via Skill tool)
[INFO] Skill tool invoked: /code

# PostToolUse hook tracks workflow steps
[DEBUG] infer_step_from_tool_use(Read, ...) → requirements
[DEBUG] set_breadcrumb: Marked "requirements_clarity_check" complete
[DEBUG] set_breadcrumb: Marked "preflight_context_validation" complete
[DEBUG] set_breadcrumb: Marked "explore_codebase" complete
[DEBUG] infer_step_from_tool_use(Edit, ...) → tdd
[DEBUG] set_breadcrumb: Marked "design_solution" complete
[DEBUG] set_breadcrumb: Marked "tdd_implementation" complete
[DEBUG] set_breadcrumb: Marked "full_test_suite" complete
[DEBUG] infer_step_from_tool_use(Bash, pytest) → verification
[DEBUG] set_breadcrumb: Marked "audit_quality_checks" complete
[DEBUG] set_breadcrumb: Marked "trace_manual_verification" complete
[DEBUG] set_breadcrumb: Marked "done_final_certification" complete

# Stop hook verifies completion
[DEBUG] verify_breadcrumb_trail: Trail has 13/13 steps complete
[DEBUG] get_enforcement_level: STANDARD (from SKILL.md)
[DEBUG] verify_with_enforcement: Duration: 45.0s (>10s ✓), Tools: 8 (≥2 ✓)
[DEBUG] verify_with_enforcement: ≥2 workflow phases completed ✓
[DEBUG] verify_with_enforcement: Verification step present ✓
[INFO] Breadcrumb verification: PASSED
[INFO] All STANDARD requirements met

# Result: Skill execution allowed
```

### Sample Run 2: Incomplete Trail (BLOCKED - STRICT MODE)

```
# User invokes /deploy-production skill
User> /deploy-production

# UserPromptSubmit hook initializes breadcrumb
[DEBUG] process_prompt_for_breadcrumbs: Detected skill invocation: /deploy-production
[DEBUG] _load_workflow_steps: Loaded 7 steps from /deploy-production SKILL.md
[INFO] Wrote pending_command_intent: {"skill": "deploy-production"}

# Skill execution begins
[INFO] Skill tool invoked: /deploy-production

# PostToolUse hook tracks workflow steps
[DEBUG] set_breadcrumb: Marked "backup_database" complete
[DEBUG] set_breadcrumb: Marked "run_migrations" complete
[DEBUG] set_breadcrumb: Marked "deploy_code" complete

# Stop hook verifies completion
[DEBUG] verify_breadcrumb_trail: Trail has 3/7 steps complete
[DEBUG] get_enforcement_level: STRICT (from SKILL.md enforcement_level)
[DEBUG] verify_with_enforcement: Missing steps: smoke_tests, monitor_rollout, rollback_on_failure
[ERROR] Breadcrumb verification: FAILED
[ERROR] STRICT mode requires ALL workflow_steps to complete
[ERROR] Missing steps: smoke_tests, monitor_rollout, rollback_on_failure

# Result: Skill execution BLOCKED
[ BLOCK ] Incomplete deployment workflow. Required steps not completed:
          - smoke_tests
          - monitor_rollover
          - rollback_on_failure
          Deployment blocked for safety.
```

### Sample Run 3: First-Tool Gating Violation (BLOCKED)

```
# User invokes /code skill but tries to use Edit tool first
User> /code
Assistant> I'll help you implement that feature. Let me read the file first.

# PreToolUse hook enforces first-tool gating
[DEBUG] PreToolUse_workflow_steps_gate: workflow_steps defined for /code
[DEBUG] PreToolUse_workflow_steps_gate: First tool = Read (expected Skill)
[ERROR] First-tool gating: BLOCKED
[ERROR] /code skill requires Skill tool to be used first
[ERROR] Hint: Invoke /code via its documented workflow (Skill tool first)

# Result: Tool use BLOCKED
[ BLOCK ] /code skill has defined workflow_steps, which requires the Skill tool to be used first.
          This ensures the skill follows its documented workflow.
          First tool used: Read
          Expected first tool: Skill
          Hint: Use /code via its documented workflow (Skill tool first)
```

### Sample Run 4: Multi-Terminal Isolation (SUCCESS)

```
# Terminal A: User invokes /code
Terminal A> /code implement feature X
[DEBUG] detect_terminal_id: console_abc123...
[DEBUG] initialize_breadcrumb_trail: Created trail for /code
[INFO] Terminal A terminal_id = console_abc123...

# Terminal B: Concurrent user invokes /code
Terminal B> /code implement feature Y
[DEBUG] detect_terminal_id: console_xyz789...
[DEBUG] initialize_breadcrumb_trail: Created trail for /code
[INFO] Terminal B terminal_id = console_xyz789...

# Terminal A: Get breadcrumb trail
Terminal A> [DEBUG] get_breadcrumb_trail: Found trail with terminal_id = console_abc123...
[INFO] Terminal A can only see its own trail

# Terminal B: Get breadcrumb trail
Terminal B> [DEBUG] get_breadcrumb_trail: Found trail with terminal_id = console_xyz789...
[INFO] Terminal B can only see its own trail (isolated from Terminal A)

# Result: Complete isolation between terminals
```

### Sample Run 5: Log Rotation (SUCCESS)

```
# Write large log (exceeds 1MB threshold)
[DEBUG] AppendOnlyBreadcrumbLog: Writing entry to /code.jsonl
[DEBUG] Current log size: 900KB
[DEBUG] AppendOnlyBreadcrumbLog: Writing entry to /code.jsonl
[DEBUG] Current log size: 1050KB (> 1MB threshold)
[INFO] Rotating log: code.jsonl → code_20260313_153045.jsonl
[INFO] New log created: code.jsonl
[DEBUG] AppendOnlyBreadcrumbLog: Writing entry to /code.jsonl
[INFO] Entry written to new log file

# Result: Log rotated successfully, no data loss
```

---

## SUMMARY

**skill-guard** is a comprehensive skill execution enforcement system with:
- **Auto-discovery**: Universal skill discovery from SKILL.md frontmatter
- **Breadcrumb tracking**: Terminal-scoped workflow progress tracking
- **Tiered enforcement**: MINIMAL/STANDARD/STRICT verification levels
- **Multi-terminal safety**: Complete isolation between concurrent sessions
- **Performance**: <100ms replay, <10MB memory, <10ms writes
- **Integration**: 30+ hooks use skill-guard APIs
- **Security**: Path traversal protection, no network dependencies
- **Test coverage**: 16 test files, 10 passing, 36% coverage (target: 80%)

**Key architectural decisions**:
1. Terminal-scoped state (not session-scoped) due to compaction
2. Append-only logging for crash safety
3. Three-tier enforcement for flexibility
4. Knowledge skills exemption for reference-only skills
5. Layer 0 first-tool gating for skills with workflow_steps

**Known issues**: All security issues fixed, coverage gap remains, Windows-specific terminal detection

**Integration points**: Hooks import skill-guard modules and call functions directly, automatic invocation by Claude Code

---

**END OF REVIEW BUNDLE**
