---
title: "what problems from this chat do you see that can be easily addressed or improved?"
date: "2026-06-18"
mode: "COPILOT"
uuid: "1d4265fe-574c-44f3-b640-feb1490adcf4"
entry_count: 20
---

## Human

what problems from this chat do you see that can be easily addressed or improved?

## Assistant

The main friction is not just “too much context” in the abstract; it’s that the session is mixing high-volume auto-injected material with tasks that only need a narrow slice of state. The easiest improvements are to make context injection more selective, reduce repeated boilerplate, and separate “must-have safety rules” from “nice-to-have background.”[1][2][3]

## Problems worth fixing first

1. The auto-injected context seems too broad for simple tasks, so even small edits inherit large, unrelated instruction blocks. Claude Code’s own best-practices page explicitly recommends using precise prompts, subagents for research-heavy work, and frequent `/clear` or `/compact` to control context growth.[1]

2. The system reminder is carrying a lot of static agent/type information that does not appear to be needed for every turn. That kind of always-on payload is exactly the sort of thing context-management guidance recommends moving behind on-demand loading or scoping more tightly.[4][2][5]

3. The current CKS-style injection logic appears to favor turn type or broad session state instead of actual relevance, which can create noise. A relevance-first approach with token budgeting is a better fit for “max value, min negative impact” because it preserves useful retrieval while cutting low-signal additions.[2][6][5]

4. Verification steps are being repeated in ways that duplicate the same file state and burn tokens. Claude Code docs recommend compacting or using targeted verification rather than repeatedly rehydrating the same large context after every small action.[1]

## Lowest-risk improvements

| Problem | Low-friction fix | Why it helps |
|---|---|---|
| Over-injection of background context | Gate injected context by explicit relevance and a small token budget | Keeps only what is likely to help the current turn [2][5] |
| Large static reminders every turn | Move rarely needed rules into scoped files or on-demand loading | Reduces baseline session cost [1][7] |
| Repeated verification dumps | Verify in batches after a logical unit of work | Cuts redundant context churn [1][3] |
| Simple transcription tasks getting heavy context | Add a narrow “simple edit/transcription” path that suppresses nonessential context | Prevents easy tasks from paying the full overhead [4][1] |

## What I would not change yet

I would avoid removing automatic context help entirely, because that would likely lower usefulness for complex or ambiguous tasks. The safer move is to make the system selective rather than silent: keep explicit retrieval, but only inject when the match quality is good and the budget allows it. That preserves the value of CKS-like behavior while reducing noise and surprise.[8][2]

## Best next step

The most effective first experiment is to measure three things on a sample of recent turns: injected-token count, retrieval hit rate, and user-visible usefulness on simple versus complex tasks. If the numbers show most overhead comes from a few always-on blocks, then scoping those blocks will give the biggest gain with the least risk.[6][3][2]

Would you like me to turn this into a concrete refactor plan for your hook/context system, with the highest-leverage changes ranked by expected token savings and risk?

## Human

what about the agent list issue?

## Assistant

The agent list issue is real, and the docs support treating it as **scoped knowledge**, not always-on payload. Claude Code says subagents are separate contexts, and that broad instructions should live in concise CLAUDE.md files while domain-specific or conditional knowledge should move into skills so it loads only when relevant.[1][2]

## What is wrong

The likely problem is that your system reminder is dumping the full agent catalog into every turn, even when the current task will never use most of those agents. That conflicts with Claude Code’s guidance that context fills quickly and should be managed aggressively, and it also conflicts with the subagent model where the parent should only receive a concise result, not the whole internal machinery. If the list is emitted unconditionally, it becomes pure overhead and a distraction, not a capability gain.[2][1]

## Best fix

The best fix is to replace the always-on agent list with a compact routing policy plus on-demand expansion. In practice that means: keep only the small set of default or high-probability agents visible in the main context, and load the full catalog only when a prompt actually needs delegation or agent selection. That preserves discoverability without paying the full token cost every turn.[1][2]

## Safer design

A better architecture is to treat agent metadata like a searchable registry rather than a reminder. The main session should know: which agent classes exist, what triggers them, and where to find the registry; it should not need all descriptions inline every time. This matches the docs’ emphasis on clear subagent descriptions for automatic delegation, while keeping the main prompt small.[2][1]

## Concrete improvements

- Replace the full agent list with a short “available agent families” summary.
- Move the detailed catalog into a file or skill that is loaded only when needed.
- Add a lightweight selector rule: only surface agents relevant to the current prompt.
- If you need the full list for debugging or maintenance, fetch it on demand, not by default.
- Measure the token cost before and after; if the list is >1–2 KB, it is a strong candidate for removal from always-on context.

## My read

The highest-value change is not deleting the agent list entirely, but **de-reifying** it: make it queryable instead of omnipresent. That gives you the same routing power with much less context pollution, and it aligns with Claude Code’s own advice to keep CLAUDE.md concise and use subagents/skills for specialized knowledge.[1][2]

If you want, I can turn that into a concrete refactor plan for your reminder system with a “minimal always-on / on-demand catalog” split.

## Human

yes please

## Assistant

Yes — the agent list should be treated as a **lazy-loaded registry**, not as always-on session context. Claude Code docs and skills guidance both point toward the same pattern: keep the main context lean, load richer instructions on demand, and use separate subagents for scoped work.[1][2][3][4]

## Recommended split

Use three layers:

- **Always-on:** only the tiny set of agent names or families you expect to use frequently.
- **On-demand registry:** the full agent list, descriptions, and routing rules.
- **Task execution:** subagents/skills that load only when triggered by a matching task.[3][4][1]

That gives you discoverability without paying the token cost every turn, which matches the on-demand loading model described for skills and the separate-context model described for subagents.[4][1]

## What to keep inline

Keep only this in the system reminder or core CLAUDE.md:

- The existence of the registry.
- The 3–8 highest-probability agent families.
- A short rule for when to delegate versus when to stay in the main thread.

Everything else should move out of the always-loaded prompt, because Claude Code best-practices emphasize keeping core instructions concise and pushing specialized knowledge into skills or separate artifacts.[2][5][3]

## What to move out

Move the following out of the main reminder:

- Long agent descriptions.
- Full tool matrices.
- Rarely used specialist roles.
- Diagnostic or archival agent types.
- Any “catalog” text that is only useful during agent selection.[1][3][4]

This is especially important if the list is being injected into every message, because that creates a fixed cost that scales with nothing useful on simple tasks.[6][5]

## Concrete implementation

A practical refactor would look like this:

1. Replace the current agent dump with a short index like “use the registry when delegating.”
2. Store the full catalog in a file or skill that is loaded only when the user asks for agent selection, debugging, or orchestration.
3. Add a lightweight “agent picker” skill that reads the registry and proposes candidates.
4. Keep the main prompt limited to high-frequency agents and a delegation rule.
5. Measure token usage before and after to confirm the gain.[6][2][1]

## Minimal policy

The best policy is: if an agent is needed for the current task, load it; otherwise do not mention it. That is the same progressive-disclosure principle used by Claude skills and the same isolation principle used by subagents.[7][4][1]

If you want, I can turn this into a concrete rewrite of your reminder text and a small registry/loader design.

## Human

yes please, as long as it is an established pattern that works for claude code.

## Assistant

Yes — the established pattern for Claude Code is **progressive disclosure**: keep `CLAUDE.md` concise, move task-specific or optional material into separate docs or skills, and let subagents isolate scoped work in separate contexts. That means the agent list should not live as a big always-on block if it can be loaded only when needed.[1][2][3][4]

## Pattern to use

The pattern that fits Claude Code best is:

- `CLAUDE.md` for universal project onboarding and rules.
- Separate markdown docs or skills for specialized knowledge.
- Subagents for delegated tasks that need their own context window.[2][4][1]

That is not just a style preference; it is the same “load only what is needed” model described in Claude’s skills docs and best-practices guidance.[3][1][2]

## What this means for the agent list

Keep only a tiny always-visible summary in the main reminder, such as the handful of agent families you actually expect to use often. Put the full agent catalog, descriptions, and routing hints into a separate registry file or skill that is loaded on demand. This preserves discoverability while avoiding permanent context bloat.[1][2][3]

## Recommended rewrite shape

Use a two-part structure:

1. **Main reminder:** one short paragraph that says the registry exists and where to find it.
2. **Registry doc/skill:** the full list of agents, each with a one-line trigger and output shape.

That structure matches Claude Code’s documented preference for concise universal instructions plus on-demand reference material.[5][2][1]

## Example policy text

You could use something like this in the always-on area:

- “Use the agent registry only when delegation is likely.”
- “Prefer the smallest agent that can complete the task.”
- “Load detailed agent descriptions from the registry, not from the main prompt.”

That keeps the main prompt thin while still giving the model a stable routing rule, which is exactly the kind of progressive disclosure Claude Code docs recommend.[4][3][1]

## My recommendation

The most defensible Claude Code pattern is: **lean root context, on-demand registry, isolated subagents**. I would not keep a long agent list in the system reminder unless you have evidence it is repeatedly needed on nearly every turn.[6][2][4][1]

## Human

give me a prompt to take to the implementing LLM.

## Assistant

Here is a prompt you can give to the implementing LLM. It is designed around an established Claude Code pattern: keep `CLAUDE.md` concise, move optional detail into on-demand files or skills, and use separate subagent context for specialized work.[1][2][3][4]

## Implementation prompt

```text
You are implementing a Claude Code context-management refactor.

Goal:
Reduce always-on prompt bloat from the agent list while preserving routing value and keeping the design aligned with established Claude Code patterns:
- keep CLAUDE.md concise and universally applicable,
- use progressive disclosure for specialized detail,
- load task-specific knowledge on demand via separate docs/skills,
- isolate delegated work in subagents with separate context windows.

Task:
Refactor the agent-list mechanism so the main always-on context contains only a small, high-value summary, while the full agent catalog is moved to an on-demand registry.

Requirements:
1. Identify the current always-on agent list or equivalent reminder text.
2. Replace it with a short, stable policy that:
   - says the registry exists,
   - says when to use it,
   - keeps only the small set of high-frequency agent families inline.
3. Move the full agent catalog, long descriptions, and routing hints into a separate registry artifact or skill loaded on demand.
4. Preserve behavior for delegation:
   - the model should still know how to delegate,
   - it should prefer the smallest agent that can do the job,
   - it should not need the full list unless selection is actually required.
5. Keep the implementation consistent with Claude Code best practices:
   - concise universal instructions in CLAUDE.md,
   - task-specific material in separate markdown files or skills,
   - subagents for scoped tasks.
6. Do not make unrelated architectural changes.
7. Preserve existing safety and routing semantics unless a minimal change is needed to support the split.
8. Add or update tests if they exist.
9. Verify the reduction in always-on text and confirm the registry can still be used on demand.

Expected output:
- A minimal patch or set of patches.
- A brief explanation of what was moved out of the always-on context.
- Any follow-up notes on token/context savings or tradeoffs.

Acceptance criteria:
- Main prompt/context is shorter.
- Full agent list is no longer injected every turn.
- Delegation still works.
- The design matches the Claude Code progressive-disclosure pattern.
- No regressions in routing behavior.

Before finishing:
- self-check that the main context contains only universal rules,
- confirm the registry is reachable on demand,
- summarize the exact files changed.
```

## Why this is the right shape

Claude Code guidance supports concise `CLAUDE.md`, progressive disclosure, and separating specialized material into skills or other files loaded only when needed. Claude Code subagents also operate in separate context windows, which makes them the right place for scoped task work rather than main-thread prompt inflation.[2][5][3][4][1]

## Optional tighter version

If you want the prompt shorter and more implementation-oriented:

```text
Refactor the always-on Claude Code agent list into a lazy-loaded registry.

Keep only a minimal inline summary in the main prompt/CLAUDE.md:
- registry exists,
- when to consult it,
- a few high-frequency agent families,
- one short delegation rule.

Move the full catalog, detailed descriptions, and routing hints into a separate on-demand file or skill. Do not load that catalog into every turn.

Preserve delegation behavior and keep changes minimal. Follow Claude Code best practices: concise universal instructions in CLAUDE.md, task-specific detail in separate markdown/skills, and subagents for isolated work. Add or adjust tests if needed and verify that the registry is still reachable on demand.
```

## Suggested implementation constraint

If you want the implementing LLM to stay disciplined, add this line:

- “Do not optimize for theoretical completeness; optimize for minimal always-on tokens while preserving routing quality.”

That aligns with the established progressive-disclosure pattern and keeps the change narrow.[3][1][2]

## Human

how will it refactor the mechanism if it's built into claude code?

## Assistant

If it is already built into Claude Code, then the refactor is not code surgery inside the product — it is a **configuration and packaging** refactor on your side. Claude Code already supports `CLAUDE.md`, skills, and subagents, so the goal is to reclassify the agent list from “always loaded” to “on-demand” by changing where that knowledge lives.[1][2][3][4]

## What changes

Instead of trying to rewrite Claude Code’s internals, you would do this:

- Keep a tiny always-on policy in `CLAUDE.md`.
- Move the full agent catalog into a skill or separate registry file.
- Make the registry discoverable via a short pointer in the main context.
- Let subagents or a selector skill load the detailed catalog only when needed.[3][4][5][1]

That is consistent with Claude Code’s built-in pattern: concise persistent instructions, on-demand skills, and isolated subagent contexts.[2][4][5][1]

## Practical mechanism

The implementing LLM should not “edit Claude Code itself.” It should:

1. Edit the always-on reminder to contain only a short delegation policy.
2. Create or update a registry skill/file containing the full agent list and routing hints.
3. Optionally create a tiny “agent picker” skill that reads the registry and recommends a candidate.
4. Update any subagent definitions so they reference the skills they actually need, rather than inheriting everything.[6][1][3]

That works because Claude Code skills are filesystem-based and load on demand, while subagents run in separate contexts and do not need the parent’s entire prompt.[4][6][3]

## What the LLM should do

The implementing LLM should treat the built-in behavior as a constraint and refactor around it, not against it. The core move is “progressive disclosure”: only the small routing rule stays in the root context, and the detailed agent catalog moves into a loadable artifact. That preserves routing quality without carrying the entire list in every turn.[5][2][3]

## One-line version

The right change is: **replace an always-on agent catalog with a built-in Claude Code skill or registry file, and keep only a short pointer plus delegation rule in `CLAUDE.md`**.[1][2][3][4]

I can also turn this into a more precise implementation prompt that tells the LLM exactly which files to touch and what not to change.

## Human

search the internet and find the truth.

## Assistant

Here is the truth, based on the strongest available Claude Code sources: Claude Code already supports the exact pattern you need, so the right move is to **refactor by packaging**, not by modifying the product internals. Skills are the on-demand layer, and subagents are separate-context workers; `CLAUDE.md` is the always-on layer that should stay concise.[1][2][3][4]

## What the official docs support

Claude Code’s skills docs say skills are modular capabilities that Claude can invoke when relevant, and the Agent Skills docs say they are packaged as `SKILL.md` files. The features overview explicitly frames `CLAUDE.md` as always-on context and skills as on-demand context, with subagents available for isolated work. That means the agent list issue should be solved by moving the long catalog out of the always-on layer and into a skill or registry file.[2][3][1]

## What is not the truth

It is not correct to say you need to change Claude Code’s internals for this. The documentation points to a built-in extension model already designed for this exact kind of separation: concise persistent instructions, on-demand skills, and isolated subagents. So the claim that “the mechanism is built into Claude Code, therefore no refactor is possible” is false; the refactor is in how you organize your files and prompts.[3][4][1][2]

## Practical conclusion

The best-supported answer is:

- Keep the root `CLAUDE.md` short and universal.
- Put the full agent list into a separate skill or registry.
- Let Claude load that registry only when delegation is needed.
- Use subagents when the task needs isolated context.[4][5][1][3]

That is the established Claude Code pattern, and it is the most defensible truth I can support from the docs.[1][2][3]

## Human

provide a prompt that supports the optimal solution.

## Assistant

Use this as the implementing prompt. It reflects the established Claude Code pattern: concise always-on `CLAUDE.md`, on-demand skills, and subagents with separate context.[1][2][3][4]

```text
You are implementing a Claude Code refactor for context management.

Goal:
Reduce always-on agent-list bloat while preserving delegation quality, using Claude Code’s built-in extension model rather than changing product internals.

Ground truth pattern to follow:
- Keep always-on context in CLAUDE.md concise and universally applicable.
- Put specialized or optional knowledge into on-demand skills or separate markdown registry files.
- Use subagents for scoped work that needs separate context.
- Prefer progressive disclosure over dumping the full catalog into the root prompt.

Task:
Refactor the current agent-list mechanism so the main always-on context contains only a short routing policy and a tiny set of high-frequency agent families, while the full agent catalog is moved into an on-demand registry artifact or skill.

Requirements:
1. Find the current always-on agent list or reminder text.
2. Replace it with a minimal policy that:
   - says a registry exists,
   - says when to consult it,
   - lists only the few agent families used most often.
3. Move the full agent list, detailed descriptions, and routing hints into a separate registry file or skill that is loaded only when relevant.
4. Keep delegation behavior intact:
   - preserve the ability to choose the right agent,
   - prefer the smallest sufficient agent,
   - do not require the full list in normal turns.
5. Keep changes minimal and local.
6. Do not modify Claude Code internals, only the project files/configuration.
7. Follow Claude Code best practices:
   - concise `CLAUDE.md`,
   - on-demand skills for specialized knowledge,
   - separate-context subagents for scoped tasks.
8. Add or update tests if this repo has them, especially if there is a registry-loading or routing path that can be validated.
9. Verify the main context is shorter and the registry is still reachable on demand.

Implementation guidance:
- Treat the agent catalog as a lazy-loaded registry, not always-on prompt content.
- If there is a selector or router, keep only the selection rule in the main context.
- If a skill is a better fit than a plain file in this repo, use a skill.
- Do not over-engineer. The optimal solution is the smallest change that preserves routing quality and reduces context load.

Expected output:
- Exact files changed.
- Brief explanation of what moved out of always-on context.
- Any measurable context/token reduction if available.
- Any tradeoffs or follow-up work.

Acceptance criteria:
- The root prompt/CLAUDE.md is materially shorter.
- The full agent list no longer appears in every turn.
- Delegation still works through the registry/skill path.
- The design matches Claude Code’s documented progressive-disclosure pattern.

Before finishing:
- self-check that the always-on layer contains only universal rules,
- confirm the registry is loadable on demand,
- summarize why this is the smallest safe refactor.
```

## Human

are you making an assumption that the agent list is in claude.md?

## Assistant

No — that would be an assumption, and the evidence does not support it as a fixed fact. The official Claude Code docs support `CLAUDE.md` as always-on context and skills/subagents as the on-demand and isolated layers, but they do **not** prove that your specific agent list currently lives in `CLAUDE.md`.[1][2][3]

## What is actually known

What is supported is the pattern: `CLAUDE.md` is for persistent context, skills are loaded on demand, and subagents have separate context windows. The context-window docs also show that skills are only re-injected when invoked, while the main prompt and `CLAUDE.md` are loaded at the start of conversation. So the safe conclusion is about **where the mechanism should live**, not where your current agent list already is.[2][3][1]

## What I should have said

I should have framed it as:

- If the agent list is in `CLAUDE.md`, the best refactor is to move it out.
- If it is in a skill, plugin, command, or another injected source, the same progressive-disclosure idea still applies.
- We need to inspect the actual files before assuming the location.[3][2]

## Correct next step

The truthful next step is to inspect the repository’s Claude Code configuration files and determine the source of the agent list before proposing edits. The docs show multiple valid places where that text could live, including `CLAUDE.md`, skills, and subagents, so the location must be verified rather than inferred.[4][1][2][3]

If you want, I can now help you build a prompt that explicitly tells the implementing LLM to first locate the source of the agent list before changing anything.

## Human

please provide a prompt that does the exploration and discovery you need, to create an optimal impelmentation prompt.

## Assistant

Use this prompt to make the implementing LLM do the exploration first and then produce an optimal implementation prompt. It is written to avoid assumptions and to discover where the agent list actually lives before recommending changes.[1][2][3][4]

```text
You are doing a discovery-first refactor analysis for a Claude Code project.

Primary goal:
Find the actual source of the “agent list” / routing catalog / reminder text, determine how it is injected, and then produce an optimal implementation prompt that minimizes always-on context while preserving delegation quality.

Important constraints:
- Do not assume the agent list is in CLAUDE.md.
- Verify the source before proposing changes.
- Treat built-in Claude Code features as the target extension model, not as something to modify internally.
- Prefer the established Claude Code pattern: concise always-on context, on-demand skills, and separate-context subagents.
- Optimize for the smallest safe refactor that preserves behavior.

Phase 1 — Discovery
Search the repository and related Claude Code configuration for:
- CLAUDE.md files at all relevant scopes.
- Skills or SKILL.md files.
- Subagent definitions.
- Hooks, commands, plugins, or other injection mechanisms.
- Any registry, routing map, or agent catalog text.
- Any code that emits the “agent list” or similar always-on reminder.

For each candidate source, report:
- file path,
- why it seems relevant,
- whether it is always-on or on-demand,
- whether it appears to be authoritative or redundant.

Phase 2 — Mechanism analysis
Explain how the agent list is actually getting into context:
- direct file injection,
- hook-based injection,
- skill loading,
- subagent invocation,
- or another mechanism.

Identify:
- what is universal and must stay always-on,
- what is optional and should be on-demand,
- what is duplicated across files,
- what is purely informational overhead.

Phase 3 — Recommendation
Based on the discovery results, recommend the best refactor strategy using this hierarchy:
1. If the list is in always-on context, move the long part into a registry or skill and keep only a short pointer plus routing rule.
2. If it is already in a skill, reduce the main prompt to a minimal selector and keep the skill on-demand.
3. If it is emitted by a hook or plugin, narrow or conditionalize the emission.
4. If the same knowledge is duplicated in multiple places, consolidate to one authoritative source.

Phase 4 — Deliverables
Produce:
1. A concise findings summary.
2. A ranked list of refactor options with tradeoffs.
3. A single implementation prompt for the coding LLM that:
   - references the discovered source paths,
   - avoids assumptions,
   - instructs the LLM to make the smallest safe change,
   - preserves delegation and routing,
   - explicitly keeps always-on context concise.
4. If needed, include a fallback prompt for the case where no centralized list exists and the “agent list” is composed from multiple sources.

Quality bar:
- Be explicit about uncertainty.
- Distinguish fact from inference.
- If the evidence is incomplete, say so.
- Prefer direct file-based evidence over generic advice.
- Do not produce the final implementation prompt until discovery is complete.

Output format:
- Section 1: Findings
- Section 2: Mechanism
- Section 3: Refactor options
- Section 4: Final implementation prompt
- Section 5: Fallback prompt, if needed
```

This prompt is aligned with Claude Code’s documented pattern that `CLAUDE.md` is always-on, skills are on-demand, and subagents provide isolated context. It also forces the LLM to verify the source before it decides how to refactor, which is the safest way to avoid the wrong assumption.[2][3][4][5][1]

If you want, I can also give you a shorter “single-pass” version that is tighter for a tool-constrained implementation model.

## Human

"
● Section 1: Findings

  Critical Discovery: The "Available agent types for the Agent tool:" reminder text is NOT injected by any file in the P:\
  repository.

  Evidence:
  - No Python files in P:\ contain the text "Available agent types"
  - No files match agent name patterns (adr_critic, adversarial-compliance, claude-code-guide) except in artifact/session files
  (outputs, not source)
  - Hook system files (registry.py, subagent_enforcer.py) do NOT inject agent catalog text
  - No agent catalog, routing map, or registry JSON files exist in the repository
  - The agent list is part of the Agent tool definition provided by the Claude Code CLI infrastructure

  Actual Source: Claude Code CLI (client software) infrastructure, not user-configurable code.

  Section 2: Mechanism

  Injection Mechanism:
  - Source: Claude Code CLI infrastructure
  - Injection point: Session initialization (system prompt construction)
  - Context type: Tool definition metadata
  - Always-on: YES (infrastructure-provided, user-configurable)
  - User code access: NONE (this is CLI-level, not plugin/hook level)

  Section 3: Refactor Options

  No local refactor options exist because the source is CLI infrastructure, not the user's codebase.

  Possible system-level approaches:
  1. Fork Claude Code CLI - Modify the source to suppress agent descriptions from tool definitions
  2. Request Anthropic feature - Add configuration flag to suppress agent catalog from context

  Trade-offs:
  - Current state: Complete agent catalog available (~3-5k tokens) for informed delegation decisions
  - Modified state: Reduced context cost but potential suboptimal routing choices if agents lack catalog knowledge

  Section 4: Final Implementation Prompt

  Not applicable - No local implementation can reduce this context because it's injected at the CLI infrastructure level, not
  through hooks, skills, or plugins.

  Section 5: Fallback Recommendation

  Recommendation: Do not proceed with local refactoring. The agent list context is provided by Claude Code CLI infrastructure and
  cannot be suppressed through user code.

  Alternative approach: If context optimization is critical, the issue should be raised with Anthropic as a feature request for CLI
  configuration options.

  Broader structural question raised: This discovery suggests that some context optimization targets may be outside the user's
  control, requiring infrastructure-level changes rather than codebase-level refactoring."

## Assistant

Yes — and the evidence now suggests the earlier “local refactor” conclusion was too strong. Claude Code’s own docs indicate the context may be coming from built-in tool definitions, managed agent infrastructure, hooks, skills, or subagents, and not necessarily from any file in your repository.[1][2][3][4]

## What the evidence supports

Claude Code’s Agent SDK and managed-agents docs show that agent definitions, tools, skills, and runtime context can be supplied by the platform itself, with a managed harness handling prompt construction and context management. The hooks docs also show that Claude Code can inject deterministic behavior at lifecycle points outside your repo code, and subagents can be spawned from the runtime rather than from a local catalog file.[2][3][5][1]

## What that means for your discovery result

If your search found no repository file containing the agent catalog text, then the likely truth is that the list is **not** user-code-controlled and may indeed be part of the Claude Code client/runtime layer. That is a plausible conclusion, but it is still an inference from absence of source in the repo plus the platform docs, not direct proof of the exact injection point.[3][4][1][2]

## Corrected implementation posture

Given that, the right implementation prompt should tell the coding LLM to:

- verify whether the text is repo-owned or runtime-owned,
- only refactor local sources if a local source exists,
- otherwise produce a minimal prompt or issue report for the platform-level limitation,
- and avoid assuming that `CLAUDE.md` is the source.[4][6][3]

## Best truth-based conclusion

So the most accurate statement is: **the agent list may be injected by Claude Code infrastructure, and if so, it cannot be removed by repository changes alone**. That means the optimal path is discovery-first, then either a local refactor if a local source exists or a feature-request / platform-level workaround if it does not.[1][2][3][4]

I can now produce a revised discovery prompt that explicitly handles the “runtime-owned vs repo-owned” fork and tells the implementing LLM exactly how to conclude each branch.

## Human

how does the internet deal with system reminder agent and skill list reduce overhead

## Assistant

The internet’s answer is pretty consistent: reduce overhead by keeping always-on context tiny, and push everything else into on-demand skills or subagents. Claude’s skills docs say skills are reusable filesystem resources that load only when relevant, and the features overview frames `CLAUDE.md` as always-on while skills are on-demand.[1][2]

## What works

The strongest repeated pattern is progressive loading: only the skill metadata is present up front, and the full body loads when invoked. Several sources also emphasize that keeping `CLAUDE.md` lean is important because anything there stays in context for the session, so it should contain only stable rules, not catalogs or long reference material.[3][4][5][2][6][1]

## Agent list problem

For an “agent list” or “system reminder agent list,” the usual recommendation is to stop embedding the full catalog in the always-on prompt and instead keep a short index plus a separate registry or skill. Sources discussing Claude Code skills repeatedly note that summary metadata is what remains in context, while the larger instructions stay out until needed. That is exactly how people are keeping overhead down in practice.[7][4][5][1][3]

## Subagents help too

Subagents are the other half of the pattern: they isolate noisy or specialized work so the main conversation does not inherit all of the detailed reasoning, tools, and instructions. In practice, that means you use the main session to decide whether delegation is needed, then let the subagent carry the heavy context.[2][8][9]

## Practical rule

The practical rule from the internet is:

- Keep always-on context for universal rules only.
- Put reusable procedures in skills.
- Put detailed catalogs in a registry or skill.
- Use subagents for scoped, high-noise tasks.
- Inspect context regularly and compact early.[4][5][1][2]

## Bottom line

So the best-overhead-reduction pattern is not “remove the agent list from Claude Code,” but “demote it from always-on context to on-demand metadata.” That preserves discovery while minimizing token waste, and it matches both the docs and the field practice people report using.[5][1][3][2]

## Human

that advise is weak.  how do we do that?

## Assistant

Do it with **three concrete moves**, not generic advice: shrink the always-on root context, move the catalog into a load-on-demand skill or rule file, and make the main prompt point to it only when needed.[1][2][3]

## 1. Split the context by load mode

Keep only universal rules in root `CLAUDE.md` or the root prompt: project identity, safety constraints, and a one-line delegation policy. Put the agent catalog into a separate file or skill package so it is not part of the always-on prompt. If you need it to be even more modular, put each topic into small scoped rule files or subagent definitions instead of one giant list.[4][5][6][2][3][7][1]

## 2. Make the catalog lazy-loaded

Use a short pointer in the always-on layer, like “agent registry lives in `.claude/skills/agent-registry/SKILL.md`” or “see `.claude/rules/agents.md` for routing details”. The skill body or registry file should contain the full list, descriptions, and selection rules, but Claude should only read it when the task actually needs delegation. That is the key mechanism that reduces overhead: metadata stays light, details stay out of context until invoked.[8][9][2][3][10][4]

## 3. Use subagents for noisy work

If part of the “agent list” problem is that routing and implementation reasoning are getting mixed together, move the heavy work into subagents with separate context windows. The main session should decide whether delegation is needed, then hand the subagent a focused task and a tiny slice of context. That preserves the main conversation while preventing the routing catalog from ballooning every turn.[11][12][13][2][14]

## Concrete structure

A practical layout looks like this:

- `CLAUDE.md`: short, universal, always-on.
- `.claude/skills/agent-registry/SKILL.md`: compact trigger metadata plus a link to the catalog.
- `.claude/skills/agent-registry/references/agents.md`: full catalog and routing details.
- `.claude/agents/`: subagents for specific noisy or repeated tasks.[12][7][4][1]

That follows the common Claude Code pattern: concise root instructions, on-demand skills, and separate-context subagents.[2][3][12]

## What to do next

The right next step is to write a discovery-first implementation prompt that tells the coding LLM to locate the actual source of the agent list, classify it by load mode, then produce the minimal refactor for the discovered source. That avoids the mistake of assuming `CLAUDE.md` owns the problem when it might actually be a skill, subagent, or runtime-injected list.[3][15][1][12][2]

## Human

validate your ideas with evidence from the internet

## Assistant

Yes. The evidence supports a specific implementation pattern: keep `CLAUDE.md` lean, put reusable procedures into skills that load on demand, and use subagents to isolate noisy work.[1][2][3][4]

## Evidence-backed mechanism

Claude’s skills docs say skills are reusable filesystem resources, and the docs explicitly note on-demand file access: Claude reads only the files needed for the task. Claude Code’s features overview and skills docs both frame skills as the on-demand layer, while `CLAUDE.md` is the always-on layer. The subagents docs say subagents are separate agent instances for focused subtasks, which keeps the main context cleaner.[2][5][4][1]

## What practitioners do

Good `CLAUDE.md` guidance consistently says to keep root instructions concise, universal, and under a few hundred lines, and to move task-specific material into separate markdown files with pointers back from `CLAUDE.md`. Skill guidance similarly emphasizes that only metadata is always visible, while full instructions and supporting files are loaded when the skill is triggered. That is the concrete overhead-reduction strategy people are using in practice.[3][6][7][8][9][10]

## How to apply it

The way to reduce overhead is:

- Shrink the always-on root prompt to one short delegation rule and a pointer to the registry.
- Put the full agent list into a skill or separate file with a short description.
- Have Claude load that skill only when it actually needs agent selection.
- Use subagents for work that would otherwise drag a lot of irrelevant context into the main session.[4][1][2][3]

## What this means for your case

If the current agent list is inside an always-on source, this pattern will reduce overhead directly. If the list is runtime-injected by Claude Code itself, you cannot remove it locally, but you can still reduce the rest of the always-on payload by moving your own catalogs and helpers out of root context.[1][2][4]

The strongest evidence-based claim is: **progressive disclosure is the established Claude Code way to reduce overhead**.[2][3][4][1]

## Human

you don't make sense.  what evidence do you have that your ideas are actually user configurable?

## Assistant

Yes — and the evidence is stronger for **some** parts than others.

### What is clearly user-configurable

- **Skills** are user-configurable because the docs describe them as filesystem-based resources you create/manage, with `SKILL.md` content and optional resources, and say they load on demand.[1][2]
- **Hooks** are user-configurable because the docs say they are user-defined shell commands configured in settings files like `.claude/settings.json` and `~/.claude/settings.json`.[3][4][5]
- **Subagents** are user-configurable as a built-in extension mechanism because Claude Code docs say the main agent can spawn them for focused subtasks.[6][7]

### What is not proven user-configurable

- The **system reminder agent list** itself is **not proven** to be configurable from repo files. The evidence I have supports that Claude Code has built-in features and context layers, but it does not prove you can remove or suppress the built-in agent catalog from the CLI runtime with a local project change.[7][1][6]
- So the safe claim is: you can reduce overhead in the parts you control, but the built-in agent list may still be runtime-injected.[1][6]

### The practical implication

If your goal is overhead reduction, the user-configurable lever is to move your own content into:
- a short root `CLAUDE.md`,
- on-demand skills,
- subagents for scoped work,
- and hooks for deterministic enforcement.[5][6][7][1]

If your goal is to remove the built-in agent list itself, I do **not** have evidence that this is user-configurable from the project side. That would require platform-level support or a CLI setting exposed by Anthropic, and I do not have evidence of such a setting in the sources I checked.[6][5][1]

If you want, I can now give you a **strictly evidence-labeled** statement of:  
1. what you can change today,  
2. what you probably cannot, and  
3. the exact prompt to use with an implementing LLM so it does not assume more than the evidence supports.

## Human

for the elements that are not controlable by the user, how can we mitigate their impact?

## Assistant

Yes. For the parts you cannot control, the evidence-backed mitigation is to reduce everything else that competes for context, and to use the platform’s own compaction and isolation mechanisms aggressively.[1][2][3][4]

## Mitigation tactics

1. Keep `CLAUDE.md` high-signal only. Claude Code’s best-practices docs say it is loaded every session and should contain only broadly applicable information; anything else should be cut.[2]
2. Push optional knowledge into skills or separate files. Skills are reusable filesystem resources that load on demand, and the docs explicitly describe on-demand file access.[5][6]
3. Delegate noisy work to subagents. Claude Code subagents are separate agent instances for focused subtasks, which helps isolate spillover from the main session.[4]
4. Use compaction proactively. The docs say Claude Code automatically compacts near limits, and the API docs recommend server-side compaction for long-running conversations.[3][1]
5. Break work into smaller sessions and clear unrelated state. The best-practices page recommends `/clear` between unrelated tasks and using subagents for research-heavy work.[2]

## What this means for unavoidable injected text

If the agent list or system-reminder payload is runtime-injected and not user-controlled, you cannot delete it locally. The mitigation is to **subtract around it**: make your own always-on context smaller, move catalogs out of root files, and use on-demand loading so the injected overhead is a smaller fraction of the total context. That is the same pattern practitioners use when they say to keep the root file lean, push reference material into skills, and let subagents do the heavy lifting.[7][8][6][9][5][2]

## Best operational pattern

The strongest evidence-based pattern is:

- Root context: only universal rules.
- Skills: task-specific procedures and catalogs, loaded only when relevant.
- Subagents: isolated execution for noisy or exploratory tasks.
- Compaction: early and deliberate, not last-minute.[1][3][4][5]

That does not remove the uncontrollable overhead, but it reduces its impact enough that the session stays usable.[1][2]

## Practical next move

The best next move is to rewrite the always-on layer so it contains only what would cause real mistakes if removed, then measure context usage before and after with `/context` or your equivalent workflow. If the unavoidable overhead still dominates, the remaining answer is platform-level feedback, not more local refactoring.[6][3][7][2]

## Human

what controls the size of t he agent list?

## Assistant

The size of the agent list is controlled by whatever mechanism is populating the Claude Code context, and the strongest evidence I found says there are **two different budgets**: a skill-description budget and a broader context budget. For skills, Claude Code explicitly says all skill names are always included, but descriptions are shortened or dropped first when the skill list is too large, and the cutoff is configurable with `maxSkillDescriptionChars`. For broader context, Claude Code compacts automatically near the limit, and the context window contains instructions, file reads, responses, and tool history.[1][2][3]

## What actually controls it

For the **skill list**, the docs say the control knobs are:
- number of skills,
- description length,
- the `maxSkillDescriptionChars` setting,
- and the fact that lower-use skills lose description text first when the budget overflows.[1]

For the **rest of the visible agent context**, the drivers are:
- how much is in `CLAUDE.md`,
- how many files are auto-loaded,
- how many subagents are referenced,
- how much tool/schema/context metadata is present,
- and whether compaction has occurred.[4][2][3]

## What this means for your “agent list”

If the “agent list” you are seeing is actually the **skills listing**, then its size is user-configurable through the skill system: trim descriptions, keep the key use case first, and lower the description budget if the setting is exposed in your config. If the “agent list” is the built-in Claude Code system-reminder or tool metadata, then the evidence does **not** show a user-controlled switch for removing it locally; in that case, its size is controlled by Claude Code’s internal runtime and whatever platform budget it uses.[2][5][1]

## Best supported mitigation

The evidence-backed way to reduce its impact is:
- reduce your own always-on context,
- shorten skill descriptions,
- move detail into on-demand files,
- and use subagents for isolated work.[6][3][4][1]

That doesn’t prove you can eliminate the built-in list, but it does show you can make the whole session much less sensitive to it.[3][2][1]

If you want, I can now give you a precise “control map” that separates **user-configurable**, **likely configurable but unverified**, and **not user-configurable** elements of Claude Code context.

## Human

find out from the internet what is the agent list and what goes into it.

## Assistant

The internet suggests the “agent list” is not one single universal object; it depends on which Claude layer you mean. In the official Anthropic docs, the closest concrete thing is the **toolset** for managed agents and the **skills/subagents** that Claude Code can load or spawn, rather than a single fixed “agent list” file.[1][2][3][4]

## What goes into it

From the managed-agents docs, the available built-in tools include Bash, Read, Write, Edit, Glob, Grep, Web fetch, and Web search, and the full toolset is enabled through the `agent_toolset_20260401` type. The docs also state that an agent is defined by the model, system prompt, tools, MCP servers, and skills.[5][6][1]

For Claude Code skills, what goes “into” a skill is the `SKILL.md` file plus optional resources such as scripts, templates, and reference materials; the docs explicitly say skills are filesystem-based and load on demand. For subagents, the official docs describe them as separate agent instances spawned to handle focused subtasks and isolate context.[2][3][7]

## What this implies about your “agent list”

If by “agent list” you mean the names/descriptions that appear in context, the internet evidence points to these being either:
- the toolset available to an agent,
- the skill catalog metadata,
- or the set of subagents/managed agents defined by the runtime or configuration.[3][1][2][5]

What I **cannot** verify from the sources I checked is a single, user-editable canonical “agent list” that every Claude Code session always loads from a repo file. The official docs instead describe composable pieces: tools, skills, subagents, MCP servers, and system prompts.[6][4][5]

## Best evidence-based conclusion

So the strongest truth is: **the “agent list” is whatever catalog of tools/skills/subagents the runtime exposes for the current agent configuration**. In Claude Code, that catalog is not one monolithic file in the repo; it is a combination of runtime-defined capabilities and user-defined skills/subagents.[4][1][2][5][3]

If you want, I can next turn this into a tight evidence table: “what the official docs prove,” “what they suggest,” and “what remains unproven.”

## Human

please think better.  find evidence for what is meant by agent list for claude code related to context use, and how to affect it's size.

## Assistant

The best evidence I found says “agent list” in Claude Code is not one thing; for **context use**, it most likely refers to the runtime-visible catalog of **skills and subagents**, plus any tool metadata the model sees when deciding what to invoke. Skills are specifically described as modular, filesystem-based resources whose names/metadata are visible up front while the full content loads only when relevant, which is the clearest documented mechanism that affects list size in context.[1][2][3][4][5][6]

## What “agent list” likely means

The official docs support three relevant buckets:
- **Skills**: a set of named capabilities that Claude can invoke when relevant, with on-demand loading and progressive disclosure.[3][1]
- **Subagents**: separate agent instances with isolated context windows for focused subtasks.[5][6]
- **Toolset / managed-agent tools**: the agent configuration can include a defined set of tools, and those tools are part of the runtime-visible capability set.[7][8]

So when people talk about an “agent list” in Claude Code context terms, they are usually talking about the visible catalog of skill/subagent/tool options the model can choose from, not a single file called “agent list”.[1][5][7]

## What goes into it

For skills, the docs and several technical writeups say the visible part is the skill name plus description metadata, while the full `SKILL.md` body and supporting files are only loaded when the skill is triggered. For subagents, the list is essentially the set of available agent types or definitions that can be spawned, each with its own isolated context. For managed agents/toolsets, the “list” is the enabled tools in the agent configuration.[4][9][8][3][5][7][1]

## How to affect its size

The evidence-backed way to make that list smaller is to reduce the amount of always-visible metadata:
- keep skill descriptions short,
- split large skills into smaller ones,
- use progressive disclosure so only the minimal metadata is visible initially,
- and use subagents for high-noise work instead of advertising every capability in the main context.[6][3][4][5]

The official skills docs are the strongest evidence here: they explicitly say on-demand file access means Claude reads only what is needed, and that progressive disclosure keeps only relevant content in the context window. That is the concrete lever you can control; it reduces the effective size of the agent list even if some runtime-visible catalog remains.[3][1]

## What is still unproven

I do **not** have direct evidence that the built-in Claude Code system-reminder agent list itself is user-configurable from repo files. The evidence supports controlling the user-defined side of the catalog—skills, subagents, and tool definitions—but not suppressing a platform-injected list if Claude Code is generating that internally.[10][8][6]

## Practical takeaway

If your goal is context reduction, the best supported approach is:
- shorten skill metadata,
- reduce the number of installed skills/subagents,
- move detail into on-demand files,
- and delegate noisy tasks to isolated subagents.[9][4][5][3]

That won’t prove you can eliminate the built-in list, but it is the strongest documented way to shrink the part you can actually affect.[5][1][3]

## Human

did you check reddit or youtube?

## Assistant

Yes — I checked both, and I found useful evidence from each. Reddit is especially useful for practical patterns and workarounds, while YouTube gives concrete skill-creation advice and examples.[1][2][3][4]

## What Reddit suggests

One Reddit thread says skills are in the main agent’s context while subagents are separate workers, and that subagents preserve the main context. Another thread specifically says the main agent has a list of available skills in its system-reminder tags, while subagents do not, and proposes a hook-based workaround to repopulate that list for subagents. There’s also a report that hidden token overhead can be large even before user input, which supports the idea that startup/system context is a real cost.[5][6][7]

## What YouTube suggests

A YouTube tutorial says good skills should be concise because when Claude decides to use a skill, it loads the skill content into context. Another video frames skills as a way to avoid flooding the context window by packaging a prompt plus reference docs into a modular unit. A different tutorial similarly describes skills as markdown-based, folder-backed packages that let Claude load only the relevant reference materials.[2][3][4]

## What this means for your question

The evidence from Reddit and YouTube is consistent with the official docs: the “agent list” is best understood as the visible catalog of skills/subagents/agents that Claude can choose from, and its context cost is driven by how much metadata and description text is present up front. The practical way people reduce that cost is by keeping the visible list short, making skill descriptions concise, and moving detailed reference material into load-on-demand files.[7][3][4][8][9][10][5]

## Limits of the evidence

Reddit and YouTube are good for implementation patterns, but they are not the same as official documentation. The strongest official evidence still comes from Anthropic/Claude docs saying skills are modular, filesystem-based, and on-demand, while subagents isolate context. So the community evidence supports the official model, but it does not prove a hidden runtime switch for the built-in agent list.[8][9][10][11][12]
