from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_BIN = Path("P:/.agents/skills/wiki-yt/scripts/bin")
if str(SCRIPTS_BIN) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_BIN))

import queue_sync


def _write_queue(path: Path, failed: list[dict]) -> None:
    queue = queue_sync._empty_queue()
    queue["failed"] = failed
    path.write_text(json.dumps(queue), encoding="utf-8")


def test_retry_failed_refuses_legacy_profileless_records(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    failed = [{"nb_id": "legacy-id", "title": "Legacy", "attempts": 1}]
    _write_queue(queue_path, failed)
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)

    before = queue_path.read_text(encoding="utf-8")
    assert queue_sync.do_retry_failed() == 2
    assert queue_path.read_text(encoding="utf-8") == before


def test_retry_poisoned_refuses_legacy_profileless_records(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    queue = queue_sync._empty_queue()
    queue["poisoned"] = [{"nb_id": "legacy-poison", "title": "Legacy", "attempts": 3}]
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)

    before = queue_path.read_text(encoding="utf-8")
    assert queue_sync.do_retry_poisoned(["legacy-poison"], "mmx") == 2
    assert queue_path.read_text(encoding="utf-8") == before


def test_retry_failed_preserves_exact_canonical_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    _write_queue(
        queue_path,
        [{
            "nb_id": "owned-id",
            "title": "Owned",
            "source_count": 50,
            "profile": "troup.hominidae",
            "attempts": 1,
        }],
    )
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)

    assert queue_sync.do_retry_failed() == 0
    result = json.loads(queue_path.read_text(encoding="utf-8"))
    assert result["failed"] == []
    assert result["pending"] == [{
        "nb_id": "owned-id",
        "title": "Owned",
        "source_count": 50,
        "profile": "troup.hominidae",
        "attempts": 1,
    }]


def test_run_captured_terminates_descendants_and_records_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        pid = 1234
        returncode = -9

        def __init__(self) -> None:
            self.communicate_calls = 0

        def communicate(self, timeout=None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(["sync"], timeout, output="partial", stderr="child")
            return "partial", "child"

        def kill(self) -> None:
            self.returncode = -9

    import subprocess

    process = FakeProcess()
    terminated: list[int] = []
    monkeypatch.setattr(queue_sync.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(queue_sync, "_terminate_process_tree", lambda value: terminated.append(value.pid))

    returncode, stdout, stderr, timed_out = queue_sync._run_captured(["sync"], timeout=1)

    assert returncode == 124
    assert stdout == "partial"
    assert "TIMEOUT after 1s; process_tree_terminated" in stderr
    assert timed_out is True
    assert terminated == [1234]


def test_degraded_success_creates_explicit_resynthesis_obligation(tmp_path: Path) -> None:
    queue = queue_sync._empty_queue()
    queue["in_progress"] = {
        "worker-1": {"lease_id": "lease-1", "profile": "a.hominidae"}
    }
    item = {
        "nb_id": "degraded-id",
        "title": "Degraded",
        "source_count": 50,
        "profile": "a.hominidae",
    }

    assert queue_sync._record_success(
        queue,
        "worker-1",
        "lease-1",
        item,
        "a.hominidae",
        "synced_degraded_fallback",
        12.5,
        output_paths=(tmp_path / "out.log", tmp_path / "err.log"),
    )

    assert queue["completed"][0]["status"] == "synced_degraded_fallback"
    assert queue["completed"][0]["stdout_path"].endswith("out.log")
    assert queue["needs_resynthesis"] == [{
        "nb_id": "degraded-id",
        "title": "Degraded",
        "source_count": 50,
        "profile": "a.hominidae",
        "reason": "degraded_fallback",
        "attempts": 0,
        "deferred_at": queue["needs_resynthesis"][0]["deferred_at"],
        "stdout_path": str(tmp_path / "out.log"),
        "stderr_path": str(tmp_path / "err.log"),
    }]


def test_semantic_success_clears_only_matching_resynthesis_obligation() -> None:
    queue = queue_sync._empty_queue()
    queue["needs_resynthesis"] = [
        {"nb_id": "keep-id", "profile": "a.hominidae"},
        {"nb_id": "clear-id", "profile": "a.hominidae"},
    ]
    queue["in_progress"] = {
        "worker-1": {"lease_id": "lease-1", "profile": "a.hominidae"}
    }

    assert queue_sync._record_success(
        queue,
        "worker-1",
        "lease-1",
        {"nb_id": "clear-id", "profile": "a.hominidae"},
        "a.hominidae",
        "synced",
        1.0,
    )

    assert [item["nb_id"] for item in queue["needs_resynthesis"]] == ["keep-id"]


def test_retry_deferred_preserves_exact_profile_and_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    queue = queue_sync._empty_queue()
    queue["needs_resynthesis"] = [{
        "nb_id": "deferred-id",
        "title": "Deferred",
        "source_count": 50,
        "profile": "troup.hominidae",
        "reason": "degraded_fallback",
        "attempts": 1,
    }]
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)

    assert queue_sync.do_retry_deferred(
        ["deferred-id"], "dgemma", timeout_s=90, max_attempts=1
    ) == 0

    result = json.loads(queue_path.read_text(encoding="utf-8"))
    assert result["pending"] == [{
        "nb_id": "deferred-id",
        "title": "Deferred",
        "source_count": 50,
        "profile": "troup.hominidae",
        "retry_backend": "dgemma",
        "force_resynthesis": True,
        "deferred_resynthesis": True,
        "timeout_s": 90.0,
        "max_attempts": 1,
        "attempts": 1,
        "last_error": "",
        "retry_reason": "bounded deferred semantic retry",
        "reopened_at": result["pending"][0]["reopened_at"],
    }]
    assert result["deferred_history"][0]["history_status"] == "reopened"


def test_queue_upgrade_recovers_legacy_degraded_completion() -> None:
    queue = {
        "completed": [{
            "nb_id": "legacy-degraded",
            "title": "Legacy",
            "profile": "a.hominidae",
            "status": "synced_degraded_fallback",
            "completed_at": "2026-08-09T00:00:00Z",
        }],
    }

    queue_sync._upgrade_queue(queue)

    assert queue["schema_version"] == queue_sync.QUEUE_SCHEMA_VERSION
    assert queue["needs_resynthesis"][0]["nb_id"] == "legacy-degraded"
    assert queue["needs_resynthesis"][0]["legacy_migration"] is True


def test_queue_upgrade_does_not_resurrect_debt_after_semantic_success() -> None:
    queue = {
        "completed": [
            {
                "nb_id": "legacy-degraded",
                "profile": "a.hominidae",
                "status": "synced_degraded_fallback",
            },
            {
                "nb_id": "legacy-degraded",
                "profile": "a.hominidae",
                "status": "synced",
            },
        ],
        "needs_resynthesis": [{
            "nb_id": "legacy-degraded",
            "profile": "a.hominidae",
            "reason": "degraded_fallback",
        }],
    }

    queue_sync._upgrade_queue(queue)

    assert queue["needs_resynthesis"] == []


def test_recover_worker_releases_only_dead_pid_without_requeue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    queue = queue_sync._empty_queue()
    queue["in_progress"] = {
        "orphan-worker": {
            "nb_id": "orphaned-id",
            "title": "Orphaned",
            "source_count": 50,
            "profile": "a.hominidae",
            "pid": 999999,
            "attempts": 1,
            "lease_id": "lease-1",
        }
    }
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    monkeypatch.setattr(queue_sync, "_pid_is_alive", lambda pid: False)

    assert queue_sync.do_recover_worker("orphan-worker") == 0

    result = json.loads(queue_path.read_text(encoding="utf-8"))
    assert result["in_progress"] == {}
    assert result["pending"] == []
    assert [item["nb_id"] for item in result["failed"]] == ["orphaned-id"]
    assert result["failure_history"][-1]["history_status"] == "abandoned_orphan"
    assert result["failure_history"][-1]["recovery_reason"] == "orphaned worker recovery"


def test_recover_worker_refuses_live_pid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    queue_path = tmp_path / "queue.json"
    queue = queue_sync._empty_queue()
    queue["in_progress"] = {
        "live-worker": {
            "nb_id": "live-id",
            "profile": "a.hominidae",
            "pid": 123,
            "attempts": 1,
            "lease_id": "lease-2",
        }
    }
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    monkeypatch.setattr(queue_sync, "QUEUE_FILE", queue_path)
    monkeypatch.setattr(queue_sync, "_pid_is_alive", lambda pid: True)

    assert queue_sync.do_recover_worker("live-worker") == 2

    result = json.loads(queue_path.read_text(encoding="utf-8"))
    assert "live-worker" in result["in_progress"]
    assert result["failed"] == []
    assert result["failure_history"] == []
