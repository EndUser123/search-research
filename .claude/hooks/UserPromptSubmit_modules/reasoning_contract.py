"""Shared reasoning contract used by multiple UserPromptSubmit hooks.

The goal is to make the baseline reasoning discipline automatic:
- verify before claiming absence or breakage
- include a counterexample / failure mode
- search existing implementations before creating new ones
- name rollback / fallback when reversibility matters
- state what evidence would change the answer
"""

from __future__ import annotations

from UserPromptSubmit_modules.base import HookContext

_HEADER = "**REASONING CONTRACT**"
_STATE_KEY = "reasoning_contract_applied"
_SOURCE_KEY = "reasoning_contract_source"


def _contract_lines(
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_investigation: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
    include_falsification: bool = True,
    include_comparison_axis: bool = True,
    include_premortem_checklist: bool = True,
    include_fix_closure_check: bool = True,
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
    if include_investigation:
        lines.append(
            "- When uncertainty exists, state the primary hypothesis first, name only the alternatives needed to test it, and choose the smallest discriminating test before concluding."
        )
    if include_rollback:
        lines.append(
            "- If the change has blast radius or is hard to reverse, name the rollback or fallback path."
        )
    if include_evidence:
        lines.append("- State what evidence would change the answer if uncertainty remains.")
    if include_falsification:
        lines.append(
            '- Before stating a conclusion, name the falsification condition: "This would be wrong if ___." Then give one concrete counterexample or disconfirming signal.'
        )
    if include_comparison_axis:
        lines.append(
            "- When comparing options, name the comparison axis and scale assumption before ranking them."
        )
    if include_premortem_checklist:
        lines.append(
            "- Before celebrating a fix, ask: what is the likely failure mode, what discriminating test would falsify it, what existing rule already covers part of the risk, could this overfire, and what snapshot must move with it?"
        )
    if include_fix_closure_check:
        lines.append(
            "- Before declaring a fix complete, say whether the user's reported gap is actually closed, not just whether a related bug was fixed."
        )

    return lines


def build_reasoning_contract(
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_investigation: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
    include_falsification: bool = True,
    include_comparison_axis: bool = True,
    include_premortem_checklist: bool = True,
    include_fix_closure_check: bool = True,
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
            include_investigation=include_investigation,
            include_rollback=include_rollback,
            include_evidence=include_evidence,
            include_falsification=include_falsification,
            include_comparison_axis=include_comparison_axis,
            include_premortem_checklist=include_premortem_checklist,
            include_fix_closure_check=include_fix_closure_check,
        )
    )


def append_reasoning_contract(
    text: str,
    *,
    include_verification: bool = True,
    include_counterexample: bool = True,
    include_discovery: bool = True,
    include_investigation: bool = True,
    include_rollback: bool = True,
    include_evidence: bool = True,
    include_falsification: bool = True,
    include_comparison_axis: bool = True,
    include_premortem_checklist: bool = True,
    include_fix_closure_check: bool = True,
) -> str:
    """Append the reasoning contract to a text block unless it is already present."""
    contract = build_reasoning_contract(
        include_verification=include_verification,
        include_counterexample=include_counterexample,
        include_discovery=include_discovery,
        include_investigation=include_investigation,
        include_rollback=include_rollback,
        include_evidence=include_evidence,
        include_falsification=include_falsification,
        include_comparison_axis=include_comparison_axis,
        include_premortem_checklist=include_premortem_checklist,
        include_fix_closure_check=include_fix_closure_check,
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


def mark_reasoning_contract_applied(context: HookContext, source: str) -> None:
    """Record that a reasoning contract has already been injected upstream."""
    data = getattr(context, "data", None)
    if not isinstance(data, dict):
        return
    data[_STATE_KEY] = True
    data[_SOURCE_KEY] = source


def reasoning_contract_already_applied(context: HookContext) -> bool:
    """Return True when a prior hook has already primed the reasoning contract."""
    data = getattr(context, "data", None)
    if not isinstance(data, dict):
        return False
    return bool(data.get(_STATE_KEY))
