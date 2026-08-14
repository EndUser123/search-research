---
title: "I'm getting an error trying to install the hermes desktop."
date: "2026-06-03"
mode: "CONCISE"
uuid: "09e3381e-7034-4e61-9941-6f6d0ca2324d"
entry_count: 9
---

## Human

I'm getting an error trying to install the hermes desktop.

## Assistant

The Hermes Desktop docs say the native desktop installer is for macOS and Windows, with Linux using terminal install instead, and the installer should provision Python, Node.js, ripgrep, ffmpeg, and PortableGit automatically on Windows.[1][2]

## First checks

The most common failure modes are:
- `hermes: command not found`, which usually means your shell PATH has not reloaded yet.[2][3]
- `Python version too old`, `uv: command not found`, or `node: command not found`, which the docs say the installer normally handles, but they can still appear if the environment is unusual or partially broken.[3]
- Permission issues, especially if the installer was run with `sudo` or from a locked-down folder.[3]

## What to try

On Windows, close the installer, open a fresh PowerShell window, and run `hermes doctor` if the install completed. The docs say `hermes doctor` reports exactly what is missing and how to fix it.[2]

If you are on macOS or Windows and just need the download path, use the official desktop downloads link from the docs rather than a third-party source.[1][2]

## Likely causes by platform

| Platform | Likely issue | What the docs suggest |
|---|---|---|
| Windows | PATH not refreshed, missing dependencies, or installer blocked | Reopen PowerShell and rerun `hermes doctor`; the desktop installer should install dependencies automatically. [2] |
| macOS | Shell/PATH or quarantine/signing-related launch friction | Use the signed/notarized desktop download and retry from a fresh session. [2] |
| Linux | Wrong install path | Hermes Desktop is not the primary Linux path; use the terminal installer instead. [2][1] |

## What I need from you

Paste the exact error text and tell me whether you are on Windows or macOS. With that, I can narrow it down to the specific fix instead of guessing.

## Human

bootstrap-installer.log

## Assistant

The install is failing in the repository stage because PowerShell is being invoked with an invalid `-File` argument: `P.claude-mutex.ps1` is being treated as the script path, but that file does not exist. The log shows the bootstrap succeeds through prerequisites, then consistently fails at `Configuring git for Windows compatibility` during the repository step.[1]

## What the log says

The installer successfully detects or installs `uv`, Python 3.11.14, Git, Node.js v24.11.1, ripgrep, and ffmpeg.[1]
The failure happens later, after `Installing to C-agent...` and `Configuring git for Windows compatibility...`, where PowerShell reports: `The argument P.claude-mutex.ps1 to the -File parameter does not exist.`[1]
That means this is not a missing dependency problem; it is a script-path/PowerShell invocation problem.[1]

## Most likely cause

The strongest clue is the weird `P.claude-mutex.ps1` path, which looks like a mangled or truncated filename rather than a real script name.[1]
That suggests one of these is happening:
- The installer is constructing the PowerShell command incorrectly.
- A temporary path is being rewritten or escaped badly.
- Some shell/environment setting is interfering with how the bootstrap script calls PowerShell.[1]

## What to try

1. Close the installer completely and rerun it from a fresh PowerShell session.  
2. Make sure the installer is launched from a normal user profile path, not from a synced or unusual directory.  
3. If you have any PowerShell profile scripts, temporarily disable them and retry.  
4. If the installer has a “repair” or “reinstall” option, use that after deleting the partial install at `C:\agent` if it exists.[1]

## Best next step

The most useful next step is to report this as a bootstrap bug, because the log points to an installer command construction issue rather than a local missing prerequisite.[1]
If you want, I can also help you extract the exact minimal error block from the log into a clean bug report you can paste into GitHub or support.

## Human

is there already a github issue for this?

## Assistant

Yes — there is already a public GitHub issue that looks very close to your error: **“Hermes Agent setup for Windows have something error”** (#37827). Its snippet shows a bootstrap failure in the `repository` stage on Windows, which matches the stage your log fails in, though the specific message in that issue is `git checkout main failed` rather than the exact `P.claude-mutex.ps1` PowerShell error you have.[1][2]

## What I found

The Hermes repo has multiple public install-related issues, including a Windows native install issue and a macOS installer failure, so this is not an isolated pattern.[3][4]
The closest current match to your log is the Windows setup issue #37827, because both fail during the bootstrap repository phase.[2][1]

## Important distinction

Your log points to a PowerShell invocation bug: `The argument P.claude-mutex.ps1 to the -File parameter does not exist.`[2]
The public issue I found instead reports `git checkout main failed`, so it is related but not identical; that means your case may still warrant a separate comment or new issue if the existing one does not mention this exact failure mode.[1][2]

## Best next step

A good move is to open #37827 and compare the reproduction steps, then add your log excerpt if the thread does not already mention the PowerShell `-File` path problem.[1][2]
If you want a tighter match search, I can look specifically for the exact `P.claude-mutex.ps1` string across GitHub issues and pull the closest result.

## Human

ye splease

## Assistant

I searched for the exact `P.claude-mutex.ps1` string and did **not** find a public GitHub issue matching that exact error. The closest public results I found were general Hermes Agent Windows install/bootstrap issues, but not this specific PowerShell `-File` path failure.[1][2][3]

## What this means

The absence of an exact match suggests your error may be a distinct installer bug rather than the same problem as the currently reported Windows bootstrap issues.[3][4]
The log still strongly points to the repository stage and a malformed PowerShell invocation, so your report would be useful even if there is already a nearby issue.[3]

## Best next move

Open the existing Windows issue only as a reference point, then file or comment with the exact log line: `The argument P.claude-mutex.ps1 to the -File parameter does not exist.`[4][3]
That gives maintainers the precise failure signature, which is more actionable than just saying “install failed.”[3]

## Paste-ready report

Use something like this:

> Hermes Desktop install fails on Windows during bootstrap repository stage.  
> Log repeatedly shows: `The argument P.claude-mutex.ps1 to the -File parameter does not exist.`  
> Prereqs succeed (`uv`, Python 3.11.14, Git, Node 24.11.1, ripgrep, ffmpeg), then failure occurs at `Configuring git for Windows compatibility...` / `Installing to C-agent...`.

Would you like me to format that into a full GitHub issue body with steps to reproduce, expected behavior, actual behavior, and the log excerpt?

## Human

is there an install method that doesn't use their exe?

## Assistant

Yes. The docs say you can install Hermes without the Desktop `.exe` by using the CLI installer instead. On Linux, macOS, and Windows, the install script supports `--include-desktop`, and the quickstart also documents a plain `pip install hermes-agent` path plus a git-based script install.[1][2][3]

## Options

- `pip install hermes-agent`, then optionally run `hermes postinstall`.[3]
- Git-based install: `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`. [1][3]
- Git-based install with desktop included: `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --include-desktop`. [2]
- On Windows native, the docs describe a PowerShell-installed CLI path alongside the desktop installer.[4][5]

## What fits your case

Given your desktop installer is failing in the bootstrap repository stage, the non-`.exe` route is the better fallback.[6]
If you are on Windows, the docs indicate the native installer is still supported without WSL, so you can try the CLI route instead of the GUI bootstrapper.[4]

## Practical recommendation

Use the CLI install path, then run `hermes doctor` after installation to verify everything is healthy. The docs explicitly say `hermes doctor` reports missing pieces and how to fix them.[1]

## Human

how do I start?

## Assistant

Start with the CLI, not the desktop installer: run the official native Windows PowerShell install command, then open a fresh terminal and launch `hermes`. The docs say the main entry point is `hermes`, and the setup commands you’ll use next are `hermes model`, `hermes setup`, `hermes doctor`, and `hermes gateway` if you want messaging platforms later.[1][2]

## Minimal path

1. Install Hermes. On Windows native, the docs show:
   `iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)`[2][1]
2. Close and reopen PowerShell so PATH updates take effect.[3][2]
3. Run `hermes`. That opens the interactive CLI conversation.[4][1]
4. If it asks for setup, run `hermes setup` or `hermes model` to choose a provider and model.[1][2]
5. Verify the install with `hermes doctor`.[2][1]

## If you want the shortest first test

Use this sequence:
- Install.
- Open a new terminal.
- Run `hermes --version`.
- Run `hermes`.
- If anything looks wrong, run `hermes doctor`.[5][2]

## If you want desktop later

The docs say the desktop app is separate, and the CLI install can optionally include it with `--include-desktop`. That means you can get working Hermes first, then add the desktop layer afterward.[6][2]

## One caution

There’s some inconsistency in the ecosystem about Windows support: the official Hermes docs now describe native Windows support, while some third-party guides still recommend WSL2 or say native Windows is experimental. For your case, I’d trust the official Hermes docs first.[7][3][1]

Would you like the exact Windows commands copied into a single paste block?

## Human

PowerShell 7.6.2
PS P:\> iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)

+---------------------------------------------------------+
|             * Hermes Agent Installer                    |
+---------------------------------------------------------+
|  An open source AI agent by Nous Research.              |
+---------------------------------------------------------+

[OK] Managed uv found (uv 0.11.18 (e32666915 2026-06-01 x86_64-pc-windows-msvc))
-> Checking Python 3.11...
[OK] Python found: Python 3.11.14
-> Checking Git...
[OK] Git found (The argument 'P:\.claude\hooks\bin\git-mutex.ps1' to the -File parameter does not exist. Provide the path to an existing '.ps1' file as an argument to the -File parameter. Windows PowerShell Copyright (C) Microsoft Corporation. All rights reserved.  Install the latest PowerShell for new features and improvements! [https://aka.ms/PSWindows](https://aka.ms/PSWindows) )
-> Set HERMES_GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe
-> Checking Node.js (for browser tools)...
[OK] Node.js v24.11.1 found
-> Checking ripgrep (fast file search)...
[OK] ripgrep 15.1.0 (rev af60c2de9d) found
-> Checking ffmpeg (TTS voice messages)...
[OK] ffmpeg found
-> Installing to C:\Users\brsth\AppData\Local\hermes\hermes-agent...
-> Configuring git for Windows compatibility...
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! [https://aka.ms/PSWindows](https://aka.ms/PSWindows)

-> Trying SSH clone...
The argument 'P:\.claude\hooks\bin\git-mutex.ps1' to the -File parameter does not exist. Provide the path to an existing '.ps1' file as an argument to the -File parameter.
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! [https://aka.ms/PSWindows](https://aka.ms/PSWindows)


[X] Installation failed: Cannot find path 'C:\Users\brsth\AppData\Local\hermes\hermes-agent' because it does not exist.

-> If the error is unclear, try downloading and running the script directly:
  Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1' -OutFile install.ps1
  .\install.ps1

PS P:\>

## Assistant

Start from the terminal install, not the `.exe`. The Hermes Desktop page shows Windows and macOS downloads, but it also points Linux users to “install via terminal,” and the docs say the CLI installer is the main fallback path with `hermes` as the entry point.[1][2][12]

## Recommended path

1. Use the official native Windows installer command in PowerShell:
   `iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)`[2][12]
2. Open a fresh PowerShell window after it finishes, so PATH updates apply.[13][2]
3. Run `hermes --version` to confirm the install, then `hermes` to start chatting.[14][15]
4. If you need to choose a provider or fix setup, run `hermes setup` or `hermes doctor`.[12][2]

## For your specific case

Because your desktop bootstrap is failing at the Git/PowerShell step, the terminal install is the cleaner route to get Hermes working first.[16]
The desktop app is optional; once the CLI works, you can decide whether to come back to the GUI installer later.[17][1]

## What to expect

The docs say Hermes on native Windows runs without WSL and supports the CLI, gateway, TUI, and tools natively.[12][13]
If you want the desktop layer later, the CLI installer can include it with `--include-desktop`.[17]

Would you like the exact Windows command sequence in one paste-ready block?

## Human

sure

## Assistant

Here’s the clean Windows path:

1. Open **PowerShell 7**.
2. Run this exact command:
   ```powershell
   iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
   ```
3. When it finishes, close PowerShell and open a new one.
4. Verify with:
   ```powershell
   hermes --version
   ```
5. Start Hermes with:
   ```powershell
   hermes
   ```

If you want the desktop app later, the official page still offers the Windows `.exe`, but the **terminal install** is the right fallback when the installer is failing. On the Hermes desktop page, Linux is explicitly “install via terminal,” and the official docs describe native Windows CLI support.[2][3]

One note for your specific machine: your log shows the desktop bootstrap is tripping over a bad PowerShell `-File` path during the Git compatibility step, so using the terminal install first is the safer route.[4]

Would you like the next commands for setting your model/provider after install?

## Human

that 's what I did

## Assistant

Right — and the desktop page confirms the install options are the Windows `.exe`, the macOS `.dmg`, or Linux via terminal.[1]

Given your log, the issue is not that you used the wrong install method; it’s that the installer is hitting a PowerShell path bug during the Git compatibility step, so reinstalling the same desktop `.exe` is unlikely to help until that bug is fixed.[3]

## What to do next

Use the CLI install path only if you want to avoid the desktop installer, but for your current problem the best practical move is to:
- keep the log,
- report the exact `P:\.claude\hooks\bin\git-mutex.ps1` / `P.claude-mutex.ps1` failure,
- and reference that the failure happens after prerequisites succeed and during `Configuring git for Windows compatibility...`.[3]

## Why this matters

The page shows Hermes Desktop is still the native Windows route, but your install log shows the bootstrapper is mis-invoking PowerShell, so this looks like an installer bug rather than a missing dependency on your machine.[1][3]

Would you like a paste-ready GitHub issue body based on your exact log?
