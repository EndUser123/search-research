"""Shared testing strategy contract used by UserPromptSubmit hooks.

The goal is to make test selection automatic and risk-aware:
- unit tests for pure logic and local contracts
- regression tests for exact bug paths and restored behavior
- integration tests for boundaries, state, I/O, and hooks
- smoke proofs for real workflows that mocks can fake
"""

from __future__ import annotations

_HEADER = "**TEST STRATEGY CONTRACT**"


def _contract_lines(
    *,
    style: str = "balanced",
    include_smoke: bool = True,
    include_snapshot: bool = True,
) -> list[str]:
    lines: list[str] = [_HEADER]

    if style == "regression_first":
        lines.append(
            "- Start with a regression test that reproduces the exact failure path, then add the smallest unit tests around the root cause."
        )
    elif style == "integration_first":
        lines.append(
            "- Start with an integration or smoke proof because the behavior crosses a boundary that unit tests can mock away."
        )
    elif style == "unit_first":
        lines.append(
            "- Start with the smallest unit test that proves the local contract, then add higher-level tests only where needed."
        )
    elif style == "snapshot_first":
        lines.append(
            "- Start with a snapshot test for the rendered output, then add unit tests for the logic that produces it."
        )
    else:
        lines.append(
            "- Choose the smallest sufficient test mix: unit for local logic, regression for exact bug paths, integration for boundaries/state/I/O."
        )

    lines.append(
        "- Use unit tests for pure logic, deterministic transforms, and local contracts that do not need process, network, filesystem, or shared-state boundaries."
    )
    lines.append(
        "- Use regression tests for every bug fix or restored behavior: reproduce the exact failure first, then prove that same path no longer fails."
    )
    lines.append(
        "- Use integration tests when behavior crosses modules, hooks, state, persistence, replay/resume, compaction, filesystem, or other I/O boundaries."
    )
    if include_smoke:
        lines.append(
            "- Use a real smoke proof for hooks, routers, or resumable workflows so a mocked implementation cannot fake success."
        )
    if include_snapshot:
        lines.append(
            "- Use snapshot tests for rendered output, generated docs, hook-injected text, and skill bodies; use unit tests for the logic that chooses or computes that output."
        )
    lines.append(
        "- Do not add integration tests when a unit test can prove the same contract."
    )
    lines.append(
        "- Do not stop at unit tests when the defect lives at a boundary, through state, or across processes."
    )
    lines.append(
        "- Before finalizing the test plan, say which layer proves what and what a lower layer would miss."
    )

    return lines


def build_testing_contract(
    *,
    style: str = "balanced",
    include_smoke: bool = True,
    include_snapshot: bool = True,
) -> str:
    """Build the canonical testing strategy contract."""
    return "\n".join(
        _contract_lines(
            style=style,
            include_smoke=include_smoke,
            include_snapshot=include_snapshot,
        )
    )


def append_testing_contract(
    text: str,
    *,
    style: str = "balanced",
    include_smoke: bool = True,
    include_snapshot: bool = True,
) -> str:
    """Append the testing strategy contract unless it is already present."""
    contract = build_testing_contract(
        style=style,
        include_smoke=include_smoke,
        include_snapshot=include_snapshot,
    )

    stripped = text.strip()
    if not stripped:
        return contract
    if _HEADER in text:
        return text
    return f"{stripped}\n\n{contract}"


def contract_clauses(
    *,
    style: str = "balanced",
    include_smoke: bool = True,
    include_snapshot: bool = True,
) -> tuple[str, ...]:
    """Return the canonical testing contract clauses for test assertions."""
    return tuple(
        _contract_lines(
            style=style,
            include_smoke=include_smoke,
            include_snapshot=include_snapshot,
        )
    )
