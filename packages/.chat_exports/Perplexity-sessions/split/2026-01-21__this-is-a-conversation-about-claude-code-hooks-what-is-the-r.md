---
title: "This is a conversation about Claude Code hooks.  What is the right thing to do?  any gaps or opportunities?

[Prompt Enh"
date: "2026-01-21"
mode: "COPILOT"
uuid: "45515fea-7d11-4f83-800b-94bf006ce923"
entry_count: 1
---

## Human

This is a conversation about Claude Code hooks.  What is the right thing to do?  any gaps or opportunities?

[Prompt Enhancements.](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)/
❯ /arch how can we stop you from being offensive? ● Architecture Analysis: Preventing Offensive Behavior 1. Mental Model Application First Principles: - "Offensive" = violating user expectations/values/preferences - Current triggers: lazy assumptions, unverified claims, dismissi
pasted
HEre's some chat history.  It seems like Claude Code is starting to forget it's constitution.  Any ideas on how to make it not forget?
7:55 PM
Diagnosed constitutional drift and architected enforcement mechanisms.

17s









This is a great diagnostic. The conversation reveals the core problem: informational hooks ≠ enforcement. Claude Code correctly identified that the hook system warns but doesn't block.
Root Cause Analysis
Why Claude Code "forgets" constitution:
FactorMechanismEvidence from Chat
Attention decay
Constitutional docs in middle of context get less weight
Made confident recommendation without verification
Goal displacement
Immediate task dominates over meta-rules
Jumped straight to /arch output format
Toothless enforcement
Hooks exit code 2 but don't actually block
"skip_active_hook" in logs - response delivered anyway
No structural gate
Nothing prevents non-compliant generation
Constitution says "investigate first" but nothing enforces it
Architectural Options
Option A: Make Hooks Actually Block
Current: Hook exits 2 → warning displayed → response delivered anyway
Required: Hook exits 2 → generation rejected → force retry with investigation
python
# In hook dispatcher (not the individual hook)
if hook_result.exit_code != 0:
    raise ConstitutionalViolation(
        hook=hook_name,
        message=hook_result.stderr,
        required_action="INVESTIGATE_FIRST"
    )
    # Don't deliver response
Problem: Claude Code's hook system may not support this natively. Need to check if Stop hooks can actually prevent response delivery or just append warnings.
Option B: Pre-Generation Constitutional Gate
Instead of post-generation validation, inject a structural checkpoint before generation:
markdown
## Pre-Response Gate (Injected by Hook)

Before responding to claims about existing systems:

CHECKPOINT:
- [ ] Have I Read() relevant files THIS MESSAGE? (not earlier in conversation)
- [ ] Can I cite file:line for each system claim?
- [ ] Am I using speculation patterns ("likely", "probably", "I think")?

If any checkbox fails → STOP and investigate first.
Implementation: PreToolUse or UserPromptSubmit hook that injects this into every message.
Option C: Evidence-Required Response Format
Force structural proof of investigation:
markdown
## System Claim: [claim here]
Evidence: Read([file]) at [timestamp this session]
Citation: [file:line]
Confidence: [tier] based on [source type]

If no Evidence block → claim is [UNVERIFIED]
Enforcement: Post-generation hook that rejects responses with system claims but no Evidence blocks.
Option D: Constitutional Refresh Injection
Problem: Constitution at conversation start loses attention weight over long sessions.
Solution: Periodic re-injection of core principles:
python
# In UserPromptSubmit hook
if message_count % 5 == 0 or contains_system_claim(user_message):
    inject_constitutional_anchor()
```

**Anchor content** (minimal, high-signal):
```
⚠️ CONSTITUTIONAL REFRESH: Investigation before claims. Cite file:line. No speculation patterns.
Option E: Session Investigation Tracking
Track what's been investigated THIS session:
python
# Session state
investigated_files = set()
investigated_topics = {}

# When Read() called
investigated_files.add(filepath)

# When system claim made without corresponding Read()
if claim_topic not in investigated_topics:
    flag("[UNVERIFIED] - No investigation this session")
Recommended Approach
Tier 1 (Immediate - 1 hour):
Option D: Add constitutional anchor injection every 5 messages
Minimal code, no architectural changes
Tier 2 (Short-term - 4 hours):
Option C: Require Evidence blocks for system claims
Post-generation validation that flags missing evidence
Tier 3 (If hooks can block - 8 hours):
Option A: Make Stop hooks actually prevent response delivery
Requires understanding Claude Code's hook dispatch mechanism
Key Question
Before implementing: Can Claude Code's hook system actually block response delivery, or only append warnings?
If it can block → Option A is the right path
If it can only warn → Option C + D is the workaround
Want me to investigate the hook dispatcher to determine what's structurally possible?
yes please.  review our hooks
7:57 PM
1 step
list_directory


Strategized systematic examination of hook configuration and architecture.

Let me examine the key architectural files:
2 steps
read_file


Examining hook logic and test assumptions.


Now let me examine the test_assumption_audit.py to see how it signals blocking:
read_file


Identified misaligned hook blocking mechanisms and configuration gaps.








Now let me check the architecture documentation to understand how hooks are supposed to signal blocking:
read_file


Now I understand the architecture better.

Let me check how a properly blocking Stop hook works:
4 steps
read_file


Uncovered mismatched JSON structures blocking hook functionality.











Now I have a complete picture. Let me verify one more thing - how Claude Code's hook system actually interprets exit codes:
read_file


Diagnosed protocol misalignment across multiple enforcement hooks.




Investigation Complete: Root Cause Identified
I've traced the full hook infrastructure. Here's the evidence:
Protocol Mismatch Analysis
ComponentExpected (PROTOCOL.md)Actual ImplementationResult
test_assumption_audit.py
{"allow": false} + exit 1
print(stderr) + exit 2
❌ Won't block
constitutional_enforcer.py
{"allow": false}
{"allow_stop": false}
❌ Wrong field
Stop_router.py
Check allow == false
Checks decision == "block"
❌ Wrong field
success_validator.py
Block on violations
Always {"allow": true}
❌ By design, doesn't block
Root Cause: Three-Way Protocol Mismatch
PROTOCOL.md says: Stop hooks should return {"allow": false, "reason": "..."} with exit code 1 to block
Stop_router.py checks for: result.get("decision") == "block" - which NO hook outputs!
Individual hooks use:
test_assumption_audit.py: exit code 2, prints to stderr
constitutional_enforcer.py: {"allow_stop": false}
success_validator.py: Always {"allow": true} (intentionally non-blocking)
None of these match what Stop_router.py checks for!
Evidence Trail
From Stop_router.py line 117-120:
python
if result and "hookSpecificOutput" in result:
    ctx = result["hookSpecificOutput"].get("additionalContext", "")
    if ctx:
        outputs.append(ctx)
elif result and result.get("decision") == "block":
    return result  # <-- This WOULD block, but nothing returns this!
```

From `PROTOCOL.md`:
```
### Exit Code
| Code | Meaning |
|------|---------|
| 0 | Allowed |
| 1 | Blocked |
Diagnosis
The hook system is architecturally broken. Every hook thinks it's blocking, but:
Different hooks use different field names
The router doesn't match what hooks output
Exit codes aren't consistently checked
This is a false sense of security - the warnings appear, but nothing actually prevents the response from being delivered.
Fix Options
Option A: Fix Stop_router.py (Minimal Change)
Make the router check for what hooks actually output:
python
# Check multiple possible blocking indicators
if result:
    # Check all known blocking patterns
    if (result.get("decision") == "block" or
        result.get("allow") == False or
        result.get("allow_stop") == False or
        result.get("validation_passed") == False):
        return {"decision": "block", "message": result.get("reason", result.get("message", ""))}
Reversibility: 1.25 (easy to revert) Risk: May block more than expected if hooks were outputting these fields as warnings
Option B: Standardize All Hooks
Update all hooks to use consistent protocol:
python
# Every hook should output:
if should_block:
    print(json.dumps({
        "decision": "block",
        "reason": "Specific violation",
        "hookSpecificOutput": {"additionalContext": "Guidance text"}
    }))
    sys.exit(1)
Reversibility: 1.5 (moderate - touching multiple files) Risk: May break other integrations relying on current output format
Option C: Add a Real Enforcement Layer
Add a new hook that actually checks exit codes:
python
# enforcement_gate.py - runs LAST
# Collects all previous hook results
# If ANY returned non-zero exit code, BLOCK

# In settings.json, register with critical: true
Reversibility: 1.25 (new file, easy to remove) Risk: Lower - additive change
Recommendation
Option A + test_assumption_audit.py fix is the fastest path:
Fix test_assumption_audit.py to output correct JSON:
python
# Instead of:
print(AUDIT_PROMPT.strip(), file=sys.stderr)
sys.exit(2)

# Do:
print(json.dumps({
    "decision": "block",
    "reason": "Assumption audit required",
    "hookSpecificOutput": {"additionalContext": AUDIT_PROMPT.strip()}
}))
sys.exit(1)
Fix Stop_router.py to check for the field hooks actually use
Want me to implement either fix?
I'd like to know what the optimal solution is.
8:03 PM
Architected unified protocol to enforce constitutional blocking systematically.

33s











Optimal Solution: Protocol-First Enforcement
Let me apply the full decision framework since this is a structural architectural change (reversibility ~1.5).
TRIAGE
Reversibility: 1.5 (moderate - touching multiple files, changes enforcement behavior)
Dependencies: 4 (router, protocol definition, individual hooks, settings)
Evidence: Tier 1 available (can execute and verify)
Route: STANDARD analysis with Decision Matrix
Root Cause (Not Symptoms)
The problem isn't "test_assumption_audit uses exit code 2" - that's a symptom.
Root cause: There is no single authoritative protocol that both hooks AND the router enforce. PROTOCOL.md exists as documentation but:
Hooks don't import it (it's markdown, not code)
Router doesn't validate against it
Each hook author invented their own convention
This is a protocol enforcement gap, not a hook bug.
Optimal Architecture: Shared Blocking Contract
Design Principle
"If blocking is important, it should be impossible to block incorrectly."
Instead of trusting each hook to output the right JSON, make blocking a function call that handles the protocol internally.
Component Design
┌─────────────────────────────────────────────────────────────┐
│                    block_protocol.py                        │
│  Single source of truth for blocking behavior               │
│  - block_response(reason, guidance, hook) → never returns   │
│  - allow_response(message?) → exits cleanly                 │
│  - Handles JSON format, exit codes, logging                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Stop_router.py                          │
│  - Validates hook output against protocol                   │
│  - Only accepts {"decision": "block"} as blocking signal    │
│  - Logs protocol violations for debugging                   │
│  - Aggregates messages, triggers actual block               │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌────────────┐   ┌────────────┐   ┌────────────┐
     │ Hook A     │   │ Hook B     │   │ Hook C     │
     │ imports    │   │ imports    │   │ imports    │
     │ block_     │   │ block_     │   │ block_     │
     │ protocol   │   │ protocol   │   │ protocol   │
     └────────────┘   └────────────┘   └────────────┘
Implementation
1. block_protocol.py (NEW - ~60 lines)
python
"""
Hook Blocking Protocol v1.0
===========================

ALL Stop hooks that want to block MUST use this module.
This ensures consistent behavior regardless of which hook triggers blocking.

Usage:
    from block_protocol import block_response, allow_response
    
    if violation_detected:
        block_response(
            reason="What violated",
            guidance="What to do instead", 
            hook="my_hook_name"
        )
    
    allow_response()  # Or allow_response("Advisory message")
"""

import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("P:/.claude/hooks/logs/block_protocol.jsonl")

def _log(event: str, data: dict):
    """Audit trail for all blocking decisions."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {"timestamp": datetime.now().isoformat(), "event": event, **data}
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def block_response(reason: str, guidance: str, hook: str, severity: str = "HIGH") -> None:
    """
    Block the response. This function NEVER returns - it exits.
    
    Args:
        reason: Why the response is being blocked (shown to Claude)
        guidance: What Claude should do instead (actionable)
        hook: Name of the hook triggering the block (for debugging)
        severity: HIGH (default), MEDIUM, or LOW
    """
    output = {
        "decision": "block",
        "reason": reason,
        "guidance": guidance,
        "hook": hook,
        "severity": severity,
    }
    
    _log("block", {"hook": hook, "reason": reason[:100], "severity": severity})
    
    print(json.dumps(output))
    sys.exit(1)

def allow_response(message: str = None) -> None:
    """
    Allow the response, optionally with an advisory message.
    
    Args:
        message: Optional advisory text (shown but doesn't block)
    """
    output = {"decision": "allow"}
    if message:
        output["message"] = message
        _log("allow_with_message", {"message": message[:100]})
    
    print(json.dumps(output))
    sys.exit(0)
2. Stop_router.py Update (~20 lines changed)
python
def process_hook_result(hook_name: str, result: dict) -> dict | None:
    """Validate and process hook output against protocol."""
    if not result:
        return None
    
    decision = result.get("decision")
    
    # Protocol validation
    if decision not in ("block", "allow", None):
        _log_protocol_violation(hook_name, f"Invalid decision value: {decision}")
        return None
    
    if decision == "block":
        # Validate required fields for blocking
        if not result.get("reason"):
            _log_protocol_violation(hook_name, "Block without reason")
        if not result.get("guidance"):
            _log_protocol_violation(hook_name, "Block without guidance")
        
        # This is a valid block - return it to trigger enforcement
        return result
    
    # Allow or advisory - return for message aggregation
    return result
3. Hook Migration Pattern
python
# BEFORE (test_assumption_audit.py)
print(AUDIT_PROMPT.strip(), file=sys.stderr)
sys.exit(2)

# AFTER
from block_protocol import block_response, allow_response

if not has_observation:
    block_response(
        reason="Response generated without verification tools",
        guidance=AUDIT_PROMPT.strip(),
        hook="test_assumption_audit"
    )

allow_response()
Decision Matrix
FieldAssessment
VALUE
0% actual enforcement → 100% intended enforcement. Currently hooks detect but don't block; after this, detection = blocking.
EVIDENCE
Tier 1: Can execute test_assumption_audit, verify it blocks, check logs
DISSENT
"This could over-block and break workflows" — Mitigated by: (1) phased rollout starting with one hook, (2) CONSTITUTIONAL_HOOKS_BYPASS preserved, (3) clear guidance in every block message
REVERSIBILITY
1.35 overall. New file (1.0), router changes (1.25), hook migrations (1.5 each but independent)
SECOND_ORDER
Success: Higher trust in constitutional system → fewer "forgotten" violations → better reliability. Failure: Over-aggressive blocking → user disables hooks → worse than before
FAILURE_SCENARIO
Hooks block legitimate responses → user frustration → sets BYPASS=1 permanently → back to no enforcement. Recovery: Revert individual hooks, adjust thresholds
Rollout Plan
Phase 1: Infrastructure (1 hour)
Create block_protocol.py
Update Stop_router.py to recognize new protocol
Add protocol violation logging (non-blocking) for existing hooks
Phase 2: Canary Hook (30 min)
Migrate test_assumption_audit.py only
Test in one session
Verify blocking actually occurs
Check bypass mechanism works
Phase 3: Monitor (1 week)
Run with single hook enforcing
Review block_protocol.jsonl for patterns
Adjust if false positive rate >10%
Phase 4: Full Migration (2 hours)
Migrate remaining Stop hooks one at a time
constitutional_enforcer.py
empirical_claims_gate.py
stop_success_validator.py
Why This Is Optimal
AlternativeWhy Inferior
Fix router only
Perpetuates inconsistent protocols, each hook still invents its own convention
Fix hooks only
Router still doesn't validate, new hooks will repeat mistakes
Add enforcement layer
Adds complexity without fixing root cause, now 3 things to keep in sync
Document harder
Documentation isn't enforcement; PROTOCOL.md already exists and is ignored
The protocol module approach:
Makes correct blocking easier than incorrect blocking (import and call)
Single source of truth (code, not docs)
Built-in audit trail (logging in the module)
Self-documenting (docstrings explain usage)
Incrementally adoptable (migrate hooks one at a time)
Confidence
85% (Tier 1 ceiling)
Basis:
Root cause clearly identified through code inspection
Solution follows established pattern (hook_tracker.py already does this for logging)
Phased rollout limits blast radius
Bypass mechanism preserved for emergencies
Gaps:
Haven't tested if Claude Code's hook dispatcher respects exit code 1 for Stop hooks (PROTOCOL.md claims it does, but should verify)
Unknown: Are there other consumers of hook output that would break?
Next Steps
Verify assumption: Test that exit code 1 from Stop hook actually blocks (create minimal test hook)
Implement Phase 1: Create block_protocol.py and router update
Canary test: Migrate test_assumption_audit.py, verify blocking works
Monitor: Run for a week before expanding
Want me to start with step 1 (verification test) or jump to implementation?
1
8:05 PM
Devised test strategy to validate hook blocking behavior.


Verification Test: Does Exit Code 1 Actually Block?
Let me create a minimal test hook to verify the protocol claim.
write_file


Deliberated testing procedures and configuration format verification.


Now I need to show you how to register and test it. Here's the test procedure:
Step 1: Add to settings.json
Add this entry to the hooks.Stop array in P:\.claude\settings.json:
json
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "command",
      "command": "python .claude/hooks/TEMP/test_stop_block_verify.py",
      "timeout": 5,
      "layer": "0_TEST_BLOCK_VERIFY",
      "critical": true,
      "description": "TEMPORARY: Verify exit code 1 blocks response"
    }
  ]
}
Step 2: Test in Claude Code
Send any simple message like "hello" to Claude Code.
Step 3: Observe Results
ObservationConclusion
Response is blocked, you see only the block message
✅ Exit code 1 works - proceed with optimal solution
Response appears AND you see block message
❌ Exit code 1 is advisory only - need different approach
Response appears, no block message visible
❌ Hook isn't running at all - check registration
Step 4: Cleanup
Remove the test hook entry from settings.json after testing.
Alternative: Check Claude Code Source
If you have access to Claude Code's hook dispatcher source, we could also verify by reading the code directly. Do you have that available, or should we proceed with the empirical test?
You have access to everything I do.
8:06 PM
Interpreted statement and contemplated accessing internal source code.

Let me search for Claude Code's hook dispatcher implementation.
20 steps
read_process_output


Investigated system components and documentation sources.

Let me search for Claude Code documentation about hooks:
2 steps
Claude Code CLI hooks stop exit code block behavior
10 results










Pondered system access implications and verification methods.

Let me search for Claude Code's hook dispatcher implementation.
4 steps
start_process


Synthesized technical documentation to clarify hook behavior mechanics.

11s









Found critical insight from the web search. Let me verify the actual protocol for Stop hooks:
read_file


Reconciled conflicting documentation about hook behavior protocols.









CRITICAL DISCOVERY: The web search reveals a fundamental misunderstanding in PROTOCOL.md.
For Stop hooks, "blocking" means preventing Claude from stopping (forcing continuation), NOT blocking the response!
Let me verify the actual Stop router behavior:
read_file


Investigated router behavior and hook decision logic.





The router checks result.get("decision") == "block" at line 117-118. Let me check what hooks are actually outputting:
read_file


Diagnosed hook output mismatch and traced execution flow.









I see - this hook uses sys.exit(2) + stderr (old pattern). Let me check constitutional_enforcer:
read_file


Examined file structure to decode output format.

Let me find the main() function and see what output format constitutional_enforcer actually uses:
read_file


Diagnosed protocol mismatch and architected unified solution.







Now I have the complete picture. Let me summarize the actual protocol mismatch:
Root Cause Analysis: Complete
What Official Claude Code Docs Say (Stop Hooks)
MethodHow It Works
JSON + exit 0
{"decision": "block", "reason": "..."} → forces Claude to continue
Exit 2 + stderr
stderr text fed back to Claude as continuation instructions
What Your Current Hooks Do
HookOutputExit CodeResult
test_assumption_audit.py
stderr text
2
⚠️ Exit 2 works BUT router doesn't pass it through correctly
constitutional_enforcer.py
{"allow_stop": false}
1
❌ Wrong field name, wrong exit code
PROTOCOL.md says
{"allow": false}
1
❌ Neither matches official spec
What Stop_router.py Checks
python
elif result and result.get("decision") == "block":
    return result
The router is looking for "decision": "block" but NO hook outputs that!
Recommended Fix
The cleanest solution is align everything to the official Claude Code protocol:
Option A (JSON method - recommended):
python
output = {
    "decision": "block",
    "reason": "Specific guidance for Claude to continue"
}
print(json.dumps(output))
sys.exit(0)
Option B (stderr method - simpler for some hooks):
python
print("Guidance for Claude to continue", file=sys.stderr)
sys.exit(2)
Should I:
Create block_protocol.py - Helper module that makes correct blocking easy
Update Stop_router.py - Ensure it correctly handles both methods
Migrate one hook (test_assumption_audit.py) as canary test
Ready to implement Phase 1?

[Claude is AI and can make mistakes. Please double-check responses.](https://support.anthropic.com/en/articles/8525154-claude-is-providing-incorrect-or-misleading-responses-what-s-going-on)
[](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)

## Assistant

# Claude Code Hook Analysis: Optimal Solution

This is a sophisticated architectural problem. Let me cut through to the right thing to do.

## The Core Issue (Re-framed)

You've correctly diagnosed **constitutional drift** but misidentified the mechanism. Your hooks aren't "weak" — they're **semantically broken**:

1. **PROTOCOL.md says** Stop hooks block Claude from stopping (force continuation) with `{"decision": "block"}`
2. **Your hooks output** either `exit 2` + stderr OR `{"allow_stop": false}` 
3. **Stop_router.py checks** for `decision == "block"` 
4. **Result**: Misalignment across all three layers = warnings without enforcement

The audit trail shows this clearly:
- `test_assumption_audit.py`: Uses old pattern (exit 2 + stderr) — works but isn't recognized by router
- `constitutional_enforcer.py`: Uses wrong field (`allow_stop`) — router ignores it
- `PROTOCOL.md`: Documents something different than what router checks

## Gaps & Opportunities

| Gap | Impact | Opportunity |
|-----|--------|-------------|
| No single authoritative protocol in code | Each hook author guesses the format | Create `block_protocol.py` as source of truth |
| Router doesn't validate hook output | Invalid formats silently fail | Add protocol validation with audit logging |
| No blocking verification test | You don't know if enforcement works | Create minimal test hook to verify behavior |
| No session-level enforcement memory | Same violation repeated across 5+ messages | Add session state tracking to protocols |
| Hooks scattered, inconsistent imports | Hard to maintain, easy to deviate | Centralize blocking logic in one module |

## The Right Thing To Do (Priority Order)

### Phase 1: Verification (30 min) — DO THIS FIRST
**Don't implement anything until you know exit code behavior**

Create this minimal test:

```python
# P:\.claude\hooks\TEMP\verify_stop_block.py
import json
import sys

output = {
    "decision": "block",
    "reason": "TEST: Does exit 0 with decision=block actually prevent response?",
    "test_phase": 1
}

print(json.dumps(output))
sys.exit(0)  # Official docs say Stop hooks use exit 0, not 1
```

Register in `settings.json` under `hooks.Stop`, send "test" message to Claude Code, observe if response is blocked.

**Why first**: If blocking doesn't actually work, the entire architecture needs rethinking. Better to know now.

### Phase 2: Protocol Module (1 hour) — Core Foundation

Create `P:\.claude\hooks\block_protocol.py`:

```python
"""
Hook Blocking Protocol v1.0
Single authoritative source for all Stop hook blocking.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

BLOCK_LOG = Path("P:/.claude/hooks/logs/block_enforcement.jsonl")

def block_response(reason: str, guidance: str, hook: str) -> None:
    """Block response using official Claude Code protocol."""
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    # Official protocol: decision=block + exit 0
    output = {
        "decision": "block",
        "reason": reason,
        "guidance": guidance,
        "hook": hook,
        "timestamp": datetime.now().isoformat()
    }
    
    # Audit trail
    with open(BLOCK_LOG, "a") as f:
        f.write(json.dumps(output) + "\n")
    
    print(json.dumps(output))
    sys.exit(0)  # Official protocol

def allow_response(message: str = None) -> None:
    """Allow response, optionally with advisory."""
    output = {"decision": "allow"}
    if message:
        output["message"] = message
    print(json.dumps(output))
    sys.exit(0)
```

**Why this matters**: Now every hook does:
```python
from block_protocol import block_response, allow_response

if violation:
    block_response("What violated", "What to do instead", "hook_name")
allow_response()
```

Impossible to get the format wrong. Automatic audit trail. No guessing.

### Phase 3: Router Validation (30 min) — Enforcement Layer

Update `Stop_router.py` to validate ALL hook outputs:

```python
def process_hook_result(hook_name: str, result: dict) -> dict | None:
    """Validate against official protocol."""
    if not result:
        return None
    
    decision = result.get("decision")
    
    # Validate protocol compliance
    if decision == "block":
        if not result.get("reason"):
            log_protocol_violation(hook_name, "Block missing 'reason'")
        if not result.get("guidance"):
            log_protocol_violation(hook_name, "Block missing 'guidance'")
    
    elif decision not in ("allow", None):
        log_protocol_violation(hook_name, f"Invalid decision: {decision}")
    
    return result if decision else None
```

**Why**: Catches protocol violations before they fail silently.

### Phase 4: Canary Migration (45 min) — Proof of Concept

Migrate ONE hook: `test_assumption_audit.py`

```python
from block_protocol import block_response, allow_response

# Replace this:
# print(AUDIT_PROMPT.strip(), file=sys.stderr)
# sys.exit(2)

# With this:
block_response(
    reason="Claim made without verification tools (Read, List)",
    guidance=AUDIT_PROMPT.strip(),
    hook="test_assumption_audit"
)
```

**Why one hook**: Verify the system works end-to-end. If it blocks correctly, migrate others. If it doesn't, you've isolated the problem.

### Phase 5: Constitutional Anchor Injection (20 min) — Attention Restoration

Add to `UserPromptSubmit` hook (or `MessageSubmit`):

```python
# Every 5 messages, inject constitutional reminder
message_count = get_session_message_count()
if message_count % 5 == 0 and message_count > 0:
    inject_system("""
⚠️ CONSTITUTIONAL CHECKPOINT
- Verify before claiming (Read/List not prior context)
- No speculation patterns on existing systems
- Cite file:line for every claim
""")
```

**Why**: Counteracts context decay. Cheap insurance against drift.

***

## Session State Tracking (Bonus Opportunity)

You have 5-6 concurrent terminals. Add session-level memory:

```python
# P:\.claude\hooks\session_state.py
SESSION_CACHE = Path("P:/.claude/session_state.json")

def record_investigation(topic: str, files_read: list, timestamp: str):
    """Track what's been investigated THIS session."""
    state = json.loads(SESSION_CACHE.read_text() or "{}")
    state[topic] = {"files": files_read, "timestamp": timestamp}
    SESSION_CACHE.write_text(json.dumps(state))

def has_investigated_this_session(topic: str) -> bool:
    """Did we already verify this topic in this session?"""
    state = json.loads(SESSION_CACHE.read_text() or "{}")
    return topic in state
```

Then in your empirical claims hook:
```python
if has_investigated_this_session("system_architecture"):
    allow_response("Already verified this session")
else:
    block_response("New claim, needs investigation", ..., "empirical_claims")
```

**Why**: Prevents repeat investigations of the same topic within a session.

***

## Implementation Order (Reversibility-First)

| Phase | Duration | Reversibility | Risk | Sequence |
|-------|----------|---------------|------|----------|
| 1: Verify | 30m | 1.0 (no changes) | 0% | ✅ **START HERE** |
| 2: block_protocol.py | 1h | 1.0 (new file) | 5% | After verification passes |
| 3: Router validation | 30m | 1.2 (one file) | 10% | Immediately after |
| 4: Canary (test_assumption) | 45m | 1.1 (one hook) | 15% | After router works |
| 5: Full migration | 2h | 1.3 (4 hooks) | 20% | After canary runs 1 week |
| 6: Constitutional anchors | 20m | 1.0 (new hook) | 5% | Anytime after phase 2 |

**Total to full enforcement**: ~4.5 hours spread over 1 week

***

## The Real Question

All of this depends on **one assumption**: Does exit code 0 with `{"decision": "block"}` actually prevent response delivery in Claude Code?

Run the verification test. If it blocks → this entire plan works.

If it doesn't block → you need either:
- A different exit code (maybe 1 is the real blocker?)
- A different response format entirely
- A pre-generation hook instead of post-generation

**What's your result from the test?** That determines everything else.
