---
title: "tuf gaming x870-plus wifi"
date: "2026-01-16"
mode: "COPILOT"
uuid: "b73e63c8-0f04-4521-8bf8-f331d8805352"
entry_count: 4
---

## Human

tuf gaming x870-plus wifi

## Assistant

**ASUS TUF Gaming X870-Plus WiFi Overview**

The ASUS TUF Gaming X870-Plus WiFi is an ATX motherboard based on the AMD X870 chipset, designed for AMD Ryzen 7000, 8000, and 9000 series processors on the AM5 socket. It features military-grade components, robust power delivery, and advanced connectivity for gaming and AI workloads.[1]

**Key Specifications**

- CPU: AMD Socket AM5 (Ryzen 9000/8000/7000 series).[2]
- Memory: 4x DDR5 DIMM slots, up to 256GB, supports 8000+ MT/s (OC), EXPO, AEMP.[2]
- Storage: 4x M.2 slots (PCIe 5.0/4.0), 2x SATA 6Gb/s ports.[2]
- Expansion: PCIe 5.0 x16 slot, additional PCIe 4.0 x16 (x4 mode).[2]
- Networking: Wi-Fi 7 (802.11be, 2x2, up to 2.9Gbps), Bluetooth 5.4, Realtek 2.5Gb Ethernet.[2]
- USB: Rear - 2x USB4 (40Gbps Type-C), 3x USB 10Gbps, 4x USB 5Gbps, 1x USB 2.0; Front - USB 20Gbps Type-C (30W PD).[2]
- Power: 16+2+1 stages, 80A SPS.[3]
- Audio: Realtek ALC1220P 7.1 Surround.[2]

**Connectivity and Features**

This board includes HDMI output, BIOS FlashBack, Q-Design elements like M.2 Q-Latch and PCIe Q-Release, and TUF protections such as LANGuard and SafeSlot. It supports AI features like AI Overclocking and AI Cooling II via Armoury Crate software.[4][2]

**Pricing in Canada**

Current prices in Canada range from about CA$350-430, with Newegg listing at CA$349.99 (down from $409.99) and other retailers like CDW at CA$429-471. Check Amazon.ca or Canada Computers for latest deals, as sales can dip to US$250 equivalents.[5][6][7][3][2]

## Human

why won't my enclosures work with them?

## Assistant

Answer skipped.

## Human

2x USB4 (40Gbps Type-C) won't work with my external drive enclosures I mean, but they say they are usb v 3.2

## Assistant

USB4 ports on the ASUS TUF Gaming X870-Plus WiFi are backward compatible with USB 3.2 devices, so your enclosures should connect and operate at USB 3.2 speeds (up to 10-20Gbps depending on the exact spec). Common issues preventing proper function include cable incompatibility, power delivery mismatches, driver problems, or enclosure chipset limitations when negotiating the USB4 link.[1][2][3][4]

## Possible Causes

USB4 requires specific cables certified for 40Gbps (often marked as USB4 or Thunderbolt-compatible) with proper electronic markers (EMCA); standard USB 3.2 cables may fail link training or drop to lower speeds/not detect. Your enclosures' USB 3.2 controllers (likely using chips like JMicron JMS583 or ASMedia ASM1352) might not fully negotiate with the board's ASMedia ASM4242 USB4 controller, causing no-detection or instability, especially under load like large file transfers from your multi-drive setup. Windows 11 USB power management or outdated chipset/USB drivers can also halt detection—your past USB3 saturation issues suggest controller overload patterns.[5][6][7][3][8]

## Troubleshooting Steps

- Test enclosures on the board's USB 3.2 ports (10Gbps Type-A) to isolate if USB4-specific; they should work there at full speed.[9]
- Swap to a certified USB4/Thunderbolt 4 cable (passive copper, <0.8m for 40Gbps); avoid active cables or USB 3.x-only ones.[3]
- Update AMD chipset drivers (from ASUS support), USB4 firmware/BIOS (latest 1022+), and disable USB Selective Suspend in Power Options > USB settings.[10][3]
- Check Device Manager for "Unknown USB Device" errors, reinstall USB controllers, and monitor Event Viewer for USB events during connection.[6]
- Verify enclosure power (separate supply if multi-drive) and test single drive; your 3-4 drive enclosures may exceed USB4 port power (15W default).

## Compatibility Notes

| Aspect | USB4 Port (TUF X870) | USB 3.2 Enclosure |
|--------|----------------------|-------------------|
| Speed | 40Gbps max, falls to 3.2 | 10/20Gbps max [1] |
| Cable Req. | USB4 certified | USB-C 3.2 OK, but USB4 better [11] |
| Power | Up to 15W (30W front) | Often needs external PSU [9] |
| Common Fix | Drivers/cable | Use USB 3.2 ports [2] |

If issues persist, share enclosure model/chipset (e.g., via USBDeview tool) and error symptoms for targeted advice.[12]

## Human

is there a picture showing which ports are usb4?

## Assistant

The ASUS TUF Gaming X870-Plus WiFi has two USB4 (40Gbps Type-C) ports on the rear I/O panel, positioned among the 10 total rear USB ports. These are the two Type-C connectors, typically located near the BIOS FlashBack button and distinguished from the surrounding Type-A ports (3x USB 10Gbps in light blue, 4x USB 5Gbps in dark blue, and 1x USB 2.0 black).[1][2][7][10]

## Rear I/O Layout
Diagrams in the official ASUS manual (E25811) and reviews clearly label them as the topmost or lowermost Type-C ports on the rear shroud. For example:[2][1]
- Left side: Often HDMI, Wi-Fi antenna, audio jacks.
- Center-right: Ethernet (2.5Gb), then clusters of Type-A USBs.
- USB4 Type-Cs: Paired together, marked with 40Gbps icons or labels in photos/manuals.[5]

## Visual References
High-res rear I/O images appear in the ASUS product page gallery, LanOC review (board layout page), and YouTube overviews like the unboxing video, showing the two silver Type-C ports explicitly as USB4. Download the full manual PDF from ASUS support for the annotated diagram—search for "Rear USB" section.[3][6][1][2]
