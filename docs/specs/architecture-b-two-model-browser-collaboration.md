# SPEC: Two-Model Browser-Mediated Collaboration (Architecture B)

**Status:** Draft — pending operator review
**Created:** 2026-07-31
**Supersedes:** chrome-acp extension-patching strategy (P:\packages\chrome-acp\SPEC.md)
**Related:** [[chrome-acp-grok-build-browser-driven-agentic-clis]], [[chrome-acp-library-stack-and-best-practices-2026]], [[concurrent-cdp-auth-contention]]

---

## 1. Goal

Replace the chrome-acp extension-patching strategy with a decoupled architecture where:

1. **A web-based model** (ChatGPT, Claude, Perplexity — accessed via browser subscription) does research, answers questions, and provides **direction**.
2. **A local model** (Grok Build — via ACP) does research, answers questions, and **implements directions**.
3. **Both models talk to each other** through a browser-mediated collaboration loop — the web model provides direction, the local model implements and reports back.
4. **The operator** monitors and intervenes at checkpoints, not as a manual relay.

This replaces the current approach of patching a stale Chrome extension with IIFE injections.

---

## 2. Why Architecture B (decoupled)

The current chrome-acp approach couples two concerns into one brittle extension:
- **Chat UI** (the side panel)
- **Browser access** (`browser_read`/`browser_execute` content scripts)

Architecture B decouples them:
- **Chat UI** → use a mature ACP client (Codeg) that already supports Grok Build
- **Browser access** → use Chrome DevTools MCP (already installed) as explicit agent tool calls
- **Cross-model collaboration** → the Grok agent itself orchestrates the loop, using browser tools to read from and write to the web model's chat interface

This eliminates: extension patching, minified-bundle IIFE injection, proxy server maintenance, and the upstream dependency on a stale 177-star project.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (Chrome)                              │
│                                                                      │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐    │
│  │  Web Model Chat      │    │  Chrome DevTools MCP (29 tools)  │    │
│  │  (ChatGPT/Claude/    │←──→│  • list_pages                    │    │
│  │   Perplexity tab)    │    │  • execute_script                │    │
│  │                      │    │  • take_snapshot                 │    │
│  │  DOM = communication │    │  • navigate_page                 │    │
│  │  channel             │    │  • etc.                          │    │
│  └─────────────────────┘    └──────────┬───────────────────────┘    │
│                                        │ CDP (port 9222)             │
└────────────────────────────────────────┼─────────────────────────────┘
                                         │
                          ┌──────────────▼──────────────┐
                          │   Grok Build Agent           │
                          │   (grok agent serve/stdio)   │
                          │                              │
                          │   • Reads web model output   │
                          │     via execute_script       │
                          │   • Sends messages to web    │
                          │     model via execute_script │
                          │   • Implements directions    │
                          │     using native tools       │
                          │   • Reports results back     │
                          └──────────────┬──────────────┘
                                         │ ACP (JSON-RPC)
                          ┌──────────────▼──────────────┐
                          │   Codeg (Chat UI)            │
                          │   • ACP client (2,484 stars) │
                          │   • Session management       │
                          │   • Tool-call rendering      │
                          │   • Operator monitors here   │
                          └─────────────────────────────┘
```

### Communication flow

The DOM of the web model's chat tab IS the communication channel:

1. **Operator** gives a high-level goal to Grok (via Codeg chat UI)
2. **Grok** reads the web model's latest response from the DOM (`execute_script` queries the chat message elements)
3. **Grok** types a message into the web model's input field (`execute_script` sets textarea value + dispatches submit)
4. **Web model** processes and responds (its normal operation — it doesn't know it's talking to an agent)
5. **Grok** polls for the web model's response (`take_snapshot` or `execute_script` to check for new messages)
6. **Grok** reads the direction, implements it using native tools (file ops, shell, git, wiki, etc.)
7. **Grok** sends results back to the web model (step 3 again)
8. **Loop** continues until the goal is achieved or the operator intervenes

---

## 4. Component selection (reuse where practical)

### 4.1 Chat UI: Codeg

**Repo:** [xintaofei/codeg](https://github.com/xintaofei/codeg) — 2,484 stars, pushed daily
**Why:** Most mature ACP client. Supports Grok Build natively. Desktop app, self-hosted server, or Docker. Session aggregation from multiple agents. Actively maintained.
**Reuse:** Deploy as-is. No fork needed. Configure Grok Build as an agent:
```json
{
  "name": "Grok Build",
  "command": "grok",
  "args": ["agent", "--always-approve", "stdio"],
  "env": {}
}
```
**Alternative:** ACP UI Desktop ([formulahendry/acp-ui](https://github.com/formulahendry/acp-ui), 424 stars) — simpler, cross-platform, but less feature-rich than Codeg.

### 4.2 Browser access: Chrome DevTools MCP

**Already installed** on this host (29 tools in the MCP server list).
**Why:** CDP-based, explicit tool calls (not ambient content scripts), already working.
**Key tools for collaboration:**
- `list_pages` — find the web model's tab
- `execute_script` — read DOM content + type into input fields
- `take_snapshot` — capture full page state for complex UIs
- `navigate_page` — navigate to web model URL if needed
**Reuse:** No fork needed. Already configured in Grok's MCP settings.

### 4.3 Cross-model collaboration protocol: new (prompt-based, not code)

The collaboration loop is **not a separate service** — it's a prompt/instructions file that tells the Grok agent how to use Chrome DevTools MCP for web-model communication. This is the only new artifact to create.

**Why not use claude-chatgpt-agent-bridge?** That bridge ([jcharveyjr/claude-chatgpt-agent-bridge](https://github.com/jcharveyjr/claude-chatgpt-agent-bridge)) connects two local CLI agents via MCP task delegation. It doesn't handle browser-mediated communication with web models. The pattern is inspiring but the implementation doesn't apply — web models can't be run as local CLI workers.

**Why not build a bridge service?** The Grok agent's native tool-calling loop already handles orchestration. Adding a separate bridge service would reinvent what the agent already does — call tools, process results, decide next action. The agent IS the orchestrator.

---

## 5. The collaboration protocol (the only new artifact)

A Grok agent-profile instructions file that defines:

### 5.1 Web model interface adapters

Per-provider selectors for reading messages and typing input:

| Provider | Read latest message | Type + send |
|----------|---|---|
| ChatGPT | `[data-message-author-role="assistant"]` last child | `textarea#prompt-textarea` + submit button |
| Claude | `[data-testid="final-response"]` or `.font-claude-message` last | `div[contenteditable]` ProseMirror editor |
| Perplexity | `.markdown` last in answer section | `textarea` composer |

These selectors drift — the adapter must be maintained per provider. This is the equivalent of chrome-acp's content scripts, but as MCP tool calls rather than injected code.

### 5.2 Collaboration loop protocol

```
STATE: idle → reading_direction → implementing → reporting → waiting_for_response → reading_direction → ...

TRANSITIONS:
  idle:                    operator gives goal → reading_direction
  reading_direction:       read web model's latest response → if new direction: implementing
                           if question for operator: ask operator (via Codeg chat)
  implementing:            use native tools to implement → reporting
  reporting:               type results summary into web model input → waiting_for_response
  waiting_for_response:    poll every 5s for new message → if new: reading_direction
                           if timeout (2 min): ask operator if web model is still thinking
```

### 5.3 Human checkpoints

The loop is NOT fully autonomous. Checkpoints where the operator must approve:
- Before sending the FIRST message to the web model (confirms the direction request is well-formed)
- Before sending implementation results that include file changes (confirms the results are accurate)
- When the web model requests sensitive actions (credentials, external API calls, payments)

---

## 6. Security considerations

### 6.1 Prompt injection (same as chrome-acp, unchanged)

The web model's responses are untrusted content. If a malicious source injects instructions into the web model's context (e.g., via a web search result the web model reads), those instructions could reach Grok via the DOM read.

**Mitigation:** Grok must treat web-model output as advisory direction, not executable commands. Implementation actions require operator checkpoint approval (§5.3). This is the same risk as chrome-acp's `browser_read` — the attack surface is identical, only the access mechanism changes (MCP tool call vs content script).

### 6.2 CSP stripping eliminated

Architecture B does NOT need the `declarativeNetRequest` CSP stripping that chrome-acp uses. Chrome DevTools MCP operates at the CDP level, which bypasses CSP entirely — no header modification needed. This eliminates the "CSP stripping is a known malicious-extension pattern" concern from the library-stack research.

### 6.3 Credential exposure

Chrome DevTools MCP can read any tab's DOM, including logged-in sessions. Same risk as chrome-acp's `browser_tabs`/`browser_read`. Same mitigation: designated terminal only, separate Chrome profile for sensitive accounts.

---

## 7. Host invariant compliance

| Invariant | Status | Mitigation |
|-----------|--------|------------|
| [[concurrent-cdp-auth-contention]] — one terminal drives CDP at a time | **Applies** — Chrome DevTools MCP uses CDP | One designated Grok session uses Chrome DevTools MCP. Other terminals use ACP without browser tools. |
| Singleton proxy eliminated | **Resolved** — no proxy server needed. Grok speaks ACP natively. | N/A — chrome-acp's localhost:9315 proxy is eliminated entirely. |
| No cookies-from-browser in parallel | **Applies** — CDP reads browser session state | Same mitigation: designated terminal only. |

---

## 8. Implementation plan

### Phase 1: Deploy Codeg as the chat UI (reuse, no fork)
1. Clone Codeg, configure Grok Build as an ACP agent
2. Verify `grok agent stdio` works through Codeg's session management
3. Verify tool-call rendering (Grok's tool calls display correctly)
4. **Acceptance:** operator can chat with Grok via Codeg, see streaming responses + tool calls

### Phase 2: Verify Chrome DevTools MCP collaboration primitives (no build)
1. Verify `execute_script` can read the web model's latest response from DOM
2. Verify `execute_script` can type into the web model's input field and submit
3. Verify `take_snapshot` captures the web model's response for complex UIs
4. **Acceptance:** Grok can read from and write to a ChatGPT/Claude/Perplexity tab via MCP tools

### Phase 3: Write the collaboration protocol (the only new artifact)
1. Create a Grok agent-profile instructions file with the web-model interface adapters (§5.1)
2. Define the collaboration loop state machine (§5.2)
3. Define human checkpoint rules (§5.3)
4. Test the full loop: operator gives goal → Grok reads direction from web model → Grok implements → Grok reports back → web model responds
5. **Acceptance:** a full collaboration cycle completes without manual relay

### Phase 4: Retire chrome-acp (cleanup)
1. Verify Architecture B covers all use cases chrome-acp served
2. Archive `P:\packages\chrome-acp\` (patches, IIFE, proxy config)
3. Update wiki concepts to mark chrome-acp approach as superseded
4. **Acceptance:** zero references to chrome-acp proxy or extension in active configs

---

## 9. What we're NOT building

- **No new proxy server** — Grok speaks ACP natively; Codeg connects directly
- **No new browser extension** — Chrome DevTools MCP replaces chrome-acp's content scripts
- **No bridge service** — the Grok agent IS the orchestrator via its tool-calling loop
- **No new framework** — Codeg is deployed as-is; Chrome DevTools MCP is already installed
- **No CSP stripping** — CDP bypasses CSP; no declarativeNetRequest rules needed

The only new artifact is the **collaboration protocol instructions file** (Phase 3).

---

## 10. Decision context

**Why this architecture over the alternatives:**

| Alternative | Why rejected |
|---|---|
| Keep chrome-acp (patch the extension) | Increasing maintenance cost, stale upstream, CSP-stripping security concern, 8 brittle IIFE patches |
| Architecture A (web client only, no browser access) | Doesn't meet requirement: both models need to talk to each other through the browser |
| Architecture C (fork chrome-acp, rebuild with WXT) | High effort, still maintains an extension + proxy; Architecture B eliminates both |
| Build a custom bridge service | Reinvents what the agent's tool-calling loop already does |

**What changed since the original chrome-acp research (2026-07-29):**
- ACP ecosystem exploded (80+ clients) — Codeg (2,484 stars) didn't exist or wasn't mature
- Chrome DevTools MCP became available on this host (29 tools, already working)
- The operator clarified the use case: it's not "agent reads browser" — it's "two models collaborate bidirectionally"
- chrome-acp upstream remained stale (issue #11 still open, no new releases)

---

## 11. Falsifier

This architecture is wrong if:
- Chrome DevTools MCP's `execute_script` proves unreliable for typing into web model input fields (React controlled inputs, ProseMirror editors, anti-bot detection)
- Codeg doesn't render Grok Build's tool calls well (untested with Grok specifically)
- The CDP-based approach hits the concurrent-cdp-auth-contention invariant too often in practice
- The web model detects automation and blocks typed input (anti-bot measures)
- The operator finds the MCP-tool-call approach too slow compared to chrome-acp's ambient content scripts

**Test before committing:** Phase 2 (verify collaboration primitives) must pass before proceeding to Phase 3.
