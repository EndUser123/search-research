---
title: "on my windows 11 pc, my internal drives seem faster than my external drives, even when using a 40gb/s enclosure.  why?"
date: "2026-01-23"
mode: "COPILOT"
uuid: "16cc9b5c-a870-408f-95d3-3fd2e6d8251c"
entry_count: 2
---

## Human

on my windows 11 pc, my internal drives seem faster than my external drives, even when using a 40gb/s enclosure.  why?

## Assistant

Internal drives on your Windows 11 PC typically outperform external drives, even those in a 40 Gb/s USB4 enclosure, due to fundamental differences in interface efficiency and overhead. Your ASUS TUF Gaming X870-Plus WiFi setup with external USB enclosures for multiple HDDs exacerbates this, as shared controller bandwidth and protocol layers limit real-world speeds.[1][2][3]

## Key Performance Differences
Internal SATA III connections deliver up to ~600 MB/s with minimal latency and direct motherboard access, ideal for HDDs which rarely exceed 200-250 MB/s sequential speeds. External USB adds protocol overhead (5-15% speed loss), enclosure controller bottlenecks, and cable limitations, often capping effective throughput below internal SATA even on USB4 ports.[4][3][5]

## USB4 Enclosure Limitations
USB4 (40 Gb/s theoretical) falls back to USB 3.2 speeds (10-20 Gb/s) with your enclosures, but HDDs can't saturate that—multi-drive enclosures share bandwidth, causing contention like your prior copy freezes. Write caching defaults and USB power modes on Windows 11 further reduce external HDD performance compared to internals.[1][6][7]

## HDD-Specific Factors
HDDs in enclosures suffer more from seek latency amplification via USB bridges and vibration isolation issues, unlike rigid internal mounting. Benchmarks show external HDDs hitting 150-200 MB/s reads vs. 200+ MB/s internals, with random I/O 20-50% slower.[3][8][9]

## Optimization Steps
- Enable write caching: Device Manager > Disk drives > Properties > Policies > "Better performance".[1]
- Use USBDeview to confirm link speed (aim for SuperSpeed+ 20Gbps); update ASMedia drivers.[10][11]
- Test single-drive enclosure on rear USB4 ports with certified cable; benchmark via CrystalDiskMark.[7]

## Human

i have a corsair 4000d case, what's the optimal way to install the HDDs?  Any pictures or video?

## Assistant

The Corsair 4000D case supports up to 2x 3.5" HDDs in a dedicated removable cage located in the PSU shroud area for optimal cable management and airflow. This positioning keeps drives secure, vibration-dampened, and away from high-heat components like the GPU.[1][2]

## HDD Cage Location
The HDD cage mounts inside the PSU shroud at the bottom front of the case, supporting 2x combo trays for 3.5" HDDs or 2.5" SSDs. It can be relocated forward for longer PSUs (up to 220mm), but default position prioritizes cooling by avoiding front fan interference.[2][1]

## Installation Steps
- Power off PC, remove side panel, and pull out the HDD cage by pinching the release tabs.[3]
- Secure HDD in tray using side tabs (no screws needed); slide tray into cage until it clicks.[3]
- Connect SATA data/power cables, route behind motherboard tray, then reinstall cage.[3]
- For multiple drives, stack trays vertically in the cage.

## Visual Guides
Detailed step-by-step HDD installation in the 4000D, including tray insertion and cabling. Full case build showing HDD cage positioning during assembly. Official quick start guide with diagrams for moving/installing the HDD cage .[4][3]
