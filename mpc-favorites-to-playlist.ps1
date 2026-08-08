# --- CONFIG: MPC-HC install folder and output playlist name ---
$mpcInstallDir = "C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64"
$playlistName  = "mpc-favorites.mpcpl"
$playlistPath  = Join-Path $mpcInstallDir $playlistName

# Registry key where MPC-HC stores favorites (K-Lite, modern MPC-HC)
$mpcFavoritesKey = "HKCU:\Software\MPC-HC\MPC-HC\Favorites\Files"

Write-Host "Reading MPC-HC favorites from registry key:"
Write-Host "  $mpcFavoritesKey"
Write-Host "Playlist will be written to:"
Write-Host "  $playlistPath"
Write-Host ""

# Ensure MPC install directory exists
if (-not (Test-Path $mpcInstallDir)) {
    Write-Host "ERROR: MPC-HC install directory not found:"
    Write-Host "  $mpcInstallDir"
    Write-Host "Adjust \$mpcInstallDir in the script if MPC-HC is elsewhere."
    return
}

# Try to open the favorites registry key
try {
    $regItem = Get-Item $mpcFavoritesKey -ErrorAction Stop
} catch {
    Write-Host "ERROR: Could not open registry key:"
    Write-Host "  $mpcFavoritesKey"
    Write-Host "If you're on an older build, try:"
    Write-Host "  HKCU:\Software\Gabest\Media Player Classic\Favorites"
    return
}

# Get all value entries under the key
$values = Get-ItemProperty -Path $mpcFavoritesKey

# Collect file paths from favorites
$filePaths = @()

foreach ($prop in $values.PSObject.Properties) {
    # Skip PowerShell metadata properties
    if ($prop.Name -in @("PSPath","PSParentPath","PSChildName","PSDrive","PSProvider")) {
        continue
    }

    $rawValue = [string]$prop.Value

    # Favorites values may store "path|position" or "title;0;0;path".
    # Extract the actual path from either format.
    $candidate = $rawValue

    if ($candidate -like "*|*") {
        $candidate = $candidate.Split("|")[0]
    } elseif ($candidate -like "*;*") {
        if ($candidate -match ";0;0;(.+)$") {
            $candidate = $Matches[1]
        } else {
            $candidate = $candidate.Split(";")[0]
        }
    }

    # Basic sanity: must look like a Windows path (drive letter or UNC)
    if ($candidate -match "^[A-Za-z]:\\" -or $candidate -like "\\*") {
        $filePaths += $candidate
    }
}

if ($filePaths.Count -eq 0) {
    Write-Host "No valid file paths were extracted from the favorites registry key."
    Write-Host "Open regedit at:"
    Write-Host "  HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files"
    Write-Host "and inspect the values so we can adjust parsing if needed."
    return
}

Write-Host "Found $($filePaths.Count) favorite entries."
Write-Host ""

# --- Build MPC-HC .mpcpl playlist content ---
# Format:
#   MPCPLAYLIST
#   1,type,0
#   1,filename,FullPathOrRelativePath
#   2,type,0
#   2,filename,FullPathOrRelativePath
#   ...

$lines = @()
$lines += "MPCPLAYLIST"

$index = 1
foreach ($path in $filePaths) {
    # 'type,0' means a normal media file entry
    $lines += "$index,type,0"
    $lines += "$index,filename,$path"
    $index++
}

# Write playlist to the MPC-HC folder
$playlistContent = $lines -join "`r`n"

Set-Content -Path $playlistPath -Value $playlistContent -Encoding UTF8 -ErrorAction Stop

Write-Host "Playlist written to:"
Write-Host "  $playlistPath"
Write-Host "You can now open this .mpcpl file in MPC-HC64 to play all favorites as a playlist."
