"""Contract-driven decision synthesis from validated inputs.

This module implements the /design workflow core: it consumes a validated
decision-request.v1 and one or more validated research-result.v1 artifacts,
and produces a decision-result.v1 proposed decision.

It deliberately does NOT:
- Run research or invoke providers
- Approve decisions
- Execute plans
- Route to /go
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .decision_request import validate as validate_decision_request
from .decision_result import validate as validate_decision_result
from .research_result import validate as validate_research_result


def synthesize(
    request: dict[str, Any],
    research_results: list[dict[str, Any]],
    *,
    request_sha256: str | None = None,
    decision_id: str = "",
    created_at: str = "",
) -> dict[str, Any]:
    """Synthesize a decision-result.v1 from a validated request and research results.

    Args:
        request: Validated decision-request.v1 dict.
        research_results: One or more validated research-result.v1 dicts.
        request_sha256: SHA-256 of the request JSON for provenance binding.
            Computed from canonical JSON if omitted.
        decision_id: Explicit decision ID (UUID). Auto-generated if empty.
        created_at: ISO-8601 timestamp. Current UTC if empty.

    Returns:
        Validated decision-result.v1 dict with approval_state=pending.

    Raises:
        ValueError: If an input is invalid, a research result has an unbound
            artifact hash, or required evidence is missing.
    """
    validate_decision_request(request)
    for rr in research_results:
        validate_research_result(rr)

    # Bind hashes for provenance
    _request_sha256 = (
        request_sha256
        or hashlib.sha256(
            json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
    )

    # Verify each research result has a usable artifact hash
    for rr in research_results:
        rr_hash = rr.get("provenance", {}).get("artifact_sha256", "")
        if not rr_hash or rr_hash == "not_bound":
            msg = (
                f"Research result {rr.get('run_id', 'unknown')} has "
                f"unbound artifact_sha256={rr_hash!r}; "
                "call build_research_result with an explicit artifact_sha256."
            )
            raise ValueError(msg)

    # Identity
    _decision_id = decision_id or str(uuid.uuid4())
    _created_at = created_at or datetime.now(timezone.utc).isoformat()

    # Extract inputs
    considered = list(request["options"]["considered"])
    authority_req = request["authority"]

    # --- Option evaluation ---
    evaluated = _evaluate_options(considered, research_results)
    selected, rejected_ids, rejection_reasons = _rank_and_select(evaluated)

    # --- Evidence state ---
    unresolved = _collect_unresolved(research_results)
    evidence_refs = _build_evidence_refs(research_results)
    supporting, conflicting = _classify_claims(selected, research_results)
    confidence = _assess_confidence(selected, unresolved, research_results)

    # --- Decision structure ---
    outcome_text, rationale_text = _build_decision_texts(
        selected, rejected_ids, rejection_reasons, unresolved,
    )

    decision_selected = (
        {"option_id": selected["option_id"], "label": selected["label"]}
        if selected
        else {"option_id": "", "label": ""}
    )

    tradeoffs = _build_tradeoffs(request)
    risks = _build_risks(research_results, unresolved)

    # Authority -- /design always produces a proposed decision
    approval_state = (
        "not_required" if not authority_req.get("approval_requirements")
        else "pending"
    )
    authority = {
        "decision_owner": authority_req["decision_owner"],
        "approvals": [],
        "approval_state": approval_state,
    }

    execution_boundary = _build_execution_boundary(unresolved)

    # Provenance
    source_artifacts, hashes = _build_provenance(
        request["request_id"], _request_sha256, evidence_refs,
    )

    result = {
        "schema_version": "decision-result.v1",
        "identity": {
            "decision_id": _decision_id,
            "request_id": request["request_id"],
            "request_sha256": _request_sha256,
            "created_at": _created_at,
        },
        "context": {
            "objective": request["decision_context"]["objective"],
            "scope": request["decision_context"]["scope"],
            "constraints": dict(request["constraints"]),
        },
        "decision": {
            "selected_option": decision_selected,
            "outcome": outcome_text,
            "rationale": rationale_text,
        },
        "alternatives": {
            "considered": [
                {"option_id": o["option_id"], "label": o["label"]}
                for o in considered
            ],
            "rejected": rejected_ids,
            "rejection_reasons": rejection_reasons,
        },
        "tradeoffs": tradeoffs,
        "evidence": {
            "research_result_refs": evidence_refs,
            "supporting_claims": supporting,
            "conflicting_claims": conflicting,
            "confidence": confidence,
            "unresolved_questions": unresolved,
        },
        "risks": risks,
        "authority": authority,
        "execution_boundary": execution_boundary,
        "provenance": {
            "source_artifacts": source_artifacts,
            "hashes": hashes,
        },
    }

    validate_decision_result(result)
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _evaluate_options(
    considered: list[dict[str, Any]],
    research_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score each considered option against available research findings."""
    evaluated: list[dict[str, Any]] = []
    for option in considered:
        supporting: list[str] = []
        conflicting: list[str] = []
        oid = option["option_id"].lower()
        olabel = option["label"].lower()
        for rr in research_results:
            for finding in rr.get("findings", []):
                text = finding.get("statement", "").lower()
                if oid not in text and olabel not in text:
                    continue
                if finding.get("status") == "verified":
                    supporting.append(finding["claim_id"])
                elif finding.get("status") in ("contradicted", "refuted"):
                    conflicting.append(finding["claim_id"])
        evaluated.append({
            "option_id": option["option_id"],
            "label": option["label"],
            "_supporting": supporting,
            "_conflicting": conflicting,
        })
    return evaluated


def _rank_and_select(
    evaluated: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[str], list[dict[str, str]]]:
    """Select the best-supported option and build rejection reasons."""
    if not evaluated:
        return None, [], []

    ranked = sorted(
        evaluated,
        key=lambda o: (
            -(len(o["_supporting"]) - len(o["_conflicting"])),
            -len(o["_supporting"]),
        ),
    )
    best = ranked[0]

    rejected_ids: list[str] = []
    rejection_reasons: list[dict[str, str]] = []

    for opt in ranked[1:]:
        rejected_ids.append(opt["option_id"])
        reasons: list[str] = []
        best_score = len(best["_supporting"]) - len(best["_conflicting"])
        opt_score = len(opt["_supporting"]) - len(opt["_conflicting"])
        if opt_score < best_score:
            reasons.append(f"Weaker evidence support than {best['option_id']}")
        if opt["_conflicting"]:
            reasons.append(
                f"{len(opt['_conflicting'])} conflicting claim(s) in research"
            )
        if not opt["_supporting"]:
            reasons.append("No supporting evidence found in research results")
        rejection_reasons.append({
            "option_id": opt["option_id"],
            "reason": "; ".join(reasons) or "Alternative not selected.",
        })

    return best, rejected_ids, rejection_reasons


def _collect_unresolved(
    research_results: list[dict[str, Any]],
) -> list[str]:
    """Collect all unresolved questions across research results, deduplicated."""
    seen: set[str] = set()
    items: list[str] = []
    for rr in research_results:
        for q in rr.get("unresolved_questions", []):
            key = q if isinstance(q, str) else str(q)
            if key not in seen:
                seen.add(key)
                items.append(key)
        for req in rr.get("evidence_requirements", {}).get("unresolved", []):
            key = req if isinstance(req, str) else str(req)
            if key not in seen:
                seen.add(key)
                items.append(key)
    return items


def _build_evidence_refs(
    research_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build evidence.research_result_refs from validated research results."""
    refs: list[dict[str, str]] = []
    seen_runs: set[str] = set()
    for rr in research_results:
        run_id = rr.get("run_id", "")
        art_hash = rr.get("provenance", {}).get("artifact_sha256", "")
        if run_id and run_id not in seen_runs:
            seen_runs.add(run_id)
            refs.append({"run_id": run_id, "artifact_sha256": art_hash})
    return refs


def _classify_claims(
    selected: dict[str, Any] | None,
    research_results: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Classify claims into supporting/conflicting for the selected option."""
    if not selected:
        return [], []
    supporting: list[str] = []
    conflicting: list[str] = []
    oid = selected["option_id"].lower()
    olabel = selected["label"].lower()
    set_supporting: set[str] = set()
    set_conflicting: set[str] = set()
    for rr in research_results:
        for finding in rr.get("findings", []):
            text = finding.get("statement", "").lower()
            if oid not in text and olabel not in text:
                continue
            cid = finding.get("claim_id", "")
            if not cid:
                continue
            if finding.get("status") == "verified":
                if cid not in set_supporting:
                    set_supporting.add(cid)
                    supporting.append(cid)
            elif finding.get("status") in ("contradicted", "refuted"):
                if cid not in set_conflicting:
                    set_conflicting.add(cid)
                    conflicting.append(cid)
    return supporting, conflicting


def _assess_confidence(
    selected: dict[str, Any] | None,
    unresolved: list[str],
    research_results: list[dict[str, Any]],
) -> str:
    """Determine the confidence level for the proposed decision."""
    if not selected:
        return "insufficient"
    total_findings = sum(
        len(rr.get("findings", [])) for rr in research_results
    )
    if total_findings == 0 and unresolved:
        return "insufficient"
    if unresolved and len(unresolved) > total_findings:
        return "low"
    return "medium"


def _build_decision_texts(
    selected: dict[str, Any] | None,
    rejected_ids: list[str],
    rejection_reasons: list[dict[str, str]],
    unresolved: list[str],
) -> tuple[str, str]:
    """Build human-readable outcome and rationale."""
    if selected:
        outcome = f"Proposed: {selected['label']}"
        rationale_parts: list[str] = [
            f"Selected {selected['option_id']} based on available research evidence."
        ]
        if rejected_ids:
            reason_summary = "; ".join(
                f"{r['option_id']}: {r['reason']}"
                for r in rejection_reasons
            )
            rationale_parts.append(f"Rejected alternatives: {reason_summary}")
        if unresolved:
            rationale_parts.append(
                f"Remaining unresolved questions ({len(unresolved)}) "
                "may affect confidence in this proposed decision."
            )
    else:
        outcome = "Insufficient evidence to propose a decision."
        rationale_parts = [
            "No considered option has adequate supporting evidence "
            "in the available research results."
        ]
        if unresolved:
            rationale_parts.append(
                f"Resolve the {len(unresolved)} outstanding evidence "
                "requirements before a decision can be proposed."
            )

    return outcome, "\n".join(rationale_parts)


def _build_tradeoffs(
    request: dict[str, Any],
) -> dict[str, list[str]]:
    """Build tradeoffs section from request constraints and priorities."""
    constraints = request.get("constraints", {})
    priorities = request.get("priorities", {})

    accepted: list[str] = []
    for key in ("technical", "compatibility", "cost"):
        items = constraints.get(key, [])
        accepted.extend(items)

    rejected: list[str] = []
    for key in ("operational", "timeline", "reversibility"):
        items = constraints.get(key, [])
        rejected.extend(items)

    consequences: list[str] = []
    if priorities:
        ordered = sorted(priorities.items(), key=lambda x: x[0])
        priority_text = ", ".join(
            f"{k}={v}" for k, v in ordered
        )
        consequences.append(
            f"Decision prioritises: {priority_text}"
        )

    return {
        "accepted": accepted,
        "rejected": rejected,
        "consequences": consequences,
    }


def _build_risks(
    research_results: list[dict[str, Any]],
    unresolved: list[str],
) -> dict[str, list[str]]:
    """Build risks section from research uncertainties."""
    known: list[str] = []
    for q in unresolved:
        known.append(f"Unresolved: {q}")
    return {
        "known": known,
        "mitigations": [
            "Keep the decision reversible where possible.",
            "Revisit when additional evidence is gathered.",
        ],
        "accepted_risks": [
            "Proposed decisions are subject to approval.",
        ],
    }


def _build_execution_boundary(
    unresolved: list[str],
) -> dict[str, bool | list[str]]:
    """Build execution_boundary based on evidence completeness."""
    has_gaps = bool(unresolved)
    return {
        "implementation_required": not has_gaps,
        "planning_required": not has_gaps,
        "blocked_items": (
            list(unresolved)
            if has_gaps
            else []
        ),
    }


def _build_provenance(
    request_id: str,
    request_sha256: str,
    evidence_refs: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, str | list[str]]]:
    """Build source_artifacts and hashes for provenance."""
    source_artifacts: list[dict[str, str]] = [
        {
            "kind": "decision_request",
            "artifact_id": request_id,
            "sha256": request_sha256,
        },
    ]
    research_hashes: list[str] = []
    for ref in evidence_refs:
        sha = ref.get("artifact_sha256", "")
        if sha:
            research_hashes.append(sha)
            source_artifacts.append({
                "kind": "research_result",
                "artifact_id": ref.get("run_id", ""),
                "sha256": sha,
            })

    hashes: dict[str, str | list[str]] = {
        "request": request_sha256,
        "research_results": research_hashes,
    }
    return source_artifacts, hashes
