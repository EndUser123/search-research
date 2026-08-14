---
title: "How do repos solve this problem?"
date: "2026-03-13"
mode: "COPILOT"
uuid: "b5bdc8a2-eb24-4ea7-9686-be629656da7a"
entry_count: 5
---

## Human

How do repos solve this problem?

## Assistant

Repos solve this by making the repo itself the single, *authoritative*, shared source of truth, and pushing everything else (skills, hooks, state, policies) into deterministic, file‑based mechanisms instead of ephemeral model context.[1]

## Core idea

A repo-centric design fixes your enforcement issues by:

- Encoding skills, workflows, and policies as versioned files in the repo (SKILL.md, CLAUDE.md, .clauderules, hooks config) rather than as “remembered rules” in the conversation.[1]
- Storing *runtime* enforcement state per terminal under a repo-local directory (for example `.claudetenantsterminal-id...`), so each terminal is a tenant over the same repo with isolated logs and state.[1]
- Having hooks recompute decisions *only* from current repo files and the terminal’s own state files on each event, with no cross-turn in‑memory flags.[1]

## How repos address your specific problems

1. **Skill-first enforcement without deadlocks**

   - The repo contains hook scripts (PreToolUse, Stop) that inspect only the current user message and current tool list to enforce “skill-first” per turn, instead of relying on fragile pending-intent files that accumulate across turns.[1]
   - These scripts live in the repo (for example under `.claudehooks`) and are versioned and testable like any other code, so you can evolve the enforcement logic safely.[1]

2. **Multi-terminal isolation**

   - The repo includes a tenancy convention: each terminal gets an ID (from your existing terminal detection) and writes all enforcement state under `.claudetenantsterminal-id` (state.json, session.log, per-skill workflow logs).[1]
   - Because those paths are scoped by terminal ID, concurrent terminals over the same repo never clobber each other’s enforcement state, even though they share source files and SKILL.md.[1]

3. **Stale-data immunity**

   - Hooks always reload current SKILL.md, hooks config, and the terminal’s workflow log from disk for each event; any caching is tied to mtime and can be thrown away at any time.[1]
   - If you change a skill’s workflowsteps in the repo, the next hook call picks up that new definition immediately, and step completion is re-evaluated against the updated config.[1]

4. **Workflowstep enforcement and gap-filling**

   - Each execution skill’s SKILL.md in the repo defines workflowsteps with ids, dependson, kind (execution, verification, summary), and expected tools.[1]
   - Per-skill workflow logs in the repo (per terminal) track which steps are done with evidence; Stop hooks use these logs to identify missing steps and ask the model to fill gaps, instead of rerunning the entire skill.[1]

5. **Separation of soft vs hard enforcement**

   - The repo distinguishes soft guidance (CLAUDE.md, .clauderules prose norms) from hard enforcement (command-type hooks, allowed-tools, disable-model-invocation, workflow logs).[1]
   - This avoids overloading SKILL.md and CLAUDE.md with “please do X” text and instead uses deterministic logic wired from files the hooks can parse.[1]

6. **Observability and regression detection**

   - Because enforcement decisions are logged to per-terminal JSONL files in the repo (`session.log`, `errors.log`), you can run verify-like scripts over the repo to compute metrics, detect false positives/negatives, and see behavior shifts when Claude or the platform changes.[1]
   - Those analysis scripts also live in the repo and can be versioned, tested, and refined as you iterate on the enforcement architecture.[1]

## Why a repo is the right boundary

- It is the only thing all terminals share reliably and durably, so it is the correct place for policies, skills, and enforcement code to live.[1]
- It gives you atomicity and determinism via file writes and git history, which you do not get from ephemeral context or per-session “remembered” rules.[1]

Given this architecture, the core remaining choice is: do you want enforcement behavior (e.g., which skills get step-level gating, which steps are critical vs advisory) to be controlled entirely via SKILL.md and hooks config in the repo, or do you still want some of that logic to live in global, non-repo configuration?

## Human

It has to be both.  The Skill() is global, the enforcement of the workflow_steps can be local.

## Assistant

Right, so treat it as a two-layer contract:

1. **Global: “Skill() happened and this is the active workflow.”**  
   - The Skill tool and SKILL.md definition remain global, repo-level truth: name, workflow_steps list, ids, dependson, kind, optional, etc.[1]
   - Global hooks (UserPromptSubmit / PreToolUse / PostToolUse / Stop) can enforce only very simple invariants that are safe across all terminals, for example: “If user starts with `/code`, the first tool this turn must be `Skill(code)`.”[1]
   - Those hooks read SKILL.md and maybe a minimal global/breadcrumb record to know which skill run is “active”, but they do not try to enforce every step; they just guarantee the global preconditions and basic shape of the run.[1]

2. **Local: “How strictly do we enforce this skill’s workflow_steps here?”**  
   - Per-terminal breadcrumb/tenant state (under `.claudestate` or `.claudetenants/terminal-id`) tracks step status and evidence for each skill run: `step_id -> {status, evidence, last_updated}`.[1]
   - Local enforcement of workflow_steps is completely computed from: current SKILL.md + that terminal’s workflow log; no cross-terminal coupling.[1]
   - You get to choose per skill how “hard” that local enforcement is:  
     - Some skills: warn-only Stop-hook behavior when verification steps are pending.  
     - Others: block-on-missing-critical-step before allowing completion.  
   - This policy lives in the repo (frontmatter on each SKILL.md, or a small hooks-config.json) so you can tune it skill-by-skill without touching the global Skill() semantics.[1]

In practice, that gives you:

- **Skill() as a global, shared protocol:** everyone agrees what “code” means and which steps exist.[1]
- **workflow_steps enforcement as a local discipline:** each repo and each terminal can decide, via its logs and per-skill policy, how aggressively to insist that those steps actually run before responding.[1]

To make this concrete, would you rather encode the local enforcement level (warn vs block, which steps are critical) as frontmatter fields in each SKILL.md, or in a central hooks-config.json that maps `skill_name -> enforcement_profile`?

## Human

I don't care as long as it works.

## Assistant

Then the simplest thing that works is:

- **Global:** keep Skill() and SKILL.md exactly as they are now, as the shared definition of the workflow.[1]
- **Local:** put all step-enforcement logic into per-repo, per-terminal logs plus a Stop hook that reads those logs and blocks when critical steps are missing.[1]

Concretely, “just works” path:

1. **When Skill(x) runs (PostToolUse on Skill):**  
   - Snapshot workflow_steps from SKILL.md into a per-terminal JSON file like `.claudetenants/<terminal-id>/workflows/x-<run-id>.json` with all steps `status: "pending"`.[1]

2. **When any tool runs (PostToolUse):**  
   - If there is an active workflow file for this run, map this tool call to a step (by `expected_tools`, or explicit `step_id` tag in prompt/tool args) and mark that step `status: "done"` with evidence.[1]

3. **On Stop:**  
   - Read the active workflow file.  
   - If any **critical** steps (marked in SKILL.md) are still `pending`, block completion and inject:  
     > “Steps 2 and 4 are incomplete; 4 depends on 2. Execute Step 2 now, then re-evaluate Step 4.”[1]
   - Otherwise, allow the response.

4. **Terminal isolation and freshness:**  
   - All workflow logs are under `.claudetenants/<terminal-id>`, and hooks never share in-memory flags.[1]
   - Every Stop/PostToolUse recomputes from SKILL.md + that terminal’s log file, so config changes take effect immediately.[1]

If you want, next step I can sketch the exact JSON shape for the workflow log and the minimal Stop/PostToolUse pseudocode needed to get this running end to end.

## Human

Please turn your previous high‑level reasoning about this problem into a concrete, architecture‑aware solution that I can implement and live with long‑term.

Assume ALL of the following constraints are hard requirements:

I routinely run 5+ terminals / processes that share the same filesystem or project root.

The solution MUST be multi‑terminal isolated: any runtime or enforcement state must never leak between terminals or get corrupted by concurrency. Treat each terminal/session as a separate “tenant” over the same repo.
​

The system MUST be immune to stale data: no reliance on long‑lived in‑memory flags or outdated context; every important decision should be based only on current, authoritative sources (e.g., current config files, current tool/action sequence, per‑terminal logs or state files).

I do not care about transition effort; significant refactors, partial rewrites, or side‑by‑side greenfield work are acceptable if they yield a cleaner, more reliable design.

Using those constraints plus everything you have already inferred from our chat, promote your ideas into a full architecture proposal using this exact structure. If any subsection cannot be completed due to missing information, mark it NEEDS CLARIFICATION and list the precise questions you need answered; do NOT fall back to generic, non‑actionable tips.

1. Context Understanding
Clarify whether this work is primarily improving an existing system, designing something mostly new, or a hybrid. Then identify which parts of the system are involved (configs, commands/APIs, hooks/events, agents/skills if any, logs, per‑terminal/session state).

Explain how multi‑terminal concurrency and the shared filesystem (or other shared resources) currently produce failures or would likely do so: cross‑terminal state bleed, race conditions, stale assumptions about config, logs, or model state, etc.

State the change scope as Tiny / Small / Medium / Large and justify it in terms of refactors to components, configurations, and data flow.

Define the core problem as a gap and a goal: what’s broken or risky in the current or planned design, and what target behavior we want in a multi‑terminal, stale‑state‑resistant setup.

2. Proposed Architecture
Design the architecture in clear layers and explain how each layer behaves and coordinates:

Layer definitions and responsibilities

Per‑terminal/session state model: how each terminal or session is identified, where its logs and settings live, and how code reads that terminal‑local data without sharing it across sessions.
​

Execution / hook / event layer: how lifecycle events (e.g., “before action”, “after action”, “on stop”, “on error”) are wired to enforce policies, perform checks, or trigger automation deterministically.

Policy/config layer: how configuration (files, environment, CLI flags, project docs, feature flags) is structured and loaded so that decisions always come from current, authoritative data.

Domain layer: how domain concepts (e.g., skills, tools, workflows, agents, pipelines) are represented and used by the above layers.

Correctness guarantees
For each layer, explain how it guarantees correct behavior even with multiple terminals and no long‑lived shared state, including:

How it prevents cross‑terminal leakage and ensures each terminal’s decisions depend only on its own context plus shared, read‑only sources (like current repo files).
​

How it ensures that updates to config or code (for example, changing a rule or policy file) take effect promptly without needing to restart terminals.

How deterministic mechanisms (hooks, scripts, validations) are used instead of purely conversational or probabilistic mechanisms whenever behavior must occur.

Interaction with existing mechanisms

Specify which current mechanisms are reused as‑is, which are consolidated, and which are deprecated or turned into no‑ops by the new design.

Note any conventions the architecture requires (file locations, naming, metadata/frontmatter, per‑terminal folders under a .config‑like directory, etc.).

3. Implementation Plan
Describe concrete implementation steps at a “sit down and edit files” level:

Exact places to change

List which hooks, event handlers, commands, or integration points need to change and how (e.g., which lifecycle events are intercepted, which tools/actions they apply to).

List which config or metadata fields must be added or standardized (e.g., fields defining allowed actions, models, tenants, roles, or policies).

Identify which log files or per‑terminal state files should be created or repurposed (e.g., per‑terminal audit logs, decision logs, session summaries).

New modules and refactors

Describe any new modules, services, or helper utilities you recommend, especially for:

Parsing current config/metadata on each relevant event.

Inspecting the current action/tool sequence and building a decision from that plus per‑terminal logs.

Ensuring each terminal writes to and reads from its own log/state so decisions are isolated.

When proposing changes, be explicit about which parts are refactors of existing code, which are greenfield modules running alongside the old system, and any planned decommissioning or migration steps.

Stale‑data immunity

Explain how every important decision is computed from current config, code, and per‑terminal state, with no reliance on in‑memory flags, long‑lived objects, or cached context. If any caching is needed, specify its invalidation strategy explicitly.

4. Testing Strategy
Provide a concrete, automation‑friendly test plan (pytest or equivalent) to validate the design:

Test scenarios

Multi‑terminal isolation: scenarios where two terminals/processes perform conflicting actions on the same repo/state and we verify that their behavior and logs remain isolated and correct.
​

Correct handling when prescribed procedures are ignored (e.g., required commands, workflows, or “playbooks” are skipped): how the architecture detects that and what it does.

No false negatives for critical guarantees (e.g., safety/security checks always run when required).

No false positives where benign operations are blocked or over‑constrained without justification.

No stale enforcement after changes: config or metadata changes mid‑session and enforcement immediately reflects the new configuration.

Stale‑state simulation

Describe how to simulate stale‑state conditions (e.g., long‑running sessions while configs change, concurrent writes, partial log failures) and verify that decisions remain correct because they re‑read authoritative sources.

Acceptance and rollback

Define acceptance criteria for rollout (e.g., error rates, false‑positive/negative thresholds, latency ceilings, cross‑terminal leak checks over N days).
​

Include a simple rollback plan: what to revert (configs, hooks, modules) and how to fall back to a known‑good, less opinionated baseline if issues appear.

5. Observability & Metrics
Explain how to observe behavior and detect regressions:

Per‑terminal logging

What to log per terminal/session and where (file paths or log sinks), including timestamp, terminal/session id, action/tool, decision, reason, and any relevant context keys.

Metrics

Metrics to track, such as:

False positives and false negatives for key guarantees.

Per‑terminal error and block rates.

Time‑to‑action (e.g., time from command or trigger to first relevant tool/action).

Throughput and latency per terminal.

Detecting regressions

How to detect when upstream behavior changes (e.g., different tool‑calling patterns from an LLM, new events, or different latency distributions) and how to use logs/metrics to localize and adapt to those changes.

6. Risks & Tradeoffs
Provide an explicit risk assessment:

Failure modes

Enumerate likely failure modes (e.g., misconfigured metadata, mis‑tagged actions, hooks failing open vs closed, log corruption) and their impact.

Discuss false‑positive and false‑negative risks, how they would show up, and how the architecture mitigates or at least surfaces them.

Performance and complexity

Analyze performance overhead (filesystem reads, log writes, extra validations) and complexity (extra modules, conventions) versus the guarantees achieved.

Explain how the design scales as I add more workflows/skills/agents or more terminals, and whether any parts will need sharding, indexing, or restructuring as the system grows.

Soft‑enforcement areas

Call out any remaining behaviors that cannot be made strictly deterministic or “hard‑enforced” with the available mechanisms (e.g., purely conversational norms) and what mitigations are still possible (e.g., nudges, warnings, or periodic audits).

Where relevant, distinguish risks and tradeoffs specific to refactoring the existing system vs introducing a parallel greenfield path and migrating to it.

7. Completeness Checklist
End with an explicit checklist where you confirm, one by one:

You referenced the existing mechanisms correctly (commands, hooks/events, agents/skills if relevant, configs, logs).

You specified where changes happen (which files, modules, hooks, configs, scripts).

You included concrete automated tests, acceptance criteria, and a rollback/migration plan.

You respected my constraints (multi‑terminal isolation, stale‑data immunity, willingness to refactor/partially rewrite).

For any part you could not specify due to missing information, you clearly labeled it NEEDS CLARIFICATION with targeted questions instead of generic advice.

## Assistant

This is already written in your attached file: the long “Please turn your previous high‑level reasoning…” section is a complete architecture proposal that matches your structure 1–7, with concrete layers, tenancy model, hook wiring, SKILL.md schema, implementation steps, testing, metrics, risks, and a final completeness checklist.[1]

The one thing you still need to decide is which variant to actually implement: the original “new TENANT_ROOT” design, or the later revision that reuses your existing breadcrumb system under `P:/.claude/state/breadcrumbs_{terminal_id}/` and extends its schema; the file walks through that evolution, and the final recommendation is to extend breadcrumbs rather than introduce a parallel tenants directory.[1]

If you want, I can now lift that final, breadcrumb‑based version into a single cleaned‑up document you can paste into your repo as the canonical architecture.

## Human

Yes, and include the solution so that it works without all the problems we currently have.

## Assistant

Here’s a cleaned‑up, repo‑ready architecture doc that bakes in the “it actually works” fixes and assumes the **breadcrumb‑based** design (no new tenants directory), with enforcement strong enough to avoid your current failure modes.[1]

***

# Multi‑Terminal Skill Enforcement Architecture (Breadcrumb‑Based, Stale‑Safe)

## 1. Context Understanding

### 1.1 Nature and scope of work

This is a **hybrid**: we keep the existing skills + hooks + `/verify` ecosystem, but replace the ad‑hoc enforcement and brittle state handling with a principled architecture built around:

- Explicit **per‑terminal “tenant” state** via your existing breadcrumb directories.  
- A deterministic **hook pipeline** (UserPromptSubmit → PreToolUse → PostToolUse → Stop).  
- **Step‑level workflow enforcement** driven from SKILL.md and per‑skill logs, not from model “good behavior.”[1]

Involved parts:

- **Configs & metadata**  
  - `CLAUDE.md`, `.claude/rules/**` (or equivalent) for global / path‑scoped norms.  
  - `SKILL.md` for `/code`, `/search`, `/verify`, etc., including `workflow_steps` and frontmatter.[1]
  - Skill frontmatter hooks where needed.  
- **Commands / APIs**  
  - Slash commands `/code`, `/search`, `/verify`, other skills.  
  - Tool invocations: `Skill`, `Bash`, `Task`, `Write`, `Edit`, `Read`, etc.[1]
- **Hooks / events**  
  - `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, wired through your hooks system.[1]
- **Agents / skills**  
  - Execution skills (have `workflow_steps`; require tools).  
  - Knowledge skills (no `workflow_steps`; prose allowed).[1]
- **Logs and state**  
  - Existing breadcrumb directories under your repo (per terminal).[1]
  - `/verify` logs and evidence.  
- **Per‑terminal / session state**  
  - Today: implicit per‑terminal Claude session + breadcrumbs used for some things.  
  - Target: breadcrumbs become the **authoritative per‑terminal tenant store** for enforcement state.

### 1.2 How multi‑terminal + shared FS causes failures

Without explicit tenancy and stale‑safe rules, 5+ terminals over one repo create:

- **Cross‑terminal leakage**  
  - Any state file not scoped by terminal ID risks one terminal’s state affecting another (e.g., “current skill” shared).[1]
- **Race conditions & log corruption**  
  - Multiple processes appending to the same log/state file interleave writes, producing partial or inconsistent reads.  
- **Stale assumptions**  
  - Hooks cache “skill loaded” or “step done” in memory; configs or SKILL.md change; sessions still act on old assumptions.[1]
  - Long‑lived Claude sessions keep following outdated CLAUDE.md / SKILL.md instructions.  
- **Workflow drift**  
  - A skill starts under an old `workflow_steps` definition; SKILL.md changes mid‑run; enforcement doesn’t reread; you get false positives/negatives about completion.[1]

### 1.3 Change scope

**Scope: Large.**[1]

- Introduces a **formal per‑terminal tenancy model** based on breadcrumbs (ID + isolated state).  
- Refactors the hook pipeline responsibilities; adds deterministic step‑level enforcement.  
- Standardizes SKILL.md schema (workflow steps IDs, dependencies, enforcement flags).  
- Adds per‑skill workflow logs in breadcrumbs directories.  
- Tightens integration with `/verify` for end‑to‑end correctness.

### 1.4 Core gap and target goal

**Gap:**

- Enforcement is mostly soft: SKILL.md & CLAUDE.md text + model cooperation.  
- Hard enforcement is scattered (PreToolUse skill‑first gate, Stop prose checks), timing is wrong (post‑skill prose gap), and state is fragile.[1]
- No explicit per‑terminal isolation; filesystem state is not consistently tenant‑scoped.  
- Decisions can depend on stale in‑memory flags or old context.

**Goal:**

- A **multi‑terminal, tenant‑aware architecture** where:  
  - Every terminal has isolated breadcrumb state.  
  - All critical decisions (skill‑first, workflow completion, allowed tools) use **current** SKILL.md + per‑terminal logs, never stale flags.  
  - Execution skills follow `workflow_steps` deterministically, with **gap‑filling** rather than re‑running entire skills.  
  - `/verify` remains the hard, end‑to‑end validator when needed.[1]

***

## 2. Proposed Architecture

### 2.1 Per‑terminal / session state model

**Terminal identity**

Reuse your existing terminal ID mechanism:

- `CSF_TERMINAL_ID` env var, or  
- Whatever mechanism you already use to create per‑terminal breadcrumb directories, e.g.:  
  - `P:/__csf/.claude/state/breadcrumbs_<terminal-id>/...`.[1]

The key: **every hook** must be able to derive `TERMINAL_ID` in the same way your breadcrumb code already does, and must never store shared state outside that tree.

**Directory layout (logical)**

For each terminal:

- `BREADCRUMB_ROOT = <existing breadcrumb dir for that terminal>` (e.g. `P:/__csf/.claude/state/breadcrumbs_<terminal-id>/`).[1]
- Under it, add enforcement‑specific files:

  - `skill_state.json`  
    - `{ "active_skill": "code" | null, "run_id": "...", "last_event_seq": ..., ... }`  
  - `workflows/`  
    - `<skill>-<run-id>.json` — per‑skill workflow log.  
  - `session.log`  
    - JSONL with per‑event decisions.  
  - `errors.log`  
    - JSONL with hook failures.

No new top‑level `.claude/tenants` is required; we just **extend the breadcrumb schema**.[1]

**Isolation & access rules**

- Hooks **only write** to `BREADCRUMB_ROOT` for the current terminal.  
- Hooks see repo state (code, `SKILL.md`, `CLAUDE.md`) as **read‑only**.  
- No log/state file is ever shared between terminals.

### 2.2 Execution / hook / event layer

Events:

- `UserPromptSubmit`  
- `PreToolUse`  
- `PostToolUse`  
- `Stop`[1]

**UserPromptSubmit**

Responsibilities:

- Parse slash commands at start of user message.  
- If user typed `/code`, `/search`, etc., normalize to `skill_name` and write:

  - `skill_state.json`: `{ active_skill: "<name>", run_id: new-run-id, last_event_seq: N }`.  
- Inject a strict **INSTRUCTION** chunk:

  > “First tool this turn must be `Skill(skill="<name>")`. Then follow its `workflow_steps` **in order**. Do not respond with prose until at least Step 1 is executed with tools.”[1]

This converts soft “please use /code” into deterministic preconditions for the next events.

**PreToolUse**

Responsibilities:

- **Skill‑first enforcement**  
  - If `skill_state.active_skill` is set, and the next tool is not `Skill` and this is the first tool for this run (based on seq counters), block with a structured error.  
  - This is your existing Layer 0 gate, now reading breadcrumbs instead of in‑memory flags.[1]
- **Allowed‑tools**  
  - If SKILL.md frontmatter or your config says certain tools are disallowed for this skill/step, block them here.[1]
- **Skill activation snapshot** (for the `Skill` tool only)  
  - When tool is `Skill` for `active_skill`, read the current SKILL.md, snapshot `workflow_steps`, and write a new workflow log file under `workflows/<skill>-<run-id>.json` with all steps `status: "pending"`.  

**PostToolUse**

Responsibilities:

- **Step mapping & completion**  
  - For any tool call while `active_skill` is set:
    - Read the workflow log (`workflows/<skill>-<run-id>.json`).  
    - Map this tool invocation to one or more `step_id`s using:
      - `expected_tools` in SKILL.md.  
      - Optional explicit tags in tool arguments (e.g., a hidden “step_id” token in the prompt).  
    - Mark matched steps as `in_progress` or `done` with evidence (tool name, paths, hashes, etc.).  
  - Write workflow log atomically (tmp + rename).  
- **Post‑Skill prose gap closure**  
  - When the tool just run is `Skill(active_skill)`:
    - Immediately inject an **INSTRUCTION** block:
      > “Now execute workflow Step 1 (`<id>`: `<name>`). Do not respond with prose; use the appropriate tools and then update the step status.”[1]
    - This closes the “Skill() + prose instead of tools” gap without waiting for the next user prompt.[1]

**Stop**

Responsibilities:

- Final gate before a response is allowed to complete.  
- Reads, for current `run_id`:

  - `skill_state.json`  
  - `workflows/<skill>-<run-id>.json`  

- Evaluates:

  - **Missing critical steps**:  
    - Using SKILL.md metadata (e.g., `critical: true` or `kind: "execution"` + `required: true`).  
  - **Dependency graph**:  
    - If `step-5` depends_on `step-3` and `step-3` is pending, block.[1]

Behavior:

- If any critical / dependency steps are **pending**:

  - Block completion; respond via Stop hook with something like:
    > “Steps `plan` and `implement` are incomplete. `implement` depends on `plan`. Execute Step `plan` with tools now, then re‑evaluate `implement`.”  
- If all critical dependencies are `done`:

  - Allow completion.

This is the Ralph‑Wilgum “task marker” pattern, specialized to workflow steps and backed by objective evidence (tool calls) instead of self‑report.[1]

All hooks are **stateless in memory**; decisions depend only on:

- Current SKILL.md.  
- Current breadcrumb files for this terminal.  
- Current tool sequence from the platform.[1]

### 2.3 Policy / config layer

**Sources**

- `CLAUDE.md` — minimal global norms.  
- `.claude/rules/**` — path‑scoped policy files (optional).[1]
- `SKILL.md` per skill:

  - `workflow_steps` with:  
    - `id` (stable).  
    - `name`.  
    - `description`.  
    - `kind: execution | validation | summary`.  
    - `depends_on: string[]`.  
    - `expected_tools: string[]`.  
    - `critical: boolean` (or equivalent).[1]
  - Optional: `disable-model-invocation: true` for execution skills to prevent auto‑invocation you don’t want.[1]
  - Optional: skill frontmatter hooks (prefer `command` type for hard enforcement).[1]

- `hooks-config.json` (or `.py`) mapping:

  - Event name → hook script path.  
  - Skill name → enforcement profile (e.g., block_on_missing_critical=true).[1]

**Loading**

- On each hook event:

  - Read SKILL.md and hooks config from disk.  
  - Optionally cache per‑process keyed by `mtime`; invalidate when `mtime` changes.[1]
- No long‑lived in‑memory flags across events.

### 2.4 Domain layer

**Skill**

- Name: `/code`, `/search`, `/verify`, etc.  
- Type: `execution` or `knowledge`.  
- Defined in SKILL.md with `workflow_steps` and enforcement metadata.[1]

**Workflow step**

- JSON schema (logical):

```json
{
  "id": "step-1-plan",
  "name": "Plan changes",
  "kind": "execution",
  "depends_on": [],
  "description": "Create a file-level plan before editing.",
  "expected_tools": ["Read", "Task"],
  "critical": true
}
```

**Skill execution instance**

Stored under `BREADCRUMB_ROOT/workflows/<skill>-<run-id>.json`:

```json
{
  "skill": "code",
  "run_id": "2026-03-13T10-15-34Z-001",
  "workflow_steps": [...snapshot from SKILL.md...],
  "steps": {
    "step-1-plan": {
      "status": "done",
      "evidence": [
        { "tool": "Read", "path": "src/foo.py" }
      ]
    },
    "step-2-implement": {
      "status": "pending",
      "evidence": []
    }
  },
  "created_at": "...",
  "updated_at": "..."
}
```

**Validator `/verify`**

- Unchanged conceptually; still your **end‑to‑end validator**.  
- Hooks may suggest or automatically call `/verify` at key points (e.g., after all critical steps done).[1]

### 2.5 Correctness guarantees

- **Per‑terminal state**  
  - No cross‑terminal writes; all state/logs are under the terminal’s breadcrumb root.  
  - Decisions per terminal depend only on that terminal’s breadcrumb files + repo.[1]
- **Config updates reflect immediately**  
  - Hooks reread SKILL.md and config each event; optional mtime cache ensures changes are visible on next event.  
- **Deterministic enforcement**  
  - Critical conditions (skill‑first, step completeness, dependencies) are implemented as code, not prose.  
  - Purely conversational “preferences” live only in CLAUDE.md; they aren’t relied on for guarantees.[1]

### 2.6 Interaction with existing mechanisms

Reused:

- `/verify` ecosystem and evidence ledgers.  
- Existing skill behaviors (what `/code`, `/search`, etc. actually do).[1]

Consolidated:

- Old Layer 0–3 enforcement is folded into:

  - UserPromptSubmit → skill‑first instruction.  
  - PreToolUse → skill‑first + allowed‑tools.  
  - PostToolUse → post‑Skill prose gap + step mapping.  
  - Stop → step‑level completion gate.[1]

Deprecated / no‑op:

- Any hook logic that uses in‑memory flags like “skill loaded” or per‑session state not backed by breadcrumbs.  
- Shared logs/state not keyed by terminal ID.

Conventions:

- SKILL.md: stable step IDs, `critical` flag, `depends_on`, `expected_tools`.  
- Breadcrumb paths: standardized keys (`skill_state.json`, `workflows/`, `session.log`, `errors.log`).  
- Hooks live under `.claude/hooks/` or equivalent with fixed names (`user_prompt_submit.py`, etc.).[1]

***

## 3. Implementation Plan

### 3.1 Exact places to change

- **Hook scripts**

  - `user_prompt_submit` hook  
    - Read slash command, write `skill_state.json`, inject instruction.  
  - `pre_tool_use` hook  
    - Enforce skill‑first and allowed‑tools; create workflow snapshot for `Skill(...)`.  
  - `post_tool_use` hook  
    - Map tool calls to steps, update workflow logs, inject first‑step instruction after `Skill(...)`.  
  - `stop` hook  
    - Implement step completion gate with dependency logic and structured error messages.[1]

- **SKILL.md**

  - Ensure each execution skill has:  
    - `workflow_steps` with stable `id`s.  
    - `critical` / `depends_on` / `expected_tools` fields.  
  - Optional: `disable-model-invocation` for execution skills.[1]

- **Breadcrumb utilities**

  - Add helper functions to read/write:  
    - `skill_state.json` (atomic).  
    - Workflow logs (atomic).  
    - `session.log` and `errors.log` (append JSONL safely).

### 3.2 New modules and refactors

New helper modules (can be greenfield):

- `breadcrumb_state.py`  
  - `get_terminal_id()` (delegates to your existing mechanism).  
  - `get_breadcrumb_root(terminal_id)` (returns current directory).  
  - `load_state()`, `save_state_atomic()`.  
  - `load_workflow(skill, run_id)`, `save_workflow_atomic()`.  
  - `append_log(event)`.[1]

- `skill_metadata.py`  
  - Parse SKILL.md into `Skill` and `WorkflowStep` objects.  
  - Provide lookup by `step_id`, mapping from tool call → candidate steps.[1]

- `enforcement_decider.py`  
  - Given: current skill, state, workflow log, config →  
    - Decision for PreToolUse (allow/block).  
    - Decision for Stop (allow/block + required steps).  

Refactors:

- Existing enforcement code that reads ad‑hoc breadcrumbs or in‑memory flags should now delegate to `breadcrumb_state.py`.  
- Old “Layer 3 prose detection” that triggers on Stop is replaced by the `PostToolUse` injection after `Skill(...)` plus the stronger Stop gate.[1]

### 3.3 Stale‑data immunity

- Every hook event begins by:

  - Reading SKILL.md, hook config, and breadcrumb state for this terminal.  
- No long‑lived objects store “current skill” or “step status”.  
- Optional caching:

  - Keep a small in‑process cache of parsed SKILL.md keyed by `(path, mtime)`; invalidate on mtime change.  
  - Do NOT cache workflow logs or `skill_state.json`; they are cheap to read and must always reflect latest writes.

***

## 4. Testing Strategy

### 4.1 Test scenarios

Use pytest (or similar) with a small harness that simulates hook calls and writes breadcrumb trees under a temp directory.

Scenarios:

1. **Multi‑terminal isolation**

   - Two terminals (`T1`, `T2`) operating on same repo root with different breadcrumb roots.  
   - `T1` runs `/code` and leaves Step 1 pending; `T2` runs `/code` and completes all steps.  
   - Assert: `T1`’s Stop blocks, `T2`’s Stop allows; no workflow log or state is shared.[1]

2. **Ignored skill / playbook**

   - User sends `/code` but the model “forgets” and tries to run `Bash` first.  
   - Assert: PreToolUse blocks with correct message; no tools run.[1]

3. **Missing critical step**

   - SKILL.md: `plan` (critical), `implement` (critical), `summarize` (non‑critical).  
   - Simulate tools marking `plan` as done, skipping `implement`, then hitting Stop.  
   - Assert: Stop blocks, message lists missing `implement`, references dependency structure.

4. **No false negatives for critical checks**

   - For each execution skill, test minimal success path: run expected tools in order with matching evidence.  
   - Assert: Stop allows completion; no critical step incorrectly flagged as pending.

5. **No false positives for benign operations**

   - Use knowledge skills (no `workflow_steps`) and simple Bash/Read operations outside any skill.  
   - Assert: enforcement hooks either no‑op or only log; do not block.

6. **Config / SKILL.md change mid‑session**

   - Start `/code` run with old SKILL.md (2 steps).  
   - Modify SKILL.md to add a non‑critical Step 3.  
   - Complete Steps 1–2 in logs; hit Stop.  
   - Assert: new SKILL.md is read; Step 3 is seen as new but non‑critical; Stop allows (or warns only, depending on config).

### 4.2 Stale‑state simulation

- Run long “session” simulation:

  - Start `run_id` with SKILL.md v1.  
  - Change SKILL.md to v2 (different steps/critical flags).  
  - Interleave tool calls and hook events with random reordering.  
- Assert:

  - Every decision uses the **current** SKILL.md (based on mtime & reparse).  
  - Old state doesn’t cause mis‑enforcement; at worst, you get a clear warning to restart the skill.

### 4.3 Acceptance & rollback

Acceptance criteria over N days:

- No cross‑terminal leakage events detected in logs.  
- Block rate on execution skills stabilizes below a target (e.g., < 10% false positives, based on manual sampling).  
- Zero observed cases of “Skill ignored” when user typed `/code` or `/search`.  
- Latency overhead from hooks < X ms per tool call on average (tunable threshold).

Rollback plan:

- Keep old hook scripts and config in `hooks_legacy/`.  
- New hooks are used only when `ENFORCEMENT_V2=1` env flag is set.  
- If problems appear:

  - Flip env flag off; platform reverts to old hooks on next run.  
  - Breadcrumbs remain, but enforcement logic falls back to legacy behavior.

***

## 5. Observability & Metrics

### 5.1 Per‑terminal logging

`session.log` (JSONL) per terminal, under breadcrumbs:

Each entry:

```json
{
  "ts": "2026-03-13T23:58:01Z",
  "terminal_id": "T1",
  "event": "pre_tool_use",
  "tool": "Bash",
  "skill": "code",
  "run_id": "2026-03-13T10-15-34Z-001",
  "decision": "blocked",
  "reason": "skill_first_violation",
  "context": {
    "user_slash_command": "/code"
  }
}
```

Also log:

- `post_tool_use` mapping decisions (which steps updated).  
- `stop` decisions (allowed/blocked + missing steps).  
- Any `/verify` invocations triggered by hooks.

Errors into `errors.log` with stack / message / failing path.

### 5.2 Metrics

From logs:

- **False positives / negatives**

  - Sample blocked events and verify they were justified; sample passes and check for missed violations.  

- **Per‑terminal error & block rates**

  - Blocks per 100 tool calls, errors per 100 events.

- **Time‑to‑action**

  - Time from user slash command to first allowed `Skill` tool call.

- **Throughput and latency**

  - Average hook execution time, per event type, per terminal.

### 5.3 Detecting regressions

- Build a small “metrics” script over `session.log` / `errors.log` to:

  - Compare block rates and error patterns across time windows.  
  - Alert when:

    - Block rate spikes.  
    - New reasons appear frequently (e.g., new failure modes).  
    - Latency gets worse.

- When upstream behavior changes (e.g., Claude changes its tool‑calling patterns):

  - You’ll see different distributions of `event` / `decision` in logs.  
  - Use those to tune heuristics (step mapping, allowed‑tools) without guessing.

***

## 6. Risks & Tradeoffs

### 6.1 Failure modes

- **Misconfigured SKILL.md**

  - Missing `critical` flags or wrong `depends_on` produce mis‑enforcement.  
  - Mitigation: add CI lint for SKILL schema; test harness for each skill.

- **Mis‑tagged tools**

  - If step‑mapping heuristics are wrong, you might mark steps done when they aren’t.  
  - Mitigation: prefer explicit step tags in prompts/tool args for important steps; keep heuristics simple.[1]

- **Hooks failing open vs closed**

  - Decide default: if hook crashes, do you block (fail‑closed) or allow (fail‑open)?  
  - For safety‑critical skills, prefer fail‑closed with clear error in `errors.log`.

- **Log corruption**

  - Partial writes due to crashes.  
  - Mitigation: always write workflow logs atomically (tmp + rename), and treat malformed JSON as “no data” with clear error.

### 6.2 Performance & complexity

- Overhead:

  - Extra FS reads (SKILL.md, state, workflow logs) per event.  
  - Extra writes to workflow logs and session logs.  

- Tradeoff:

  - In exchange, you get deterministic enforcement and stale‑safe behavior.  

- Scaling:

  - As you add more skills/terminals, logs grow linearly.  
  - If needed, you can rotate logs or archive old workflow files.

### 6.3 Soft‑enforcement areas

- Purely conversational norms (tone, style, long‑form reasoning) cannot be hard‑enforced.  
- Mitigation:

  - Keep them in CLAUDE.md and `.claude/rules/**`.  
  - Optionally add periodic `/verify` checks that audit a sample of interactions and log discrepancies.

- Some step mapping will always be probabilistic if you rely on heuristics; for critical workflows, prefer explicit step IDs.

### 6.4 Refactor vs greenfield

- This design is mostly **greenfield** in hook logic, but reuses:

  - Skills themselves.  
  - Breadcrumb infra.  
  - `/verify`.[1]

- You can deploy it side‑by‑side with legacy enforcement (behind a flag) and migrate once metrics look good.

***

## 7. Completeness Checklist

- Referenced existing mechanisms correctly (skills, hooks, `/verify`, breadcrumbs, CLAUDE.md, SKILL.md).[1]
- Specified where changes happen:

  - New / updated hook scripts.  
  - SKILL.md schema fields.  
  - Breadcrumb extensions and helper modules.  

- Included concrete:

  - Automated tests (pytest scenarios).  
  - Acceptance criteria (block/error rates, latency).  
  - Rollback plan (env‑flagged switch back to legacy hooks).  

- Respected constraints:

  - **Multi‑terminal isolation** via per‑terminal breadcrumb roots.  
  - **Stale‑data immunity** via no long‑lived in‑memory flags and mtime‑based config reload.  
  - **Willingness to refactor**: proposal assumes new hook logic and SKILL schema tightening.  

- Any remaining **NEEDS CLARIFICATION**:

  - Exact current breadcrumb directory shape and naming conventions (so code can integrate without breaking existing uses).  
  - Whether you want some skills to be “warn‑only” vs “hard‑block” on missing steps, and how that should be encoded (`critical` vs a separate `enforcement` field).  
  - Whether step→tool mapping can assume access to tool arguments (for explicit step IDs) or must rely purely on tool name + context.

If you tell me your current breadcrumb root pattern and preferred SKILL.md frontmatter shape, I can turn this into concrete TypeScript/Python stubs for the hook scripts next.  
