#!/usr/bin/env python3
"""ANSI-free operator display for the run-ornith llama-server supervisor."""

from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

try:
    import psutil
except ImportError:  # pragma: no cover - the workspace runtime provides psutil
    psutil = None


_monitor_mutex_handle: Any = None


def _acquire_monitor_mutex() -> bool:
    """Allow only one live dashboard instance per machine."""
    global _monitor_mutex_handle
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_bool
        handle = kernel32.CreateMutexW(None, True, "Local\\OrnithMonitorDashboard")
        if not handle:
            return False
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(handle)
            return False
        _monitor_mutex_handle = handle
        atexit.register(kernel32.CloseHandle, handle)
        return True
    except (OSError, ValueError):
        return False


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read().decode("utf-8")


def _read_llama_metrics(endpoint: str) -> dict[str, float] | None:
    """Read llama.cpp's authoritative cumulative Prometheus counters."""
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
    """Read admission-proxy request lifecycle metrics, if the proxy is up."""
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
    """Persist monotonic local-request counters from the current slot sample."""
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

    # These counters reset when llama.cpp moves to a new task. Count only the
    # positive delta so a task transition or monitor restart cannot subtract
    # from totals or create a negative rate.
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
        # Replace inferred cumulative token totals/rates with llama.cpp's
        # process-owned counters. Request starts remain explicitly sampled:
        # the public metrics endpoint exposes processing/deferred gauges, not
        # a completed-request counter.
        metrics["prompt_tokens_processed"] = int(llama_metrics.get("prompt_tokens_processed", metrics["prompt_tokens_processed"]))
        metrics["generated_tokens"] = int(llama_metrics.get("generated_tokens", metrics["generated_tokens"]))
        metrics["prompt_tps"] = llama_metrics.get("prompt_tps", metrics["prompt_tps"])
        metrics["generation_tps"] = llama_metrics.get("generation_tps", metrics["generation_tps"])
        metrics["requests_processing"] = int(llama_metrics.get("requests_processing", 0))
        metrics["requests_deferred"] = int(llama_metrics.get("requests_deferred", 0))
        metrics["source"] = "llama.cpp /metrics"
    else:
        metrics["source"] = "dashboard /slots sampling"
    ccr_metrics = _read_ccr_metrics(ccr_endpoint)
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


def _clip_line(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return text[:1]
    return text[: width - 1] + "…"


COLOR_DEFAULT = 7
COLOR_GREEN = 10
COLOR_CYAN = 11
COLOR_RED = 12
COLOR_YELLOW = 14
DOMAIN_WIDTH = 9
LABEL_WIDTH = 12
VALUE_COLUMN = DOMAIN_WIDTH + LABEL_WIDTH + 2


class ColorSpan(NamedTuple):
    start: int
    length: int
    attribute: int


class ScreenLine(NamedTuple):
    text: str
    spans: tuple[ColorSpan, ...] = ()


def _clip_screen_line(line: ScreenLine, width: int) -> ScreenLine:
    text = _clip_line(line.text, width)
    spans = tuple(
        ColorSpan(span.start, min(span.length, max(0, len(text) - span.start)), span.attribute)
        for span in line.spans
        if span.start < len(text)
    )
    return ScreenLine(text, spans)


def build_screen(
    snapshot: dict[str, Any], next_seconds: int, frame: int, width: int = 120
) -> list[ScreenLine]:
    """Build the aligned dashboard and native-console color metadata."""
    heartbeat = (".", "o", "O", "o")[frame % 4]
    screen: list[ScreenLine] = []

    def row(domain: str, label: str, value: str, value_color: int = COLOR_DEFAULT) -> None:
        text = f"{domain:<{DOMAIN_WIDTH}} {label:<{LABEL_WIDTH}} {value}"
        spans: list[ColorSpan] = []
        if domain:
            spans.append(ColorSpan(0, len(domain), COLOR_CYAN))
        if label:
            spans.append(ColorSpan(DOMAIN_WIDTH + 1, len(label), COLOR_CYAN))
        if value:
            spans.append(ColorSpan(VALUE_COLUMN, len(value), value_color))
        screen.append(ScreenLine(text.rstrip(), tuple(spans)))

    state_color = COLOR_GREEN if snapshot["state"] == "LOADED" else COLOR_RED
    slot_color = COLOR_GREEN if snapshot["slot"] == "IDLE" else COLOR_YELLOW
    activity_color = COLOR_YELLOW if snapshot["slot"] == "BUSY" else COLOR_DEFAULT
    row("model", "", snapshot["model"])
    screen.append(ScreenLine(""))
    row("status", "state", snapshot["state"], state_color)
    row("", "slot", snapshot["slot"], slot_color)
    row("", "task", snapshot["task"])
    row("", "activity", snapshot["activity"], activity_color)
    row("", "prompt", snapshot.get("prompt_progress", "n/a"))
    metrics = snapshot.get(
        "metrics",
        {
            "requests": 0,
            "prompt_tokens_processed": 0,
            "generated_tokens": 0,
            "prompt_tps": 0.0,
            "generation_tps": 0.0,
        },
    )
    row("", "generated", f"{snapshot.get('decoded', 0):,}")
    row("", "remain", f"{snapshot.get('remaining', 0):,}")
    screen.append(ScreenLine(""))
    row("usage", "gpu", snapshot["gpu"])
    row("", "temp", snapshot["temperature"])
    row("", "vram", snapshot["vram"])
    row("", "context", snapshot["context"])
    ccr = snapshot.get("ccr_metrics", {})
    if not ccr:
        row("", "sampled starts", f"{metrics['requests']:,}")
    row("", "processing", f"{metrics.get('requests_processing', 0):,}")
    row("", "deferred", f"{metrics.get('requests_deferred', 0):,}")
    row("", "prompt tok", f"{metrics['prompt_tokens_processed']:,} ({metrics['prompt_tps']:.1f}/s)")
    row("", "gen tok", f"{metrics['generated_tokens']:,} ({metrics['generation_tps']:.1f}/s)")
    screen.append(ScreenLine(""))
    row("CCR requests", "in flight", f"{int(ccr.get('in_flight', 0)):,}")
    row("", "completed", f"{int(ccr.get('completed', 0)):,}")
    row("", "failed", f"{int(ccr.get('failed', 0)):,}")
    row("", "cancelled", f"{int(ccr.get('cancelled', 0)):,}")
    row("", "rejected", f"{int(ccr.get('rejected', 0)):,}")
    row("", "fallbacks", f"{int(ccr.get('fallbacks', 0)):,}")
    row("", "quota failures", f"{int(ccr.get('quota_failures', 0)):,}")
    screen.append(ScreenLine(""))
    row("timing", "checked", snapshot["checked"].strftime("%H:%M:%S"))
    row("", "uptime", _format_uptime(snapshot["started"], snapshot["checked"]))
    row("", "next", f"{max(0, next_seconds)}s")
    row("", "heartbeat", heartbeat, COLOR_GREEN)
    return [_clip_screen_line(line, width) for line in screen]


def build_lines(
    snapshot: dict[str, Any], next_seconds: int, frame: int, width: int = 120
) -> list[str]:
    """Return the aligned dashboard text without terminal control bytes."""
    return [line.text for line in build_screen(snapshot, next_seconds, frame, width)]


class _Coord(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class _SmallRect(ctypes.Structure):
    _fields_ = [
        ("Left", ctypes.c_short),
        ("Top", ctypes.c_short),
        ("Right", ctypes.c_short),
        ("Bottom", ctypes.c_short),
    ]


class _ConsoleScreenBufferInfo(ctypes.Structure):
    _fields_ = [
        ("dwSize", _Coord),
        ("dwCursorPosition", _Coord),
        ("wAttributes", wintypes.WORD),
        ("srWindow", _SmallRect),
        ("dwMaximumWindowSize", _Coord),
    ]


class WindowsConsoleRegion:
    """Rewrite a small console region via Win32 calls, never ANSI sequences."""

    def __init__(self) -> None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel32.GetStdHandle.restype = wintypes.HANDLE
        kernel32.GetConsoleScreenBufferInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_ConsoleScreenBufferInfo),
        ]
        kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
        kernel32.SetConsoleCursorPosition.argtypes = [wintypes.HANDLE, _Coord]
        kernel32.SetConsoleCursorPosition.restype = wintypes.BOOL
        kernel32.FillConsoleOutputCharacterW.argtypes = [
            wintypes.HANDLE,
            wintypes.WCHAR,
            wintypes.DWORD,
            _Coord,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.FillConsoleOutputCharacterW.restype = wintypes.BOOL
        kernel32.FillConsoleOutputAttribute.argtypes = [
            wintypes.HANDLE,
            wintypes.WORD,
            wintypes.DWORD,
            _Coord,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.FillConsoleOutputAttribute.restype = wintypes.BOOL
        kernel32.WriteConsoleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel32.WriteConsoleW.restype = wintypes.BOOL
        kernel32.WriteConsoleOutputAttribute.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.WORD),
            wintypes.DWORD,
            _Coord,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.WriteConsoleOutputAttribute.restype = wintypes.BOOL
        self._kernel32 = kernel32
        self._handle = kernel32.GetStdHandle(wintypes.DWORD(-11 & 0xFFFFFFFF))
        info = self._get_info()
        # Force the cursor to the top of a buffer tall enough to hold the
        # dashboard's full screen. The previous code stored the cursor Y
        # verbatim; if the supervisor's Start-Process opens the dashboard
        # mid-buffer (or the buffer is too short for ~32 lines starting
        # from the cursor), render() returns False on the first call and
        # the loop permanently falls back to plain-append mode.
        min_buffer_height = 50
        try:
            buffer_height = int(info.dwSize.Y)
            if buffer_height < min_buffer_height:
                window_height = int(info.srWindow.Bottom - info.srWindow.Top + 1)
                if window_height > min_buffer_height:
                    clamped_window = _SmallRect(
                        Left=int(info.srWindow.Left),
                        Top=int(info.srWindow.Top),
                        Right=int(info.srWindow.Right),
                        Bottom=int(info.srWindow.Top) + min_buffer_height - 1,
                    )
                    kernel32.SetConsoleWindowInfo(
                        self._handle, True, ctypes.byref(clamped_window)
                    )
                new_size = _Coord(int(info.dwSize.X), min_buffer_height)
                kernel32.SetConsoleScreenBufferSize(self._handle, new_size)
            kernel32.SetConsoleCursorPosition(self._handle, _Coord(0, 0))
            info = self._get_info()
        except OSError:
            # If the resize or cursor move fails, leave the cursor where it
            # is. render() will report the outcome via _first_render_outcome.
            pass
        self._top = 0
        self._default_attributes = int(info.wAttributes)
        self._last_height = 0
        self._last_lines: list[ScreenLine] = []
        self._first_render_outcome: str | None = None

    @classmethod
    def try_create(cls) -> WindowsConsoleRegion | None:
        if os.name != "nt" or not sys.stdout.isatty():
            return None
        try:
            return cls()
        except (OSError, ValueError):
            return None

    def _get_info(self) -> _ConsoleScreenBufferInfo:
        info = _ConsoleScreenBufferInfo()
        if not self._kernel32.GetConsoleScreenBufferInfo(
            self._handle, ctypes.byref(info)
        ):
            raise OSError(ctypes.get_last_error(), "GetConsoleScreenBufferInfo")
        return info

    def width(self) -> int:
        info = self._get_info()
        return max(1, int(info.srWindow.Right - info.srWindow.Left + 1))

    def render(self, lines: list[ScreenLine]) -> bool:
        try:
            info = self._get_info()
            left = int(info.srWindow.Left)
            width = max(1, int(info.srWindow.Right - info.srWindow.Left + 1))
            clipped_lines = [_clip_screen_line(line, width - 1) for line in lines]
            rows = max(self._last_height, len(clipped_lines))
            if self._top + rows >= int(info.dwSize.Y):
                self._record_first_render("buffer_too_small")
                return False
            written = wintypes.DWORD()
            for index in range(rows):
                if index < len(clipped_lines) and index < len(self._last_lines):
                    if clipped_lines[index] == self._last_lines[index]:
                        continue
                position = _Coord(left, self._top + index)
                self._kernel32.FillConsoleOutputCharacterW(
                    self._handle,
                    " ",
                    width,
                    position,
                    ctypes.byref(written),
                )
                self._kernel32.FillConsoleOutputAttribute(
                    self._handle,
                    self._default_attributes,
                    width,
                    position,
                    ctypes.byref(written),
                )
                if index < len(clipped_lines):
                    line = clipped_lines[index]
                    text = line.text
                    self._kernel32.SetConsoleCursorPosition(self._handle, position)
                    self._kernel32.WriteConsoleW(
                        self._handle,
                        text,
                        len(text),
                        ctypes.byref(written),
                        None,
                    )
                    for span in line.spans:
                        if span.length <= 0:
                            continue
                        attributes = (wintypes.WORD * span.length)(
                            *([span.attribute] * span.length)
                        )
                        self._kernel32.WriteConsoleOutputAttribute(
                            self._handle,
                            attributes,
                            span.length,
                            _Coord(left + span.start, self._top + index),
                            ctypes.byref(written),
                        )
            self._kernel32.SetConsoleCursorPosition(
                self._handle, _Coord(left, self._top + len(clipped_lines))
            )
            self._last_height = len(clipped_lines)
            self._last_lines = clipped_lines
            self._record_first_render("ok")
            return True
        except (OSError, ValueError):
            self._record_first_render("error")
            return False

    def _record_first_render(self, outcome: str) -> None:
        """Capture the outcome of the first render attempt for the startup log."""
        if self._first_render_outcome is None:
            self._first_render_outcome = outcome


def _plain_snapshot_key(snapshot: dict[str, Any]) -> tuple[Any, ...]:
    metrics = snapshot.get("metrics", {})
    ccr = snapshot.get("ccr_metrics", {})
    return (
        snapshot.get("model"),
        snapshot.get("state"),
        snapshot.get("slot"),
        snapshot.get("task"),
        snapshot.get("activity"),
        snapshot.get("gpu"),
        snapshot.get("temperature"),
        snapshot.get("vram"),
        snapshot.get("context"),
        snapshot.get("prompt_progress"),
        snapshot.get("decoded"),
        snapshot.get("remaining"),
        metrics.get("requests"),
        metrics.get("prompt_tokens_processed"),
        metrics.get("generated_tokens"),
        metrics.get("requests_processing"),
        metrics.get("requests_deferred"),
        tuple(sorted(ccr.items())),
    )


def _write_plain(lines: list[str]) -> None:
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


def _append_startup_log(state_file: Path, **fields: Any) -> None:
    """Append a tab-separated key=value log line to the dashboard's startup log.

    The log lives next to the state file. Lines are ISO-timestamped; each
    subsequent key=value pair is tab-separated. The OSError swallowing is
    deliberate: a logging failure must never prevent the dashboard from running.
    """
    log_path = state_file.parent / "ornith-monitor-startup.log"
    try:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(datetime.now().isoformat())
            for key, value in fields.items():
                handle.write(f"\t{key}={value}")
            handle.write("\n")
    except OSError:
        # Logging must never prevent the dashboard from running.
        pass


def _log_startup_mode(state_file: Path, isatty: bool, win32_renderer: bool, argv: list[str]) -> None:
    """Record the renderer's startup decision to a sibling log file.

    The dashboard can silently fall back from the in-place Win32 renderer to
    append-mode plain output when sys.stdout.isatty() returns False. That
    fallback is correct behavior, but invisible to the operator when stdout is
    also the wrong destination. Writing a single tab-separated line to a known
    state-file sibling makes the failure mode observable from outside the
    dashboard window.
    """
    _append_startup_log(
        state_file,
        isatty=isatty,
        renderer="Win32" if win32_renderer else "plain",
        argv=" ".join(argv),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:8010")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--metrics-file", type=Path)
    parser.add_argument("--ccr-endpoint", default="http://127.0.0.1:3458")
    parser.add_argument("--poll-seconds", type=int, default=2)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()

    if not sys.stdout.isatty() and not (args.once or args.plain):
        return 0

    metrics_file = args.metrics_file or args.state_file.with_name("ornith-monitor-metrics.json")
    if not args.once and not _acquire_monitor_mutex():
        return 0
    snapshot = read_snapshot(args.endpoint, args.state_file, metrics_file, args.ccr_endpoint)
    if args.once:
        _write_plain(build_lines(snapshot, 0, 0))
        return 0 if snapshot["state"] == "LOADED" else 2

    renderer = None if args.plain else WindowsConsoleRegion.try_create()
    _log_startup_mode(args.state_file, sys.stdout.isatty(), renderer is not None, sys.argv[1:])
    next_poll = time.monotonic()
    frame = 0
    last_plain_key: tuple[Any, ...] | None = None
    first_render_logged = False
    while True:
        now = time.monotonic()
        refreshed = False
        if now >= next_poll:
            snapshot = read_snapshot(args.endpoint, args.state_file, metrics_file, args.ccr_endpoint)
            next_poll = now + max(1, args.poll_seconds)
            refreshed = True
        frame = (frame + 1) % 4
        remaining = math.ceil(max(0, next_poll - time.monotonic()))
        width = renderer.width() if renderer is not None else 120
        screen = build_screen(snapshot, remaining, frame, width=width)
        if renderer is not None:
            render_ok = renderer.render(screen)
            first_outcome = renderer._first_render_outcome
            if not render_ok:
                renderer = None
            if not first_render_logged:
                first_render_logged = True
                _append_startup_log(
                    args.state_file,
                    first_render=first_outcome or "ok",
                )
        elif refreshed:
            plain_key = _plain_snapshot_key(snapshot)
            if plain_key != last_plain_key:
                _write_plain([line.text for line in screen])
                last_plain_key = plain_key
            if not first_render_logged:
                first_render_logged = True
                _append_startup_log(args.state_file, first_render="renderer_none")
        time.sleep(1)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
