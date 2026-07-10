"""Findings JSON schema validator for /red-team disk-backed handoff.

Pure logic, no I/O. The smallest slice of orchestrator.py (Phase 1) that makes
the schema invariant unit-testable. Anchors the per-specialist writer_session
contract (STATE-2) and gives the critic a deterministic pre-check before its
FM-2 parse fallback kicks in.
"""

from __future__ import annotations
from typing import Any

REQUIRED_FINDING_FIELDS = ("id", "severity", "location", "title", "detail", "evidence", "fix")
VALID_SEVERITIES = ("BLOCK", "REVISE", "NIT")
VALID_CLAIM_TYPES = (
    "existence",
    "static-shape",
    "behavior",
    "non-code",
    # scope-completeness: the claim is "I checked everywhere X could be" and
    # verification is "grep the whole monorepo / relevant root, not just the
    # file the author named". This is the failure mode where a self-review
    # claims "X is untouched" or "no regressions" without scanning the full
    # blast radius. See `agents/red-team-claim-refuter.md` for the branch.
    "scope-completeness",
)


def validate(findings_obj: Any) -> list[str]:
    """Return validation error strings; empty list = valid.

    Accepts a parsed findings object (dict). Does NOT parse JSON — the caller
    wraps Read in try/except per the critic's FM-2 contract.
    """
    if not isinstance(findings_obj, dict):
        return ["findings object is not a dict"]
    findings = findings_obj.get("findings")
    if findings is None:
        return ["missing 'findings' list"]
    if not isinstance(findings, list):
        return ["'findings' is not a list"]
    errors: list[str] = []
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            errors.append(f"finding[{i}] is not a dict")
            continue
        for field in REQUIRED_FINDING_FIELDS:
            if field not in f:
                errors.append(f"finding[{i}] missing required field '{field}'")
        sev = f.get("severity")
        if sev is not None and sev not in VALID_SEVERITIES:
            errors.append(f"finding[{i}] severity '{sev}' not in {VALID_SEVERITIES}")
        ct = f.get("claim_type")
        if ct is not None and ct not in VALID_CLAIM_TYPES:
            errors.append(f"finding[{i}] claim_type '{ct}' not in {VALID_CLAIM_TYPES}")
    return errors
