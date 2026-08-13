import json
import sys
from pathlib import Path


sys.path.insert(0, "P:/.agents/skills/wiki-yt/scripts")
import maintenance
import sync


def test_export_receipt_is_propagated_after_validation(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sync, "WIKI_VAULT", tmp_path / "wiki")
    monkeypatch.setattr(sync, "SYNC_MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(sync, "notebook_title", lambda *_args: "Notebook")
    monkeypatch.setattr(sync, "source_id_snapshot", lambda *_args: (["source-1"], "hash-1"))
    monkeypatch.setattr(sync, "load_manifest", lambda: {"notebooks": {}})
    monkeypatch.setattr(sync, "auto_link", lambda *_args: None)
    monkeypatch.setattr(sync, "append_log_entries", lambda *_args: None)
    monkeypatch.setattr(sync, "rename_notebook", lambda *_args, **_kwargs: None)

    export = {
        "exported": 1,
        "skipped": 0,
        "failed": 0,
        "from_cache_count": 1,
        "cache_hit_count": 1,
        "cache_miss_count": 0,
        "cache_unresolved_count": 0,
        "feed_forward_success_count": 1,
        "feed_forward_failure_count": 0,
    }

    def fake_run(command, **_kwargs):
        name = Path(command[1]).name
        if name == "export_transcripts.py":
            return 0, json.dumps(export), ""
        if name == "cluster_transcripts.py":
            output = Path(command[command.index("-o") + 1])
            output.write_text(json.dumps({"cluster_count": 1}), encoding="utf-8")
            return 0, "", ""
        if name == "synthesize_subtopics.py":
            output = Path(command[command.index("-o") + 1])
            output.write_text(json.dumps([{"title": "Concept"}]), encoding="utf-8")
            return 0, "", ""
        if name == "reconcile.py":
            return 0, json.dumps([{"disposition": "new", "title": "Concept"}]), ""
        if name == "write_pages.py":
            return 0, json.dumps({"written": [{"slug": "concept"}], "failed": []}), ""
        if name == "report.py":
            return 0, "", ""
        raise AssertionError(command)

    saved = {}
    monkeypatch.setattr(sync, "run", fake_run)
    monkeypatch.setattr(sync, "save_manifest", lambda manifest: saved.update(manifest))

    result = sync.sync_one("nb-1", "a.hominidae", dry_run=False, clusters_path=None)

    expected = sync._export_receipt(export)
    assert result["status"] == "synced"
    assert result["export_receipt"] == expected
    assert saved["notebooks"]["nb-1"]["export_receipt"] == expected


def test_save_manifest_merges_stale_worker_updates(monkeypatch, tmp_path):
    manifest_path = tmp_path / "nlm-sync-manifest.json"
    manifest_path.write_text(
        json.dumps({"notebooks": {"base": {"title": "Base"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(sync, "SYNC_MANIFEST", manifest_path)

    sync.save_manifest({"notebooks": {"worker-a": {"title": "A"}}})
    # Simulate a second worker saving a snapshot that did not contain worker-a.
    sync.save_manifest({"notebooks": {"worker-b": {"title": "B"}}})

    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(result["notebooks"]) == {"base", "worker-a", "worker-b"}
    assert not list(tmp_path.glob("*.tmp"))


def test_manifest_and_state_writes_fsync_before_publish(monkeypatch, tmp_path):
    manifest_path = tmp_path / "nlm-sync-manifest.json"
    state_path = tmp_path / "nested" / "state.json"
    monkeypatch.setattr(sync, "SYNC_MANIFEST", manifest_path)
    fsync_calls = []
    monkeypatch.setattr(sync.os, "fsync", lambda descriptor: fsync_calls.append(descriptor))

    sync.save_manifest({"notebooks": {"nb-1": {"title": "Notebook"}}})
    sync.save_state({"synced": ["nb-1"]}, state_path)

    assert len(fsync_calls) == 2
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["notebooks"]["nb-1"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["synced"] == ["nb-1"]


def test_maintenance_repair_reloads_latest_manifest(monkeypatch, tmp_path):
    manifest_path = tmp_path / "nlm-sync-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "notebooks": {
                    "worker-a": {"title": "A", "concept_slugs": ["stale"]},
                    "worker-b": {"title": "B", "concept_slugs": ["kept"]},
                }
            }
        ),
        encoding="utf-8",
    )
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "kept.md").write_text("# kept", encoding="utf-8")
    monkeypatch.setattr(maintenance, "SYNC_MANIFEST", manifest_path)
    monkeypatch.setattr(maintenance, "CONCEPTS_DIR", concepts)

    assert maintenance.fix_stale_slugs(confirm=True) == 1

    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["notebooks"]["worker-a"]["concept_slugs"] == []
    assert result["notebooks"]["worker-b"] == {
        "title": "B",
        "concept_slugs": ["kept"],
    }
    assert not list(tmp_path.glob("*.tmp"))
