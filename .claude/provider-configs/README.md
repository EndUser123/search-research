# Provider Configs

PowerShell scripts that configure Claude Code's LLM backend. Two categories:

- **Provider scripts** (`cc-*.ps1`) — point Claude Code at an alternative API provider
- **Proxy script** (`proxy.ps1`) — manage the local reverse proxy that routes subagents

---

## Provider Scripts

| Script | Command | Provider | Model Family |
|--------|---------|----------|--------------|
| `cc-bifrost.ps1` | `cc-bf [route]` | Bifrost AI Gateway | See route table below |
| `cc-glm.ps1` | `cc-glm [4\|5]` | Z.ai | glm-4.7 (default) or glm-5 |
| `cc-mm.ps1` | `cc-mm` | MiniMax | MiniMax-M2.7 |

All providers expose an Anthropic-compatible API, so Claude Code needs no modification.

### Bifrost Routes

Bifrost proxies to multiple providers via a local gateway at `http://localhost:8081/anthropic`.

| Command | Provider | Sonnet/Opus/Haiku |
|---------|----------|-----------------|
| `cc-bf` | Default (M27 + GLM-5.1) | M27 / GLM-5.1 / M27 |
| `cc-bf M27` | MiniMax | MiniMax-M2.7 all tiers |
| `cc-bf GLM-5.1` | Z.AI | glm-5.1 / glm-5.1 / glm-4.5-air |
| `cc-bf DeepSeek` or `cc-bf DSv4` | Nvidia | DSv4-flash all tiers |
| `cc-bf or-ling` or `cc-bf ling` | OpenRouter | ling-2.6-1t:free all tiers |
| `cc-bf hy3` | OpenRouter | hy3-preview:free all tiers |
| `cc-bf mistral` | OpenRouter | devstral-latest all tiers |
| `cc-bf step` | Nvidia | step-3.5-flash all tiers |
| `cc-bf gemini-lite` | Gemini | gemini-3.1-flash-lite-preview all tiers |
| `cc-bf gemini` | Gemini | gemini-3.1-flash-live-preview all tiers |
| `cc-bf gemini-pro` | Gemini | gemini-3.1-pro-preview all tiers |
| `cc-bf gpt5` or `cc-bf gh` | GitHub | gpt-5-mini all tiers |
| `cc-bf gemma` | OpenRouter | gemma-4-31b-it:free all tiers |
| `cc-bf qwen` | OpenRouter | qwen3-coder:free all tiers |

### Troubleshooting: `failed to get config for provider: not found` (or 404)

**Symptom (in Claude Code, after `cc-bf`):**
```
API Error: 500 failed to get config for provider: not found
```
or requests silently 404 with `extra_fields.provider = cerebras`.

**Root cause:** the model string `cc-bifrost.ps1` injects into Claude Code
(`ANTHROPIC_DEFAULT_{SONNET,OPUS,HAIKU}_MODEL`) must match a Bifrost routing
rule's CEL expression **exactly and case-sensitively**. When it doesn't, the
request matches no rule and falls through to the empty-CEL `cerebras` catch-all,
which has no usable config → `not found` / 404.

This happened because the CEL rules in the Bifrost DB were migrated to a
prefixed/lowercase key scheme (`mx:…`, `nv:…`, `or:…`, `ms:…`, lowercase
`glm-5.1`) but the script still injected old display names (`MiniMax-M2.7`,
`GLM-5.1`).

**The invariant:** `ANTHROPIC_DEFAULT_*_MODEL` value === a route key returned by
`bifrost_db.py --get-routes` === the literal in the rule's `cel_expression`.

**How to diagnose (independent evidence sources, no guessing):**
```powershell
# 1. Daemon up + provider keys aligned?
& "P:\.claude\provider-configs\cc-bifrost.ps1" --status

# 2. What CEL string does each rule actually require? (live API, authoritative)
curl -s http://localhost:8080/api/governance/routing-rules | `
  python -c "import sys,json;[print(r['name'],r.get('cel_expression')) for r in json.load(sys.stdin)['rules']]"

# 3. Reproduce: does the exact injected string route? (definitive)
curl -s http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" `
  -d '{\"model\":\"glm-5.1\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}'
# OK  -> extra_fields.provider = Z.AI        (string matches a rule)
# bad -> extra_fields.provider = cerebras    (fell through; string matches NO rule)
```

**The fix (already applied 2026-05-28):** `cc-bifrost.ps1` now injects
CEL-matching keys directly and no longer rewrites them. See:
- Defaults block (~line 55): Sonnet/Haiku = `mx:minimax/MiniMax-M2.7`, Opus = `glm-5.1`
- `$modelOverride` block: passes the DB route key through unchanged (no normalization)
- `c=` custom-slot block: same passthrough
- The dead `Resolve-ModelName` function (stale name-rewriting) was deleted

**If it recurs:** the rule keys drifted again. Run step 2, then set the defaults
in `cc-bifrost.ps1` to whatever `cel_expression` literals the rules now require.
Do NOT reintroduce a normalization/alias-rewrite layer in the override path —
that is exactly what caused this; `$routes` is already keyed by the live CEL keys.
A `--status` "ALL ALIGNED" is **not** sufficient — that check lowercases provider
names, so it can hide case drift; only the step-3 probe is conclusive.

### GLM and MiniMax (Direct API)

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
function cc-bf   { & "P:\.claude\provider-configs\cc-bifrost.ps1" @Args }
function cc-glm  { & "P:\.claude\provider-configs\cc-glm.ps1" @Args }
function cc-mm   { & "P:\.claude\provider-configs\cc-mm.ps1"  @Args }
function proxy   { & "P:\.claude\provider-configs\proxy.ps1"  @Args }
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
