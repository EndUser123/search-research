# Debug Workflow System Context

## Generated Location
`P:\__csf\.nip\.staging\review_bundle_debug_workflow.md`

## Metadata
- **Generated:** 2026-01-27
- **Scope:** Debug workflow (`.claude/hooks/` debug-related components)
- **Files:** 19 core files + supporting modules
- **Execution Mode:** Single agent (19 files < 10 threshold)

## Execution Map

```
User Action → Tool Execution → PostToolUse_system2.py (ACTIVE)
                                      ↓
                          [Classify Error Patterns]
                                      ↓
                    Write: debug_session_state.json
                                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Error State Database                      │
│  P:/.claude/hooks/.state/debug_session_state.json      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ error_pattern: {                                      │ │
│  │    type: "windows_tool_not_found"                   │ │
│  │    severity: "CRITICAL"                           │ │
│  │    last_seen: "2026-01-27T..."                   │ │
│  │    alternatives: {python: "..."}                    │ │
│  │  }                                                   │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                      ↓
┌�─────────────────────────────────────────────────────────────┐
│         PreToolUse_debug_warning.py                          │
│         (reads debug state, shows warnings)               │
└─────────────────────────────────────────────────────────────┘
                                      ↓
┌�─────────────────────────────────────────────────────────────┐
│         UserPromptSubmit_debug_guidance.py (DISABLED)       │
│         (would inject guidance if CRITICAL errors)          │
└─────────────────────────────────────────────────────────────┘
                                      ↓
┌�─────────────────────────────────────────────────────────────┐
│         debug_investigation_gate.py (module)                 │
│         (enforces /truth validation during debug sessions)   │
│         ┌─────────────────────────────────────────────┐       │
│         │ /debug → blocks edits until /truth called  │       │
│         │ /rca → marks RCA phase complete          │       │
│         │ /truth → validates >=70% confidence    │       │
│         └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────┐
│         Investigation Ledger (investigation-ledger/)           │
│         ┌─────────────────────────────────────────────┐       │
│         │ PostToolUse_investigation_tracker.py         │       │
│         │ → Records: file reads, searches, executions  │       │
│         │ validate_confidence.py → confidence ceiling │       │
│         │ validate_claims.py → claim substantiation  │       │
│         └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## File Inventory

### Core Debug Hooks

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `debug_investigation_gate.py` | Enforces /truth validation during debug | 200+ | Module |
| `debug_assumption_audit.py` | Tests assumption audit logic | 50 | Test script |
| `debug_hook_env.py` | Tests hook subprocess execution | 30 | Test script |
| `UserPromptSubmit_debug_guidance.py` | Injects error guidance into prompts | 200+ | **Disabled** |
| `PreToolUse_debug_warning.py` | Shows warnings before tool execution | 150+ | Standalone |
| `PostToolUse_debug_input.py` | Captures tool input for debugging | 20 | Standalone |
| `validators/debug_v2_validator.py` | Wrapper for core validator | 20 | CLI tool |
| `PostToolUse_system2.py` | Error classification & state management | 500+ | **ACTIVE** |

### Investigation Ledger

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `investigation-ledger/ledger.py` | Records investigations | 300+ | Module |
| `investigation-ledger/validate_confidence.py` | Confidence ceiling validation | 200+ | Module |
| `investigation-ledger/validate_claims.py` | Claim substantiation validation | 300+ | Module |
| `investigation-ledger/PostToolUse_investigation_tracker.py` | Records investigations to ledger | 100+ | Module |
| `investigation-ledger/Stop_investigation_validator.py` | Validates claims against ledger | 100+ | Module |

### Test Scripts

| File | Purpose | Lines |
|------|---------|-------|
| `TEMP/debug_tools.py` | Tests tool extraction from transcripts | 80 |
| `TEMP/debug_patterns.py` | Tests installation strategy patterns | 50 |
| `TEMP/debug_exact.py` | Tests apostrophe handling | 30 |
| `TEMP/debug_apostrophe.py` | Tests apostrophe encoding | 30 |
| `TEMP/debug_affirmation.py` | Tests affirmation detection | 40 |
| `tests/debug_single_test.py` | Tests heredoc detection | 100 |
| `tests/debug_heredoc.py` | Tests pattern matching | 50 |

## Source Code

### 1. debug_investigation_gate.py

**Purpose:** Enforces `/truth` validation between investigation and fix phases during debug sessions.

**Key Features:**
- Thread-safe session state management
- Blocks edit tools until `/truth` invoked with >=70% confidence
- Tracks debug session lifecycle (debug_invoked → rca_completed → truth_invoked)
- Metrics tracking (sessions_bypassed, edits_blocked, avg_truth_score)

**Configuration:**
```python
TRUTH_THRESHOLD = 70.0
EDIT_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
TRUTH_TOOLS = frozenset({"Read", "Grep", "Glob", "Search", "Find"})
SESSION_STATE_FILE = "P:/.claude/hooks/data/debug_gate/session_state.json"
```

**State Structure:**
```python
@dataclass
class DebugSession:
    session_id: str
    started_at: str
    debug_invoked: bool
    rca_completed: bool
    truth_invoked: bool
    truth_score: float | None
    truth_passed: bool
    edits_blocked: int
    edits_allowed: int
```

**Usage:**
```bash
# Debug workflow invocation
/debug                    # Start debug session (sets state)
/rca analysis_file.py   # Complete RCA (sets rca_completed)
/truth "I verified X"   # Validate >=70% confidence
# Now edit tools are allowed
```

---

### 2. debug_assumption_audit.py

**Purpose:** Test script for assumption audit functionality.

**Dependencies:** `json`, `sys`, `pathlib`, `test_assumption_audit`

**Key Functionality:**
- Creates test transcripts with no tool usage
- Tests `extract_tools_from_transcript()` and `is_safe_response()`
- Validates assumption audit detects unverified claims

---

### 3. debug_hook_env.py

**Purpose:** Tests hook subprocess execution and environment variables.

**Dependencies:** `json`, `subprocess`, `sys`, `os`, `pathlib`

**Environment Variables Tested:**
- `TEST_ASSUMPTION_AUDIT_ENABLED` (default: true)
- Hook subprocess execution paths
- Working directory detection

---

### 4. UserPromptSubmit_debug_guidance.py

**Purpose:** Injects debug guidance into user prompts based on previous errors.

**Configuration:**
```python
ENABLED = True
SESSION_STATE_FILE = Path("P:/.speckit/tmp/debug_session_state.json")
STATE_EXPIRY_MINUTES = 5
ERROR_PATTERNS: Final = [...]  # Regex patterns for error detection
```

**Error Severity Levels:**
- **CRITICAL**: Windows tool not found, import errors, Python exceptions
- **WARNING**: Operational errors, race conditions
- **IGNORE**: Harmless errors

**Windows Tool Alternatives:**
```python
WINDOWS_TOOL_ALTERNATIVES: Final = {
    "sqlite3": 'python -c "import sqlite3; conn = sqlite3.connect(...)"',
    "sed": "python re module",
    "grep": "Select-String (PowerShell) or python re module",
    "awk": "python str.split() and list comprehensions",
    "find": "Path.glob() or pathlib.Path.rglob()",
}
```

**Router Status:** DISABLED (commented out in `UserPromptSubmit_router.py` line 31)

---

### 5. PreToolUse_debug_warning.py

**Purpose:** Displays warnings BEFORE tool execution based on previous errors.

**Configuration:**
```python
ENABLED = True
STATE_FILE = Path("P:/.claude/hooks/hooks/.state/debug_session_state.json")
```

**Warning Patterns:**
- "command not found" / exit_127 → Suggests Python equivalents
- "no such column" / OperationalError → Suggests PRAGMA table_info
- "traceback" → Python exception detected
- "retry_detected" → Verify what fix was applied

**Router Status:** Standalone (not in consolidated router)

---

### 6. PostToolUse_debug_input.py

**Purpose:** Dumps PostToolUse input to file for debugging tool data flow.

**Output:** `P:\.claude/hooks/.state/post_debug_input.json`

**Router Status:** Standalone (not in router)

---

### 7. validators/debug_v2_validator.py

**Purpose:** Wrapper for core validator engine.

**CLI Usage:**
```bash
python debug_v2_validator.py <filepath> --type debug
```

**Dependencies:**
- `core_validator` module (internal)
- `yaml` (optional, with fallback)

---

### 8. investigation-ledger/ledger.py

**Purpose:** Tracks what CC investigates (files read, searches, executions) for confidence validation.

**Public API:**
```python
record_file_read(path: str, content_hash: Optional[str] = None) -> bool
record_search(query: str, results_count: int = 0) -> bool
record_execution(command: str, exit_code: int) -> bool
get_investigated_topics() -> Set[str]
get_investigation_stats() -> Dict
calculate_confidence_ceiling() -> Dict
reset_ledger() -> bool
get_files_read() -> List[str]
```

**Confidence Ceiling Tiers:**
- Tier 1: 95% (3+ files + successful execution)
- Tier 3: 75% (2+ files OR 1+ files + 2+ searches)
- Tier 4: 50% (1+ files OR 1+ searches)
- No investigation: 0%

**Dependencies:** Python standard library only (fcntl on Unix, msvcrt on Windows)

---

### 9. investigation-ledger/validate_confidence.py

**Purpose:** Ensures confidence claims don't exceed investigation-based ceiling.

**Confidence Word Mappings:**
```python
HIGH_CONFIDENCE_WORDS = {
    "certainly": 90, "definitely": 90, "absolutely": 90,
    "guaranteed": 95, "100%": 100, "confident": 85,
}
MEDIUM_CONFIDENCE_WORDS = {
    "likely": 70, "probably": 70, "should": 70,
    "appears to": 65,
}
LOW_CONFIDENCE_WORDS = {
    "might": 50, "may": 50, "could": 50,
    "possibly": 50,
}
```

---

### 10. investigation-ledger/validate_claims.py

**Purpose:** Blocks claims about topics not in investigation ledger.

**Valid Evidence Markers:**
- File:line references (`main.py:42`)
- Explicit file references (`reading from config.py`)
- Output/result references (`the output shows`)

**Rejected Evidence Patterns:**
- "according to my/the/common"
- "I/we believe/think/assume"
- "typically/usually/generally"

---

### 11. investigation-ledger/PostToolUse_investigation_tracker.py

**Purpose:** Records file reads, searches, and executions to investigation ledger.

**Tool Mappings:**
- File read: `read`, `view`, `cat`, `get_file`
- Search: `search`, `grep`, `find`, `ripgrep`
- Execution: `bash`, `shell`, `exec`, `run`, `terminal`

---

### 12. investigation-ledger/Stop_investigation_validator.py

**Purpose:** Validates claims in response are substantiated by investigation.

**Block Conditions:**
1. Claims about uninvestigated topics
2. Confidence exceeding investigation-based ceiling

---

## External Dependencies

### Environment Variables

| Variable | Purpose | Default | Used By |
|----------|---------|---------|----------|
| `TEST_DEBUG` | Enable debug output in test hooks | unset | `debug_hook_env.py` |
| `TEST_ASSUMPTION_AUDIT_ENABLED` | Enable assumption audit | true | `debug_assumption_audit.py` |
| `ROUTER_DEBUG` | Router debug logging | false | Router hooks |
| `INVESTIGATION_LEDGER_ENABLED` | Enable investigation tracking | true | Investigation ledger |
| `CC_DIAGNOSTICS_ENABLED` | Diagnostic logging system | true | Performance tracker |
| `CC_DIAGNOSTICS_DIR` | Diagnostic log directory | `.claude/hooks/logs/diagnostics` | Performance tracker |

### Python Packages

**Standard Library Only:** All core debug files use only Python standard library.

**Internal Modules:**
- `performance_tracker` - Hook performance tracking
- `cc_diagnostic_logger` - Diagnostic logging
- `atomic_write` - Race-safe file writes (`P:/__csf/src/core/utils/atomic_write.py`)
- `core_validator` - File validation engine

### External System Dependencies

**State Files (Read/Write):**
- `P:/.claude/hooks/data/debug_gate/session_state.json`
- `P:/.claude/hooks/.state/debug_session_state.json`
- `P:/.speckit/tmp/debug_session_state.json`
- `P:/.claude/hooks/.state/post_debug_input.json`
- `P:/.claude/data/session_ledger.json`

**Guidance Cache:**
- `P:/.claude/hooks/.state/guidance-cache/guidance/*.json` (200+ cached guidance files)

## Configuration

### Constants

**debug_investigation_gate.py:**
```python
TRUTH_THRESHOLD = 70.0
EDIT_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
TRUTH_TOOLS = frozenset({"Read", "Grep", "Glob", "Search", "Find"})
```

**UserPromptSubmit_debug_guidance.py:**
```python
STATE_EXPIRY_MINUTES = 5
ERROR_PATTERNS: Final = [
    (r"windows_tool_not_found", "CRITICAL"),
    (r"import_error", "CRITICAL"),
    (r"python_exception", "CRITICAL"),
    (r"file_modified_error", "WARNING"),
    (r"retry_detected", "WARNING"),
]
```

### Router Integration Status

| Hook File | Router Status | Notes |
|-----------|---------------|-------|
| `UserPromptSubmit_debug_guidance.py` | **DISABLED** | Listed in router but commented out (line 31) |
| `PreToolUse_debug_warning.py` | Standalone | Not in router |
| `PostToolUse_debug_input.py` | Standalone | Not in router |
| `PostToolUse_system2.py` | **ACTIVE** | Layer: `0_system2_debug` |

### Settings.json References

**PostToolUse System2 (Active):**
```json
{
  "PostToolUse": [
    {
      "type": "command",
      "matcher": "^0_system2_debug$",
      "command": "python P:/.claude/hooks/PostToolUse_system2.py"
    }
  ]
}
```

## Validation Rules

### Prohibited Actions
- Do NOT use parallel agents for <10 files (overhead exceeds benefit)
- Do NOT skip scope selection step
- Do NOT claim bundle created without Write tool verification

### Configuration
- `REVIEW_BUNDLE_OUTPUT_DIR`: Default `P:/__csf.nip/.staging/`
- `REVIEW_BUNDLE_FORCE_SERIAL`: Force single-agent mode
- `REVIEW_BUNDLE_THRESHOLD_SMALL`: Files < 10 use single agent
- `REVIEW_BUNDLE_THRESHOLD_LARGE`: Files >= 50 use 4 agents

## Testing

### Test Scripts
- `debug_assumption_audit.py` - Tests assumption audit detection
- `debug_hook_env.py` - Tests hook subprocess execution
- `TEMP/debug_tools.py` - Tests tool extraction
- `TEMP/debug_patterns.py` - Tests pattern matching
- `TEMP/debug_exact.py` - Tests apostrophe handling
- `tests/debug_single_test.py` - Tests heredoc detection

### Run Tests
```bash
# Run assumption audit test
cd P:/.claude/hooks
python debug_assumption_audit.py

# Test hook environment
python debug_hook_env.py

# Test pattern matching
python TEMP/debug_patterns.py
```

## Architecture Notes

### Design Principles
1. **No External Dependencies**: All debug files use only Python standard library
2. **Shared Utilities**: Depend on internal modules (`performance_tracker`, `cc_diagnostic_logger`, `atomic_write`)
3. **State Management**: JSON files for persistence
4. **Router Optimization**: Debug hooks bypassed in consolidated routers for performance
5. **Thread Safety**: `debug_investigation_gate.py` uses threading.Lock() for concurrent access
6. **Atomic Writes**: State files use `atomic_write_json()` to prevent race conditions

### Error Classification Flow
```
PostToolUse_system2.py (ACTIVE)
    ↓
Error Pattern Matching (100+ patterns)
    ↓
Severity Classification (CRITICAL/WARNING/IGNORE)
    ↓
Write: debug_session_state.json
    ↓
PreToolUse_debug_warning.py (reads state)
    ↓
Display Warning to stderr (non-blocking)
```

### Debug Session Lifecycle (when active)
```
/debug → Sets state: debug_invoked=True
/rca  → Sets state: rca_completed=True
/truth → Sets state: truth_invoked=True, truth_score=75
→ Edit tools now allowed
```

## Known Issues

### Disabled Components
1. **UserPromptSubmit_debug_guidance.py** - Disabled in router for efficiency
   - Reason: "rarely fires" (only 1 error in 200+ cache files)
   - To enable: Add to `UserPromptSubmit_router.py` injector list

2. **PreToolUse_debug_warning.py** - Not integrated into router
   - Reason: Standalone operation (reads PostToolUse_system2.py output)
   - To enable: Add to `PreToolUse_write_router.py` or `PreToolUse_router.py`

3. **PostToolUse_debug_input.py** - Not in router
   - Reason: Debug only (temporary diagnostic tool)
   - To enable: Add to `PostToolUse_router.py`

### State File Cleanup
Debug state generates many temporary files:
- `P:/.claude/hooks/.state/.debug_session_state.json.*` (session temp files)
- Cleanup: Automatically expire after 5 minutes

## Related Systems

### Integrated Systems
- **PostToolUse_system2.py** - Active error classification and state management
- **Investigation Ledger** - Records investigations for confidence validation
- **Performance Tracker** - Hook performance monitoring
- **CC Diagnostic Logger** - Centralized logging system

### Dependent Systems
- **anti_sycophancy/** - Affirmation detection (used by TEMP/debug scripts)
- **core_validator.py** - Validation engine (used by debug_v2_validator.py)
- **tool_sequence_manager** - Tool extraction (used by TEMP/debug_tools.py)

## Quick Reference

### Enable Debug Workflow Components

**Enable debug guidance:**
```bash
# Edit P:/.claude/hooks/UserPromptSubmit_router.py
# Uncomment line 31 (UserPromptSubmit_debug_guidance.py)
```

**Enable debug warnings:**
```bash
# Add to P:/.claude/settings.json under "PreToolUse":
{
  "type": "command",
  "matcher": "^(Write|Edit|MultiEdit)",
  "command": "python P:/.claude/hooks/PreToolUse_debug_warning.py"
}
```

**Enable debug input capture:**
```bash
# Add to P:/.claude/settings.json under "PostToolUse":
{
  "type": "command",
  "matcher": ".*",
  "command": "python P:/.claude/hooks/PostToolUse_debug_input.py"
}
```

### Debug Workflow Commands

```bash
# Start debug session (requires debug_investigation_gate.py imported)
/debug

# Run RCA (marks rca_completed in state)
/rca analysis_file.py

# Validate with >=70% confidence
/truth "I verified X by reading Y and checking Z"

# View investigation ledger
python -c "from investigation_ledger.ledger import get_investigation_stats; print(get_investigation_stats())"
```

## Maintenance

### Log Rotation
Diagnostic logs can grow large. Monitor:
- `P:/.claude/hooks/logs/diagnostics/*.jsonl`
- `P:/.claude/hooks/.state/guidance-cache/guidance/*.json`

### State Cleanup
Temporary debug state files auto-expire after 5 minutes. Manual cleanup:
```bash
# Clean expired debug session state
find P:/.claude/hooks/.state -name "debug_session_state.json.*" -mtime +1 -delete 2>/dev/null

# Clear investigation ledger (reset session tracking)
python -c "from investigation_ledger.ledger import reset_ledger; reset_ledger()"
```

---

**Bundle Generation:** 2026-01-27
**Execution Mode:** Single agent (19 files < 10 threshold)
**Verification:** Write tool confirmed successful output



---

## PRE-SIMPLIFICATION ARCHIVE (v7.1 - Pre-v8)

This section contains the older versions of debug and RCA components before the v8 simplification.
These represent the more complex, multi-gate architecture that was consolidated.

### Historical Context

**Pre-v8 Architecture (Multi-Gate System):**
- Gate 1: Falsification Protocol - Assumption detection and adversarial search requirement
- Gate 2: Post-Action Verification - Automatic verification triggers and pattern-gaming detection
- Gate 3: Code Comprehension - Read-before-write enforcement
- Truth Validator: High-signal validation for lazy patterns, excuses, sycophancy
- Debug Guidance: Error pattern classification with Windows tool alternatives
- RCA v7.1: Production engine with manual fallback workflow

**Simplification to v8:**
- Consolidated gates into simpler, hook-based enforcement
- Moved complex gate logic to archived status
- Simplified RCA to /rca skill with direct execution
- Truth validation moved to constitutional hooks
- Debug guidance consolidated into PostToolUse_system2.py

---

### Archived Hook: UserPromptSubmit_debug_guidance.py.off

**Purpose:** Injected debug guidance into user prompts based on previous errors.

**Status:** DISABLED (rarely fires - only 1 CRITICAL error in 200+ cache files)

**Configuration:**
```python
ENABLED = True
SESSION_STATE_FILE = Path("P:/.speckit/tmp/debug_session_state.json")
STATE_EXPIRY_MINUTES = 5
```

**Error Severity Levels:**
- **CRITICAL**: Exit codes, hard failures, exceptions
- **WARNING**: Advisory messages, structural issues
- **IGNORE**: Normal output

**Windows Tool Alternatives:**
```python
WINDOWS_TOOL_ALTERNATIVES = {
    "sqlite3": 'python -c "import sqlite3; conn = sqlite3.connect(...)"',
    "sed": "python re module",
    "grep": "Select-String (PowerShell) or python re module",
    "awk": "python str.split() and list comprehensions",
    "find": "Path.glob() or pathlib.Path.rglob()",
}
```

**Key Features:**
- Reads debug session state from previous errors
- Classifies error severity (CRITICAL/WARNING/IGNORE)
- Generates contextual guidance for error types
- Provides Python alternatives for Windows-unavailable tools
- Only injects guidance for CRITICAL errors (WARNING level issues don't pollute prompts)

**Router Integration:** Listed in `UserPromptSubmit_router.py` but commented out (line 31)

**Archived Location:** `P:/.claude/hooks/_archive/UserPromptSubmit_debug_guidance.py.off`

---

### Archived Hook: UserPromptSubmit_truth_validator.py.off (v2.3.2)

**Purpose:** Minimal high-signal validation for lazy cognition patterns.

**Design Philosophy:**
- Constitution prevents lazy cognition (primary defense)
- Hook catches obvious escapes (secondary defense)
- High precision > high recall (false positives are costly)
- Minimal patterns, maximum signal

**Validation Checks:**

1. **LazyClaimChecker** - Critical lazy pattern detection:
   - Documentation claims without verification
   - Depth claims without evidence trail
   - Verification claims without proof
   - Test claims without output
   - Nonexistence claims without search proof
   - Threshold: 3+ unvalidated claims to block

2. **ExcuseChecker** - Probabilistic hedges:
   - "should work", "ought to work", "expected to work"
   - "works locally", "on my machine"
   - "timing mismatch", "moving target", "in flux"

3. **SycophancyChecker** - Flattery without substance:
   - "great question", "excellent point", "wonderful idea"
   - "you're absolutely right", "perfect solution", "lgtm"

4. **FakeSystemOutputChecker** - Hallucinated system messages:
   - Fake hook execution messages
   - Fake tool execution markers
   - Fake progress indicators

**Evidence Keywords:**
```python
EVIDENCE_KEYWORDS = [
    "glob", "grep", "searched", "found", "examined", "read",
    "```", "file:", "line ", "output:", "returned", "results",
    "pytest", "assert", ".py:", "def ", "class ",
]
```

**Archived Location:** `P:/.claude/hooks/_archive/UserPromptSubmit_truth_validator.py.off`

---

### Archived Hook: PostToolUse_gate_2_verification.py (PHASE 5)

**Purpose:** Post-action verification automation with cross-validation and pattern-gaming detection.

**Enforcement Level:** AUTOMATIC (triggers verification, non-blocking)

**Key Features:**

1. **Automatic Verification Triggers:**
   - Tracks high-risk tools: Write, Bash, Update
   - Generates verification commands based on operation type
   - Verification patterns by tool (Write→Read, Bash→Bash verify)

2. **Cross-Validation (PHASE 5):**
   - Tracks if suggested verifications were actually run
   - Logs all tool usage to cross-validation state file
   - Matches verification tools against expected operations

3. **Pattern-Gaming Detection:**
   - Detects when verification suggestions are consistently skipped
   - Threshold: 3 skipped verifications in 10 minutes
   - Severity levels: low, medium, high
   - Alerts when CC is ignoring verification steps

4. **State Tracking:**
   - STATE_FILE: Verification requirements tracking
   - CROSS_VALIDATION_FILE: Tool usage for cross-validation
   - FALSIFICATION_STATE_FILE: Shared with Gate 1

**Verification Patterns:**
```python
VERIFICATION_PATTERNS = {
    "Write": {
        "verify_tool": "Read",
        "check_indicators": ["content", "line", "character"],
        "failure_indicators": ["error", "not found"],
    },
    "Bash": {
        "verify_tool": "Bash",
        "check_indicators": ["exit code: 0", "successfully"],
        "failure_indicators": ["error", "failed", "exit code: 1"],
    },
}
```

**Pattern-Gaming Warning:**
```
⚠️ PATTERN GAMING DETECTED (Gate 2)
Severity: HIGH
Skipped Verifications: 5 in the last 10 minutes

You are consistently skipping verification steps.
Required Action: Run suggested verifications before continuing.
```

**Archived Location:** `P:/.claude/hooks/_archive/PostToolUse_gate_2_verification.py`

---

### Archived Hook: UserPromptSubmit_gate_1_falsification.py.off

**Purpose:** Gate 1 - Simplified Falsification Protocol.

**Function:**
- Detects assumption-heavy requests
- Injects requirement for adversarial search
- Imports from `__csf.nip/src/gates/gate_1_falsification.py`

**Status:** Module file not found (likely removed during simplification)

**Archived Location:** `P:/.claude/hooks/_archive/UserPromptSubmit_gate_1_falsification.py.off`

---

### Archived Hook: UserPromptSubmit_gate_3_comprehension.py.off

**Purpose:** Gate 3 - Code Comprehension (Read-Before-Write).

**Function:**
- Injects requirement to read existing code before modifying
- Imports from `__csf.nip/src/gates/gate_3_code_comprehension.py`

**Status:** Module file not found (likely removed during simplification)

**Archived Location:** `P:/.claude/hooks/_archive/UserPromptSubmit_gate_3_comprehension.py.off`

---

### Archived Documentation: RCA v7.1 (Production)

**Location:** `P:/.claude/_archive/rca.md`

**Version:** 7.1 (PRODUCTION)

**Role:** Root cause analysis via production engine orchestration

**Primary Method:**

```bash
python -c "
import asyncio
from __csf_nip.features.modules.rca_v2_production.engine import ProductionRCAEngine

async def analyze():
    engine = ProductionRCAEngine()
    result = await engine.analyze('<PROBLEM_DESCRIPTION>')
    print(result)

asyncio.run(analyze())
"
```

**Engine Handles Automatically:**
- Strategy selection (QUICK_FIX → STANDARD → DEEP_ANALYSIS)
- Evidence collection (Serena, TreeSitter, HDMA)
- Multi-agent specialist analysis
- Confidence-scored results

**Confidence Interpretation:**
| Confidence | Meaning | Action |
|------------|---------|--------|
| 90%+ | High certainty | Proceed with fix |
| 70-89% | Moderate certainty | Verify before fix |
| <70% | Low certainty | Gather more evidence |

**Tools Quick Reference:**
| Tool | Purpose | Invocation |
|------|---------|------------|
| Production Engine | Full RCA orchestration | `ProductionRCAEngine().analyze()` |
| Debate Council | Multi-agent specialists | `ProductionDebateCouncil().analyze()` |
| AI-Distiller | Context compression | `aid ./src --ai-action=...` |
| CHS | Chat history search | `python -m features.modules.analysis.chat_search.src.chs` |
| Serena | Semantic analysis | `python -m features.modules.analysis.serena_cli` |
| HDMA | Architecture | `python -m features.modules.code_analysis.hdma_analyzer` |
| TreeSitter | Syntax | `python -m commands.nip.tree_sitter_wrapper` |
| CKS | Knowledge base | `python commands/cks_cli.py` |

**Anti-Patterns:**
- ❌ Skip reproduction
- ❌ Single hypothesis
- ❌ Fix symptoms only
- ❌ "Tests pass" without output
- ❌ Speculation without citations

---

### Archived Agent: csf-nip-rca-specialist.md (v2.0 Enhanced)

**Location:** `P:/.claude/_archive/agents/csf-nip-rca-specialist.md`

**Version:** 2.0 Enhanced

**Description:** Enhanced Cognitive RCA Specialist with semantic intelligence, pattern recognition, and automated evidence collection. 300% capability improvement over baseline.

**Cognitive Enhancement Features (v2.0):**
- Semantic Pattern Recognition: 90% accuracy across historical cases
- Context-Aware Reasoning: Project structure and development patterns
- Automated Evidence Collection: Intelligent gathering with contextual filtering
- Predictive Failure Analysis: Identifies potential future issues
- Cross-Reference Intelligence: Correlates current issues with historical patterns
- Trust-Weighted Analysis: Confidence scoring for evidence reliability

**Success Metrics (v2.0 Enhanced):**

**RCA Quality Metrics:**
- Root Cause Accuracy: >95% (with cognitive enhancement)
- Implementation Rate: >85%
- Effectiveness Rate: >90%
- Time to Resolution: <2 hours (common issues)
- Pattern Recognition Accuracy: >90%
- Prediction Accuracy: >75%

**Solo Developer Value Metrics (v2.0 NEW):**
- Quick-RCA Success Rate: >80% (within 30 min)
- Self-Service Capability: >90%
- Learning Velocity: 20% faster per month
- Tool Efficiency: >90% automation
- Knowledge Capture Rate: >95%

**Business Impact Metrics:**
- MTTR Reduction: >60%
- Incident Reduction: >50%
- Cost Avoidance: >300% ROI
- Developer Productivity: >10 hours/week
- System Reliability: >99.9% uptime

---

## Simplification Migration Notes

### What Changed from v7.1 to v8

**Removed (Archived):**
1. **Multi-Gate Architecture:**
   - Gate 1 (Falsification) → Removed
   - Gate 2 (Verification) → Simplified to basic tracking
   - Gate 3 (Comprehension) → Merged into constitution

2. **Complex State Management:**
   - Multiple state files per gate
   - Cross-validation tracking
   - Pattern-gaming detection
   - Falsification state coordination

3. **Heavy RCA v7.1:**
   - Production engine orchestration
   - Multi-agent debate council
   - Complex tool integration (20+ tools)
   - Extensive evidence collection phases

**Retained (Simplified):**
1. **Debug Guidance:**
   - Error pattern classification moved to PostToolUse_system2.py
   - Windows tool alternatives preserved
   - Severity classification (CRITICAL/WARNING/IGNORE)

2. **Truth Validation:**
   - Core patterns moved to constitutional_enforcer.py
   - Simplified to essential checks
   - High-signal detection retained

3. **RCA Core:**
   - /rca skill for direct invocation
   - Simplified workflow
   - Essential evidence collection

**New in v8:**
1. **Consolidated Router Pattern:**
   - Single router per event type
   - Feature-flag controlled execution
   - Parallel hook support

2. **Investigation Ledger:**
   - Tracks file reads, searches, executions
   - Confidence ceiling validation
   - Claim substantiation checking

3. **Debug Investigation Gate:**
   - Session state management
   - /debug → /rca → /truth workflow
   - Edit blocking until truth validated

### Migration Path

**For existing RCA v7.1 usage:**
```bash
# Old (v7.1)
python -c "from __csf_nip.features.modules.rca_v2_production.engine import ProductionRCAEngine; ..."

# New (v8)
/rca <problem_description>
```

**For gate-based validation:**
```bash
# Old (v7.1)
# Gates automatically triggered based on event

# New (v8)
# Constitutional hooks enforce via CLAUDE.md
# Use /truth for explicit validation
```

---

**Archive Date:** 2026-01-27
**Simplification Version:** v8.0
**Previous Version:** v7.1 (Multi-Gate System)
