"""Reference loader for the AAR lean-hybrid architecture.

This module implements the physical conditional-loading mechanism introduced
in Phase 1 of the lean-hybrid implementation. The SKILL.md core contains
only the lean synthesis contract plus 1-line trigger definitions; the full
detail lives in ``references/*.md`` files. The loader is the single source
of truth for *which references are loaded given which triggers*.

Design contract
---------------
- ``load_references_for_triggers(fired_triggers)`` returns a dict of
  ``{reference_name: file_path}`` for every reference that should load.
- A reference loads **only** when at least one of its declared triggers is
  in ``fired_triggers``.
- The loader never loads all references. The default lean invocation has
  zero triggers fired → zero references loaded.
- A missing reference file raises ``MissingReferenceError`` so the failure
  is visible (per spec: "missing references fail visibly").
- The loader does NOT inspect detector signals directly; the caller passes
  in the set of triggers that have fired. A weak detector signal alone
  must not load a reference — the caller decides whether the signal rises
  to a trigger.

Trigger names are stable strings. Adding a new trigger requires updating
``REFERENCE_TRIGGERS`` below AND the SKILL.md core §triggers section.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REFERENCE_DIR_NAME = "references"
SKILL_DIR = Path(__file__).resolve().parent.parent  # .grok/skills/aar/


class MissingReferenceError(FileNotFoundError):
    """Raised when a trigger fires for a reference file that does not exist."""


@dataclass(frozen=True)
class ReferenceSpec:
    """One conditional reference and the triggers that load it."""

    name: str          # short identifier (e.g. "opportunity-discovery")
    filename: str      # file under references/
    triggers: tuple[str, ...]  # trigger names that load this reference


# Authoritative trigger → reference map.
# Adding a reference requires: (1) entry here, (2) file under references/,
# (3) trigger definition in SKILL.md core.
REFERENCE_TRIGGERS: tuple[ReferenceSpec, ...] = (
    ReferenceSpec(
        name="opportunity-discovery",
        filename="opportunity-discovery.md",
        triggers=(
            "full_mode_promoted",
            "user_asked_opportunity_landscape",
            "successful_efficiency_session",
        ),
    ),
    ReferenceSpec(
        name="interaction-quality",
        filename="interaction-quality.md",
        triggers=(
            "user_correction_high",
            "objective_drift_any",
            "correction_propagation_failure_any",
            "procedure_saturation_any",
            "user_repeated_goal_restoration",
            "user_asked_what_went_wrong",
        ),
    ),
    ReferenceSpec(
        name="epistemic-calibration",
        filename="epistemic-calibration.md",
        triggers=(
            "architectural_change_proposed",
            "durable_rule_promotion_claimed",
            "high_severity_defect",
            "cross_session_aggregation_claim",
            "headline_makes_comparative_claim",
            "user_asked_deep_root_cause",
        ),
    ),
    ReferenceSpec(
        name="operational-safety",
        filename="operational-safety.md",
        triggers=(
            "destructive_write_signal",
            "tool_result_secret_exposure_signal",
            "user_paste_secret_warning_signal",
            "file_edit_reversal_high",
            "active_incident_reported",
        ),
    ),
    ReferenceSpec(
        name="external-insight",
        filename="external-insight.md",
        triggers=(
            "user_asked_external_research",
            "reusable_failure_class_revealed",
            "root_cause_benefits_from_external_evidence",
            "platform_capabilities_may_have_changed",
            "improvement_may_exist_elsewhere",
            "local_evidence_supports_competing_explanations",
            "cross_domain_analogies_relevant",
            "full_mode_promoted",
        ),
    ),
    ReferenceSpec(
        name="handoff-and-temporal",
        filename="handoff-and-temporal.md",
        triggers=(
            "handoff_document_present",
            "prior_session_state_referenced",
            "recommendation_revision_aggregate_high",
            "stale_state_risk_material",
        ),
    ),
)


def all_reference_names() -> tuple[str, ...]:
    """Return the names of every known conditional reference."""
    return tuple(spec.name for spec in REFERENCE_TRIGGERS)


def triggers_for_reference(reference_name: str) -> tuple[str, ...]:
    """Return the triggers declared for a reference (raises KeyError if unknown)."""
    for spec in REFERENCE_TRIGGERS:
        if spec.name == reference_name:
            return spec.triggers
    raise KeyError(f"unknown reference: {reference_name!r}")


def references_for_triggers(
    fired_triggers: Iterable[str],
    *,
    skill_dir: Path | None = None,
    verify_files_exist: bool = True,
) -> dict[str, Path]:
    """Return ``{reference_name: absolute_path}`` for references that should load.

    A reference loads when at least one of its declared triggers appears in
    ``fired_triggers``. Unknown trigger names in ``fired_triggers`` are
    silently ignored (they may be detector signals the caller chose not to
    promote to triggers).

    Parameters
    ----------
    fired_triggers : iterable of str
        Trigger names that have fired for this session.
    skill_dir : Path, optional
        Override the skill root (used in tests). Defaults to the parent of
        the directory containing this module.
    verify_files_exist : bool, default True
        If True, raise MissingReferenceError when a reference that should
        load does not exist on disk.
    """
    fired = set(fired_triggers)
    skill_root = skill_dir or SKILL_DIR
    ref_dir = skill_root / REFERENCE_DIR_NAME
    loaded: dict[str, Path] = {}
    for spec in REFERENCE_TRIGGERS:
        if not any(t in fired for t in spec.triggers):
            continue
        path = ref_dir / spec.filename
        if verify_files_exist and not path.is_file():
            raise MissingReferenceError(
                f"reference {spec.name!r} should load (trigger fired) but "
                f"file {path} does not exist"
            )
        loaded[spec.name] = path
    return loaded


def default_loaded_references() -> dict[str, Path]:
    """Return the references loaded on a default lean invocation.

    The default lean invocation has zero triggers fired → zero references.
    This function exists for tests and for asserting the contract.
    """
    return references_for_triggers(fired_triggers=())


def effective_default_instruction_lines(*, skill_dir: Path | None = None) -> int:
    """Count lines loaded on a default lean invocation.

    This is SKILL.md only. References are not loaded by default.
    Used to verify the Phase 1 size-reduction acceptance criterion.
    """
    skill_root = skill_dir or SKILL_DIR
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        raise MissingReferenceError(f"SKILL.md not found at {skill_md}")
    with skill_md.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def full_mode_instruction_lines(*, skill_dir: Path | None = None) -> int:
    """Count lines loaded when all triggers fire (upper bound)."""
    skill_root = skill_dir or SKILL_DIR
    base = effective_default_instruction_lines(skill_dir=skill_root)
    ref_total = 0
    all_refs = references_for_triggers(
        fired_triggers=[t for spec in REFERENCE_TRIGGERS for t in spec.triggers],
        skill_dir=skill_root,
    )
    for path in all_refs.values():
        with path.open("r", encoding="utf-8") as f:
            ref_total += sum(1 for _ in f)
    return base + ref_total
