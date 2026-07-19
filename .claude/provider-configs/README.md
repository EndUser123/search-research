# Provider Configs

This directory contains the active Claude/CCR launchers and local routing helpers.

## Active commands

| Script | Invocation | Purpose |
|---|---|---|
| `cc-ccr.ps1` | `cc-ccr` | **Bring up the entire fleet** — starts/reuses CCR, admission proxy, local model supervisor, dashboard, and watcher. Wires Claude Code env vars. Shows infrastructure + fleet status + routing. |
| | `cc-ccr -Stop` | Stop CCR and admission proxy only. Leaves supervisor + llama-server + dashboard running. |
| | `cc-ccr -StopAll` | Stop the **entire fleet** — CCR, proxy, supervisor, dashboard, watcher, llama-server. Use before restarting with stale code. |
| | `cc-ccr -Usage` | **Same as `cc-ccr` (full startup) plus** provider quota gauges appended at the end. Does NOT skip startup — `-Usage` is additive. |
| | `cc-ccr -Test` | Restart CCR for a clean state, then send one real inference request through the full chain to verify routing works. |
| | `cc-ccr -Config` | Launch the interactive TUI to configure model routes. |
| `cc-ccr-tui.ps1` | `cc-ccr -Config` | Interactive route configuration UI. |
| `cc-glm.ps1` | `cc-glm` | Route Claude Code through Z.ai/GLM. |
| `cc-mm.ps1` | `cc-mm` | Route Claude Code through MiniMax. |
| `proxy.ps1` | `proxy` when configured | Manage the local subagent reverse proxy. |

### cc-ccr design contract

**`cc-ccr` is a bring-everything-up command.** It starts whatever is not running, reuses what is healthy, and restarts what is stale (the proxy auto-detects code changes via file LastWriteTime comparison). Every flag (`-Usage`, `-Test`, `-Log`) is **additive** — it adds behavior on top of the normal startup, never subtracts from it.

**Do not gate startup paths behind `-Usage` or any other flag.** If you find yourself writing `if (-not $Usage) { ...start something... }`, you are breaking the contract. See commit `1d558fe` for the revert that fixed this exact mistake.

## CCR support files

- `cc-ccr-subscription-usage.ps1` collects OpenAI and Anthropic subscription windows without API spend reporting.
- `ccr-custom-router.js` contains the custom local-first routing logic referenced by CCR configuration.
- `ccr-admission-proxy.js` — **observability and forwarding layer** (not a gate). Counts logical requests, records lifecycle events in a SQLite ledger (`ccr-request-ledger.js`), exposes Prometheus metrics on `/metrics`, and forwards all requests to CCR unchanged. The context ceiling was removed in commit `c91e058`; the proxy no longer rejects or gates requests.
- `ccr-request-ledger.js` — SQLite-backed durable request summaries (Node 24 `node:sqlite`). WAL mode, bounded retention, schema versioning. Stores summaries only — never prompt bodies, tool args, or API keys.
- `ccr-fallback-log.ps1` reads CCR fallback events and writes the audit trail.
- `ccr-custom-router.test.js` tests the custom router and admission behavior.

## Configuration

- CCR routing source of truth: `C:\Users\brsth\.claude-code-router\config.json`.
- Provider secrets source of truth: `P:\.env`.
- Confirm the active PowerShell profile with `$PROFILE` before changing aliases.

## Testing

Run the JavaScript suite with:

```powershell
$tests = Get-ChildItem P:\.claude\provider-configs -Filter '*.test.js' -File |
    Select-Object -ExpandProperty FullName
node --test $tests
```

Run the PowerShell suite with Pester 5 or newer. Pester 3 is not compatible
with the `Should -Be` assertions used by these tests:

```powershell
Get-Module -ListAvailable Pester | Sort-Object Version -Descending | Select-Object -First 1
Invoke-Pester P:\.claude\provider-configs\cc-ccr.Tests.ps1
```

Do not add API keys or subscription tokens to tracked scripts. Subscription quota collectors should use the provider's existing local login/session material and should never print credentials.
