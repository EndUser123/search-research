---
title: "are there any chrome extension that I can use with perpexity comet, that keep the model picker pinned to 'Sonar'?"
date: "2026-04-18"
mode: "CONCISE"
uuid: "467f9b9a-7f4a-4603-ba5e-755c5a502cde"
entry_count: 1
---

## Human

are there any chrome extension that I can use with perpexity comet, that keep the model picker pinned to 'Sonar'?

## Assistant

Short answer: there’s no official or widely‑used Comet‑specific extension whose whole job is “always force the model picker to Sonar,” but there *is* at least one Perplexity model selector Chrome extension that (a) persists your chosen model and (b) should work in Comet like it does in Chrome, since Comet supports standard Chrome extensions.[1][2]

### What exists today

1. **“Perplexity Model Selector” Chrome extension (3rd‑party)**
   - Adds its own model selector UI on Perplexity, including **Sonar**.[1]
   - Features:
     - Quick switch between Auto, Sonar, GPT‑4o, GPT‑4.5, Claude 3.7 Sonnet, Grok‑2, Gemini 2.0 Flash, etc.[1]
     - **Persistent model selection** – it saves your chosen model and reuses it for future searches, which is the closest thing to “keep model pinned to Sonar.”[1]
   - It’s implemented as a standard MV3 Chrome extension with a content script matching `https://www.perplexity.ai/*`, which means it should also run inside **Comet**, because Comet explicitly supports Chrome extensions.[2][1]

2. **Comet + Chrome extensions generally**
   - Perplexity’s Comet docs state that Comet supports Chrome extensions (“Chrome extension support — keep all your favorite tools”).[2]
   - Comet’s policy docs even describe controlling extension types and install policy via the usual Chromium MDM mechanisms, confirming it’s a normal Chromium extension host.[1]

So: you can’t “pin” the *native* Comet model picker today, but you *can* use that extension so that whenever you open perplexity.ai in Comet, its injected selector is locked to Sonar and remembered.

### How to set this up in Comet

1. **Install the extension**
   - In Comet, open the Chrome Web Store page for the *Perplexity Model Selector* (the GitHub repo references a Web Store listing: `chromewebstore.google.com/detail/perplexity-model-selector/...`).[1]
   - Click **Add to Comet** (or “Add to Chrome,” depending on wording).[3]

2. **Enable it and ensure it runs on perplexity.ai**
   - Go to Comet’s extensions management (similar to `chrome://extensions` in Chrome).[3][1]
   - Make sure the Perplexity Model Selector is **enabled** and allowed on `https://www.perplexity.ai/*`.[1]

3. **Select Sonar once**
   - Open `https://www.perplexity.ai` inside Comet.
   - Use the extension’s injected model selector UI in the search interface and choose **Sonar**.[1]
   - The extension will persist that choice and reuse it for future queries, effectively “pinning” to Sonar unless you switch it.[1]

### Caveats / limits

- This is **not** an official Perplexity/Comet feature; it’s a community extension.[1]
- It only affects **Perplexity’s web app model choice**, not the internal “agent model” Comet uses to run browsing automations.
- Some users have reported that *certain* extensions behave inconsistently on Perplexity pages in Comet (e.g., Recall/Obsidian clippers), so there’s a small risk it may not hook properly in all Comet builds.[4]
- There’s no documented Comet policy or flag to globally force the UI model to Sonar across all sessions; the closest you get is:
  - Perplexity’s own “Model” setting in account settings (which just sets your default for the web app).[1]
  - A persistent model selector like the extension above.

### If that extension doesn’t work for you

Given your stack and comfort level, the fallback is trivial:

- Fork the GitHub repo, keep only **Sonar** in the `models` array, and have the content script:
  - Auto‑select Sonar on page load.
  - Optionally hide Perplexity’s native model picker so you don’t accidentally change it.[1]

This is a small MV3 content‑script tweak and should be much less effort than building a custom MCP/Comet integration.

Would you like a minimal MV3 `manifest.json` + `content.js` sketch that auto‑forces Sonar on any perplexity.ai page in Comet?
