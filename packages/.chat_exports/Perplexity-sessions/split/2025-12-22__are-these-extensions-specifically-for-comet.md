---
title: "are these extensions specifically for comet?"
date: "2025-12-22"
mode: "COPILOT"
uuid: "e70abf04-3697-4b55-9c3e-7308e4a2a41c"
entry_count: 4
---

## Human

are these extensions specifically for comet?

## Assistant

No, there are no extensions that are “specifically for Comet” in the sense of a separate Comet-only extension ecosystem. Comet is a Chromium-based browser that supports most regular Chrome extensions, which you install fresh from the Chrome Web Store or via standard extension install flows, just like in Chrome or other Chromium browsers.[1][2]

Comet’s differentiation comes from its built-in AI features (assistant, personal search, browser commands, etc.), not from a special extension format. The main Comet-specific requirement is that you need to reinstall and reconfigure your existing Chrome extensions when moving to Comet, because extension data does not automatically transfer from Chrome.[2][3][1]

## Human

no extensions that modify comet behavior?

## Assistant

Based on the Perplexity documentation, Comet does not officially offer extensions that modify its core behavior or AI functionality. However, there's an important limitation: **Comet does not support extensions that alter the new tab page**.[1]

Beyond that restriction, standard Chromium extensions should work in Comet, but they operate the same way they would in Chrome—they don't have special hooks into Comet's built-in features like the Assistant panel, Personal Search, or Agent Actions. Those capabilities are native to the browser itself, not extensible through third-party add-ons.

If you're looking to customize Comet's behavior, your options are:
- **Settings menu** – Configure privacy, ad blocking, tab management, and assistant preferences
- **Comet's native features** – Use the Assistant button, @tab selection, and browser commands (which are built-in, not extension-based)
- **Standard Chrome extensions** – Install any extension except those that modify the new tab page

There's no "Comet extension API" or developer ecosystem for extending Comet's AI-specific functionality like there would be for a platform like VS Code or Claude's tools.

## Human

any extensions for perplexity

## Assistant

Based on Perplexity's help documentation, there are no official third-party extensions or add-ons for the Perplexity web app or Comet browser that extend Perplexity's core AI functionality.

Perplexity's capabilities are delivered through:
- The web app itself (perplexity.ai)
- The Comet browser (with built-in features like Personal Search, Assistant panel, Agent Actions)
- The Sonar API for developers who want to integrate Perplexity into their own applications

If you're looking to automate or enhance your Perplexity workflow, your best options are:
- **Comet's native features** – Browser commands, @tab selection, Assistant actions
- **Sonar API** – Build custom integrations or applications (contact api@perplexity.ai for details)
- **Standard browser extensions** – Use general-purpose extensions (password managers, ad blockers, etc.) in Comet or other browsers to improve your overall browsing experience

Unlike some other AI platforms, Perplexity doesn't have a public extension marketplace or plugin system at this time.

## Human

but what about for chrome?  surely it has extensions for perplexity in the extensions for chrome?

## Assistant

You're absolutely right! There are several Chrome extensions for Perplexity available in the Chrome Web Store:[1][2][3]

1. **Perplexity - AI Companion** – The most popular official extension (421 ratings). Allows you to ask questions directly from your toolbar, get instant page summaries, and have contextual conversations without leaving your current tab.[1]

2. **Perplexity - AI Search** – Lets you set Perplexity as your default search engine in Chrome. Search from your address bar and get lightning-fast results with transparent sourcing (174 ratings).[2]

3. **Perplexity AI** – Another extension that routes searches through Perplexity.ai. You can type directly in the browser's search bar and Perplexity processes the query, with the ability to switch between search engines.[3]

There's also a **third-party community extension** created by a user (DigitsOfPi314) that integrates Perplexity results into Google Search results in a sidebar, so you can use both simultaneously.[4]

You can also manually add Perplexity as a custom search engine in Chrome settings without an extension by going to Settings → Search Engine and configuring a custom search URL.[5]

So yes—there's actually a decent ecosystem of extensions available, they just aren't officially listed in Perplexity's help docs since they're managed through the Chrome Web Store rather than Perplexity's own website.
