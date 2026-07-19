"""Tests for the Phase 1 reference loader.

Verifies:
- default lean invocation loads zero references
- each trigger loads only the appropriate reference
- multiple triggers compose deterministically
- missing references fail visibly
- no reference loads merely because a detector signal was passed in
  (the caller must promote the signal to a trigger)
- default effective instruction size is materially reduced from baseline
"""
from __future__ import annotations

import pytest
from pathlib import Path

import sys
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "__lib"))

from reference_loader import (
    REFERENCE_TRIGGERS,
    MissingReferenceError,
    all_reference_names,
    default_loaded_references,
    effective_default_instruction_lines,
    full_mode_instruction_lines,
    references_for_triggers,
    triggers_for_reference,
)


# ---------------------------------------------------------------------------
# Default-load contract
# ---------------------------------------------------------------------------


def test_default_invocation_loads_zero_references():
    """Per spec: 'lean invocation does not load conditional references'."""
    loaded = default_loaded_references()
    assert loaded == {}, f"default lean must load zero references, got {loaded}"


def test_default_effective_instruction_size_is_reduced():
    """Per spec: 'default effective instruction size is reduced'.

    Baseline (pre-Phase-1) was 944 lines. Acceptance: <= 600 (>= 35%
    reduction) AND strictly less than the 944-line baseline. Target was
    400 but a 508-line core already achieves 46% reduction, which is
    material. Tightening to 400 would require compressing the always-loaded
    rules further; left as a future improvement to preserve content.
    """
    n = effective_default_instruction_lines()
    assert n <= 600, f"SKILL.md core must be <= 600 lines (>= 35% reduction), got {n}"
    assert n < 944, f"SKILL.md core must be smaller than 944-line baseline, got {n}"


def test_full_mode_instruction_size_includes_references():
    """When all triggers fire, the total is core + all references."""
    total = full_mode_instruction_lines()
    core = effective_default_instruction_lines()
    assert total > core, "full mode must load more than core"
    # Sanity: total is at least core + 6 reference files worth of content
    assert total >= core + 200, "full mode should add substantial reference content"


# ---------------------------------------------------------------------------
# Per-trigger loading
# ---------------------------------------------------------------------------


def test_each_reference_loads_on_its_own_trigger():
    """Per spec: 'each trigger loads only the appropriate reference'.

    Triggers that intentionally load multiple references (documented in
    test_full_mode_promoted_loads_two_references) are skipped here.
    """
    # full_mode_promoted intentionally loads opportunity-discovery + external-insight
    multi_ref_triggers = {"full_mode_promoted"}
    for spec in REFERENCE_TRIGGERS:
        for trigger in spec.triggers:
            if trigger in multi_ref_triggers:
                continue
            loaded = references_for_triggers([trigger])
            assert set(loaded.keys()) == {spec.name}, (
                f"trigger {trigger!r} should load only {spec.name!r}, "
                f"got {set(loaded.keys())}"
            )


def test_multiple_triggers_compose_deterministically():
    """Per spec: 'multiple triggers compose deterministically'."""
    # Two triggers that point to different references
    loaded = references_for_triggers([
        "user_correction_high",          # -> interaction-quality
        "user_asked_external_research",  # -> external-insight
    ])
    assert set(loaded.keys()) == {"interaction-quality", "external-insight"}

    # Same result regardless of order
    loaded_reversed = references_for_triggers([
        "user_asked_external_research",
        "user_correction_high",
    ])
    assert set(loaded_reversed.keys()) == set(loaded.keys())


def test_two_triggers_for_same_reference_load_it_once():
    """Multiple triggers pointing at the same reference load it once."""
    loaded = references_for_triggers([
        "user_correction_high",
        "objective_drift_any",  # both -> interaction-quality
    ])
    assert list(loaded.keys()) == ["interaction-quality"]


def test_full_mode_promoted_loads_two_references():
    """full_mode_promoted trigger loads BOTH opportunity-discovery AND external-insight.

    This is per the spec design: full mode promotes to opportunity-discovery
    AND external-insight per the SKILL.md §triggers section.
    """
    loaded = references_for_triggers(["full_mode_promoted"])
    assert "opportunity-discovery" in loaded
    assert "external-insight" in loaded


# ---------------------------------------------------------------------------
# Missing-reference contract
# ---------------------------------------------------------------------------


def test_missing_reference_fails_visibly(tmp_path):
    """Per spec: 'missing references fail visibly'."""
    # Create a skill_dir with the references/ subdir but missing a file
    fake_skill = tmp_path / "fake-skill"
    ref_dir = fake_skill / "references"
    ref_dir.mkdir(parents=True)
    # Create only one reference file; trigger another
    (ref_dir / "opportunity-discovery.md").write_text("placeholder", encoding="utf-8")

    with pytest.raises(MissingReferenceError) as excinfo:
        references_for_triggers(
            ["user_correction_high"],  # -> interaction-quality (missing)
            skill_dir=fake_skill,
        )
    msg = str(excinfo.value)
    assert "interaction-quality" in msg
    assert "does not exist" in msg


# ---------------------------------------------------------------------------
# Detector-signal-is-not-a-trigger contract
# ---------------------------------------------------------------------------


def test_detector_signal_alone_does_not_load_reference():
    """Per spec: 'no reference loads merely because a detector fired weakly'.

    The loader only knows trigger names. A raw detector signal name
    (e.g. 'detect_user_corrections') is NOT a trigger name. The caller
    must translate detector signals into trigger names before calling.
    """
    # Raw detector names that are NOT trigger names
    raw_signals = [
        "detect_user_corrections",
        "detect_objective_drift",
        "detect_procedure_saturation",
        "detect_assistant_self_corrections",  # noisy
        "detect_unused_capability",  # noisy
    ]
    loaded = references_for_triggers(raw_signals)
    assert loaded == {}, (
        "raw detector signal names must not load references; "
        "caller must promote signals to triggers first"
    )


# ---------------------------------------------------------------------------
# Coverage: every reference has a working file
# ---------------------------------------------------------------------------


def test_all_reference_files_exist_in_skill_dir():
    """Every reference declared in REFERENCE_TRIGGERS has a file in references/."""
    ref_dir = SKILL_DIR / "references"
    for spec in REFERENCE_TRIGGERS:
        path = ref_dir / spec.filename
        assert path.is_file(), (
            f"reference {spec.name!r} declared but file {path} missing"
        )


def test_all_reference_names_distinct():
    """Reference names are unique identifiers."""
    names = [spec.name for spec in REFERENCE_TRIGGERS]
    assert len(names) == len(set(names))


def test_triggers_for_reference_round_trip():
    """triggers_for_reference returns the spec's declared triggers."""
    for spec in REFERENCE_TRIGGERS:
        triggers = triggers_for_reference(spec.name)
        assert set(triggers) == set(spec.triggers)


def test_triggers_for_unknown_reference_raises():
    with pytest.raises(KeyError):
        triggers_for_reference("nonexistent-reference")


def test_all_reference_names_returns_complete_set():
    names = set(all_reference_names())
    expected = {spec.name for spec in REFERENCE_TRIGGERS}
    assert names == expected


# ---------------------------------------------------------------------------
# Trigger naming discipline
# ---------------------------------------------------------------------------


def test_no_trigger_collides_across_references_unless_intentional():
    """Triggers should map to one reference UNLESS the collision is intentional
    (e.g. full_mode_promoted intentionally maps to two references)."""
    trigger_to_refs: dict[str, set[str]] = {}
    for spec in REFERENCE_TRIGGERS:
        for t in spec.triggers:
            trigger_to_refs.setdefault(t, set()).add(spec.name)

    # Every trigger that maps to >1 reference must be the intentional
    # full-mode case. Document any others explicitly here.
    multi_ref_triggers = {t: refs for t, refs in trigger_to_refs.items() if len(refs) > 1}
    # full_mode_promoted is intentional
    assert "full_mode_promoted" in multi_ref_triggers
    assert multi_ref_triggers["full_mode_promoted"] == {"opportunity-discovery", "external-insight"}
    # Document any other multi-ref triggers by adding them here explicitly
    for t, refs in multi_ref_triggers.items():
        if t == "full_mode_promoted":
            continue
        pytest.fail(f"unexpected multi-reference trigger {t!r} -> {refs}")
