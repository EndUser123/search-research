# Architecture Decision: Preventing "Speculating Without Evidence"

**Date**: 2026-03-12
**Template**: Python
**Intent**: DEFAULT (general architecture decision)
**Status**: Approved

## Decision

Implement **3 targeted improvements** to existing evidence enforcement infrastructure:

1. **CoVe-inspired 4-phase verification hook** - New Stop hook with Draft→Plan→Execute→Synthesize phases
2. **Enhanced inline speculation detection with confidence tagging** - Extend speculation_detector_hook.py
3. **Evidence freshness hash-based invalidation** - Document existing capability

## Rationale

**Build on existing infrastructure**: The codebase already has robust evidence enforcement:
- `unified_evidence_enforcer.py` (UEEA) - Single-pass validation with OBSERVATION_REQUIRED, SPECULATION_VIOLATION, ASSUMPTION_WITHOUT_EVIDENCE checks
- `verify_claims.py` - 5-signal verification (theater detection, semantic matching, evidence window, claim specificity)
- `speculation_detector_hook.py` - PostToolUse hook detecting uncertainty markers

**Practical scope for solo dev**: These are 3-5 day implementations using stdlib-only patterns, matching the solo dev constraint documented in `hooks/CLAUDE.md`.

**Directly addresses failure mode**: The transcript file (`speculating without evidence.txt`) shows AI making claims about tool invocation behavior without checking logs. CoVe methodology prevents this by requiring explicit verification plans.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **A) Full CoVe with external LLM verification** | Requires API dependencies, violates stdlib-only constraint for hooks |
| **B) Sentence-transformer upgrade to larger model** | Current `all-MiniLM-L6-v2` is adequate; larger models add latency without addressing root cause (no tool verification before claims) |
| **C) MCP server for fact-checking** | Over-engineering for single-user codebase; hooks already provide enforcement |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| **False positive rate**: Enhanced speculation detection may block legitimate hypotheses | Confidence tagging allows "hypothetical" language without blocking |
| **Performance**: File hash checking on every Stop hook | Already implemented in UEEA with content caching (lines 309-326) |
| **Multi-terminal isolation**: Current `terminal_id` tracking must be preserved | New CoVe hook will use existing terminal isolation patterns |

## Technical Details

### Async Assessment
**Mixed I/O-bound workload**: Evidence validation involves file I/O (reading tool output, session state) and CPU (semantic embeddings, regex). **Sync is acceptable** for current scale—existing UEEA performs <100ms per check.

### Type System
**Current state**: Good type coverage with room for Protocol-based interfaces:
```python
@dataclass
class EvidenceRecord:
    timestamp: str
    tool_name: str
    evidence_type: str
    content: str

class EvidenceValidator(Protocol):
    def validate(self, claim: str, evidence: list[EvidenceRecord]) -> float: ...
```

### GIL & Multiprocessing
**Not worth complexity yet**: Semantic embeddings are cached after first load. Cross-terminal isolation would be complex with multiprocessing. Consider if validation consistently blocks for >1 second.

### Framework Selection
**Standalone hooks with stdlib-only** is correct. No web framework needed; PreToolUse → PostToolUse → Stop validation chain works well.

## Implementation Plan

### Phase 1: Confidence Tagging (1 day)
**File**: `P:\.claude/hooks/posttooluse/speculation_detector_hook.py`
**Changes**: Add confidence score extraction (1-5 scale) with 50 lines of new code
**Configuration**: `SPECULATION_CONFIDENCE_THRESHOLD` (default: 4), `SPECULATION_VERBOSE_MODE` (default: true)

### Phase 2: CoVe Verification Hook (3 days)
**File**: `P:\.claude/hooks/Stop_cove_verification.py` (new)
**Pattern**: Detect claims → Generate verification plan → Execute verification → Synthesize
**Registration**: Add to `Stop_router.py` priority 3.5
**Test coverage**: 8 tests (claim detection, plan generation, tool matching, bypass flags)

### Phase 3: Documentation (1 day)
**File**: `P:\.claude/hooks/CLAUDE.md`
**Section**: Add "Evidence Freshness" section documenting file hash tracking

## Confidence

**85%** — Based on:
- Codebase analysis: 15+ files read (hooks, evidence system, verification infrastructure)
- Research synthesis: CoVe methodology, inline fact-checking patterns
- Python 3.12 compatibility: No breaking changes in type system or async patterns

## Key Assumptions

1. **stdlib-only constraint** applies (no new external dependencies for hooks)
2. **Solo development environment** (no team coordination overhead)
3. **<100ms latency budget** for Stop hooks is acceptable
4. **File hash-based invalidation** (already in UEEA) is sufficient for evidence freshness

## Adversarial Self-Review

**Weakest assumption**: That confidence tagging will reduce false positives without allowing unverified claims to slip through.

**Consequence**: If confidence tags are overused as loopholes, the enforcement system becomes toothless.

**Mitigation**: Audit confidence tag usage weekly via `analyze_blocked_claims.py` (already implemented for skill claim verification).

## Evidence Basis

- **Codebase**: 15+ files analyzed (UEEA, verify_claims.py, speculation_detector_hook.py)
- **Research**: CoVe methodology (arXiv:2309.11495), inline fact-checking patterns
- **Python 3.12**: Verified no breaking changes affect implementation

## References

- Transcript: `C:\Users\brsth\Downloads\speculating without evidence.txt`
- Research: Chain-of-Verification (CoVe) methodology, inline fact-checking
- Existing: `P:\.claude/hooks\__lib\unified_evidence_enforcer.py`
- Existing: `P:\.claude\hooks\verify_claims.py`
- Existing: `P:\.claude\hooks\posttooluse\speculation_detector_hook.py`
