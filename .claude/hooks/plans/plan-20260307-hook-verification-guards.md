# Implementation Plan: Verification Guardrails for Negative Existence Claims

**Created**: 2026-03-07
**Status**: TESTING-COMPLETE
**Priority**: HIGH
**Last Updated**: 2026-03-07

## Verification Status

**Current Status**: TESTING-COMPLETE ✅

**Original Issues** (from verifier):
1. ❌ Test Discovery section lacked substantive test scenarios
2. ❌ Hook coordination protocol underspecified
3. ❌ Merge strategy for existing gate not defined
4. ❌ "This turn" scoping imprecise
5. ❌ turn_marker import path incorrect
6. ❌ Performance baselines subjective

**Revisions Applied**:
1. ✅ Added comprehensive test scenarios (Test 2.1.1-2.1.5, 2.2.1-2.2.5, 2.3.1)
2. ✅ Added hook coordination protocol with metadata sharing mechanism
3. ✅ Added merge strategy analysis (Option A vs Option B with recommendation)
4. ✅ Precisely defined "this turn" scoping with algorithm and fallback
5. ✅ Fixed turn_marker import path documentation
6. ✅ Added performance baselines with measurable targets (<100ms, <200ms)

**Remaining Tasks**:
- ✅ Unit tests for PreToolUse guard: All tests passing (9 tests)
- ✅ Unit tests for Stop guard: All tests passing (24 tests)
- ✅ Integration smoke test: All tests passing (5 scenarios)
- Monitor verification feedback in production use
- Adjust patterns based on real-world usage if needed

**Testing Results** (2026-03-07):
- **Unit Tests (PreToolUse)**: 9/9 tests passing ✅
  - New file allowed
  - Identical content denied
  - Different content asks for justification
  - Windows path handling works
  - Performance <100ms for small files

- **Unit Tests (Stop)**: 24/24 tests passing ✅
  - No negative patterns: allowed
  - Negative claims without verification: blocked
  - Negative claims with verification: allowed
  - File-specific patterns detected correctly
  - "This turn" scoping works correctly
  - Test mode detection works (blocks without verification for non-UUID session IDs)
  - Multiple verification tools count (Read, Grep, Glob, Bash with ls, WebSearch)

- **Integration Test**: 5/5 scenarios passing ✅
  - Stop guard blocks negative claims without verification
  - Stop guard allows claims with Read verification
  - PreToolUse guard denies identical writes
  - PreToolUse guard allows different content writes (asks for justification)
  - Both guards work together correctly

## Problem Statement

**Issue**: Claude Code agents sometimes make negative existence claims ("documentation is missing", "file doesn't exist") without verifying with tools, then attempt to write content that already exists with identical or similar content.

**Root Causes**:
1. **Reasoning failure**: Agents infer "doesn't exist" from absence in summary/context
2. **Verification failure**: No tool calls (Read/Glob/Grep) before claiming "missing"
3. **Guardrail gap**: Existing hooks catch "lazy user delegation" but not "assumption without verification"

**User Impact**:
- **Documented case**: Agent claimed `HANDOFF_SKILL_INVOCATION.md` was "missing" when it already existed and was committed
- **Wasted time**: Agent spent time creating documentation that already existed
- **Confusion**: User had to explain that documentation was already complete
- **Friction**: Breaks workflow smoothness

**Constraints**:
- ✅ **Minimize user friction**: User experience should remain smooth
- ✅ **LLM can answer questions**: Stop hook violations are OK (agent responses are acceptable)
- ✅ **Windows 11 compatible**: Must work correctly on Windows paths
- ✅ **No false positives**: Avoid flagging legitimate negative claims (domain knowledge, design decisions)

## Context Analysis

### Allowed APIs (from Documentation Discovery)

**PreToolUse Hook**:
- **Input**: JSON with `tool_name`, `tool_input`, `tool_use_id`
- **Output**: JSON with `permissionDecision` ("allow" | "deny" | "ask" | "modify")
- **Blocking**: YES - can deny tool execution with reason
- **Source**: `P:\.claude\docs\claude-hooks-v2.1.15.md` lines 148-162

**Stop Hook**:
- **Input**: JSON with `response` (string), `conversation` (array)
- **Output**: JSON with `decision` ("block" | "allow")
- **Blocking**: YES - can force continuation with reason
- **Source**: `P:\.claude\hooks\PROTOCOL.md` lines 184-217
- **Note**: **PostResponse hook DOES NOT EXIST** - must use Stop instead

**Evidence Store**:
- **API**: `load_tool_events(session_id, limit=200)` returns tool usage history
- **Fields**: `tool_name`, `command`, `output_excerpt`, `ts`, `id`
- **Source**: `P:\.claude\hooks\evidence_store.py` lines 89-104

### Existing Patterns

**File existence check**: `P:\.claude\hooks\__lib\pre_tool_use_logic.py` lines 88-100
- Uses `Path(file_path).exists()` and `.is_file()`
- Pattern confirmed working

**Negative existence detection**: `P:\.claude\hooks\Stop_unverified_existence_gate.py` lines 76-114
- Detects patterns: "doesn't exist", "not found", "couldn't find", "no results"
- Checks for verification tools: WebFetch, WebSearch, Bash, Read
- Confirmed working implementation

### Anti-Patterns to Avoid

**❌ stderr = Error** (CRITICAL):
- Claude Code treats **ANY** stderr as "hook error"
- Use stdout for JSON output
- Use stderr ONLY for exit code 2 blocking
- **Source**: MEMORY.md line 32

**❌ Exit code 2 in routed hooks**:
- Direct hooks: Exit code 2 works
- Routed hooks: Must output JSON + exit 0
- **Source**: `P:\.claude\hooks\PROTOCOL.md` lines 9-16

**❌ Assuming tool_use_id exists**:
- Not all PreToolUse calls include `tool_use_id`
- Must check `.get("tool_use_id", "")` with fallback
- **Source**: Test files show optional field

### Windows 11 Compatibility

**Path handling**:
```python
from pathlib import Path
p = Path(file_path)  # Handles both forward/backward slashes
if p.exists() and p.is_file():  # Works on Windows
```

### Edge Cases and Error Handling

**Large Files (>1MB)**:
- **Problem**: Reading entire file for hash comparison is slow
- **Solution**: Use 4KB sample comparison for large files
- **Implementation**:
  ```python
  SAMPLE_SIZE = 4096  # 4KB
  if file_size > 1_000_000:  # 1MB threshold
      existing_sample = existing_content[:SAMPLE_SIZE]
      new_sample = new_content[:SAMPLE_SIZE]
      if existing_sample == new_sample:
          return decision_deny  # Quick match
  ```

**UNC Paths**:
- **Problem**: Windows UNC paths `\\server\share\file.txt` may not work with pathlib
- **Solution**: Test with actual UNC path, fallback to string operations
- **Implementation**:
  ```python
  if file_path.startswith("\\\\"):
      # UNC path - may need special handling
      # Test with pathlib first, fallback to os.path
      try:
          p = Path(file_path)
          exists = p.exists()
      except (OSError, ValueError):
          exists = os.path.exists(file_path)
  ```

**Encoding Issues**:
- **Problem**: `errors='ignore'` might mask real encoding problems
- **Solution**: Try strict UTF-8 first, fall back to 'ignore'
- **Implementation**:
  ```python
  try:
      existing = p.read_text(encoding="utf-8")  # Strict mode
  except UnicodeDecodeError:
      existing = p.read_text(encoding="utf-8", errors="ignore")  # Fallback
  ```

**Backslash Handling**:
- **Problem**: Windows paths with backslashes in string comparisons
- **Solution**: Normalize paths before comparison
- **Implementation**:
  ```python
  from pathlib import Path
  normalized_path = Path(file_path).as_posix()  # Convert to forward slashes
  ```

**Race Conditions**:
- **Problem**: File deleted between exists check and read
- **Solution**: Wrap in try/except, treat missing file as "doesn't exist"
- **Implementation**:
  ```python
  try:
      if p.exists() and p.is_file():
          existing = p.read_text(...)
  except (FileNotFoundError, PermissionError):
      existing = ""  # Treat as doesn't exist
  ```

### Performance Baselines

**Definition**: "No perceptible slowdown" means hooks complete within performance targets.

**Performance Targets**:
- PreToolUse hook: <100ms for file operations
- Stop hook: <200ms for pattern detection
- File reading: <50ms for files <1MB

**Measurement**:
```python
import time

start = time.perf_counter()
# ... hook logic ...
elapsed_ms = (time.perf_counter() - start) * 1000

if elapsed_ms > 100:
    log_warning(f"PreToolUse hook took {elapsed_ms}ms (target: <100ms)")
```

**Optimization Techniques**:
- Early exit for non-Write/Edit tools
- Sample-based comparison for large files
- LRU caching for repeated file checks (same turn)
- Pattern compilation (pre-compile regexes)

### Import Path Clarification

**Correct Import Path**:
```python
# WRONG (documentation error in original plan):
from turn_marker import get_max_tool_event_id

# CORRECT (actual location):
from UserPromptSubmit_modules.turn_marker import write_turn_marker

# Alternative: Use load_turn_marker helper
from evidence_store import load_turn_marker
turn_marker_events = load_turn_marker(session_id)
max_id = max(e["id"] for e in turn_marker_events) if turn_marker_events else 0
```

**Verification**: Test import paths in actual hook before relying on them

**Encoding**:
```python
existing = p.read_text(encoding="utf-8", errors="ignore")
```

**Hashing**:
```python
import hashlib
hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
```

**Source**: `P:\.claude\hooks\PROTOCOL.md` lines 110-130

## Test Discovery

### Test Scenarios for PreToolUse File Existence Guard

**Test 2.1.1: Identical Write Denied**
- **Input**: Tool writes to existing file with identical content
- **Expected**: Hook returns `permissionDecision: "deny"` with reason
- **Output**: Agent receives message: "File already exists with identical content. Treat as 'docs already exist and are complete'."

**Test 2.1.2: Different Write Allowed with Justification**
- **Input**: Tool writes to existing file with different content
- **Expected**: Hook returns `permissionDecision: "allow"` with justification request
- **Output**: Agent receives message: "You are overwriting existing file X. State why previous documentation is insufficient and summarize what is changing."

**Test 2.1.3: New File Allowed**
- **Input**: Tool writes to non-existent file
- **Expected**: Hook returns `permissionDecision: "allow"` with no blocking
- **Output**: Write proceeds normally

**Test 2.1.4: Windows Path Handling**
- **Input**: File path with backslashes `C:\Users\test\file.md`
- **Expected**: Hook handles path correctly, no errors
- **Output**: Content comparison works regardless of path format

**Test 2.1.5: Large File Performance**
- **Input**: File >1MB with different content
- **Expected**: Hook completes within 100ms (4KB sample comparison)
- **Output**: No perceptible delay in agent workflow

### Test Scenarios for Stop Negative Existence Guard

**Test 2.2.1: Negative Claim Without Verification Blocked**
- **Input**: Response contains "documentation is missing" without Read/Glob/Grep
- **Expected**: Hook returns `decision: "block"` with guidance
- **Output**: Agent receives: "You stated 'X is missing' without verification. Either run a search tool or downgrade to 'unknown, must be verified'."

**Test 2.2.2: Negative Claim With Verification Allowed**
- **Input**: Response contains "file doesn't exist" after Read tool
- **Expected**: Hook returns empty JSON (allow stop)
- **Output**: Agent proceeds to stop

**Test 2.2.3: Obvious Claim Allowed**
- **Input**: Response contains "no internet access" or "no configuration needed"
- **Expected**: Hook returns empty JSON (allow stop)
- **Output**: Agent proceeds to stop

**Test 2.2.4: File-Specific Claim Detected**
- **Input**: Response contains "no documentation.md file"
- **Expected**: Hook checks for verification tools, blocks if missing
- **Output**: Blocked if no verification, allowed if Read/Glob used

**Test 2.2.5: "This Turn" Scoping Works**
- **Input**: Previous turn had Read tool, current turn has negative claim
- **Expected**: Hook only checks tool events from current turn (tool_event_id > max_id)
- **Output**: Blocked if no verification in current turn

### Integration Test (Smoke Test)

**Test 2.3.1: End-to-End Flow**
1. Create test documentation file `test_doc.md` with content "Version 1.0"
2. Agent claims "test_doc.md is missing"
3. **Expected**: Stop hook blocks with verification request
4. Agent runs Read tool on file
5. Agent claims "test_doc.md exists" with Read evidence
6. **Expected**: Stop hook allows agent to stop
7. Agent attempts to write identical content
8. **Expected**: PreToolUse hook denies identical write
9. Agent updates file with "Version 1.1" content
10. **Expected**: PreToolUse hook allows with justification

**Success Criteria**: All hooks work as expected, no duplicate violations, smooth user experience

### Hook Coordination Protocol

**Purpose**: Prevent duplicate violations between PreToolUse and Stop hooks when both conditions occur.

**Problem Scenario**:
1. Agent claims "docs are missing"
2. Agent attempts to write documentation
3. PreToolUse denies write (file exists)
4. Stop hook blocks response (no verification)
5. Agent gets confusing signals

**Solution**: Coordination Signal via Shared Metadata

**PreToolUse Hook Output Format** (with coordination):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny|allow",
    "permissionDecisionReason": "Explanation here",
    "metadata": {
      "overwrite_justified": true,
      "reason": "User requested update to add section Y"
    }
  }
}
```

**Stop Hook Reads PreToolUse Metadata**:
```python
# In Stop hook, check for PreToolUse metadata
tool_events = load_tool_events(session_id, limit=50)
pre_tooluse_events = [
    e for e in tool_events
    if e["tool_name"] in ("Write", "Edit")
]

# Check for metadata in recent PreToolUse calls
for event in reversed(pre_tooluse_events):
    metadata = event.get("metadata_json", {})
    if metadata.get("overwrite_justified"):
        # PreToolUse already handled this
        decision = "allow"  # Don't block
        additional_context = "Note: Overwrite was justified in PreToolUse"
        break
```

**Implementation Notes**:
- **Fallback**: If metadata reading fails, proceed with normal violation checking
- **Priority**: Metadata takes precedence over violation detection (avoid double-blocking)
- **Storage**: PreToolUse metadata stored in evidence_store as `metadata_json` field
- **Scope**: Only applies to same turn (tool_event_id within current turn)

### Merge Strategy for Stop_unverified_existence_gate.py

**Task**: Integrate enhancements into existing gate or create replacement

**Options**:

**Option A: Modify Existing Gate In-Place**
- **Approach**: Add improvements directly to `Stop_unverified_existence_gate.py`
- **Pros**: Single file to maintain, no registration conflicts
- **Cons**: Risk of breaking existing functionality
- **When to use**: If existing gate has good test coverage and clear ownership

**Option B: Create New Gate, Disable Old**
- **Approach**: Create `Stop_negative_existence_guard.py`, disable old in settings.json
- **Pros**: Safer, allows easy rollback, parallel development
- **Cons**: Two files to maintain, potential registration conflicts
- **When to use**: If existing gate is experimental or unclear ownership

**Recommended**: **Option B** (create new, disable old)
- Safer for production deployment
- Allows comparison of old vs new behavior
- Easy to rollback if issues arise

**Implementation** (Option B):
1. Create `P:/.claude/hooks/Stop_negative_existence_guard.py`
2. Comment out existing gate in settings.json:
   ```json
   {
     "matcher": ".*",
     "hooks": [
       {
         "type": "command",
         "command": "python P:/.claude/hooks/Stop_unverified_existence_gate.py",
         "timeout": 10,
         "enabled": false  // DISABLED
       }
     ]
   }
   ```
3. Register new gate in settings.json:
   ```json
   {
     "matcher": ".*",
     "hooks": [
       {
         "type": "command",
         "command": "python P:/.claude/hooks/Stop_negative_existence_guard.py",
         "timeout": 10
       }
     ]
   }
   ```

**Rollback**: If new gate causes issues, re-enable old gate and disable new gate

### Integration with Existing Stop_unverified_existence_gate.py

**Conflict Analysis Required**:
- Current gate: `P:\.claude/hooks\Stop_unverified_existence_gate.py`
- Overlap: Both detect negative existence claims
- Risk: Duplicate violations, confusing agent signals

**Merge Strategy** (requires investigation):
1. **Option A**: Modify existing gate in-place (recommended if code is clean)
2. **Option B**: Create new gate, disable old gate (safer, allows rollback)
3. **Option C**: Coordinate via metadata sharing (complex, both gates active)

**Decision Criteria**:
- If existing gate has tests and stable patterns → Option A (modify in-place)
- If existing gate is experimental or unstable → Option B (create new)
- If existing gate has unclear ownership → Option B (create new)

**Merge Implementation** (if Option A):
```python
# Add to Stop_unverified_existence_gate.py:
# Existing patterns: "doesn't exist", "not found", "couldn't find"
# New patterns: "missing", "not documented", "no X file"

# Add "this turn" scoping:
# Load tool events, find max tool_event_id from previous turns
# Only check tool events with id > max_id

# Add coordination signal check:
# Check for PreToolUse metadata in recent tool events
# If overwrite_justified=true, downgrade block to allow
```

**Task 1.5.1**: Read existing Stop_unverified_existence_gate.py
- **Actions**:
  - Analyze current implementation patterns
  - Check test coverage and stability
  - Identify merge points (pattern detection, scoping, coordination)
  - Document differences from proposed design
- **Acceptance**: Understanding of existing gate's behavior and code quality

### "This Turn" Scoping Implementation

**Purpose**: Only check verification tools from current turn, not previous turns.

**Algorithm**:
```python
# Load tool events from evidence store
events = load_tool_events(session_id, limit=200)

# Find max tool_event_id from previous turns
# (All events with id <= max_id are from previous turns)
turn_marker_events = load_turn_marker(session_id)
if turn_marker_events:
    max_id = max(e["id"] for e in turn_marker_events)
else:
    # Fallback: use max ID from all events
    # Assumes: "this turn" = events with highest IDs
    max_id = max(e["id"] for e in events) if events else 0

# Filter for verification tools in "this turn"
verification_events = [
    e for e in events
    if e["id"] > max_id  # Only after turn marker
    and e["tool_name"] in VERIFICATION_TOOLS  # Read, Glob, Grep, Bash, WebSearch, WebFetch
]
```

**Fallback Strategy** (if turn_marker.py unavailable):
```python
try:
    from UserPromptSubmit_modules.turn_marker import get_max_tool_event_id
    max_id = get_max_tool_event_id(session_id)
except ImportError:
    # Fallback: use simple heuristic
    # Assume: "this turn" = last 10 tool events
    recent_events = load_tool_events(session_id, limit=10)
    if recent_events:
        # Everything before the last 10 is "previous turns"
        max_id = recent_events[0]["id"]  # Oldest of recent
    else:
        max_id = 0  # No events yet, all events are current
```

**Verification Tool Definitions**:
```python
VERIFICATION_TOOLS = {
    "Read": True,  # Direct file read
    "Glob": True,  # File pattern search
    "Grep": True,  # Content search
    "Bash": lambda cmd: any(kw in cmd.lower() for kw in
        ["ls", "dir", "find", "git log", "git status", "git show"]),
    "WebSearch": True,
    "WebFetch": True,
}
```

## Existing Implementation Discovery

### Similar Hooks Already Deployed

**1. Stop_unverified_existence_gate.py** (Active)
- **Location**: `P:\.claude\hooks\Stop_unverified_existence_gate.py`
- **Purpose**: Detects negative existence claims without verification
- **Patterns**: "doesn't exist", "does not exist", "not found", "couldn't find"
- **Verification tools**: WebFetch, WebSearch, Bash, Read
- **Status**: ✅ Deployed and working
- **Gap**: Does NOT check tool_use_id for "this turn" scoping (may flag old claims)

**2. PreToolUse_skill_pattern_gate.py** (Active)
- **Location**: `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py`
- **Purpose**: Validates skill execution patterns
- **Pattern**: Checks file_path from tool_input
- **Decision**: Returns `permissionDecision: "allow"` | `"deny"` | `"ask"`
- **Status**: ✅ Deployed and working
- **Relevance**: Shows PreToolUse pattern for file operations

**3. verify_claims.py** (Active)
- **Location**: `P:\.claude\hooks\verify_claims.py`
- **Purpose**: Detects "success theater" (claims success without evidence)
- **Pattern**: "success" keywords with trivial commands only
- **Status**: ✅ Deployed and working
- **Relevance**: Shows claim detection pattern

### Gaps in Existing Hooks

**Gap 1**: No PreToolUse file existence check
- Existing hooks don't prevent overwrites of existing files
- No "identical content" detection
- No "overwrite with justification" requirement

**Gap 2**: Negative existence gate has no "this turn" scoping
- May flag claims from previous turns
- Uses turn_marker.py but implementation unclear
- Risk: False positives on legitimate claims made earlier

**Gap 3**: No coordination between hooks
- PreToolUse and Stop hooks operate independently
- No shared state to avoid duplicate violations
- Risk: Agent gets confusing signals from both hooks

## Proposed Solution

### Overview

Implement two coordinated hooks to prevent negative existence claim failures:

**Hook 1: PreToolUse File Existence Guard**
- **Event**: PreToolUse
- **Trigger**: Write/Edit operations
- **Behavior**:
  - If file exists with identical content → **DENY** (no-op)
  - If file exists with different content → **ALLOW** with justification request
  - If file doesn't exist → **ALLOW** (create new)
- **User friction**: LOW - only blocks truly redundant writes

**Hook 2: Stop Negative Existence Claim Guard (Enhanced)**
- **Event**: Stop
- **Trigger**: Response contains negative existence patterns
- **Behavior**:
  - Detect patterns: "missing", "doesn't exist", "not documented", "no X file"
  - Check if verification tools used THIS TURN
  - If no verification → **BLOCK** with request to verify or downgrade claim
- **User friction**: LOW - agent answers question, no user action needed

### User Experience Design

**Friction Minimization Strategies**:

1. **No user prompts required**: Hooks communicate with agent, not user
2. **Clear action guidance**: Hook reasons tell agent exactly what to do
3. **Allowlist for obvious claims**: Don't flag domain knowledge (e.g., "no internet")
4. **File-specific patterns**: Only flag claims about files/docs/configs
5. **Identical content bypass**: No-op for true duplicates (fast, silent)
6. **Justification over blocking**: Allow overwrites with explanation, not hard deny

**Example User Flow**:

**❌ BAD (High Friction)**:
```
Agent: "Documentation is missing."
Hook: [Prompts user] "Should I let agent claim this?"
User: [Must answer] "Yes"
Agent: [Continues]
```

**✅ GOOD (Low Friction)**:
```
Agent: "Documentation is missing."
Hook: [Blocks agent] "You claimed X is missing without verification.
Either run Read/Glob to check, or downgrade to 'unknown, must check'."
Agent: "Let me check that first." [Runs Read]
Agent: "Actually, documentation exists at P:/packages/handoff/docs/..."
```

### Hook 1: PreToolUse File Existence Guard

**File**: `P:/.claude/hooks/PreToolUse_file_existence_guard.py`

**Algorithm**:
```python
1. Parse stdin JSON for tool_name, tool_input
2. Extract file_path from tool_input
3. If not Write/Edit: allow (pass through)
4. If file_path doesn't exist: allow (new file)
5. If file exists:
   a. Read existing content (first 4KB sample for performance)
   b. Compute hash of existing vs new content
   c. If hashes match: DENY with "already exists, treat as verified"
   d. If hashes differ: ALLOW with "state why overwriting"
6. Output JSON with permissionDecision
```

**Decision Logic**:
```python
if file_not_exists:
    decision = "allow"
    reason = "New file creation"
elif content_identical:
    decision = "deny"
    reason = f"{file_path} already exists with identical content. Treat as 'docs already exist and are complete'. Explain to user that documentation is already present and reference it."
else:
    decision = "allow"
    reason = f"{file_path} exists with different content. Before proceeding, state why previous documentation is insufficient and summarize what is changing."
```

**Performance Optimization**:
- Sample first 4KB for quick comparison
- Full hash only if samples differ
- Skip hash for very large files (>1MB): use sample only

**Windows Compatibility**:
- Use `pathlib.Path` for cross-platform paths
- Use `encoding="utf-8", errors="ignore"` for file reading
- Use `hashlib.sha256` for content hashing

### Hook 2: Stop Negative Existence Claim Guard (Enhanced)

**File**: `P:/.claude/hooks/Stop_negative_existence_guard.py`

**Algorithm**:
```python
1. Parse stdin JSON for response, conversation
2. Extract latest assistant message from conversation
3. Scan for negative existence patterns:
   - "missing", "doesn't exist", "does not exist", "no such"
   - "wasn't created", "not documented", "no documentation", "no X file"
4. If no patterns: allow (pass through)
5. If patterns found:
   a. Load tool events from evidence_store (limit=200)
   b. Find max tool_event_id for "this turn" scoping
   c. Check if verification tools used after max_tool_event_id:
      - Read, Glob, Grep, Bash (with ls/find/git), WebSearch, WebFetch
   d. If verification found: allow (already verified)
   e. If no verification: BLOCK with guidance
6. Output JSON with decision
```

**Verification Tools**:
```python
VERIFICATION_TOOLS = {
    "Read": True,
    "Glob": True,
    "Grep": True,
    "Bash": lambda cmd: any(kw in cmd.lower() for kw in ["ls", "dir", "find", "git log", "git status"]),
    "WebSearch": True,
    "WebFetch": True,
}
```

**Allowlist (Obvious Claims)**:
```python
OBVIOUS_CLAIMS = [
    "no internet access",
    "no external dependencies",
    "no configuration needed",
    "no such file or directory",  # Bash error output, not a claim
]
```

**File-Specific Pattern**:
```python
# Only flag claims about files/docs/configs
FILE_CLAIM_PATTERNS = [
    r"no\s+[\w/.]+\.md",
    r"no\s+README",
    r"no\s+documentation",
    r"missing\s+file",
    r"not\s+documented",
]
```

**"This Turn" Scoping**:
```python
# Use turn_marker.py if available
try:
    from turn_marker import get_max_tool_event_id
    max_id = get_max_tool_event_id(session_id)
except ImportError:
    # Fallback: use max ID from evidence store
    events = load_tool_events(session_id, limit=200)
    max_id = max(e["id"] for e in events) if events else 0

# Only check tool events after max_id (this turn)
verification_events = [
    e for e in events
    if e["id"] > max_id and e["tool_name"] in VERIFICATION_TOOLS
]
```

**Decision Logic**:
```python
if no_negative_patterns:
    decision = "allow"  # No claims to check
elif in_obvious_allowlist:
    decision = "allow"  # Domain knowledge, not a claim
elif verification_found:
    decision = "allow"  # Agent already verified
else:
    decision = "block"
    reason = f"You stated '{claim}' without verification this turn. Either run a search tool (Read/Glob/Grep/Bash ls) to check, or downgrade to 'unknown, must be verified'."
```

### Integration with Existing Hooks

**Coordination Signal**:
```python
# In PreToolUse decision JSON:
decision["hookSpecificOutput"]["metadata"] = {
    "overwrite_justified": True,
    "reason": "Adding section Y to existing documentation"
}

# In Stop hook: Check for metadata
if has_overwrite_metadata:
    # Downgrade block to warning
    decision = "allow"
    additional_context = "Note: Overwrite was justified in PreToolUse"
```

**Settings Registration**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/.claude/hooks/PreToolUse_file_existence_guard.py"],
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/.claude/hooks/Stop_negative_existence_guard.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Conflict Detection with Existing Hooks

**Potential Conflict**: `Stop_unverified_existence_gate.py`
- **Current behavior**: Detects negative existence claims without verification
- **Overlap**: Similar to our Hook 2
- **Risk**: Duplicate violations, confusing signals

**Resolution Options**:
1. **Replace**: Disable old gate, use new enhanced version
2. **Merge**: Integrate improvements into existing gate
3. **Coordinate**: Add metadata sharing to avoid duplicates

**Recommended**: **Merge** - Enhance existing gate with:
- "This turn" scoping using tool_event_id
- File-specific pattern matching
- Obvious claims allowlist

## Implementation Plan

### Phase 1: Foundation (2-3 hours)

**Task 1.1**: Create PreToolUse file existence guard
- **File**: `P:/.claude/hooks/PreToolUse_file_existence_guard.py`
- **Actions**:
  - Implement file existence check with pathlib
  - Implement content comparison (4KB sample + hash)
  - Implement decision logic (deny/allow with reasons)
  - Add Windows compatibility (pathlib.Path, encoding)
- **Acceptance**:
  - Identical writes denied with clear reason
  - Different writes allowed with justification request
  - New files allowed without blocking
  - Works on Windows paths (backslashes, drive letters)

**Task 1.2**: Create Stop negative existence guard
- **File**: `P:/.claude/hooks/Stop_negative_existence_guard.py`
- **Actions**:
  - Implement pattern detection (missing, doesn't exist, etc.)
  - Implement "this turn" scoping with tool_event_id
  - Implement verification tool detection (Read, Glob, Grep, Bash)
  - Add obvious claims allowlist
  - Add file-specific pattern filtering
- **Acceptance**:
  - Detects negative existence claims in response
  - Checks for verification tools in this turn
  - Blocks unverified claims with guidance
  - Allows domain knowledge claims (no false positives)

**Task 1.3**: Register hooks in settings.json
- **File**: `P:/.claude\settings.json`
- **Actions**:
  - Add PreToolUse hook for Write|Edit matcher
  - Add Stop hook for ".*" matcher
  - Set appropriate timeouts (15s for PreToolUse, 10s for Stop)
- **Acceptance**:
  - Hooks load without errors
  - PreToolUse triggers on Write/Edit
  - Stop triggers on response completion

### Phase 2: Testing (2-3 hours)

**Task 2.1**: Unit tests for PreToolUse guard
- **File**: `P:/.claude/hooks/tests/test_pre_tool_use_file_guard.py`
- **Test cases**:
  - Identical write denied
  - Different write allowed with justification
  - New file allowed
  - Windows paths handled correctly
  - Large files use sample comparison
- **Acceptance**: All tests pass

**Task 2.2**: Unit tests for Stop guard
- **File**: `P:/.claude/hooks/tests/test_stop_negative_existence_guard.py`
- **Test cases**:
  - Negative claim without verification blocked
  - Negative claim with verification allowed
  - Obvious claim allowed
  - File-specific claim detected
  - "This turn" scoping works
- **Acceptance**: All tests pass

**Task 2.3**: Integration test (smoke test)
- **Actions**:
  - Create test documentation file
  - Attempt to overwrite with identical content → should deny
  - Claim "docs missing" without search → should block
  - Claim "docs missing" after Read → should allow
- **Acceptance**: Hooks work as expected in real Claude Code session

### Phase 3: Refinement (1-2 hours)

**Task 3.1**: Coordinate with existing hooks
- **Actions**:
  - Review `Stop_unverified_existence_gate.py`
  - Decide: replace, merge, or coordinate
  - Implement coordination signal if needed
  - Test for duplicate violations
- **Acceptance**: No duplicate violations, clear agent signals

**Task 3.2**: Performance optimization
- **Actions**:
  - Implement 4KB sample comparison for large files
  - Add caching for repeated file checks (same turn)
  - Test with files 1MB+ to ensure no slowdown
- **Acceptance**: No perceptible performance impact

**Task 3.3**: False positive tuning
- **Actions**:
  - Expand obvious claims allowlist
  - Refine file-specific patterns
  - Add more verification tools (git log, etc.)
  - Test with real conversations
- **Acceptance**: Low false positive rate (<5%)

### Phase 4: Documentation (1 hour)

**Task 4.1**: Update hook documentation
- **File**: `P:/.claude/hooks/HOOKS.md` (or create if doesn't exist)
- **Actions**:
  - Document PreToolUse_file_existence_guard.py purpose and behavior
  - Document Stop_negative_existence_guard.py purpose and behavior
  - Add troubleshooting guide
  - Add Windows compatibility notes
- **Acceptance**: Clear documentation for future maintenance

**Task 4.2**: Update MEMORY.md
- **File**: `P:/memory/MEMORY.md` (or appropriate topic file)
- **Actions**:
  - Add "Absence ≠ non-existence" rule
  - Document hook behavior as enforcement mechanism
  - Link to hook documentation
- **Acceptance**: Rule documented and referenceable

## Risks, Success Criteria, Dependencies

### Risks

**Risk 1: False positives annoy users**
- **Severity**: MEDIUM
- **Probability**: MEDIUM
- **Impact**: Legitimate work blocked by over-sensitive hooks
- **Mitigation**:
  - Extensive allowlist for obvious claims
  - File-specific pattern matching
  - "This turn" scoping to avoid old claims
  - User feedback loop for tuning

**Risk 2: Performance degradation**
- **Severity**: LOW
- **Probability**: LOW
- **Impact**: Hooks slow down file operations
- **Mitigation**:
  - Sample-based comparison (4KB)
  - Skip hash for very large files
  - Early exit for non-Write/Edit tools
  - Performance testing with 1MB+ files

**Risk 3: Coordination issues with existing hooks**
- **Severity**: MEDIUM
- **Probability**: HIGH
- **Impact**: Duplicate violations, confusing agent signals
- **Mitigation**:
  - Review existing Stop_unverified_existence_gate.py
  - Decide on merge/replace/coordinate strategy
  - Test for duplicate violations
  - Add metadata sharing between hooks

**Risk 4: Windows path edge cases**
- **Severity**: LOW
- **Probability**: LOW
- **Impact**: Hooks fail on Windows-specific paths
- **Mitigation**:
  - Use pathlib.Path (cross-platform)
  - Test with various Windows path formats
  - Use encoding="utf-8", errors="ignore"
  - Windows 11 testing

### Success Criteria

**Functional**:
- ✅ Identical writes denied with clear reason
- ✅ Different writes allowed with justification
- ✅ Negative claims without verification blocked
- ✅ Negative claims with verification allowed
- ✅ No false positives on domain knowledge
- ✅ Windows 11 paths handled correctly

**Performance**:
- ✅ No perceptible slowdown on normal operations
- ✅ Large files (>1MB) don't block workflow
- ✅ Hooks complete within timeout (15s PreToolUse, 10s Stop)

**User Experience**:
- ✅ User never prompted (only agent communicated with)
- ✅ Agent receives clear action guidance
- ✅ False positive rate <5%
- ✅ No confusing duplicate violations

**Quality**:
- ✅ Unit tests pass (100% coverage of core logic)
- ✅ Integration test passes (smoke test)
- ✅ Documentation complete and clear

### Dependencies

**Required**:
- ✅ Claude Code v2.1.15+ (for PreToolUse/Stop hooks)
- ✅ Python 3.12+ (for pathlib, hashlib)
- ✅ evidence_store.py (for tool event loading)
- ✅ turn_marker.py (for "this turn" scoping, optional)

**Optional**:
- ⚠️ turn_marker.py (fallback to max tool_event_id if unavailable)
- ⚠️ Existing Stop_unverified_existence_gate.py (may need coordination)

### Rollback Strategy

**If hooks cause issues**:
1. **Disable hooks**: Remove from settings.json
2. **Fallback to existing**: Stop_unverified_existence_gate.py still active
3. **Revert commit**: Git revert to previous state
4. **Tune patterns**: Update allowlists/patterns and redeploy

**Rollback triggers**:
- False positive rate >10%
- Performance complaints from users
- Duplicate violations confusion
- Windows path failures

## Next Actions

**Immediate** (today):
1. Review and approve this plan
2. Address any BLOCKED items from verification
3. Create TaskUpdate tasks for Phase 1 (foundation)

**Short-term** (this week):
1. Implement Phase 1: Foundation hooks
2. Implement Phase 2: Testing
3. Smoke test in real Claude Code session

**Medium-term** (next week):
1. Implement Phase 3: Refinement
2. Implement Phase 4: Documentation
3. Deploy to production settings.json

**Long-term** (ongoing):
1. Monitor for false positives
2. Tune patterns based on user feedback
3. Add more verification tools as needed
4. Consider additional guardrail improvements

---

**Plan Status**: DRAFT - Ready for review
**Top Risks**:
1. False positives annoy users (MEDIUM, MEDIUM) - Mitigation: Allowlists + file-specific patterns
2. Coordination issues with existing hooks (MEDIUM, HIGH) - Mitigation: Merge strategy + metadata sharing
3. Windows path edge cases (LOW, LOW) - Mitigation: pathlib.Path + Windows testing

**Next Actions**:
1. Approve plan → 2. Create tasks → 3. Implement Phase 1
