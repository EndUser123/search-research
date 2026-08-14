---
title: "are there claude code cli arguments that allow me to start without hooks?  I need a clean system to work with."
date: "2026-03-14"
mode: "COPILOT"
uuid: "4ccfc5de-b773-496a-aa4b-8a672d027b14"
entry_count: 8
---

## Human

are there claude code cli arguments that allow me to start without hooks?  I need a clean system to work with.

## Assistant

Short answer: there is currently no documented CLI flag that starts Claude Code “with hooks disabled”; hooks are controlled via settings, not command‑line arguments.[1][2][3]

## What is officially available

- The CLI reference lists flags like `--init`, `--init-only`, `-p/--print`, `--continue`, `--output-format`, etc., but nothing to skip or disable hooks on startup.[4][5][3]
- Hooks are configured and toggled through `settings.json` (global or project) or the `/hooks` UI, not via CLI.[6][2][1]
- To disable hooks, the docs say to set `"disableAllHooks": true` in your settings file or use the toggle at the bottom of the `/hooks` menu; there is explicitly “no way to disable an individual hook” besides editing config.[2][1]

## Practical ways to get a “clean” system

You effectively have three options:

1. **Global disable via settings** (affects all sessions)  
   - Edit `~/.claude/settings.json` (and any project `.claude/settings.json`) and add:  
     ```json
     {
       "disableAllHooks": true
     }
     ```  
     This disables all non‑managed hooks everywhere until you flip it back.[1][2]

2. **Project‑local clean config**  
   - In a scratch directory, create `.claude/settings.json` with *no* `hooks` section and optionally an explicit `"disableAllHooks": true`.  
   - Start Claude Code in that directory; it will only see that minimal config for the project scope.[6][2]

3. **Separate user profile / settings tree** (heavier, but fully isolated)  
   - If you want to truly separate “hooked” and “clean” work, create a wrapper script that:
     - Sets a different `HOME` or `XDG_CONFIG_HOME` pointing at an alternate config directory that has plain `settings.json` with no hooks.
     - Then runs `claude` inside that environment.  
   - This leverages the fact that Claude Code loads settings from well‑defined locations; changing those locations effectively gives you a second profile.[2][1]

There is ongoing community desire for a `--no-hooks` style flag, but as of the latest docs and discussions it has not been added; the recommended path is settings‑based disabling instead.[7][8][1]

Would you prefer a minimal wrapper script approach (e.g., PowerShell/bash launcher that guarantees a clean profile), or are you okay with flipping `disableAllHooks` in your current `settings.json` when you need a clean session?  

## Human

I thought there was a new command like 'simple'.

## Assistant

You’re remembering **simple mode**, but it’s not a `claude simple` subcommand; it’s an environment toggle that changes which tools are available and does, in practice, give you a “no hooks” environment.[1]

## What “simple mode” actually is

- Recent updates added a *simple mode* that you enable via an environment variable, not a CLI flag or command name.[1]
- In simple mode, Claude Code exposes only a very small tool set (bash + file edit) and explicitly disables MCP tools, attachments, hooks, and Claw.[1]

Concretely, from what’s documented/shown:

- There is an environment variable like `CLAUDE_CODE_SIMPLE` (spelled in the video as `claude_code_simple` env var) that, when set, runs Claude Code in simple mode.[1]
- When that variable is set:
  - Only Bash and file-edit tools are available.[1]
  - Hooks do not run at all.[1]

So to approximate what you want (clean, no hooks) you can run something like:

```bash
# bash / zsh
export CLAUDE_CODE_SIMPLE=1
claude
```

```powershell
$env:CLAUDE_CODE_SIMPLE = "1"
claude
```

Then clear it when you’re done:

```powershell
Remove-Item Env:CLAUDE_CODE_SIMPLE
```

Docs haven’t yet added a `--simple` or `--no-hooks` flag; the only hook-related flag proposal I see is a still-open `--no-hooks` feature request. Simple mode via env var is currently the closest “clean system” switch that also suppresses hooks.[2]

Do you want a small cross‑shell launcher script that always starts Claude in simple mode for a given project, so you can keep your regular sessions fully hooked?  

## Human

how do I set that variable in powershell before I launch claude?

## Assistant

In PowerShell you set it on the `$env:` drive before running `claude`, so it’s visible to that process.[1]

## One-off for the current PowerShell session

Run this in the same PowerShell where you’ll launch Claude:

```powershell
$env:CLAUDE_CODE_SIMPLE = "1"
claude
```

That starts Claude in simple mode (clean, no hooks/MCP/etc.). The variable only lives for that PowerShell session; closing the window forgets it.[2][1]

If you want to go back to normal **within** the same session, you can clear it:

```powershell
Remove-Item Env:CLAUDE_CODE_SIMPLE
# or
$env:CLAUDE_CODE_SIMPLE = $null
```

## Make a tiny launcher function (optional)

Add this to your PowerShell profile so you can just type `claude-simple`:

```powershell
function claude-simple {
    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = "1"
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}
```

Then just run:

```powershell
claude-simple
```

Do you usually start Claude via `claude`, `npx claude`, or through a specific `.ps1` shim on Windows? That slightly affects how I’d wrap it.  

## Human

Like this?  Can this be organized better?
"# Auto-switch to P:\\ workspace if launched from user home

if ($PWD.Path -eq $HOME) {

    Set-Location "P:\\"

}



if ($env:TERM_PROGRAM -eq "vscode") { . "$(code --locate-shell-integration-path pwsh)" }



# Unblock Claude Code proxy scripts

$proxyScripts = @(

    'P:\\.claude\\proxy\\cc_z_ai.ps1',

    'P:\\.claude\\proxy\\cc_selector.ps1'

)

foreach ($script in $proxyScripts) {

    if (Test-Path $script) {

        Unblock-File -Path $script -ErrorAction SilentlyContinue

    }

}



# Claude Code Proxy Aliases

Set-Alias -Name cc-glm -Value 'P:\\.claude\\proxy\\cc-glm.ps1'



# Use function wrapper for cc-selector (direct alias doesn't work)

function cc-selector {

    & 'P:\\.claude\\proxy\\cc_selector.ps1'

}



# yt-fts: Use project-local database

$env:YT_FTS_DB_PATH = "P:\\projects\\yt-fts\\data\\subtitles.db"





$env:GeminiKey = "[REDACTED]"

$env:GROQ_API_KEY = "[REDACTED]"

$env:MistralKey = "[REDACTED]"

$env:OpenRouterKey = "[REDACTED]"

$env:PerplexityKey = "[REDACTED]"





function claude-simple {

    $old = $env:CLAUDE_CODE_SIMPLE

    try {

        $env:CLAUDE_CODE_SIMPLE = "1"

        claude @Args

    }

    finally {

        $env:CLAUDE_CODE_SIMPLE = $old

    }

}

"

## Assistant

Functionally, yes; structurally and security‑wise, it can be organized much better.[1][2]

Below is a cleaned‑up version, then notes on why.

```powershell
# ----- Workspace bootstrap -----

# If launched in user home, jump to P:\
if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

# VS Code shell integration (only when in VS Code)
if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# ----- Claude Code proxy + simple mode -----

# Unblock Claude Code proxy scripts if present
$ccProxyRoot = 'P:\.claude\proxy'
$proxyScripts = @(
    Join-Path $ccProxyRoot 'cc_z_ai.ps1'
    Join-Path $ccProxyRoot 'cc_selector.ps1'
)

foreach ($script in $proxyScripts) {
    if (Test-Path $script) {
        Unblock-File -Path $script -ErrorAction SilentlyContinue
    }
}

# Proxy alias (GLM)
Set-Alias -Name cc-glm -Value (Join-Path $ccProxyRoot 'cc-glm.ps1')

# Wrapper for cc-selector (alias to script with params can be finicky)
function cc-selector {
    & (Join-Path $ccProxyRoot 'cc_selector.ps1') @Args
}

# Simple-mode launcher for Claude (no hooks/MCP/etc.)
function claude-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}

# ----- Project-local env vars -----

# yt-fts uses project-local DB
$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# ----- API keys (strongly recommend moving these out of the profile) -----
# TODO: load from a secure secrets store or separate, gitignored file
# Import-Module Microsoft.PowerShell.SecretManagement
# $env:GeminiKey      = (Get-Secret -Name 'GeminiKey'      -AsPlainText)
# $env:GROQ_API_KEY   = (Get-Secret -Name 'GROQ_API_KEY'   -AsPlainText)
# $env:MistralKey     = (Get-Secret -Name 'MistralKey'     -AsPlainText)
# $env:OpenRouterKey  = (Get-Secret -Name 'OpenRouterKey'  -AsPlainText)
# $env:PerplexityKey  = (Get-Secret -Name 'PerplexityKey'  -AsPlainText)
```

### Key improvements

- Grouped sections with comments: workspace bootstrap, Claude stuff, project env, secrets, which matches typical profile best practice.[3][1]
- Centralized the proxy root (`$ccProxyRoot`) and used `Join-Path` so you don’t repeat the raw `P:\.claude\proxy\...` string and can change it once.[4]
- `claude-simple` now accepts and forwards arbitrary args correctly via a param block and `ValueFromRemainingArguments` (helps if you start using `claude-simple /bug` etc. later).[5]
- Left API keys but clearly marked them as “move to SecretManagement / vault” because embedding live keys in a profile is a huge foot‑gun if this ever gets shared or checked in.[6][7][8]

If you tell me whether those keys are ever needed **outside** Claude (e.g., used by other tools), I can sketch a secrets‑loading pattern that still keeps your `claude-simple` flow trivial.  

## Human

we don't need the proxy anymore.

why doesn't the claude-simple look like the cc-glm alias?

## Assistant

Two things:

1. Yes, you can drop all the proxy bits now if you’re on native Claude Code.  
2. `claude-simple` is a **function** instead of a `Set-Alias` on purpose, because aliases can’t “bake in” environment-variable changes or default arguments safely; functions can.[1][2][3]

### Why not just `Set-Alias claude-simple 'claude ...'`?

PowerShell aliases are just alternate names for an existing command; they cannot include logic like “set this env var, then run claude, then restore the old value.” They also can’t encapsulate default parameters in the middle the way bash aliases do.[2][4][3][1]

By contrast, a function:

- Can change `$env:CLAUDE_CODE_SIMPLE` before `claude` starts and then restore the previous value in `finally`.  
- Can accept and forward arbitrary arguments (`@Args`) while still wrapping that extra logic.[5][1]

That’s why `claude-simple` needs to be a function, not a raw alias, while `cc-glm` can be a `Set-Alias` because it just points at a script that already does all the env juggling.

### Minimal, organized version without proxy

Given you don’t need the proxy anymore, I’d slim your profile to:

```powershell
# If launched in user home, jump to P:\
if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

# VS Code shell integration
if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# Simple-mode launcher for Claude
function claude-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}

# Project-local env vars
$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# TODO: load API keys from secure store rather than hardcoding here
```

If you want `cc-glm` behaviour for simple mode, we can also make a tiny `claude-simple.ps1` in your `%USERPROFILE%\.local\bin` (or similar) and then use `Set-Alias claude-simple 'path\to\claude-simple.ps1'`, mirroring your GLM setup. Do you prefer the profile‑function approach or a separate `claude-simple.ps1` script on PATH?[6]

## Human

we still need the cc-glm part

## Assistant

Right, so we want to keep GLM and add simple‑mode, without the old proxy clutter.

Conceptually, `cc-glm` is just an alias to a wrapper script, while `claude-simple` needs inline logic (set env var, run, restore). Aliases can’t do that safely, which is why they look different.[1][2]

Here’s a tight profile version that keeps GLM and adds simple mode:

```powershell
# If launched in user home, jump to P:\
if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

# VS Code shell integration
if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# ----- Claude Code helpers -----

# GLM wrapper alias (points to your existing GLM script)
Set-Alias -Name cc-glm -Value 'P:\.claude\proxy\cc-glm.ps1'

# Simple-mode launcher (no hooks / MCP, etc.)
function claude-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}

# ----- Project-local env vars -----

$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# TODO: load API keys from a secrets store instead of hardcoding
```

- `cc-glm` stays a **Set-Alias** because the GLM logic lives inside `cc-glm.ps1`; the alias just points to it.[3][4]
- `claude-simple` must be a **function** because it needs to set and restore `CLAUDE_CODE_SIMPLE` around `claude` itself; an alias cannot wrap that behavior.[2][1]

If you’d like `cc-glm` to also run in simple mode (no hooks, GLM backend), I can show a combined wrapper that composes both behaviors.  

## Human

can we add a claude-glm?  normally I would do 'cc-glm', then 'claude'.

## Assistant

Yes. Make `claude-glm` a thin function that wraps `cc-glm` (to swap the backend) and then launches `claude` (optionally in simple mode).

Here are two variants; pick the one that matches how you want it to behave.

## Option 1: `claude-glm` with normal (full) mode

```powershell
# Existing GLM wrapper alias
Set-Alias -Name cc-glm -Value 'P:\.claude\proxy\cc-glm.ps1'

function claude-glm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    # Switch Claude Code to GLM backend
    cc-glm

    # Then start Claude with whatever settings/hooks are active
    claude @Args
}
```

Usage:

```powershell
claude-glm
claude-glm /bug
```

This is equivalent to `cc-glm; claude`, just in one command.

## Option 2: `claude-glm` in “clean” simple mode

If you want `claude-glm` to always be GLM **and** simple (no hooks/MCP):

```powershell
Set-Alias -Name cc-glm -Value 'P:\.claude\proxy\cc-glm.ps1'

function claude-glm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    # Remember previous simple-mode state
    $oldSimple = $env:CLAUDE_CODE_SIMPLE
    try {
        # Force simple mode for this run
        $env:CLAUDE_CODE_SIMPLE = '1'

        # Switch backend
        cc-glm

        # Launch Claude
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $oldSimple
    }
}
```

You can keep `claude-simple` as a separate helper alongside this:

```powershell
function claude-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}
```

Would you rather have `claude-glm` default to simple (clean) mode or to full mode with your normal hooks and tools?  

## Human

ok, so we can have 'cc-glm', 'claude-glm', and 'claude-simple', and hte api keys?

## Assistant

Yes, you can have all of those: `cc-glm` (alias), `claude-glm` (function), `claude-simple` (function), plus API keys set in the profile.

Here’s a compact, organized profile snippet that does exactly that:

```powershell
# ----- Workspace bootstrap -----

# If launched in user home, jump to P:\
if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

# VS Code shell integration
if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# ----- Claude Code helpers -----

# GLM backend wrapper (your existing script)
Set-Alias -Name cc-glm -Value 'P:\.claude\proxy\cc-glm.ps1'

# Simple-mode launcher (no hooks/MCP/etc.)
function claude-simple {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    $old = $env:CLAUDE_CODE_SIMPLE
    try {
        $env:CLAUDE_CODE_SIMPLE = '1'
        claude @Args
    }
    finally {
        $env:CLAUDE_CODE_SIMPLE = $old
    }
}

# GLM + normal mode (equivalent to: cc-glm; claude)
function claude-glm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    cc-glm      # switch backend to GLM
    claude @Args
}

# If you’d rather GLM always be simple/clean, use this instead:
# function claude-glm {
#     param(
#         [Parameter(ValueFromRemainingArguments = $true)]
#         [object[]] $Args
#     )
#     $old = $env:CLAUDE_CODE_SIMPLE
#     try {
#         $env:CLAUDE_CODE_SIMPLE = '1'
#         cc-glm
#         claude @Args
#     }
#     finally {
#         $env:CLAUDE_CODE_SIMPLE = $old
#     }
# }

# ----- Project-local env vars -----

$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# ----- API keys (session-scoped env vars) -----
# Best practice is still to keep these out of git and ideally load from a
# secrets store, but setting them in a profile is a supported pattern.[web:46][web:84][web:82]

$env:GeminiKey      = 'YOUR_GEMINI_KEY'
$env:GROQ_API_KEY   = 'YOUR_GROQ_KEY'
$env:MistralKey     = 'YOUR_MISTRAL_KEY'
$env:OpenRouterKey  = 'YOUR_OPENROUTER_KEY'
$env:PerplexityKey  = 'YOUR_PERPLEXITY_KEY'
# Optionally:
# $env:ANTHROPIC_API_KEY = 'YOUR_ANTHROPIC_KEY'  # if you ever go API-based[web:35][web:82]
```

This gives you:

- `cc-glm` to configure GLM backend once (as today).  
- `claude-glm` to do “cc-glm; claude” in one shot (with or without simple mode depending on which version you choose).  
- `claude-simple` for Anthropic backend in clean/simple mode.  
- API keys available as environment variables for Claude Code and any other tools that expect them.[1][2][3]

Do you want `claude-glm` to default to **simple** mode (clean, no hooks) or **full** mode (your usual hooks and MCP)?  
