---
name: ask
description: Universal CLI router for intelligent command discovery, prompt enhancement, and orchestration
version: "3.7"
status: stable
category: consultation
enforcement: advisory
triggers:
  - /ask
  - "help"
  - "what can you do"
aliases:
  - /ask

follow_up_offer:
  - /search
  - /orchestrator

workflow_steps:
  - name: triage
    description: Assess complexity and select cognitive approach
  - name: parse
    description: Extract intent from user request
  - name: enhance
    description: Detect ambiguity, expand vague prompts, inject domain context
  - name: explore
    description: Understand context before routing
  - name: validate
    description: Truth-check any claims with evidence-based scoring
  - name: route
    description: Match to best command via intent patterns or command discovery
  - name: execute
    description: Hand off to target command with gathered context

# First-tool coherence (v3.6): /ask is a router — its first substantive
# tool must be a discovery/search action, NOT execution (Bash/python).
# Discovery questions ("what uses X?") require code search first.
# Routing questions ("which command for X?") require reading skills.
allowed_first_tools:
  - Grep
  - Glob
  - Read
  - Task
  - WebSearch
---


# /ask - Universal CLI Router

## Purpose

Primary entry point for all CLI operations with intelligent command discovery, routing, and orchestration. Triages requests, parses intent, explores context, validates claims, and routes to the optimal command.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **No enterprise patterns**: Simple routing, not complex orchestration frameworks
- **Truthfulness required**: Validate claims before routing execution commands
- **Evidence-based routing**: Understand context before routing, don't guess

### Technical Context
- **Skill discovery**: read SKILL.md frontmatter directly under `P:/packages/.claude-marketplace/plugins/`. No registry, no index — files are the source of truth. Glob `**/SKILL.md`, Grep frontmatter (`name`, `description`, `triggers`, `aliases`), then Read the shortlisted candidate(s).
- **Triage levels**: FAST (<2s), STANDARD (<15s), CAREFUL (<60s)
- **Evidence tiers**: Tier 1 (95%), Tier 2 (85%), Tier 3 (75%), Tier 4 (50%)

### Architecture Alignment
- Universal router for marketplace plugins
- Integrates with CHS (session context), CKS (patterns)
- Links to /orchestrator, /nse, /search for related operations

## Your Workflow

1. **TRIAGE** — Assess complexity (reversibility, dependencies) → select path (FAST/STANDARD/CAREFUL)
2. **PARSE** — Extract intent, explicit commands, claims, context references
3. **ENHANCE** — Detect ambiguity, expand vague prompts, inject domain context
4. **EXPLORE** — Understand context before routing (scan files, search skills, check session history)
5. **VALIDATE** — Truth-check any claims with evidence-based scoring
6. **ROUTE** — Match to best command via intent patterns or command discovery
7. **EXECUTE** — Hand off to target command with gathered context

## Validation Rules

- **Before routing**: Understand request context, don't route blindly
- **Before accepting claims**: Apply evidence-based scoring, block if truth_score < 0.7
- **Before command discovery**: Read candidate SKILL.md frontmatter (Glob + Grep + Read), don't guess from names
- **Ambiguous requests**: Ask one clarifying question, don't fabricate route

### Prohibited Actions
- Routing without understanding request context
- Accepting unverified claims about completed work
- Summarizing this documentation instead of executing
- Fabricating command capabilities

## PHASE STRUCTURE

```
PHASE 1: TRIAGE + PARSE + ENHANCE (Generation)
    ↓ STOP: Ask clarifying question if ambiguous
PHASE 2: EXPLORE (Generation)
    ↓ STOP: Confirm context before routing
PHASE 3: VALIDATE (Validation)
    ↓ STOP: Block if truth_score < 0.7
PHASE 4: ROUTE + EXECUTE (Generation)
```

**STOP conditions separate each phase:**
- Between PHASE 1 and PHASE 2: STOP if prompt is ambiguous (ask clarifying question)
- Between PHASE 2 and PHASE 3: STOP if context insufficient (gather more context)
- Between PHASE 3 and PHASE 4: STOP if claims unverified (block routing)

## ⚡ EXECUTION DIRECTIVE

When invoked, execute these steps in order. Do not summarize this file.

```
STEP 0: TRIAGE → Assess complexity and select cognitive approach
STEP 1: PARSE  → Extract intent from user request
STEP 1.5: ENHANCE → Detect ambiguity, expand vague prompts, inject domain context
STEP 2: EXPLORE → Understand context before routing (if needed)
STEP 3: VALIDATE → Truth-check any claims (if present)
STEP 4: ROUTE  → Match to best command
STEP 5: EXECUTE → Hand off to target command
```

**Avoid:**

- Summarizing this documentation
- Routing without understanding request context
- Accepting unverified claims about completed work

**Default (no arguments):** Display available commands and offer routing assistance.


## STEP 0: RAPID TRIAGE

Assess before routing to select appropriate cognitive approach.

```
Reversibility Assessment:
├─ 1.0-1.25 (trivial: help, status, simple query) → FAST PATH
├─ 1.5-1.75 (moderate: analysis, planning, research) → STANDARD PATH
└─ 2.0 (irreversible: execution, deployment) → CAREFUL PATH

Dependency Count:
├─ 0-1 dependencies → Direct routing
├─ 2-4 dependencies → Confirm understanding first
└─ 5+ dependencies → Decompose before routing
```

| Path     | Approach                            | Budget |
| -------- | ----------------------------------- | ------ |
| FAST     | Direct route, minimal validation    | <2s    |
| STANDARD | Context exploration + routing       | <15s   |
| CAREFUL  | Full validation + user confirmation | <60s   |


## STEP 1: PARSE USER INPUT

Extract from user request:

- **Intent:** What does the user want to accomplish?
- **Explicit command:** Did they mention a specific command? (arch, rca, plan, etc.)
- **Claims:** Are they asserting completed work? (triggers truth validation)
- **Context references:** Do they reference files, projects, or prior work?


## STEP 1.5: PROMPT ENHANCEMENT

After parsing, evaluate whether the user's prompt is ambiguous, vague, or lacks sufficient context. Enhancement operates on the parsed intent — it does not change the routing decision, only improves the quality of information available for it.

### Ambiguity Detection

Check for these patterns:

| Pattern | Example | Issue |
|---------|---------|-------|
| Unclear antecedent | "fix it", "check this" | What specifically? |
| Missing specifics | "implement this", "add that" | What should be built? |
| Ambiguous improvement | "make it better", "optimize this" | Which aspects? |
| Too brief (1-2 words) | "help", "fix", "debug" | No actionable context |

### Domain Context Injection

When domain is detectable from prompt keywords or working directory, inject relevant context:

| Domain | Indicators | Context to Inject |
|--------|------------|-------------------|
| Security | auth, vulnerability, XSS, injection | Consider OWASP Top 10, input validation, output encoding |
| Testing | test, pytest, mock, fixture | TDD principles, arrange-act-assert, edge cases |
| Database | sql, migration, schema, query | Data integrity, transaction safety, indexing |
| Frontend | react, component, css, html | Component reusability, accessibility, responsive design |

### Enhancement Actions

```
IF prompt is ambiguous:
    → Ask ONE clarifying question before routing
    → "Which file/component should I focus on?"

IF prompt is too brief (1-2 words) AND no slash command:
    → Ask what they want to accomplish
    → Offer 2-3 likely interpretations

IF prompt has detectable domain:
    → Inject domain context into exploration step
    → Domain awareness carries through to routed command

IF prompt is specific and clear:
    → PASS — proceed directly to STEP 2 (no enhancement needed)
```

**Key constraint**: Enhancement asks at most ONE question. If the prompt is already clear, skip entirely. Enhancement serves routing accuracy, not conversation expansion.


## STEP 2: CONTEXT EXPLORATION

**When to explore (STANDARD or CAREFUL path):**

```
IF request references specific files or code:
    → Scan file/directory to understand structure
    → Map dependencies before proposing route

IF request asks "what [category] command would help..." or seeks command discovery:
    → Glob: P:/packages/.claude-marketplace/plugins/**/SKILL.md
    → Grep frontmatter (name, description, triggers, aliases) for intent keywords
    → Read full SKILL.md for shortlisted candidates (≤5), then route to best match

IF request is ambiguous:
    → Ask one clarifying question before routing
    → "Are you asking about X or Y?"

IF request builds on prior work:
    → Check session context for relevant history
    → Carry forward established context
```

**Skip exploration when:**

- Request is explicit command invocation
- Request is simple help/status query
- FAST path triage


## STEP 3: TRUTH VALIDATION

Execute when user request contains development claims. Block routing if truth_score < 0.7.

_See `references/truth-validation.md` for claim detection patterns, evidence-based scoring formula, and blocking logic._


## STEP 4: ROUTING DECISION

### 4.1 Explicit Command Detection

```
IF user mentions specific command:
    → Route directly to that command
    → Pass original request as context
```

### 4.2 Intent-Based Routing

_See `references/intent-routing-table.md` for the complete intent-to-command mapping, command categories, and discovery commands._

### 4.3 Command Discovery Integration

Commands are discovered by reading SKILL.md frontmatter directly under the marketplace root (`P:/packages/.claude-marketplace/plugins/`). There is no registry — Glob, Grep, Read.

### 4.4 Ambiguous Request Handling

_See `references/integration-notes.md` for ambiguous request handling and fallback behavior._


## STEP 5: EXECUTE HANDOFF

```
1. Confirm selected route (for STANDARD/CAREFUL paths)
2. Pass original user request to target command
3. Include context gathered during exploration
4. Include any truth validation notes
5. Transfer session context if applicable
6. If authorized and bounded → complete directly (see Bounded Action Continuation below)
```

### Bounded Action Continuation

When all four of the following are true, complete the bounded action directly
instead of stopping to re-ask the user:

1. The user has clearly authorized the goal (explicit request, not inferred).
2. The next action is bounded — one file edit, one grep, one test run, one
   small script execution, no blast radius beyond the stated scope.
3. The action is reversible or trivially correctable (git-edit, not git-reset).
4. The action is directly implied — there is no reasonable alternative path that
   would change the user's intent.

Do **not** continue when: the action is destructive (delete, drop, rm -rf),
unclear (two valid interpretations), outside stated scope, or when the user's
prior message signals they want a plan or report rather than execution.

The failure pattern this prevents: "say the word" deferral after bounded work
is already clearly requested — the user has authorized, the action is small and
reversible, and asking again wastes a turn.


## QUICK REFERENCE

### Common Routes

| User Says                            | Routes To          |
| ------------------------------------ | ------------------ |
| "help", "what can you do"            | Help display       |
| "plan project", "break down task"    | `/breakdown`            |
| "should I extract this service"      | `/adf`             |
| "architecture design", "how to design" | `/design`            |
| "why is this failing"                | `/rca` or `/debug` |
| "research X", "learn about Y"        | `/research`        |
| "document this code", "ingest docs"  | `/doc`             |
| "verify my claims", "did I actually" | `/truth`           |
| "analyze code quality"               | `/analyze`         |
| "what did we discuss about X"        | `/search`             |
| "list available commands"            | Command discovery  |
| "discover patterns in codebase"      | `/discover`        |

### Routing Principles

1. **Understand before routing** — Context exploration prevents misroutes
2. **Verify before trusting** — Claims about work require evidence
3. **Ask when uncertain** — One clarifying question beats wrong routing
4. **Preserve context** — Carry forward relevant session state


## Evidence-First Principles

### E1 — Evidence before claims
Before claiming code is absent, unchanged, or non-existent — search the codebase and verify with tools first. Claims of absence are only valid after confirmed Read/Grep/git failures.

### E4 — Investigate before asking
Do NOT answer without reading relevant source files first. Do not ask the user for information you can obtain yourself via Read, Grep, Bash, git, or available MCP tools.

### E5 — Anti-lazy escape hatch
Prohibited:
- "I assume", "I think", "probably" without tool verification
- Claiming something doesn't exist without confirmed tool failure
- Skipping evidence gathering because the answer seems obvious

## Abstraction Audit Manifest

Before running a Deeper Abstraction Check or claiming "full coverage" in any
audit, first run the deterministic manifest generator:

```
python cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py \
  --repo-root <marketplace-root>
```

The script writes `.artifacts/abstraction-audit/<timestamp>/manifest.json` and
`manifest.md` with:
- whole-repo file inventory (skills, commands, references, hooks, tests, evals, registries)
- 31-term search hits by file
- risk-flag heuristics (false full-coverage, runtime/advisory confusion, permission deferral, wiki auto-write, telemetry swallowing, missing eval terms)
- recommended read set ranked by term density

**Use the manifest as evidence, not as the conclusion.** The LLM must inspect
the recommended read set before making high-confidence cross-skill claims.
If the script was not run, the audit must say why and classify coverage as
`sampled` or `targeted` — never `whole_repo_static`.

Coverage authority: `whole_repo_static` only when the manifest generator ran
from the repo root. Otherwise: `sampled` or `targeted`.

## Deeper Abstraction Check

`/ask` owns cross-skill/plugin inspection — when discovery surfaces a **local
concept** (a rule, field, classification, or contract that lives in one skill
or command), answer this question before closing:

> **What deeper abstraction does this local concept imply?**

The discipline is to look *past* the local instance to the reusable class. Do
**not** ask "where should we paste this rule?" — that question anchors on
copying prose. Ask "what reusable abstraction or ownership model does this rule
reveal?" — that question surfaces whether the concept belongs in a shared
reference, a pointer pattern, a runtime hook, or correctly stays local.

Emit one Deeper Abstraction Check artifact when a local concept is non-trivial
(recurring shape, multi-command relevance, or a fixed vocabulary that could
drift). Fields:

| Field | Required | Definition |
|---|---|---|
| `local_concept` | yes | The rule/field/classification as it exists today, with its file:line. |
| `deeper_abstraction` | yes | One sentence: the reusable abstraction or ownership model this concept implies. |
| `affected_surfaces` | yes | Commands/skills/hooks that already have (or would need) the same shape. Cite file:line. |
| `current_owner` | yes | The command/skill that owns the concept today. |
| `disposition` | yes | One of: `should_be_shared_reference`, `pointer_only`, `runtime_hook`, `test`, `backlog`, `do_nothing`. |
| `evidence` | yes | file:line citations proving the concept is local and proving the affected surfaces. **No vibes.** |
| `coverage_authority` | yes | One of: `whole_repo_static` (file enumeration), `targeted` (named-surface grep/read), `sampled` (subset of named surface), `runtime_surface` (live behavior), `live_behavior` (runtime probe). Required on any audit/claim that would otherwise be tempted to say "full coverage." |
| `activation_truth_layer` | yes | One of: `source_changed`, `cache_rebuilt`, `plugin_loaded`, `command_resolves`, `behavior_observed`. Required on any claim about a skill/plugin/process being "live" or "active." |
| `bounded_actions_completed_or_deferred` | yes | List of bounded actions that the audit recommended and whether they were completed in this session or deferred to a tracker task. Required on any audit-style report. |
| `recommended_action` | yes | The smallest change that moves the concept toward the chosen disposition. |

### Disposition guide

- `should_be_shared_reference` — the concept is a compliance vocabulary emitted
  by multiple commands → make it a report contract
  (see `debrief/references/report-contracts.md`).
- `pointer_only` — the abstraction already has a canonical home; other surfaces
  need a one-line pointer, not a copy.
- `runtime_hook` — the concept is a behavior that prose cannot enforce → wire a
  hook/gate, do not just document it.
- `test` — the concept is an invariant a static test can pin → add a pytest test.
- `backlog` — real abstraction, not worth moving now → create a tracker task.
- `do_nothing` — the concept is genuinely local with no deeper class → say so
  explicitly so the next reader does not re-litigate.

### Coverage Authority

When the Deeper Abstraction Check (or any audit/claim) refers to the breadth of
its evidence, name the authority. Five values, in increasing strength:

| Authority | Means |
|---|---|
| `sampled` | A subset of the named surface was inspected; results may not generalize. |
| `targeted` | Named surfaces (specific files / skills / hooks) were grep'd or read; non-named surfaces were not. |
| `whole_repo_static` | The marketplace tree was enumerated (Glob) and every named file was inspected. |
| `runtime_surface` | A live process or hook dispatch path was exercised; behavior is observed, not inferred. |
| `live_behavior` | A real user path (slash command → orchestrator → output) was driven end-to-end and observed. |

Prohibited: "full coverage" without an authority label. Prohibited: "the codebase"
without a Glob result. Prohibited: "every skill has X" without an enumerated
check. If the authority is `sampled` or `targeted`, say so plainly so the
reader does not over-trust the conclusion.

### Activation Truth Model

A claim about a skill, plugin, hook, or process being "live" or "active" must
identify which layer is actually proven. The five layers, in increasing
strength:

| Layer | Proves |
|---|---|
| `source_changed` | A file was edited in source. Nothing more. |
| `cache_rebuilt` | The version-keyed plugin cache was rebuilt from the new source. |
| `plugin_loaded` | The plugin is loaded into the running Claude Code session. |
| `command_resolves` | The slash command resolves to a real implementation (`claude plugin list` / dispatcher output). |
| `behavior_observed` | The user path (slash command → orchestrator → output) was driven end-to-end and the expected behavior was observed. |

Prohibited: claiming "wired" or "live" from a source edit alone. Prohibited:
claiming "shipped" from a cache rebuild without confirming plugin load. Each
layer requires its own evidence; the CEC `claim_type` enum's
`source_changed` / `plugin_bumped` / `cache_rebuilt` / `runtime_behavior_changed`
/ `user_visible_behavior_verified` rows map onto this ladder directly.

This check is **prompt-advisory**. `/ask` emits the artifact; nothing at
runtime forces it. If a discovered abstraction should become a runtime gate,
say so in `disposition: runtime_hook` and route the wiring to the command that
owns that surface.

## ERROR HANDLING

_See `references/integration-notes.md` for error handling, session context, command registry, and workflow integration details._
