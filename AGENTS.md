# AGENTS.md

## Skill-specific instructions override general heuristics

When a skill gives a specific instruction, follow it exactly. If a general rule and the skill conflict, **the skill wins.** See `wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md`.

## Maintenance reminders

- Run `/recover` immediately when a file is missing after concurrent agent activity.
- Run `python P:/.data/wiki/scripts/index_skills.py --audit` quarterly.

## Search Topology (read before any existence/absence claim)

`P:\` is a multi-root workspace. Code for one subsystem is split across these roots:

| Root | What lives there |
|------|------------------|
| `P:\.claude\hooks\` | User-level hooks (dispatched from `~/.claude/settings.json`) |
| `P:\.claude\scripts\` | Maintenance/audit scripts (e.g. `hooks_audit.py`) |
| `P:\packages\.claude-marketplace\plugins\<name>\` | Plugin SOURCE (canonical) |
| `~\.claude\plugins\cache\` | Version-keyed plugin CACHE — never edit |
| `P:\.claude\worktrees\`, `P:\worktrees\`, `P:\tmp\` | Stale copies/experiments — exclude from truth claims |

Never claim a file "does not exist" until you've searched both live roots:
```
rg --files -g "*<name>*" P:/.claude/hooks P:/.claude/scripts P:/packages/.claude-marketplace/plugins
```
For hook ground truth: `python P:/.claude/scripts/hooks_audit.py --packages P:/packages/.claude-marketplace/plugins`

## Host runtime: Grok Build (not Claude Code)

Before assuming a Claude Code feature works identically here, verify against `~/.grok/docs/user-guide/`. Known differences:

| Area | Claude Code | Grok Build |
|------|-------------|------------|
| Hook types | `command`, `prompt`, `agent` | `command`, `http` only |
| Hook discovery | `~/.claude/settings.json` + plugins | All hook scopes merge. See `~/.grok/docs/user-guide/10-hooks.md` |
| Slash commands | `.claude/commands/` | `.grok/commands/` |
| Session ID env | `$CLAUDE_SESSION_ID` | `$GROK_SESSION_ID` |

**Rule:** cite the Grok Build doc that confirms a feature works here before proposing any hook, command, or skill mechanism.

**Session start:** read `~/.grok/active-surface.last.md` before assuming any documented enforcement is active. Trust the snapshot over documentation when they conflict. Re-run `python ~/.grok/hooks/scripts/active_surface_snapshot.py` if config changed mid-session.

**Session start — surface open work:** after reading the active-surface
snapshot, run:
- `harvest show --top 5` (with `HARVEST_HOME=P:/.data/harvest`) — shows
  open obligations from this and prior sessions
- `python P:/.agents/scripts/workspace_opportunity_scan.py` — surfaces
  gaps, pending suggestions, and untested changes

Present as a brief "open work" summary — one or two lines. Skip if both
return nothing.

## Model routing policy (read before dispatching subagents)

Read `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` and `P:/.data/wiki/concepts/context-firewall-architecture.md` before dispatching subagents. Pass `model=<domain-default>` instead of inheriting parent Grok.

## Delegation signal — prepare, don't implement

When the user's prompt connects a task to a future or separate session (triggers: "for a fresh cold start LLM," "for next session," "to be picked up cold"), default to producing a delegation packet — objective, scope, acceptance criteria, file paths, constraints. Do NOT implement unless the user says "do this now" / "ship it" / "go ahead."

## Scope drift re-anchor

When current work is in a different subsystem than the original user request, emit once per drift event: `Note: session started on <original task>; current work is <current task>.` Not a question, not a gate. If the user says nothing, continue.

## Proactive skill suggestions

After completing work, proactively recommend the right skill at the right
time. One line at end of turn. Do not auto-invoke; recommend.

**Exception — `/wiki` auto-captures (see `~/.grok/AGENTS.md` "Decision-and-fix documentation rule"):** when the agent produces durable findings or decisions, it appends a `WIKI:` marker and auto-runs `/wiki` at session boundaries (before `/handoff` or `/close`). This is the only skill that auto-fires — because knowledge capture has the highest miss-cost and the operator should not have to remember.

**Verification skills:**
- **`/check`** when: ≥2 concerns touched, runtime claims unverified, about to claim "done."
- **`/review`** when: hooks/plugins/schemas/dispatch chains touched, new enforcement introduced, shared infrastructure modified.
- **`/fmea`** when: pipeline scripts written or modified (Python files with I/O ops). Run before scaling a pipeline or after refactoring one.

**Knowledge and continuity skills:**
- **`/wiki`** when: durable knowledge produced (new pattern, decision with rationale, transferable technique) but not yet captured.
- **`/handoff`** when: work spans sessions, open workstreams exist, or session is ending with unfinished threads.

**Improvement and learning skills:**
- **`/harvest`** when: root causes diagnosed, error patterns identified, or unrealized obligations exist (the standing question in /tp, /aar, /harvest fires this).
- **`/aar`** when: ≥2 operator corrections happened (behavioral pattern signal), or session had material failures with recoverable lessons.

**Skip when:** trivial work, already ran the skill, or user said "quick."

## Workspace knowledge is primary input

The thing that makes the agent great is treating the workspace's accumulated
knowledge (wiki, skills, prior decisions, handoffs) as the **primary input**,
and its own reasoning as the **secondary input**. Before proposing any solution:

1. **Search the wiki** for existing solutions, patterns, or prior decisions
2. **Search handoffs** for related open work
3. **Search skills** for capabilities that already exist
4. **Then reason** — informed by what the workspace already knows

The failure pattern is: reasoning first, searching never (or searching as
afterthought). When the agent invents a "new" solution that already exists
in the wiki, or proposes an approach a prior session already rejected, the
root cause is always the same — it treated its own reasoning as primary.

This ordering should be mechanical, not behavioral. Skills that enforce it
(`/preflight`, `/go` H3-discover, `/www` Phase 1) are the structural fix.
When in doubt: grep the wiki first.

## Exploration vs execution — respect the operator's intent signal

The operator's language encodes their intent. When they say "ideas,"
"thought partner," "what should we change," "what can we add," "looking
for," or "help me think" — **STOP implementing.** Respond with ideas,
discussion, and recommendations. Do not write code, create files, or
commit until the operator explicitly says to implement.

The failure pattern: the operator asks an exploratory question, the agent
defaults to action bias and implements something. The operator then has
to say "I wasn't looking for implementing, I was looking for ideas" —
which wastes a turn and erodes trust.

The operator self-routes correctly: `/tp` and `/www` for exploration,
`/go` for execution. The agent's job is to match its response mode to
the operator's request mode, not to impose execution on every input.

**Rule:** exploration language → exploration response. Period.

## Session-close accounting

When asked "are we done?" / "what are we forgetting?" / "did we miss anything?" or about to claim work is complete, produce:
```
ACCOUNTING: this session's work
  Fully done:        <list>
  Partially done:    <list>
  Not started:       <list>
```
Classify from conversation context (commits, edits, decisions), NOT from `git status`. Never include other sessions' work. Ground each entry in a tool-call receipt.

For each shipped artifact: verify it has a handoff OR is discoverable from an existing handoff. Decisions need rationale documented. If missing, write a handoff before declaring done.

## Narrative-as-signal (anti-dismissal rule)

When you construct a plausible narrative for why something "can't be done" or "doesn't exist," treat that as the **signal to read documentation** — not as the answer. The moment you think "this can't be done because X": have you read the docs? Have you checked the obvious config locations?

**Separate findings from fixes:** a wrong fix does not invalidate a correct finding. Evaluate them independently.

## Replacement-before-investigation (anti-premature-recommendation rule)

Before recommending that a tool, service, or skill be **replaced** with an alternative, enumerate:

1. **What was tried** with the current tool — specific flags, parameters, invocations (not "it didn't work")
2. **What workarounds exist** that haven't been tested — check docs, GitHub issues, `[[tool-fallbacks]]`, prior sessions
3. **Whether the failure was verified** on our actual workload vs a different context (a timeout on a 90K-token prompt ≠ "the tool is broken")

If any of these is unanswered, the recommendation is premature. Label it `[PREMATURE]` and state what investigation would upgrade it to actionable.

**Anti-pattern recognition:** if you find yourself writing "X doesn't work because..." or "we should replace X with Y..." — STOP. Have you tried X's documented workarounds? Have you verified the failure is about X and not about your specific invocation? This is the [[replacement-before-investigation-pattern]]. Reference: 13+ handoffs exhibit this pattern across 6 days (2026-07-26 through 2026-08-01).

**Applies to restructuring callers too, not just replacing tools.** When an external component (CLI, API, subprocess, hook) doesn't behave as expected, reproduce the failure in isolation — run the underlying command directly — before changing the orchestration layer (threading model, timeout handling, retry logic). The root cause is almost always a config mismatch or incompatible parameter in the callee, discoverable in seconds with an isolated test. Restructuring the caller to work around an undiagnosed callee failure introduces new bugs while leaving the original problem active.

## Workspace Routing

Before acting on a package, read its local instruction files. For `yt-is`: read `P:\packages\yt-is\CLAUDE.md`, `AGENTS.md`, `HANDOFF.md`. Do not rely on parent-workspace prompt when package-local docs exist.

For experiments/benchmarks/A/B comparisons: use the `evidence-driven-experiment-loop` skill.

## Observe-Before-Propose (anti-oscillation rule)

Before proposing any structure (file layout, naming scheme, storage location, process design), **inspect the user's existing patterns first** and cite what you found. Propose only after observation. Forbidden: proposing a structure without a preceding `grep`/`list_dir`/`read_file`.

**Re-observe on rejection:** if the user rejects a proposal, STOP generating alternatives from the same observation. Re-observe with broader scope, cite what the broader search found, then re-propose.

## Code-first breadth scan before LLM fan-out

Before spawning N>5 subagents to analyze N artifacts, run a code-based breadth scan first. Reserve LLM subagents for high-density subset.

**Model tiering:** Mechanical → ccr-ornith (free local); Synthesis → parent-inherited; Cross-model → /agy, /codex, /mmx. See `[[tool-fallbacks]]`.

## Skill lifecycle maintenance

After adding/removing/renaming any skill: `python P:/.data/wiki/scripts/index_skills.py`

## Internet research policy

Follow the tool-selection rule in `~/.grok/AGENTS.md` (`minimax-search__web_search` → `web-search-prime` → built-in `web_search`). Do not re-specify locally.

Skills that need web research add only their domain-specific layer. **Staleness rubric:** library docs fresh 6-12 months; tool comparisons 6 months; patterns 1-2 years; architecture 5+ years; papers never; security 3-6 months. Run ≥2 searches: one supporting, one disconfirming.

## Review Discipline

Separate verified facts, measured metrics, inferences, and unsupported claims. Do not promote an inference into an implementation decision, live run authorization, or `ready_for_parent_review` handoff. If a new explanation is only inferred, the next allowed action is evidence gathering.
