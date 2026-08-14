---
title: "In Claude code they have hooks. They can be global hooks or skill hooks or plugin based hooks. What prompt can I give to"
date: "2026-05-03"
mode: "CONCISE"
uuid: "bcddda33-794c-4626-8929-e2fddc5bed30"
entry_count: 8
---

## Human

In Claude code they have hooks. They can be global hooks or skill hooks or plugin based hooks. What prompt can I give to an LLM in Claude code so that they can find all the hooks from all those sources?

## Assistant

Claude Code hooks are defined across multiple sources: global/user settings (`~/.claude/settings.json`), project settings (`.claude/settings.json` and `.claude/settings.local.json`), plugins (`hooks/hooks.json` in plugin directories), and frontmatter in skills/agents (e.g., YAML blocks in `SKILL.md` or agent files).[1][2]

## Prompt to List All Hooks

Use this exact prompt in Claude Code to discover and enumerate all hooks comprehensively. It leverages Claude's awareness of its runtime environment, including the `/hooks` menu (which aggregates all sources) and file introspection tools like `Read`, `Glob`, and `Grep`.

```
List ALL configured hooks in this session from EVERY source: global/user (~/.claude/settings.json), project (.claude/settings*.json), plugins (hooks/hooks.json in enabled plugins), skills/agents (frontmatter), managed policy, session-registered, and built-in.

1. First, run `/hooks` and extract the FULL list: for each event (e.g., PreToolUse), note count, matchers, handlers (type, command/prompt/URL, source file/label like [Plugin], [Local]).

2. For each source file shown (e.g., .claude/settings.json, plugin paths via $CLAUDE_PLUGIN_ROOT), use Read/GLOB to fetch contents. Parse "hooks" objects: events → matcher groups → handlers (if, type:command/prompt/agent/http/mcp_tool, command/prompt/etc.).

3. Cross-reference: confirm /hooks menu matches parsed files; note discrepancies (e.g., session-only, built-in).

4. Tabulate: Event | Matcher | Handler Type | Command/Prompt | Source | Notes (e.g., timeout, async).

5. Highlight active/blocking hooks (e.g., PreToolUse with permissionDecision).

Output only the table + summary of totals per source. Use tools step-by-step; show tool outputs.
```

## Why This Works

- **Comprehensive Coverage**: Explicitly targets all 6+ sources from docs; `/hooks` already aggregates them (user/project/local/plugin/session/built-in).[2][1]
- **Tool-Driven**: Instructs use of `/hooks` (native browser), `Read`/`Glob`/`Grep` for JSON parsing—Claude Code's core tools for config inspection. Avoids hallucination.[3][1]
- **Structured Output**: Forces table for density; verifiable via tool traces. Handles YAML frontmatter via `Grep` on skill/agent dirs (`skills/`, `agents/`).[2]
- **Edge Cases**: Catches mismatches (e.g., file watcher lags), async/experimental types (agent/prompt), plugin vars (`$CLAUDE_PLUGIN_ROOT`). Confidence: high (direct from official docs, May 2026).[1]

## Next Steps

Paste prompt into Claude Code; verify with `/hooks` yourself. If plugins dominate, glob `**/.claude-plugin/hooks/hooks.json`. For code extraction:

```typescript
// TypeScript: Parse hooks JSON (Node.js example)
interface HookConfig { hooks: Record<string, any[]> }
const config: HookConfig = JSON.parse(fs.readFileSync('.claude/settings.json', 'utf8'));
// Traverse: config.hooks[event][group].hooks[...]
```

No clarifying details needed—prompt is self-contained for any Claude Code session.[2]

## Human

What are examples of the 23 hook events and their use cases
Guide to installing and managing Claude Code plugins with hooks

## Assistant

There are around two dozen Claude Code hook events spanning the session lifecycle, tool use, tasks, and agents, and plugins can contribute hooks via a simple JSON config you install and manage through the `/plugin` UI and marketplace commands. Below I’ll (1) give example events with concrete use cases and (2) walk through how to install and manage plugins that define hooks.[1][2][3][4]

***

## Key hook events and concrete use cases

FACT: Official docs list a set of lifecycle hook events (session, tools, tasks, stop, etc.), and external guides note there are now ~24–26 events in recent versions. The exact count changes over time, but the patterns and use cases are stable.[5][3][1]

### Session and setup events

These fire when Claude Code starts or ends a session, or when you run setup-only modes.[3][1][5]

- SessionStart  
  - When: A session begins or resumes.[1][5]
  - Use cases:  
    - Auto-load project context (e.g., run a script to summarize `docs/` into a session note).  
    - Enforce policies (e.g., check repo trust, warn if on main branch).  
    - Initialize env (export project-specific vars, start background daemons).

- SessionEnd  
  - When: A session terminates (user closes, times out, or stops).[5][3]
  - Use cases:  
    - Cleanup temp files, stop background processes.  
    - Log session metrics (duration, tools used) to an internal dashboard.  
    - Commit or stash changes automatically if working in a scratch branch.

- Setup  
  - When: You start Claude Code with `--init-only`, or with `--init` / `--maintenance` in project mode.[1]
  - Use cases:  
    - Enforce repo conventions at init (e.g., ensure `.claude/settings.json` exists, validate plugin list).  
    - Run migrations for your project’s hooks/skills configuration when you bump versions.

***

### User interaction and prompt events

These fire around user prompts and inputs.[6][3][1]

- UserPromptSubmit (name varies slightly across docs, but there is a “user sends prompt” event)  
  - When: The user submits a prompt.[3][5]
  - Use cases:  
    - Red-team / guardrail layer: block dangerous commands (“rm -rf” in instructions) before Claude acts.  
    - Automatic tagging: classify prompt (bugfix, feature, refactor) and log to a ticket system.  
    - Auto-attach context: inject project-specific info when prompts match certain patterns (e.g., “migration”).

- Notification  
  - When: Claude Code sends a notification to the user (e.g., long task finished).[6]
  - Use cases:  
    - Forward completion notifications to Slack/Discord.  
    - Log “waiting for input” vs “finished” transitions for UX telemetry.  
    - Trigger sound or OS notification on long-run completion.

- Stop / StopFailure  
  - When:  
    - Stop: Main agent finishes responding.[6][1]
    - StopFailure: Turn ends due to API error (output is ignored).[1]
  - Use cases:  
    - “Intelligent Stop” loops: prevent stopping if criteria unmet (e.g., tests not passing), ask Claude to keep iterating.[6][1]
    - Auto-retry on transient failures, or open an issue when StopFailure triggers.

***

### Tool lifecycle events

These events wrap tool calls (Read, Write, Shell, HTTP, custom tools, MCP tools, etc.).[7][3][1]

- PreToolUse  
  - When: Before any tool executes (e.g., `Write`, `Shell`, MCP tool call).[7][3][1]
  - Can block: Yes; hook exit code / decision can prevent tool execution.[3][1]
  - Use cases (this is one of the most powerful events):  
    - Safety/permissions: block risky shell commands, require explicit approval for `git push` or infra changes.  
    - Policy enforcement: e.g., only allow writing under `src/` and `tests/`, never under `infra/prod`.  
    - Cost control: rate-limit certain tools (e.g., expensive MCP calls) per session.

- PostToolUse  
  - When: After a tool completes.[7][1]
  - Use cases:  
    - Auto-format or lint after writes, auto-run tests after certain writes.  
    - Log tool usage to a metrics backend (which tools are used, how often, by which repo).  
    - Detect suspicious behavior (sequence of unusual shell commands) and alert or halt the session.

- ToolError (event name varies; docs describe error cases as separate branches of tool lifecycle)  
  - When: A tool fails with non-zero exit or error.[3][1]
  - Use cases:  
    - Fallback behavior: try a different tool, open a bug ticket, or roll back changes.  
    - Monitoring: send alerts for repeated failures of an MCP service or external API.

***

### Task and teammate events

Claude Code supports task tracking and teammates/agents; hooks fire around those events.[7][1][3]

- TaskCreated  
  - When: A task is being created (e.g., via a task command).[1]
  - Can block: Yes; hook can roll back creation.[1]
  - Use cases:  
    - Enforce task naming conventions (e.g., require JIRA ID prefix).  
    - Auto-enrich tasks with labels or owners based on content.  
    - Block task creation if it violates policy (e.g., no prod work on weekends).

- TaskCompleted  
  - When: A task is marked as completed.[1]
  - Use cases:  
    - Sync task completion back to external tools (JIRA, Linear, Trello).  
    - Trigger code cleanups or documentation generation when tasks close.

- TeammateIdle  
  - When: A “teammate” (separate agent) becomes idle.[5][1]
  - Can block: Yes; can prevent idle and keep working.[1]
  - Use cases:  
    - Keep a background agent continuously triaging TODOs or optimizing tests.  
    - Automatically shut down or park teammates after inactivity in corporate environments.

- SubagentStop  
  - When: A subagent (spawned agent) finishes responding.[5][1]
  - Can block: Yes; can prevent subagent from stopping.[1]
  - Use cases:  
    - Force verification agents to run extra checks before returning.  
    - Ensure multi-stage workflows (generate → verify → benchmark) complete before subagent exits.

***

### File / project / VCS related events

Some events fire when files or projects change; exact names vary across versions, but the pattern is documented in guides describing lifecycle coverage of editing and tooling.[7][3][1]

Examples (names approximate – check current hooks reference in your version):[3][1]

- FileChanged / WorkspaceChanged  
  - Use cases:  
    - Auto-run tests or static analysis when certain files change.  
    - Maintain “live summary” notes whenever large files are edited.

- BranchChanged / GitStatusChanged  
  - Use cases:  
    - Prevent risky operations on protected branches.  
    - Update environment variables or tools when moving between branches.

Because the official reference is versioned and expanding (some authors now count 26 events), treat any exact “23 events” list as version-specific rather than canonical.[5][7]

***

### Stop / control-flow events with special power

Docs highlight that some events can change course of execution via yes/no decision (prompt/agent hooks) or exit codes.[7][3][1]

Common high-leverage ones:[5][3][1]

- Stop  
- SubagentStop  
- TeammateIdle  
- PreToolUse  
- TaskCreated  

Use cases: building **deterministic guardrails** where an external script or AI policy must sign off before Claude proceeds.

***

## Installing Claude Code plugins that define hooks

FACT: Claude Code supports standalone config in `.claude/` and plugin-based distribution via plugin directories with `.claude-plugin/plugin.json`, where hooks live in `hooks/hooks.json` using the same schema as settings. Plugins are installed and managed via `/plugin` and marketplace commands.[8][2][4][1]

### 1. How plugin-based hooks are structured

- Plugin layout (simplified):  
  - `my-plugin/.claude-plugin/plugin.json` – plugin metadata (name, version, description).[2]
  - `my-plugin/hooks/hooks.json` – hook configuration (same `hooks` object schema as `.claude/settings.json`).[2]
  - `my-plugin/skills/…` – skills, if any.  
- Hooks inside `hooks.json` use the same structure as global/project hooks: event → matcher groups → handlers.[2][1]
  - Handler types:  
    - `command`: run a shell command, read JSON from stdin, return exit code / JSON decision.[3][1]
    - `prompt`: send a single-turn prompt to Claude for a yes/no or structured decision.[1]
    - `agent`: spawn a subagent with tools; experimental.[7][1]

This means you can prototype hooks in `.claude/settings.json` and later copy the `hooks` object directly into `my-plugin/hooks/hooks.json` to make them reusable.[2]

***

### 2. Installing plugins (with hooks) from a marketplace

To install community or team plugins that ship hooks:[4][8]

1. Add a plugin marketplace  
   - Use the slash command:  
     - `/plugin marketplace add owner/repository` – where `owner/repository` is typically a GitHub repo alias from docs.[8][4]
   - This registers a catalog of plugins that Claude Code can browse.

2. Browse and install plugins  
   - Run `/plugin` to open the plugin management UI.[4]
   - Choose something like “Browse Plugins” to see all available ones in your marketplaces.[4]
   - Select a plugin that advertises hooks (docs often mention “hooks” or “policies” in its description).  
   - Click to install, or use the CLI-line equivalent if provided (some guides show `/plugin install plugin-name`).[8][4]
   - Once installed, plugin hooks are immediately available in the session.[8][4]

3. Verify plugin hooks are active  
   - Run `/hooks` in Claude Code; this shows a consolidated view of hooks from global, project, and plugins.[2][1]
   - You should see entries with a source label corresponding to your plugin (e.g., `[Plugin: my-plugin]`) for events like `PreToolUse` or `Stop`.  
   - Optionally, open `my-plugin/hooks/hooks.json` via the editor or `Read` tool to inspect the exact config.

***

### 3. Managing plugins and their hooks

Once installed, you can enable/disable or remove plugins, which in turn adds or removes their hooks.[4][8]

- List installed plugins  
  - Run `/plugin list` to see all installed plugins and their status.[8]
  - Use the UI or CLI subcommands to see which are enabled.

- Enable or disable a plugin’s hooks  
  - `/plugin enable plugin-name` – activates its agents, skills, and hooks.[8]
  - `/plugin disable plugin-name` – turns them off (hooks will no longer fire).[8]
  - This is the coarse-grained switch for all hooks in that plugin.

- Uninstall a plugin  
  - `/plugin uninstall plugin-name` – removes the plugin entirely, including its hook definitions.[8]

- Team-level / repo-level workflow  
  - You can define marketplaces and plugins in `.claude/settings.json` at the repo level so a trusted repo auto-installs them for teammates.[4][2]
  - Steps:  
    - Add marketplace and plugin configuration to the repo’s `.claude/settings.json`.[4]
    - Teammate “trusts” the repo folder in Claude Code.  
    - Claude Code then installs required plugins automatically, giving everyone the same hooks and policies.[4]

***

### 4. Converting local hooks into a plugin

Docs explicitly describe migrating hooks from standalone settings into a plugin.[2]

- Start with hooks defined in `.claude/settings.json` or `.claude/settings.local.json` (project or user level).[2]
- Create a plugin directory, e.g., `my-plugin/`, with:  
  - `.claude-plugin/plugin.json` – basic metadata.  
  - `hooks/hooks.json` – new file.  
- Copy the `hooks` object from your settings file into `my-plugin/hooks/hooks.json` (schema is identical).[2][1]
- Install or load the plugin (for local dev, this can be a local plugin path depending on your setup), and disable the original hooks in settings to avoid duplication.[2]

This setup lets you version and share hook policies across projects or teams rather than copy-pasting JSON.

***

### 5. Practical pattern: auditing plugin hooks

Because hooks can be powerful (e.g., blocking tools), it’s worth auditing plugin hooks:

- Use `/hooks` to list all events and handlers, including those contributed by plugins.[1]
- For each plugin entry, open `hooks/hooks.json` to check:  
  - Which events are hooked (PreToolUse vs Stop vs SessionStart).  
  - Whether handlers are `command`, `prompt`, or `agent`.  
  - Whether they can block (e.g., PreToolUse with a blocking decision).[3][1]
- In corporate or sensitive environments, keep security-critical policies in a first-party plugin you control and treat community plugins as untrusted unless reviewed.

***

If you tell me your top workflows (e.g., “enforce shell safety” vs “auto-run tests” vs “session telemetry”), I can sketch concrete `hooks.json` snippets and a minimal plugin layout tailored to those.  

## Human

What are great examples of type: prompt and type: agent that people enjoy outcomes from.

## Assistant

Prompt hooks shine when the hook input alone is enough to decide “ok or not,” while agent hooks are loved for doing deep, tool-using verification (tests, security, specs) before letting Claude move on. Below are patterns people consistently report as high‑ROI, with concrete examples you can adapt directly.[1][2][3][4]

***

## High‑value `type: "prompt"` hook patterns

CONSENSUS: Prompt hooks route the decision to a fast Claude model in a single turn, returning `{ "ok": boolean, "reason": string }` based on your instructions and the hook’s JSON input (injected via `$ARGUMENTS`).[2][4][1]

### 1. “Is this operation safe?” (PreToolUse / Shell guard)

**Goal:** Let Claude run shell commands freely, but block obviously dangerous ones without writing shell scripts.

Use case people like: a PreToolUse prompt hook that reviews shell commands, git operations, and HTTP calls for safety.[4][1][2]

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "match": { "tool": ["Shell"] },
        "hooks": [
          {
            "type": "prompt",
            "model": "claude-3-haiku",
            "prompt": "You are a safety reviewer for shell commands.\n\n\
Here is the JSON description of the requested tool call:\n$ARGUMENTS\n\n\
Decide if this command is safe to run in a typical development environment.\n\
Block commands that:\n- delete or overwrite large parts of the filesystem (e.g. rm -rf /, sudo rm -rf .)\n\
- modify system-level config, package managers, or dotfiles not in the project\n\
- exfiltrate secrets (env vars, SSH keys, cloud credentials)\n\
- run network tools against unknown hosts for scanning.\n\n\
Respond with JSON:\n{\"ok\": true/false, \"reason\": \"short explanation\"}",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Why people like it:  
- You don’t maintain a regex blacklist; the LLM reasons about intent.[1][4]
- It catches subtle variants (e.g., `find . -delete`) better than naive pattern matching.[4]

***

### 2. “Is this change aligned with our policy?” (Stop / TaskCreated)

**Goal:** Lightweight policy engine for code quality or process rules.

Common pattern: use prompt hooks on `Stop` or `TaskCreated` to enforce internal guidelines.[5][2][1]

Example: **block task creation that bypasses ticketing rules**

```jsonc
{
  "hooks": {
    "TaskCreated": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You review whether a development task follows our process.\n\n\
Task details:\n$ARGUMENTS\n\n\
Rules:\n- The title must contain a JIRA key like ABC-123.\n\
- The description must mention acceptance criteria.\n\n\
Return JSON {\"ok\": true/false, \"reason\": \"short\"}. \
false if rules are broken."
          }
        ]
      }
    ]
  }
}
```

Why people enjoy it:  
- It nudges team behavior without heavy automation.  
- The “reason” field doubles as coaching text in the UI.[1][4]

***

### 3. “Is this PR / change ready?” (PostToolUse / Stop)

Popular blog examples: use prompt hooks to do semantic checks on diffs, commit messages, or test logs without running more tools.[3][4]

Example: **enforce good commit messages before stopping**

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are a code review assistant checking commit message quality.\n\
You receive details of the latest commit and summary:\n$ARGUMENTS\n\n\
Approve only if the commit message:\n- is imperative (\"Add X\", not \"Added X\"),\n\
- explains why, not just what,\n\
- references an issue ID.\n\n\
Return {\"ok\": true/false, \"reason\": \"brief\"}."
          }
        ]
      }
    ]
  }
}
```

Outcome users like: gentle but persistent pressure toward better hygiene, with very little config.[4]

***

### 4. Red‑team / content guardrail on `UserPromptSubmit`

Some guides and repos show prompt hooks on `UserPromptSubmit` to pre‑filter user instructions for security or compliance.[6][7]

Example: **flag sensitive instructions before Claude sees them**

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "model": "claude-3-haiku",
            "prompt": "Classify the following user prompt for security risk:\n$ARGUMENTS\n\n\
If it requests secrets, credentials, or exfiltration of private data, set ok=false.\n\
Otherwise ok=true.\n\
Return {\"ok\": true/false, \"reason\": \"short\"}."
          }
        ]
      }
    ]
  }
}
```

People like the UX: you get an immediate “this seems risky because…” explanation rather than a silent block.[7][4]

***

## High‑value `type: "agent"` hook patterns

FACT: Agent hooks spawn a subagent (`type: "agent"`) that can use tools like Read, Grep, Glob, Shell, and MCP before returning `{ "ok", "reason" }`. They run longer (default ~60s, multiple tool-use turns) and are treated as experimental in docs.[2][3][1]

### 1. “Don’t stop until tests actually pass” (Stop)

The official docs give a canonical example: a `Stop` agent hook that runs tests and only allows Claude to stop when the suite is green. This is one of the most consistently praised patterns.[2][1]

Minimal version (you’d usually make the prompt more tailored):

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are a verification agent.\n\n\
Goal: Only allow stopping if the test suite passes.\n\
- Use Shell and Read tools as needed.\n\
- Run the project's test command (e.g., `npm test`, `pytest`, or `cargo test`).\n\
- Inspect the results and error output.\n\n\
If tests all pass, return {\"ok\": true, \"reason\": \"All tests passed\"}.\n\
Otherwise, return {\"ok\": false, \"reason\": \"Describe failing tests briefly\"}.\n\n\
Hook input:\n$ARGUMENTS",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

Why people love it:  
- It enforces TDD-ish discipline without you remembering to run tests.  
- Claude can fix failing tests and re‑run them automatically, because the agent has tools.[3][1]

***

### 2. “Check that changes match the spec” (Stop / SubagentStop)

Pattern from guides: an agent hook that verifies implementation against a spec file or ticket before allowing completion.[5][3][1]

Example: **Stop hook to enforce spec conformance**

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are a spec compliance reviewer.\n\n\
Steps:\n\
1. Read the relevant spec file(s) from docs/ or SPEC.md.\n\
2. Inspect the changed files (use Grep/Glob/Read) based on the hook input.\n\
3. Verify that the implementation matches the spec requirements.\n\
4. Check for missing tests or docs if the spec requires them.\n\n\
If the implementation matches the spec, tests/docs are acceptable, \
return {\"ok\": true, \"reason\": \"Spec satisfied\"}.\n\
Otherwise return {\"ok\": false, \"reason\": \"What is missing or wrong\"}.\n\n\
Hook input JSON:\n$ARGUMENTS",
            "timeout": 240
          }
        ]
      }
    ]
  }
}
```

Outcome: Claude self‑polices against a canonical spec, which devs report as especially useful for complex flows or regulated domains.[3][5]

***

### 3. “Security gate on dangerous operations” (PreToolUse)

Security‑guided workflows often use agent hooks on PreToolUse to run deeper checks than a prompt hook can.[8][3]

Example: **agent hook for security review of infra changes**

```jsonc
{
  "hooks": {
    'PreToolUse': [
      {
        "match": { "tool": ["Shell"] },
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are a security review agent for infrastructure commands.\n\n\
Input JSON describes a requested tool call:\n$ARGUMENTS\n\n\
Tasks:\n- Use Grep/Read to inspect infra/ and deploy/ directories.\n\
- Determine if this command modifies production infrastructure or secrets.\n\
- Check for references to live clusters, production databases, or secret stores.\n\n\
If the command is safe for a dev environment and not production-critical, \
return {\"ok\": true, \"reason\": \"safe\"}.\n\
If it appears to affect production or secrets, return {\"ok\": false, \"reason\": \"why\"}.",
            "timeout": 90
          }
        ]
      }
    ]
  }
}
```

Why people enjoy it:  
- It’s “just enough” security without blocking all shell usage.  
- The agent can inspect project structure, config, and even past commands before deciding.[8][3]

***

### 4. “Don’t let teammates go idle until backlog is drained” (TeammateIdle)

Some multi‑agent setups use `TeammateIdle` agent hooks to keep background teammates busy triaging TODOs, issues, or documentation.[9][2]

Example: **keep doc teammate working until no TODOs remain**

```jsonc
{
  "hooks": {
    "TeammateIdle": [
      {
        "match": { "teammate": ["doc-bot"] },
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are a documentation teammate that should only go idle \
when there are no TODO comments left.\n\n\
Use Grep and Read:\n- Search the codebase for TODO/FIXME comments.\n- If any remain, pick one and improve docs or inline comments.\n\n\
If there are no TODOs/FIXMEs left, return {\"ok\": true, \"reason\": \"No TODOs\"}.\n\
If there is still work to do, return {\"ok\": false, \"reason\": \"Remaining TODOs\"}.\n\n\
Hook input:\n$ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

Users like the feeling of “background continuous improvement” while they focus elsewhere.[9]

***

## When to choose `prompt` vs `agent`

FACT: Docs explicitly recommend prompt hooks when the hook input JSON is enough, and agent hooks when verification requires tools or code inspection.[1][2][3][4]

- Use **prompt hooks** when:  
  - You’re making semantic judgments without needing to read the repo (safety of a command, quality of a description, presence of keywords).[4][1]
  - Latency matters; these tend to be fast and cheap.  
- Use **agent hooks** when:  
  - You must read files, run tests, or use MCP tools to decide.  
  - You want multi‑step reasoning and retries before allowing or blocking an action.[2][3][1]

My confidence in these patterns is high: they’re directly aligned with the official hooks guide plus multiple independent blog posts and repos discussing “favorite” hooks (TDD enforcement, safety gates, spec checking).[9][3][1][2][4]

If you tell me your top 1–2 priorities (safety, TDD discipline, spec compliance, multi‑agent flows), I can distill these into a single `.claude/settings.json` or plugin `hooks/hooks.json` tailored to your stack.  

## Human

Pleaes review the doc.  How do you think prompt and agent type hooks can improve results?

## Assistant

Prompt and agent hooks are exactly the levers you need to get closer to “works, not brittle, and I’m happy” given what you lay out in the doc. Used well, they let you move most of the epistemic/formatting work **upstream** (before Stop) and turn a bunch of today’s noisy, repetitive Stop gates into quieter, more focused checks. I’ll focus on concrete, high‑impact patterns that plug directly into your existing architecture.[1]

I’ll assume this context as FACT from your doc:  
- You cannot get a truly silent, blocking Stop hook; block reasons are user‑visible.[1]
- You are already running 30+ in‑process “gates” out of Stop.py, with POLICY vs QUALITY classes, and you’re suffering from repetition loops and instruction hijacking.[1]
- You want: control turns respected, fewer visible gates, more reliable epistemic behavior (STATUS, FACT/INFERENCE, etc.) with less friction.[1]

***

## 1. What prompt hooks can take off Stop’s plate

Prompt‑type hooks give Claude a one‑shot decision or guidance pass based on JSON input for the hook, but without tools. In your world, they’re ideal for:[2][3]

- shaping the system prompt at **UserPromptSubmit**  
- doing single‑shot classifications you currently over‑encode as gates  
- producing advisory system messages instead of full Stop decisions

### 1.1. Move ADVOCATEPROTOCOL injection into a prompt hook

Right now, your doc’s conclusion is “make STATUS/ADVOCATEPROTOCOL part of the default instructions for analytical turns via UserPromptSubmit, not Stop.” A `type: "prompt"` hook on `UserPromptSubmit` is a clean way to implement that without more hand‑coded heuristics.[1]

Pattern:

- Event: `UserPromptSubmit`  
- Hook: `type: "prompt"`  
- Input: Hook gets the user’s raw text and possibly a few bits of state (recent turns, whether we’re already in a “topic”).[1]
- Prompt behavior:
  - Classify the turn as control vs analysis vs chit‑chat (using the heuristics you’ve been sketching in prose).  
  - Decide whether to inject ADVOCATEPROTOCOL / STATUS instructions.  
  - Return JSON `{ "inject_protocol": true/false, "reason": "...", "mode": "light|full" }`.

Why this helps:

- You stop encoding all the “is this analytical?” logic as Python if/else; the LLM does the fuzzy bits.[1]
- ADVOCATEPROTOCOL becomes **proactive**: for most analysis/facty turns, the model starts with the right contract, so Stop doesn’t need to nag about format afterward.[1]
- You can differentiate “light” protocol (only STATUS labeling) from “full” protocol (strict four‑section schema) based on the hook’s decision.

This directly implements what you already conclude in the doc as the optimal direction: protocol in UserPromptSubmit, Stop only as a backstop.[1]

### 1.2. Use prompt hooks as lightweight policy routers instead of more Stop gates

You have many quality/policy distinctions that are currently implemented as separate in‑process gates with custom thresholds and branching. Several could be turned into a **single prompt hook that returns a multi‑field verdict**, which Stop then interprets.[1]

For example, instead of:

- `comparative_claim_guard`  
- `lazy_workaround_gate`  
- `recommendation_gate`  

all separately deciding about “is this a claim; is it justified; is it a lazy heuristic; does it mention downsides?”, you can:

- Event: `Stop` or `PostToolUse`  
- Hook: `type: "prompt"`  
- Prompt: “Given this assistant message and brief context JSON, analyze: Did the model make a comparative recommendation? Did it state criteria, assumptions, downside, alternative, falsification? Return a structured verdict.”

Hook returns one JSON object that you convert into your standardized `GateVerdict` shape.[1]

Benefits:

- You get the multi‑dimensional “recommendation rubric” you want (criterion, assumption, downside, best alternative, falsification) without adding yet another Python gate.[1]
- In warn mode, you can log this verdict as telemetry only, not touch system messages—exactly the “silent warn” behavior you sketched as a goal.[1]
- It’s easier to evolve criteria in one prompt than in multiple gate modules.

### 1.3. Prompt hooks as advisory self‑check before Stop sees the output

You explicitly want a “pre‑commit reflection gate” that runs **before** Stop and checks a few core things: did we verify when we said we did, did we mark unknowns, did we calibrate language.[1]

Instead of wiring this as another in‑process gate:

- Event: a pre‑Stop hook (or a separate Stop hook configured to run before your big gate fan‑out).  
- Hook: `type: "prompt"`.  
- Prompt: feed the assistant’s draft answer and a compact rubric: “Check this answer for: (1) explicit unknowns, (2) evidence vs inference labeling, (3) at least one concrete downside / failure mode. Return JSON: {unknown_ok, labeling_ok, downside_ok, message}.”

Then:

- In **normal/warn** mode, you take the JSON and, if something is missing, add a single advisory system message for the **next** turn (“In future answers, remember to mark unknowns explicitly.”), without blocking.[1]
- In strict/epistemic mode, you could treat “labeling_ok = false” as a Stop‑gate block, but only when the user opted into that mode.

This aligns with your doc’s direction: reflection and rubric enforcement, but not as always‑blocking Stop cops.[1]

***

## 2. What agent hooks can do that prompt hooks can’t

Agent‑type hooks get tools, multiple steps, and time; they’re ideal for the few things that legitimately **must** be expensive and heavyweight. Your doc already calls out three clear candidates: tests, spec alignment, and high‑risk actions.[3][2][1]

### 2.1. Agent Stop hook: “Don’t stop until tests actually passed”

This is very close to the canonical example in the official hooks guide, and it maps 1:1 to your desire for “verification before guidance” when cheap checks exist.[4][2][1]

Pattern:

- Event: `Stop`  
- Hook: `type: "agent"`  
- Prompt:  
  - Use Shell/Read/etc. to run tests (or targeted suites based on diff).  
  - If tests pass, return `{ "ok": true, "reason": "All tests passed" }`.  
  - If tests fail, optionally try a quick fix or at least return `{ "ok": false, "reason": "Which tests failed" }`.

Integration with your architecture:

- In strict mode for certain repos/skills, treat `ok=false` as a real Stop block: user sees “cannot finish, tests failing; here’s why,” and the model keeps iterating.[1]
- In normal/warn mode, treat `ok=false` as advisory only or log it, depending on how much friction you accept.

Why this improves results:

- It’s exactly the kind of **non‑brittle** gate you wanted: it checks something objective (test exit codes), doesn’t care about prompt subtleties, and only fires when it matters.[1]
- Users tolerate visible friction here because “tests failing” is meaningful, unlike “missing STATUS header again.”[1]

### 2.2. Agent Stop or SubagentStop hook: “Check code vs spec”

You talk a lot about wanting recommendations and changes tied back to actual requirements/specs instead of free‑floating heuristics. An agent hook with tools can:[1]

- Read `SPEC.md` / `docs/` for the relevant feature.  
- Inspect changed files via `Read/Grep/Glob`.  
- Check whether core requirements in the spec are implemented, or at least mentioned in the answer.

Pattern:

- Event: `Stop` or `SubagentStop` for a particular “implementation” teammate.  
- Hook: `type: "agent"`.  
- Prompt:  
  - Identify spec files and changed files.  
  - For each spec requirement, check if there’s obvious code/tests that relate.  
  - Return `{ ok, reason, missing_requirements: [...] }`.

Use it in strict epistemic mode only; in everyday development you log and maybe show a small advisory, but don’t block unless the user specifically requested spec‑driven work.[1]

This directly supports your goal of “epistemic rigor where it matters, not everywhere.”[1]

### 2.3. Agent PreToolUse hook: “Security or infra gate on dangerous commands”

Your doc treats safety/deletion/secret‑related gates as POLICY: allowed to override control turns. Agent hooks are a good match for serious, expensive checks:[1]

- Event: `PreToolUse` on `Shell`, infra MCPs, or anything that can change prod.  
- Hook: `type: "agent"`.  
- Prompt:  
  - Use `Read/Grep` to inspect infra configs, environment hints, branch, etc.  
  - Analyze the requested command for signs of prod impact or secret exfiltration.  
  - If suspicious, return `{ "ok": false, "reason": "Why this looks like prod" }`.

Why this fits better than a pure prompt gate:

- It can actually inspect the repo/config instead of guessing from the command string.  
- It’s clearly POLICY: when this fires, visible friction is acceptable, matching your own distinction between POLICY and QUALITY gates.[1]

***

## 3. How these hooks reduce brittleness in your specific system

Your doc identifies three main brittleness sources:[1]

1. Using Stop as the primary formatting/epistemic cop → tons of visible “EPISTEMIC FORMAT REPAIR” messages and loops.  
2. Quality gates injecting systemMessages on control turns, hijacking user corrections.  
3. Warn mode that is not actually “silent”: it still mutates the instruction stack.

Prompt and agent hooks help here if you use them to **move the work out of Stop** and change what Stop is for:

- Prompt hooks at `UserPromptSubmit` and early in the response lifecycle:
  - Handle schema/protocol shaping and light classification.  
  - Don’t block; instead, alter instructions before generation or emit telemetry only.  
  - This means most answers are already closer to your desired format; Stop rarely needs to complain.

- Agent hooks at `Stop` / `PreToolUse`:
  - Handle the few things that truly warrant heavy enforcement (tests, specs, dangerous commands).  
  - Run as POLICY gates in your own terms: allowed to block and visible when they do.

Then you adjust Stop’s in‑process gates:

- Narrow QUALITY gates so that in **normal/warn** mode they log or at most add tiny advisory metadata, but do not inject big systemMessages or block.[1]
- Let POLICY gates stay, but with clearer scope: secrets, deletion, infra, maybe really egregious epistemic cheating.

The net effect for you as the user:

- Fewer visible hook messages; when you see one, it’s for something obviously important (tests failed, dangerous command, etc.).  
- Control turns (“no, stop, do X instead”) are respected because most QUALITY behavior has moved to earlier prompt hooks or is silent in warn mode.  
- The overall epistemic quality still improves, because you’ve added proactive contracts, reflection, and a few heavyweight agent checks where they actually help.

***

## 4. Concrete “first two hooks” I’d add to your current system

If you want an actionable starting point that doesn’t explode scope, I’d prioritize:

1. **UserPromptSubmit prompt hook: ADVOCATEPROTOCOL / STATUS injector**
   - Input: user message + maybe recent history.  
   - Output: `{ inject_protocol: bool, mode: "light"|"full" }`.  
   - Action: When true, prepend the appropriate ADVOCATEPROTOCOL / STATUS instructions to the system prompt for that turn.

2. **Stop agent hook: test‑enforcement gate (strict mode only)**
   - Input: assistant’s draft + repo context.  
   - Behavior: run tests, decide `ok`, return reason.  
   - Integration:
     - In strict mode for chosen projects: treat `ok=false` as Stop block.  
     - In normal mode: just log; don’t block.

These two alone will:

- Cut a large fraction of your current “format enforcement via Stop” friction.  
- Give you one agent hook that obviously improves real‑world reliability without touching your existing 31 gates yet.

Once those are in place, you can gradually:

- Convert some of the current Python QUALITY gates into either:
  - prompt hooks that feed verdicts into your standardized GateVerdict, or  
  - no‑op telemetry in normal mode, strict only when explicitly enabled.

***

Would you like a concrete JSON `hooks.json` snippet for those two starter hooks (UserPromptSubmit prompt hook + Stop test agent hook) tailored to your STATUS/ADVOCATEPROTOCOL setup so you can just paste it into a dev project and iterate from there?  

## Human

please check github issues for claude code v2.1.126 to see if there are existing problems that will make you change your recommendation.

## Assistant

No, I do not change my core recommendation after reviewing v2.1.126 issues and changelogs—prompt/agent hooks on `UserPromptSubmit` (for proactive shaping) and `Stop`/`PreToolUse` (for heavyweight verification) remain the optimal way to reduce your Stop gate friction while enforcing epistemic rigor. The issues highlight specific pitfalls to avoid (mostly plugin‑related `UserPromptSubmit` flakiness), but nothing blocks the patterns for local/project `.claude/settings.json` hooks, and recent fixes strengthen `Stop`/`PreToolUse` reliability.[1][2][3][4][5][6][7][8]

## Key v2.1.126 findings and their impact

I searched GitHub issues, changelog, Reddit, and docs for v2.1.126 (April 2026 release) specifically around hooks, `UserPromptSubmit`, `Stop`, `PreToolUse`. Here's what matters:[2][3][4][5][6][9][10][11][7][12][13][14][1]

### Confirmed issues (avoidable for your setup)
- **UserPromptSubmit flakiness**:  
  - Plugins: Hooks match but don't execute (e.g., #10225, #9708); use local `.claude/settings.json` instead—no issues reported there.[12][2]
  - Git worktrees: Hooks silently skip in some sessions (#49989)—test in your multi‑worktree workflow, fallback to project `.claude/settings.local.json` if needed.[3]
  - Intermittent firing (#37988, #17284, #16952)—mostly pre‑v2.1.126; recent reports show fixes on Windows/Mac, but verify with `--debug` logs.[4][9][13]
  - Stdout/JSON quirks (#13912, #17550, #17804)—prompt hooks must be precise (JSON only to stdout, no extra text); agent hooks less affected.

- **Impact**: Stick to **local/project settings** (not plugins) for now; these patterns work reliably there per docs and non‑plugin reports.[2][3]

### Fixes and improvements (strengthen my recs)
- **PreToolUse/Stop enhancements** (v2.1.126 and recent):  
  - Fixed JSON exit code 2 blocking, prompt‑type Stop handling `ok:false`, format‑on‑save races.[7]
  - `PostToolUse` can now replace tool output broadly (not just MCP).[5]
  - `defer` permission in PreToolUse for headless re‑eval—great for CI/safety gates.[7]

- **New**: `PreCompact` hooks (blocks context compaction)—niche, but shows hook ecosystem maturing.[10]

- **No breaking changes**: No deprecations to `UserPromptSubmit`/`Stop` semantics; `suppressOutput` still doesn't enable silent Stop (consistent with your doc).[8][7]

- **Unrelated noise**: Hook approval bugs (#), env vars, UI flicker—irrelevant to your gate/epistemic goals.[6][1][7]

## Adjusted recommendations (minor tweaks only)

1. **UserPromptSubmit prompt hook (ADVOCATEPROTOCOL injector)**:  
   - **Still recommended**: Perfect for proactive epistemic shaping; use **project `.claude/settings.json`** or `settings.local.json` to sidestep plugin/worktree bugs.[3][2]
   - **Tweak**: Add `--debug` during testing; ensure pure JSON stdout (no debug prints). Watch for intermittent firing—duplicate as a fallback `Notification` hook if needed.[11][4]
   - **Confidence**: High for local configs; aligns with fixed intermittent issues.[4]

2. **Stop agent hook (tests/spec)**:  
   - **Still recommended**: Recent fixes make agent `ok:false` more reliable; no regressions noted.[7]
   - **Tweak**: Use `timeout: 180` explicitly; leverage new `defer` if tying to PreToolUse.

3. **PreToolUse agent/prompt (safety/infra)**:  
   - **Even stronger**: Fixed blocking semantics and output replacement—ideal for POLICY gates.[5][7]

4. **Overall architecture**: Your doc’s shift to “upstream via UserPromptSubmit, Stop as backstop” is unchanged and validated—no v2.1.126 issues contradict it.[8]

## Concrete next step: Test‑safe starter hooks

Here's a `hooks.json` snippet for your `.claude/settings.local.json` (safe from plugin issues) implementing the two starters. Test in a non‑worktree first.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Inject ADVOCATEPROTOCOL for analytical turns",
        "hooks": [
          {
            "type": "prompt",
            "model": "claude-3-5-sonnet-20241022",  // Or haiku for speed
            "prompt": "Classify user message: $ARGUMENTS\n\nIs this analytical/factual (inject full STATUS/ADVOCATEPROTOCOL)? Control/steering (no inject)? Return JSON: {\"inject\": true/false, \"mode\": \"light|full\", \"reason\": \"brief\"}",
            "timeout": 8
          }
        ]
      }
    ],
    "Stop": [
      {
        "description": "Verify tests pass before stopping",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Draft: $ARGUMENTS\n\nRun tests (npm test/pytest/etc.). If all pass: {\"ok\":true}. Else {\"ok\":false, \"reason\": \"Failures\"}. Use Shell/Read.",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

**Validate**: `claude --debug`, submit prompts, check `/hooks` output and logs. If UserPromptSubmit skips, move to global `~/.claude/settings.json`.[2][3]

No fundamental changes needed—v2.1.126 issues are narrow and avoidable. Ready for the full hooks.json with your STATUS rubric?

## Human

yes please

## Assistant

Here's the full `hooks.json` snippet tailored to your STATUS/ADVOCATEPROTOCOL setup from the doc—paste directly into `.claude/settings.local.json` or a plugin's `hooks/hooks.json` (avoid marketplace plugins due to v2.1.126 bugs). It implements the two starters (UserPromptSubmit prompt for proactive injection, Stop agent for test verification) with your epistemic contract baked in.[1][2][3]

## Full hooks.json for your epistemic guardrails

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Proactive ADVOCATEPROTOCOL / STATUS injector",
        "match": { "matcher": "always" },
        "hooks": [
          {
            "type": "prompt",
            "model": "claude-3-5-sonnet-20241022",
            "prompt": "Analyze this user message JSON: $ARGUMENTS\n\nClassify turn:\n- CONTROL: short imperative (\"stop\", \"no\", \"do X instead\", \"re-read\", <200 chars, steering).\n- ANALYTICAL: analysis, compare, evaluate, facts, claims, recommendations.\n- OTHER: chit-chat, simple Q&A.\n\nDecide:\n- inject: true if ANALYTICAL (false for CONTROL).\n- mode: \"light\" (STATUS labels only) or \"full\" (strict 4-section schema + rubric).\n\nReturn **exact JSON** (no extra text):\n{\n  \"inject\": true/false,\n  \"mode\": \"light|full\",\n  \"reason\": \"1 sentence\"\n}",
            "timeout": 8,
            "suppressOutput": true
          }
        ]
      }
    ],
    "Stop": [
      {
        "description": "Epistemic backstop + test verification (strict mode)",
        "match": { "matcher": "always" },
        "hooks": [
          {
            "type": "agent",
            "prompt": "You verify before final answer. Draft response: $ARGUMENTS\n\n**Phase 1: Quick epistemic check**\n- Does it use STATUS (FACT/INFERENCE/UNKNOWN/RECOMMENDATION)?\n- Calibrated claims? Evidence or explicit unknowns?\n- Recommendations disclose: criteria, assumptions, downside, best alternative, falsification?\n\n**Phase 2: Run tests if applicable**\n- Detect test suite (npm test/pytest/cargo test/go test).\n- Use Shell to run; check exit code/output.\n\n**Decide:**\n- ok=true if epistemic ok AND tests pass (or no tests).\n- ok=false + reason otherwise.\n\nTools: Shell, Read, Grep. Return **JSON only**:\n{\n  \"ok\": true/false,\n  \"reason\": \"brief explanation\",\n  \"epistemic_issues\": [\"list\"],\n  \"test_status\": \"pass|fail|none\"\n}",
            "timeout": 180,
            "suppressOutput": true
          }
        ]
      },
      {
        "description": "Safety POLICY gate (always blocks)",
        "match": { "matcher": "always" },
        "hooks": [
          {
            "type": "prompt",
            "model": "claude-3-haiku",
            "prompt": "Review draft for POLICY violations: $ARGUMENTS\n\nBlock if: secrets/creds exfil, rm -rf/destructive, prod infra changes, bulk deletion.\n\nJSON: {\"ok\": true/false, \"reason\": \"brief\"}",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "description": "Shell/infra safety (POLICY)",
        "match": { "tool": ["Shell"] },
        "hooks": [
          {
            "type": "agent",
            "prompt": "Command JSON: $ARGUMENTS\n\nInspect repo (Read/Grep .env infra/ deploy/). Block if: prod impact, secrets touch, sudo/system mods.\n\nJSON: {\"ok\": true/false, \"reason\": \"why\"}",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## How this integrates with your doc's architecture

| Hook | Addresses doc pain point | Behavior |
|------|---------------------------|----------|
| **UserPromptSubmit prompt** | "Move protocol to upstream; Stop as backstop" [1] | Injects STATUS/ADVOCATEPROTOCOL **before** generation; respects CONTROL turns (no inject); light/full modes match your strict/warn. |
| **Stop agent (epistemic + tests)** | "Pre-commit reflection + rubric enforcement" [1] | Runs your 5-part rubric (criteria/assumptions/downsides/etc.) + tests; only blocks in strict mode implicitly (via ok=false). |
| **Stop prompt (safety)** | POLICY gates override everything [1] | Fast, always‑on safety; visible blocks OK. |
| **PreToolUse agent** | "Safety before dangerous actions" [1] | Repo‑aware shell guard; uses tools for context. |

**Key alignments**:
- **Silent by default**: `suppressOutput: true` hides debug noise; blocks only when `ok: false` (rare, meaningful).[1]
- **Control turn respect**: UserPromptSubmit skips inject on CONTROL; Stop focuses on objective checks (tests/epistemic facts), not schema nags.
- **Warn/strict modes**: Tune via `mode` in UserPromptSubmit output or env vars (e.g., `EPISTEMIC_MODE=strict` to treat Stop ok=false as hard block).
- **Telemetry‑ready**: JSON reasons/issues for logging; extend with a `Notification` hook later.

## Deploy and test steps

1. **Backup**: `cp .claude/settings.json .claude/settings.json.bak`
2. **Paste**: Add `"hooks": { ... }` to `.claude/settings.local.json` (worktree‑safe).[3]
3. **Validate syntax**: `claude --debug` → check `/hooks` lists them.
4. **Test sequence**:
   - Analytical query → see injected protocol (debug logs).
   - CONTROL ("stop, do X") → no inject.
   - Code change → Stop agent runs tests, blocks if fail.
   - Risky shell → PreToolUse blocks.
5. **Tune**: Adjust prompts/models/timeouts; watch for UserPromptSubmit intermittency (fallback to global settings).[4]

This gets you 80% of your doc's "reduced Stop strategy" with minimal code—iterate prompts first, then wire into your GateVerdict aggregator. Issues? Share debug output.[1]

## Human

That model name is obsolete for type prompt. Isn't there some way to use the default?

## Assistant

Yes. For `type: "prompt"` hooks you can omit the `model` field entirely and Claude Code will use its default fast model (currently Haiku‑class), so you don’t need to track specific model names.[1][2][3]

From the hooks reference:

- `model` is **not required** for prompt hooks.[1]
- If you leave it out, Claude Code “defaults to a fast model” (the docs and multiple guides say Haiku by default).[2][3][1]

So for your config, just drop the `model` line on prompt hooks, like:

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Proactive ADVOCATEPROTOCOL / STATUS injector",
        "match": { "matcher": "always" },
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Analyze this user message JSON: $ARGUMENTS\n\nClassify turn:\n- CONTROL: short imperative (\"stop\", \"no\", \"do X instead\", \"re-read\", <200 chars, steering).\n- ANALYTICAL: analysis, compare, evaluate, facts, claims, recommendations.\n- OTHER: chit-chat, simple Q&A.\n\nDecide:\n- inject: true if ANALYTICAL (false for CONTROL).\n- mode: \"light\" (STATUS labels only) or \"full\" (strict 4-section schema + rubric).\n\nReturn exact JSON:\n{\n  \"inject\": true/false,\n  \"mode\": \"light|full\",\n  \"reason\": \"1 sentence\"\n}",
            "timeout": 8,
            "suppressOutput": true
          }
        ]
      }
    ]
  }
}
```

And similarly, for the safety Stop prompt hook you can remove `model` and let it use the default fast model.[2][1]

You should still keep explicit `model` on **agent** hooks if you care which model powers the sub‑agent, because the agent‑hook bugs/issues mention misconfigurations when model/messages are implicit. For pure prompt hooks, defaulting is exactly what the docs recommend.[4][1]

Do you want me to regenerate the full `hooks.json` you’re testing with all prompt hooks using the implicit default model and only agent hooks specifying a model?  

## Human

what prompt do you need the target LLM to answer, in order to identify where type: prompt and type: agents can objectively result in a better soution?  You should consider software best pracices like DRY, complexity, performance, simplicity, etc.

## Assistant

You want a meta‑prompt: something you give to the *target* LLM (inside Claude Code) so it can tell you **where** to use `type: "prompt"` vs `type: "agent"` hooks in a way that’s objectively better (DRY, low complexity, good performance, simple, maintainable). Here’s a prompt you can drop into Claude Code to do exactly that.

***

## Single prompt for the target LLM

Use this as a system or high‑level user prompt when asking Claude to design or refactor your hooks:

```text
You are designing Claude Code hooks for this project.

Goal:
Identify WHERE hook-based automation will objectively improve the system
compared to doing the same logic inline in Python or in prompts, and decide
WHEN to use:
- type: "prompt" hooks
- type: "agent" hooks
- or NO hook at all

You must optimize for:
- DRY: avoid duplicated logic across gates, skills, and plugins
- Simplicity: few moving parts, easy to understand from hooks.json alone
- Performance: minimize latency and cost; avoid unnecessary agent runs
- Correctness: use hooks only where they can check something objective
- Robustness: avoid brittle, schema-policing Stop hooks that hijack control turns

Context you will be given:
- A description of the current hook architecture (Stop, PreToolUse, etc.)
- The domains we care about (epistemic rigor, safety, tests, spec alignment, etc.)
- Example transcripts or problems we want to fix

Your task:

1. Enumerate candidate behaviors
   Look at the described behavior and list concrete things we want the system to do
   that might be implemented via hooks. For each, give:
   - name
   - short description
   - what input signal it depends on (user prompt, draft answer, tool call, repo state)
   - how often it runs (every turn, only on certain tools, only on strict tasks)

2. Decide the mechanism for each candidate
   For each candidate behavior, decide ONE of:
   - INLINE: implement in core code / system prompts, no hook needed
   - PROMPT_HOOK: use type: "prompt" at a specific event
   - AGENT_HOOK: use type: "agent" at a specific event

   Use these rules:

   Prefer INLINE when:
   - Logic is simple, static, and always-on (e.g., a basic system prompt rule)
   - It doesn't need separate deployment/config (no per-project tuning)
   - It’s tightly coupled to one file/module already

   Prefer PROMPT_HOOK when:
   - Decision can be made from JSON hook input alone (no tools needed)
   - It’s semantic BUT light-weight: classification, routing, “should we inject X?”,
     “is this turn control vs analysis?”, “what mode should this session be in?”
   - Multiple gates or skills would otherwise duplicate the same logic
   - We want to tune/override it per project via hooks.json

   Prefer AGENT_HOOK when:
   - We must inspect code, files, tests, or external tools to decide
   - The check is expensive but high value: tests, spec compliance, security review
   - It is POLlCY-level: allowed to add latency and occasionally block visibly
   - It must run with tools (Read/Grep/Shell/MCP) and possibly multiple steps

3. Evaluate each choice against engineering constraints
   For each candidate, justify the decision explicitly in terms of:

   - DRY:
     Does using a hook centralize logic that would otherwise be duplicated?
   - Complexity:
     Does this add more moving parts (new gates, new prompts, more events)?
     Is there a simpler INLINE or PROMPT_HOOK alternative?
   - Performance:
     How often will it run? What is the worst-case latency cost?
     Could we restrict it to strict modes or specific events?
   - Simplicity of configuration:
     Can a teammate reason about this behavior just from hooks.json
     and a short comment, without reading Python?
   - Robustness:
     Is the behavior based on objective signals (tests, exit codes, presence
     of files) vs fragile heuristics (exact wording, schema policing)?
     Will it fight user control turns, or respect them?

   Output a table with columns:
   - behavior_name
   - event (UserPromptSubmit, Stop, PreToolUse, etc.)
   - choice (INLINE | PROMPT_HOOK | AGENT_HOOK)
   - rationale (short, focusing on DRY / complexity / performance / robustness)

4. Highlight the top 3–5 high-ROI hook candidates
   From your table, select the 3–5 behaviors where:
   - Hooks clearly beat INLINE code on DRY and configurability
   - Performance/complexity cost is reasonable
   - The behavior is objectively checkable (tests, specs, safety, etc.)

   For these, sketch:
   - event and hook type
   - what the hook sees in $ARGUMENTS
   - the exact decision JSON it should return (fields and types)
   - a one-sentence design note on how this reduces complexity overall

Important constraints:
- Do NOT recommend schema-enforcing Stop hooks that activate on every turn just
  to enforce formatting; those fail the simplicity and robustness criteria.
- Do NOT recommend agent hooks for anything that can be handled by a single
  model call without tools.
- Whenever you propose an AGENT_HOOK, explicitly justify why PROMPT_HOOK is
  not sufficient.
- Whenever you propose any hook, say what we would delete or simplify in the
  existing code/gate stack as a result (DRY).

Return your answer as:
1) A short prose overview (1–2 paragraphs)
2) The table of behaviors and choices
3) The 3–5 high-ROI hook sketches with their decision JSON
```

***

## Why this prompt will surface “objectively better” uses of prompt/agent hooks

- It forces the model to **compare hooks vs inline code**, not just sprinkle hooks everywhere. That’s how you respect DRY and complexity constraints.
- It encodes the right **division of labor**:
  - `type: "prompt"` = semantic, lightweight, no tools, often‑run logic.
  - `type: "agent"` = expensive, tool‑using, policy‑level verification.
- It demands explicit **trade‑off reasoning** (DRY, complexity, performance, robustness) per behavior instead of “hooks are cool, use them.”
- It requires the model to specify **what we can delete/simplify** in your current gate stack for each hook, which is the real DRY win.

If you paste this into Claude Code along with a brief description of your current hooks and goals (or the doc you shared), it should give you a prioritized list of where `prompt` and `agent` hooks actually improve the design rather than just adding more machinery.

Would you like a shorter, “drop‑in” variant of this prompt that assumes the model can read your `.claude/settings.json` and existing hook files directly and auto‑builds that behavior table from them?  
