---
title: "what files and directories might we find in a claude code .claude folder?"
date: "2025-12-13"
mode: "COPILOT"
uuid: "576c6579-42ed-478b-ab86-d41183ec0c44"
entry_count: 6
---

## Human

what files and directories might we find in a claude code .claude folder?

## Assistant

The `.claude` folder in a Claude Code project serves as a centralized location for configuration, memory, and rules that guide the AI during development tasks.[1][2]

## Core Files
CLAUDE.md provides main project instructions, such as architecture details, coding standards, and workflows; it can be created via the `/init` command and supports imports from other files using `@path` syntax.[3][1]
CLAUDE.local.md stores personal, non-version-controlled preferences specific to the project and is auto-added to `.gitignore`.[3]

## Rules Directory
The `.claude/rules/` subdirectory holds modular `.md` files for topic-specific guidelines, loaded automatically with the same priority as CLAUDE.md.[3]
Examples include `code-style.md` for formatting rules, `testing.md` for conventions, and `security.md` for requirements; files support YAML frontmatter for path-scoped rules using glob patterns like `src/**/*.ts`.[3]
Subdirectories within `rules/` (e.g., `frontend/react.md`) and symlinks to shared rules are discovered recursively.[3]

## Other Possible Contents
A `settings.json` file may configure personal preferences, as noted in user setups.[4]
User-level rules can exist in `~/.claude/rules/`, but project-specific ones stay local to `./.claude/`.[3]

## Human

and what for the project .claude?  skills?  plugins?  other?

## Assistant

The `.claude` folder in a Claude Code project expands beyond core files and rules to include skills and plugin-related elements for enhanced agentic capabilities.[2][1]

## Skills Directory
`.claude/skills/` contains subdirectories for project-specific Agent Skills, each with a `SKILL.md` file defining instructions, descriptions, and optional supporting files like scripts or templates.[1]
Skills activate autonomously based on task context matching their YAML frontmatter description, enabling specialized workflows such as PDF processing or code review.[3][1]
Supporting assets (e.g., `scripts/helper.py`, `templates/`) reside alongside `SKILL.md` and load via progressive disclosure.[2]

## Plugins Integration
Plugins bundle components into project `.claude/` via installation, including `skills/`, `commands/`, `agents/`, `hooks/`, and `.claude-plugin/plugin.json` for metadata.[4]
Project plugins extend Claude with custom slash commands (in `commands/`), subagents (in `agents/`), and event hooks (via `hooks/hooks.json`), auto-discovered on load.[6][7]
Global plugins or marketplaces feed into local `.claude/settings.json` for team consistency.[4]

## Additional Elements
`settings.json` configures plugin marketplaces, tool permissions, and preferences.[8]
`.mcp.json` defines MCP servers for external tools, sometimes copied into `.claude/` for project portability.[8]

## Human

Does this make sense?

Final .claude Protection Rules
Allowed Subdirectories:
DirectoryPurpose
commands/
Slash command stubs
hooks/
Runtime hooks
agents/
Subagent definitions
logs/
Runtime logs
skills/
Agent skills (SKILL.md + scripts)
rules/
Modular rule files (.md)
.claude-plugin/
Plugin metadata
Allowed Root Files:
FilePurpose
settings.json
Main config
settings.local.json
Local overrides
claude.md
Project instructions
claude.local.md
Personal instructions (gitignored)
.mcp.json
MCP server config
current_session.json
Session state
sessions.json
Session tracking
session_config.json
Session config
mutex_session.json
Mutex state
orchestrated_session.json
Orchestration state
hook_validation_results.json
Hook output
deliberate_hook_changes.jsonl
Hook tracking
.session_start_lock
Lock file
Blocked (triggers CLAUDE_DIRECTORY_VIOLATION):
projects/, tests/, data/, plans/, helpers/, proxy/
cache/, injection_cache/, backups/
Nested .claude/ or __csf.nip/
session_* directories (consolidate to allowed files)
Random files like *.md docs, pytest.ini, *.py scripts

## Assistant

Yes, this protection ruleset for the project `.claude` folder makes sense as a security hardening measure aligned with Claude Code's sandboxed design, which strictly confines writes to the working directory and subfolders while blocking risky operations.[1][2]

## Allowed Structure Matches Docs
Subdirectories like `commands/`, `hooks/`, `agents/`, `skills/`, and `rules/` directly correspond to official Claude Code components for slash commands, runtime hooks, subagents, Agent Skills (with `SKILL.md`), and modular rules.[3][4]
Root files such as `settings.json`, `claude.md` (and `.local.md`), and `.mcp.json` reflect documented configs for preferences, instructions, and MCP servers.[5][3]
Session-related files (`current_session.json`, `sessions.json`, etc.) and locks (`.session_start_lock`) fit runtime state management, with JSONL for logs like `deliberate_hook_changes.jsonl`.[5]

## Blocked Items Enhance Safety
Excluding `projects/`, `cache/`, `backups/`, nested `.claude/`, and random scripts/docs prevents recursive escapes, injection vectors, or unintended data sprawl, echoing Claude Code's permission blocks on parent directory changes and command blocklists.[2][1]
Consolidating `session_*` dirs into files avoids directory proliferation, while banning `pytest.ini` or `*.py` at root stops executable creep outside `skills/` scripts.[3]
This setup complements core protections like explicit approvals and context-aware analysis without conflicting with auto-loading of approved elements.[2]

## Human

pre-mortem

## Assistant

## Potential Security Bypasses
Path traversal exploits like CVE-2025-54794 could let Claude escape `.claude/` via manipulated paths in session files (e.g., `current_session.json`), writing to blocked dirs despite rules; prefix checks fail on symlink tricks or `echo` injections.[1][2]
Command injection through whitelisted tools (curl/fetch) might create forbidden files like `pytest.ini` or nested `.claude/`, triggering CLAUDE_DIRECTORY_VIOLATION late after damage.[3][4]
MCP server misconfigs in `.mcp.json` enable external script execution that indirectly populates `cache/` or `backups/`, evading local checks.[5]

## Session State Exploits
Session isolation leaks (e.g., GitHub #1985) could cross-contaminate `sessions.json` across projects, exposing hook outputs (`hook_validation_results.json`) or mutex states to unauthorized reads.[6]
Concurrent sessions racing on `.session_start_lock` might overwrite `orchestrated_session.json`, allowing subagents to spawn in `projects/` via incomplete validation.[7]
JSONL logs like `deliberate_hook_changes.jsonl` grow unbounded, enabling DoS or injection if Claude parses them unsafely during reloads.

## Rule Enforcement Gaps
Claude ignores user rules systematically (GitHub #5055), auto-loading unvetted skills/plugins that create `helpers/` or `proxy/` despite blocks, as pattern-matching overrides instructions.[8][7]
Missing glob enforcement lets `rules/` subdirs hide scripts (e.g., `rules/security.py`), treated as valid but executing outside sandbox.
No runtime audit of `settings.local.json` overrides permits disabling protections, backdooring via gitignored personal instructions.[9]

## Mitigation Failures
False negatives on "random" files: symlinks or renames (e.g., `data.md` as `data/`) slip past static checks, proliferating nests.
Overly permissive `skills/` loads untrusted `SKILL.md` scripts, chaining to blocked ops like backups under "agent workflow" pretext.[5]
No size/type limits on allowed files let bloated `claude.md` imports trigger OOM, forcing fallback to unsafe defaults.[10]

## Human

How to run a pre mortem workshop step by step
Pre mortem vs post mortem differences and when to use each
Common biases to watch for during a pre mortem session
Pre mortem templates for engineering project risks
How to document pre mortem findings in project files CLAUDE.md

## Assistant

Pre-mortems anticipate project failures proactively by imagining worst-case scenarios upfront, while post-mortems analyze actual outcomes reactively after completion.[1][2]

## Pre-Mortem vs Post-Mortem
Pre-mortems occur before launch to identify and mitigate risks through backward brainstorming, fostering open dissent and reducing overconfidence; use them at project kickoff or milestones for high-stakes engineering efforts like security hardening.[3][4]
Post-mortems happen post-completion to review what succeeded or failed, extracting lessons for future iterations; reserve them for retrospectives to avoid hindsight bias in planning phases.[2][5]
Pre-mortems excel in uncertain domains like AI system design, where biases inflate success odds, unlike post-mortems suited for process audits.[6][7]

## Workshop Steps
Gather 5-10 stakeholders in a 45-60 minute session with sticky notes, timers, and a facilitator; start by stating "The project failed—explain why" and give 5 minutes silent ideation.[8][3]
Participants share notes one-by-one, grouping into themes (e.g., technical, security) via affinity mapping, then vote on top risks by likelihood/impact.[9][6]
Brainstorm mitigations for high-priority items, assign owners/actions with deadlines, and end by updating the project plan.[10][1]

## Common Biases
Confirmation bias leads teams to favor optimistic assumptions over critical risks; counter by anonymous voting and rotating facilitators.[11][7]
Groupthink suppresses dissent as confidence builds; enforce "devil's advocate" roles and time-box positive framing.[7][4]
Overconfidence bias underestimates engineering pitfalls like exploits; use data-driven likelihood scoring (1-10) to ground discussions.[12][11]

## Engineering Templates
Use a table categorizing risks by phase: Planning, Implementation, Testing, Deployment, with columns for Failure Mode, Likelihood, Impact, Mitigation.

| Phase | Failure Mode | Likelihood (1-10) | Impact (1-10) | Mitigation |
|-------|--------------|-------------------|---------------|------------|
| Security | Directory bypass via symlink | 7 | 9 | Glob validation in rules [13] |
| Runtime | Session leak across projects | 6 | 8 | Mutex locks + isolation [1] |
| Scaling | Unbounded JSONL logs | 5 | 7 | Size caps + rotation [14]|

Adapt from Atlassian/Asana templates for software risks like dependency failures or sandbox escapes.[15][6]

## CLAUDE.md Documentation
Embed findings in `.claude/rules/premortem.md` as a modular rule file: start with YAML frontmatter scoping to `*.claude/*` paths, list risks/mitigations as bulleted hierarchies, and reference in main CLAUDE.md via `@.claude/rules/premortem.md`.[16]
Include a tracked table of top risks with status (Open/Mitigated), owners, and verification steps; gitignore local variants for team overrides.[13][17]
Prefix with "Pre-mortem: Project failed on [date]" to trigger auto-loading during agent tasks, ensuring Claude enforces mitigations.[17]

## Human

Create a premortem template focused on technical dependencies
Mitigation planning steps after a premortem session

## Assistant

Technical dependencies in engineering projects like Claude Code setups often fail due to version mismatches, API changes, or integration breaks; a premortem template surfaces these preemptively.

## Premortem Template: Technical Dependencies
Use this table to brainstorm failures, scoring likelihood/impact on 1-10 scales. Adapt for `.claude/` risks like MCP server drifts or plugin incompatibilities.

| Dependency | Failure Mode | Likelihood (1-10) | Impact (1-10) | Root Cause Example |
|------------|--------------|-------------------|---------------|--------------------|
| Claude Code CLI v2.x | Breaks slash commands in `commands/` | 6 | 8 | Upstream Anthropic update skips deprecation |
| MCP servers (.mcp.json) | Tool calls timeout, spawning rogue sessions | 7 | 9 | Auth token expiry or endpoint relocation |
| Skills/Plugins (skills/, .claude-plugin/) | SKILL.md ignored due to YAML parse error | 5 | 7 | Marketplace version drift |
| Session state files (sessions.json) | Cross-project leaks via shared FS | 4 | 9 | Mutex race on concurrent agents |
| Rules loader (rules/) | Glob patterns miss symlinks, allowing bypass | 8 | 8 | Edge-case path traversal in subdirs |

Populate silently first, then group and prioritize top 5.

## Mitigation Planning Steps
Triage risks by score product (likelihood × impact > 40), assigning owners immediately.[1]
For each, define 2-3 concrete actions: e.g., "Pin MCP version in settings.json; test weekly via hook"—with deadlines, verification (e.g., smoke test script), and fallback (e.g., manual override).[2]
Integrate into project files: append to CLAUDE.md as "## Dependency Mitigations" section with status column (Open/In Progress/Done), and create `.claude/rules/dependencies.md` for agent enforcement via `@import`.[3]
Schedule follow-ups: 2-week check-in and milestone reviews to track efficacy, updating scores post-test.[4]
