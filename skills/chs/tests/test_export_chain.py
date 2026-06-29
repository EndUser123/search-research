"""Tests for /chs export chain reconstruction (CHANGE-001/002/003)."""

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.chs.scripts.chs_cli import CHSExporter  # noqa: E402

_SNAPSHOT_LIB = Path(
    "P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib"
)
if _SNAPSHOT_LIB.exists() and str(_SNAPSHOT_LIB) not in sys.path:
    sys.path.insert(0, str(_SNAPSHOT_LIB))


def _proj(tmp_path: Path) -> Path:
    d = tmp_path / "projects"
    d.mkdir()
    return d


def _entry(sid: str, ts: int, transcript_path: str, handoff_path: str | None) -> dict:
    e = {"session_id": sid, "ts": ts, "transcript_path": transcript_path}
    if handoff_path:
        e["handoff_path"] = handoff_path
    return e


def _write_registry(tmp_path: Path, entries: list[dict]) -> Path:
    reg = tmp_path / "session_registry.jsonl"
    with open(reg, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return reg


def _write_handoff(tmp_path: Path, name: str, rs: dict) -> Path:
    hp = tmp_path / name
    with open(hp, "w", encoding="utf-8") as f:
        json.dump({"resume_snapshot": rs}, f)
    return hp


def _stems(result) -> list[str]:
    return [sid for sid, _ in (result or [])]


# --- CHANGE-001/002: graph walk ---


def test_walk_two_hop_oldest_first(tmp_path):
    """A->B->C resume chain reconstructs oldest-first across handoffs."""
    proj = _proj(tmp_path)
    pa, pb, pc = (proj / f"{s}.jsonl" for s in ("A", "B", "C"))
    for p in (pa, pb, pc):
        p.write_text("[]", encoding="utf-8")
    hA = _write_handoff(tmp_path, "hA.json", {"n_1_transcript_path": str(pb)})
    hB = _write_handoff(tmp_path, "hB.json", {"n_1_transcript_path": str(pc)})
    reg = _write_registry(
        tmp_path,
        [
            _entry("A", 30, str(pa), str(hA)),
            _entry("B", 20, str(pb), str(hB)),
            _entry("C", 10, str(pc), None),
        ],
    )
    result = CHSExporter()._resolve_chain_from_handoff("A", reg, 30)
    assert _stems(result) == ["C", "B", "A"]


def test_walk_unions_old_handoffs_for_ancestor(tmp_path):
    """Freshest handoff lacks the ancestor; an older handoff carries it.

    Reproduces the real 754f0d6e case: the newest handoff has n_2=None, only an
    older handoff records the grandparent. The walk must union across handoffs.
    """
    proj = _proj(tmp_path)
    pa, pb = (proj / f"{s}.jsonl" for s in ("A", "B"))
    for p in (pa, pb):
        p.write_text("[]", encoding="utf-8")
    h_new = _write_handoff(tmp_path, "hA_new.json", {})  # no parent links
    h_old = _write_handoff(tmp_path, "hA_old.json", {"n_2_transcript_path": str(pb)})
    reg = _write_registry(
        tmp_path,
        [
            _entry("A", 5, str(pa), str(h_old)),
            _entry("A", 9, str(pa), str(h_new)),  # freshest, no link
            _entry("B", 1, str(pb), None),
        ],
    )
    result = CHSExporter()._resolve_chain_from_handoff("A", reg, 30)
    assert _stems(result) == ["B", "A"]


def test_walk_cycle_safe(tmp_path):
    """A->B->A loop terminates with no duplicates."""
    proj = _proj(tmp_path)
    pa, pb = (proj / f"{s}.jsonl" for s in ("A", "B"))
    for p in (pa, pb):
        p.write_text("[]", encoding="utf-8")
    hA = _write_handoff(tmp_path, "hA.json", {"n_1_transcript_path": str(pb)})
    hB = _write_handoff(tmp_path, "hB.json", {"n_1_transcript_path": str(pa)})
    reg = _write_registry(
        tmp_path,
        [
            _entry("A", 20, str(pa), str(hA)),
            _entry("B", 10, str(pb), str(hB)),
        ],
    )
    stems = _stems(CHSExporter()._resolve_chain_from_handoff("A", reg, 30))
    assert stems == ["B", "A"]  # no infinite loop, no dupes


def test_walk_resolves_source_session_id(tmp_path):
    """source_session_id is followed when no n_1/n_2 path is present."""
    proj = _proj(tmp_path)
    pa, pb = (proj / f"{s}.jsonl" for s in ("A", "B"))
    for p in (pa, pb):
        p.write_text("[]", encoding="utf-8")
    hA = _write_handoff(tmp_path, "hA.json", {"source_session_id": "B"})
    reg = _write_registry(
        tmp_path,
        [
            _entry("A", 20, str(pa), str(hA)),
            _entry("B", 10, str(pb), None),
        ],
    )
    assert _stems(CHSExporter()._resolve_chain_from_handoff("A", reg, 30)) == ["B", "A"]


def test_walk_no_parents_returns_self(tmp_path):
    """A session with no parent links returns just itself."""
    proj = _proj(tmp_path)
    pa = proj / "A.jsonl"
    pa.write_text("[]", encoding="utf-8")
    hA = _write_handoff(tmp_path, "hA.json", {})
    reg = _write_registry(tmp_path, [_entry("A", 5, str(pa), str(hA))])
    assert _stems(CHSExporter()._resolve_chain_from_handoff("A", reg, 30)) == ["A"]


def test_walk_unknown_session_returns_none(tmp_path):
    """Unknown session_id -> None (caller falls back to Strategy 1/2)."""
    reg = _write_registry(tmp_path, [_entry("A", 5, "x.jsonl", None)])
    assert CHSExporter()._resolve_chain_from_handoff("ZZZ", reg, 30) is None


# --- CHANGE-003: compaction boundary markers ---


def test_format_transcript_compaction_markers(tmp_path):
    """isCompactSummary entries emit numbered boundary markers, in line order."""
    transcript = tmp_path / "t.jsonl"
    lines = [
        {"type": "user", "message": {"role": "user", "content": "first"}},
        {"type": "user", "message": {"role": "user", "content": "summary1", "isCompactSummary": True}},
        {"type": "assistant", "message": {"role": "assistant", "content": "reply"}},
        {"type": "user", "message": {"role": "user", "content": "top-level", "isCompactSummary": True}},
    ]
    with open(transcript, "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e) + "\n")

    class _Sink(list):
        def write(self, s):
            self.append(s)

    sink = _Sink()
    CHSExporter()._format_transcript_to_file(transcript, sink)
    text = "".join(sink)
    assert "*compaction cycle 1*" in text
    assert "*compaction cycle 2*" in text
    assert text.index("compaction cycle 1") < text.index("compaction cycle 2")


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
