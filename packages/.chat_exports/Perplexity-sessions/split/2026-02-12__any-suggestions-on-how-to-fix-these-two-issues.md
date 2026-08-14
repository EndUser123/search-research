---
title: "Any suggestions on how to fix these two issues?"
date: "2026-02-12"
mode: "COPILOT"
uuid: "eb2bdd57-b253-49f4-ba60-b97e6f72cce8"
entry_count: 4
---

## Human

Any suggestions on how to fix these two issues?

## Assistant

Two separate problems are happening here: Opus setup failing (exit code 1) and Windows refusing the folder because it’s outside your home directory. Here’s how to tackle both.

## 1. “Feature enablement failed (exit code 1)”

This is usually Opus failing to initialize a local feature (file access / workspace watcher / plugin) because the folder selection or permissions are invalid.

Try, in order:

1. Run Opus as admin once  
   - Close Opus.  
   - Right‑click its shortcut → Run as administrator → retry setup.  
   - If it succeeds, you can run it normally afterward.

2. Reset the workspace/folder choice  
   - Instead of reusing the failing “Work in a folder” entry, create a new task or workspace that points to a very simple path like `C:\Users\<you>\Documents\OpusTest`.  
   - If that works, the original path is what’s breaking setup.

3. Check security software  
   - Temporarily disable or create an allow‑rule for Opus in Defender / your AV, then retry.  
   - Some AVs block local feature enablement and cause generic exit code 1.

4. Reinstall or repair  
   - Uninstall Opus, delete its config directory (usually under your user profile’s AppData\Roaming or AppData\Local), then reinstall the latest build and retry setup.  
   - If there are logs (often under `%LOCALAPPDATA%\Opus\logs`), check the latest one around the time of “exit code 1” for a more specific subsystem error.

If you can grab the log line mentioning which feature failed (e.g., file indexer, plugin manager), paste it here and I can suggest a more targeted fix.

## 2. “The selected folder is outside your home directory”

Opus (or its Windows helper) is enforcing a sandbox: it will only work with folders under your Windows *home* directory, something like:

- `C:\Users\<your-username>\...`

To fix this:

1. Move or create a mirror of your project  
   - If your code lives under something like `D:\Dev\ProjectX`, create `C:\Users\<you>\Dev\ProjectX` and point Opus at that path.  
   - For large trees, use an NTFS junction or symlink (below) instead of copying.

2. Use a junction/symlink back into your real workspace  
   - From an elevated PowerShell or CMD:

   PowerShell:
   ```powershell
   New-Item -ItemType Junction `
     -Path "C:\Users\<you>\Dev\ProjectX" `
     -Target "D:\Dev\ProjectX"
   ```

   CMD:
   ```cmd
   mklink /J "C:\Users\<you>\Dev\ProjectX" "D:\Dev\ProjectX"
   ```

   - Then tell Opus to “Work in a folder” at `C:\Users\<you>\Dev\ProjectX`.  
   - Windows sees this as inside your home, but it actually points to your existing location.

3. Verify your “home” is what Opus expects  
   - Make sure you’re not selecting something like `C:\` or `D:\` root or a network drive.  
   - If your real profile is on another drive (Roaming profile, OneDrive redirection, etc.), check whether Opus is hard‑coding `C:\Users\<name>`; if so, using the junction above is the safest workaround.

If you tell me:

- The exact path you were trying to select, and  
- Whether your projects live on a different drive (e.g., `D:` or `E:`),

I can give you an exact junction/symlink command tailored to your setup and we can see if that also clears the exit‑code‑1 setup step.

## Human

chrome-native-host.log

## Assistant

This log looks completely healthy and doesn’t explain the Opus setup failure or the “outside your home directory” dialog by itself.[1]

## What the log shows

- It’s just the Chrome native host for the MCP browser bridge starting and stopping cleanly many times.[1]
- Each session logs: starting version 0.1.0, creating a Windows named pipe `\\.\\mcp-browser-bridge-brsth`, entering the main loop, then “Chrome disconnected EOF received” and a clean shutdown.[1]
- There are no ERROR or WARNING lines, only INFO entries.[1]

## Implications for your issues

- The Opus feature‑enablement failure is almost certainly happening in a *different* component (Opus desktop app / worker) rather than the Chrome native host.[1]
- The “selected folder is outside your home directory” is likely enforced by the Opus desktop app or a Windows‑side helper, not this Chrome host.[1]

## Next useful artifacts

If you want to dig deeper, the best logs to grab are:

- Opus desktop/client logs (often under `%LOCALAPPDATA%\Opus\logs` or a similar vendor folder).  
- Any log that actually contains `ERROR`, `WARN`, or “feature enablement failed” text.

If you can locate and attach the Opus app log from the time of the failure (or tell me the exact path you tried to select when you saw the home‑directory error), I can pinpoint why feature enablement is returning exit code 1 and propose a concrete fix.

## Human

%LOCALAPPDATA%\Opus\logs, doesn't exist.

## Assistant

That path not existing is actually a useful clue: it means Opus isn’t writing any desktop‑side logs at all, so the failure is happening very early in its startup or in a different component.[1]

Given what we know so far, here’s what I’d do next, in a minimal, practical order:

1. Confirm the exact folder path you’re selecting  
   - Please paste the literal path you chose when you saw “The selected folder is outside your home directory.”  
   - Also paste your actual home path (from PowerShell: `echo $env:USERPROFILE`).  
   - This will tell us whether the sandbox check is simply rejecting a different drive (e.g., `D:`) and whether a junction/symlink workaround is the right move.

2. Try a “known good” test folder  
   - In File Explorer, create `C:\Users\<you>\OpusTest`.  
   - Point Opus’s “Work in a folder” directly at that, then hit “Let’s go” and see if:  
     - a) you still get “outside your home directory”, or  
     - b) you instead get only “feature enablement failed (exit code 1)”, or  
     - c) it finally works.  
   - Each outcome narrows down whether the check is path‑based or something deeper in feature setup.[1]

3. Look for any other Opus‑related logs/configs  
   Since `%LOCALAPPDATA%\Opus\logs` doesn’t exist, check these instead (just see whether any folder exists, no need to send contents yet):  
   - `%LOCALAPPDATA%\Anthropic\Opus` or `%LOCALAPPDATA%\Anthropic\Claude`  
   - `%APPDATA%\Anthropic`  
   - `%LOCALAPPDATA%\Programs\Opus` or the folder where you installed Opus.[2][1]
   If you find anything with `log` in the filename or a JSON/TOML config, that could contain the specific feature‑enablement error.

4. Check the Chrome MCP bridge situation (sanity check)  
   - Your `chrome-native-host.log` shows the `mcp-browser-bridge` native host is fine, with repeated clean starts and stops.[3][2]
   - Just confirm in Chrome that you have only one relevant MCP extension installed and it shows the native host as connected; duplicate or mismatched registrations *can* sometimes confuse desktop clients.[4][2][3]

5. Reinstall Opus with a full reset  
   - Uninstall Opus.  
   - Manually delete any leftover `Opus` or `Anthropic` folders under `%LOCALAPPDATA%` and `%APPDATA%` (or move them aside) so it doesn’t reuse a bad config.[1]
   - Reinstall the latest Opus build, then immediately try the simple `C:\Users\<you>\OpusTest` folder again.

If you can send:

- The exact project path you were trying to use, and  
- The output of `echo $env:USERPROFILE`, and  
- Whether the `OpusTest` folder works,

I can turn this into a very targeted fix (including an exact junction command if we need to route a `D:\` tree into your home sandbox).

## Human

It's just the feature enablement now.

## Assistant

Good, that means the home‑directory restriction is satisfied now; only the feature‑enablement step is failing on `C:\Users\brsth\OneDrive\Documents`.[1]

Here are the most likely causes and concrete things to try:

1. OneDrive / sync conflicts  
   - Opus may be trying to set up watchers or local indexes that OneDrive’s virtualization blocks or delays.[1]
   - Test with a truly local folder: create `C:\Users\brsth\OpusTest` (not under OneDrive), point Opus at that, and hit “Let’s go”.  
   - If that works, the fix is to either move your working folder outside OneDrive or create a junction like `C:\Users\brsth\OpusDocs` → `C:\Users\brsth\OneDrive\Documents` and see if Opus is happier with that indirection.

2. Permissions or lock on the target folder  
   - Ensure you have full control on `C:\Users\brsth\OneDrive\Documents` (Properties → Security → your user has Full control).  
   - Close apps that might be locking the folder (file indexers, backup tools) and retry; some tools holding an exclusive handle can cause generic exit‑code‑1 failures.[2]

3. Opus config corruption  
   - With Opus closed, temporarily move its config folders (if present) out of the way, then restart:  
     - `%APPDATA%\Anthropic\Opus` (or `%APPDATA%\Anthropic\Claude`),  
     - `%LOCALAPPDATA%\Anthropic\Opus` (names may vary slightly).[3][1]
   - Opus will recreate fresh config on next launch; then immediately select a simple local folder (like `OpusTest`) and see if feature enablement succeeds.

4. Try running once as administrator  
   - Right‑click the Opus shortcut → Run as administrator → select `C:\Users\brsth\OpusTest` and click “Let’s go”.  
   - If this succeeds but normal runs fail, it points to a permissions/path issue we can then target more precisely.[2]

If you can run these two quick experiments and report back:

- Does `C:\Users\brsth\OpusTest` succeed or still show “feature enablement failed (exit code 1)”?  
- If it still fails, did running Opus as admin change anything?

With those answers, we can either lock in “OneDrive is the culprit” and design a clean junction‑based workaround, or dig deeper into permissions/config specifically for your user profile.
