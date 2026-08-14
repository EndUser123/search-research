---
title: "I think I messed this up.  I want to use cc-glm to use the glm script and then claude.  and cc-simple to be claude with "
date: "2026-03-14"
mode: "COPILOT"
uuid: "ed6300de-ae21-4450-ae32-ea5154c331cb"
entry_count: 1
---

## Human

I think I messed this up.  I want to use cc-glm to use the glm script and then claude.  and cc-simple to be claude with the simple arguments.

"# ----- Workspace bootstrap -----



# If launched in user home, jump to P:\\

if ($PWD.Path -eq $HOME) {

    Set-Location 'P:\\'

}



# VS Code shell integration

if ($env:TERM_PROGRAM -eq 'vscode') {

    . "$(code --locate-shell-integration-path pwsh)"

}



# ----- Claude Code helpers -----



# GLM backend wrapper (your existing script)

Set-Alias -Name p-glm -Value 'P:\\.claude\\proxy\\cc-glm.ps1'



# Simple-mode launcher (no hooks/MCP/etc.)

function cc-simple {

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

function cc-glm {

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



$env:YT_FTS_DB_PATH = 'P:\\projects\\yt-fts\\data\\subtitles.db'



# ----- API keys (session-scoped env vars) -----

# Best practice is still to keep these out of git and ideally load from a

# secrets store, but setting them in a profile is a supported pattern.[web:46][web:84][web:82]



$env:GeminiKey = "[REDACTED]"

$env:GROQ_API_KEY = "[REDACTED]"

$env:MistralKey = "[REDACTED]"

$env:OpenRouterKey = "[REDACTED]"



"

## Assistant

You’re right that it’s currently messed up: your `cc-glm` function is recursively calling itself instead of the actual GLM wrapper script, so it will infinite‑loop and never reach `claude`.[1][2]

Here’s a corrected, minimal version that matches what you described:

- `cc-glm` → run the GLM backend script, then launch Claude with any arguments.
- `cc-simple` → launch Claude in **simple** mode with the given arguments.

```powershell
# ----- Workspace bootstrap -----

if ($PWD.Path -eq $HOME) {
    Set-Location 'P:\'
}

if ($env:TERM_PROGRAM -eq 'vscode') {
    . "$(code --locate-shell-integration-path pwsh)"
}

# ----- Claude Code helpers -----

# Point this alias to your actual GLM wrapper script
Set-Alias -Name p-glm -Value 'P:\.claude\proxy\cc-glm.ps1'

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

# GLM + normal mode (equivalent to: p-glm; claude ...)
function cc-glm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $Args
    )

    # 1) Switch backend to GLM by running your wrapper script
    p-glm

    # 2) Start Claude Code with whatever args you passed
    claude @Args
}

# ----- Project-local env vars -----

$env:YT_FTS_DB_PATH = 'P:\projects\yt-fts\data\subtitles.db'

# ----- API keys (session-scoped env vars) -----
$env:GeminiKey      = "[REDACTED]"
$env:GROQ_API_KEY   = "[REDACTED]"
$env:MistralKey     = "[REDACTED]"
$env:OpenRouterKey  = "[REDACTED]"
```

Usage examples:

- Normal Claude with Anthropic backend:  
  `claude` or `claude --project .`
- GLM backend, normal (full) Claude mode:  
  `cc-glm --project .`
- Simple Claude (no MCP/hooks/etc.) on Anthropic:  
  `cc-simple --project .`
- If you want “GLM + simple” later, you can add:

  ```powershell
  function cc-glm-simple {
      param(
          [Parameter(ValueFromRemainingArguments = $true)]
          [object[]] $Args
      )

      $old = $env:CLAUDE_CODE_SIMPLE
      try {
          $env:CLAUDE_CODE_SIMPLE = '1'
          p-glm
          claude @Args
      }
      finally {
          $env:CLAUDE_CODE_SIMPLE = $old
      }
  }
  ```

Key assumption: `P:\.claude\proxy\cc-glm.ps1` is your working GLM wrapper (it should set `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`, etc., then exit).[1]

Do you also want a variant where `cc-glm` selects a specific GLM model (e.g., 4.5 vs 5) via an argument, or are you happy to let the wrapper script decide the model?  
