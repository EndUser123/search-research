---
title: "I'd like a deep research prompt to use to find out how to fix Claude Codes Compaq forgetting context issue.  Here's what"
date: "2026-03-25"
mode: "COPILOT"
uuid: "e0cdb347-c189-48a7-9859-d7f21839c4c8"
entry_count: 2
---

## Human

I'd like a deep research prompt to use to find out how to fix Claude Codes Compaq forgetting context issue.  Here's what I have so far. Can you improve it?

 Please research:
  1. How do AI coding assistants distinguish "user wants to resume work" from "user is asking a new question" after
  compaction? What intent signals exist?
  2. What patterns exist for stale plan detection — distinguishing plans that were completed/shelved vs still active?
  3. For schema versioning in agent state files: forward/backward compatibility strategies when hook schemas evolve across
  versions?
  4. The PostToolUse hook stdout injection pattern — how does it compare to PreToolUse blocking for confirmation gates?

## Assistant

Here’s a tightened, more *research-focused* version of your prompt that channels your system‑design instincts and explicitly pushes for mechanistic/implementation‑level answers (tools, patterns, tradeoffs):

***

**Research Prompt:**

> Conduct a deep technical investigation into the design and behavior of AI coding assistants—especially **Claude Code**—around **context‑compaction boundaries** and **state continuity**. Frame your answers concretely around architectures, hooks, and practical patterns, not just high‑level concepts.
>
> 1. **Intent signaling after context compaction**  
>    - How do modern AI coding assistants (including Claude Code, Cursor, Windsurf, GitHub Copilot X, etc.) distinguish “user wants to resume previous work” from “user is starting a new, unrelated question” *after* history has been compacted or truncated?  
>    - Enumerate the **intent signals** they rely on (e.g., file paths opened, last‑edited ranges, dialogue‑level markers like “continue”, comment tags, project‑state diff, CI/IDE signals, etc.) and list which are *observable* vs *opaque* to the user.  
>    - For Claude‑specific workflows: given **compacted chats / sliced histories**, what observable patterns can a user or toolchain engineer follow to *re‑inject* or *re‑establish* continuity (e.g., custom comment tags, scratch files, workspace metadata)?
>
> 2. **Stale plan detection and lifecycle**  
>    - What patterns exist for **detecting stale plans** in agent‑based coding assistants:  
>      - Heuristics for when a plan should be considered **completed**, **abandoned**, or **shelved** (e.g., matching file edits, git diff, test outcomes, tool‑use sequences, explicit user confirmation).  
>      - How agents track **plan provenance** (which plan led to which file ranges, branches, or reviewable diffs) and whether they maintain a **plan graph** or only a flat log.  
>    - How do existing systems (e.g., Cursor, Devin‑like tools, GitHub Copilot agents) handle **plan versioning** when the user edits generated code, then asks “continue” or “do this instead”?  
>    - Propose concrete hooks or metadata structures (e.g., YAML/TOML headers in scratch files, `.meta` files, git tags/ref‑like markers) that a user or framework could adopt to help agents *reliably* detect whether a prior plan is still active or stale.
>
> 3. **Schema versioning in agent state files**  
>    - How do **multi‑agent / tool‑use frameworks** and **LLM agents** manage schema evolution in their **internal state files** (JSON, YAML, protobuf, etc.), especially when hook APIs or tool contracts change across versions?  
>    - Enumerate practical **forward‑compatibility** and **backward‑compatibility** strategies:  
>      - Versioning fields (e.g., `agent_version`, `schema_version`).  
>      - Optional vs required fields, defaults, and fallback modes.  
>      - Migration strategies: out‑of‑band scripts, inline migrations on load, shadow fields, etc.  
>    - For **Claude Code** or similar toolchains, how might schema evolution affect long‑running projects if the agent’s state/schema is persisted in git‑tracked or workspace files?  
>    - Propose a minimal schema‑versioning pattern (e.g., a small `.agentstate` file per workspace) that balances expressiveness, safety, and tooling‑agnostic readability.
>
> 4. **Post‑ToolUse hook stdout injection vs Pre‑ToolUse confirmation gates**  
>    - Analyze the **PostToolUse hook stdout injection pattern** (where the agent’s tool output or tool log is injected into the model’s context after the tool call) versus **Pre‑ToolUse confirmation gates** (where the agent must get explicit user approval or validation before executing a tool).  
>    - Compare on:  
>      - **Safety** (risk of hidden or mis‑interpreted actions).  
>      - **Context fidelity** (whether the model can “reason” about the *actual* effect of the tool use).  
>      - **Compaction behavior** (which pattern survives window‑slicing or compaction better).  
>      - **Debuggability** for the user (e.g., can they replay or inspect the exact sequence).  
>    - Where are these patterns used in practice (e.g., in GitHub Copilot, Cursor, Claude Code’s hook system, or DIY MCP‑based agents)?  
>    - Suggest a hybrid pattern you could implement or configure in a Claude Code–style workflow (e.g., “pre‑gate on risky operations, post‑inject logs for safe ones”) and outline its schema and control‑flow.
>
> For all questions, prioritize **current, concrete implementations** (e.g., released Copilot/Claude Code workflows, Cursor, MCP‑based agents, OSS agent frameworks) over speculative designs, and distinguish clearly between:
> - **Documented / implemented behavior**  
> - **Reasonable inference**  
> - **Speculative suggestion**
>
> When possible, reference:
> - Public documentation, RFCs, or GitHub repos  
> - Publicly shared architecture posts or blog diagrams  
> - Any observable hook or metadata patterns in existing toolchains  

***

If you want, I can also turn this into a **Claude‑specific “diagnosis + fix” prompt** that you can paste into Claude Code itself to analyze *your* current compaction‑forgetting setup and propose concrete hooks/metadata changes.

## Human

Yes, please.

## Assistant

Here’s a **Claude‑specific “diagnosis + fix” prompt** you can paste into Claude Code itself. It’s designed to make Claude analyze *your* current setup, connect the dots to compaction‑forgetting, and emit concrete, implementable hooks / metadata patterns instead of high‑level theory.[1][2][3][4]

***

### Claude‑focused “fix my context‑forgetting” prompt

> You are an expert Claude Code architect and systems designer.  
> I am using **Claude Code** in a multi‑step, project‑level coding workflow, and I’m running into **context‑compaction–induced forgetfulness**:  
> - After auto‑compaction, Claude Code forgets active plans, open files, and earlier instructions that I *explicitly* loaded (e.g., via `CLAUDE.md`, hooks, or long‑running subagents).[5][3][1]
> - I suspect this is due to how **compaction**, **tool‑use hooks**, and **state persistence** are layered, not just “more tokens”.[2][6][4]
>
> Your job is to:
> 1) **Diagnose** why Claude Code is losing context in *my* workflow, and  
> 2) **Propose a concrete, minimal, Claude‑Code–native** solution (hooks, `.md` patterns, MCP‑side state, or repo‑level metadata) that mitigates this.
>
> ---
>
> **1. Diagnose my current setup**
>
> Assume the following about my workflow:
> - I use **Claude Code CLI** in a git repo with:  
>   - `CLAUDE.md` for project‑wide instructions and “always‑on” context.[7][3]
>   - `UserPromptSubmit` and `PreToolUse` hooks for control‑flow and gating.[8][9][10]
>   - Optionally: MCP‑based agents or subagents for isolated tasks.[3][7]
> - I frequently:
>   - Open multiple files, edit in chunks, and run long tool‑use sequences.[11][4]
>   - Replay or “continue” after compaction or long pauses.[1][2]
> - I want Claude Code to:
>   - Remember which **plan** is active, which **files** are “in‑flight”, and which **decisions** were made, even after compaction.[12][3]
>
> Answer:
> - What are the **three most likely reasons** Claude Code is forgetting things after compaction in this setup?  
>   - For each, indicate whether it is **design‑wise lossy compaction behavior**, **user‑side pattern gap**, or **misuse of hooks / CLAUDE.md**.[6][2][1]
> - How does **CLAUDE.md** vs **hook‑injected context** behave across compaction boundaries? Which is safer for preserving “always‑on” state?[4][7][3]
> - When does **SessionStart** vs **UserPromptSubmit** vs **PostToolUse** stdout injection actually persist past compaction, and when does it get summarized away?[9][10][8]
>
> ---
>
> **2. Fix: “resumable plan” metadata pattern**
>
> I want Claude Code to:
> - Track **active plans** (e.g., “feature‑X refactoring”, “bug‑fix‑Y rewrite”) across messages and compaction.  
> - Distinguish **completed**, **shelved**, and **abandoned** plans.  
> - Re‑inject the minimal “plan header” when a user types `continue` or opens a relevant file.  
>
> Propose:
> - A **minimal schema** for a `.plan` file (YAML or JSON) or a `.md` header (e.g., `PLAN.md` or top‑of‑file comments) that encodes:
>   - Plan ID, title, status (`active`/`completed`/`shelved`/`abandoned`).[3][12]
>   - Associated files and ranges.  
>   - Last updated timestamp.  
> - How `UserPromptSubmit` or `SessionStart` hooks can:
>   - Read the plan file(s) on disk.[10][9]
>   - Decide which plan(s) are still relevant and inject a **short, Claude‑readable header** into context via stdout.[8]
> - How I can train myself to write `continue` prompts that trigger this detection (e.g., including plan IDs or file‑based signals).  
>
> ---
>
> **3. Hook strategy: PostToolUse vs PreToolUse**
>
> Analyze using **my workflow**:
> - `PreToolUse` hooks: they can **block** risky operations and add small amounts of context.[9][8]
> - `PostToolUse` hooks: they fire after a tool runs and can **inject stdout** as context.[8][9]
>
> Answer:
> - For a **resumable plan** workflow, is `PostToolUse` stdout injection or `PreToolUse` blocking more useful for preserving context and detectability after compaction? Why?[11][4][8]
> - Propose a **hybrid pattern**:
>   - `PreToolUse` for **confirmation gates** on destructive or irreversible actions, and  
>   - `PostToolUse` for **non‑destructive logging** (e.g., “Plan X applied to file Y, updated lines 10–15”) injected into Claude’s context.[10][9][8]
> - Write a **minimal Bash hook template** (with `jq`‑style parsing of stdin) for:
>   - A `PreToolUse` confirm‑or‑block hook.[9]
>   - A `PostToolUse` hook that writes a small context line summarizing what changed to stdout.  
> - How should that injected text be formatted so Claude can easily parse it vs other noise (e.g., delimiters, tags like `PLAN:` or `FILE:`)?[2][3]
>
> ---
>
> **4. Schema‑versioning and forward‑compatibility**
>
> Suppose my plan‑state files and hooks evolve over time:
> - New plan status codes, extra fields, changed tool contracts.  
> - New MCP agents or Claude Code versions.[7][11]
>
> For the **plan metadata** and **hook contracts** you propose:
> - Recommend a **minimal schema‑versioning strategy** (e.g., `schema_version: 1`) that supports:
>   - **Forward‑compatibility**: newer hooks can ignore extra fields;  
>   - **Backward‑compatibility**: older hooks can fall back on defaults when fields are missing.[4][7]
> - Suggest where this versioning lives (e.g., in `.plan` header, in hook configuration JSON, or in `CLAUDE.md` control section).  
>
> ---
>
> **Deliverables**
>
> 1. A **short diagnosis** of my compaction‑forgetting problem (3 main root‑cause buckets).[1][2][3]
> 2. A **concrete plan schema** (YAML/JSON) and **file‑layout** (e.g., per‑repo or per‑workspace).  
> 3. **Two minimal hook scripts** (Bash/Python) for:
>    - `PreToolUse` confirm‑or‑block on risky actions.  
>    - `PostToolUse` logging that feeds small, structured context lines back into Claude.[10][8][9]
> 4. A **claude‑side prompting pattern** (example prompts and comments) I can adopt to consistently trigger “resume this plan” behavior.[2][3]
>
> Keep everything as **minimal, concrete, and implementable** as possible. Avoid generic “best practices” that don’t directly tie to compaction‑related forgetfulness.[4][2]

***

If you like, I can next turn this into a **ready‑to‑run Bash/Python skeleton** (hooks, `PLAN.md` layout, and `CLAUDE.md` stanzas) that you can drop into your project and then iterate on.
