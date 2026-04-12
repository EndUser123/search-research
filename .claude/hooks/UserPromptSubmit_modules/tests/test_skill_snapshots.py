from __future__ import annotations

from pathlib import Path


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


def _snapshot(name: str) -> str:
    return _normalize((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def test_think_skill_snapshot_matches():
    assert _body(SKILLS_DIR / "think" / "SKILL.md") == _snapshot("think.body.md")


def test_decision_tree_skill_snapshot_matches():
    assert _body(SKILLS_DIR / "decision-tree" / "SKILL.md") == _snapshot("decision-tree.body.md")
