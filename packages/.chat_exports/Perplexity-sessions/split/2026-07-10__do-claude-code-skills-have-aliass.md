---
title: "do claude code skills have alias's?"
date: "2026-07-10"
mode: "COPILOT"
uuid: "a1f92b10-64e0-4ae9-90f1-d0c21ca72450"
entry_count: 2
---

## Human

do claude code skills have alias's?

## Assistant

Yes, but not in the “per‑skill multiple names” sense you’re probably thinking of. Out of the box, each Claude Code skill maps to a single slash command name, and the only built‑in “alias” concept is at the filesystem path level plus whatever alias skills you create yourself.[1][2][3]

## What exists today

- Each skill is a folder under `.claude/skills/` with a `SKILL.md`, and the folder name becomes the **command name** (e.g. `.claude/skills/image-to-prompt/` → `/image-to-prompt`).[2][3][1]
- There’s a **path alias** for legacy commands: putting files in `.claude/commands/` is treated as an alias of `.claude/skills/` and produces the same `/command`.[2]
- Skills and slash commands are now unified: “skills and slash commands are the same thing”, so the skill name is effectively the slash command name.[4][2]

So: a given skill has one canonical name (its folder / file name), and you don’t define multiple names for the same skill in frontmatter or similar.[3][1][2]

## Types of “aliases” you can use

Here are the alias‑like mechanisms that do exist:

- **Filesystem alias (canonical vs legacy paths)**  
  - `.claude/skills/` is canonical.  
  - `.claude/commands/` is a backward‑compatible alias that creates identical commands.[2]
  - Example: `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both yield `/deploy`. If both exist, the skill wins.[2]

- **User vs project scope aliases**  
  - Project‑scoped: `.claude/skills/` or `.claude/commands/` inside a repo → shared via git.[2]
  - User‑scoped: `~/.claude/skills/` or `~/.claude/commands/` → personal aliases not shared.[2]

- **Alias skills that point at other skills**  
  - Community skills like “Claude Command Aliaser” or “skill‑alias” create small wrapper skills that act as **shortcuts** and delegate to other skills / commands.[5][6]
  - These are separate skills with their own name (e.g. `/itp`) that internally invoke another skill (e.g. `/image-to-prompt`).[6][5]

- **Planned / requested name aliases (initialisms)**  
  - There’s a feature request for “auto‑initialism aliases” like `/itp` resolving to `/image-to-prompt`.[7]
  - That’s not documented as a generally available built‑in feature yet; it’s more of a requested enhancement than guaranteed behavior.[7]

## Practical takeaway

- FACT: A skill’s name is determined by its directory / file name, and that becomes the slash command.[1][3][2]
- FACT: `.claude/commands/` is an alias path for `.claude/skills/`; both produce the same command name.[2]
- CONSENSUS: If you want multiple “aliases” like `/itp` and `/image-to-prompt`, you currently do that by creating **separate tiny skills or wrapper commands** that forward to the main skill, or by using an “alias” utility skill from the marketplace.[5][6]
- SPECULATION (medium confidence): Native multi‑name alias support (automatic initialisms, multiple invocations for one skill) is likely to show up, given the feature discussions, but you should not rely on it until it’s in the official docs.[7][1]

If you tell me how you’d *like* aliases to work (e.g. initialisms, synonyms, per‑repo vs global), I can sketch a concrete pattern for building an alias system with minimal wrapper skills in your current Claude Code setup.  

## Human

what about skill frontmatter?

## Assistant

Skill frontmatter does **not** define aliases; it defines metadata like the skill’s name, description, and optional fields, and the `name` still has to match the directory and becomes the single slash command.[1][2][3]

## What frontmatter can do

The `SKILL.md` frontmatter supports these core fields (Agent Skills spec + Claude Code docs):[2][3][1]

- `name` (required): Unique identifier for the skill, lowercase, hyphens only, must match the parent directory name and becomes the skill/command name.[3][1]
- `description` (required): Text describing what the skill does and when to use it; used for routing and auto‑invocation.[1][3]
- `license` (optional): License string or reference to a bundled license file.[3]
- `compatibility` (optional): Environment requirements (product, packages, network access, etc.).[3]
- `metadata` (optional): Arbitrary key–value pairs for custom properties.[3]
- `allowed-tools` (optional, experimental): Space‑separated list of tools the skill is pre‑approved to run.[3]

After the frontmatter, the markdown body is the actual instructions, examples, and guidelines Claude uses once the skill is activated.[4][1][3]

## Why it doesn’t give you aliases

- FACT: Spec and examples only allow a **single** `name` field, and it must match the folder name.[1][3]
- FACT: There is no `aliases`, `shortcut`, or similar field in the official frontmatter spec or Claude Code docs today.[2][1][3]
- CONSENSUS: Tools and marketplace skills that implement aliasing (like command aliasers) do it by creating separate wrapper skills/commands, not frontmatter‑level alias lists.[5][6]
- SPECULATION (medium confidence): If alias support is added, it would likely show up as either new frontmatter fields (e.g. `aliases`) or an engine‑level convention, but you should assume it’s **not** available until the spec/docs explicitly say so.[7][3]

## How to use frontmatter for “alias‑like” behavior

Even though you can’t define multiple names, you can still use frontmatter to make skills feel discoverable and “alias‑like”:

- Use a short, canonical `name` (e.g. `itp`) and reflect the long form in the `description` (“Image to prompt (alias for /image-to-prompt workflow)”).[1][3]
- Embed keywords and common synonyms in `description` so auto‑invocation and search surface the skill when you type natural language (“image prompt, reverse image search, prompt from picture, itp”).[1][3]
- Use `metadata` to tag skills with categories or custom routing hints (e.g. `metadata: { category: "images", alias-for: "image-to-prompt" }`) that you can read with your own tooling.[3]

If you share a minimal `SKILL.md` you’re using, I can propose a concrete frontmatter pattern (name, description, metadata) that gives you the best discoverability and plays nicely with any alias wrapper skills you build.  
