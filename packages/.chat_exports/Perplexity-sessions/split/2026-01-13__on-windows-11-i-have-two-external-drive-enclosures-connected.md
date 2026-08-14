---
title: "On Windows 11 I have two external drive enclosures connected with USB-C. Can I unplug the USB-C cable without any harm?"
date: "2026-01-13"
mode: "CONCISE"
uuid: "0584b68c-da1b-4f7e-a97b-63ec191e12b9"
entry_count: 1
---

## Human

On Windows 11 I have two external drive enclosures connected with USB-C. Can I unplug the USB-C cable without any harm?

## Assistant

No, unplugging USB-C cables from external drive enclosures on Windows 11 without safely ejecting can risk data corruption or loss if write operations are pending, though the default "Quick removal" policy minimizes this for most setups.[1][2][3]

## Default Policy
External USB drives, including those in enclosures connected via USB-C, default to "Quick removal" in Windows 11. This disables write caching, allowing unplugging without the "Safely Remove Hardware" process while prioritizing safety over peak performance.[4][2][5][6]

## Potential Risks
Abrupt removal during active reads or writes—even under Quick removal—can corrupt files or damage the file system on HDDs or SSDs in enclosures. Multiple drives increase the chance of background activity, like indexing or backups.[7][8][3][1]

## Safe Removal Steps
- Right-click the "Safely Remove Hardware" icon in the system tray (expand hidden icons if needed), select the drive, and wait for "Safe to Remove Hardware."[9][1]
- Or, right-click the drive in File Explorer and choose "Eject."[10]
- In Settings > System > Storage > Disks & volumes, check properties for each drive.[4]

## Check Your Policy
Open Disk Management (diskmgmt.msc), right-click the drive label, select Properties > Policies, and confirm "Quick removal" (default safe for unplugging). Switch to "Better performance" only if needed for speed, but always eject then.[2][6][4]
