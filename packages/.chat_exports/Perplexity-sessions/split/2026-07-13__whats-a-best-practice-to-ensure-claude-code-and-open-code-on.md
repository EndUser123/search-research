---
title: "what's a best practice to ensure claude code and open code, on windows 11, use powershell 7 and python when optimal?  'M"
date: "2026-07-13"
mode: "COPILOT"
uuid: "ae091ee8-889e-476a-862c-beb10963eaab"
entry_count: 6
---

## Human

what's a best practice to ensure claude code and open code, on windows 11, use powershell 7 and python when optimal?  "Make it durable through three layers: policy, routing, and verification. Do not rely on a paragraph copied into individual implementation prompts.
Recommended architecture
1. Put the normative rule in the workspace’s canonical guidance
Add a concise policy to the highest applicable source of truth, likely:
P:\AGENTS.md

or, if the rule is specifically for Claude Code agents:
P:\.claude\AGENTS.md

The top-level rule should remain short enough to be consistently followed:
Tool-selection invariant:

Choose tools by the operation, not by the host operating system.

Priority:
1. Native agent tools for repository search and file inspection.
2. Existing tested repository utilities.
3. Python for structured, reusable, deterministic, or cross-platform logic.
4. PowerShell for Windows-native administration and runtime integration.
5. Shell pipelines only for small disposable operations.

Do not encode maintained policy in ad hoc shell pipelines.
Do not create a maintained helper for a one-time search.
For any new helper, identify its owner, callers, inputs, outputs, failure behavior, and tests.

This makes the policy available to all workstreams without bloating every prompt.
2. Put detailed decision logic in a plugin-owned skill
The full policy should not live only in AGENTS.md. Create or extend a reusable plugin-owned capability, for example:
P:\packages\.claude-marketplace\plugins\<governance-plugin>\
    skills\tool-selection\
        SKILL.md
        references\decision-matrix.md
        tests\

This skill should own:
the decision matrix;
examples and counterexamples;
rules for Python versus PowerShell;
when native Grep, Glob, and Read are preferred;
when an existing project script has authority;
standards for introducing maintained helpers;
failure and fallback behavior.
Local .claude files should only contain a thin registration or adapter if required.
Do not add the policy independently to /go, /review, /red-team, /codex, and /agy. That would recreate the drift you are already fighting.
3. Use routing rather than unconditional prompt injection
The rule should always be visible at a high level, but the detailed skill should activate only when tool choice matters.
Suitable triggers include:
a prompt proposes a new script or helper;
the agent is about to use PowerShell, Bash, Python, Node, or another runtime;
repository discovery is required;
a cross-platform or Windows-specific implementation is requested;
a command triggers a permission prompt;
duplicated shell pipelines appear;
an implementation introduces operational automation.
The router should inject a small directive such as:
Apply the canonical tool-selection policy. Prefer native repository tools for discovery, existing tested utilities for established workflows, Python for maintained structured logic, and PowerShell only for Windows-native responsibilities. Justify any new maintained helper.

It should not paste the entire decision matrix into every request.
4. Add a pre-execution check for maintained helpers
Before adding a new .py, .ps1, .sh, .js, or executable wrapper, require a small structured decision:
tool_choice:
  operation:
  selected_tool:
  alternatives_considered:
  one_time_or_maintained:
  existing_utility_checked:
  owner:
  callers:
  failure_behavior:
  test_path:

This need not be shown to the user for every simple command. It should be required when a new maintained execution path is being introduced.
The important gate is:
New maintained helper
    ↓
Existing utility searched?
    ↓
Responsibility and owner known?
    ↓
Tool choice justified?
    ↓
Focused test exists?

If those answers are missing, the agent should not add the helper yet.
5. Add a lightweight audit, not a hard semantic hook
A deterministic hook cannot reliably determine whether Python or PowerShell was the best design choice. Avoid a brittle rule such as:
PowerShell detected → block

Instead, use an advisory audit that flags suspicious patterns:
rg | Select-String | Select-String;
long inline python -c programs;
reusable logic embedded in shell commands;
new scripts with no callers or tests;
Python used only to invoke one Windows-native cmdlet;
PowerShell used for complex JSON transformations;
duplicate helpers implementing the same operation;
new wrappers that bypass canonical runtime entrypoints.
The audit should produce findings, not automatically reject all violations:
TOOL_SELECTION_REVIEW_REQUIRED
reason: maintained policy appears embedded in an ad hoc PowerShell pipeline

A hard block should be reserved for objective failures such as:
a new executable helper has no owner;
a claimed existing utility was not searched for;
a package-owned capability was added to a generated cache;
a new runtime path has no verification path.
6. Create a shared regression corpus
Keep a small canonical set of examples used by relevant skills and hooks:
OperationPreferred choice
Search repository text
Grep or rg
Find files
Glob or rg --files
Read a file
Read
Parse and compare JSON
Python
Classify a worktree inventory
Python
Inspect Windows ACLs
PowerShell
Read machine/user environment scopes
PowerShell
Thin Windows launcher
PowerShell
Reusable cross-platform resolver
Python
One simple native command
Direct command
Multi-stage disposable filtering
Native search options before pipelines
Tests should verify the policy and router, not try to prove that one language is universally superior.
7. Capture telemetry before adding stronger enforcement
For a few weeks, record:
operation_category
selected_tool
new_helper_created
existing_utility_found
permission_prompt_triggered
fallback_used
review_finding
changed_after_review

Store it as run-scoped operational telemetry, not source:
P:\.claude\.artifacts\tool-selection\

Then review whether the policy actually reduces:
unnecessary permission prompts;
duplicate utilities;
brittle shell pipelines;
Windows-only logic where cross-platform behavior was intended;
excessive helper proliferation.
Only strengthen enforcement where recurring failure patterns are proven.
8. Integrate it into /go at specific boundaries
For /go, apply the detailed policy at:
discovery planning;
implementation-plan approval;
before introducing a helper, wrapper, or runtime dependency;
completion review.
Do not make tool selection another permanent /go phase. It is a cross-cutting check at the points where tool choice becomes consequential.
A completion packet should mention tool choice only when a maintained mechanism was introduced:
TOOL_SELECTION:
- operation:
- implementation chosen:
- existing alternatives inspected:
- why this choice is durable:
- verification:

Durable source-of-truth model
P:\AGENTS.md
    concise invariant
        ↓
plugin-owned tool-selection skill
    detailed policy and examples
        ↓
router
    activates policy when consequential
        ↓
advisory audit
    identifies suspicious choices
        ↓
tests and telemetry
    prove whether the policy works

What not to do
Do not:
paste the full policy into every implementation prompt;
globally prohibit PowerShell;
globally prefer Python;
create another local classifier under P:\.claude\hooks;
make the policy dependent on LLM memory;
allow the policy to become a reason for unnecessary design ceremony;
let the audit claim a tool is wrong without checking callers, authority, and runtime requirements.
The most effective first implementation is: add the concise invariant to the canonical AGENTS.md, create one plugin-owned detailed policy, and have /go consult it only when introducing or changing a maintained execution mechanism."

## Assistant

You already have the right high‑level pattern; the “best practice” is to make PowerShell 7 and Python preference a durable, system‑level invariant backed by routing and verification, not something you paste into prompts. The concrete next step is to implement the policy exactly where agents actually read from: AGENTS.md, a plugin-owned skill, and your router + audit hooks.[1][2][3][4][5]

## 1. Canonical invariant in AGENTS.md

On Windows 11 with Claude Code and Open Code, treat your AGENTS.md as the front door for AI agents: concise, high‑signal rules they read before doing work.[2][3][4][1]

For your case, the invariant you sketched is appropriately short and durable:

> Tool‑selection invariant:  
> Choose tools by the operation, not by the host operating system.  
> Priority:  
> 1. Native agent tools for repository search and file inspection.  
> 2. Existing tested repository utilities.  
> 3. Python for structured, reusable, deterministic, or cross‑platform logic.  
> 4. PowerShell for Windows‑native administration and runtime integration.  
> 5. Shell pipelines only for small disposable operations.

Putting that in `P:\AGENTS.md` (and optionally `P:\.claude\AGENTS.md` as your Claude‑specific layer) aligns with current AGENTS.md guidance: global, concise rules at the top, directory‑specific overrides below when really needed.[3][4][5][1][2]

You’re correctly avoiding the anti‑pattern AGENTS.md videos warn about (turning it into a novel that agents ignore); keep this invariant short, timestamp it, and periodically test whether agents actually follow it.[6][5]

## 2. Detailed logic in a plugin‑owned “tool‑selection” skill

The full decision matrix (Python vs PowerShell vs native tools) should live in a plugin‑owned skill, not in scattered prompts or duplicated local hook configs. That matches how other AI agent ecosystems use “policy skills” or plugin capabilities as reusable governance modules.[4][1][2][3]

Your proposed layout is solid:

- `P:\packages\.claude-marketplace\plugins\<governance-plugin>\skills\tool-selection\SKILL.md` for the narrative policy and usage patterns.  
- `references\decision-matrix.md` for tabular cases, examples, and counterexamples.  
- `tests\` for concrete repository scenarios that assert:  
  - Python when logic is cross‑platform, structured, or deterministic.  
  - PowerShell when you are touching Windows ACLs, registry, environment scopes, task scheduler, etc.[7][8]

This skill becomes the single authority for:

- When to favor native *agent* tools (e.g., Grep/rg, Glob, Read, built‑in repo search) instead of writing custom scripts.  
- When existing project utilities (e.g., `tools\scan.ps1`, `scripts\scan.py`) must be used before new helpers.  
- Explicit rules for Python vs PowerShell, including:  
  - PowerShell only when the operation is fundamentally Windows‑native (ACLs, env scopes, scheduled tasks, thin launchers).[8]
  - Python when you need robust JSON handling, cross‑platform behaviour, or reusable classification logic.[9][10][7]

Local `.claude` config files then just register this skill or provide adapters; they should not each contain a divergent version of the policy. That avoids policy drift across `/go`, `/review`, `/red-team`, `/codex`, and `/agy`.

## 3. Router triggers and minimal prompt injection

Instead of pasting the whole decision matrix into every task, you want a router that injects a small directive when tool selection is actually consequential. That’s consistent with the way agent frameworks describe AGENTS.md and routing: global hints, plus specific injections only when context demands it.[5][1][3][4]

The triggers you listed are good; I’d keep them tight:

- When a new script/helper is proposed (`.py`, `.ps1`, `.sh`, `.js`, executable wrapper).  
- When the agent is about to choose between Python, PowerShell, Bash, Node, or similar runtimes.  
- When repository discovery or cross‑platform implementation is requested.  
- When a command triggers a permission prompt or uses Windows‑specific capabilities.  

Then inject a compact directive like:

> Apply the canonical tool‑selection policy. Prefer native repository tools for discovery, existing tested utilities for established workflows, Python for maintained structured logic, and PowerShell only for Windows‑native responsibilities. Justify any new maintained helper.

The router should *call* the tool‑selection skill when these triggers fire, not try to embed the entire policy into every Claude Code or Open Code request. That keeps prompts lean while still enforcing your invariant at the boundaries that matter.

### How this makes “PowerShell 7 and Python when optimal” real

Because the router only activates the policy on “tool choice” events, you get durable behaviour without ceremony:

- For one‑off disposable operations, agents can still use short native commands or tiny pipelines.  
- For any maintained mechanism (new helper, new runtime path), the skill and router enforce the Python vs PowerShell rules and require justification.  
- On Windows 11, PowerShell 7 is used only for operations that are intrinsically Windows‑native; Python is preferred for reusable logic and cross‑platform tasks.

## 4. Pre‑execution structured decision for maintained helpers

To avoid half‑baked helpers, require a small, structured “tool_choice” record before adding any new maintained execution path:

```yaml
tool_choice:
  operation:
  selected_tool:
  alternatives_considered:
  one_time_or_maintained:
  existing_utility_checked:
  owner:
  callers:
  failure_behavior:
  test_path:
```

This matches the spirit of “briefing packets” and structured project docs: agents read them, and they’re concise, testable, and easy to audit.[1][2][3][4]

Practically, you can implement this as:

- A router hook that, when a new `.py` or `.ps1` is being created, asks the agent to fill this block into a `tool-selection.yaml` or an inline comment next to the helper.  
- A governance plugin function that validates the fields:
  - `existing_utility_checked` must reference a search (e.g., `rg` or repo script) that was actually run.  
  - `owner` and `callers` must be concrete.  
  - `test_path` must point to at least one test or usage example.  

If any of those are missing, the plugin returns “do not yet add this helper”. This is how you make “Python and PowerShell only when optimal” a gate, not just a suggestion.

## 5. Advisory audit hook rather than hard blocks

A deterministic rule like “block PowerShell whenever detected” will fail on Windows‑native operations and cause friction, which AGENTS.md best‑practice discussions explicitly warn against: policy should guide, not become ceremony.[5]

Instead, implement an advisory audit that:

- Scans for suspicious PowerShell and Python patterns, such as:
  - Long inline `python -c` or PowerShell pipelines where logic clearly belongs in a maintained script.  
  - New scripts with no callers and no tests.  
  - PowerShell being used for complex JSON transformations or cross‑platform logic that Python would better handle.[10][7][9]
  - Duplicate helpers implementing the same operation.  
- Emits findings like:

```text
TOOL_SELECTION_REVIEW_REQUIRED
reason: maintained policy appears embedded in an ad hoc PowerShell pipeline
```

Hard rejections should be reserved for objective failures:

- New helpers with no owner.  
- Claimed existing utilities not actually searched in the repo.  
- Package‑owned capabilities added to generated caches.  
- New runtime paths with no verification tests.

This keeps agents productive while creating a clear feedback loop that gradually pushes them toward your Python/PowerShell norms.

## 6. Regression corpus and telemetry

You already outlined a canonical examples table; that’s exactly what you want to codify in the governance plugin and tests. For Windows 11, the key rows are:

| Operation                          | Preferred tool                 |
|------------------------------------|--------------------------------|
| Search repository text             | Grep / rg                      |
| Find files                         | Glob / `rg --files`           |
| Read a file                        | Native Read tool              |
| Parse and compare JSON             | Python                         |
| Classify worktree inventory        | Python                         |
| Inspect Windows ACLs               | PowerShell                     |
| Read machine/user environment      | PowerShell                     |
| Thin Windows launcher              | PowerShell                     |
| Reusable cross‑platform resolver   | Python                         |
| One simple native command          | Direct command                 |
| Multi‑stage disposable filtering   | Native options before pipeline |

Tests should assert that, given each of these operations, the tool‑selection skill and router choose the expected runtime and tools, and that the audit does not flag correct choices.  

To validate the policy actually helps, collect telemetry as you described:

- `operation_category`, `selected_tool`, `new_helper_created`, `existing_utility_found`, `permission_prompt_triggered`, `fallback_used`, `review_finding`, `changed_after_review`.  
- Store per‑run artifacts under something like `P:\.claude\.artifacts\tool-selection\`, mirroring how agents store local operational artifacts.[11][8]

After a few weeks, you can measure whether you reduced:

- unnecessary permission prompts on Windows;  
- duplicate utilities and brittle pipelines;  
- Windows‑only logic for operations that should have been cross‑platform Python;  
- proliferation of half‑maintained helpers.

Only then strengthen enforcement (e.g., upgrade some advisory findings to hard blocks).

## 7. Integrate with `/go` at consequential boundaries

Rather than adding a permanent “tool selection phase”, thread the policy through existing `/go` boundaries:

- Discovery planning: ensure the plan mentions whether Python or PowerShell will be used and why.  
- Implementation‑plan approval: require a quick check against the decision matrix before green‑lighting new maintained helpers.  
- Before introducing helpers/wrappers/runtimes: invoke the tool‑selection skill and fill the `tool_choice` structure.  
- Completion review: only mention TOOL_SELECTION when a maintained mechanism was introduced, e.g.:

```text
TOOL_SELECTION:
- operation: classify repo inventory
- implementation chosen: Python module + tests
- existing alternatives inspected: tools/inventory.py
- why this choice is durable: cross-platform, structured JSON, tested
- verification: pytest::test_inventory_classification
```

This keeps ceremony minimal while still making your Python/PowerShell policy visible at the moments that matter.

***

**Assumptions & uncertainty**

- FACT (high confidence): AGENTS.md is the right place for concise, global guidance; plugin/skill + router are the right places for detailed policy and activation logic.[2][3][4][1][5]
- CONSENSUS (medium‑high): Python is preferred for cross‑platform, structured logic and JSON handling; PowerShell is preferred for Windows‑native operations on Windows 11.[7][9][8][10]
- SPECULATION (medium): The exact file paths (`P:\…`) and router implementation details depend on your local Claude/Open Code setup; I’m assuming a plugin‑based architecture and AGENTS.md support similar to current agent tools.[3][4][1][2]

A concrete next step is: implement the concise invariant in `P:\AGENTS.md`, stub the governance plugin with the decision matrix and a small set of tests, and add one router trigger (“before creating new helpers”) that calls the tool‑selection skill and forces the `tool_choice` structure to be filled.

What’s your current router implementation stack for Claude Code/Open Code on Windows (e.g., MCP, custom Python/TS gateway, something else)? That will determine the cleanest place to insert the tool‑selection skill and advisory audit.  

## Human

what prompt should I give to claude code?

## Assistant

For Claude Code, the “prompt” you give should be a thin, targeted directive that activates your canonical tool‑selection policy and governance plugin when tool choice is consequential, not a giant policy block pasted every time.[1][2][3][4][5]

## 1. Your default Claude Code system-style prompt

When you start a Claude Code session in this workspace, a good top‑level instruction is:

> You are a coding agent working in a Windows 11 environment with Python and PowerShell 7 available. Apply the workspace’s canonical tool‑selection invariant from `P:\AGENTS.md`: choose tools by the operation, not by the host OS. Prefer native agent tools for repository search and file inspection, existing tested repository utilities for established workflows, Python for structured reusable cross‑platform logic, PowerShell only for Windows‑native responsibilities, and shell pipelines only for small disposable operations. Do not duplicate existing utilities or embed maintained policy in ad hoc shell pipelines.

This tells Claude Code where the policy lives (AGENTS.md) and summarizes the invariant at a level that AGENTS.md guidance suggests is effective: short, consistent rules that agents actually follow.[2][3][4][5][1]

You can keep this as your “workspace instruction” or “project preamble” rather than retyping it.

## 2. The routing prompt when tool choice is about to matter

The more important prompt is what your router injects when Claude Code is about to:

- create a new `.py`, `.ps1`, `.sh`, `.js`, or wrapper;  
- choose between Python vs PowerShell vs Bash vs Node;  
- introduce a maintained runtime path.

In those moments, inject something like:

> Before you choose a runtime or create a new helper, apply the canonical tool‑selection policy owned by the governance plugin’s `tool-selection` skill.  
> 1. Decide whether the operation is best served by native agent tools, an existing project utility, Python, or PowerShell.  
> 2. Use Python for structured, reusable, deterministic, or cross‑platform logic.  
> 3. Use PowerShell 7 only for Windows‑native responsibilities such as ACL inspection, environment scopes, registry, and thin launchers.  
> 4. Do not embed maintained logic into long shell or PowerShell pipelines; instead propose a small maintained script when appropriate.  
> 5. Fill a `tool_choice` block explaining:  
>    - operation, selected_tool, alternatives_considered, one_time_or_maintained, existing_utility_checked, owner, callers, failure_behavior, test_path.

This is aligned with best practices you see in “tool I wish existed” and “folder audit” prompts: precise instructions, concrete fields to fill, and a focus on durable automation rather than ad hoc commands.[6]

## 3. A concrete prompt you can paste right now

If you want a single prompt you can immediately paste into Claude Code in this Windows 11 workspace, here is a combined version:

> Context:  
> - Windows 11 host with Python and PowerShell 7 available.  
> - Workspace has a canonical tool‑selection invariant in `P:\AGENTS.md`.  
> - A governance plugin exposes a `tool-selection` skill with the detailed decision matrix.
>  
> Job:  
> - When proposing or implementing any new maintained helper (`.py`, `.ps1`, `.sh`, `.js`, launcher, or wrapper), explicitly choose the tool according to the policy and justify it.  
>  
> Rules:  
> - Choose tools by the operation, not the host OS.  
> - Prefer native agent tools for repository search and file inspection.  
> - Prefer existing tested repository utilities for established workflows.  
> - Prefer Python for structured, reusable, deterministic, or cross‑platform logic.  
> - Use PowerShell 7 only for Windows‑native responsibilities (ACLs, registry, environment scopes, scheduled tasks, thin Windows launchers).  
> - Use shell pipelines only for small disposable operations.  
> - Do not encode maintained policy in ad hoc shell pipelines.  
> - Do not create a maintained helper for a one‑time search.  
>  
> When you decide to add a maintained helper or runtime path, first output:
> ```yaml
> tool_choice:
>   operation:
>   selected_tool:
>   alternatives_considered:
>   one_time_or_maintained:
>   existing_utility_checked:
>   owner:
>   callers:
>   failure_behavior:
>   test_path:
> ```
> Then explain in 3–5 sentences why this choice is durable on Windows 11 and how it aligns with the canonical policy.

This prompt is intentionally compact but explicit, similar in style to proven “tool/script” prompts that get good results with Claude Code.[6]

If you tell me how you currently inject instructions into Claude Code (manual, AGENTS.md only, MCP router, or VS Code extension config), I can adapt this into the exact format that slot expects.

## Human

um, nothing is implemented yet.  how do I inject instructions?  I type on the keyboard or I shout at the monitor, but that doesn't work very well.

we do have claude.md but it gets ignored often.  we do have mcps but no mcp router.  what's that?

we have hooks, hundreds of hooks.

## Assistant

You don’t need to shout at the monitor; you need to wire your rules into Claude Code’s config and hooks so they show up as system‑level instructions instead of fragile chat text. On Claude Code today, the durable way to “inject instructions” is via CLAUDE.md plus lifecycle hooks, not just what you type in the chat box.[1][2][3][4]

## 1. What a “router” is in this context

Given what you described (MCP servers but no router, hundreds of hooks), “router” here is conceptual rather than a special product:

- MCP: lets Claude Code call external tools via Model Context Protocol.[3]
- Hooks: event‑driven scripts or prompts that fire at specific lifecycle events (before a tool runs, when a file changes, when the session starts).[4][1][3]
- A **router** is just: “a hook (or small set of hooks) that decides when to inject which instructions or call which MCP tools based on the event and context”.

You already have the primitives (hooks + MCP); the router is a pattern:

- When `PreToolUse` fires and tool choice is about to matter, call a governance MCP tool or inject a short directive.  
- When `SessionStart` fires, inject your high‑level invariant.  
- When a new helper file is about to be created, run a hook that asks for the `tool_choice` structure.

No new vendor feature required; you implement this in `.claude/settings.json` (project) or `~/.claude/settings.json` (global).[1][3][4]

## 2. Why CLAUDE.md gets ignored, and how to fix that

The current ecosystem is pretty frank: CLAUDE.md is helpful, but its instructions are not treated as hard rules and may be sidelined or compacted, especially when they’re long or generic.[5][6][2][7]

Key points from recent guides and bug threads:

- CLAUDE.md is read, but its content often arrives with “this may or may not be relevant” framing; it’s a suggestion, not a contract.[6][2]
- Long, dense CLAUDE.md files get truncated or semantically down‑weighted; short, concrete instructions fare better.[8][2][6]
- Hooks output shows up as clean, high‑priority “system‑style” messages without disclaimers, which agents respect more.[6][3][4]

So the fix is:

- Keep CLAUDE.md small and point it at the canonical policy file (AGENTS.md or similar).[2][8]
- Move “Claude must always…” and enforcement logic into hooks and skills, not CLAUDE.md.[3][4][6]

Example CLAUDE.md pattern (first line pointer is documented in AGENTS.md spec):

```markdown
# CLAUDE.md

@import ./AGENTS.md

- Claude Code should apply the tool-selection invariant defined in AGENTS.md.
- For detailed tool decision logic, use the governance plugin's `tool-selection` skill.
```

That keeps CLAUDE.md light while making sure the real rules live in AGENTS.md and in your governance skill.[8][2]

## 3. How to “inject instructions” in practice

There are three durable channels you can use right now, keyboard only, no shouting.

### A. AGENTS.md / CLAUDE.md for baseline guidance

Per current AGENTS.md spec and best‑practice articles, put concise, global rules in AGENTS.md at the repo root (and optionally per package).[9][10][2][8]

For tool‑selection, your AGENTS.md might say:

```markdown
# AGENTS.md

Tool-selection invariant:

- Choose tools by the operation, not the host OS.
- Use native agent tools for repo search and file inspection.
- Use existing tested utilities before making new helpers.
- Use Python for structured, reusable, deterministic, or cross-platform logic.
- Use PowerShell 7 for Windows-native administration and runtime integration.
- Use shell pipelines only for small disposable operations.
```

Then CLAUDE.md imports it and adds Claude‑specific hints as above.[2][8]

This gives you a shared, cross‑agent source of truth; but as you’ve noticed, it’s not enough on its own. That’s where hooks come in.

### B. SessionStart / UserPrompt hooks for “always‑on” reminders

Hooks live in JSON config, and they can run a **prompt** or **command** on events like `SessionStart` or `UserPromptSubmit`.[4][1][3]

A simple project‑level hook file (committed) in `.claude/settings.json` might include:

```json
{
  "hooks": [
    {
      "event": "SessionStart",
      "type": "prompt",
      "name": "tool-selection-invariant",
      "prompt": "You are a coding agent on Windows 11 with Python and PowerShell 7. Apply the tool-selection invariant from AGENTS.md: prefer native repo tools and tested utilities, use Python for structured cross-platform logic, and use PowerShell only for Windows-native responsibilities."
    }
  ]
}
```

This yields a clean, system‑style reminder every time Claude Code starts a session in that repo, without you typing it.[6][3][4]

You can add a `UserPromptSubmit` hook if you want a very short reminder on every prompt, but usually `SessionStart` + PreToolUse is enough.

### C. PreToolUse / FileCreated hooks as your “router”

To turn your hundreds of hooks into an actual router, add one or two **PreToolUse**‑style hooks that only fire when tool choice is consequential.[3][4]

You can configure a hook to:

- Check the tool Claude is about to run (Python, PowerShell, Bash).  
- If it’s about to create a maintained helper (`.py`, `.ps1`, etc.), run a governance prompt or call an MCP tool that enforces your policy.

Example (conceptual) hook snippet:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "type": "prompt",
      "name": "tool-selection-governance",
      "match": {
        "tool": ["python", "powershell", "bash"]
      },
      "prompt": "Before proceeding, decide if this operation should use native repo tools, an existing utility, Python, or PowerShell 7. Use Python for structured cross-platform logic and PowerShell only for Windows-native responsibilities. If you are introducing a new maintained helper, first output a `tool_choice` YAML block with operation, selected_tool, alternatives, one_time_or_maintained, existing_utility_checked, owner, callers, failure_behavior, and test_path."
    }
  ]
}
```

Under the hood, Claude Code will:

- Fire this hook before running the tool.  
- Show your governance prompt as a system reminder.  
- Let the LLM respond with the `tool_choice` block and justification before continuing.[4][3]

This is your “router”: it injects the tool‑selection policy only when the event and tool match certain criteria, not on every turn.

## 4. Where MCP fits (even without a router yet)

You already have MCP servers; you just don’t have a *routing policy* that decides when to call them.

Hook handler types include an `mcp_tool` handler that can call a connected MCP server instead of a prompt.[3][4]

So you can:

- Implement a governance MCP server with a `tool-selection` tool that:
  - Accepts the intended operation and candidate tools.  
  - Returns the recommended tool plus a validated `tool_choice` structure.  
- Wire a `PreToolUse` hook with `type: "mcp_tool"` that calls this MCP tool whenever Claude is about to create a new helper or run Python/PowerShell.

The hook config would look something like:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "type": "mcp_tool",
      "name": "tool-selection-mcp",
      "server": "governance",
      "tool": "tool-selection",
      "match": {
        "tool": ["python", "powershell"]
      }
    }
  ]
}
```

Now your MCP server *is* the router logic; Claude Code calls it at the right lifecycle points, no extra typing required.[11][4][3]

## 5. How to start from “nothing is implemented”

Given your baseline (CLAUDE.md often ignored, many hooks, MCP servers but no router), a minimal sequence that fits your earlier design:

1. **Add a concise tool‑selection invariant to AGENTS.md** at the repo root (or `P:\AGENTS.md`). Keep it under ~10 lines.[9][8][2]
2. **Point CLAUDE.md at AGENTS.md** and keep CLAUDE.md short (imports + Claude‑specific hints).[8][2]
3. **Add a `SessionStart` hook** in `.claude/settings.json` that injects a short version of the invariant as a prompt.  
4. **Add a `PreToolUse` hook** that fires only for Python/PowerShell tools and either:
   - Injects a governance prompt with the `tool_choice` YAML requirement, or  
   - Calls a governance MCP tool that returns the decision and justification.  
5. **Later, add an audit hook** (`PostToolUse` or `ConfigChange`) that scans for suspicious patterns (long PowerShell pipelines, duplicate helpers) and emits findings, but doesn’t hard‑block yet.[4]

This gives you real, durable “instruction injection” without needing an extra framework.

***

If you’re up for it, I can draft concrete JSON for a `SessionStart` and `PreToolUse` hook that match your Windows 11 + Python + PowerShell 7 policy, assuming you want project‑committed hooks in `.claude/settings.json` rather than user‑global ones in `~/.claude/settings.json`.

## Human

how do we not waste tokens wiht mcp servers?  how do we make hooks intelligent and not constantly shoout at the llm?

Are there existing popular repos that are maintained wiht these patterns?

## Assistant

You keep MCP and hooks cheap and intelligent by minimizing what’s *always* loaded, consolidating tools, and making hooks event‑driven and conditional instead of chat spam. There are already repos and patterns in the wild doing this for Claude Code, AGENTS.md, and MCP.[1][2][3][4][5][6][7][8][9][10]

## 1. Not wasting tokens with MCP servers

FACT: Every connected MCP server contributes its tool schemas to the context; many servers with many verbose tools can add tens of thousands of tokens per turn.[6][11][1]

Concrete practices from recent guides and tools:

- Load fewer servers by default.  
  - Audit your `~/.claude/settings.json` and project `.claude/settings.json` `mcpServers` section; keep only what you use in almost every project, and move niche servers into project‑specific configs.[3][6]
  - Tools like “McPick” exist purely to toggle servers on/off before sessions; they recommend enabling only the relevant ones per project.[3]

- Consolidate tools inside each server.  
  - Instead of 20 small tools, expose a few parameterized tools that handle related operations; this shrinks tool schemas and descriptions.[2][4][6][3]
  - Keep tool descriptions short, one sentence, and move long documentation into external docs linked by URL.[7][6][3]

- Prefer skills and hooks over MCP when possible.  
  - Several “Claude Skills vs MCP” articles show that skills (local capabilities) can provide routing and governance with much less per‑turn overhead than remote MCP tools.[4][7]
  - Use MCP servers as data gateways (e.g., fetch a structured dataset or graph), and then let Claude Code script locally with Python/PowerShell, rather than exposing dozens of fine‑grained tools.[7]

- Use project‑level configurations and focused agents.  
  - Best‑practice guides recommend per‑project `.claude/settings.json` with only the servers needed for that codebase, not a global “everything ever”.[6][7]
  - Some patterns use separate agents (or subagents) with minimal tool sets for specific tasks, instead of one omni‑agent with all tools loaded.[6][7]

- Monitor and trim over time.  
  - Token‑overhead articles suggest periodically inspecting token usage and connecting spikes to new MCP servers or tools; culprits are often a few very verbose servers.[12][6]

Consensus: treat MCP as a *sharp tool*: few servers, few concise tools, and project‑specific configs, rather than a global “load everything” strategy.[4][3][7][6]

## 2. Making hooks intelligent instead of “shouting”

Right now your hooks are your laws; prompts are suggestions. The way to avoid “constant shouting at the LLM” is:[5][9]

- Prefer **non‑blocking hint hooks** for advisory feedback.  
  - Guides describe “hint hooks” that only emit a short message when something looks off (e.g., “this could use the existing `scan.py` script”) and otherwise stay quiet.[9][7]
  - Use these for tool‑selection advice, code style hints, or “you’re reinventing an existing helper”, not for every action.

- Use **blocking hooks** only for objective failures.  
  - Articles on enforcement emphasize that hooks should hard‑block only when something is clearly wrong: destructive actions without confirmation, missing tests, no owner, etc.[8][5][9]
  - For tool selection, that means blocking “new helper with no owner or tests” rather than “Python vs PowerShell choice I don’t like”.

- Make hooks conditional and scoped.  
  - Hook references show you can match by event, tool name, file path, etc.; use this to avoid firing on every turn.[8]
  - Examples:
    - `PreToolUse` hooks that only trigger when the tool is `python`, `powershell`, or when a new file is being created.  
    - `ConfigChange` hooks that scan for new helpers and then prompt for a `tool_choice` block only in those cases.

- Keep hook prompts very short.  
  - “Rules ignored” posts and videos show that long hook prompts and CLAUDE.md content get truncated or down‑weighted; short, precise instructions fare better.[13][5][9][7]
  - For governance, your hook message might be a single sentence plus a YAML skeleton, not a page of policy.

- Use hooks to **run code**, not just send text.  
  - Strong enforcement patterns run shell or Python in hooks (linting, tests, diff analysis) and then only show the LLM a concise result (“blocked: no test for new helper” or “warning: duplicate script detected”).[5][9][8]
  - That reduces token use and avoids repeating long policy text; the hook computes and sends just a small result.

Speculation (medium confidence): for your environment with “hundreds of hooks”, a near‑term win is to tag them by severity (hint vs guard vs gate), and have your router only send text to the LLM for hint hooks and concise failure messages for gates, instead of sending full policy every time. This matches patterns described in advanced Claude Code hook guides.[9][7][8]

## 3. Repos and patterns already using these ideas

FACT: There are curated lists and repos that show exactly how people are using AGENTS.md, CLAUDE.md, hooks, skills, and MCP in production‑like setups. A few relevant categories:[14][10][7]

- **Awesome Claude Code lists**  
  - The `awesome-claude-code` list includes:  
    - linters/LSP that validate AGENTS.md, CLAUDE.md, SKILL.md, hooks, and MCP configs.  
    - orchestrators that coordinate agents and tools with attention to cost and security.[10]
  - These repos often embed token‑efficiency strategies (minimal tool sets, short descriptions, project‑level configs).

- **Token-optimizer MCP servers**  
  - There is at least one “token-optimizer-mcp” repo focused on reducing context overhead via caching, compression, and tool intelligence.[2]
  - Patterns here include:  
    - Tool response caching at the MCP layer.  
    - Serving minimal, structured data instead of verbose text.  
    - Deliberately small schemas and descriptions.

- **Context-efficient MCP usage guides**  
  - Posts like “Optimising MCP Server Context Usage in Claude Code” and “Claude Skills vs MCP” walk through real measurements and illustrate project‑level config, tool consolidation, and description trimming.[3][4][6]
  - These are practical, maintained write‑ups, not just conceptual blog posts.

- **Hook-focused enforcement repos**  
  - Blog posts and videos showing “Hooks as laws” build production hooks that:  
    - Run tests or analyses via code.  
    - Only speak to the LLM when necessary.  
    - Treat hooks as the primary enforcement layer, not CLAUDE.md.[5][7][9]

Consensus: the ecosystem is converging on “AGENTS.md + CLAUDE.md for guidance, hooks for enforcement, MCP as slim data gateways, skills for local intelligence, and project‑level configs for cost control.”[1][10][4][7][8][9][5][6]

***

Assumptions & confidence:

- FACT: MCP tool schemas and descriptions contribute to token use; fewer, smaller tools and project‑level configs reduce overhead.[11][1][4][3][6]
- CONSENSUS: Hooks are the only reliable enforcement channel; prompts and CLAUDE.md content get ignored more easily.[13][7][9][5]
- SPECULATION: How many of your existing hooks are hint vs gate vs guard isn’t known; refactoring them into a severity‑layered router will likely help, but the exact split depends on your current files.

A concrete next step for you: pick one repo, add a lean `.claude/settings.json` that loads only the MCP servers you actively use there, add a single `PreToolUse` hook that calls a governance MCP tool or skill for Python/PowerShell choices, and log the token usage before/after. That will give you direct evidence of the impact.

Would you like me to sketch a minimal `.claude/settings.json` that reflects your Windows 11 + Python + PowerShell + tool‑selection policy and keeps MCP servers lean for one project?

## Human

I've found that advisory hooks are ignored.

## Assistant

You’re running into the current reality: advisory anything (CLAUDE.md, “please do X”, advisory hooks) is treated as theatre much of the time. If you truly care about a behaviour, you need the hook to *mechanically* block or gate the action, not just emit advice into the token soup.[1][2][3][4][5][6][7][8]

## 1. What “advisory hooks are ignored” actually means

FACT: Claude Code distinguishes between hooks that change the control flow (blocking / gating) and hooks that only emit text or JSON feedback.[9][4][5][7][1]

- Advisory hooks:  
  - Exit with success, produce a message, and let the tool call proceed.  
  - The LLM may read or ignore the advice; it competes with all other context.[2][3][1][9]
  - Empirical reports show ~40–60% compliance at best.[6]

- Blocking / gating hooks:  
  - Return a specific exit code or JSON decision that *denies* or *modifies* the action.  
  - Claude Code itself enforces the decision; the LLM doesn’t get to “choose” whether to obey.[4][5][1][9][2]

One practitioner’s write‑up puts it bluntly: “Blocking hooks: ~95% effective. Advisory hooks: ~40–60%. Blocking beats advising. If it matters, exit 2; otherwise accept the variance.”[6]

So your experience is not a bug in your setup; it matches what other teams are seeing with advisory hooks and CLAUDE.md‑style rules.[10][3][11][6]

## 2. When to stop trying advisory and move to blocking

Given your governance goals (tool selection, PowerShell vs Python, avoiding new helpers without owners/tests), you’re talking about **behaviours that matter**:

- Creating a new maintained helper.  
- Choosing Windows‑only tooling for cross‑platform logic.  
- Bypassing existing repo utilities.  

Per hook guides and case studies, those belong in blocking hooks, not advisory:[3][12][5][7][2][4]

- Use **blocking PreToolUse hooks** for:  
  - “New helper with no owner/test” → deny tool call.  
  - “Tool selection violates invariants (e.g., PowerShell for cross‑platform JSON logic)” → deny and require re‑selection.

- Use **PostToolUse advisory hooks** for:  
  - Quality hints, style suggestions, and non‑critical improvements.  

The pattern that’s emerging in the ecosystem:

- Hooks are **laws** (deterministic control layer).[5][2][3]
- CLAUDE.md / AGENTS.md and advisory hooks are **instructions and hints**; they drive soft behaviour but not guarantees.[13][14][10][6]

Given that your advisory hooks are ignored, the practical step is to promote the critical ones to blocking/gating.

## 3. How to turn your tool-selection policy into a blocking hook

Hook references and guides show how PreToolUse hooks can deny tool calls based on JSON input and exit behaviour.[7][1][9][2][4][5]

At a high level:

1. Configure a `PreToolUse` hook in `.claude/settings.json` that runs whenever Claude Code is about to call Python or PowerShell.  
2. Have the hook script:
   - Read the event JSON (tool name, arguments, target file).  
   - Decide whether the operation violates your tool‑selection invariant.  
   - If OK: exit with success (allow).  
   - If not OK: output a small JSON object with a `deny` decision and a short reason, and exit with the blocking status the docs describe.[1][9][4]

This makes the decision deterministic:

- If the hook says “deny”, Claude Code does not run the tool.  
- The LLM receives a concise message: “Tool call denied: new helper has no owner/test; choose Python vs PowerShell according to policy and fill tool_choice.”  

Hook guides emphasize a few mechanical points to get this right:

- stdout must contain only JSON when you want Claude Code to consume it; no mixed text.[9][5][1]
- Exit codes matter; Claude Code only processes JSON on specific success codes and treats others as failures or ignored content.[1][9]
- HTTP hooks can’t block with 4xx/5xx alone; you must return a 2xx with a deny decision field.[7]

Once you do this, “advisory” becomes a post‑fact review and logging; the actual gate is blocking.

## 4. What to do with advisory hooks you still want

You don’t have to delete advisory hooks; you just need to re‑scope them.

Guides on production patterns suggest:

- Use advisory hooks for **feedback loops** and **observability**, not policy enforcement.[12][2][5][7]
  - Example: a PostToolUse hook that runs lint or tests and emits a message if they fail, but doesn’t stop the action (because you want a human to decide).  
  - Example: logging telemetry about tool choices and new helpers.

- Keep advisory outputs tiny and specific.  
  - One sentence plus a link or reference, not a long policy dump, to reduce token bloat and keep messages legible.[15][16][5][7]

- Accept 40–60% compliance as the design, not a bug.  
  - The “Advisory is theater” formulation is meant literally: advisory is valuable, but not a guarantee; treat it like code review comments, not a compiler.[6]

Given your goals, you might:

- Keep your tool‑selection *explanations* advisory (the LLM writes a tool_choice justification).  
- Make the existence of an owner and test path **non‑negotiable** via blocking hook.

***

**Assumptions & confidence**

- FACT (high confidence): Blocking/gating hooks can deterministically deny tool calls or actions; advisory hooks and CLAUDE.md are not guaranteed to be followed.[2][3][4][5][9][7][1]
- CONSENSUS (medium‑high): If a behaviour really matters (safety, governance, tool‑selection), it belongs in a blocking hook, not in advisory text.[3][12][4][2][7][6]
- SPECULATION (medium): Some of your advisory hooks may be misconfigured (exit codes, JSON shape, event names), which could further reduce their impact; we’d need to inspect your actual hook scripts to be sure.[5]

A concrete next step: pick one critical governance rule—e.g., “no new maintained helper without owner and test”—and convert its hook from advisory to blocking for Python/PowerShell tool calls, following the PreToolUse doc semantics. Once that’s stable, you can decide which other “advisory” hooks deserve promotion.

Would you be willing to share (or summarize) one of your current advisory hooks so we can design its blocking variant in detail?

## Human

I don't think your popular maintained repos were really directly connected to the question about Python, PowerShell, and intelligently enforcing it.

## Assistant

You’re right to push on that; the earlier repos were more about “Claude Code ecosystem” than “Python vs PowerShell governance on Windows 11.” Let’s be precise about how to enforce your Python/PowerShell policy intelligently, and what’s actually out there that’s close to what you want.[1][2][3][4][5]

## 1. What you’re actually trying to enforce

Restating your goal in concrete terms:

- On Windows 11, Claude Code (and Open Code) should:
  - Use **Python** for structured, reusable, deterministic, cross‑platform logic and JSON/data processing.  
  - Use **PowerShell 7** only for Windows‑native responsibilities: ACLs, env scopes, registry, scheduled tasks, thin Windows launchers, etc.[2][3][4]
  - Prefer native agent tools (rg, glob, read) and existing repo utilities before inventing new helpers.  
- This needs to be enforced at the **tool‑call and helper‑creation level**, not just through advisory text.

That’s subtly different from generic “Claude Code hooks” repos; it’s a **policy about which runtime is allowed for which operation**.

## 2. The enforcement mechanism that actually fits this

From the hooks docs and production patterns, the piece that matches your need is:

- A **PreToolUse hook** that:
  - Sees which tool Claude is about to call (`python`, the PowerShell tool, bash, etc.).[6][7][1]
  - Sees the target file(s) and arguments.  
  - Applies your decision rules: “is this a Windows‑native operation or cross‑platform logic?”  
  - Either **allows** the call or **denies** it with a short reason.[8][9][1][6]

For example, for Windows 11 + native PowerShell tool support:

- Claude Code exposes a **PowerShell tool** that can run cmdlets directly when you set `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.[10][2]
- PreToolUse hooks can intercept such tool calls, read their JSON, and gate them.[7][1][6]

So your “intelligent enforcement” is:

- A hook that **blocks** PowerShell when the operation is cross‑platform JSON/data logic, and **blocks** Python when the operation is Windows‑native admin.  
- The LLM sees a concise explanation and can retry with the right runtime.

That’s much closer to what you want than the generic “auto‑test” hooks in most repos.

## 3. Patterns and examples actually about Python + PowerShell on Windows

There isn’t (yet) a single famous OSS repo that says “here is the canonical Python/PowerShell governance policy for Claude Code on Windows 11.” That’s the gap you’re trying to fill. But there are **pieces** that are directly relevant:

- **Python interpreter sanity on Windows 11 (Claude Code & shells)**  
  - A maintained gist walks through making `python3` resolve correctly across PowerShell, cmd, Git Bash, etc., with explicit PowerShell shims and detection.[4]
  - It treats “agent‑proof” Python resolution as a separate, enforceable concern: fix the shell environment so agents can’t hit Store stubs.  
  - This shows that people are already codifying Windows‑specific Python rules in scripts, but not yet as hooks.

- **Using Claude Code in a PowerShell project**  
  - A PowerShell‑focused guide recommends:  
    - A CLAUDE.md at the root describing runtime targets and conventions.  
    - A PowerShell module **skill** in `.claude/skills/` that enforces project‑wide PowerShell rules.[3]
  - That’s very similar to your idea of a plugin‑owned skill for tool selection; it’s just scoped to “PowerShell module quality” rather than “Python vs PowerShell choice.”

- **Any‑shell agents with AGENTS.md & hooks**  
  - An “anywhere‑agents” project uses AGENTS.md plus shell bootstrap scripts and notes that Claude Code’s PreToolUse hooks still gate outer MCP calls.[5]
  - Again, not exactly your policy, but evidence that AGENTS.md + hooks is a live pattern for cross‑shell governance.

- **PowerShell support and Windows workflows in Claude Code**  
  - Recent release notes explicitly call out PowerShell tool support on Windows and improved MCP server management.[2]
  - The messaging there reinforces: PowerShell is a first‑class tool, not a hacked‑in shell; it’s meant for Windows‑native operations.

Consensus: you’re operating in a space that’s only partially charted—people have solved “Python resolution on Windows” and “PowerShell module conventions” and “AGENTS.md + hooks”, but not a full cross‑runtime tool‑selection policy baked into hooks.

## 4. How to make enforcement “intelligent” instead of brute

Based on hook docs and complete guides:

- Hooks see **structured JSON**, not just free text.  
  - PreToolUse hooks receive tool metadata and arguments; you can inspect these to infer the operation category (file type, flags, path).[1][6][7]
- You can encode **operation categories** mechanically:  
  - If the tool target is a `*.json` or `*.py` and the command includes parsing, diffing, or classification operations → treat as logic/JSON task.  
  - If the tool target is ACLs, registry keys, env variables, `C:\Windows\…` paths, or system services → treat as Windows‑native admin.[3][4][10][2]

So an “intelligent” hook can:

1. Map the tool call to an operation category using file types and arguments.  
2. Apply your matrix:
   - JSON/data/logic → must use Python.  
   - Windows ACL/env/registry/launcher → must use PowerShell.  
3. Allow or deny, and emit a short reason when denying.

This is enforcement by **rules and categories**, not by “block PowerShell always.”

If you later add a governance MCP server, that server can own the categorization and decision logic; the hook just calls it and enforces its result, which matches your “plugin‑owned skill” idea.[11][3]

## 5. Why advisory versions of this get ignored

You already noticed, and the public write‑ups confirm: “advisory hooks” and CLAUDE.md content get treated as suggestions; the LLM frequently does something else.[12][13][14][6][1]

Given Python vs PowerShell governance is core to durability, those rules belong in:

- **Blocking PreToolUse hooks** for tool calls.  
- **Blocking hooks on file creation** for helpers (no `.py` or `.ps1` if policy violated).  

Advisory text can still explain why, but the enforcement is mechanical.

***

FACT (grounded): Claude Code’s hook system can see tool calls and block them based on deterministic logic, including on Windows and for PowerShell tools.[6][7][8][1][2]
CONSENSUS: Python is preferred for structured/cross‑platform logic, PowerShell for Windows‑native operations; using hooks to enforce this per operation is sensible for a Windows 11 environment.[4][10][2][3]
SPECULATION: There isn’t yet a widely‑known repo that has exactly your “tool‑selection invariant + governance skill + hooks + telemetry” pattern—if you build it, you’re likely ahead of the curve rather than contradicting best practice.

A practical next step aligned with this: in one Windows‑11 project, add a single PreToolUse hook that (a) categorizes operations from tool metadata, (b) blocks PowerShell for cross‑platform JSON/logic tasks and blocks Python for Windows‑ACL/admin tasks, and (c) logs decisions for later refinement. Then see how often that gate fires compared to your current advisory attempts.
