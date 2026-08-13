"""Offline tests for resumable Stage-C synthesis checkpoints."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import synthesize_subtopics as synth


def _members(cluster, _directory):
    sid = f"source-{cluster['cluster_id']}"
    return [{"source_id": sid, "title": f"Source {sid}",
             "text": f"Grounded text for cluster {cluster['cluster_id']}", "url": None}]


def _parsed(cluster, members):
    member = members[0]
    return {"title": f"Topic {cluster['cluster_id']}", "definition": "A grounded topic.",
            "details": ["A detail"], "values": [], "related": [],
            "citations": [{"claim": "Grounded text", "source_id": member["source_id"],
                           "source_title": member["title"], "cited_text": member["text"]}]}


def _invoke(monkeypatch, tmp_path, checkpoint=None, resume=None, failures=(),
            allow_degraded=False, degraded_clusters=()):
    clusters = [{"cluster_id": 1, "name": "One", "member_source_ids": ["source-1"]},
                {"cluster_id": 2, "name": "Two", "member_source_ids": ["source-2"]}]
    subtopics = tmp_path / "subtopics.json"
    subtopics.write_text(json.dumps({"notebook_id": "nb", "clusters": clusters}), encoding="utf-8")
    output = tmp_path / "concepts.json"
    calls = []

    def fake_synth(cluster, members, *args, **kwargs):
        calls.append(cluster["cluster_id"])
        if cluster["cluster_id"] in failures:
            return None, "stub failure"
        parsed = _parsed(cluster, members)
        if cluster["cluster_id"] in degraded_clusters:
            parsed["synthesis_quality"] = "degraded_fallback"
        return parsed, ""

    monkeypatch.setattr(synth, "gather_members", _members)
    monkeypatch.setattr(synth, "synth_cluster", fake_synth)
    monkeypatch.setattr(synth.time, "sleep", lambda _seconds: None)
    argv = ["synthesize_subtopics.py", "--subtopics", str(subtopics),
            "--transcripts-dir", str(tmp_path), "--notebook", "nb",
            "--notebook-title", "Notebook", "-o", str(output)]
    if checkpoint:
        argv += ["--checkpoint", str(checkpoint)]
    if resume:
        argv += ["--resume", str(resume)]
    if allow_degraded:
        argv.append("--allow-degraded-fallback")
    monkeypatch.setattr(sys, "argv", argv)
    return synth.main(), calls, output, subtopics


def test_checkpoint_persists_after_successful_clusters(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    rc, calls, _output, _ = _invoke(monkeypatch, tmp_path, checkpoint=checkpoint)
    assert rc == 0
    assert calls == [1, 2]
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [record["cluster_id"] for record in payload["records"]] == [1, 2]
    assert payload["failed"] == []
    assert not list(tmp_path.glob(".stage-c.json.*.tmp"))


def test_resume_skips_validated_success_and_retries_failure(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    rc, calls, output, _ = _invoke(monkeypatch, tmp_path, checkpoint=checkpoint, failures=(2,))
    assert rc == 5 and calls == [1, 2] and not output.exists()
    rc, calls, output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 0 and calls == [2] and output.exists()


def test_resume_retries_missing_cluster_record(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    _invoke(monkeypatch, tmp_path, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    payload["records"] = payload["records"][:1]
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    rc, calls, _output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 0 and calls == [2]


def test_corrupt_checkpoint_is_rejected_before_backend(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    checkpoint.write_text("{not json", encoding="utf-8")
    rc, calls, _output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 2 and calls == []


def test_duplicate_or_mismatched_cluster_checkpoint_is_rejected(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    _invoke(monkeypatch, tmp_path, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    payload["records"].append(payload["records"][0])
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    rc, calls, _output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 2 and calls == []


def test_mismatched_cluster_checkpoint_is_rejected(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    _invoke(monkeypatch, tmp_path, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    payload["records"][0]["cluster_id"] = 99
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    rc, calls, _output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 2 and calls == []


def test_resume_does_not_reuse_degraded_record_without_opt_in(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    rc, calls, _output, _ = _invoke(
        monkeypatch, tmp_path, checkpoint=checkpoint,
        allow_degraded=True, degraded_clusters=(1,),
    )
    assert rc == 0 and calls == [1, 2]
    rc, calls, output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint)
    assert rc == 0 and calls == [1] and output.exists()
    concepts = json.loads(output.read_text(encoding="utf-8"))
    assert all(item["synthesis_quality"] != "degraded_fallback" for item in concepts)


def test_failed_run_does_not_promote_or_modify_final_output(monkeypatch, tmp_path):
    checkpoint = tmp_path / "stage-c.json"
    rc, _calls, output, _ = _invoke(monkeypatch, tmp_path, checkpoint=checkpoint, failures=(2,))
    assert rc == 5 and not output.exists()
    output.write_text("sentinel", encoding="utf-8")
    rc, _calls, _output, _ = _invoke(monkeypatch, tmp_path, resume=checkpoint, failures=(2,))
    assert rc == 5 and output.read_text(encoding="utf-8") == "sentinel"
    assert not list(tmp_path.glob(".concepts.json.*.tmp"))
