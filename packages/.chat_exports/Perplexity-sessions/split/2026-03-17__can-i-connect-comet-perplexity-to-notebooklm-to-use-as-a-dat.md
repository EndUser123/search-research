---
title: "can I connect comet / perplexity to notebooklm to use as a data source?"
date: "2026-03-17"
mode: "COPILOT"
uuid: "5d53359d-e35c-4e2e-a827-e45f0c1cead0"
entry_count: 3
---

## Human

can I connect comet / perplexity to notebooklm to use as a data source?

## Assistant

Short answer: there is no native, first‑class integration today where Perplexity/Comet can directly treat Google’s NotebookLM as a built‑in “data source” in the same way it does for its own libraries or web search.

## Current integration status

- Perplexity does not list NotebookLM as a supported connector or source in its official docs.  
- NotebookLM itself exposes no public MCP server, API, or connector specifically advertised as compatible with Perplexity or Comet. (This is an inference from Perplexity’s docs plus the lack of any mention of NotebookLM integrations.)

So you cannot “add NotebookLM” as a toggleable source in Perplexity/Comet the way you would add, say, an MCP connector to a database or file system.

## What you can do instead

Given your background, the realistic path is to invert the direction and/or use MCP as glue:

1. Use MCP as the bridge  
   - Perplexity supports local (and soon remote) MCP servers, which can connect to arbitrary external data sources and tools.  
   - If NotebookLM ever exposes:  
     - a public API,  
     - or can be driven via a headless browser / automation layer,  
     then you could wrap that in a custom MCP server and surface it as a connector to Perplexity. This would make “NotebookLM-derived” content available, even if Perplexity still doesn’t know it’s NotebookLM.

2. Share underlying data, not the NotebookLM app  
   - Treat NotebookLM as “one of several consumers” of a shared corpus, not as the canonical store.  
   - Put your source material (docs, PDFs, transcripts) in a location both systems can read: e.g., GDrive folder, local files, or your own RAG store.  
   - Connect Perplexity/Comet to that same corpus via:  
     - filesystem MCP (for local stores),  
     - a custom remote MCP over your vector DB / knowledge service,  
     while NotebookLM ingests the same raw docs through its own UI.

3. Use export → ingest workflows  
   - If NotebookLM lets you export notes/summaries, you can:  
     - Export from NotebookLM (e.g., text/markdown).  
     - Save them into a directory or repo wired into Perplexity via filesystem MCP or a custom “notes” MCP.  
   - Perplexity then reasons over those exports as part of its context, even though it cannot “call NotebookLM” live.

## Practical next step

Given what exists today, the most robust, low-friction option is: build or reuse a simple MCP server over the same source-of-truth corpus that you’re already feeding into NotebookLM (e.g., a GDrive sync → local mirror → filesystem MCP, or a small HTTP RAG API wrapped as a remote MCP). Perplexity then queries that corpus directly, sidestepping the need to integrate with NotebookLM as a product.

Would you rather: (a) share a corpus between Perplexity and NotebookLM, or (b) go all‑in on a custom MCP that becomes your primary knowledge back-end that both can read from indirectly?

## Human

how do I add a mcp server to comet so you can use it's features?

## Assistant

You add an MCP server to Comet via Perplexity’s **Connectors → MCP** flow; once it’s configured and running, its tools become available as “Sources” you can toggle for a Comet/Labs session.

### Prerequisites and platform limits

- MCP support is currently documented for the **Perplexity Mac app** via local MCP; remote MCP is “coming soon.”  
- You need: Perplexity account (ideally paid, since rollout is prioritized there), the **Perplexity Mac app**, and a working MCP server command (from the server’s README).

### One‑time setup for local MCP (Mac)

1. Open **Perplexity Mac app → Account settings → Connectors**.  
2. Install **PerplexityXPC** when prompted; this is the helper that lets Perplexity talk to local MCP servers securely.  
3. After install, go back to **Connectors** and click **Add Connector**.

### Register your MCP server

On the “Add Connector” page, under the **Simple** tab:

- Set **Server Name**: any label (e.g. `my-files-mcp` or the feature name you care about).  
- Set **Command**: the exact shell command that starts your MCP server, as documented in that server’s README (examples: `npx -y @modelcontextprotocol/filesystem`, `uvx my-mcp`, `python -m my_mcp`).  
- Ensure all runtime deps are installed first (Node, Python, etc.) per the server README.  
- Click **Save** and wait until the connector shows status **Running** in the list.

At this point, Comet/Labs can invoke any tools that server exposes; they’re now part of the environment, even though there’s no special “Comet-only” toggle.

### Enabling and using it in chats / Labs

1. From the Perplexity home screen, under **Sources**, toggle your new MCP connector **on**.  
2. Start a **new chat** or **Labs/Comet project** with that source enabled.  
3. Prompt in a way that clearly calls for the MCP’s capabilities, e.g. “Use my filesystem MCP to inspect the repo in ~/Projects/x and summarize the architecture.”  
4. The assistant will call the MCP tools when needed and (if required) ask for confirmation before performing actions like editing files or creating resources.

### Minimal sanity‑check example

If you wire up, say, the official **filesystem MCP**:

- Configure a connector with command like: `npx -y @modelcontextprotocol/filesystem` (or whatever its README specifies).  
- In a new Comet/Labs run, with that source toggled, ask: “List the files in the directory you have access to via the filesystem MCP, then propose a refactoring plan.”  
- If you see tool calls and file listings show up, the integration is working and you can start layering your own MCP features.

Do you already have a specific MCP server in mind (filesystem, custom RAG, app automation), or are you still choosing which one to wire into Comet first?

## Human

I'm on windows 11

## Assistant

Perplexity’s current MCP integration is Mac‑only, so you can’t yet add or use MCP servers directly from Comet on Windows 11.[1][2]

### What this means on Windows

- Local MCP support is documented specifically for the **Perplexity Mac app**, via the PerplexityXPC helper and Connectors UI.[2][1]
- Docs and coverage explicitly say MCP is available on Mac now, with **remote MCP “planned/coming”**, but there is no equivalent Windows connector UI or helper app yet.[2]
- So on Windows/Comet, there’s no supported way today to register a local MCP server in the same way you can on macOS.[1][2]

### Workarounds you can use today

Given your stack, the main options are:

- Run MCP‑capable clients on Windows that can themselves call Perplexity via API: e.g., Claude Desktop for Windows with a **Perplexity MCP server** so Claude can invoke Perplexity search from Windows tools, while Comet is just your browser.[3][4]
- Host your custom tools behind a normal HTTP API (or RAG service) and just call them “manually” by copy‑pasting URLs/results into Comet, until Perplexity exposes remote MCP that works cross‑platform.[5][1]
- If you have access to a Mac somewhere, you can set up MCP there and treat it as your “tooling host,” while you keep Windows as your main dev box.

Once Perplexity ships remote MCP that works from the browser or from Windows, your MCP servers should become available to Comet without OS‑specific helpers.[1][2]

Do you have access to any Mac hardware or macOS VM that you’d be willing to use as an MCP host, or do we need to plan around “Windows‑only plus browser” for now?
