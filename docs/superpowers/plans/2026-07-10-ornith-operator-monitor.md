# Ornith Operator Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use task-by-task implementation with a fresh verification checkpoint after each task. Do not stage, commit, push, or reset git state.

**Goal:** Build a read-only terminal monitor for the live Ornith llama-server that presents health, model/context, GPU/VRAM, slot progress, recent inference timing, and CCR routing in one stable operator view.

**Architecture:** Add a standalone `ornith-monitor.ps1` that polls existing read-only endpoints and parses existing local logs. Keep `run-ornith-server.ps1` responsible for process lifecycle and watchdog behavior; the monitor must never restart, stop, or mutate llama-server. Use pure parsing/normalization functions so the display can be tested without a live server.

**Tech Stack:** PowerShell 7, built-in HTTP/file/process APIs, Pester 5, ANSI terminal control only when interactive. No new runtime dependency and no Prometheus dependency.

## Global Constraints

- Work directory: `P:\`.
- Allowed implementation files: `P:\packages\installers\ornith-monitor.ps1`, `P:\packages\installers\ornith-monitor.Tests.ps1`, and an optional `P:\packages\installers\README-ornith-monitor.md` only if the command contract needs documentation.
- Existing source of truth: `P:\packages\installers\run-ornith-server.ps1` and `P:\packages\installers\run-ornith-server.Tests.ps1`; read them before editing.
- Live endpoint: `http://127.0.0.1:8010`.
- Available data sources: `/health`, `/v1/models`, `/slots`, `nvidia-smi`, `P:\packages\installers\ornith-server.log.err`, and `P:\.claude\state\ccr-route-log.jsonl`.
- `/metrics` currently returns HTTP `501 Not Implemented`; do not build `/metrics` parsing into the first implementation.
- Do not modify CCR routes, `ccr-custom-router.js`, `config.json`, model arguments, watchdog restart rules, or local model state semantics.
- Do not log or display prompt text, message content, tool arguments, or secrets.
- Endpoint failure must be represented as `UNKNOWN`, `STALE`, or `N/A`; never convert a failed probe into a false healthy/idle state.
- Do not stop, restart, kill, or send inference requests to llama-server from the monitor.
- Do not stage, commit, push, reset, or overwrite unrelated working-tree changes.

## Data Contract

Every poll must produce one normalized snapshot with this shape. Missing fields are `$null` or the explicit string `UNKNOWN`; the monitor must not invent values.

```powershell
@{
  timestamp = [datetime]
  server = @{
    state = 'HEALTHY' | 'STALE' | 'UNKNOWN'
    health = $true | $false | $null
    model = [string] | $null
    contextTokens = [long] | $null
    endpoint = [string]
  }
  gpu = @{
    utilizationPercent = [int] | $null
    temperatureC = [int] | $null
    vramUsedMb = [int] | $null
    vramTotalMb = [int] | $null
    powerW = [double] | $null
  }
  slot = @{
    count = [int]
    state = 'IDLE' | 'PROMPT' | 'GENERATING' | 'UNKNOWN'
    id = [int] | $null
    task = [long] | $null
    promptTokens = [long] | $null
    promptProcessed = [long] | $null
    decodedTokens = [long] | $null
    remainingTokens = [long] | $null
    detail = [string]
  }
  performance = @{
    promptTokensPerSecond = [double] | $null
    generationTokensPerSecond = [double] | $null
    sampleAgeSeconds = [double] | $null
    source = 'llama-log' | 'derived' | 'none'
  }
  routing = @{
    requestId = [string] | $null
    backendProvider = [string] | $null
    backendModel = [string] | $null
    localUsed = $true | $false | $null
    tokenCount = [long] | $null
    decisionSource = [string] | $null
    reason = [string] | $null
  }
  diagnostics = @{
    metricsEndpoint = 'NOT_IMPLEMENTED' | 'AVAILABLE' | 'UNKNOWN'
    warnings = [string[]]
  }
}
```

## Task 1: Establish the read-only command contract

**Files:**
- Create: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`

**Interfaces:**
- Command: `pwsh -NoProfile -File P:\packages\installers\ornith-monitor.ps1 [-Endpoint <uri>] [-IntervalSeconds <int>] [-Once] [-Plain] [-NoColor]`.
- Defaults: endpoint `http://127.0.0.1:8010`, interval `2`, interactive refresh enabled unless `-Once` or output is redirected.
- `-Once` collects exactly one snapshot, renders it, and exits with code `0` when the server is reachable or `2` when all server probes fail.
- `-Plain` emits one stable snapshot without ANSI escape sequences and never clears the screen.

- [ ] Read `run-ornith-server.ps1` and its Pester tests. Record the existing `/slots` field handling and do not duplicate lifecycle behavior.
- [ ] Add parameter parsing and a `New-EmptySnapshot` function matching the data contract above.
- [ ] Add tests for `-Once` argument defaults and the empty snapshot shape without contacting the live endpoint.
- [ ] Run: `Invoke-Pester -Path P:\packages\installers\ornith-monitor.Tests.ps1 -Output Detailed`.
- [ ] Stop if the existing launcher contract requires modifying watchdog behavior; report the conflict instead of changing it.

## Task 2: Implement endpoint and hardware adapters

**Files:**
- Modify: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`

**Interfaces:**
- `Get-HealthSnapshot -Endpoint <string> -TimeoutSeconds <int>` returns `{ ok, status, detail }`.
- `Get-ModelSnapshot -Endpoint <string> -TimeoutSeconds <int>` returns `{ model, contextTokens, rawAvailable }`.
- `Get-SlotSnapshot -Endpoint <string> -TimeoutSeconds <int>` returns the normalized `slot` object and supports both `/slots` array and `{ slots: [...] }` response shapes.
- `Get-GpuSnapshot` runs `nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits` and returns the first GPU as the normalized `gpu` object. A failed command returns null fields.
- `Get-MetricsCapability -Endpoint <string>` may probe `/metrics` only to record `NOT_IMPLEMENTED` for HTTP 501; it must not parse or retry the endpoint.

- [ ] Write fixture tests first for idle slot, prompt processing, generation, empty slots, wrapped slots, malformed JSON, timeout, and HTTP failure.
- [ ] Implement the adapters with bounded timeouts and no inference requests.
- [ ] Map slot phases as follows: `is_processing=false` → `IDLE`; `n_prompt_tokens_processed < n_prompt_tokens` → `PROMPT`; otherwise → `GENERATING`.
- [ ] Preserve raw counts when present: `id_task`, `n_prompt_tokens`, `n_prompt_tokens_processed`, `next_token.n_decoded`, and `next_token.n_remain`.
- [ ] Add tests that assert a failed `/slots` call produces `UNKNOWN`, not `IDLE`.
- [ ] Run the focused Pester adapter tests and confirm all pass.

## Task 3: Add timing and routing history adapters

**Files:**
- Modify: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`

**Interfaces:**
- `Get-LlamaTimingSnapshot -LogPath <string> -AfterOffset <long>` reads only new log bytes after the previous offset and returns `{ promptTokensPerSecond, generationTokensPerSecond, sampleAgeSeconds, source, nextOffset }`.
- `Get-RouteSnapshot -RouteLogPath <string>` reads the newest valid JSONL event and returns only the routing fields in the data contract.

- [ ] Add fixtures for the existing llama-server timing format, including `prompt eval time`, `eval time`, and malformed/unrelated lines.
- [ ] Parse completed-request timing only; do not claim a live PP/TG rate from GPU utilization or from a request that has not completed.
- [ ] Calculate rates as `tokens / seconds`; return `$null` for zero or missing durations.
- [ ] Read the CCR route log defensively: skip malformed lines, never display `reason` if it contains prompt content, and do not fail the entire dashboard because the file is missing.
- [ ] Add a test proving that a route event exposes request ID/backend/token count but no prompt content.
- [ ] Run focused timing and routing tests.

## Task 4: Build the normalized snapshot and alert rules

**Files:**
- Modify: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`

**Interfaces:**
- `Get-OrnithSnapshot` calls the adapters and returns the complete data contract.
- `Get-OrnithWarnings -Snapshot <hashtable>` returns a string array.

- [ ] Implement `Get-OrnithSnapshot` with independent failure handling per data source.
- [ ] Mark server `STALE` only when a prior healthy snapshot exists and the newest health poll fails; mark it `UNKNOWN` when no healthy snapshot exists.
- [ ] Add warnings for: server probe unavailable, slot telemetry unavailable, VRAM over 95% when total is known, temperature at or above 80 C, and recent CCR local-fail-fallback routing.
- [ ] Do not add a warning for ordinary idle state.
- [ ] Add tests for healthy, stale, unknown, high-VRAM, hot-GPU, and fallback-routing snapshots.
- [ ] Run all pure snapshot and warning tests.

## Task 5: Implement the terminal renderer

**Files:**
- Modify: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`

**Interfaces:**
- `Format-OrnithScreen -Snapshot <hashtable> -NoColor` returns an array of display lines.
- `Write-OrnithScreen -Lines <string[]> -Interactive <bool>` refreshes the current terminal only when interactive; plain mode writes lines once.

The display must be compact and stable:

```text
ORNITH / LLAMA.CPP                         HEALTHY  02:14:05
Model: ornith-1.0-9b-Q4_K_M.gguf           Context: 58,982 / 65,536
GPU:  3%  54C   VRAM: 11,274 / 12,288 MB   Power: n/a

SLOT 0  IDLE
Prompt: n/a       Generated: n/a            Remaining: n/a
Last PP: 3,521 tok/s   Last TG: 68.4 tok/s  Source: llama log

CCR: llama-cpp / ornith-1.0-9b             Request: req-4
Warnings: none

Keys: q quit | p pause | l toggle recent events | r refresh
```

- [ ] Add renderer tests for fixed-width alignment, missing values, warnings, `-NoColor`, and no prompt content.
- [ ] Use ANSI cursor movement only for interactive mode; use plain output when `-Plain`, `-Once`, or stdout is redirected.
- [ ] Make idle output stable: do not print a new screen every poll when the snapshot is unchanged.
- [ ] Keep the renderer independent of network calls so it can be tested with fixtures.
- [ ] Run all renderer tests.

## Task 6: Add the polling loop and safe smoke verification

**Files:**
- Modify: `P:\packages\installers\ornith-monitor.ps1`
- Test: `P:\packages\installers\ornith-monitor.Tests.ps1`
- Optional documentation: `P:\packages\installers\README-ornith-monitor.md`

- [ ] Implement the polling loop with a `Stopwatch`-based interval and graceful Ctrl+C handling.
- [ ] Never call `Stop-Process`, `Start-Process`, launcher scripts, inference endpoints, or CCR mutation endpoints.
- [ ] Add a `-Once -Plain` smoke test path that performs one live read-only collection.
- [ ] Run:

```powershell
Invoke-Pester -Path P:\packages\installers\ornith-monitor.Tests.ps1 -Output Detailed
pwsh -NoProfile -File P:\packages\installers\ornith-monitor.ps1 -Once -Plain
```

- [ ] If the live server is unavailable, the smoke command must still produce a structured `UNKNOWN` result and exit `2`; do not start the server as part of verification.
- [ ] Verify the monitor does not append to `P:\.claude\state\ccr-route-log.jsonl` or alter `local-model-state.json`.

## Explicitly Deferred

Do not implement these in this task:

- Prometheus `/metrics` parsing until the endpoint returns HTTP 200 with a real payload.
- Prompt-cache hit percentage, KV-cache utilization percentage, token eviction/shift events, and per-slot sampling flags unless a verified data source is added.
- Multi-GPU tensor split visualization; the current deployment is a single-GPU monitor and no live split telemetry has been established.
- Automatic remediation, watchdog integration, route changes, quota changes, or model argument changes.

## Final Verification and Handoff

The implementing worker must return an evidence packet containing:

- Objective and implementation status.
- Exact files read and changed.
- Commands run with exit codes.
- Pester result with test count and failures.
- Output of `-Once -Plain` or the precise live-server blocker.
- Confirmation that no `/metrics` parser was added and no routing/watchdog behavior changed.
- Any unsupported data fields encountered.
- `git status --short` output.
- Explicit statement that no files were staged, committed, pushed, reset, deleted, or moved.

The parent agent decides whether to accept the implementation. Do not claim PP/TG, KV, or cache metrics are available unless the output source and parsing tests prove them.
