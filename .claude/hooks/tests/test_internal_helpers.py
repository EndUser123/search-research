"""Meta tests that enforce _is_task_relevant_verification_update scope invariants
and health calibration correctness."""

import ast
import importlib
import inspect
import json
import os
import time
from pathlib import Path
from unittest import mock


def test_verification_update_helper_scope_is_local():
    """_is_task_relevant_verification_update is Stop-local, not a shared classifier."""
    Stop = importlib.import_module("Stop")
    helper = getattr(Stop, "_is_task_relevant_verification_update", None)

    assert helper is not None, "_is_task_relevant_verification_update not found in Stop"

    # Must be defined in Stop, not in some shared utils module
    assert helper.__module__ == "Stop", (
        f"helper lives in {helper.__module__} — must stay Stop-local"
    )

    # Not imported into known hook modules as a public helper
    forbidden_import_modules = [
        "__lib.task_contract",
        "Stop_behavior_gates",
        "Stop_semantic_critic",
        "Stop_reasoning_quality_gate",
    ]

    for mod_name in forbidden_import_modules:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue  # module doesn't exist yet — that's fine

        for name, obj in vars(mod).items():
            if obj is helper:
                raise AssertionError(
                    f"_is_task_relevant_verification_update leaked into {mod_name} "
                    f"as {name}; helper must remain Stop-local."
                )


def test_verification_update_helper_only_called_from_orthogonality():
    """Only _is_response_orthogonal_to_contract may call this helper inside Stop.py."""
    Stop = importlib.import_module("Stop")
    source = inspect.getsource(Stop)
    tree = ast.parse(source)

    calls: list[str] = []

    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                if node.func.id == "_is_task_relevant_verification_update":
                    # Walk up to find containing FunctionDef
                    func_name = _find_containing_func(tree, node)
                    calls.append(func_name)
            self.generic_visit(node)

    CallVisitor().visit(tree)

    assert calls, (
        "helper is never called — test may be stale or implementation changed"
    )

    actual_callers = sorted(set(calls))
    expected = {"_is_response_orthogonal_to_contract"}

    assert set(actual_callers) == expected, (
        "helper must only be used from _is_response_orthogonal_to_contract; "
        f"found calls from: {actual_callers}"
    )


def _find_containing_func(tree: ast.AST, node: ast.AST) -> str | None:
    """Return the name of the innermost FunctionDef that contains `node`."""
    # Build parent map by walking the tree
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            try:
                child_id = id(child)
                # Only keep the closest parent for each child
                if child_id not in parents:
                    parents[child_id] = parent
            except Exception:
                pass

    current = node
    while current is not None:
        parent = parents.get(id(current))
        if isinstance(parent, ast.FunctionDef):
            return parent.name
        current = parent
    return None


# =============================================================================
# Health calibration tests
# =============================================================================


def test_rolling_1h_filter_excludes_old_events():
    """events older than 3600s are not counted in rolling window."""
    import Stop

    now = time.time()
    old_ts = (now - 7200) * 1000  # 2 hours ago in ms
    recent_ts = (now - 1800) * 1000  # 30 minutes ago in ms

    fake_log = Path("P:/fake_errors_last_hour.jsonl")
    try:
        fake_log.write_text(
            json.dumps({"timestamp": _fmt_ts(old_ts), "error_type": "execute"}) + "\n"
            + json.dumps({"timestamp": _fmt_ts(recent_ts), "error_type": "load"}) + "\n",
            encoding="utf-8",
        )

        errors, real_fails, expected = Stop._classify_error_events(fake_log)
        assert errors == 1, "only recent event should count"
        assert real_fails == 1, "load is a real failure"
        assert expected == 0
    finally:
        fake_log.unlink(missing_ok=True)


def test_timeout_events_classified_separately():
    """timeout_imminent/killed/terminated/exceeded are NOT real failures."""
    import Stop

    now = time.time()
    recent = (now - 300) * 1000  # 5 minutes ago

    fake_log = Path("P:/fake_timeout_events.jsonl")
    try:
        fake_log.write_text(
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "load"}) + "\n"
            + json.dumps({"timestamp": _fmt_ts(recent), "error_type": "timeout_imminent"}) + "\n"
            + json.dumps({"timestamp": _fmt_ts(recent), "error_type": "timeout_terminated"}) + "\n"
            + json.dumps({"timestamp": _fmt_ts(recent), "error_type": "timeout_killed"}) + "\n"
            + json.dumps({"timestamp": _fmt_ts(recent), "error_type": "timeout_exceeded"}) + "\n",
            encoding="utf-8",
        )

        errors, real_fails, expected = Stop._classify_error_events(fake_log)
        assert errors == 5, "all events counted"
        assert real_fails == 1, "only 'load' is a real failure"
        assert expected == 4, "4 timeout patterns are expected, not failures"
    finally:
        fake_log.unlink(missing_ok=True)


def test_benign_not_task_start_volume_health_under_new_model(tmp_path):
    """High not-task-start volume must NOT fire any writer alert under tuned model.

    The old 'HIGH skip rate' wording is gone. The tuned model classifies
    'not_a_task_start' as benign — it does not count toward suspicious skips.
    A window of 100 benign skips should produce a healthy summary.
    """
    import json
    from datetime import datetime, timezone
    from contract_health import get_health_summary

    diag = tmp_path / "logs" / "diagnostics"
    diag.mkdir(parents=True)

    now = datetime.now(timezone.utc).timestamp()
    writer_lines = [
        json.dumps({
            "event": "contract_skip",
            "reason": "not_a_task_start",
            "feature": "task_contract_writer",
            "terminal_id": "test",
            "timestamp": now - i,
        }) for i in range(100)
    ]
    (diag / "task_contract_writer_telemetry.jsonl").write_text(
        "\n".join(writer_lines) + "\n"
    )

    summary = get_health_summary(hooks_dir=tmp_path)
    assert summary.healthy is True, (
        f"100% benign skips should be healthy; got alerts: {summary.alerts}"
    )
    alert_text = " ".join(summary.alerts)
    assert "HIGH skip rate" not in alert_text
    assert "writer underperformance" not in alert_text


def test_real_suspicious_skip_problem_uses_tuned_wording(tmp_path):
    """Real writer infrastructure failure must surface 'writer underperformance'.

    Suspicious skip ratio > 40% triggers the tuned model alert. The old
    'HIGH skip rate' wording must NOT appear.
    """
    import json
    from datetime import datetime, timezone
    from contract_health import get_health_summary

    diag = tmp_path / "logs" / "diagnostics"
    diag.mkdir(parents=True)

    now = datetime.now(timezone.utc).timestamp()
    writer_lines = []
    writer_lines += [
        json.dumps({
            "event": "contract_create",
            "feature": "task_contract_writer",
            "terminal_id": "test",
            "timestamp": now - i,
        }) for i in range(30)
    ]
    writer_lines += [
        json.dumps({
            "event": "contract_skip",
            "reason": "not_a_task_start",
            "feature": "task_contract_writer",
            "terminal_id": "test",
            "timestamp": now - i,
        }) for i in range(30, 55)
    ]
    writer_lines += [
        json.dumps({
            "event": "contract_skip",
            "reason": "no_terminal_id",
            "feature": "task_contract_writer",
            "terminal_id": "test",
            "timestamp": now - i,
        }) for i in range(55, 85)
    ]
    (diag / "task_contract_writer_telemetry.jsonl").write_text(
        "\n".join(writer_lines) + "\n"
    )

    summary = get_health_summary(hooks_dir=tmp_path)
    assert summary.healthy is False, (
        f"55% suspicious ratio should be unhealthy; got healthy={summary.healthy}"
    )
    alert_text = " ".join(summary.alerts)
    assert "writer underperformance" in alert_text
    assert "HIGH skip rate" not in alert_text


def test_real_failures_still_alert():
    """load/execute/runtime errors above threshold should still trigger alert."""
    import Stop

    # Simulate 6 real failures in the last hour (threshold = 5)
    now = time.time()
    recent = (now - 300) * 1000

    fake_log = Path("P:/fake_real_failures.jsonl")
    try:
        lines = [
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "load"}) + "\n",
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "execute"}) + "\n",
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "runtime"}) + "\n",
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "load"}) + "\n",
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "execute"}) + "\n",
            json.dumps({"timestamp": _fmt_ts(recent), "error_type": "stderr"}) + "\n",
        ]
        fake_log.write_text("".join(lines), encoding="utf-8")

        errors, real_fails, expected = Stop._classify_error_events(fake_log)
        assert errors == 6
        assert real_fails == 6, "load/execute/runtime/stderr all count as real failures"
        assert expected == 0

        # Threshold is 5, 6 failures > 5 → should alert
        error_threshold = int(os.environ.get("CC_ERRORS_THRESHOLD", "5"))
        should_alert = real_fails > error_threshold
        assert should_alert, "6 real failures should alert with threshold 5"
    finally:
        fake_log.unlink(missing_ok=True)


def _fmt_ts(ms: float) -> str:
    """Format milliseconds-epoch as ISO string for cc_errors log."""
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ms / 1000))