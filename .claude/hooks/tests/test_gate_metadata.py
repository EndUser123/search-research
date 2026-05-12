#!/usr/bin/env python3
"""
test_gate_metadata.py — Phase 1 tests for gate metadata registry.

Tests:
  GATE_METADATA existence and structure
  GATE_CLASSES ↔ GATE_METADATA sync check
  trivial_suppressible correctness per class
  Priority ordering correctness
  Policy block arbitration (when implemented)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure hooks dir is on path
_HOOKS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS))

import pytest


class TestGateMetadataExists:
    """GATE_METADATA dict is present and well-formed."""

    def test_gate_metadata_is_dict(self):
        from Stop import GATE_METADATA
        assert isinstance(GATE_METADATA, dict)

    def test_all_gates_in_gate_classes_have_metadata(self):
        from Stop import GATE_CLASSES, GATE_METADATA
        missing = [k for k in GATE_CLASSES if k not in GATE_METADATA]
        assert not missing, f"GATE_METADATA missing entries for: {missing}"

    def test_metadata_entries_have_required_fields(self):
        from Stop import GATE_METADATA
        required = {"class", "trivial_suppressible", "priority", "description"}
        for name, meta in GATE_METADATA.items():
            missing = required - set(meta.keys())
            assert not missing, f"{name}: missing fields {missing}"

    def test_class_field_is_policy_or_quality(self):
        from Stop import GATE_METADATA
        valid = {"policy", "quality"}
        bad = {n: m["class"] for n, m in GATE_METADATA.items() if m["class"] not in valid}
        assert not bad, f"Gates with invalid class: {bad}"

    def test_priority_is_integer(self):
        from Stop import GATE_METADATA
        bad = {n: type(m["priority"]).__name__ for n, m in GATE_METADATA.items()
               if not isinstance(m["priority"], int)}
        assert not bad, f"Gates with non-int priority: {bad}"

    def test_priority_range(self):
        from Stop import GATE_METADATA
        bad = {n: m["priority"] for n, m in GATE_METADATA.items()
               if not (0 <= m["priority"] <= 99)}
        assert not bad, f"Gates with out-of-range priority: {bad}"

    def test_description_is_non_empty_string(self):
        from Stop import GATE_METADATA
        bad = {n: m["description"] for n, m in GATE_METADATA.items()
               if not (isinstance(m["description"], str) and m["description"].strip())}
        assert not bad, f"Gates with empty/missing description: {bad}"

    def test_trivial_suppressible_is_boolean(self):
        from Stop import GATE_METADATA
        bad = {n: type(m["trivial_suppressible"]).__name__
               for n, m in GATE_METADATA.items()
               if not isinstance(m["trivial_suppressible"], bool)}
        assert not bad, f"Gates with non-bool trivial_suppressible: {bad}"


class TestSyncCheck:
    """GATE_CLASSES and GATE_METADATA stay in sync."""

    def test_class_field_matches_gate_classes(self):
        from Stop import GATE_CLASSES, GATE_METADATA
        mismatches = []
        for name, cls in GATE_CLASSES.items():
            if name in GATE_METADATA:
                if GATE_METADATA[name]["class"] != cls:
                    mismatches.append(
                        f"  {name}: GATE_CLASSES={cls}, GATE_METADATA[class]={GATE_METADATA[name]['class']}"
                    )
        assert not mismatches, f"Class field mismatches:\n" + "\n".join(mismatches)


class TestTrivialSuppressibleContract:
    """trivial_suppressible must be False for policy gates, True for quality gates."""

    def test_policy_gates_not_suppressible(self):
        from Stop import GATE_METADATA
        policy = {n: m for n, m in GATE_METADATA.items() if m["class"] == "policy"}
        suppressible = [n for n, m in policy.items() if m["trivial_suppressible"]]
        assert not suppressible, (
            f"Policy gates MUST NOT be trivial-suppressible: {suppressible}. "
            "Policy gates are never suppressed on trivial exchanges."
        )

    def test_quality_gates_suppressible(self):
        from Stop import GATE_METADATA
        quality = {n: m for n, m in GATE_METADATA.items() if m["class"] == "quality"}
        not_suppressible = [n for n, m in quality.items() if not m["trivial_suppressible"]]
        assert not not_suppressible, (
            f"Quality gates should be trivial-suppressible: {not_suppressible}. "
            "All quality gates SHOULD be suppressible, but this is not enforced as hard."
        )


class TestPriorityOrdering:
    """Priority values are correctly ordered: policy < quality."""

    def test_all_policy_priorities_lower_than_quality(self):
        from Stop import GATE_METADATA
        policy = {n: m["priority"] for n, m in GATE_METADATA.items() if m["class"] == "policy"}
        quality = {n: m["priority"] for n, m in GATE_METADATA.items() if m["class"] == "quality"}

        max_policy = max(policy.values()) if policy else -1
        min_quality = min(quality.values()) if quality else 100

        overlap = [n for n, p in policy.items() if p >= min_quality]
        assert not overlap, (
            f"Policy gates with priority >= {min_quality} (min quality): {overlap}. "
            f"Max policy priority = {max_policy}."
        )

    def test_safety_gate_has_priority_0(self):
        from Stop import GATE_METADATA
        assert GATE_METADATA["safety_gate"]["priority"] == 0


class TestPolicyBlockPriorityDict:
    """_POLICY_BLOCK_PRIORITY is derived from GATE_METADATA."""

    def test_policy_block_priority_exists(self):
        from Stop import _POLICY_BLOCK_PRIORITY
        assert isinstance(_POLICY_BLOCK_PRIORITY, dict)

    def test_policy_block_priority_only_has_policy_gates(self):
        from Stop import _POLICY_BLOCK_PRIORITY, GATE_METADATA
        quality = [n for n in _POLICY_BLOCK_PRIORITY if GATE_METADATA.get(n, {}).get("class") == "quality"]
        assert not quality, f"_POLICY_BLOCK_PRIORITY contains quality gates: {quality}"

    def test_policy_block_priority_matches_metadata(self):
        from Stop import _POLICY_BLOCK_PRIORITY, GATE_METADATA
        mismatches = {}
        for name, priority in _POLICY_BLOCK_PRIORITY.items():
            if name in GATE_METADATA:
                expected = GATE_METADATA[name]["priority"]
                if priority != expected:
                    mismatches[name] = f"got {priority}, expected {expected}"
        assert not mismatches, f"Priority mismatches: {mismatches}"


class TestTrivialSuppressibleAttribute:
    """All GATE_METADATA entries are accessible via .get() for safe lookup."""

    def test_all_registered_gates_accessible(self):
        from Stop import GATE_CLASSES, GATE_METADATA
        for name in GATE_CLASSES:
            meta = GATE_METADATA.get(name)
            assert meta is not None, f"{name} not in GATE_METADATA"
            assert "trivial_suppressible" in meta
            assert "priority" in meta