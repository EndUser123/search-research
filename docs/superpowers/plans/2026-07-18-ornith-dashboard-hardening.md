# Ornith Dashboard Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Ornith dashboard the single production display, with fixed-region updates, honest observed-request/token metrics, and no obsolete PowerShell display implementation.

**Architecture:** `run-ornith-server.ps1` remains the lifecycle supervisor and launches the existing Python dashboard. `ornith-monitor.py` owns all operator display and persists only monotonic observation counters. Exact request accounting is explicitly not claimed until it is instrumented at the local API boundary.

**Tech Stack:** PowerShell 7, Python standard library, Win32 console APIs, llama.cpp `/health`, `/v1/models`, and `/slots` endpoints.

## Global Constraints

- Do not log prompt text, credentials, or request contents.
- Keep `-Probe` read-only and side-effect free.
- Live TTY output must repaint a fixed region; plain/log output may append.
- Metrics must be labeled as observed unless counted at the API boundary.
- Preserve the existing supervisor crash-recovery behavior.

---

### Task 1: Remove the obsolete PowerShell display path

**Files:**
- Modify: `P:/packages/installers/run-ornith-server.ps1`
- Modify: `P:/packages/installers/run-ornith-server.Tests.ps1`

**Interfaces:**
- Preserve `Get-LocalModelState`, `Start-OrnithDashboard`, and supervisor lifecycle behavior.
- Delete `Get-LocalSlotStatus`, `Format-HeartbeatLine`, and `Write-HeartbeatBlock`; the Python dashboard is the only operator display.

- [x] Delete the three unused PowerShell display functions and their formatter-focused tests.
- [x] Keep the supervisor poll limited to watchdog state and taskbar title updates.
- [x] Parse the PowerShell script and run its remaining Pester suite.

### Task 2: Harden dashboard counters and labels

**Files:**
- Modify: `P:/packages/installers/ornith-monitor.py`
- Modify: `P:/packages/installers/test_ornith_monitor.py`

**Interfaces:**
- `read_snapshot(endpoint, state_file, metrics_file=None)` returns current slot telemetry plus persisted observation metrics.
- Metrics are labeled `requests seen`, `prompt tokens processed`, and `generated tokens`; no “accepted tokens” claim is made.

- [x] Count a request on a task transition or a processing transition when no task ID is available.
- [x] Persist counters atomically and tolerate a missing/corrupt metrics file by resetting safely.
- [x] Exclude volatile persistence timestamps from the plain-output change key.
- [x] Add tests for task-ID and no-task-ID request transitions, counter persistence, prompt progress, and plain-output stability.

### Task 3: Verify the complete dashboard path

**Files:**
- Verify: `P:/packages/installers/ornith-monitor.py`
- Verify: `P:/packages/installers/run-ornith-server.ps1`
- Verify: `P:/packages/installers/llama-stop.ps1`

- [x] Run Python compilation and the available Python test runner.
- [x] Run a live `--once --plain` dashboard probe against `127.0.0.1:8010`.
- [x] Run the PowerShell parser and Pester suite.
- [x] Confirm no old PowerShell display function remains referenced.
- [x] Review the final diff for secrets, prompt-content logging, dead code, and whitespace errors.
