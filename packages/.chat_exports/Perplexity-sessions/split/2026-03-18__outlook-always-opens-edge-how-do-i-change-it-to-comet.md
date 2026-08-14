---
title: "outlook always opens edge, how do I change it to comet?"
date: "2026-03-18"
mode: "COPILOT"
uuid: "89894688-e57f-4d3f-ad52-044973cbb3bd"
entry_count: 1
---

## Human

outlook always opens edge, how do I change it to comet?

## Assistant

You can’t set Outlook to open links directly in “Comet” by name, but you can make Outlook use your **system‑level default browser** (which you set to Comet).[1][2][3]

### 1. Tell Outlook to use your default browser
In **desktop Outlook (Windows 365 / Outlook 2021 etc.)**:  
1. Open Outlook.  
2. Go to **File → Options → Advanced**.[2][3][1]
3. Under **File and browser preferences**, find **“Open hyperlinks from Outlook in:”**.[3][1][2]
4. Change it from **Microsoft Edge** to **Default browser**, then click **OK**.[1][2][3]
5. Restart Outlook.[3]

Now Outlook will hand links to whatever your Windows default browser is.[4][2]

### 2. Set Comet as the default browser in Windows
You must set Comet as the default HTTP/HTTPS handler in Windows:

1. Press **Win + I** to open **Settings**.  
2. Go to **Apps → Default apps**.[5][6]
3. Scroll down and click **Choose default apps by protocol** (or similar).[6][5]
4. For **HTTP** and **HTTPS**, pick **Comet** if it appears; if Comet doesn’t list there, set the default browser in the main “Web browser” entry, then confirm Comet opens HTTP/HTTPS.[5][6]

### 3. If Comet doesn’t appear at all
- Ensure Comet is installed, and you can open it directly.  
- If it still doesn’t show up in Windows defaults, links will fall back to whatever Windows treats as the default (e.g., Edge, Chrome, etc.).[6][5]

If you tell me whether you’re using **“new Outlook” (the UI‑revamped Outlook for Windows)** or the **classic Outlook desktop**, I can give you the exact menu path for that edition.
