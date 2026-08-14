---
title: "why won't my xreal beam connect to the internet?"
date: "2026-07-17"
mode: "COPILOT"
uuid: "423825ea-4455-430a-962e-69674d1ca101"
entry_count: 2
---

## Human

why won't my xreal beam connect to the internet?

## Assistant

Most XREAL Beam “connected but no internet” issues are caused by Wi‑Fi/security settings on the router or by the Beam’s own network/date settings, not by a hardware fault. I’ll walk you through the highest‑leverage checks and fixes in order.[1][2][3][4]

***

## Quick triage (what exactly is failing?)

Before changing anything, confirm what you’re seeing on the Beam:

- Does it show your Wi‑Fi SSID, let you enter the password, and then say “Network not available” or “Connected, no internet”?[4][1]
- Can it connect to an open (no‑password) hotspot from your phone, but not to your home Wi‑Fi that uses WPA2/WPA3? This is a known pattern.[2]
- Are other devices using the same Wi‑Fi successfully (laptop/phone on that SSID)? If they also fail, it’s a router/internet issue, not Beam‑specific.

If you can share the exact message and whether you’re on Beam vs Beam Pro, I can narrow this further.

***

## Fixes on the Beam itself

These are low‑risk changes on the device and often resolve the issue.

### 1. Verify date and time settings

Some internet services will refuse connections or show “no internet” if the device’s clock is wrong.[3][4]

On Beam / Beam Pro:

- Open **Settings → System → Date & time**.[3]
- Turn on **“Set time automatically”** and **“Set time zone automatically”**.[4][3]
- Toggle Wi‑Fi off/on and try browsing again.[3][4]

If your clock was far off, this alone can flip from “no internet” to working.

### 2. Toggle and “forget” your Wi‑Fi network

Corrupted or stale Wi‑Fi profiles can cause Beam to say the password is correct but then fail to get internet.[1][3]

- Go to **Settings → Network & Internet → Internet**.[5][3]
- Turn **Wi‑Fi** off, wait ~5 seconds, then turn it back on.[3]
- Tap your home SSID, open its details, and select **Forget**.[3]
- Let it reappear in the list, tap it, and re‑enter the password, then test again.[5][3]

This is especially effective when Beam reports “Network not available” right after the password checkmark.[1]

### 3. Reset Beam’s network settings

If multiple networks fail or things worked before and suddenly broke after updates, a full network reset helps.[6][3]

On Beam Pro (similar on Beam):

- Open **Settings → System → Reset options**.[6][3]
- Choose **Reset Bluetooth and Wi‑Fi** and confirm.[6]
- Reboot the Beam, then reconnect to Wi‑Fi and test.

This clears all stored network configs and returns Wi‑Fi to a clean state.[6]

***

## Router and Wi‑Fi configuration issues

XREAL Beam is picky about certain router settings. These are common traps.

### 4. Check IPv6 on your router

There’s a documented case where Beam would not complete initial Wi‑Fi setup until IPv6 was disabled; after Beam updated, IPv6 could be re‑enabled.[1]

- In your router’s admin UI, look for **IPv6** and temporarily **disable** it.[1]
- Reboot router, reconnect the Beam, and see if it now gets internet.[1]
- Once Beam pulls its firmware update successfully, you can usually turn IPv6 back on.[1]

This is particularly relevant if you’re using Google Wifi or similar mesh systems.[1]

### 5. WPA2 vs WPA3 security

Some users after updates reported Beam refusing to connect to password‑protected networks, working only with open hotspots; changing Wi‑Fi security helped.[2]

- In your router, find the Wi‑Fi **security mode**.  
- If it’s **WPA3** or “WPA2/WPA3 mixed”, try forcing **WPA2‑PSK (AES)** only.[2]
- Save, reboot router, then reconnect the Beam.

Several reports suggest “forgetting” the SSID and switching to WPA2 cleared whatever bit was stuck and restored connectivity.[2]

### 6. Guest network / captive portals

Beam can struggle with guest networks that use captive portals (web pages where you have to click “Accept” or enter info). This often appears as “connected, no internet”.

- If your SSID is a **guest network** or uses **web‑based login**, try a normal home SSID without captive portal.  
- Test Beam on a simple phone hotspot (WPA2, no captive portal). If that works, your router’s guest/captive setup is the issue, not the Beam.

***

## Firmware and special cases

### 7. Make sure Beam firmware is up to date

Early firmware had more Wi‑Fi quirks, and XREAL has been pushing connectivity fixes over time.[7][1]

- If you can get *any* connection (e.g., phone hotspot), use that to check for updates in **Settings → System → System update** (location may vary slightly).  
- Apply the latest update, then retest on your home Wi‑Fi.[7][1]

Some users needed the firmware update *plus* network configuration changes (like IPv6 or WPA2) to fully resolve issues.[7][2][1]

### 8. If Beam is connected to a laptop/PC

If you’re using Beam with a laptop and seeing Wi‑Fi drop on the laptop when the glasses connect, the system may detect the glasses as a network‑capable USB‑C device and disable Wi‑Fi due to security policy.[7]

On Windows:

- Open **Control Panel → Network and Internet → Network Connections**.  
- Look for a new **USB‑C adapter** that appears when the glasses are plugged in and **disable** it.[7]

Some users also entered developer mode on the glasses and disabled the TCP/IP function when the device was being recognized as Ethernet, but this is more advanced and can affect Beam Pro communication.[7]

***

## My assessment and uncertainty

- **FACT (cited):** IPv6 and WPA3 can block Beam’s Wi‑Fi until settings are changed.[2][1]
- **FACT (cited):** Wrong date/time and corrupt Wi‑Fi profiles produce “connected, no internet” symptoms on Beam Pro.[4][3]
- **CONSENSUS:** Most connectivity issues are fixed by router security tweaks (IPv6/WPA), network resets, and firmware updates.[6][2][3][7][1]
- **SPECULATION (medium confidence):** If none of these help, you might be hitting either a rare firmware bug or an ISP/router‑specific quirk; in that case, logs and exact model details become necessary for further diagnosis.

A concrete next step: try the on‑device fixes (date/time, forget network, network reset) and switch your router to WPA2‑only; if Beam still shows no internet, temporarily disable IPv6 and test again.

What exact error message do you see on the Beam when you connect to your home Wi‑Fi, and are you using a standard home router or something more locked‑down (work, campus, hotel)?

## Human

It actually says connected / limited connection, and then says it can't connect to the internet

## Assistant

“Connected / limited connection” on the XREAL Beam basically means Wi‑Fi association succeeded but the Beam can’t reach internet services (usually due to time, DNS, or router security settings). The fastest path is to fix the Beam’s date/time, then test on a simple hotspot and, if needed, tweak your router (WPA2, IPv6).[1][2][3][4]

***

## Step 1 – Fix the Beam’s time (high‑impact)

Beam and Beam Pro can show “connected but limited” or “can’t connect to the internet” when the system clock is wrong; fixing auto time often immediately restores browsing.[2][3]

On Beam / Beam Pro:

- Open **Settings → System → Date & time**.[2]
- Turn on **Set time automatically** and **Set time zone automatically**.[3][2]
- Go back, close settings, and try something that uses the internet (e.g. the browser or Netflix sign‑in).[3][2]

If this was the issue, the “limited connection” warning should disappear once the time syncs.[3]

***

## Step 2 – Verify that any internet works at all

You want to distinguish “Beam is broken” from “Beam doesn’t like your router’s configuration”.

- Turn on a **phone hotspot** (WPA2, normal password, no fancy guest portal).  
- Connect the Beam to that hotspot and try loading a page or app that clearly needs internet.  

If it works fine on the hotspot but not at home:

- The hardware and Beam’s Wi‑Fi stack are fine.  
- The problem is very likely your home router’s security/IPv6/DNS settings.[5][4][1]

If it fails even on the hotspot, it’s either a Beam config issue (network settings, time, firmware) or a deeper bug; then focus on the Beam‑side fixes below.

***

## Step 3 – Clean up Wi‑Fi profiles and network settings

Corrupt Wi‑Fi profiles and bad network configuration are a common cause of “connected / limited” states.[6][5][2]

On the Beam:

- Go to **Settings → Network & internet → Internet**.[7][2]
- Toggle **Wi‑Fi** off, wait 5–10 seconds, then back on.[2]
- Tap your home network, open its **details**, and **Forget** it.[2]
- Wait until the SSID reappears, tap it, re‑enter password, and reconnect.[7][2]

If that doesn’t help:

- Go to **Settings → System → Reset options → Reset Bluetooth and Wi‑Fi** and confirm.[6]
- Reboot the Beam and reconnect to Wi‑Fi from scratch.[6]

A full network reset returns Wi‑Fi, Bluetooth, and related configs to factory defaults, which often clears “limited connection” states that persist across networks.[6]

***

## Step 4 – Router settings that often break Beam

If the Beam works on a hotspot but not your home Wi‑Fi, the router config is probably the culprit.

### IPv6

Initial Beam setup has been blocked on some routers until IPv6 was disabled; after updating, IPv6 could be re‑enabled.[4]

- Log into your router admin page.  
- Find the **IPv6** setting and temporarily **disable IPv6**.[4]
- Reboot router, reconnect the Beam, and test internet access again.[4]

On Google Wifi / mesh systems this is a known workaround.[4]

### WPA2 vs WPA3

Some Beam users report that after updates, password‑protected networks give connection but no internet until security is changed from WPA3/mixed to WPA2.[5]

- In Wi‑Fi settings, set security to **WPA2‑PSK (AES)** only (no WPA3 or mixed mode).[5]
- Save and reboot router.  
- Forget and re‑add the network on Beam as above, then test.  

Changing security mode plus forgetting the SSID often clears the “bit” that’s stuck in Beam’s network stack.[5]

### DNS / “no internet but DNS works”

There’s at least one detailed write‑up where the Beam connects to Wi‑Fi that has DNS but no routed internet, and it complains that the network has no internet and refuses to move on.[1]

- Ensure your home network actually has working **internet**, not just LAN + DNS (check on a laptop/phone).  
- If you have any special firewall rules blocking outbound traffic for new devices or for the Beam’s MAC address, temporarily relax them and retest.  

Beam expects to reach specific external services during setup and OTA updates; some strict firewalls make it think “this network has no internet” even when local devices work.[8][1]

***

## Step 5 – Firmware and “first‑time setup” behavior

Beam’s first activation and OTA update are sensitive to having a truly online Wi‑Fi connection; on some networks it refuses to proceed if it detects “no internet”.[8][1]

- If you haven’t yet completed the **initial OTA update**, use a phone hotspot or a simpler Wi‑Fi network (no guest portal, no advanced security) just long enough for the Beam to finish updating.[1][8][4]
- Afterwards, reconnect it to your home Wi‑Fi and see if the “limited connection” error persists.[1][4]

Once current firmware is installed, Beam is generally more tolerant of different setups, though security settings can still matter.[9][5][4]

***

## My read and next best move

Given your symptom text (“connected / limited connection”, then “can’t connect to the internet”), the most probable causes are:

- **Wrong date/time or network config on the Beam itself** (high confidence).[3][2][6]
- **Router security/IPv6 or DNS rules that make Beam think the network has no internet**, especially if other devices work fine (medium‑high confidence).[1][5][4]

Concrete next steps (minimal but high‑impact):

1. Turn on automatic date/time + time zone on Beam.[2][3]
2. Test on a phone hotspot; if it works there, focus on router (set WPA2‑only, disable IPv6 temporarily, ensure no special firewall/DNS rules).[5][4][1]
3. If hotspot also shows “limited”, perform the network reset on Beam (Reset Bluetooth and Wi‑Fi) and reconnect.[6]

If you’re up for it, can you tell me which router/Wi‑Fi system you’re using at home (e.g. Google Wifi mesh, ISP combo modem/router, UniFi), and whether Beam works on a phone hotspot? That will narrow the remaining possibilities a lot.
