---
title: "Chrome ACP + Grok Build: driving agentic CLIs from the browser — architecture, security, and safe implementation"
created: 2026-07-29
source: session-2026-07-29
tags: [acp, agent-client-protocol, chrome-acp, grok-build, browser-automation, security, prompt-injection, agentic-cli, multi-agent, host-invariants]
summary: >
  How to drive Grok Build (and other agentic CLIs) from a browser front-end using ACP
  (Agent Client Protocol), the security risks of browser-driven agents, what works/breaks
  in practice, and the safe implementation pattern for this host's multi-terminal fleet.
  ACP is a real, vendor-backed standard (Zed + JetBrains) with stable 1.0 SDKs, but
  Chrome ACP specifically is a low-adoption hobby project with an open Windows crash bug.
  The dominant risk is indirect prompt injection + full-session exposure via browser_execute.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
relations:
  - target: wiki/concepts/mcp-server-sharing-multi-terminal.md
    type: related
    reciprocal: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
    reciprocal: related
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: supports
  - target: wiki/concepts/multi-model-ai-workflow-patterns.md
    type: refines
  - target: wiki/concepts/ai-cli-tools-and-coding-agents.md
    type: refines
---

## Summary

The operator wants consumer-web LLMs (ChatGPT, Claude, Perplexity) and a browser front-end
to drive Grok Build and other local agentic CLIs in a two-way loop: the web side provides
thinking/research/guidance, the CLI implements/reviews. This page documents the viable
architectures, the security risks (which are severe and well-documented), what works and
breaks in practice, and the safe implementation for this host.

## Decision context

**The problem:** how to let browser-based AI interfaces (consumer chatbot subscriptions OR
a generic ACP client) drive Grok Build and other agentic CLIs on this Windows 11 host, with
two-way communication, using existing subscriptions (not API spend).

**What alternatives were explored:**
1. Custom HTTP broker (rejected — reinvents what ACP already standardizes)
2. Native vendor Remote Control (Claude Remote Control, ChatGPT Remote Connections — verified
   real but only drives same-vendor agents, not Grok Build)
3. ACP as the protocol layer (chosen — Grok Build ships `grok agent serve` natively, ACP
   SDKs reached 1.0, registry lists 30+ agents)
4. Browser extensions that bridge DOM↔agent (Chrome ACP, Multi-LLM Web Orchestrator — evaluated
   for the browser-side of the loop)

**What the research changed:** initially assumed a custom broker was needed. Research proved
ACP is the standardized protocol that makes this turnkey: Grok Build speaks it natively, ACP UI
is a mature client, and Chrome ACP bridges the browser↔agent gap. The security research then
surfaced that browser-driven agents are a high-risk surface (prompt injection, session exposure)
that requires deliberate mitigations — this flipped the framing from "how to build it" to
"whether the browser path is worth the risk vs ACP UI desktop." This connects to
[[mcp-server-sharing-multi-terminal]] (the transport-architecture decision for fleet agents)
and [[multi-model-ai-workflow-patterns]] (the broader pattern of composing multiple models).

---

## ACP maturity [HIGH confidence — ≥3 sources, disconfirmation-qualified]

The Agent Client Protocol is a real, vendor-backed standard, not a toy:

- **Backed by Zed + JetBrains.** Lead Maintainer Sergey Ignatov (JetBrains) joined Feb 2026.
  A Transports Working Group (JetBrains + Block/Goose) is standardizing WebSocket/HTTP.
- **SDKs reached 1.0.0** (Rust + TypeScript) on June 25, 2026 — stable foundations.
- **ACP v2 is in Draft** (July 20, 2026); v1 is stabilized through 20+ completed RFDs
  (elicitation, cancellation, session resume/close/delete, logout, workspace roots, etc.).
- **Registry released March 2026** with 30+ agents: Claude, Codex, Grok Build, Gemini, GLM,
  OpenCode, Copilot, Cursor, Cline, Qwen, and more.
- ⚠️ **Qualifier:** the ACP repo README states "Consumers should not infer wire compatibility
  from the crate or schema release version alone." Expect breaking changes between versions.
  Build for the protocol, not a frozen version.

Sources: agentclientprotocol.com/updates (fetched 2026-07-29), zylos.ai/research,
swarmsignal.net, mcphubz.com

---

## Grok Build as an ACP server [HIGH — verified from own runtime docs + CLI]

Grok Build ships three agent-mode transports, all speaking ACP/JSON-RPC:

| Command | Transport | Use case |
|---------|-----------|----------|
| `grok agent serve --bind 127.0.0.1:2419 --secret <token>` | WebSocket server | Browser/remote clients connect over WS |
| `grok agent stdio` | stdin/stdout JSON-RPC | Local bridges, IDE extensions |
| `grok agent headless --grok-ws-url wss://relay/ws` | WebSocket relay | Internet access via self-hosted relay |

Key flags: `--always-approve` (no interactive prompts), `--model grok-build`, `--agent-profile`.

**x.ai/* extension methods** (filesystem, git, terminal, search, session mgmt) are non-standard.
ACP clients like ACP UI or Chrome ACP handle the base protocol (sessions, prompts, streaming,
tool calls) but may not surface x.ai/* extensions. The core loop works; advanced IDE features may not.

**Grok Build is NOT in ACP UI's default agent list** (checked: defaults include Claude Code,
Codex, Copilot, Gemini, Qwen, Auggie, OpenCode, OpenClaw, Kiro, Hermes — but not Grok).
Adding it requires a custom agents.json entry pointing at `grok agent serve` or `grok agent stdio`.

Sources: `grok agent --help` (run 2026-07-29), `15-agent-mode.md`, `14-headless-mode.md`

---

## Chrome ACP [MEDIUM confidence — single source, limited adoption, known Windows bug]

[Areo-Joe/chrome-acp](https://github.com/Areo-Joe/chrome-acp) — a Chrome extension + proxy
server that bridges the browser to any ACP agent.

**Architecture:**
```
Chrome Extension ↔ Proxy Server (WS, localhost:9315) ↔ ACP Agent (stdio)
```

**Browser tools exposed to the agent:**
- `browser_tabs` — list all open tabs (id, url, title, active status)
- `browser_read` — read DOM content of any tab as simplified Markdown
- `browser_execute` — execute arbitrary JavaScript in any tab's page context

**Maintenance health:**
- 174 stars, last push 2026-04-09 (~3.5 months ago), last release v1.0.40 (2026-03-09)
- Issue #11 OPEN: "Crashes on Windows" (bug, help wanted, good first issue) — **directly relevant to this host**
- Supports: Claude Code, Codex, Gemini CLI, OpenCode, Qwen, Augment, "any ACP-compatible agent"

⚠️ **Not verified:** no practitioner report exists of Chrome ACP working with Grok Build
specifically. The Windows crash bug (#11) may block this host entirely. Test before building on it.

---

## Browser agent security — the dominant risk [HIGH — ≥6 sources, strong academic + industry consensus]

This is the most critical section. Browser-driven agents are a well-studied high-risk surface.

### The six attack vectors (per OWASP LLM Top 10 + Witness AI + Palo Alto Unit42)

1. **Indirect prompt injection** (OWASP LLM01:2025): attacker embeds instructions in web
   content the agent reads → agent executes them with user's credentials. "The attacker never
   touches the prompt interface — instructions are smuggled in through untrusted external
   content" (Brave Security). Documented by Palo Alto Unit42 (Mar 2026) as observed in the wild.

2. **Full authenticated-session exposure**: browser agents inherit ALL authenticated sessions
   across ALL tabs simultaneously. An agent tasked with one app can act across every connected
   system (email, banking, CRM, code repos). "Granting an AI browser agent access to a browser
   delegates much of an employee's digital identity" (Witness AI).

3. **Same-Origin Policy breakdown**: academic research confirms SOP — the internet's fundamental
   security boundary — breaks when an AI agent controls the browser. An agent can observe content
   in one tab and reproduce/act on it in another tab/domain (arXiv:2505.13076).

4. **Documented real-world attacks**: SquareX demoed an agent that entered credentials on a
   phishing site impersonating Salesforce. Another agent fell prey to an OAuth attack granting
   full Google Drive access. Browser Use CVE-2025-47241 (CVSS 9.3) confirmed.

5. **Hidden text / invisible characters**: attackers embed prompt injections in invisible text,
   HTML comments, or multimodal inputs (images) that humans don't see but agents execute.

6. **Cross-application authority**: a browser AI agent completing inbox tasks propagated a
   malicious link to a colleague via calendar invite — crossed app boundaries, violated user intent.

### What this means for the ChatGPT/Claude → Grok Build loop

The specific risk for the operator's use case: if Grok Build reads a ChatGPT/Claude/Perplexity
tab via `browser_read`, and that tab contains content injected by a malicious source (e.g., a
web search result with hidden instructions), Grok executes those instructions with full local
filesystem + tool access. The chatbot tab is the injection vector; the local CLI is the blast radius.

### Mitigations (ranked by effectiveness for this host)

| Mitigation | What it prevents | Effort |
|-----------|-----------------|--------|
| **Separate Chrome profile for agent use** | Cross-contamination with daily browsing, banking, etc. | Low — create a dedicated profile |
| **Read-only mode (browser_read only, no browser_execute)** | Arbitrary JS execution in logged-in tabs | Low — don't enable execute unless needed |
| **Human-in-the-loop approval** | Unreviewed agent actions | Built into ACP (don't use --always-approve for browser tasks) |
| **Scope browser_tabs to specific tab IDs** | Agent reading arbitrary tabs | Medium — extension-level allowlist |
| **No logged-in sensitive accounts in the agent profile** | Session/token theft blast radius | Low — separate profile achieves this |
| **Audit trail (log all browser_read/execute calls)** | Post-incident forensics | Medium — proxy-level logging |

Sources: witness.ai/blog/ai-browser-agent-security-risks (Jul 2026), arxiv.org/html/2505.13076v1,
unit42.paloaltonetworks.com/ai-agent-prompt-injection (Mar 2026), imperva.com, OWASP LLM Top 10,
Microsoft AI Red Team failure taxonomy (Jun 2026)

---

## What people like [PRACTITIONER signal]

- **ACP ecosystem growing fast.** 5+ ACP-based projects on HN (agent-team, VT Code, Toad,
  Forge, Rowboat at 219pts). The "one client, many agents" pattern is the emerging sweet spot.
- **ACP UI praised for cross-platform** (desktop + mobile + web) and multi-agent switching.
- **Browser-automation agents are a validated category** — Browser Use raised $17M; demand is real.
- **The proxy pattern (Chrome ACP, stdio-to-ws) is clean** — keeps the agent local, browser as
  thin client, no credentials leave the machine.

## What people don't like [PRACTITIONER signal]

- **DOM-automation brittleness**: selector drift, provider anti-automation, SPA soft-navigations.
  The Multi-LLM Web Orchestrator author's own words: "Browser-UI automation is inherently brittle.
  Providers change DOM structure frequently."
- **ACP wire-format instability**: "should not infer wire compatibility from version alone."
- **Chrome ACP Windows crashes** (issue #11, still open).
- **Remote ACP setup friction**: Auth headers, wss:// requirements, tunnel configuration,
  mixed-content rules (HTTPS pages can't open ws://).
- **ACP UI tool-call rendering bugs** (issue #9).

---

## Safe implementation for this host

### Recommended architecture (lowest risk → highest risk)

**Tier 0 — ACP UI Desktop + Grok Build (safest, recommended first):**
```
ACP UI Desktop → grok agent stdio (local subprocess)
```
No browser exposure, no tunnel, no prompt-injection surface. Configure in agents.json:
```json
"Grok Build": { "command": "grok", "args": ["agent", "--always-approve", "stdio"], "env": {} }
```
This is the turnkey path. Proven transport (stdio), proven client (ACP UI, 424 stars, actively
maintained), native Grok subscription.

**Tier 1 — ACP UI Web + Grok serve + tunnel (browser access, moderate risk):**
```
ACP UI Web (acp-ui.github.io) → wss://<devtunnel> → grok agent serve (localhost:2419)
```
No browser_execute — the browser is just a chat UI, not a DOM controller. The risk is the
tunnel exposure, not prompt injection. Use a strong secret token.

**Tier 2 — Chrome ACP + Grok Build (full browser control, highest risk, highest capability):**
```
Chrome Extension → Proxy Server (localhost:9315) → grok agent stdio
```
This gives Grok `browser_read`/`browser_execute` on your logged-in tabs. Only use if you
specifically need Grok to read/interact with chatbot web pages. **Mandatory mitigations:**
separate Chrome profile, read-only where possible, no --always-approve, audit logging.

### Host invariant check (Round 3.5)

| Invariant | Violation risk | Safe alternative |
|-----------|---------------|-----------------|
| **Multi-terminal cookie/CDP isolation** ([[concurrent-cdp-auth-contention]]) | Chrome ACP content scripts read logged-in tabs. If multiple fleet terminals drive the same Chrome profile, auth sessions can invalidate (same pattern as `--cookies-from-browser` parallel access). | ONE designated terminal drives Chrome ACP at a time. Others use Tier 0 (ACP UI desktop, no browser access). |
| **Singleton proxy** | Chrome ACP's proxy server (localhost:9315) is a single process. Multiple agents can't share it concurrently. | One proxy instance per Chrome profile, or serialize access. |
| **No cookies-from-browser in parallel** | Chrome ACP's browser_read effectively reads browser session state. Same invariant. | Same mitigation: designated terminal only. |

Host invariant check: **2 violations identified and mitigated.** The concurrent-CDP invariant
from [[concurrent-cdp-auth-contention]] directly applies — Chrome ACP's browser access is the
same failure class as `--cookies-from-browser chrome` in parallel. This is exactly the Mode 2
(context blindness) pattern from [[invariants-beat-environment-comfort]]: the generic best
practice (let the agent read your browser) is unsafe for this fleet without the designated-terminal
mitigation.

---

## How to make the system better

1. **Add Grok Build to ACP UI's default agents.** Currently absent from the defaults; adding
   a `Grok Build` entry to ACP UI's agents.json is the single highest-leverage improvement.
   Upstream it to formulahendry/acp-ui.

2. **Fix Chrome ACP issue #11 (Windows crash).** This blocks the entire Tier 2 path on this
   host. If the operator wants browser-driven Grok, this bug needs fixing or forking.

3. **Build a Grok worker adapter for claude-chatgpt-agent-bridge.** The bridge (jcharveyjr)
   already has Claude Code and Codex workers with `delegate_task`/`get_task` MCP tools. Grok
   speaks ACP natively — adding a Grok worker is trivial and enables cross-vendor delegation
   (GPT delegates to Grok, Grok implements).

4. **Add prompt-injection guardrails to the proxy.** Chrome ACP's proxy server is the natural
   choke point for filtering browser_read content before it reaches the agent. A content-script
   that strips hidden text / HTML comments / known injection patterns would mitigate the #1 risk.

5. **Use Perplexity as an MCP tool inside an agent, not as a peer.** Perplexity has no ACP agent
   and its subscription is web-only. But `perplexity-web-mcp` (already installed on this host)
   can be configured as an MCP server inside the Grok or Codex ACP agent — giving it Perplexity
   research as a tool without needing Perplexity to speak ACP.

---

## Falsifier

This concept is wrong if:
- ACP fails to gain traction and is superseded by MCP or A2A for agent-to-client communication
  (watch: if JetBrains or Zed drops ACP support, or if the registry stops growing)
- Chrome ACP's Windows crash bug proves unfixable and no fork emerges (watch: issue #11 resolution)
- Browser-agent security mitigations prove insufficient and a major incident causes vendors to
  restrict browser-automation access entirely (watch: Chrome/Edge policy changes restricting
  content-script injection)
- Grok Build drops `agent serve`/`stdio` mode (watch: grok agent --help in future versions)

---

## Sources

- ACP updates: https://agentclientprotocol.com/updates (fetched 2026-07-29)
- ACP registry: https://agentclientprotocol.com/get-started/registry (fetched 2026-07-29)
- Chrome ACP: https://github.com/Areo-Joe/chrome-acp (issues, README fetched 2026-07-29)
- ACP UI: https://github.com/formulahendry/acp-ui (README fetched 2026-07-29)
- Witness AI browser agent security: https://witness.ai/blog/ai-browser-agent-security-risks/ (Jul 2026)
- arXiv Browser Use analysis: https://arxiv.org/html/2505.13076v1 (May 2025)
- Palo Alto Unit42 prompt injection: https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/ (Mar 2026)
- Multi-LLM Web Orchestrator: https://github.com/paritoshv/multi-llm-web-orchestrator
- Claude-ChatGPT Agent Bridge: https://github.com/jcharveyjr/claude-chatgpt-agent-bridge
- Grok Build agent mode docs: ~/.grok/docs/user-guide/15-agent-mode.md
- HN signal: agent-team, VT Code, Toad, Forge, Rowboat (219pts), ContextFort (14pts)
