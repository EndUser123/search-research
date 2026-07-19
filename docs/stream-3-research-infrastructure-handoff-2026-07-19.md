# Stream 3: Research + infrastructure probing handoff

| Field | Value |
|---|---|
| **Stream** | Web research (Claude Code ultrathinks) + MCP/tool probing (3 broken/unused tools) |
| **Priority** | MEDIUM — unblocks Stream 4; MCP fixes may unblock other workflows |
| **Status** | **COMPLETE 2026-07-19** — all 4 deliverables closed; 3 of 3 MCP issues resolved (firecrawl OAuth done, episodic-memory config patched + MCP host picked it up, minimax vision probed & working). See **Status & Findings** below. |
| **Effort** | ~1.5 hours estimated; ~1 hour actual (parallel fan-out via `/go`) |
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

**Prompt:** "What thinking/reasoning quality hooks does Claude Code offer that a Grok Build agent with /go (Think Pack, 4-lens pass), /tp (behavioral drift correction), and /red-team (adversarial specialists) might be missing? Focus on patterns that improve reasoning quality before action — not code review or testing. Return a structured comparison: pattern name → what it does → do we have an equivalent → if not, should we build one?"

**Output:** Write findings to `P:/tmp/ultrathinks-research-results.md`.

**Why external:** this is a "what are we missing?" question — exactly the B-class blind-spot case where same-model research produces confirmation bias.

### 2. minimax-search understand_image probe (subagent)

**Delegate to:** subagent (`explore`, `capability_mode: execute` — needs to call the MCP tool, not just read)

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

1. [x] `P:/tmp/ultrathinks-research-results.md` exists with structured comparison — **24,847 B**, VERDICT complete
2. [x] `P:/tmp/minimax-vision-probe-results.md` exists with pass/fail on the tool — **7,354 B**, VERDICT complete (PASS, ~11.4 s latency)
3. [x] Firecrawl: **fixed** — auth resolved via TUI OAuth 2026-07-19 12:20, `~/.grok/mcp_credentials.json` (630 B) cached, 26 tools discovered, smoke test PASS (`firecrawl_scrape` of example.com → 200 OK, 1 credit, cache hit)
4. [x] Episodic-memory: **fixed** — `.mcp.json` absolute-path patch applied 2026-07-19; MCP host reload (triggered by T3 OAuth completion) picked up the fix; handshake OK, 2 tools discovered

---

## Status & Findings (post-execution, 2026-07-19)

### Deliverable outcomes

| # | Deliverable | Path | Size | VERDICT |
|---|---|---|---|---|
| T1 | Claude Code ultrathinks research | `P:/tmp/ultrathinks-research-results.md` | 24,847 B | complete |
| T2 | minimax-search `understand_image` probe | `P:/tmp/minimax-vision-probe-results.md` | 7,354 B | complete (PASS) |
| T3 | firecrawl MCP auth | `P:/tmp/firecrawl-mcp-fix-results.md` | 9,398 B | **RESOLVED** (OAuth + smoke test) |
| T4 | episodic-memory handshake | `P:/tmp/episodic-memory-mcp-fix-results.md` | 12,260 B | **RESOLVED** (config patch + host reload) |

### Key findings

- **T1 — Ultrathinks research.** 9 patterns assessed by agy (Gemini CLI, different model architecture). After synthesis reclassification: **3 BUILD** (Hierarchical Rule Inheritance HIGH ROI; Auto Memory / `MEMORY.md` analog MEDIUM ROI; Diagnostic Hypothesis Ledger MEDIUM ROI), **5 SKIP** (patterns Grok already covers), **1 MONITOR** (Adaptive Thinking Budget — host-model-dependent). B-class mitigation worked: agy miscategorized 3 rows as "Claude Code patterns Grok covers" when they actually describe Grok patterns — recategorized honestly in synthesis. See `P:/tmp/ultrathinks-research-results.md` for the full structured comparison.
- **T2 — minimax vision probe.** `minimax-search__understand_image` works on this host. **~11.4 s end-to-end latency** measured with PowerShell Stopwatch (start 11:32:43.481 → end 11:32:54.896). Accurate on prose description; minor misread on numeric badge ("3 → 4 REVIEW AGENTS") — disclosed in report. Format caveat: **JPEG/PNG/WebP only**. Tool description verified verbatim from `search_tool` schema discovery (no parameter guessing).
- **T3 — firecrawl MCP auth.** Root cause was a **Grok-side OAuth gate** (not server-side rejection). The hosted server at `https://mcp.firecrawl.dev/v2/mcp` is actually reachable (unauthenticated probes during T3 succeeded: `tools/list` returned full inventory; `firecrawl_scrape` returned real markdown from example.com). Grok refuses to connect without an OAuth token cached in `~/.grok/mcp_credentials.json`. **Resolution:** user ran the documented TUI flow (`/mcps` → navigate to firecrawl row → press `i` → browser OAuth at firecrawl.dev → Grok wrote the credentials file automatically). Smoke test confirmed: 26 tools reachable, live `firecrawl_scrape` against example.com returned real markdown with `cacheState: hit` (cache warmed by T3's earlier probe).
- **T4 — episodic-memory handshake.** Root cause: plugin's `.mcp.json` shipped Codex-form relative paths (`./cli/mcp-server-wrapper.js`, `cwd: "."`); Grok's MCP host launches with CWD `P:\`, so Node resolved `./cli/...` to `P:\cli\mcp-server-wrapper.js` (nonexistent) → `MODULE_NOT_FOUND` → child exits → stdio pipe closes → Rust parent surfaces "os error 232". **Fix:** absolute paths in `args` and `cwd`. **Resolution path:** T4's fix was applied; the MCP host reloaded when firecrawl OAuth completed (12:21), picked up the new config, handshake succeeded. Stderr log is now the clean 45 B ready banner.

### Side-effects (require ongoing awareness)

- **T4 `.mcp.json` edit (durability caveat).** `~/.grok/installed-plugins/episodic-memory-479fd403/.mcp.json` was patched from relative to absolute paths. The plugin's own test suite (`test/codex-plugin.test.ts`) hard-asserts the Codex relative-path form and would fail against the patched file. **Future `git pull` or plugin reinstall will silently revert this fix.** Durable remediation is upstream: file an issue against `obra/episodic-memory` requesting a host-aware `.mcp.json` (e.g., a `cwd: "${PLUGIN_ROOT}"` placeholder that the host expands at launch) so the same plugin works under both Codex and Grok MCP hosts.
- **`~/.grok/tool-fallbacks.md` updates.** Three rows added/updated in the MCP server availability table: `minimax-search` flipped from `TBD` → `WORKING` (T2); `firecrawl` row added with `WORKING` status and auth-flow instructions (T3); `episodic-memory` row added with `WORKING` status and durability caveat (T4).
- **State file.** `P:/.artifacts/console_1209/stream-3-state.md` (12-char `termSafe`, per `/go` SKILL.md) tracks current state across sessions. Includes `/check` verdicts and a transcript-disambiguation lesson (the initial `/check` process verifier picked the wrong concurrent-session transcript; corrected via `user_query` line matching).
- **No commits.** `/go` did not commit any work; all output went to `P:/tmp/` (transient artefacts per workspace root cleanliness rule).

### Inputs for downstream streams

- **Stream 4 (prompt enhancements).** T1's 3 BUILD recommendations are **not blocking** but are useful inputs. The Hierarchical Rule Inheritance finding (HIGH ROI) in particular may inform how Stream 4 structures new skill prompts across the workspace.

### Process notes

- Executed under `/go parallel-change` profile with H1 (think) / H3 (discover) / H4 (parallel) / H6 (verify) packs.
- 4 subagents fanned out in parallel: T1 via `agy` CLI (external LLM, B-class mitigation), T2/T3/T4 via `general-purpose` subagents with `capability_mode: execute`.
- T3 needed one corrective retry: first write call returned success but the file did not land; parent `/go` caught the missing file in its verification pass, resumed the subagent, and the second attempt produced the deliverable.
- `/check` post-execution: 5/5 verifiers PASS (T1, T2, T3, T4 deliverable verifiers + 1 process-discipline verifier). Run dir: `P:/.artifacts/console_12092a49-e448-4be3-b146-7930/grok-check/20260719-114623-599/` (36-char `termSafe`, differs from `/go`'s 12-char `console_1209` — both are valid per their respective SKILL.md specs).

## Source references

- Session-start system reminder listed MCP connection status
- `~/.grok/tool-fallbacks.md` — MCP server availability table (lines 35-41)
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SCHEMA.md` — for comparing thinking patterns
- `C:/Users/brsth/.grok/skills/go/SKILL.md` — /go Think Pack (H1) for comparison
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — /tp for comparison
