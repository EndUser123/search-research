# Implementation Plan: Unified Risk-Tiered Command Safety Gate

**Created:** 2026-03-01
**Status:** DRAFT
**Priority:** HIGH

---

## 1. Problem Statement

Current Claude Code hooks implement tiered command safety behaviors scattered across multiple hooks:

- **Tier 1 (Advisory)**: Implemented in `PreToolUse_observe_before_act_gate.py` (warn at 2 edits, block at 3)
- **Tier 2 (Confirmation)**: Implemented in `PreToolUse_authorization_gate.py` (destructive command authorization)
- **Tier 3 (Deny)**: Implemented in `PreToolUse_path_validator.py` (restricted path protection)

**Problems identified:**
1. **ARCH-002**: Tier overlap conflict - same command could trigger multiple hooks (e.g., `git push --force` is both in DESTRUCTIVE_PATTERNS and should be Tier 1 advisory)
2. **ARCH-003**: No centralized tier classification system - each hook has its own pattern lists
3. **ARCH-006**: Duplicate blocking - multiple hooks can block the same command, creating UX confusion
4. **Maintenance burden**: Adding new command patterns requires updating multiple files

**Desired state:** Single unified `PreToolUse_risk_tier_gate.py` that consolidates all tiered safety behaviors with clear classification rules and deduplication.

---

## 2. Context Analysis

### Hook Protocol Specification

**Source:** `P:\.claude\hooks\PROTOCOL.md:44-96`

**Input Structure (JSON via stdin):**
```python
{
    "tool_name": str,      # "Bash" for command safety
    "tool_input": {
        "command": str      # The command to check
    },
    "session_id": str,     # Optional
    "terminal_id": str,    # Optional
}
```

**Output Options:**

**Option 1: In-Process (Recommended)**
```python
def run(data: dict) -> dict | None:
    """
    Returns:
        None = Allow
        {"decision": "block", "reason": "..."} = Block
        {"continue": True, "advisories": [...]} = Allow with warnings
    """
```

**Option 2: Subprocess**
```python
# Block with exit code 2
sys.exit(2)

# Allow with exit code 0 (stdout optional)
sys.exit(0)
```

**CRITICAL:** Never write to stderr (Claude Code treats ANY stderr as hook error)

### Allowed APIs

| Component | Structure | Source |
|-----------|-----------|--------|
| Hook input | `{"tool_name": str, "tool_input": dict}` | PROTOCOL.md:48-54 |
| In-process return | `None` or `{"decision": "block", "reason": str}` | PreToolUse.py:410-411 |
| Advisory response | `{"continue": True, "advisories": [str]}` | observe_before_act_gate.py:360-365 |
| Registration | Add to `UNIVERSAL` list in PreToolUse.py | PreToolUse.py:308-341 |

### Anti-Patterns to Avoid

**❌ stderr Violation**
```python
# WRONG: Claude Code treats ANY stderr as "hook error"
print("Warning message", file=sys.stderr)  # Triggers hook error UI

# CORRECT: Use stdout JSON for advisories
print(json.dumps({"continue": True, "advisories": ["Warning"]}))
```

**❌ Wrong Exit Codes**
```python
# WRONG: Exit code 1 for blocking
sys.exit(1)  # May not work in routed hooks

# CORRECT: Always use exit code 2 for blocking
sys.exit(2)
```

**❌ Missing from CRITICAL_HOOKS**
```python
# WRONG: Safety hook not in CRITICAL_HOOKS (fails open on error)

# CORRECT: Add to CRITICAL_HOOKS set
CRITICAL_HOOKS = {
    "PreToolUse_risk_tier_gate.py",  # Fail closed
}
```

### Existing Hook Architecture

**Router Pattern:** `PreToolUse.py:365-436`
```python
def run_hook(hook_name: str, data: dict) -> dict | None:
    # 1. Try In-Process Execution (Ultra-fast)
    if hook_name in IN_PROCESS_HOOKS:
        res = IN_PROCESS_HOOKS[hook_name](data)
        if res == "subprocess":
            pass  # Force subprocess fallback
        else:
            return res

    # 2. Subprocess Execution
    # ... subprocess run ...

    # 3. Parse stdout for JSON with decision="block"
```

**Registration:** `PreToolUse.py:308-341`
```python
UNIVERSAL = [
    "PreToolUse_path_validator.py",
    "PreToolUse_observe_before_act_gate.py",
    # Add: "PreToolUse_risk_tier_gate.py"
]

TOOL_HOOKS = {
    "Bash": [
        "PreToolUse_authorization_gate.py",  # After risk_tier_gate
    ]
}
```

### Tier Classification Requirements

Based on proposal and existing patterns:

**Tier 1 (Advisory)** - Log warning, allow execution:
- Global git operations (`git status`, `git diff` without `--` limiter)
- Package operations (`pip install`, `npm install`)
- Docker operations (`docker build`, `docker run`)
- **Rationale:** Reversible operations, common in dev workflow

**Tier 2 (Confirmation)** - Require explicit user authorization:
- Destructive git (`git reset --hard`, `git push --force`, `git branch -D`)
- File deletion (`rm -rf`, `rmdir`, `del`, `rd`)
- Schema changes (`DROP TABLE`, `TRUNCATE`, migrations)
- CI config changes (modifying `.github/workflows/`, `Jenkinsfile`)
- **Rationale:** Destructive but sometimes necessary

**Tier 3 (Deny)** - Block with explanation:
- Production infrastructure (commands touching `/prod/`, `/production/`)
- Secrets directories outside dev mirrors (`/etc/secrets/`, production vaults)
- **Rationale:** Catastrophic risk, no legitimate dev use case

---

## 3. Existing Implementation Discovery

### Current Tiered Safety Implementations

**File:** `P:\.claude\hooks\PreToolUse_observe_before_act_gate.py:1-385`

**Pattern:** Advisory → Block progression
```python
# Lines 156-172
def _check_multi_edit_gate(tool_name, tool_input, state):
    if new_edit_count >= MULTI_EDIT_BLOCK_THRESHOLD:
        return False, reason  # Block
    elif new_edit_count >= MULTI_EDIT_WARNING_THRESHOLD:
        state.setdefault("advisories", []).append(reason)
        return True, ""  # Allow with advisory
```

**Response Format:**
```python
# Lines 360-365
response = {
    "continue": False,
    "reason": reason
}
print(json.dumps(response))
sys.exit(2)
```

---

**File:** `P:\.claude\hooks\PreToolUse_authorization_gate.py:1-646`

**Pattern:** Explicit authorization check
```python
# Lines 64-87 - Destructive patterns
DESTRUCTIVE_PATTERNS = [
    r"git\s+rm\b",
    r"git\s+reset\s+--hard",
    r"git\s+push\s+(-f|--force)",
    r"rm\s+-rf?\b",
    r"drop\s+(table|database|schema)",
]

# Lines 293-306 - Authorization check
def has_explicit_authorization(text: str) -> bool:
    AUTHORIZATION_PATTERNS = [
        r"\bdo\s+it\b",
        r"\bproceed\b",
        r"\bgo\s+ahead\b",
        r"^\d+\b",  # Numbered option
    ]
```

**Confirmation UX:**
```python
# Lines 519-522
"Respond with a number:\n"
"  1 - Proceed\n"
"  2 - Skip/Cancel\n"
"(Or use: 'proceed', 'do it', 'go ahead')"
```

---

**File:** `P:\.claude\hooks\PreToolUse_path_validator.py:1-332`

**Pattern:** Deny based on path
```python
# In-process run() function
def run(data: dict) -> dict | None:
    file_path = data.get("tool_input", {}).get("file_path", "")

    if _is_restricted_path(file_path):
        return {
            "decision": "block",
            "reason": f"RESTRICTED_PATH: {suggested_alternative}"
        }
    return None  # Allow
```

---

### Hook Registration Pattern

**File:** `P:\.claude\hooks\PreToolUse.py:308-341`

```python
# Hooks that run for ALL tool types
UNIVERSAL = [
    "PreToolUse_path_validator.py",
    "PreToolUse_observe_before_act_gate.py",
]

# Hooks by tool type
TOOL_HOOKS = {
    "Bash": [
        "PreToolUse_authorization_gate.py",
        "PreToolUse_bulk_delete_gate.py",
    ],
}
```

### Test Pattern Reference

**File:** `P:\.claude\hooks\tests\test_observe_before_act_gate.py:1-545`

**Test Structure:**
```python
# Lines 22-33 - Fixtures
@pytest.fixture
def sample_session_id() -> str:
    import uuid
    return f"test-session-{uuid.uuid4().hex[:8]}"

# Lines 46-56 - Helper
def run_hook(hook_path: Path, payload: dict) -> tuple[int, str]:
    input_json = json.dumps(payload)
    result = subprocess.run(
        ["python", str(hook_path)],
        input=input_json,
        capture_output=True,
        text=True,
        timeout=5
    )
    return result.returncode, result.stdout

# Lines 79-80 - Assertion
assert exit_code == 0, "First edit without read should be allowed"
```

---

## 4. Test Discovery

### Required Test Coverage

Based on `test_observe_before_act_gate.py` pattern:

**Unit Tests:**
1. **Tier Classification Accuracy**
   - Commands map to correct tier (advisory/confirm/deny)
   - Commands matching no tier return None (allow)
   - Tier 3 (deny) commands always block

2. **Response Handlers**
   - Tier 1 (advisory) returns `{"continue": True, "advisories": [...]}`
   - Tier 2 (confirm) blocks without authorization (exit code 2)
   - Tier 2 (confirm) allows with authorization (`"proceed"`, `"do it"`, numbered)
   - Tier 3 (deny) blocks always (exit code 2)

3. **Deduplication**
   - `tier_checked` flag set in data dict prevents re-check
   - Existing hooks respect `tier_checked` flag (early return)

4. **Edge Cases**
   - Commands matching multiple tier patterns (highest tier wins)
   - Empty command (allow)
   - Command variations (git vs. /usr/bin/git, quoting differences)
   - Session/terminal ID missing (graceful degradation)

**Integration Tests:**
1. Hook executes in UNIVERSAL chain before authorization_gate
2. No duplicate blocking when both hooks present
3. Hook protocol compliance (stdin JSON, stdout JSON, exit codes)

### Test File Structure

**Create:** `P:\.claude\hooks\tests\test_risk_tier_gate.py`

```python
class TestTierClassification:
    def test_git_status_is_tier1_advisory(self, ...):
    def test_rm_rf_is_tier2_confirm(self, ...):
    def test_prod_secrets_is_tier3_deny(self, ...):

class TestResponseHandlers:
    def test_advisory_allows_with_warning(self, ...):
    def test_confirm_blocks_without_authorization(self, ...):
    def test_confirm_allows_with_authorization(self, ...):
    def test_deny_always_blocks(self, ...):

class TestDeduplication:
    def test_tier_checked_flag_prevents_recheck(self, ...):
    def test_authorization_gate_respects_tier_checked(self, ...):

class TestEdgeCases:
    def test_multiple_pattern_match_highest_tier_wins(self, ...):
    def test_empty_command_allows(self, ...):
    def test_missing_session_graceful_degradation(self, ...):
```

---

## 5. Proposed Solution

### Architecture: Single Unified Hook

**Create:** `P:\.claude\hooks\PreToolUse_risk_tier_gate.py`

**Design Principles:**

1. **Centralized Tier Schema** - All command patterns in one place
2. **Highest Tier Wins** - If command matches multiple tiers, use highest risk
3. **Deduplication Flag** - Set `tier_checked` in data to prevent double-blocking
4. **Backward Compatible** - Existing hooks respect `tier_checked` flag

### Component Design

#### 1. Tier Pattern Schema

```python
# Risk tier definitions
RISK_TIERS = {
    "ADVISORY": {
        "level": 1,
        "patterns": [
            r"git\s+status(?!\s+--)",      # git status without path limiter
            r"git\s+diff(?!\s+--)",        # git diff without path limiter
            r"pip\s+install",
            r"npm\s+install",
            r"docker\s+(build|run)",
        ],
        "action": "advisory",
        "message": "Advisory: This command is reversible but should be used with caution."
    },
    "CONFIRM": {
        "level": 2,
        "patterns": [
            r"git\s+reset\s+--hard",
            r"git\s+(push|force)\s+.*(-f|--force)",
            r"git\s+branch\s+-[dD]",
            r"rm\s+-rf?",
            r"rmdir",
            r"del\s+/[fqs]",
            r"rd\s+/[sq]",
            r"drop\s+(table|database|schema)",
            r"truncate\s+table",
        ],
        "action": "ask",
        "message": "Confirmation required: This is a destructive command."
    },
    "DENY": {
        "level": 3,
        "patterns": [
            r"rm\s+-rf\s+.*(/prod/|/production/)",
            r"drop\s+database\s+prod",
            r".*\.env\.prod",  # Production secrets
        ],
        "action": "deny",
        "message": "Blocked: This command targets production infrastructure."
    }
}
```

#### 2. Classification Algorithm

```python
def classify_command(command: str) -> tuple[int, str, str] | None:
    """
    Classify command into risk tier.

    Returns:
        (level, tier_name, message) or None (no tier match)
    """
    command_lower = command.lower()

    # Check tiers in descending order (highest risk first)
    for tier_name in ["DENY", "CONFIRM", "ADVISORY"]:
        tier = RISK_TIERS[tier_name]
        for pattern in tier["patterns"]:
            if re.search(pattern, command_lower):
                return (tier["level"], tier_name, tier["message"])

    return None  # No tier match
```

#### 3. Response Handlers

```python
def handle_advisory(data: dict, message: str) -> dict:
    """Tier 1: Allow with advisory warning."""
    return {
        "continue": True,
        "advisories": [message]
    }

def handle_confirm(data: dict, message: str, command: str) -> dict:
    """Tier 2: Check authorization, block if missing."""
    last_user_msg = get_last_user_message(data)

    if has_explicit_authorization(last_user_msg):
        return None  # Allow

    # Block with confirmation request
    return {
        "decision": "block",
        "reason": (
            f"{message}\n\n"
            f"Command: {command[:100]}\n\n"
            "Respond with a number:\n"
            "  1 - Proceed\n"
            "  2 - Skip/Cancel\n\n"
            "(Or use: 'do it', 'proceed', 'go ahead')"
        )
    }

def handle_deny(data: dict, message: str, command: str) -> dict:
    """Tier 3: Always block."""
    return {
        "decision": "block",
        "reason": (
            f"{message}\n\n"
            f"Command: {command[:100]}\n\n"
            "This operation is not allowed in the development environment."
        )
    }
```

#### 4. Deduplication Coordination

```python
def main():
    data = json.loads(sys.stdin.read())
    command = data.get("tool_input", {}).get("command", "")

    # Check if already tier-checked by this hook
    if data.get("tier_checked"):
        return  # Already handled

    # Classify command
    classification = classify_command(command)
    if not classification:
        return  # No tier match, allow

    level, tier_name, message = classification

    # Set deduplication flag
    data["tier_checked"] = tier_name

    # Dispatch to handler
    if tier_name == "ADVISORY":
        result = handle_advisory(data, message)
        print(json.dumps(result))
        return
    elif tier_name == "CONFIRM":
        result = handle_confirm(data, message, command)
        if result and result.get("decision") == "block":
            print(json.dumps(result))
            sys.exit(2)
        return
    elif tier_name == "DENY":
        result = handle_deny(data, message, command)
        print(json.dumps(result))
        sys.exit(2)
```

### Integration with Existing Hooks

**Update:** `P:\.claude\hooks\PreToolUse_authorization_gate.py`

```python
# Add at top of main()
def main():
    data = json.loads(sys.stdin.read())

    # NEW: Respect tier_checked flag
    if data.get("tier_checked"):
        print(json.dumps({"decision": "allow"}))
        return

    # ... existing authorization logic ...
```

**Register:** `P:\.claude\hooks\PreToolUse.py`

```python
CRITICAL_HOOKS = {
    "PreToolUse_path_validator.py",
    "PreToolUse_authorization_gate.py",
    "PreToolUse_risk_tier_gate.py",  # NEW
}

UNIVERSAL = [
    "PreToolUse_path_validator.py",
    "PreToolUse_risk_tier_gate.py",  # NEW - before observe_before_act
    "PreToolUse_observe_before_act_gate.py",
]
```

### Hook Ordering Justification

Placing `risk_tier_gate` before `observe_before_act_gate` in the UNIVERSAL chain is intentional for three reasons:

1. **Fundamental Classification**: Tier classification is a more fundamental check than behavioral analysis. Commands should be classified by risk level before tracking multi-edit state or detecting skill patterns. Early classification prevents wasted computation on high-risk actions that will be blocked anyway.

2. **State Tracking Hygiene**: The `observe_before_act_gate` tracks per-file edit counts in session state. If a destructive command (Tier 3 DENY) is blocked, we should not increment those counters. Blocking earlier prevents state pollution from actions that never executed.

3. **Performance Optimization**: High-risk operations (schema migrations, production infra changes) should be blocked immediately rather than after downstream hooks have run. This reduces hook execution overhead for blocked actions.

### Pattern Synchronization Strategy

During the transition period, `authorization_gate.py` continues to exist alongside the new unified `risk_tier_gate.py`. Pattern definitions (DESTRUCTIVE_PATTERNS, AUTHORIZATION_PATTERNS) are duplicated with deprecation comments.

**Approach: Copy with Deprecation Comment**

```python
# DEPRECATED: Patterns now defined in PreToolUse_risk_tier_gate.py
# This copy maintained for backward compatibility during transition.
# TODO: Remove this file after verification phase (2026-Q2).
DESTRUCTIVE_PATTERNS = [
    # ... patterns ...
]
```

**Rejected Alternatives:**

- **Shared Config Module**: Import patterns from a `risk_tier_config.py` module. Rejected due to I/O overhead (file read on every hook execution) and complexity (managing module imports vs. subprocess isolation).

- **Sync Script**: Run a sync script to update both files when patterns change. Rejected as over-engineering - human copy-paste with deprecation comments is simpler and less error-prone for this transition period.

**Migration Path:**

After `risk_tier_gate.py` is verified working (2026-Q2), deprecate and remove `authorization_gate.py` entirely. The `tier_checked` deduplication flag prevents double-blocking during the transition.

---

## 5.5. Alternative Approaches

This section evaluates alternative design options against the recommended unified hook solution.

### Option A: Unified Risk-Tier Hook (RECOMMENDED)

**Description:** Single `PreToolUse_risk_tier_gate.py` consolidates all tiered behaviors with centralized `RISK_TIERS` schema and `tier_checked` deduplication.

**Trade-offs:**
| Aspect | Impact | Rationale |
|--------|--------|-----------|
| **Complexity** | **MEDIUM** - Single file with 3-tier logic | Moderate complexity, clear separation of concerns |
| **Maintenance** | **LOW** - One place to update patterns | Adding new commands requires updating only `RISK_TIERS` |
| **Performance** | **FAST** - In-process (~1-2ms) | Direct function call, minimal overhead |
| **UX** | **GOOD** - Single confirmation dialog | Users see consistent tier-based responses |
| **Integration** | **LOW EFFORT** - Add tier_checked flag to existing hooks | Minimal changes to `authorization_gate.py` |

**Advantages:**
- ✅ Single source of truth for command classification
- ✅ Eliminates duplicate blocking (tier_checked coordination)
- ✅ Easy to extend (add new tier or pattern in one place)
- ✅ Clear tier hierarchy (DENY → CONFIRM → ADVISORY)

**Disadvantages:**
- ⚠️ Requires updating existing hooks to respect `tier_checked` flag
- ⚠️ Single file becomes larger (~500 lines vs ~200 lines per hook)
- ⚠️ If unified hook fails, all tiered safety fails (mitigated by CRITICAL_HOOKS)

---

### Option B: Separate Hooks with Shared Configuration

**Description:** Keep `authorization_gate.py`, `observe_before_act_gate.py`, `path_validator.py` separate but share pattern definitions from a central `risk_tiers.json` config file.

**Architecture:**
```
PreToolUse_risk_tier_gate.py (NEW - coordinator)
  ├── Reads RISK_TIERS from config/risk_tiers.json
  ├── Delegates to existing hooks based on tier
  └── Sets tier_checked flag to prevent duplicate execution

authorization_gate.py
  ├── Reads RISK_TIERS from config/risk_tiers.json (CONFIRM tier)
  └── Checks authorization for CONFIRM-tier commands

observe_before_act_gate.py
  ├── Reads RISK_TIERS from config/risk_tiers.json (ADVISORY tier)
  └── Tracks multi-edit state separately

path_validator.py
  ├── Reads RESTRICTED_PATHS from config/directory_policy.json
  └── Continues path-based protection (unchanged)
```

**Trade-offs:**
| Aspect | Impact | Rationale |
|--------|--------|-----------|
| **Complexity** | **HIGH** - Config file + coordinator + 3 hooks | More moving parts, config file parsing overhead |
| **Maintenance** | **MEDIUM** - Update config, hooks auto-sync | Adding patterns requires config update only, but hooks must parse config |
| **Performance** | **SLOWER** - Config file I/O on each hook execution | File reads add ~1-3ms per hook, ~3-9ms total for 3 hooks |
| **UX** | **GOOD** - Same behavior as Option A (tier_checked coordination) | Consistent tier-based responses, but slightly slower |
| **Integration** | **MEDIUM EFFORT** - Create config file, add coordinator | New config file format, coordinator hook, config parsing logic |

**Advantages:**
- ✅ Existing hooks mostly unchanged (only add config reading)
- ✅ Clear separation of concerns (each hook still owns its logic)
- ✅ Config file can be reloaded without restarting hooks
- ✅ Easier to test (each hook can be tested independently)

**Disadvantages:**
- ❌ More complex architecture (3 hooks + config + coordinator)
- ❌ Config file I/O on every hook execution (performance cost)
- ❌ Config file parsing errors could break all hooks simultaneously
- ❌ More files to maintain (config schema + 3 hooks + coordinator)

**Rejection Rationale:** This option adds unnecessary complexity for a problem that doesn't need runtime configuration. The tier patterns don't change frequently enough to justify a config file system.

---

### Option C: Keep Existing Hooks, Add Coordination Layer

**Description:** No new unified hook. Instead, add a lightweight coordinator that:
1. Runs first in UNIVERSAL chain
2. Classifies command tier
3. Sets `tier_checked` flag
4. Each existing hook respects `tier_checked` flag (early return)

**Architecture:**
```
PreToolUse_risk_tier_coordinator.py (NEW - lightweight classifier)
  ├── Classifies command into tier
  ├── Sets data["tier_checked"] = "ADVISORY"|"CONFIRM"|"DENY"
  └── Exits (no blocking, just sets flag)

authorization_gate.py (MODIFIED)
  ├── Check: if data.get("tier_checked") == "CONFIRM": return
  ├── Check: if data.get("tier_checked") in ["ADVISORY", "DENY"]: return
  └── Existing CONFIRM-tier logic continues

observe_before_act_gate.py (UNCHANGED)
  ├── Multi-edit tracking (separate concern)
  └── No tier coordination needed

path_validator.py (UNCHANGED)
  └── Path-based protection (separate concern)
```

**Trade-offs:**
| Aspect | Impact | Rationale |
|--------|--------|-----------|
| **Complexity** | **LOW-MEDIUM** - New coordinator, minimal changes to existing | Coordinator is simple (~100 lines), existing hooks mostly unchanged |
| **Maintenance** | **MEDIUM** - Update coordinator patterns, existing hooks unchanged | Pattern updates in coordinator only, but authorization_gate needs tier_checked logic |
| **Performance** | **FAST** - Coordinator is lightweight (~1ms), existing hooks unchanged | Minimal overhead, fast path through existing hooks |
| **UX** | **GOOD** - Same behavior, existing hooks preserved | Users see same responses, hooks maintain their current behavior |
| **Integration** | **LOW-MEDIUM EFFORT** - Add coordinator, modify authorization_gate | New coordinator file, add tier_checked checks to 1-2 existing hooks |

**Advantages:**
- ✅ Minimal changes to existing hooks (preserve investment)
- ✅ Coordinator is simple and focused (classification only)
- ✅ Existing hook behaviors preserved (less regression risk)
- ✅ Performance is good (lightweight coordinator + existing fast paths)

**Disadvantages:**
- ⚠️ Still have duplicate pattern definitions (coordinator + authorization_gate)
- ⚠️ Pattern drift risk (coordinator and authorization_gate patterns diverge over time)
- ⚠️ Requires ongoing synchronization when patterns are added
- ⚠️ Three hooks still run (vs. one unified hook)

**Rejection Rationale:** This option preserves existing hooks but creates a synchronization problem. The coordinator and `authorization_gate.py` would both need CONFIRM-tier patterns, leading to duplication and drift risk.

---

### Option D: Do Nothing (Document Current Behavior)

**Description:** No new hooks. Accept current scattered tier implementation as-is. Document which hooks handle which tiers in CLAUDE.md or hooks README.

**Trade-offs:**
| Aspect | Impact | Rationale |
|--------|--------|-----------|
| **Complexity** | **NONE** - No changes | Keep current architecture |
| **Maintenance** | **HIGH** - Update 3 separate hooks for new patterns | Adding patterns requires updating multiple files |
| **Performance** | **FAST** - No new overhead | Existing hook chain unchanged |
| **UX** | **POOR** - Duplicate blocking persists | Users see multiple block messages for same command |
| **Integration** | **NO EFFORT** - Documentation only | No code changes required |

**Advantages:**
- ✅ Zero implementation effort
- ✅ No regression risk (existing hooks unchanged)
- ✅ No performance degradation

**Disadvantages:**
- ❌ ARCH-002 (tier overlap conflict) remains UNRESOLVED
- ❌ ARCH-003 (no centralized classification) remains UNRESOLVED
- ❌ ARCH-006 (duplicate blocking) remains UNRESOLVED
- ❌ Maintenance burden remains HIGH (update 3 files per pattern change)

**Rejection Rationale:** This option leaves all identified problems unresolved. The architecture review specifically identified these as issues that need fixing.

---

### Comparison Matrix

| Criterion | Option A (Unified) | Option B (Shared Config) | Option C (Coordinator) | Option D (Do Nothing) |
|-----------|------------------|------------------------|---------------------|-------------------|
| **Solves ARCH-002?** | ✅ Yes (single classifier) | ✅ Yes (shared patterns) | ⚠️ Partial (coordination only) | ❌ No |
| **Solves ARCH-003?** | ✅ Yes (centralized schema) | ✅ Yes (config file) | ⚠️ Partial (coordinator patterns) | ❌ No |
| **Solves ARCH-006?** | ✅ Yes (tier_checked flag) | ✅ Yes (tier_checked flag) | ✅ Yes (tier_checked flag) | ❌ No |
| **Implementation Complexity** | MEDIUM (1 new file, 1 file update) | HIGH (config + coordinator + updates) | LOW-MEDIUM (coordinator + 1 update) | NONE (docs only) |
| **Maintenance Burden** | LOW (1 file) | MEDIUM (config + 4 files) | MEDIUM (coordinator + 3 files) | HIGH (3 files) |
| **Performance** | FAST (~1-2ms) | SLOWER (~3-9ms with I/O) | FAST (~1-2ms + existing) | FAST (unchanged) |
| **UX Quality** | GOOD (single dialog) | GOOD (single dialog) | GOOD (single dialog) | POOR (duplicate blocks) |
| **Regression Risk** | MEDIUM (modifies existing hooks) | HIGH (changes hook + adds config) | LOW-MEDIUM (minimal changes) | NONE (no changes) |
| **Scalability** | GOOD (easy to extend) | GOOD (config updates) | FAIR (coordinator updates) | POOR (3 file updates) |

---

### Recommendation

**Choose Option A (Unified Risk-Tier Hook)**

**Why this is optimal:**

1. **Solves all identified problems** (ARCH-002, ARCH-003, ARCH-006)
2. **Best balance of complexity and maintainability** (single source of truth)
3. **Good performance** (in-process, no config file I/O)
4. **Clear architecture** (easy to understand and extend)
5. **Reasonable regression risk** (CRITICAL_HOOKS ensures fail-closed behavior)

**Why not other options:**
- **Option B**: Unnecessary complexity (config file I/O) for a problem that doesn't need runtime configuration
- **Option C**: Pattern synchronization problem (coordinator and authorization_gate drift risk)
- **Option D**: Leaves all problems unresolved

---

### Risk Mitigation for Chosen Approach

**Risk:** Existing hook modification could introduce bugs

**Mitigation Strategy:**
1. **Phased rollout** - Implement and test unified hook before modifying existing hooks
2. **Backward compatibility** - Keep existing hooks as fallback during transition
3. **Comprehensive testing** - 23 tests covering all tier combinations and edge cases
4. **Rollback plan** - Revert UNIVERSAL registration if issues occur (documented in Section 7)

**Implementation Confidence:** HIGH - Based on:
- ✅ Complete documentation discovery (all APIs verified)
- ✅ Existing working patterns to copy from
- ✅ Test pattern reference from `observe_before_act_gate.py`
- ✅ Clear rollback strategy (revert UNIVERSAL registration)

---

## 6. Pre-Mortem Analysis (Failure Mode Prevention)

**Methodology**: Imagine it's September 2026 (6 months from now) and the Unified Risk-Tiered Command Safety Gate has **failed** or caused **significant production problems**. Work backward to identify root causes and preventive actions.

### Failure Mode #1: Pattern False Positives Block Legitimate Work (HIGH Severity)

**Symptoms**:
- Developers can't run legitimate commands like `git status` in repos named "production"
- `docker build` commands blocked even when targeting test environment
- Frustration leads to users disabling hooks entirely via bypass

**Root Causes**:
1. **Overly broad regex patterns** - `r"docker.*(build|run)"` matches `docker build -t test-app`
2. **No context awareness** - Pattern matches command string regardless of CWD or environment
3. **No allow-list mechanism** - No way to say "this specific repo/script is safe"

**Preventive Actions** ✅:

1. **Add Context-Aware Pattern Matching** (modify Phase 2.5):
   ```python
   def classify_command(command: str, cwd: str | None = None) -> tuple[int, str, str] | None:
       # Check if in known safe directory (e.g., test/ environment)
       if cwd and ("/test/" in cwd or "/dev/" in cwd):
           # Relax restrictions for test environments
           if "production" not in command.lower():
               return None  # Allow
       # ... rest of classification
   ```

2. **Add Allow-List Configuration** (new Phase 2.5):
   ```python
   # In PreToolUse_risk_tier_gate.py
   ALLOWED_CONTEXTS = {
       "test_docker_builds": [r".*test.*\.dockerfile$", r"/test/"],
       "dev_git_reset": [r".*/dev/.*", r".*-dev\.git"],
   }
   ```

3. **Make Patterns More Specific** (update RISK_TIERS):
   ```python
   # BEFORE (too broad):
   r"docker.*(build|run)"

   # AFTER (context-aware):
   r"docker\s+(build|run)\s+.*(-t\s+prod|--tag=production)"
   ```

**Test to Add**:
```python
def test_docker_build_allowed_in_test_env(self):
    """Docker build in test directory should not trigger Tier 1 advisory."""
    cmd = {"tool_name": "Bash", "tool_input": {"command": "docker build -t test-app", "cwd": "/test/"}}
    result = run_hook("PreToolUse_risk_tier_gate.py", cmd)
    assert result["continue"] is True  # No advisory
```

---

### Failure Mode #2: Multi-Terminal `tier_checked` Race Condition (CRITICAL Severity)

**Symptoms**:
- Terminal A blocks `rm -rf` command (sets `tier_checked: "CONFIRM"`)
- Terminal B sees `tier_checked` flag from Terminal A and skips its own check
- Terminal B executes destructive command without confirmation
- **Data loss occurs**

**Root Causes**:
1. **Shared state file collision** - Multiple terminals read/write same state file
2. **No terminal isolation** - `tier_checked` flag not scoped to terminal_id
3. **Stale flag re-use** - Flag from previous session re-used in new session

**Preventive Actions** ✅:

1. **Scope `tier_checked` to Terminal + Session** (modify Phase 3):
   ```python
   # In main(), AFTER reading data dict:
   terminal_id = data.get("terminal_id", "")
   session_id = data.get("session_id", "")

   # Check tier_checked for THIS terminal only
   checked_key = f"tier_checked_{terminal_id}_{session_id}"
   if data.get(checked_key):
       return None  # Already checked

   # Later, AFTER classification:
   data[checked_key] = tier_name  # Scoped to terminal
   ```

2. **Add TTL to `tier_checked` Flag**:
   ```python
   def is_tier_check_valid(data: dict, terminal_id: str) -> bool:
       """Check if tier_checked flag is still valid (within 5 minutes)."""
       checked_key = f"tier_checked_{terminal_id}"
       checked_at = data.get(f"{checked_key}_at")
       if not checked_at:
           return False

       age_seconds = time.time() - checked_at
       return age_seconds < 300  # 5 minutes
   ```

**Test to Add**:
```python
def test_tier_checked_scoped_to_terminal(self):
    """tier_checked from Terminal A should not affect Terminal B."""
    terminal_a = {"tool_name": "Bash", "tool_input": {"command": "rm -rf test"}, "terminal_id": "A"}
    terminal_b = {"tool_name": "Bash", "tool_input": {"command": "rm -rf test"}, "terminal_id": "B"}

    # Terminal A sets flag
    result_a = run_hook("PreToolUse_risk_tier_gate.py", terminal_a)
    assert result_a["decision"] == "block"

    # Terminal B should NOT see Terminal A's flag
    result_b = run_hook("PreToolUse_risk_tier_gate.py", terminal_b)
    assert result_b["decision"] == "block"  # Still blocks, not skipped
```

---

### Failure Mode #3: Hook Ordering Breaks `observe_before_act_gate` (MEDIUM Severity)

**Symptoms**:
- Multi-edit detection stops working
- Users can edit files 10+ times without reading them first
- Code corruption occurs from incomplete context edits

**Root Causes**:
1. **Early blocking prevents state tracking** - `risk_tier_gate` blocks before `observe_before_act_gate` can increment counters
2. **State tracking logic assumes all tools run** - Counters only increment if hook allows execution
3. **No fallback tracking** - Blocked commands don't count toward edit limits

**Preventive Actions** ✅:

1. **Track State BEFORE Classification** (modify `observe_before_act_gate.py`):
   ```python
   # In observe_before_act_gate.py main()

   # Track state FIRST, before any other checks
   tool_name = data.get("tool_name", "")
   tool_input = data.get("tool_input", {})

   if _is_edit_tool(tool_name):
       file_path = tool_input.get("file_path", "")
       if file_path:
           file_key = f"file:{file_path}"
           state["edit_attempts"][file_key] = state["edit_attempts"].get(file_key, 0) + 1
           _save_state(terminal_id, session_id, state)

   # NOW run validation checks (which may block)
   ```

**Test to Add**:
```python
def test_blocked_command_still_counts_toward_edit_limit(self):
    """Command blocked by risk_tier_gate should still increment edit counter."""
    # First edit: allowed
    cmd1 = {"tool_name": "Edit", "tool_input": {"file_path": "test.py", ...}}
    run_hook("observe_before_act_gate.py", cmd1)

    # Second edit: blocked by risk_tier_gate (Tier 2)
    cmd2 = {"tool_name": "Edit", "tool_input": {"file_path": "test.py", ...}}
    result = run_hook("PreToolUse_risk_tier_gate.py", cmd2)
    assert result["decision"] == "block"

    # Third edit: should still warn (2 edits attempted)
    cmd3 = {"tool_name": "Edit", "tool_input": {"file_path": "test.py", ...}}
    result = run_hook("observe_before_act_gate.py", cmd3)
    assert "advisories" in result  # Warning about 2 edits
```

---

### Failure Mode #4: Authorization Detection Broken (HIGH Severity)

**Symptoms**:
- Claude Code updates to v1.5 with new chat format
- `get_last_user_message()` returns empty string or wrong message
- All confirmation checks fail, blocking legitimate work
- Users forced to use bypass constantly

**Root Causes**:
1. **Hardcoded transcript structure assumptions** - Code assumes specific JSON schema
2. **No version detection** - Function doesn't adapt to Claude Code version
3. **No fallback mechanism** - Fails hard instead of degrading gracefully

**Preventive Actions** ✅:

1. **Add Version Detection** (modify Phase 2):
   ```python
   def get_last_user_message(data: dict) -> str | None:
       """Get last user message with Claude Code version detection."""
       transcript = data.get("transcript", [])
       if transcript:
           # New format: list of {"role": "user", "content": "..."}
           for msg in reversed(transcript):
               if msg.get("role") == "user":
                   content = msg.get("content", "")
                   if isinstance(content, str):
                       return content

       # Fallback to old format (Claude Code < 1.5)
       # ... existing logic ...

       return None  # No message found
   ```

2. **Add Graceful Degradation**:
   ```python
   def handle_confirm(data: dict, message: str) -> dict:
       """Tier 2: Require explicit authorization."""
       last_msg = get_last_user_message(data)

       if last_msg is None:
           # Detection failed, but don't block - log and allow
           log_hook_event("authorization_detection_failed", {"data": data})
           return None  # Allow (fail open for detection failures)

       # ... rest of authorization logic ...
   ```

**Test to Add**:
```python
def test_authorization_detection_fails_gracefully(self):
    """When get_last_user_message fails, hook should allow (not block)."""
    cmd = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf test"},
        "transcript": []  # Empty transcript - detection fails
    }
    result = run_hook("PreToolUse_risk_tier_gate.py", cmd)
    assert result["decision"] != "block"  # Should allow, not block
```

---

### Failure Mode #5: Pattern Drift During Transition (MEDIUM Severity)

**Symptoms**:
- New pattern added to `risk_tier_gate.py` but not `authorization_gate.py`
- Commands trigger different hooks depending on which runs first
- Inconsistent UX: sometimes confirms, sometimes doesn't
- Developers lose trust in safety system

**Root Causes**:
1. **Manual sync process error-prone** - Humans forget to copy patterns
2. **No automated diff detection** - No test that catches pattern mismatches
3. **Deprecation comments ignored** - Developers don't see TODO comments

**Preventive Actions** ✅:

1. **Add Pattern Sync Test** (new Phase 6.5):
   ```python
   def test_patterns_synced_between_hooks(self):
       """Ensure risk_tier_gate and authorization_gate have matching CONFIRM patterns."""
       import PreToolUse_risk_tier_gate as risk_gate
       import PreToolUse_authorization_gate as auth_gate

       risk_patterns = set(risk_gate.RISK_TIERS["CONFIRM"]["patterns"])
       auth_patterns = set(auth_gate.DESTRUCTIVE_PATTERNS)

       # Should match (or auth_gate should be subset during transition)
       assert auth_patterns.issubset(risk_patterns), (
           f"Pattern mismatch! auth_gate has patterns not in risk_gate: "
           f"{auth_patterns - risk_patterns}"
       )
   ```

2. **Add Pre-Commit Hook for Pattern Sync**:
   ```bash
   # .git/hooks/pre-commit
   python .claude/hooks/tests/test_pattern_sync.py
   ```

3. **Document Migration Deadline** in Section 5.4:
   > **Migration Deadline**: 2026-06-01 - After this date, `authorization_gate.py` will be deprecated and removed. All pattern updates MUST go to `risk_tier_gate.py` only.

---

### Pre-Mortem Summary

**Top 5 Failure Modes (Ranked by Severity)**:

| Rank | Failure Mode | Impact | Prevention Effort |
|------|--------------|--------|-------------------|
| **#2** | **Multi-Terminal Race Condition** | **CRITICAL** - Data loss | MEDIUM (scope tier_checked) |
| **#1** | **Pattern False Positives** | HIGH - Legitimate work blocked | MEDIUM (context-aware patterns) |
| **#4** | **Authorization Detection Broken** | HIGH - System unusable | LOW (version detection) |
| **#3** | **Hook Ordering Regression** | MEDIUM - Multi-edit checks broken | LOW (track state early) |
| **#5** | **Pattern Drift** | MEDIUM - Inconsistent UX | LOW (sync test) |

**Implementation Confidence After Pre-Mortem**:

- **Before**: HIGH ✅
- **After**: **MEDIUM-HIGH** ⚠️ → ✅

**Reasoning**: All failure modes are preventable with specific mitigations. Most are low-medium effort. No showstoppers identified.

**Updated Phase Plan**: All preventive measures integrated into implementation phases below.

---

## 7. Implementation Plan (Updated with Pre-Mortem Mitigations)

### Phase 1: Create Hook Skeleton (10 min)

**Task:** Create `PreToolUse_risk_tier_gate.py` with basic structure

1. Create file with standard imports (json, sys, re)
2. Define `RISK_TIERS` constant with pattern lists
3. Implement `classify_command()` function
4. Implement `main()` with stdin/stdout handling
5. Test basic execution (no classification yet)

**Verification:**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"echo test"}}' | python P:\.claude\hooks\PreToolUse_risk_tier_gate.py
# Expected: exit code 0, no output (allow)
```

---

### Phase 2: Implement Tier Classification (25 min)

**Task:** Implement classification logic and response handlers with pre-mortem mitigations

1. Implement `classify_command()` with **context-aware** regex pattern matching (Failure Mode #1 prevention)
2. Implement `handle_advisory()` with JSON response
3. Implement `handle_confirm()` with **version-aware** authorization check (Failure Mode #4 prevention)
4. Implement `handle_deny()` with block response
5. Add `get_last_user_message()` helper with version detection and graceful degradation

**Context-Aware Classification** (NEW - prevents false positives):
```python
def classify_command(command: str, cwd: str | None = None) -> tuple[int, str, str] | None:
    """Classify command into risk tier with context awareness."""
    command_lower = command.lower()

    # Check if in known safe directory (e.g., test/ environment)
    if cwd and ("/test/" in cwd or "/dev/" in cwd):
        # Relax restrictions for test environments
        if "production" not in command_lower:
            return None  # Allow - safe context

    # Check tiers in descending order (highest risk first)
    for tier_name in ["DENY", "CONFIRM", "ADVISORY"]:
        tier = RISK_TIERS[tier_name]
        for pattern in tier["patterns"]:
            if re.search(pattern, command_lower):
                return (tier["level"], tier_name, tier["message"])

    return None  # No tier match
```

**Version-Aware Authorization Detection** (UPDATED - prevents breakage):
```python
def get_last_user_message(data: dict) -> str | None:
    """Get last user message with Claude Code version detection."""
    transcript = data.get("transcript", [])
    if transcript:
        # New format: list of {"role": "user", "content": "..."}
        for msg in reversed(transcript):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content

    # Fallback to old format (Claude Code < 1.5)
    # ... existing logic from authorization_gate.py:412-483 ...

    return None  # No message found
```

**Graceful Degradation** (NEW - prevents system unusable):
```python
def handle_confirm(data: dict, message: str) -> dict:
    """Tier 2: Require explicit authorization."""
    last_msg = get_last_user_message(data)

    if last_msg is None:
        # Detection failed, but don't block - log and allow
        log_hook_event("authorization_detection_failed", {"data": data})
        return None  # Allow (fail open for detection failures)

    # ... rest of authorization logic ...
```

**Verification:**
```bash
# Test advisory
echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: {"continue":true,"advisories":["Advisory: ..."]}

# Test confirm (no auth)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"}}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: exit code 2, {"decision":"block","reason":"Confirmation required: ..."}

# Test context-aware (docker in test dir)
echo '{"tool_name":"Bash","tool_input":{"command":"docker build -t test","cwd":"/test/"}}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: {"continue":true} (no advisory - safe context)

# Test graceful degradation (empty transcript)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"},"transcript":[]}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: {"decision":"allow"} (detection failed, fail open)
```

---

### Phase 3: Implement Deduplication (20 min)

**Task:** Add terminal-scoped `tier_checked` flag to prevent double-blocking (Failure Mode #2 prevention)

1. Extract `terminal_id` and `session_id` from data dict
2. Create terminal-scoped key: `f"tier_checked_{terminal_id}_{session_id}"`
3. Add **TTL validation** for stale flags (5-minute timeout)
4. Set `data[checked_key] = tier_name` after classification

**Terminal-Scoped Deduplication** (UPDATED - prevents race condition):
```python
def main():
    # ... read stdin ...

    # Extract terminal and session IDs
    terminal_id = data.get("terminal_id", "")
    session_id = data.get("session_id", "")

    # Check tier_checked for THIS terminal only
    checked_key = f"tier_checked_{terminal_id}_{session_id}"
    checked_at_key = f"{checked_key}_at"

    if data.get(checked_key):
        # Verify flag is still valid (within 5 minutes)
        checked_at = data.get(checked_at_key, 0)
        age_seconds = time.time() - checked_at
        if age_seconds < 300:  # 5 minutes
            return None  # Already checked and valid

    # ... perform classification ...

    # After classification, set terminal-scoped flag
    data[checked_key] = tier_name
    data[checked_at_key] = time.time()
```

**Verification:**
```bash
# Test that tier_checked prevents recheck
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"},"tier_checked_TERM1_SESS1":"CONFIRM","tier_checked_TERM1_SESS1_at":'$(date +%s)'}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: exit code 0, no output (allow, already checked)

# Test terminal isolation (Terminal B should not see Terminal A's flag)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"},"tier_checked_TERM2_SESS1":"CONFIRM","terminal_id":"TERM2"}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: exit code 2 (blocks - different terminal)

# Test TTL expiration (old flag ignored)
OLD_TIME=$(($(date +%s) - 400))  # 6 minutes 40 seconds ago
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"},"tier_checked_TERM1_SESS1":"CONFIRM","tier_checked_TERM1_SESS1_at":'$OLD_TIME'}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: exit code 2 (blocks - flag expired)
```
3. Verify flag is passed through hook chain

**Verification:**
```bash
# Test that tier_checked prevents re-check
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf test"},"tier_checked":"CONFIRM"}' | python hooks/PreToolUse_risk_tier_gate.py
# Expected: exit code 0, no output (allow, already checked)
```

---

### Phase 4: Update Existing Hooks (15 min)

**Task:** Make `authorization_gate.py` respect `tier_checked` flag

1. Open `PreToolUse_authorization_gate.py`
2. Add early return if `data.get("tier_checked")` exists
3. Test that rm -rf only triggers `risk_tier_gate`, not both hooks

**Verification:**
```bash
# Test with both hooks registered
# Command: rm -rf test
# Expected: Only risk_tier_gate blocks, authorization_gate allows (tier_checked)
```

---

### Phase 5: Register Hook (5 min)

**Task:** Add to UNIVERSAL list and CRITICAL_HOOKS

1. Open `PreToolUse.py`
2. Add `"PreToolUse_risk_tier_gate.py"` to `CRITICAL_HOOKS` set
3. Add to `UNIVERSAL` list (before `observe_before_act_gate.py`)
4. Test registration with `python tests/test_hook_registration.py`

**Verification:**
```bash
python P:\.claude\hooks\tests\test_hook_registration.py
# Expected: All hooks registered, no "dead hooks" reported
```

---

### Phase 6: Write Test Suite (45 min)

**Task:** Create comprehensive test coverage

1. Create `test_risk_tier_gate.py`
2. Implement `TestTierClassification` class (9 tests)
3. Implement `TestResponseHandlers` class (8 tests)
4. Implement `TestDeduplication` class (2 tests)
5. Implement `TestEdgeCases` class (4 tests)
6. Fix any test failures

**Test Structure:**
```python
@pytest.fixture
def hook_path():
    return Path(__file__).parent.parent / "PreToolUse_risk_tier_gate.py"

def run_hook(hook_path, payload):
    # ... subprocess call ...
```

**Verification:**
```bash
pytest P:\.claude\hooks/tests/test_risk_tier_gate.py -v
# Expected: All tests pass (23 tests)
```

---

### Phase 7: Integration Testing (20 min)

**Task:** Verify hook chain behavior

1. Test UNIVERSAL hook execution order
2. Test that `observe_before_act_gate` still works for multi-edit
3. Test that `authorization_gate` respects `tier_checked`
4. Test with actual Claude Code session (run a risky command)

**Verification:**
- No duplicate blocking messages
- Tier 1 (advisory) allows with warning
- Tier 2 (confirm) blocks until authorization
- Tier 3 (deny) always blocks

---

## 7. Risks, Success Criteria, Dependencies

### Risks

**Technical Risks:**

1. **Pattern Conflict** (MEDIUM)
   - **Risk:** Command matches multiple tier patterns, unclear which wins
   - **Mitigation:** "Highest tier wins" algorithm (check DENY → CONFIRM → ADVISORY in order)
   - **Test:** `test_multiple_pattern_match_highest_tier_wins`

2. **False Positives** (MEDIUM)
   - **Risk:** Legitimate dev commands repeatedly warned (e.g., `pip install` during setup)
   - **Mitigation:** Tier 1 is advisory only (allows execution), user can dismiss
   - **Test:** Manual verification with common dev workflows

3. **Hook Chain Latency** (LOW)
   - **Risk:** Adding UNIVERSAL hook increases latency for all tools
   - **Mitigation:** In-process execution (fast, ~1-2ms per hook)
   - **Test:** Benchmark before/after hook registration

4. **Authorization Pattern Miss** (LOW)
   - **Risk:** `authorization_gate` has authorization patterns not copied to `risk_tier_gate`
   - **Mitigation:** Copy AUTHORIZATION_PATTERNS from authorization_gate.py:89-112
   - **Test:** Verify all authorization patterns work in new hook

**Operational Risks:**

1. **User Confusion** (MEDIUM)
   - **Risk:** Two different confirmation dialogs if deduplication fails
   - **Mitigation:** `tier_checked` flag must be set correctly, tested in Phase 3
   - **Rollback:** Revert UNIVERSAL registration if duplicate blocking occurs

2. **Pattern Maintenance** (LOW)
   - **Risk:** New tools/commands need pattern updates
   - **Mitigation:** Single file to update (better than scattered hooks)
   - **Process:** Document pattern addition in code comments

### Success Criteria

1. ✅ **Functional Requirements**
   - Single hook replaces tiered safety across all bash commands
   - Tier classification accuracy >95% (verified by tests)
   - No duplicate blocking (tier_checked flag works)
   - All 23 tests pass

2. ✅ **Non-Functional Requirements**
   - Hook latency <5ms (in-process execution)
   - Hook registration successful (no "dead hooks")
   - Backward compatible (existing hooks respect tier_checked)

3. ✅ **Integration Requirements**
   - UNIVERSAL chain execution order correct
   - `observe_before_act_gate` still works for multi-edit detection
   - `authorization_gate` allows when `tier_checked` is set

4. ✅ **Documentation Requirements**
   - Pattern addition documented in code comments
   - Tier definitions clear (advisory/confirm/deny)
   - Hook protocol compliance verified (no stderr, exit code 2 for block)

### Dependencies

**Required Files (Must Exist):**
- `P:\.claude\hooks\PROTOCOL.md` ✅ (verified)
- `P:\.claude\hooks\PreToolUse.py` ✅ (verified)
- `P:\.claude\hooks\PreToolUse_authorization_gate.py` ✅ (verified)
- `P:\.claude\hooks\PreToolUse_observe_before_act_gate.py` ✅ (verified)
- `P:\.claude\hooks\tests/test_observe_before_act_gate.py` ✅ (reference pattern)

**Required Modules (Standard Library):**
- `json` ✅
- `sys` ✅
- `re` ✅
- `pathlib.Path` ✅

**No External Dependencies:** All required modules are in Python standard library.

### Rollback Strategy

**If implementation fails:**
1. Remove `PreToolUse_risk_tier_gate.py` from UNIVERSAL list
2. Revert changes to `authorization_gate.py` (remove tier_checked check)
3. Delete `test_risk_tier_gate.py` (or keep for future reference)
4. Existing hooks continue working (no breaking changes)

**If duplicate blocking occurs:**
1. Check that `tier_checked` is being set correctly
2. Verify `authorization_gate` has early return for `tier_checked`
3. Add debug logging to verify hook chain order
4. Fall back to keeping hooks separate (document known conflict)

---

## Next Actions

1. **Start Implementation:** Begin Phase 1 (Create Hook Skeleton)
   ```bash
   # Create file with basic structure
   touch P:\.claude\hooks\PreToolUse_risk_tier_gate.py
   ```

2. **Verify Dependencies:** Confirm all required files exist
   ```bash
   ls -la P:\.claude\hooks\PROTOCOL.md
   ls -la P:\.claude\hooks\PreToolUse.py
   ls -la P:\.claude\hooks\PreToolUse_authorization_gate.py
   ```

3. **Run Verification Tests:** After Phase 6, run test suite
   ```bash
   pytest P:\.claude\hooks\tests\test_risk_tier_gate.py -v
   ```

4. **Integration Test:** After Phase 7, test with actual Claude Code
   ```bash
   # Test Tier 2 confirmation flow
   echo "Testing rm -rf confirmation"
   # Trigger command in Claude Code, verify confirmation dialog
   ```

---

**Plan Complete - Ready for Verifier Review**

### Phase 6.5: Pattern Sync Verification (15 min) **NEW**

**Task:** Add automated pattern synchronization test (Failure Mode #5 prevention)

1. Create `test_pattern_sync.py` in hooks/tests/
2. Implement pattern sync verification between `risk_tier_gate` and `authorization_gate`
3. Add pre-commit hook to run sync test

**Pattern Sync Test:**
```python
def test_patterns_synced_between_hooks():
    """Failure Mode #5: Ensure risk_tier_gate and authorization_gate patterns match."""
    import PreToolUse_risk_tier_gate as risk_gate
    import PreToolUse_authorization_gate as auth_gate

    risk_patterns = set(risk_gate.RISK_TIERS["CONFIRM"]["patterns"])
    auth_patterns = set(auth_gate.DESTRUCTIVE_PATTERNS)

    # Authorization patterns should be subset of risk_tier patterns
    assert auth_patterns.issubset(risk_patterns), (
        f"Pattern mismatch! auth_gate has patterns not in risk_gate: "
        f"{auth_patterns - risk_patterns}\n"
        "Update risk_tier_gate.py RISK_TIERS['CONFIRM']['patterns'] to match."
    )
```

**Verification:**
```bash
python .claude/hooks/tests/test_pattern_sync.py
# Expected: PASS (patterns are synchronized)
```

