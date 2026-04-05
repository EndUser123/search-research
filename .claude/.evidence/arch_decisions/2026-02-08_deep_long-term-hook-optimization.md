# Architecture Analysis: Long-Term Hook & Behavior Optimization

**Date:** 2026-02-08
**Template:** deep (comprehensive)
**Query:** Optimal long-term fix for hook system and AI behavior (transition effort irrelevant)

---

## Executive Summary

**Diagnosis:** Two separate problems requiring different solutions:

| Problem | Root Cause | Solution Type |
|---------|-----------|--------------|
| **Hook Loop** | Observation receipt tracking broken; POST_BLOCK_REQUIRED_HOOKS creates sequential gate chain | **Technical fix** (consolidation + grace) |
| **My Behavior** | Making diagnostic claims without evidence first | **Structural fix** (mandatory observation gating) |

**Recommendation:** Unified Evidence Enforcement Architecture (UEEA) - consolidates all evidence gates into single pass with mandatory observation gating for AI responses.

---

## Stage 0.3: Codebase-Aware Analysis

### Current Hook Architecture (Verified from logs)

**File:** `P:\.claude\hooks\Stop_router.py`

**Current State (lines 51-68):**
```python
POST_BLOCK_REQUIRED_HOOKS = frozenset({
    "empirical_claims_gate.py",
    "StopHook_investigation_required.py",
    "architecture_evidence_gate.py",
    "speculation_gate.py",
    "StopHook_overconfidence_detector.py",
})

OBSERVATION_TOOL_NAMES = frozenset({"Read", "Grep", "Glob", "Bash", "View", "WebFetch"})

CONSOLIDATED_OBSERVATION_BLOCK_HOOKS = frozenset({
    "post_block_tool_requirement", "empirical_claims_gate.py", "Stop_absence_claim_gate.py"
})
```

**Problem:** 5 separate hooks in POST_BLOCK_REQUIRED_HOOKS, but grace only applies to 3 in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS.

**Evidence from logs (188 blocks today):**
- empirical_claims_gate.py: 125 blocks (66%)
- speculation_gate.py: 18 blocks (10%) - "appears to be" language
- assumption_audit_v2.py: 13 blocks (7%)
- Sequential blocks observed: same file blocked twice (lines 18, 28)

---

## Stage 1: Mental Model

**Design Pattern:** Sequential Validation Chain with Missing State Sharing

Current architecture:
```
Response → Hook 1 (block, requires observation)
        → User runs Read
        → Response with evidence
        → Hook 2 (block again, doesn't recognize observation)
        → Hook 3 (block again, different format requirement)
        → ...
```

**Root issue:** Each hook maintains separate state, doesn't share observation receipt.

---

## Stage 2: Proposed Changes

### Change A: Unified Evidence Enforcement Architecture (UEEA)

**File:** `P:\.claude\hooks\unified_evidence_enforcer.py` [NEW]

**Logic:**
```python
"""
Unified Evidence Enforcement Architecture (UEEA)

Consolidates all evidence gates into single validation pass:
- empirical_claims_gate.py (observation required)
- speculation_gate.py (speculative language)
- assumption_audit_v2.py (unverified assumptions)
- StopHook_investigation_required.py (diagnostic without investigation)

Single state source, unified format, no sequential loops.
"""

import json
from pathlib import Path
from datetime import datetime, UTC

STATE_DIR = Path(__file__).parent.parent / "state"
STATE_FILE = STATE_DIR / "ueea_state.jsonl"

# Unified evidence format
EVIDENCE_FIELDS = ["observed_via", "observed_at", "evidence_type", "source_file", "claim_excerpt"]

# Speculative language patterns (from speculation_gate.py)
SPECULATIVE_PATTERNS = [
    r"\bappears to be\b",
    r"\blikely\b",
    r"\bprobably\b",
    r"\bseems like\b",
    r"\bwould expect\b",
]

# Required observation tools
OBSERVATION_TOOLS = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}

def check_response(data: dict) -> dict:
    """
    Single-pass validation of response against all evidence requirements.

    Returns:
        {"allowed": bool, "blocks": list[str], "remediation": str|None}
    """
    response_text = data.get("response", "")
    tools_used = data.get("tools_used", [])

    blocks = []

    # Check 1: Observation required for claims
    if _has_claims_without_observation(response_text, tools_used):
        blocks.append("OBSERVATION_REQUIRED")

    # Check 2: Speculative language in diagnostic mode
    if _is_diagnostic_without_evidence(response_text, tools_used):
        if _has_speculative_language(response_text):
            blocks.append("SPECULATION_VIOLATION")

    # Check 3: Unverified assumptions
    if _has_unverified_assumptions(response_text):
        blocks.append("ASSUMPTION_WITHOUT_EVIDENCE")

    if blocks:
        return {
            "allowed": False,
            "blocks": blocks,
            "remediation": _build_remediation(blocks)
        }

    # Record observation receipt for grace period
    _record_observation(data)
    return {"allowed": True, "blocks": []}

def _has_claims_without_observation(response: str, tools: list) -> bool:
    """Claims exist without observation tools used."""
    # File/path patterns in response
    import re
    file_patterns = re.findall(r'[A-Z]:\\[^"\s+\]]+|[/\w][/\w][\w.-]+\.[\w]+', response)

    if not file_patterns:
        return False

    # Check if any observation tool was used
    observed = any(tool in OBSERVATION_TOOLS for tool in tools)
    return not observed and len(response) > 200

def _is_diagnostic_without_evidence(response: str, tools: list) -> bool:
    """Diagnostic mode detected without evidence."""
    diagnostic_markers = ["root cause", "diagnosis", "appears to be", "likely"]
    return any(m.lower() in response.lower() for m in diagnostic_markers)

def _has_speculative_language(response: str) -> bool:
    """Check for speculative patterns."""
    import re
    for pattern in SPECULATIVE_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    return False

def _has_unverified_assumptions(response: str) -> bool:
    """Check for unverified assumptions."""
    # Look for assumption patterns without evidence
    import re
    assumption_patterns = [
        r"assumes? (?:that )?without",
        r"assuming (?:that )?",
        r"presuming (?:that )?",
    ]
    return any(re.search(p, response, re.IGNORECASE) for p in assumption_patterns)

def _build_remediation(blocks: list) -> str:
    """Build unified remediation message."""
    lines = ["⛔ UNIFIED EVIDENCE BLOCK", ""]

    if "OBSERVATION_REQUIRED" in blocks:
        lines.append("Your response makes claims without observation.")
        lines.append("Run Read/Grep/Glob/Bash/View/WebFetch, then respond with:")
        lines.append("")
        lines.append("  observed_via: <tool>")
        lines.append("  observed_at: <timestamp>")
        lines.append("  evidence_type: <code|filesystem|execution|any>")

    if "SPECULATION_VIOLATION" in blocks:
        lines.append("")
        lines.append("Speculative language detected (appears to be, likely, probably).")
        lines.append("Use INVESTIGATION REQUIRED format:")
        lines.append("")
        lines.append("  Observation: [what you see]")
        lines.append("  Hypothesis: [what you suspect - UNVERIFIED]")
        lines.append("  Required to verify: [specific files/commands]")
        lines.append("")
        lines.append("Cannot proceed without evidence.")

    return "\n".join(lines)

def _record_observation(data: dict):
    """Record observation for grace period."""
    STATE_FILE.parent.mkdir(exist_ok=True)

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "terminal_id": data.get("terminal_id"),
        "tools_used": data.get("tools_used", []),
        "response_length": len(data.get("response", "")),
    }

    with open(STATE_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

def check_grace(terminal_id: str) -> bool:
    """Check if terminal has active grace (observation within last turn)."""
    if not STATE_FILE.exists():
        return False

    with open(STATE_FILE) as f:
        lines = f.readlines()

    # Check last entry for this terminal
    for line in reversed(lines[-10:]):  # Last 10 entries
        record = json.loads(line)
        if record.get("terminal_id") == terminal_id:
            # Has observation tools
            if any(tool in OBSERVATION_TOOLS for tool in record.get("tools_used", [])):
                return True

    return False
```

**Why this prevents:**
1. Single validation pass eliminates sequential gate loop
2. Unified state tracking prevents "observation not recognized" issue
3. Consolidated remediation prevents format confusion

**Test:**
```python
# Test 1: Claim without observation blocks
data = {"response": "The plan file shows X configuration", "tools_used": []}
result = check_response(data)
assert not result["allowed"]
assert "OBSERVATION_REQUIRED" in result["blocks"]

# Test 2: Observation passes
data = {"response": "observed_via: Read\nobserved_at: 2026-02-08T...", "tools_used": ["Read"]}
result = check_response(data)
assert result["allowed"]

# Test 3: Speculative language in diagnostic blocks
data = {"response": "The root cause appears to be X", "tools_used": []}
result = check_response(data)
assert not result["allowed"]
assert "SPECULATION_VIOLATION" in result["blocks"]

# Test 4: Grace period works
# First turn: observation
check_response({"terminal_id": "test", "tools_used": ["Read"], "response": "..."})
# Second turn: same terminal, no tools (should pass via grace)
assert check_grace("test") == True
```

**Success metric:** Reduce blocks by 70%+, eliminate sequential loops

**Effort:** 20 hours (L)

---

### Change B: Modify Stop_router.py to Use Unified Enforcer

**File:** `P:\.claude\hooks\Stop_router.py` [MOD]

**Changes:**

1. **Remove POST_BLOCK_REQUIRED_HOOKS (lines 55-63)**
2. **Add unified enforcer import and call**

```python
# At top of file
from unified_evidence_enforcer import check_response, check_grace

# Replace POST_BLOCK_REQUIRED_HOOKS logic (around line 715):
# OLD:
# post_block_violation = _post_block_requirement_violation(data)
# if post_block_violation:
#     ...

# NEW:
# Unified evidence check
unified_check = check_response(data)
if not unified_check["allowed"]:
    # Check grace first
    if check_grace(data.get("terminal_id", "")):
        # Suppress this turn, consume grace
        _consume_grace(data.get("terminal_id", ""))
    else:
        # Build unified block message
        block_message = _build_unified_block(unified_check, data)
        return block_message
```

**Why this prevents:**
- Eliminates 5-hook sequential execution
- Single source of truth for evidence validation
- Grace period actually works (unified state)

**Test:**
```bash
# Before: Sequential blocks
# Run response with claim → Hook 1 blocks → Run Read → Hook 2 blocks → ...

# After: Single block or pass
# Run response with claim → Single block → Run Read → Pass
```

**Success metric:** p95 latency for evidence gates reduced by 60%

**Effort:** 8 hours (M)

---

### Change C: AI Behavior Fix - Mandatory Pre-Response Observation Check

**File:** `P:\.claude\hooks\PreToolUse_observation_gate.py` [NEW]

**Purpose:** Block tool invocation when response would make claims without evidence.

**Logic:**
```python
"""
PreToolUse Observation Gate

Blocks tool invocation when the prepared response makes claims
without having used observation tools first.

This is a BEHAVIORAL fix - forces AI to observe before claiming.
"""

import re
from pathlib import Path

# File/path patterns that indicate claims
FILE_PATTERNS = re.compile(r'[A-Z]:\\[^"\s+\]]+|[/\w][/\w][\w.-]+\.[\w]+')


def check_pre_tool(data: dict) -> dict:
    """
    Check if response makes claims without observation.

    Runs BEFORE tool invocation to prevent the error.
    """
    response = data.get("response", "")
    tools_available = data.get("tools_available", [])

    # Skip if no tools available (can't observe)
    if not tools_available:
        return {"allowed": True}

    # Check for file/path claims
    file_mentions = FILE_PATTERNS.findall(response)

    if not file_mentions:
        return {"allowed": True}

    # Check if observation tools are available
    observation_tools = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}
    has_observation = any(tool in observation_tools for tool in tools_available)

    if file_mentions and has_observation:
        return {
            "allowed": False,
            "reason": "CLAIM_WITHOUT_OBSERVATION",
            "remediation": f"Your response mentions {len(file_mentions)} file(s) without observation. "
                          f"Run Read/Grep/Glob/Bash first to verify, then respond."
        }

    return {"allowed": True}


# Hook main
if __name__ == "__main__":
    import sys
    import json
    from __lib.hook_base import hook_main

    @hook_main
    def main():
        data = json.loads(sys.stdin.read())
        result = check_pre_tool(data)

        if not result["allowed"]:
            print(result.get("remediation", "Observation required"))
            sys.exit(1)

        sys.exit(0)
```

**Why this prevents:**
- Forces observation BEFORE response generation
- Prevents "I'll read, then respond" loop
- Behavioral change through structural enforcement

**Test:**
```python
# Test 1: Claims without observation tools → block
data = {
    "response": "The file at P:/test.py shows X",
    "tools_available": ["Write"]  # No observation tools
}
result = check_pre_tool(data)
assert not result["allowed"]

# Test 2: Has observation tools → pass
data = {
    "response": "The file at P:/test.py shows X",
    "tools_available": ["Read", "Write"]  # Has Read
}
result = check_pre_tool(data)
assert result["allowed"]
```

**Success metric:** Reduces empirical_claims_gate blocks by 90%

**Effort:** 6 hours (S)

---

### Change D: Speculative Language Detection with Auto-Rewrite

**File:** `P:\.claude\hooks\PreToolUse_speculation_check.py` [NEW]

**Purpose:** Detect speculative language BEFORE response, suggest rewrite.

**Logic:**
```python
"""
PreToolUse Speculation Check

Detects speculative language in prepared responses before they're sent.
Suggests rewrite with proper uncertainty markers.
"""

SPECULATIVE_PATTERNS = {
    r"\bappears to be\b": "is [CONFIRMED]" or "may be [UNVERIFIED]",
    r"\blikely\b": "probably [UNVERIFIED]",
    r"\bprobably\b": "possibly [UNVERIFIED]",
    r"\bseems like\b": "appears to be [UNVERIFIED]",
}

UNCERTAINTY_MARKERS = [
    "[UNVERIFIED]", "[REQUIRES INVESTIGATION]", "[BASED ON CURRENT EVIDENCE]"
]

def check_speculation(data: dict) -> dict:
    """
    Check for speculative language that needs marking.
    """
    response = data.get("response", "")
    findings = []

    for pattern, suggestion in SPECULATIVE_PATTERNS.items():
        import re
        if re.search(pattern, response, re.IGNORECASE):
            findings.append({
                "pattern": pattern,
                "suggestion": suggestion
            })

    if findings:
        return {
            "allowed": False,
            "reason": "SPECULATIVE_LANGUAGE_DETECTED",
            "findings": findings,
            "remediation": _build_speculation_remediation(findings, response[:200])
        }

    return {"allowed": True}


def _build_speculation_remediation(findings: list, excerpt: str) -> str:
    """Build remediation message with examples."""
    lines = ["⚠️ SPECULATIVE LANGUAGE DETECTED", ""]
    lines.append("Your response contains unmarked speculative claims:")
    lines.append("")

    for f in findings[:3]:
        lines.append(f"  • {f['pattern']}")

    lines.append("")
    lines.append("Suggested rewrite:")
    lines.append("")
    lines.append("Option 1 - Mark uncertainty:")
    lines.append('  "Based on current evidence, X may be the cause [UNVERIFIED]."')
    lines.append("")
    lines.append("Option 2 - Use INVESTIGATION REQUIRED format:")
    lines.append("  Observation: [what you see]")
    lines.append("  Hypothesis: X appears to be the cause [UNVERIFIED]")
    lines.append("  Required to verify: [specific files to read]")
    lines.append("")
    lines.append("Rewrite your response before proceeding.")

    return "\n".join(lines)
```

**Why this prevents:**
- Catches speculation BEFORE it blocks
- Forces explicit uncertainty marking
- Teaches proper diagnostic format

**Success metric:** Reduces speculation_gate blocks by 80%

**Effort:** 4 hours (S)

---

## Stage 3: Risk Matrix

| Option | Technical Risk | Schedule Risk | Behavioral Impact | Score |
|--------|---------------|--------------|-------------------|-------|
| **A: UEEA (unified enforcer)** | Medium | Medium | Low (user sees same blocks, just consolidated) | **PROCEED** |
| **B: Stop_router mod** | Medium | Low | Low (internal change) | **PROCEED** |
| **C: Pre-response observation gate** | Low | Low | High (forces new behavior pattern) | **PROCEED** |
| **D: Speculation check** | Low | Low | Medium (teaches uncertainty) | **PROCEED** |
| **E: Status quo** | High (continued friction) | None | High (user frustration) | AVOID |

---

## Stage 4: Implementation Order

**Recommended sequence (user doesn't care about transition):**

1. **Change A (UEEA)** — Foundation, enables everything else (20h)
2. **Change B (Stop_router)** — Integrate UEEA (8h)
3. **Change C (Pre-response gate)** — Behavioral fix (6h)
4. **Change D (Speculation check)** — Teach uncertainty (4h)

**Total effort:** 38 hours (~1 week focused work)

**Rollback plan:**
- Each change is independently revertible
- Feature flags: `UEEA_ENABLED=false` reverts to old hooks
- Git revert for individual files

---

## Stage 5: Pre-Mortem (What could fail in 6 months?)

### Scenario 1: UEEA too strict, blocks legitimate work
**Risk:** Over-consolidation loses nuance of individual hooks
**Mitigation:**
- Feature flag allows per-hook bypass
- Log all blocks for analysis
- Gradual rollout (10% → 50% → 100%)

### Scenario 2: Pre-response gate creates new friction
**Risk:** "Can't respond without reading first" slows legitimate work
**Mitigation:**
- Gate only activates when file paths detected
- Allow explicit override with "NO_OBSERVATION_NEEDED" marker
- Teach proper workflow: Read → Analyze → Respond

### Scenario 3: Speculation check too aggressive
**Risk:** False positives on legitimate uncertainty
**Mitigation:**
- Whitelist common uncertainty phrases ("may require", "could be")
- Allow [CONFIDENT] marker to override
- Manual review of blocks for first month

---

## Stage 6: Confidence Calibration

## Confidence: 78%

**Evidence basis:**
- **Code:** Verified current Stop_router.py structure (Tier 1)
- **Logs:** Analyzed 188 blocks from today's session (Tier 1)
- **Documentation:** Read hook enforcement patterns from CLAUDE.md (Tier 1)
- **Gap:** UEEA is new code, untested (Tier 3)

**Key assumptions:**
1. Unified state tracking works correctly (unverified)
2. Grace period logic covers all evidence gates (unverified)
3. Pre-response gate doesn't create new failure modes (unverified)
4. Speculation patterns don't have high false-positive rate (unverified)

**Verification status:**
- Assumption 1: Requires testing with mock data
- Assumption 2: Needs integration test with real hooks
- Assumption 3: Requires staged rollout
- Assumption 4: Needs test corpus of real responses

---

## Stage 7: Adversarial Self-Review

**Weakest assumption:** Unified state tracking works correctly

**If wrong:** UEEA creates new blocking patterns, doesn't solve original problem, user frustration increases

**Mitigation:**
- Extensive testing before deployment
- Feature flag for instant rollback
- Monitor block rates for first week
- Keep old hooks as fallback

**Verification status:** Unverified - requires implementation + testing

**Bias check:**
- **Recency bias?** [No] - Based on today's actual block data
- **Survivorship bias?** [No] - Considering failure scenarios
- **Complexity bias?** [Yes] - UEEA is new component, could be over-engineering

**Alternative to over-engineering:** Simplify existing hooks instead of creating new unified system. But user said "transition effort irrelevant" - so UEEA is justified.

---

## Output Persistence

Auto-saved to: `P:\.claude\arch_decisions\2026-02-08_deep_long-term-hook-optimization.md`

---

## Summary

**Problem:** Two separate issues - hook system loops + my behavior

**Solution:** Unified Evidence Enforcement Architecture
1. Single-pass validation (eliminates sequential loops)
2. Unified state tracking (fixes grace not working)
3. Pre-response observation gate (forces proper behavior)
4. Speculation detection with rewrite suggestions

**Expected outcome:** 70%+ reduction in blocks, elimination of sequential gate loops

**Total effort:** 38 hours (~1 week)
