from __future__ import annotations

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.testing_contract import (
    append_testing_contract,
    build_testing_contract,
    contract_clauses,
)


SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").strip().split("\n"))


def _snapshot(name: str) -> str:
    return _normalize((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def test_testing_contract_includes_baseline_clauses() -> None:
    contract = build_testing_contract()
    lower = contract.lower()

    assert "test strategy contract" in lower
    assert "smallest sufficient test mix" in lower
    assert "unit tests for pure logic" in lower
    assert "regression tests for every bug fix" in lower
    assert "integration tests when behavior crosses modules" in lower
    assert "smoke proof for hooks, routers, or resumable workflows" in lower
    assert "snapshot tests for rendered output" in lower
    assert "lower layer would miss" in lower


def test_testing_contract_snapshot_matches() -> None:
    assert _normalize(build_testing_contract()) == _snapshot("testing_contract.full.txt")


def test_testing_contract_style_variants_change_the_lead_clause() -> None:
    regression = build_testing_contract(style="regression_first").lower()
    unit = build_testing_contract(style="unit_first").lower()
    integration = build_testing_contract(style="integration_first").lower()
    snapshot = build_testing_contract(style="snapshot_first").lower()

    assert "reproduces the exact failure path" in regression
    assert "smallest unit test" in unit
    assert "integration or smoke proof" in integration
    assert "snapshot test for the rendered output" in snapshot


def test_append_testing_contract_is_idempotent() -> None:
    base_text = "Base block"
    once = append_testing_contract(base_text)
    twice = append_testing_contract(once)

    assert once == twice
    assert once.startswith("Base block")
    assert "regression tests" in once.lower()


def test_contract_clauses_match_expected_baseline() -> None:
    clauses = contract_clauses()

    assert clauses[0] == "**TEST STRATEGY CONTRACT**"
    assert any("unit tests for pure logic" in clause.lower() for clause in clauses)
    assert any("regression tests for every bug fix" in clause.lower() for clause in clauses)
    assert any("integration tests when behavior crosses modules" in clause.lower() for clause in clauses)
    assert any("smoke proof for hooks" in clause.lower() for clause in clauses)
