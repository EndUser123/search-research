---
title: "media player classic home, how do I play all my saved favorites as a playlist?"
date: "2026-07-24"
mode: "COPILOT"
uuid: "a8c2f057-d083-419f-a59c-e7bf58798a24"
entry_count: 9
---

## Human

media player classic home, how do I play all my saved favorites as a playlist?

## Assistant

Yes — in Media Player Classic Home Cinema, the practical way to play all saved favorites as one sequence is to turn those favorites into a playlist, then open that playlist and play it in order. MPC-HC’s built-in Favorites feature is for individual media files, not playlist files, so you usually cannot “play favorites as a playlist” directly from Favorites itself.[1][2]

## How to do it
1. Open the playlist panel: **View → Playlist**, or press **Ctrl+7**.[3]
2. Add your saved items into that playlist. If they are already media files, use **File → Open File** and check **Add to playlist without opening** so they accumulate instead of replacing the current list.[1]
3. Save the assembled list by right-clicking the **playlist frame** and choosing **Save As** to create an `.mpcpl` playlist file.[1]
4. Later, open that `.mpcpl` file in MPC-HC and it will play the entries in sequence.[2]

## If your “favorites” are individual files
MPC-HC favorites are stored as file entries, not playlist entries, so the simplest workflow is:
- open each favorite into the playlist window,
- save the resulting playlist,
- then reopen that saved playlist whenever you want the full sequence.[2]

## Important detail
Right-click the **playlist area/frame**, not a single file inside the playlist, or you’ll only get item-specific options instead of playlist-wide commands. Also, if the playlist window is not visible when you add more files, MPC-HC may start a new playlist rather than appending to the existing one.[1]

## Fastest workflow
The shortest path is usually:
- **View → Playlist**
- add all favorites
- **Save As**
- later, open the saved `.mpcpl` file and press play.[3][1]

Would you like the exact steps for your MPC-HC version, including where the menu items are if you’re using the compact interface?

## Human

is there another video play app that can import or migrate these individual videos into a playlist?

## Assistant

Yes. The most straightforward cross-platform option is **VLC**, because it can add files or whole folders to a playlist, append new items to the current list, and open saved playlist files like `.m3u`, `.xspf`, and `.pls`.[1][2]

## Good options

| App | Best for | Why it fits |
|---|---|---|
| VLC | Windows, macOS, Linux | Can build playlists from local files/folders and open saved playlist files [1][2]. |
| PotPlayer | Windows | Strong playlist handling and import/export support, including its own playlist format and common playlist formats [3][4]. |
| IINA | macOS | Modern macOS player with playlist support and strong local playback features [1]. |

## What to use for your case
If your goal is to migrate a bunch of individual saved videos into one playable queue, **VLC is usually the easiest starting point** because you can drag files in, add folders, then save the result as a playlist file for reuse.[2][3]
If you are on Windows and want more playlist-control features, **PotPlayer** is often the stronger playlist-centric option.[4][5]
If you are on Mac, **IINA** is the cleanest modern alternative.[1]

## Practical migration path
1. Gather the individual video files into one place or a few folders.
2. Import them into the player’s playlist window.
3. Save the playlist as a file so you can reopen it later.
4. If you want portability, prefer `.m3u` or `.xspf`, since VLC supports both.[1]

## Important limitation
Most players do not “migrate favorites” directly from MPC-HC’s favorites database into another app automatically; in practice, you usually export or rebuild the list as a playlist file first.[6][1]
So the key question is whether your current favorites are already file paths you can collect, or whether they are only stored inside MPC-HC. If they are only inside MPC-HC, you may need a manual one-time rebuild before importing into another player.  

Would you like the best option specifically for **Windows 11**, with the exact steps to move your MPC-HC favorites into VLC or PotPlayer?

## Human

Are they in a registry or ini file for mpc?

## Assistant

Yes. For MPC-HC, favorites are typically stored either in a **registry key** or in the **INI file**, depending on whether you’re using a normal install or portable/INI mode.[1][2]

## Where to look
- **Portable / “Store settings to .ini file” enabled:** check the `MPlayerC.ini` file, under a `Favorites` section.[1]
- **Normal install:** check the registry under `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files` for newer MPC-HC versions.[3][1]
- **Older Media Player Classic builds:** favorites may be under `HKEY_CURRENT_USER\Software\Gabest\Media Player Classic\Favorites`.[4][1]

## What this means
If you want to back them up or migrate them, the simplest method is usually to export that registry branch or copy the INI file, depending on how your MPC-HC is configured.[5][1]
That is also why another player usually cannot read MPC-HC favorites directly unless you first extract the file paths from the registry or INI.[3][1]

## Practical next step
The first thing to check is whether your MPC-HC installation is using **INI mode** or **registry mode**. If you tell me which one you’re using, I can give you the exact backup/export steps and, if needed, a way to convert those favorites into a VLC or PotPlayer playlist.[5][1]

## Human

where's my ini file?

## Assistant

Short answer: if MPC-HC is actually using an INI file, it lives **in the same folder as the MPC-HC executable**, with (almost) the same name as the `.exe` — e.g. `mpc-hc.ini`, `mpc-hc64.ini` or `mplayerc.ini` in the install/portable directory.[1][2]

## Check if you’re using INI mode

1. In MPC-HC, go to **View → Options… → Player**.
2. Look for **“Store settings to .ini file”**.
   - If checked (and not greyed out), MPC-HC writes settings (including favorites) to an INI instead of the registry.[3][4]
   - If unchecked or greyed out, there may be **no INI file**, and settings are in the registry/appdata instead.[5][6]

## Default INI location

When INI mode is enabled, MPC-HC builds the INI path from the program path:

- It takes the full path to the `.exe` and just swaps the extension to `.ini`.[1]
- So if your player is at:
  - `C:\Program Files\MPC-HC\mpc-hc64.exe`  
    then the INI will be:
  - `C:\Program Files\MPC-HC\mpc-hc64.ini` .[2][1]

Common places to check on Windows:

- `C:\Program Files\MPC-HC\`
- `C:\Program Files (x86)\MPC-HC\`
- Inside the **K-Lite Codec Pack** folder if you installed MPC-HC with K-Lite, e.g.  
  `C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64.ini`.[7]

If you use a fully portable ZIP version, the INI will be in **whatever folder you extracted MPC-HC into**, next to `mpc-hc.exe` / `mplayerc.exe`.[2]

## Why you might not see it

- If **“Store settings to .ini file”** is off, MPC-HC uses **registry / AppData** only, so no INI is created.[6][5]
- If MPC-HC is installed under `Program Files` and doesn’t have write permissions, it may fail to create/update the INI until you run it with appropriate rights or move it elsewhere.[8][6]

## Concrete next step

- Open MPC-HC → **View → Options → Player** and confirm the **“Store settings to .ini file”** checkbox state.
- Then:
  - If checked: locate `mpc-hc*.exe` on disk, and in that same folder you should find the matching `*.ini`.
  - If not checked: we’ll instead look at your registry keys for favorites.

If you tell me your MPC-HC build (32/64-bit, K-Lite vs standalone) and approximate install path, I can give you the exact INI or registry path to copy.  

## Human

C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64

## Assistant

Given that path, your MPC-HC64 INI file (if it exists) will be in **that same folder**:  

`C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64.ini` or `mpc-hc.ini`.[1][2]

## What to check right now

1. Open File Explorer and go to:  
   `C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64`
2. Look for any of these files:
   - `mpc-hc64.ini`
   - `mpc-hc.ini`
   - occasionally `mplayerc.ini` (older builds).[2][3]

If **none** of those exist, your K-Lite MPC-HC is almost certainly using **registry mode**, not INI mode, and you’ll need to switch it or read favorites from the registry.[4][2]

## Verify in MPC-HC itself

Inside MPC-HC64 (the one from K-Lite):

1. Go to **View → Options → Player**.
2. Check **“Store settings to .ini file”**:
   - If checked: MPC-HC will create/use `mpc-hc64.ini` in `C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64` when you close the player.[5][2]
   - If unchecked: settings (including favorites) live in the **registry**, and there will be no INI file.[2][4]

If you tell me whether you see `mpc-hc64.ini` in that folder and whether “Store settings to .ini file” is checked, I can give you exact steps to extract your favorites and convert them into a playlist.  

## Human

it's not there

## Assistant

If there’s no INI file in that folder, your K-Lite MPC-HC64 is almost certainly using the **registry** for settings and favorites instead of an INI file.[1][2]

## Where your favorites are now

For a normal (non‑portable) MPC-HC install, favorites are stored under this registry key:

- `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files` .[2][1]

Older Gabest-era MPC builds used:

- `HKEY_CURRENT_USER\Software\Gabest\Media Player Classic\Favorites` .[1]

Since you’re on K-Lite MPC-HC64 and there’s no `.ini` in  
`C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64`, the active location is almost certainly the **`MPC-HC\MPC-HC\Favorites`** branch in your user registry hive.[3][2]

## How to confirm and view the favorites

1. Press **Win + R**, type `regedit`, press Enter.
2. Navigate to:  
   `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files` .[2]
3. You should see values that contain:
   - paths to the video files, and
   - possibly stored positions/extra metadata for each favorite.[4][1]

If that key exists and has entries, those are your favorites. If it doesn’t, check the older Gabest path above just in case you have a very old MPC build.[1]

## Why no INI file exists

- In K-Lite’s MPC-HC, **“Store settings to .ini file”** is often **disabled or unchecked by default**, so MPC-HC writes to the registry only.[5][6]
- An INI file (`mpc-hc64.ini`) will only be created if that option is enabled and MPC-HC can write to its install folder.[6][7]

So: “no INI file” is expected behavior for your setup, not a bug.

## Next step if your goal is migration

If you want to migrate favorites into another player or into a playlist file, the next step is to:

- Export that registry branch (right‑click `Favorites` → **Export**), which gives you a `.reg` file with all the paths.[4][2]
- From there, we can parse the file paths and generate a playlist (`.m3u` or `.xspf`) for VLC/other players.

If you’re comfortable using PowerShell, I can give you a one‑liner or small script that:

- reads `Favorites\Files` from the registry,
- extracts the file paths,
- writes them out as a `.m3u` playlist you can open directly in VLC or PotPlayer.

Would you like a PowerShell script to turn your MPC-HC favorites registry entries into a VLC-compatible `.m3u` playlist?  

## Human

yes please

## Assistant

Here’s a focused **PowerShell script** that reads MPC-HC favorites from the registry and writes them to a **VLC-compatible `.m3u` playlist**. This assumes your favorites are in the standard MPC-HC key (K-Lite install, registry mode).[1][2]

## 1. Registry path assumptions (FACT)

For K-Lite MPC-HC64 with registry settings, favorites are typically stored under:

- `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files` .[2][1]

Each value usually contains a file path (and possibly timing info); for building a playlist we care about the paths.[3][1]

If your install differs, we can adjust the `-Path` later.

## 2. PowerShell script to create `.m3u` (CONSENSUS, high confidence)

Open **PowerShell** and run the script below. You can paste it into a `.ps1` file or run it directly in a console.

```powershell
# --- CONFIGURE THESE IF YOU WANT TO CHANGE OUTPUT LOCATION ---
$playlistName = "mpc-favorites.m3u"
$playlistPath = Join-Path $env:USERPROFILE $playlistName

# MPC-HC favorites registry key (current user)
$mpcFavoritesKey = "HKCU:\Software\MPC-HC\MPC-HC\Favorites\Files"

Write-Host "Reading MPC-HC favorites from: $mpcFavoritesKey"
Write-Host "Playlist will be written to:  $playlistPath"
Write-Host ""

# Try to get the registry key
try {
    $regItem = Get-Item $mpcFavoritesKey -ErrorAction Stop
} catch {
    Write-Host "ERROR: Could not open registry key:"
    Write-Host "  $mpcFavoritesKey"
    Write-Host "Check if MPC-HC is using this path or an older Gabest path."
    return
}

# Get all value entries under the key
$values = Get-ItemProperty -Path $mpcFavoritesKey

# Collect file paths
$filePaths = @()

foreach ($prop in $values.PSObject.Properties) {
    # Skip default metadata properties
    if ($prop.Name -in @("PSPath","PSParentPath","PSChildName","PSDrive","PSProvider")) {
        continue
    }

    $rawValue = [string]$prop.Value

    # Some favorites entries include extra data (position, etc.).
    # Common pattern: path|timestamp or path;timestamp.
    # We heuristically take the first "segment" that looks like a path.
    # This is SPECULATION but usually works in practice [web:14][web:84].
    $candidate = $rawValue

    # If there is a '|' separator, take part before the first '|'
    if ($candidate -like "*|*") {
        $candidate = $candidate.Split("|")[0]
    } elseif ($candidate -like "*;*") {
        # Sometimes ';' is used as separator
        $candidate = $candidate.Split(";")[0]
    }

    # Basic sanity check: must look like a drive-based or UNC path
    if ($candidate -match "^[A-Za-z]:\\" -or $candidate -like "\\*") {
        $filePaths += $candidate
    }
}

if ($filePaths.Count -eq 0) {
    Write-Host "No valid file paths were found in favorites registry key."
    Write-Host "Raw values might use a different format; script may need adjustment."
    return
}

Write-Host "Found $($filePaths.Count) favorite entries."
Write-Host ""

# Build M3U content
# M3U: first line is #EXTM3U (optional but recommended), then one path per line
$m3uLines = @()
$m3uLines += "#EXTM3U"

foreach ($path in $filePaths) {
    $m3uLines += $path
}

# Write to file
$m3uContent = $m3uLines -join "`r`n"
Set-Content -Path $playlistPath -Value $m3uContent -Encoding UTF8

Write-Host "Playlist written."
Write-Host "Open '$playlistPath' with VLC, PotPlayer, or MPC-HC to play all favorites."
```

### What this script does (FACT)

- Reads all values under `HKCU\Software\MPC-HC\MPC-HC\Favorites\Files`.[1][2]
- Extracts what looks like a file path, ignoring extra timing metadata (best-effort heuristic).[3][1]
- Writes a standard `.m3u` playlist with one path per line, plus `#EXTM3U` header.[4][5]
- Saves it to `C:\Users\<you>\mpc-favorites.m3u`.

Confidence: **High** for standard MPC-HC (post-MPC-HC fork) and K-Lite builds using the documented favorites key; **medium** for very old Gabest-era MPC, in which case the key path might differ.[2][1]

## 3. How to load the playlist in VLC (FACT)

Once `mpc-favorites.m3u` exists:

- Open **VLC** → **Media → Open File…** and choose `mpc-favorites.m3u`, or
- Drag-and-drop the `.m3u` file onto VLC; it will populate the playlist and play sequentially.[5][4]

Same idea works for **PotPlayer** and even back into MPC-HC itself (File → Open File, point to the `.m3u`).[6][7]

## 4. If the registry key path is different (SPECULATION, medium confidence)

On some installs, especially older ones, the path might be:

- `HKCU\Software\Gabest\Media Player Classic\Favorites`.[1]

If the script prints “Could not open registry key”, change:

```powershell
$mpcFavoritesKey = "HKCU:\Software\MPC-HC\MPC-HC\Favorites\Files"
```

to:

```powershell
$mpcFavoritesKey = "HKCU:\Software\Gabest\Media Player Classic\Favorites"
```

and re-run.

***

If you run this and it doesn’t pick up any paths (or the values look very different when you inspect them in `regedit`), paste one or two raw registry value examples here and I’ll adjust the parsing logic to match your exact favorites format.

## Human

writing to mpc playlist would be better, or are they the same thing?

## Assistant

They’re **not** the same thing. An MPC-HC **playlist** is a `.mpcpl` file with a specific text format, while your **favorites** are registry entries (or INI entries) containing paths plus optional metadata. Writing directly to an MPC playlist (`.mpcpl`) is better if your goal is to keep using MPC-HC (or related players) with a native playlist file you can open, edit, and back up.[1][2][3][4][5]

## Favorites vs `.mpcpl` playlist (FACT)

- **Favorites**
  - Stored in registry or INI, not as a standalone file by default.[5][6]
  - Good for quick access inside MPC-HC, but harder to migrate to other players without extraction.[7][5]
- **`.mpcpl` playlist**
  - A plain-text file that MPC-HC and similar players open as a playlist.[4][1]
  - Lives wherever you save it (e.g. alongside your videos), easy to copy, sync, or feed into scripts.[8][3]

For migration, a `.mpcpl` is strictly more flexible than leaving things as registry favorites.

## What an `.mpcpl` looks like (FACT)

A minimal MPC-HC playlist file looks like this:[9][1]

```text
MPCPLAYLIST
1,type,0
1,filename,D:\Videos\clip1.mkv
2,type,0
2,filename,D:\Videos\clip2.mp4
```

Key points:

- First line: `MPCPLAYLIST` (header).[1]
- Each item has an index (`1`, `2`, …).
- For each index:
  - `N,type,0` means a normal file entry.
  - `N,filename,<full-or-relative-path>` is the path.[9][1]
- Optional fields like `label`, `subtitle`, or `ydlSourceURL` can be present but are not required for basic use.[10][11]

MPC-HC can also save `.m3u` playlists, but `.mpcpl` is the **native** format and is what K-Lite MPC-HC64 uses by default when you “Save As” from the playlist window.[3][12][8]

## Why writing `.mpcpl` is “better” (CONSENSUS, high confidence)

If you stay in MPC-HC:

- **Pros of `.mpcpl`:**
  - MPC-HC reads and writes `.mpcpl` natively; you can open it via File → Open or drag-and-drop.[8][3]
  - K-Lite and portable builds recognize `.mpcpl` as “MPC Playlist File” associated with `mpc-hc64.exe`.[2][13]
  - Paths can be absolute or relative; relative paths make it easier to move your video folders and playlists together.[14][8]

Compared to writing `.m3u`:

- `.m3u` is more cross-player friendly (VLC, PotPlayer, etc.).[15][16][17]
- `.mpcpl` is more feature-complete and reliable inside MPC-HC (and close derivatives like MPC-BE).[4][1][9]

So if your **primary target is MPC-HC**, generating `.mpcpl` from favorites is better than `.m3u`. If you want maximum portability across players, `.m3u` still wins.

## What changes in the script to write `.mpcpl` instead (SPECULATION, medium confidence)

The registry reading part we discussed still applies; only the **output format** changes:

1. Same PowerShell logic to:
   - read values from `HKCU\Software\MPC-HC\MPC-HC\Favorites\Files`;
   - extract file paths ([this remains the “hard” part]).
2. Instead of `#EXTM3U` + one path per line, you:
   - Write `MPCPLAYLIST` as first line.
   - For each path, write:
     - `N,type,0`
     - `N,filename,<path>`

Example skeleton:

```powershell
$m3uPaths = $filePaths  # from previous script

$lines = @()
$lines += "MPCPLAYLIST"

$index = 1
foreach ($path in $m3uPaths) {
    $lines += "$index,type,0"
    $lines += "$index,filename,$path"
    $index++
}

$playlistPath = Join-Path $env:USERPROFILE "mpc-favorites.mpcpl"
Set-Content -Path $playlistPath -Value ($lines -join "`r`n") -Encoding UTF8
```

Then `mpc-favorites.mpcpl` becomes a native MPC-HC playlist you can open and play.[2][1][8]

## Are `.mpcpl` and `.m3u` interchangeable?

- MPC-HC can read both `.mpcpl` and `.m3u` (with some quirks).[12][9]
- Other players (VLC, PotPlayer, etc.) generally read `.m3u` but **do not** understand `.mpcpl`.[17][15][2]

So they are **not** equivalent:

- `.mpcpl`: MPC-specific, richer, best if you stay with MPC-HC.
- `.m3u`: generic, best if you want cross-player compatibility.

Given your setup (K-Lite MPC-HC64 as primary) and goal (“play all favorites as a playlist”), I’d suggest:

- Generate **both**:
  - one `.mpcpl` for long-term MPC-HC use,
  - optionally one `.m3u` for other players or future migration.

Do you want me to rewrite the previous PowerShell script so it outputs a **`.mpcpl` playlist** instead of `.m3u`, while keeping all the registry-reading logic the same?

## Human

Yes please, use the path I gave you if needed

## Assistant

Got it. Since your MPC-HC64 lives at:

`C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64`

we’ll generate a **native MPC-HC `.mpcpl` playlist** and drop it in that folder so you can open it directly in MPC-HC64.

Below is a **complete PowerShell script** that:

- reads favorites from the MPC-HC registry key,
- extracts file paths,
- writes an `mpc-favorites.mpcpl` playlist into your MPC-HC64 folder using the `.mpcpl` format MPC-HC expects.[1][2][3]

***

## PowerShell script: favorites → `mpc-favorites.mpcpl`

Run this in **PowerShell** (as your user). If your MPC-HC favorites key is standard, it should just work.

```powershell
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

    # Favorites values often store "path|position" or similar; we only want the path.
    # Heuristic: take the substring before the first '|' or ';' if present.
    $candidate = $rawValue

    if ($candidate -like "*|*") {
        $candidate = $candidate.Split("|")[0]
    } elseif ($candidate -like "*;*") {
        $candidate = $candidate.Split(";")[0]
    }

    # Basic sanity: must look like a Windows path (drive letter or UNC)
    if ($candidate -match "^[A-Za-z]:\\" -or $candidate -like "\\*") {
        $filePaths += $candidate
    }
}

if ($filePaths.Count -eq 0) {
    Write-Host "No valid file paths were extracted from the favorites registry key."
    Write-Host "Open regedit at:"
    Write-Host "  HKEY_CURRENT_USER\\Software\\MPC-HC\\MPC-HC\\Favorites\\Files"
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
    # 'type,0' means a normal media file entry [web:88][web:94]
    $lines += "$index,type,0"
    $lines += "$index,filename,$path"
    $index++
}

# Write playlist to the MPC-HC folder
$playlistContent = $lines -join "`r`n"

Set-Content -Path $playlistPath -Value $playlistContent -Encoding UTF8

Write-Host "Playlist written to:"
Write-Host "  $playlistPath"
Write-Host "You can now open this .mpcpl file in MPC-HC64 to play all favorites as a playlist."
```

***

## How to use the generated playlist (FACT)

After running the script:

1. In MPC-HC64, go to  
   **File → Open File…**
2. Browse to:  
   `C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-favorites.mpcpl`
3. Open it; MPC-HC will load the playlist and you can start playback from the playlist window.[3][4][5]

You can also drag `mpc-favorites.mpcpl` from Explorer onto MPC-HC’s window to load it directly.[6][3]

***

## If the favorites key is different

If the script errors with “Could not open registry key”, your favorites might be under the older Gabest path:

- `HKCU:\Software\Gabest\Media Player Classic\Favorites` .[1]

In that case, change this line:

```powershell
$mpcFavoritesKey = "HKCU:\Software\MPC-HC\MPC-HC\Favorites\Files"
```

to:

```powershell
$mpcFavoritesKey = "HKCU:\Software\Gabest\Media Player Classic\Favorites"
```

and re-run.

***

If you’d like, you can paste one sample value from `Favorites\Files` (from regedit), and I’ll tighten the parsing so it correctly handles whatever extra metadata MPC-HC is storing with each favorite.
