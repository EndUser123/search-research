#!/usr/bin/env python3
from __future__ import annotations

"""
Truth Validator - In-process adapter.

Validates tool outputs for truthfulness indicators (absolute claims).
Absorbed from PostToolUse_truth_validator.py.

Original matcher: ^(Edit|Write|Bash)$
"""

from typing import Any

from posttooluse.base import PostToolUseHook

CLAIM_INDICATORS = [
    'is the best', 'is the only', 'always works', 'never fails',
    'guaranteed to', 'proven to', 'completely solves',
    'perfect solution', 'optimal choice', 'industry standard'
]


class TruthValidatorHook(PostToolUseHook):
    """Validates tool outputs for unsubstantiated claims."""

    tool_matcher = {"Edit", "Write", "Bash"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        tool_output = str(
            tool_response.get("output", tool_response.get("result", ""))
        )

        if not tool_output or len(tool_output) < 20:
            return {"passed": True}

        text_lower = tool_output.lower()
        claims_found = [ind for ind in CLAIM_INDICATORS if ind in text_lower]

        if not claims_found:
            return {"passed": True}

        parts = ['⚠️ TRUTH VALIDATION: Review claims for evidence']
        parts.append(f"Claims detected: {', '.join(claims_found[:3])}")
        if len(claims_found) > 2:
            parts.append('Confidence: LOW - Add evidence before proceeding')

        return {"passed": True, "injection": '\n'.join(parts)}
