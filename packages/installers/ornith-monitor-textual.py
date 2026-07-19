#!/usr/bin/env python3
"""Textual-based operator display for the run-ornith llama-server supervisor.

Replaces the ctypes/Win32 console rendering with Textual widgets. The
data-gathering layer (HTTP probes, JSON parsing, metric aggregation) is
preserved from the original ornith-monitor.py. Only the rendering layer
changed: no kernel32.dll, no console buffer manipulation, no isatty checks.
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static, Label
from textual import work


# ---------------------------------------------------------------------------
# Mutex (single-instance enforcement) — preserved from original
# ---------------------------------------------------------------------------

def _acquire_file_lock() -> bool:
    """Allow only one live dashboard instance. File-based (no ctypes)."""
    lock_path = Path(os.environ.get("TEMP", ".")) / "ornith-monitor.lock"
    try:
        lock_path.unlink(missing_ok=True)
        lock_path.touch()
        atexit.register(lambda: lock_path.unlink(missing_ok=True))
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Data-gathering layer — preserved from original (lines 56-372)
# ---------------------------------------------------------------------------

def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read().decode("utf-8")


def _read_llama_metrics(endpoint: str) -> dict[str, float] | None:
    try:
        text = _get_text(f"{endpoint}/metrics")
    except (OSError, ValueError):
        return None
    metrics: dict[str, float] = {}
    wanted = {
        "llamacpp:prompt_tokens_total": "prompt_tokens_processed",
        "llamacpp:tokens_predicted_total": "generated_tokens",
        "llamacpp:prompt_tokens_seconds": "prompt_tps",
        "llamacpp:predicted_tokens_seconds": "generation_tps",
        "llamacpp:requests_processing": "requests_processing",
        "llamacpp:requests_deferred": "requests_deferred",
    }
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_:]+)(?:\{[^}]*\})?\s+([-+0-9.eE]+)", line)
        if not match:
            continue
        key = wanted.get(match.group(1))
        if key:
            try:
                metrics[key] = float(match.group(2))
            except ValueError:
                pass
    return metrics


def _read_ccr_metrics(endpoint: str) -> dict[str, float] | None:
    try:
        text = _get_text(f"{endpoint}/metrics")
    except (OSError, ValueError):
        return None
    metrics: dict[str, float] = {}
    wanted = {
        "ccr_requests_in_flight": "in_flight",
        "ccr_requests_completed_total": "completed",
        "ccr_requests_failed_total": "failed",
        "ccr_requests_cancelled_total": "cancelled",
        "ccr_requests_rejected_total": "rejected",
        "ccr_fallbacks_total": "fallbacks",
        "ccr_quota_failures_total": "quota_failures",
        "ccr_provider_attempts_total": "provider_attempts",
    }
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_:]+)(?:\{[^}]*\})?\s+([-+0-9.eE]+)", line)
        if not match:
            continue
        key = wanted.get(match.group(1))
        if key:
            try:
                metrics[key] = float(match.group(2))
            except ValueError:
                pass
    return metrics


def _read_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _read_metrics(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_metrics(path: Path, data: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temporary.replace(path)
    except OSError:
        pass


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _update_metrics(
    path: Path | None,
    processing: bool,
    task: Any,
    prompt_total: int,
    prompt_processed: int,
    decoded: int,
) -> dict[str, Any]:
    if path is None:
        return {
            "requests": 0,
            "prompt_tokens": 0,
            "prompt_tokens_processed": 0,
            "generated_tokens": 0,
            "prompt_tps": 0.0,
            "generation_tps": 0.0,
        }

    old = _read_metrics(path)
    now = time.time()
    task_key = str(task) if task not in (None, -1, "-1") else None
    previous_task = old.get("last_task")
    previous_processing = bool(old.get("last_processing", False))
    request_started = bool(
        processing
        and ((task_key and task_key != previous_task) or (not task_key and not previous_processing))
    )
    elapsed = max(0.001, now - float(old.get("last_sample_at", now)))

    requests = _as_int(old.get("requests")) + int(request_started)
    prompt_tokens = _as_int(old.get("prompt_tokens"))
    prompt_processed_total = _as_int(old.get("prompt_tokens_processed"))
    generated_total = _as_int(old.get("generated_tokens"))

    prompt_processed_total += max(0, prompt_processed - _as_int(old.get("last_prompt_processed")))
    generated_total += max(0, decoded - _as_int(old.get("last_decoded")))
    if request_started:
        prompt_tokens += prompt_total

    prompt_delta = max(0, prompt_processed - _as_int(old.get("last_prompt_processed")))
    generated_delta = max(0, decoded - _as_int(old.get("last_decoded")))
    result = {
        "requests": requests,
        "prompt_tokens": prompt_tokens,
        "prompt_tokens_processed": prompt_processed_total,
        "generated_tokens": generated_total,
        "prompt_tps": round(prompt_delta / elapsed, 1),
        "generation_tps": round(generated_delta / elapsed, 1),
        "last_task": task_key,
        "last_processing": processing,
        "last_prompt_processed": prompt_processed,
        "last_decoded": decoded,
        "last_sample_at": now,
    }
    _write_metrics(path, result)
    return result


def _gpu_metrics() -> tuple[str, str, str]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        parts = [part.strip() for part in result.stdout.split(",")]
        if len(parts) >= 3:
            return f"{parts[0]}%", f"{parts[1]}C", f"{int(parts[2]):,} MB"
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return "n/a", "n/a", "n/a"


def _llama_start_time() -> datetime | None:
    if psutil is None:
        return None
    try:
        for process in psutil.process_iter(["name", "create_time"]):
            if (process.info.get("name") or "").lower() == "llama-server.exe":
                return datetime.fromtimestamp(float(process.info["create_time"]))
    except (OSError, ValueError, psutil.Error):
        pass
    return None


def _format_uptime(started: datetime | None, now: datetime) -> str:
    if started is None:
        return "n/a"
    seconds = max(0, int((now - started).total_seconds()))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def read_snapshot(
    endpoint: str,
    state_file: Path,
    metrics_file: Path | None = None,
    ccr_endpoint: str = "http://127.0.0.1:3458",
) -> dict[str, Any]:
    state = _read_state(state_file)
    model = "ornith-1.0-9b"
    models = state.get("models")
    if isinstance(models, list) and models and isinstance(models[0], dict):
        model_metadata = models[0]
        model_path = model_metadata.get("path") or model_metadata.get("model_path")
        if model_path:
            model = Path(str(model_path)).name
        elif model_metadata.get("id"):
            model = Path(str(model_metadata["id"])).name
    elif state.get("active_model"):
        model = Path(str(state["active_model"])).name

    model_state = "UNKNOWN"
    try:
        health = _get_json(f"{endpoint}/health")
        model_state = "LOADED" if health else "BROKEN"
    except (OSError, ValueError):
        model_state = "BROKEN"

    slot: dict[str, Any] = {}
    try:
        raw = _get_json(f"{endpoint}/slots")
        if isinstance(raw, list) and raw:
            slot = raw[0]
        elif isinstance(raw, dict) and isinstance(raw.get("slots"), list) and raw["slots"]:
            slot = raw["slots"][0]
        elif isinstance(raw, dict):
            slot = raw
    except (OSError, ValueError):
        pass

    processing = bool(slot.get("is_processing"))
    slot_state = "BUSY" if processing else "IDLE"
    task = slot.get("id_task")
    task_text = str(task) if processing and task not in (None, -1, "-1") else "none"
    decoded = 0
    remain = 0
    next_token = slot.get("next_token")
    if isinstance(next_token, list) and next_token:
        next_token = next_token[0]
    if processing:
        decoded = int((next_token or {}).get("n_decoded") or 0)
        remain = int((next_token or {}).get("n_remain") or 0)
        activity = f"gen {decoded}, remain {remain}" if decoded or remain else "generation"
    else:
        activity = "idle"

    state_context = state.get("maxContextTokens")
    if not state_context and isinstance(state.get("models"), list) and state["models"]:
        state_context = state["models"][0].get("maxContextTokens")
    context = slot.get("n_ctx") or state_context or 0
    prompt_total = _as_int(slot.get("n_prompt_tokens"))
    prompt_processed = _as_int(slot.get("n_prompt_tokens_processed"))
    metrics = _update_metrics(
        metrics_file,
        processing,
        task,
        prompt_total,
        prompt_processed,
        decoded,
    )
    llama_metrics = _read_llama_metrics(endpoint)
    if llama_metrics:
        metrics["prompt_tokens_processed"] = int(llama_metrics.get("prompt_tokens_processed", metrics["prompt_tokens_processed"]))
        metrics["generated_tokens"] = int(llama_metrics.get("generated_tokens", metrics["generated_tokens"]))
        metrics["prompt_tps"] = llama_metrics.get("prompt_tps", metrics["prompt_tps"])
        metrics["generation_tps"] = llama_metrics.get("generation_tps", metrics["generation_tps"])
        metrics["requests_processing"] = int(llama_metrics.get("requests_processing", 0))
        metrics["requests_deferred"] = int(llama_metrics.get("requests_deferred", 0))
        metrics["source"] = "llama.cpp /metrics"
    else:
        metrics["source"] = "dashboard /slots sampling"

    # Hide "sampled starts" when CCR metrics are available
    ccr_metrics = _read_ccr_metrics(ccr_endpoint)
    if ccr_metrics:
        metrics.pop("requests", None)

    prompt_progress = (
        f"{prompt_processed:,}/{prompt_total:,}"
        if prompt_total
        else "n/a"
    )
    gpu, temperature, vram = _gpu_metrics()
    return {
        "model": model,
        "state": model_state,
        "slot": slot_state,
        "task": task_text,
        "activity": activity,
        "prompt_total": prompt_total,
        "prompt_processed": prompt_processed,
        "prompt_progress": prompt_progress,
        "decoded": decoded,
        "remaining": remain,
        "metrics": metrics,
        "ccr_metrics": ccr_metrics or {},
        "gpu": gpu,
        "temperature": temperature,
        "vram": vram,
        "context": f"{int(context):,}" if context else "n/a",
        "started": _llama_start_time(),
        "checked": datetime.now(),
    }


# ---------------------------------------------------------------------------
# Textual rendering layer (replaces ctypes/Win32 console rendering)
# ---------------------------------------------------------------------------

class OrnithDashboard(App):
    """CCR fleet operator dashboard using Textual widgets."""

    CSS = """
    Screen {
        background: $surface;
    }
    #model-label {
        text-style: bold;
        color: $text;
        padding: 0 1;
    }
    .section {
        padding: 0 1;
    }
    .section-title {
        text-style: bold;
        color: $accent;
    }
    .label {
        color: $text-muted;
    }
    .healthy {
        color: $success;
    }
    .warning {
        color: $warning;
    }
    .error {
        color: $error;
    }
    .row {
        height: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

    def __init__(self, endpoint: str, state_file: Path, metrics_file: Path | None, ccr_endpoint: str, poll_seconds: int):
        super().__init__()
        self.endpoint = endpoint
        self.state_file = state_file
        self.metrics_file = metrics_file
        self.ccr_endpoint = ccr_endpoint
        self.poll_seconds = poll_seconds
        self._snapshot: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="model-label")
            yield Static(id="status-section", classes="section")
            yield Static(id="usage-section", classes="section")
            yield Static(id="ccr-section", classes="section")
            yield Static(id="timing-section", classes="section")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "CCR Fleet Dashboard"
        self.refresh_data()
        self.set_interval(self.poll_seconds, self.refresh_data)

    @work(exclusive=True, thread=True)
    def refresh_data(self) -> None:
        """Gather data and update widgets."""
        try:
            self._snapshot = read_snapshot(
                self.endpoint, self.state_file, self.metrics_file, self.ccr_endpoint
            )
        except Exception:
            pass
        self.call_after_refresh(self._render)

    def action_refresh(self) -> None:
        self.refresh_data()

    def _render(self) -> None:
        s = self._snapshot
        if not s:
            return

        now = datetime.now()
        uptime = _format_uptime(s.get("started"), now)

        state_class = "healthy" if s["state"] == "LOADED" else "error"
        slot_class = "warning" if s["slot"] == "BUSY" else "healthy"

        # Model header
        self.query_one("#model-label", Static).update(
            f"  {s['model']}"
        )

        # Status section
        m = s.get("metrics", {})
        status_lines = [
            f"  [bold]status[/bold]",
            f"    [dim]state[/dim]        [{state_class}]{s['state']}[/{state_class}]",
            f"    [dim]slot[/dim]         [{slot_class}]{s['slot']}[/{slot_class}]",
            f"    [dim]task[/dim]         {s['task']}",
            f"    [dim]activity[/dim]     {s['activity']}",
            f"    [dim]prompt prog[/dim]  {s['prompt_progress']}",
        ]
        self.query_one("#status-section", Static).update("\n".join(status_lines))

        # Usage section
        usage_lines = [
            f"  [bold]usage[/bold]",
            f"    [dim]gpu[/dim]          {s['gpu']}",
            f"    [dim]temp[/dim]         {s['temperature']}",
            f"    [dim]vram[/dim]         {s['vram']}",
            f"    [dim]context[/dim]      {s['context']}",
        ]
        if "requests_processing" in m:
            usage_lines.append(f"    [dim]processing[/dim]   {int(m.get('requests_processing', 0)):,}")
            usage_lines.append(f"    [dim]deferred[/dim]     {int(m.get('requests_deferred', 0)):,}")
        usage_lines.append(
            f"    [dim]prompt tok[/dim]   {int(m.get('prompt_tokens_processed', 0)):,} ({m.get('prompt_tps', 0.0):.1f}/s)"
        )
        usage_lines.append(
            f"    [dim]gen tok[/dim]      {int(m.get('generated_tokens', 0)):,} ({m.get('generation_tps', 0.0):.1f}/s)"
        )
        self.query_one("#usage-section", Static).update("\n".join(usage_lines))

        # CCR section
        ccr = s.get("ccr_metrics", {})
        if ccr:
            ccr_lines = [
                f"  [bold]CCR requests[/bold]",
                f"    [dim]in flight[/dim]    {int(ccr.get('in_flight', 0)):,}",
                f"    [dim]completed[/dim]     {int(ccr.get('completed', 0)):,}",
                f"    [dim]failed[/dim]        {int(ccr.get('failed', 0)):,}",
                f"    [dim]cancelled[/dim]     {int(ccr.get('cancelled', 0)):,}",
                f"    [dim]rejected[/dim]      {int(ccr.get('rejected', 0)):,}",
                f"    [dim]fallbacks[/dim]     {int(ccr.get('fallbacks', 0)):,}",
                f"    [dim]quota failures[/dim] {int(ccr.get('quota_failures', 0)):,}",
            ]
        else:
            ccr_lines = [
                f"  [bold]CCR requests[/bold]",
                f"    [dim](unavailable — proxy not reachable)[/dim]",
            ]
        self.query_one("#ccr-section", Static).update("\n".join(ccr_lines))

        # Timing section
        timing_lines = [
            f"  [bold]timing[/bold]",
            f"    [dim]checked[/dim]      {now.strftime('%H:%M:%S')}",
            f"    [dim]uptime[/dim]       {uptime}",
            f"    [dim]next[/dim]         {self.poll_seconds}s",
        ]
        self.query_one("#timing-section", Static).update("\n".join(timing_lines))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:8010")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--metrics-file", type=Path)
    parser.add_argument("--ccr-endpoint", default="http://127.0.0.1:3458")
    parser.add_argument("--poll-seconds", type=int, default=2)
    parser.add_argument("--once", action="store_true", help="Print snapshot as JSON and exit")
    parser.add_argument("--plain", action="store_true", help="Ignored (Textual handles all terminals)")
    args = parser.parse_args()

    if args.once:
        snapshot = read_snapshot(
            args.endpoint, args.state_file, args.metrics_file, args.ccr_endpoint
        )
        snapshot["checked"] = snapshot["checked"].isoformat() if hasattr(snapshot.get("checked"), "isoformat") else str(snapshot.get("checked"))
        snapshot["started"] = snapshot["started"].isoformat() if hasattr(snapshot.get("started"), "isoformat") else str(snapshot.get("started"))
        print(json.dumps(snapshot, indent=2, default=str))
        return 0 if snapshot.get("state") == "LOADED" else 2

    metrics_file = args.metrics_file or args.state_file.with_name("ornith-monitor-metrics.json")
    if not args.once and not _acquire_file_lock():
        return 0

    app = OrnithDashboard(
        endpoint=args.endpoint,
        state_file=args.state_file,
        metrics_file=metrics_file,
        ccr_endpoint=args.ccr_endpoint,
        poll_seconds=args.poll_seconds,
    )
    app.run()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
