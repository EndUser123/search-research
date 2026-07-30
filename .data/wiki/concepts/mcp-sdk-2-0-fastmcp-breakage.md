---
title: "MCP SDK 2.0 fastmcp Breakage: Systemic Pin Workaround for 1.x-era MCP Servers"
created: 2026-07-30
source: session-20260730
tags: [mcp, dependency-fragility, uvx, fastmcp, breaking-change, install-workaround]
summary: >
  MCP SDK 2.0.0 (released ~2026) removed `mcp.server.fastmcp`, which the
  entire 1.x-era MCP server ecosystem imports. Both kinocut 1.11.1 and
  opencv-mcp-server 1.29.0 break on first launch with
  `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`. The fix is to
  pin `--with "mcp<2"` in uvx launch args. This applies to ANY MCP server
  installed or updated after the SDK 2.0 release until each publishes a
  2.0-compatible version.
agent: grok
host: grok
cognitive_load: 2
verification: dual-source-verified
sources:
  - https://github.com/KyaniteLabs/kinocut (kinocut 1.11.1 — confirmed broken)
  - https://github.com/GongRzhe/opencv-mcp-server (opencv-mcp-server 1.29.0 — confirmed broken)
relations:
  - target: wiki/concepts/mcp-servers-for-polishing-code-words-images-video.md
    type: documents-caveat-for
---

# MCP SDK 2.0 fastmcp Breakage

## The problem

The MCP Python SDK released version 2.0.0 (~2026), which removed or renamed
`mcp.server.fastmcp`. The entire generation of MCP servers written against
SDK 1.x imports `from mcp.server.fastmcp import FastMCP` at module load time.

When `uvx` resolves dependencies for these servers, it picks `mcp==2.0.0`
(the latest), and the server crashes immediately:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

## Confirmed affected servers

| Server | Version | Import line | Status |
|--------|---------|-------------|--------|
| kinocut | 1.11.1 | `from mcp.server.fastmcp import Context` | Broken without pin |
| opencv-mcp-server | 1.29.0 | `from mcp.server.fastmcp import FastMCP` | Broken without pin |

Both confirmed via direct stdio handshake test on 2026-07-30 on this Windows 11 host.

## The fix

Pin `mcp<2` in the `uvx` launch args. For config.toml:

```toml
[mcp_servers.<name>]
command = "uvx"
args = ["--from", "<package>", "--with", "mcp<2", "<entrypoint>"]
```

Or for bare package servers:

```toml
[mcp_servers.<name>]
command = "uvx"
args = ["--with", "mcp<2", "<package>"]
```

The `--with "mcp<2"` flag tells `uvx` to resolve the MCP SDK at a 1.x version,
satisfying the `from mcp.server.fastmcp import ...` import.

## When this applies

**Any MCP server installed or re-resolved after the SDK 2.0 release** will hit
this unless:
1. The server has already published a 2.0-compatible release, OR
2. The server's `pyproject.toml` pins `mcp<2` itself, OR
3. You add `--with "mcp<2"` to the launch args

This is a **systemic ecosystem breakage**, not a per-server bug. The
implication: when installing any new MCP server via `uvx`, **probe the
handshake first without the pin**. If it fails with the `fastmcp` import error,
add the pin.

## Diagnostic probe (for any new MCP server)

```python
import subprocess, json, time
# Quick handshake probe — if this exits with ImportError, add the pin
p = subprocess.Popen(["uvx", "<package>"], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
p.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
    "params":{"protocolVersion":"2024-11-05","capabilities":{},
              "clientInfo":{"name":"probe","version":"0.1"}}}) + "\n")
p.stdin.flush()
# If process exits with rc=1 and stderr has ModuleNotFoundError, add the pin
```

## When to drop the pin

Drop `--with "mcp<2"` only after the server publishes a release that:
- Imports from the new module path (e.g., `mcp.server.fastmcp` → wherever 2.0 moved it), OR
- Pins `mcp<2` in its own `pyproject.toml`, OR
- Explicitly supports `mcp>=2` in its changelog/release notes

Until then, the pin is load-bearing. A future `uvx` resolver change that
ignores `--with` overrides would break the server on launch again.
