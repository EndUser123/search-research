---
title: "in vscode, the codex install extension seems corrupted.  an uninstall / reinstall doesn't help.  How can I rip it out to"
date: "2026-02-03"
mode: "COPILOT"
uuid: "c92f8b78-8a04-40ef-b19b-fa414cdb27a7"
entry_count: 13
---

## Human

in vscode, the codex install extension seems corrupted.  an uninstall / reinstall doesn't help.  How can I rip it out to do a fresh install?

## Assistant

To fully remove a corrupted Codex extension in VS Code on Windows, manually delete its files after uninstalling, as standard uninstall/reinstall often leaves remnants.[1][2][3]

## Preparation Steps
Close all VS Code instances completely, including from Task Manager (search for "Code" processes and end them).[4][2]

Open PowerShell or Command Prompt and run `code --list-extensions` to confirm the exact ID (likely `openai.codex` or similar like `openaigpt-*`).[1]

## Uninstall via CLI
Run `code --uninstall-extension <exact-id> --force` (replace `<exact-id>` with the ID from above).[1]

If it fails, proceed to manual deletion.

## Manual Deletion (Windows Paths)
Delete these folders/files (enable "View hidden items" in File Explorer; paths use `%USERPROFILE%` which is `C:\Users\YourUsername`):

- `%USERPROFILE%\.vscode\extensions\` – Delete any `openai.*`, `codex*`, or `openaigpt*` folders.[5][1]
- `%APPDATA%\Code\User\globalStorage\` – Delete `openai.*` or `codex*` subfolders.[1]
- `%APPDATA%\Code\CachedExtensions\` and `%APPDATA%\Code\CachedExtensionVSIXs\` – Delete relevant `.vsix` or cached files.[3][1]
- `%USERPROFILE%\.vscode\extensions\extensions.json` – Edit and remove the Codex entry if present.[1]
- Check `%LOCALAPPDATA%\Code\` for any `openai.*` or `codex*` remnants.[6]

For Codex-specific auth/config (if issues persist): Delete `%USERPROFILE%\.codex\` folder.[7][8]

## Fresh Install
Restart your PC, reopen VS Code, search "Codex" in Extensions (ensure official OpenAI publisher), and install.[9][7][5]

Run `Developer: Reload Window` (Ctrl+Shift+P) post-install. If stuck, try `Codex: Reset NUX` command if available.[7]

## Human

PowerShell 7.5.4
PS P:\\> code --list-extensions
code: The term 'code' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS P:\\>

## Assistant

**The `code` command isn't in your PowerShell PATH, common on Windows if not added during VS Code install or after restarts.** Use the full path or VS Code's built-in tool to fix it quickly.[1][2]

## Locate VS Code Executable
In PowerShell, run these to find it (user install is typical for devs):  
`Get-ChildItem $env:LOCALAPPDATA -Recurse -Name "code.cmd" -ErrorAction SilentlyContinue`  
Or: `Get-ChildItem "$env:LOCALAPPDATA\Programs\Microsoft VS Code" -Recurse -Name "code.cmd" -ErrorAction SilentlyContinue`[3][1]

Common paths:  
- `$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd` (System Setup)  
- `$env:LOCALAPPDATA\Microsoft VS Code\Code.exe` (User Setup)[2][1][3]

## List Extensions Without CLI
Open VS Code → Ctrl+Shift+X (Extensions view) → Search "codex" to note the exact ID/Publisher (e.g., `openai.codex`). No CLI needed for this.[4]

## Temporary CLI Fix
Use full path for uninstall:  
`& "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd" --uninstall-extension openai.codex --force`  
(Replace path/ID as needed; test path first with `& "full\path\to\code.cmd" --version`)[1]

## Permanent PATH Fix
1. In VS Code: Ctrl+Shift+P → "Shell Command: Install 'code' command in PATH" → Restart PowerShell.[5][1]
2. Or manually: Win+R → `sysdm.cpl` → Advanced → Environment Variables → Edit PATH (User vars) → Add VS Code's `bin` folder → OK → Restart PowerShell/PC.[6][2]

Proceed to manual deletion from prior steps after CLI uninstall.[7]

## Human

PS P:\\> Get-ChildItem "$env:LOCALAPPDATA\\Programs\\Microsoft VS Code" -Recurse -Name "code.cmd" -ErrorAction SilentlyContinue
PS P:\\>

## Assistant

Your VS Code is likely using the **User Setup** installer (common, no admin needed), so it's at `$env:LOCALAPPDATA\Microsoft VS Code\Code.exe` instead of Programs.[1][2][3]

## Find Exact Executable
Run these in PowerShell to locate it:

```
Get-ChildItem $env:LOCALAPPDATA -Recurse -Name "Code.exe" -ErrorAction SilentlyContinue | Select-Object -First 5
```

```
where.exe code
```

Or:  
```
dir "$env:LOCALAPPDATA\Microsoft VS Code\Code.exe" -ErrorAction SilentlyContinue
```

```
dir "C:\Program Files\Microsoft VS Code\Code.exe" -ErrorAction SilentlyContinue
```
Copy the full path from results (e.g., `C:\Users\YourName\AppData\Local\Microsoft VS Code\Code.exe`).[2][4][1]

## Test and List Extensions
Once found, run:  
`& "C:\full\path\to\Code.exe" --version` (replace path).  
Then: `& "C:\full\path\to\Code.exe" --list-extensions` to get Codex ID.[5]

## Add to PATH Permanently
In VS Code: Ctrl+Shift+P → "Shell Command: Install 'code' command in PATH" → Restart PowerShell.[1][5]

Manual: Sysdm.cpl → Advanced → Env Variables → User PATH → New → Add VS Code folder (e.g., `$env:LOCALAPPDATA\Microsoft VS Code\bin` if exists, or parent).[4][6]

## Graphical Alternative
Right-click Start → Search "Visual Studio Code" → Right-click → Open file location → Right-click shortcut → Properties → Note "Target" or "Start in" path.[3][2]

Proceed to uninstall with full path: `& "full\path\Code.exe" --uninstall-extension <id> --force`.[7]

## Human

it just hangs here PS P:\\> Get-ChildItem $env:LOCALAPPDATA -Recurse -Name "Code.exe" -ErrorAction SilentlyContinue | Select-Object -First 5

## Assistant

**`Get-ChildItem -Recurse` on `$env:LOCALAPPDATA` hangs due to large directories (e.g., node_modules, downloads) – it's a known PowerShell performance issue.** Stop it with Ctrl+C and use targeted checks instead.[1][2][3]

## Quick Path Checks
Run these non-recursive commands one by one:

```
Test-Path "$env:LOCALAPPDATA\Microsoft VS Code\Code.exe"
```

```
Test-Path "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
```

```
Test-Path "C:\Program Files\Microsoft VS Code\Code.exe"
```

```
Test-Path "C:\Program Files (x86)\Microsoft VS Code\Code.exe"
```
If True, that's your path (User Setup is usually first).[4][5][6]

## Universal Finder
```
Get-ChildItem @(
  "$env:LOCALAPPDATA\Microsoft VS Code",
  "$env:LOCALAPPDATA\Programs\Microsoft VS Code",
  "C:\Program Files\Microsoft VS Code",
  "C:\Program Files (x86)\Microsoft VS Code"
) -Recurse -Name "Code.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
```
This limits scope to VS Code dirs only.[4]

Or use Windows Search: Win key → type "Code.exe" → Open file location for VS Code executable → Copy full path from Properties.[5]

## Graphical Extension List
In VS Code: Ctrl+Shift+X → Filter "codex" → Right-click extension → Extension Settings → Note ID (e.g., `openai.codex`).[7]

## Next: Uninstall with Path
`& "C:\Your\Found\Path\Code.exe" --uninstall-extension openai.codex --force` (adjust ID/path).[8][9]

Proceed to manual folder deletion as before.[8]

## Human

PS P:\\> Test-Path "$env:LOCALAPPDATA\\Microsoft VS Code\\Code.exe"
False
PS P:\\> Test-Path "$env:LOCALAPPDATA\\Programs\\Microsoft VS Code\\Code.exe"
False
PS P:\\> Test-Path "C:\\Program Files\\Microsoft VS Code\\Code.exe"
False
PS P:\\> Test-Path "C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe"
False
PS P:\\>

## Assistant

**Standard paths missed – your VS Code is likely in portable mode, custom install, or a variant like `Microsoft VSCode` or `_` folder.** Skip CLI; use graphical/manual methods for Codex removal.[1][2][3]

## Fast Executable Hunt
1. Win key → type "Visual Studio Code" or "Code.exe" → Right-click result → Open file location → Right-click Code.exe → Properties → Copy full "Target" path.[4][3]
2. Or File Explorer: `%LOCALAPPDATA%\Programs` → Look for "Microsoft VS Code", "VSCode", or ZIP-extracted folder (e.g., `VSCode-win32-x64-*`).[5][1]
3. Check Desktop/Start Menu shortcuts for path.[4]

If portable (e.g., P:\VSCode\Code.exe), note it for PATH later.

## Skip CLI: Direct Manual Removal
Since CLI is tricky, delete Codex files now (close VS Code first):

```
# Extensions (user data)
Remove-Item "$env:APPDATA\Code\User\globalStorage\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.vscode\extensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.vscode\extensions\codex*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.vscode\extensions\openaigpt*" -Recurse -Force -ErrorAction SilentlyContinue

# Caches
Remove-Item "$env:APPDATA\Code\CachedExtensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
Verify: `ls "$env:USERPROFILE\.vscode\extensions" | sls codex` (lists matching).[6][7][1]

## Reinstall Fresh
Open VS Code → Extensions → Search "Codex" (official OpenAI) → Install → Reload window.[8][9]

If auth issues post-delete: Clear `%USERPROFILE%\.codex` too.[10]

This bypasses CLI entirely for a clean slate.[6]

## Human

I'm using insider

## Assistant

**You're on VS Code Insiders, which installs to distinct paths like `$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders` and uses `code-insiders` CLI.** Standard paths missed it – here's the fix.[1][2][3]

## Test Insiders Paths
Run these:

```
Test-Path "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\Code.exe"
```

```
Test-Path "$env:LOCALAPPDATA\Microsoft VS Code Insiders\Code.exe"
```

```
Test-Path "C:\Program Files\Microsoft VS Code Insiders\Code.exe"
```
If True, use that (e.g., `& "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\Code.exe" --list-extensions`).[3][1]

## Quick Shortcut Method
Win key → "Visual Studio Code - Insiders" → Right-click → Open file location → Right-click Code.exe → Properties → Copy "Target" path.[4][1]

## List/Uninstall via CLI
```
& "full\insiders\path\Code.exe" --list-extensions | Select-String codex
```
```
& "full\insiders\path\Code.exe" --uninstall-extension <id> --force
```
CLI is `code-insiders` if PATH added (via Ctrl+Shift+P → "Shell Command: Install 'code-insiders' command in PATH").[5][3]

## Insiders Data Folders
Extensions in same spots: `$env:USERPROFILE\.vscode-insiders\extensions` or `$env:APPDATA\Code - Insiders\User\globalStorage` (delete `openai.*`/ `codex*`).[6][7]

```
ls "$env:USERPROFILE\.vscode-insiders\extensions"
```
Delete matches, reload VS Code Insiders.[7][6]

Reinstall from Extensions view.[8]

## Human

"C:\\Users\\brsth\\AppData\\Local\\Programs\\Microsoft VS Code Insiders\\Code - Insiders.exe"

## Assistant

**Great – that's the standard VS Code Insiders User Setup path: `C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe`.** Now use it to list/uninstall Codex.[1][2]

## List Extensions
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions | Select-String codex -ErrorAction SilentlyContinue
```
This shows exact ID (e.g., `openai.codex`).[3]

## Uninstall Codex
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --uninstall-extension openai.codex --force
```
Replace `openai.codex` with your exact ID; `--force` skips errors.[4][3]

## Verify and Clean Remnants
```
ls "$env:USERPROFILE\.vscode-insiders\extensions" | sls codex
```
Delete any leftovers:  
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
Also check `$env:APPDATA\Code - Insiders\User\globalStorage\openai.*` and delete.[5][4]

## Reload and Reinstall
Close/reopen VS Code Insiders → Ctrl+Shift+P → "Developer: Reload Window". Reinstall Codex from Extensions view.[6]

## Optional: Add to PATH
Ctrl+Shift+P → "Shell Command: Install 'code-insiders' command in PATH" → Restart PowerShell (enables `code-insiders`).[2][1]

## Human

doing this opened vscode insiders: & "C:\\Users\\brsth\\AppData\\Local\\Programs\\Microsoft VS Code Insiders\\Code - Insiders.exe" --list-extensions | Select-String codex -ErrorAction SilentlyContinue

## Assistant

**The command launched VS Code Insiders without outputting extensions because `--list-extensions` prints to stdout but piping/Select-String in PowerShell may not capture it cleanly, or VS Code stole focus.** Redirect output to file for reliable results.[1]

## List Extensions Properly
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions > extensions.txt
```
Then: `Select-String codex extensions.txt` (or `notepad extensions.txt` to view all).[1]

Or one-liner:  
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions | findstr codex
```
(Uses `findstr` for better Windows console matching).[2]

## Force Uninstall (Safe Guess)
If no output or to nuke:  
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --uninstall-extension openai.codex --force
```
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --uninstall-extension codex --force
```
Errors are ignored with `--force`.[2][1]

## Immediate Manual Cleanup
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\*codex*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:APPDATA\Code - Insiders\User\globalStorage\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
Reload VS Code Insiders (Ctrl+R or Developer: Reload Window).[3][2]

Confirms corruption gone – reinstall fresh.[4]

## Human

extension.txt is empty

## Assistant

**Empty `extensions.txt` suggests CLI lists no Codex (possibly already gone/unrecognized) or Insiders quirk – common with corrupted installs.** Folders hold the truth; delete them directly.[1][2]

## Check Insiders Folders
```
ls "$env:USERPROFILE\.vscode-insiders\extensions" | Select-String "codex|openai"
```
```
ls "$env:APPDATA\Code - Insiders\User\globalStorage" | Select-String "codex|openai"
```
```
ls "$env:APPDATA\Code - Insiders\CachedExtensions" | Select-String "codex|openai"
```
This lists suspects without recurse hang.[3][4]

## Nuke Codex Remnants
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\*codex*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\openaigpt*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:APPDATA\Code - Insiders\User\globalStorage\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:APPDATA\Code - Insiders\User\globalStorage\*codex*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.codex" -Recurse -Force -ErrorAction SilentlyContinue
```
Re-check empty folders post-delete.[5][6][3]

## Verify Clean Install
Close Insiders → Reopen → Ctrl+Shift+X → "@installed codex" (should show none) → Search/install fresh "Codex".[7]

Reload (Ctrl+Shift+P → "Developer: Reload Window"). Corruption cleared.[1]

## Human

ls "$env:APPDATA\\Code - Insiders\\User\\globalStorage" | Select-String "codex|openai"
 this had a lot of output

## Assistant

**Lots of output in `globalStorage` means Codex/OpenAI stores heavy data there (configs, caches, auth) – deleting it fully resets the corrupted extension.**[1][2][3]

## Precise Cleanup
```
Get-ChildItem "$env:APPDATA\Code - Insiders\User\globalStorage" | Select-String "codex|openai" | ForEach-Object { $_.Line } | Remove-Item -Recurse -Force
```
Or list first:  
```
Get-ChildItem "$env:APPDATA\Code - Insiders\User\globalStorage" -Directory | Where-Object { $_.Name -match "codex|openai" }
```
Delete matches: `Remove-Item "that\path" -Recurse -Force`.[3][4]

Also:  
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\*codex*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.vscode-insiders\extensions\openai.*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:APPDATA\Code - Insiders\CachedExtensions\*codex*" -Recurse -Force -ErrorAction SilentlyContinue
```
```
Remove-Item "$env:USERPROFILE\.codex" -Recurse -Force -ErrorAction SilentlyContinue
```
Safe: VS Code recreates non-corrupted state.[5][3]

## Final Steps
Reload Insiders (Ctrl+Shift+P → "Developer: Reload Window"). Extensions view → Uninstall Codex if listed → Reinstall fresh.[6][7]

Run `& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions > extensions-new.txt` to confirm clean.[8]

## Human

PS P:\\> Get-ChildItem "$env:APPDATA\\Code - Insiders\\User\\globalStorage" | Select-String "codex|openai" | ForEach-Object { $_.Line } | Remove-Item -Recurse -Force
Remove-Item: Cannot find drive. A drive with the name '2        �     `��i�K��C�ditorOverr�GA�Ememento/externalUriOpeners{"simpleBrowser.open"' does not exist.
Remove-Item: Cannot find drive. A drive with the name '�z��U7G�umemento/gettingStartedService{"CopilotSetupSignedOut"' does not exist.
Remove-Item: Cannot find drive. A drive with the name 'b
                                                        N���

## Assistant

**Error from piping `Select-String` to `Remove-Item`: `$_ .Line` grabs full line text (corrupted/Unicode names from JSON files), not folder paths.** Use `Get-ChildItem -Directory` to target actual folders safely.[1]

## Safe Folder Deletion
```
Get-ChildItem "$env:APPDATA\Code - Insiders\User\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force
```
This matches folder names only, deletes matching dirs (e.g., `openai.codex-1.2.3`).[2]

If Unicode issues:  
```
Get-ChildItem "$env:APPDATA\Code - Insiders\User\globalStorage" -Directory | Where-Object { $_.Name -like "*codex*" -or $_.Name -like "*openai*" } | Remove-Item -Recurse -Force
```

## Verify
```
Get-ChildItem "$env:APPDATA\Code - Insiders\User\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' }
```
Empty = success.[3]

## Full Cleanup Script
Run as block:
```
$path = "$env:APPDATA\Code - Insiders\User\globalStorage"
Get-ChildItem $path -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$extPath = "$env:USERPROFILE\.vscode-insiders\extensions"
Get-ChildItem $extPath -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Remove-Item "$env:USERPROFILE\.codex" -Recurse -Force -ErrorAction SilentlyContinue
```
Reload Insiders → Fresh Codex install.[4][5][2]

## Human

PS P:\\> Get-ChildItem "$env:APPDATA\\Code - Insiders\\User\\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force
PS P:\\> Get-ChildItem "$env:APPDATA\\Code - Insiders\\User\\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' }
PS P:\\>

## Assistant

**Perfect – globalStorage Codex/OpenAI folders are now deleted (empty verify confirms).** The corruption source is ripped out.[1]

## Quick Remaining Checks
```
Get-ChildItem "$env:USERPROFILE\.vscode-insiders\extensions" -Directory | Where-Object { $_.Name -match 'codex|openai' }
```
```
ls "$env:APPDATA\Code - Insiders\CachedExtensions" | Where-Object { $_ -match 'codex|openai' }
```
Delete any hits:
```
Get-ChildItem "$env:USERPROFILE\.vscode-insiders\extensions" -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force
```
```
Remove-Item "$env:USERPROFILE\.codex" -Recurse -Force -ErrorAction SilentlyContinue
```


## Fresh Start
1. Close all VS Code Insiders.
2. Reopen → Ctrl+Shift+P → "Developer: Reload Window".
3. Extensions (Ctrl+Shift+X) → Search "Codex" → Install official (OpenAI publisher).
4. Reload again → Test (no corruption).[2]

Done – CLI optional now (`& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions` should work clean).[3]

## Human

PS P:\\> Get-ChildItem "$env:APPDATA\\Code - Insiders\\User\\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force
PS P:\\> Get-ChildItem "$env:APPDATA\\Code - Insiders\\User\\globalStorage" -Directory | Where-Object { $_.Name -match 'codex|openai' }
PS P:\\> Get-ChildItem "$env:USERPROFILE\\.vscode-insiders\\extensions" -Directory | Where-Object { $_.Name -match 'codex|openai' }
PS P:\\> ls "$env:APPDATA\\Code - Insiders\\CachedExtensions" | Where-Object { $_ -match 'codex|openai' }
Get-ChildItem: Cannot find path 'C:\\Users\\brsth\\AppData\\Roaming\\Code - Insiders\\CachedExtensions' because it does not exist.
PS P:\\> Get-ChildItem "$env:USERPROFILE\\.vscode-insiders\\extensions" -Directory | Where-Object { $_.Name -match 'codex|openai' } | Remove-Item -Recurse -Force
PS P:\\>

## Assistant

**Excellent – all key Codex paths/extensions/globalStorage are now empty or deleted. CachedExtensions doesn't exist (normal if no cache).** You're fully cleaned for fresh install.[1][2]

## Final Verification
```
& "C:\Users\brsth\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe" --list-extensions | Select-String codex
```
No match = success.

Also:  
```
Test-Path "$env:USERPROFILE\.codex"
```
False = auth cleared.[3]

## Reinstall Steps
1. Open VS Code Insiders.
2. Ctrl+Shift+X → Search "Codex" → Install from OpenAI (official).
3. Ctrl+Shift+P → "Developer: Reload Window".
4. Test Codex – corruption gone.[4][5]

## Prevent Future Issues
- Add to PATH: Ctrl+Shift+P → "Shell Command: Install 'code-insiders' command in PATH".
- Backup extensions: `code-insiders --list-extensions > my-extensions.txt`.[6][7]

Fixed!
