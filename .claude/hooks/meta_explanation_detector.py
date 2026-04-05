"""
Meta-Explanation Detector

Shared helper for assumption_audit_v2 and speculation_gate to detect
when Claude is explaining hook/system behavior rather than making
empirical claims about external state.

Meta-explanations about hooks should be downgraded from block to warn
since they're discussing system internals, not making unverified claims
about files, tests, or runtime behavior.

Requires 2+ term matches to avoid false positives from incidental mentions.
"""

# Terms indicating the response is about hooks/system internals
META_HOOK_TERMS = (
    # Router files
    "stop_router.py",
    "userpromptsubmit_router.py",
    "posttooluse_router.py",
    # Individual hooks (lowercase for matching)
    "assumption_audit_v2",
    "assumptionauditv2",
    "posttooluse_claimguard",
    "claimguard",
    "speculation_gate",
    "stophook_cross_validator",
    "cross_validator",
    "stophook_overconfidence_detector",
    "overconfidence_detector",
    "empirical_claims_gate",
    "constitutional_enforcer",
    "post_block_tool_requirement",
    "investigation_required",
    "evidence_store",
    "tool_sequence_manager",
    # Generic hook discussion terms
    "stop router",
    "hook output",
    "this hook",
    "hook fires",
    "hook blocks",
    "hook allows",
    "hook system",
    "hook enforcement",
    "pretooluse",
    "posttooluse",
    "sessionstart",
    "hook_sequence",
    "evidence window",
    "claim scope",
)


def is_meta_explanation(response_text: str) -> bool:
    """Detect if response is primarily explaining hook/system behavior.

    Returns True when 2+ meta terms are present, indicating the response
    is discussing the hook system itself rather than making empirical claims.
    """
    if not response_text:
        return False
    lower = response_text.lower()
    count = sum(1 for term in META_HOOK_TERMS if term in lower)
    return count >= 2
