# Provider Configs

PowerShell scripts that configure Claude Code's LLM backend. Two categories:

- **Provider scripts** (`cc-*.ps1`) — point Claude Code at an alternative API provider
- **Proxy script** (`proxy.ps1`) — manage the local reverse proxy that routes subagents

---

## Provider Scripts

| Script | Command | Provider | Orchestrator model | Base URL |
|--------|---------|----------|--------------------|----------|
| `cc-glm.ps1` | `cc-glm [4\|5]` | Z.ai | glm-4.7 (default) or glm-5 | `https://api.z.ai/api/anthropic` |
| `cc-mm.ps1` | `cc-mm` | MiniMax | MiniMax-M2.7 | `https://api.minimax.io/anthropic` |

Both providers expose an Anthropic-compatible API, so Claude Code needs no modification.

```powershell
cc-glm       # route orchestrator to GLM-4.7, launch claude
cc-glm 5     # use GLM-5 family instead
cc-mm        # route orchestrator to MiniMax-M2.7, launch claude
```

To set env vars without launching claude (e.g. for testing):

```powershell
& "P:\.claude\provider-configs\cc-mm.ps1"
```

---

## Proxy Script

`proxy.ps1` wraps `proxy_manager.py` — the Go reverse proxy that intercepts subagent
requests and routes them to cheaper providers based on agent name.

```powershell
proxy start [N]     # start proxy for terminal N (default: 1, port 3001)
proxy stop [N]      # stop proxy for terminal N
proxy restart [N]   # stop then start
proxy status        # show all running proxies
proxy stop-all      # stop all proxies
proxy help          # show usage + port map
```

The proxy reads its config from:
`P:\packages\.mcp\claude-code-proxy\config-terminal<N>.yaml`

Subagent routing is defined under `subagents.mappings` in that file.
See that file's inline comments for benchmark rationale behind each mapping.

---

## Profile Functions (PS7)

All commands are thin wrappers defined in the PS7 profile:

```powershell
function cc-glm { & "P:\.claude\provider-configs\cc-glm.ps1" @Args }
function cc-mm  { & "P:\.claude\provider-configs\cc-mm.ps1"  @Args }
function proxy  { & "P:\.claude\provider-configs\proxy.ps1"  @Args }
```

### PowerShell Profile Location — Critical

This machine has three profile files. Only one is loaded by PS7 (`pwsh`):

| Shell | Profile path | Loaded? |
|-------|-------------|---------|
| PS7 (`pwsh`) | `C:\Users\brsth\OneDrive\Documents\PowerShell\Microsoft.PowerShell_profile.ps1` | **YES — edit this one** |
| PS5 (`powershell`) | `C:\Users\brsth\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1` | PS5 only |
| Unused | `C:\Users\brsth\Documents\PowerShell\Microsoft.PowerShell_profile.ps1` | Never loaded |

`Documents\` is redirected to OneDrive — `$HOME\Documents` ≠ `C:\Users\brsth\Documents`.
Always confirm with `pwsh -NoProfile -Command '$PROFILE'` before editing.

---

## Adding a New Provider

1. Copy `cc-mm.ps1` as a template; set `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`.
2. Add a one-liner `function cc-<name>` to the PS7 profile.
3. To route a subagent through the proxy, add an entry to `config-terminal1.yaml`
   under `subagents.mappings` and restart: `proxy restart`.
