---
title: "on windows 11, I'm using codex.  It says it can't see any web pages or look at any web based diagrams.  This seems wrong"
date: "2026-04-17"
mode: "CONCISE"
uuid: "1eacaa65-ee64-4978-8379-48d588670b96"
entry_count: 4
---

## Human

on windows 11, I'm using codex.  It says it can't see any web pages or look at any web based diagrams.  This seems wrong.  What do I need to do, in order for codex, to look at the web pages it is creating, and see the visual problems, and even to click buttons for testing and fixing?

## Assistant

Perplexity's "Codex" likely refers to OpenAI's Codex AI agent (or a misreference to Perplexity Computer/Comet integration), which has limited web visibility on Windows 11 due to sandboxing that blocks full browser access, network, or visual rendering in agent mode. This prevents seeing created web pages, diagrams, or clicking buttons natively.[1][2]

## Enable Browser Access
Install Perplexity's **Comet browser** (agentic Chromium-based), which grants AI full visual perception via annotated DOM (interactables like buttons/links), clicking, scrolling, and testing—explicitly for AI agents like Computer to "see" and fix web issues.[3][4][5]
- Download Comet .exe from https://www.perplexity.ai/comet (Windows 11 supported).[6][7]
- Run installer; sign in with Perplexity Pro/Max account (required for Computer agents).[8]
- Launch Comet, open Perplexity Computer (via perplexity.ai/computer or sidebar), grant browser permissions for agent control.[9]

## Test Web Interaction
In Comet with Computer agent:
1. Prompt: "Create a webpage with a broken button, open it, screenshot diagram issues, click/fix."[4]
2. Agent reads simplified HTML/visuals, clicks via ref IDs/coords, iterates visually.[5]
Confidence: High (direct from Perplexity docs/tech analyses); assumes Pro subscription—free tier limits agents.[10]

## OpenAI Codex Alternative
If OpenAI Codex: Use in-app browser (Ctrl+Shift+B) for shared previews/local dev (no auth/cookies). Full agent visual testing unreliable on Windows due to sandbox—no network/visuals. Switch to Comet for production web fixing.[2][1]

Next: Confirm "codex" (OpenAI or Perplexity?) and subscription for exact setup.

## Human

It's OpenAI Codex CLI/app

## Assistant

**OpenAI Codex CLI/app on Windows 11 has experimental native support with no direct web page visibility, rendering, or interactive clicking—it's sandboxed to your directory (read/edit files, run local commands only), blocking network/browser access by design for security.** Use the **Codex desktop app** (not pure CLI) for limited visual web testing via its in-app browser, or run CLI in **WSL2** for stability.[1][2][3]

## Install/Run Codex CLI (Experimental)
- Requires Node.js/npm; ChatGPT Plus/Pro/API key.[1]
```
npm i -g @openai/codex
codex  # Auth first run; dir-scoped only
```
- Windows unstable: Crashes/UI issues common; no web.[1]

## Enable Web Visuals (App Path)
Download Codex app (codex.app or npm-linked); open project, use **in-app browser** (Ctrl+Shift+B).[3]
- Previews local dev servers/public pages (no login/cookies/extensions).[3]
- Codex "sees" rendered HTML via shared view; add visual comments on elements/diagrams (Shift+click areas).[3]
- Prompt: "Fix mobile button overflow per browser comment"—iterates code, re-previews.[3]
- Limits: Untrusted; no auth flows/secrets; scope to single pages.[3]

## Recommended: WSL2 Setup
1. Enable WSL2/Ubuntu (Windows Settings > Apps > Optional features).[1]
2. In WSL: `npm i -g @openai/codex; codex`—full Linux stability.[1]
3. For web: Run local server (e.g., `npm start`), use app's in-app browser or external (manual share screenshots).[3]
- Multimodal: Drag screenshots/diagrams to CLI/app for "visual" analysis (OCR/parsing, not live).[4]

## Alternatives for Full Clicking/Testing
- **Playwright/Puppeteer**: Codex CLI/app can generate/run these for headless/visual browser automation (screenshots, clicks).[4]
- **VS Code + Continue.dev/Cursor**: Native web preview + agent vision.
Uncertainty: No native "seeing/clicking" web in sandbox; app browser closest (read-only shared). Test in-app first.[3]

What project/web tool (local server, framework)?

## Human

I'm not fully understanding. In the codex from OpenAI Windows 11 application, you say use Ctrl-Shift-B, but I don't know what to do after that.

## Assistant

You’re right to be confused—OpenAI’s Codex app UX around the browser is not obvious, and the docs are a bit hand‑wavy. Let’s walk it step‑by‑step and also be clear about what it **can** and **cannot** do.

Below is **how to actually use Ctrl+Shift+B**, and what you should expect.

***

## 1. Preconditions: What has to be true first

All of this applies to the **Codex desktop app**, not the bare CLI in a terminal. The CLI has **no browser**; only the app does.[1][2]

You need:

1. **Codex app installed on Windows** and signed in (ChatGPT / OpenAI account).[1]
2. A **folder opened as a project** in Codex that contains your web app (HTML, React, etc.).[1]
3. Ideally, a **dev server running** (e.g. `npm run dev`, `npm start`) so you have a URL like `http://localhost:5173` or similar.[3]

If you don’t have (3), the in‑app browser can still open static HTML files, but the flow is a bit different.

***

## 2. What Ctrl+Shift+B actually does

From the official docs:  

> “Open the in-app browser from the toolbar, by clicking a URL, by navigating manually in the browser, or by pressing Cmd+Shift+B (Ctrl+Shift+B on Windows).”[3]

So:

- **Ctrl+Shift+B** on Windows = *Open/bring forward the in‑app browser panel* in the Codex app.[3]
- It does **not** automatically know which URL to open unless you either:
  - Have a **dev server task** configured that Codex knows about and can start/use, or  
  - Manually type/paste a URL (e.g. `http://localhost:3000` or a public URL).[3]

Also, the in‑app browser has limitations:
- No login/auth/cookies/extensions; only pages Codex can open without signing in.[3]

***

## 3. Concrete step‑by‑step flow on Windows 11

### A. Make sure your web app can be opened in a browser

If it’s a local dev app:

1. In Codex, open the folder with your project (File → Open Folder).[1]
2. In the **terminal panel** inside Codex (or an external terminal), run your dev server, e.g.:

   ```bash
   npm install   # first time
   npm run dev   # or npm start / next dev, etc.
   ```

3. Note the URL it prints, e.g. `http://localhost:5173` or `http://localhost:3000`.

***

### B. Open the in‑app browser with Ctrl+Shift+B

1. Focus the Codex app window.  
2. Press **Ctrl+Shift+B**.  
   - This should open a **browser pane** either as a right‑side panel or bottom panel.  
   - If nothing appears, look for a small “browser” icon in the toolbar and click that once; after that, Ctrl+Shift+B should toggle it.[3]

3. In the browser’s address bar:
   - Paste the URL for your app (e.g. `http://localhost:3000`).  
   - Or type any **public URL** that doesn’t require login.

Now Codex has a **rendered view** of your page inside the app.

***

## 4. How to “show Codex the visual problem”

Once the in‑app browser is open on the right URL, you need to **comment on the page** so Codex understands what you are seeing.[3]

From the docs:[3]

> “When a bug is visible only in the rendered page, use browser comments to give Codex precise feedback on the page.  
> – Turn on comment mode, select an element or area, and submit a comment.  
> – In comment mode, hold Shift and click to select an area.”

In practice:

1. Look for a **comment / annotation icon** in the browser pane toolbar (often looks like a speech bubble or comment pin). Click it to enter **comment mode**.[3]
2. Move your mouse over the page. In comment mode:
   - Click on a specific element (button, card, etc.) **or**  
   - Hold **Shift and click** drag/select an area (e.g. the broken section).[3]
3. A small pop‑up text box should appear. Describe the problem, e.g.:

   > “On mobile width, this ‘Submit’ button is offscreen to the right and not clickable.”

4. Submit the comment. Codex will see:
   - The screenshot/region you marked, and  
   - The text you wrote about it.[3]

Then in the **main Codex chat**, you can say something like:

> “Use the browser comments on `/settings` to fix the layout and overflow so the button is visible on mobile.”

Codex will then:
- Edit the relevant source files in your project.  
- Optionally run or restart the dev server.  
- You can re‑load in‑app browser and verify.

***

## 5. What Codex *cannot* do in that browser

Very important constraints (this may be where expectations differ):

- The in‑app browser is **for review and iteration**, not a full automation agent.[3]
- It **does not**:
  - Log into authenticated sites.  
  - Use your normal Chrome/Edge profile, cookies, or extensions.  
  - Run completely arbitrary browsing “like a user” on the open internet.[3]
- It **can**:
  - Load **local dev servers or public anonymous pages**.  
  - Understand what you highlight/comment on.  
  - Use that as context to modify your code.[3]

It’s not like Playwright/Comet-style full browser automation; it’s more like a **shared view/screenshot + DOM hints**.

***

## 6. If Ctrl+Shift+B seems to do nothing

Possible reasons and checks:

1. **You’re in the CLI, not the GUI app**  
   - If you’re in a plain terminal with `codex` running, Ctrl+Shift+B does nothing. Only the **desktop app** has the in‑app browser.[2][1]

2. **Older or different app build**  
   - Some early builds or unpacked versions may not have the browser UI enabled yet.[4]
   - Confirm you’re on the official Codex app from OpenAI’s site.[1]

3. **Browser pane already open but hidden**  
   - Look for a browser icon or “Browser” tab and click it.  
   - Try resizing panels—sometimes it’s collapsed to 0 height/width.

4. **Keybinding conflicts**  
   - If Ctrl+Shift+B is captured by another tool (e.g. Windows shortcut managers), use the toolbar button instead.[5][6]

***

## 7. How to get to “click buttons for testing and fixing”

Today, with stock Codex app, the realistic pattern is:

1. Run dev server.  
2. Use in‑app browser (Ctrl+Shift+B) to open `http://localhost:...`.  
3. **You** click and reproduce the bug.  
4. Enter comment mode, mark the broken area, describe the issue.  
5. Tell Codex in chat: “Use the browser comments to fix this issue.”  
6. Let it change code, reload the page, repeat.

If you truly want **automatic clicking/testing** (without you manually clicking):

- You’d pair Codex with **Playwright / Puppeteer / a browser MCP**; Codex generates tests and scripts, and those tools actually drive the browser.[7]
- That’s a different setup (more like what you’re probably doing with Claude Code + MCP).

***

### To make this concrete for you

Given your workflow, I’d propose:

1. Confirm: Are you running **Codex desktop app**, not only CLI?  
2. In the app, open your current React/Next project.  
3. Start dev server in the integrated terminal.  
4. Hit **Ctrl+Shift+B**, paste the localhost URL, and make one test comment on a random button.  
5. Paste what you see (or a screenshot) back here if any of those steps don’t match reality.

If you tell me exactly what appears after Ctrl+Shift+B (nothing, a panel with no URL bar, etc.), I can adapt this to the specific build you have.

## Human

are there youtube videos for this on windows 11?

## Assistant

Yes—there are a few useful Windows‑focused Codex videos, but note that **most current videos focus on install + basic usage, not deeply on the in‑app browser commenting flow.** You’ll probably need to combine a general “Codex Desktop App on Windows” video with the browser docs I summarized earlier.

Here are the most relevant ones:

### 1. Desktop app on Windows 11 (what you want)

- **“Getting Started with Codex Desktop App || Full Beginner Guide”** (YouTube)[1]  
  - Walks through **installing and using the Codex desktop app**, including selecting a project folder and running tasks.  
  - On a recent build (2026‑03‑24), so the UI is close to what you see on Windows 11.[1]
  - Watch this for: getting comfortable with the app layout, panels, terminals, and where the browser panel typically lives.

- **“Install & Use Codex App on Windows for FREE (The Only …)”**[2]
  - Explicitly about **Codex app on Windows**, aimed at ChatGPT users.  
  - Covers installing the app and basic workflow; may briefly show browser panel or project view.[2]

- **“How To Download & Install ChatGPT Codex on Windows 11”**[3]
  - 2026 tutorial that shows **fetching Codex from the Microsoft Store**, launching it, and logging in.[4][3]
  - Good for confirming you have the same Windows build and layout.

These will help you visually anchor the UI I’ve been describing (where the right‑side pane is, how the terminal and project tree look, etc.), even if they don’t narrate “now press Ctrl+Shift+B” explicitly.

***

### 2. CLI‑oriented but useful context

These focus on the CLI, not the GUI, but are helpful to understand how Codex thinks about projects and commands:

- **“How to Install & Use OpenAI Codex CLI on Windows”**[5]
- **“How to Install And Use OpenAI Codex CLI”**[6]
- **“OpenAI Codex Tutorial #1 – Introduction & Setup”**[7]

They’ll reinforce the idea that:
- CLI = no in‑app browser (just terminal).  
- Desktop app = has the browser panel and visual context (what you’re after).[8][9]

***

### 3. How to tie this to the in‑app browser

There isn’t yet (as of April 2026) a great, widely‑watched “Codex in‑app browser + comments” Windows‑specific tutorial. The detailed behavior is in the official docs: Codex app → **In‑app browser** section.[10]

From the docs, once you’ve got the app layout clear from a video, the concrete sequence is:

1. Open project in Codex app.  
2. Start dev server in the integrated terminal.  
3. Open the browser panel (toolbar button or **Ctrl+Shift+B**).[10]
4. Enter the localhost URL in the browser pane’s address bar.  
5. Click the “comment” icon in that pane, then Shift+click to mark an area and describe the bug.[10]

You can watch one of the “Desktop App Beginner Guide” videos side‑by‑side with that doc page and my prior step‑by‑step to translate it to exactly what you see on your screen.

***

If you’d like, tell me **which video you pick** (e.g. the March 24 beginner guide), and I can give you a “watching notes” checklist like: *“At 3:10, when they open the right panel—that’s the slot where your browser will appear when you hit Ctrl+Shift+B.”*
