---
title: "I had this conversation with Claude Code.  Please come up with better ideas with reasons.
'
❯ I have another LLM implem"
date: "2026-03-15"
mode: "COPILOT"
uuid: "121c8b84-b8ff-4b99-b864-e8e0d7751c00"
entry_count: 11
---

## Human

I had this conversation with Claude Code.  Please come up with better ideas with reasons.
"
❯ I have another LLM implementing the plan, but they ran out of context.  I'm guessing subagents returned a bunch of
context into memory all at once and exceeded what was available.  How to we avoid that problem?

● This is a structural problem with how subagent results flow back to the orchestrator. The core issue: every subagent
  return value lands in the parent's context window, so parallel agents that each return substantial output can blow the
  budget in one shot.

  The fix: outputs are files, not return values

  The pattern that causes the blowout:
  Orchestrator launches agents A, B, C in parallel
    → A returns 3000 tokens of analysis
    → B returns 4000 tokens of analysis
    → C returns 2000 tokens of analysis
  = 9000 tokens dumped into orchestrator context simultaneously

  The pattern that prevents it:
  Orchestrator launches agents A, B, C with instruction:
    "Write your output to .claude/hooks/state/agent-{name}.json. Return only: status, filepath, 3-line summary."
    → A returns: "done → .claude/hooks/state/agent-compliance.json (2 findings)"
    → B returns: "done → .claude/hooks/state/agent-performance.json (1 finding)"
    → C returns: "done → .claude/hooks/state/agent-quality.json (3 findings)"
  = ~150 tokens in orchestrator context
  Orchestrator reads only the files it needs, when it needs them

  Concrete changes for this plan's implementation

  1. Per-task output contract — add to every task description:

  ▎ Agent MUST write all outputs to the task's designated file. Return to orchestrator: status (done/blocked), file
  written, ≤3 line summary. No inline code, no inline diffs.

  2. Phase gates instead of phase dumps — the natural break points already exist between Phase 1 → 2 → 3. Treat each phase
  boundary as a context reset. At the end of Phase 1, the implementer should:
  - Write a phase summary to a file
  - Start a fresh session for Phase 2 (using the handoff system you already have)
  - The new session reads the phase summary, not the full conversation history

  3. Sequential task execution within a phase — the dependency chain already enforces this (TASK-001 → TASK-002 → TASK-004,
   etc.), but it's worth making explicit: don't launch TASK-003 and TASK-006 in parallel just because they have no shared
  prerequisites. Parallel saves wall-clock time but doubles context consumption.

  4. TASK-008 specifically needs a spike first — it's the highest-point task and the one most likely to generate
  back-and-forth exploration. Add a 1-point spike task before it:

  ▎ TASK-008-spike: Write the VerificationVerdict dataclass and the match_claim_to_events stub with type signatures only.
  No implementation. Return: the two type signatures. Review before proceeding.

  This gives you a cheap context-light decision point before committing to the 8-point implementation.

  5. Reading files selectively — the biggest silent context killer is an agent that does Read(evidence_store.py) returning
  800 lines when it only needed the schema. Instruct implementers to use Read with offset and limit, or Grep to find the
  specific section first.

  Practical addition to the plan

  Add this to the Dependencies section at the bottom:

  ### Implementation Context Budget Rules
  - Each task agent writes outputs to disk; returns ≤3 line status to orchestrator
  - Phase 1 → Phase 2 boundary: start fresh session via handoff system; load phase summary only
  - No parallel task execution within a phase (sequential preserves context headroom)
  - TASK-008 requires spike (type signatures only) before full implementation
  - File reads use offset/limit or Grep; never read whole files for partial information

  Want me to add that section to the plan file now?

✻ Worked for 50s

❯ /ask yes, and please add it to /plan-workflow, and /code, and /refactor, and other skills you think might benefit from
it, maybe /s

● Let me locate all the relevant skill files first.

● Searched for 2 patterns, read 2 files (ctrl+o to expand)

● Let me look at the right insertion points in each skill before editing.

● Searched for 2 patterns, read 4 files (ctrl+o to expand)

● Good. Let me also check a few more relevant skills before editing.

● Searched for 2 patterns, read 2 files (ctrl+o to expand)

● Good picture. Now applying all edits. Starting with the plan file, then each skill:

● Update(.claude\\hooks\\plans\\plan-20260314-verification-claim-grounding.md)
  ⎿  Added 8 lines, removed 1 line
      251  - CLAUDE_TERMINAL_ID must be set per process. Already in place via SessionStart_terminal_id.py.
      252  - evidence_store.py schema already has terminal_id column. No migration needed.
      253  - Existing hook env-flag rollback pattern must be preserved for all refactored hooks.
      254 -- TASK-006 findings must be reviewed before TASK-013 implementation begins.
      254   No newline at end of file
      255 +- TASK-006 findings must be reviewed before TASK-013 implementation begins.
      256 +
      257 +### Implementation Context Budget Rules
      258 +- Each task agent writes outputs to disk; returns ≤3-line status to orchestrator (no inline code, no inli
          +ne diffs)
      259 +- Phase 1 → Phase 2 boundary: start fresh session via handoff system; load phase summary only, not full c
          +onversation history
      260 +- No parallel task execution within a phase — sequential preserves context headroom even when prerequisit
          +es would allow parallelism
      261 +- TASK-008 requires a spike task (type signatures only, no implementation) before full work begins
      262 +- File reads use `offset`/`limit` or `Grep` to target specific sections; never read whole files for parti
          +al information
      263   No newline at end of file

● Read 1 file (ctrl+o to expand)

● Update(.claude\\skills\\plan-workflow\\SKILL.md)
  ⎿  Added 13 lines
      1094  - Include acceptance criteria for all tasks → improves evidence_quality score
      1095  - Review RTM after plan creation → catch orphan requirements before implementation
      1096
      1097 +## Subagent Context Budget Rules
      1098 +
      1099 +When a plan is handed to another LLM or subagent system for implementation, enforce these rules to preve
           +nt context window exhaustion:
      1100 +
      1101 +- **Outputs are files, not return values** — each subagent writes results to disk and returns only: stat
           +us (done/blocked), file written, ≤3-line summary. No inline code, no inline diffs in return values.
      1102 +- **Phase boundaries = context resets** — use the handoff system between Phase 1→2→3. Start a fresh sess
           +ion for each phase; load the phase summary file, not full conversation history.
      1103 +- **Sequential within phases** — do not parallelize tasks just because prerequisites allow it. Sequentia
           +l execution preserves context headroom. Parallel saves wall-clock time but multiplies context consumptio
           +n.
      1104 +- **Spike before high-complexity tasks** — for any task ≥8pts, write type signatures and interfaces only
           + first. Review the spike output before committing to full implementation.
      1105 +- **Selective file reads** — use `offset`/`limit` or `Grep` to target specific sections. Never load a wh
           +ole file when only one function or block is needed.
      1106 +- **Pass task excerpts, not full plans** — when briefing an implementer subagent, pass only the relevant
           + task block, not the entire plan document.
      1107 +
      1108 +---
      1109 +
      1110  ## Appendix: Implementation Details
      1111
      1112  This section contains internal implementation details. Most users don't need to read this.

● Now the three skills in parallel — code, refactor, cwo:

● Update(.claude\\skills\\code\\SKILL.md)
  ⎿  Added 13 lines
      344  - Declaring plan/build done without explicit completion evidence
      345  - Skipping tasks without explicit user-approved skip record
      346  - Claiming done without residual risk statement and final calibration checks
      347 +- Returning subagent output inline to orchestrator instead of writing to disk first
      348 +- Launching parallel subagents when sequential execution would fit in context budget
      349
      350 +## Subagent Context Budget Rules
      351 +
      352 +When using subagents (team/hybrid/subagents execution mode):
      353 +
      354 +- **Outputs are files, not return values** — each subagent writes results to disk and returns only: statu
          +s (done/blocked), file written, ≤3-line summary. No inline code or diffs in return values.
      355 +- **Phase boundaries = context resets** — use the handoff system between major phases; new session reads
          +phase summary, not full history.
      356 +- **Sequential by default within a phase** — don't parallelize tasks just because prerequisites allow it;
          + parallel doubles context consumption.
      357 +- **Spike before high-complexity tasks** — for tasks estimated >4h, write type signatures/interfaces only
          + first, review, then implement.
      358 +- **Selective file reads** — use `offset`/`limit` or `Grep` to target specific sections; never `Read` a w
          +hole file for a single function.
      359 +- **Pass task excerpts, not full plans** — brief implementer subagents with only the relevant task block.
      360 +
      361  ## ⚡ ALLOCATION DIRECTIVE
      362
      363  **When `/build` is invoked:**

● Update(.claude\\skills\\refactor\\SKILL.md)
  ⎿  Added 12 lines
      455  - Adding abstraction layers for "flexibility" (YAGNI)
      456  - Implementing factory patterns (enterprise bloat)
      457  - Suggesting changes without reading actual code first
      458 +- Returning agent analysis inline to orchestrator instead of writing findings to disk first
      459 +- Launching all discovery agents in parallel when context budget is already under pressure
      460
      461 +## Subagent Context Budget Rules
      462 +
      463 +When discovery or refactor agents are used:
      464 +
      465 +- **Outputs are files, not return values** — each agent writes findings to disk (e.g., `.claude/state/age
          +nt-{name}.json`) and returns only: status, filepath, ≤3-line summary. No inline analysis in return values
          +.
      466 +- **Phase boundaries = context resets** — use the handoff system between discovery→plan→execute; new sess
          +ion reads summary file, not full history.
      467 +- **Sequential by default** — don't parallelize the 4 discovery agents unless context headroom is confirm
          +ed clear (< 30% of window used).
      468 +- **Selective file reads** — use `Grep` to find relevant sections first; pass `offset`/`limit` to `Read`.
          + Never load whole files into agent prompts.
      469 +- **Spike before large refactors** — for changes touching >3 files, produce a type-signature-only diff fi
          +rst and review before full implementation.
      470 +
      471  ## Execution Directive
      472
      473  **Invoke the multi-file-refactor skill using the Skill tool.**

● Update(.claude\\skills\\cwo\\SKILL.md)
  ⎿  Added 9 lines
      60  - Bypassing RWV protocol (read-before-write)
      61  - Running implementation without Ralph loop when appropriate
      62  - Skipping step validation and health checks
      63 +- Accumulating subagent return values in orchestrator context instead of writing to disk
      64
      65 +## Subagent Context Budget Rules
      66 +
      67 +- **Outputs are files, not return values** — each subagent writes results to disk and returns only: status
         + (done/blocked), file written, ≤3-line summary. No inline code or diffs.
      68 +- **Phase boundaries = context resets** — use the handoff system between phases; new session reads phase s
         +ummary, not full conversation history.
      69 +- **Sequential by default within a phase** — parallelize only when context headroom is confirmed clear.
      70 +- **Selective file reads** — use `Grep` + `offset`/`limit`; never load whole files for partial information
         +.
      71 +- **Spike before high-complexity steps** — for steps estimated >4h, produce signatures/interfaces only fir
         +st and review before full implementation.
      72 +
      73  ## Usage
      74
      75  ```bash

● Now subagent-driven-development and /s:

● Update(.claude\\skills\\subagent-driven-development\\SKILL.md)
  ⎿  Added 13 lines
      76  - Skipping verification to save time
      77  - Proceeding without user checkpoint for significant changes
      78  - Using vague task descriptions ("implement the module")
      79 +- Returning subagent output inline to orchestrator instead of writing to disk first
      80 +- Launching parallel tasks when sequential would fit in context budget
      81
      82 +## Subagent Context Budget Rules
      83 +
      84 +Context exhaustion is the primary failure mode for multi-agent implementations. Enforce these rules on eve
         +ry dispatch:
      85 +
      86 +- **Outputs are files, not return values** — each subagent writes results to disk and returns only: status
         + (done/blocked), file written, ≤3-line summary. No inline code, no inline diffs, no inline analysis in ret
         +urn values. The orchestrator reads from disk only what it needs, when it needs it.
      87 +- **Phase boundaries = context resets** — use the handoff system between major phases. Start a fresh sessi
         +on; load only the phase summary file, not full conversation history.
      88 +- **Sequential by default** — do not parallelize tasks just because prerequisites allow it. Parallel execu
         +tion multiplies context consumption in the orchestrator. Only parallelize when: (a) context window is <30%
         + used, and (b) all agents are confirmed to return file paths, not inline content.
      89 +- **Spike before high-complexity tasks** — for any task estimated >4h or >8pts, the first sub-task is alwa
         +ys: write type signatures, interfaces, and acceptance criteria only. Review before proceeding to implement
         +ation.
      90 +- **Selective file reads** — instruct subagents to use `Grep` to locate sections first, then `Read` with `
         +offset`/`limit`. Never pass whole-file contents in an agent prompt.
      91 +- **Pass task excerpts, not full plans** — brief each subagent with only the task block it needs, not the
         +entire plan document.
      92 +
      93  ### Task Decomposition Required
      94  - Multiple test files involved
      95  - Multiple TDD phases in one description

● Read 1 file (ctrl+o to expand)

● Update(.claude\\skills\\s\\SKILL.md)
  ⎿  Added 8 lines
      373  /p           # Make it work (implementation)
      374  ```
      375
      376 +## Context Budget Note
      377 +
      378 +`/s` output is large by design (5 personas × scored recommendations). When used inside a larger multi-ste
          +p workflow:
      379 +
      380 +- **Write output to disk** — use `--output markdown` and redirect to a file, or capture the session file
          +written to `.claude/state/`. Reference the file path in subsequent prompts rather than pasting the full o
          +utput inline.
      381 +- **Don't chain inline** — passing `/s` output directly as context into another LLM call can consume >30%
          + of the context window. Instead: run `/s`, note the session file path, reference it by path in the next s
          +tep.
      382 +- **One `/s` per phase** — if you need strategic input at multiple points in a workflow, run `/s` at phas
          +e boundaries and reset context between phases using the handoff system.
      383 +
      384  ## Deprecations
      385
      386  - `/llm-brainstorm` -> `/s`

● Quick verification that all 6 files got the additions:

● Searched for 1 pattern (ctrl+o to expand)

● All 7 files updated. Here's what went where and why:

  ┌─────────────────────────────┬───────────────────────────────┬──────────────────────────────────────────────────────┐
  │            File             │         Section added         │                       Framing                        │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │ ### Implementation Context    │ Implementer-facing; references TASK-008 spike by     │
  │ plan file                   │ Budget Rules at end of        │ name                                                 │
  │                             │ Dependencies                  │                                                      │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │ plan-workflow               │ ## Subagent Context Budget    │ Plan authors briefing implementers; includes "pass   │
  │                             │ Rules before Appendix         │ task excerpts, not full plans"                       │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │ ## Subagent Context Budget    │ Execution-mode aware (team/hybrid/subagents);        │
  │ code                        │ Rules + 2 new Prohibited      │ threshold tied to >4h estimates                      │
  │                             │ Actions                       │                                                      │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │ ## Subagent Context Budget    │ Discovery-agent aware; adds "sequential unless       │
  │ refactor                    │ Rules + 2 new Prohibited      │ context headroom confirmed <30%"                     │
  │                             │ Actions                       │                                                      │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │ ## Subagent Context Budget    │ Compact — CWO already has strong phase structure,    │
  │ cwo                         │ Rules + 1 new Prohibited      │ rules reinforce it                                   │
  │                             │ Action                        │                                                      │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │ ## Subagent Context Budget    │ This skill is the primary place where the pattern    │
  │ subagent-driven-development │ Rules (most detailed) + 2 new │ gets violated; gets the fullest treatment including  │
  │                             │  Prohibited Actions           │ the 30% headroom threshold                           │
  ├─────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────┤
  │                             │                               │ Different framing — /s isn't a dispatcher, it's a    │
  │ s                           │ ## Context Budget Note        │ large-output script. Rule is "write to disk,         │
  │                             │                               │ reference by path, don't chain inline"               │
  └─────────────────────────────┴───────────────────────────────┴──────────────────────────────────────────────────────┘

✻ Sautéed for 4m 25s

❯ I'm not really a fan of context budget.  Why use that concept?

● Honest answer: I grabbed it because it's a term that circulates in LLM engineering circles, not because it's the clearest
   label for what the rules actually say.

  The rules themselves are concrete:
  - Write to disk, return a path
  - Reset between phases
  - Read selectively
  - Spike before big tasks

  None of those require the word "budget." Budget implies active tracking and allocation decisions — spending context
  wisely. But these rules aren't about careful spending, they're about not dumping large return values into the
  orchestrator's window in the first place. The problem isn't scarcity management, it's routing: outputs should flow
  through disk, not through return values.

  A more accurate name would just describe what the rules prevent. Something like:

  - Subagent Output Discipline — describes who it applies to and what it governs
  - Multi-Agent Output Routing Rules — explicit that the issue is where output goes
  - Context Overflow Prevention — describes the failure mode, not a spending metaphor

  Or skip the section header concept entirely and just fold the rules into the existing Prohibited Actions list in each
  skill, which is where behavioral rules already live. That's actually the cleanest fit — no new concept needed, just more
  items in a list that implementers already read.

  Want me to rename the sections and move the rules into Prohibited Actions where they fit?"

## Assistant

You’re already enforcing “outputs are files, not return values” and phase resets, which is the main structural fix. The biggest improvement now is to make the whole thing less vibes‑y (“context budget”) and more like an explicit, testable resource/contract model.

Below are alternative concepts + concrete mechanics that go beyond what Claude proposed.

***

## 1. Rename the concept: from “context budget” to explicit failure mode

If you dislike “context budget,” drop it entirely and name the rules after the failure you’re actually preventing.

Options that better match the mechanics:

- **Context Overflow Prevention Rules** – names the failure mode directly.[1][2]
- **Subagent Output Routing Rules** – expresses that the issue is where outputs flow (disk vs return).[3][4]
- **Multi‑Agent State Handoff Rules** – aligns with “handoff” language used by OpenAI, Vellum, etc.[5][3]

Reasoning (FACT, CONSENSUS):

- Industry writeups increasingly talk about “context overflow” or “context window overflow” as the problem, not “budget.”[2][6][1]
- Multi‑agent posts focus on **routing and handoff** (files / memory pointers / shared stores) rather than budgeting metaphors.[4][3][5]

So instead of “Subagent Context Budget Rules,” you could use:

- “Subagent Output Routing Rules” in skills that are all about subagents.  
- “Context Overflow Prevention Rules” in more general skills (/s, /code).  

***

## 2. Make “files not return values” a hard interface, not just guidance

Claude’s rule is phrased as style (“outputs are files, not return values”). Turn this into an explicit interface contract plus a tiny protocol.

**Change the contract:**

- Each subagent returns a **fixed schema**:

  ```json
  {
    "status": "done" | "blocked" | "retry",
    "artifact": "relative/path/to/file.json",
    "summary": "≤ 3 lines",
    "metrics": {
      "tokens_read": 0,
      "tokens_written": 0
    }
  }
  ```

- The orchestrator **never** reads the full artifact into the LLM; it only:
  - Validates the path exists and is sane.
  - Optionally inspects a small metadata header (e.g., first N lines / JSON header) for routing.  

**Why this is better (FACT, CONSENSUS):**

- File‑based handoff with a strict schema is already a common pattern in serious agent systems (handoff JSON in worktrees, “memory pointer” style protocols).[6][3][4]
- Adding `tokens_read`/`tokens_written` gives you telemetry without forcing “budget metaphors,” and allows later enforcement if you want.  

You could codify this as:

- “Subagent Result Envelope” – a named shape that every agent must return.  
- The rules then become: “All subagents must return a valid Result Envelope; artifacts are consumed only via envelopes.”

***

## 3. Replace “context budget” with “routing tiers” and explicit scopes

Instead of “budget,” define **tiers of where data may live** and what’s allowed to flow into the LLM at each tier.

Example scheme:

- **Tier 0 – Orchestrator Context:**  
  - Only short summaries, IDs, file paths, and decisions.  
  - Hard rule: no bulk analysis, no full diffs, no long logs.  

- **Tier 1 – Handoff Store (files / state dir / worktree):**  
  - Full analyses, diffs, logs, search results, etc.  
  - Accessed via IDs/paths from Tier 0.  

- **Tier 2 – Cold Storage / History:**  
  - Old handoff chains, archived sessions.  
  - Only reloaded via a deliberate “retrieve history” step.

Rules become:

- “Never promote Tier 1 content directly into Tier 0; always summarize first.”  
- “Subagents may read Tier 1 artifacts directly; orchestrator sees only summaries and pointers.”  

Why this is useful (SPECULATION, high confidence):

- It reframes the behavior away from “budget” and toward **access levels** and **routing**, which is closer to how multi‑agent systems papers describe context engineering.[7][3]
- It matches what you’re already doing with `.handoff` / `.state` dirs, just with explicit semantics.[4]

You can then rename sections as:

- “Subagent Output Routing & Storage Tiers” instead of “Context Budget Rules.”

***

## 4. Add structural safeguards: caps, chunking, and auto‑summarization

Claude’s rules prevent the worst pattern, but they’re purely behavioral. You can add **guardrails that trip before overflow**, still without talking about “budget” in user‑facing docs.

Mechanics:

1. **Per‑agent return cap (by design, not tracking):**  
   - Enforce: “Summaries must be ≤ N tokens or ≤ M characters; orchestrator will truncate beyond that.”  
   - Make this explicit in the Subagent Result Envelope.  

2. **File size / line count hints in envelopes:**  
   - Subagent writes `approx_bytes` or `line_count` into the artifact header.  
   - Orchestrator can decide: “This diff file is large; do not read inline, only pass reference to another specialized agent.”  

3. **Automatic summarization layer:**  
   - If orchestrator must read a large artifact, it first calls a **Summarizer agent** that:
     - Reads the file directly.  
     - Emits a constrained, short summary file.  
     - Orchestrator only loads that summary into its context.  

Why this is better (FACT, CONSENSUS):

- “Writing context, selecting context, compressing context” are standard multi‑agent patterns.[3][1]
- Research on handling tool outputs of arbitrary length emphasizes **memory pointers + summarization** instead of dumping raw data.[6]

You can describe this as:

- “Oversized artifact handling rules”  
- “Summarizer before read‑back”  
- No “budget” wording required.

***

## 5. Replace “no parallel within phase” with “safe parallelism conditions”

Claude’s rule “no parallel within phase” is safe but leaves performance on the floor. You can keep your routing discipline and still allow **conditional parallelism** without ever mentioning “budget.”

Define something like:

- **Parallelism Guard Rails:**
  - Only run tasks in parallel if:
    - Each task’s expected output artifact is **classification or metadata only** (short JSON, not long prose / diffs), or  
    - Each task is flagged `low_output: true` in the plan, or  
    - A central “headroom checker” confirms artifacts are below some size threshold (e.g., estimated lines / bytes from prior runs).  

Implementation idea (CONSENSUS, SPECULATION):

- Use your planner to annotate tasks with `output_profile: "small" | "medium" | "large"` based on type (e.g., “read schema,” “generate tests,” “rewrite N files”).  
- Orchestrator then has a simple rule: “Only parallelize tasks whose output_profile is small.”  

This reframes from “spending budget” to “these tasks are safe to run in parallel because they only produce small artifacts.”

***

## 6. Integrate rules into existing structures, not separate headings

You already noticed the cleanest place is “Prohibited Actions.” I’d go further and make the rules:

- Mostly **negative constraints** under “Prohibited Actions”:  
  - “Do not return analysis inline; write it to disk and return a path.”  
  - “Do not pass full plan documents to subagents; pass the task excerpt only.”  
  - “Do not read entire files for partial info; use grep + offset/limit first.”  

- Plus one small **“Subagent Output Routing Rules”** box in skills that heavily use subagents.  

Benefits (SPECULATION, high confidence):

- You remove the need for any extra conceptual term (“budget”/“overflow”), but retain strong behavior.  
- It matches how serious systems describe context handling as part of their **architecture and contracts**, not a separate “budget policy.”[5][3][4]

***

## 7. Two concrete renames you could apply today

Given the edits you pasted, I’d specifically change:

1. In `plan-workflow`, `code`, `refactor`, `cwo`, `subagent-driven-development`:

   - Rename section headers from `## Subagent Context Budget Rules` to `## Subagent Output Routing Rules` or `## Context Overflow Prevention Rules`.  
   - Leave the bullets largely as‑is, maybe tightening wording to emphasize routing (files, summaries, selective reads).

2. In the plan file:

   - `### Implementation Context Budget Rules` → `### Context Overflow Prevention Rules` or `### Multi‑Agent Output Routing Rules`.  

Both keep all the good structure you already added, but line the naming up with:

- How multi‑agent posts talk about “handoffs” and “output routing.”[3][4][5]
- How infra posts talk about “overflow” as the failure mode.[1][2][6]

***

If you had to pick just one direction: would you rather frame this as “Output Routing Rules” (focus on mechanism) or “Overflow Prevention Rules” (focus on failure mode)?  

## Human

Please provide a prompt I can give to CC so that it can implement your ideas.

## Assistant

Here’s a prompt you can paste into Claude Code to implement the ideas we discussed, including renaming, interface contracts, and structural rules.

***

You are editing my Claude Code configuration and skills to improve **multi‑agent output routing and overflow prevention**. I already have recent changes that added “Subagent Context Budget Rules” sections and “Implementation Context Budget Rules” in several files. Those sections are conceptually good, but I want you to refactor and extend them according to the instructions below.

### High‑level goal

Turn the current “context budget” framing into a **clean, explicit architecture** for:

- Subagent output routing (files, not inline returns)  
- Strict subagent result envelopes  
- Clear storage tiers (what can/can’t enter the LLM context)  
- Guardrails for safe parallelism and large artifacts  

Avoid the phrase “context budget” entirely in user‑facing text. Prefer naming around **output routing** and **overflow prevention**.

***

## 1. Rename sections to match the real failure mode/mechanism

In all the files that currently contain:

- `### Implementation Context Budget Rules`  
- `## Subagent Context Budget Rules`  

do the following:

1. Replace `Implementation Context Budget Rules` with:  
   - `Context Overflow Prevention Rules` (preferred), or  
   - If you see an obviously better fit per file, use `Multi‑Agent Output Routing Rules`.  
2. Replace every `Subagent Context Budget Rules` heading with:  
   - `Subagent Output Routing Rules` (preferred).  

Keep the existing bullet lists but update wording to align with “routing” and “overflow prevention” instead of “budget metaphors.” For example, phrases like “preserves context headroom” can become “prevents context overflow in the orchestrator window.”

List the files you modified and show a small before/after diff for each heading change.

***

## 2. Introduce a strict “Subagent Result Envelope” interface

In skills that invoke subagents (plan workflow, subagent‑driven‑development, code, refactor, cwo, and any others you find), define a **standard result envelope** that every subagent must return.

Add a short normative subsection in each relevant skill, titled:

- `### Subagent Result Envelope`

The envelope spec should look like this (adapt to existing style/format, but keep fields and semantics):

- Each subagent **must** write its detailed output to disk (JSON or markdown file).  
- Each subagent **must** return a small JSON object with this shape:

  ```jsonc
  {
    "status": "done" | "blocked" | "retry",
    "artifact": "relative/path/to/file.ext",
    "summary": "≤ 3 short lines of text",
    "metrics": {
      "tokens_read": <optional integer>,
      "tokens_written": <optional integer>
    }
  }
  ```

Rules:

- `summary` is human‑readable, ≤3 short lines, no large analysis, no code blocks, no diffs.  
- `artifact` is a path into my `.claude/state` or equivalent worktree area.  
- `metrics` is optional but **encouraged**; it allows later observability on usage without introducing “budget” language.  

Wherever the current text says “Return to orchestrator: status, file written, ≤3‑line summary” or similar, rewrite it to explicitly reference this **Result Envelope** and keep behavior consistent.

Add one short sentence per skill that states: “The orchestrator consumes only the Result Envelope plus selective reads of artifacts; it never inlines full artifacts into its own context.”

***

## 3. Express “tiers” of storage instead of “budget”

Add a small conceptual box (2–5 bullets) in the most central skills (`plan-workflow`, `subagent-driven-development`, and whichever skill orchestrates multi‑step work most often), titled:

- `### Output Routing Tiers`

Express three tiers:

- **Tier 0 – Orchestrator Context**  
  - Contains only short summaries, decisions, IDs, file paths, and Result Envelopes.  
  - Prohibit: full diffs, long logs, large analyses in this tier.

- **Tier 1 – Handoff Store (files / state dir)**  
  - Contains full analyses, diffs, logs, tool outputs.  
  - Accessed using file paths from Result Envelopes.  
  - Agents read from here directly when needed.

- **Tier 2 – History / Archive**  
  - Contains old handoff chains and session histories.  
  - Only loaded via explicit “retrieve history” operations, not by default.

Tie this into your existing wording by replacing any “context headroom” talk with tier language, for example:

- “Subagents write full results into Tier 1; orchestrator reads only summaries and pointers into Tier 0.”  
- “Do not promote Tier 1 content directly into Tier 0 without summarization.”

Do **not** introduce new configuration knobs or code behavior; this is prompt‑level architectural discipline.

***

## 4. Guardrails for parallelism without using “budget” language

Where the current rules say “No parallel within a phase” or similar, refactor to a clearer **safe‑parallelism policy**:

- Default: “Sequential by default within a phase.”  
- Allow explicit exceptions only when tasks are clearly low‑output.

Update relevant skills (plan‑workflow, subagent‑driven‑development, code, refactor, cwo) to include something like:

- “Only parallelize tasks when they are explicitly marked as low‑output or classification‑only, or when their expected artifacts are small (short JSON metadata, no large prose or diffs).”  
- “Do not run multiple high‑output tasks in parallel; stagger them so only one large artifact is created at a time.”

If any planning skill is already estimating task size or complexity (points, hours, etc.), you may tie the rule to those estimates, e.g.:

- “Tasks ≥8 points or estimated >4h are high‑output; run those sequentially.”

Rewrite to use “high‑output / low‑output” language, not “budget” or “headroom.”

***

## 5. Oversized artifact handling and summarization

Add a short, consistent rule set for **large file handling** in the main skills where agents read code or logs (code, refactor, subagent‑driven‑development, cwo):

- Before an agent reads an artifact that is obviously large (big diff, long log, entire module), it should:  
  - Prefer `Grep` / search tools plus `offset`/`limit`.  
  - If a large file truly must be processed, first call a **summarizer step** that:
    - Reads the file directly.  
    - Writes a new, smaller summary artifact.  
    - Returns a Result Envelope pointing to the summary file, not the full original.

Express this as “Oversized artifact handling” or “Large artifact summarization” within each relevant skill, and align wording with the existing “Selective file reads” bullets (don’t duplicate, extend them).

Again: do not mention “budget”; describe this purely as routing and overflow prevention.

***

## 6. Integrate with existing “Prohibited Actions” instead of adding new conceptual bloat

For each skill that currently has:

- “Subagent Context Budget Rules” + “Prohibited Actions”  

do the following:

- Keep the new section, but also **promote the key behavioral constraints into `Prohibited Actions`**.  
  - E.g., “Returning subagent output inline to orchestrator instead of writing to disk first” stays as a prohibited action.  
  - Add or refine items like:
    - “Passing entire plan documents into subagents instead of the relevant task excerpt.”  
    - “Reading entire files when only a function or block is needed.”  
    - “Returning large diffs or logs inline instead of writing them to artifacts.”

The goal: if a user only reads “Prohibited Actions,” they still get the full behavioral picture, without needing to internalize any special “budget” concept.

***

## 7. Implementation details and verification

1. Enumerate all files you touch (at minimum the ones shown in the earlier conversation:  
   - `.claude/hooks/plans/plan-…verification-claim-grounding.md`  
   - `.claude/skills/plan-workflow/SKILL.md`  
   - `.claude/skills/code/SKILL.md`  
   - `.claude/skills/refactor/SKILL.md`  
   - `.claude/skills/cwo/SKILL.md`  
   - `.claude/skills/subagent-driven-development/SKILL.md`  
   - `.claude/skills/s/SKILL.md`  
   - plus any other skills that obviously use multi‑agent orchestration.)

2. For each file, show a concise diff of:
   - Heading renames.  
   - New “Subagent Result Envelope” blocks.  
   - New “Output Routing Tiers” blocks (where added).  
   - Any changes to “Prohibited Actions.”

3. Ensure that:
   - The phrase “context budget” no longer appears anywhere.  
   - “Context overflow,” “overflow prevention,” and “output routing” are used instead where appropriate.  
   - The Result Envelope schema and file‑first routing are consistent across all skills.

When you’re done, summarize in a small table:

- File  
- New section names  
- Whether it defines Result Envelope, Output Tiers, and any special parallelism rules.

Then ask me if I want you to tighten or relax any of the rules (for example, parallelism criteria or required `metrics` fields) before we consider this pattern stable.

## Human

How to integrate RAG pipelines to prevent context bloat

## Assistant

Use RAG as a **selector and compressor** between agents and the LLM, not as another way to shovel more stuff into context. The key is to make *all* large artifacts “RAG-addressable” and only ever load the top, small subset per step.[1][2][3]

Below is a concrete pattern you can fold into your existing multi‑agent / file‑first setup.

***

## 1. Treat everything as a RAG corpus, not inline context

Instead of feeding raw plan text, logs, or code into prompts:

- Persist all “big” artifacts to disk or an object store:
  - Plan documents, task specs, design notes.
  - Subagent outputs, diffs, logs, traces.
  - Code snippets or whole modules if they’re often retrieved.[4][1]
- Index those artifacts into a vector store, with:
  - Dense embeddings over chunks.
  - Metadata: task id, phase, file path, agent name, timestamp, tags.[5][4]

Then, **at inference time**, you *never* pass full artifacts; you:

- Embed the current query or task.  
- Retrieve a handful of relevant chunks.  
- Insert only those chunks into the LLM’s context.[2][4]

This is how modern RAG and vector‑db‑backed agents keep windows small even with huge corpora.[6][4][5]

***

## 2. Use narrow queries and re‑ranking to keep the window small

To avoid “RAG bloat” (lots of barely relevant chunks):

- Use **hybrid retrieval** (dense + keyword/metadata filters) to narrow before the LLM sees anything.[7][6]
- Apply a **two‑stage retrieval**:
  - Stage 1: Fetch, say, top 50–100 candidates cheaply.  
  - Stage 2: Re‑rank them with a cross‑encoder or cheap LLM scorer, keep top 5–10 for the final prompt.[7][6]

This keeps recall high while still feeding only a small, high‑quality set of chunks into the model.[6][7]

***

## 3. Use long context mainly for aggregation, not raw docs

Recent practice is **RAG first, long context second**:[8][1]

- Use RAG to pick small, coherent chunks.  
- Use the LLM’s long context window to:
  - Aggregate multiple retrieved snippets.  
  - Chain multi‑step reasoning or multi‑agent summaries.  

Don’t use long context to “just shove in everything”; that’s exactly what causes overflow and degraded answers.[1][2]

In your setup this means:

- Subagents write outputs → index them.  
- Orchestrator or downstream agents query the index with tight questions, then reason over just the retrieved snippets.  

***

## 4. Put a hard cap and ranking on retrieved tokens

Even good retrieval can over‑fetch. Add explicit caps and scoring:

- Limit total RAG tokens per call (for example, 1–2k tokens maximum for retrieved text).  
- Rank candidates by a composite score:
  - Similarity score from the vector store.  
  - Freshness / recency from metadata.  
  - Source reliability (e.g., tests > logs > ad‑hoc notes).[9]

Always cut off low‑scoring chunks until you’re under the token cap. This forces the system to choose only the highest‑value context.[9][2]

***

## 5. Summarize into the corpus instead of into prompts

When history or logs get large, don’t keep summarizing into the current prompt; summarize **back into the RAG corpus**:[2][1]

- Periodically:
  - Summarize old conversation spans, long logs, or multi‑step reasoning traces into concise notes.  
  - Store those summaries as new, separate documents (with links to originals).  
  - Remove the original bulk text from the “hot” retrieval index or mark it low‑priority.  

Future queries then retrieve the summaries, not the entire original blobs, keeping prompts small while preserving the important information.[1][2]

***

## 6. Tie RAG to your routing tiers

Given the output‑routing tiers pattern:

- Tier 1 (Handoff Store) doubles as your **RAG backing store**.  
- RAG retrieval becomes the **only** path by which Tier 1 data is allowed into Tier 0 (LLM context), except for very small snippets.  

This gives you one simple invariant:

- “Nothing large goes into context unless it’s been selected by RAG + filters and fits under the retrieval token cap.”

***

If you share your current RAG stack (vector DB, embedding model, where you index code vs logs vs plans), I can sketch a concrete pipeline with component choices and exact caps (e.g., k, chunk size, token limits) that align with your multi‑agent setup.

## Human

"
● Current RAG Stack

  Confidence: HIGH (verified from code)

  Vector Database

  ┌────────┬───────────────────────────────┬─────────────────────────────────┐
  │ System │           Vector DB           │             Purpose             │
  ├────────┼───────────────────────────────┼─────────────────────────────────┤
  │ CHS    │ FAISS (file-based)            │ Chat history semantic search    │
  ├────────┼───────────────────────────────┼─────────────────────────────────┤
  │ CKS    │ FAISS (file-based)            │ Constitutional knowledge system │
  ├────────┼───────────────────────────────┼─────────────────────────────────┤
  │ CDS    │ None (AST-based)              │ Code documentation search       │
  ├────────┼───────────────────────────────┼─────────────────────────────────┤
  │ Grep   │ None (AST-based)              │ Code pattern search             │
  ├────────┼───────────────────────────────┼─────────────────────────────────┤
  │ Skills │ None (progressive disclosure) │ Skill/command search            │
  └────────┴───────────────────────────────┴─────────────────────────────────┘

  Embedding Models

  ┌────────┬───────────────────────────────┬────────────────────────────┬───────────┐
  │ System │         Primary Model         │       Fallback Model       │ Dimension │
  ├────────┼───────────────────────────────┼────────────────────────────┼───────────┤
  │ CHS    │ all-MiniLM-L6-v2              │ None (daemon-based)        │ 384       │
  ├────────┼───────────────────────────────┼────────────────────────────┼───────────┤
  │ CKS    │ BAAI/bge-small-en-v1.5 (fast) │ all-MiniLM-L6-v2 (quality) │ 384       │
  └────────┴───────────────────────────────┴────────────────────────────┴───────────┘

  What Gets Indexed Where

  CHS (Chat History)

  - Indexed: Chat conversations, session transcripts
  - Location: P:/__csf/data/chat_history_faiss_424k/faiss_index.bin
  - Search method: FAISS semantic search + FTS5 full-text fallback
  - Update: Incremental updates via daemon (11-minute rebuild cycle)
  - Content: Messages, session context, problem-solving chains

  CKS (Constitutional Knowledge)

  - Indexed: Knowledge artifacts, patterns, lessons, decisions
  - Location: P:/__csf/data/cks_hypergraph/
  - Search method: FAISS vector search + multi-graph engine
  - Content types:
    - memory - Chat history, Q&A
    - pattern - Documentation, best practices
    - code - Code snippets, examples
    - knowledge - Articles, references
    - correction - Mistakes and fixes
    - decision - Architectural decisions
    - insight - Realizations
    - learning - Lessons learned

  CDS (Code Documentation)

  - Indexed: Docstrings, comments, type hints
  - Method: AST-based extraction (no embeddings)
  - Update: On-demand via AST traversal
  - Content: Function/class documentation, module docstrings

  Grep (Code Patterns)

  - Indexed: Function names, class names, AST patterns
  - Method: AST-based code search (no embeddings)
  - Content: Code structure, signatures, imports

  Skills

  - Indexed: Skill names, descriptions, triggers
  - Method: Progressive disclosure search (no embeddings)
  - Content: Available commands, their purposes and usage

  Key Architecture Points

  1. FAISS-based - Both CHS and CKS use FAISS for vector similarity search
  2. 384-dimensional embeddings - Standard across both systems (all-MiniLM-L6-v2)
  3. File-based indexes - No separate vector database server required
  4. Hybrid search - Combines semantic (FAISS) + lexical (FTS5) for optimal results
  5. Lazy loading - Embedding models loaded on-demand to save RAM
  6. Graceful degradation - Falls back to CPU if GPU unavailable, uses alternative
  models if primary fails

  Performance Characteristics

  ┌────────┬────────────────┬────────────┬────────────────────────────┐
  │ System │   Index Time   │ Query Time │      Update Strategy       │
  ├────────┼────────────────┼────────────┼────────────────────────────┤
  │ CHS    │ ~87s (initial) │ <1s        │ Incremental (11-min cycle) │
  ├────────┼────────────────┼────────────┼────────────────────────────┤
  │ CKS    │ ~30-60s        │ <1s        │ Batch backfill             │
  ├────────┼────────────────┼────────────┼────────────────────────────┤
  │ CDS    │ Instant (AST)  │ <0.5s      │ On-demand                  │
  ├────────┼────────────────┼────────────┼────────────────────────────┤
  │ Grep   │ Instant (AST)  │ <0.5s      │ On-demand                  │
  └────────┴────────────────┴────────────┴────────────────────────────┘

  GPU Acceleration

  - CHS: GPU acceleration available via PyTorch (optional)
  - CKS: GPU acceleration available via PyTorch (optional)
  - Both: Automatic CPU fallback if GPU unavailable"

## Assistant

You already have a solid local RAG baseline; the integration work is mostly about *how* you call it and *how much* you let through. Given CHS/CKS + AST search, you can aggressively offload context into those stores and only rehydrate a small, ranked slice into any agent’s prompt.[1][2][3]

Below is a concrete way to wire that into your multi‑agent / file‑first architecture so RAG actively prevents bloat.

***

## 1. Define what must *never* go directly into prompts

Given your stack, treat these as “RAG‑only, not inline”:

- Chat history beyond the current turn → CHS.  
- Knowledge artifacts, patterns, and decisions → CKS.  
- Large reasoning traces or subagent outputs → written to disk, then indexed into CKS.  

Architectural invariant:

- Orchestrator / agents only see:
  - Current user message.  
  - A small number of retrieved chunks from CHS/CKS/CDS/Grep.  
  - Short summaries + file paths (Result Envelopes), never big blobs.  

This matches best‑practice “writing, selecting, compressing, isolating” context engineering patterns.[4][3]

***

## 2. Wrap CHS/CKS in a single “Routed Retrieval” service

Create a thin retrieval layer that sits between agents and your FAISS/AST stack:

- Input:
  - `query_text` (what the agent is doing right now).  
  - `scope` / `intent` flags: `chat_history`, `knowledge`, `code_docs`, `patterns`, `decisions`.  
  - Hard caps: `max_chunks`, `max_tokens`.  

- It internally:
  - Routes to the right index:
    - CHS → FAISS + FTS5 for conversational memory.  
    - CKS → FAISS + hypergraph/metadata filters for patterns/decisions.[5][6]
    - CDS/Grep → AST search for code structure (signatures, docstrings).  
  - Runs hybrid retrieval where possible (semantic + lexical).[7][8]
  - Re‑ranks and truncates to respect `max_tokens`.  

- Output:
  - A list of **small, pre‑trimmed snippets** (e.g., 3–10 chunks) plus their metadata.  

Every agent call that “needs context” should go through this service instead of direct file reads or raw CHS/CKS calls. This is exactly how RAG pipelines in the literature reduce token usage without hurting accuracy: top‑N retrieval + FAISS + truncation.[2][1]

***

## 3. Index subagent outputs and logs into CKS

Right now, CKS holds “knowledge artifacts, patterns, lessons, decisions.” You can extend it to absorb:

- Subagent outputs (analysis files, diff summaries, investigation notes).  
- Long, one‑off reasoning chains that you may want to reuse.  

Mechanics:

- When a subagent writes a result file:
  - Keep the file as Tier‑1 artifact.  
  - Chunk it (e.g., 300–600 tokens).  
  - Embed with your 384‑dim model and insert into CKS with rich metadata:
    - `task_id`, `phase`, `agent_name`, `file_path`, `tag: "agent_output"` / `"reasoning_trace"`.  

- When a later agent needs “prior work on TASK‑XYZ”:
  - It queries the RAG layer with `scope: knowledge + decisions + agent_output`, filters on `task_id` or tags, gets only the 3–7 most relevant chunks.  

Empirically, RAG on large notes/logs can match full‑document performance while using much less context.[2][5]

***

## 4. Use CHS instead of long conversation windows

You already have CHS with FAISS + FTS5 and an 11‑minute update cycle.[1][5]

Use it to enforce **short conversational context**:

- In prompts, keep:
  - Current user message.  
  - At most a tiny sliding window of the last few turns.  
- For “older but relevant” history, agents should:
  - Formulate a retrieval query against CHS (“past discussion of X in this session/project”).  
  - Pull back a handful of CHS chunks through the retrieval layer.  

This matches how modern conversational RAG uses history: small in‑prompt window, larger in‑index history store.[9][3]

***

## 5. Push summarization *into* CKS instead of prompts

To avoid summary‑of‑summary rot in prompts:

- When a chat thread or agent log becomes long:
  - Run a summarizer agent that:
    - Reads the long artifact.  
    - Writes a concise summary artifact (e.g., “session X summary”).  
    - Inserts that summary as a new CKS document with type `summary` and links to the original.  

- Mark the original artifacts as:
  - Lower priority for retrieval (or remove from the “hot” index).  

Later retrievals:

- Prefer `summary` chunks.  
- Only fetch original long text if specifically requested.  

This “summarize into the corpus, not into the prompt” pattern is what recent context‑engineering and RAG reviews recommend to avoid prompt bloat and context rot.[3][10][5]

***

## 6. Slot RAG into your Output Routing Tiers

Given your multi‑agent pattern, align RAG with tiers:

- Tier 0 (LLM context):  
  - Only:
    - Current turn.  
    - A small number of RAG‑retrieved chunks from CHS/CKS/CDS/Grep.  
    - Subagent Result Envelopes (summary + file path).  

- Tier 1 (files, FAISS indexes, AST search):  
  - All heavy content: logs, plans, outputs, code.  

- The only allowed promotion from Tier 1 → Tier 0 is:
  - Through the retrieval layer, honoring `max_tokens`.  

This enforces a simple invariant: **no large artifact reaches a prompt unfiltered**, which is exactly the mitigation for context explosion in multi‑agent frameworks.[4][3]

***

## 7. Concrete next steps in your stack

With your current setup, I’d implement:

1. A unified retrieval module that wraps:
   - CHS FAISS + FTS5.  
   - CKS FAISS + hypergraph.  
   - CDS/Grep AST search.  

2. A small schema for retrieval requests/responses (query, scopes, caps, returned chunks).  
3. A “RAG‑first” convention in all skills:
   - “When you need prior knowledge or history, use the retrieval tool with a precise query. Do not call `Read` on large files or paste entire logs.”  

If you share one of your current prompt templates (e.g., for `/code` or `subagent-driven-development`), I can show you the exact edits to add RAG calls and remove direct inline history/plan injection.  

## Human

SKILL.md

## Assistant

You have three different SKILL.md files here:

- `file:52` – `/plan-workflow` (planning + quality checks).[1]
- `file:53` – `/refactor` (multi-file refactoring orchestrator).[2]
- `file:54` – `/s` (strategy / multi‑persona brainstorming).[3]

Each already references search/RAG‑like behavior (CHS/CKS/code backends, recall flags), but none yet formalize the “Subagent Result Envelope,” “Output Routing Tiers,” or explicit RAG‑first retrieval contracts we discussed.[1][2][3]

To move forward: which skill do you want to adapt first for RAG‑based context control and output routing—`/plan-workflow`, `/refactor`, or `/s`?

## Human

all of them.

## Assistant

Here’s a compact edit plan you can apply across all three SKILL.md files to integrate RAG + output routing and kill context bloat, without changing your code stack.

I’ll give you reusable text blocks you can paste and then tweak.

***

## 1. Add “Subagent Output Routing Rules” (where applicable)

For skills that call subagents or produce large artifacts (`/plan-workflow`, `/refactor`, `/s` via `run_heavy.py` orchestrator), add a section like this near existing “Prohibited Actions” / workflow rules.

### For `/plan-workflow` SKILL.md

Add after the adversarial-review / plan mechanics section:

```md
## Subagent Output Routing Rules

This skill may delegate work to other agents and tools. To prevent context overflow:

- **Outputs are files, not return values**  
  - Subagents and tools MUST write detailed results (plans, findings, diffs, logs) to disk and return only: a small status object, file path, and ≤3‑line summary.  
  - Never paste full plans, logs, or diffs inline in replies to the orchestrator.

- **Subagent Result Envelope (contract)**  
  Every subagent returns a JSON-like envelope:
  ```jsonc
  {
    "status": "done" | "blocked" | "retry",
    "artifact": "relative/path/to/file.ext",
    "summary": "≤ 3 short lines",
    "metrics": {
      "tokens_read": <optional int>,
      "tokens_written": <optional int>
    }
  }
  ```
  The orchestrator consumes only this envelope plus selective reads of the artifact. It MUST NOT inline the full artifact into its own context.

- **Pass task excerpts, not full plans**  
  When briefing implementer agents, pass only the relevant task block or section from the plan, not the entire plan document.

- **Selective file reads only**  
  Use search (`/search`, `Grep`, AST tools, CDS) to locate sections first, then `Read` with offsets/limits. Never load whole files into agent prompts when only one function, block, or section is needed.
```

You can mention CHS/CKS explicitly if you like, but that happens in the Tiers section below.

### For `/refactor` SKILL.md

Add near the existing multi‑agent RED/ADVERSARIAL rules:

```md
## Subagent Output Routing Rules

When this skill uses multiple agents (discovery, adversarial review, refactor, regression, simplifier):

- Agents MUST write detailed findings and diffs to disk (e.g. `.evidence/`, `.claude/state/`) and return only a small Result Envelope (status, artifact path, ≤3‑line summary, optional metrics).
- The orchestrator MUST NOT inline large analyses or diffs from subagents; it reads artifacts from disk selectively (e.g. specific hunks or functions) when needed.
- Multi-agent discussions and characterization logs are stored as artifacts and retrieved via search/RAG, not kept as growing inline conversation history.
```

### For `/s` SKILL.md

Add after “Execution” / context resolution:

```md
## Output Routing for Heavy Strategy Runs

`/s` can generate large outputs (multi-persona brainstorm, decision memo, hints). To prevent context overflow when `/s` is used inside larger workflows:

- **Write heavy output to disk**  
  - Always run `run_heavy.py` with `--output markdown` (or json) and write results to a file in the project state directory.  
  - Present a concise summary plus the file path in the terminal, not the entire raw content when called as a sub‑step.

- **Result Envelope for callers**  
  When `/s` is invoked programmatically by other skills, it MUST return a small Result Envelope (status, artifact path, ≤3‑line summary) instead of the full brainstorm content.
```

***

## 2. Add “Output Routing Tiers” + RAG hook in `/plan-workflow` and `/s`

These are your RAG integration points; they tell agents “CHS/CKS/CDS/Grep first, then small snippets.”

### For `/plan-workflow` SKILL.md

Right after “🔍 Search Integration” or “How It Works”, add:

```md
## Output Routing Tiers for Planning

This skill uses three tiers of information:

- **Tier 0 – Plan-Builder Context (LLM window)**  
  - Contains only: the current user request, a small number of retrieved snippets, and short summaries + file paths.  
  - PROHIBITED: full plans, full chat transcripts, large logs, or diffs pasted inline.

- **Tier 1 – Handoff Store (files + indexes)**  
  - Contains full plan documents, adversarial review outputs, discovery notes, diffs, and logs saved under `.claude/` and project directories.  
  - Accessed via file paths, `/search`, CHS, CKS, CDS, and Grep.

- **Tier 2 – History / Archive**  
  - Contains older plans, deprecated decisions, and long session histories.  
  - Loaded only via explicit “recall” or `/search` queries, not automatically.

**Invariant:**  
When planning or verifying, ALWAYS fetch additional context via `/search` (CHS/CKS/code/docs) or AST search, then include only the top, small set of snippets in the prompt. Never promote entire Tier‑1 artifacts directly into Tier 0 without summarization.
```

### For `/s` SKILL.md

After “Anti‑Anchoring vs Context Awareness” or the “Context Resolution” section:

```md
## RAG-First Context Use

`/s` uses existing search and recall mechanisms instead of long inline history:

- **Chat history**  
  - When `--recall` is used, search CHS for past brainstorm sessions and related discussions on the topic.  
  - Include only a few short, high‑relevance snippets in the prompt, not full transcripts.

- **Knowledge and patterns**  
  - Use CKS to pull prior decisions, patterns, and lessons relevant to the topic.  
  - Retrieve a small set of chunks, each trimmed to essential context.

- **Code and project context**  
  - When `--context-path` is set, use AST/Grep/CDS to sample only key docstrings, signatures, and summaries from that path.  
  - Avoid pasting entire files; rely on structured search to find the right parts.

**Rule:** `/s` MUST treat CHS/CKS/CDS/Grep as the primary way to access history and knowledge. Only RAG-selected snippets and short summaries are allowed into the brainstorming prompt.
```

***

## 3. Add “Safe Parallelism” rule where there is multi‑agent / multi‑step work

### For `/plan-workflow` and `/refactor`

Add a short section (or 3 bullets) near the multi‑agent description:

```md
### Safe Parallelism

- Default: run high-output tasks sequentially (plan creation, adversarial review, refactor application, large diff generation).
- Only parallelize agents when they are explicitly low-output (classification, tagging, small metadata extraction) OR when their expected artifacts are small.
- Do not launch multiple large-analysis agents in parallel if their combined outputs would produce multiple big artifacts at once; stagger them so only one large artifact is produced in each step.
```

This documents the behavior you want without “budget” language.

***

## 4. Wire in RAG retrieval explicitly (minimal prompt‑level change)

You already mention `/search` in `/plan-workflow` and `--recall` in `/s`. Tighten that into explicit instructions.

### In `/plan-workflow` “🔍 Search Integration” section

Add a short normative note:

```md
**Normative rule:**  
Before reading any large file or pasting previous conversations or plans into the prompt, first call `/search` with a precise query and use its top results as context. Do not call `Read` on entire files when `/search` or AST tools can give you focused snippets instead.
```

### In `/s` under `--recall`

Augment the description:

```md
--recall                  Search previous brainstorm sessions on similar topics via CHS/CKS; only top-ranked snippets (not full sessions) are included as context
```

And a one‑liner near “What `/s` does With Your Topic”:

```md
When `/s` needs prior context, it queries CHS/CKS/CDS/Grep and pulls in only a few highly relevant snippets instead of reloading full history or documents.
```

### In `/refactor`

Near the discovery / adversarial review description, add:

```md
When you need prior decisions, patterns, or previous refactors, use the retrieval/search tools (CHS/CKS/CDS/Grep) to pull a few relevant snippets. Do not paste entire prior sessions or large logs into the refactor agent’s context.
```

***

## 5. If you want a single invariant to enforce across all skills

You can add this short block (or its essence) to each SKILL:

```md
## Context Overflow Prevention Invariant

For this skill:

- Large artifacts (plans, logs, diffs, long brainstorms) live on disk and in indexes (CHS/CKS/CDS/Grep).
- Agents and orchestrators MAY include:
  - Current user input
  - A small number of retrieved snippets
  - Short summaries and file paths
- Agents and orchestrators MUST NOT:
  - Inline full large artifacts in their prompts
  - Chain large skill outputs directly into the next call without writing to disk and using retrieval/selective reading.
```

This makes the “don’t blow the window” behavior explicit without ever saying “context budget.”

***

If you paste one of these SKILL.md files back after you make first-pass edits (or just a relevant section), I can tighten wording and check for contradictions with your existing text.

## Human

What do you think of this feedback?
"
● Most of it is already done, and in some cases done better. Here's the honest breakdown:

  Already covered, skip:
  - Sections 1 and 3 — Subagent Output Routing Rules, Result Envelope, Safe Parallelism. We have all of this, with better
  language (their envelope still has tokens_read/tokens_written which we already decided against; their parallelism rule is
   vaguer than our high-output/low-output framing).
  - Section 2 tiers — already in plan-workflow, subagent-driven-development, cwo, with better tier names (Artifact Store vs
   their "Handoff Store").

  Genuinely new, worth doing — Section 4:

  The RAG-first retrieval rule. Everything we added addresses the output side: what subagents return to the orchestrator.
  Section 4 addresses the input side: what goes into agent prompts in the first place. That's a real gap we didn't cover.

  The normative rule is: before reading a large file or pasting prior context, call /search or Grep first and use only the
  top results as input — don't load whole files into prompts.

  This applies in /plan-workflow (before reading existing plans or code), /refactor (before loading prior sessions or large
   files into discovery agents), and /s (the --recall path should pull snippets, not full sessions).

  Section 5 — maybe:

  The unified "MAY include / MUST NOT" invariant is a nice tight expression of the principle. Worth considering as a
  one-liner addition to the canonical shared/result-envelope.md rather than repeating it across all skills.

  ---
  So the real question is: do you want to add the Section 4 RAG-first input rules to plan-workflow, refactor, and s? That's
   the only thing in that doc that adds something we don't have.

✻ Baked for 37s

❯ what are the potential failure scenarios where we'd be disapointed using it?

● Thinking through the specific failure modes:

  1. It undermines the verification system you're building

  This is the most serious one given the plan we just reviewed. The Stop_hypothesis_as_fact_gate grounds claims against
  tool events in evidence_store — those events come from actual Read, Glob, and Bash tool calls. RAG retrieval via /search
  or CHS/CKS doesn't write tool events. So an agent that follows the RAG-first rule and retrieves a snippet about "package
  has no skill/ directory" will make that claim with zero grounding evidence in the store. The gate will see it as SILENT —
   unverified — even though the agent did look something up. The two systems actively conflict.

  2. False confidence from stale or misranked retrieval

  The agent runs the search, gets results, proceeds. If the top result is from a previous session where the code was
  structured differently, or it ranks 4th when the actually relevant piece is 5th, the agent has no signal its retrieval
  was incomplete. At least reading a whole file tells you what you have. RAG retrieval can produce confident-looking
  context that's quietly wrong, with no mechanism to detect it.

  3. Mandatory overhead for cases that don't need it

  "Before reading any large file, search first" requires the agent to decide what's large, run a query, evaluate results,
  then decide whether to also read the file anyway. For scoped tasks — fix this function, add this parameter — this is pure
   friction. The rule doesn't distinguish between navigating an unfamiliar large codebase (where RAG helps) and making a
  targeted edit to a known file (where it just slows things down).

  4. Nothing to retrieve for novel work

  RAG-first only helps when relevant context already exists in the indexes. For new architecture decisions, new modules
  being introduced, or anything that predates the search index, the search returns noise or nothing. The agent follows the
  rule, gets bad results, and either proceeds on noise or falls back to file reads anyway — now with an extra round trip
  and no guidance on what the fallback behavior should be.

  5. Prompt-level rules have no enforcement

  Hooks run as code. SKILL.md instructions are suggestions that an agent under pressure, mid-execution, or interpreting the
   rule loosely will skip. The output routing rules we added are more durable because they're tied to a concrete interface
  (the Result Envelope schema). "Search first" has no such anchor — there's no output shape the orchestrator can check to
  verify the rule was followed.

  ---
  Net assessment:

  The RAG-first rule is useful when an agent is navigating unfamiliar context in a large codebase. It's harmful or neutral
  in the context of this specific system because of the verification conflict (point 1) and the enforcement gap (point 5).
  The safe version is narrower: add it specifically to the documentation discovery phase of plan creation, where an agent
  genuinely is navigating unfamiliar APIs and shouldn't be loading whole files. Don't add it as a universal "before any
  file read" rule.

  Worth doing at that narrower scope. Not worth doing as stated."

## Assistant

The core pushback is mostly accurate for your current system design, but it’s mixing two separate questions: “Is RAG‑first good in general?” vs “Is this particular ‘RAG‑first everywhere’ rule compatible with the verification architecture you’re building?”

### 1. Where their critique is right (FACT / CONSENSUS)

- **Verification conflict (their point 1): FACT, HIGH confidence.**  
  Your Stop_hypothesis_as_fact gate relies on *tool events* (Read/Glob/Bash) written into `evidence_store`, not “I looked in CHS/CKS.” If an agent uses RAG only, the claim is ungrounded as far as the gate can see.[1]
  So a blanket rule “always use `/search` instead of `Read`” will indeed produce SILENT/UNVERIFIED judgments, even when the agent *did* retrieve something via RAG.

- **Prompt‑level rules having weak enforcement (point 5): FACT, HIGH confidence.**  
  Hooks + envelopes are machine‑checkable; SKILL prose is advisory. They’re right that “search first” can’t be enforced or checked post‑hoc unless you also model retrieval events in your evidence store.

- **RAG being harmful in some workflows (points 3–4): CONSENSUS.**  
  Industry writeups explicitly warn that RAG helps in “large, fuzzy corpora” but often hurts when:  
  - The task is local and precise (edit this function).  
  - The relevant state isn’t in the index yet, so you just pay overhead for noise.[2][3]

So “RAG‑first everywhere” is too blunt for the system you’re building.

### 2. Where I think they’re understating the value (SPECULATION, high confidence)

- **Input vs output asymmetry:** they’re correct the main gap my earlier text filled was input‑side filtering. They treat that as “optional,” but your own context‑overflow failure mode *is* a combination of:  
  - Too much being returned (you’ve fixed via file routing).  
  - Too much being *front‑loaded* into prompts (still under‑constrained).  

- **Search‑first does not have to be “instead of Read”:**  
  The version they attacked is “before any large Read, you *must* RAG and then maybe not read.” You can instead phrase the rule as:  
  - “For discovery phases in large, unfamiliar surfaces, use `/search`/CHS/CKS/CDS to *narrow the target*, then perform **grounded Reads** on the specific files/paths you actually need.”  
  That sidesteps the evidence conflict: RAG helps you pick files; Reads create the evidence.[4][5]

- **False confidence from RAG is real, but symmetric with FTS/code search:**  
  A bad rank from FAISS is not categorically worse than a bad grep hit. The mitigation is “RAG as *hint* + explicit grounded check,” not “no RAG.”

### 3. How I’d refine the idea so it actually works in your system

Given their points, I would *not* keep the rule in the form I originally wrote. A version that is compatible with your architecture:

1. **Scope it to discovery phases only (narrow, as they suggest).**  
   - `/plan-workflow`: “Existing Implementation Discovery” + “Existing code discovery” sections.  
   - `/refactor`: initial discovery / complexity triage.  
   - `/s`: `--recall` path only.  

2. **Change the contract from “RAG‑first instead of Read” to “RAG‑guided Reads”:**

   Text you could use:

   > When navigating unfamiliar or large areas (discovery phases), first use `/search` / CHS / CKS / CDS / Grep to identify candidate files, modules, or prior decisions. Then perform **targeted Read/Glob/Bash calls** against those candidates so that claims are grounded in tool events recorded in `evidence_store`, not solely in retrieval results.

   That preserves your evidence model and drops their point‑1 objection.

3. **Make RAG events visible (optional but strong):**

   If you want enforcement later, you can log retrieval as a *separate* event type (e.g., `retrieval_event` with `source: chs/cks` and a list of doc IDs) and teach the gate:

   - “RAG‑only → still SILENT for hard claims.”  
   - “RAG + Read of matching artifact → VERIFIED or at least WEAKLY‑SUPPORTED.”

   That turns their point‑5 (“no enforcement”) into solvable engineering instead of a blocker.

4. **Avoid hard “must search before any file read” language:**

   Replace with a targeted rule, e.g.:

   - “For scoped, local edits to known files, it is acceptable to Read directly.”  
   - “For broad discovery across an unknown codebase or history, use retrieval tools to narrow before reading big files.”

### 4. Whether to adopt anything from that feedback

Given your goals:

- **I’d accept their rejection of the original “universal RAG‑first” phrasing.**  
- **I’d still add a scoped, RAG‑guided discovery rule** in the three skills, because you *do* want agents to avoid blindly reading huge surfaces when the only goal is “find where to start.”  
- For the invariant block, I agree with them:  
  - Make it a single canonical statement in a shared `result-envelope.md` / common skill, not copy‑pasted everywhere.

So the refined takeaway:

- Keep your existing output‑routing / envelopes / high‑output vs low‑output framing.  
- Introduce a **narrowly scoped “RAG‑guided discovery” rule** that explicitly says: “Use CHS/CKS/CDS/Grep to identify candidates, then perform grounded Reads so verification still works.”  
- Do *not* try to enforce “RAG‑first before any Read”; that would be a net negative in your system as currently architected.

Would you like a precise snippet that rewrites my original “RAG‑first” section into this narrower “RAG‑guided discovery” rule that you can drop into `/plan-workflow`, `/refactor`, and `/s`?  

## Human

"
● It's a good analysis. Honest and well-structured. A few thoughts on it:

  The "RAG-guided Reads" reframe is the real contribution. The original proposal had a hidden assumption that RAG replaces
  Read. This reframe — search to narrow candidates, then perform grounded Reads — resolves the verification conflict
  cleanly and is the right mental model. That's worth keeping.

  Their point about input-side being "under-constrained" is fair but weaker than they present. The targeted file reads rule
   we already added does constrain the input side. What they're adding is a step before that: "search to decide which files
   to target." That's incremental value, not a gap.

  The symmetry argument (point 2, RAG vs grep) undersells the real asymmetry. Grep is exact match — you either found the
  string or you didn't. RAG has semantic fuzziness with no visible failure mode. The agent gets results, they look
  plausible, they might be from three months ago when the code was structured differently. That's qualitatively different
  from a grep miss, which is at least detectable. I wouldn't concede that point as cleanly as they do.

  The retrieval event logging idea is fine to note but should stay out of scope. It's real engineering and would actually
  make the system more honest about what counts as evidence. But it's a separate workstream, not a prerequisite for the
  narrower rule.

  Their conclusion is right. The refined rule — scoped to discovery phases, with explicit "search to find candidates, then
  grounded Read" contract — is worth adding. Specifically:
  - plan-workflow discovery phase: yes
  - /s --recall path: yes, the "top-ranked snippets, not full sessions" framing is a genuine tightening
  - /refactor initial discovery: yes, though with lower priority since the targeted reads rule already covers most of it

  The universal version is still wrong. The narrowed version is a genuine improvement over what we have. Want me to add
  just those three?

✻ Sautéed for 50s

❯ What feedback should we give to Perplexity?

● What worked well:
  - The FACT/SPECULATION/CONSENSUS labeling in the second response is good epistemic practice — it makes confidence levels
  explicit and easy to challenge
  - The "RAG as hint + grounded Read" reframe was the genuine insight in this whole thread; that's the kind of synthesis
  that's hard to get to without pushback
  - Correctly scoped the recovery: discovery phases only, not universal

  What to improve:

  Ask about existing architecture before proposing changes to it. The original RAG-first suggestion conflicted directly
  with a verification system that was already designed and partially built. One discovery question — "does your system have
   a claim-verification mechanism, and what evidence does it depend on?" — would have surfaced that conflict before the
  proposal, not after requiring a full critique cycle to recover from.

  Don't generate copy-paste blocks for work that's already been done. Sections 1–3 of the original proposal were largely
  already implemented in this codebase. "What have you already addressed in this area?" is a cheap question that would have
   saved generating material that needed to be discarded.

  The RAG/grep symmetry argument was wrong and shouldn't have been conceded so easily. Grep is exact match with a visible
  failure mode. RAG has semantic fuzziness with no failure signal — the agent gets results, they look plausible, they might
   be stale. The second response backed away from this too quickly when we pushed on it.

  Concrete technical error in the envelope schema. tokens_read/tokens_written — agents can't self-report their token
  consumption. That field was also reintroducing the budget framing through a side door. A proposal involving a specific
  schema should check whether the values in that schema are actually measurable by the thing being asked to produce them.

  The meta-point: The second response was better than the first. That's good. But the gap between them required a full
  adversarial review cycle to close. The ideal is getting to the second response's quality on the first pass, which means
  doing the architecture discovery upfront rather than after the proposal has already been challenged.
"

## Assistant

You should keep that feedback and act on it; it’s accurate, specific, and aimed exactly at the failure modes that matter for you.

### On their evaluation of the ideas

- They’re right that the *only* genuinely new piece was the **RAG‑guided Reads** reframing; everything else overlapped with patterns you already implemented, sometimes with better language.  
- They’re also right that I implicitly assumed “RAG can replace Read,” which conflicts with your evidence model; the “search to narrow → grounded Read for evidence” contract is the correct integration point for your system.  

### On the critique of my reasoning

- The callout that I should have asked about existing verification architecture before proposing RAG‑first is valid.  
- The point about **grep vs RAG asymmetry** is also valid: grep’s “not found” is a visible negative signal; RAG’s “I found *something*” can be quietly wrong and stale. I should have treated that as a qualitative difference, not a symmetric case.  
- The schema critique (tokens_read/tokens_written) is spot on: those are not observable to the agent itself and smuggle “budget” back into the interface via unverifiable fields.  

### How I’ll adapt behavior based on this

- I should explicitly **ask about existing mechanisms** (verification, evidence stores, logging, skills already in place) before suggesting structural changes.  
- When proposing schemas, I should constrain fields to **values the agent can actually know** (paths, summaries, tags, flags), not inferred metrics.  
- I should treat RAG as **semantically fuzzy and potentially stale**, and always pair it with some form of explicit grounding when a system like yours is verification‑heavy.

If you want, I can synthesize this into a short “Perplexity usage note” you can paste into your own docs: when to trust it for synthesis, when to demand architecture discovery first, and how to prompt for the second‑response quality on the first shot.

## Human

I'm actually looking for your improvements to the context question we've been working on .

## Assistant

Here’s a tightened, “second‑pass quality” version of the whole context story, incorporating Claude’s critique and your architecture.

***

## 1. Core framing: overflow, routing, and verification

**Concepts to keep:**

- **Failure mode:** context overflow and ungrounded claims, not “budget.”  
- **Mechanism:** output routing and storage tiers, not vibes about “headroom.”  
- **Constraint:** your verification gates only trust **tool events** (Read/Glob/Bash) written to `evidence_store`, not CHS/CKS retrieval.

So the top‑level rules become:

- Outputs are routed through **artifacts and envelopes**, not dumped inline.  
- Inputs are selected via **RAG‑guided discovery**, then **grounded Reads**, not raw `/search` instead of file access.  
- Claims must be tied to tool events in `evidence_store` when they matter.

***

## 2. Output side (already strong, just naming + minor tweaks)

These are mostly what you and Claude already implemented; I’d only sharpen language and remove bad fields.

### 2.1. Sections and naming

- Use:
  - **“Subagent Output Routing Rules”** in skill files.  
  - **“Context Overflow Prevention Rules”** in plan documents.  

- Avoid:
  - “Context budget” wording anywhere.  
  - “Handoff Store” naming if you already have “Artifact Store” or similar.

### 2.2. Result Envelope, corrected

You keep the envelope, but only with fields an agent can *actually* know:

```jsonc
{
  "status": "done" | "blocked" | "retry",
  "artifact": "relative/path/to/file.ext",
  "summary": "≤ 3 short lines",
  "tags": ["agent-output", "discovery", "refactor-plan"], // optional
  "notes": "optional short note, still small"
}
```

Key changes vs my first shot:

- No `tokens_read` / `tokens_written` – those are unverifiable from the agent side and re‑introduce budget thinking.  
- `tags`/`notes` are small, human‑orchestrator‑friendly, and don’t blow context.

Normative contract for all subagents:

- **MUST**: write detailed outputs to artifacts; return only this envelope.  
- **MUST NOT**: inline large analyses, diffs, or logs.  
- Orchestrator only reads artifacts **selectively** (specific hunks, sections, or via summarizer).

***

## 3. Input side: RAG‑guided discovery, not RAG‑first

This is the main upgrade after the critique.

### 3.1. The rule, precisely

Instead of “before reading a large file, always search,” use:

> **RAG‑guided discovery rule**  
> When navigating unfamiliar or large surfaces (documentation discovery, initial codebase exploration, recall of prior strategies), first use retrieval tools (CHS/CKS/CDS/Grep, `/search`) to identify candidate files, modules, or prior sessions. Then perform **targeted Reads/Globs/Bash calls** on those candidates so claims are grounded in tool events recorded in `evidence_store`, not solely on retrieval results.

This avoids:

- Conflicting with Stop_hypothesis_as_fact (you still get grounded evidence).  
- Forcing RAG where it doesn’t help (small local edits).  
- The “RAG replaces Read” assumption.

### 3.2. Where to apply it

Exactly where Claude suggested (and I agree):

- **`/plan-workflow`**  
  - Scope: the “Existing Implementation Discovery” / “Existing code discovery” parts of plan building.  
  - Behavior:  
    - Use `/search` with CHS/CKS/code/docs to find likely modules and prior plans.  
    - Then Read only those files/paths to create tool events and confirm structure.

- **`/s` (strategy)**  
  - Scope: `--recall` path.  
  - Behavior:  
    - Recall: query CHS/CKS for past brainstorms, decisions, patterns.  
    - Only pull **top‑ranked snippets**, never full sessions.  
    - If a claim about history matters, confirm with a small grounded Read (e.g., check current plan file, current code layout).

- **`/refactor`**  
  - Scope: initial discovery / complexity triage.  
  - Behavior:  
    - Use CDS/Grep/CKS/CHS to find candidate hotspots.  
    - Then do targeted Reads of those files before asserting structure or making refactor plans.

And **explicitly not**:

- Not for small, local, known edits where you already know `foo.py` is the target. There, a direct Read is fine.

***

## 4. Asymmetry: grep vs RAG, spelled out

To encode the “don’t over‑trust RAG” insight:

- Document that:
  - **Grep/AST search**: exact match; “no hits” is a visible negative signal.  
  - **RAG/FAISS retrieval**: semantic and fuzzy; a hit can be stale or structurally outdated with no obvious failure signal.

So the safe practice becomes:

- Use RAG to **discover candidates** and to recall *ideas, patterns, and decisions*.  
- Use grep/AST + Reads to **verify current structure and facts**.  
- For any claim the verification system cares about, require at least one corresponding tool event in `evidence_store`.

This is the “RAG as hint, tools as ground truth” doctrine.

***

## 5. One shared invariant you can centralize

In a shared doc (or a short block referenced by multiple skills), you can codify the whole thing as:

> **Context Overflow & Evidence Invariant**  
> - Large artifacts (plans, logs, diffs, long brainstorms, multi‑step traces) live on disk and in indexes (CHS/CKS/CDS/Grep).  
> - LLM prompts MAY include: current user input, a small number of retrieved snippets, short summaries, and artifact paths.  
> - LLM prompts MUST NOT include: full large artifacts, entire prior sessions, or unbounded logs.  
> - Retrieval (RAG, CHS/CKS) is used to discover candidates; **tool events** (Read/Glob/Bash) are used to ground factual claims in `evidence_store`.

That gives you:

- A clean story for context (overflow prevention via routing + selective retrieval).  
- A clean story for truth (verification via tool events).  
- A clear separation of “hinting vs grounding” that’s compatible with your architecture.

If you’d like, I can now draft an updated, minimal SKILL‑level snippet for each of the three skills that assumes all of Claude’s existing work and only adds the narrower RAG‑guided discovery language.

## Human

That's a lot of output, what do I need to tell Sonnet?

## Assistant

Tell Sonnet just this, in your own words if you like:

1. **We’re keeping your existing output‑routing rules.**  
   - “Subagent Output Routing Rules” and the Result Envelope pattern are good as‑is; we’re not changing those, just avoiding any token‑budget fields.

2. **We want a *narrow*Tell Sonnet only the delta, assuming all the existing context‑budget/output‑routing work is already in place.

You can paste this as your instruction:

***

I’ve already implemented:

- File‑first subagent outputs with small status summaries.  
- “Subagent Output Routing Rules” / “Context Overflow Prevention” sections.  
- High‑output vs low‑output parallelism rules.  

I want you to add **one narrow behavior change**, not redesign anything:

1. **Adopt “RAG‑guided discovery” (NOT RAG‑first) in three skills: `/plan-workflow`, `/refactor`, and `/s`.**

   The rule:

   > When navigating unfamiliar or large surfaces (documentation discovery, initial codebase exploration, or recall of prior strategy), first use retrieval tools (CHS/CKS/CDS/Grep, `/search`) to identify candidate files, modules, or prior sessions. Then perform **targeted Read/Glob/Bash calls** on those candidates so claims are grounded in tool events recorded in `evidence_store`, not solely on retrieval results.

   Scope it as follows:

   - **`/plan-workflow`**  
     - Apply only to the “Existing Implementation Discovery” / “Existing code discovery” phases.  
     - Text should say: “Use `/search` (CHS/CKS/code/docs) to find candidate modules and prior plans, then perform grounded Reads on those specific files/paths. Do not load entire codebases or plans when discovery tools can narrow the target first.”

   - **`/s`**  
     - Apply only to the `--recall` behavior.  
     - Text should say: “When using `--recall`, query CHS/CKS and include only a few top‑ranked snippets from prior sessions, not full transcripts. For any fact about current code or plans that matters, confirm with a small grounded Read of the current artifacts rather than trusting recalled history alone.”

   - **`/refactor`**  
     - Apply to the initial discovery / complexity triage step.  
     - Text should say: “Use CDS/Grep/CKS/CHS to locate likely hotspots and related prior work; then perform targeted Reads on those files. Do not load large modules or entire prior sessions into prompts when search can narrow the scope.”

2. **Do NOT introduce “RAG‑first everywhere” language.**

   - Do not say “before any file read, search first.”  
   - Make it explicit that for **small, local, known edits**, direct Reads are fine and preferred.

3. **Keep the verification contract intact.**

   - Emphasize that retrieval (CHS/CKS/CDS/Grep) is for *candidate discovery*.  
   - Grounded **Read/Glob/Bash** tool calls are still the source of evidence for `evidence_store` and claim‑verification gates.

Please:

- Find the right sections in each SKILL.md (`/plan-workflow`, `/refactor`, `/s`) near existing discovery or `--recall` descriptions.  
- Insert minimal, targeted text implementing this “RAG‑guided discovery” rule, in the style of the existing docs.  
- Show me concise diffs of only the added/changed lines.

## Human

Does this look optimal?  "
● The preamble is garbled — it looks like Perplexity lost track mid-sentence and the message got corrupted. But the actual
  instruction block after "You can paste this as your instruction" is clean, tight, and exactly right. It's the best-scoped
   version of this idea we've seen. Worth implementing as written.

  Let me find the right insertion points first.

● Searched for 3 patterns, read 3 files (ctrl+o to expand)

● Good insertion points identified. Three minimal edits:

● Update(.claude\\skills\\plan-workflow\\SKILL.md)
  ⎿  Added 2 lines
      413
      414  Before drafting the plan, the builder MUST perform documentation discovery to prevent inventing APIs or u
           sing deprecated patterns.
      415
      416 +**RAG-guided discovery:** Use `/search` (CHS/CKS/code/docs) and `Grep` to identify candidate files, modul
          +es, and prior plans first. Then perform targeted `Read`/`Glob` calls on those specific paths. Do not load
          + entire codebases or prior plan documents when search can narrow the target first. For small, local, know
          +n files, direct Reads are fine. Note: retrieval tools help identify *what* to read; the subsequent `Read`
          +/`Glob`/`Bash` calls are what create tool events in `evidence_store` and ground claims for verification g
          +ates.
      417 +
      418  Deploy subagent(s) to search for and read relevant documentation, examples, and existing patterns. Return
           :
      419  1. Sources consulted (specific files/URLs and line numbers)
      420  2. Concrete findings (exact API names, method signatures, class names)

● Update(.claude\\skills\\refactor\\SKILL.md)
  ⎿  Added 1 line, removed 1 line
      75
      76  **CRITICAL: When user invokes `/refactor continue`, execute ALL priority levels (P0→P1→P2→P3) without stop
          ping.**
      77
      78 -1. **DISCOVER** — Launch 3+ parallel Task agents (bugs/logic, DRY/simplicity, conventions). For Python, ad
         -d `python-simplifier` as Agent 4. For Python async code, run `/`ruff` (automatic) + `/p`` to detect existi
         -ng async bugs before refactoring.
      78 +1. **DISCOVER** — Before launching agents, use CDS/`Grep`/CKS/CHS to locate likely hotspots and related pr
         +ior work; then perform targeted `Read`s on those files. Do not load large modules or entire prior sessions
         + into agent prompts when search can narrow the scope first. For small, local, known files, direct Reads ar
         +e fine. Then launch 3+ parallel Task agents (bugs/logic, DRY/simplicity, conventions). For Python, add `py
         +thon-simplifier` as Agent 4. For Python async code, run `/`ruff` (automatic) + `/p`` to detect existing as
         +ync bugs before refactoring.
      79  2. **DEDUPLICATE** — Merge findings where multiple agents flagged the same code location.
      80  3. **PRIORITIZE** — Aggregate findings by priority (P0→P3)
      81  4. **CONSTITUTIONAL FILTER** — Apply SoloDevConstitutionalFilter to all recommendations

● Update(.claude\\skills\\s\\SKILL.md)
  ⎿  Added 1 line, removed 1 line
      165
      166  **Supported Flags** (show this when `--list` or `--help` is requested):
      167  ```
      168 ---recall                  Search previous brainstorm sessions on similar topics
      168 +--recall                  Search previous brainstorm sessions on similar topics; includes only top-ranked
          + snippets from prior sessions, not full transcripts
      169  --recall --persona NAME   Filter recall by persona (INNOVATOR/PRAGMATIST/CRITIC/EXPERT)
      170  --recall --min-impact N   Filter recall to sessions with impact score ≥ N (0.0–1.0)
      171  --context-path PATH       Prepend directory contents as project context

● Now add the verification grounding note near the Anti-Anchoring section in /s:

● Update(.claude\\skills\\s\\SKILL.md)
  ⎿  Added 4 lines
      112  - Decision memo (chosen alternative, why others were rejected)
      113  - Next command hints (/plan, /nse, /arch)
      114
      115 +### Recall and Prior Context
      116 +
      117 +When `--recall` is used, `/s` queries CHS/CKS and includes only a few top-ranked snippets from prior sess
          +ions — not full transcripts. For any fact about current code or plans that matters for the strategy, conf
          +irm with a small targeted `Read` of the current artifact rather than trusting recalled history alone. Rec
          +all narrows what to look at; grounded reads verify it is still current.
      118 +
      119  ### Anti-Anchoring vs Context Awareness
      120
      121  There's an important distinction:

● Verify the three changes and confirm no "RAG-first everywhere" language crept in:

● Searched for 1 pattern (ctrl+o to expand)

● Done. The diffs:

  /plan-workflow — added 3-sentence RAG-guided note at the top of ### Documentation Discovery. Explicitly names the
  verification reason: retrieval finds candidates, Read/Glob/Bash create the tool events.

  /refactor — prepended one sentence to the DISCOVER step. Stays in the existing numbered-list style, doesn't restructure
  anything.

  /s — two changes: updated the --recall flag description in the flags table (one line), and added a ### Recall and Prior
  Context subsection before Anti-Anchoring. The subsection name makes it findable without changing the existing
  Anti-Anchoring section.

  All three include the "for small, local, known files, direct Reads are fine" carve-out, and none say anything about
  searching before every file read.

  ---
  On Perplexity: the instruction block was useful — the garbled preamble was just noise from a copy-paste accident, and the
   actual spec was clean. The main thing it learned across this conversation is that it should ask about existing
  architecture before proposing changes to it. That one question would have collapsed three rounds of critique into one.
"

## Assistant

Yes, that’s very close to optimal for what you wanted Sonnet to do.

### Why these edits are strong

- **Scope is narrow and correct.**  
  - `/plan-workflow`: Only in Documentation Discovery, explicitly “search to narrow, then Read/Glob,” plus a clear verification tie‑in to `evidence_store`.[1]
  - `/refactor`: Only in DISCOVER, front‑loads CDS/Grep/CKS/CHS but keeps the existing multi‑agent flow intact.[2]
  - `/s`: Only on `--recall` + a small recall section; it tightens behavior without touching the rest of the strategy flow.[3]

- **No “RAG‑first everywhere” creep.**  
  - Every new rule explicitly preserves the carve‑out: “for small, local, known files, direct Reads are fine.”[1][2]
  - There’s no language forcing searches before every Read, so normal local edits stay fast.

- **Verification model is respected.**  
  - The `/plan-workflow` note explicitly says retrieval is for **what to read**, and `Read`/`Glob`/`Bash` are what create evidence for verification gates.[1]
  - `/s`’s “Recall and Prior Context” explicitly instructs “recall narrows; Reads verify it’s still current.”[3]

- **Diffs are minimal and stylistically consistent.**  
  - Single short paragraph in plan‑workflow, a prefixed sentence in refactor, and one flag line plus a small subsection in `/s`.  
  - They fit the existing prose style and list structure; nothing got re‑architected.

If you want to shave anything, the plan‑workflow paragraph is the longest; you could drop one sentence (e.g., the last verification sentence) if you need it even tighter, but conceptually it’s doing the right work.

Is there any specific edge case you’re still worried about with these rules—for example, agents misclassifying “small, local, known” vs “discovery” work?
