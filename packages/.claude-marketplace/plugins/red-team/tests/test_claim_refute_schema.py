"""test_claim_refute_schema.py - codify the §1.5 claim-refute pass contract.

The claim-refuter agent (agents/red-team-claim-refuter.md) writes
`{run_dir}/claim-refute.json` in the findings schema. The critic globs
`{run_dir}/*.json` and validates via __lib/findings_schema.py — so the
contract that keeps the critic consuming unchanged is: the claim-refute
output MUST pass `findings_schema.validate()`.

Asserts:
  - a populated claim-refute object (one failed claim) validates cleanly,
  - the all-verified edge case (empty `findings: []` + meta counts) validates,
  - a malformed finding (missing required field / bad severity / bad claim_type)
    is REJECTED — so the critic's FM-2 parse fallback isn't the only guard,
  - the agent file documents the exact schema fields the test checks.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "__lib"))
from findings_schema import validate  # noqa: E402

_AGENT = ROOT / "agents" / "red-team-claim-refuter.md"


def _obj(findings):
    return {"specialist": "claim-refuter", "writer_session": "s1",
            "meta": {"claims_checked": 2, "claims_verified": 1, "claims_failed": 1},
            "findings": findings}


POPULATED = _obj([{
    "id": "CLAIM-1", "severity": "REVISE", "category": "unverified-claim",
    "location": "commands/red-team.md:84", "title": "claim X is wired",
    "detail": "asserts wired; grep shows no registration",
    "evidence": "grep: 0 hits", "confidence": "high",
    "fix": "register or remove the claim", "claim_type": "existence",
}])


def test_populated_output_validates():
    assert validate(POPULATED) == []


def test_all_verified_empty_findings_validates():
    """When every claim verifies, the file still must be schema-valid (empty list + meta)."""
    obj = _obj([])
    obj["meta"] = {"claims_checked": 1, "claims_verified": 1, "claims_failed": 0}
    assert validate(obj) == []


def test_missing_required_field_rejected():
    bad = _obj([{"id": "X", "severity": "REVISE"}])  # missing location/title/detail/evidence/fix
    errs = validate(bad)
    assert errs, f"expected validation errors, got none"
    assert any("missing required field" in e for e in errs)


def test_bad_severity_rejected():
    bad = _obj([{**POPULATED["findings"][0], "severity": "MAYBE"}])
    errs = validate(bad)
    assert any("severity" in e and "MAYBE" in e for e in errs), errs


def test_bad_claim_type_rejected():
    bad = _obj([{**POPULATED["findings"][0], "claim_type": "vibe"}])
    errs = validate(bad)
    assert any("claim_type" in e and "vibe" in e for e in errs), errs


def test_agent_doc_matches_schema_fields():
    """The agent markdown must document every required field the schema enforces."""
    text = _AGENT.read_text(encoding="utf-8", errors="replace")
    for field in ("id", "severity", "location", "title", "detail",
                  "evidence", "fix", "claim_type"):
        assert field in text, f"agent doc missing required field '{field}'"
    # The claim_type branches the agent switches on — including the
    # scope-completeness branch added to catch the self-review failure mode
    # where an author claims "X is untouched" without grepping the monorepo.
    for ct in ("existence", "static-shape", "behavior", "non-code", "scope-completeness"):
        assert ct in text, f"agent doc missing claim_type branch '{ct}'"


def test_scope_completeness_claim_type_accepted():
    """The scope-completeness branch must pass validation — it is the claim_type
    that backs 'I checked everywhere' claims and is verified by repo-wide grep,
    not by reading the file the author named. Catches the self-review failure
    mode where the same context that drafted the code accepts its own scope
    claim without scanning the full blast radius."""
    obj = _obj([{
        "id": "CLAIM-1", "severity": "REVISE",
        "category": "unverified-claim",
        "location": "cc-skills-ai-api/skills/ai-cli/ai_cli.py:4532",
        "title": "claim: prompting-toolkit refs removed from monorepo",
        "detail": "summary said refs removed; repo-wide grep shows live import",
        "evidence": "grep -rn prompting_toolkit P:/packages -> 3 hits incl ai_cli.py",
        "confidence": "high",
        "fix": "remove the --prompt-toolkit flag from ai_cli.py or mark pending_backend",
        "claim_type": "scope-completeness",
    }])
    assert validate(obj) == []


def test_scope_completeness_branch_is_in_agent_doc():
    """The agent must document the scope-completeness verification procedure
    (grep the monorepo, cite the command + hit count), since that is the
    discriminating step that makes the branch useful."""
    text = _AGENT.read_text(encoding="utf-8", errors="replace")
    assert "scope-completeness" in text
    assert "monorepo" in text or "repo-wide" in text or "repo wide" in text.lower()
    assert "grep" in text


def test_agent_doc_claim_type_enum_matches_schema():
    """The claim_type values documented in the agent prompt must match
    VALID_CLAIM_TYPES in the schema exactly — no drift."""
    import re
    text = _AGENT.read_text(encoding="utf-8", errors="replace")
    # Find all claim_type enumerations in the agent doc
    matches = re.findall(r'"claim_type":\s*"([^"]+)"', text)
    assert matches, "No claim_type examples found in agent doc"
    documented = set()
    for m in matches:
        for part in m.split("|"):
            documented.add(part.strip())
    schema_types = set(__import__("findings_schema").VALID_CLAIM_TYPES)
    missing_from_doc = schema_types - documented
    assert not missing_from_doc, (
        f"VALID_CLAIM_TYPES has types not in agent doc examples: {missing_from_doc}"
    )
