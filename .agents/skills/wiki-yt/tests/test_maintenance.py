import sys
from pathlib import Path


sys.path.insert(0, "P:/.agents/skills/wiki-yt/scripts")
import maintenance


def test_offline_audit_skips_live_inventory(monkeypatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "nlm-sync-manifest.json"
    manifest_path.write_text(
        '{"notebooks": {"nb-1": {"title": "Local", "concept_slugs": ["missing"]}}}',
        encoding="utf-8",
    )
    concepts = tmp_path / "concepts"
    concepts.mkdir()

    monkeypatch.setattr(maintenance, "SYNC_MANIFEST", manifest_path)
    monkeypatch.setattr(maintenance, "CONCEPTS_DIR", concepts)

    def fail_if_called(_profile: str):
        raise AssertionError("offline audit must not query NotebookLM")

    monkeypatch.setattr(maintenance, "list_notebooks", fail_if_called)

    report = maintenance.audit("a.hominidae", offline=True)

    assert report["live_inventory_status"] == "skipped"
    assert report["live_notebooks_available"] is False
    assert report["live_notebook_count"] is None
    assert report["stale_slugs"] == [{"notebook_id": "nb-1", "slug": "missing"}]
    assert report["orphaned_transcripts"] == []
    assert report["orphaned_manifest_entries"] == []


def test_offline_audit_does_not_turn_skip_into_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        maintenance,
        "audit",
        lambda _profile, *, offline: {
            "live_inventory_status": "skipped",
            "live_notebooks_available": False,
            "live_notebook_count": None,
            "tracked_notebook_count": 0,
            "stale_slugs": [],
            "orphaned_transcripts": [],
            "untracked_transcripts": 0,
            "orphaned_manifest_entries": [],
            "missing_pipeline_tag": [],
        },
    )
    monkeypatch.setattr(sys, "argv", ["maintenance.py", "--audit", "--offline"])

    assert maintenance.main() == 0
    assert "SKIPPED (--offline" in capsys.readouterr().out
