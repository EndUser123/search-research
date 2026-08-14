---
title: "microsoft smart app control is blocking some of my agentic cli tools.  How do I add the cli to the whitelist?"
date: "2026-01-30"
mode: "COPILOT"
uuid: "ecf8fd55-aff5-4fac-99e4-5b3463517cf0"
entry_count: 2
---

## Human

microsoft smart app control is blocking some of my agentic cli tools.  How do I add the cli to the whitelist?

## Assistant

## Microsoft Smart App Control: Whitelist and Workaround Options

**Critical Finding: Smart App Control Does Not Support Whitelisting**

Smart App Control (SAC) does not have a traditional whitelist or per-app exception mechanism, which is an important limitation for power users running unsigned CLI tools. Instead of allowing you to whitelist specific applications, SAC operates on a binary model: it either blocks untrusted code or permits it based on Microsoft's cloud-powered reputation database and code integrity checks.[1][2][3]

### Your Practical Options

**Option 1: Temporarily Disable SAC (Recommended for CLI Tools)**

Given your use case with agentic CLI tools—which are often unsigned or frequently updated—the most practical approach is to disable SAC temporarily while running your tools, then re-enable it.[3][4]

**Via Windows Security GUI:**
1. Press Windows key → type "Settings" → press Enter
2. Navigate to **Privacy & Security** → **Windows Security** → **App & Browser Control**
3. Click **Smart App Control settings**
4. Toggle to **Off**
5. Confirm with "Yes, I'm sure"
6. Run your CLI tools
7. Re-enable SAC by toggling back to **On**

**Via Registry (PowerShell):**
Create and run this REG file to automate toggling:

```
Windows Registry Editor Version 5.00
[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\CI\Policy]
"VerifiedAndReputablePolicyState"=dword:00000000
```

Change `00000000` to:
- `00000001` to enable (Enforce mode)
- `00000002` to enable (Evaluation mode—less strict)

**Option 2: Run in Evaluation Mode**

If SAC is currently in Evaluation mode (value `2`), it observes behavior without blocking. This is less restrictive than Enforce mode while still providing some protection. You can check your current status and adjust via the registry editor as shown above.[5]

**Option 3: Digitally Sign Your CLI Tools**

The most permanent solution is to digitally sign your agentic CLI tools with a valid certificate. This requires obtaining a code-signing certificate, which adds overhead but ensures SAC recognizes your tools as trusted. This is the path developers typically take when distributing tools to end users.[1]

### Important Context for Your Workflow

As of Windows 11 Build 26220.7070 (Windows Insider Program, not yet production), Microsoft is testing toggling SAC on/off without requiring a clean Windows install—a major improvement from the previous permanent disable requirement. However, **there is still no per-app whitelist feature**, so temporary disabling remains your best operational option for development.[3]

Since you're running multiple CLI tools across 5–6 concurrent terminals,[user-context] the toggle approach minimizes friction: disable SAC before your development sprint, re-enable afterward for general browsing/usage.

### Workaround: Evaluation Mode Approach

Set SAC to **Evaluation mode** (`VerifiedAndReputablePolicyState=dword:00000002`) as a middle ground. This allows your unsigned CLI tools to run while still gathering threat intelligence without hard-blocking. You can monitor Windows Security logs to see if any of your tools trigger new detection patterns, giving you visibility without enforcement.

The bottom line: no whitelist exists for Smart App Control. Temporary disable-before-run or Evaluation mode remain your operational options.

## Human

this says I can't turn it back on.  How do we mitigate taht?

## Assistant

Excellent news—this limitation has **just been solved**. The screenshot you're seeing reflects the old behavior, but Microsoft pushed a critical fix very recently.

## The Breakthrough: Registry Workaround (January 2026)

As of late January 2026, **you can re-enable Smart App Control without reinstalling Windows** using a registry edit. This was discovered by the community and works on current Windows 11 versions.[1][2]

**The Registry Fix:**

1. **Create a System Restore point first** (safety net):
   - Type `System Restore` in Windows search → Click **Create a restore point** → Click **Create**

2. **Edit the registry** (Run as Administrator):
   - Press `Win + R` → Type `regedit` → Press Enter
   - Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\CI\Policy`
   - Find the key: `VerifiedAndReputablePolicyState`
   - Double-click and change the **Value Data**:
     - `0` = Off
     - `1` = On (Enforced)
     - `2` = Evaluation Mode

3. **Toggle cycle for CLI workflow**:
   - Set to `0` (Off) → Run your CLI tools
   - Set to `1` (On) → Re-enable protection afterward[1]

**Why this works:** The registry key directly controls SAC's state without requiring Windows to assess a clean install. This bypasses the permanent-disable logic that made the UI option greyed out.

## Your Operational Workflow

For your agentic CLI tools running 5–6 concurrent terminals:[user-context]

1. Before running CLI tools: Set `VerifiedAndReputablePolicyState=0`
2. Run your tools
3. After completion: Set `VerifiedAndReputablePolicyState=1`
4. Verify in Settings that SAC shows as "On"

**Automate it with PowerShell** (optional):

```powershell
# Disable SAC
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState /t REG_DWORD /d 0 /f

# [Run your CLI tools here]

# Re-enable SAC  
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState /t REG_DWORD /d 1 /f
```

Run this as Administrator in PowerShell, and you can integrate it directly into your development sprint startup scripts.

## Incoming Microsoft Fix (Windows Insider)

Microsoft is also testing a proper UI toggle in Windows Insider Program builds that will let you flip SAC on/off like any normal setting—no registry edit required. This should roll out to production in 2026, but the registry method works **right now**.[2]

The key takeaway: That greyed-out "Off" message in your screenshot is outdated. You **can** turn it back on via registry without a full Windows reset.
