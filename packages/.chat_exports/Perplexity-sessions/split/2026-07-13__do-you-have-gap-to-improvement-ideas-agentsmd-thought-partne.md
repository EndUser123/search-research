---
title: "do you have gap to improvement ideas?# AGENTS.md

## Thought-Partner Operating Mode

When the user asks for a 'thought p"
date: "2026-07-13"
mode: "COPILOT"
uuid: "e3cda06c-fdfc-49e9-a1ce-e70a33f30df3"
entry_count: 1
---

## Human

do you have gap to improvement ideas?# AGENTS.md

## Thought-Partner Operating Mode

When the user asks for a "thought partner," "brainstorm," "what could improve," "what are we missing," "how can we add value," "what would make this stronger," "sanity check," or similar semantic request, treat it as broad, goal-oriented collaboration rather than a minimal critique.

- Inspect real artifacts and verify important claims when available.
- Review the current approach adversarially for correctness, security, performance, workflow, migration, and operational risks.
- Identify workflow and process improvements, simpler or more durable approaches, and new value opportunities.
- Anticipate future needs and surface adjacent ideas that could materially move the user closer to the goal.
- Separate verified facts, inferences, hypotheses, and ideas.
- Prioritize recommendations by impact, effort, risk, and confidence.
- Explicitly identify shortcuts taken, omissions, untested paths, and intentionally untouched areas.
- End with concrete next actions and state what would increase confidence or value next.

This applies to all agentic tools and workflows operating in `P:\`, including Codex, Claude Code, PI, OpenCode, and related orchestrators.

## Director + AI Coder Review Protocol

When one human is directing work and an AI agent is designing or implementing,
the director and coder must review the system boundary before optimizing the
visible behavior. A passing happy-path test is not enough when the work involves
brokers, multiplexers, shared state, adapters, orchestration, authentication,
process ownership, or client compatibility.

These are general review lenses, not an MCP-only checklist. Apply them to
adapters, wrappers, migrations, queues, caches, plugins, APIs, agent workflows,
and other systems where one component stands between an actor and a resource.

### Generalized review lenses

- **Authority and identity:** Who writes, carries, reads, trusts, authenticates,
and owns each important identity or decision? What happens on collision,
impersonation, reconnect, restart, or stale state?
- **Semantic preservation:** Which user-visible or protocol-visible meanings must
survive the boundary? Check capabilities, context, ordering, correlation,
notifications, cancellation, errors, and lifecycle—not only the primary
request/response.
- **Isolation and scope:** What is intentionally shared, and what must remain
isolated across users, sessions, projects, credentials, tenants, versions, or
failure domains? Proving resource reuse does not prove safe isolation.
- **Lifecycle and failure ownership:** Who starts, supervises, retries, drains,
stops, cleans up, and reports failure for every resource? Test races, partial
failure, recovery, timeout, shutdown, and orphan/stale state.
- **Configuration and source of truth:** What identifies a configuration, which
artifact is authoritative, how does precedence work, and what happens when
two actors provide different configuration or versions?
- **Evidence and reversibility:** Can each claim be reproduced and falsified?
Are artifacts immutable or revision-pinned, runs uniquely identified, timing
windows explicit, and changes backed up and reversible?

### What to inspect before proposing a solution

- Map the authority path end to end: writer, serialized field, transport,
reader, registry/state key, owner, collision behavior, reconnect behavior,
and failure direction.
- Identify the source of identity: process, session, client, workspace, config,
credential, and version. Ask whether each identity is generated, supplied,
trusted, authenticated, persisted, or accidentally reused.
- Enumerate the protocol surface, not just the common request path. Include
initialization, notifications, request IDs, cancellation, progress,
subscriptions, roots, server-to-client requests, shutdown, and reconnect.
- Map configuration identity separately from filesystem path identity. Test what
happens when two versions or two contents use the same path or endpoint.
- Treat local IPC as a security boundary. Inspect endpoint naming, ACLs,
impersonation/authentication, stale endpoint recovery, and wrong-owner or
wrong-broker behavior.
- Separate process isolation, routing isolation, session-state isolation,
credential isolation, and client-config isolation. Proving one does not prove
the others.

### Required design-review questions

For any boundary, shared-resource, orchestration, or multi-client design, answer
these before implementation:

1. What authority and identity paths cross the boundary?
2. What semantics are preserved, transformed, unsupported, or silently lost?
3. What is shared, what is isolated, and what is the narrowest safe scope?
4. What happens when two actors use identical identifiers or conflicting
context/configuration concurrently?
5. What happens when each lifecycle stage or dependency fails partially?
6. Which artifact is the source of truth, and how are version/collision cases
resolved?
7. How do we prove ownership, reproducibility, reversibility, and falsifiability?

### Required plan gates

- Add a source/authority audit before writing the test harness.
- Keep the reviewed candidate immutable; use a worktree or external harness
for validation changes and record both upstream and validation revisions.
- Make run IDs, process ownership, timing windows, and evidence schemas explicit.
- Use a real harmless implementation after fixtures, but choose it according to
the safety claim: stateless for shared-mode proof; stateful/filesystem/browser
examples for per-session proof.
- Test races, duplicate startup, same-ID concurrency, reconnect, death,
cleanup, stale endpoints, and configuration collisions—not only success.
- Define separate authorization levels for protocol viability, limited pilot,
multi-client use, and production. Do not let a passing repository test suite
silently become an adoption decision.
- Require an explicit human checkpoint before touching production configuration.
- Maintain a compact claim ledger: `Claim | Type | Evidence | Falsifier |
Action allowed`. Inferences and hypotheses authorize evidence gathering, not
implementation or live rollout.

### How to handle improvement opportunities

Reviews should surface durable opportunities such as capability-aware policies,
canonical configuration generation, machine-readable status, server contracts,
resource governance, and reusable conformance tests. Tag each as `required now`,
`required before pilot`, `required before production`, or `later opportunity`.
Do not let valuable future architecture expand the first safe validation branch
unless it changes the current decision or prevents a material false pass.

## Search Topology (read before any existence/absence claim)

`P:\` is a multi-root workspace. Code for one subsystem is split across these
roots - a search scoped to only one of them proves nothing:

| Root | What lives there |
|------|------------------|
| `P:\.claude\hooks\` | User-level hooks (dispatched from `~/.claude/settings.json`) |
| `P:\.claude\scripts\` | Maintenance/audit scripts (e.g. `hooks_audit.py`) |
| `P:\packages\.claude-marketplace\plugins\<name>\` | Plugin SOURCE (canonical). Plugin hooks live in per-plugin `hooks/` or `scripts/` dirs and dispatch via the plugin's `__lib/router.py` |
| `~\.claude\plugins\cache\` | Version-keyed plugin CACHE - generated, never edit; may lag source |
| `P:\.claude\worktrees\`, `P:\worktrees\`, `P: mp\` | Stale copies/experiments - exclude from truth claims |

**Absence rule:** never claim a file, hook, or module "does not exist" until you
have searched BOTH live roots. Canonical command:

```
rg --files -g "*<name>*" P:/.claude/hooks P:/.claude/scripts P:/packages/.claude-marketplace/plugins
```

(`rg` respects .gitignore, so node_modules/.venv noise is excluded automatically.)
For hook ground truth, prefer running the audit over searching by hand:
`python P:/.claude/scripts/hooks_audit.py --packages P:/packages/.claude-marketplace/plugins`

If a spec names a file you can't find in one root, check the other root before
concluding the spec is wrong.

## Workspace Routing

This `P:\` workspace contains multiple packages. Before acting on a package, read
that package's local instruction files and treat them as the governing guidance
for work under that path.

For `yt-is` work under `P:\packages\yt-is`, read:

- `P:\packages\yt-is\CLAUDE.md`
- `P:\packages\yt-is\AGENTS.md`
- `P:\packages\yt-is\HANDOFF.md`

Do not rely on a parent-workspace prompt or chat summary when package-local
instructions, handoffs, or operation docs exist.

For experiments, benchmarks, performance optimization, A/B comparisons,
live-run decisions, or fresh-agent experiment handoffs, use the installed
`evidence-driven-experiment-loop` skill and validate its state before action.

## Review Discipline

For non-trivial analysis, proposals, mechanism investigations, benchmark
interpretations, or decision packets, separate verified facts, measured metrics,
inferences, hypotheses, historical context, and unsupported claims.

Do not promote an inference or hypothesis into an implementation decision, live
run authorization, or `ready_for_parent_review` handoff. If a new explanation is
only inferred, the next allowed action is evidence gathering.

## Web Search Routing

Multiple search tools are configured (see `~/.config/opencode/opencode.json`).
**Never default to a single tool.** Pick by epistemic need, then by query type.
Full rules: see `~/.config/opencode/AGENTS.md` (global) — local additions below.

### NotebookLM — both CLIs and skills coexist

Two packages are installed intentionally; both are kept on PATH and both skills
fire on the same keywords. This is **not a conflict** — pick by intent:

| Intent | Use |
|---|---|
| Default for any NotebookLM operation (notebooks, sources, artifacts, research, chat) | **`notebooklm` CLI (teng-lin)** via Bash, or `notebooklm-py` skill at `~/.agents/skills/notebooklm/` / `P:\.agents\skills\notebooklm\SKILL.md` |
| One-off alternative invocation, or to cross-check behavior | `nlm` CLI (jacob-bd) — installed, but not the default |
| When user explicitly says `nlm` | `nlm` CLI + `nlm-skill` at `~/.agents/skills\nlm-skill/` |

Reason for defaulting to teng-lin: master-token auth (works headless / CI),
broader interface surface (Python API + CLI + MCP + REST), larger community.
jacob-bd is kept as a fallback in case teng-lin breaks for a specific workflow.

### Perplexity — opt-in only

**Never auto-select the Perplexity MCP or `pwm` CLI** unless the user explicitly
asks for "perplexity", "pplx", or "pwm". When the user does ask, prefer the
`pwm` CLI (richer output, JSON-friendly) over the MCP tool unless the workflow
specifically needs MCP context.

### Default for an unclassified query

`mmx search query` (fast, free, neutral). If it returns empty or insufficient,
escalate: Exa (semantic) → Brave (broad) → Tavily (deep) → DDG (fallback) →
`web-search-prime` (recency).

### Parallel multi-backend queries

For research questions requiring coverage + triangulation (e.g., "what's the
current state of X", "compare approaches to Y"):

1. **Delegate each backend to a subagent** (Task tool with `subagent_type:
general` or `explore`). The subagent runs the search, dedupes results, and
returns a compact summary (titles + URLs + 1-line relevance per hit). This
protects the main agent's context window from raw search payloads.
2. **Run at least two backends in parallel** when the question is contested,
time-sensitive, or has high variance across sources. mmx + Exa is the
default pair for "what's true about X"; Brave + mmx for "what's happening
with X"; Tavily + Exa for "deep dive on X".
3. **For different models in parallel** — the Task tool's subagent_type is
hardcoded (general/explore/external-writer/external-readonly) and custom
subagents with model overrides can't be dispatched (issue #29616).
**Workaround:** use `opencode run` with `XDG_DATA_HOME` isolation:
```
XDG_DATA_HOME=/tmp/oc-<uuid> opencode run --model opencode/deepseek-v4-flash-free "<task>"
```
`XDG_DATA_HOME` is the real DB isolation lever (binary-verified: 8
occurrences in opencode.exe). `OPENCODE_DB` is NOT a real env var (0
occurrences) — do not use it. Note: even XDG isolation is not fully
reliable (issue #33321); prefer the in-process Task tool when possible.
Free models available: `opencode/deepseek-v4-flash-free`,
`opencode/nemotron-3-ultra-free`, `opencode/hy3-free`,
`opencode/mimo-v2.5-free`, `opencode/north-mini-code-free`.
4. **Synthesize in main context** — don't paste raw results into your reply.
Cite the source URL inline so the user can verify.
5. **Never auto-select Perplexity in parallel queries** — same opt-in rule.

## Boundaries

- Do not edit `~/.claude/CLAUDE.md` or any file under `~/.claude/`. That
belongs to Claude Code. For global opencode rules, use
`~/.config/opencode/AGENTS.md` instead.

## Temp files

- Bash `/tmp` resolves to `%LOCALAPPDATA%\Temp`, NOT `P:\tmp`.
- When giving the user a file path, always use the real Windows path and
verify it exists with `ls` before stating it.
- Put temp files the user needs to access in `P:\tmp\` — create the
directory if it doesn't exist.

## Assistant

You already have a strong gap-to-opportunity discipline baked into this AGENTS.md; the main improvement opportunities are around making it more operational, more measurable, and easier for agents (and you) to actually run gap analyses as a repeatable protocol rather than as prose guidance.[1][2]

Below I’ll treat your AGENTS.md itself as the artifact and propose “gap-to-improvement” ideas along four axes: structure, operationalization, measurement, and adjacent value.

***

## Quick read: core suggestions

- Turn the Thought-Partner + Director/AI Coder sections into a **concrete gap-analysis protocol** with explicit inputs/outputs and run IDs, instead of purely narrative guidance.[2][1]
- Add a **minimal “agent checklist”** at the top with 5–8 questions the agent must answer before proposing changes, mirroring your review lenses.[1]
- Introduce a **claim ledger template** (you already name it) and standardize it as a table + file path so every non‑trivial review produces machine‑readable evidence.[2][1]
- Define a **lightweight gap-to-opportunity framework** for P:\ work: current state → desired state → gap → opportunities → action plan, with tags (`required now`, `before pilot`, etc.) that agents must assign.[3][1]
- Add pointers from AGENTS.md to small, focused protocol files (e.g., `REVIEW_PROTOCOL.md`, `SEARCH_TOPOLOGY.md`) so agents aren’t scrolling a monolith and can follow progressive disclosure.[4][5]

Confidence: high that these will make the file more effective for agents like me; medium that they perfectly align with your internal mental models (you may want to tweak naming).

***

## Structure: make AGENTS.md behave like a framework

Most “how to write a great AGENTS.md” guidance suggests keeping it minimal and using **progressive disclosure**: the root file says what the project is, how to build it, and where to go for deeper protocols. Your AGENTS.md currently functions as a rich meta‑protocol for all agents in P:\, which is powerful but cognitively dense.[5][4]

Improvement ideas:

- **Add a one-sentence scope description at the top.**  
  Example: “This AGENTS.md defines cross‑package review and gap-analysis protocols for AI agents operating in P:\.” This aligns with best practice for agents.md files and orients new agents quickly.[4][5]

- **Segment into explicit sections with links to sub-docs.**  
  Right now, “Thought-Partner Operating Mode”, “Director + AI Coder Review Protocol”, “Search Topology”, and “Workspace Routing” all live inline. You could extract each into its own markdown file (`THOUGHT_PARTNER.md`, `REVIEW_PROTOCOL.md`, `SEARCH_TOPOLOGY.md`, `WORKSPACE_ROUTING.md`) and keep AGENTS.md as an index of protocols.[5][4]

- **Introduce a standard “Protocol header” pattern.**  
  For each protocol file, define: Purpose, Scope, Inputs, Outputs, When to use, Not for. This is borrowed from gap analysis and process frameworks that emphasize scope and objectives first.[6][1]

Impact: medium/high (reduces cognitive load, easier for agents to route themselves correctly). Effort: low/medium (mostly refactoring text).

***

## Operationalization: turn guidance into a callable gap-analysis protocol

You already specify that for non-trivial work, agents must separate verified facts, inferences, hypotheses, metrics, etc., and that gap opportunities should be tagged (`required now`, `before pilot`, etc.). That’s essentially a **gap-analysis framework**: current state, desired state, gap, and ideas to close it.[3][1]

Concrete improvements:

- **Define a canonical “Gap-to-Opportunity Review” protocol.**  
  Base it on standard gap analysis stages (current state, future state, gap, improvement plan). For your context, a simple template could be:[3][1]

  1. Current state: what’s actually implemented / configured (with citations).  
  2. Desired state: what the spec or user ultimately wants (clarified, with assumptions).  
  3. Gaps: specific discrepancies in behavior, coverage, authority, isolation, etc.  
  4. Opportunities: ideas tagged by `required now`, `before pilot`, `before production`, `later opportunity`.  
  5. Action plan: 1–3 concrete next steps + evidence to gather.

  This gives agents a structured way to answer your “do you have gap to improvement ideas?” question without free‑form dumping.[1][2]

- **Make the “Required plan gates” a checklist with explicit outputs.**  
  Right now they read as narrative bullet points. Turn them into a required checklist the agent must satisfy before recommending implementation or rollout, e.g.:

  - Source/authority audit done? Artifact path: `P:\tmp\audit-<run-id>.md`.  
  - Candidate kept immutable? If not, explain deviation.  
  - Run ID assigned, timing window recorded, evidence file created?  
  - Races and collisions tested, not just success? List tests.  

  This mirrors how formal gap analysis frameworks insist on definable scopes, data sources, and documented action plans.[6][1]

- **Standardize the Claim Ledger format.**  
  You already specify `Claim | Type | Evidence | Falsifier | Action allowed`. Turn that into a markdown table schema that agents must populate for any non-trivial review.[1]

  Example table:

  | Claim | Type | Evidence | Falsifier | Action allowed |
  |-------|------|----------|-----------|----------------|
  | Hooks audit matches spec | Verified fact | `hooks_audit.py` run log | Re-run audit on new commit | Safe to refactor hook naming |

  This aligns with “evidence and reversibility” best practice in strategic gap analysis.[2][1]

Impact: high (turns your philosophy into executable patterns). Effort: medium (template design, minor refactor).

***

## Measurement: add metrics and run IDs to make reviews reproducible

Your instructions already mention “run IDs, process ownership, timing windows, and evidence schemas explicit.” That’s very close to what modern gap-analysis frameworks suggest: always tie analysis to a specific point in time and a set of data sources.[6][1]

Improvements:

- **Define a standard Run ID scheme and file naming convention.**  
  For example: `gap-review-<package>-<YYYYMMDD>-<HHMM>-<agent>.md`. Agents must include it at the top of any review output and use it in evidence file paths. This mirrors “runs uniquely identified, timing windows explicit” guidance in your text and in evidence‑driven frameworks.[1]

- **Add a minimal metrics section per review.**  
  Even if qualitative, ask agents to estimate:

  - Impact: low/medium/high (on safety, correctness, migration risk).  
  - Effort: low/medium/high (implementation cost).  
  - Confidence: low/medium/high (in the claim).  

  This is consistent with gap-analysis best practice (prioritize gaps by impact and effort).[6][1]

- **Introduce a simple “gap severity” taxonomy.**  
  For example: `Blocking`, `Degrades correctness`, `Degrades observability`, `Migration risk`, `Perf risk`, `Minor opportunity`. That helps classify findings and ties them into your `required now` vs `later opportunity` tagging.[1]

Impact: medium/high, especially for multi-agent comparison and historical review. Effort: low.

***

## Adjacent value: align AGENTS.md with external AGENTS.md best practices

There’s a growing body of guidance on how to make AGENTS.md genuinely useful for coding agents (GitHub Copilot, etc.), emphasizing minimalism, clarity, and progressive disclosure. Some of your content—especially around search routing and workspace roots—is exactly what those guides recommend including, but a lot of the meta-review discipline might be better as linked protocols.[4][5]

Potential improvements:

- **Separate “agent operational constraints” from “epistemic review philosophy.”**  
  Keep things like root directories, search commands, “don’t touch ~/.claude” and tool routing in the root AGENTS.md (these are universally relevant to every task). Move review philosophy (authority paths, semantic preservation, lifecycle ownership) into `REVIEW_PROTOCOL.md` that AGENTS.md links to.[5][4]

- **Add micro-examples for each generalized review lens.**  
  External best practices for AI code review suggest that guidance is much more effective when paired with small, concrete examples. For each lens (e.g., “Authority and identity” or “Isolation and scope”), include a 2–3 line example of what a good analysis looks like:[7][8]

  - “Authority and identity – example: For MCP server X, identity is the MCP config file path, workspace, and auth token; on reconnect, stale tokens are invalidated by Y; collisions handled via Z.”

  This makes your lenses actionable without expanding their conceptual scope.

- **Flag this AGENTS.md explicitly as cross-package and not package-local.**  
  Aligns with your “Workspace Routing” section; AGENTS.md should say: “For package-local instructions, read <package>/AGENTS.md; this file covers cross-package behavior in P:\ only.” This mirrors how multi-root workspaces are documented in other systems.[5]

Impact: medium (makes it easier for external agents, or unfamiliar ones, to snap to the right mental model). Effort: low.

***

## Explicit separation of FACT, CONSENSUS, SPECULATION

You asked for explicit distinctions; here’s a compact mapping applied to what I’m proposing:

- FACT (high confidence, externally grounded):  
  - Gap analysis is a standard framework with stages of current state, future state, gap, and improvement/action plan.[3][6][1]
  - Best-practice AGENTS.md guidance favors minimal core instructions and progressive disclosure into specialized docs.[4][5]

- CONSENSUS (aligned with industry patterns, but not fully formalized):  
  - Making AI review output structured (claim ledgers, run IDs, metrics) improves reproducibility and safety in code review workflows.[8][7]
  - Tagging opportunities by phase (`required now`, `before pilot`, etc.) is common in strategic planning and gap-analysis frameworks.[6][1]

- SPECULATION (my synthesis, medium confidence):  
  - Converting your existing review bullets into explicit, machine-readable protocols and checklists will significantly improve how AI agents operating in P:\ behave (fewer “fast but shallow” responses, more reproducible audits).  
  - Splitting AGENTS.md into an index plus 3–5 protocol files will reduce misrouting and instruction overload enough to be worth the refactor.

Key assumptions:

- You want agents to not just think “gap-to-opportunity” but to **produce artifacts** (tables, files, claim ledgers) you can inspect and diff over time.  
- You maintain P:\ over the long term, so structural improvements to AGENTS.md pay off across many runs.

***

## Concrete next steps

If you want to turn “gap to improvement ideas” into a repeatable, inspectable behavior for agents, I’d suggest:

1. **Add a short “Gap-to-Opportunity Review” section near the top of AGENTS.md.**  
   - Define the 5 stages (current state, desired state, gaps, opportunities, action plan).  
   - Require a markdown claim ledger table for non-trivial reviews.  

2. **Create `P:\AGENTS_INDEX.md` and move AGENTS.md into a protocol file (e.g., `P:\GLOBAL_AGENTS.md`).**  
   - Let `AGENTS_INDEX.md` simply link to `GLOBAL_AGENTS.md`, `REVIEW_PROTOCOL.md`, `SEARCH_TOPOLOGY.md`, etc.  

3. **Draft one concrete protocol file: `P:\REVIEW_PROTOCOL.md`.**  
   - Encode the generalized review lenses as a checklist with example questions and required outputs (e.g., “Authority path map”, “Lifecycle failure matrix”).  

4. **Define a run ID and evidence file convention in this global AGENTS.md.**  
   - For example, “All non-trivial reviews must produce `P:\tmp\review-<run-id>.md` with a claim ledger and metrics.”  

What would increase my confidence and make advice sharper next is seeing one real “gap review” artifact you’ve produced (e.g., a prior review of hooks or MCP routing) so we can tune the protocol to match how you actually like to read and use these outputs.

What kind of artifact or review do you most want agents to produce when you ask for “gap to improvement ideas”—a concise ledger, a narrative packet, or something closer to a checklist?  
