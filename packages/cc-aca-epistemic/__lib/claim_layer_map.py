"""Claim-layer mapping for conditional hook routing.

Provides:
- CLAIM_LAYER_MAP: Maps claim types to required artifacts and evidence checks
- classify_claim(): Classifies user prompt into claim type
- get_required_artifacts(): Returns artifact list for a claim type
- get_block_message(): Returns block message for unverified claims

This is the shared source of truth for both:
1. UserPromptSubmit claim classification
2. Stop artifact enforcement
"""

from __future__ import annotations

import re

# Claim types
CLAIM_TYPE_MECHANISM = "mechanism_investigation"
CLAIM_TYPE_DESIGN = "design_recommendation"
CLAIM_TYPE_CODE = "code_work"
CLAIM_TYPE_STYLE = "style_heavy"
CLAIM_TYPE_QUESTION = "question"

MECHANISM_PATTERNS = [
    r"\b(ran|executed|rotated|co-?fired|occurred|fired|triggered|dispatched)\b",
    r"\b(session|run|benchmark|process|worker|hook|gate).*\b(had|has|will|did)\b",
    r"\btelemetry\b.*\b(shows|indicates|proves)\b",
    r"\b(overlap|co-fire|same-turn)\b",
    r"\b(age.?guard|worker).*\b(fired|blocking|active)\b",
    r"\b(stop.?gate|gate).*\b(warn|block|allow)\b.*\d+",
]

DESIGN_PATTERNS = [
    r"\b(consolidate|merge|delete|remove|combine|refactor)\b.*\b(hook|gate|module)\b",
    r"\brecommend.*\b(deletion|consolidation|restructure)\b",
    r"\b(should|could|propose).*\b(consolidate|merge|delete)\b",
    r"\blayer.?aware\b",
]

QUESTION_PATTERNS = [
    r"^\s*(what|why|how|when|can|could|does|do|is|are|should)\b",
]

STYLE_PATTERNS = [
    r"\b(always|never|must|will definitely|is definitely|clearly|obviously)\b",
    r"\b(is|are)\s+\w+\s+and\s+\w+\s+(is|are)\b",  # twin assertions
]


def classify_claim(prompt_text: str) -> str:
    """Classify user prompt into claim type.

    Priority: mechanism > design > question > style > code
    """
    text_lower = prompt_text.lower()

    for pattern in MECHANISM_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return CLAIM_TYPE_MECHANISM

    for pattern in DESIGN_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return CLAIM_TYPE_DESIGN

    for pattern in QUESTION_PATTERNS:
        if re.match(pattern, text_lower):
            return CLAIM_TYPE_QUESTION

    for pattern in STYLE_PATTERNS:
        if re.search(pattern, text_lower):
            return CLAIM_TYPE_STYLE

    return CLAIM_TYPE_CODE


# Claim-layer mapping: maps claim keywords to required artifact sources
# Format: "claim_keyword": {"required": [...], "block_msg": "..."}
CLAIM_LAYER_MAP = {
    "co-fire": {
        "required": ["ups_execution_trace.jsonl"],
        "block_msg": "Co-fire claims require ups_execution_trace.jsonl same-turn evidence.",
    },
    "operating_rules_and_behavior_contract": {
        "required": ["ups_execution_trace.jsonl"],
        "block_msg": "operating_rules + behavior_contract co-fire requires ups_execution_trace.jsonl.",
    },
    "age_guard_fired": {
        "required": ["stop_gate_telemetry.jsonl"],
        "block_msg": "Age guard claims require stop_gate_telemetry.jsonl grep evidence.",
    },
    "stop_gate_warn_count": {
        "required": ["stop_gate_telemetry.jsonl"],
        "block_msg": "Warn count claims require jq verification of stop_gate_telemetry.jsonl.",
    },
    "gate_fired": {
        "required": ["stop_gate_telemetry.jsonl"],
        "block_msg": "Gate fire claims require stop_gate_telemetry.jsonl evidence.",
    },
}


def get_required_artifacts(claim_type: str) -> list[str]:
    """Return required artifact list for a claim type."""
    if claim_type == CLAIM_TYPE_MECHANISM:
        return ["stop_gate_telemetry.jsonl", "ups_execution_trace.jsonl"]
    return []


def get_block_message(claim_key: str | None = None) -> str | None:
    """Return block message for a claim key, or None if no enforcement."""
    if claim_key and claim_key in CLAIM_LAYER_MAP:
        return CLAIM_LAYER_MAP[claim_key]["block_msg"]
    return None