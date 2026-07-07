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
    # The four claim_type branches the agent switches on.
    for ct in ("existence", "static-shape", "behavior", "non-code"):
        assert ct in text, f"agent doc missing claim_type branch '{ct}'"
