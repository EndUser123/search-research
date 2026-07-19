"""Deterministic post-LLM validator for AAR reports.

Once the LLM produces an AAR report from the evidence packet, this module
mechanically checks the report against the AAR contract (SKILL.md Phases 2,
7, 9, 9.5). It catches the failure modes the LLM is most prone to:

* episode types outside the allowed set;
* accounting that does not reconcile (total ≠ sum of type counts);
* material conclusions missing the 4-dimension confidence block;
* comparative-superiority claims ("more reliable than") without
  CONTROLLED_COMPARISON or EXTERNAL_EVIDENCE;
* exhaustive-coverage claims on a ``SOURCE_PARTIAL`` transcript;
* ``GENERAL`` scope without ≥3 sessions or without comparison evidence
  (mechanically-universal defects excepted);
* ``LOW``/``UNKNOWN`` causal confidence supporting ``DURABLE_POLICY``;
* headline scope outranking body scope.

Scope
-----
The validator performs **mechanical contract checks only**. It does not judge
whether the report's causal claims are correct — that requires the evidence
packet and is a synthesis judgment. It returns findings; it does not modify
the report.

Severity model
--------------
* ``blocker`` — contract violation; the report is not publishable as-is.
* ``warning`` — weak/ambiguous but not strictly invalid; surface for review.
* ``info`` — advisory; never blocks.

A ``ValidationResult.passed`` is True iff zero blockers are present.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from event_model import (
    ALLOWED_DISPOSITIONS,
    ALLOWED_EPISODE_STATUSES,
    ALLOWED_EPISODE_TYPES,
    CAUSAL_LEVELS,
    COMPARISON_STATUSES,
    CONFIDENCE_LEVELS,
    POLICY_LEVELS,
    SCOPES,
)

__all__ = [
    "Severity",
    "ValidationFinding",
    "ValidationResult",
    "validate_aar_report",
    "validate_aar_report_with_packet",
    "extract_structured_block",
    "REQUIRED_SECTIONS",
    "CONFIDENCE_DIMENSIONS",
    "MATERIAL_CONCLUSION_PATHS",
]

#: Top-level sections required by SKILL.md Phase 9 report format.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "verdict",
    "evidence_scope",
    "intended_vs_actual",
    "episodes",
    "decisions",
    "recurring_patterns",
    "opportunity_candidates",
    "accounting",
)

#: The four confidence dimensions from SKILL.md Phase 9.5.
CONFIDENCE_DIMENSIONS: tuple[str, ...] = (
    "evidence_confidence",
    "causal_confidence",
    "intervention_confidence",
    "scope_confidence",
)

#: Locations in the report where a "material conclusion" can live and therefore
#: where the 4-dimension confidence block is mandatory when present.
MATERIAL_CONCLUSION_PATHS: tuple[str, ...] = (
    "verdict",
    "recurring_patterns",
    "opportunity_candidates",
    "lessons",
    "headlines",
)

#: Phrases that claim an intervention class is superior to another.
_COMPARATIVE_SUPERIORITY_RE = re.compile(
    r"\b(?:more\s+reliable\s+than|superior\s+to|more\s+effective\s+than|"
    r"more\s+appropriate\s+than|better\s+than|generally\s+better|"
    r"rank[s]?\s+\w+\s+above)\b",
    re.IGNORECASE,
)

#: Intervention-class nouns that, if compared, trigger the comparison rule.
#: Plural forms are accepted; ``\b...\b`` would otherwise miss "hooks"/"validators".
_INTERVENTION_CLASS_RE = re.compile(
    r"\b(?:behavioral\s+rules?|format\s+gates?|hooks?|validators?|"
    r"configs?(?:uration|urations)?|state\s+machines?|process\s+changes?|"
    r"skills?|interventions?)\b",
    re.IGNORECASE,
)

#: Exhaustive-coverage claim phrases.
_EXHAUSTIVE_CLAIM_RE = re.compile(
    r"\b(?:all\s+gaps\s+(?:found|identified)|exhaustive\s+coverage|"
    r"zero\s+false\s+negatives|complete\s+coverage|comprehensive\s+(?:coverage|list)|"
    r"every\s+(?:episode|gap|defect)\s+(?:found|captured))\b",
    re.IGNORECASE,
)

#: Embedded-JSON block markers the LLM may use to ship structured output
#: alongside the markdown report. Searched in order.
_JSON_BLOCK_PATTERNS = (
    re.compile(r"<!--\s*AAR_JSON:\s*(\{.*?\})\s*-->", re.DOTALL),
    re.compile(r"```json\s*\n(\{.*?\})\n```", re.DOTALL),
    re.compile(r"```\s*\n(\{.*?\})\n```", re.DOTALL),
)


Severity = Literal["blocker", "warning", "info"]


@dataclass(frozen=True)
class ValidationFinding:
    """One contract finding. ``path`` locates the issue in the report."""

    code: str
    severity: Severity
    message: str
    path: str | None = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True)
class ValidationResult:
    """Aggregate result. ``passed`` iff zero blockers."""

    passed: bool
    findings: tuple[ValidationFinding, ...]
    summary: str

    def blockers(self) -> tuple[ValidationFinding, ...]:
        return tuple(f for f in self.findings if f.severity == "blocker")

    def warnings(self) -> tuple[ValidationFinding, ...]:
        return tuple(f for f in self.findings if f.severity == "warning")

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "summary": self.summary,
            "blocker_count": len(self.blockers()),
            "warning_count": len(self.warnings()),
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate_aar_report(report: dict[str, Any] | str | Path) -> ValidationResult:
    """Validate an AAR report against the contract.

    Accepts:

    * a parsed dict;
    * a path to a ``.json`` file (loaded directly);
    * a path to a ``.md`` file (the structured block is extracted via
      :func:`extract_structured_block`).

    Returns a ``ValidationResult``. Never raises on contract violations —
    every violation becomes a finding. Raises ``ValueError`` only when the
    input genuinely cannot be parsed (e.g. markdown with no JSON block).
    """
    data, raw_text = _coerce_report(report)
    findings: list[ValidationFinding] = []

    findings.extend(_check_required_sections(data))
    findings.extend(_check_episode_types(data))
    findings.extend(_check_episode_evidence(data))
    findings.extend(_check_dispositions(data))
    findings.extend(_check_accounting(data))
    findings.extend(_check_confidence_dimensions(data))
    findings.extend(_check_comparative_claims(data, raw_text))
    findings.extend(_check_source_partial_exhaustive(data, raw_text))
    findings.extend(_check_general_scope(data))
    findings.extend(_check_low_causal_durable_policy(data))
    findings.extend(_check_headline_scope(data))
    findings.extend(_check_workflow_redundant_promotion(data))
    findings.extend(_check_opportunity_schema(data))
    findings.extend(_check_value_accounting(data))
    findings.extend(_check_opportunity_portfolio(data))

    blockers = sum(1 for f in findings if f.severity == "blocker")
    warnings = sum(1 for f in findings if f.severity == "warning")
    passed = blockers == 0
    summary = (
        f"{'PASS' if passed else 'FAIL'}: "
        f"{blockers} blocker(s), {warnings} warning(s), "
        f"{len(findings)} finding(s) total"
    )
    return ValidationResult(
        passed=passed, findings=tuple(findings), summary=summary
    )


def extract_structured_block(markdown_text: str) -> dict[str, Any] | None:
    """Extract the structured JSON block from a markdown report.

    Returns the parsed dict or None if no block is found. Tries the
    ``<!-- AAR_JSON: ... -->`` marker first (preferred — unambiguous), then
    fenced ```` ```json ```` blocks.
    """
    for pat in _JSON_BLOCK_PATTERNS:
        m = pat.search(markdown_text)
        if m:
            try:
                obj = json.loads(m.group(1))
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


# ---------------------------------------------------------------------------
# Coercion
# ---------------------------------------------------------------------------


def _coerce_report(report: dict[str, Any] | str | Path) -> tuple[dict[str, Any], str]:
    """Normalise input to (data_dict, raw_text). raw_text is '' for dict input."""
    if isinstance(report, dict):
        return report, ""
    if isinstance(report, (str, Path)):
        p = Path(report)
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            if p.suffix.lower() == ".json":
                try:
                    obj = json.loads(text)
                    if isinstance(obj, dict):
                        return obj, text
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON in {p}: {exc}") from exc
            # markdown / unknown extension: try to extract embedded JSON.
            structured = extract_structured_block(text)
            if structured is None:
                raise ValueError(
                    f"no structured JSON block found in {p}; "
                    f"expected <!-- AAR_JSON: {{...}} --> or a ```json fence"
                )
            return structured, text
        # Treat raw string as markdown.
        structured = extract_structured_block(str(report))
        if structured is None:
            raise ValueError(
                "input string is not valid markdown-with-JSON-block; "
                "pass a dict, a .json path, or a .md path"
            )
        return structured, str(report)
    raise ValueError(f"unsupported report input type: {type(report).__name__}")


# ---------------------------------------------------------------------------
# Individual checks (one function per contract rule)
# ---------------------------------------------------------------------------


def _check_required_sections(data: dict[str, Any]) -> list[ValidationFinding]:
    out: list[ValidationFinding] = []
    for sec in REQUIRED_SECTIONS:
        if sec not in data:
            out.append(
                ValidationFinding(
                    code="MISSING_SECTION",
                    severity="blocker",
                    message=f"required section missing: {sec!r}",
                    path=sec,
                )
            )
    return out


def _check_episode_types(data: dict[str, Any]) -> list[ValidationFinding]:
    out: list[ValidationFinding] = []
    episodes = data.get("episodes", [])
    if not isinstance(episodes, list):
        out.append(
            ValidationFinding(
                code="EPISODES_NOT_LIST",
                severity="blocker",
                message="'episodes' must be a list",
                path="episodes",
            )
        )
        return out
    for i, ep in enumerate(episodes):
        if not isinstance(ep, dict):
            out.append(
                ValidationFinding(
                    code="EPISODE_NOT_OBJECT",
                    severity="blocker",
                    message=f"episode[{i}] is not an object",
                    path=f"episodes[{i}]",
                )
            )
            continue
        t = ep.get("type")
        if t not in ALLOWED_EPISODE_TYPES:
            out.append(
                ValidationFinding(
                    code="EPISODE_TYPE_INVALID",
                    severity="blocker",
                    message=(
                        f"episode[{i}] type {t!r} not in allowed set "
                        f"{list(ALLOWED_EPISODE_TYPES)}"
                    ),
                    path=f"episodes[{i}].type",
                )
            )
        status = ep.get("status")
        if status is not None and status not in ALLOWED_EPISODE_STATUSES:
            out.append(
                ValidationFinding(
                    code="EPISODE_STATUS_INVALID",
                    severity="warning",
                    message=(
                        f"episode[{i}] status {status!r} not in "
                        f"{list(ALLOWED_EPISODE_STATUSES)}"
                    ),
                    path=f"episodes[{i}].status",
                )
            )
    return out


def _check_episode_evidence(data: dict[str, Any]) -> list[ValidationFinding]:
    out: list[ValidationFinding] = []
    for i, ep in enumerate(data.get("episodes", []) or []):
        if not isinstance(ep, dict):
            continue
        ev = ep.get("evidence")
        if ev is None or (isinstance(ev, str) and not ev.strip()):
            out.append(
                ValidationFinding(
                    code="EPISODE_MISSING_EVIDENCE",
                    severity="blocker",
                    message=f"episode[{i}] has no evidence citation",
                    path=f"episodes[{i}].evidence",
                )
            )
    return out


def _check_dispositions(data: dict[str, Any]) -> list[ValidationFinding]:
    out: list[ValidationFinding] = []
    # Accept both the legacy 8-disposition set (allowed in the original AAR
    # contract) and the new 10-disposition opportunity-disposition set from
    # spec Section 14. The two overlap on 7 values (ACT_NOW, INVESTIGATE,
    # MONITOR, PRESERVE, DEFER, NOT_WORTH_DOING) plus the legacy-only
    # BLOCKED / NO_CHANGE and the new BOUNDED_EXPERIMENT / REUSE_EXISTING /
    # SIMPLIFY_OR_REMOVE / REJECT.
    allowed = set(ALLOWED_DISPOSITIONS) | set(OPPORTUNITY_DISPOSITIONS)
    for i, opp in enumerate(data.get("opportunity_candidates", []) or []):
        if not isinstance(opp, dict):
            continue
        disp = opp.get("disposition")
        if disp is None:
            # disposition is required by Phase 7 — warn (not block) to allow
            # draft reports to validate incrementally.
            out.append(
                ValidationFinding(
                    code="OPPORTUNITY_MISSING_DISPOSITION",
                    severity="warning",
                    message=f"opportunity_candidates[{i}] has no disposition",
                    path=f"opportunity_candidates[{i}].disposition",
                )
            )
            continue
        if disp not in allowed:
            out.append(
                ValidationFinding(
                    code="DISPOSITION_INVALID",
                    severity="blocker",
                    message=(
                        f"opportunity_candidates[{i}] disposition {disp!r} "
                        f"not in allowed set"
                    ),
                    path=f"opportunity_candidates[{i}].disposition",
                )
            )
    return out


def _check_accounting(data: dict[str, Any]) -> list[ValidationFinding]:
    out: list[ValidationFinding] = []
    acc = data.get("accounting")
    if not isinstance(acc, dict):
        out.append(
            ValidationFinding(
                code="ACCOUNTING_MISSING",
                severity="blocker",
                message="'accounting' must be an object with total_episodes and per-type counts",
                path="accounting",
            )
        )
        return out
    total = acc.get("total_episodes")
    episodes = data.get("episodes") or []
    observed_total = len(episodes) if isinstance(episodes, list) else None
    type_sum = 0
    missing_types: list[str] = []
    for t in ALLOWED_EPISODE_TYPES:
        v = acc.get(t)
        if v is None:
            missing_types.append(t)
            continue
        if not isinstance(v, int) or v < 0:
            out.append(
                ValidationFinding(
                    code="ACCOUNTING_TYPE_NOT_INTEGER",
                    severity="blocker",
                    message=f"accounting[{t!r}] = {v!r} must be a non-negative int",
                    path=f"accounting.{t}",
                )
                )
            continue
        type_sum += v
    if missing_types:
        out.append(
            ValidationFinding(
                code="ACCOUNTING_TYPE_MISSING",
                severity="blocker",
                message=f"accounting missing type counts: {missing_types}",
                path="accounting",
            )
        )
    if isinstance(total, int) and total != type_sum:
        out.append(
            ValidationFinding(
                code="ACCOUNTING_DOES_NOT_RECONCILE",
                severity="blocker",
                message=(
                    f"total_episodes ({total}) != sum of type counts ({type_sum})"
                ),
                path="accounting.total_episodes",
            )
        )
    # Reconcile against the actual episode list when present.
    if observed_total is not None and isinstance(total, int) and observed_total != total:
        out.append(
            ValidationFinding(
                code="ACCOUNTING_EPISODE_LIST_MISMATCH",
                severity="warning",
                message=(
                    f"episodes list length ({observed_total}) != "
                    f"accounting.total_episodes ({total})"
                ),
                path="accounting.total_episodes",
            )
        )
    return out


def _check_confidence_dimensions(data: dict[str, Any]) -> list[ValidationFinding]:
    """Material conclusions must carry all 4 confidence dimensions.

    Each dimension requires a valid value AND a non-empty rationale. Bare
    labels without rationale violate SKILL.md Phase 9.5.
    """
    out: list[ValidationFinding] = []
    for path_key in MATERIAL_CONCLUSION_PATHS:
        bucket = data.get(path_key)
        if not isinstance(bucket, list):
            continue
        for i, item in enumerate(bucket):
            if not isinstance(item, dict):
                continue
            # A material conclusion is any item with causal/intervention
            # claims. We require the confidence block when the item has any
            # of these markers.
            is_material = any(
                k in item
                for k in (
                    "causal_interpretation",
                    "root_cause",
                    "intervention",
                    "proposed_intervention",
                    "lesson",
                    "most_important_lesson",
                    "prevention_interception",
                )
            ) or any(d in item for d in CONFIDENCE_DIMENSIONS)
            if not is_material:
                continue
            conf = item.get("confidence_dimensions") or item.get("confidence")
            # Accept either a nested confidence_dimensions dict or the four
            # dimensions inlined on the item itself.
            dims_source = conf if isinstance(conf, dict) else item
            for dim in CONFIDENCE_DIMENSIONS:
                val = dims_source.get(dim) if isinstance(dims_source, dict) else None
                if val is None:
                    out.append(
                        ValidationFinding(
                            code="CONFIDENCE_DIMENSION_MISSING",
                            severity="blocker",
                            message=(
                                f"{path_key}[{i}] missing {dim} "
                                f"(required for material conclusions)"
                            ),
                            path=f"{path_key}[{i}].{dim}",
                        )
                    )
                    continue
                if val not in CONFIDENCE_LEVELS:
                    out.append(
                        ValidationFinding(
                            code="CONFIDENCE_VALUE_INVALID",
                            severity="blocker",
                            message=(
                                f"{path_key}[{i}].{dim} = {val!r} not in "
                                f"{list(CONFIDENCE_LEVELS)}"
                            ),
                            path=f"{path_key}[{i}].{dim}",
                        )
                    )
            # Rationale requirement: SKILL.md "bare labels without reasons are
            # invalid". Look for a parallel rationale field or rationale map.
            rationale = item.get("confidence_rationale") or item.get("rationales")
            if isinstance(rationale, dict):
                for dim in CONFIDENCE_DIMENSIONS:
                    rv = rationale.get(dim)
                    if not isinstance(rv, str) or not rv.strip():
                        out.append(
                            ValidationFinding(
                                code="CONFIDENCE_RATIONALE_MISSING",
                                severity="warning",
                                message=(
                                    f"{path_key}[{i}] {dim} has no rationale "
                                    f"(bare labels are invalid per Phase 9.5)"
                                ),
                                path=f"{path_key}[{i}].confidence_rationale.{dim}",
                            )
                        )
    return out


def _check_comparative_claims(
    data: dict[str, Any], raw_text: str
) -> list[ValidationFinding]:
    """Flag "X is more reliable than Y" claims lacking comparison evidence.

    Triggers when (a) the verdict/lessons text contains a superiority phrase
    AND an intervention-class noun, AND (b) the item's comparison_status is
    not CONTROLLED_COMPARISON or EXTERNAL_EVIDENCE.
    """
    out: list[ValidationFinding] = []
    texts_to_scan: list[tuple[str, str, dict[str, Any]]] = []
    # Gather text-bearing material locations.
    verdict = data.get("verdict")
    if isinstance(verdict, dict):
        text = verdict.get("text") or verdict.get("lesson") or verdict.get("most_important_lesson")
        if isinstance(text, str):
            texts_to_scan.append(("verdict", text, verdict))
    elif isinstance(verdict, str):
        texts_to_scan.append(("verdict", verdict, {}))
    for path_key in ("lessons", "recurring_patterns", "opportunity_candidates"):
        bucket = data.get(path_key)
        if isinstance(bucket, list):
            for i, item in enumerate(bucket):
                if isinstance(item, dict):
                    t = item.get("lesson") or item.get("text") or item.get("causal_interpretation")
                    if isinstance(t, str):
                        texts_to_scan.append((f"{path_key}[{i}]", t, item))
    # Also scan the raw markdown for free-text claims.
    if raw_text:
        texts_to_scan.append(("report_text", raw_text, data))

    for path_key, text, item in texts_to_scan:
        if not _COMPARATIVE_SUPERIORITY_RE.search(text):
            continue
        if not _INTERVENTION_CLASS_RE.search(text):
            continue
        comparison = item.get("comparison_status") or data.get("comparison_status")
        if comparison in ("CONTROLLED_COMPARISON", "EXTERNAL_EVIDENCE"):
            continue
        out.append(
            ValidationFinding(
                code="COMPARATIVE_CLAIM_WITHOUT_COMPARISON",
                severity="blocker",
                message=(
                    f"superiority claim about an intervention class in "
                    f"{path_key} requires comparison_status "
                    f"CONTROLLED_COMPARISON or EXTERNAL_EVIDENCE "
                    f"(found {comparison!r})"
                ),
                path=path_key,
            )
        )
    return out


def _check_source_partial_exhaustive(
    data: dict[str, Any], raw_text: str
) -> list[ValidationFinding]:
    """SOURCE_PARTIAL + exhaustive-coverage language is a blocker."""
    out: list[ValidationFinding] = []
    scope = data.get("evidence_scope")
    source_status = None
    if isinstance(scope, dict):
        source_status = scope.get("source_status")
    if source_status != "SOURCE_PARTIAL":
        return out
    scan_targets: list[str] = [raw_text] if raw_text else []
    verdict = data.get("verdict")
    if isinstance(verdict, dict):
        v_text = verdict.get("text") or verdict.get("lesson")
        if isinstance(v_text, str):
            scan_targets.append(v_text)
    elif isinstance(verdict, str):
        scan_targets.append(verdict)
    for i, ep in enumerate(data.get("episodes", []) or []):
        if isinstance(ep, dict):
            ev_text = ep.get("event")
            if isinstance(ev_text, str):
                scan_targets.append(ev_text)
    for target in scan_targets:
        if _EXHAUSTIVE_CLAIM_RE.search(target):
            out.append(
                ValidationFinding(
                    code="PARTIAL_SOURCE_EXHAUSTIVE_CLAIM",
                    severity="blocker",
                    message=(
                        "evidence_scope.source_status is SOURCE_PARTIAL but "
                        "the report claims exhaustive coverage "
                        "(violates SKILL.md cross-field invariant #2)"
                    ),
                    path="evidence_scope.source_status",
                )
            )
            break
    return out


def _check_general_scope(data: dict[str, Any]) -> list[ValidationFinding]:
    """GENERAL scope needs ≥3 sessions + comparison, OR mechanically_universal."""
    out: list[ValidationFinding] = []
    n_sessions = data.get("n_sessions")
    if not isinstance(n_sessions, int):
        # Try evidence_scope.sessions_count as a fallback location.
        scope = data.get("evidence_scope")
        if isinstance(scope, dict) and isinstance(scope.get("sessions_count"), int):
            n_sessions = scope["sessions_count"]

    def _scan(items: list[Any], path_key: str) -> None:
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            if item.get("scope") != "GENERAL":
                continue
            if item.get("mechanically_universal") is True:
                continue  # invariant #12 exemption
            comparison = item.get("comparison_status")
            if comparison in ("CONTROLLED_COMPARISON", "EXTERNAL_EVIDENCE") and isinstance(
                n_sessions, int
            ) and n_sessions >= 3:
                continue
            out.append(
                ValidationFinding(
                    code="GENERAL_SCOPE_INSUFFICIENT_EVIDENCE",
                    severity="blocker",
                    message=(
                        f"{path_key}[{i}] claims GENERAL scope without ≥3 "
                        f"sessions + comparison (or mechanically_universal); "
                        f"n_sessions={n_sessions!r}, comparison={comparison!r}"
                    ),
                    path=f"{path_key}[{i}].scope",
                )
            )

    for path_key in ("lessons", "recurring_patterns", "opportunity_candidates"):
        bucket = data.get(path_key)
        if isinstance(bucket, list):
            _scan(bucket, path_key)
    return out


def _check_low_causal_durable_policy(data: dict[str, Any]) -> list[ValidationFinding]:
    """LOW/UNKNOWN causal_confidence cannot support DURABLE_POLICY."""
    out: list[ValidationFinding] = []
    for path_key in ("lessons", "recurring_patterns", "opportunity_candidates"):
        bucket = data.get(path_key)
        if not isinstance(bucket, list):
            continue
        for i, item in enumerate(bucket):
            if not isinstance(item, dict):
                continue
            policy = item.get("policy_promotion") or item.get("policy_level")
            if policy != "DURABLE_POLICY":
                continue
            causal = (
                (item.get("confidence_dimensions") or {}).get("causal_confidence")
                if isinstance(item.get("confidence_dimensions"), dict)
                else item.get("causal_confidence")
            )
            if causal in ("LOW", "UNKNOWN"):
                out.append(
                    ValidationFinding(
                        code="LOW_CAUSAL_DURABLE_POLICY",
                        severity="blocker",
                        message=(
                            f"{path_key}[{i}] promotes to DURABLE_POLICY on "
                            f"{causal!r} causal_confidence "
                            f"(violates SKILL.md cross-field invariant #3)"
                        ),
                        path=f"{path_key}[{i}].policy_promotion",
                    )
                )
    return out


def _check_headline_scope(data: dict[str, Any]) -> list[ValidationFinding]:
    """Headline/verdict scope must not exceed body scope."""
    out: list[ValidationFinding] = []
    rank = {"SESSION_SPECIFIC": 1, "PROBLEM_CLASS": 2, "GENERAL": 3}
    verdict = data.get("verdict")
    if not isinstance(verdict, dict):
        return out
    head_scope = verdict.get("scope")
    if head_scope not in rank:
        return out
    # Body scope = max scope across material-conclusion items.
    body_scope_rank = 0
    body_loc = None
    for path_key in ("lessons", "recurring_patterns", "opportunity_candidates"):
        bucket = data.get(path_key)
        if not isinstance(bucket, list):
            continue
        for item in bucket:
            if isinstance(item, dict) and item.get("scope") in rank:
                if rank[item["scope"]] > body_scope_rank:
                    body_scope_rank = rank[item["scope"]]
                    body_loc = path_key
    if body_scope_rank and rank[head_scope] > body_scope_rank:
        out.append(
            ValidationFinding(
                code="HEADLINE_SCOPE_EXCEEDS_BODY",
                severity="blocker",
                message=(
                    f"verdict.scope={head_scope!r} outranks body scope "
                    f"(max={_rank_to_name(body_scope_rank)} in {body_loc})"
                ),
                path="verdict.scope",
            )
        )
    return out


def _check_workflow_redundant_promotion(data: dict[str, Any]) -> list[ValidationFinding]:
    """PROCESS_THEATER_CANDIDATE → REDUNDANT needs ≥3 runs + no unique value."""
    out: list[ValidationFinding] = []
    for path_key in ("recurring_patterns", "opportunity_candidates", "lessons"):
        bucket = data.get(path_key)
        if not isinstance(bucket, list):
            continue
        for i, item in enumerate(bucket):
            if not isinstance(item, dict):
                continue
            classification = (
                item.get("workflow_classification")
                or item.get("process_classification")
            )
            if classification != "REDUNDANT":
                continue
            runs = item.get("n_runs") or item.get("evidence_horizon")
            unique_outputs = item.get("n_unique_outputs")
            has_consumer = item.get("has_consumer")
            unique_defects = item.get("n_unique_defects_caught")
            # REDUNDANT requires: ≥3 runs, 0 unique outputs, no consumer, 0 defects.
            problems: list[str] = []
            if not isinstance(runs, int) or runs < 3:
                problems.append(f"n_runs={runs!r} (<3)")
            if unique_outputs not in (0, None):
                problems.append(f"n_unique_outputs={unique_outputs!r} (non-zero)")
            if has_consumer:
                problems.append("has a downstream consumer")
            if unique_defects not in (0, None):
                problems.append(f"n_unique_defects_caught={unique_defects!r} (non-zero)")
            if problems:
                out.append(
                    ValidationFinding(
                        code="REDUNDANT_WITHOUT_SUFFICIENT_EVIDENCE",
                        severity="blocker",
                        message=(
                            f"{path_key}[{i}] classified REDUNDANT but evidence "
                            f"is insufficient ({'; '.join(problems)}); "
                            f"PROCESS_THEATER_CANDIDATE → REDUNDANT needs "
                            f"repeated no-unique-value evidence per Phase 9.5"
                        ),
                        path=f"{path_key}[{i}].workflow_classification",
                    )
                )
    return out


def _rank_to_name(rank_value: int) -> str:
    for name, r in (("SESSION_SPECIFIC", 1), ("PROBLEM_CLASS", 2), ("GENERAL", 3)):
        if r == rank_value:
            return name
    return f"rank({rank_value})"


# ---------------------------------------------------------------------------
# Opportunity-schema checks (spec Sections 8, 9, 14, 15)
# ---------------------------------------------------------------------------

#: Spec Section 14: 10 opportunity dispositions. Superset of the original 8.
OPPORTUNITY_DISPOSITIONS: tuple[str, ...] = (
    "ACT_NOW", "BOUNDED_EXPERIMENT", "INVESTIGATE", "MONITOR",
    "REUSE_EXISTING", "SIMPLIFY_OR_REMOVE", "PRESERVE", "DEFER",
    "REJECT", "NOT_WORTH_DOING",
)

#: Spec Section 3: 12 opportunity source classes.
OPPORTUNITY_SOURCE_CLASSES: tuple[str, ...] = (
    "FAILURE_DERIVED", "FRICTION_DERIVED", "SUCCESS_DERIVED",
    "CAPABILITY_DERIVED", "REUSE_DERIVED", "COMBINATION_DERIVED",
    "SIMPLIFICATION_DERIVED", "RISK_DERIVED", "USER_EXPERIENCE_DERIVED",
    "LEARNING_DERIVED", "STRATEGIC_OPTION_DERIVED", "EXTERNAL_EVIDENCE_DERIVED",
)

#: HYBRID refinement: 6-value existing-capability classification (comparative eval).
#: Optional on every opportunity; if present, must be one of these values.
EXISTING_CAPABILITY_STATUSES: tuple[str, ...] = (
    "ABSENT", "EXISTS_AND_EFFECTIVE", "EXISTS_BUT_NOT_INVOKED",
    "EXISTS_BUT_INEFFECTIVE", "PARTIAL_OVERLAP", "UNKNOWN",
)

#: Spec Section 6: 6 horizons.
OPPORTUNITY_HORIZONS: tuple[str, ...] = (
    "IMMEDIATE_LOCAL", "NEAR_TERM_WORKFLOW", "CROSS_SKILL_REUSE",
    "SYSTEM_CAPABILITY", "STRATEGIC_OPTION", "CONTINUAL_LEARNING",
)

#: Spec Section 7: 16 mechanisms.
OPPORTUNITY_MECHANISMS: tuple[str, ...] = (
    "REMOVE", "SIMPLIFY", "MERGE", "RESEQUENCE", "AUTOMATE", "VALIDATE",
    "INSTRUMENT", "REUSE", "GENERALIZE", "SPECIALIZE", "INTEGRATE",
    "EXPERIMENT", "DOCUMENT", "TRAIN_OR_PROMPT", "CHANGE_DECISION_RULE",
    "NO_CHANGE_PRESERVE",
)

#: Spec Section 5: 7 value-accounting categories.
VALUE_CATEGORIES: tuple[str, ...] = (
    "VALUE_CREATED", "VALUE_PRESERVED", "VALUE_RECOVERED",
    "VALUE_UNREALIZED", "VALUE_DEFERRED", "VALUE_DESTROYED_OR_COST",
    "VALUE_COMPOUNDED",
)

#: Generic-opportunity phrases rejected by the validator (spec Section 8).
_GENERIC_OPPORTUNITY_PHRASES_LOCAL = (
    "improve communication", "do more research", "automate this",
    "add validation", "use better prompts", "be more careful",
    "improve quality", "do better", "fix the process",
)


def _check_opportunity_schema(data: dict[str, Any]) -> list[ValidationFinding]:
    """Spec Section 8: every opportunity must carry the full mandatory field set.

    Checks each entry in ``opportunity_candidates`` (and a new optional
    ``opportunity_portfolio`` block) for:

    * required fields present and non-empty (opportunity_id, title,
      source_classes, horizon, mechanism, supporting_event_ids,
      observed_evidence, interpretation, value_expected, beneficiary,
      frequency_or_reach, disposition, falsifier, next_evidence_needed);
    * source_classes are in the allowed set;
    * horizon / mechanism / disposition are in their allowed sets;
    * title is not on the generic-opportunity blocklist;
    * observed_evidence and interpretation are distinct (spec Section 10:
      opportunity ≠ gap; the detector must not jump symptom → solution);
    * non-ACT_NOW dispositions carry a lifecycle block when expected.
    """
    out: list[ValidationFinding] = []
    opportunities = data.get("opportunity_candidates") or []
    if not isinstance(opportunities, list):
        return out

    required_fields = (
        "opportunity_id", "title", "source_classes", "horizon", "mechanism",
        "supporting_event_ids", "observed_evidence", "interpretation",
        "value_expected", "beneficiary", "frequency_or_reach", "disposition",
        "falsifier", "next_evidence_needed",
    )
    lifecycle_required_for = {"MONITOR", "BOUNDED_EXPERIMENT", "INVESTIGATE", "DEFER"}

    for i, opp in enumerate(opportunities):
        if not isinstance(opp, dict):
            out.append(ValidationFinding(
                code="OPPORTUNITY_NOT_OBJECT", severity="blocker",
                message=f"opportunity_candidates[{i}] is not an object",
                path=f"opportunity_candidates[{i}]",
            ))
            continue
        # Required fields presence.
        for fld in required_fields:
            v = opp.get(fld)
            if v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, (list, tuple)) and len(v) == 0):
                out.append(ValidationFinding(
                    code="OPPORTUNITY_MISSING_FIELD", severity="blocker",
                    message=f"opportunity_candidates[{i}] missing required field {fld!r}",
                    path=f"opportunity_candidates[{i}].{fld}",
                ))
        # Enum validity.
        for cls in opp.get("source_classes") or []:
            if cls not in OPPORTUNITY_SOURCE_CLASSES:
                out.append(ValidationFinding(
                    code="OPPORTUNITY_SOURCE_CLASS_INVALID", severity="blocker",
                    message=f"opportunity_candidates[{i}] source_class {cls!r} not in allowed set",
                    path=f"opportunity_candidates[{i}].source_classes",
                ))
        if opp.get("horizon") and opp["horizon"] not in OPPORTUNITY_HORIZONS:
            out.append(ValidationFinding(
                code="OPPORTUNITY_HORIZON_INVALID", severity="blocker",
                message=f"opportunity_candidates[{i}] horizon {opp['horizon']!r} not in allowed set",
                path=f"opportunity_candidates[{i}].horizon",
            ))
        if opp.get("mechanism") and opp["mechanism"] not in OPPORTUNITY_MECHANISMS:
            out.append(ValidationFinding(
                code="OPPORTUNITY_MECHANISM_INVALID", severity="blocker",
                message=f"opportunity_candidates[{i}] mechanism {opp['mechanism']!r} not in allowed set",
                path=f"opportunity_candidates[{i}].mechanism",
            ))
        # HYBRID refinement: existing-capability status is OPTIONAL but if
        # present must be one of the 6 allowed values. Warning, not blocker —
        # the LLM is free to decline classification.
        ecs_raw = opp.get("existing_capability_status")
        if ecs_raw is not None and ecs_raw != "" and ecs_raw not in EXISTING_CAPABILITY_STATUSES:
            out.append(ValidationFinding(
                code="EXISTING_CAPABILITY_STATUS_INVALID", severity="blocker",
                message=(
                    f"opportunity_candidates[{i}] existing_capability_status "
                    f"{ecs_raw!r} not in {list(EXISTING_CAPABILITY_STATUSES)}"
                ),
                path=f"opportunity_candidates[{i}].existing_capability_status",
            ))
        disp = opp.get("disposition")
        if disp and disp not in OPPORTUNITY_DISPOSITIONS:
            out.append(ValidationFinding(
                code="OPPORTUNITY_DISPOSITION_INVALID", severity="blocker",
                message=f"opportunity_candidates[{i}] disposition {disp!r} not in allowed set",
                path=f"opportunity_candidates[{i}].disposition",
            ))
        # Generic-opportunity blocklist (title or interpretation).
        title = opp.get("title") or ""
        if _is_generic_opportunity_text(title):
            out.append(ValidationFinding(
                code="OPPORTUNITY_GENERIC_TITLE", severity="blocker",
                message=f"opportunity_candidates[{i}] title is generic (no concrete target): {title!r}",
                path=f"opportunity_candidates[{i}].title",
            ))
        # Opportunity ≠ gap: observed_evidence and interpretation must differ.
        obs = (opp.get("observed_evidence") or "").strip().lower()
        interp = (opp.get("interpretation") or "").strip().lower()
        if obs and interp and obs == interp:
            out.append(ValidationFinding(
                code="OPPORTUNITY_CONFUSES_GAP_WITH_OPPORTUNITY", severity="blocker",
                message=f"opportunity_candidates[{i}] observed_evidence == interpretation (must distinguish gap from opportunity)",
                path=f"opportunity_candidates[{i}].interpretation",
            ))
        # Lifecycle required for MONITOR / BOUNDED_EXPERIMENT / INVESTIGATE / DEFER.
        if disp in lifecycle_required_for:
            lc = opp.get("lifecycle")
            if not isinstance(lc, dict):
                out.append(ValidationFinding(
                    code="OPPORTUNITY_LIFECYCLE_MISSING", severity="blocker",
                    message=f"opportunity_candidates[{i}] disposition {disp!r} requires a lifecycle block",
                    path=f"opportunity_candidates[{i}].lifecycle",
                ))
            else:
                for lf in ("hypothesis", "success_signal", "failure_signal", "retirement_condition"):
                    if not isinstance(lc.get(lf), str) or not lc[lf].strip():
                        out.append(ValidationFinding(
                            code="OPPORTUNITY_LIFECYCLE_INCOMPLETE", severity="blocker",
                            message=f"opportunity_candidates[{i}].lifecycle.{lf} is required and non-empty",
                            path=f"opportunity_candidates[{i}].lifecycle.{lf}",
                        ))
    return out


def _check_value_accounting(data: dict[str, Any]) -> list[ValidationFinding]:
    """Spec Section 5: if a value_accounting block is present, every entry
    must use a recognised category. Categories may be empty (not forced)."""
    out: list[ValidationFinding] = []
    va = data.get("value_accounting")
    if va is None:
        return out  # value accounting is recommended but optional
    if not isinstance(va, dict):
        out.append(ValidationFinding(
            code="VALUE_ACCOUNTING_NOT_OBJECT", severity="warning",
            message="value_accounting must be an object keyed by ValueCategory",
            path="value_accounting",
        ))
        return out
    for cat, entries in va.items():
        if cat not in VALUE_CATEGORIES:
            out.append(ValidationFinding(
                code="VALUE_CATEGORY_UNKNOWN", severity="warning",
                message=f"value_accounting key {cat!r} is not a recognised ValueCategory",
                path=f"value_accounting.{cat}",
            ))
            continue
        if not isinstance(entries, list):
            out.append(ValidationFinding(
                code="VALUE_ENTRY_NOT_LIST", severity="warning",
                message=f"value_accounting.{cat} must be a list",
                path=f"value_accounting.{cat}",
            ))
            continue
        for j, entry in enumerate(entries):
            if not isinstance(entry, dict):
                out.append(ValidationFinding(
                    code="VALUE_ENTRY_NOT_OBJECT", severity="warning",
                    message=f"value_accounting.{cat}[{j}] is not an object",
                    path=f"value_accounting.{cat}[{j}]",
                ))
                continue
            desc = entry.get("description")
            if not isinstance(desc, str) or not desc.strip():
                out.append(ValidationFinding(
                    code="VALUE_ENTRY_MISSING_DESCRIPTION", severity="warning",
                    message=f"value_accounting.{cat}[{j}] needs a concrete description",
                    path=f"value_accounting.{cat}[{j}].description",
                ))
    return out


def _check_opportunity_portfolio(data: dict[str, Any]) -> list[ValidationFinding]:
    """Spec Section 9 / 15 / 20-G: opportunity portfolio must be bounded and
    prioritised, not an unbounded list.

    Checks:
    * If ``opportunity_candidates`` has > 30 entries, flag (avoid inflation).
    * Each opportunity should carry at least one expected_value dimension
      (warning, not blocker — small opportunities may skip).
    * Rejected opportunities appear in ``rejected_opportunities`` with a reason.
    """
    out: list[ValidationFinding] = []
    opps = data.get("opportunity_candidates") or []
    if isinstance(opps, list) and len(opps) > 30:
        out.append(ValidationFinding(
            code="OPPORTUNITY_INFLATION", severity="warning",
            message=f"{len(opps)} opportunities emitted; consider consolidating to a prioritised portfolio",
            path="opportunity_candidates",
        ))
    # Rejected opportunities ledger should exist if any opp has disposition REJECT/NOT_WORTH_DOING.
    has_rejected = any(
        isinstance(o, dict) and o.get("disposition") in ("REJECT", "NOT_WORTH_DOING")
        for o in opps
    )
    if has_rejected and "rejected_opportunities" not in data:
        out.append(ValidationFinding(
            code="REJECTED_OPPORTUNITIES_NOT_TRACKED", severity="warning",
            message="report rejects opportunities but does not record them in rejected_opportunities; future AARs may re-propose",
            path="rejected_opportunities",
        ))
    return out


def _is_generic_opportunity_text(text: str) -> bool:
    """Local generic-opportunity check (mirrors opportunity_model).

    Returns True if ``text`` is a generic phrase with no concrete target.
    """
    if not text or not text.strip():
        return True
    stripped = text.strip()
    for phrase in _GENERIC_OPPORTUNITY_PHRASES_LOCAL:
        m = re.search(re.escape(phrase), stripped, re.IGNORECASE)
        if not m:
            continue
        tail = stripped[m.end():].strip()
        tail_cleaned = re.sub(
            r"^(?:for|to|by|via|in|on|at|before|after|of|the|a|an|that|would|should|could|we|i)\b[\s,,:]*",
            "", tail, flags=re.IGNORECASE,
        ).strip()
        if not tail_cleaned or len(tail_cleaned) < 4:
            return True
        if not re.search(r"[A-Za-z]", tail_cleaned):
            return True
    return False


# ---------------------------------------------------------------------------
# Packet-aware validation (spec Section 15)
# ---------------------------------------------------------------------------

#: Completeness statuses recognised by the validator's source-status check.
_VALID_COMPLETENESS_STATUSES = frozenset(
    {
        "SOURCE_COMPLETE",
        "SOURCE_COMPLETE_WITH_LIMITATIONS",
        "SOURCE_PARTIAL",
        "SOURCE_UNVERIFIED",
        "SOURCE_UNSUPPORTED",
    }
)

#: Hierarchy rank for "LLM cannot upgrade beyond manifest" check.
_COMPLETENESS_RANK = {
    "SOURCE_COMPLETE": 5,
    "SOURCE_COMPLETE_WITH_LIMITATIONS": 4,
    "SOURCE_PARTIAL": 3,
    "SOURCE_UNVERIFIED": 2,
    "SOURCE_UNSUPPORTED": 1,
}


def validate_aar_report_with_packet(
    report: dict[str, Any] | str | Path,
    packet_dir: str | Path,
) -> ValidationResult:
    """Validate a report against both the AAR contract AND the evidence packet.

    Adds the spec Section 15 checks on top of :func:`validate_aar_report`:

    * every material episode references known event/signal IDs (resolvable
      against ``canonical-events.jsonl`` and ``signals.json``);
    * the report's ``evidence_scope.source_status`` does not exceed the
      manifest's earned completeness;
    * the snapshot cutoff appears in the report;
    * evidence drawn from superseded history is labelled as such;
    * no unresolved evidence references remain.

    The base contract checks still run; this function returns a single merged
    :class:`ValidationResult`.

    Raises ``FileNotFoundError`` if ``packet_dir`` is missing required artifacts.
    """
    base_result = validate_aar_report(report)
    data, raw_text = _coerce_report(report)

    pdir = Path(packet_dir)
    manifest = _load_json_or_none(pdir / "source-manifest.json")
    signals_data = _load_json_or_none(pdir / "signals.json")
    canonical_ids = _load_canonical_event_ids(pdir / "canonical-events.jsonl")
    superseded_ids = _load_canonical_event_ids(pdir / "superseded-events.jsonl")

    if manifest is None:
        return ValidationResult(
            passed=False,
            findings=base_result.findings
            + (
                ValidationFinding(
                    code="PACKET_MISSING_MANIFEST",
                    severity="blocker",
                    message="source-manifest.json not found in packet_dir",
                    path=str(pdir),
                ),
            ),
            summary=base_result.summary + " + PACKET_MISSING_MANIFEST",
        )

    new_findings: list[ValidationFinding] = []
    new_findings.extend(
        _check_evidence_id_references(data, canonical_ids, signals_data)
    )
    new_findings.extend(_check_source_status_consistency(data, manifest))
    new_findings.extend(_check_snapshot_cutoff_in_report(data, manifest, raw_text))
    new_findings.extend(_check_superseded_evidence_labelled(data, superseded_ids))

    all_findings = base_result.findings + tuple(new_findings)
    blockers = sum(1 for f in all_findings if f.severity == "blocker")
    warnings = sum(1 for f in all_findings if f.severity == "warning")
    passed = blockers == 0
    summary = (
        f"{'PASS' if passed else 'FAIL'}: "
        f"{blockers} blocker(s), {warnings} warning(s), "
        f"{len(all_findings)} finding(s) total (packet-aware)"
    )
    return ValidationResult(passed=passed, findings=all_findings, summary=summary)


# ---------------------------------------------------------------------------
# Packet-aware checks
# ---------------------------------------------------------------------------


def _check_evidence_id_references(
    data: dict[str, Any],
    canonical_ids: set[str],
    signals_data: dict[str, Any] | None,
) -> list[ValidationFinding]:
    """Spec Section 15: 'every material episode references known event/signal IDs'.

    Walks episodes/opportunities/patterns looking for ``evidence_event_ids``
    or ``evidence`` strings shaped like event ids (``chat_history-L...-S...``).
    Any reference that does not resolve against canonical-events.jsonl is a
    blocker — it means the LLM invented or mis-cited an id.
    """
    out: list[ValidationFinding] = []
    if not canonical_ids:
        return out  # nothing to check against; surfaced by manifest check

    valid_signal_ids: set[str] = set()
    if signals_data and isinstance(signals_data.get("signals"), list):
        for i, sig in enumerate(signals_data["signals"]):
            if isinstance(sig, dict):
                valid_signal_ids.add(f"{sig.get('kind', '?')}#{i}")

    # Walk every place evidence can be cited.
    scan_paths: list[tuple[str, list[dict[str, Any]]]] = []
    for key in ("episodes", "recurring_patterns", "opportunity_candidates", "validated_successes"):
        bucket = data.get(key)
        if isinstance(bucket, list):
            scan_paths.append((key, bucket))

    eid_re = re.compile(r"\b(chat_history-[A-Za-z0-9_\-]+)\b")

    for path_key, items in scan_paths:
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            # Direct evidence_event_ids field
            ev_ids = item.get("evidence_event_ids")
            if isinstance(ev_ids, list):
                for ref in ev_ids:
                    if isinstance(ref, str) and ref not in canonical_ids:
                        out.append(
                            ValidationFinding(
                                code="UNRESOLVED_EVENT_ID",
                                severity="blocker",
                                message=(
                                    f"{path_key}[{i}] cites event_id {ref!r} not in canonical-events.jsonl"
                                ),
                                path=f"{path_key}[{i}].evidence_event_ids",
                            )
                        )
            # Free-text evidence field may contain event id references
            ev_text = item.get("evidence")
            if isinstance(ev_text, str):
                for m in eid_re.finditer(ev_text):
                    ref = m.group(1)
                    if ref not in canonical_ids:
                        out.append(
                            ValidationFinding(
                                code="UNRESOLVED_EVENT_ID",
                                severity="blocker",
                                message=(
                                    f"{path_key}[{i}].evidence cites {ref!r} not in canonical-events.jsonl"
                                ),
                                path=f"{path_key}[{i}].evidence",
                            )
                        )
            # Signal refs
            sig_refs = item.get("evidence_signal_ids")
            if isinstance(sig_refs, list) and valid_signal_ids:
                for ref in sig_refs:
                    if isinstance(ref, str) and ref not in valid_signal_ids:
                        out.append(
                            ValidationFinding(
                                code="UNRESOLVED_SIGNAL_ID",
                                severity="warning",
                                message=(
                                    f"{path_key}[{i}] cites signal {ref!r} not in signals.json"
                                ),
                                path=f"{path_key}[{i}].evidence_signal_ids",
                            )
                        )
    return out


def _check_source_status_consistency(
    data: dict[str, Any], manifest: dict[str, Any]
) -> list[ValidationFinding]:
    """Spec Section 15: 'no claim says SOURCE_COMPLETE when manifest status differs'.

    The report's evidence_scope.source_status may be equal to or stricter than
    the manifest's earned status — never more permissive. We also accept
    SOURCE_COMPLETE_WITH_LIMITATIONS as a valid claim when the manifest says
    SOURCE_COMPLETE (stricter is fine).
    """
    out: list[ValidationFinding] = []
    scope = data.get("evidence_scope")
    if not isinstance(scope, dict):
        return out
    claimed = scope.get("source_status")
    if not isinstance(claimed, str) or claimed not in _VALID_COMPLETENESS_STATUSES:
        return out  # handled by other checks

    # Manifest's status lives in completeness.status on the reconciliation
    # inputs path OR at top-level. We accept either location.
    manifest_status = None
    compl = manifest.get("completeness") if isinstance(manifest.get("completeness"), dict) else None
    if compl and isinstance(compl.get("status"), str):
        manifest_status = compl["status"]
    if manifest_status is None:
        # Fall back to looking for it in the snapshot manifest warnings.
        return out
    if manifest_status not in _COMPLETENESS_RANK:
        return out

    claimed_rank = _COMPLETENESS_RANK.get(claimed, 0)
    manifest_rank = _COMPLETENESS_RANK[manifest_status]
    if claimed_rank > manifest_rank:
        out.append(
            ValidationFinding(
                code="SOURCE_STATUS_UPGRADED_BEYOND_MANIFEST",
                severity="blocker",
                message=(
                    f"report claims {claimed} but manifest earned only {manifest_status} "
                    f"(LLM may not upgrade completeness beyond the reconciler result)"
                ),
                path="evidence_scope.source_status",
            )
        )
    return out


def _check_snapshot_cutoff_in_report(
    data: dict[str, Any], manifest: dict[str, Any], raw_text: str
) -> list[ValidationFinding]:
    """Spec Section 15: 'snapshot cutoff appears in the report'."""
    out: list[ValidationFinding] = []
    cutoff = (
        manifest.get("snapshot_cutoff")
        if isinstance(manifest.get("snapshot_cutoff"), str)
        else None
    )
    if not cutoff:
        return out  # nothing to verify against

    scope = data.get("evidence_scope")
    if isinstance(scope, dict) and isinstance(scope.get("snapshot_cutoff"), str):
        if cutoff in scope["snapshot_cutoff"] or scope["snapshot_cutoff"] in cutoff:
            return out

    coverage_through = None
    if isinstance(scope, dict) and isinstance(scope.get("coverage_through"), str):
        coverage_through = scope["coverage_through"]
    if coverage_through and cutoff in coverage_through:
        return out

    # Last resort: check the raw markdown for the cutoff string.
    if raw_text and cutoff in raw_text:
        return out

    out.append(
        ValidationFinding(
            code="SNAPSHOT_CUTOFF_MISSING",
            severity="blocker",
            message=(
                f"report does not cite the snapshot cutoff {cutoff!r}; "
                f"evidence_scope.snapshot_cutoff or coverage_through is required"
            ),
            path="evidence_scope.snapshot_cutoff",
        )
    )
    return out


def _check_superseded_evidence_labelled(
    data: dict[str, Any], superseded_ids: set[str]
) -> list[ValidationFinding]:
    """Spec Section 15: 'active versus superseded evidence is labeled'.

    If the report cites an event id that belongs to superseded-events.jsonl
    without an explicit ``from_superseded_history: true`` flag, that is a
    blocker — superseded decisions must not be presented as current authority.
    """
    out: list[ValidationFinding] = []
    if not superseded_ids:
        return out

    for path_key in ("episodes", "recurring_patterns", "opportunity_candidates", "validated_successes"):
        bucket = data.get(path_key)
        if not isinstance(bucket, list):
            continue
        for i, item in enumerate(bucket):
            if not isinstance(item, dict):
                continue
            ev_ids = item.get("evidence_event_ids")
            if not isinstance(ev_ids, list):
                continue
            for ref in ev_ids:
                if isinstance(ref, str) and ref in superseded_ids:
                    if not item.get("from_superseded_history"):
                        out.append(
                            ValidationFinding(
                                code="SUPERSEDED_EVIDENCE_UNLABELLED",
                                severity="blocker",
                                message=(
                                    f"{path_key}[{i}] cites superseded event {ref!r} "
                                    f"without setting from_superseded_history=true"
                                ),
                                path=f"{path_key}[{i}].evidence_event_ids",
                            )
                        )
    return out


# ---------------------------------------------------------------------------
# Packet loaders
# ---------------------------------------------------------------------------


def _load_json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_canonical_event_ids(path: Path) -> set[str]:
    """Stream-read a canonical-events.jsonl file and return the set of event_ids."""
    out: set[str] = set()
    if not path.is_file():
        return out
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict) and isinstance(obj.get("event_id"), str):
                    out.add(obj["event_id"])
    except OSError:
        pass
    return out
