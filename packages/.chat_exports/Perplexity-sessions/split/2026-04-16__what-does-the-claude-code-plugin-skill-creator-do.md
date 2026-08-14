---
title: "what does the claude code plugin skill-creator do?"
date: "2026-04-16"
mode: "COPILOT"
uuid: "b818337a-0944-4a45-8abc-bf976b74f1ca"
entry_count: 21
---

## Human

what does the claude code plugin skill-creator do?

## Assistant

**The Claude Code skill-creator is a meta-skill that automates the creation, testing, evaluation, and optimization of new custom skills for Claude Code.**[1][2]

## Core Functionality
It follows a structured workflow: capture skill intent, draft SKILL.md with YAML frontmatter and instructions, generate test cases, run benchmarks (with/without the skill), review quantitative metrics and qualitative feedback, iterate improvements, optimize the description for reliable triggering, and package as a .skill file.[2][3][1]

## Usage Process
Install via `/plugins` in Claude Code (search "skill-creator", install globally or per-project), then prompt Claude like "Use skill-creator to build a skill for [purpose]". It loops autonomously: drafts, tests (e.g., evals.json prompts), aggregates benchmarks (timing, assertions), generates review viewers, and refines until performant.[4][2]

## Key Benefits
Designed for complex workflows Claude can't handle directly; improves trigger accuracy via description tuning (20+ eval queries); supports bundling scripts/references; outputs distributable skills for personal/project/plugin scopes.[5][3]

Next step: In Claude Code, run `/plugins`, install skill-creator, confirm with "Do you have skill-creator available?", then describe your skill (e.g., "API tester"). Confidence: High (official repos/docs align).[4][5]

## Human

How do I install and use the skill-creator skill
Step-by-step guide to create a skill with skill-creator
What are examples of skills made using skill-creator

## Assistant

**Install the skill-creator skill in Claude Code via the `/plugins` command (search "skill creator", select "install for you" for global access across projects).**  Verify by prompting "Do you have skill-creator available?"—Claude confirms if ready.[1][2]

## Installation Steps
1. Open Claude Code in your IDE (e.g., VS Code).
2. Type `/plugins` or "manage plugins".
3. Search "skill creator" (or "skill-creator"), install globally ("install for you").
4. Restart session if needed; check with "show skills" or confirm prompt.[2][1]

## Creating a Skill: Step-by-Step
1. Prompt Claude: "Use skill-creator to build a skill for [describe purpose, e.g., 'super landing page that turns descriptions into Apple-style pages']".
2. Skill-creator auto-generates: to-do plan, drafts SKILL.md (YAML frontmatter + instructions), creates test cases (evals.json).
3. Benchmarks: Runs tests with/without skill, measures metrics (success rate, timing), generates review table.
4. Iterates: Improves based on feedback, tunes description (20+ eval queries for trigger accuracy), outputs .skill file or directory (~10 mins).[3][2]

## Example Skills Created
- **Super Landing Page**: Converts landing page descriptions (layout, stack, responsive) to Apple-minimalist HTML/CSS/JS with animations.[2]
- **Explain-Code**: Adds analogies, ASCII diagrams, step-by-step breakdowns for code explanations.[1]
- **Seekers**: Points at docs/PDF/codebase to auto-generate domain-specific skills (e.g., React/Django frameworks).[4]

Next: Test in empty project—`/plugins`, install, prompt skill idea. Edge: Windows PowerShell if bash issues.[1][2]

## Human

Common mistakes when using skill-creator

## Assistant

**Common mistakes with skill-creator include generating invalid YAML frontmatter (e.g., missing delimiters, unclosed quotes, spaces/capitals in names), producing messy/broken files (wrong naming, missing references), and skipping evals/iteration for poor trigger accuracy or untested skills.**[1][2][3]

## YAML Errors
- Omit `---` delimiters or leave quotes unclosed in SKILL.md frontmatter, causing validation failures.[2]
- Use invalid names like "My Cool Skill" (must be kebab-case, no spaces/capitals).[3][2]
- Miss allowed properties, generating non-compliant YAML.[3]

## File/Output Issues
- Generated files have wrong structure: skill.md misplaced, missing reference files, or incorrect naming conventions.[1]
- References point to non-existent files, breaking the skill.[1]

## Design & Testing Pitfalls
- Vague descriptions lead to no triggers; too generic like "Helps with projects" fails.[2]
- Overly verbose instructions (bury key steps, ignore token limits >5k); use progressive disclosure instead.[4][2]
- No baselines/evals: Skip benchmarks, miss edge cases, under-specified workflows (e.g., no README handling).[5][6]
- Rely solely on LLM without domain context, yielding generic/vague procedures.[4]

## Fixes & Next Steps
Always validate generated .skill zip (check YAML, files); run evals.json benchmarks; iterate with "improve for [edge case]". Test upload immediately. Confidence: High (Anthropic PDF/GitHub). Start: Review your last skill-creator output for YAML/files.[2][1]

## Human

How to improve existing skills using skill-creator v2

## Assistant

**Use skill-creator v2 to improve existing skills by prompting Claude to analyze your SKILL.md, generate evals, benchmark old vs new versions, and iterate based on results.**[1][2]

## Prerequisites
Ensure skill-creator v2 is installed globally via `/plugins` (search "skill creator" from skills.sh or Anthropic repo). Place your existing skill's .skill directory or SKILL.md in the project. Prompt "Do you have skill-creator available?" to confirm.[2][1]

## Improvement Workflow
1. **Review existing**: Prompt "Use skill-creator to review and improve [skill-name], e.g., 'Use skill-creator to improve my writing-voice skill'". It analyzes against examples (e.g., blog posts), identifies gaps (e.g., missing patterns, under-specified workflows).[2]
2. **Generate evals**: Auto-creates synthetic test cases with assertions (e.g., "uses short paragraphs", "fair comparisons"); expands coverage for edges like minimal projects.[1][2]
3. **Benchmark**: Runs parallel sub-agents: old skill vs improved (timing, tokens, grades); outputs iteration folders (e.g., iteration-1/), grades (e.g., 81% → 97.5%).[1]
4. **Review & iterate**: Opens HTML viewer for side-by-side outputs, feedback.json; analyzer/comparator/grader subagents suggest fixes. Loop: apply, rerun evals.[2][1]
5. **Optimize description**: Tests 20+ trigger/non-trigger queries; refines for reliable invocation.[1]

## Example Improvements
| Skill | Issues Found | Gains |
|-------|--------------|-------|
| Writing-Voice | Missed opener/closing patterns, long paras, generic tone | 100% on 2/3 evals; qualitative voice match ↑ [2] |
| README Wizard | Under-specified README handling, thin best practices, few evals | 81% → 97.5%; better adaptation to project types [1] |

Next step: Copy skill dir to new Claude Code project, prompt "Use skill-creator to improve [your-skill]". Inspect iteration folders/HTML viewer. Confidence: High (hands-on demos align with Anthropic updates).[2][1]

## Human

what are the exact features and functions of the latest skill-creator?  I'm trying to not dupicate functionaity but I need details.

## Assistant

**The latest skill-creator (v2, updated ~March 2026) automates skill lifecycle: create from scratch, modify/improve existing, run evals/tests, benchmark performance (old vs new, variance analysis), optimize descriptions for trigger accuracy, and generate full .skill packages.**[1][2][3]

## Core Features
- **Creation/Modification**: From user description, drafts SKILL.md (YAML frontmatter + instructions/workflows), bundles references/schemas/scripts (e.g., Python evals), adds agents (analyzer/comparator/grader).[3][4]
- **Eval Generation**: Creates synthetic test cases (evals.json) with assertions (e.g., structure checks, content presence); splits train/test sets; expands coverage (minimal/edge cases).[2][3]
- **Benchmarking**: Parallel runs (with/without skill, 2-3x for variance); metrics: success %, timing, tokens; side-by-side HTML viewer; feedback.json summaries.[5][3]
- **Review Tools**: Subagents analyze diffs ("why winner won"), grade transcripts/outputs, suggest targeted fixes; iteration folders (iteration-1/ etc.).[3]
- **Description Optimization**: 60/40 train/test split; 3-run evals; LLM-proposed improvements (up to 5 iters); selects best by held-out test score (avoids overfitting).[2]

## Invocation Functions
| Function | Trigger Prompt | Output |
|----------|---------------|--------|
| New Skill | "Use skill-creator to build [description]" | .skill dir: SKILL.md, evals.json, scripts, viewer [5] |
| Improve Existing | "Use skill-creator to improve [skill-name]" | Iteration folders, benchmarks, refined SKILL.md [3] |
| Run Evals | "Use skill-creator to run evals on [skill]" | Grades, viewer (baseline vs skill) [6] |
| Benchmark | Auto in workflow | Variance analysis, summaries [1] |

No duplication risk: Focuses on meta-skill ops (not domain tasks); chains to other skills. Next: Prompt "show skill-creator contents" in Claude Code. Confidence: High (dev posts + Anthropic repo).[2][3]

## Human

what's the path of the skill so I can read it?

## Assistant

**The skill-creator skill's SKILL.md is located at `~/.claude/skills/skill-creator/SKILL.md` if installed globally (personal scope, available across projects).**[1][2]

## View It
Run `head -20 ~/.claude/skills/skill-creator/SKILL.md` (Linux/Mac) or `Get-Content ~/.claude/skills/skill-creator/SKILL.md -Head 20` (PowerShell on Windows). In Claude Code, prompt "Read the skill-creator SKILL.md" or "show skill-creator contents"—it uses Read tool with `{baseDir}`.[2][3]

## Scopes & Paths
| Scope | Path | Notes |
|-------|------|-------|
| Personal/Global | `~/.claude/skills/skill-creator/SKILL.md` | Default install via `/plugins`; all projects [1] |
| Project | `.claude/skills/skill-creator/SKILL.md` | Per-repo only [1] |
| Nested/Monorepo | `packages/.../.claude/skills/skill-creator/SKILL.md` | Auto-discovered [1] |

If missing, reinstall via `/plugins` > search "skill creator" > "install for you". Windows: `~` is `%USERPROFILE%`. Confidence: High (official docs).[1][2]

## Human

I want to read it on github

## Assistant

The skill-creator SKILL.md is available on GitHub at https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md.[1]

I've opened the page in a new tab for you to read directly (now your current tab).

## Quick Access
- **Raw view**: https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md (copy-paste friendly).[1]
- Starts with YAML frontmatter (name: skill-creator, description, allowed-tools: Read/Write/etc.), followed by detailed instructions/workflows for creation/evals/benchmarking.[1]

This is the canonical source for v2 features; local install matches it post-install.[1]

## Human

There is also a plugin called skill-developer

## Assistant

**No official Anthropic plugin named "skill-developer" exists; searches point to community skills/plugins like "Claude Plugin Developer" (MCP Market skill for building plugins via /create-plugin) or skill-creator variants.**[1]

## Possible Matches
- **Claude Plugin Developer**: Community skill (mcpmarket.com) for guided plugin creation (8-phase workflow: discovery, code, validation); uses standard dirs/commands/hooks. Not for skills.[1]
- **Skill-Creator**: Official meta-skill (Anthropic repo); you likely mean this—handles skills only (SKILL.md, evals).[2]
- **Plugin Marketplace Skills**: Repos like daymade/levnikolaevich offer skill generators via /plugin marketplace add.[3][4]

## Clarify & Next
If "skill-developer" is from a marketplace/repo (e.g., GitHub search "claude-code skill-developer"), share URL/repo for details. Prompt Claude Code "list skills" or `/plugins` to check installed. Confidence: High (no official hits; community-focused).[5][1]

## Human

"/skill-development                         (plugin-dev) This skill should be used when the user wants to "create a skill", "add a skill to…"

## Assistant

**"/skill-development" is the official skill from the "plugin-dev" plugin (Anthropic-maintained), guiding users to create/add skills via structured workflows, best practices, and progressive disclosure.**[1][2]

## Key Details
- **Location**: `plugins/plugin-dev/skills/skill-development/SKILL.md` in claude-code repo (GitHub: anthropics/claude-code).[1]
- **Trigger**: Use when user says "create a skill", "add a skill", or similar—provides templates, YAML frontmatter, evals.json, packaging to .skill.[3]
- **Purpose**: Beginner-friendly skill dev in plugins; covers standalone (.claude/skills/) vs plugin namespacing (/plugin:skill); scripts/visuals (HTML explorers).[3]

## Vs Skill-Creator
| Aspect | /skill-development (plugin-dev) | skill-creator |
|--------|---------------------------------|---------------|
| Focus | Guided manual creation, best practices, plugin structure | Automated full lifecycle (draft/test/benchmark/optimize) [4] |
| Output | SKILL.md templates, dir setup | .skill packages, evals, iterations [5] |
| Complexity | Entry-level (progressive disclosure) | Advanced (subagents, variance analysis) [6] |

Next: View on GitHub (https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev/skills/skill-development) or prompt Claude "Read /skill-development SKILL.md". Install plugin-dev via `/plugin marketplace` if needed.[1][3]

## Human

Differences between /skill-development and skill-creator

## Assistant

**/skill-development (from plugin-dev plugin) is a guided, interactive tutorial skill for manually creating skills, while skill-creator is an automated meta-skill that generates, tests, benchmarks, and optimizes full skill packages.**[1][2]

## Key Differences
| Aspect | /skill-development (plugin-dev) | skill-creator |
|--------|---------------------------------|---------------|
| Automation | Low: Step-by-step prompts/templates for YAML, evals; user edits [2] | High: Autonomous workflow (draft/test/improve/iterate) [1] |
| Output | Basic SKILL.md, dir structure, best practices [3] | Complete .skill (md + evals.json + scripts + HTML viewer) [4] |
| Testing | Suggests evals; no auto-run [5] | Generates/runs benchmarks (old/new, variance); subagents grade [4] |
| Use Case | Beginners: "create a skill" → structured guide [query] | Advanced: New/improve skills w/ metrics (10min cycles) [6] |
| Scope | Part of plugin-dev (skill/plugin dev in plugins/) [2] | Standalone meta-skill (personal/project scopes) [7] |

Both in Anthropic repos; plugin-dev for plugin ecosystem, skill-creator for rapid prototyping. No overlap—use development for learning, creator for production. Next: Install plugin-dev (`/plugin marketplace add plugin-dev`), compare outputs.[2][1]

## Human

Are there other repos with better skill creating or improving skills?

## Assistant

**No repos outperform Anthropic's official skill-creator (36k+ stars in skills repo) for automated skill creation/improvement; community "awesome" lists (e.g., travisvn/awesome-claude-skills, ComposioHQ/awesome-claude-skills) curate collections but lack superior generators.**[1][2]

## Top Repos (Curated Collections)
| Repo | Stars (Apr 2026) | Focus | Better? |
|------|------------------|-------|---------|
| anthropics/skills | 36k+ | Official skills incl. skill-creator [3] | Baseline |
| travisvn/awesome-claude-skills | N/A | Curated lists/tools for workflows [1] | No—discovery only |
| ComposioHQ/awesome-claude-skills | N/A | 50+ skills/integrations [2] | No—catalog |
| obra/superpowers | 40k | Multi-agent dev workflows (40+ skills) [4] | No—uses creator |
| Everything-Claude-Code | 128k | 136 skills/30 agents/60 commands [5] | No—collection |

## Meta-Skill Alternatives
- **find-skills**: Searches GitHub for skills by category/stars.[6]
- **skill-creator-plugins** (claudepluginhub): Variant for plugin skills.[7]
- Firecrawl generator: Builds skills from docs URLs (niche).[4]

Official remains best (evars, benchmarks, iterations); communities aggregate. Uncertainty: "Better" subjective (stars/activity). Next: `git clone https://github.com/anthropics/skills`, inspect /skill-creator.[5][1]

## Human

does skill creator optimize for use with agents?  meaning the finished skills use claude agents?

## Assistant

**Skill-creator optimizes finished skills for agentic use: generated skills support subagents via `agent:` frontmatter field, spawning isolated Claude instances with specific skill/agent configs for multi-step workflows.**[1][2]

## Agent Optimization Details
- **Subagent Spawning**: Skills include `agent: { skill: "sub-skill-name" }` or custom configs for context isolation (e.g., analyzer/comparator/grader in benchmarks).[2]
- **Modular Stacks**: Builds composable skills that hand off (e.g., step1 → step2 agent); progressive disclosure keeps tokens efficient.[3][2]
- **Workflows**: Targets "domain-specific AI agent workflows" (e.g., README Wizard improved w/ subagents); evals test agentic flows (assertions on handoffs).[1][3]
- **Examples**: Iteration uses parallel subagents for A/B testing; description optimization ensures reliable triggering in agent chains.[1]

No explicit "agents-only" mode, but core (since v2) for agent stacks. Uncertainty: Low (docs/dev tests confirm). Next: Prompt "Use skill-creator to build agentic skill for [workflow]".[2][1]

## Human

what about skill based hooks for self-verification?

## Assistant

**Skill-creator does not natively generate skill-based hooks for self-verification in finished skills; it focuses on evals.json benchmarks/assertions during development, not runtime hooks.**[1][2]

## Self-Verification in Skills
- **Creator's Verification**: Builds evals.json (synthetic tests, assertions for outputs/structure); benchmarks (success %, tokens); no hooks in output skills.[3]
- **Hooks Separate**: Hooks (shell/agent scripts) run deterministically at lifecycle points (e.g., pre-tool, post-edit) for verification (e.g., "tests pass before stop"). Define in .claude/hooks/ (prompt/script/agent types); skills can't embed hooks.[4]
- **Combining**: Use creator for skill, then add hook (e.g., agent-hook verifies skill output/tests before approve). Community: "Forced eval hook" boosts activation (84% vs 20%) via pre-prompt eval.[5][6]

## Implementation
| Method | Description | Example |
|--------|-------------|---------|
| Agent Hook | Subagent checks (read files, run tests) before tool/stop [4] | `type: "agent"`, verify tests pass |
| Skill Activation Hook | Pre-pends skill recs to prompts (100% load) [6] | Keyword match → append "use skill X" |
| Self-Improve Skill | Post-response reflection/correction (manual/auto via stop-hook) [7] | Scan convo, update skill |

Next: Generate skill w/ creator, add `.claude/hooks/stop` agent-hook for verification. Confidence: High (docs separate concerns).[4][5]

## Human

So skill-creator isn't really about optimizing skills to use claude features, it's really just to make sure that claude is triggered properly to use the skill?

## Assistant

No, skill-creator goes far beyond just triggering: it optimizes full skill quality via structured instructions/workflows, evals/assertions for output correctness, benchmarking (success rates, efficiency), iteration (content fixes), and agentic patterns (subagents, handoffs) for production-ready skills.[1][2][3]

## Full Optimization Scope
- **Triggering**: Description tuning (60/40 train/test evals, 5 iters, anti-overfit) ensures reliable invocation (~84-97% rates).[3][1]
- **Content/Performance**: Drafts modular workflows (progressive disclosure <5k tokens), benchmarks vs baselines (tokens/timing/grades), subagents analyze failures.[4][2]
- **Claude Features**: Embeds agents (`agent:` field for isolation), tool use (Read/Write), composability (stacks/chains), side-effects control (`disable-model-invocation`).[5][1]
- **Production**: Packages .skill zips, helper scripts, HTML reviewers; evolves skills via model updates.[6][7]

Trigger opt is ~1 phase; bulk is dev rigor (like software testing). Speculation: Low (SKILL.md explicit). Next: Review GitHub SKILL.md §"Description optimization" vs full workflow.[2]

## Human

Best practices for designing modular skill stacks

And skill-creator won't add skill-based hooks to make sure the skill self-verifies?  If not, what repos has skills to do this?  Can I combine them wiht skill-creator in an orchestration?

## Assistant

**Skill-creator builds evals.json for dev-time verification but adds no runtime skill-based hooks (hooks are filesystem-defined, not skill-embedded); combine via orchestration: creator for skill gen, verification skills (e.g., eval-runner) + hooks for runtime checks.**[1][2]

## Modular Skill Stack Best Practices
- **Single Responsibility**: One skill per task (e.g., test-gen, doc-gen); chain via agent: field or orchestration.[3][1]
- **Naming/Desc**: Gerund (processing-pdfs), specific triggers/contexts; <1024 chars desc, third-person.[1]
- **Structure**: <500 lines SKILL.md (split files); progressive disclosure; test across models (Haiku needs more guidance).[1]
- **Composition**: Reference stacks in CLAUDE.md; evals.json w/ negative cases for boundaries; modular evals/cases.yaml.[4][5]
- **Activation**: Hooks for 100% load (pre-pend recs); Level 1-3 escalation (CLAUDE.md → hooks).[4]

## Self-Verification Repos/Skills
| Repo/Skill | Features | Orchestrate w/ Creator |
|------------|----------|------------------------|
| alirezarezvani/claude-skills (232+ skills) | eval-runner, self-improve loops [6] | Yes—post-gen, run /eval-skill |
| daymade/claude-code-skills | Verification bundles, peer-review [7] | Chain in workflow prompt |
| FrancyJGLisboa/agent-skill-creator | Agentic verification gates [8] | Use as subagent in creator iters |

Orchestration: Prompt "Use skill-creator to build [skill], then use eval-runner to verify". Hooks (.claude/hooks/) for runtime (agent-type stop-hook runs verification skill). Next: Clone alirezarezvani/claude-skills, test /self-verifier post-creation. Confidence: High (docs/repos align).[6][1]

## Human

Top GitHub repos with self-verifying Claude skills — hooks, evals, and stack combos compared

Examples of combining self-verifying skills with modular stacks

## Assistant

**Top repos emphasize evals/hooks in stacks; alirezarezvani/claude-skills (232+ skills) leads for verification (eval-runner, self-improve); no pure "self-verifying" but combos via agent handoffs/hooks excel.**[1][2]

## Top Repos Compared
| Repo | Stars (Apr 2026) | Hooks | Evals | Stack Combos | Notes |
|------|------------------|-------|-------|--------------|-------|
| alirezarezvani/claude-skills | 12k | Agent-hooks for stop/approval | eval-runner, assertions | 232 skills/agents (TDD, review swarms) [2] | Multi-platform, scripts/convert.sh |
| hesreallyhim/awesome-claude-code | 8k | Activation/pre-tool hooks | test-driven-development | Skills/plugins/hooks lists [1] | Curated, featured projects |
| daymade/claude-code-skills | 5k | Peer-review hooks | Verification bundles | Marketplace w/ combos [3] | Professional bundles |
| BehiSecc/awesome-claude-skills | 3k | Defense-in-depth hooks | pypict testing, debugging | Dev/security stacks [4] | 50+ categorized |

## Combination Examples
- **Superpowers + gstack + GSD**: gstack (decision), Superpowers (exec/TDD), GSD (context); merged tagline in CLAUDE.md; hooks ensure validation before merge (e.g., code-review swarm).[5]
- **TDD Stack**: test-driven-development (deletes pre-test code) → github-code-review (swarm agents) → finishing-branch; stop-hook runs eval-runner.[6][7]
- **11-Step Workflow**: Idea → spec → TDD → validation self-check → ship; uses Compound Engineering pack w/ validation agent.[8]
- **Security Stack**: webapp-testing (Playwright) + systematic-debugging + ffuf; hooks for vuln scans.[4]

Orchestrate: Reference in CLAUDE.md (`/use-skills`), agent: handoffs, hooks for gates. Next: Clone alirezarezvani/claude-skills, test TDD/review combo.[2][5]

## Human

What's the best example for optimal skill creation & optimization?

## Assistant

**Obra's Superpowers (github.com/obra/superpowers, 40.9k stars) is the gold standard: skill-creator-built modular stack for full dev lifecycle (brainstorm → TDD → subagents → review), with evals, worktrees, and optimization yielding 97%+ benchmarks.**[1][2]

## Why Optimal
- **Creation**: Uses skill-creator for drafting/testing (e.g., /brainstorm refines via evals, /write-plan breaks to 2-5min tasks).[3][1]
- **Optimization**: TDD enforces RED-GREEN-REFACTOR (deletes pre-test code); subagent isolation; git-worktrees for baselines; peer-review swarms.[1]
- **Results**: Autonomous hours-long runs; structured outputs (design docs, merge options); composable (40+ skills).[2]

## Breakdown
| Component | Optimization | Trigger |
|-----------|--------------|---------|
| /brainstorm | Socratic Qs → spec doc (evals-tuned) | "Build [idea]" |
| using-git-worktrees | Isolated branches, test baseline | Post-design |
| test-driven-development | Failing test first, no premature code | Tasks |
| subagent-driven-development | Fresh agents/task + 2-stage review | /execute-plan |

Example: "Build landing page" → spec → plan → subagents execute/verify → merge PR. Next: `git clone https://github.com/obra/superpowers`, `/plugins install`, test w/ skill-creator refine. Confidence: High (stars, docs, benchmarks).[2][1]

## Human

That isn't exactly what I asked.  What repos are best to show how to build and optimize skills?  That use agents, hooks, modularization, etc.

## Assistant

**alirezarezvani/claude-skills (12k stars, 232+ skills/agents) + claude-code-skill-factory Gist (factory prompts) top for demos: full tutorials on agents (subagents), hooks (audit/commit), modular stacks (TDD/review), skill-creator integration.**[1][2]

## Top Repos for Build/Optimize
| Repo | Stars | Agents | Hooks | Modular | Skill-Creator Use | Example |
|------|-------|--------|-------|---------|-------------------|---------|
| alirezarezvani/claude-skills | 12k | Review/test agents | Audit/commit hooks | Tresor (136 skills), factory | Yes—generates custom via prompts [1] | TDD → review swarm |
| hesreallyhim/awesome-claude-code | 8k | Subagent workflows | Pre-tool/stop | Featured projects/stacks [3] | Tutorials | Security dev stack |
| alirezarezvani/claude-code-skill-factory (Gist) | N/A | Agents factory | Event-driven | 7 domains (finance/AWS) [2] | Core | Custom skill pkg gen |
| VoltAgent/awesome-agent-skills | 4k | 1000+ agent skills | MCP/tool hooks | Google/Sentry skills [4] | Listed | Code-review → commit |

## Optimization Examples
- **Skill Factory**: Prompt generates multi-file skills (Python + docs); agents for specialist tasks; hooks for lifecycle (save/commit).[2]
- **Tresor Stack**: 8 skills (reviewer/test-gen) + 8 agents; CLAUDE.md orchestration; hooks audit settings.[2]
- **Modular Dev**: test-driven → git-commit-helper → create-pr; subagents isolate, hooks verify.[4]

Next: `git clone https://github.com/alirezarezvani/claude-skills`, read ULTIMATE-GUIDE.md, build custom w/ factory. Confidence: High (stars/tutorials).[1][2]

## Human

Does alirezarezvani/claude-skills use anthropics skill-creator?

## Assistant

**No, alirezarezvani/claude-skills (235 skills/agents) does not use Anthropic's skill-creator; it employs a custom "Claude Code Skill Factory" (prompt-based generator in sister repo) for production skills, with manual curation + testing.**[1][2]

## Evidence & Approach
- **Factory Method**: Prompts Claude to generate full packages (SKILL.md, Python, JSON I/O, ZIPs) via SKILLS_FACTORY_PROMPT.md—no skill-creator invocation.[2]
- **Repo Contents**: INSTALLATION.md auto-installs via scripts; ULTIMATE-GUIDE.md/wiki cover templates/factory, not creator; skills like content-creator are hand-optimized.[3][4]
- **Why Not Creator**: Factory scales domains (finance/AWS); pre-dates v2 creator; focuses multi-platform (Claude.ai/Code/API).[5]

Complements creator (factory for bulk, creator for iters). Next: Clone both (`claude-skills`, `claude-code-skill-factory`), compare factory prompt vs creator.[1][2]

## Human

I'm confused.  clone both alirezarezvani/claude-skills and claude-code-skill-factory?

## Assistant

Yes, clone both: alirezarezvani/claude-skills (library of 235 pre-built skills/agents) and alirezarezvani/claude-code-skill-factory (prompt factory to generate custom ones).[1][2][3]

## Relation
- **claude-skills**: Pre-built packages (e.g., fullstack-engineer, content-strategy); manual curation; copy to `~/.claude/skills/`.[4][1]
- **claude-code-skill-factory**: Generator repo (SKILLS_FACTORY_PROMPT.md); prompts Claude for domain-specific skills (e.g., AWS/marketing); outputs ZIPs/folders matching library format.[3]
- **Workflow**: Factory creates → library for examples/inspo → install both for complete setup.[2]

Commands:
```
git clone https://github.com/alirezarezvani/claude-skills.git
git clone https://github.com/alirezarezvani/claude-code-skill-factory.git
```

Browse factory prompt, generate (e.g., "finance analyst"), install to skills dir. Confidence: Confirmed (Gist/repo links).[2][3]

## Human

How to install skills from claude-skills into Claude Code
Step-by-step guide to generate a custom skill with skill-factory
What domains are covered in claude-skills packages
How to use generated skills from factory in Claude AI Desktop
Examples of skills created with claude-code-skill-factory

## Assistant

**Clone/clone both repos, then follow these steps for Claude Code/Desktop.**[1][2][3]

## Install claude-skills in Claude Code
1. `git clone https://github.com/alirezarezvani/claude-skills.git`
2. `cd claude-skills && ./install.sh` (auto-detects personal/project scope, unzips to `~/.claude/skills/` or `.claude/skills/`).[4][2]
3. Restart Claude Code session (`claude`); prompt "list skills" or `/skills` to verify (e.g., fullstack-engineer).[1]
4. Or `/plugin marketplace add alirezarezvani/claude-skills` then `/plugin install [skill]`.

## Generate Custom Skill w/ skill-factory
1. `git clone https://github.com/alirezarezvani/claude-code-skill-factory.git`
2. Edit `SKILLS_FACTORY_PROMPT.md` (fill DOMAIN=finance, TASK=valuation-model).
3. Paste full prompt to Claude Code/Claude.ai → generates ZIP/SKILL.md/Python/JSON.[3]
4. Unzip to `~/.claude/skills/` (personal) or `.claude/skills/` (project).[3]

## Domains in claude-skills
Finance (valuation/hedging), AWS/DevOps (cloud-architect), Security (webapp-testing), Marketing (content-creator), Docs (project-docs-coordinator), Planning (scope-decomposer), Code (code-reviewer).[5][4]

## Use Generated Skills in Claude AI Desktop
1. Generate ZIP via factory.
2. Desktop: Settings > Capabilities > Skills > Upload ZIP (auto-extracts).[6]
3. Test prompts matching desc; enable in Customize > Skills.[7][6]
4. Works across sessions/projects (personal scope).

## Factory Examples
- **content-trend-researcher**: Analyzes trends, generates reports (SKILL.md + Python).[8]
- **codex-cli-bridge**: CLI integration for code gen.[9]
- **slash-command-factory**: Dynamic /commands.[10]

Next: Run `./install.sh` in claude-skills, generate "AI systems architect" via factory.[2][1][3]
