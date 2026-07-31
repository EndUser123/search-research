# Chrome ACP Ship Spec

## Context

Chrome ACP proxy bridges browser tabs to `grok agent stdio`. A session transcript (using M3) revealed multiple bugs: vanishing writes, empty read_file, fabricated cancel signals, and shell-quoting cascades. Root cause: proxy used `process.cwd()` as agent CWD; when launched from `C:\Users\brsth\chrome-acp`, the agent's native tools enforced the wrong workspace boundary, silently dropping all `P:\` operations.

## Completed work (do not redo)

- `command.js`: hard-coded `WORKSPACE_ROOT = "P:\\"` replacing `process.cwd()` — verified live, `proxy.log` shows `CWD: P:\`
- `server.js`: added `POST /restart-proxy` endpoint
- `restart-proxy.js`: detached spawn helper
- `sidepanel-t6n74ra3.js`: Feature 7 (proxy-down banner), Feature 8 (floating buttons)
- `re-apply-patches.ps1`: covers all patched files
- MCP server installs: Kinocut + OpenCV MCP, both verified
- Wiki concepts: `mcp-sdk-2-0-fastmcp-breakage.md`, `asserting-runtime-behavior-from-memory-not-testing.md`
- pytest suites: `P:/tmp/test_chrome_acp_patches.py`, `P:/tmp/test_feature8_floating_buttons.py`, `P:/tmp/test_sidepanel_runtime_pytest.py`

## Ship requirements

### S1: Verify vanishing-write fix is live

**What:** The proxy is running with `WORKSPACE_ROOT = "P:\\"` (confirmed in `proxy.log`). The live verification — having the Chrome ACP agent write a file to `P:\tmp\` and read it back — was never completed.

**Acceptance criteria:**
- Chrome ACP agent (via sidepanel) successfully writes a file to `P:\tmp\test-cwd-fix.txt`
- Agent reads the file back via `read_file` and the content matches
- No fallback to `python -c` or terminal commands was needed (native tools worked directly)
- Receipt: agent session output showing both write and read succeeding

**Verification command:** Manual — connect sidepanel, send a prompt asking the agent to write + read a test file to `P:\tmp\`

**Files involved:** No file changes. This is a runtime verification of existing code.

### S2: Fix fabricated cancel bug

**What:** The proxy reports `stopReason: "cancelled"` in two scenarios that are NOT user-initiated cancels:
1. Duplicate-prompt suppression (`server.js` ~line 487): same prompt text within 400ms → silently dropped as "cancelled"
2. WebSocket disconnect handler (`server.js` ~lines 517-525): any WS drop → agent process killed, reported as "cancelled"

The operator confirmed they did not cancel. A malformed `python -c` command caused M3 to loop; during that loop the WebSocket dropped or the agent process crashed; the sidepanel saw it as "cancelled." This is a trust-integrity bug: the operator cannot trust "cancelled" messages.

**Acceptance criteria:**
- `server.js` distinguishes between: (a) genuine user cancel (operator clicked stop), (b) WebSocket disconnect, (c) agent process crash/exit, (d) duplicate-prompt suppression
- Each scenario sends a distinct `stopReason` or error message to the sidepanel
- The sidepanel displays the actual cause, not a generic "cancelled"
- `node --check server.js` passes
- pytest verification covers the new branching logic
- Receipt: test output showing distinct stop reasons for each scenario

**Files to modify:**
- `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\server.js`
- `C:\Users\brsth\chrome-acp\server.patched.js` (update patched copy)
- `P:/tmp/test_chrome_acp_patches.py` (add tests for cancel distinction)

**Key code locations:**
- `server.js` line ~487: duplicate-prompt suppression block
- `server.js` lines ~517-525: `handleDisconnect` function
- `server.js` lines ~528-555: `handleCancel` function (genuine cancel — this is the correct path)
- `server.js` line ~488: `send(ws, "prompt_complete", { stopReason: "cancelled" })` — this is the duplicate-suppression false-cancel

### S3: Run mcpolish as one-shot CLI

**What:** `mcpolish` is a static linter for MCP tool descriptions. The Chrome ACP proxy exposes `browser_tabs`, `browser_read`, `browser_execute` as MCP tools. The operator wants mcpolish run against these descriptions to catch vague or colliding tool descriptions.

**Acceptance criteria:**
- `pip install mcpolish` or `pipx run mcpolish` succeeds
- mcpolish runs against the Chrome ACP tool descriptions (extract from `mcp/handler.js` or query the live proxy's `tools/list`)
- Output shows any findings (vague descriptions, parameter type issues, collisions)
- Results documented (wiki concept or handoff update)
- Receipt: mcpolish command output

**Files involved:** No file changes unless findings warrant patches.

### S4: Structural prevention for assert-without-investigating pattern

**What:** The agent repeatedly asserted runtime/platform behavior as fact without testing. The operator said "we must kill this behavior." A wiki concept (`asserting-runtime-behavior-from-memory-not-testing.md`) was written, but no structural enforcement exists.

**Acceptance criteria:**
- Evaluate whether a hook (PreToolUse on Stop, or a PostToolUse check) could catch claims about runtime behavior that lack a verification receipt
- If a hook is feasible: implement it, test it
- If a hook is not feasible: document why in the wiki concept and propose the next-best structural mitigation (e.g., a checklist gate in a skill)
- Receipt: working hook test OR documented infeasibility with proposed alternative

**Files to modify (if hook feasible):**
- `P:/.claude/hooks/` or `~/.grok/hooks/` (new hook file)
- `~/.grok/config.toml` (hook registration, if Grok Build)
- `P:/.data/wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md` (update with structural fix)

## Out of scope

- Model routing (resolved: tools own their model config, orchestrator model is irrelevant to per-tool model selection)
- Chrome ACP extension store packaging
- Native messaging host for cold-start proxy launch
- Storybook MCP, video-audio-mcp (explicitly skipped per install analysis)
