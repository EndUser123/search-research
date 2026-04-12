"""Shared reasoning contract used by multiple UserPromptSubmit hooks.

The goal is to make the baseline reasoning discipline automatic:
- verify before claiming absence or breakage
- include a counterexample / failure mode
- search existing implementations before creating new ones
- name rollback / fallback when reversibility matters
- state what evidence would change the answer
"""

from __future__ import annotations

_HEADER = "**REASONING CONTRACT**"


def _contract_lines(
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
) -> list[str]:
    lines: list[str] = [_HEADER]

    if include_verification:
        lines.append(
            "- Verify repo/runtime facts before claiming absence, breakage, or implementation state."
        )
    if include_counterexample:
        lines.append(
            "- Name one counterexample, failure mode, or negative example that would invalidate the recommendation."
        )
    if include_discovery:
        lines.append(
            "- Search existing implementations first before proposing new code or removing behavior."
        )
    if include_rollback:
        lines.append(
            "- If the change has blast radius or is hard to reverse, name the rollback or fallback path."
        )
    if include_evidence:
        lines.append("- State what evidence would change the answer if uncertainty remains.")

    return lines


def build_reasoning_contract(
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
) -> str:
    """Build the canonical reasoning contract block.

    The defaults intentionally include the full baseline. Individual hooks
    can disable clauses that are redundant with their own branch-specific text.
    """
    return "\n".join(
        _contract_lines(
            include_verification=include_verification,
            include_counterexample=include_counterexample,
            include_discovery=include_discovery,
            include_rollback=include_rollback,
            include_evidence=include_evidence,
        )
    )


def append_reasoning_contract(
    text: str,
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
) -> str:
    """Append the reasoning contract to a text block unless it is already present."""
    contract = build_reasoning_contract(
        include_verification=include_verification,
        include_counterexample=include_counterexample,
        include_discovery=include_discovery,
        include_rollback=include_rollback,
        include_evidence=include_evidence,
    )

    stripped = text.strip()
    if not stripped:
        return contract
    if _HEADER in text:
        return text
    return f"{stripped}\n\n{contract}"


def contract_clauses() -> tuple[str, ...]:
    """Return the canonical contract clauses for test assertions."""
    return tuple(_contract_lines())
