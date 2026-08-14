---
title: "with qbittorent, when I would add torrent files from my HDD, when they got added to qbittorent, they would be deleted fr"
date: "2025-12-28"
mode: "COPILOT"
uuid: "c58323bc-ec85-470d-a7cf-37eaac895a8b"
entry_count: 1
---

## Human

with qbittorent, when I would add torrent files from my HDD, when they got added to qbittorent, they would be deleted from the HDD, now they don't.  why?

## Assistant

Most likely a qBittorrent setting changed (or a version upgrade reset it), so the “delete .torrent after adding” behavior is no longer enabled, and qBittorrent now just copies the torrent into its own BT_backup folder without touching your original file.[1][2]

## What qBittorrent normally does

- When you add a torrent, qBittorrent stores its own copy of the metadata under its profile (e.g. `BT_backup`), so the original `.torrent` on your HDD is not required anymore.[2]
- By default, qBittorrent does **not** track or manage your original `.torrent` files after adding; deleting them is treated as your responsibility unless you enable a specific “delete after adding” option or use a watch folder with that flag.[3][1]

## Why they used to be deleted

There are three common ways you could have had automatic deletion before:

- **“Delete .torrent files afterwards” for watched folders**  
  In `Tools → Options → Downloads` (or BitTorrent/Downloads depending on version), there is an option for automatically added torrents from specific folders to “Delete .torrent files afterwards”. If that was enabled before and is now off, your HDD torrent files will remain.[4][5]

- **Using a watched folder with an external tool**  
  Some setups (Sonarr/Radarr/etc.) rely on qBittorrent’s auto-add + delete flags so that any `.torrent` dropped in a folder is both added and then deleted. If something changed (new path, different client profile, or option reset), they will stop being removed.[6][7]

- **Config reset after upgrade / profile change**  
  qBittorrent 5.x introduced changes around trash/removal behavior, and configuration resets or profile changes can affect how file deletion works. A reset could have turned off the “delete .torrent after adding” checkbox, so the original torrent files now stay on disk.[8][5]

## What to check in your setup

On your Windows 11 box, open qBittorrent and verify:

- Under **Options → Downloads** (and any **Watched folders / Automatically add torrents from** section):  
  - Confirm if there is an option like **“Delete .torrent files afterwards”** and whether it is currently unchecked.[5][4]
- If you recently:
  - Upgraded qBittorrent (especially to 5.x)  
  - Changed profiles, reinstalled, or moved config folders  
  then your old setting could have been lost, reverting to the default of **not** deleting the source `.torrent` file.[8][5]

If you want the old behavior back, re-enable that “delete .torrent files afterwards” option in the relevant auto-add/watched-folder configuration, or explicitly delete/clean up `.torrent` files via a script or file manager after adding them.[4][5]
