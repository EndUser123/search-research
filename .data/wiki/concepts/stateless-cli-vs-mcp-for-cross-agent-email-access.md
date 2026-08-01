---
title: "Stateless CLI vs MCP for Cross-Agent Email Access"
slug: stateless-cli-vs-mcp-for-cross-agent-email-access
created: 2026-07-28
category: decision
tags: [email, cli, mcp, multi-agent, cross-runtime, stateless, himalaya, ortie, architecture, fleet, grok-build, claude-code, codex, opencode]
summary: >
  Architecture decision: for a multi-agent fleet where Claude Code, Codex,
  Grok Build, OpenCode, and Pi all need email access, a stateless CLI tool
  (e.g. himalaya + ortie) is the correct substrate, not MCP servers. MCP
  servers are tied to each runtime's MCP client implementation (separate
  config, version skew, registration per platform); a CLI binary on PATH
  is universally available to any agent with shell access. The CLI pattern
  matches the fleet's existing tool substrate (nlm, yt-dlp, mmx) and is
  60-90% cheaper on token cost than MCP schemas. TTL cache + file lock
  handles concurrent access safely; a wrapper script (email-skill
  scan-inbox --json) provides the scoped operation contract.
cognitive_load: 3
verification: multi-source-verified
agent: grok
host: both
sources:
  - "Composio — Best MCP servers for Claude Code and Codex 2026 — https://composio.dev/content/best-mcp-servers-claude-code-codex (MCP vs CLI decision framework)"
  - "Pimalaya/himalaya — https://github.com/pimalaya/himalaya (stateless CLI design, JSON output, multi-account)"
  - "Pimalaya/ortie — https://github.com/pimalaya/ortie (OAuth2 token helper for himalaya)"
  - "Hermes Agent himalaya skill — https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/email/email-himalaya (agent-platform integration pattern)"
  - "LobsterMail — himalaya OAuth2 full setup guide — https://lobstermail.ai/blog/himalaya-oauth2-the-full-setup-guide-and-why-agents-can-t-use-it (browser auth limitation + refresh token persistence)"
  - "MindStudio — CLI vs MCP vs API for AI Agents — https://www.mindstudio.ai/blog/cli-vs-mcp-vs-api-ai-agents (token cost comparison)"
  - "Aembit — MCP or CLI how to choose — https://aembit.io/blog/mcp-or-cli-how-to-choose-right-interface-for-your-ai-tools/ (shared state advantage of MCP)"
  - "jannikreinhard.com — CLI Tools vs MCP — https://jannikreinhard.com/why-cli-tools-are-beating-mcp-for-ai-agents/ (33% efficiency advantage benchmark)"
  - "AWS CLI Agent Orchestrator — https://aws.amazon.com/blogs/opensource/introducing-cli-agent-orchestrator-transforming-developer-cli-tools-into-a-multi-agent-powerhouse/ (fleet-scale shared-CLI pattern)"
  - "Nango — concurrency with OAuth token refreshes — https://nango.dev/blog/concurrency-with-oauth-token-refreshes/ (file-locking pattern for multi-process token refresh)"
relations:
  - target: wiki/concepts/mcp-servers-for-email-social-unified-task-scanning.md
    type: supersedes
  - target: wiki/concepts/adhd-friendly-unified-todo-workspace-email-scanning.md
    type: refines
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
  - target: wiki/concepts/dynamic-wiki-driven-skill-configuration.md
    type: related
---

# Stateless CLI vs MCP for Cross-Agent Email Access

## Decision context

**The problem:** the operator runs a fleet of AI coding agents across 5
different runtimes (Claude Code, Codex, Grok Build, OpenCode, Pi). The
`/todo` skill needs to scan 3 email accounts (2 Gmail + 1 Hotmail) to
produce a unified "what should I do?" action list. The question: what is
the right substrate for email access that works from *every* agent
runtime, not just one?

**What the research found:** MCP servers are portable across runtimes in
theory but fragmented in practice — each runtime has its own MCP client
implementation (`~/.claude/settings.json` for Claude Code,
`~/.codex/config.toml` for Codex, `opencode.json` for OpenCode), its own
config format, its own version skew issues, and its own registration
process. A stateless CLI binary on `PATH` is universally available to any
agent with shell access — no registration, no MCP client, no version
tracking. This matches the fleet's existing tool substrate pattern (nlm,
yt-dlp, mmx, agy, codex CLIs) and is 60-90% cheaper on token cost.

**What this decision changes:** `/todo` calls `email-skill scan-inbox
--json` (a thin wrapper around `himalaya envelope list --output json`)
instead of calling MCP email tools. Every agent runtime can invoke this
the same way. The MCP email servers surveyed in
[[mcp-servers-for-email-social-unified-task-scanning]] remain useful for
the social side (Reddit, HN) which is Grok-Build-specific, but for email
the CLI is the cross-agent path.

## The core argument

### Why CLI, not MCP

| Factor | Stateless CLI | MCP Server |
|--------|--------------|------------|
| **Agent runtime support** | Any agent with shell access (all 5 runtimes) | Per-runtime MCP client (fragmented config) |
| **Token cost** | ~0 at session start (invoked on demand) | 20k-150k tokens schema loaded per session |
| **Registration** | Binary on PATH — done | Per-runtime config file + auth flow |
| **State** | Stateless per invocation; state in files | In-memory, persistent process |
| **Auth** | OAuth via ortie (file-based tokens, shared) | Per-runtime OAuth (runtime-managed) |
| **Concurrent access** | File lock + TTL cache | In-process coordination (if same server) |
| **Composability** | Shell pipes, jq, scripts | Tool-call API |
| **Security scoping** | Wrapper script limits operations | Tool schema constrains operations |
| **Debuggability** | Run the command yourself, see the output | Must go through MCP client |

**The decisive factor is not any single row — it is the combination.**
CLI is the only substrate that works identically across all 5 agent
runtimes without per-runtime configuration, registration, or MCP client
version tracking. The operator already has 5+ stateless CLIs in the fleet
(nlm, yt-dlp, mmx, agy, codex); adding one more (himalaya/ortie or a
wrapper) follows the established pattern.

### The token cost difference is significant

MCP servers load their full tool schema into the agent's context at
session start. For email MCP servers, this is 20k-150k tokens of tool
definitions the agent carries for the entire session, even if email is
never accessed. A CLI invocation costs zero tokens until the moment it
runs, and the output (JSON) is the only thing that enters context.

Sources: MindStudio benchmarks (60-90% cheaper), jannikreinhard.com
(33% efficiency advantage, CLI scored 202 vs MCP's 152), composio.dev
("MCP still makes sense when the service lacks a good CLI").

### The shared-state counterargument (qualified)

The strongest argument FOR MCP is shared state: an MCP server maintains
a persistent connection pool, session affinity, and in-memory state that
multiple agents can share. A stateless CLI has none of this.

**Why this doesn't apply here:** the shared state that matters for email
scanning is the TTL cache (scan results) and the OAuth refresh token
(auth state). Both of these are files, not in-memory state. The file
lock + TTL cache pattern from
[[adhd-friendly-unified-todo-workspace-email-scanning]] handles concurrent
access safely — only one agent scans at a time; others read the cache.

The one case where MCP's shared state wins is **IMAP connection pooling**
— a persistent MCP server can reuse a single IMAP connection across
calls, while a stateless CLI opens a new connection per invocation.
Provider IMAP connection limits (Gmail: 15 concurrent, Outlook: similar)
could be hit if N agents scan simultaneously. The TTL cache (15-min
default) means scans are rare and serialized by the file lock, making
this a non-issue in practice.

## The concrete implementation

### Layer 1: himalaya CLI (the backend)

[Himalaya](https://github.com/pimalaya/himalaya) is a Rust CLI email
client that is explicitly stateless by design: *"There is no event loop:
you interact with your emails using shell commands, in a stateless way."*

Key properties:
- Multi-account via TOML config (`~/.config/himalaya/config.toml`)
- JSON output via `--output json` (wrapped object `{"envelopes": [...]}`)
- OAuth2 support for Gmail and Outlook
- IMAP, SMTP, JMAP, Gmail REST, Microsoft Graph backends
- Pre-built binaries for Windows (Scoop, cargo, or direct download)

### Layer 2: ortie (the OAuth token helper)

[Ortie](https://github.com/pimalaya/ortie) is Pimalaya's OAuth2 token
manager, designed to work with himalaya. It handles:
- Authorization code + device code grants
- PKCE (required for Microsoft)
- Auto-refresh of expired access tokens
- Persistent REPL session (`ortie repl`) so multiple CLI invocations
  share one unlocked auth session

Wired into himalaya config:
```toml
backend.auth.type = "oauth2"
backend.auth.token.command = ["ortie", "token", "show", "-a", "gmail"]
```

This is the key to headless/multi-agent use: ortie holds the OAuth state
in a persistent process, and himalaya (stateless) calls ortie to get the
current token on each invocation. Multiple agents calling himalaya all
share the same ortie-managed token.

### Layer 3: email-skill wrapper (the scoped contract)

A thin wrapper script that normalizes himalaya output into the `/todo`
email-scan contract:

```
email-skill scan-inbox --json [--account <name>] [--max <N>]
email-skill read-message <id> --json
email-skill search <query> --json
email-skill defer <thread-id> --hours <N>
email-skill ignore <thread-id> --reason "<text>"
```

The wrapper:
1. Checks the TTL cache (`P:/.data/email-scan/cache.json`)
2. If fresh: returns cached results
3. If stale: acquires file lock, calls `himalaya envelope list --output json`
   for each account, applies scoring, writes cache, releases lock
4. Returns normalized JSON

This wrapper is what every agent calls — not raw himalaya. It provides
the scoped operation contract that addresses the "CLI gives full shell"
security concern (disconfirmation finding).

### Layer 4: /todo orchestrator (the consumer)

`/todo` Step 2 calls `email-skill scan-inbox --json` and merges results
with the workspace scan (Step 1). The TTL cache + deferral state lives
in `P:/.data/email-scan/` — shared across terminals, per the existing
[[adhd-friendly-unified-todo-workspace-email-scanning]] design.

## What about agents that DON'T have shell access?

Some agent runtimes (Claude Desktop, ChatGPT) don't have shell access
and can only use MCP tools. For those, the CLI pattern doesn't work
directly.

**Resolution:** this is not our constraint. All 5 runtimes in the fleet
(Claude Code, Codex, Grok Build, OpenCode, Pi) have shell access. If a
future runtime lacks shell access, the wrapper can be exposed as an MCP
server (`nylas mcp install` pattern — same binary, two transports). This
is the hybrid approach documented by composio.dev: CLI as source of
truth, MCP as optional thin wrapper.

## The pattern in the fleet's existing substrate

| CLI tool | What it does | Who calls it |
|----------|-------------|-------------|
| `nlm` | NotebookLM API access | Grok Build, Claude Code, Codex |
| `yt-dlp` | YouTube transcript/download | Grok Build, Claude Code |
| `mmx` | MiniMax cross-model second opinion | Grok Build |
| `agy` | Antigravity/Gemini cross-model | Grok Build |
| `codex` | OpenAI Codex CLI | Grok Build |
| **`himalaya` + `email-skill`** | **Email access** | **All 5 runtimes** |

The stateless CLI pattern is not novel for this fleet — it is the
established way tools are shared across agent runtimes. Email is just
the latest tool to join the substrate.

## Disconfirmation results

Three concerns surfaced during disconfirmation research:

1. **MCP handles shared state better (aembit.io)** — QUALIFIED. For
   connection pooling and in-memory session state, yes. But the shared
   state that matters for email scanning (TTL cache, OAuth tokens) is
   file-based and handled by the existing file-lock pattern.

2. **CLI gives full shell access, less constrained than MCP (Reddit)** —
   CONFIRMED as a real concern. Addressed by the wrapper script
   (`email-skill scan-inbox`) that scopes operations to safe subsets.
   Agents never call raw `himalaya` with arbitrary arguments.

3. **IMAP concurrent connection limits (Zoho/Gmail)** — CONFIRMED as a
   limitation. Each `himalaya` invocation opens a new IMAP connection.
   Addressed by the TTL cache (15-min default) + file lock — only one
   agent scans at a time; most invocations read the cache without
   connecting.

**No conclusions refuted.** All three concerns are addressed by the
existing design (TTL cache, file lock, wrapper contract).

## Receipts

- **Himalaya stateless design claim** — Source: [github.com/pimalaya/himalaya](https://github.com/pimalaya/himalaya) README: *"There is no event loop: you interact with your emails using shell commands, in a stateless way."* Verified via web_fetch 2026-07-28.
- **Himalaya JSON output format** — Source: [Arch man page](https://man.archlinux.org/man/himalaya.1.en): `--json` flag "Enable JSON output. When set, command output (data or errors) is displayed as JSON string." Hermes Agent docs confirm `--output json` usage pattern.
- **Ortie OAuth token helper** — Source: [github.com/pimalaya/ortie](https://github.com/pimalaya/ortie) README. Research subagent (task 019faa37) confirmed: handles auth-code + device-code grants, PKCE, auto-refresh, persistent REPL session. [INFERENCE]: the `token.command` config wiring pattern is documented but not tested on Windows yet.
- **Token cost comparison (60-90% cheaper)** — Source: MindStudio blog [cli-vs-mcp-vs-api-ai-agents](https://www.mindstudio.ai/blog/cli-vs-mcp-vs-api-ai-agents). Research subagent (task 019faa37) cited this benchmark.
- **CLI 33% efficiency advantage** — Source: jannikreinhard.com, "CLI scored 202 vs MCP's 152." Research subagent (task 019faa37).
- **MCP cross-runtime portability (composio article)** — Source: [composio.dev](https://composio.dev/content/best-mcp-servers-claude-code-codex) — documents separate MCP config for Claude Code (`claude mcp add`) vs Codex (`~/.codex/config.toml`). Fetched directly 2026-07-28.
- **Hermes Agent himalaya integration** — Source: [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/email/email-himalaya) — shows a production agent platform using himalaya as a bundled skill with `--output json`. Fetched directly 2026-07-28.
- **AWS CLI Agent Orchestrator (fleet-scale shared-CLI pattern)** — Source: research subagent (task 019faa37-5813) cited [aws.amazon.com/blogs/opensource](https://aws.amazon.com/blogs/opensource/introducing-cli-agent-orchestrator-transforming-developer-cli-tools-into-a-multi-agent-powerhouse/).
- **File-locking for multi-process OAuth refresh** — Source: research subagent (task 019faa37-5813) cited [nango.dev/blog/concurrency-with-oauth-token-refreshes](https://nango.dev/blog/concurrency-with-oauth-token-refreshes/). [INFERENCE]: the lockfile + re-read + atomic-rename pattern is the standard solution but has not been tested in our specific email-scan implementation yet.
- **LobsterMail OAuth agent limitation** — Source: [lobstermail.ai](https://lobstermail.ai/blog/himalaya-oauth2-the-full-setup-guide-and-why-agents-can-t-use-it) — documents the browser-redirect limitation for headless agents and the refresh-token-persistence workaround. Fetched directly 2026-07-28 (prior turn).
- **Existing fleet CLI substrate** — Source: workspace skills list (session system-reminder): nlm, yt-dlp, mmx, agy, codex CLIs all documented as stateless command-line tools invoked from multiple agent runtimes.

## Falsifier

This decision is wrong if:
- Himalaya's OAuth2 flow proves too fragile for Windows (keyring issues,
  PKCE failures, token refresh bugs specific to the platform)
- The ortie helper doesn't work reliably on Windows or doesn't support
  the 3 account types needed (2 Gmail + 1 Hotmail)
- IMAP connection limits are hit despite the TTL cache (would need to
  investigate connection pooling or Graph API instead of IMAP)
- A future agent runtime in the fleet lacks shell access AND cannot use
  an MCP wrapper (extremely unlikely given current trajectories)
- The operator finds that maintaining the himalaya config + ortie + wrapper
  script is more maintenance burden than maintaining per-runtime MCP
  configs would have been

## Decision context (why this research was needed)

The operator discovered that MCP email servers are Grok-Build-specific
(each runtime has its own MCP client), while the fleet needs email access
from 5 different runtimes. The prior wiki concept
([[mcp-servers-for-email-social-unified-task-scanning]]) recommended MCP
servers as the primary approach, which is correct for Grok Build alone
but wrong for the cross-agent fleet. This concept supersedes that
recommendation for the email use case specifically.

The research hole was useful because it explored three paths:
1. **Pure MCP** (codefuturist/email-mcp) — works for Grok Build only
2. **Direct provider APIs** (Gmail API + MS Graph) — cross-agent but
   requires building auth, token refresh, and JSON serialization twice
3. **Stateless CLI** (himalaya + ortie) — cross-agent, zero custom auth
   code, matches existing fleet substrate

Path 3 won because it is the only one that works from all 5 runtimes
without per-runtime configuration and follows the established pattern.

## Related

- [[mcp-servers-for-email-social-unified-task-scanning]] — SUPERSEDED for
  email; still valid for social (Reddit, HN) which is Grok-Build-specific
- [[adhd-friendly-unified-todo-workspace-email-scanning]] — the /todo
  design this enables; the TTL cache + file lock + deferral pattern
- [[concurrent-cdp-auth-contention]] — same multi-terminal auth isolation
  pattern; ortie's persistent REPL session is the email equivalent of
  the CDP session singleton
- [[invariants-beat-environment-comfort]] — this decision follows the
  invariant (multi-terminal isolation) over the comfortable default
  (just install the MCP server)
- [[dynamic-wiki-driven-skill-configuration]] — same "shared plugin,
  per-session consumer" pattern
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
