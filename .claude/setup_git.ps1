# setup_git.ps1 — put P:\ under git (one repo at the root), logs excluded.
# Run natively on Windows: powershell -ExecutionPolicy Bypass -File P:\.claude\setup_git.ps1
# Rationale: single root repo satisfies both "P: under git" and "P:/.claude under
# git"; nested clones in packages\.github_repos are excluded (they have their own
# .git); log files/dirs excluded per policy.

$ErrorActionPreference = "Stop"

# 1. Remove the corrupt .git the sandbox mount left in P:\.claude (config is NUL bytes)
$stale = "P:\.claude\.git"
if (Test-Path "$stale\config") {
    $bytes = [IO.File]::ReadAllBytes("$stale\config")
    if ($bytes.Length -eq 0 -or ($bytes | Where-Object { $_ -ne 0 }).Count -eq 0) {
        Write-Host "Removing corrupt $stale (config is all NUL bytes)"
        Remove-Item -Recurse -Force $stale
    } else {
        Write-Host "WARNING: $stale exists and config is non-empty — inspect before proceeding."
        exit 1
    }
}

# 2. Root .gitignore (create only if absent; never clobber an existing one)
$gi = "P:\.gitignore"
if (-not (Test-Path $gi)) {
@"
# logs excluded per policy; everything else is tracked
logs/
**/logs/
*.log

# runtime junk
__pycache__/
*.pyc
*.tmp
.artifacts/

# event/artifact stores are logs in db form
events.db
artifacts.db

# independently-cloned repos manage their own history
packages/.github_repos/
"@ | Set-Content -Encoding UTF8 $gi
    Write-Host "Wrote $gi"
} else {
    Write-Host "$gi already exists — left untouched; review it covers logs/ and packages/.github_repos/"
}

# 3. Init + first commit
Set-Location P:\
if (-not (Test-Path "P:\.git")) {
    git init -b main
}
git add -A 2>&1 | Select-String "warning" | ForEach-Object { Write-Host $_ }
# Embedded-repo warnings above mean a subdir has its own .git — decide per case:
# add to .gitignore, or convert to a submodule. Do not blindly commit them.
$staged = (git diff --cached --name-only | Measure-Object -Line).Lines
Write-Host "Staged $staged files"
git commit -m "Initial snapshot: P:\ under version control (logs excluded)"
git log --oneline -1
Write-Host "Done. Verify with: git -C P:\ status"
