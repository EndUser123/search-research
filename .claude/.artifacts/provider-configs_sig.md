
## PACK: provider-configs
======================

## PACK INFO
=========
**Target:** `P:\.claude\provider-configs`
**Output:** `P:\.claude\.artifacts\provider-configs_sig.md`, `P:\.claude\.artifacts\provider-configs_full.md`
**Files:** 13 total (2 .py, 1 .md)

## SIGNATURE TOC
=============

### `scripts\bifrost_db.py`
- `def get_routes() -> dict`
- `def get_rules() -> list[dict]`
- `def get_status() -> dict`
- `def enable_rules() -> int`
- `def main() -> `


### `scripts\routes_probe.py`
- `def extract_model(cel) -> str | None`
- `def is_free_model(mid, pricing) -> bool`
- `def passes_filter(mid, ctx, prov, only_providers, pricing) -> bool`
- `def parse_argv_flags() -> tuple[list[str], list[str], str | None]`
- `def fetch_catalog() -> list[dict]`
- `def inject_static_models(all_models) -> list[dict]`
- `def filter_candidates(all_models, routed, only_providers, exclude_terms, include_routed) -> list[dict]`
- `def apply_latest_only(candidates, only_providers) -> list[dict]`
- `def load_latency_history() -> dict[str, list[dict]]`
- `def save_latency_history(history) -> None`
- `def record_latency(history, model, latency_ms) -> float | None`
- `def avg_latency_str(history, model) -> str`
- `def display_width(s) -> int`
- `def pad_to(s, width) -> str`
- `def ansi_width(s) -> int`
- `def pad_ansi(s, width) -> str`
- `def short_error(err) -> str`
- `def active_filters(only_providers, exclude_terms) -> str`
- `def print_unrouted(candidates, only_providers, title) -> None`
- `def print_routed(rules, only_providers) -> None`
- `def model_version(mid) -> tuple[str, float]`
- `def probe_once() -> `


## DIRECTORY / FILE INDEX
======================

### /.
- `README.md`
- `cc-bf-bench.ps1`
- `cc-bifrost.ps1`
- `cc-glm.ps1`
- `cc-mm.ps1`
- `proxy.ps1`

### /.claude\hooks\state
- `compaction_marker_console_b0504729-3e20-4988-8f51-0883bd8fa200.json`

### /.claude\state\sessions\4e6e9b0a-4c23-4337-8d58-95ee42e31f02
- `intent_state.json`

### /scripts
- `bifrost_db.py`
- `routes_probe.py`

### /scripts\.claude\hooks\state
- `compaction_marker_console_b0504729-3e20-4988-8f51-0883bd8fa200.json`

### /scripts\.claude\state\sessions\4e6e9b0a-4c23-4337-8d58-95ee42e31f02
- `intent_state.json`

### /scripts\.claude\state\sessions\e92a44d3-fa6e-4d9b-91f4-c0dbb35e47b1
- `intent_state.json`

## TOP-LEVEL MARKDOWN
==================

### `README.md`
```
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

```


---

## PS7 PROFILE: Microsoft.PowerShell_profile.ps1




---

## PS7 PROFILE




---

## PS7 PROFILE: Microsoft.PowerShell_profile.ps1

```powershell
# ----- Workspace bootstrap -----

if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# Prefer the WinGet-installed ripgrep instead of the blocked Codex-bundled copy.
$script:CodexRipgrepPath = $null

function Get-CodexRipgrepPath {
    if ($script:CodexRipgrepPath -and (Test-Path -LiteralPath $script:CodexRipgrepPath)) {
        return $script:CodexRipgrepPath
    }

    $winGetRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    $candidate = Get-ChildItem -Path $winGetRoot -Recurse -Filter rg.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like '*BurntSushi.ripgrep.MSVC*' } |
        Sort-Object FullName -Descending |
        Select-Object -First 1

    if ($candidate) {
        $script:CodexRipgrepPath = $candidate.FullName
        return $script:CodexRipgrepPath
    }

    return $null
}

function rg {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $exe = Get-CodexRipgrepPath
    if ($exe) {
        & $exe @Args
        return
    }

    Write-Error 'ripgrep is not installed. Install BurntSushi.ripgrep.MSVC with winget.'
}

# ----- Claude Code helpers -----

# Point this alias to your actual GLM wrapper script
Set-Alias -Name p-glm -Value 'P:/.claude/provider-configs/cc-glm.ps1'

# Simple-mode launcher (no hooks/MCP/etc.)
function cc-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'   # minimal system prompt, no MCP/CLAUDE.md/etc. [web:6]
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}

# GLM + normal mode (GLM-5.1 only)
# Usage: cc-glm [claude args...]
function cc-glm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    # Run GLM wrapper (sets env vars for GLM-5.1)
    p-glm

    # Start Claude with any remaining args (but NOT if no args)
    if ($Args.Count -gt 0) {
        claude @Args
    }
}

# ----- Project-local env vars -----

$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# ----- uv tool shims -----

$script:UvToolScripts = 'C:\Users\brsth\AppData\Roaming\uv\tools\notebooklm-mcp-cli\Scripts'
if ((Test-Path -LiteralPath $script:UvToolScripts) -and ($env:Path -notlike "*$script:UvToolScripts*")) {
    $env:Path = "$script:UvToolScripts;$env:Path"
}

# ----- API keys (session-scoped env vars) -----

$env:GROQ_API_KEY        = "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"
$env:MISTRAL_API_KEY     = "shuopOxLGjNjIBRBWEocfNVZpJHw8FJL"
$env:OPENROUTER_API_KEY  = "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"
$env:GITHUB_API_KEY      = "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"
$env:HF_API_KEY          = "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"
$env:CHUTES_API_KEY      = "cpk_36a85003a47e493ab0ab6cac2a5d660e.8b9e63e6374653919f5e220d9098d62c.wZjpOd615GIShkCV0yDeRAKDXaQ6BGvb"
$env:Z_AI_API_KEY        = "2cad921721204afc94eb39f25dc1ac0a.7rcNIxBWcuWkaJck"

$env:GEMINI_API_Key      = "AIzaSyB9vIPzbqLUVSq0Ha2q3EJhyIRftyXll5w"
$env:YT_API_KEY_1        = "AIzaSyBDzOLSFoV1PeRA6oH9wCeivJbZwxD5lWg"
$env:YT_API_KEY_2        = "AIzaSyBx8EXghdfnsRj1yC9fVmCIwcey6xxkV8I"
$env:YT_API_KEY_3        = "AIzaSyBKYDGhxMgOBCZEgfuTESJltobqqtojQhU"
$env:YT_API_KEY_4        = "AIzaSyAWi9E-6yF6IFbnzgBEi0uODYPmAW0Ksvk"

$env:context7_API_KEY 	 = "ctx7sk-765a1ef6-70e0-4ada-b026-8f0ff048834a"
$env:cerebras_API_KEY	 = "csk-kkfthwyvy4rtk4hyh3rjk6rfdjfh4yyyp9e9rh3edf85knx6"
$env:brave_API_KEY	 = "BSApM27yWJJglJVW9P2SKKlT2Zd1naA"
$env:exa_API_KEY	 = "28ee31e1-cec4-47b0-bc6e-2da42c34bdfa"
$env:tavily_API_KEY	 = "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"
$env:serper_API_KEY	 = "63f1739979c1df2dc8e94754dbb95151eeff8098"

function aid { & "C:\Users\brsth\.aid\bin\aid.exe" $args }
function cc-bf { & "P:\.claude\provider-configs\cc-bifrost.ps1" @Args }
function cc-mm { & "P:\.claude\provider-configs\cc-mm.ps1" @Args }

# ----- BF Compare service (LangGraph, port 8091) -----
function start-bf-stage2 {
    $servicePath = "P:\tools\mcp\bf_v3_service.py"
    if (-not (Test-Path $servicePath)) {
        Write-Host "bf_v3_service.py not found at $servicePath" -ForegroundColor Red
        return
    }
    $jobName = "bf-stage2"
    $existing = Get-Job | Where-Object { $_.Name -eq $jobName -and $_.State -eq 'Running' }
    if ($existing) {
        Write-Host "bf-stage2 already running (Job Id: $($existing.Id))" -ForegroundColor Yellow
        return
    }
    # Read VK from cc-bifrost.ps1 (which exports ANTHROPIC_API_KEY)
    $vk = & "P:/.claude/provider-configs/cc-bifrost.ps1" 2>$null
    $vk = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")
    if ([string]::IsNullOrEmpty($vk)) {
        $vk = "sk-bf-99f7318e-ad10-4ae0-8669-d9e874661853"
    }
    $env:BF_COMPARE_MODELS = "M27,GLM-5.1,DSv4-flash"
    $env:BF_TIMEOUT_MS = "120000"
    Write-Host "Starting bf-stage2 on port 8091..." -ForegroundColor Cyan
    $job = Start-Job -Name $jobName -ScriptBlock {
        param($svcPath, $vk, $compareModels, $timeoutMs, $pyPath)
        $env:BIFROST_VK = $vk
        $env:BF_COMPARE_MODELS = $compareModels
        $env:BF_TIMEOUT_MS = $timeoutMs
        Set-Location "P:/tools/mcp"
        & $pyPath -m uvicorn bf_v3_service:app --host 127.0.0.1 --port 8091
    } -ArgumentList $servicePath, $env:BIFROST_VK, "M27,GLM-5.1,DSv4-flash", "120000", "C:\Python314\python.exe"
    Start-Sleep -Seconds 3
    if ($job.State -ne 'Running') {
        Write-Host "bf-stage2 failed to start." -ForegroundColor Red
        Receive-Job $job -Keep
    } else {
        Write-Host "bf-stage2 started (Job Id: $($job.Id))" -ForegroundColor Green
        Write-Host "  Health: http://127.0.0.1:8091/health" -ForegroundColor White
        Write-Host "  Compare: POST http://127.0.0.1:8091/bf/compare" -ForegroundColor White
    }
}

function stop-bf-stage2 {
    $job = Get-Job | Where-Object { $_.Name -eq 'bf-stage2' -and $_.State -eq 'Running' }
    if (-not $job) {
        Write-Host "bf-stage2 not running." -ForegroundColor Yellow
        return
    }
    Stop-Job $job -Force -ErrorAction SilentlyContinue
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    Write-Host "bf-stage2 stopped." -ForegroundColor Green
}

# ----- Filesystem MCP server (for Bifrost routing) -----
function start-fsmcp {
    & "P:\tools\mcp\start-bifrost-stack.ps1" @Args
}

# ----- Proxy management -----

function proxy { & "P:\.claude\provider-configs\proxy.ps1" @Args }

```
