"""Tests for wiki-yt report metric extraction."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from report import extract_cited_source_ids


def test_extract_cited_source_ids_supports_legacy_and_transcript_cluster_forms():
    legacy_id = "11111111-1111-1111-1111-111111111111"
    transcript_id = "22222222-2222-2222-2222-222222222222"
    bare_id = "33333333-3333-3333-3333-333333333333"
    text = f"""
sources:
  - \"NotebookLM source {legacy_id}\" (synced 2026-08-10)
- **Claim:** grounded claim
  - Source: Transcript title (`{transcript_id}`)
  - Context: excerpt
- **Claim:** another claim
  - Source: `{bare_id}`
"""

    assert extract_cited_source_ids(text) == {legacy_id, transcript_id, bare_id}


def test_extract_cited_source_ids_ignores_notebook_and_concept_ids():
    notebook_id = "44444444-4444-4444-4444-444444444444"
    concept_id = "55555555-5555-5555-5555-555555555555"
    text = (
        f"id: {concept_id}\n"
        f"url: https://notebooklm.google.com/notebook/{notebook_id}\n"
        "No citation lines are present."
    )

    assert extract_cited_source_ids(text) == set()
