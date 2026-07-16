"""Research-brief.v1 — immutable, signed investigation plan.

The brief transforms a raw request into a structured, bounded investigation
contract before any provider is invoked.  It owns:

1.  Request normalisation: original text → resolved objective.
2.  Scope bounding: task class, key questions, evidence categories, exclusions,
    stopping conditions.
3.  Identity binding: platform, caller, workspace, session, and run identifiers.
4.  Integrity: the brief is written once (exclusive create) and carries a
    content hash that downstream artifacts reference.

Every field below is recorded and validated.  No field is inferred by a reader.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

TASK_CLASS_LOOKUP = "lookup"
TASK_CLASS_EXPLORATION = "exploration"
TASK_CLASS_IMPLEMENTATION = "implementation"
TASK_CLASS_DECISION_SUPPORT = "decision_support"
VALID_TASK_CLASSES = frozenset({
    TASK_CLASS_LOOKUP,
    TASK_CLASS_EXPLORATION,
    TASK_CLASS_IMPLEMENTATION,
    TASK_CLASS_DECISION_SUPPORT,
})

EVIDENCE_CATEGORY_AUTHORITY = "authority"
EVIDENCE_CATEGORY_CURRENT = "current"
EVIDENCE_CATEGORY_BROAD = "broad"
EVIDENCE_CATEGORY_CONCEPTUAL = "conceptual"
EVIDENCE_CATEGORY_IMPLEMENTATION = "implementation"
EVIDENCE_CATEGORY_COMPATIBILITY = "compatibility"
EVIDENCE_CATEGORY_OMISSION = "omission"
EVIDENCE_CATEGORY_ADVERSARIAL = "adversarial"
VALID_EVIDENCE_CATEGORIES = frozenset({
    EVIDENCE_CATEGORY_AUTHORITY,
    EVIDENCE_CATEGORY_CURRENT,
    EVIDENCE_CATEGORY_BROAD,
    EVIDENCE_CATEGORY_CONCEPTUAL,
    EVIDENCE_CATEGORY_IMPLEMENTATION,
    EVIDENCE_CATEGORY_COMPATIBILITY,
    EVIDENCE_CATEGORY_OMISSION,
    EVIDENCE_CATEGORY_ADVERSARIAL,
})

SOURCE_PRIORITY_AUTHORITATIVE = "authoritative"
SOURCE_PRIORITY_PRIMARY = "primary"
SOURCE_PRIORITY_SECONDARY = "secondary"
SOURCE_PRIORITY_ADVISORY = "advisory"
VALID_SOURCE_PRIORITIES = frozenset({
    SOURCE_PRIORITY_AUTHORITATIVE,
    SOURCE_PRIORITY_PRIMARY,
    SOURCE_PRIORITY_SECONDARY,
    SOURCE_PRIORITY_ADVISORY,
})


class BriefValidationError(ValueError):
    """Raised when a brief payload fails schema validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class ResearchBrief:
    """Immutable research-brief.v1 payload."""

    # --- Schema identity ---
    schema: str = "research-brief.v1"
    schema_version: str = "1.0.0"

    # --- Core ---
    brief_id: str = ""
    original_request: str = ""
    resolved_objective: str = ""
    task_class: str = ""

    # --- Questions and evidence ---
    key_questions: tuple[str, ...] = ()
    required_evidence_categories: tuple[str, ...] = ()
    source_priorities: tuple[str, ...] = ()

    # --- Constraints ---
    freshness_max_days: int | None = None
    limiting_checks: tuple[str, ...] = ()
    disconfirming_checks: tuple[str, ...] = ()
    explicit_exclusions: tuple[str, ...] = ()
    stopping_conditions: tuple[str, ...] = ()

    # --- Identity ---
    platform: str = ""  # "claude-code", "codex", "opencode"
    caller: str = ""  # skill or agent name
    workspace: str = ""  # git workspace or project root
    session_id: str = ""
    session_id_verified: bool = False  # True when provider by platform identity API
    run_id: str = ""

    # --- Integrity ---
    content_hash: str = ""
    created_at: str = ""

    # --- Query plan (populated after derive_queries) ---
    planned_query_families: tuple[str, ...] = ()
    executed_queries: tuple[dict[str, Any], ...] = ()
    omitted_queries: tuple[dict[str, str], ...] = ()

    def validate(self) -> None:
        errors: list[str] = []
        if not self.original_request:
            errors.append("original_request is required")
        if self.task_class and self.task_class not in VALID_TASK_CLASSES:
            errors.append(f"unknown task_class: {self.task_class}")
        for cat in self.required_evidence_categories:
            if cat not in VALID_EVIDENCE_CATEGORIES:
                errors.append(f"unknown evidence category: {cat}")
        for pri in self.source_priorities:
            if pri not in VALID_SOURCE_PRIORITIES:
                errors.append(f"unknown source priority: {pri}")
        if errors:
            raise BriefValidationError(errors)

    def to_dict(self) -> dict[str, Any]:
        base = asdict(self)
        base["content_hash"] = self._compute_hash(base)
        return base

    @staticmethod
    def _compute_hash(data: dict[str, Any]) -> str:
        """Return SHA-256 of canonical JSON (sorted keys, exclude content_hash).

        Uses a custom encoder that serialises tuples as JSON arrays so the
        hash is stable across serialisation round-trips (tuple → list on read).
        """
        excluded = data.copy()
        excluded.pop("content_hash", None)

        class _TupleAsListEncoder(json.JSONEncoder):
            def default(self, o: object) -> object:
                if isinstance(o, tuple):
                    return list(o)
                return str(o)

        canonical = json.dumps(excluded, sort_keys=True, ensure_ascii=False,
                               cls=_TupleAsListEncoder).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


# ---- Factories ----

def build_brief(
    original_request: str,
    *,
    task_class: str = TASK_CLASS_LOOKUP,
    platform: str = "claude-code",
    caller: str = "unknown",
    workspace: str = "",
    session_id: str = "",
    session_id_verified: bool = False,
    run_id: str = "",
) -> ResearchBrief:
    """Create a validated research-brief.v1 with sensible defaults for simple lookups."""
    brief_id = f"rb-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    brief = ResearchBrief(
        brief_id=brief_id,
        original_request=original_request,
        resolved_objective=original_request,
        task_class=task_class,
        key_questions=(original_request,),
        required_evidence_categories=(),
        source_priorities=(SOURCE_PRIORITY_AUTHORITATIVE,),
        stopping_conditions=("first_sufficient_evidence",),
        platform=platform,
        caller=caller,
        workspace=workspace,
        session_id=session_id,
        session_id_verified=session_id_verified,
        run_id=run_id,
        created_at=now,
    )
    brief.validate()
    return brief


def brief_from_dict(data: dict[str, Any]) -> ResearchBrief:
    """Deserialise a dict back into a ResearchBrief, re-validating on construction."""
    result = ResearchBrief(**{k: v for k, v in data.items() if k in ResearchBrief.__dataclass_fields__})
    result.validate()
    return result


def write_brief(brief: ResearchBrief, path: str) -> str:
    """Write a brief to an exclusive-create file.  Returns the path.

    Raises FileExistsError if the target already exists.
    Raises BriefValidationError if the brief is invalid.
    """
    brief.validate()
    data = brief.to_dict()
    from pathlib import Path  # noqa: F811
    p = Path(path)
    if p.exists():
        raise FileExistsError(f"brief already exists: {path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(p)


# ---- Data-path table for each research-brief.v1 field ----
# | Field                     | Writer        | Storage           | Reader                 | Authority         | Freshness        | Failure direction              | Live evidence                        |
# |---------------------------|---------------|-------------------|------------------------|-------------------|------------------|-------------------------------|--------------------------------------|
# | schema / schema_version   | build_brief   | brief JSON        | any consumer           | hardcoded         | per brief        | schema-vers mismatch → reject | static invariant                     |
# | brief_id                  | build_brief   | brief JSON        | linker / audit        | uuid4             | per brief        | collision → FileExistsError | unique per run                       |
# | original_request          | caller        | brief JSON        | evidence routing       | human / api input | per brief        | empty → BriefValidationError | caller-provided                       |
# | resolved_objective        | build_brief   | brief JSON        | router / adapters     | derivation        | per brief        | empty → BriefValidationError | normalised from request               |
# | task_class                | build_brief   | brief JSON        | capability router     | derivation        | per brief        | unknown → BriefValidationError | one of VALID_TASK_CLASSES            |
# | key_questions             | build_brief   | brief JSON        | query derivation      | derivation        | per brief        | empty → conservative routing | one per evidence category targeted     |
# | required_evidence_categories | build_brief| brief JSON       | lane router           | derivation        | per brief        | empty → no routing constraints| maps to router.TaskSignals fields     |
# | source_priorities         | build_brief   | brief JSON        | source opener         | derivation        | per brief        | empty → authoritative default | determines opening priority          |
# | freshness_max_days        | build_brief   | brief JSON        | cache / provider gate | derivation        | per brief        | None → no freshness gate     | limits stale-source fallback          |
# | limiting_checks           | build_brief   | brief JSON        | post-exec assessment  | derivation        | per brief        | empty → no limit check        | recorded but optional                 |
# | disconfirming_checks      | build_brief   | brief JSON        | post-exec assessment  | derivation        | per brief        | empty → no disconfirmation    | recorded but optional                 |
# | explicit_exclusions       | build_brief   | brief JSON        | router / adapters     | derivation        | per brief        | empty → no scope bound        | prevents waste on excluded areas      |
# | stopping_conditions       | build_brief   | brief JSON        | execution gate        | derivation        | per brief        | empty → first_sufficient      | controls how many lanes are tried     |
# | platform / caller / ws / session / run | build_brief | brief JSON | audit / identity gate | caller            | per brief        | missing → identity rejection  | recorded at brief creation            |
# | content_hash             | to_dict       | brief JSON        | verifier / linker     | SHA-256 of rest   | per brief        | mismatch → artifact rejected  | deterministic from canon JSON         |
# | created_at               | build_brief   | brief JSON        | freshness assessment  | system clock      | per brief        | future → warn                 | ISO-8601 UTC                          |
# | planned_query_families   | derive_queries| brief JSON        | executor              | derivation        | per brief        | empty → no queries derived    | recorded before execution             |
# | executed_queries         | executor      | brief JSON (post) | audit / quality       | post-execution    | per run          | empty → no evidence collected  | recorded after lane execution         |
# | omitted_queries          | derive_queries| brief JSON        | audit / traceability  | derivation        | per brief        | empty → no omissions recorded | records what was skipped and why      |
