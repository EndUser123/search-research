---
title: "PowerShell Profile Customization Landscape"
date: 2026-08-13
tags: [powershell, shell, productivity, profile, windows]
host: both
confidence: SUPPORTED
source_quality: multi-source
---

# PowerShell Profile Customization Landscape

## Context

Researched 2026-08-13 via `/www` after optimizing the operator's PowerShell 7
profile (`D:\OneDrive\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`).
The operator's profile was purely utility-focused (encoding, PATH, ripgrep
wrapper, tool launchers) with zero interactive-experience customization.

## What people actually put in their profiles

Based on Reddit practitioner threads (r/PowerShell "what's in your $profile"
series), blog guides, and GitHub gists, the landscape clusters into 4 tiers:

### Tier 1 — PSReadLine configuration (highest value, most mentioned)

The #1 addition. PSReadLine ships with PowerShell 7 but defaults are minimal.

**History-based predictions** — ghost-text autocomplete based on command history:
```powershell
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView  # dropdown alternative
Set-PSReadLineOption -Colors @{ InlinePrediction = 'DarkGray' }
```

**History search on arrow keys** — type a prefix, UpArrow searches backward:
```powershell
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
```

**Menu completion on Tab** — cycle through completions with arrow keys instead
of sequential tab:
```powershell
Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
```

**History size + dedup:**
```powershell
Set-PSReadLineOption -MaximumHistoryCount 10000 -HistoryNoDuplicates
```

### Tier 2 — Prompt customization (oh-my-posh)

The #2 addition. Oh My Posh provides git-aware, themed prompts:

```powershell
# Install: winget install JanDeDobbeleer.OhMyPosh
# Install a Nerd Font: oh-my-posh font install meslo
oh-my-posh init pwsh --config 'jandedobbeleer' | Invoke-Expression
```

Popular themes: `jandedobbeleer` (default, git+path), `atomic` (minimal dark),
`catppuccin-mocha` (soft palette), `paradox` (powerlevel10k-like).

Alternative: Starship (Rust-based, cross-shell). posh-git (git status only).

### Tier 3 — Navigation and search tools

**zoxide** — "smart cd" that learns frequently visited directories:
```powershell
# Install: winget install ajeetdsouza.zoxide
Invoke-Expression (& { (zoxide init powershell) | Out-String })
```
Usage: `z <partial-path>` jumps to the most likely match.

**fzf** — fuzzy finder for interactive filtering:
```powershell
# Install: winget install junegunn.fzf
# Profile integration for directory fuzzy-search:
function fz { Get-ChildItem -Recurse | fzf | Set-Location }
```

### Tier 4 — Utility aliases (quality of life)

**JSON shortcuts** (widely loved on Reddit):
```powershell
Set-Alias -Name cfj -Value ConvertFrom-Json
Set-Alias -Name ctj -Value ConvertTo-Json
```

**Remove the curl alias** (PowerShell aliases curl → Invoke-WebRequest, breaking
muscle memory for real curl users):
```powershell
Remove-Item alias:curl -ErrorAction SilentlyContinue
```

**gsudo** (sudo for Windows):
```powershell
# Install: winget install gerardog.gsudo
Set-Alias sudo gsudo
```

## Non-obvious findings

1. **The `@args` no-param-block pattern for wrapper functions** — the
   operator's ripgrep wrapper avoids a `[Parameter()]` block specifically
   because PowerShell short flags (`-i`) bind to PS parameters
   (`-InformationAction`) instead of forwarding to the executable. This is a
   workspace-validated pattern, not just a blog tip.

2. **Profile load time matters** — heavy profiles (oh-my-posh + module imports)
   can add 2-5 seconds to shell startup. Deferred/async module loading via
   runspaces is the mitigation. Relevant as the operator's profile grows.

3. **`chcp 65001 > $null`** — suppresses the "Active code page: 65001" console
   noise on every shell launch. Applied this session, verified working.

## What this workspace already has (no action needed)

- UTF-8 encoding setup (PYTHONIOENCODING, OutputEncoding, chcp)
- PATH management (P:\scripts, uv tools, duplicate-check pattern)
- VS Code shell integration (guarded with TERM_PROGRAM + Get-Command)
- Ripgrep wrapper (WinGet binary, function approach with @args)
- Tool launcher functions (cc-ccr, llama-start/stop, agentgateway)
- Terminal ID mapping for hook session scoping
- Intelligent Terminal shell integration

## What was added this session (2026-08-13)

- ✅ PSReadLine configuration (predictions, history search, MenuComplete, 10K history)
- ✅ zoxide for smart directory jumping (`z <partial-path>`)
- oh-my-posh — deferred (lower value for fleet workflow; requires Nerd Font install)
- JSON aliases (cfj/ctj) — not added (low frequency for current workflow)
- curl alias removal — not added (not a friction point)

## Sources

- Reddit r/PowerShell: "What clever things do you have in your $profile?" (2025)
- Reddit r/PowerShell: "What do you folks put in your powershell profile?" (2023)
- Microsoft Learn: Set-PSReadLineOption documentation
- ohmyposh.dev: official documentation and theme gallery
- zoxide.org: installation and init guide
- timsneath profile gist (PowerShell template profile)
- gsudo GitHub: gerardog/gsudo
