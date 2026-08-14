---
title: "the latest version of claude code has 1M context.  But the cheaper models I'm using wth it don't have 1M context.  How c"
date: "2026-05-01"
mode: "COPILOT"
uuid: "1f7935b7-56a3-4f3f-89e7-46e90acd0221"
entry_count: 2
---

## Human

the latest version of claude code has 1M context.  But the cheaper models I'm using wth it don't have 1M context.  How can I limit the context claude code expects the models to have?

## Assistant

You can’t change the *actual* context window of the cheaper models, but you **can** make Claude Code behave as if it had a smaller window by (a) switching away from the 1M model where possible and (b) forcing more aggressive compaction / shorter history so the IDE agent never tries to fill 1M tokens.[1][2][3]

Below are the practical levers you have today, plus some workflow patterns that mimic a “smaller-context” Claude Code.

***

## 1. Turn off / avoid the 1M model

In the Claude UI and in Claude Code, the 1M context variant is often auto‑selected if your account has access.[2]

To avoid Claude Code behaving like it has 1M context:

- In regular chats: explicitly select a non‑1M model (e.g. a 200k Sonnet/Opus) instead of the “1M” variant when you start the session.[4][3]
- In Claude Code: start the coding session from a non‑1M chat, or, if you see a command interface (like `/model`), use it to switch to a 200k model and keep it there. Some users have reported doing this in Max sessions via `/model opus` or similar to move off the 1M code model.[1]

This doesn’t change the cheap models’ context, it just prevents the IDE from planning around “there’s 1M tokens available.”

***

## 2. Force more aggressive context trimming

Even when you’re not on the 1M model, Claude Code will try to stuff a lot of history and file content into the window unless you keep it tight.[5][2]

Use these patterns:

- Manually compact often  
  - If there’s a `/compact` or “summarize conversation” feature, call it *before* things get huge, not after you hit the wall. Users report this materially reduces context bloat.[5][1]

- Periodically **start a fresh Claude Code session**  
  - When the conversation starts to feel sluggish or you see the model referencing very old state incorrectly, spin up a new chat and re‑attach only the files that matter for the current task. This behaves like imposing an artificial 20–50k “mental window” instead of relying on 200k+.[6]

- Prune project / workspace instructions  
  - Long project instructions and huge markdown notes get pulled into context over and over. Anthropic’s own docs suggest keeping instructions concise and using them only for essentials.[3]
  - Move detailed docs out of always‑on instructions and into files the model can open on demand.

These steps don’t literally change the tokens‑limit, but they make the *effective* context much smaller and more compatible with cheaper models’ behavior.[6]

***

## 3. Reduce what Claude Code loads from your repo

The IDE agent can burn context quickly by pulling large files, logs, and long markdown.[2][5]

Concrete tactics:

- Exclude noisy files from analysis  
  - Use `.gitignore` plus any IDE‑specific ignore mechanism (if available) to keep generated artifacts, huge logs, and build outputs out of its “known world.” This reduces what the tool ever considers loading.

- Ask it to work file‑by‑file  
  - Instead of “understand the whole repo,” say “only consider these 2–3 files for this task unless I say otherwise.” This keeps prompts small, which better matches a non‑1M model’s sweet spot (typically 20k–80k per request).[6]

- Compress long terminal / test output  
  - Summarize failing test logs into short bullet lists before pasting them or ask Claude to summarize them once, then refer back to the summary instead of the raw logs in subsequent turns. This is explicitly recommended as a way to avoid hitting context limits.[7][5]

***

## 4. Adopt a “narrow‑context by design” workflow

Production guidance from multiple sources is that *even when* you have 200k–1M available, you get better reliability if you operate in a much smaller working window (tens of thousands of tokens) and only occasionally do massive context sweeps.[4][6]

Patterns that line up with cheaper models:

- Episodic tasks  
  - Treat each significant subtask as a mini‑project: new chat, brief instructions, only relevant files.  
  - When done, close it and start fresh for the next task; don’t maintain a mega‑thread that accumulates thousands of turns.[3][6]

- Retrieval over giant prompts  
  - Instead of “read this entire codebase and answer questions,” keep most of the repo *out* of immediate context and let the model open specific files on demand. This emulates a RAG‑style approach where the prompt stays small.[3]

- Aggressive summarization of past decisions  
  - Periodically ask: “Summarize the key architectural decisions and constraints we’ve made so far in ≤ X tokens; from now on, rely on that summary.” Then in a new session, just paste that summary and continue. This is how Anthropic describes managing long conversations in general.[3]

***

## 5. What you *cannot* do (as of now)

Based on current public info:

- You cannot set a numeric “max context size” knob in Claude Code (e.g., “pretend you only have 32k tokens”) from the UI or from a config file. There’s no documented setting like that.[5][3]
- You cannot make the 1M IDE agent itself run on a smaller window if Anthropic’s backend has hard‑wired it, beyond switching models and managing your prompts as above.[4][2]

So the control is indirect: choose a smaller‑window model where possible, and design your workflow so the agent never *tries* to build 1M‑token prompts.

***

Given your setup, the single most powerful lever will probably be *how aggressively you reset and compact sessions*. Would you rather minimize manual intervention (auto‑compact, short sessions) or are you comfortable with a more “disciplined” workflow where you frequently start new chats and paste in a carefully‑curated short context summary?

## Human

Best practices for context compression in Claude Code

## Assistant

Context compression in Claude Code is mostly about deciding what *must* persist (rules, architecture, decisions) vs what can be lossy (chat history, tool noise), then using compaction, CLAUDE.md, and short sessions to enforce that separation.[1][2]

Below is a set of concrete, Claude-Code‑specific practices you can operationalize.

***

## 1. Treat CLAUDE.md as “compaction‑proof memory”

Claude Code uses three layers: system prompt (incl. CLAUDE.md), conversation history, and project files; only conversation history is aggressively compacted.[2][1]

Best practices:

- Put **all non‑negotiable rules** in CLAUDE.md: architecture constraints, naming conventions, things Claude must never touch, security rules, build commands, and formatting expectations.[1][2]
- Do **not** rely on “remember this for the rest of the session” in chat; compaction will drop these first. Instead, convert durable instructions into bullets in CLAUDE.md as soon as they stabilize.[1]
- Encode cross‑session decisions as files: `ARCHITECTURE.md`, `DECISIONS.md`, `WORKFLOW.md`. Claude can re‑read them when history has been compressed away.[2][1]

Effective mental model: CLAUDE.md = *ROM*, conversation = *RAM that can be lossy*, repo files = *re-loadable storage*.

***

## 2. Use compaction intentionally, not reactively

Claude’s own cookbook and community experience both recommend *deliberate* compaction thresholds instead of waiting to hit the wall.[3][4][1]

Patterns to borrow (even if you’re not directly coding against the API):

- Prefer **early compaction**  
  - Anthropic suggests compaction once token usage passes a configurable threshold, often 50–100k for 200k windows, so you preserve quality before context rot sets in.[3]
  - For human use with `/compact`, call it when the session *starts feeling dense*, not after a failure. External guides recommend around 60% utilization as a heuristic.[4]

- Think in phases  
  - At each checkpoint (e.g., “basic scaffolding done”, “feature X implemented”), run compaction or manually ask: “Summarize everything we’ve done so far, focusing on A/B/C.” Then treat that summary as the new baseline.[5][1]
  - This matches Anthropic’s recommended “multi‑phase workflows with compaction at natural checkpoints.”[3]

- Keep sessions short on purpose  
  - Practitioners working with Claude Code daily report better reliability when they break work into 30–60 minute focused sessions instead of 3–4 hour mega‑threads that compact multiple times.[1]
  - Start fresh; rely on CLAUDE.md + a short “what we’re doing now” summary instead of a gigantic compressed history.[1]

***

## 3. Customize what compaction *preserves*

Default compaction aims to keep “what to do next” (recent code, tool results, errors) at the expense of older decisions and nuanced instructions.[2][1]

To mitigate:

- Customize your **compact prompt**  
  - Guides explicitly recommend tailoring the compact instruction to your domain: e.g. “When compacting, preserve: current task definition, unresolved TODOs, file paths and functions recently modified, and any architectural decisions that constrain future work.”[6][1]
  - If you’re using Claude’s SDK or custom skills, pass a domain‑specific prompt to the compactor to anchor what matters.[6][3]

- Use **anchored summaries** rather than freeform ones  
  - Frameworks like “Anchored Iterative Summarization” keep a stable, structured header (project goals, constraints, key decisions) and append deltas as the session progresses.[6]
  - In practice: maintain a “Session Summary” file with sections like: Context, Decisions, Open Questions, Modified Files. Periodically ask Claude to update it *instead of* only compressing chat.[6]

- Encode decisions in artifacts, not just chat  
  - Decision context is the first casualty of compression (why we chose approach A over B, what tradeoffs we accepted).[1]
  - When you finalize a choice, have Claude write/update `DECISIONS.md` with: problem, options considered, chosen approach, reasons, and implications. This survives compaction and can be re‑loaded on demand.[2][1]

***

## 4. Control token growth at the source

Compaction is a safety net; better is to slow token growth so you need it less.[3][2][1]

Concrete practices:

- Constrain scope per session  
  - Limit a session to a **single feature or bug** and a small set of files. Tool‑heavy workflows with clear boundaries benefit from low compaction thresholds (5k–20k tokens in API scenarios) exactly because you don’t need long history between units.[3]
  - Explicitly say: “In this session, only work in files X, Y, Z unless I say otherwise.”

- Aggressively summarize large tool outputs  
  - Long logs, traces, or search results explode context. Cookbook examples show using tools to summarize tool results before reinserting them into context.[2][3]
  - Pattern: “Summarize this test output into ≤ N bullets focused on failing cases, expected vs actual, and suspected root causes; forget line‑by‑line detail.”

- Use retrieval instead of “read everything”  
  - The context‑engineering docs highlight that Claude Code itself layers compaction with memory (CLAUDE.md, auto‑memory) rather than trying to keep whole histories in every prompt.[2]
  - Emulate that: let Claude open files as needed; avoid instructions like “read the entire repo.” Ask questions that operate on specific files or directories.

***

## 5. Design your own compression loop (if you build agents)

If you’re orchestrating Claude Code‑like behavior via the API or custom skills, you can implement more explicit compression control.[6][3][2]

Patterns from Anthropic’s cookbook and external skills:

- Token‑budget thresholds  
  - Track the running token count; when it exceeds a threshold, trigger a compaction pass that summarizes older messages, keeping the last K steps verbatim.[3]
  - Different thresholds fit different workloads: 5k–20k for many small independent items, 50k–100k for multi‑phase tasks, 100k+ for history‑heavy tasks.[3]

- Context editing and tool‑result clearing  
  - Claude’s API supports server‑side context editing and clearing bulky tool results while retaining their summaries.[2]
  - Use this to drop huge intermediate outputs while keeping high‑level conclusions in the conversation.

- Structured memory objects  
  - Some Claude Code–oriented skills store persistent “memory objects” (e.g. per‑file change logs, decision records) in a separate store and only inject relevant snippets per step.[6][2]
  - This gives you a higher‑level, queryable memory instead of relying on raw compressed chat.

***

## 6. Concrete checklist for day‑to‑day Claude Code use

Distilling the above into something you can operationalize immediately:[4][1][3][2]

- Move all hard rules into CLAUDE.md and project docs; don’t depend on chat for anything that must survive compaction.  
- Keep sessions narrow and time‑boxed; start fresh rather than pushing into multiple compactions.  
- Run `/compact` (or equivalent) at natural milestones, slightly *before* things feel unstable.  
- Maintain a small `DECISIONS.md` / `SESSION_NOTES.md` that you periodically refresh via Claude.  
- Summarize big logs and tool results aggressively; avoid re‑pasting them raw.  
- Ask Claude to operate on small, explicit file sets per task, not the entire repo.

If you share your current Claude Code setup (VS Code extension vs browser, any custom skills/agents you’ve added), I can sketch a very concrete “ritual” for when to compact, what to put in CLAUDE.md, and how to structure decisions and notes so you virtually never lose anything important.
