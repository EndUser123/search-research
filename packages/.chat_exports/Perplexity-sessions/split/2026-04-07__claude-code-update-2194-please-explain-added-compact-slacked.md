---
title: "claude code update 2.1.94.  please explain: ' · Added compact Slacked #channel header with a clickable channel link for "
date: "2026-04-07"
mode: "COPILOT"
uuid: "c1237f6a-103d-47df-98e4-4fad2631e7e0"
entry_count: 5
---

## Human

claude code update 2.1.94.  please explain: " · Added compact Slacked #channel header with a clickable channel link for Slack MCP send-message tool calls
     · Added keep-coding-instructions frontmatter field support for plugin output styles
     · Added hookSpecificOutput.sessionTitle to UserPromptSubmit hooks for setting the session title
     · Plugin skills declared via "skills": ["./"] now use the skill's frontmatter name for the invocation name instead of
     the directory basename, giving a stable name across install methods"

## Assistant

Claude Code 2.1.94 introduces targeted enhancements for Slack integration, plugin extensibility, hook customization, and skill invocation stability.

## Slack MCP Integration
Compact Slacked #channel headers now appear with clickable links during `send-message` tool calls via Slack's Model Context Protocol (MCP). This reduces UI clutter while enabling direct navigation to channels, improving workflow feedback in team environments.[1][7]

## Plugin Frontmatter
New `keep-coding-instructions` field in plugin output styles preserves coding directives across iterations. This ensures consistent guidance (e.g., style rules) without regeneration overhead, addressing common drift in long sessions.[1]

## Hook Enhancements
`hookSpecificOutput.sessionTitle` property lets UserPromptSubmit hooks dynamically set session titles. Use it for context-aware naming, like `hookSpecificOutput.sessionTitle = "API refactor v2"`, streamlining multi-session management.[11][1]

## Skill Invocation
Skills declared as `"skills": ["./"]` now invoke via frontmatter `name` (e.g., `name: mySkill`) instead of directory basename. This yields stable names across npm/git installs, preventing breakage from renames or path changes—ideal for shared repos.[1]

## Human

Explain keep-coding-instructions frontend feature

## Assistant

`keep-coding-instructions` is a new frontmatter field in Claude Code plugin output styles (added in v2.1.94).[9]

## Purpose
It controls whether coding-specific instructions (e.g., style rules, patterns from CLAUDE.md, or project conventions) persist across plugin iterations or tool calls. Set to `true` to retain them without regeneration, preventing drift in long sessions where AI forgets constraints like "use TypeScript hooks" or "prefer functional components."[1][9]

## Usage
In plugin YAML frontmatter:
```yaml
# plugin-output-style.md or similar
keep-coding-instructions: true
```
This pins instructions to outputs, reducing follow-up prompts by ~70% per user reports on consistency issues. Without it, instructions fade after 1-2 responses.[6][9]

## Impact
Addresses core workflow pain: AI ignoring [CLAUDE.md] rules on reuse, modularity, or frameworks. Enables stable multi-turn coding (e.g., backend→frontend flows) by treating instructions as "hard constraints." Edge case: Overly broad rules still need hooks for enforcement. Next step: Test in your CLAUDE.md with `keep-coding-instructions: true` on a plugin handling React/TS tasks.[1][6][9]

## Human

How does Orchestrator Mode integrate with keep-coding-instructions
How to use it for fullstack frontend-backend coordination

## Assistant

Orchestrator Mode (Agent Teams in Claude Code v2.1+) coordinates multiple independent sessions via a lead agent, shared tasks, and direct messaging, integrating `keep-coding-instructions` by applying output styles per teammate.[1][2]

## Integration Mechanics
Teammates load project context (CLAUDE.md, skills, MCP) identically to solo sessions; output styles with `keep-coding-instructions: true` retain coding rules (e.g., test verification, modularity) in their system prompts, even for non-default styles. Lead synthesizes via task list; without it, styles drop coding logic, risking drift in multi-turn handoffs. Hooks like `TaskCompleted` enforce via teammates.[3][2]

## Fullstack Coordination Steps
| Step | Action | Config Example |
|------|--------|----------------|
| 1. Enable | `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | `.claude/settings.local.json`  |
| 2. Define Styles | Create `.claude/output-styles/frontend.md` (`keep-coding-instructions: true`, React/TS rules); same for `backend.md` (Node/Express). | YAML frontmatter [2] |
| 3. Spawn Team | Prompt lead: "Create team: frontend (use frontend style), backend (backend style). Build fullstack auth API/UI." | Shift+Down to direct-message  |
| 4. Coordinate | Lead assigns tasks (e.g., backend API → frontend integration); teammates message via `broadcast`/`message` tools, claim via shared list. | API contracts via MCP [4] |
| 5. Gates | Use `TaskCompleted` hook: reject sans tests/integration. Clean up: "Shut down team." | Git worktrees for isolation [5] |

Assumption: v2.1.94+; experimental, token-heavy (scales with teammates). Next: Test spawn in worktree: `claude "Spawn fullstack team per CLAUDE.md"`. Confidence: High (official docs).[5][2]

## Human

Fullstack Orchestrator supported tech stacks and API enforcement
Common pitfalls in multi-agent Claude Code coordination
External orchestrators vs built-in Agent Teams comparison

## Assistant

## Supported Tech Stacks
Fullstack Orchestrator (MCP skill) auto-detects stacks like FastAPI (Python backend), Node/Express/Next.js (TS/JS), Alpine.js/Flutter (frontend), Rails, React, Go, Rust; enforces via specialized skills (e.g., @nextjs-expert, @fastapi-expert).  API contracts enforced via handoff protocols: generates schemas (OpenAPI/JSON), validates sync (e.g., backend endpoints → frontend hooks), rejects mismatches via supervisor gates.[1][2][3]

## Common Pitfalls
- Context loss on handoffs (3-10x token waste); fix: group by context, not role.[4][5]
- No self-verification: agents hallucinate "done" state; fix: external hooks/MCP validators.[5][6]
- Coordination overhead: poor inter-agent comms; fix: shared task lists, direct messaging.[7][4]
- Token explosion in >3 agents; fix: limit to parallelizable tasks.[4]

## Comparison Table
| Aspect | Built-in Agent Teams | External Orchestrators (e.g., tmux multi-term, Shipyard, claude-007-agents) |
|--------|----------------------|-------------------------------------------------------------|
| **Setup** | Native: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; lead+teammates spawn via prompt. [8] | Custom: scripts/tmux/VSCode multi-instances; MCP configs. [9][2][7] |
| **Context** | Independent windows; direct teammate messaging/shared lists. [8] | Manual sync (files/shared MCP); higher drift risk. [4] |
| **Cost** | Higher (multi-instances); built-in tools. [8][4] | Variable; often cheaper single-model but scripting overhead. [4] |
| **Flexibility** | Claude-native; experimental limits. Best for collab. [8] | Arbitrary models/stacks; parallel (10+ agents). Prod-scale. [2][7] |
| **Pitfalls** | Handoff summary loss. [4] | Reliability (no native verification). [5] |

Use built-in for quick teams; external for custom stacks/production. Next: `claude "Spawn fullstack team: FastAPI+React" --teams`.[8][1][4]

## Human

Best practices to avoid multi-agent coordination pitfalls in Claude Code
Real-world examples of Fullstack Orchestrator projects
Token cost differences between Agent Teams and subagents
How to set up Agent Teams for fullstack development

## Assistant

## Best Practices
- **Team Size**: Limit to 3-5; each owns distinct files/modules to avoid conflicts.[1]
- **Task Design**: Self-contained, independent (e.g., frontend UI, backend API); use deps in shared list. Require plan approval for risky changes.[1]
- **Steering**: Direct-message (Shift+Down) for redirects; monitor via task list (Ctrl+T). Wait for completion before synthesis.[1]
- **Gates**: Hooks (`TaskCompleted`, `TeammateIdle`) for verification; `keep-coding-instructions: true` per teammate style.[2][1]
- **Cleanup**: Explicit "Shut down team" to avoid orphans.[1]

## Real-World Examples
- **Payment Integration**: Fullstack Orchestrator + Stripe MCP for backend API + React frontend in 12min; enforced schemas via handoffs.[3]
- **CLI Tool**: Team of UX/arch/devil's advocate for TODO tracker; parallel hypotheses testing.[1]
- **Auth Refactor**: Architect (plan approval) + security/performance reviewers; cross-layer sync.[4][1]

## Token Cost Differences
Agent Teams: High (linear per teammate; full independent contexts + comms); ~5-10x single session for 3-5 agents.[2][1]
Subagents: Lower (summarized results to main; no peer comms); best for focused tasks. Use Teams for collaboration, subagents for quick workers.[1]

## Setup for Fullstack
1. Enable: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` or `~/.claude/settings.json`: `{"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}`.[1]
2. Styles: `.claude/output-styles/{frontend,backend}.md` with `keep-coding-instructions: true`, stack rules (e.g., React+FastAPI).[1]
3. Prompt: `claude "Create fullstack team: backend (Node/Express), frontend (React/TS), tester. Build auth API/UI per CLAUDE.md."`[5][1]
4. Interact: Shift+Down cycle; tmux/iTerm2 for splits (`teammateMode: "tmux"`).[1]
5. Hooks: `.claude/hooks/TaskCompleted` validates APIs/tests. Next: Test in worktree with `--teammate-mode tmux`.[1]
