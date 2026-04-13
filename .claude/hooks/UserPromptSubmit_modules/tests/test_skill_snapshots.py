from __future__ import annotations

from pathlib import Path

from UserPromptSubmit_modules.reasoning_contract import build_reasoning_contract
from UserPromptSubmit_modules.testing_contract import build_testing_contract


ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = ROOT / "skills"
SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").strip().split("\n"))


def _body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return _normalize(parts[2])
    return _normalize(text)


def _section(path: Path, start_marker: str, end_marker: str) -> str:
    body = _body(path)
    start = body.index(start_marker)
    end = body.index(end_marker, start)
    return _normalize(body[start:end])


def _snapshot(name: str) -> str:
    return _normalize((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def test_think_skill_snapshot_matches():
    assert _body(SKILLS_DIR / "think" / "SKILL.md") == _snapshot("think.body.md")


def test_decision_tree_skill_snapshot_matches():
    assert _body(SKILLS_DIR / "decision-tree" / "SKILL.md") == _snapshot("decision-tree.body.md")


def test_tdd_skill_snapshot_matches():
    assert _section(
        SKILLS_DIR / "tdd" / "SKILL.md",
        "## Test Selection Contract",
        "## Critique-Agent Triggers",
    ) == _snapshot("tdd.test_selection_contract.md")


def test_t_skill_snapshot_matches():
    assert _section(
        SKILLS_DIR / "t" / "SKILL.md",
        "### Test Selection Contract",
        "## Modes",
    ) == _snapshot("t.test_selection_contract.md")


def test_sqa_skill_snapshot_matches():
    assert _section(
        SKILLS_DIR / "sqa" / "SKILL.md",
        "## Test Selection Contract",
        "### Findings Accumulation Model",
    ) == _snapshot("sqa.test_selection_contract.md")


def test_sqd_skill_snapshot_matches():
    assert _section(
        SKILLS_DIR / "sqd" / "SKILL.md",
        "## Test Selection Contract",
        "### QR1: Strategic Checks (if routed)",
    ) == _snapshot("sqd.test_selection_contract.md")


def test_investigation_phrase_is_aligned_between_think_and_contract():
    think_body = _body(SKILLS_DIR / "think" / "SKILL.md")
    contract = build_reasoning_contract()

    assert "smallest discriminating test" in think_body.lower()
    assert "smallest discriminating test" in contract.lower()


def test_test_selection_phrase_is_aligned_between_skills_and_contract():
    tdd_body = _body(SKILLS_DIR / "tdd" / "SKILL.md")
    t_body = _body(SKILLS_DIR / "t" / "SKILL.md")
    sqa_body = _body(SKILLS_DIR / "sqa" / "SKILL.md")
    sqd_body = _body(SKILLS_DIR / "sqd" / "SKILL.md")
    contract = build_testing_contract()

    assert "smallest sufficient test mix" in tdd_body.lower()
    assert "smallest sufficient test mix" in t_body.lower()
    assert "smallest sufficient test mix" in sqa_body.lower()
    assert "smallest sufficient test mix" in sqd_body.lower()
    assert "smallest sufficient test mix" in contract.lower()
