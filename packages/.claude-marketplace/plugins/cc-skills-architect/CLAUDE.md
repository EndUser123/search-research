# cc-skills-architect

The System Hub for Claude Code — master routers, meta-development tools, and implementation strategy.

## 🧠 The Architect Tribe

Tools for building, documenting, and evolving the CLI system and complex project implementation.

### 1. Master Routing (Production)
The central triage for all CLI operations.

| Skill | Purpose | Home |
|-------|---------|------|
| /ask | Universal CLI router for command discovery | `ask/` |
| /bf | Bifrost: multi-model comparison and agentic workflows | `bf/` |

### 2. Meta-Development Toolbox
Tools used to grow and maintain the skill ecosystem.

| Skill | Purpose | Home |
|-------|---------|------|
| /skill-creator| Standardized skill creation (Subscription-first) | `skill-creator/` |
| /skill-craft | Advanced auditing and Mermaid generation | `skill-craft/` |
| /skill-to-page | Generates HTML documentation from SKILL.md | `skill-to-page/` |
| /write-a-skill | Quick-start skill authoring workflow | `write-a-skill/` |
| doc-compiler | Multi-module documentation aggregator | `doc-compiler/` |
| doc-to-skill | Bootstraps a skill from Markdown documentation | `doc-to-skill/` |
| gitready | Scaffolding and asset readiness | `gitready/` |
| standards | Solo-dev architectural standard enforcement | `standards/` |
| usm | Master skill/plugin coordinator | `usm/` |
| garden | Knowledge cleanup and pattern pruning | `garden/` |
| evolve | Modernization and technical debt refactoring | `evolve/` |

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
| prompt-refiner | Automated prompt engineering for skills | `prompt-refiner/` |

## Artifacts Convention

All runtime artifacts write to:
`.claude/.artifacts/{terminal_id}/{skill_name}/`

Skills MUST NOT write state to their own directory or to the package root.

## Installation

Skills surfaced via junctions in `P:/.claude/skills/`.
