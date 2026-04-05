from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unified_claim_verifier as ucv


def test_detect_claims_basic() -> None:
    text = "The file module exists.\nNo-op line.\nTests pass now."
    claims = ucv.detect_claims(text)
    assert len(claims) == 2


def test_extract_entities_keeps_compounds() -> None:
    entities = ucv._extract_entities("`append_tool_event` lives in evidence_store.py")
    assert "append_tool_event" in entities
    assert "evidence_store.py" in entities


def test_claim_detection_does_not_overmatch_process_language() -> None:
    text = "I verified the file contents and confirmed the line numbers."
    claims = ucv.detect_claims(text)
    assert claims == []


def test_scoped_invalidation_preserves_unrelated_observations() -> None:
    events = [
        {"name": "Read", "command": "src/a.py", "cwd": "P:/repo", "output": ""},
        {"name": "Read", "command": "src/b.py", "cwd": "P:/repo", "output": ""},
        {"name": "Edit", "command": "src/a.py", "cwd": "P:/repo", "output": ""},
    ]
    window = ucv._evidence_window(events)
    assert [e["command"] for e in window] == ["src/b.py"]


def test_fuzzy_entity_matching_handles_basename_variants() -> None:
    claim_entities = {"sessionstart_router"}
    evidence_entities = {"SessionStart_router.py"}
    matches = ucv._match_entities(claim_entities, evidence_entities)
    assert "SessionStart_router.py" in matches


def test_equivalence_claim_requires_same_chunk_cooccurrence() -> None:
    response = "I found that `arch` is `architectural-validator`."
    tool_sequence = [
        {"name": "Read", "command": "docs/skills.md", "output": "architectural-validator package details"},
        {"name": "Read", "command": "docs/commands.md", "output": "/arch command usage"},
    ]
    result = ucv.evaluate_claims(response_text=response, tool_sequence=tool_sequence)
    assert result["decision"] == "block"
    assert result["reason"] == "UNVERIFIED_CLAIMS"


def test_equivalence_claim_allows_same_chunk_cooccurrence() -> None:
    response = "I found that `arch` is `architectural-validator`."
    tool_sequence = [
        {
            "name": "Read",
            "command": "docs/skills.md",
            "output": "The /arch command is provided by the architectural-validator package.",
        },
    ]
    result = ucv.evaluate_claims(response_text=response, tool_sequence=tool_sequence)
    assert result["decision"] == "allow"


def test_detect_claims_plain_equivalence_form() -> None:
    claims = ucv.detect_claims("arch is architectural-validator")
    assert len(claims) == 1


def test_plain_equivalence_requires_same_chunk_cooccurrence() -> None:
    response = "arch is architectural-validator"
    split_evidence = [
        {"name": "Read", "command": "docs/skills.md", "output": "architectural-validator package details"},
        {"name": "Read", "command": "docs/commands.md", "output": "arch command usage"},
    ]
    same_chunk = [
        {"name": "Read", "command": "docs/skills.md", "output": "arch is architectural-validator."},
    ]
    blocked = ucv.evaluate_claims(response_text=response, tool_sequence=split_evidence)
    allowed = ucv.evaluate_claims(response_text=response, tool_sequence=same_chunk)
    assert blocked["decision"] == "block"
    assert allowed["decision"] == "allow"


def test_equivalence_alias_phrase_blocks_without_cooccurrence() -> None:
    response = "`arch` is an alias for `architectural-validator`."
    tool_sequence = [
        {"name": "Read", "command": "docs/skills.md", "output": "architectural-validator package details"},
        {"name": "Read", "command": "docs/commands.md", "output": "/arch command usage"},
    ]
    result = ucv.evaluate_claims(response_text=response, tool_sequence=tool_sequence)
    assert result["decision"] == "block"


def test_is_fixed_not_classified_as_equivalence() -> None:
    assert not ucv._is_equivalence_claim(
        "The bug is fixed in /arch.",
        {"bug", "arch"},
    )


def test_match_entities_combines_exact_and_fuzzy() -> None:
    claim_entities = {"arch", "architectural-validator"}
    evidence_entities = {"arch", "architectural", "validator"}
    matches = ucv._match_entities(claim_entities, evidence_entities)
    assert "arch" in matches
    assert "architectural" in matches or "validator" in matches


# === Regression tests: structural formatting should not trigger claims ===

def test_markdown_header_with_missing_not_detected() -> None:
    """Regression: '## What's Missing (Minor)' was falsely detected as a claim."""
    claims = ucv.detect_claims("## What's Missing (Minor)\n\nThe core system works.")
    header_claims = [c for c in claims if "Missing" in c and c.startswith("#")]
    assert header_claims == [], f"Header falsely detected as claim: {header_claims}"


def test_question_with_claim_keyword_not_detected() -> None:
    """Regression: question ending with '?' was falsely detected as a claim."""
    claims = ucv.detect_claims("Or is there a different practical improvement you had in mind?")
    assert claims == [], f"Question falsely detected as claim: {claims}"


def test_blockquote_not_detected() -> None:
    """Blockquoted text should not be detected as claims."""
    claims = ucv.detect_claims("> The file was deleted\n\nI will check the current state.")
    blockquote_claims = [c for c in claims if "deleted" in c.lower()]
    assert blockquote_claims == [], f"Blockquote falsely detected: {blockquote_claims}"


def test_table_row_not_detected() -> None:
    """Table rows are formatting, not factual claims."""
    claims = ucv.detect_claims("| Component | Status |\n|---|---|\n| Missing items | Not verified |")
    assert claims == [], f"Table row falsely detected as claim: {claims}"


def test_question_starting_with_would_not_detected() -> None:
    """Questions starting with 'Would you' should not be claims."""
    claims = ucv.detect_claims("Would you like me to add the missing test scenarios?")
    assert claims == [], f"Question falsely detected: {claims}"


def test_real_claim_still_detected_after_stripping() -> None:
    """Actual claims in body text must still be detected after formatting is stripped."""
    text = "## Summary\n\nThe implementation is fixed and working correctly.\n\n---"
    claims = ucv.detect_claims(text)
    assert len(claims) >= 1, f"Real claim not detected after stripping: {claims}"
    # The header and HR should be gone, but the body claim should remain
    assert not any(c.startswith("#") for c in claims), "Header leaked through"
