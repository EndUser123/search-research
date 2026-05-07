#!/usr/bin/env python3
"""Aggregation, deduplication, and prioritization for Stop-phase hook results.

Reduces noise by:
- Classifying raw hook results into structured issues with root_issue, severity,
  and confidence.
- Deduplicating overlapping results that fire on the same underlying problem.
- Prioritizing output: blocks first, then top warnings by confidence.
- Suppressing low-confidence advisories when stronger issues exist.
- Rendering compact, actionable messages with supporting hook names.

Integrates into Stop.py and Stop_router.py with minimal intrusion — call
aggregate_and_render() on the collected messages before returning.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Max warn messages to surface after deduplication
_MAX_WARN_MESSAGES = 2

# Enable/disable aggregation (default: true)
def _aggregation_enabled() -> bool:
    return os.environ.get("STOP_AGGREGATOR_ENABLED", "true").lower() in (
        "1", "true", "yes", "on",
    )


# ---------------------------------------------------------------------------
# Issue taxonomy
# ---------------------------------------------------------------------------

RootIssue = str

ROOT_ISSUES: list[RootIssue] = [
    "fabricated_evidence",
    "unsupported_causal_claim",
    "empty_ack_after_correction",
    "diagnostic_analysis_incomplete",
    "lazy_closure",
    "coverage_gap",
    "destructive_risk",
    "tool_usage_anomaly",
    "overconfidence",
    "missing_verification",
    "epistemic_format",
    "other",
]

Severity = str  # "block" | "warn" | "info"
Confidence = str  # "high" | "medium" | "low"


# ---------------------------------------------------------------------------
# Hook classification
# ---------------------------------------------------------------------------

# Maps hook_name (as used in Stop.py gate names or Stop_router file names)
# to (root_issue, confidence) tuple.
# Hooks NOT listed default to ("other", "medium").
_HOOK_CLASSIFICATION: dict[str, Tuple[RootIssue, Confidence]] = {
    # High confidence — evidence-backed, fabrication, destructive risk
    "cited_content_guard": ("fabricated_evidence", "high"),
    "cross_validator": ("fabricated_evidence", "high"),
    "completion_verification_guard": ("missing_verification", "high"),
    "deletion_verification_guard": ("destructive_risk", "high"),
    "correction_acknowledgment": ("empty_ack_after_correction", "high"),
    "correction_followthrough": ("empty_ack_after_correction", "high"),
    "behavior_gates_agreement": ("empty_ack_after_correction", "high"),
    "behavior_gates_blacklist": ("destructive_risk", "high"),
    "safety_gate": ("destructive_risk", "high"),
    "command_execution_validator": ("destructive_risk", "high"),
    "frameguard_stop": ("destructive_risk", "high"),
    # Medium confidence — structural/causal/diagnostic checks
    "hypothesis_as_fact_gate": ("unsupported_causal_claim", "medium"),
    "hypothesis_enforcement": ("unsupported_causal_claim", "medium"),
    "comparative_claim_guard": ("unsupported_causal_claim", "medium"),
    "diagnostic_analysis_quality": ("diagnostic_analysis_incomplete", "medium"),
    "lazy_workaround_gate": ("lazy_closure", "medium"),
    "epistemic_contract": ("epistemic_format", "medium"),
    "unverified_stance": ("unsupported_causal_claim", "medium"),
    "empirical_claims_gate": ("missing_verification", "medium"),
    "fix_verification_enforcer": ("missing_verification", "medium"),
    "architecture_evidence_gate": ("unsupported_causal_claim", "medium"),
    "assumption_audit": ("unsupported_causal_claim", "medium"),
    "speculation_gate": ("unsupported_causal_claim", "medium"),
    "recommendation_gate": ("lazy_closure", "medium"),
    "intent_artifact_alignment": ("coverage_gap", "medium"),
    "narrative_intent": ("unsupported_causal_claim", "medium"),
    "behavior_gates_guidance": ("coverage_gap", "medium"),
    "dependency_chain_guard": ("unsupported_causal_claim", "medium"),
    # Low confidence — heuristic/style advisories
    "self_reflection": ("other", "low"),
    "referent_coverage": ("coverage_gap", "low"),
    "overconfidence_detector": ("overconfidence", "low"),
    "tool_sanity": ("tool_usage_anomaly", "low"),
    "advisory": ("other", "low"),
    "reflect_integration": ("other", "low"),
    "reasoning_quality_gate": ("other", "low"),
    "reasoning_enhanced": ("other", "low"),
    "optimality_check": ("other", "low"),
    "symptom_map": ("other", "low"),
    "negative_existence_guard": ("unsupported_causal_claim", "low"),
    "positive_existence_guard": ("unsupported_causal_claim", "low"),
    "perf_attribution_gate": ("unsupported_causal_claim", "low"),
    "drift_sentinel": ("other", "low"),
    "step_header_verifier": ("other", "low"),
    "rca_reflector": ("other", "low"),
    "rca_contract": ("other", "low"),
    "good_question_gate": ("other", "low"),
    "skill_question_marker": ("other", "low"),
    "ralph_loop": ("other", "low"),
    "autonomy_gate": ("other", "low"),
    "proposal_decision_scanner": ("other", "low"),
    "arch_gap_detection": ("coverage_gap", "low"),
    "tdd_refactor_gate": ("other", "low"),
    "task_completion_gate": ("other", "low"),
    "rsn_display_gate": ("other", "low"),
    "skill_first_stop_gate": ("other", "low"),
    "post_skill_prose_gate": ("other", "low"),
    "verification_enforcement": ("missing_verification", "medium"),
    "git_diff_reground": ("other", "low"),
    "skill_dir_correlation": ("other", "low"),
    "cks_correction_anchor": ("other", "low"),
    "consultation_loop_interrupt": ("other", "low"),
}

# Priority for rendering (lower = higher priority)
_ISSUE_PRIORITY: dict[RootIssue, int] = {
    "destructive_risk": 0,
    "fabricated_evidence": 1,
    "missing_verification": 2,
    "empty_ack_after_correction": 3,
    "unsupported_causal_claim": 4,
    "diagnostic_analysis_incomplete": 5,
    "lazy_closure": 6,
    "coverage_gap": 7,
    "overconfidence": 8,
    "tool_usage_anomaly": 9,
    "epistemic_format": 10,
    "other": 11,
}

_CONFIDENCE_PRIORITY: dict[Confidence, int] = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

# Root issues that should be collapsed together when multiple hooks fire
_COLLAPSE_GROUPS: dict[RootIssue, list[RootIssue]] = {
    "fabricated_evidence": ["fabricated_evidence", "unsupported_causal_claim", "missing_verification"],
    "empty_ack_after_correction": ["empty_ack_after_correction", "lazy_closure"],
    "unsupported_causal_claim": ["unsupported_causal_claim", "overconfidence"],
}

# Actionable next steps per root issue
_NEXT_STEPS: dict[RootIssue, str] = {
    "fabricated_evidence": "Verify claims with actual tool evidence before asserting.",
    "unsupported_causal_claim": "Add source trace (file:line) or state as uncertainty.",
    "empty_ack_after_correction": "Acknowledge the correction and execute the requested action.",
    "diagnostic_analysis_incomplete": "Add one alternative explanation, one falsification test, and one baseline comparison.",
    "lazy_closure": "Execute the actual fix instead of accepting or working around the issue.",
    "coverage_gap": "Address the items the user explicitly asked about.",
    "destructive_risk": "Verify the operation is intentional before proceeding.",
    "tool_usage_anomaly": "Confirm repeated or high-risk tool usage is intentional.",
    "overconfidence": "Add uncertainty language or evidence support for strong claims.",
    "missing_verification": "Run verification (tests, file checks) before claiming completion.",
    "epistemic_format": "Structure analytical responses with FACT/INFERENCE/UNKNOWN/RECOMMENDATION sections.",
    "other": "Review the advisory and adjust if needed.",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class RawHookResult:
    """Normalized result from a single hook."""
    hook_name: str
    severity: Severity  # "block", "warn", "info"
    message: str
    root_issue: RootIssue
    confidence: Confidence


@dataclass
class AggregatedIssue:
    """Deduplicated issue from one or more hook results."""
    root_issue: RootIssue
    severity: Severity
    confidence: Confidence
    primary_message: str
    next_step: str
    source_hooks: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _normalize_hook_name(raw_name: str) -> str:
    """Extract a clean hook name from various formats."""
    # Strip path prefix, extension, and Stop/StopHook prefix patterns
    name = raw_name.strip()
    # Handle "Stop.py:gatename" format from Stop.py
    if ":" in name:
        name = name.split(":")[-1]
    # Handle file paths — take basename without extension
    if "/" in name or "\\" in name:
        name = name.replace("\\", "/").split("/")[-1]
    if name.endswith(".py"):
        name = name[:-3]
    # Normalize common prefixes
    name = name.replace("StopHook_", "").replace("Stop_", "")
    return name


def classify_result(hook_name: str, severity: Severity) -> Tuple[RootIssue, Confidence]:
    """Infer root_issue and confidence from hook name and severity."""
    clean = _normalize_hook_name(hook_name)
    # Direct lookup
    if clean in _HOOK_CLASSIFICATION:
        return _HOOK_CLASSIFICATION[clean]
    # Partial match (hook names may have variants)
    for key, value in _HOOK_CLASSIFICATION.items():
        if key in clean or clean in key:
            return value
    return ("other", "medium")


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _find_collapse_root(issue: RootIssue) -> RootIssue:
    """Find the canonical root issue for a deduplication group."""
    for primary, members in _COLLAPSE_GROUPS.items():
        if issue in members:
            return primary
    return issue


def _deduplicate(issues: list[RawHookResult]) -> list[AggregatedIssue]:
    """Collapse overlapping hook results into aggregated issues."""
    groups: dict[Tuple[RootIssue, Severity], AggregatedIssue] = {}

    for result in issues:
        canonical = _find_collapse_root(result.root_issue)
        key = (canonical, result.severity)

        if key not in groups:
            groups[key] = AggregatedIssue(
                root_issue=canonical,
                severity=result.severity,
                confidence=result.confidence,
                primary_message=result.message,
                next_step=_NEXT_STEPS.get(canonical, "Review and adjust."),
                source_hooks=[result.hook_name],
            )
        else:
            existing = groups[key]
            existing.source_hooks.append(result.hook_name)
            # Upgrade confidence if a higher-confidence hook fires
            if _CONFIDENCE_PRIORITY[result.confidence] < _CONFIDENCE_PRIORITY[existing.confidence]:
                existing.confidence = result.confidence
                existing.primary_message = result.message

    return list(groups.values())


# ---------------------------------------------------------------------------
# Prioritization
# ---------------------------------------------------------------------------

def _sort_key(issue: AggregatedIssue) -> Tuple[int, int, int]:
    """Sort key: severity (block first), then issue priority, then confidence."""
    severity_order = {"block": 0, "warn": 1, "info": 2}
    return (
        severity_order.get(issue.severity, 1),
        _ISSUE_PRIORITY.get(issue.root_issue, 11),
        _CONFIDENCE_PRIORITY.get(issue.confidence, 2),
    )


def _prioritize(issues: list[AggregatedIssue]) -> list[AggregatedIssue]:
    """Sort by priority and limit warn/info messages."""
    blocks = [i for i in issues if i.severity == "block"]
    warns = [i for i in issues if i.severity == "warn"]
    infos = [i for i in issues if i.severity == "info"]

    blocks.sort(key=_sort_key)
    warns.sort(key=_sort_key)
    infos.sort(key=_sort_key)

    # If strong issues exist, suppress low-confidence infos
    has_strong = any(i.confidence in ("high", "medium") for i in blocks + warns)
    if has_strong:
        infos = [i for i in infos if i.confidence == "high"]

    result = blocks + warns[:_MAX_WARN_MESSAGES] + infos[:1]
    return result


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_issue(issue: AggregatedIssue) -> str:
    """Render a single aggregated issue as a compact, actionable message."""
    signals = ", ".join(issue.source_hooks[:4])
    if len(issue.source_hooks) > 4:
        signals += f" +{len(issue.source_hooks) - 4} more"

    label = issue.root_issue.replace("_", " ")
    severity_tag = issue.severity

    return (
        f"{label} ({severity_tag}): "
        f"{issue.next_step} "
        f"Signals: {signals}."
    )


def render_aggregated(issues: list[AggregatedIssue]) -> str:
    """Render all prioritized issues into a single systemMessage."""
    if not issues:
        return ""
    return "\n".join(_render_issue(issue) for issue in issues)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def aggregate_raw_messages(
    messages: list[Tuple[str, str, str]],
) -> list[AggregatedIssue]:
    """Aggregate raw (hook_name, severity, message) tuples.

    This is the main entry point for both Stop.py and Stop_router.py.

    Args:
        messages: List of (hook_name, severity, message) tuples.

    Returns:
        Sorted, deduplicated, prioritized list of AggregatedIssue objects.
    """
    if not messages:
        return []

    raw_results: list[RawHookResult] = []
    for hook_name, severity, message in messages:
        root_issue, confidence = classify_result(hook_name, severity)
        raw_results.append(RawHookResult(
            hook_name=_normalize_hook_name(hook_name),
            severity=severity,
            message=message,
            root_issue=root_issue,
            confidence=confidence,
        ))

    deduped = _deduplicate(raw_results)
    return _prioritize(deduped)


def aggregate_and_render(
    messages: list[Tuple[str, str, str]],
) -> str:
    """Aggregate and render messages into a compact systemMessage.

    Returns empty string if no messages. Falls back to simple dedup
    when aggregator is disabled.
    """
    if not messages:
        return ""

    if not _aggregation_enabled():
        return "\n\n".join(dict.fromkeys(msg for _, _, msg in messages if msg))

    issues = aggregate_raw_messages(messages)
    return render_aggregated(issues)
