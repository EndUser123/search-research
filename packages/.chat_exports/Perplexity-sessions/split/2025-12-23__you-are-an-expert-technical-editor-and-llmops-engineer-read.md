---
title: "You are an expert technical editor and LLM‑ops engineer.
Read the entire conversation below (post + comments). Remove na"
date: "2025-12-23"
mode: "COPILOT"
uuid: "e2fed9fe-56e9-4496-970d-b4e39f98cb5e"
entry_count: 1
---

## Human

You are an expert technical editor and LLM‑ops engineer.
Read the entire conversation below (post + comments). Remove navigation, ads, jokes, and repeated points. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works.
Produce a rewritten version of the thread that:
Keeps every distinct insight, workflow, or configuration detail.
Preserves all mentions of tools, agents, actions, and integrations (e.g., GitHub actions, zen-mcp, codex, Copilot, MCP, hooks, CLAUDE.md, pre‑commit, etc.) and what people actually do with them.
Removes repeated restatements of the same idea unless they add a new nuance.
After the rewrite, add a section called “Operational patterns and setups” where you explicitly list:
Multi-model review flows (e.g., “I use zen-mcp and have all 3 review the code, then have Claude consolidate and apply fixes”).
Automation patterns (GitHub auto‑review actions, agents/skills triggered at the end of each dev phase, hooks that detect ‘fallback’/‘backwards compatible’ code, pre‑commit checks referencing code-patterns.md).
Guardrail artifacts (CLAUDE.md, .claude/development-principles.md, code-patterns.md) and the key rules they encode.
Add a final section “Practical recommendations” that distills the most useful advice into concrete steps another developer could implement (e.g., “Set up zen‑mcp with three reviewers and a Claude consolidation agent”, “Add a hook to block ‘fallback’ code paths”, “Configure codex or similar as a PR reviewer only, not auto‑fixer”).
Format the answer with short sections and bullets. Be concise but do not omit any unique workflow or recommendation from the conversation.

## Assistant

Claude’s first-pass code is often buggy, over-engineered, and prone to “fallback” and “backwards compatible” hacks, so people are building layered review workflows, automation, and guardrail artifacts (CLAUDE.md, development-principles.md, code-patterns.md) to control it rather than trusting one-shot generations. Human judgment remains essential, with LLMs positioned as aggressive reviewers, pattern enforcers, and code-editing agents wired into Git, GitHub, MCP, and hooks.[1]

***

## Core ideas from the thread

- A “hate review” prompt run on `git diff` reveals that first-pass Claude 4.5 Opus code routinely contains serious bugs and design flaws, even when it initially looks mergeable.[1]
- Running this review once or twice surfaces real issues, but repeated runs drift into made‑up problems and heavy over‑engineering, so suggestions must be filtered by a human.[1]
- Multiple users report recent regression in Opus 4.5 code reliability, needing several self‑reviews to catch critical bugs that did not appear a week earlier.[1]

- Community consensus: Claude is best used as a **pair programmer and reviewer**, not as a one‑shot code generator or sole reviewer.[1]
- Static analysis, linters, pre‑commit checks, and custom pattern detectors are treated as non‑negotiable additional layers.[1]
- Multi‑model setups (Claude + codex + Copilot, etc.) and GitHub automations are common to broaden coverage and reduce blind spots.[1]

***

## Guardrails via principles and artifacts

- One user keeps `.claude/development-principles.md` and imports it via `CLAUDE.md`, explicitly instructing Claude to follow SRP, DRY, KISS, and YAGNI to avoid over‑engineering.[1]
- Another extends CLAUDE.md with rules like “respect encapsulation” and “single source of truth,” and suggests using inheritance when a feature seems to require duplicate code.[1]
- Planning is emphasized: think through likely future extensions and the software lifecycle so Claude builds a structure that does not require massive refactors later.[1]

- A user proposes a dedicated `code-patterns.md` that enumerates anti‑patterns with “Always use” / “Never use” guidance and examples.[1]
- `code-patterns.md` is referenced prominently in CLAUDE.md so the agent repeatedly sees and adheres to the same constraints.[1]
- These patterns are also encoded in a blocking pre‑commit custom detection script; if a pattern is detected, the message points directly to `code-patterns.md` so the developer (and Claude) see the rationale.[1]

- One user has “a plethora of guidelines, CLAUDE.md, hooks, preflight script with a ton of custom checks, linting rules,” all now automated through hooks after initially being run manually to understand their behavior.[1]

***

## Automated reviewers and multi-model flows

- Anthropic’s official GitHub auto‑review action for Claude is mentioned as a way to have Claude review PRs without using a personal subscription, especially when tied to an Anthropic console API account.[1]
- Some note the auto‑reviewer “misses a lot” unless given explicit direction and constraints.[1]

- Several users use `codex` as a **GitHub auto reviewer**, called via `@codex` on PRs.[1]
- `codex` is praised as “king of code reviews”: excellent at pointing out bugs with minimal context, but users intentionally do not let it auto‑fix; it is kept as a reviewer only.[1]

- One team uses Copilot for auto‑reviews on every PR, then has Claude consume those comments via the GitHub MCP and apply changes “where appropriate.”[1]
- Another user prefers the GitHub CLI over the GitHub MCP for integrating with Claude.[1]

- A user with zen‑mcp:  
  - Has “all 3” models review the code (implied: three different LLMs/models).[1]
  - Then asks Claude to consolidate the feedback and apply it to the code.[1]
  - Reports this works well even on other people’s code.[1]

- A user defines a dedicated **code‑review agent** in an `.md` agent file, with:  
  - `name: code-reviewer`, description emphasizing balanced, evidence‑based analysis, tools: `Read`, `Grep`, `Glob`, `Bash`, model: `opus`.[1]
  - Explicit “Anti‑Sycophancy Directives” (never sugarcoat, provide arguments for and against, require `file:line` for each claim, state confidence levels, question assumptions, prioritize objective truth, say “unsure” rather than defaulting to approval).[1]
  - Execution steps: run `git diff` / `git diff --cached`, focus on modified files, analyze against a checklist, present dual‑perspective output.[1]
  - Review checklist including: simplicity/readability, naming, duplication, error handling, secrets/API keys, input validation, tests, performance, no bandaid fixes, and especially **no backwards compatibility hacks or fallback logic masking issues**.[1]
  - Structured output format with tables for issues, “arguments this code is sound,” “arguments this code has problems,” and a final verdict with assessment, confidence, and recommendation.[1]

- Another user uses custom agents, slash commands, skills, and hooks so that at the end of each development phase a routine runs that:  
  - Performs “actual security checks.”  
  - Runs other bug and completeness checks.  
  - Is described as methodical, always firing, and always finding issues.[1]

***

## Handling over-engineering and hallucinated issues

- The original “hate review” prompt is:  
  - “You wrote the code that currently is in git changes. Do a git diff and now pretend you're a senior dev doing a code review and you HATE this implementation. What would you criticize? What are the edge cases I'm not seeing?”[1]
- OP notes this will **always** find something, even on good code; running it once or twice is useful, but more than that tends to surface fake or trivial issues.[1]
- Variants like “critical issues only” or “but don’t force it if code is already good” still tend to produce “critical” findings that are not actually critical.[1]

- A Hacker News anecdote: asking Claude to “improve” code 200 times led to increasingly extreme over‑engineering, reinforcing that not every suggestion should be implemented.[1]
- Community guidance: treat such prompts as stress tests; if a hostile reviewer can only find minor issues, the code is probably fine.[1]

- Several users describe Claude inventing problems, e.g., spending 45 minutes debugging issues that turned out to be fabricated despite repeated “FOUND IT!” claims.[1]
- Another warns that prompts like “Ask me any questions for better clarity before starting” cause LLMs to ask low‑value, obvious questions, wasting time and shifting responsibility for clarity away from the human.[1]

***

## Fallbacks, backwards compatibility, and refactoring

- One user says the best instruction for Claude-written code is “remove all those fallbacks,” reporting that fallbacks it writes have **never** improved the codebase and that Claude “loves” adding them.[1]
- OP confirms: even with explicit instructions “no fallbacks or default values, throw if missing, delete everything the old solution uses,” Claude implemented the new path with the old approach as a fallback underneath.[1]

- To counter this, a user suggests adding a **hook** that matches on common fallback language such as “fallback” and “backwards compatible,” noting Claude often labels such sections in comments and the hook can catch them.[1]

- Another user notes Claude “hates aggressive refactoring”; automated guidance (principles, patterns) helps, but explicit steering is still required when it resists large structural changes.[1]
- OP considers this double‑edged: reluctance to refactor is good for mature codebases where refactors must be deliberate, but on a young codebase it leads to fragmentation unless constantly steered.[1]

***

## Operational patterns and setups

### Multi-model review flows

- **zen‑mcp tri‑review + Claude consolidation**  
  - Use zen‑mcp to have three different models review the same code changes.[1]
  - Instruct Claude to aggregate all feedback and apply the agreed‑upon fixes, including for other people’s code.[1]

- **Copilot + Claude via GitHub MCP**  
  - Copilot runs auto‑reviews on every PR.[1]
  - Claude consumes Copilot’s comments through the GitHub MCP and selectively applies changes.[1]

- **codex as PR reviewer only**  
  - Install codex as a GitHub app and call it with `@codex` on PRs.[1]
  - Use codex strictly as a reviewer that flags bugs with minimal context; do not grant it auto‑fix permissions.[1]

- **Claude + human layered review**  
  - Claude performs an initial review (via auto‑review action or local diff review).[1]
  - A human performs the final review, especially to discard over‑engineering and non‑issues.[1]

### Automation patterns

- **Anthropic GitHub auto‑review action**  
  - Configure Claude as a PR reviewer using Anthropic’s official GitHub action connected to a console API account so team usage doesn’t consume individual subscriptions.[1]

- **End‑of‑phase agent runs (skills + hooks)**  
  - Define custom agents and skills that run at the end of each development phase.[1]
  - Automation includes security checks, bug checks, and completeness checks, and is described as methodical and reliably finding issues.[1]

- **Pre‑commit pattern enforcement**  
  - Maintain `code-patterns.md` with anti‑patterns and “Always use” / “Never use” entries.[1]
  - Implement a blocking custom detection script in pre‑commit that scans diffs for those patterns and blocks them, printing an error message that links directly to `code-patterns.md`.[1]

- **Hooks for fallbacks and backwards compatibility**  
  - Add hooks that scan code and comments for phrases like “fallback” and “backwards compatible.”[1]
  - Use them to block or at least flag newly introduced fallback paths or compatibility hacks that Claude tends to introduce.[1]

- **Preflight script + linting + hooks**  
  - Run a preflight script with “a ton of custom checks” plus linting rules before commit or merge.[1]
  - Initially run these checks manually to understand their output, then automate them via hooks once tuned.[1]

- **git diff–driven agents**  
  - Code review agent MD file defines execution: run `git diff` or `git diff --cached`, focus on modified files, review against checklist, and output structured findings with `file:line` references and confidence levels.[1]

### Guardrail artifacts and encoded rules

- **CLAUDE.md**  
  - Central file that imports other principle documents (e.g., `.claude/development-principles.md`) and references `code-patterns.md`.[1]
  - Encodes: SRP, DRY, KISS, YAGNI; respect encapsulation; single source of truth; preference for inheritance over duplication in some cases.[1]

- **`.claude/development-principles.md`**  
  - Holds core development principles for the repo and is wired into CLAUDE.md.[1]
  - Functions as the primary “quality spec” for how Claude should structure code and avoid over‑engineering.[1]

- **`code-patterns.md`**  
  - Lists patterns to **never** repeat with “Always use” / “Never use” rules and examples.[1]
  - Is referenced in CLAUDE.md and by pre‑commit hooks; when a violation is detected, the error message points explicitly to this file.[1]

- **Agent MD config for code-reviewer**  
  - Name, description, tools, model, anti‑sycophancy directives, execution plan, checklist, and output format (change summary, issues table, dual‑perspective analysis, verdict).[1]
  - Checklist explicitly bans “backwards compatibility hacks” and “fallback logic masking issues.”[1]

***

## Practical recommendations

- **Use a structured “hate review” once, not endlessly**  
  - After Claude writes code, run a single structured diff review: “You wrote the code in `git diff`. As a senior dev who hates this implementation, what would you criticize? What edge cases am I missing? Critical issues only.”[1]
  - Manually pick 1–2 real issues to fix; ignore trivial or clearly over‑engineered suggestions.[1]

- **Create and wire up guardrail files**  
  - Add `.claude/development-principles.md` with SRP, DRY, KISS, YAGNI, respect for encapsulation, and single source of truth.[1]
  - Create `code-patterns.md` listing banned patterns (e.g., silent fallbacks, “backwards compatible” hacks, bandaid fixes) with “Always use” / “Never use” rules and examples.[1]
  - Reference both in `CLAUDE.md` so every Claude session is constrained by these documents.[1]

- **Set up pre‑commit and hooks**  
  - Implement a pre‑commit script that scans diffs for patterns defined in `code-patterns.md` and blocks commits when they appear, printing a message that links to the relevant section.[1]
  - Add another hook that scans for “fallback” and “backwards compatible” in code and comments and blocks or flags those additions.[1]

- **Deploy multi-model review flows**  
  - With zen‑mcp (or similar), configure three models to review the same diff, then have a Claude agent consolidate their feedback and apply only the overlapping or well‑justified changes.[1]
  - Configure codex or a similar tool as a PR reviewer (e.g., `@codex` in GitHub) but not as an auto‑fixer, and treat its suggestions as input to Claude or human editors.[1]
  - Use Copilot for continuous PR auto‑review, then have Claude read Copilot’s comments via GitHub MCP or the GitHub CLI and apply selective fixes.[1]

- **Automate end-of-phase checks**  
  - Define a code‑review agent MD file (like the “code-reviewer” example) with anti‑sycophancy rules, `git diff` execution steps, checklists, and dual‑perspective output.[1]
  - Trigger this agent plus security and completeness checks via hooks at the end of each development phase so they always run, not just when remembered.[1]

- **Keep humans in the loop and limit refactors**  
  - Treat Claude as an elite pair programmer and reviewer; always do a final human pass before merging to filter hallucinated issues and over‑engineering.[1]
  - For mature codebases, require explicit approval (from you) before allowing Claude to perform aggressive refactors; for new codebases, supervise it closely to avoid fragmentation and unintended fallbacks.[1]
