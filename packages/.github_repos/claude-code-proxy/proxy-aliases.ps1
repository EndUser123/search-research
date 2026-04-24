# proxy-aliases.ps1 -- PowerShell helper functions for claude-code-proxy
# Source this in your PS7 profile:
#   . P:\packages\.mcp\claude-code-proxy\proxy-aliases.ps1

$ProxyDir = "P:\packages\.mcp\claude-code-proxy"

# ── Proxy start/stop shortcuts ────────────────────────────────────────────────
function Start-ProxyAnthropic { python "$ProxyDir\proxy_manager.py" start anthropic }
function Start-ProxyGLM       { python "$ProxyDir\proxy_manager.py" start glm }
function Start-ProxyM27       { python "$ProxyDir\proxy_manager.py" start m27 }

function Stop-ProxyAnthropic  { python "$ProxyDir\proxy_manager.py" stop anthropic }
function Stop-ProxyGLM        { python "$ProxyDir\proxy_manager.py" stop glm }
function Stop-ProxyM27        { python "$ProxyDir\proxy_manager.py" stop m27 }

function Restart-ProxyAnthropic { python "$ProxyDir\proxy_manager.py" restart anthropic }
function Restart-ProxyGLM       { python "$ProxyDir\proxy_manager.py" restart glm }
function Restart-ProxyM27       { python "$ProxyDir\proxy_manager.py" restart m27 }

# ── Status ────────────────────────────────────────────────────────────────────
function Show-ProxyStatus {
    python "$ProxyDir\proxy_manager.py" status
}

# ── Environment (sets ANTHROPIC_BASE_URL in current shell) ───────────────────
function Use-ProxyAnthropic { . "$ProxyDir\proxy-claude-env.ps1" -Mode anthropic }
function Use-ProxyGLM       { . "$ProxyDir\proxy-claude-env.ps1" -Mode glm }
function Use-ProxyM27       { . "$ProxyDir\proxy-claude-env.ps1" -Mode m27 }

# ── Help ──────────────────────────────────────────────────────────────────────
function Show-ProxyHelp {
    Write-Host @"

Claude Code Proxy — Quick Reference
====================================

WORKFLOW
  1. Start a proxy:      Start-ProxyAnthropic   (or Start-ProxyGLM / Start-ProxyM27)
  2. Set env for shell:  Use-ProxyAnthropic     (sets ANTHROPIC_BASE_URL)
  3. Launch Claude:      claude

PROXY MANAGEMENT
  Start-ProxyAnthropic    Start Anthropic proxy  (port 3001, real Claude orchestrator)
  Start-ProxyGLM          Start GLM proxy        (port 3004, GLM-5/4.7 orchestrator via z.ai)
  Start-ProxyM27          Start MiniMax proxy    (port 3005, MiniMax M2.7 orchestrator)

  Stop-ProxyAnthropic / Stop-ProxyGLM / Stop-ProxyM27
  Restart-ProxyAnthropic / Restart-ProxyGLM / Restart-ProxyM27
  Stop-All-Proxies        Stop all running proxies

ENVIRONMENT (dot-source to persist in this shell)
  Use-ProxyAnthropic      . proxy-claude-env.ps1 -Mode anthropic
  Use-ProxyGLM            . proxy-claude-env.ps1 -Mode glm
  Use-ProxyM27            . proxy-claude-env.ps1 -Mode m27
  (no -Mode arg)          . proxy-claude-env.ps1     (interactive menu)

STATUS
  Show-ProxyStatus        Show all configured proxies and running state

PYTHON CLI (same as above, more options)
  python proxy_manager.py start <name>
  python proxy_manager.py stop <name>
  python proxy_manager.py restart <name>
  python proxy_manager.py status
  python proxy_manager.py stop-all
  python proxy_manager.py --help

CONFIG FILES  (gitignored, one per LLM)
  config-anthropic.yaml   port 3001
  config-glm.yaml         port 3004
  config-m27.yaml         port 3005

API KEYS  (all read automatically from P:\.env)
  ZHIPU_API_KEY       GLM via z.ai
  MINIMAX_API_KEY     MiniMax M2.7
  GEMINI_FREE_API_KEY / GEMINI_PAID_API_KEY

"@ -ForegroundColor Cyan
}

function Stop-All-Proxies {
    python "$ProxyDir\proxy_manager.py" stop-all
}

# ── Aliases ───────────────────────────────────────────────────────────────────
Set-Alias -Name proxy-anthropic -Value Start-ProxyAnthropic -Force
Set-Alias -Name proxy-glm       -Value Start-ProxyGLM       -Force
Set-Alias -Name proxy-m27       -Value Start-ProxyM27       -Force
Set-Alias -Name proxy-status    -Value Show-ProxyStatus     -Force
Set-Alias -Name proxy-help      -Value Show-ProxyHelp       -Force

Write-Host "Claude Code Proxy aliases loaded. Run 'Show-ProxyHelp' or 'proxy-help' for reference." -ForegroundColor Green
