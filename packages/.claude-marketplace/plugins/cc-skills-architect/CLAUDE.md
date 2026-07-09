# cc-skills-architect

The System Hub for Claude Code — master routers, meta-development tools, and implementation strategy.

## 🧠 The Architect Tribe

Tools for building, documenting, and evolving the CLI system and complex project implementation.

### 1. Master Routing (Production)
The central triage for all CLI operations.

| Skill | Purpose | Home |
|-------|---------|------|
| /ask | Universal CLI router for command discovery | `ask/` |
| /ai-api | Unified LLM API — direct SDK (Bifrost `bf` route RETIRED — not in use) | `ai-api/` (in cc-skills-ai-api) |

### 2. Meta-Development Toolbox
Tools used to grow and maintain the skill ecosystem.

| Skill | Purpose | Home |
|-------|---------|------|
| /skill-to-page | Generates HTML documentation from SKILL.md | `skill-to-page/` |
| /skill-write | Quick-start skill authoring workflow | `skill-write/` |
| doc-compiler | Multi-module documentation aggregator | `doc-compiler/` |
| skill-from-docs | Bootstraps a skill from Markdown documentation | `skill-from-docs/` |
| gitready | Scaffolding and asset readiness | `gitready/` |
| usm | Master skill/plugin coordinator | `usm/` |
| garden | Knowledge cleanup and pattern pruning | `garden/` |
| evolve | Modernization and technical debt refactoring | `evolve/` |

**Note on `/skill-creator`:** The measure instrument (eval / benchmark / description-optimizer / tournament) lives in the separate `skill-creator@local` plugin — a fork of Anthropic's upstream that carries our tournament customizations. It is enabled; the upstream `skill-creator@claude-plugins-official` is disabled. `skill-write` (above) is the author instrument; `skill-creator` is the measure instrument — the create-side pair. The former architect-local fork of helper scripts was removed (dead, zero callers).

### 3. Implementation Planning
Advanced logic for high-stakes technical sessions.

| Skill | Purpose | Home |
|-------|---------|------|
| ralph | Local PR-ready loop logic | `ralph/` |
| subagent-driven-development | Plan execution orchestrator | `subagent-driven-development/` |
| constitutional-patterns | Logic for adhering to project principles | `constitutional-patterns/` |
| constraints | Project-level constraint enforcement | `constraints/` |
| decision-tree | Complex tradeoff visualization | `decision-tree/` |
| solo-dev-authority | Implementation authority for solo dev | `solo-dev-authority/` |
| prompt-refiner | *DEPRECATED stub → /improve generate-prompt* (Q1-Q3 triage + scoring heuristics + 6 cognitive-technique templates; engine retained) | `prompt-refiner/` |

## Artifacts Convention

All runtime artifacts write to:
`.claude/.artifacts/{terminal_id}/{skill_name}/`

Skills MUST NOT write state to their own directory or to the package root.

## Installation

Plugins live directly in `P:/packages/.claude-marketplace/plugins/<name>/`.
