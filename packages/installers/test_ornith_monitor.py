from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("ornith-monitor.py")
SPEC = importlib.util.spec_from_file_location("ornith_monitor", SCRIPT)
assert SPEC and SPEC.loader
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


def test_build_lines_contains_compact_operator_fields_without_ansi():
    checked = datetime(2026, 7, 12, 20, 30, 10)
    lines = monitor.build_lines(
        {
            "model": "ornith-1.0-9b-Q4_K_M.gguf",
            "state": "LOADED",
            "slot": "IDLE",
            "task": "none",
            "activity": "idle",
            "gpu": "5%",
            "temperature": "50C",
            "vram": "10,973 MB",
            "context": "65,536",
            "started": checked - timedelta(minutes=40),
            "checked": checked,
        },
        next_seconds=9,
        frame=2,
        width=80,
    )
    output = "\n".join(lines)

    assert len(lines) == 32
    assert lines.count("") == 4
    assert "model" in output
    assert "ornith-1.0-9b-Q4_K_M.gguf" in output
    assert "LOADED" in output
    assert "10,973 MB" in output
    assert "65,536" in output
    assert "prompt" in output
    assert "sampled starts" in output
    assert "processing" in output
    assert "deferred" in output
    assert "prompt tok" in output
    assert "gen tok" in output
    assert "CCR requests" in output
    assert "in flight" in output
    assert "quota failures" in output
    assert "20:30:10" in output
    assert "next" in output and "9s" in output
    assert "O" in output
    assert "\x1b" not in output
    assert not output.startswith("\n")
    assert not output.endswith("\n")


def test_build_lines_crops_narrow_console_without_long_rows():
    lines = monitor.build_lines(
        {
            "model": "ornith-1.0-9b-Q4_K_M.gguf",
            "state": "LOADED",
            "slot": "IDLE",
            "task": "none",
            "activity": "idle",
            "gpu": "5%",
            "temperature": "50C",
            "vram": "10,973 MB",
            "context": "65,536",
            "started": None,
            "checked": datetime(2026, 7, 12, 20, 30, 10),
        },
        next_seconds=1,
        frame=0,
        width=24,
    )

    assert lines
    assert all(len(line) <= 24 for line in lines)


def test_build_screen_keeps_aligned_columns_and_dynamic_colors():
    checked = datetime(2026, 7, 12, 20, 30, 10)
    screen = monitor.build_screen(
        {
            "model": "ornith-1.0-9b-Q4_K_M.gguf",
            "state": "LOADED",
            "slot": "BUSY",
            "task": "1294",
            "activity": "gen 934, remain 63066",
            "gpu": "98%",
            "temperature": "63C",
            "vram": "11,021 MB",
            "context": "65,536",
            "started": checked - timedelta(minutes=40),
            "checked": checked,
        },
        next_seconds=9,
        frame=2,
        width=100,
    )

    populated = [line for line in screen if line.text]
    value_starts = {
        line.text.index(value)
        for line, value in (
            (populated[1], "LOADED"),
            (populated[2], "BUSY"),
            (populated[3], "1294"),
            (populated[4], "gen 934"),
        )
    }
    assert value_starts == {monitor.VALUE_COLUMN}
    assert any(span.attribute == monitor.COLOR_GREEN for span in populated[1].spans)
    assert any(span.attribute == monitor.COLOR_YELLOW for span in populated[2].spans)
    assert any(span.attribute == monitor.COLOR_GREEN for span in populated[-1].spans)


def test_monitor_source_does_not_use_rich_live_or_ansi_sequences():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "from rich" not in source
    assert "Live(" not in source
    assert "\\x1b" not in source


def test_read_snapshot_uses_slot_context_and_generation_progress(monkeypatch, tmp_path):
    responses = {
        "http://test/health": {"status": "ok"},
        "http://test/slots": [
            {
                "is_processing": True,
                "id_task": 21616,
                "n_ctx": 65536,
                "n_prompt_tokens": 1200,
                "n_prompt_tokens_processed": 1200,
                "next_token": [{"n_decoded": 139, "n_remain": 63861}],
            }
        ],
    }
    monkeypatch.setattr(monitor, "_get_json", lambda url: responses[url])
    monkeypatch.setattr(monitor, "_gpu_metrics", lambda: ("98%", "63C", "11,021 MB"))
    monkeypatch.setattr(monitor, "_llama_start_time", lambda: None)
    (tmp_path / "state.json").write_text(
        '{"active_model":"ornith-1.0-9b"}', encoding="utf-8"
    )

    snapshot = monitor.read_snapshot("http://test", tmp_path / "state.json")

    assert snapshot["state"] == "LOADED"
    assert snapshot["slot"] == "BUSY"
    assert snapshot["task"] == "21616"
    assert snapshot["activity"] == "gen 139, remain 63861"
    assert snapshot["prompt_progress"] == "1,200/1,200"
    assert snapshot["prompt_processed"] == 1200
    assert snapshot["decoded"] == 139
    assert snapshot["context"] == "65,536"
    assert snapshot["gpu"] == "98%"


def test_read_snapshot_displays_gguf_filename_from_model_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor, "_get_json", lambda url: {"status": "ok"} if url.endswith("/health") else [])
    monkeypatch.setattr(monitor, "_gpu_metrics", lambda: ("3%", "51C", "11,029 MB"))
    monkeypatch.setattr(monitor, "_llama_start_time", lambda: None)
    (tmp_path / "state.json").write_text(
        '{"active_model":"ornith-1.0-9b",'
        '"models":[{"id":"ornith-1.0-9b",'
        '"path":"P:/packages/models/ornith-1.0-9b-Q4_K_M.gguf"}]}',
        encoding="utf-8",
    )

    snapshot = monitor.read_snapshot("http://test", tmp_path / "state.json")

    assert snapshot["model"] == "ornith-1.0-9b-Q4_K_M.gguf"


def test_update_metrics_counts_task_transition_once_and_persists(monkeypatch, tmp_path):
    metrics_file = tmp_path / "metrics.json"
    first = monitor._update_metrics(metrics_file, True, 7, 100, 40, 3)
    second = monitor._update_metrics(metrics_file, True, 7, 100, 80, 8)
    third = monitor._update_metrics(metrics_file, False, 7, 100, 80, 8)

    assert first["requests"] == 1
    assert second["requests"] == 1
    assert third["requests"] == 1
    assert second["prompt_tokens_processed"] == 80
    assert second["generated_tokens"] == 8
    assert metrics_file.exists()


def test_update_metrics_counts_busy_transition_without_task_id(tmp_path):
    metrics_file = tmp_path / "metrics.json"
    first = monitor._update_metrics(metrics_file, False, None, 0, 0, 0)
    second = monitor._update_metrics(metrics_file, True, None, 50, 10, 0)
    third = monitor._update_metrics(metrics_file, True, None, 50, 20, 2)

    assert first["requests"] == 0
    assert second["requests"] == 1
    assert third["requests"] == 1


def test_read_llama_metrics_parses_authoritative_counters(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "_get_text",
        lambda url: """# HELP llamacpp:prompt_tokens_total total
llamacpp:prompt_tokens_total 1234
llamacpp:tokens_predicted_total{model=\"ornith\"} 567
llamacpp:prompt_tokens_seconds 42.5
llamacpp:predicted_tokens_seconds 18.25
llamacpp:requests_processing 1
llamacpp:requests_deferred 2
""",
    )
    metrics = monitor._read_llama_metrics("http://test")

    assert metrics == {
        "prompt_tokens_processed": 1234.0,
        "generated_tokens": 567.0,
        "prompt_tps": 42.5,
        "generation_tps": 18.25,
        "requests_processing": 1.0,
        "requests_deferred": 2.0,
    }


def test_read_ccr_metrics_parses_bounded_request_counters(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "_get_text",
        lambda url: """# HELP ccr_requests_in_flight current
ccr_requests_in_flight 2
ccr_requests_completed_total 11
ccr_requests_failed_total 3
ccr_requests_cancelled_total 1
ccr_requests_rejected_total 4
ccr_fallbacks_total 5
ccr_quota_failures_total 6
ccr_provider_attempts_total 17
""",
    )
    metrics = monitor._read_ccr_metrics("http://test")

    assert metrics == {
        "in_flight": 2.0,
        "completed": 11.0,
        "failed": 3.0,
        "cancelled": 1.0,
        "rejected": 4.0,
        "fallbacks": 5.0,
        "quota_failures": 6.0,
        "provider_attempts": 17.0,
    }


def test_plain_snapshot_key_ignores_persistence_timestamp(tmp_path):
    metrics_file = tmp_path / "metrics.json"
    first = monitor._update_metrics(metrics_file, False, None, 0, 0, 0)
    second = monitor._update_metrics(metrics_file, False, None, 0, 0, 0)
    base = {
        "model": "ornith",
        "state": "LOADED",
        "slot": "IDLE",
        "task": "none",
        "activity": "idle",
        "gpu": "0%",
        "temperature": "49C",
        "vram": "11,000 MB",
        "context": "65,536",
        "prompt_progress": "n/a",
        "decoded": 0,
        "remaining": 0,
    }
    assert monitor._plain_snapshot_key({**base, "metrics": first}) == monitor._plain_snapshot_key({**base, "metrics": second})


def test_build_lines_hides_sampled_starts_when_ccr_metrics_present():
    """When CCR is reachable the real counters are authoritative; the
    'sampled starts' fallback field is only for when CCR is unavailable.
    Showing both creates a misleading appearance of a count that does not
    match the CCR section's zero/real values."""
    checked = datetime(2026, 7, 18, 14, 41, 17)
    lines = monitor.build_lines(
        {
            "model": "ornith-1.0-9b",
            "state": "LOADED",
            "slot": "IDLE",
            "task": "none",
            "activity": "idle",
            "gpu": "0%",
            "temperature": "50C",
            "vram": "11,100 MB",
            "context": "65,536",
            "started": checked - timedelta(seconds=8),
            "checked": checked,
            "metrics": {
                "requests": 3,
                "prompt_tokens_processed": 0,
                "generated_tokens": 0,
                "prompt_tps": 0.0,
                "generation_tps": 0.0,
                "requests_processing": 0,
                "requests_deferred": 0,
            },
            "ccr_metrics": {
                "in_flight": 0.0,
                "completed": 0.0,
                "failed": 0.0,
                "cancelled": 0.0,
                "rejected": 0.0,
                "fallbacks": 0.0,
                "quota_failures": 0.0,
            },
        },
        next_seconds=1,
        frame=0,
        width=80,
    )
    output = "\n".join(lines)

    assert "sampled starts" not in output
    assert "CCR requests" in output
    assert "in flight" in output


def test_log_startup_mode_writes_observable_line(tmp_path):
    """The startup log must record the renderer's chosen mode and the
    raw argv, so silent fallback from Win32 to plain is observable from
    outside the dashboard window."""
    state_file = tmp_path / "local-model-state.json"
    monitor._log_startup_mode(state_file, isatty=False, win32_renderer=False, argv=["--state-file", str(state_file), "--poll-seconds", "2"])

    log_path = state_file.parent / "ornith-monitor-startup.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8").strip()
    parts = content.split("\t")
    assert len(parts) == 4
    assert parts[1] == "isatty=False"
    assert parts[2] == "renderer=plain"
    assert state_file.name in parts[3]

    state_file2 = tmp_path / "local-model-state.json"
    monitor._log_startup_mode(state_file2, isatty=True, win32_renderer=True, argv=["--state-file", str(state_file2)])
    appended = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(appended) == 2
    second = appended[1].split("\t")
    assert second[1] == "isatty=True"
    assert second[2] == "renderer=Win32"
