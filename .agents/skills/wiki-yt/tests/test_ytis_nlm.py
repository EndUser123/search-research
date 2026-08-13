from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
BIN_DIR = SCRIPTS_DIR / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

import ytis_nlm
import export_transcripts
import queue_sync
import export_yt_cookies
import sync as sync_orchestrator


class _FakeClient:
    def __init__(self) -> None:
        self.closed = False
        self.notebooks = SimpleNamespace(
            list=lambda: "notebooks.list",
            get=lambda notebook_id: ("notebooks.get", notebook_id),
            rename=lambda notebook_id, title: ("notebooks.rename", notebook_id, title),
        )
        self.sources = SimpleNamespace(
            list=lambda notebook_id: ("sources.list", notebook_id),
            get_fulltext=lambda notebook_id, source_id, output_format: (
                "sources.fulltext", notebook_id, source_id, output_format
            ),
        )

    def run(self, operation):
        if operation == "notebooks.list":
            return [SimpleNamespace(id="nb-1", title="Notebook", sources_count=3)]
        if operation == ("notebooks.get", "nb-1"):
            return SimpleNamespace(id="nb-1", title="Notebook", sources_count=3)
        if operation == ("notebooks.rename", "nb-1", "Renamed"):
            return SimpleNamespace(id="nb-1", title="Renamed", sources_count=3)
        if operation == ("sources.list", "nb-1"):
            return [
                SimpleNamespace(
                    id="source-1",
                    title="Video",
                    url="https://example.test/video",
                    _type_code=14,
                    status=SimpleNamespace(value=2),
                )
            ]
        if operation == ("sources.fulltext", "nb-1", "source-1", "text"):
            return SimpleNamespace(content="transcript text")
        raise AssertionError(f"unexpected operation: {operation!r}")

    def close(self) -> None:
        self.closed = True


def test_sync_persists_complete_child_failure_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sync_orchestrator, "CHILD_FAILURE_ROOT", tmp_path)

    receipt = sync_orchestrator.persist_child_failure(
        "notebook-123",
        "synthesis",
        5,
        "child stdout",
        "FAILURE_CLASS=synthesis_backend_exhausted\nfull backend error",
    )

    payload = __import__("json").loads(Path(receipt).read_text(encoding="utf-8"))
    assert payload["notebook_id"] == "notebook-123"
    assert payload["stage"] == "synthesis"
    assert payload["returncode"] == 5
    assert payload["stdout"] == "child stdout"
    assert "full backend error" in payload["stderr"]


def test_queue_snapshot_fsync_before_publish(monkeypatch, tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    fsync_calls = []
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    monkeypatch.setattr(queue_sync.os, "fsync", lambda descriptor: fsync_calls.append(descriptor))

    queue_sync.save_queue(queue_sync._empty_queue())

    assert len(fsync_calls) == 1
    assert queue_path.is_file()


def test_legacy_shapes_are_recreated_from_direct_client() -> None:
    client = _FakeClient()

    assert ytis_nlm.list_notebooks_from_client(client) == [
        {"id": "nb-1", "title": "Notebook", "source_count": 3}
    ]
    assert ytis_nlm.get_notebook_from_client(client, "nb-1")["title"] == "Notebook"
    assert ytis_nlm.list_sources_from_client(client, "nb-1") == [
        {
            "id": "source-1",
            "title": "Video",
            "url": "https://example.test/video",
            "type": 14,
            "status": 2,
        }
    ]
    assert ytis_nlm.get_source_content_from_client(client, "nb-1", "source-1") == "transcript text"
    assert ytis_nlm.rename_notebook_from_client(client, "nb-1", "Renamed")["title"] == "Renamed"


def test_account_wrapper_uses_exact_identity_and_closes(monkeypatch) -> None:
    client = _FakeClient()
    calls = []

    def open_client(account_profile: str, *, worker_id: str):
        calls.append((account_profile, worker_id))
        return client

    monkeypatch.setattr(ytis_nlm, "open_account_client", open_client)

    assert ytis_nlm.list_notebooks("a.hominidae", worker_id="test-worker")[0]["id"] == "nb-1"
    assert calls == [("a.hominidae", "test-worker")]
    assert client.closed is True


def test_probe_delegates_to_ytis_read_only_probe(monkeypatch) -> None:
    expected = SimpleNamespace(ok=True, reason="ok")
    calls = []

    class _Module:
        @staticmethod
        def probe_account_session(account_profile, *, worker_id):
            calls.append((account_profile, worker_id))
            return expected

    monkeypatch.setattr(ytis_nlm, "_load_nlm_module", lambda: _Module)

    assert ytis_nlm.probe_account_session("troup.hominidae", worker_id="probe") is expected
    assert calls == [("troup.hominidae", "probe")]


def test_export_does_not_treat_auth_failure_as_ytdlp_source_fallback(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise RuntimeError("authentication expired")

    monkeypatch.setattr(export_transcripts, "get_source_content", fail)

    with pytest.raises(RuntimeError, match="canonical account authentication failed"):
        export_transcripts.fetch_content("source-1", "a.hominidae", "nb-1")


def test_wiki_yt_scripts_do_not_invoke_legacy_cli_or_login() -> None:
    script_paths = sorted(SCRIPTS_DIR.rglob("*.py"))
    forbidden = ('["nlm"', "'nlm'", "nlm login")
    violations = []
    for path in script_paths:
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            violations.append(str(path))
    assert violations == []


def test_queue_failure_and_retry_records_preserve_account_identity() -> None:
    item = {"nb_id": "nb-1", "title": "Notebook", "source_count": 80, "profile": "troup.hominidae"}

    failure = queue_sync._failure_record(item, "a.hominidae", "failed (rc=5)", 2)
    pending = queue_sync._pending_record(item, "a.hominidae")

    assert failure["profile"] == "troup.hominidae"
    assert pending["profile"] == "troup.hominidae"
    assert failure["source_count"] == 80


def test_retry_poisoned_reopens_exact_item_and_preserves_history(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    queue = queue_sync._empty_queue()
    queue["poisoned"] = [
        {
            "nb_id": "poison-1",
            "title": "Poison one",
            "source_count": 27,
            "profile": "a.hominidae",
            "error": "failed (synthesis_backend_exhausted)",
            "attempts": 3,
        },
        {
            "nb_id": "poison-2",
            "title": "Poison two",
            "source_count": 36,
            "profile": "a.hominidae",
            "error": "failed (synthesis_backend_exhausted)",
            "attempts": 3,
        },
    ]
    queue_sync.save_queue(queue)

    assert queue_sync.do_retry_poisoned(
        ["poison-1"], "dgemma", "bounded alternate-backend validation"
    ) == 0

    updated = queue_sync.load_queue()
    assert [item["nb_id"] for item in updated["pending"]] == ["poison-1"]
    assert updated["pending"][0]["attempts"] == 3
    assert updated["pending"][0]["retry_backend"] == "dgemma"
    assert updated["pending"][0]["force_resynthesis"] is True
    assert [item["nb_id"] for item in updated["poisoned"]] == ["poison-2"]
    assert len(updated["poisoned_history"]) == 1
    assert updated["poisoned_history"][0]["nb_id"] == "poison-1"
    assert updated["poisoned_history"][0]["history_status"] == "reopened"
    assert updated["poisoned_history"][0]["force_resynthesis"] is True


def test_retry_poisoned_preserves_synthesis_context_budget(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    queue = queue_sync._empty_queue()
    queue["poisoned"] = [{
        "nb_id": "poison-budget",
        "title": "Budget",
        "source_count": 27,
        "profile": "a.hominidae",
        "error": "failed (synthesis_degraded)",
    }]
    queue_sync.save_queue(queue)

    assert queue_sync.do_retry_poisoned(
        ["poison-budget"],
        "dgemma",
        "bounded context budget",
        synth_context_budget=500_000,
    ) == 0

    updated = queue_sync.load_queue()
    assert updated["pending"][0]["synth_context_budget"] == 500_000
    assert updated["poisoned_history"][0]["synth_context_budget"] == 500_000


def test_retry_poisoned_persists_per_notebook_checkpoint_path(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "queue.json"
    checkpoint_dir = tmp_path / "checkpoints"
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    queue = queue_sync._empty_queue()
    queue["poisoned"] = [{
        "nb_id": "poison-checkpoint",
        "title": "Checkpoint",
        "source_count": 27,
        "profile": "a.hominidae",
        "error": "failed (synthesis_backend_exhausted)",
    }]
    queue_sync.save_queue(queue)

    assert queue_sync.do_retry_poisoned(
        ["poison-checkpoint"],
        "dgemma",
        "bounded checkpoint retry",
        synth_checkpoint_dir=checkpoint_dir,
    ) == 0

    updated = queue_sync.load_queue()
    checkpoint = Path(updated["pending"][0]["synth_checkpoint_path"])
    assert checkpoint == checkpoint_dir.resolve() / "a.hominidae-poison-checkpoint.stage-c.json"
    assert updated["poisoned_history"][0]["synth_checkpoint_path"] == str(checkpoint)


def test_queue_checkpoint_args_create_then_resume(tmp_path) -> None:
    checkpoint = tmp_path / "stage-c.json"
    item = {"synth_checkpoint_path": str(checkpoint)}
    assert queue_sync._synth_checkpoint_args(item) == ["--synth-checkpoint", str(checkpoint)]
    checkpoint.write_text("{}", encoding="utf-8")
    assert queue_sync._synth_checkpoint_args(item) == ["--synth-resume", str(checkpoint)]


def test_queue_requires_explicit_pipeline_success() -> None:
    assert queue_sync.classify_sync_result(0, "Synced: 1/1", "") == "synced"
    assert queue_sync.classify_sync_result(0, "SKIP (source_ids unchanged since last sync)", "") == "skipped_unchanged"
    assert queue_sync.classify_sync_result(0, "Synced: 0/1\nFailed: ['nb-1']", "") == "failed (pipeline_not_complete)"
    assert queue_sync.classify_sync_result(1, "Synced: 0/1", "") == "failed (rc=1)"
    assert queue_sync.classify_sync_result(5, "", "FAILURE_CLASS=citation_invalid") == "failed (citation_invalid)"
    assert queue_sync.classify_sync_result(5, "FAILURE_CLASS=synthesis_degraded", "") == "failed (synthesis_degraded)"
    assert queue_sync.classify_sync_result(1, "", "FAILURE_CLASS=synthesis_backend_exhausted") == "failed (synthesis_backend_exhausted)"
    assert queue_sync.classify_sync_result(
        0,
        "SYNTHESIS_QUALITY=degraded_fallback\nSynced: 1/1",
        "",
    ) == "failed (degraded_fallback_not_promoted)"
    assert queue_sync.classify_sync_result(
        0,
        "SYNTHESIS_QUALITY=degraded_fallback\nDEGRADED_FALLBACK_PROMOTED=1\nSynced: 1/1",
        "",
    ) == "synced_degraded_fallback"


def test_queue_success_archives_prior_failed_attempts() -> None:
    queue = queue_sync._empty_queue()
    queue["pending"] = [{"nb_id": "nb-1", "title": "Notebook", "profile": "a.hominidae"}]
    claim, reason = queue_sync._claim_pending(queue, "worker-1", "a.hominidae")
    assert reason == "claimed"
    claimed, lease_id = claim
    queue["failed"] = [{
        "nb_id": "nb-1",
        "title": "Notebook",
        "profile": "a.hominidae",
        "attempts": 1,
        "error": "failed (rc=1)",
    }]

    assert queue_sync._record_success(
        queue, "worker-1", lease_id, claimed, "a.hominidae", "synced", 2.5
    )
    assert queue["failed"] == []
    assert queue["failure_history"][0]["nb_id"] == "nb-1"
    assert queue["failure_history"][0]["history_status"] == "resolved_terminal"


def test_queue_reconcile_archives_stale_failures_for_success_and_poison() -> None:
    queue = queue_sync._empty_queue()
    queue["completed"] = [{"nb_id": "done", "profile": "a.hominidae"}]
    queue["poisoned"] = [{"nb_id": "poison", "profile": "troup.hominidae"}]
    queue["failed"] = [
        {"nb_id": "done", "profile": "a.hominidae", "attempts": 1},
        {"nb_id": "poison", "profile": "troup.hominidae", "attempts": 2},
        {"nb_id": "active", "profile": "a.hominidae", "attempts": 1},
    ]

    assert queue_sync.reconcile_terminal_records(queue) == 2
    assert [item["nb_id"] for item in queue["failed"]] == ["active"]
    assert {item["nb_id"] for item in queue["failure_history"]} == {"done", "poison"}


def test_queue_claim_enforces_global_and_per_account_capacity() -> None:
    queue = queue_sync._empty_queue()
    queue["config"]["workers"] = 3
    queue["config"]["profile_limits"]["a.hominidae"] = 1
    queue["pending"] = [
        {"nb_id": "pro-1", "profile": "a.hominidae"},
        {"nb_id": "pro-2", "profile": "a.hominidae"},
        {"nb_id": "free-1", "profile": "troup.hominidae"},
    ]

    first, reason = queue_sync._claim_pending(queue, "worker-pro-1", "a.hominidae")
    assert reason == "claimed"
    assert first[0]["profile"] == "a.hominidae"
    assert queue["in_progress"]["worker-pro-1"]["lease_id"] == first[1]

    second, reason = queue_sync._claim_pending(queue, "worker-pro-2", "a.hominidae")
    assert second is None
    assert reason == "capacity"

    third, reason = queue_sync._claim_pending(queue, "worker-free-1", "troup.hominidae")
    assert reason == "claimed"
    assert third[0]["nb_id"] == "free-1"


def test_queue_reclaims_only_expired_iso_epoch_leases() -> None:
    queue = queue_sync._empty_queue()
    queue["config"]["lease_timeout_s"] = 60
    queue["in_progress"] = {
        "stale": {
            "nb_id": "nb-stale", "title": "Stale", "profile": "a.hominidae",
            "started_at": "2026-01-01T00:00:00Z", "started_at_epoch": 1.0,
        },
        "legacy": {
            "nb_id": "nb-legacy", "title": "Legacy", "profile": "a.hominidae",
            "started_at": "23:59:59",
        },
    }

    reclaimed = queue_sync._reclaim_stale_leases(queue, now_epoch=1000.0)
    assert [item["nb_id"] for item in reclaimed] == ["nb-stale"]
    assert queue["in_progress"]["legacy"]["nb_id"] == "nb-legacy"
    assert queue["pending"][0]["nb_id"] == "nb-stale"


def test_corrupt_queue_is_not_replaced_with_empty_queue(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "queue.json"
    queue_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    monkeypatch.setattr(queue_sync, "_lock_path", lambda: queue_path.with_suffix(".lock"))

    with pytest.raises(RuntimeError, match="invalid JSON"):
        queue_sync.load_queue()
    assert queue_path.read_text(encoding="utf-8") == "{not-json"


def test_cookie_export_honors_explicit_output_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(export_yt_cookies, "load_canonical_cookies", lambda _profile: [
        {"domain": ".youtube.com", "name": "SID", "value": "secret", "path": "/"}
    ])
    explicit = tmp_path / "custom" / "cookies.txt"
    result = export_yt_cookies.export_profile(
        "a.hominidae", tmp_path / "default", output_path=explicit
    )

    assert result == explicit
    assert explicit.exists()
    assert "SID\tsecret" in explicit.read_text(encoding="utf-8")
    assert not (tmp_path / "default" / "cookies-a.hominidae.txt").exists()


def test_sync_refuses_to_advance_when_source_snapshot_fails(monkeypatch) -> None:
    monkeypatch.setattr(sync_orchestrator, "notebook_title", lambda _nb, _profile: "Notebook")

    def fail(*_args, **_kwargs):
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(sync_orchestrator, "list_sources", fail)
    result = sync_orchestrator.sync_one(
        "nb-1", "a.hominidae", dry_run=False, clusters_path=None
    )

    assert result["status"] == "source_snapshot_failed"
