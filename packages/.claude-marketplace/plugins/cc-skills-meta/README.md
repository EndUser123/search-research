# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, self-improvement, and orchestration.

## Skills (51)

| Skill | Purpose |
|-------|---------|
| behave | Structured behavioral analysis for LLM performance debugging — hypothesis testing for session patterns (loops, context degradation, decision inefficiency, cognitive overload, attention drift) |
| cks | Constitutional Knowledge System - unified command for search, add, and session extraction |
| concept-mapper | Unified concept mapping for learning, system architecture, and text analysis. Creates Mermaid diagrams for mind maps, concept maps, system diagrams, and knowledge structures. Use for studying, documentation, architecture visualization, or converting articles/text into visual maps. |
| config-audit | Audit Claude Code configuration artifacts (hooks, skills, CLAUDE.md, agents) for over-engineering, redundancy, and token waste. Uses model routing (haiku for research, sonnet for analysis) with decision memory. |
| constitutional-patterns | Standards for constitutional compliance and pattern enforcement. |
| constraints | Show active project constraints from CLAUDE.md |
| csf-nip-integration | Guide Claude in working with CSF NIP architecture, commands, patterns, and conventions |
| decision-tree | SDLC decision engine for architecture, incidents, refactors, migrations, and release risk. |
| dne | DUF-NSE - Pre-mortem checks + Next Steps. Past to future analysis. |
| doc-compiler | Compile skills, plugins, projects, and workflows into interactive, verified HTML documentation with Mermaid diagrams, TOC, proof metadata, and browser validation. |
| doc_to_skill | Convert documentation into Claude Skills using automated scraping and AI enhancement |
| dream | Memory consolidation pass — synthesize recent learnings into organized durable memories. Use when session has yielded significant learnings, before long sessions, or when memory feels cluttered. Triggers automatically on session end via SessionStart hook. |
| epistemic-check | Validate any Q&A response against the 4-section epistemic contract. Runs 3-phase audit (format → causal → comparative), reports violations and minimal repairs. |
| evolve | Unified modernization workflow to transform working code into high-standard systems. |
| execution-clarity | Atomic execution phases + confidence scoring for risk-aware decision-making. |
| friction | Detect interaction friction and workflow automation opportunities from chat history and session evidence. |
| garden | Knowledge hygiene for CKS and SKILL.md to prevent knowledge entropy |
| genius | Apply a high-quality thought-partner lens to a problem, challenge premises, and surface overlooked angles |
| gitready | This skill should be used when the user asks to "create a package", "scaffold a Python library", "make a GitHub-ready repo", "generate badges", "convert to plugin", "brownfield conversion", "validate plugin standards", or mentions package scaffolding, portfolio polish, repository structure setup, badge generation, or plugin standards validation. Creates GitHub-ready Python libraries, Claude skills, and Claude Code plugins with badges, coverage metrics, media artifacts, interactive course modules, and automatic plugin standards validation. Includes PHASE 6: GitHub Publication and PHASE 7: Repository Finalization. |
| gto | GTO v4.2 — Session-aware gap-to-opportunity analysis with RNS-compatible output |
| gto-old | Analyze what happened in this session and recommend what to do next. Detects: what skills were used, what wasn't completed, what gaps exist, what other skills should be invoked (like /pre-mortem after code changes, /critique after reviews, /git after edits). |
| learn | Intelligent lesson capture with novelty detection and usefulness filtering |
| lmc | Lossless Maximal Compaction - Maximum token optimization that preserves all critical information |
| mlc | Minimal Lossy Compaction - Conservative token optimization that preserves most information while dropping redundancy |
| pace | Cognitive load and WIP tracking for solo dev throttle |
| prompt-refiner | Executable prompt specification system with constitutional compliance and cognitive techniques |
| prompt_refiner | Executable prompt specification system with constitutional compliance and cognitive techniques |
| ralph | Ralph Loop - task decomposition and iterative development |
| reason | Route analysis by epistemic state and blend internal reflection with external verification when needed |
| recap | Catch up on all sessions in this terminal via checkpoint chain traversal and surface unresolved assumptions, contract gaps, Contract Authority Packet gaps, and resume risks |
| reflect | Analyzes conversation transcripts to extract user corrections, patterns, and preferences, then proposes skill improvements. Use this skill when users provide corrections, express preferences about code style, or when patterns emerge from successful approaches. Can be triggered manually with /reflect or automatically at session end when enabled. |
| response-atomicity | Enforces atomic responses and phase separation in task execution. |
| retro | Identify what went wrong, what went right, and what to do differently next time. Chains 6 skills: recap → gap analysis → friction → pre-mortem → actions. |
| sequential-thinking | Apply Generate → Critique → Improve loop to make reasoning smarter through self-reflection |
| similarity | Find skills similar to a target skill based on keywords, dependencies, and metadata |
| simplify | Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality. Focuses on recently modified code unless instructed otherwise. |
| skeptic | AI output validation using cognitive frameworks and evidence checking |
| skill-craft | Unified Skill-Craft Orchestrator — coordinates skill improvement through a 5-phase pipeline (diagnose → plan → execute → evaluate → gate) with fidelity closing gates. Use when improving an existing skill, crafting documentation with mermaid diagrams, or running structured skill reviews. |
| skill-creator | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |
| skill-to-page | Transform a skill's SKILL.md into a navigable, verified index.html with Mermaid diagrams, TOC, search, viewport controls, provenance, and proof-oriented verification. |
| slc | Pragmatic Solo Dev Guidelines - lean development principles for solo developers |
| solo-dev-authority | Constitutional constraints on patterns for solo developers. |
| standards | Read and enforce CSF NIP standards |
| subagent-driven-development | Execute implementation plans by dispatching specialized subagents with two-stage review. |
| top-problems | Analyze recent session history, premortem evidence, and task data to find the most impactful fixable problems, including systemic contract and stale-data failures |
| tot | Tree-of-thoughts reasoning - explore multiple branches of thought and evaluate different perspectives. |
| trace | Manual trace-through verification for code, skills, workflows, and documents - catch logic errors that automated testing misses |
| truth | Truth Constitution Command - Verify claims using actual evidence |
| usm | The master coordinator for AI skills and Claude Code plugins. Discovers skills from multiple sources (SkillsMP.com, SkillHub, ClawHub, and skills.sh) and plugins from multiple sources (official marketplace, community directories, and GitHub curations), manages installation, and synchronization across Claude Code, Gemini CLI, Google Anti-Gravity, OpenCode, and other AI tools. Handles User-level (Global) and Project-level (Local) scopes. |
| why | Decision archaeology — trace backward through sessions to reconstruct why something exists, what caused it, and the reasoning chain behind it. NOT a debug tool — answers "why are we doing X?" |
| write-a-skill | Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill. |

## Installation

Skills are surfaced via junctions in `.claude/skills/`.

```bash
# As a Claude Code plugin
/plugin install cc-skills-meta
```

## Artifacts Convention

All runtime artifacts write to:

```
.claude/.artifacts/{terminal_id}/{skill_name}/
```

Skills must not write state to their own directory or to the package root.
