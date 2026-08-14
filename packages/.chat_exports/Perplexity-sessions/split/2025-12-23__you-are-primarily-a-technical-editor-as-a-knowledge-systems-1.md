---
title: "You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insi"
date: "2025-12-23"
mode: "COPILOT"
uuid: "64bc538e-0f97-4916-98d1-04823da3d4d2"
entry_count: 1
---

## Human

You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insights.

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and repeated points. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works.

Produce a rewritten version of the thread that:

Keeps every distinct insight, workflow, or configuration detail.

Preserves all mentions of tools, agents, actions, and integrations (e.g., GitHub actions, zen-mcp, codex, Copilot, MCP, hooks, CLAUDE.md, pre-commit, etc.) and what people actually do with them.

Removes repeated restatements of the same idea unless they add a new nuance.

After the rewrite, add a section called “Operational patterns and setups” where you explicitly list:

Multi-model review flows (e.g., “I use zen-mcp and have all 3 review the code, then have Claude consolidate and apply fixes”).

Automation patterns (GitHub auto-review actions, agents/skills triggered at the end of each dev phase, hooks that detect ‘fallback’/‘backwards compatible’ code, pre-commit checks referencing code-patterns.md).

Guardrail artifacts (CLAUDE.md, .claude/development-principles.md, code-patterns.md) and the key rules they encode.

Add a final section “Practical recommendations” that distills the most useful advice into concrete steps another developer could implement (e.g., “Set up zen-mcp with three reviewers and a Claude consolidation agent”, “Add a hook to block ‘fallback’ code paths”, “Configure codex or similar as a PR reviewer only, not auto-fixer”).

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow or recommendation from the conversation.

## Assistant

Claude’s first-pass code is often flawed, but the thread converges on a workable pattern: define strong guardrails (CLAUDE.md + principles files), add automated multi-model reviews, and treat Claude as a disciplined pair programmer rather than a one-shot generator.[1]

***

## Core prompt and its impact

- The OP uses a review prompt after implementing a feature:  
  “You wrote the code that currently is in git changes. Do a git diff and now pretend you're a senior dev doing a code review and you HATE this implementation. What would you criticize? What are the edge cases I'm not seeing?”[1]
- Running it once or twice routinely surfaces **critical flaws and big bugs** in Opus 4.5’s first-pass code, revealing that naive “merge on first try” workflows are risky.[1]
- The prompt can be pushed too far: you can run it many times and Claude will keep “finding” issues that are not real problems, leading to over‑engineering if you accept everything.[1]

***

## Guardrails and principles

- One user reports large quality gains from explicitly instructing Claude to follow SRP, DRY, KISS, and YAGNI via a `.claude/development-principles.md` file imported through `CLAUDE.md`.[1]
- Another adds to CLAUDE.md explicit rules: respect encapsulation, respect a single source of truth, and if a feature seems to require duplicate code, consider inheritance.[1]
- Planning is emphasized: think through features, likely future extensions, and broader lifecycle phases up front so the codebase doesn’t need heavy refactors later.[1]
- A different commenter argues that Claude will still often “recite” principles and then violate them, so you must **continually steer it back** when it strays; purely automated principle enforcement is not enough.[1]

***

## Code-patterns and pre-commit checks

- One approach:  
  - Identify patterns you **never** want repeated and write a `code-patterns.md` file listing anti‑patterns with “Always use” / “Never use” guidance and a few examples.[1]
  - Reference `code-patterns.md` prominently in `CLAUDE.md` so Claude “knows” these rules.[1]
  - Implement a custom detection script in pre‑commit that blocks commits when forbidden patterns appear; the error message should link directly to `code-patterns.md`.[1]
  - The author notes there are more advanced tools, but this simple pipeline works; pre‑commit is described as painful but effective.[1]
- OP says they already maintain: a rich `CLAUDE.md`, hooks, a preflight script with many custom checks, and linting rules; they initially did the reviews manually to understand the output, then automated via a hook once the process was well understood.[1]

***

## Fallbacks and backwards‑compat hacks

- One commenter’s strongest advice: tell Claude to “remove all those fallbacks”; they report never seeing a fallback implementation from Claude that **improves** the codebase, and claim the model “loves” adding them.[1]
- OP confirms this pattern: even with explicit instructions “no fallbacks or default values; throw if value is missing; delete everything used by the old solution”, Claude implemented the new way **plus** kept the old approach as a fallback.[1]
- Another user suggests adding a hook that matches on common fallback language (“fallback”, “backwards compatible”) because Claude often labels such code paths in comments; the hook then flags or blocks these changes.[1]

***

## Multi-model and automated review flows

- Several participants recommend using Anthropic’s official **GitHub auto-review action** to run Claude as a PR reviewer.[1]
- One user uses **codex** as an automatic reviewer:  
  - It runs in GitHub; they can `@codex` on a PR.  
  - They find codex “king of code reviews,” excellent at spotting bugs with little context but they **do not** let it auto‑fix issues.[1]
- Another uses **zen-mcp** to orchestrate three reviewers: all three models review the code, and then Claude consolidates the feedback and applies the fixes; this also works well when reviewing other people’s code.[1]
- One team uses **Copilot** to auto‑review every PR, then uses Claude plus the **GitHub MCP** to read Copilot’s comments and apply them where appropriate.[1]
- A commenter notes they use Claude as a GitHub reviewer via Anthropic console/API so team reviews don’t consume their personal subscription.[1]
- Another warns that even with Claude in GitHub as a reviewer, you still need multiple layers: more reviewers plus as many static analysis and linting tools as possible.[1]

***

## Custom agents, skills, and hooks

- A user highlights Anthropic’s ecosystem features: slash commands, skills, hooks, and custom agents.[1]
- Their workflow:  
  - Define a few agents and at least one skill.  
  - At the end of **each development phase**, they trigger these agents/skill to run checks.  
  - This includes dedicated **security checks**, other bug checks, and completeness checks; it’s methodical, always fires, and always finds issues.[1]
- Another full‑time developer uses an agent `.md` file named `code-reviewer` with:  
  - Model: `opus`.  
  - Tools: Read, Grep, Glob, Bash.[1]
  - Role: senior code reviewer giving balanced, evidence‑based analysis without sycophancy.[1]

**Anti‑sycophancy directives** in this agent:[1]
- Never sugarcoat issues.  
- Present arguments for **and** against code changes.  
- Require specific `file:line` references for every claim.  
- State confidence level explicitly (High/Medium/Low).  
- Question assumptions before concluding.  
- Prioritize objective truth over developer agreement.  
- If unsure, say so—do not default to approval.[1]

**Execution steps** for the agent:[1]
1. Run `git diff` (or `git diff --cached` for staged changes).  
2. Focus only on modified files.  
3. Analyze against a checklist.  
4. Present balanced dual‑perspective output.  

**Review checklist** includes:[1]
- Simple, readable code.  
- Well‑named functions and variables.  
- No duplicated code.  
- Proper error handling.  
- No exposed secrets or API keys.  
- Input validation present.  
- Good test coverage.  
- Performance considerations addressed.  
- No bandaid fixes (must treat root causes).  
- No backwards‑compatibility hacks.  
- No fallback logic that masks issues.[1]

**Output format** of this agent:[1]
- “Change Summary” (2–3 sentences).  
- “Issues Found” table: Priority (Critical/Warning/Suggestion), Issue, Evidence (`file:line`), Fix.  
- “Dual-Perspective Analysis” with two tables:  
  - Arguments code is sound (Aspect, Evidence `file:line`, Strength).  
  - Arguments code has problems (Aspect, Evidence `file:line`, Severity).  
- “Verdict”: Assessment (Sound/Problematic/Mixed), Confidence, and a concrete recommendation.[1]

***

## Human judgment and over‑engineering

- Several users stress that Claude will happily keep “improving” code hundreds of times, quickly drifting into extreme over‑engineering; one Hacker News example asked for 200 rounds of “improve” and the code became absurdly complex.[1]
- The consensus:  
  - Use prompts like the “hate review” to identify weaknesses, but **do not** implement every suggestion.  
  - Treat the review as a signal: if a hostile reviewer can only find minor issues, the code is probably good enough.[1]
  - Pick only one or two worthwhile suggestions per iteration and ignore exaggerated labels like “🚨 CRITICAL” when the underlying issue is minor.[1]
- Some users describe Claude inventing problems during debugging sessions—repeatedly claiming it has found the bug when it has not—so human validation remains necessary.[1]

***

## Model behavior notes

- A user observes that Opus 4.5 recently started finding more critical bugs in its own code on re‑review, whereas a week earlier it would mostly approve its work or point out small flaws, suggesting a change in behavior or tuning.[1]
- Another notes that instructions like “ask me questions before starting” often cause the model to ask trivial, time‑wasting questions; they see this as the model trying to play the “ask clarifying questions” role that should often remain human.[1]
- One commenter remarks that Claude “hates refactoring,” resisting aggressive refactor requests, which is good for mature codebases but problematic in early, less stable ones; without strong steering, the codebase can fragment.[1]

***

## Operational patterns and setups

**Multi-model review flows**

- Use **codex** as a PR auto‑reviewer in GitHub, invoked via `@codex`; treat it as a reviewer only, not an auto‑fixer.[1]
- Use **zen-mcp** to fan out reviews to three different models, have each review the code, then have Claude **consolidate feedback and apply fixes**, working on both own and other people’s code.[1]
- Run **Copilot** as an automatic reviewer for all PRs; then use Claude via the **GitHub MCP** to read Copilot’s comments and apply them selectively.[1]
- Run Anthropic’s **Claude auto-review GitHub Action** on PRs, possibly wired to an Anthropic console/API account so team review traffic doesn’t hit individual subscriptions.[1]

**Automation patterns**

- After every development phase, trigger a set of custom agents and a skill (via slash commands/skills/hooks) that:  
  - Run security checks.  
  - Run bug and completeness checks.  
  - Always fire, producing consistent gatekeeping before merging.[1]
- Use pre‑commit hooks with custom detection scripts that:  
  - Block commits containing anti‑patterns defined in `code-patterns.md`.  
  - Emit error messages that directly link to `code-patterns.md` so developers and Claude see what to change.[1]
- Add a hook that scans diffs for common fallback / backwards compatibility language (e.g., “fallback”, “backwards compatible”) in code and comments, and flags or blocks these changes.[1]
- Configure GitHub‑resident reviewers (`codex`, Claude auto review, Copilot) so reviews run automatically on PR creation or when explicitly `@`‑mentioned.[1]
- Use an agent `.md` specification (`code-reviewer`) that standardizes execution (run `git diff`, focus on modified files, apply a checklist) and output format (tables + verdict) for consistent, parseable reports.[1]

**Guardrail artifacts and encoded rules**

- `CLAUDE.md`:[1]
  - Imports `.claude/development-principles.md`.  
  - References `code-patterns.md` so quality rules and anti‑patterns are part of Claude’s context.  
  - Encodes principles like SRP, DRY, KISS, YAGNI; respect encapsulation; respect single source of truth; prefer inheritance over duplication when appropriate.[1]
- `.claude/development-principles.md`:[1]
  - Houses the core development principles and operational definitions that Claude must follow.  
- `code-patterns.md`:[1]
  - Lists anti‑patterns you never want to see again in the codebase.  
  - For each anti‑pattern, defines “Always use” vs “Never use” along with examples.[1]
- Agent definition `.md` (e.g., `code-reviewer.md`):  
  - Defines model, allowed tools (Read, Grep, Glob, Bash), anti‑sycophancy directives, checklist, and output schema (issues table, dual‑perspective analysis, verdict).[1]
- Hooks and preflight scripts:  
  - Custom checks for anti‑patterns and fallbacks.  
  - Lint rules and additional constraints specific to the codebase.[1]

***

## Practical recommendations

- **Add explicit principles files and wire them in**  
  - Create `.claude/development-principles.md` with SRP, DRY, KISS, YAGNI, encapsulation, single source of truth, and guidance on using inheritance vs duplication.  
  - Create `code-patterns.md` listing “never again” patterns with “Always use”/“Never use” plus examples.  
  - Import both via `CLAUDE.md` and reference them prominently so Claude treats them as hard constraints.[1]

- **Standardize a non‑sycophantic review agent**  
  - Define a `code-reviewer` agent `.md` using Opus with tools (Read, Grep, Glob, Bash).  
  - Include anti‑sycophancy directives, the review checklist (secrets, input validation, tests, performance, no bandaids, no fallbacks), and a structured output format (issues table, dual‑perspective analysis, verdict).[1]

- **Implement multi‑layer, multi‑model reviews**  
  - Set up **codex** as a GitHub PR reviewer, invoked via `@codex`, but do not allow it to auto‑modify code.  
  - Use **zen-mcp** (or an equivalent orchestration layer) to have multiple models review the same diff and then let Claude consolidate feedback and apply fixes.  
  - Optionally add **Copilot** as an auto‑reviewer and have Claude, via GitHub MCP or CLI, apply only the useful subset of Copilot’s comments.[1]

- **Automate checks at lifecycle boundaries**  
  - Define a “development phase complete” slash command or hook that runs your agents/skills for security, bugs, and completeness every time a phase ends.  
  - Make this gate mandatory before merging or tagging releases.[1]

- **Harden your pre‑commit and hooks**  
  - Add a pre‑commit hook that scans for anti‑patterns from `code-patterns.md` and blocks commits with a message linking back to the file.  
  - Add a hook that scans diffs for “fallback” and “backwards compatible” and either fails the commit or forces a manual override.  
  - Consider a script that rejects changes that reintroduce deprecated paths the plan said should be deleted.[1]

- **Use “hate review” prompts judiciously**  
  - Keep using prompts like the OP’s Git diff “you hate this implementation” review, but limit to 1–2 passes and manually filter suggestions.  
  - Treat many “critical” flags as prioritization hints, not absolute truth; focus on genuinely risky issues, not every stylistic nit.[1]

- **Retain human oversight and validation**  
  - Never assume Claude’s self-review or debugging claims are correct; verify critical bugs and fixes yourself.  
  - If Claude starts inventing issues or endlessly refactoring, stop, reset context, and restate constraints rather than chasing phantom bugs.[1]
