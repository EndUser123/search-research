---
title: "MCP server sharing in multi-terminal environments (Windows 11)"
created: 2026-07-21
source: session-2026-07-21
tags: [mcp, transport, stdio, streamable-http, sse, multi-terminal, windows-11, singleton, multiplexing, architecture, fleet]
summary: >
  Two MCP transports: stdio (process-per-client, spawned by Grok per session) and
  Streamable HTTP (one server, many clients over a URL). For this host's multi-terminal
  setup, stdio gives free isolation but duplicates processes and loses shared state
  (caching, health tracking). Streamable HTTP shares one process across all terminals
  with shared cache/health but needs a long-running daemon and port management. The
  optimal pattern per tool: stdio for stateless/light tools (filesystem, per-session
  isolation critical); Streamable HTTP for stateful/shared-cache tools (search, knowledge
  graph, expensive init). The Search MCP is the prime candidate for Streamable HTTP.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/web-search-tool-routing
    type: related
  - target: wiki/concepts/mcp-http-server-placeholder-resolution
    type: related
  - target: wiki/concepts/optimal-multi-backend-search-strategy
    type: related
---

# MCP server sharing in multi-terminal environments (Windows 11)

## The question

This host runs multiple Grok Build terminals simultaneously. Each terminal is a Grok
session with its own context, worktree, and state. **When should MCP servers be shared
across terminals vs isolated per-terminal?**

## The two transports (MCP spec 2025-11-25)

| Property | **stdio** | **Streamable HTTP** |
|----------|-----------|---------------------|
| Process model | Client spawns server as child process | Server runs independently; clients connect via URL |
| Client count | **One** (the spawning client) | **Many concurrent** |
| State sharing | None — each process has its own memory | Shared — one process serves all clients |
| Cold start | Per session (200-400ms Python/Node) | Once at daemon start |
| Auth | Inherits parent env vars | HTTP headers (OAuth, bearer, API key) |
| Fault isolation | Perfect — one crash = one session | Server crash affects all connected clients |
| Network | None (local pipes) | TCP (localhost or remote) |
| Audit | Per-process stderr only | Centralized HTTP interception point |
| Grok config | `[mcp_servers.x] command = "..."` | `[mcp_servers.x] url = "http://..."` |

**The deciding question:** does one client own the server process (stdio), or do many
clients share one server over a network (Streamable HTTP)?

## What "mux pattern" / "multiplexing" means

The user asked about the "mux pattern." In MCP context, this is **MCP Multiplexing** —
running one server process that multiple clients connect to. Two flavors:

1. **Transport-level multiplexing** — Streamable HTTP transport inherently supports
   multiple clients on one server process. This is built into the spec (2025-03-26+).
   No extra software needed.

2. **Gateway-level multiplexing** — federating multiple MCP servers behind a single
   gateway endpoint (AgentGateway, TrueFoundry MCP Gateway). Clients connect to one URL
   and see tools from all federated servers. This is enterprise-scale; overkill for a
   solo operator but the architecture is worth knowing.

For this host, **transport-level multiplexing via Streamable HTTP is the right pattern**
for shared MCP servers. No gateway needed.

## Critical finding: stdio MCP servers CANNOT share across clients

From the MCP TypeScript SDK issue #243 (closed Dec 2025):

> "A MCP server cannot handle connections from multiple MCP clients. The clients can be
> different applications or multiple replicas of the same application."

This is fundamental to stdio: the transport is stdin/stdout pipes between **one** parent
and **one** child. You cannot multiplex stdio across multiple Grok terminals.

**What this means today:** every Grok terminal spawns its own copy of every stdio MCP
server. With 5 terminals and the Search MCP, that's 5 Python processes each with their
own health tracker, no shared cache, 5× the memory.

## When to share (Streamable HTTP) vs isolate (stdio)

### Share via Streamable HTTP when:

| Reason | Example |
|--------|---------|
| **Stateful server with expensive init** | Search MCP loads backend configs, establishes health state — wasteful to redo per terminal |
| **Shared cache benefits all clients** | Search results cached in one process serve all terminals; RRF health tracking is cumulative |
| **Resource-heavy per process** | Python MCP ~60-120MB resident; 5 terminals = 300-600MB of duplicate processes |
| **Centralized audit matters** | All tool calls go through one interceptable endpoint |
| **Credential rotation** | One place to update API keys, not per-terminal env |

### Isolate via stdio when:

| Reason | Example |
|--------|---------|
| **Per-session state is the point** | Filesystem tools, git operations, worktree-specific context |
| **Fault isolation is critical** | A crash in terminal A must not affect terminal B |
| **Stateless/lightweight tool** | A simple utility that has no cache or shared state to lose |
| **Security boundary** | Each terminal's secrets stay in that terminal's process |
| **No network infrastructure wanted** | stdio = zero config, zero ports, zero daemons |

## Do's and don'ts (Windows 11 specific)

### Do

- **Use stdio for per-terminal-isolated tools.** Filesystem, git, worktree context —
  these should be stdio so each terminal has its own instance. This is the default.

- **Use Streamable HTTP for shared-state tools.** The Search MCP, episodic-memory,
  any tool with an expensive cache or cumulative health tracker. Run as a daemon.

- **Bind HTTP servers to localhost only** (`127.0.0.1` or `localhost`). Do not expose
  MCP servers to the network unless you have auth. Windows Firewall will prompt; deny
  public network access.

- **Use a Windows Service or Task Scheduler** for long-running HTTP MCP daemons. A
  scheduled task at logon with `python server.py` keeps the daemon alive across terminal
  restarts. Or use NSSM (Non-Sucking Service Manager) to install as a Windows Service.

- **Pick unique ports per shared MCP.** Search MCP on `localhost:8321`, episodic-memory
  on `localhost:8322`, etc. Document in config.

- **Handle startup ordering.** If Grok starts before the HTTP MCP daemon is listening,
  you get `ECONNREFUSED`. Either: (a) start daemons at logon via Task Scheduler before
  Grok, (b) add retry logic in the Grok MCP client config, or (c) accept the first
  terminal may need a manual daemon start.

- **Use FastMCP's `transport="streamable-http"` for Python servers.** One line change:
  ```python
  mcp.run(transport="streamable-http", host="127.0.0.1", port=8321)
  ```

- **Keep stdio as fallback.** If the HTTP daemon is down, the tool is unavailable to all
  terminals. For critical tools, consider a stdio fallback config that can be swapped in.

- **Monitor daemon health.** A dead HTTP MCP daemon silently breaks all terminals.
  Use a simple health check: `curl http://localhost:8321/health` in a scheduled task.

### Don't

- **Don't use the deprecated HTTP+SSE transport** (spec 2024-11-05). It was deprecated
  in 2025-03-26 and replaced by Streamable HTTP. New builds should use Streamable HTTP.
  Grok's config supports it via `url = "..."`.

- **Don't expose MCP HTTP servers to `0.0.0.0`** on Windows without auth. Localhost only.
  Windows machines are often on networks with other devices; an open MCP port is an
  unauthenticated tool API.

- **Don't share stateful MCP servers across DIFFERENT users.** Multi-user sharing requires
  proper auth (OAuth headers, per-user sessions). This host is single-user multi-terminal,
  so localhost-only without auth is fine. But don't extend to remote users without auth.

- **Don't forget that stdio gives free fault isolation.** If a shared HTTP MCP server
  crashes, ALL terminals lose the tool simultaneously. With stdio, only the crashed
  terminal is affected. For tools where availability matters more than cache, stdio wins.

- **Don't assume `mcp.run()` defaults to HTTP.** FastMCP defaults to stdio. You must
  explicitly pass `transport="streamable-http"`.

- **Don't put HTTP MCP servers behind Windows authentication** (IIS/Windows Auth). MCP
  clients expect bearer tokens or no auth on localhost. Windows Integrated Auth will
  break the HTTP negotiation.

- **Don't run multiple instances of the same HTTP MCP on the same port.** The second
  instance fails to bind. Use a PID file or port check before starting.

## The specific recommendation for this host's Search MCP

**Current state:** stdio (each Grok terminal spawns its own `server.py` process).

**Problem:** 5 terminals = 5 Search MCP processes, each ~60-120MB, each with independent
health tracking (no shared circuit breaker state), no shared result cache.

**Optimal:** Convert to Streamable HTTP daemon on `localhost:8321`.

### Migration (one-line change in server.py)

```python
# Current (stdio):
mcp.run()

# Optimal (Streamable HTTP):
mcp.run(transport="streamable-http", host="127.0.0.1", port=8321)
```

### Grok config change

```toml
# Current (stdio — one process per terminal):
[mcp_servers.search]
command = "python"
args = ["C:/Users/brsth/.grok/search-mcp/server.py"]

# Optimal (Streamable HTTP — one shared process):
[mcp_servers.search]
url = "http://127.0.0.1:8321/mcp"
```

### Daemon management (Windows 11)

**Option A: Task Scheduler at logon (simplest)**
```powershell
# Create a scheduled task that starts the Search MCP daemon at logon
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:/Users/brsth/.grok/search-mcp/server.py"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "SearchMCP-Daemon" -Action $action -Trigger $trigger -RunLevel Highest
```

**Option B: NSSM (Windows Service — survives logoff)**
```powershell
nssm install SearchMCP "C:\Python314\python.exe" "C:\Users\brsth\.grok\search-mcp\server.py"
nssm start SearchMCP
```

**Option C: Manual start (simplest, no automation)**
```powershell
# Run in a terminal that stays open
python C:/Users/brsth/.grok/search-mcp/server.py
```

### Trade-offs for this specific migration

| Factor | stdio (current) | Streamable HTTP (proposed) |
|--------|-----------------|---------------------------|
| Memory (5 terminals) | 5 × ~100MB = ~500MB | 1 × ~100MB = ~100MB |
| Shared health tracking | No (each has own circuit breaker) | Yes (cumulative across terminals) |
| Shared result cache | No | Yes (if cache is added later) |
| Fault isolation | Perfect (one crash = one terminal) | Shared (daemon crash = all terminals) |
| Startup latency | 200-400ms per terminal open | 0ms (daemon already running) |
| Complexity | Zero config | Daemon management + port + health check |
| Credential rotation | Update .env, restart all terminals | Update .env, restart one daemon |

**Recommendation:** convert the Search MCP to Streamable HTTP. The shared health tracking
alone is worth it — the DDG circuit breaker state currently resets per terminal, losing
the knowledge that DDG has been failing. With a shared daemon, all terminals benefit from
one terminal's discovery that a backend is down.

**Keep stdio for:** filesystem tools, git tools, any future per-session-isolated MCP.
The rule: if the tool's state is per-session, use stdio; if the tool's state is shared
(cache, health, cumulative knowledge), use Streamable HTTP.

## Existing MCP servers on this host — share vs isolate

| MCP Server | Current Transport | Share or Isolate? | Reason |
|------------|-------------------|-------------------|--------|
| **search** (our new one) | stdio | **Share** (Streamable HTTP) | Cumulative health tracking, potential cache |
| **firecrawl** | OAuth HTTP MCP (already shared) | Already shared ✓ | Hosted by Firecrawl; inherently multi-client |
| **minimax-search** | stdio (Grok-managed) | **Isolate** (keep stdio) | Stateless; per-session is fine |
| **web-search-prime** | stdio (Grok-managed) | **Isolate** (keep stdio) | Stateless; per-session is fine |
| **chrome-devtools** | stdio | **Isolate** | Per-terminal browser context |
| **episodic-memory** | stdio | **Consider sharing** | Has a SQLite store that could be shared; but write conflicts risk |
| **tasks** | stdio | **Consider sharing** | Task store is already file-based (shared by design) |

## Authority sources (scored)

| Source | Score | Key finding |
|--------|-------|-------------|
| [TrueFoundry: Stdio vs Streamable HTTP](https://www.truefoundry.com/blog/mcp-stdio-vs-streamable-http-enterprise) (2026-05-21) | 12 | Process-per-user model breaks at scale; shared cache is 2 orders of magnitude less memory; migration is a 5-line patch |
| [StartDebugging: MCP stdio vs HTTP vs SSE](https://startdebugging.net/2026/07/mcp-stdio-vs-http-vs-sse-transport-which-to-choose/) (2026-07-02) | 12 | Clear decision rule: stdio for local single-client, Streamable HTTP for remote/multi-client, HTTP+SSE deprecated |
| [MCP spec 2025-11-25: Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | 12 | Authoritative spec; defines both transports as first-class |
| [GitHub: MCP TypeScript SDK #243](https://github.com/modelcontextprotocol/typescript-sdk/issues/243) (closed Dec 2025) | 11 | Confirms stdio cannot multi-client; Streamable HTTP solves it; CVE-2026-25536 cross-client leak fixed Feb 2026 |
| [AgentGateway: MCP Multiplexing](https://agentgateway.dev/blog/2026-02-20-mcp-multiplexing-tool-access-agentgateway) (2026-02-20) | 10 | Gateway-level federation pattern (enterprise; overkill for solo but architecture is correct) |
| [Grok Build docs: 07-mcp-servers.md](https://~/.grok/docs/user-guide/07-mcp-servers.md) | 11 | Confirms Grok supports both `command` (stdio) and `url` (HTTP/SSE) config |
| [Grizzly Peak: MCP Transport Options](https://www.grizzlypeaksoftware.com/library/mcp-transport-options-stdio-vs-sse-vs-websocket-decbjfzs) (2026-02-13) | 10 | stdio provides "perfect isolation between clients"; SSE for web-accessible |

## Conflicts / caveats

- **⚠️ CVE-2026-25536** (cross-client data leak in MCP TypeScript SDK, fixed Feb 2026):
  if using Streamable HTTP with the TS SDK, ensure version is post-fix. Python SDK
  (FastMCP) was not affected.
- **⚠️ Startup race**: HTTP MCP daemon must be running before Grok connects. Use Task
  Scheduler at logon or accept manual start for first terminal.
- **⚠️ FastMCP `stateless_http=True`**: for truly stateless tools, set this flag to
  avoid session overhead. For the Search MCP (which has health tracking), keep stateful.
- **⚠️ Port conflicts**: if another process uses port 8321, the daemon fails silently.
  Use a port check before binding.

## Relationship to existing concepts

- **Related** [[web-search-tool-routing]] — the Search MCP is the execution engine for
  the routing strategy described there.
- **Related** [[mcp-http-server-placeholder-resolution]] — prior finding about HTTP MCP
  header config; still applies to Streamable HTTP servers.
- **Related** [[optimal-multi-backend-search-strategy]] — RRF and parallel dispatch
  benefit from shared daemon state (cumulative health tracking).

## Sources

- https://www.truefoundry.com/blog/mcp-stdio-vs-streamable-http-enterprise (2026-05-21)
- https://startdebugging.net/2026/07/mcp-stdio-vs-http-vs-sse-transport-which-to-choose/ (2026-07-02)
- https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- https://github.com/modelcontextprotocol/typescript-sdk/issues/243
- https://agentgateway.dev/blog/2026-02-20-mcp-multiplexing-tool-access-agentgateway
- `~/.grok/docs/user-guide/07-mcp-servers.md`
- https://www.grizzlypeaksoftware.com/library/mcp-transport-options-stdio-vs-sse-vs-websocket-decbjfzs

## Staleness

MCP spec is evolving (2026-07-28 release candidate goes stateless). Re-check transport
recommendations if >6 months old. FastMCP API may change; verify `transport=` parameter
on upgrade.

## Auto-related

- [[mcp-http-server-placeholder-resolution]]
- [[auto-commit-authority-isolation]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
