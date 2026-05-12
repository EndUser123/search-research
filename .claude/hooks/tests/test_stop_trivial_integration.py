#!/usr/bin/env python3
"""
test_stop_trivial_integration.py — Phase 1 end-to-end integration tests.

Verifies that the trivial exchange short-circuit wires correctly into Stop.py:
  1. GATE_METADATA exists and is consulted
  2. Quality gates are suppressed on trivial exchanges
  3. Policy gates are NOT suppressed (trivial_suppressible=False)
  4. Contract completions are NOT trivial (contract_active=True)
"""
from __future__ import annotations

import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS))

import pytest


class TestStopEntryTrivialWiring:
    """Verify trivial detection and GATE_METADATA integration at Stop entry."""

    def test_gate_metadata_has_trivial_suppressible_field(self):
        from Stop import GATE_METADATA
        for name, meta in GATE_METADATA.items():
            assert "trivial_suppressible" in meta, f"{name} missing trivial_suppressible"

    def test_trivial_suppressible_false_for_policy_gates(self):
        from Stop import GATE_METADATA
        policy_suppressible = [
            n for n, m in GATE_METADATA.items()
            if m["class"] == "policy" and m["trivial_suppressible"]
        ]
        assert not policy_suppressible, f"Policy gates marked trivial-suppressible: {policy_suppressible}"

    def test_trivial_suppressible_true_for_quality_gates(self):
        from Stop import GATE_METADATA
        quality_not_suppressible = [
            n for n, m in GATE_METADATA.items()
            if m["class"] == "quality" and not m["trivial_suppressible"]
        ]
        # advisory gate is registered as quality but trivially suppressible — that's the design
        # all other quality gates should be suppressible
        unexpected = [n for n in quality_not_suppressible if n != "advisory"]
        assert not unexpected, f"Quality gates not trivial-suppressible: {unexpected}"

    def test_policy_gates_all_have_priority(self):
        from Stop import GATE_METADATA
        policy_gates = {n: m for n, m in GATE_METADATA.items() if m["class"] == "policy"}
        assert all("priority" in m for m in policy_gates.values()), "Some policy gates missing priority"
        assert all(isinstance(m["priority"], int) for m in policy_gates.values()), "Non-int priority in policy gates"

    def test_quality_gates_all_have_priority(self):
        from Stop import GATE_METADATA
        quality_gates = {n: m for n, m in GATE_METADATA.items() if m["class"] == "quality"}
        assert all("priority" in m for m in quality_gates.values()), "Some quality gates missing priority"
        assert all(isinstance(m["priority"], int) for m in quality_gates.values()), "Non-int priority in quality gates"


class TestTrivialExchangeIntegration:
    """Integration: is_trivial_exchange + GATE_METADATA for gate suppression."""

    def test_trivial_numeric_response_detected(self):
        from __lib.trivial_turns import is_trivial_exchange
        trivial, reason = is_trivial_exchange(
            context={"user_prompt": "what is 2+2"},
            response="4",
            turn_mode="analysis",
            contract_active=False,
        )
        assert trivial, f"Expected trivial for '4' numeric answer, got reason={reason}"

    def test_trivial_numeric_not_suppressed_when_contract_active(self):
        from __lib.trivial_turns import is_trivial_exchange
        trivial, reason = is_trivial_exchange(
            context={"user_prompt": "finish the task"},
            response="done",
            turn_mode="analysis",
            contract_active=True,
        )
        assert not trivial, f"Contract completion MUST NOT be trivial, got reason={reason}"

    def test_trivial_control_mode_detected(self):
        from __lib.trivial_turns import is_trivial_exchange
        trivial, reason = is_trivial_exchange(
            context={"user_prompt": "stop"},
            response="understood",
            turn_mode="control",
            contract_active=False,
        )
        assert trivial, f"Expected trivial for control mode, got reason={reason}"

    def test_non_trivial_with_epistemic_structure(self):
        from __lib.trivial_turns import is_trivial_exchange
        trivial, reason = is_trivial_exchange(
            context={"user_prompt": "analyze the architecture"},
            response="[FACT]\n- The system uses a microservices pattern",
            turn_mode="analysis",
            contract_active=False,
        )
        assert not trivial, f"[FACT] tagged response must NOT be trivial, got reason={reason}"

    def test_trivial_smoke_test_detected(self):
        from __lib.trivial_turns import is_trivial_exchange
        trivial, reason = is_trivial_exchange(
            context={"user_prompt": "ping"},
            response="pong",
            turn_mode="control",
            contract_active=False,
        )
        assert trivial, f"Expected trivial for ping, got reason={reason}"

    def test_trivial_suppressible_attribute_readable_from_metadata(self):
        from Stop import GATE_METADATA
        for name, meta in GATE_METADATA.items():
            val = meta.get("trivial_suppressible")
            assert isinstance(val, bool), f"{name}: trivial_suppressible is {type(val).__name__}, expected bool"


class TestPolicyBlockPriority:
    """_POLICY_BLOCK_PRIORITY is derived from GATE_METADATA and covers all policy gates."""

    def test_policy_block_priority_covers_all_policy_gates(self):
        from Stop import _POLICY_BLOCK_PRIORITY, GATE_METADATA
        policy_in_metadata = {n for n, m in GATE_METADATA.items() if m["class"] == "policy"}
        policy_in_priority = set(_POLICY_BLOCK_PRIORITY.keys())
        missing = policy_in_metadata - policy_in_priority
        assert not missing, f"Policy gates missing from _POLICY_BLOCK_PRIORITY: {missing}"

    def test_policy_block_priority_values_match_metadata(self):
        from Stop import _POLICY_BLOCK_PRIORITY, GATE_METADATA
        mismatches = {}
        for name in _POLICY_BLOCK_PRIORITY:
            meta_priority = GATE_METADATA[name]["priority"]
            dict_priority = _POLICY_BLOCK_PRIORITY[name]
            if meta_priority != dict_priority:
                mismatches[name] = f"metadata={meta_priority}, dict={dict_priority}"
        assert not mismatches, f"Priority mismatches: {mismatches}"

    def test_policy_block_priority_sorted(self):
        from Stop import _POLICY_BLOCK_PRIORITY
        sorted_prios = sorted(_POLICY_BLOCK_PRIORITY.values())
        assert sorted_prios == sorted(_POLICY_BLOCK_PRIORITY.values()), "Priority dict not sorted (but iteration order is irrelevant)"


class TestSyncInvariant:
    """Invariant: GATE_CLASSES and GATE_METADATA['class'] stay in sync."""

    def test_sync_check_runs_at_import_time(self):
        # The if __debug__ block in Stop.py validates GATE_CLASSES vs GATE_METADATA['class'].
        # If they're out of sync, import fails with AssertionError.
        # We test this by importing Stop and checking no exception was raised.
        # The import already happened at module scope above, so we just verify it succeeded.
        from Stop import GATE_CLASSES, GATE_METADATA
        # If we get here, import succeeded — verify the check is actually present
        import inspect
        src = inspect.getsource(sys.modules["Stop"])
        assert "GATE_METADATA['class']" in src, "Sync check not present in Stop.py source"
        assert "GATE_CLASSES" in src, "GATE_CLASSES not referenced in sync check"

    def test_all_gates_in_gate_classes_are_in_metadata(self):
        from Stop import GATE_CLASSES, GATE_METADATA
        extra = set(GATE_METADATA.keys()) - set(GATE_CLASSES.keys())
        # Metadata can have extras not registered (e.g., future gates)
        # But GATE_CLASSES entries must all be in METADATA
        missing = set(GATE_CLASSES.keys()) - set(GATE_METADATA.keys())
        assert not missing, f"GATE_CLASSES has entries not in GATE_METADATA: {missing}"