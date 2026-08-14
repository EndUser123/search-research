---
title: "how can I open a second claude desktop app with a different account?"
date: "2026-06-05"
mode: "COPILOT"
uuid: "495d45b6-c5ed-4934-bd9b-91faaa092e6a"
entry_count: 5
---

## Human

how can I open a second claude desktop app with a different account?

## Assistant

Claude Desktop does **not** officially support two simultaneous accounts in one app; the supported path is switching accounts in the account menu, not running a second logged-in profile inside the same instance. Claude’s help center says if you have multiple Claude accounts tied to the same email, you can switch by clicking your initials in the lower-left corner and selecting the other account.[1]

## What you can do
- **Officially supported:** sign out/switch accounts inside Claude Desktop.[1]
- **If you need two accounts open at once:** use a separate app instance with isolated app data. Community reports show this is possible on macOS by launching Claude with a separate `--user-data-dir`, which creates a distinct profile and login state.[2]
- **On Windows:** community guides use the same idea by isolating each install/profile so each account has separate config and auth state.[3]

## Practical macOS approach
A commonly reported method is to quit Claude, then launch a second instance with a different profile directory, for example:  
`open -n -a "Claude" --args --user-data-dir="$HOME/Library/Application Support/Claude-Work"`[2][1]
That gives the second window its own login session so you can sign into a different account without affecting the first.[1][2]

## Important caveat
This is **not** documented as an official Claude Desktop feature, so it may break with updates or behave inconsistently. If your real goal is just to use both accounts, the lowest-risk option is to switch accounts from the sidebar menu; if your goal is side-by-side simultaneous use, the separate-profile workaround is the usual route.[2][1]

Would you like the exact steps for **macOS** or **Windows**?

## Human

windows

## Assistant

On Windows, the practical way to run a second Claude Desktop instance with a different account is to create a separate app/profile state so each instance has its own login data.[1][2]

## Best path on Windows
- **Don’t rely on the normal app switcher.** Claude Desktop is generally single-login, so switching accounts in one instance is the default behavior rather than true parallel accounts.[3]
- **Use separate profile data for each instance.** Community guidance for Windows does this by faking a separate home/profile directory per account so each launch gets its own `~\.claude.json` and related config.[1]
- **Launch each profile separately.** The same source describes creating two launch paths, such as `claude-work` and `claude-personal`, each pointing at a different profile directory.[1]

## What that looks like
A workable pattern is:
1. Create two separate folders, one per account profile, for example `C:\Users\<you>\.claude-split\.claude-personal\` and `C:\Users\<you>\.claude-split\.claude-work\`.[1]
2. Start Claude in a context where `USERPROFILE` points at the chosen folder, so the app stores auth and config there instead of sharing one set of files.[1]
3. Open one instance for personal and another for work; each should keep its own session state.[1]

## Caveats
This is a **workaround**, not an official multi-account feature, so updates may break it. The same Windows guide also notes some side effects around tools that expect a normal Windows profile, and it suggests symlinks or elevated PowerShell in some setups to smooth that over.[1]

## Safer alternative
If you only need to use both accounts occasionally, the safer approach is still to log out and switch accounts in the app, because that’s the supported flow described in Claude’s help center. If you need them simultaneously, the separate-profile approach is the one most likely to work on Windows.[3][1]

Would you like a **PowerShell script** that sets up two Windows launchers for Claude Work and Claude Personal?

## Human

in my single windows 11 account, i have already used two claude accounts.  they do seem to have different history and sessions.  does that mean there are already two paths?

## Assistant

Yes, that **likely means Claude is already maintaining separate session/history state per account**, but it does **not** prove you have two fully separate Windows app paths or profiles. Claude’s desktop app is known to keep account switching state locally, and switching accounts can change what session history is visible.[1][2]

## What that implies
- If each Claude account shows different history, Claude is at least separating **account-level data** such as sessions and conversation history.[2][1]
- That separation may come from the app’s own account/session store, not necessarily from two distinct Windows user profiles or two separate install paths.[3][1]
- In other words, you may already have **two accounts in one local app container**, but not necessarily two independent app installations.[3][2]

## How to tell the difference
Check whether the two accounts are using:
- the same Claude Desktop install folder,
- the same Windows user profile,
- and the same local config directory under your home path.  

If those are shared, then you have **one app path with two account states**, not two separate paths. If you have separate config directories or launch methods that isolate `USERPROFILE` or a Claude config directory, then you do have separate paths.[4][3]

## Practical read
For your situation, the strongest interpretation is: Claude is already preserving **per-account sessions** for the two logins you used, but the app itself is probably still using one underlying Windows profile unless you deliberately set up isolation. So the presence of different history is evidence of **separate account data**, not proof of **separate app instances**.[1][2][3]

## Next check
A useful test is to sign out of one account and see whether the other account’s history remains available after signing back in. If it does, that supports account-scoped history; if both histories disappear together, then they were sharing the same local store more than expected.[2][1]

Would you like a Windows-specific way to inspect the local Claude folders and confirm whether you already have one profile or two?

## Human

yes

## Assistant

Yes — on Windows, the clearest sign is that Claude-related state is usually stored in a local config directory under your Windows user profile, and separate account sessions can exist without separate app installs.[1][2]

## What to inspect
Look for these paths first:
- `C:\Users\<you>\.claude\` for Claude Code-style config and credentials.[2][1]
- `C:\Users\<you>\AppData\Roaming\Claude\` for Claude Desktop config files such as `claude_desktop_config.json`.[3]
- Possibly `C:\Users\<you>\Documents\Claude\` for desktop-side project/session data, depending on the build/version.[4]

## What the paths mean
If both Claude accounts are showing different history but you only see one set of those folders, then you probably have **one Windows profile and one Claude install with multiple account sessions stored inside it**.[1][3]
If you find separate folders like `.claude-personal` and `.claude-work`, or you have launchers that set a different `CLAUDE_CONFIG_DIR` / `USERPROFILE`, then you really do have **two isolated paths**.[5][6][1]

## Quick test
1. Open File Explorer.
2. Paste `%USERPROFILE%\.claude` and see whether it exists.
3. Paste `%APPDATA%\Claude` and see whether it exists.
4. Compare timestamps and contents after logging into each account.[3][1]

If the same folder changes when you switch accounts, the app is storing both accounts in the same path. If each account maps to a different folder or launcher, then you’ve already got separate paths.[5][1]

## Most likely for your case
Based on what you described, the most likely situation is **shared Windows profile + separate Claude account sessions inside that profile**, not two fully separate installs. That would explain why histories differ while still living on the same machine.[7][2][1][3]

## Best next step
Check whether `%USERPROFILE%\.claude` exists and whether `%APPDATA%\Claude` contains multiple account-specific files or just one config set. If you want, I can give you a **5-minute PowerShell checklist** that prints the exact folders and files to compare.[1][3]

## Human

yes please provide the powershell checklist

## Assistant

Yes. Here’s a **PowerShell checklist** to determine whether your two Claude accounts are already using separate local paths on Windows, or whether they’re just separate sessions inside one shared profile.[1][2][3]

## 1) Inspect the obvious Claude folders
Run this in PowerShell:

```powershell
$paths = @(
  "$env:USERPROFILE\.claude",
  "$env:APPDATA\Claude",
  "$env:LOCALAPPDATA\Packages"
)

$paths | ForEach-Object {
  [pscustomobject]@{
    Path = $_
    Exists = Test-Path $_
    LastWrite = if (Test-Path $_) { (Get-Item $_).LastWriteTime } else { $null }
  }
} | Format-Table -Auto
```

Claude Code-related config is commonly under `~\.claude`, while Claude Desktop config is commonly under `%APPDATA%\Claude\claude_desktop_config.json`.[2][3][1]

## 2) Look inside the Claude folders
Run this next:

```powershell
if (Test-Path "$env:USERPROFILE\.claude") {
  Get-ChildItem "$env:USERPROFILE\.claude" -Force | Select-Object Name, FullName, LastWriteTime | Format-Table -Auto
}

if (Test-Path "$env:APPDATA\Claude") {
  Get-ChildItem "$env:APPDATA\Claude" -Force | Select-Object Name, FullName, LastWriteTime | Format-Table -Auto
}
```

If you see separate account-related files, credentials, histories, or distinct subfolders, that’s evidence of local separation.[4][3]

## 3) Check whether Claude Desktop is using the MSIX app-data path
Some Windows builds read from an app-container path instead of the plain roaming path, so compare both locations.[5][6]

```powershell
Get-AppxPackage -Name "Claude" | Select-Object Name, PackageFamilyName, Version, InstallLocation

$pkg = Get-AppxPackage -Name "Claude" | Select-Object -First 1
if ($pkg) {
  $real = "$env:LOCALAPPDATA\Packages\$($pkg.PackageFamilyName)\LocalCache\Roaming\Claude"
  [pscustomobject]@{
    RealPath = $real
    Exists = Test-Path $real
    LastWrite = if (Test-Path $real) { (Get-Item $real).LastWriteTime } else { $null }
  } | Format-List
}
```

That MSIX path is important because some reports show the app reading from there even when a UI button opens `%APPDATA%\Claude`.[6][5]

## 4) Compare the config files
Run:

```powershell
$files = @(
  "$env:APPDATA\Claude\claude_desktop_config.json",
  "$env:LOCALAPPDATA\Packages\$(Get-AppxPackage -Name 'Claude' | Select-Object -First 1 | ForEach-Object { $_.PackageFamilyName })\LocalCache\Roaming\Claude\claude_desktop_config.json"
)

$files | ForEach-Object {
  [pscustomobject]@{
    File = $_
    Exists = Test-Path $_
    Size = if (Test-Path $_) { (Get-Item $_).Length } else { $null }
    LastWrite = if (Test-Path $_) { (Get-Item $_).LastWriteTime } else { $null }
  }
} | Format-Table -Auto
```

If one file changes when you switch accounts, Claude is likely sharing one local config store.[2][6]

## 5) Search for multiple profile-like directories
Run:

```powershell
Get-ChildItem "$env:USERPROFILE" -Force -Directory |
  Where-Object { $_.Name -match 'claude|\.claude' } |
  Select-Object Name, FullName, LastWriteTime | Format-Table -Auto
```

If you already have things like `.claude-work` or `.claude-personal`, then you’ve probably already created separate paths, intentionally or accidentally.[3][7][8]

## How to interpret the results
- **One `.claude` and one Claude folder:** you probably have one Windows profile with two account sessions inside it.[3][2]
- **Separate folders per account:** you already have isolated paths.[7][3]
- **MSIX path exists and differs from `%APPDATA%\Claude`:** your app may be using the packaged location, not the obvious roaming path.[5][6]

## What I’d do next
Run steps 1 to 4, then compare the `LastWrite` timestamps before and after switching accounts. If you want, I can give you a second script that **monitors the folders live** while you sign out and back in, so you can see exactly which path changes.
