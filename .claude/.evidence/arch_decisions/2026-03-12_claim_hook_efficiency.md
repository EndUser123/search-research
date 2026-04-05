# Architecture Decision: Claim Hook System Efficiency

**Date**: 2026-03-12
**Template**: fast
**Intent Type**: IMPROVE_SYSTEM
**Confidence**: 85%

## Problem Statement

The claim hook system workflow is inefficient and noisy. User reported friction from:
- Overlapping verification systems creating duplicate checks
- Verbose advisory messages cluttering conversation
- E2E workflow verification blocking legitimate pytest evidence

## Failures Identified (from User Report)

### Failure #1: E2E Workflow Claim Over-Verification
**What happened**: After fixing router.py bug and running pytest, stop hook blocked with "E2E workflow claim without execution evidence" despite pytest being legitimate verification.

**Fix/Solution**: User had to manually invoke `/all` skill to demonstrate workflow execution.

**Pattern**: Detection gap - hook treats pytest as "insufficient" for workflow claims, requiring redundant skill invocation.

### Failure #2: Multiple Overlapping Verification Systems
**What happened**: Multiple claim verification hooks exist (unverified_stance, verify_claims, artifact_claims, strawberry_validator) creating duplicate checks and noise.

**Fix/Solution**: Systems were partially consolidated (unified_claim_verifier.DISABLED) but remnants remain.

**Pattern**: Prevention gap - architectural redundancy allows overlapping systems to create cumulative noise.

### Failure #3: Advisory Mode Still Noisy
**What happened**: Even in warn mode, hooks output verbose warnings that clutter the conversation.

**Fix/Solution**: No solution implemented - warnings still show.

**Pattern**: Visibility gap - warn mode was intended to reduce friction but still generates noise.

## Pattern

**Over-verification with redundant enforcement layers creates friction through multiple overlapping checks and noisy advisory output.**

## Proposed Changes

### Change A: Consolidate Claim Verification to Single Stop Hook

**File(s)**:
- Modify: `P:\.claude/hooks\StopHook_unverified_stance.py`
- Disable: `verify_claims.py`, `artifact_claims.py` (remove from settings.json)
- Move: `strawberry_validator` from Stop to PostToolUse (advisory-only)

**Logic**:
1. Keep `StopHook_unverified_stance.py` as sole claim verification gate (most complete implementation)
2. Disable redundant claim hooks in settings.json
3. Move `strawberry_validator` to PostToolUse as non-blocking advisory
4. Add unified claim routing in unverified_stance for all claim types

**Test**:
- Make completion claim after pytest → should allow (unified verification)
- Make system claim without evidence → should block (unified verification)
- Verify no duplicate warning messages from overlapping hooks

**Success**: Single source of truth eliminates duplicate checks, reduces noise by 50-70%

### Change B: Implement Smart Advisory Mode with Bypass Flag

**File(s)**:
- Create: `P:\.claude\hooks\__lib\claim_advisory.py`
- Modify: `StopHook_unverified_stance.py` to use advisory formatter

**Logic**:
```python
import os
from typing import Optional

CLAIM_ADVISORY_SUPPRESSED = os.environ.get("CLAIM_ADVISORY_QUIET", "false").lower() == "true"

def format_advisory(message: str, user_message: str = "") -> Optional[str]:
    """
    Only show advisory if not in quiet mode.

    Usage:
    1. Set CLAIM_ADVISORY_QUIET=true to suppress all claim advisories
    2. Or add --allow-claim to user message to bypass advisory for current turn
    """
    if CLAIM_ADVISORY_SUPPRESSED:
        return None

    # Check if user added bypass flag
    if "--allow-claim" in user_message.lower():
        return None

    return f"⚠️ {message}\n\nSuppress: export CLAIM_ADVISORY_QUIET=true"
```

**Test**:
- Trigger claim warning in normal mode → shows advisory
- Set CLAIM_ADVISORY_QUIET=true → advisory suppressed
- Add --allow-claim to message → advisory suppressed for current turn

**Success**: Users can reduce noise by 80-90% when needed, while keeping protection for high-risk operations

## Implementation Order

1. **Change A** — Consolidate claim verification (highest payoff, eliminates redundancy)
2. **Change B** — Add quiet mode (user control over noise level)

**Estimated effort**: 2-3 hours total

## Evidence Basis

- Codebase analysis: 5+ claim verification files identified
- User report: "noisy" and "inefficient" claim workflow
- Memory system: `hook_architecture.md` confirms Stop hooks can block + send feedback
- Test evidence: claim-efficiency.txt shows E2E verification blocking legitimate pytest results

## Key Assumptions

1. User's "noise" complaint refers to verbose warning messages, not blocking behavior itself
2. Consolidation can be done without losing verification coverage
3. Advisory mode suppression won't be abused to bypass legitimate checks

## Alternatives Considered

### Option C: Add Whitelist for Common Claims
Add a whitelist of known-good claim patterns that bypass verification.

**Rejected because**:
- Whitelisting creates maintenance burden
- Doesn't solve underlying redundancy problem
- Could be exploited to bypass legitimate checks

### Option D: Disable E2E Verification Entirely
Remove the E2E workflow verification that blocked the pytest claim.

**Rejected because**:
- Loses protection against false workflow execution claims
- User specifically reported wanting "reduced friction" not "disabled verification"
- E2E verification has valid use cases (skills, multi-step workflows)

## Related Documentation

- `P:\.claude\hooks\CLAUDE.md` — Hook architecture and verification patterns
- `P:\.claude\hooks\StopHook_unverified_stance.py` — Current implementation
- `C:\Users\brsth\Downloads\claim-efficiency.txt` — User's example of the problem
