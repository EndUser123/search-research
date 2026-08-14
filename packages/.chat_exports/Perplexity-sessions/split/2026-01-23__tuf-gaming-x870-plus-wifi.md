---
title: "tuf gaming x870-plus wifi"
date: "2026-01-23"
mode: "CONCISE"
uuid: "8fa843a1-08be-404c-9f20-5b5acfe7f87e"
entry_count: 3
---

## Human

tuf gaming x870-plus wifi

## Assistant

The ASUS TUF Gaming X870-PLUS WiFi is an AM5 ATX motherboard with Wi‑Fi 7, USB4, PCIe 5.0 for GPU and NVMe, and a mid‑range “TUF‑grade” power design aimed at Ryzen 7000–9000 builds.[1][4]

## Key specs

- **Socket / chipset**: AMD AM5, X870 chipset; supports Ryzen 7000, 8000G, and 9000 series desktop CPUs.[4][7][1]
- Memory: 4× DDR5 DIMM, up to 192 GB, with support for high-speed EXPO/XMP kits via ASUS AEMP.[4]
- Expansion:
  - 1× PCIe 5.0 x16 slot for GPU.[1][4]
  - Additional PCIe slots (including a lower x4) for expansion cards like capture or NICs.[4]
- Storage:
  - 4× M.2: two PCIe 5.0 NVMe slots and two PCIe 4.0 slots, with large heatsinks.[1][4]
  - 2× SATA 6 Gbps ports.[4]

## Power and thermals

- **VRM**: 16+2+1 power stages (80A SPS), 8‑layer PCB, ProCool connectors, alloy chokes and durable caps; solid for 12–16‑core Ryzen and overclocking.[7][1][4]
- Cooling features:
  - Large VRM heatsinks and M.2 heatsinks.[1][4]
  - Multiple fan headers and support for ASUS AI Cooling II.[4]

## Connectivity and I/O

- Network:
  - Onboard Wi‑Fi 7 (IEEE 802.11be) with Bluetooth.[5][1][4]
  - 2.5 GbE Realtek LAN.[5][4]
- Rear I/O highlights:
  - Dual USB4 (40 Gbps) Type‑C ports and front‑panel USB‑C 20 Gbps with PD fast‑charge support.[5][4]
  - HDMI for iGPU output.[4]
  - BIOS FlashBack button for easy CPU‑less flashing.[6]

## PCIe / M.2 lane quirks

- Community notes point out:
  - The M.2_2 slot shares lanes with the GPU; populating it can drop the main x16 slot to x8, which usually costs only ~1–2% performance even on high‑end GPUs but is still a design annoyance.[2]
  - Another M.2 slot (M.2_4) shares with a secondary PCIe slot, so only one of those can be used at a time.[2]
- These lane‑sharing choices are a common criticism and can matter if you plan to max out M.2 plus multiple add‑in cards.[8][2]

## User / review sentiment

- Positives:
  - Strong overall performance and stability with Ryzen 9.[7][5]
  - Very fast Wi‑Fi 7, good overclocking options (AI Overclocking, PBO enhancements, Dynamic OC Switcher, Core Flex), and convenient USB4 connectivity.[7][5][4]
- Negatives:
  - Lane‑sharing layout makes storage/expansion planning a bit finicky; some reviewers argue other X870 boards offer cleaner PCIe layouts at similar prices.[8][2]
  - A few reports of occasional Ethernet issues and concern about price/value at MSRP.[8][5]

If you share your planned CPU, GPU, number of NVMe drives, and whether you need extra PCIe cards (capture/10G NIC/etc.), a tailored “is this board a good fit?” breakdown for your specific build is possible.

## Human

how can I get the high speed usb ports (40gb/s) working on Windows 11?

## Assistant

Based on your hardware context (ASUS TUF Gaming X870-PLUS WiFi), here's a focused walkthrough for enabling USB4 40Gbps support on Windows 11:

## Driver Setup

**1. Chipset drivers first**
Download the latest AMD Chipset Drivers from ASUS's support site for your motherboard. This includes the ASMedia USB4 controller support.[1]

**2. Windows 11 USB4 native support**
Windows 11 (version 23H2 and later) includes native USB4 40Gbps support, so dedicated USB4 drivers may not be necessary; however, you should force Windows Update to check for optional updates in `Settings > Update & Security > Update History > View optional updates` to grab any relevant chipset/USB4 controller updates.[2]

**3. Device Manager check**
Open Device Manager and look under "Universal Serial Bus controllers" for:
- `USB4 Router` or `AS Controller` (ASMedia)
- If these don't appear or show as "Unknown Device," the controller isn't being recognized

If you see unknown devices, right-click → **Update driver** → browse to ASUS's driver folder or let Windows search online.

## BIOS Settings (Critical)

The X870-PLUS WiFi's onboard USB4 ports are tied to the ASMedia ASM4242 controller running on PCIe 4.0 x4. You need to verify:

1. **Boot into BIOS** (Del key during POST)
2. Look for settings like:
   - `PCIe Configuration` → Check USB4/Thunderbolt is enabled
   - `Power Management` → Disable aggressive USB power-saving for USB4 ports
   - `M.2_2 Slot` mode: By default, populating M.2_2 reduces USB4 bandwidth; if needed, adjust in BIOS

3. Save and reboot

## Common Issues & Fixes

**No recognition in Device Manager:**
- Uninstall all "Unknown Devices" in Device Manager, reboot, and let Windows re-enumerate (it will pull from Windows Update or chipset driver).[3]
- If X870 boards are problematic with USB4 on Windows 11, check ASUS's support forum; some early X870 boards had Windows 11 USB4 driver gaps (ASUS may have firmware/BIOS updates to address this)[1]

**Low speed or devices not detected:**
- Check rear I/O: The two USB4 ports are **Type-C, 40Gbps** on the rear I/O panel
- Use native USB4 Type-C cables (not regular USB-C)
- Test each port individually; one may be faulty

**Power delivery issues:**
- Ensure your USB4 cable supports 60W PD if needed (the X870-PLUS supports up to 20V/3A, 60W quick-charge)[4]

## Full Windows 11 Settings Path

Once everything is recognized, navigate to:
`Settings > Bluetooth & Devices > USB` → you should see USB4 management options where you can monitor connected devices and bandwidth utilization.[2]

If your USB4 ports remain invisible after chipset drivers + BIOS config, this may indicate a board-level issue or that ASUS hasn't released Windows 11 drivers yet for that specific controller—check ASUS support tickets or consider a BIOS update if available.

## Human

It should look like this?

## Assistant

Yes, your Device Manager screenshot shows **healthy USB4 support** on Windows 11. Key indicators that it's working correctly:

## Good Signs

- **`USB4 Root Router (1.0)`** — Present and enumerated. This is the critical entry; it means Windows recognizes the USB4 controller.
- **`USB4(TM) Host Router (Microsoft)`** — Also present. This is Microsoft's native USB4 stack driver, which handles the 40Gbps protocol.
- **ASMedia USB 3.x controllers** — These are the onboard controllers for your other USB 3.0/3.1 ports; all showing valid driver versions.
- **No "Unknown Devices"** — Nothing is showing as broken or requiring driver updates.

## What's Missing (and Why That's OK)

You don't see:
- A discrete "USB4 Device" or connected peripheral
- ASMedia USB4-specific driver entries

This is **normal** when no USB4 device is plugged in. Once you connect a USB4 external drive, dock, or cable, Windows will enumerate the device under the USB4 Root Router tree.

## To Verify Full 40Gbps Capability

**Test with an actual USB4 device:**
1. Plug in a USB4 drive or dock
2. Return to Device Manager → expand `USB4 Root Router (1.0)`
3. You should see the device listed underneath with its connection speed

**Check negotiated speed in Settings:**
- `Settings > Bluetooth & Devices > USB` → select the USB4 port/device
- Look for bandwidth or speed information (should show 40Gbps if fully negotiated)

**PowerShell diagnostics (optional):**
```powershell
Get-PnpDevice -Class USB | Where-Object {$_.Name -like "*USB4*"} | Format-List
```

Your setup is **ready to go**. The USB4 stack is present and active. Test with actual USB4 hardware to confirm speeds.
