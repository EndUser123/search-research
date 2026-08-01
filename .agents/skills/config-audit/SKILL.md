---
name: config-audit
description: >
  Audit and optimize Grok Build configuration (AGENTS.md, config.toml,
  plugin settings, MCP servers) against best practices. Scans all
  configuration files, scores them against a rubric, and proposes
  targeted improvements. Adapted from Claude-side "claudit" for Grok
  Build (AGENTS.md instead of CLAUDE.md, config.toml instead of
  settings.json, no Claude-specific hooks/plugins).
host: both
domain: self-improvement
---

# /config-audit — Configuration audit and optimization

Audit the workspace's configuration files for over-engineering, redundancy,
security posture, MCP health, plugin health, and context efficiency. Scores
each category and proposes actionable fixes.

## When to use

- Monthly maintenance
- After major config changes (new plugins, AGENTS.md edits, new MCP servers)
- When context feels bloated or contradictory
- Before a major development push (ensure config is clean)

## When NOT to use

- Skill-specific pruning — use `/skill-prune`
- General health check — use `/workspace-health`
- File recovery — use `/recover`

## Configuration files scanned

### Grok Build (primary)

| File | What it checks |
|---|---|
| `P:/AGENTS.md` | Over-engineering (line count, redundancy, restated built-ins), structure quality, contradictory instructions |
| `~/.grok/config.toml` | Config validity, contradictory settings, dead MCP servers, model config drift |
| `~/.grok/AGENTS.md` | Global agent rules (cross-host) — redundancy with P:/AGENTS.md |
| `P:/.claude/CLAUDE.md` | Compat-loaded artifact — is it stale? Does it contradict AGENTS.md? |
| `~/.grok/tool-fallbacks.md` | Known-broken tool table — is it current? |
| `~/.grok/config.toml [plugins]` | Plugin enable/disable consistency with `~/.claude/settings.json enabledPlugins` |
| `~/.grok/config.toml [mcp_servers]` | MCP server health, dead servers, duplicate functionality |
| `P:/.data/wiki/SCHEMA.md` | Wiki conventions — is it current? Has it grown too large? |

### Claude compat (secondary, checked for conflicts)

| File | What it checks |
|---|---|
| `~/.claude/settings.json` | `enabledPlugins` — do they conflict with Grok's `[plugins].disabled`? |
| `P:/.claude/CLAUDE.md` | "CLAUDE Constitution" — is it the compat version or stale? |

## Scoring categories (6)

| Category | Weight | What it measures |
|---|---|---|
| **AGENTS.md Quality** | 20% | Structure, sections, length (≤200 lines ideal per Codeminer42 research), no restated built-ins |
| **Over-Engineering** | 20% | Redundant instructions, duplicated rules across files, hook sprawl |
| **Security Posture** | 15% | Permission settings, API key exposure, destructive-operation guards |
| **MCP Configuration** | 15% | Server health, dead servers, duplicate functionality, port conflicts |
| **Plugin Health** | 15% | Enable-state consistency (Grok vs Claude), stale plugins, version drift |
| **Context Efficiency** | 15% | Token cost of always-loaded config, AGENTS.md + CLAUDE.md + compat files |

## Audit phases (3, adapted from claudit's 5)

### Phase 1: Configuration map

Scan all config files. Build a manifest:

```
=== CONFIGURATION MAP ===
Scope: Comprehensive (P:/ project + global)

PROJECT: P:/
  AGENTS.md:                    85 lines  (~850 tokens)
  .claude/CLAUDE.md:            120 lines (~1200 tokens, compat artifact)
  .data/wiki/SCHEMA.md:         500 lines (~5000 tokens, wiki conventions)

GLOBAL: ~/.grok/
  config.toml:                  520 lines (~5200 tokens)
  AGENTS.md:                    0 lines (not present — uses P:/AGENTS.md)
  tool-fallbacks.md:            95 lines (~950 tokens)

CROSS-HOST:
  ~/.claude/settings.json:      340 lines (enabledPlugins: 51 entries)

MCP SERVERS (config.toml):
  search, context7              2 servers configured

PLUGINS:
  Grok disabled: 30 plugins
  Claude enabled: 51 plugins
  Conflict: cc-skills-media (Grok ✗, Claude ✓)

TOTAL CONTEXT COST: ~13,200 tokens always-loaded
=== END MAP ===
```

### Phase 2: Audit + score

For each category, check against the rubric and assign deductions/bonuses.

**AGENTS.md Quality checks:**
- Line count >200? (Codeminer42 research: CLAUDE.md/AGENTS.md outperforms skills at any length, but >200 lines causes its own activation gap)
- Restated built-ins? (e.g., "always verify before claiming" when AGENTS.md already has the receipt rule)
- Contradictory instructions? (e.g., "minimal fix" vs "optimal long-term")
- Missing sections? (maintenance reminders, file editing protocol, etc.)

**Over-Engineering checks:**
- Same rule stated in AGENTS.md + CLAUDE.md + SCHEMA.md?
- Hook count >20? (hook sprawl)
- Skills that duplicate AGENTS.md rules?

**Security checks:**
- API keys in tracked files? (scan config.toml, settings.json)
- Destructive git operations not guarded?
- Permission mode set to "always-approve"? (security risk)

**MCP checks:**
- Servers with missing binaries?
- Duplicate functionality across servers?
- Port conflicts?

**Plugin checks:**
- Plugins disabled in Grok but enabled in Claude (or vice versa)?
- Stale plugin caches?
- Version mismatches between cache and marketplace source?

**Context Efficiency checks:**
- Total always-loaded token estimate
- Redundant content across config files
- CLAUDE.md compat artifact still needed? (test: does removing it break anything?)

### Phase 3: Report + recommendations

```
╔════════════════════════════════════════════════╗
║          CONFIG AUDIT HEALTH REPORT            ║
╠════════════════════════════════════════════════╣
║  Scope: Comprehensive | Files: 8 scanned       ║
║  Overall Score: XX/100  Grade: X               ║
╚════════════════════════════════════════════════╝

AGENTS.md Quality   ████████████████████░░░░░  XX/100
Over-Engineering    ████████████████████░░░░░  XX/100
Security Posture    ████████████████████░░░░░  XX/100
MCP Configuration   ████████████████████░░░░░  XX/100
Plugin Health       ████████████████████░░░░░  XX/100
Context Efficiency  ████████████████████░░░░░  XX/100

=== RECOMMENDATIONS ===
1. [CRITICAL] ... (specific file:line, +N pts)
2. [HIGH] ... (specific file:line, +N pts)
...
```

Present recommendations via interactive selection. Implement only operator-confirmed fixes.

## Grok Build differences from Claude Code

| Aspect | Claude Code ("claudit") | Grok Build (this skill) |
|---|---|---|
| Primary config | `CLAUDE.md` | `AGENTS.md` |
| Settings file | `~/.claude/settings.json` (JSON) | `~/.grok/config.toml` (TOML) |
| Plugin state | `enabledPlugins` (opt-in) | `[plugins].disabled` (opt-out) |
| Hooks | Claude hook system (command/prompt/agent) | Grok hook system (command/http only) |
| Managed policy | macOS/Linux system-level | N/A |
| Expert context | Fetches Anthropic docs dynamically | Uses local wiki + workspace conventions |
| Audit agents | 3 parallel subagents (global, project, ecosystem) | Inline (single session; dispatch if scope is large) |
| Decision memory | JSON file tracking past audit decisions | N/A (use wiki concepts for durable audit findings) |
| Phase count | 5 (map → expert → audit → interactive → PR) | 3 (map → audit → report) |

## References

- `wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md` — why AGENTS.md >200 lines causes its own activation gap
- `wiki/concepts/structural-enforcement-for-skipped-rules-grok-build-2026.md` — enforcement mechanisms
- Adapted from Claude-side `claudit` skill (quickstop marketplace)
