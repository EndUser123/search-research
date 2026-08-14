---
title: "microsoft is blocking language_server_something.  Do you know how to fix that?"
date: "2026-01-30"
mode: "COPILOT"
uuid: "1d1ec958-9760-48d2-84ab-85d2f7993422"
entry_count: 1
---

## Human

microsoft is blocking language_server_something.  Do you know how to fix that?

## Assistant

Most likely Windows Defender flagged and blocked a binary that `google-antigravity` downloaded or tried to run (maybe a language server helper), and the toast disappeared before you could read it. You can 1) find the exact thing Defender blocked, and 2) decide whether to allow it.

Below is the minimal path on Windows 11:

***

## 1. Find what Defender blocked

1. Press `Win` and type: **Windows Security** → open it.  
2. Go to **Virus & threat protection**.  
3. Click **Protection history**.

You should see recent events there. Look for entries around the time you ran google antigravity:

- Type: *Threat blocked*, *Quarantined*, or *Controlled folder access blocked*  
- Click the entry to expand it and see:
  - The **threat name**
  - The **file path** (e.g. `C:\Users\<you>\AppData\...language_server_*.exe`)
  - The **action** Defender took (blocked, quarantined, etc.)

If you can, copy the **full path** and **threat name** somewhere.

***

## 2. Decide if you actually trust it

Before you whitelist anything:

- Confirm you got `google-antigravity` from a **legit repo/site** (e.g. official GitHub, not a random mirror).
- Check that the blocked file lives in a plausible tool or cache directory (e.g. under your user profile, `AppData\Local\Programs`, `node_modules`, etc.), not some weird location (e.g. `C:\Windows\System32\random.exe`).

If anything looks off, do **not** unblock it; it could be real malware.

***

## 3. Allow the file if you’re confident it’s safe

From the same **Protection history** entry:

1. Expand the relevant entry.
2. If Defender allows it, click **Actions** → **Allow on device** (or **Restore** then **Allow**).
3. After allowing, try running google antigravity again and see if the block reappears.

If that option is greyed out:

- The file might already be deleted; re-run the install or command that created it, then re-check **Protection history**.
- Or Defender has stricter policy; in that case you can add an exclusion (see below) – but that’s riskier.

***

## 4. (Optional, riskier) Add a folder or process exclusion

If the tool keeps regenerating the same file and Defender keeps nuking it, you can exclude its folder, **only if you’re very sure** it’s safe:

1. In **Windows Security** → **Virus & threat protection** → **Manage settings** (under *Virus & threat protection settings*).
2. Scroll to **Exclusions** → **Add or remove exclusions**.
3. Click **Add an exclusion** → choose **Folder**.
4. Select the specific tool folder (e.g. `C:\Users\<you>\AppData\Local\google-antigravity\bin`) rather than something broad like `C:\Users` or entire drives.

This tells Defender to ignore that folder, so be precise.

***

## 5. If you want, I can help you pinpoint the exact file

If you open **Protection history** and paste back:

- The **“Affected item”** file path
- The **“Detected”** threat name (e.g. `Trojan:Win32/...`),
- And roughly what google antigravity command you ran,

I can:

- Tell you whether it looks like a false positive or genuinely sketchy
- Suggest a safer, narrower exclusion strategy or alternative way to run it.
