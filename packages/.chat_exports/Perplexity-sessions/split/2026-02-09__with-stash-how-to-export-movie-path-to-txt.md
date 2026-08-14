---
title: "with stash how to export movie path to txt?"
date: "2026-02-09"
mode: "CONCISE"
uuid: "0d9493b0-9bca-4155-b77f-2d030a01a0ff"
entry_count: 4
---

## Human

with stash how to export movie path to txt?

## Assistant

In Stash (the self‑hosted video organizer), you can get file paths into a text file by exporting metadata and then extracting the paths from the JSON.[1]

### Option 1 – Built‑in full export + simple parsing

1. In Stash, go to **Tasks → Metadata → Full export** and run it. This creates a metadata folder tree (files, scenes, etc.) on disk.[1]
2. Inside the export, look in the `files` or `scenes` JSON files; each entry includes the absolute file path for the video file.[1]
3. Use a quick script (Python, jq, etc.) to read that JSON and write just the `path` field to `paths.txt`.

Example with `jq` (Linux/macOS, or Windows with jq):

```bash
jq -r '.[].path' files.json > paths.txt
```

If the path is nested (e.g., `.[].file.path`), adjust accordingly.

### Option 2 – GraphQL query for scenes → txt

If you are comfortable calling Stash’s GraphQL API, query the `findScenes` or `findFiles` fields and dump the `path` field from the response to a text file (same idea as above, but without doing a full export).[2][1]

If you tell me exactly what you mean by “movie” in your setup (Stash “Movies” entity vs. underlying scene files, and OS), I can give you a ready‑to‑run command/script that outputs one path per line to a `.txt`.

## Human

not a scene, the video file path, windows 11

## Assistant

On Windows 11, the simplest way is to use Stash’s JSON **Files** export and then extract the `path` field into a `.txt`.[1]

### Step 1 – Export all file metadata from Stash

1. In Stash, go to **Tasks → Metadata → Full export**.[1]
2. Note the **metadata path** in your config; the export will create a `files` subfolder there containing JSON for every video file.[2][1]

Typical folder after export (example):

```text
D:\Stash\metadata\
  files\
    00.filename.hash.json
    01.otherfile.hash.json
    ...
```

Each “Video file” JSON has a structure that includes a `path` field with the full video file path.[1]

### Step 2 – Extract all video file paths to TXT (PowerShell)

In PowerShell, cd to the `files` export directory, for example:

```powershell
Set-Location "D:\Stash\metadata\files"
```

Then run:

```powershell
Get-ChildItem -Filter *.json -Recurse |
  Get-Content |
  ConvertFrom-Json |
  Where-Object { $_.type -eq 'video' } |
  Select-Object -ExpandProperty path |
  Set-Content "D:\Stash\video_paths.txt"
```

Explanation:

- `type -eq 'video'` limits it to actual video files.[1]
- `path` is the field in each exported “Video file” entry that holds the video file’s filesystem path.[1]
- `video_paths.txt` will contain one absolute video path per line.

If your export directory is different, just adjust the two `D:\Stash\...` paths.

## Human

PS C:\\Users\\brsth\\Downloads\\export20260209-084830\\scenes> Get-ChildItem -Filter *.json -Recurse |
>>   Get-Content |
>>   ConvertFrom-Json |
>>   Where-Object { $_.type -eq 'video' } |
>>   Select-Object -ExpandProperty path |
>>   Set-Content "video_paths.txt"
ConvertFrom-Json:
Line |
   3 |    ConvertFrom-Json |
     |    ~~~~~~~~~~~~~~~~
     | Conversion from JSON failed with error: Additional text encountered after finished reading JSON content: {. Path '', line 9, position 0.
PS C:\\Users\\brsth\\Downloads\\export20260209-084830\\scenes>

## Assistant

Each file in `scenes\` is a full scene object, so concatenating them and calling `ConvertFrom-Json` fails because PowerShell expects one JSON document, not many.[1]

### Use the `files\` export instead

The **video file paths** live in the `files\` export, not the `scenes\` export.[1]

1. Go to your export root (same level as `scenes`):

   ```text
   C:\Users\brsth\Downloads\export20260209-084830\
     files\
     scenes\
     performers\
     ...
   ```

2. `cd` into `files` and run this PowerShell:

   ```powershell
   Set-Location "C:\Users\brsth\Downloads\export20260209-084830\files"

   Get-ChildItem -Filter *.json -Recurse |
     ForEach-Object {
       Get-Content $_.FullName -Raw | ConvertFrom-Json
     } |
     Where-Object { $_.type -eq 'video' } |
     Select-Object -ExpandProperty path |
     Set-Content "C:\Users\brsth\Downloads\video_paths.txt"
   ```

   - `-Raw` reads each file as a single JSON string so `ConvertFrom-Json` parses one object at a time.[1]
   - `type -eq 'video'` and `path` match the documented “Video file” export structure.[1]

### If you really want to work from `scenes\`

`scenes` JSON doesn’t contain the full file path in the documented bulk-export spec, only scene metadata and a `file` object with technical info.[1]
So for a clean list of actual filesystem paths, the `files\` export is the correct source.

## Human

how do I export for files?

## Assistant

To get the `files` export, you run a **Full export** of metadata; Stash always includes a `files` folder in that export.[1][2]

### 1. Run the full metadata export

1. In Stash, open the web UI.  
2. Go to **Tasks → Metadata**.[2]
3. Click **Full export** and let it finish. This writes JSON to your configured metadata/export directory.[2]

The exported structure is documented as:[1]

```text
<export root>\
  files\
  galleries\
  images\
  performers\
  scenes\
  studios\
  groups\
```

So if your current path is:

```text
C:\Users\brsth\Downloads\export20260209-084830\scenes
```

then the `files` export you want should be at:

```text
C:\Users\brsth\Downloads\export20260209-084830\files
```

### 2. Extract video file paths on Windows

From an elevated or normal PowerShell:

```powershell
Set-Location "C:\Users\brsth\Downloads\export20260209-084830\files"

Get-ChildItem -Filter *.json -Recurse |
  ForEach-Object {
    Get-Content $_.FullName -Raw | ConvertFrom-Json
  } |
  Where-Object { $_.type -eq 'video' } |
  Select-Object -ExpandProperty path |
  Set-Content "C:\Users\brsth\Downloads\video_paths.txt"
```

In the `files` export, each “Video file” object has `type = "video"` and a `path` field with the full filesystem path, matching the JSON spec.[1]
