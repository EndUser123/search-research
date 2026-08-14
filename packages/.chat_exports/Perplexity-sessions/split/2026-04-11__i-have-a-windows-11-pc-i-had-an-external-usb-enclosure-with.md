---
title: "I have a windows 11 PC.  I had an external usb enclosure with a running HDD.  I kicked it by mistake.  Now the drive won"
date: "2026-04-11"
mode: "COPILOT"
uuid: "9d515b04-6239-44d2-bc26-6c113765a7d3"
entry_count: 1
---

## Human

I have a windows 11 PC.  I had an external usb enclosure with a running HDD.  I kicked it by mistake.  Now the drive won't show up in Windows.  How can I make it come back?

## Assistant

Since you kicked the enclosure and the drive is physically damaged, here's the troubleshooting sequence:

## Hardware-Level Checks

**First, verify the drive is actually being detected at all.**  Start with basic checks:  ensure the USB is firmly inserted and try a different USB port directly on your motherboard (back of PC) rather than a front panel port.  Also try a different USB cable, as physical damage could have affected the connector.  Test the enclosure on a different computer—if it works elsewhere, your system settings are the issue, not the hardware.[1][2][3]

## Disk Management Inspection

**If the drive shows any sign of life, check Disk Management.**  Open Device Manager (right-click Start), look for any devices with exclamation marks, then uninstall and rescan for hardware changes.  Open Disk Management (Win + X > Disk Management) and select **Action > Rescan Disks**.  The drive may appear as "Unallocated" if the partition table was damaged by the impact. If it does appear but shows as Unallocated, you can right-click and select **New Simple Volume** to format it (this erases data).[4][1]

## Driver Updates

 If the drive shows in Device Manager with a yellow exclamation mark, expand **Disk Drives** and **Universal Serial Bus** listings, right-click the drive, choose **Properties**, and try updating the driver from the **Driver** tab.  If updates fail, try uninstalling and restarting your PC to force driver reinstallation.[5][6]

## Data Recovery Consideration

**Before reformatting**, assess the damage severity.  If the drive is detected in another PC, back up the data first. If you get read errors, tools like Recuva can attempt recovery. Only after confirming data is off (or unrecoverable) should you reformat via Disk Management.[7]

## Physical Damage Assessment

If after these steps the drive shows no signs of life—no USB detection, no sounds, no lights— the enclosure or drive controller may be physically damaged. As a last resort, if the drive uses a standard form factor (2.5" or 3.5"), you could carefully remove it from the enclosure and test it directly (if you have a desktop with SATA ports available), though this assumes the internal connections weren't damaged.[8][9]

**What's the status right now—does the enclosure make any sounds (spinning, clicking) or show any lights when plugged in?** This tells us if there's power reaching the drive at all.
