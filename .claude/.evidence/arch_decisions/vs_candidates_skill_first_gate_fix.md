# Verbalized Sampling Candidates: Skill-First Gate Enforcement Fix

## Context (from codebase analysis and web research)

**Problem**: Skill-first gate enforcement is "broken by design" because:
1. Intent file creation in `skill_enforcer.py` (lines 152-156) returns early if `terminal_id` is missing
2. The "stateless" gate in `PreToolUse_skill_pattern_gate.py` (lines 494-589) actually reads intent files
3. Documentation claims "TELEMETRY ONLY - NOT USED FOR ENFORCEMENT" (line 137) but code contradicts this
4. Single point of failure: missing terminal_id causes enforcement gap

**Constitutional Constraints**:
- Multi-terminal isolation is REQUIRED (every terminal has isolated state)
- Stale data immunity is REQUIRED (state changes must propagate)
- Hooks MUST NOT have external dependencies (Hook External Dependency Policy)

**Web Research Insights**:
- Stateless hooks should be pure functions of inputs, but stateful enforcement is acceptable when correctness requires it
- Terminal isolation uses session_id for routing behavior
- Intent file pattern is valid for "structural gates" but should not have single points of failure
- Graceful degradation: system should fail-open without creating shared mutable state

---

## Candidate 1: **Hybrid Fallback with Session_ID** (Probability: 0.65)

**Primary Lens**: Dependency Lens (MUST vs SHOULD vs MAY)

**Approach**: Always create intent files, using terminal_id when available, session_id as fallback

**Implementation**:
```python
# In skill_enforcer.py _log_command_intent_telemetry():
raw_terminal_id = _get_terminal_id(context)
raw_session_id = _get_session_id(context)

# Use terminal_id if available, otherwise session_id for isolation
scope_id = raw_terminal_id if raw_terminal_id else raw_session_id
scope_type = "terminal" if raw_terminal_id else "session"

if not scope_id or scope_id == "unknown":
    # Only skip if BOTH are missing
    return

# Create intent file with scope_id
intent_file = base / f"terminals/{scope_id}/pending_command_intent.json"
```

**Tradeoffs**:
- **Favored**: Reliability (enforcement works even without terminal_id), Multi-terminal safety (session-scoped fallback)
- **Degraded**: Adds complexity to intent file reading logic, Session-scoped files (weaker isolation than terminal-scoped)
- **Failure Conditions**: If both terminal_id AND session_id are missing, enforcement still fails
- **ISO 25010**: +Reliability, +Maintainability, -Security (weaker isolation with session fallback)

**Evidence from codebase**: `PreToolUse_skill_pattern_gate.py:547` already checks multiple intent file paths, suggesting the system can handle fallback logic

---

## Candidate 2: **Truly Stateless Gate via user_message Injection** (Probability: 0.55)

**Primary Lens**: Contract Lens (schemas/APIs defined first)

**Approach**: Remove intent file dependency entirely. Have UserPromptSubmit inject the slash command into the AI's context, and PreToolUse validates tool usage against the injected context.

**Implementation**:
```python
# In skill_enforcer.py: Build context injection instead of intent file
# Store in-memory (session-scoped) instead of file:
context_data = {
    "slash_command": command,
    "timestamp": time.time(),
    "session_id": raw_session_id,
}

# Inject into AI context via additionalContext
# (No file I/O, no terminal_id dependency)

# In PreToolUse_skill_pattern_gate.py:
# Read from injected context (not from file)
# Parse the user_message from hook input or from session context
```

**Tradeoffs**:
- **Favored**: Simplicity (no intent file complexity), True statelessness (no file I/O), Performance (no disk operations)
- **Degraded**: Requires hook input schema changes, May not work across all hook invocation patterns, Session-scoped only (weaker multi-terminal isolation)
- **Failure Conditions**: If hook input doesn't include user_message, gate cannot detect slash commands
- **ISO 25010**: +Performance Efficiency, +Maintainability, -Reliability (depends on hook input availability)

**Evidence from codebase**: `PreToolUse_skill_pattern_gate.py:497` comment acknowledges "PreToolUse hooks don't receive user_message in their input schema" — this would require framework changes

---

## Candidate 3: **Terminal ID Hardening** (Probability: 0.45)

**Primary Lens**: Evidence Lens (what evidence supports this decision)

**Approach**: Fix the root cause by ensuring terminal_id is ALWAYS available. Add fallback detection methods and fail-closed if unavailable.

**Implementation**:
```python
# In __lib/hook_base.py or __lib/runtime_env.py:
def get_terminal_id(data: dict) -> str:
    # Try multiple sources in priority order
    for key in ["terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"]:
        if value := data.get(key):
            if value.strip():
                return value.strip()

    # Fallback: Generate deterministic ID from session_id + cwd
    session_id = data.get("session_id", "")
    cwd = data.get("cwd", "")
    if session_id and cwd:
        # Create terminal-scoped ID from available context
        import hashlib
        combined = f"{session_id}:{cwd}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    # Last resort: Fail-closed with error
    raise RuntimeError("Cannot determine terminal_id - enforcement requires terminal identification")

# In skill_enforcer.py:
# No early return - terminal_id is now guaranteed
```

**Tradeoffs**:
- **Favored**: Correctness (fixes root cause, not symptoms), Strong multi-terminal isolation (true terminal-scoping)
- **Degraded**: May break existing workflows where terminal_id truly isn't available, Adds complexity to detection logic, Potential for false deterministic IDs
- **Failure Conditions**: If all detection sources fail, system errors instead of degrading gracefully
- **ISO 25010**: +Reliability, +Security (strong isolation), -Maintainability (complex detection logic)

**Evidence from codebase**: `__lib/runtime_env.py` already has `get_terminal_id()` function that could be enhanced

---

## Candidate 4: **Dual-Layer Enforcement (Intent Files + Direct Pattern)** (Probability: 0.25)

**Primary Lens**: Consolidation Lens (are we duplicating mechanisms?)

**Approach**: Keep intent files for telemetry AND add a direct pattern-matching layer that doesn't depend on files. The gate works even if intent files are missing.

**Implementation**:
```python
# In PreToolUse_skill_pattern_gate.py:
# Layer 1: Try intent file first (fast path)
slash_command = _read_intent_file(terminal_id)
if slash_command:
    return _check_skill_first_gate(slash_command, tool_name, tool_input)

# Layer 2: Fallback to pattern matching on user_message
# (requires hook input to include user_message)
user_message = data.get("user_message", "")
if user_message:
    import re
    match = re.match(r"^/([a-z0-9-]+)", user_message.strip())
    if match:
        slash_command = match.group(1)
        return _check_skill_first_gate(slash_command, tool_name, tool_input)

# Layer 3: If both fail, allow (fail-open for graceful degradation)
return {"continue": True}
```

**Tradeoffs**:
- **Favored**: Robustness (multiple enforcement layers), Graceful degradation (works even if intent files fail), Backward compatible
- **Degraded**: Complexity (two enforcement mechanisms to maintain), May hide underlying problems, Potential for inconsistency between layers
- **Failure Conditions**: Both layers fail, but fail-open allows execution
- **ISO 25010**: +Reliability (redundancy), -Maintainability (two mechanisms), +Function Suitability (graceful degradation)

**Evidence from codebase**: `PreToolUse_skill_pattern_gate.py` already has parallel validation infrastructure (lines 674-752) that could be extended

---

## Summary Table

| Candidate | Probability | Primary Lens | Favored Quality | Degraded Quality | Complexity |
|-----------|-------------|--------------|-----------------|------------------|------------|
| **1. Hybrid Fallback** | 0.65 | Dependency | Reliability | Security (weaker isolation) | Medium |
| **2. Truly Stateless** | 0.55 | Contract | Performance, Simplicity | Reliability (schema dependency) | High (framework change) |
| **3. Terminal ID Hardening** | 0.45 | Evidence | Correctness, Security | Maintainability | Medium |
| **4. Dual-Layer** | 0.25 | Consolidation | Robustness | Maintainability (duplication) | High |

---

## GoT Analysis

**Extracted Nodes**:
- **Constraints**: ["Multi-terminal isolation REQUIRED", "No external dependencies in hooks", "Graceful degradation required"]
- **Ideas**: ["Session_id fallback", "Truly stateless gate", "Terminal ID hardening", "Dual-layer enforcement"]
- **Risks**: ["Session fallback weakens isolation", "Framework changes required", "Hardening may break workflows", "Dual-layer adds complexity"]
- **Components**: ["skill_enforcer.py", "PreToolUse_skill_pattern_gate.py", "__lib/runtime_env.py"]

**Edge Relationships**:
- "Session_id fallback" supports "Reliability" ✓
- "Truly stateless" supports "Simplicity" ✓
- "Terminal ID hardening" supports "Strong isolation" ✓
- "Dual-layer" supports "Robustness" ✓
- "Session fallback" contradicts "Multi-terminal isolation" ⚠️ (weaker isolation)
- "Truly stateless" contradicts "Hook input schema" ⚠️ (requires framework change)
- "Terminal ID hardening" depends on "Detection sources availability"
- "Dual-layer" contradicts "Consolidation Lens" ⚠️ (duplicates mechanisms)

**Cycles Detected**: None

**Architectural Insights**:
- Tension between Reliability (Candidate 1) and Strong Isolation (Candidate 3)
- Framework change requirement for Candidate 2 may be prohibitive
- Candidate 4 violates consolidation principle (duplicates mechanisms)
- **Recommendation**: Candidate 1 balances reliability with acceptable isolation tradeoff
