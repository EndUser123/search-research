# Stream 3: Research + infrastructure probing handoff

| Field | Value |
|---|---|
| **Stream** | Web research (Claude Code ultrathinks) + MCP/tool probing (3 broken/unused tools) |
| **Priority** | MEDIUM — unblocks Stream 4; MCP fixes may unblock other workflows |
| **Status** | Not started; all independent investigations |
| **Effort** | ~1.5 hours (parallel: external LLM + explore subagent) |
| **Delegation** | `/agy` for research; subagent (`explore`) for MCP probes |

## Goal

Four independent investigations: (1) what Claude Code thinking hooks/plugins exist that we should port to Grok, (2) probe `minimax-search__understand_image`, (3) fix firecrawl MCP auth, (4) fix episodic-memory MCP handshake failure.

## Background

### Claude Code ultrathinks

The user asked: "should we use Claude Code's ultrathinks/thinking skills/hooks/plugins for Grok? What integrations can it have with wiki and /tp?" I couldn't answer without more research. Claude Code has thinking hooks (type: prompt, type: agent, external LLM invocation) that may have patterns our `/go` H1 Think Pack and `/tp` don't cover.

### MCP failures (session-start)

At session start, two MCP servers failed:
- `episodic-memory`: "handshake failed: Send message error Transport [xai_grok_mcp::servers::SafeTokioChildProcess] error: The pipe is being closed. (os error 232)"
- `firecrawl`: "auth required"

Plus one never probed:
- `minimax-search__understand_image`: 2nd tool in the minimax-search MCP; described as "LLM-powered vision tool that can analyze and interpret image content." Never tested.

## Deliverables

### 1. Claude Code ultrathinks research (external LLM)

**Delegate to:** `/agy` (Gemini CLI — different model architecture, catches different patterns)

**Prompt:** "Research what Claude Code offers for extended thinking / reasoning quality. Specifically: (a) what are the 'ultrathink' and 'ultracode' modes — are they hooks, skills, or model configs? (b) what thinking hooks exist (type: prompt, type: agent, external LLM)? (c) what patterns do they implement that a Grok Build agent with /go (Think Pack, 4-lens pass), /tp (behavioral drift correction), and /red-team (adversarial specialists) might be missing? (d) are any of these portable to a non-Claude-Code environment? Return a structured comparison: pattern name → what it does → do we have an equivalent → if not, should we build one?"

**Output:** Write findings to `P:/tmp/ultrathinks-research-results.md`.

**Why external:** this is a "what are we missing?" question — exactly the B-class blind-spot case where same-model research produces confirmation bias.

### 2. minimax-search understand_image probe (subagent)

**Delegate to:** subagent (`explore`, read-only)

**Task:**
1. Read the tool's input schema (already known: `prompt` + `image_source`)
2. Find or generate a test image (any small PNG in `P:/tmp/` or download one)
3. Call `minimax-search__understand_image` with a simple prompt ("describe this image")
4. Report: does it work? What's the output quality? Latency? Any errors?
5. Document findings

**Output:** Write to `P:/tmp/minimax-vision-probe-results.md`.

### 3. firecrawl MCP auth fix (subagent)

**Delegate to:** subagent (`explore`, execute)

**Task:**
1. Search for firecrawl configuration: `rg -r '' 'firecrawl' ~/.grok/ ~/.claude/ P:/packages/ --type toml --type json -l`
2. Find the MCP server config (likely in settings.json or .mcp.json)
3. Determine what auth is needed (API key? OAuth? Token from firecrawl.dev?)
4. Check if a key exists in env vars or config: `rg 'FIRECRAWL' ~/.grok/ ~/.claude/`
5. If key missing: document where to get one (firecrawl.dev signup)
6. If key present but wrong: fix the config

**Output:** Write to `P:/tmp/firecrawl-mcp-fix-results.md`. If fix applied, note the config change.

### 4. episodic-memory MCP handshake fix (subagent)

**Delegate to:** subagent (`explore`, execute)

**Task:**
1. Find the episodic-memory MCP server config
2. Error was: "The pipe is being closed. (os error 232)" — this is a Windows pipe error, often caused by the child process exiting before the parent reads from the pipe
3. Check: is the server process starting? `Get-Process | Where-Object { $_.Name -like '*episodic*' -or $_.Name -like '*memory*' }`
4. Check: is there a log file? Look under `~/.grok/logs/` or `P:/.claude/logs/`
5. Check: does the server binary/script exist at the configured path?
6. Common Windows fixes: run as admin, check pipe permissions, restart the MCP host

**Output:** Write to `P:/tmp/episodic-memory-mcp-fix-results.md`.

## Dependencies

- None. All four investigations are independent.
- Stream 4 (prompt enhancements) benefits from deliverable #1 (ultrathinks research) but doesn't block on it.

## Verification criteria

1. `P:/tmp/ultrathinks-research-results.md` exists with structured comparison
2. `P:/tmp/minimax-vision-probe-results.md` exists with pass/fail on the tool
3. Firecrawl: either fixed (auth resolved, tool callable) or documented (what's needed)
4. Episodic-memory: either fixed (handshake succeeds) or root-caused (what's broken, what to try next)

## Source references

- Session-start system reminder listed MCP connection status
- `~/.grok/tool-fallbacks.md` — MCP server availability table (lines 35-41)
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SCHEMA.md` — for comparing thinking patterns
- `C:/Users/brsth/.grok/skills/go/SKILL.md` — /go Think Pack (H1) for comparison
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — /tp for comparison
