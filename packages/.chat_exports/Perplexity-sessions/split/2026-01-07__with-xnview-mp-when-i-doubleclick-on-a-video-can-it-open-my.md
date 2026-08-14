---
title: "with xnview mp, when I doubleclick on a video, can it open my external media player?"
date: "2026-01-07"
mode: "COPILOT"
uuid: "d099baab-204f-4bbd-b0af-35a47a591e1a"
entry_count: 2
---

## Human

with xnview mp, when I doubleclick on a video, can it open my external media player?

## Assistant

Yes. XnView MP can open videos in an external media player when you double‑click them, but you need to change a setting.

## Enable external player for videos

On current XnView MP builds (e.g. 1.4.x+):

1. Open **Tools → Settings**.  
2. Go to **Interface → Video** (or **Playback / Video** depending on version).  
3. Enable the option like **“Use external player for video”** and specify your preferred player executable (e.g. `mpv.exe`, `potplayer.exe`, `vlc.exe`).[1][2]
4. Confirm and restart XnView MP if needed.

After that, double‑clicking a video thumbnail in the browser should launch your chosen external player instead of the internal one.[2][1]

If your version lacks that checkbox, the older workaround is:

- Define your player under **Tools → Settings → Integration → Associated programs**, bind it to a hotkey (for example Alt+1), then use that hotkey to send the file to the external player.[3]

## Human

I'm using v 1.9.8 64-bit.  I don't see those options.

## Assistant

In XnView MP version 1.9.8, the option to force an external player is not located in the generic "Interface" or "Video" sections found in other versions. You must configure a **Custom Filter** to tell the browser to handle video files differently.

### Method 1: The "Custom Filter" Setting (Recommended)
This method tells XnView MP to bypass its internal viewer specifically for video files and pass them to your OS default player instead.

1.  Go to **Tools → Settings**.
2.  Select **File List** in the left sidebar.
3.  Click the **Custom Filter** tab at the top.
4.  In the list of file types, locate the **Video** row.
5.  Look for the **Open with** column in that row.
6.  Click the setting for Video in that column and change it from *XnView* to **Associated program**.
7.  Click **OK**.

*Result:* When you double-click a video file in the browser, XnView will now launch it using your Windows default media player (e.g., VLC, MPC-HC) instead of opening a tab in XnView.

### Method 2: The ".ini" File Edit (Force Disable)
If the Custom Filter options are grayed out or unavailable in your specific build, you can force this behavior by editing the configuration file.

1.  Close XnView MP completely.
2.  Open your XnView MP installation folder (or `%appdata%\XnViewMP` if installed as a standard app).
3.  Locate the file named **xnview.ini**.
4.  Open it with Notepad.
5.  Search for the line:
    `useInternalVideoPlayer=true`
6.  Change it to:
    `useInternalVideoPlayer=false`
7.  Save the file and restart XnView MP.

### Method 3: Mouse Shortcut Workaround
If you prefer to keep the internal player for quick previews but want an option to open externally:

1.  Go to **Tools → Settings → Interface → Shortcuts**.
2.  Search for the command **Open with associated program**.
3.  Assign a key (e.g., `F3` or `Alt+V`).
4.  Now, when you select a video, hitting that key will launch your external player. (Note: You cannot assign "Double Click" to this action directly in the Mouse settings, only keyboard shortcuts).
