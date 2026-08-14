---
title: "are you able to find the repos for each of these extensions, and idtentify which would be best to enable chrome cdp, so "
date: "2026-08-02"
mode: "COPILOT"
uuid: "eb85acae-f401-4a03-b099-c56cb81e5469"
entry_count: 1
---

## Human

are you able to find the repos for each of these extensions, and idtentify which would be best to enable chrome cdp, so that my agentic cli can talk to comet best?

## Assistant

You already have multiple good CDP-capable options here, but for a Comet‑style agentic CLI talking to a browser via CDP, the OpenClaw relay family and BrowserPilot stand out as the most suitable foundations.[1][2][3][4]

I’ll break this into:
- repos for the key CDP extensions on that page
- how they expose CDP / relay endpoints
- which one is best aligned with a “Comet‑like” agentic CLI, plus concrete next steps

***

## 1. Mapping the Chrome Web Store results to repos

From the search page you’re viewing, these are the extensions that explicitly mention CDP or agentic browser control.[1]

Below is the subset that looks relevant to “enable Chrome CDP so my agentic CLI can talk to Comet‑like browser control”, and whether there’s an identifiable GitHub‑style repo.

| Extension (Web Store) | Purpose (from listing) | Repo / project found | CDP exposure mode |
|-----------------------|------------------------|----------------------|-------------------|
| OpenClaw Browser Relay (multiple IDs + “for Windows”) | Attach OpenClaw to existing Chrome tab via local CDP relay server. [1] | `audichuang/openclaw-chrome-extension` – OpenClaw Chrome Extension (Browser Relay). [3] | Local HTTP + WebSocket relay to managed CDP port (default 18792), auto‑attach tabs. [3][4] |
| OpenClaw Extension | AI browser copilot with CDP dashboard. [1] | Same OpenClaw ecosystem; issues and setup docs under `openclaw/openclaw` and related repos. [5][6][4][7] | Uses dedicated Chrome profile controlled via CDP; extension provides relay + UI. [4] |
| BrowserPilot | AI browser automation for live authenticated tabs; MCP‑compatible. [1] | `ai-naymul/BrowserPilot` GitHub repository. [2] | Treats browser as a tool for LLM agents; uses CDP / automation stack under the hood. [2] |
| CoTabor | AI browser co‑worker with LangGraph agent and MCP tool ecosystem. [1] | Not directly resolved, but strongly suggests a GitHub repo behind MCP tools (likely linked from extension or docs). [1] | MCP tool ecosystem where browser control is one tool; details likely in its repo. (Uncertain.) |
| Hyperframe Screenshots | Capture pages using CDP, including full page/viewport/crop. [1] | No repo found yet; likely proprietary. (Uncertain.) | Uses DevTools Protocol for screenshots only, not general control. [1] |
| AX Tree Exporter | Exports accessibility tree via CDP. [1] | No repo found yet; may have small GitHub but not easily discoverable. (Uncertain.) | CDP used for AX tree, not full automation. [1] |
| Mini Modifier | Intercept/modify JSON API responses via CDP. [1] | No repo surfaced from quick search; may be closed‑source. (Uncertain.) | DevTools Network interception only. [1] |
| Tool++ | Captures browser debugging sessions. [1] | Appears to be part of RecordDA / Tool++ ecosystem, but repo URL not confirmed in quick search. (Uncertain.) | Debugging capture; limited CDP exposure. [1] |
| Browsr Relay | Attach browser tabs as relay sessions for Browsr Cloud. [1] | Likely backed by `browsr.dev` repos, but exact extension repo not in top results. [1] | Relay sessions for a remote cloud service, not a simple local CDP port. [1] |

### The clearly identified repos

1. **OpenClaw Chrome Extension (Browser Relay)**  
   - Repo: [`audichuang/openclaw-chrome-extension`](https://github.com/audichuang/openclaw-chrome-extension).[3]
   - Purpose: attach OpenClaw to all Chrome tabs automatically so the gateway can automate them via a local CDP relay server.[3]
   - Default relay port: `18792`, matching an “Managed browser CDP / Chrome extension relay” endpoint in OpenClaw’s setup guide.[4][3]

2. **OpenClaw / agent-browser integration**  
   - An OpenClaw setup guide shows a port layout: `18789` (Gateway WebSocket), `18791` (browser control HTTP API), and `18792` (managed browser CDP / Chrome extension relay).[4]
   - That guide references a GitHub project `vercel-labs/agent-browser` for command‑line CDP control (`agent-browser --cdp 18792`).[4]

3. **BrowserPilot**  
   - Repo: [`ai-naymul/BrowserPilot`](https://github.com/ai-naymul/BrowserPilot).[2]
   - Described as an open‑source alternative to Perplexity Comet + director.ai + Firecrawl, focused on natural language browser automation.[2]

4. **OpenClaw core issues / config**  
   - Issues under `openclaw/openclaw` describe browser relay behavior and CDP configuration, including `cdpUrl` and `cdpPort` fields in `openclaw.json`.[6][7]
   - Example config snippet sets a `chrome` profile with `cdpPort: 9222`.[6]

Confidence:  
- FACT: Repos for OpenClaw Chrome Extension and BrowserPilot exist and expose CDP‑style browser control.[2][3][4]
- CONSENSUS: These projects are considered usable, modern CDP tooling based on issue activity and docs.[5][7][6][4]
- SPECULATION (medium): CoTabor, Mini Modifier, Hyperframe etc. have internal repos but are less suitable as a primary CDP bridge for an agentic CLI.

***

## 2. How these extensions actually expose CDP to an agent/CLI

### OpenClaw Chrome Extension (Browser Relay)

From the extension repo and setup guide:[3][4]

- The extension connects to a local relay server, default `http://127.0.0.1:18792/`.[3][4]
- That relay multiplexes **tabs** → CDP sessions, exposing:
  - HTTP control API at `18791` for browser control.[4]
  - WebSocket CDP endpoint at `ws://127.0.0.1:18792/cdp` shared by all tabs, according to an OpenClaw issue.[7]
- The extension can auto‑attach to all tabs or let you click to attach/detach per tab, depending on variant.[3][4]
- OpenClaw recommends a dedicated Chrome profile for relay usage, not your personal profile, so agents don’t interfere with your normal browsing.[4]

This architecture is essentially:

> Agentic CLI → local gateway → CDP relay (18792) → OpenClaw Chrome extension → real browser tabs.[7][3][4]

### BrowserPilot

From the BrowserPilot repo description:[2]

- BrowserPilot is an “open‑source alternative to Perplexity Comet and director.ai and firecrawl combined”, with natural language browser automation and data extraction.[2]
- It is explicitly framed as a **tool for LLM agents**, i.e., you call BrowserPilot from an agent/CLI, and it handles navigation, scraping, and interactions.[2]

The details of its CDP integration are not fully visible from the snippet, but given its goals and modern stack, it very likely uses CDP, Playwright, or similar under the hood, and exposes a CLI or HTTP server tool that your agent can call.[2]

Assumption: BrowserPilot offers a CLI/server that agents can call, and that internally it uses CDP/automation. I would verify its README for exact ports and protocols before wiring it in (low uncertainty once inspected).

### OpenClaw core / agent-browser

From the OpenClaw browser setup guide:[4]

- OpenClaw runs a dedicated Chrome profile controlled via CDP, separate from your personal browser.[4]
- Port layout includes `18792` as “managed browser CDP / Chrome extension relay” and examples of `cdpPort` for profiles like `work`.[6][4]
- `agent-browser --cdp 18792` is shown as the canonical way to connect to the managed browser’s CDP port.[4]

That means a **CLI tool already exists** (`agent-browser`) that expects a CDP port and acts as a high‑level browser agent.[4]
You can either call `agent-browser` from your own agentic CLI or mirror this pattern for your own Comet‑like CLI.

***

## 3. Which extension is “best” to enable Chrome CDP for a Comet‑style agentic CLI?

Given your goal (“my agentic CLI can talk to Comet best”), the key criteria are:

- Stable CDP relay with clear port semantics.  
- Good match to an agent/CLI orchestration model (MCP, tools, HTTP, or subprocess).  
- Strong ecosystem and documentation so you’re not fighting mystery behavior.  
- Prefer open‑source so you can introspect and harden.

Based on the data:

### 3.1. For a dedicated managed CDP browser: OpenClaw Chrome Extension + OpenClaw relay

This is the most direct, CDP‑focused choice.[3][4]

- It explicitly exposes **CDP via local ports** (18792 and others) intended for agent control.[7][4]
- The extension repo is open‑source and focused on “attach OpenClaw to all tabs automatically so the Gateway can automate them”.[3]
- The setup guide is already written in terms of a CLI: `agent-browser --cdp 18792`.[4]

For a Comet‑like architecture, you can:

- Treat the OpenClaw CDP relay as your managed browser.  
- Have your agentic CLI open a WebSocket to `ws://127.0.0.1:18792/cdp` or call an HTTP API on `18791`.[7][4]
- Configure profiles via `openclaw.json` (e.g., `chrome` with `cdpPort: 9222` if you want direct Chrome CDP instead of relay).[6]

I would consider **OpenClaw Chrome Extension + its relay as the best CDP enabler** for a Comet‑like CLI, with the caveat that issues show some tab‑attachment regressions you’ll want to track (loss of connection on navigation or tab change).[5][7]

Confidence: High that this is the correct choice if you want dedicated CDP and local control, because the docs and issues are explicit about CDP and relay semantics.[6][7][3][4]

### 3.2. For “Comet‑style” high‑level browser agent: BrowserPilot

BrowserPilot is explicitly pitched as an open‑source alternative to Perplexity Comet.[2]
If your CLI is meant to behave like Comet, you may want to use BrowserPilot itself as the browser tool:

- Your CLI exposes a “browser” tool that internally calls BrowserPilot’s CLI or HTTP API.[2]
- BrowserPilot itself handles navigation, scraping, and interactions, probably via CDP or a high‑level automation framework.

In that case, you might not need to wire CDP manually; you just need:

- A well‑defined interface from CLI → BrowserPilot (e.g., JSON RPC, MCP, or simple CLI invocation).[2]

Confidence: Medium, pending a README inspection, but the positioning strongly suggests it is designed as a plug‑in agent tool similar to Comet.[2]

### 3.3. Systems that are less ideal as core CDP bridge

- **Hyperframe Screenshots**: great for screenshot capture via CDP, but it exposes only screenshot functionality, not full browser control.[1]
- **AX Tree Exporter**, **Mini Modifier**, **Tool++**: highly focused on specific DevTools capabilities (AX tree, network interception, debugging). Useful as *additional* tools, but not as your main managed CDP endpoint.[1]
- **Browsr Relay**: optimized for connecting tabs to a cloud service, not a local agentic CLI.[1]

Consensus judgement: For your use‑case, these are supplementary tools, not the primary CDP bridge.

***

## 4. Concrete next steps to wire this into your agentic CLI

Assuming you want both a managed CDP browser and a Comet‑like agent behavior:

### Step 1 – Install and configure OpenClaw Chrome Extension relay

1. Clone and build the extension from `audichuang/openclaw-chrome-extension`.[3]
2. Follow the OpenClaw browser setup guide:[4]
   - Start the OpenClaw gateway with browser control enabled.[4]
   - Ensure `http://127.0.0.1:18792/` is reachable as your managed CDP relay.[4]
   - Load the extension via `chrome://extensions` → Developer mode → Load unpacked, using the path printed by `openclaw browser extension path`.[4]
   - Use a dedicated Chrome profile for this relay browser.[4]

### Step 2 – Configure your agentic CLI to use the CDP port

In your CLI’s config (JSON/YAML/TS), define a browser tool that:

- Connects to `ws://127.0.0.1:18792/cdp` for DevTools commands.[7][4]
- Or wraps `agent-browser --cdp 18792` and sends high‑level navigation tasks (depending on how much you want to implement yourself).[4]

From the OpenClaw config example, you can also define profiles like:

```json
{
  "browser": {
    "profiles": {
      "chrome": {
        "cdpPort": 9222,
        "color": "#00AA00"
      }
    }
  }
}
```

This shows how to route different profiles to different CDP ports.[6]

### Step 3 – Optionally integrate BrowserPilot as your “Comet” module

If you want an open‑source Comet analogue:

- Install BrowserPilot from `ai-naymul/BrowserPilot`.[2]
- Expose a tool in your CLI where user tasks like “find X, click Y, extract Z” are delegated to BrowserPilot’s API/CLI.[2]
- Let BrowserPilot itself manage the browser automation; your CLI focuses on orchestration, task decomposition, and multi‑agent routing.

This gives you:

- OpenClaw relay for low‑level CDP/browser control.[3][4]
- BrowserPilot for “Comet‑like” human‑level browser tasks (if its abstraction matches what you want).[2]

***

## 5. Assumptions and uncertainties

- I have not inspected BrowserPilot’s full README and source in this pass; I’m inferring its CDP/automation details from its description and positioning.[2]
- CoTabor and some others likely have rich agent/browser integration, but without the repo URL directly visible, I’m not treating them as first‑choice building blocks.[1]
- OpenClaw browser relay has active issues about connection stability across navigation/tab changes; you should read those before putting it into production and possibly apply fixes from forks like `openclaw-browser-relay` hardened versions.[8][5][7]

If you share a bit more about your current agentic CLI stack (MCP vs custom tools vs LangGraph, and whether you want cloud vs strictly local), I can suggest a concrete TypeScript/Python integration pattern for OpenClaw + BrowserPilot.

What stack are you currently using for your agentic CLI (e.g., MCP servers, LangGraph, custom Node/Python router), and do you want the browser automation to be 100% local or is a hosted component acceptable?
