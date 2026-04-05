# Review Bundle: Claude Configuration, Memory System, and Stop Hooks

**Generated**: 2026-03-05
**Scope**: CLAUDE.md, Memory System (auto-memory), Stop Hooks (router + gates)
**File Count**: ~30 files
**Execution Mode**: Single-agent (focused scope with prior exploration)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

This bundle covers the **foundational configuration and behavioral enforcement systems** for a Claude Code workspace:

- **CLAUDE.md** - Workspace root configuration (development model, coding standards, key commands)
- **Memory System** - Auto-memory with topic-based persistence (11 topic files + index)
- **Stop Hooks** - Response-time behavioral enforcement router with 13+ gates

### Domain & Purpose

**Purpose**: These systems form the constitutional governance layer for AI-assisted development, enforcing:

1. **Development Model Constraints** - Professional solo dev + AI workforce (NOT enterprise team bloat)
2. **Pattern Persistence** - Cross-session learning via topic-based memory files
3. **Behavioral Enforcement** - Stop-time gates prevent anti-patterns (unverified claims, sycophancy, safety violations)

**Who uses it**: All Claude Code sessions in the P:\ workspace automatically inherit these constraints via:
- System prompt injection (CLAUDE.md, MEMORY.md)
- Hook execution (Stop.py router invokes all gates)
- Memory loading (topic files loaded on-demand)

**Why it's critical**: These systems prevent recurring AI mistakes (dismissal of user reports, unverified claims, enterprise bloat patterns) and encode learned lessons from months of development.

### Scale Metrics

- **LOC**: ~3,000 lines (Stop hooks: ~1,800, Memory topics: ~1,200, CLAUDE.md: ~88)
- **Major subsystems**: 3 (Config, Memory, Behavioral Enforcement)
- **Deployment scope**: Workspace-wide (all sessions inherit)
- **Change frequency**: Medium (memory updated weekly, hooks updated monthly)

### Your Environment

- **OS and shell**: Windows 11, Bash (Git for Windows)
- **Primary languages**: Python 3.x (hooks), Markdown (documentation)
- **Package managers**: None (hooks use stdlib only)
- **Databases/external services**: None (memory is file-based JSONL/Markdown)

---

## 2. ARCHITECTURE OVERVIEW

### System Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION START                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CLAUDE.md    │  │ MEMORY.md    │  │ SessionStart │      │
│  │ (200 lines)  │  │ (200 lines)  │  │ hooks        │      │
│  │ → System     │  │ → System     │  │ → Init       │      │
│  │   Prompt     │  │   Prompt     │  │   Context    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSATION LOOP                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  User Prompt → AI Response → Tool Execution          │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              STOP HOOK ROUTER (Stop.py)               │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ IN-PROCESS GATES (direct function calls)        │  │  │
│  │  │ • safety_gate (secrets, forbidden patterns)    │  │  │
│  │  │ • behavior_audit (unverified claims)            │  │  │
│  │  │ • skill_first_stop_gate (/command enforcement)  │  │  │
│  │  │ • behavior_gates (agreement, guidance, tools)   │  │  │
│  │  │ • anti_sycophancy_quality (affirmation, etc.)   │  │  │
│  │  │ • advisory (next-step menu generation)          │  │  │
│  │  │ • reflect_integration (background reflection)    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                      ↓                                 │  │
│  │              Block or Allow?                           │  │
│  │                      ↓                                 │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ SIDE EFFECTS (subprocess, fire-and-forget)      │  │  │
│  │  │ • conversation_storage.py                       │  │  │
│  │  │ • auto_cks_storage.py                           │  │  │
│  │  │ • Stop_cks_decision_capture.py                  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 MEMORY SYSTEM (Auto-Memory)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Location: C:\Users\brsth\.claude\projects\P--\memory\ │  │
│  │                                                       │  │
│  │ Topic Files (loaded on-demand):                     │  │
│  │ • MEMORY.md (index, 200-line limit)                 │  │
│  │ • workflow_clarification.md (Director + AI model)    │  │
│  │ • bugfixes.md (historical fixes)                     │  │
│  │ • tool_usage_patterns.md (Edit validation, etc.)     │  │
│  │ • recruiter_perception.md (large file perception)    │  │
│  │ • memory_management.md (best practices)              │  │
│  │ • chutes_provider.md (API access)                    │  │
│  │ • aid_files.md (AI Distiller templates)              │  │
│  │ • working_principles.md (heuristics)                 │  │
│  │ • + 2 more specialized files                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Subsystem Details

#### CLAUDE.md (Workspace Configuration)

**Location**: `P:\CLAUDE.md`

**Purpose**: Root-level configuration inherited by all sessions

**Key sections**:
1. **Project Context** - Multi-purpose workspace for tooling/automation/AI workflows
2. **Development Model** - Professional solo dev + AI workforce (NOT enterprise team)
3. **Key Commands** - Python/npm/git conventions
4. **File Structure References** - `.claude/docs/` for Claude-generated content
5. **Python Code Standards** - Function length limits, `print()` for CLI tools
6. **Work Mode Preferences** - Slash commands, testing assumptions
7. **Token Efficiency** - Auto-memory location, topic file loading
8. **Code Analysis** - Serena skill preference for semantic analysis

**Critical constraints**:
- Line limit: 200 lines (first 200 loaded into system prompt)
- Updates: Human-authored only (Claude writes to `.claude/docs/` instead)
- Scope: Workspace-wide (all sessions inherit)

**Dependencies**: None (standalone configuration)

#### Memory System (Auto-Memory)

**Location**: `C:\Users\brsth\.claude\projects\P--\memory\`

**Purpose**: Persistent cross-session learning via topic-based files

**Architecture**:
- **Index file**: `MEMORY.md` (200 lines, loaded into system prompt)
- **Topic files**: 11 specialized `.md` files (loaded on-demand)
- **Access pattern**: Index references → topic file loaded when needed

**Topic file catalog**:

| File | Purpose | Key Content |
|------|---------|-------------|
| `MEMORY.md` | Index | 200-line summary, topic catalog, reading order |
| `workflow_clarification.md` | **READ FIRST** | Director + AI workforce model (what's appropriate) |
| `bugfixes.md` | Historical fixes | Compact matcher, daemon startup, stderr false positives |
| `tool_usage_patterns.md` | Tool-specific | Edit validation, router integration, test data |
| `recruiter_perception.md` | **CRITICAL for packages/** | Recruiter heuristics, large file perception |
| `working_principles.md` | Decision-making | Functional testing, biggest ROI, evidence over speculation |
| `memory_management.md` | **READ THIS** | Best practices for MEMORY.md, topic files, monitoring |
| `chutes_provider.md` | API access | User has full access to all Chutes models |
| `aid_files.md` | AI Distiller | Template files (single-file-docs.md, etc.) |
| `api_key_fix.md` | Bug history | API key resolution fix |
| `chutes_zai_separation_fix.md` | Bug history | Chutes/ZAI separation fix |
| `missing_discovery_patterns.md` | Bug history | Discovery pattern issues |

**State management**:
- Storage: File-based (Markdown + JSONL for logs)
- Isolation: Per-workspace (`P:\` workspace has its own memory)
- Consistency: Manual updates (no automatic synchronization)

**Critical invariants**:
1. **200-line limit** on MEMORY.md (enforced by system prompt truncation)
2. **Topic file focus** - Detailed content moved to topic files to keep index concise
3. **Reading order = Execution order** - Structure must match logical flow
4. **User authority** - User's direct report ALWAYS overrides cached state

**Dependencies**: None (file-based, no external services)

#### Stop Hooks (Behavioral Enforcement)

**Location**: `P:\.claude\hooks\Stop*.py`

**Purpose**: Response-time gates enforce constitutional constraints before AI output reaches user

**Architecture**: **Router pattern** (v3.0+ - In-process gate execution)

**Router file**: `Stop.py` (900 lines)

**Gate execution model**:
- **IN-PROCESS GATES** (13 gates): Direct function calls, ~300-500ms saved vs subprocess
- **SIDE EFFECTS** (3 hooks): Subprocess with ThreadPool for isolation (fire-and-forget)

**Blocking gate sequence** (evaluated in order, first block wins):

1. `safety_gate` - Secret/PII leakage, forbidden patterns (daemons, autonomous fixes)
2. `skill_first_stop_gate` - Block when `/command` typed but AI responded with prose only
3. `behavior_audit` - Unverified claims (Strategy A: tool-call evidence tracking)
4. `behavior_gates_agreement` - Block empty agreements without action tools
5. `behavior_gates_guidance` - Warn about guidance without Read verification
6. `behavior_gates_blacklist` - Warn about blacklisted tools
7. `narrative_intent` - Warn on un-hedged design-intent speculation
8. `challenge_requires_tool` - Block stance-taking on challenged claims without verification
9. `anti_sycophancy_quality` - Affirmation, overconfidence, lazy closure detection
10. `command_execution_validator` - Validate bash commands match user intent
11. `advisory` - Non-blocking suggestions + next-step menu generation
12. `reflect_integration` - Spawn background reflection
13. `cleanup_verifier` - Check for missing cleanup steps
14. `existence_gate` - **DISABLED** (Strategy B+C now handled by behavior_audit)

**Side effects** (run only if not blocked):
- `conversation_storage.py` - Log conversation for later analysis
- `auto_cks_storage.py` - Store lessons to Constitutional Knowledge System
- `Stop_cks_decision_capture.py` - Capture decisions for CKS

**Gate dependencies**:

| Gate | External Dependencies | Integration Points |
|------|----------------------|-------------------|
| `safety_gate` | None (stdlib regex) | Settings (policy patterns) |
| `behavior_audit` | `unified_claim_verifier.py` | CKS (Strategy B evidence) |
| `skill_first_stop_gate` | State files (`pending_command_intent_*.json`) | PreToolUse skill-first gate |
| `behavior_gates_*` | `Stop_behavior_gates.py` | Settings (blacklist) |
| `narrative_intent` | `narrative_intent_detector.py` | None |
| `challenge_requires_tool` | Anti-sycophancy injector markers | UserPromptSubmit hook |
| `anti_sycophancy_quality` | `anti_sycophancy/` detectors | Z.AI API (overconfidence) |
| `advisory` | `Stop_advisory.py`, `Stop_next_step_suggester.py` | Next-step state |
| `reflect_integration` | `Stop_reflect_integration.py` | Reflect skill |
| `cleanup_verifier` | `Stop_cleanup_verifier.py` | None |

**State management**:
- Location: `P:\.claude\hooks\state\` and `session_data\`
- Isolation: Session-scoped (session_id + terminal_id)
- Consistency: File-based JSON (marker files for cross-hook coordination)

**Critical invariants**:
1. **Fail-open for safety/advisory gates** (except behavior_audit - fail-closed)
2. **First block wins** (gate sequence order matters)
3. **Side effects run only if not blocked** (no cleanup on block)
4. **Exit code 2 = block** (exit 0 = allow)
5. **stderr = error** (hooks must write to stdout or stay silent)

**Known integration points**:
- **PreToolUse hooks** - Store intent markers for `skill_first_stop_gate` and `challenge_requires_tool`
- **UserPromptSubmit hooks** - Inject anti-sycophancy challenge markers
- **CKS** - `behavior_audit` queries CKS for Strategy B evidence
- **Reflect skill** - `reflect_integration` spawns background reflection

---

## 3. EXECUTION AND DATA FLOW

### Session Start Sequence

```
1. Claude Code CLI launches
2. SessionStart hooks execute (if registered)
   - SessionStart_semantic_daemon.py (start unified semantic daemon)
3. CLAUDE.md read (first 88 lines → system prompt)
4. MEMORY.md read (first 200 lines → system prompt)
5. User prompt processed
```

### Conversation Loop

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User submits prompt                                      │
│    - UserPromptSubmit hooks inject context                  │
│    - Intent markers stored (for skill-first enforcement)    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI generates response + tool calls                       │
│    - PreToolUse hooks validate before each tool             │
│    - PostToolUse hooks analyze after each tool              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Stop hook router executes (IN-PROCESS GATES)             │
│    For each gate in sequence:                                │
│    - Call gate function with data dict                      │
│    - If gate returns {"decision": "block"}:                 │
│      - Print block payload as JSON                          │
│      - Exit 2 (STOP execution)                              │
│    - If gate returns {"systemMessage": "..."}:              │
│      - Accumulate message for output                        │
│    - If gate returns None:                                  │
│      - Continue to next gate                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Side effects execute (SUBPROCESS, if not blocked)        │
│    - ThreadPool runs 3 hooks in parallel                    │
│    - 5-second timeout per hook                              │
│    - Errors logged to stderr (non-blocking)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Output delivered to user                                 │
│    - Accumulated systemMessages appended                    │
│    - Block reasons shown if blocked                         │
│    - Response allowed if no blocks                          │
└─────────────────────────────────────────────────────────────┘
```

### State Management

**State stores**:
- `P:\.claude\hooks\state\` - Cross-hook coordination (intent markers, challenge markers)
- `P:\.claude\hooks\session_data\` - Session-scoped data (last blocked claim markers)
- `C:\Users\brsth\.claude\projects\P--\memory\` - Auto-memory topic files

**Ownership**:
- **Hook state**: Each hook reads/writes its own state files
- **Session state**: Scoped by session_id + terminal_id (prevents cross-terminal bleed)
- **Memory state**: Manual updates (human-authored topic files)

**Consistency model**:
- **Hooks**: File-based JSON with atomic writes (no concurrent access)
- **Memory**: Manual version control (git tracked)
- **Isolation**: Session-scoped state prevents cross-session interference

### Error Handling

**Fail-open vs fail-closed policy**:

| Hook Type | Failure Mode | Rationale |
|-----------|--------------|-----------|
| `safety_gate` | Fail-open | Don't deadlock on safety check errors |
| `behavior_audit` | **Fail-closed** | Silent failures allow lies to slip through |
| `anti_sycophancy_quality` | Fail-open | Behavioral checks are advisory |
| `advisory` | Fail-open | Suggestions are non-blocking |
| `narrative_intent` | Fail-open | Narrative checks are warnings only |

**Retry/timeout behavior**:
- **In-process gates**: No retry (immediate fail)
- **Side effects**: 5-second timeout, logged errors, non-blocking
- **Subprocess calls**: No retry (fire-and-forget)

---

## 4. COMPONENT INVENTORY

### Core Logic

#### CLAUDE.md
- **Path**: `P:\CLAUDE.md`
- **Key sections**:
  - Development Model (Professional solo dev + AI workforce)
  - Python Code Standards (function length, print() for CLI)
  - Token Efficiency (auto-memory location)
  - Code Analysis (Serena skill preference)
- **Responsibility**: Workspace-wide configuration
- **Inputs**: None (static file)
- **Outputs**: System prompt injection
- **Known limitations**:
  - 200-line limit on MEMORY.md (truncation in system prompt)
  - Manual updates required (no automatic synchronization)

#### Memory System
- **Path**: `C:\Users\brsth\.claude\projects\P--\memory\`
- **Key functions**:
  - Index file (MEMORY.md) provides topic catalog
  - Topic files loaded on-demand (references in index)
  - Cross-session learning via persistent patterns
- **Responsibility**: Store and retrieve learned patterns
- **Inputs**: Manual updates (human-authored)
- **Outputs**: Topic file content (loaded into context)
- **Known limitations**:
  - No automatic synchronization across workspaces
  - Manual maintenance required (topic file pruning)
  - Risk of stale content if not updated regularly

#### Stop Router (Stop.py)
- **Path**: `P:\.claude\hooks\Stop.py`
- **Key functions**:
  - `_run_safety_gate()` - Secret/forbidden pattern detection
  - `_run_behavior_audit()` - Unverified claim detection
  - `_run_skill_first_stop_gate()` - /command enforcement
  - `_run_behavior_gates_*()` - Agreement, guidance, tool blacklist
  - `_run_anti_sycophancy_quality()` - Affirmation, overconfidence, lazy closure
  - `_run_advisory()` - Next-step menu generation
  - `_run_reflect_integration()` - Background reflection
  - `main()` - Gate sequence orchestration
- **Responsibility**: Route response through all gates, block or allow
- **Inputs**: JSON dict via stdin (response, tool_calls, session metadata)
- **Outputs**: JSON dict (decision, reason, systemMessage)
- **Known limitations**:
  - Gate sequence order matters (first block wins)
  - Side effects run even if advisory-only output
  - No automatic gate dependency resolution

#### Behavior Audit (Stop_behavior_audit.py)
- **Path**: `P:\.claude\hooks\Stop_behavior_audit.py`
- **Key functions**:
  - `check_user_dismissal()` - Detect user dismissal after correction
  - `main()` - Run behavioral verification via `unified_claim_verifier`
- **Responsibility**: Cross-reference claims against tool-call history
- **Inputs**: JSON dict via stdin (response, transcript)
- **Outputs**: JSON dict (block if unverified claims detected)
- **Known limitations**:
  - User dismissal detection only triggers after CORRECTION intent
  - Requires reconciliation patterns to avoid false positives
  - Dependent on `unified_claim_verifier.py`

#### Safety Gate (Stop_safety_gate.py)
- **Path**: `P:\.claude\hooks\Stop_safety_gate.py`
- **Key functions**:
  - `check_secrets()` - Detect API keys, credentials
  - `check_forbidden()` - Detect daemons, background tasks
  - `check_protocol()` - Detect command description vs execution
- **Responsibility**: Block safety/policy violations
- **Inputs**: JSON dict via stdin (response)
- **Outputs**: JSON dict (block if violation detected)
- **Known limitations**:
  - Regex-based detection (can generate false positives)
  - No whitelist mechanism for legitimate patterns
  - Fails open on error (may miss violations)

### Utilities/Helpers

#### Unified Claim Verifier
- **Path**: `P:\.claude\hooks\unified_claim_verifier.py`
- **Key functions**:
  - `evaluate_claims()` - Check claims against tool-call evidence
- **Responsibility**: Strategy A verification (tool-call evidence tracking)
- **Inputs**: Response text, session_id, terminal_id
- **Outputs**: Verification result (block/warn/allow)
- **Known limitations**:
  - Requires tool_calls in Stop input (may be missing in some cases)
  - Strategy B (CKS integration) requires external service
  - No whitelist for exempt claims

#### Anti-Sycophancy Detectors
- **Path**: `P:\.claude\hooks\anti_sycophancy\`
- **Key modules**:
  - `affirmation_detector.py` - Detect praise openers
  - `overconfidence_detector.py` - Detect overconfident language
  - `lazy_closure_detector.py` - Detect lazy closure patterns
  - `response_structure_detector.py` - Detect response structure issues
- **Responsibility**: Behavioral quality checks (advisory-only, except overconfidence block)
- **Inputs**: Response text
- **Outputs**: Detection results (warn or block)
- **Known limitations**:
  - Overconfidence detector requires Z.AI API (external dependency)
  - Regex-based patterns (can generate false positives)
  - No learning mechanism (patterns are static)

#### Next Step Suggester
- **Path**: `P:\.claude\hooks\Stop_next_step_suggester.py`
- **Key functions**:
  - `get_next_step_options()` - Generate next-step menu
  - `build_alphanumeric_menu()` - Format menu for display
- **Responsibility**: Generate contextually relevant next steps
- **Inputs**: Data dict (response, command history)
- **Outputs**: Menu options (A/B/C/...)
- **Known limitations**:
  - Collision detection only (no deduplication)
  - No automatic menu pruning (stale options persist)

### Configuration

#### Directory Policy
- **Path**: `P:\.claude\hooks\config\directory_policy.json`
- **Purpose**: Define Claude-restricted paths (user-authored content)
- **Current restrictions**:
  - `docs/` - User project documentation (Claude writes to `.claude/docs/` instead)
- **Known limitations**:
  - No wildcard support
  - No recursive pattern matching

#### Settings (settings.json)
- **Path**: `P:\.claude\settings.json`
- **Purpose**: Environment variables for all hooks
- **Key sections**:
  - `env` - Environment variables (hook toggles, API keys)
  - `hooks` - Hook registration
- **Known limitations**:
  - No schema validation
  - Manual updates required

### Infrastructure

#### State Management
- **Path**: `P:\.claude\hooks\state\`
- **Purpose**: Cross-hook coordination (intent markers, challenge markers)
- **Key files**:
  - `pending_command_intent_{session_id}.json` - Skill-first enforcement
  - `challenge__{session_id}__{terminal_id}.json` - Challenge markers
  - `last_blocked_claim_{session_id}_{terminal_id}.json` - Behavior audit markers
- **Known limitations**:
  - No automatic cleanup (marker files accumulate)
  - No TTL enforcement (relied on gate logic)

#### Session Data
- **Path**: `P:\.claude\hooks\session_data\`
- **Purpose**: Session-scoped data (blocked claim markers)
- **Key files**:
  - Scoped markers for behavior_audit pushback protocol
- **Known limitations**:
  - No automatic cleanup
  - No session timeout enforcement

#### Logs
- **Path**: `P:\.claude\hooks\logs\`
- **Purpose**: Observability for hook execution
- **Key files**:
  - `anti_sycophancy_violations.jsonl` - Anti-sycophancy detections
  - `skill_first_enforcement.jsonl` - Skill-first violations
- **Known limitations**:
  - No log rotation
  - No automatic pruning

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Constitutional Enforcement** - Hooks enforce behavioral constraints (not just guidelines)
2. **Evidence-Based Verification** - Claims require tool-call evidence or explicit hedging
3. **Professional Solo Dev Model** - AI-assisted workflow WITHOUT enterprise team bloat
4. **Cross-Session Learning** - Memory system persists lessons across sessions
5. **Fail-Closed for Critical Gates** - Behavior audit fails closed (silent failures allow lies)

### Technology Constraints

1. **Python stdlib only** - No external dependencies for hooks (reduces startup time)
2. **File-based state** - No databases (JSON files for state, Markdown for memory)
3. **Windows compatibility** - All hooks must work on Windows 11 (Git Bash)
4. **Subprocess isolation** - Side effects run in subprocess (in-process for blocking gates)
5. **JSON over stdin/stdout** - Hook communication protocol (no stdout logging in blocking gates)

### Performance SLAs

1. **Stop router latency**: <500ms total (13 gates in-process)
2. **Side effect timeout**: 5 seconds per hook (fire-and-forget)
3. **Memory load time**: <100ms per topic file (on-demand loading)
4. **CLAUDE.md load time**: <50ms (88 lines, static file)

### Things That Must NOT Change

1. **200-line limit on MEMORY.md** - System prompt truncation at 200 lines
2. **Exit code 2 = block** - All blocking hooks must exit 2 on block
3. **stderr = error** - Hooks must write to stdout or stay silent
4. **First block wins** - Gate sequence order matters (no short-circuit evaluation)
5. **User authority** - User's direct report ALWAYS overrides cached state
6. **Topic file focus** - Detailed content in topic files, not MEMORY.md index
7. **Fail-closed for behavior_audit** - Critical gate must block on crash

---

## 6. KNOWN ISSUES

### Issue 1: Memory File Staleness

**Scenario**: Topic files contain outdated patterns (e.g., deprecated hook paths)

**Expected vs Actual**:
- Expected: Topic files updated when codebase changes
- Actual: Topic files manual update only, risk of stale content

**Impact**: Medium - May mislead with outdated information

**Current workaround**: Manual review and update of topic files

---

### Issue 2: Gate Sequence Order Sensitivity

**Scenario**: Earlier gate blocks before later gate can provide context

**Expected vs Actual**:
- Expected: All gates evaluated, most relevant block shown
- Actual: First block wins, earlier gates may block with less specific reason

**Impact**: Low - Functionally correct but may show confusing block reasons

**Current workaround**: Manually reorder gate priority in `IN_PROCESS_GATES` list

---

### Issue 3: No Automatic State Cleanup

**Scenario**: Marker files accumulate in `state/` and `session_data/`

**Expected vs Actual**:
- Expected: Marker files auto-cleaned after TTL
- Actual: No cleanup mechanism, files accumulate indefinitely

**Impact**: Low - Storage bloat, no functional impact

**Current workaround**: Manual cleanup of old marker files

---

### Issue 4: Anti-Sycophancy Overconfidence Detector External Dependency

**Scenario**: Overconfidence detector requires Z.AI API (glm-4-plus model)

**Expected vs Actual**:
- Expected: Detector works offline (stdlib only)
- Actual: Requires external API call (Z.AI backend)

**Impact**: Medium - Overconfidence detection fails without API key

**Current workaround**: Set `OVERCONFIDENCE_DETECTOR_ENABLED=false` in settings.json

---

### Issue 5: No Whitelist for Safety Gate Patterns

**Scenario**: Legitimate patterns (e.g., "background process" in documentation) blocked

**Expected vs Actual**:
- Expected: Whitelist for known-safe patterns
- Actual: All patterns matching regex blocked

**Impact**: Low - False positives require manual bypass

**Current workaround**: Set `CONSTITUTIONAL_HOOKS_BYPASS=1` temporarily

---

### Issue 6: Memory System No Automatic Sync

**Scenario**: Pattern learned in one workspace not available in others

**Expected vs Actual**:
- Expected: Cross-workspace memory synchronization
- Actual: Each workspace has independent memory directory

**Impact**: Medium - Patterns must be manually copied across workspaces

**Current workaround**: Manual copy of topic files to other workspace memory directories

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### Adding a New Stop Gate

**Interface**: Add function to `Stop.py` and register in `IN_PROCESS_GATES`

```python
def _run_my_custom_gate(data: dict) -> dict | None:
    """Custom gate logic."""
    response = data.get("response", "")
    if not response:
        return None

    # Your validation logic here
    if violation_detected:
        return {
            "decision": "block",
            "reason": "Custom violation reason",
            "blocking_hook": "Stop.py:my_custom_gate",
        }
    return None
```

**Registration**:
```python
IN_PROCESS_GATES = [
    # ... existing gates ...
    ("my_custom_gate", _run_my_custom_gate),
]
```

**Invocation model**: Automatic (called by Stop.py main() for every response)

**Data exchange**:
- Input: `data` dict (response, tool_calls, session_id, terminal_id, etc.)
- Output: `dict` with `decision`, `reason`, `blocking_hook` or `None`

**Output expectations**:
- Block: `{"decision": "block", "reason": "...", "blocking_hook": "..."}`
- Warn: `{"systemMessage": "..."}`
- Allow: `None`

---

#### Adding a New Memory Topic File

**Interface**: Create `.md` file in memory directory, add reference to MEMORY.md

**Template**:
```markdown
# Topic Name

Brief description (1-2 sentences).

## Key Pattern 1

Description of pattern.

**Anti-pattern**: What to avoid

**Correct pattern**: What to do instead

## Key Pattern 2

...
```

**Registration**: Add to MEMORY.md topic catalog:
```markdown
| `topic_name.md` | Brief description | Key content |
```

**Invocation model**: Manual (file loaded when referenced in MEMORY.md)

**Data exchange**: File content loaded as context

---

#### Adding a New Side Effect Hook

**Interface**: Create Python script, register in `SIDE_EFFECTS` list

**Template**:
```python
#!/usr/bin/env python3
"""my_side_effect.py - My custom side effect."""

import json
import sys

def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    data = json.loads(raw_input)

    # Your side effect logic here (non-blocking)
    # Examples: logging, storage, telemetry

    sys.exit(0)  # Always exit 0 (side effects are non-blocking)

if __name__ == "__main__":
    main()
```

**Registration**:
```python
SIDE_EFFECTS = [
    # ... existing side effects ...
    "my_side_effect.py",
]
```

**Invocation model**: Automatic (subprocess, fire-and-forget, only if not blocked)

**Data exchange**:
- Input: JSON via stdin (same as Stop.py input)
- Output: Ignored (side effects are non-blocking)

**Exit code expectations**: Always exit 0 (non-blocking)

---

### Hook Integration Points

#### PreToolUse Integration

**Purpose**: Store intent markers for Stop gates

**Example**: Skill-first enforcement
1. UserPromptSubmit stores intent in `pending_command_intent_{session_id}.json`
2. PreToolUse blocks tool calls until Skill tool invoked
3. Stop.skill_first_stop_gate blocks if AI responds without Skill tool

**Data contract**:
- Intent file: `{"skill": "skill_name", "prompt": "...", "timestamp": ...}`
- Marker file: Read by Stop gate, deleted after check

---

#### UserPromptSubmit Integration

**Purpose**: Inject challenge markers for anti-sycophancy

**Example**: Challenge-requires-tool gate
1. UserPromptSubmit detects challenge language ("that sounds wrong")
2. Store marker in `state/anti_sycophancy_injector/challenge__{session_id}__{terminal_id}.json`
3. Stop.challenge_requires_tool blocks if response opens with stance without verification tools

**Data contract**:
- Challenge marker: `{"timestamp": ..., "challenge_text": "..."}`
- Read by Stop gate, deleted after check

---

#### CKS Integration

**Purpose**: Strategy B evidence for behavior_audit

**Example**: Unverified claim detection
1. Stop.behavior_audit detects claim without tool evidence
2. Query CKS for Strategy B evidence (previous findings)
3. Block if claim contradicts CKS entries, warn if evidence unavailable

**Data contract**:
- CKS query: `cks.search(query, entry_type="pattern|decision", limit=1)`
- Result: Dict with `title`, `content`, `entry_type`

**Graceful degradation**: CKS failures don't block hooks (fail open)

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample 1: Behavior Audit Block (Unverified Claims)

**Scenario**: AI claims "I fixed the bug" without testing

**Stop input** (abbreviated):
```json
{
  "response": "I've fixed the bug in the escape_fts5_query function. The issue was that special FTS5 characters weren't being properly escaped.",
  "tool_calls": "[{\"tool\": \"Edit\", \"input\": {\"file_path\": \"src/search/fts5.py\", ...}}]",
  "session_id": "sess_123",
  "terminal_id": "term_456"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED CLAIMS: Response contains unverified success claim ('fixed the bug') without test output or verification tool results.\n\nEvidence missing for: ['success claim: fixed the bug', 'assertion: issue was X']",
  "blocking_hook": "Stop.py:behavior_audit"
}
```

**Exit code**: 2 (block)

---

### Sample 2: Safety Gate Block (Secret Detection)

**Scenario**: AI accidentally includes API key in response

**Stop input**:
```json
{
  "response": "Here's the configuration:\n\nOPENAI_API_KEY=sk-abc123def456789xyz00000000000000\n\nThis key has access to GPT-4.",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "SAFETY VIOLATION: Possible Secret/API Key detected in output.",
  "blocking_hook": "Stop.py:safety_gate"
}
```

**Exit code**: 2 (block)

---

### Sample 3: Advisory Output (Next-Step Menu)

**Scenario**: Command execution completes, suggest next steps

**Stop input**:
```json
{
  "response": "I've updated the escape_fts5_query function with proper FTS5 character escaping.",
  "tool_calls": "[{\"tool\": \"Edit\", \"input\": {\"file_path\": \"src/search/fts5.py\", ...}}]",
  "last_command": "pytest tests/test_fts5.py -v"
}
```

**Stop output**:
```json
{
  "systemMessage": "\n\n💡 **ADVISORY**: Consider adding test coverage for edge cases | Verify FTS5 queries with special characters work correctly\n\n**Next Steps**:\n0. Run tests: pytest tests/test_fts5.py -v\n1. Check FTS5 escaping: python -c \"...\"\n2. View diff: git diff src/search/fts5.py\n\n(Reply with the option number only, e.g. \"0\", to run it.)"
}
```

**Exit code**: 0 (allow)

---

### Sample 4: Challenge-Requires-Tool Block

**Scenario**: User challenges claim, AI opens with apology instead of investigating

**User input** (previous turn): "That sounds wrong. I never saw that error before."

**Challenge marker** (stored by UserPromptSubmit):
```json
{
  "timestamp": 1741234567.89,
  "challenge_text": "That sounds wrong. I never saw that error before."
}
```

**Stop input**:
```json
{
  "response": "You're right to be skeptical. I apologize for the confusion. The actual issue is...",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "CHALLENGE-REQUIRES-TOOL: User challenged a factual claim and the response opens with agreement/apology before investigating. Investigate with tools first, THEN state your conclusion. Do not start with 'You're right' or apologies.",
  "blocking_hook": "Stop.py:challenge_requires_tool"
}
```

**Exit code**: 2 (block)

---

### Sample 5: Anti-Sycophancy Quality Warn

**Scenario**: AI uses overconfident language without verification

**Stop input**:
```json
{
  "response": "Clearly, the issue is X. There's no doubt about it. This is definitely the problem.",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "systemMessage": "OVERCONFIDENCE CHECK:\n- Clearly → Consider: \"Appears to be\" or \"Evidence suggests\"\n- There's no doubt about it → Consider: \"Further investigation needed\"\n- definitely → Consider: \"likely\" or \"probably\"\n\nThese patterns suggest overconfidence without verification evidence."
}
```

**Exit code**: 0 (allow with warning)

---

## END OF BUNDLE

**Next steps for LLM question-answering**:

1. **For architectural questions**: Consult Section 2 (Architecture Overview) and Section 5 (Design Intent)
2. **For behavioral questions**: Consult Section 3 (Execution and Data Flow) and Section 4 (Component Inventory)
3. **For integration questions**: Consult Section 7 (Integration Points)
4. **For debugging**: Consult Section 6 (Known Issues) and Section 8 (Sample Runs)

**Critical constraints to remember**:
- Professional solo dev + AI workforce (NOT enterprise team)
- 200-line limit on MEMORY.md
- Exit code 2 = block, exit 0 = allow
- User's direct report ALWAYS overrides cached state
- Behavior audit fails closed (critical gate)
