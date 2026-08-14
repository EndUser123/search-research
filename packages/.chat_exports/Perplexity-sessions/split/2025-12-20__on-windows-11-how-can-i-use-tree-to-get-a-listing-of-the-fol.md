---
title: "On windows 11, how can I use 'tree' to get a listing of the folders, but not __pycache__, .cache, etc?  Just the folders"
date: "2025-12-20"
mode: "COPILOT"
uuid: "12913312-2021-464f-bb63-5b7fe052c1fd"
entry_count: 3
---

## Human

On windows 11, how can I use "tree" to get a listing of the folders, but not __pycache__, .cache, etc?  Just the folders that are important for software developmenet.

## Assistant

On Windows 11, the built-in `tree` command lacks built-in exclude options, so use PowerShell's `Get-ChildItem` (aliased as `dir` or `ls`) with filtering for a customizable directory tree listing that skips common development clutter like `__pycache__`, `.cache`, `node_modules`, `.git`, `venv`, and `dist`.  This approach shows only relevant software development folders (source code, configs, docs) in a tree-like format via recursion and indentation.[1][2][3][4][5]

## PowerShell One-Liner
Run this in PowerShell from your project root to list directories only, excluding dev cache/junk:

```
gci -Directory -Recurse | ?{$_.Name -notin '__pycache__','.cache','node_modules','.git','venv','env','dist','build','.vs','.vscode-test'} | %{"  "*($_.PSPath.Split('\').Count-3)+$_.Name}
```

Adjust the exclude list (`-notin` array) for your needs—add patterns like `'*test*'` with `-notlike "*test*"`.[5][1]

## Custom Tree Function
For reusable tree output, define this function in your PowerShell profile (`$PROFILE`) or run it once per session:

```
function Show-Tree { param([string]$Path='.',[string[]]$Exclude=@('__pycache__','.cache','node_modules','.git','venv','env','dist','build')) gci -Path $Path -Directory -Recurse | ?{$_.Name -notin $Exclude} | %{"  "*($_.PSPath.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries).Count-2)+$_.Name} }
```

Usage: `Show-Tree` or `Show-Tree C:\MyProject -Exclude @('__pycache__','custom-junk')`. It indents based on depth for a clean tree view.[1][5]

## Advanced Filtering Tips
- **Hidden folders**: Add `-Force` to `gci` if needed, then filter `?{-not $_.Attributes.HasFlag([IO.FileAttributes]::Hidden)}`.[4]
- **Regex excludes**: Use `-notmatch` for patterns: `?{$_.Name -notmatch '(pycache|cache|node)'}`. [5]
- **Output to file**: Append `| Out-File tree.txt` for docs. [6]
- Matches your VS Code/PowerShell workflow for quick project overviews.[7]

## Human

can we limit it to the top 5 folders?

## Assistant

Yes, limit the PowerShell tree to the top 5 immediate subfolders (non-excluded) using `Select-Object -First 5` on the first-level `-Directory` results before recursing.  This keeps output concise for quick project scans in your dev workflow.[1][2]

## Modified One-Liner
```
gci -Directory | ?{$_.Name -notin '__pycache__','.cache','node_modules','.git','venv','env','dist','build'} | select -First 5 | %{$_.Name; gci $_.FullName -Directory -Recurse | ?{$_.Name -notin '__pycache__','.cache','node_modules','.git','venv','env','dist','build'} | %{"  "*($_.PSPath.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries).Count-2)+$_.Name}}
```

Pipes first-level dirs (top 5 after exclude/sort), then recurses into each with indentation.[1][3]

## Updated Tree Function
Add `-Top` param for flexibility:

```
function Show-Tree { param([string]$Path='.',[string[]]$Exclude=@('__pycache__','.cache','node_modules','.git','venv','env','dist','build'),[int]$Top=0) $topDirs = gci -Path $Path -Directory | ?{$_.Name -notin $Exclude} | sort Name | select -First $Top; if($Top -eq 0){$topDirs} foreach($dir in $topDirs){$dir.Name; gci $dir.FullName -Directory -Recurse | ?{$_.Name -notin $Exclude} | %{"  "*($_.PSPath.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries).Count-2)+$_.Name}} }
```

Usage: `Show-Tree -Top 5` (or omit for all). Sort by `LastWriteTime` or `Get-ChildItem | Sort Length -Desc` for size-based top 5. [1]

## Human

that does't seem to limit the depth.

## Assistant

Yes, add PowerShell 5.0+ `-Depth` parameter to limit recursion depth (e.g., 2 for top-level + one sublevel) while keeping top 5 folders and exclusions.  This prevents deep nesting in your project trees.[1][2][3][4]

## Updated One-Liner
Limit to top 5 first-level folders, recurse only 2 deep total (adjust `-Depth 2` as needed):

```
gci -Directory | ?{$_.Name -notin '__pycache__','.cache','node_modules','.git','venv','env','dist','build'} | select -First 5 | %{$_.Name; gci $_.FullName -Directory -Recurse -Depth 2 | ?{$_.Name -notin '__pycache__','.cache','node_modules','.git','venv','env','dist','build'} | %{"  "*($_.PSPath.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries).Count-2)+$_.Name}}
```

`-Depth 1` shows only immediate subfolders; `-Depth 0` skips recursion entirely.[5][1]

## Enhanced Tree Function
Add `-Depth` and `-Top` params for full control:

```
function Show-Tree { param([string]$Path='.',[string[]]$Exclude=@('__pycache__','.cache','node_modules','.git','venv','env','dist','build'),[int]$Top=0,[int]$Depth=999) $topDirs = gci -Path $Path -Directory | ?{$_.Name -notin $Exclude} | sort Name | select -First $Top; if($Top -eq 0 -or $Top -ge 999){$topDirs} foreach($dir in $topDirs){$dir.Name; gci $dir.FullName -Directory -Recurse -Depth $Depth | ?{$_.Name -notin $Exclude -and $_.FullName -ne $dir.FullName} | %{"  "*($_.PSPath.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries).Count-2)+$_.Name}} }
```

Usage: `Show-Tree -Top 5 -Depth 2`. Fits your Python/VS Code project scans perfectly.[4][6]
