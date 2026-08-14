---
title: "I have 8000 torrent files in qbittorent, but the website path has changed.  How can I mass change them all to point to t"
date: "2026-01-05"
mode: "COPILOT"
uuid: "9385412e-d733-471a-ba52-7290f6a5746c"
entry_count: 2
---

## Human

I have 8000 torrent files in qbittorent, but the website path has changed.  How can I mass change them all to point to the right comment website?

## Assistant

qBittorrent stores torrent metadata, including comments, in .torrent files within the BT_backup directory on Windows, typically at `%LOCALAPPDATA%\qBittorrent\BT_backup` (expand via `%LOCALAPPDATA%` in File Explorer).[1][2]

These bencoded files hold the "comment" field containing the website URL or description you want to update.[3][4]

## Locate BT_backup
Open PowerShell or Command Prompt and run `explorer.exe $env:LOCALAPPDATA\qBittorrent\BT_backup` to access the folder with ~8000 .torrent and .fastresume files paired by hash.[5][1]

## Edit with Python Script
Use a Python script leveraging the `bencode.py` library to batch replace old website strings in comments. Install via `pip install bencode.py`, then run code like this (backup BT_backup first via `Compress-Archive BT_backup BT_backup_backup.zip`):

```python
import os
import bencode
import glob

bt_backup = os.path.expandvars(r'%LOCALAPPDATA%\qBittorrent\BT_backup')
old_url = 'https://old.website.com'  # Replace with your old path
new_url = 'https://new.website.com'  # Replace with your new path

for torrent_file in glob.glob(os.path.join(bt_backup, '*.torrent')):
    with open(torrent_file, 'rb') as f:
        data = bencode.decode(f.read())
    
    if 'comment' in data['info']:
        data['info']['comment'] = data['info']['comment'].replace(old_url, new_url)
    
    with open(torrent_file, 'wb') as f:
        f.write(bencode.encode(data))

print('Updated all torrent comments.')
```

Relaunch qBittorrent or right-click torrents > Force recheck to refresh displays.[3]

## Alternative: WebUI JavaScript
Enable WebUI, open browser console on `/torrents` page, and adapt scripts from tracker edits to list properties and update if a comment endpoint exists (check API docs), but direct BT_backup editing is more reliable for comments.[6][7]

## Human

do I have to shutdown qbittorent first or export torrents?

## Assistant

No, shutting down qBittorrent or exporting torrents is not strictly required, but closing it first is strongly recommended to prevent file locks or corruption during edits.[1]

## Risks Without Shutdown
qBittorrent keeps BT_backup files open for active torrents, risking write conflicts or incomplete saves on Windows.[2]

Closing ensures clean access; restart after edits and force recheck torrents to sync changes.[3]

## Quick Workflow
- Pause all torrents or exit qBittorrent fully via system tray.
- Backup BT_backup: `Compress-Archive $env:LOCALAPPDATA\qBittorrent\BT_backup BT_backup_$(Get-Date -Format 'yyyyMMdd').zip`
- Run the Python script.
- Relaunch qBittorrent; changes appear immediately or after recheck.[1]
