# CCR Fleet Request Lifecycle and Operator Dashboard — Cold-Start Handoff

## Read this first

This is a handoff for a fresh LLM continuing work on the Windows `P:\` CCR/llama.cpp fleet. Preserve the existing dirty worktree. Do not reset, checkout, delete, or overwrite unrelated changes.

The immediate user-visible issue was transient terminal windows flashing open and closed. The root cause was local readiness probing in `cc-ccr.ps1`: each probe used the PowerShell call operator to launch a new `pwsh.exe`. That was changed to a redirected `.NET Process` with `UseShellExecute = false`, `CreateNoWindow = true`, and redirected stdout/stderr. The persistent minimized supervisor and the operator dashboard are separate intentional processes.

## User and operating context

- User is a solo director operating an AI-coding fleet on Windows 11.
- CCR is Claude Code Router. Normal Claude traffic should enter through the admission proxy on port `3458`.
- CCR normally listens on the configured `PORT` from `C:\Users\brsth\.claude-code-router\config.json`; current observed CCR port was `3457`, but never hard-code that assumption without checking config.
- Local llama.cpp/Ornith service listens on `http://127.0.0.1:8010`.
- The user values operational triage, accurate status, no misleading fallback claims, no prompt-content telemetry, and stable in-place dashboard rendering.

## Canonical files

### CCR launch and display

- `P:\.claude\provider-configs\cc-ccr.ps1`
  - Starts/reuses CCR.
  - Starts/reuses the admission proxy.
  - Starts the local model supervisor when needed.
  - Wires `ANTHROPIC_BASE_URL` and custom local-model variables.
  - Renders Infrastructure, Claude environment, Routing, and runtime status trees.
  - Uses the configured CCR port rather than assuming `3456`.
  - Contains the fixed hidden local probe implementation in `Invoke-LocalModelProbe`.
- `P:\.claude\provider-configs\cc-ccr.Tests.ps1`
  - Existing PowerShell tests for readiness, routing display, and admission-proxy ownership.
- `P:\.claude\provider-configs\cc-ccr-tui.ps1`
  - Interactive route configuration UI.

### Admission boundary and request ledger

- `P:\.claude\provider-configs\ccr-admission-proxy.js`
  - Canonical request boundary on port `3458`.
  - Recognizes Anthropic and OpenAI-compatible inference paths:
    `/v1/messages`, `/v1/chat/completions`, `/v1/completions`, `/completion`, `/infill`.
  - Passes health, metadata, and metrics endpoints without counting them as inference requests.
  - Generates/propagates `x-request-id`.
  - Records logical request lifecycle events and exposes Prometheus-compatible `/metrics`.
- `P:\.claude\provider-configs\ccr-request-ledger.js`
  - SQLite-backed durable summaries using Node 24 `node:sqlite`.
  - Default DB: `P:\.claude\state\ccr-request-ledger.sqlite`.
  - Uses WAL, `synchronous=NORMAL`, busy timeout, schema versioning, and bounded retention cleanup.
  - Stores summaries only; never persist prompt bodies, tool arguments, message content, API keys, or request IDs as metric labels.
- Tests:
  - `P:\.claude\provider-configs\ccr-admission-proxy.integration.test.js`
  - `P:\.claude\provider-configs\ccr-request-ledger.test.js`

### Local model and dashboard

- `P:\packages\installers\run-ornith-server.ps1`
  - Long-lived local model supervisor.
  - Starts `llama-server.exe`, writes `ornith-server.log`, updates `local-model-state.json`, and restarts on failures under its configured policy.
  - Starts the Python operator dashboard and hidden system watcher.
  - Readiness states include `DEAD`, `STUCK`, `BROKEN`, `LOADING`, `LOADED`, `READY`, and `HUNG`.
- `P:\packages\installers\ornith-monitor.py`
  - Operator dashboard for llama.cpp execution data plus a separate CCR request summary domain.
  - Must update in place; do not reintroduce repeated full-screen output or flicker.
  - llama.cpp-owned metrics remain separate from CCR logical-request counts.
- `P:\packages\installers\watch-system.ps1`
  - Background system metrics watcher.
- State/log locations:
  - `P:\.claude\state\local-model-state.json`
  - `P:\.claude\state\ccr-request-ledger.sqlite`
  - `P:\.claude\state\ccr-admission-proxy.log`
  - `P:\packages\installers\ornith-server.log`
  - `P:\packages\installers\system_watch.log`

## Architectural decisions

1. The admission proxy is the authoritative boundary for logical request counts.
2. Logical requests and provider attempts are separate concepts. CCR internal retries must not inflate logical-request totals.
3. SQLite is the source of truth for compact durable summaries; Prometheus output is an operational projection.
4. Direct traffic bypassing port `3458` is unobserved. Never reconstruct or guess it from timestamps.
5. CCR logs are diagnostic evidence, not the primary request ledger.
6. llama.cpp `/metrics` and local execution state remain authoritative for local processing/token/throughput fields.
7. Provider fallback correlation is only safe when a request ID is preserved. Uncorrelatable fallback observations must remain explicitly unjoined.
8. Healthy status should be green; branch-level labels and tree structure should remain normal white unless the value itself is an alert.
9. Readiness must distinguish “process alive,” “model loaded,” “inference responsive,” and “hung.” A live process with failed optional inference is not automatically dead.
10. Startup probes and service child processes must be hidden. The operator-facing dashboard may remain visible/minimized if that is the chosen UI.

## Request ledger behavior

Logical request outcomes:

```text
completed
failed
cancelled
rejected
upstream_unavailable
```

The ledger captures received/completed timestamps, route/model alias, bounded request size and token estimate, admission decision, response status, duration, output-token estimate where available, retry/fallback counts, and cancellation/disconnect state.

A streaming client disconnect after partial output is classified as `cancelled`.

Current important limitation: the proxy can record its own request-to-CCR attempt, but CCR’s internal fallback attempts are not automatically joined unless CCR exposes a safe correlatable request ID/event. Do not claim `ccr_fallbacks_total` is complete merely because the metric exists.

## Metrics/dashboard contract

The admission proxy exposes bounded-label metrics including:

```text
ccr_requests_received_total
ccr_requests_admitted_total
ccr_requests_completed_total
ccr_requests_failed_total
ccr_requests_cancelled_total
ccr_requests_rejected_total
ccr_requests_in_flight
ccr_provider_attempts_total
ccr_fallbacks_total
ccr_quota_failures_total
ccr_request_duration_seconds
```

The dashboard should show CCR accounting separately:

```text
CCR requests
├─ in flight
├─ completed
├─ failed
├─ cancelled
├─ rejected
├─ fallbacks
└─ quota failures
```

Local llama.cpp fields remain separate:

```text
llama.cpp
├─ processing
├─ deferred
├─ prompt tokens
├─ generated tokens
└─ throughput
```

`sampled starts` is only an explicitly labeled approximate fallback when CCR metrics are unavailable. It is not a request count.

## Terminal-window diagnosis and fix

Verified process topology at the time of the fix included:

- `run-ornith-server.ps1` as a long-lived supervisor.
- `ornith-monitor.py` as the dashboard child.
- `watch-system.ps1` as a hidden watcher child.
- CCR and admission proxy as hidden service children.
- The old `Invoke-LocalModelProbe` path using `& pwsh.exe @args`, which could create transient console hosts.

The probe was changed to `System.Diagnostics.ProcessStartInfo` with:

```powershell
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
```

Do not hide the dashboard accidentally while fixing this. If the user later asks for zero visible console windows, first decide whether the dashboard should become a real GUI/web dashboard or merely be hidden; do not silently suppress the operator surface.

Also remember that manually launching an outer command such as:

```powershell
pwsh -File P:\.claude\provider-configs\cc-ccr.ps1
```

from a GUI or non-console host can itself create a visible window. That is different from the hidden service children.

## Verification already completed

- PowerShell parser check for `cc-ccr.ps1`: passed.
- `cc-ccr.Tests.ps1`: 11 passed, 0 failed.
- JavaScript test suite across `ccr-admission-proxy.integration`, `ccr-request-ledger`, `ccr-context-shaper`, and `ccr-custom-router`: 54 passed (8 + 46 split between the proxy/ledger files and the shaper/router files).
- Python dashboard tests: 11 passed.
- Pester installer tests (`run-ornith-server.Tests.ps1`): 3 passed. The earlier "14" figure refers to a pre-refactor version of this file; it was trimmed to its current 3-test shape as part of recent work. All assertions still cover the same contract surface (operator-display delegation, single PowerShell heartbeat, side-effect-free probe).
- Python compile check passed.
- `node --check` passed for proxy/ledger.
- `git diff --check` passed.
- Live CCR/admission restart and post-start probe succeeded.
- Live admission-proxy `/metrics` returned HTTP 200.
- Live hidden local readiness probe returned `LOADED`.
- The live probe did not add a console host; the observed conhost count decreased as unrelated short-lived processes exited.

## Known risks and unfinished work

1. The worktree is dirty and contains unrelated user changes. Inspect `git status` and diffs before editing.
2. CCR internal fallback correlation remains incomplete without a safe CCR event/request-ID contract.
3. `ccr_fallbacks_total` may remain zero even when CCR internally falls back; this is a known observability boundary, not proof that no fallback occurred.
4. Provider quota semantics vary by provider. HTTP 429 and quota/rate-limit response text are detected heuristically; keep quota classification bounded and avoid persisting sensitive response bodies.
5. The dashboard is still terminal-based. In-place rendering must be preserved, but a future web/GUI operator dashboard may be more robust than manipulating console output.
6. Process-specific VRAM is not automatically a reliable llama.cpp-owned metric on every Windows/NVIDIA setup. Global GPU VRAM and llama.cpp `/metrics` should not be conflated.
7. Never label a local model `hung` solely because it is still loading or because an optional inference probe failed during startup.
8. The hidden probe implementation depends on the available PowerShell/.NET runtime supporting `ProcessStartInfo.ArgumentList`; verify runtime compatibility before porting it.

## Recommended next steps

1. Reproduce the user’s original flashing-window scenario from the actual launcher they use, not from an ad hoc terminal command.
2. Observe process creation with `Win32_Process`/parent IDs and identify any remaining transient `pwsh.exe`, `powershell.exe`, `cmd.exe`, or `conhost.exe` launchers.
3. Confirm `cc-ccr` startup, `-usage`, `-test`, and `-stop` all preserve the intended visible output and do not spawn flashes.
4. Exercise one real inference request through port `3458`; verify exactly one logical request row, terminal outcome, and correct CCR metric increments.
5. Exercise a 429/quota response and a fallback; verify quota classification and explicitly document whether the fallback is joined or unjoined.
6. Run the full JS, Python, and Pester suites after any change.
7. Only then consider changing the supervisor/dashboard window policy.

## Safe diagnostic commands

```powershell
# Current relevant process tree
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'cc-ccr|ccr-admission|run-ornith|ornith-monitor|watch-system' } |
  Select-Object ProcessId,ParentProcessId,Name,CommandLine

# CCR/admission health
Invoke-WebRequest http://127.0.0.1:3457/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3458/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3458/metrics -UseBasicParsing

# Ledger schema and rows, using Node 24
node -e "const {DatabaseSync}=require('node:sqlite'); const d=new DatabaseSync('P:/\.claude/state/ccr-request-ledger.sqlite'); console.log(d.prepare(\"select name from sqlite_master where type='table'\").all());"

# Tests
Invoke-Pester -Path P:\.claude\provider-configs\cc-ccr.Tests.ps1
node --test P:\.claude\provider-configs\ccr-request-ledger.test.js P:\.claude\provider-configs\ccr-admission-proxy.integration.test.js
python P:\packages\installers\test_ornith_monitor.py
```

## Handoff rule

Do not say “fixed,” “production-ready,” or “complete” based only on source inspection. Provide evidence from the relevant live path and tests. Separate verified facts, measurements, inferences, hypotheses, and remaining gaps in every review.
