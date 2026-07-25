---
title: "Agentic workflows: Grok / Claude Code / Codex orchestration best practices"
created: 2026-07-24
updated: 2026-07-25
source: session-2026-07-24 (/www research, two runs — Grok workflows + cross-tool best practices) + session-2026-07-25 (/www gap-fill on community sentiment + security incident)
sources:
  - https://x.ai/news/workflows
  - https://code.claude.com/docs/en/workflows
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://openai.com/index/open-source-codex-orchestration-symphony/
  - https://github.com/openai/symphony
  - https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
  - https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns
  - https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/
  - https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/
  - https://avinashsangle.com/blog/claude-code-dynamic-workflows-guide
  - https://www.tamirdresher.com/blog/2026/05/21/deterministic-meets-squads
  - https://tylerfolkman.substack.com/p/claude-code-workflows-are-here-dont
  - https://claudefa.st/blog/guide/development/ultracode-dynamic-workflows-agent-teams
  - https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost
  - https://news.ycombinator.com/item?id=48311705            # HN: Dynamic Workflows in Claude Code (sentiment + best-practice tips) [2026-07-25]
  - https://www.reddit.com/r/ClaudeAI/comments/1tq9ofy/introducing_dynamic_workflows_in_claude_code/   # "big yikes on the cost" consensus
  - https://www.theregister.com/ai-and-ml/2026/07/14/musk-promises-purge-after-grok-build-caught-sending-entire-repos-to-the-cloud/5271123   # Grok Build repo-upload incident
  - https://www.penligent.ai/hackinglabs/grok-build-cli-repository/   # wire-capture analysis of the upload behavior
  - https://cybernews.com/ai-news/grok-build-git-repository-upload/   # independent confirmation + credential-rotation advice
  - https://aiweekly.co/alerts/xai-grok-cli-uploads-full-repos-and-secrets-opt-out-ignored   # multi-source confirmation
  - https://pub.towardsai.net/grok-build-the-fourth-contender-in-the-ai-coding-agent-race-fe14ca73fef1   # Grok parallel sub-agent architecture
  - https://www.buildthisnow.com/fr/blog/tools/extensions/grok-build-vs-claude-code   # 16 concurrent / 1000 total per run; 8 fixed racing agents
tags: [grok-build, claude-code, codex, workflow, rhai, javascript, symphony, orchestration, fan-out, subagents, deterministic, langgraph, framework-matrix, community-sentiment, security-incident, primitive-proliferation]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  A **workflow** is a deterministic script that orchestrates subagents — fan
  a large task out across many parallel agents, each with clean isolated
  context, verify findings adversarially, and synthesize one report. Three
  implementations share the "code orchestrates, model judges" architecture:
  **Grok Build** (Rhai, 128/1024 agents), **Claude Code** (JavaScript,
  "dynamic workflows" + ultracode session toggle), and **Codex** (no native
  script-runtime; uses Symphony — an open-source scheduler that turns an
  issue tracker into a control plane). Optimal for embarrassingly-parallel,
  independently-verifiable tasks; gated by per-agent context-overhead cost
  (~$13/dev/day, ~10× a normal session), not the parallelism ceiling.
---

# Grok Build workflows: Rhai-orchestrated deterministic subagent fan-out

## What it is

A **Grok Build workflow** is an orchestration script written in **Rhai** (an
embeddable scripting language) that fans a task out across many subagents,
runs in the background, and reports back in one structured result. You
describe the task in plain language ("review each feature in this PR"); Grok
plans it as a script of phases, agents in each phase, and a roll-up, then
launches it as a background run.

> "Grok Build can now run **workflows**: describe a large task in plain
> language, and Grok plans it, fans it out across hundreds of parallel agents
> in the background, and reports back when everything is done. Your session
> stays free the whole time."
> — [x.ai/news/workflows](https://x.ai/news/workflows) (published 2026-07-23)

Key parameters (verified against the official announcement + the bundled
`create-workflow` skill):

| Parameter | Value |
|---|---|
| Scripting language | **Rhai** (maps `#{}`, `agent()`, `parallel()`, `phase()`, `complete()`) |
| Default agent budget | 128 logical agent calls per run |
| Max agent budget | 1,024 (caller-set via `agent_budget`) |
| Concurrency model | `parallel()` is the ONLY concurrency; it's a barrier (nothing downstream runs until the slowest job finishes) |
| Agent context | Each agent starts with clean, focused context — no shared conversation bleeding |
| Resume | Progress journaled; pause/resume never redoes committed host calls |
| Saved locations | `.grok/workflows/<name>.rhai` (project/team) or `~/.grok/workflows/<name>.rhai` (user-global) |
| Built-in | `/deep-research` ships built-in (fan-out investigators → verify-against-sources → cited report) |

## Architecture: deterministic orchestration + non-deterministic judgment

Grok workflows are the **deterministic half of a hybrid pattern** (per
[tamirdresher](https://www.tamirdresher.com/blog/2026/05/21/deterministic-meets-squads)
and [Microsoft Conductor](https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/)):

- **Deterministic layer** (the Rhai script): the phases, the fan-out
  sharding, the verification gates, the synthesis roll-up. This is plain
  code — it spends **zero model tokens on coordination**. Loops, branches,
  and barriers are ordinary control flow.
- **Non-deterministic layer** (the agents): each `agent()` call invokes a
  model that reads code, forms judgments, and returns structured output.
  The judgment is where the intelligence (and non-determinism) lives.

This is the "**code orchestrates, model judges**" architecture, coined for
Anthropic's Claude Code workflows (which use JavaScript). Grok Build adopted
the same architecture with Rhai as the scripting language. The lineage is
direct: Claude Code workflows (JS, 2026) → Grok Build workflows (Rhai, Jul
2026).

> **What changed between Claude and Grok:** the orchestration language (JS →
> Rhai). Everything else — the script-as-orchestrator model, the
> fan-out→verify→synthesize shape, the 128/1024 agent budgets, the saved
> workflow as slash-command, the journal-resume semantics — is structurally
> identical.

## When to use a workflow (and when NOT to)

### Use a workflow when

- The work **splits into many independent pieces** that don't share
  intermediate state (parallel code review across N files, parallel research
  across N sources, codebase-wide audit for one class of bug).
- The task is **too large to hold in one conversation** (reviewing every
  feature in a large PR, triaging 100 issues).
- The output should **end in one clear report**.
- Each piece is **independently verifiable** — you can build in adversarial
  skeptics that check every finding before it reaches synthesis.

### Do NOT use a workflow when (disconfirmation-survived qualifiers)

These are the gating constraints the disconfirmation pass surfaced:

1. **The task is small and sequential.** "Use normal Claude Code / Grok when
   the task is small and sequential. Use subagents when you need a few
   independent perspectives. Use a workflow when [the task is large and
   parallel]." — [tylerfolkman](https://tylerfolkman.substack.com/p/claude-code-workflows-are-here-dont)
2. **The task isn't large enough to pay per-agent context overhead.** "Cost
   can jump by an order of magnitude versus a normal session because each
   agent pays its own context overhead. Scope a small task first."
   — [avinashsangle](https://avinashsangle.com/blog/claude-code-dynamic-workflows-guide).
   "Dynamic workflows is awesome but crazy expensive." — [Reddit r/ClaudeCode](https://www.reddit.com/r/ClaudeCode/comments/1tqtlz6/)
3. **Correctness, not parallelism, is the bottleneck.** "My limiting factor
   is not how quickly Claude can self-trudge through code. It's whether Claude
   is going to do the task correctly or not." — [HN](https://news.ycombinator.com/item?id=48311705).
   Workflows optimize throughput; they do not improve per-agent correctness.

## What people like (community sentiment, Jul 2026)

Distilled from the HN "Dynamic Workflows in Claude Code" thread ([48311705](https://news.ycombinator.com/item?id=48311705)),
the r/ClaudeAI launch thread, and Anthropic-internal practitioner reports.
Grok-specific workflow coverage is thin (feature launched 2026-07-23 — 2 days
before this update); the sentiment below is from the Claude Code workflows
predecessor, which is architecturally identical (Rhai vs JS aside).

**What practitioners praise (in their words):**

- **Visibility into in-flight runs.** "The TUI for in-flight dynamic workflows
  is really nice — great visibility into exactly what's happening." The
  script-as-orchestrator model means the run is inspectable in a way a
  model-internal plan is not.
- **Automatic context management at scale.** "For anything larger than a
  1-shot PR, it's worth firing off a workflow for better automatic context
  management alone." Each agent's clean context window is itself a feature —
  it prevents the conversation-pollution failure mode of long single sessions.
- **Effectiveness on long-running tasks.** "Dynamic workflows, in my
  experience, make Claude more effective at complex long-running tasks. They
  help precisely with getting Claude to do the task correctly." This
  contradicts the naive read of "workflows = speed"; the reported win is
  *correctness on tasks too big to hold in one context*.
- **Anthropic-internal adoption.** "Dynamic workflows have been a game
  changer for engineering here at Anthropic." (bcherny, Anthropic staff)

**Concrete quantified wins (Anthropic-internal, bcherny):**

| Metric | Result |
|---|---|
| Claude Agent SDK startup time | **−61%** |
| CPU and memory use | **2–10× improvement** |
| False-positive permission prompts | **−45%** |
| Code deleted in one campaign | **10,000+ lines** |
| Bun Zig→Rust port | 750K lines in 6 days, **99.8% test suite passing** (Jarred Sumner) |

These qualify the "use only for fan-out" framing: workflows also excel at
**sustained single-codebase refactoring campaigns** where the win is
correctness-on-large-scope, not parallelism.

**What practitioners dislike / warn against:**

- **Cost (the universal critique).** Reddit launch-thread consensus: *"a big
  'yikes' on the cost… overwhelmingly [concerned about] the cost."* See
  § "Cost economics" — per-agent context overhead is the driver.
- **Primitive-proliferation confusion.** *"I'm getting so confused when to use
  what… agents, sub-agents, tasks, teammates, /goal, /loop, and now
  workflow."* This is a new failure mode not in the original run: the
  decision isn't "workflow vs not" but "which of 7 coexisting primitives,"
  and vendors have not published clear escalation ladders.
- **Session noise in long runs.** *"Longer sessions will introduce 'noise'."*
  Qualifies the refactoring-campaign wins above — long workflows accumulate
  drift; budget for it or shard.
- **Token-burn suspicion.** *"Is this a way to increase token burn?"* The
  feature is sometimes read as vendor-aligned (more tokens) rather than
  user-aligned (better outcomes).

**Best-practice tips from practitioners (HN thread):**

1. **Use deterministic tools for hard rules, not workflows.** *"If you want
   hard rules, use deterministic tools."* A workflow cannot enforce a rule a
   hook or linter can enforce for free.
2. **Lint-after-edit hooks.** *"Run the linter after each edit through a hook,
   give feedback to the LLM."* The feedback closes the loop inside the agent.
3. **Skills-in-pipeline.** *"Write a skill outlining your expectations of the
   code, put that skill into the pipeline."* The skill is the contract each
   agent in the workflow is held to.
4. **Review-loop with fresh sub-agents.** *"Within a Claude Code session I
   just tell it to spawn three review sub-agents."* Lighter than a full
   workflow when you need adversarial review of one artifact.
5. **Be extremely explicit in prompts.** *"I have to be extremely explicit to
   avoid adding this noise."* Terse prompts to cold sub-agents produce empty
   or garbage returns — see "Terse-prompt garbage" in § Failure modes.

## Patterns that work (reusable shapes)

These recur across the workflow frameworks (Grok, Claude, LangGraph) per the
[5-pattern taxonomy](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work):

| Pattern | How it maps in Rhai | Best fit |
|---|---|---|
| **Fan-out → verify → synthesize** | `parallel(jobs)` → filter failed slots → `parallel(verify_jobs)` → `complete(...)` | The default. PR review, codebase audit |
| **Adversarial verification** | Independent skeptics prompted to refute; require concrete evidence before `real=true` | Any finding that will reach a final report |
| **Loop-until-dry** | Keep spawning finders until two consecutive rounds surface nothing new; `fingerprint()` each round to detect stalls | Open-ended discovery |
| **Vote panels** | N skeptics per item in one flat `parallel()` (items × votes), regroup by index arithmetic | High-stakes decisions needing consensus |
| **Plan → fan-out → synthesize** | `phase("Plan")` → `phase("Execute")` → `phase("Synthesize")` | Work that needs a discovery step before sharding |

The single most important architectural rule: **the orchestrator (Rhai) is
code, not model turns.** A run of 113 agents can spend 1.95M tokens on agent
work while the coordinating script spends zero on coordination. Intermediate
results live in script variables, not in the model's context window.

## Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **Runaway fan-out** | A general-purpose agent decides to spawn more agents autonomously; one prompt → 339 subagents | Cap with `agent_budget`; size panels with headroom for synthesis; refuse over-broad prompts |
| **Context-overhead cost explosion** | Each agent pays its own context overhead; total cost jumps ~10× vs a normal session | Scope a small task first; only fan-out on genuinely independent pieces |
| **Correctness-not-parallelism blindness** | Workflow returns faster wrong answers instead of slower right ones | Adversarial verification gate before synthesis; fail closed on missing evidence |
| **Terse-prompt garbage** | A cold subagent told "count the TODOs" returns `{findings: []}` without running a tool | Command tool use explicitly ("use grep/read_file"); spell out what a valid empty answer requires |
| **Scoping leak** | A discovery agent reaches for `git log --all --name-only` and reports paths far outside the intended root | Re-filter agent output in plain Rhai against the invariant (e.g. keep only paths under `args.root`) before sharding |
| **Silent truncation reads as full coverage** | A `MAX_*` cap drops findings without logging | `log()` whatever got dropped |
| **Primitive-proliferation confusion** | User can't pick among subagent / skill / agent-team / /goal / /loop / workflow; picks workflow by default for tasks that needed a subagent | Use the 4-rung ladder (Claude docs): normal → subagent (few independent) → workflow (many independent) → agent-team (few interdependent). Workflow is *not* the top of the ladder — it's one branch |
| **Vendor data-exfiltration incident (Grok-specific, Jul 2026)** | Grok Build CLI uploaded entire repos — full git history + `.env` secrets — to xAI cloud by default; opt-out was wire-captured to be ignored | **Rotate any credentials that were ever in a repo touched by Grok Build pre-Jul-16-2026.** Treat the CLI as untrusted until open-source audit; for sensitive repos use Claude Code or run on a scrubbed mirror. See [The Register](https://www.theregister.com/ai-and-ml/2026/07/14/musk-promises-purge-after-grok-build-caught-sending-entire-repos-to-the-cloud/5271123), [Penligent wire-capture](https://www.penligent.ai/hackinglabs/grok-build-cli-repository/), [Cybernews](https://cybernews.com/ai-news/grok-build-git-repository-upload/) |

## Rhai dialect specifics (the constraint)

Rhai is the scripting language; it shapes what's expressible:

- Maps are `#{ ... }`; unit `()` is null; `x != ()` is the existence check.
- **No closures** in `parallel()` — takes an array of option maps.
- **No regex** — hand-roll string ops or simplify.
- **No wall-clock or randomness** — `timestamp()`, `sleep()`, `exit()` throw. Pass timestamps via `args`; vary parallel prompts by index, not chance.
- String mutators (`s.trim()`) change in place and return `()` — `x.trim() != ""` is always true. Trim on its own line, then use `x`.
- Reserved keywords (`shared`, `sync`, `async`, `match`, `case`, `default`, `void`, `null`, `nil`, `exit`, `static`, `var`, `new`, `go`, `thread`, `spawn`, `await`) fail with `'X' is a reserved keyword` — rename them.
- Workflows **cannot launch other workflows** — inline the child's logic.

The determinism requirement (control flow derives only from `args` and host
results, never from time or randomness) is what enables **journal resume**:
committed host-call results are reused on resume, so pause/resume never
redoes finished work.

## How to create one

Two paths:

1. **Auto-generate (the default):** describe the task in plain language in a
   Grok Build session ("create and run a workflow to review PR #4821"). Grok
   authors the Rhai script, smoke-checks it (`validate_only: true`), and
   launches. You never write the script.
2. **Hand-author (full control):** use the `/create-workflow` skill (bundled
   at `~/.grok/bundled/skills/create-workflow/SKILL.md`), which is the
   complete authoring procedure + Rhai language reference. Save to
   `.grok/workflows/<name>.rhai` and it becomes `/<name>` as a slash command.

## Cross-tool best practices: Claude Code

Claude Code's "dynamic workflows" ([official docs](https://code.claude.com/docs/en/workflows))
are the direct ancestor of Grok workflows — same architecture, JavaScript
instead of Rhai. Claude distinguishes **four primitives**, not one, and the
decision between them is the highest-leverage best practice:

| Primitive | What decides next step | Where results live | Scale |
|---|---|---|---|
| **Subagents** | Claude, turn by turn | Claude's context window | A few delegated tasks per turn |
| **Skills** | Claude, following the prompt | Claude's context window | Same as subagents |
| **Agent teams** | A lead agent, turn by turn | A shared task list | A handful of long-running peers |
| **Workflows** | **The script** | **Script variables** | Dozens to hundreds per run |

> The core distinction: with subagents/skills/teams, Claude is the
> orchestrator and every result lands in a context window. A **workflow**
> moves the plan into code — the script holds loops, branching, and
> intermediate results, so Claude's context holds only the final answer.

### Claude-specific best practices

- **The subagent→workflow escalation ladder:** normal Claude Code (small,
  sequential) → isolated subagents (a few independent perspectives) →
  workflow (many items / verify-discover-rank at scale). Pick wrong at the
  low end and you cap scale; pick wrong at the high end and you burn 2–4×
  tokens. — [tylerfolkman](https://tylerfolkman.substack.com/p/claude-code-workflows-are-here-dont),
  [claudefa.st](https://claudefa.st/blog/guide/development/ultracode-dynamic-workflows-agent-teams)
- **`ultracode`** is a *session policy*, not a third execution model. It
  sets model to `xhigh` reasoning effort AND auto-orchestrates a workflow
  for every substantive task in the session. Use it for an audit-grade
  session; drop back to `/effort high` the moment you return to routine
  edits — the workflow layer applies to *every* substantive task whether it
  needed one or not. — [Claude Code docs](https://code.claude.com/docs/en/workflows)
- **Approval modes matter:** Default/accept-edits prompts every run; Auto
  prompts first-launch only (and is skipped when ultracode is on);
  Bypass/`-p`/Agent SDK never prompt. Don't run workflows in bypass mode
  without a verification gate — the script's adversarial check is your only
  safety net.
- **Workflows vs Agent Teams (the trap people fall into):** a workflow fans
  out across isolated agents that **never talk to each other** (structure
  fixed in code before anything runs). An Agent Team is a **small set of
  peers that message each other and renegotiate the plan live**. Use teams
  for 2–5 interdependent pieces whose interface is still moving (schema +
  API + UI designed together). Use workflows for "same thing across many
  items" or "verify/discover/rank at scale." — [claudefa.st](https://claudefa.st/blog/guide/development/ultracode-dynamic-workflows-agent-teams)
- **The landmark case:** Jarred Sumner ported ~750,000 lines of Bun from Zig
  to Rust in **6 days** using dynamic workflows — hundreds of parallel
  subagents, each writing a `.rs` file, each reviewed by two adversarial
  agents, 99.8% of the test suite passing. This is the existence proof that
  workflows work at migration scale. — [lassiecoder/Medium](https://medium.com/illumination/claude-codes-dynamic-workflows-the-ai-agent-architecture-that-just-rewrote-750-000-lines-of-code-d605a1d9b6d4)

## Cross-tool best practices: Codex / Symphony

Codex CLI takes a **fundamentally different approach** — it has no native
deterministic script-runtime like Grok's Rhai or Claude's JS. Instead,
OpenAI built **[Symphony](https://github.com/openai/symphony)**, an
open-source spec that turns an issue tracker (Linear) into a control plane
for coding agents.

| Dimension | Grok / Claude workflows | Codex / Symphony |
|---|---|---|
| **Orchestration unit** | A script (Rhai / JS) run per task | An issue on a tracker, run continuously |
| **Trigger** | You ask for it in a session | The tracker has an open task |
| **Lifetime** | One run (background, resumable) | Always-on daemon (never sleeps) |
| **What the human does** | Reviews the report | Files tickets; reviews PRs |
| **Scale evidence** | 128–1024 agents per run | 500% increase in landed PRs at OpenAI |

### Symphony-specific best practices (from OpenAI's own account)

- **Decouple work from sessions and PRs.** Tickets can represent much larger
  units than a single PR. Some issues produce multiple PRs across repos;
  others are pure investigation that never touch the codebase.
- **Use ticket status as a state machine.** Symphony watches the board and
  ensures every active task has an agent running. If an agent crashes, it
  restarts. The DAG of dependencies executes naturally in parallel.
- **Give agents objectives, not strict state transitions.** "Treating agents
  as rigid nodes in a state machine doesn't work. Models get smarter and can
  solve bigger problems than the box we try to fit them in." Give them tools
  (`gh` CLI, CI-log skills) and let them reason. — [OpenAI](https://openai.com/index/open-source-codex-orchestration-symphony/)
- **Shepherd PRs through the last mile.** Symphony watches CI, rebases,
  resolves conflicts, retries flaky checks — the fragile part of landing a
  PR in a large monorepo.
- **Lose the ability to nudge mid-flight.** The tradeoff of ticket-level
  dispatch: you cannot course-correct interactively. "Sometimes the agent
  produced something that completely missed the mark." Mitigation: add
  guardrails and skills so agents succeed the next time, rather than patching
  the result manually.
- **Not every task fits.** "Some problems still require engineers working
  directly with interactive Codex sessions, especially ambiguous problems or
  work that requires strong judgment." Symphony handles the bulk of routine
  implementation; humans focus on hard single problems.

### Codex's other orchestration paths

- **Native subagents** (Codex CLI 2026): can spawn subagents within a session.
- **Agents SDK + Codex-as-MCP-server**: expose Codex as a tool to the OpenAI
  Agents SDK for custom orchestration. ([OpenAI cookbook](https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk))
- **External harnesses** (e.g. Intent): users run 15+ agents from one prompt
  via a CLI harness on top of Codex.

## Framework comparison matrix

The [5-pattern taxonomy](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
+ [7-pattern set](https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns)
collapses to five reusable shapes. Which framework supports which natively:

| Pattern | What it does | LangGraph | Claude/Grok workflows | Codex/Symphony | CrewAI | AutoGen |
|---|---|---|---|---|---|---|
| **Fan-out** | Same/N tasks in parallel, aggregate | ✅ native | ✅ native (`parallel()`) | ⚠️ via DAG | ✅ native | ✅ native |
| **Pipeline** | Sequential stages, each feeds next | ✅ native | ✅ via `phase()` | ✅ via ticket flow | ✅ native | ✅ native |
| **Supervisor** | Lead agent decomposes + synthesizes (2–5 subtasks) | ✅ native | ✅ native (subagents) | ⚠️ via harness | ✅ hierarchical | ✅ native |
| **Debate** | N agents argue, judge arbiters | ✅ patternable | ⚠️ build-your-own | ❌ | ⚠️ patternable | ✅ native |
| **Swarm** | 50+ dynamic agents, dynamic population | ⚠️ patternable | ⚠️ build-your-own | ❌ | ❌ | ⚠️ patternable |

**2026 production default: supervisor.** It has the widest native framework
support, the best-understood failure mode (over-delegation, bounded by
iteration ceilings), and the most production references. Add fan-out
branches when subtasks are genuinely independent. Use debate when stakes
justify ~2.5× cost. Reach for swarm only at 50+ genuine concurrent agents.

**Where each tool wins:**
- **LangGraph** — most broadly capable (native/patternable across all 5);
  best for complex workflows with conditional logic, feedback loops,
  long-running checkpointed jobs. Cost: significant infrastructure overhead.
- **Claude/Grok workflows** — excel at fan-out + supervisor, embedded in the
  coding CLI, no separate infrastructure. Require custom code for debate and
  swarm.
- **Codex/Symphony** — excels at always-on, ticket-driven continuous work.
  Not a script-runtime; a scheduler.
- **CrewAI** — ideal for prototyping and role-based "crews" with shared
  context. Simple multi-agent.
- **AutoGen** — structured multi-agent conversations; strongest debate
  support.

**Swarm frontier (the 5th pattern):** Kimi K2.6 (Moonshot AI) ships swarm
as a first-class native primitive — 300 parallel sub-agents executing
4,000-step coordination, 13-hour autonomous coding sessions, 256K context.
No other framework ships swarm natively at this scale. This is where the
"1024 max" workflow ceiling sits competitively: Grok/Claude can *pattern*
swarm but don't optimize for it.

## Cost economics (the gating constraint, quantified)

The disconfirmation pass established that cost — not the parallelism ceiling
— is the real gate. The numbers:

- **~$13 per developer per active day**, **$150–250 per developer per
  month** on Claude Code (Anthropic's own enterprise figures). — [developersdigest cost analysis](https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost),
  [morphllm](https://www.morphllm.com/ai-coding-costs)
- **Per-agent context overhead is the cost driver.** Each agent re-pays the
  cost of entering context. A workflow with N agents pays N × context-entry
  cost, which is why total cost can jump an **order of magnitude** versus a
  normal session. — [avinashsangle](https://avinashsangle.com/blog/claude-code-dynamic-workflows-guide)
- **Debate costs ~2.5× single-model.** Microsoft Copilot Council runs GPT-5.4
  and Claude in parallel, then a judge model to arbitrate — ~2.5× the cost
  of a single-model call. The two-stage Critique variant adds ~20%. Use
  debate when stakes justify the premium, not as a default quality booster.
  — [digitalapplied](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
- **Context compression saves 40–95% on tokens.** A code knowledge graph that
  gives agents exactly the context they need (vs. stuffing the window) cuts
  cost dramatically. — [jakenesler/Medium](https://medium.com/@jakenesler/context-compression-to-reduce-llm-costs-and-frequency-of-hitting-limits-e11d43a26589)
- **Kimi K2.6 is the cost-efficient frontier:** cache hit $0.30/MTok, input
  $3.00/MTok — cheaper than Gemini 2.5 Pro ($1.25/$10.00) and far cheaper
  than frontier Claude/GPT. Relevant when swarm-scale fan-out makes
  per-token cost dominate.

**Practical implication:** scope a small task first to estimate the
agent-count multiplier before launching a full workflow. A 100-agent
workflow is not 100× the cost of one agent — it's roughly 100× the
context-entry cost, which can exceed a full day's Claude Code spend in a
single run.

## Decision context (why this research was needed)

**The motivating question:** the operator asked "what's a Grok workflow?"
The real question behind it: *is the workflow system worth adopting for this
fleet, and if so, when — and how does it compare to Claude Code and Codex
orchestration?* The feature had launched 18 hours before the first research
run, so the local wiki had no coverage and the operator needed a grounded,
comparative understanding before deciding to invest agent time in building
workflows. A follow-up run extended coverage to Claude Code and Codex after
the operator asked whether best practices for each tool had been captured.

**Alternatives explored during research:**
- Whether Grok workflows are unique to xAI or a broader industry pattern →
  found they are xAI's Rhai adaptation of Anthropic's Claude Code workflows
  (JS), which are themselves one instance of the "deterministic
  orchestration" movement (Microsoft Conductor, diagrid Dapr, LangGraph).
- Whether they compete with general orchestration frameworks (LangGraph,
  AutoGen, CrewAI) → found they occupy a specific niche: agent-native,
  embedded in the coding CLI, no separate infrastructure. LangGraph is more
  broadly capable (native across all 5 orchestration patterns); Grok/Claude
  workflows excel at fan-out + supervisor but require custom code for debate
  and swarm.
- Whether Codex has an equivalent → it does NOT have a script-runtime.
  Instead it has Symphony (issue-tracker-as-control-plane) + native
  subagents + Agents-SDK-as-MCP-server. The architectural difference is
  fundamental: Grok/Claude orchestrate *within a session*; Codex/Symphony
  orchestrates *across sessions continuously*.
- Whether the pattern is debunked or has known failure modes → confirmed the
  cost-explosion and correctness-not-parallelism failure modes via the
  disconfirmation pass (Reddit, HN, avinashsangle).

**What the research changed:** it established that (1) Grok workflows are the
deterministic-orchestration half of a hybrid, not a standalone solution; (2)
the gating constraint is per-agent context cost (~$13/dev/day baseline, ~10×
under fan-out), not the 1024-agent ceiling; (3) the optimal use case is
bounded: large, parallel, independently-verifiable tasks ending in a report;
(4) the three tools are complementary, not competing — Grok/Claude for
in-session fan-out, Codex/Symphony for always-on ticket-driven work,
LangGraph for complex graph-structured workflows. This narrows the decision:
adopt Grok workflows for PR review / codebase audit / issue triage; do NOT
adopt them as a general "make agents faster" layer — correctness is the real
bottleneck for most work.

**Run 3 (2026-07-25) additions** — gap-fill on the operator's "what people
like / what to avoid" framing. Three new findings: (a) **community sentiment
is net-positive on visibility + context-management + long-task correctness,
net-negative on cost** — the praise is not "speed" but "correctness on tasks
too big for one context"; (b) **primitive-proliferation confusion** is a new
failure mode — vendors ship 7 coexisting primitives (subagent / skill /
team / /goal / /loop / workflow / agent) without an escalation ladder;
(c) **the Grok Build repo-upload security incident (Jul 12-16, 2026)** is a
Grok-specific "what to avoid" missing from the original runs — any credentials
in a repo touched by Grok Build pre-Jul-16 should be considered exposed and
rotated. Also added bcherny's Anthropic-internal quantified wins (SDK startup
−61%, CPU/mem 2-10×, false-positive prompts −45%, 10K+ LOC deleted), which
qualify the "fan-out only" framing: sustained single-codebase refactoring
campaigns are a second fit pattern, not just parallel fan-out.

## Related

- [[brainstorming-ideation-with-llms]] — Claude Code workflow patterns + ultracode (the JS predecessor)
- [[llm-handoff-best-practices]] — agent context isolation (the "clean focused context" property)
- [[agentic-sdlc-skill-lifecycle-architecture]] — where workflows sit in the agent SDLC maturity model
- [[dead-code-detection-workflow]] — a *process* workflow (not a Rhai script), complementary terminology
