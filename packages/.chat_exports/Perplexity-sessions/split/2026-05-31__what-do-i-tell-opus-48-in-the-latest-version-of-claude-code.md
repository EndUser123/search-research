---
title: "what do I tell opus 4.8 in the latest version of claude code so that it delegate to a cheaper model to save costs"
date: "2026-05-31"
mode: "COPILOT"
uuid: "d7bf5892-9022-41af-bc4b-04c55d921f3a"
entry_count: 3
---

## Human

what do I tell opus 4.8 in the latest version of claude code so that it delegate to a cheaper model to save costs

## Assistant

You can’t currently “auto‑delegate” Opus 4.8 to a cheaper base model just by saying “use a cheaper model” in plain language; you either (a) run Claude Code itself on a cheaper model, or (b) use Opus to orchestrate explicit sub‑agents/skills that call Sonnet/Haiku for specific work.[1][2]

Below I’ll lay out the two concrete patterns that actually save money today, plus how I’d wire them given your background.

## Option 1: Run Claude Code on a cheaper model

The simplest cost control is to change the model Claude Code itself uses, either per‑session or as a default.[2]

### Change model for the current Claude Code session

In your terminal, when you start Claude Code:

```bash
# Example: use Sonnet instead of Opus for this session
claude --model claude-sonnet-4-6

# Or Haiku:
claude --model claude-haiku-4-5-20251001
```

Claude Code will then use that model for all interactions in that session.[2]

If you’re already inside a Claude Code session, you can type:

```text
/model
```

Then choose a cheaper model (e.g. Sonnet 4.6 or Haiku 4.5) from the interactive menu.[2]

### Set a cheaper model as the default

If you want all new Claude Code sessions to default to a cheaper model, set the `ANTHROPIC_MODEL` env var in your shell config.[2]

For bash (Linux, WSL, or PowerShell via bash):

```bash
echo 'export ANTHROPIC_MODEL="claude-sonnet-4-6"' >> ~/.bashrc
source ~/.bashrc
```

For zsh (macOS):

```bash
echo 'export ANTHROPIC_MODEL="claude-sonnet-4-6"' >> ~/.zshrc
source ~/.zshrc
```

Then start Claude Code with:

```bash
claude
```

All sessions will now use that cheaper model by default until you override it.[2]

**Tradeoff:** You lose Opus‑level reasoning everywhere, so this is best if you’re okay with Sonnet/Haiku as your main coding copilot most of the time.

## Option 2: Use Opus as an orchestrator with cheaper sub‑agents

If you want Opus 4.8 for “brainy” tasks but cheaper models for grunt work, the pattern Anthropic pushes is: use Opus as the top‑level agent and define skills/sub‑agents that explicitly run on Sonnet/Haiku.[3][1]

### High‑level pattern

Conceptually:

- Opus 4.8:
  - Plans the work, decomposes tasks, verifies critical pieces.
  - Decides *when* to call a cheaper model.
- Cheaper sub‑agents (Sonnet/Haiku):
  - Handle repetitive transformations, simple summarization, quick code rewrites, or mechanical refactors.

In Claude Code, skills can be bound to specific models; the larger model can call a skill with its own model configuration.[1]

Given your background, you’d treat this as a mini‑orchestrator:

1. Define a “cheap‑model skill” that:
   - Accepts a task description + context.
   - Dispatches that to Sonnet/Haiku (or an API wrapper) with strict constraints.
2. In your Opus session prompt, instruct:
   - “For simple tasks X/Y/Z, call the cheap‑model skill; keep the main Opus context small and only pull results back when needed.”

### Example: Prompt pattern for Opus

Inside Claude Code (running on Opus 4.8), you can establish an explicit control contract like:

> You are the primary orchestrator running on claude‑opus‑4‑8.  
> Whenever you detect a task that is:
> - Purely mechanical code transformation, or  
> - Simple summarization or format conversion, or  
> - A self‑contained question answerable from provided context,  
> then you **must** route that task to the `cheap_subagent` skill instead of doing the work yourself.  
> Only perform high‑effort reasoning when:
> - The task requires cross‑file reasoning, or  
> - The task involves novel architecture decisions, or  
> - Safety/epistemic validation is needed.  
> Ask for confirmation if you’re unsure which path to take.

You then implement `cheap_subagent` as a skill bound to Sonnet/Haiku (via Claude Code tools or your own API path), so Opus’s “call skill” action actually uses the cheaper model.

**Important:** This isn’t auto‑delegation; you’re building an explicit routing layer and telling Opus how to use it. That is currently the only “delegation” mechanism that reliably saves money.[1]

## Using effort levels and fast mode with Opus 4.8

Opus 4.8 adds effort control and a new fast mode, which change cost and performance tradeoffs even if you stay on Opus.[4][5]

Key facts:

- Regular Opus 4.8 pricing is the same as Opus 4.7 baseline: about 5 per million input tokens and 25 per million output tokens.[5]
- Fast mode for Opus 4.8:
  - Up to 2.5× output speed.
  - Now three times cheaper than fast mode on previous Opus models (same 10/50 structure but at lower relative cost vs older fast modes).[6][7][4]
- Effort levels:
  - Default is “high” (balanced quality vs speed).
  - You can use lower effort for cheaper, faster responses; higher modes (“extra”, “max”, “ultra code”) spend more tokens for tougher tasks.[8][4][5]

In Claude Code, you can toggle fast mode with a `/fast` command, and effort levels via effort settings in the interface.[9][3]

**Cost strategy if you stay on Opus 4.8:**

- Use **low/medium effort** for trivial requests and rely on your own judgement to keep prompts lean.
- Reserve **extra/max** only for:
  - Complex architecture questions.
  - Large‑scale refactors.
  - Long‑running workflows where missteps are more expensive than extra thinking.[4][5]

This won’t “delegate to a cheaper model,” but it *does* moderate Opus’s token use per task.

## What you cannot do (yet)

Based on Anthropic’s public docs and community notes:

- There is no built‑in switch like “run small tasks on Haiku automatically” inside Claude Code without you defining skills/sub‑agents or changing the model manually.[1][2]
- There’s no native per‑request “use Opus to think but Haiku to answer” toggle in Claude Code UI today; that kind of pattern needs to be implemented in an API‑level orchestrator or via skills.[10][1]

**Confidence:** High that the mechanisms I’ve described are the main supported paths as of May 2026, but moderate on exact UX details for any newly released dynamic workflows, which Anthropic is actively iterating on.[11][3]

Given how you work, are you primarily trying to reduce cost inside **interactive Claude Code sessions**, or are you designing an **API‑side orchestrator** (e.g., with LangGraph/Bifrost) where Opus routes to Sonnet/Haiku for sub‑tasks?  

## Human

reduce cost inside interactive session.   Would I put this in the claude.md?  "You are the primary orchestrator running on claude‑opus‑4‑8.
Whenever you detect a task that is:

Purely mechanical code transformation, or

Simple summarization or format conversion, or

A self‑contained question answerable from provided context,
then you must route that task to the cheap_subagent skill instead of doing the work yourself.
Only perform high‑effort reasoning when:

The task requires cross‑file reasoning, or

The task involves novel architecture decisions, or

Safety/epistemic validation is needed.
Ask for confirmation if you’re unsure which path to take."

## Assistant

You *could* put logic like that in `CLAUDE.md`, but by itself it will not cause Opus to actually “route” work to a cheaper model inside a single interactive session, because Claude Code does not currently support per‑request model switching or sub‑agent delegation purely via instructions.[1][2]

## What `CLAUDE.md` is good for

`CLAUDE.md` is read at the start of each session in that repo and used as persistent project‑specific context, so it’s ideal for:[2][1]

- Architecture overview and constraints  
- Coding conventions, tooling rules, safety policies  
- High‑level “how to collaborate” instructions  

Anthropic and community guides explicitly recommend a *tight* `CLAUDE.md` and moving specialized behaviors into slash commands or other mechanisms to avoid token bloat.[3][4][1]

So adding some *lightweight* cost‑control instructions there is reasonable, but it won’t magically create routing to Haiku/Sonnet unless you manually switch models or define tools/flows that actually call them.[5][2]

## Why your orchestrator text doesn’t do what you want

Your text:

> “You are the primary orchestrator… route that task to the `cheap_subagent` skill…”

assumes that:

1. Claude Code has a `cheap_subagent` skill configured that calls a cheaper model, and  
2. Opus can change models mid‑session for individual actions.

Today, in interactive Claude Code:

- Model selection is per session; you pick the model with `/model` or when launching `claude`.[2][5]
- Delegation to other models requires explicit tools / API orchestration; Claude Code doesn’t expose a built‑in “call Haiku as a sub‑agent” primitive in the UI.[5][2]

So putting those instructions in `CLAUDE.md` is *descriptive*, but there’s no corresponding mechanism wired up to obey them. Opus will just try to follow the spirit of the instructions *using itself*.

**FACT vs SPECULATION**

- FACT: `CLAUDE.md` is used as persistent context and can shape behavior; it does not change which model is used or create real sub‑agents.[1][2]
- CONSENSUS: The most effective cost savings in interactive sessions come from model choice (`/model`), context management (`/compact`, `/clear`), and lean `CLAUDE.md`, not from complex orchestrator prompts.[6][2][5]
- SPECULATION (medium confidence): Very detailed orchestration instructions in `CLAUDE.md` may increase tokens and cognitive overhead without delivering proportional savings.

## What I’d actually put in `CLAUDE.md`

Given that you want to stay in an Opus 4.8 interactive session but reduce cost, I’d keep `CLAUDE.md` under ~100–150 lines and encode *simple, cheap* behavior rules, not an elaborate routing story.[4][3]

Example (shortened, tuned for cost):

```markdown
# Claude collaboration contract

- Default to **concise** answers; prefer bullet lists.
- Before long reasoning or code generation, briefly state a plan.
- Ask for confirmation before starting any multi-step refactor.

## Cost and context discipline

- Treat this repo as **architecture/complex** work only.
- For purely mechanical tasks (formatting, simple rewrites, trivial Q&A),
  I will usually switch to a cheaper model with `/model`.
- When my instructions are ambiguous, ask for clarification
  instead of guessing and producing long speculative output.
- If the conversation becomes long or topic changes, propose using `/compact`
  or starting a fresh session with a short summary.

## Code manipulation preferences

- Prefer minimal diffs and explicit patch descriptions.
- When editing large files, operate on specific ranges, not entire files.
```

This:

- Keeps `CLAUDE.md` lean (low token overhead)  
- Gives Opus a clear *behavior profile* for your interactive usage  
- Puts the *routing decision* back in your hands (via `/model`)

Then, in practice, you:

- Run Sonnet/Haiku sessions for routine work: `claude --model claude-sonnet-4-6` or `/model` mid‑session.[2][5]
- Use Opus 4.8 for gnarly reasoning and architecture only.[2]

## Concrete, low‑friction cost levers in interactive sessions

These are the levers that have strong empirical backing:

1. **Switch model mid‑session with `/model`**  
   - Use Haiku for mechanical tasks, Sonnet for daily work, Opus for hardest problems.[4][5][2]
   - You can keep multiple sessions open (different terminals) for different roles.

2. **Control context size aggressively**  
   - `/compact` when the conversation gets long, especially after resolving an issue.[1][2]
   - `/clear` or start a new session when switching to an unrelated task.[6][1]

3. **Keep `CLAUDE.md` small and focused**  
   - Guides recommend under ~200 lines; some go as far as 50 lines to minimize overhead.[3][4]
   - Move detailed workflows into slash commands under `.claude/commands/` instead of bloating `CLAUDE.md`.[7][1]

4. **Use `/cost` to create a feedback loop**  
   - Check frequently (`/cost` every 5–15 messages) to see where tokens go and adjust habits.[8][6][1]

Given all this, I’d *not* paste your whole orchestrator block into `CLAUDE.md`. I’d instead:

- Put a short “cost discipline” section as above.  
- Rely on `/model` to actually use cheaper models for interactive mechanical tasks.  
- Keep any real routing/orchestration logic in a separate, explicit tool or API orchestrator if you need it later.

If you share a typical “day in the life” for your Claude Code use (e.g., how often you’re doing mechanical edits vs deep design), I can propose a concrete model‑switching and session‑management pattern that hits a target monthly spend.

## Human

Is there a hook we can use for this?  Are there repos that have already done this?

## Assistant

Yes — there are **two viable mechanisms** here: subagents and hooks. For interactive Claude Code cost reduction, subagents are the official mechanism for routing specific work to cheaper models, while hooks are the enforcement/automation layer that can recommend or even auto-switch the session model.[1][2]

Your original `CLAUDE.md` idea is weaker than either of those, because Claude Code now officially supports custom subagents with their own `model` field, and the docs explicitly say subagents can be used to “control costs” by routing tasks to cheaper models like Haiku.[1]

## Best mechanism

For your specific goal — *reduce cost inside an interactive session* — the cleanest supported pattern is:

- Keep the **main session** on Opus only when you truly need it.
- Create one or more custom **subagents** with `model: haiku` or `model: sonnet` for mechanical work.
- Optionally add a **hook** that warns or auto-switches the top-level session when the prompt obviously belongs on a cheaper tier.[2][1]

This matters because Claude Code’s subagent docs state:

- Subagents have their own context window, own prompt, tool access, and model choice.[1]
- Claude can delegate to them automatically when the description matches.[1]
- The `model` field supports `haiku`, `sonnet`, `opus`, full model IDs, or `inherit`.[1]

So the official answer is: **yes, use a subagent for delegation; use hooks if you also want deterministic routing or session-model switching.**[2][1]

## Hooks you can use

Claude Code supports lifecycle hooks in `settings.json`, and hook events fire independently of model intent, which makes them useful for deterministic routing policies.[3][4]

The most relevant hook points for this use case are:

- `SessionStart` — inject model-tier guidance or setup state.[2]
- `UserPromptSubmit` — inspect the user prompt before the turn proceeds, then warn or mutate config.[2]
- `PreToolUse` / `PostToolUse` — more useful for enforcement, validation, and guardrails than for model routing.[4][1]

There is a key limitation, though:

- A hook can **recommend** a different model or even modify `settings.json` to auto-switch the session model.[2]
- A hook does **not** natively force the already-running model to answer that same turn using a cheaper model unless the hook implementation changes the active session config in time and Claude Code honors it for the next step. That is implementation-dependent and somewhat hacky.[2]

So from a reliability standpoint:

- **Subagent routing = first-class, supported.**[1]
- **Hook-based autoswitch = practical, but more of a userland hack/policy layer.**[2]

## Repos that already did it

There is at least one repo that has already implemented this pattern directly for Claude Code:

| Repo | What it does | Evidence |
|---|---|---|
| [tzachbon/claude-model-router-hook](https://github.com/tzachbon/claude-model-router-hook) | Classifies prompts by complexity, warns on mismatch by default, can auto-switch `settings.json`, and injects subagent model-selection rules at `SessionStart`. [2] | The README says it uses `SessionStart` plus `UserPromptSubmit`, supports `warn` or `autoswitch`, and defines tier rules for Haiku/Sonnet/Opus. [2] |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | Curated collection of Claude Code subagents, useful as implementation examples for task-specific delegation patterns. [5] | Search results identify it as a repository of Claude Code subagents. [5] |

The strongest match to your question is `tzachbon/claude-model-router-hook`, because it is explicitly about **automatic model switching for Claude Code** and describes the exact routing heuristic you were trying to express in prose.[2]

Its documented behavior includes:

- `session-init.sh` on `SessionStart` to inject sub-agent model rules.[2]
- `model-router-hook.sh` on `UserPromptSubmit` to classify prompts and compare the recommended tier with the current model.[2]
- Default `action: "warn"`; optional `action: "autoswitch"` to edit `settings.json` automatically.[2]

That is very close to a productionized version of your idea.

## What I would recommend

Given your preference for deterministic control and minimal changes, I would use a **hybrid** setup:

1. Create explicit cheap subagents in `~/.claude/agents/` or `.claude/agents/`.
2. Add a hook that warns when a prompt is mismatched for the current session model.
3. Only use auto-switch after you trust the classifier.[1][2]

Example cheap subagent:

```markdown
---
name: cheap-mechanical
description: Use for simple mechanical tasks like formatting, grep-style code lookup, small renames, simple rewrites, and self-contained summarization.
tools: Read, Grep, Glob, Bash, Edit, Write
model: haiku
effort: low
---

You handle narrow, mechanical tasks cheaply and concisely.
Do not do architecture work.
Escalate back to the parent if the task requires cross-file reasoning, design tradeoffs, or uncertain interpretation.
```

This is fully aligned with the official subagent config model, including `model`, `tools`, and `effort`.[1]

Then pair it with a hook like the router repo’s `UserPromptSubmit` classifier so that when you type “rename these imports” or “format and commit this,” you get either:

- A warning: “recommended Haiku,” or
- An automatic switch, if you enable that mode.[2]

## Caveats

A few important constraints from the docs:

- Subagents can use their own model, but they work **within the same overall session**, not as free-form recursive agents.[1]
- Subagents cannot spawn other subagents, so you don’t get infinite agent trees.[1]
- If you add/edit subagent files manually on disk, you usually need to restart the session for them to load, unless created through `/agents`.[1]
- Plugin subagents do not support all frontmatter fields like `hooks`, `mcpServers`, or `permissionMode`; user/project subagents are more flexible.[1]

**Confidence:** High that subagents are the best official solution; medium-high that hook-based autoswitch is workable today because a real open-source implementation exists, but lower confidence on how robust it is across future Claude Code releases.[1][2]

If you want, I can draft a **minimal `.claude/settings.json` hook config plus 2–3 subagent files** tailored to your workflow: one for mechanical edits, one for repo exploration, and one for deep architecture.
