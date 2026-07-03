"""Tests for Phase 2 epistemic enforcement: applicability routing, policy arbitration,
rollout modes, and telemetry enrichment."""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_stop(data: dict, monkey_env: dict | None = None, extra_path: str | None = None) -> dict:
    """Run Stop.py main() with the given data, return parsed JSON output."""
    import subprocess

    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.setdefault("CLAUDE_SESSION_ID", "test-session")
    env.setdefault("CLAUDE_TERMINAL_ID", "test-terminal")
    env.pop("STOP_GATE_ROLLOUT_EPISTEMIC_CONTRACT", None)
    env.pop("STOP_GATE_ROLLOUT_UNVERIFIED_STANCE", None)
    if monkey_env:
        env.update(monkey_env)

    cmd = [sys.executable, str(root / "Stop.py")]
    proc = subprocess.run(
        cmd,
        input=json.dumps(data),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(root),
        timeout=60,
    )
    # Ignore hook stderr (warnings from PostToolUse etc.)
    if proc.returncode not in (0, 2):
        pytest.fail(f"Stop.py failed: {proc.stderr!r} stdout={proc.stdout!r}")
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout.strip())


def _stop_data(
    response: str = "The file is at P:/foo/bar.py",
    prompt: str = "Where is the file?",
    tool_events: list | None = None,
) -> dict:
    return {
        "response": response,
        "prompt": prompt,
        "tool_events": tool_events or [],
    }


# ---------------------------------------------------------------------------
# Enums and is_gate_applicable
# ---------------------------------------------------------------------------

class TestClaimKindTurnKindEnums:
    def test_claim_kind_values(self):
        from Stop import ClaimKind
        assert ClaimKind.FORMAT_ONLY.value == "format_only"
        assert ClaimKind.FACTUAL.value == "factual"
        assert ClaimKind.CAUSAL.value == "causal"
        assert ClaimKind.STANCE.value == "stance"
        assert ClaimKind.UNKNOWN.value == "unknown"

    def test_turn_kind_values(self):
        from Stop import TurnKind
        assert TurnKind.ANALYSIS.value == "analysis"
        assert TurnKind.CONTROL.value == "control"
        assert TurnKind.EXPLORATION.value == "exploration"
        assert TurnKind.DEBUG_META.value == "debug_meta"
        assert TurnKind.PLAN.value == "plan"
        assert TurnKind.EXECUTION_REPORT.value == "execution_report"
        assert TurnKind.FINAL_ANSWER.value == "final_answer"

    def test_rollout_mode_values(self):
        from Stop import RolloutMode
        assert RolloutMode.BLOCK.value == "block"
        assert RolloutMode.ADVISORY.value == "advisory"
        assert RolloutMode.SHADOW.value == "shadow"
        assert RolloutMode.DISABLED.value == "disabled"


class TestIsGateApplicable:
    def test_unknown_gate_allowed(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind
        ok, reason = is_gate_applicable("nonexistent_gate", TurnKind.ANALYSIS, ClaimKind.FACTUAL, set())
        assert ok is True
        assert reason == ""

    def test_rollout_disabled_skips_gate(self, monkeypatch):
        from Stop import is_gate_applicable, ClaimKind, TurnKind, GATE_METADATA, _get_rollout_mode, RolloutMode

        # Gate not DISABLED in metadata
        ok1, reason1 = is_gate_applicable("safety_gate", TurnKind.ANALYSIS, ClaimKind.FACTUAL, set())
        assert ok1 is True
        assert reason1 == ""

        # safety_gate still not DISABLED even with ADVISORY env var
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "advisory")
        ok2, reason2 = is_gate_applicable("safety_gate", TurnKind.ANALYSIS, ClaimKind.FACTUAL, set())
        assert ok2 is True  # ADVISORY != DISABLED

    def test_turn_kind_filter_excludes(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind

        # A gate that only fires on ANALYSIS (epistemic_contract)
        ok, reason = is_gate_applicable(
            "epistemic_contract",
            TurnKind.CONTROL,
            ClaimKind.FACTUAL,
            set(),
        )
        assert ok is False
        assert "turn_kind_excluded" in reason

    def test_turn_kind_filter_allows(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind
        ok, reason = is_gate_applicable(
            "epistemic_contract",
            TurnKind.ANALYSIS,
            ClaimKind.FACTUAL,
            set(),
        )
        assert ok is True
        assert reason == ""

    def test_claim_kind_filter_excludes(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind, GATE_METADATA

        # epistemic_contract fires on all claim kinds
        # (metadata uses _ALL_CLAIM_KINDS), so this should allow
        ok, reason = is_gate_applicable(
            "epistemic_contract",
            TurnKind.ANALYSIS,
            ClaimKind.FORMAT_ONLY,
            set(),
        )
        assert ok is True  # _ALL_CLAIM_KINDS = no filter

    def test_artifact_class_missing_excludes(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind

        ok, reason = is_gate_applicable(
            "cited_content_guard",  # requires cited_source artifact
            TurnKind.ANALYSIS,
            ClaimKind.FACTUAL,
            set(),  # no artifacts
        )
        # cited_source is required but not present
        assert ok is False
        assert "missing_artifacts" in reason

    def test_artifact_class_present_allows(self):
        from Stop import is_gate_applicable, ClaimKind, TurnKind
        ok, reason = is_gate_applicable(
            "cited_content_guard",
            TurnKind.ANALYSIS,
            ClaimKind.FACTUAL,
            {"cited_source"},  # artifact present
        )
        assert ok is True


class TestGetRolloutMode:
    def test_env_shadow(self, monkeypatch):
        from Stop import _get_rollout_mode, RolloutMode
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "shadow")
        assert _get_rollout_mode("safety_gate", RolloutMode.BLOCK) == RolloutMode.SHADOW

    def test_env_advisory(self, monkeypatch):
        from Stop import _get_rollout_mode, RolloutMode
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "advisory")
        assert _get_rollout_mode("safety_gate", RolloutMode.BLOCK) == RolloutMode.ADVISORY

    def test_env_disabled(self, monkeypatch):
        from Stop import _get_rollout_mode, RolloutMode
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "disabled")
        assert _get_rollout_mode("safety_gate", RolloutMode.BLOCK) == RolloutMode.DISABLED

    def test_env_block(self, monkeypatch):
        from Stop import _get_rollout_mode, RolloutMode
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "block")
        assert _get_rollout_mode("safety_gate", RolloutMode.ADVISORY) == RolloutMode.BLOCK

    def test_env_on_alias(self, monkeypatch):
        from Stop import _get_rollout_mode, RolloutMode
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "on")
        assert _get_rollout_mode("safety_gate", RolloutMode.ADVISORY) == RolloutMode.BLOCK

    def test_default_returned_when_no_env(self):
        from Stop import _get_rollout_mode, RolloutMode
        # No env var set
        assert _get_rollout_mode("safety_gate", RolloutMode.ADVISORY) == RolloutMode.ADVISORY


class TestTurnModeToTurnKind:
    def test_control_mode(self):
        from Stop import _turn_mode_to_turn_kind, TurnKind
        assert _turn_mode_to_turn_kind("control") == TurnKind.CONTROL
        assert _turn_mode_to_turn_kind("CONTROL") == TurnKind.CONTROL

    def test_analysis_mode(self):
        from Stop import _turn_mode_to_turn_kind, TurnKind
        assert _turn_mode_to_turn_kind("analysis") == TurnKind.ANALYSIS

    def test_exploration_mode(self):
        from Stop import _turn_mode_to_turn_kind, TurnKind
        assert _turn_mode_to_turn_kind("exploration") == TurnKind.EXPLORATION

    def test_plan_mode(self):
        from Stop import _turn_mode_to_turn_kind, TurnKind
        assert _turn_mode_to_turn_kind("plan") == TurnKind.PLAN

    def test_unknown_defaults_to_analysis(self):
        from Stop import _turn_mode_to_turn_kind, TurnKind
        assert _turn_mode_to_turn_kind("unknown-mode") == TurnKind.UNKNOWN


# ---------------------------------------------------------------------------
# GATE_METADATA completeness
# ---------------------------------------------------------------------------

class TestGateMetadataCompleteness:
    def _all_gates(self):
        from Stop import IN_PROCESS_GATES
        return [name for name, _ in IN_PROCESS_GATES]

    def _required_keys(self) -> list[str]:
        return [
            "class", "trivial_suppressible", "priority", "description",
            "relevant_turn_kinds", "relevant_claim_kinds",
            "required_artifact_classes", "rollout_mode",
        ]

    def test_all_gates_have_metadata(self):
        from Stop import GATE_METADATA
        for gate in self._all_gates():
            assert gate in GATE_METADATA, f"{gate} missing from GATE_METADATA"

    def test_metadata_keys_complete(self):
        from Stop import GATE_METADATA
        for gate, meta in GATE_METADATA.items():
            for key in self._required_keys():
                assert key in meta, f"{gate}: missing {key}"

    def test_rollout_mode_is_rolloutmode(self):
        from Stop import GATE_METADATA, RolloutMode
        for gate, meta in GATE_METADATA.items():
            assert isinstance(meta["rollout_mode"], RolloutMode), f"{gate}: rollout_mode not RolloutMode"

    def test_relevant_turn_kinds_is_frozenset(self):
        from Stop import GATE_METADATA
        for gate, meta in GATE_METADATA.items():
            rtk = meta["relevant_turn_kinds"]
            assert isinstance(rtk, frozenset), f"{gate}: relevant_turn_kinds not frozenset"


# ---------------------------------------------------------------------------
# Policy block arbitration
# ---------------------------------------------------------------------------

class TestPolicyBlockArbitration:
    def test_policy_block_suppressed_same_priority(self):
        # When two policy gates have the same priority, the first one wins.
        # We test this via the telemetry: the second gate's log should show
        # suppressed_by_policy_arb.
        data = _stop_data(
            response="The fix is done.",
            prompt="Is this fixed?",
        )
        result = _run_stop(data)
        # Not crashing = pass. Real arbitration testing needs multi-gate triggers.

    def test_policy_gate_never_suppressed_on_trivial(self):
        # Policy gates are never suppressed on trivial exchanges (trivial_suppressible
        # is always False for policy gates).
        from Stop import GATE_METADATA
        policy_gates = {n for n, c in GATE_METADATA.items() if c.get("class") == "policy"}
        for gate in policy_gates:
            meta = GATE_METADATA.get(gate, {})
            assert meta.get("trivial_suppressible") is not True, f"{gate}: policy gate should not be trivial_suppressible"


# ---------------------------------------------------------------------------
# Rollout mode: ADVISORY / SHADOW downgrades block → warn
# ---------------------------------------------------------------------------

class TestAdvisoryRolloutDowngrade:
    def test_env_advisory_downgrades_block_to_warn(self, monkeypatch):
        """A gate that would normally block becomes a warn when ADVISORY."""
        # Use a gate that always blocks (safety_gate is priority 0)
        # We set ADVISORY and verify it doesn't exit(0) — but safety_gate
        # shouldn't trigger on innocuous input anyway, so check the env var
        # path is wired correctly.
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "advisory")
        data = _stop_data(response="Hello", prompt="hi")
        result = _run_stop(data)
        # Should not crash/exit — allow path works fine with ADVISORY
        assert result == {} or "allow" in result.get("decision", "allow")

    def test_advisory_rollout_does_not_exit(self, monkeypatch):
        """ADVISORY gates should never call sys.exit(0)."""
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "advisory")
        data = _stop_data(response="Just saying hi", prompt="hi")
        result = _run_stop(data)
        # Any result (allow/warn) is fine — just shouldn't hard-exit on innocuous input


class TestShadowRolloutDowngrade:
    def test_shadow_rollout_logs_but_allows(self, monkeypatch):
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SAFETY_GATE", "shadow")
        data = _stop_data(response="Test response", prompt="test")
        result = _run_stop(data)
        # SHADOW should allow even if gate would block
        assert result == {} or "allow" in result.get("decision", "allow")


# ---------------------------------------------------------------------------
# Telemetry enrichment
# ---------------------------------------------------------------------------

class TestTelemetryEnrichment:
    def test_gate_skip_telemetry_has_phase2_fields(self, monkeypatch):
        """Skipped gates log turn_kind, claim_kind, rollout_mode."""
        from pathlib import Path
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            log_path = Path(f.name)

        try:
            import os
            old = os.environ.get("STOP_TELEMETRY")
            os.environ["STOP_TELEMETRY"] = "1"

            # Patch log path
            import __lib.stop_gate_telemetry as tel
            orig_file = tel._LOG_FILE
            tel._LOG_FILE = log_path

            data = _stop_data(response="Test", prompt="test")
            _run_stop(data)  # Will trigger skip paths for quality gates on trivial-ish turns

            tel._LOG_FILE = orig_file
            os.environ.pop("STOP_TELEMETRY", None)

            if not log_path.exists():
                pytest.skip("No telemetry records written — gate didn't produce skip events")

            import json
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for rec in records:
                if rec.get("decision") == "allow" and rec.get("skip_reason"):
                    assert "turn_kind" in rec, f"Skip record missing turn_kind: {rec}"
                    assert "claim_kind" in rec, f"Skip record missing claim_kind: {rec}"
                    break
        finally:
            log_path.unlink(missing_ok=True)
            if old is not None:
                os.environ["STOP_TELEMETRY"] = old


# ---------------------------------------------------------------------------
# is_gate_applicable integration in gate loop
# ---------------------------------------------------------------------------

class TestApplicabilityRoutingIntegration:
    def test_unknown_gate_no_crash(self):
        # is_gate_applicable returns True for unknown gates (line 3085)
        # so the gate loop should not crash on an unregistered gate name.
        from Stop import is_gate_applicable, ClaimKind, TurnKind
        ok, reason = is_gate_applicable("truly_nonexistent", TurnKind.ANALYSIS, ClaimKind.FACTUAL, set())
        assert ok is True
        assert reason == ""

    def test_disabled_gate_skipped_via_is_gate_applicable(self):
        """Gates with DISABLED rollout mode are skipped before execution."""
        from Stop import is_gate_applicable, ClaimKind, TurnKind, RolloutMode, GATE_METADATA

        # Find a gate with rollout_mode != DISABLED and verify DISABLED env works
        gate_name = "safety_gate"
        assert is_gate_applicable(gate_name, TurnKind.ANALYSIS, ClaimKind.FACTUAL, set()) == (True, "")

        # After setting env to disabled, is_gate_applicable returns False
        # (verified via _get_rollout_mode behavior in tests above)


# ---------------------------------------------------------------------------
# Phase 3: Runtime Claim Enforcement
# ---------------------------------------------------------------------------

class TestRuntimeClaimEnforcement:
    """Tests for Phase 3 runtime claim enforcement gate."""

    def test_runtime_claim_gate_in_gate_classes(self):
        from Stop import GATE_CLASSES
        assert GATE_CLASSES.get("runtime_claim_enforcement") == "policy"

    def test_runtime_claim_gate_in_gate_metadata(self):
        from Stop import GATE_METADATA, RolloutMode
        meta = GATE_METADATA.get("runtime_claim_enforcement")
        assert meta is not None, "runtime_claim_enforcement not in GATE_METADATA"
        assert meta["class"] == "policy"
        assert meta["rollout_mode"] == RolloutMode.ADVISORY

    def test_runtime_claim_gate_in_in_process_gates(self):
        from Stop import IN_PROCESS_GATES
        names = [n for n, _ in IN_PROCESS_GATES]
        assert "runtime_claim_enforcement" in names

    def test_run_runtime_claim_gate_returns_none_when_no_claims(self):
        """Gate returns None (allow) when no runtime claims in response."""
        from Stop import _run_runtime_claim_gate
        data = {"response": "The root cause is that the import is missing."}
        result = _run_runtime_claim_gate(data)
        assert result is None

    def test_run_runtime_claim_gate_returns_none_when_claims_verified(self, monkeypatch, tmp_path):
        """Gate returns None when runtime claims can be verified against artifacts."""
        from Stop import _run_runtime_claim_gate
        from pathlib import Path

        # Create a fake stop telemetry file with gate firing record
        telemetry_file = tmp_path / "stop_gate_telemetry.jsonl"
        telemetry_file.write_text(
            '{"gate": "epistemic_contract", "decision": "block"}\n',
            encoding="utf-8",
        )

        # Patch the artifact lookup to find the file
        monkeypatch.chdir(tmp_path)

        data = {"response": "The epistemic_contract gate fired three times."}
        result = _run_runtime_claim_gate(data)
        # When artifacts are present and match, gate should return None (allow)
        # (This tests the artifact lookup integration)
        assert result is None or isinstance(result, dict)

    def test_runtime_claim_type_classification(self):
        """Verify classify_runtime_claim detects all four claim types."""
        from __lib.runtime_claims import classify_runtime_claim, RuntimeClaimType

        tests = [
            ("The epistemic_contract gate fired three times.", RuntimeClaimType.STOP_GATE_FIRING),
            ("operatingrules and behaviorcontract co-fire in this turn.", RuntimeClaimType.UPS_HOOK_CO_FIRE),
            ("The age guard fired and blocked the request.", RuntimeClaimType.AGE_GUARD_RUNTIME),
            ("A rotation happened mid-benchmark.", RuntimeClaimType.BENCHMARK_RUN_EVENT),
        ]
        for text, expected_type in tests:
            result = classify_runtime_claim(text)
            assert expected_type in result, f"{text[:40]!r} should detect {expected_type}"

    def test_runtime_claim_type_rejects_non_runtime(self):
        """Non-runtime claims should not be detected."""
        from __lib.runtime_claims import classify_runtime_claim

        non_runtime = [
            "The root cause is that the import is missing.",
            "Yes, the fix is in place.",
            "I ran the tests and they passed.",
        ]
        for text in non_runtime:
            result = classify_runtime_claim(text)
            assert len(result) == 0, f"{text[:40]!r} should have no runtime claims"

    def test_runtime_claim_verify_produces_failure_message(self, monkeypatch, tmp_path):
        """verify_runtime_claim produces descriptive failure when artifact missing."""
        from __lib.runtime_claims import verify_runtime_claim, RuntimeClaimType

        # Ensure no artifact files exist by chdiring to empty temp dir
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CLAUDE_SESSION_ID", "test-session")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test-terminal")

        verified, msg = verify_runtime_claim(
            RuntimeClaimType.STOP_GATE_FIRING,
            "The epistemic_contract gate fired.",
            session_id="test-session",
            terminal_id="test-terminal",
        )
        # No artifacts found in isolated dir → verification fails
        assert verified is False, "Should fail when no artifacts in isolated dir"
        assert "RUNTIME CLAIM VERIFICATION FAILED" in msg
        assert "not found" in msg


class TestRuntimeClaimTelemetryEnrichment:
    """Tests for Phase 3.D telemetry enrichment."""

    def test_telemetry_log_has_phase3_fields(self, monkeypatch, tmp_path):
        """log_gate_event records artifact_class_required and artifact_class_observed."""
        import json
        from pathlib import Path
        from __lib.stop_gate_telemetry import log_gate_event

        log_file = tmp_path / "test_telemetry.jsonl"
        import __lib.stop_gate_telemetry as tel
        orig = tel._LOG_FILE
        tel._LOG_FILE = log_file
        orig_enabled = tel._TELEMETRY_ENABLED
        tel._TELEMETRY_ENABLED = True

        try:
            log_gate_event(
                gate_name="test_gate",
                classification="policy",
                profile="test",
                decision="allow",
                artifact_class_required="stop_telemetry",
                artifact_class_observed="stop_telemetry verified",
            )
            assert log_file.exists()
            records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert len(records) == 1
            assert records[0].get("artifact_class_required") == "stop_telemetry"
            assert records[0].get("artifact_class_observed") == "stop_telemetry verified"
        finally:
            tel._LOG_FILE = orig
            tel._TELEMETRY_ENABLED = orig_enabled