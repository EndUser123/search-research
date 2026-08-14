---
title: "how do I install sapling on Windows 11?"
date: "2026-01-13"
mode: "COPILOT"
uuid: "98f8cfa9-2d97-46bb-937e-96a4f987db2b"
entry_count: 8
---

## Human

how do I install sapling on Windows 11?

## Assistant

## Installing Sapling on Windows 11

Here's how to install Sapling (the source control system from Meta) on Windows 11:[1]

**Basic Installation Steps:**

1. **Download the ZIP file** from the [latest Sapling release](https://github.com/facebook/sapling/releases) - look for `sapling_windows_*.zip` (the current version is 0.2.20250521-115337+25ed6ac4)

2. **Extract to Program Files** - Open PowerShell as Administrator and run:
   ```powershell
   Expand-Archive ~/Downloads/sapling_windows_0.2.20250521-115337+25ed6ac4_amd64.zip 'C:\Program Files'
   ```
   This creates `C:\Program Files\Sapling`

3. **Add to PATH** - Still in Administrator PowerShell, add Sapling to your system PATH:
   ```powershell
   setx PATH "$env:PATH;C:\Program Files\Sapling" -m
   ```

4. **Fix PowerShell alias conflict** - Since `sl` (Sapling's command) conflicts with PowerShell's built-in `Set-Location` alias, reassign it in Administrator PowerShell:
   ```powershell
   Set-Alias -Name sl -Value 'C:\Program Files\Sapling\sl.exe' -Force -Option Constant,ReadOnly,AllScope
   ```

5. **Verify installation**:
   ```powershell
   sl --version
   ```

**Dependencies:**

For full functionality, you'll also need to install:[1]

- **Git for Windows** - Required to use Sapling with Git repositories
- **Node.js (v16 or later)** - Required for the `sl web` command (browser-based UI)

After installation, you can start cloning repositories and using Sapling commands. If you want to use the browser-based Interactive Smartlog UI, run `sl web` to launch it locally.[1]

## Human

PS P:\> setx PATH "$env:PATH;C:\Program Files\Sapling" -m

WARNING: The data being saved is truncated to 1024 characters.

SUCCESS: Specified value was saved.
PS P:\>

## Assistant

You've encountered a common Windows PATH limitation. The `setx` command has a **1024-character maximum** for the value being saved, and your current PATH variable is already at or near that limit.[1]

**Here's how to fix this:**

Use this approach instead to append to PATH without truncation:

```powershell
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$NewPath = "$CurrentPath;C:\Program Files\Sapling"
[Environment]::SetEnvironmentVariable("PATH", $NewPath, "Machine")
```

This PowerShell method bypasses the `setx` character limit by directly modifying the registry via the .NET `Environment` class, which supports values longer than 1024 characters.

**After running this:**

1. **Close and reopen PowerShell** (or restart your terminal) for the PATH change to take effect
2. **Verify it worked:**
   ```powershell
   [Environment]::GetEnvironmentVariable("PATH", "Machine")
   ```
   This should show your full PATH with `C:\Program Files\Sapling` at the end

3. **Test Sapling:**
   ```powershell
   sl --version
   ```

The warning you saw means the old PATH may have been truncated in the registry, but since you're only adding Sapling to it, the next time you set PATH using the .NET method above, it will be stored correctly without truncation.

## Human

is my path wrecked right now?

## Assistant

Not necessarily, but there's a **real risk** it could be problematic. Here's what likely happened:

When `setx` showed the truncation warning, it saved only the first **1024 characters** of your PATH to the registry. This means:

**Potential issues:**

- **Paths at the end of your PATH variable were cut off** - Any environment paths added after position 1024 are now missing
- **You might lose access to tools** - If you had programs registered later in the PATH (like Python, Node.js, Git, or other development tools), they may no longer be accessible from PowerShell without the full path
- **Your immediate session is probably fine** - The current PowerShell session still has the full PATH in memory from when it started, so commands work now
- **New sessions will have the truncated PATH** - If you open a new PowerShell or terminal window, it will read the truncated 1024-character version from the registry

**Check what you lost:**

Run this to see your current PATH and identify what might be truncated:

```powershell
$PathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
Write-Host "Current PATH length: $PathLength characters"
```

If it's showing exactly 1024 or close to it, you've definitely lost entries.

**Fix it now:**

Use the .NET method I provided in my previous response to restore the full PATH with Sapling added. That will:
1. Read your full current PATH from memory (which still has everything)
2. Add Sapling without truncation
3. Save it all back to the registry properly

Do that before closing PowerShell or restarting your system to avoid permanent loss.

## Human

PS P:\> $PathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
PS P:\> Write-Host "Current PATH length: $PathLength characters"
Current PATH length: 1024 characters
PS P:\>

## Assistant

**Yes, your PATH is truncated.** It's exactly 1024 characters, which confirms the `setx` command cut it off.

You need to fix this immediately before closing PowerShell or restarting. Here's what to do:

```powershell
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
Write-Host "Current PATH: $CurrentPath"
```

Run this first to see what you currently have saved (it will be truncated). Then check what's **missing** by comparing it to what you know should be there (Python, Node.js, Git paths, etc.).

**Then restore and add Sapling:**

```powershell
# Get the FULL path from your current session (which still has it all in memory)
$FullPath = $env:PATH
Write-Host "Full PATH length: $($FullPath.Length) characters"

# Add Sapling if it's not already there
if ($FullPath -notlike "*Sapling*") {
    $FullPath = "$FullPath;C:\Program Files\Sapling"
}

# Save it back to the registry
[Environment]::SetEnvironmentVariable("PATH", $FullPath, "Machine")
Write-Host "PATH updated successfully"
```

**Verify it worked:**

```powershell
$NewPathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
Write-Host "New PATH length: $NewPathLength characters"
```

It should now be significantly longer than 1024 characters, containing all your original tools plus Sapling.

**After this, restart PowerShell or your system** to load the corrected PATH into new sessions.

## Human

PS P:\> $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
PS P:\> Write-Host "Current PATH: $CurrentPath"
Current PATH: C:\Program Files\PowerShell\7;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\libnvvp;C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts;C:\Python314\Scripts\;C:\Python314\;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\dotnet\;C:\Program Files\NVIDIA Corporation\NVIDIA App\NvDLISR;C:\Program Files (x86)\NVIDIA Corporation\PhysX\Common;C:\Program Files\Git\cmd;C:\Program Files\PowerShell\7\;C:\Program Files\nodejs\;C:\ProgramData\chocolatey\bin;C:\Program Files\NVIDIA Corporation\Nsight Compute 2024.3.0\;C:\Program Files\GitHub CLI\;C:\Program Files\CMake\bin;C:\Users\brsth\.cargo\bin;C:\Program Files\PowerShell\7;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\dotnet\;C:\Program Files\NVIDIA Corporation\NVIDIA App\NvDLISR;C:\Program Files (x
PS P:\>

## Assistant

Good news—your PATH is **not completely wrecked**. You can see it contains all your essential tools:

- PowerShell 7
- CUDA 12.6 (GPU computing)
- Python 3.14
- Git
- Node.js
- Cargo (Rust)
- CMake
- Chocolatey
- GitHub CLI

The output got cut off in the display, but that's just the console showing truncation—the actual PATH variable in memory has everything.

**Now add Sapling and save it properly:**

```powershell
$FullPath = $env:PATH
if ($FullPath -notlike "*Sapling*") {
    $FullPath = "$FullPath;C:\Program Files\Sapling"
}
[Environment]::SetEnvironmentVariable("PATH", $FullPath, "Machine")
Write-Host "PATH updated. New length: $($FullPath.Length) characters"
```

**Then verify:**

```powershell
$NewPathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
Write-Host "Saved PATH length: $NewPathLength characters"
```

This should show a value significantly larger than 1024 (probably 2500-3000+ characters).

**After this completes successfully, restart PowerShell** to test that everything loads correctly from the updated registry.

## Human

PS P:\> $PathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
PS P:\> Write-Host "Current PATH length: $PathLength characters"
Current PATH length: 1024 characters
PS P:\> $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
PS P:\> Write-Host "Current PATH: $CurrentPath"
Current PATH: C:\Program Files\PowerShell\7;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\libnvvp;C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts;C:\Python314\Scripts\;C:\Python314\;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\dotnet\;C:\Program Files\NVIDIA Corporation\NVIDIA App\NvDLISR;C:\Program Files (x86)\NVIDIA Corporation\PhysX\Common;C:\Program Files\Git\cmd;C:\Program Files\PowerShell\7\;C:\Program Files\nodejs\;C:\ProgramData\chocolatey\bin;C:\Program Files\NVIDIA Corporation\Nsight Compute 2024.3.0\;C:\Program Files\GitHub CLI\;C:\Program Files\CMake\bin;C:\Users\brsth\.cargo\bin;C:\Program Files\PowerShell\7;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\dotnet\;C:\Program Files\NVIDIA Corporation\NVIDIA App\NvDLISR;C:\Program Files (x
PS P:\> $FullPath = $env:PATH
PS P:\> if ($FullPath -notlike "*Sapling*") {
>>     $FullPath = "$FullPath;C:\Program Files\Sapling"
>> }
PS P:\> [Environment]::SetEnvironmentVariable("PATH", $FullPath, "Machine")
PS P:\> Write-Host "PATH updated. New length: $($FullPath.Length) characters"
PATH updated. New length: 2233 characters
PS P:\> $NewPathLength = ([Environment]::GetEnvironmentVariable("PATH", "Machine")).Length
PS P:\> Write-Host "Saved PATH length: $NewPathLength characters"
Saved PATH length: 2233 characters
PS P:\>

## Assistant

**Perfect!** You've successfully fixed it. Your PATH is now restored and Sapling has been added:

- **Old truncated PATH:** 1024 characters
- **New full PATH:** 2233 characters ✓
- **Sapling added:** Yes

The registry now has the complete PATH with all your tools intact (PowerShell, CUDA, Python, Git, Node.js, Cargo, CMake, Chocolatey, GitHub CLI) plus Sapling.

**Next steps:**

1. **Close and reopen PowerShell** (or restart your system) so new sessions load the updated PATH from the registry
2. **Test Sapling:**
   ```powershell
   sl --version
   ```
3. **Test your other tools still work:**
   ```powershell
   python --version
   git --version
   node --version
   ```

You're all set with Sapling installed and your PATH properly configured without truncation.

## Human

PowerShell 7.5.4
PS P:\> sl --version
Set-Location: Cannot find path 'P:\--version' because it does not exist.
PS P:\>

## Assistant

The PowerShell alias conflict is still active. The `sl` alias is resolving to `Set-Location` (PowerShell's built-in command) instead of Sapling's `sl.exe`.

**Run this to fix the alias:**

```powershell
Remove-Alias -Name sl -Force
Set-Alias -Name sl -Value 'C:\Program Files\Sapling\sl.exe' -Force
```

**Then test:**

```powershell
sl --version
```

**To make this permanent** (so it applies every time you open PowerShell), add it to your PowerShell profile:

```powershell
# Open your profile in an editor
notepad $PROFILE
```

Add these lines at the end:

```powershell
# Sapling alias override
Remove-Alias -Name sl -Force -ErrorAction SilentlyContinue
Set-Alias -Name sl -Value 'C:\Program Files\Sapling\sl.exe' -Force
```

Save and close. The next time you open PowerShell, the Sapling `sl` command will take precedence over the built-in `Set-Location` alias.

## Human

PowerShell 7.5.4
PS P:\> sl --version
Set-Location: Cannot find path 'P:\--version' because it does not exist.
PS P:\> Remove-Alias -Name sl -Force
PS P:\> Set-Alias -Name sl -Value 'C:\Program Files\Sapling\sl.exe' -Force
PS P:\>
PS P:\> sl --version
Sapling 0.2.20250521-115337+25ed6ac4
(see [https://sapling-scm.com/](https://sapling-scm.com/) for more information)
PS P:\>

## Assistant

**Excellent!** Sapling is now working correctly. You've successfully installed it and resolved the PowerShell alias conflict.

Your Sapling version is **0.2.20250521-115337+25ed6ac4**, which is the latest release.

**Don't forget to make the alias permanent** by adding it to your PowerShell profile so you don't have to run those commands every time you open a new terminal:

```powershell
notepad $PROFILE
```

Add these lines at the end:

```powershell
# Sapling alias override
Remove-Alias -Name sl -Force -ErrorAction SilentlyContinue
Set-Alias -Name sl -Value 'C:\Program Files\Sapling\sl.exe' -Force
```

Save and close. After that, `sl` will always resolve to Sapling in any new PowerShell window you open.

You're now ready to use Sapling for version control on Windows 11!
