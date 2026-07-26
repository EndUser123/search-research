---
title: "Agent config directory taxonomy: .agents vs .grok vs .claude vs .codex"
created: 2026-07-22
source: session-2026-07-22
tags: [agent-config, directory-convention, cross-tool, skills, agents-md, skill-md, multi-agent, taxonomy, host-setup]
summary: >
  The SKILL.md format is an open standard (agentskills.io) but the directory
  location is NOT — each tool uses its own (.claude/, .grok/, .codex/).
  The .agents/skills/ path is the emerging cross-agent convention: GitHub
  Copilot supports it natively; Claude Code does not (issue #66352 closed
  as not planned). AGENTS.md is the cross-tool instruction-file standard
  (60k+ repos, 20+ tools). On a multi-tool host: use ~/.grok/ for Grok-only
  skills, .claude/ for Claude-only, and .agents/ for cross-tool skills that
  any agent should discover.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/skill-path-resolution-gotcha
    type: refines
  - target: wiki/concepts/context-file-deduplication-agents-md-as-source
    type: related
  - target: wiki/concepts/skill-catalog
    type: related
---

## Summary

Two open standards govern AI agent configuration in 2026: **AGENTS.md** (the cross-tool instruction file, 60k+ repos) and **SKILL.md / Agent Skills** (the cross-tool skill format, agentskills.io). But neither standard mandates WHERE skills live on disk. Each tool has its own directory convention (`.claude/`, `.grok/`, `.codex/`, `.cursor/`). The `.agents/skills/` path is the emerging cross-agent convention — recognized by Copilot and the community, but not yet universally adopted.

## The two open standards

| Standard | URL | What it standardizes | What it does NOT standardize | Adoption |
|---|---|---|---|---|
| **AGENTS.md** | agents.md | A markdown file at repo root for agent instructions (build steps, tests, conventions) | Directory structure; skill format | 60k+ repos; 20+ tools (Codex, Cursor, Claude, Gemini, Devin, Aider, VS Code, etc.) |
| **Agent Skills** | agentskills.io | The SKILL.md format (frontmatter + body), directory structure within a skill | The PARENT directory where skills live | 32+ platforms |

**The gap:** the format is standardized; the location is not. This is the root cause of the path-resolution failures documented in [[skill-path-resolution-gotcha]].

## Directory taxonomy (verified per-tool)

| Directory | Scope | Who reads it | Use for |
|---|---|---|---|
| `~/.grok/skills/` | User (Grok) | Grok Build only | Grok meta-tools (/tp, /plan, /go, /handoff, /design) |
| `P:/.grok/skills/` | Workspace (Grok) | Grok Build only | Project-specific Grok overrides (being phased out) |
| `~/.claude/skills/` | User (Claude) | Claude Code only | Claude user-level skills |
| `<project>/.claude/skills/` | Project (Claude) | Claude Code only | Claude project-level skills |
| `~/.copilot/skills/` | User (Copilot) | GitHub Copilot only | Copilot user-level skills |
| **`~/.agents/skills/`** | **User (cross-tool)** | **Copilot ✅, others proposed** | **Cross-tool skills any agent can use** |
| **`<project>/.agents/skills/`** | **Project (cross-tool)** | **Copilot ✅, others proposed** | **Project-level cross-tool skills** |
| `.codex/` | Project (Codex) | Codex only | Codex config |
| `.cursor/` | Project (Cursor) | Cursor only | Cursor config |
| `.gemini/` | Project (Gemini) | Gemini CLI | Gemini config |

**Key distinction:** `.agents/` is the ONLY directory convention that is explicitly cross-tool. The rest are vendor-specific.

## The .agents/ convention (emerging, not universal)

**What `.agents/skills/` IS:**
- Recognized as "the cross-agent convention" by the community [source: dev.to, 10/12]
- Supported natively by GitHub Copilot (checks `.agents/skills/` alongside `.github/skills/` and `.claude/skills/`) [source: dev.to, 10/12]
- Part of the broader `.agents/` convention: `~/.agents/instructions/` for shared instructions, `~/.agents/skills/` for shared skills, `~/.agents/agents/` for shared agent configs [source: GitHub #66352, 10/12]
- Proposed for Claude Code (issue #66352, Jun 2026) but **closed as not planned** [source: GitHub #66352]

**What `.agents/skills/` is NOT:**
- Not yet supported by Claude Code (uses `.claude/skills/` only)
- Not yet supported by Grok Build (uses `~/.grok/skills/` only)
- Not part of the official SKILL.md spec (agentskills.io defines the format, not the location)
- Not universally adopted — it's a community convention, not a ratified standard

**Practical status:** `.agents/skills/` works with Copilot today. Other tools need manual configuration or symlinks to discover skills there. The community is pushing for broader adoption (GitHub #66352, dot-agents.com) but tool vendors haven't converged yet.

## Decision rule for this host

| Skill type | Where it goes | Why |
|---|---|---|
| Grok meta-tool (/tp, /plan, /go, /handoff) | `~/.grok/skills/` | Grok-specific; only Grok reads it |
| Cross-tool skill (preflight, notebooklm) | `P:/.agents/skills/` | Any agent can discover it; format is standard SKILL.md |
| Project-specific tool | `P:/.grok/skills/` (deprecated) or `P:/.agents/skills/` | Depends on whether other tools need it |
| Claude-specific skill | `~/.claude/skills/` or `<project>/.claude/skills/` | Only Claude reads it |
| Cross-tool instructions | `AGENTS.md` at repo root | The standard; 20+ tools read it |

## Conflicts in the ecosystem

**⚠️ Claude Code does not support `.agents/skills/`**
- dev.to (Mar 2026): "Claude Code uses its own `.claude/` directory structure, not `.agents/`."
- GitHub #66352 (Jun 2026): Feature request for `~/.agents/skills/` discovery — **closed as not planned**
- **Resolution:** If you want Claude Code to discover cross-tool skills, symlink or configure manually. The vendor hasn't adopted the convention.

**⚠️ No standard precedence rule**
- When a skill exists in BOTH `.claude/skills/` and `.agents/skills/`, which wins?
- GitHub #66352 proposed: project > user; tool-specific > generic. Not adopted.
- **Resolution:** avoid duplication (per [[skill-path-resolution-gotcha]]). One skill, one location.

**⚠️ Grok Build's directory model differs from the industry**
- Grok uses `~/.grok/skills/` (user) and `.grok/skills/` (workspace) — neither is `.agents/`
- The industry uses `.agents/skills/` (cross-tool) and tool-specific dirs
- **Resolution:** documented in this concept; Grok skills stay at `~/.grok/` because they're Grok-specific (not cross-tool)

## Related

- [[skill-path-resolution-gotcha]] — the failure mode this taxonomy prevents
- [[context-file-deduplication-agents-md-as-source]] — AGENTS.md as single source of truth
- [[skill-catalog]] — auto-generated index of all 970 skills across 21 directories

## Sources

- agents.md (official): https://agents.md/ — authority=3, recency=3, evidence=3, bias=3 → **12/12**
- agentskills.io specification: https://agentskills.io/specification — **12/12**
- debs_obrien, "What Are Agent Skills? Beginners Guide", dev.to (Mar 2026): https://dev.to/debs_obrien/what-are-agent-skills-beginners-guide-e2n — **10/12**
- GitHub #66352, "Support user-level .agents/skills/ discovery" (Jun 2026): https://github.com/anthropics/claude-code/issues/66352 — **10/12** (closed as not planned; valuable for documenting the gap)
- "CLAUDE.md vs AGENTS.md vs SKILL.md", towardsai.net (Jul 2026): https://pub.towardsai.net/claude-md-vs-agents-md-vs-skill-md-which-file-owns-what-in-2026-13859378f56a — **10/12**

**Source diversity:** 2 official specs, 1 practitioner guide, 1 GitHub issue, 1 comparison article. No LOW-QUALITY sources.

## Auto-related

- [[skill-catalog]]
- [[grok-build-compat-layer-marketplace-plugin-skills]]

