from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit_manifest_gaps import build_report, render_markdown


def test_gap_audit_reports_only_completed_ids_missing_from_manifest(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    evidence = tmp_path / "logs"
    evidence.mkdir()
    (evidence / "worker.log").write_text("completed=nb-gap\n", encoding="utf-8")
    (evidence / "transcript.md").write_text(
        "---\nsource_id: source-1\nnotebook_id: nb-gap\nexported: 2026-08-09\n---\n",
        encoding="utf-8",
    )
    (evidence / "concept.md").write_text(
        "sources:\n  - NotebookLM notebook nb-gap (title, synced 2026-08-09)\n",
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps({
            "completed": [{"nb_id": "nb-present"}, {"nb_id": "nb-gap"}, {"nb_id": "nb-gap"}],
        }),
        encoding="utf-8",
    )
    manifest.write_text(json.dumps({"notebooks": {"nb-present": {}}}), encoding="utf-8")

    report = build_report(queue, manifest, (evidence,), evidence, evidence)

    assert report["completed_distinct_count"] == 2
    assert report["manifest_entry_count"] == 1
    assert report["gap_count"] == 1
    assert report["gaps"][0]["notebook_id"] == "nb-gap"
    assert report["gaps"][0]["status"] == "output_and_receipt_found_manual_review"
    assert report["gaps"][0]["source_ids"] == ["source-1"]
    assert "nb-gap" in render_markdown(report)


def test_gap_audit_does_not_invent_missing_evidence(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    queue.write_text(json.dumps({"completed": [{"nb_id": "nb-gap"}]}), encoding="utf-8")
    manifest.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")

    report = build_report(
        queue,
        manifest,
        (tmp_path / "missing",),
        tmp_path / "missing",
        tmp_path / "missing",
    )

    assert report["gaps"][0]["status"] == "queue_only_no_local_output_evidence"
    assert report["gaps"][0]["transcript_paths"] == []


def test_textual_notebook_id_is_not_output_evidence(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "notes.md").write_text("nb-gap was mentioned here\n", encoding="utf-8")
    queue.write_text(json.dumps({"completed": [{"nb_id": "nb-gap"}]}), encoding="utf-8")
    manifest.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")

    report = build_report(queue, manifest, (evidence,), evidence, evidence)

    assert report["gaps"][0]["status"] == "queue_only_no_local_output_evidence"
    assert report["output_provenance_found_count"] == 0


def test_audit_flags_degraded_page_missing_from_current_manifest_slugs(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    notebook_id = "22222222-2222-2222-2222-222222222222"
    (concepts / "old-fallback-page.md").write_text(
        "---\n"
        "title: old-fallback-page\n"
        "tags: [nlm-synced, degraded-fallback]\n"
        "---\n"
        "sources:\n"
        f"  - NotebookLM notebook {notebook_id} (title, synced 2026-08-12)\n",
        encoding="utf-8",
    )
    (concepts / "current-page.md").write_text(
        "---\n"
        "title: current-page\n"
        "tags: [nlm-synced, degraded-fallback]\n"
        "---\n"
        "sources:\n"
        f"  - NotebookLM notebook {notebook_id} (title, synced 2026-08-12)\n",
        encoding="utf-8",
    )
    queue.write_text(json.dumps({"completed": []}), encoding="utf-8")
    manifest.write_text(
        json.dumps({"notebooks": {notebook_id: {"concept_slugs": ["current-page"]}}}),
        encoding="utf-8",
    )

    report = build_report(queue, manifest, (), None, concepts)

    assert report["unmanifested_degraded_page_count"] == 1
    page = report["unmanifested_degraded_pages"][0]
    assert page["slug"] == "old-fallback-page"
    assert page["status"] == "degraded_page_slug_missing_from_manifest"
    assert "old-fallback-page" in render_markdown(report)


def test_audit_flags_degraded_page_when_notebook_is_not_in_manifest(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "orphan-page.md").write_text(
        "---\ntags: [degraded-fallback]\n---\n"
        "NotebookLM notebook 11111111-1111-1111-1111-111111111111\n",
        encoding="utf-8",
    )
    queue.write_text(json.dumps({"completed": []}), encoding="utf-8")
    manifest.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")

    report = build_report(queue, manifest, (), None, concepts)

    assert report["unmanifested_degraded_pages"][0]["status"] == (
        "degraded_page_notebook_missing_from_manifest"
    )


def test_gap_audit_records_hashes_and_manifest_page_parity(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    concepts = tmp_path / "concepts"
    transcripts = tmp_path / "transcripts"
    concepts.mkdir()
    transcripts.mkdir()
    transcript = transcripts / "source.md"
    transcript.write_text(
        "---\nsource_id: source-1\nnotebook_id: nb-gap\n---\ntext\n",
        encoding="utf-8",
    )
    concept = concepts / "owned.md"
    concept.write_text("NotebookLM notebook nb-gap\n", encoding="utf-8")
    (concepts / "unowned.md").write_text("historical page\n", encoding="utf-8")
    queue.write_text(json.dumps({"completed": [{"nb_id": "nb-gap"}]}), encoding="utf-8")
    manifest.write_text(
        json.dumps({"notebooks": {"other": {"concept_slugs": ["owned"]}}}),
        encoding="utf-8",
    )

    report = build_report(queue, manifest, (), transcripts, concepts)
    row = report["gaps"][0]
    assert row["transcript_sha256"][str(transcript)] == hashlib.sha256(
        transcript.read_bytes()
    ).hexdigest()
    assert row["concept_sha256"][str(concept)] == hashlib.sha256(
        concept.read_bytes()
    ).hexdigest()
    parity = report["manifest_page_parity"]
    assert parity["manifest_references_missing_on_disk"] == []
    assert parity["unowned_concept_file_count"] == 1
    assert "Manifest/page parity" in render_markdown(report)


def test_reconciliation_receipt_reports_hashes_terminal_ids_and_coverage(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "semantic.md").write_text(
        "---\ntags: [nlm-synced]\n---\n"
        "## Citations (from contributing transcripts)\n\n"
        "- **Claim:** grounded claim\n  - Source: source-1\n",
        encoding="utf-8",
    )
    (concepts / "degraded.md").write_text(
        "---\ntags: [nlm-synced, degraded-fallback]\n---\n"
        "No semantic citations.\n",
        encoding="utf-8",
    )
    queue.write_text(json.dumps({
        "completed": [],
        "failed": [{"nb_id": "failed-1"}],
        "poisoned": [{"nb_id": "poisoned-1"}],
        "needs_resynthesis": [{"nb_id": "deferred-1"}],
    }), encoding="utf-8")
    manifest.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")

    report = build_report(queue, manifest, (), None, concepts)

    assert report["queue_sha256"] == hashlib.sha256(queue.read_bytes()).hexdigest()
    assert report["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert report["queue_state_ids"] == {
        "failed": ["failed-1"],
        "poisoned": ["poisoned-1"],
        "deferred": ["deferred-1"],
        "in_progress": [],
    }
    coverage = report["citation_coverage"]
    assert coverage["concept_page_count"] == 2
    assert coverage["pages_with_citations"] == 1
    assert coverage["citation_coverage_percent"] == 50.0
    assert coverage["degraded_page_count"] == 1
    assert coverage["degraded_citation_coverage_percent"] == 0.0
    receipt = report["reconciliation_receipt"]
    assert receipt["recovery_eligibility"]["eligible"] is False
    assert receipt["recovery_eligibility"]["status"] == "ineligible_read_only_audit"


def test_terminal_receipt_mode_does_not_require_output_file(tmp_path) -> None:
    """The CLI can emit a read-only receipt without creating an audit artifact."""
    import subprocess

    queue = tmp_path / "queue.json"
    manifest = tmp_path / "manifest.json"
    queue.write_text(json.dumps({"completed": []}), encoding="utf-8")
    manifest.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "scripts" / "audit_manifest_gaps.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--queue", str(queue),
            "--manifest", str(manifest),
            "--print-receipt",
            "--transcript-root", str(tmp_path / "missing-transcripts"),
            "--concept-root", str(tmp_path / "missing-concepts"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    receipt = json.loads(result.stdout)
    assert receipt["reconciliation_receipt"]["recovery_eligibility"]["eligible"] is False
