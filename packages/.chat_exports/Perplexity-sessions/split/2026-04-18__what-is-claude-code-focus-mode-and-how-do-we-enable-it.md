---
title: "what is claude code focus mode and how do we enable it?"
date: "2026-04-18"
mode: "COPILOT"
uuid: "73eb660d-474c-4817-9dde-62e4e80e2efb"
entry_count: 29
---

## Human

what is claude code focus mode and how do we enable it?

## Assistant

Claude Code “focus mode” is just a transcript/view mode that hides most of the tool spam and keeps the chat pane compact so you can concentrate on the latest exchange.  It doesn’t change the model’s behavior; it changes how the conversation is rendered (vs the default or “verbose” view, which shows every tool call and log line).[1]

There are two relevant knobs:

1. A *sticky* `/focus` toggle during a session (transcript view)
2. A *default* `viewMode` setting in Claude Code’s config so new sessions start in focus/verbose/default.[1]

***

## What is Focus Mode (exactly)?

Claude Code has a `viewMode` setting that controls the transcript view: `default`, `verbose`, or `focus`.[1]

- `default` – normal chat with some tool detail.[1]
- `verbose` – more detailed logs and tool output.[1]
- `focus` – hides most of the noise so you mostly see your prompts and Claude’s replies.[1]

The docs note that `viewMode` “overrides the sticky `/focus` selection when set,” meaning you can either:
- flip it per-session with `/focus`, or  
- lock your preferred mode globally with `viewMode`.[1]

***

## How to enable Focus Mode (CLI / TUI / “Claude Code app”)

Assuming you’re using the standard Claude Code REPL/TUI:

### 1. Enable it for the current session

Use the slash command:

```text
/focus
```

This switches the transcript into focus view for that session until you change it or something overrides it.[1]

If you want to go back to the more detailed view in the same session, use:

```text
/verbose
```

or

```text
/default
```

depending on what you prefer.[1]

### 2. Make Focus Mode the default view

Claude Code has a settings system you can reach via `/config` or `/tui`.[1]

Steps:

1. In Claude Code (terminal REPL), run:

   ```text
   /config
   ```

   or, if you’re already in the TUI:

   ```text
   /tui
   ```

   This opens the tabbed settings interface.[1]

2. Find the `viewMode` setting. In the docs it’s listed like:

   ```text
   | viewMode | Default transcript view mode on startup: "default", "verbose", or "focus". Overrides the sticky `/focus` selection when set | "verbose" |
   ```  
[1]

3. Change `viewMode` to `"focus"`.

After that, every new Claude Code session will start in focus mode by default, regardless of whether you previously ran `/focus` in another session.[1]

***

## How this interacts with other settings

- `viewMode` is the *startup* view; it overrides whatever you last did with `/focus` between sessions.[1]
- Within a session, you can still switch modes with `/focus`, `/verbose`, or `/default`.[1]
- This is purely a UX/display-level setting; it doesn’t affect permission modes, plan/auto modes, or the model used (Opus/Sonnet/etc.). Those are controlled elsewhere.[2][1]

***

If you tell me whether you’re primarily using:
- the terminal REPL,
- Claude Desktop’s built-in Claude Code,
- or the VS Code extension,

I can give exact keystrokes and where to click for your specific setup.

## Human

I am using the Claude Code terminal REPL on Windows

## Assistant

Since you’re on the Claude Code terminal REPL (likely via WSL on Windows), here’s exactly how focus mode works *there*.

### 1. Check whether `/focus` is available in your build

Focus mode is rolling out and not everyone has the `/focus` slash command yet.[1]

In the Claude Code REPL:

```text
/focus
```

- If it works, you’ll see the transcript UI change (fewer tool logs, more compact messages).  
- If you get `Unknown command` or similar, your version/tenant doesn’t have the command yet and you’ll need to rely on `viewMode` defaults once they land in your build, or just stick with the existing views for now.[1]

There’s also at least one known quirk where `/focus` only appears after some UI-related flags are enabled on Anthropic’s side, so if it’s missing, it’s not something you can fix locally.[1]

### 2. If `/focus` works: use it per-session

Once available, focus mode is just a transcript view toggle, not a different “mode” in the sense of planning/auto.[2]

Per session:

```text
/focus      # switch to focus view
/verbose    # show more logs again
/default    # go back to standard view
```

These commands only affect the *current* REPL session.[2]

### 3. Configure default view via `/config` (when `viewMode` lands)

Claude Code has a `viewMode` setting that controls the startup transcript view: `"default"`, `"verbose"`, or `"focus"`.[2]

In the terminal REPL:

1. Open settings:

   ```text
   /config
   ```

   (`/settings` is an alias). This opens the tabbed settings UI in the REPL.[3][2]

2. In the settings, find `viewMode`. In the docs it’s described as:

   > `viewMode` – Default transcript view mode on startup: `"default"`, `"verbose"`, or `"focus"`. Overrides the sticky `/focus` selection when set.[2]

3. Set it to `focus`.

After that, new sessions will start in focus mode even if you haven’t run `/focus` yet.[2]

### 4. Reality check for **today**, on Windows terminal / WSL

Given current docs + chatter:

- `viewMode` is formally documented, but not all builds expose `"focus"` yet.[2]
- `/focus` is visible for some users, totally missing (“Unknown command”) for others.[1]

So, your exact path:

1. In your *WSL* Claude Code REPL, try:

   ```text
   /help
   ```

   and then type `/` to bring up the slash-command list; see if `focus` appears there.[3]

2. If `focus` is listed:
   - Use `/focus` now.
   - Then open `/config` and set `viewMode` to `focus` so it sticks.[2]

3. If `focus` is **not** listed, or `/focus` says unknown:
   - You don’t have the flag yet; there’s nothing to toggle locally.[1]
   - The only workaround is to live with the current transcript view until Anthropic rolls the feature to your account/region.

***

If you paste the output of `/help` (and maybe a screenshot or text of your `/config` page), I can tell you definitively whether focus mode is present in your specific build and what, if anything, you can tweak right now.

## Human

it's not available.  Can we recreate it?

## Assistant

Yes, **partially**. We can recreate the *effect* of focus mode by filtering Claude Code’s terminal output, but we probably cannot recreate the real native feature exactly unless Anthropic exposes the underlying transcript/view hooks.[1][2]

FACT: the documented native mechanism is a transcript `viewMode` plus a `/focus` toggle, and in your build that capability is not exposed yet.  FACT: because the native feature appears account/build-gated, a local clone has to work as an overlay or wrapper, not as a true built-in mode.[2][1]

## What is feasible

The practical options are:

- A PowerShell wrapper that runs `claude` and hides noisy transcript lines, simplest and lowest risk.[1]
- A richer custom TUI that tails/parses Claude session output and renders a cleaner “conversation-first” view, more work but closer to real focus mode.[3][4]
- A direct patch to Claude Code internals, only viable if the package exposes stable rendering hooks; I do **not** have evidence from current docs that it does.[1]

I created the first option for you: a Windows-friendly PowerShell wrapper that filters many box-drawing/log/tool-status lines so the transcript reads more like a compact focus view. This is **not** a real Claude Code patch; it is a display filter layered on top.[2][1]

## What I made

The wrapper script:

- launches `claude`,
- passes through normal arguments,
- suppresses many obvious tool/log/transcript-chrome lines,
- leaves most assistant/user text visible.[4]

The key caveat is uncertainty around Claude Code’s exact terminal behavior: if it uses a full-screen interactive terminal flow in your setup, any stdout/stderr wrapper may be imperfect, because TUIs often rely on terminal control sequences rather than plain line-oriented output.  So this is best treated as a first-pass approximation, not a guaranteed drop-in replica.[5][6]

## How to use it

From PowerShell, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\claude-focus-wrapper.ps1
```

Or pass normal Claude args through:

```powershell
powershell -ExecutionPolicy Bypass -File .\claude-focus-wrapper.ps1 --resume
powershell -ExecutionPolicy Bypass -File .\claude-focus-wrapper.ps1 --dangerously-skip-permissions
```

You should tune the regex list inside the script after one or two real sessions, because the right filter set depends on the exact output patterns your Claude build emits. That is the fastest path to a usable pseudo-focus mode.[4][2]

## Best next step

The most robust version would be a small Node or Python TUI that does all of this:

- spawns Claude in a subprocess,
- classifies lines into `assistant`, `user`, `tool`, `status`, `diff`, `command`,
- lets you toggle hidden categories with hotkeys,
- optionally keeps a split view: compact transcript on top, raw logs on demand below.[7][3][5]

That approach is much closer to native focus mode than a regex-only wrapper, and it matches your stack better if you want something maintainable in TypeScript. Would you like a proper Node/TypeScript terminal app version next?

## Human

how about as an output style?

## Assistant

Yes — that is probably the **best** workaround. Claude Code now supports output styles, and they modify how Claude responds by adding instructions to the system prompt, affecting tone and format rather than core capabilities.[1]

The important distinction is:

- Focus mode = transcript/view rendering, native UI concern.[2]
- Output style = how Claude writes its replies, system-prompt concern.[1]

So you cannot fully recreate native focus mode as an output style, but you *can* get 70–90% of the user experience by forcing Claude to answer in a compressed, low-noise format.[2][1]

## What an output style can do

A custom output style can tell Claude to:

- avoid narration about tool use,
- skip verbose preambles,
- suppress long step-by-step chatter unless asked,
- default to compact bullets, diffs, commands, and next actions,
- keep responses “conversation-first” instead of “process-first.”[1]

FACT: custom output styles are Markdown files with frontmatter and prompt text, and Claude Code supports creating them either through files or the `/output-style:new` flow.  FACT: output styles are intended for exactly this kind of repeated response-shaping use case.[3][1]

## Main limitation

Output styles change *response behavior*, not the surrounding terminal chrome or built-in transcript event rendering.  So if the noise you dislike is Claude’s own explanatory prose, output styles are ideal; if the noise is tool banners, box drawing, status lines, or UI log events, output style alone will not remove those.[2][1]

That means the strongest setup is:

- custom output style for compact answers,
- native `/focus` later when Anthropic exposes it,
- optional wrapper only if terminal chrome still bothers you.[4][1][2]

## Recommended style

For your use case, I’d define a style like this conceptually:

- Default to terse, high-density answers.
- No narration of obvious actions.
- Put the answer first.
- Use bullets only when they improve scan speed.
- Show commands/code without extra commentary.
- State assumptions and uncertainty explicitly.
- Only expand reasoning when asked.[1]

A good name would be something like `focus-compact` or `architect-dense`. Claude Code lets you create and switch styles from `/output-style`, and custom styles can live in global or project-specific output-style folders.[5][3][1]

## Practical recommendation

For you, I would treat output style as the primary workaround, because it is lower friction and more stable than wrapping terminal output.  The wrapper is still useful only if you specifically want to suppress transcript chrome that the model itself does not control.[2][1]

Would you like me to draft a high-signal custom output style file optimized for your preferences, with `keep-coding-instructions: true` so Claude still behaves like Claude Code while answering in a pseudo-focus style?

## Human

yes

## Assistant

Yes — I drafted a custom Claude Code output style tuned for your preferences: dense, answer-first, low-noise, explicit about uncertainty, and still compatible with Claude Code’s coding behavior via `keep-coding-instructions: true`.[1]

It is designed to approximate a pseudo-focus mode at the *response layer*, not the transcript UI layer, so it will reduce verbosity in Claude’s replies but will not remove native terminal chrome or tool-rendering noise by itself.[1][2]

## What this style does

The style tells Claude Code to:

- answer directly first,
- avoid narrating obvious process,
- compress formatting by default,
- challenge premises when needed,
- state uncertainty and assumptions clearly,
- prefer actionable commands and compact structure over long prose.[1]

I tuned it around your stated preferences for high information density, explicit tradeoffs/risks, readable non-JSON output, and technical bias toward minimal-change system guidance.

## Install

Claude Code supports custom output styles as Markdown files with frontmatter, and the docs describe using `/output-style` and `/output-style:new` to manage them.[1]

Use the included install notes, then in Claude Code select it with:

```text
/output-style
```

or create/manage styles with:

```text
/output-style:new
```

## Fit and limits

This is the right workaround if your main complaint is that Claude’s *answers* are too chatty.  It is not enough if your complaint is mostly about terminal transcript scaffolding, since native focus mode is a separate view/rendering concept.[2][1]

The strongest setup is likely:
- this custom output style now,
- native `/focus` later when your build gets it,
- optional wrapper only if the terminal chrome remains the main annoyance.[3][2][1]

Would you like a second variant optimized specifically for code review output, with fixed sections like `Context`, `What changed`, `Tradeoffs`, `Risks`, and `Next steps`?

## Human

Can we make it include that adaptively?

## Assistant

Yes. An output style can be written to apply sections like `Context`, `Tradeoffs`, `Risks`, and `Next steps` **adaptively** instead of forcing them on every reply, because output styles are just system-prompt instructions about formatting and structure.[1]

The right pattern is conditional rules such as: use those sections only when the task is design/review/architecture-heavy; skip them for simple factual answers, short commands, or straightforward fixes. That keeps the style dense without becoming rigid or noisy.[2][1]

## Best approach

I would change the style from “always use these headings” to something like:

- For short factual questions: answer directly in 1–3 sentences.
- For implementation tasks: use `Plan`, `Changes`, `Risks`, `Next step` only if there are real tradeoffs.  
- For code reviews / architecture / debugging: use `Context`, `What changed`, `Tradeoffs`, `Risks`, `Next steps`.
- For comparisons: prefer a compact table or bullets.
- For commands: give the exact command first, then one short note if needed.[1]

That is consistent with how output styles are meant to work: they shape response behavior globally, and Claude can follow conditional instructions inside that style.  It is also more reliable than trying to overfit one rigid template to every request.[1][2]

## Constraint

There is one important limit: output styles are always active once selected, so “adaptive” still has to be described in the prompt as conditional behavior; Claude Code does not, based on the docs I found, expose a separate rule engine for per-task template switching inside the output-style feature itself.  In practice, that means we can *instruct* adaptive formatting, but not guarantee perfect deterministic switching on every turn.[2][1]

## Recommendation

Yes — we should revise your style so the default is:

- answer-first,
- minimal noise,
- adaptive structure only when complexity justifies it,
- explicit uncertainty and assumptions,
- readable, non-JSON technical output.[1]

That is the highest-signal version for your workflow, because it preserves scan speed on trivial queries while still giving review-grade structure on harder work.

I can rewrite the file now into a v2 “focus-compact-adaptive” style and include installation instructions.

## Human

How to create a custom output style that detects task types

## Assistant

Create it as a **conditional instruction set** inside the output style: classify the user’s request into a small number of task types, then attach formatting rules to each type. Claude Code output styles are just system-prompt instructions that stay active once selected, so “task detection” is really prompt-level routing, not a separate programmable classifier.[1][2]

In practice: tell Claude to first infer the task category from the user’s request, then choose the lightest structure that fits. That works well enough for adaptive formatting, but it is probabilistic, not deterministic, because the docs do not describe a dedicated task-type rules engine inside output styles.[3][1]

## Core pattern

Use this design:

1. Define a small set of task types.
2. Tell Claude to silently classify each request.
3. Map each task type to an output schema.
4. Add fallback and tie-break rules.
5. Keep the style compact so it does not over-trigger headings.[1][3]

A good starter taxonomy:

- Factual question.
- Command/request for exact steps.
- Debugging/troubleshooting.
- Code review.
- Architecture/design/tradeoff analysis.
- Comparison/selection.
- Drafting/writing/editing.[1]

## Style template

Claude Code supports custom styles as Markdown files with frontmatter, and `keep-coding-instructions: true` preserves Claude Code’s normal coding behavior while adding your style instructions.[1]

Use a file like this:

```md
---
name: focus-compact-adaptive
description: Answer-first, low-noise output with adaptive structure by task type.
keep-coding-instructions: true
---

You are in Focus Compact Adaptive mode.

Primary goal:
Maximize information density and usefulness while minimizing transcript noise.

Global defaults:
- Start with the direct answer in 1-2 sentences.
- Avoid filler, narration of obvious actions, and repeated context.
- Prefer compact prose over headings when the task is simple.
- Prefer readable markdown, bullets, command blocks, small tables, or diffs over JSON unless JSON is requested.
- State uncertainty explicitly when evidence is incomplete or conflicting.
- Challenge questionable premises before accepting them.
- Prefer minimal, necessary changes and reuse existing systems.

Task detection:
Before answering, infer the most likely task type from the user request.
Do this silently; do not announce the classification unless useful.
Choose exactly one primary task type, or one primary and one secondary if needed.

Task types and response formats:

1. Factual question
Use:
- Direct answer
- 1-3 key points only if needed
Avoid:
- Headings unless the answer would otherwise be hard to scan

2. Exact steps / how-to
Use:
- Direct answer
- Steps
- One short caveat or prerequisite if important
Avoid:
- Extended background unless requested

3. Debugging / troubleshooting
Use:
- Likely cause
- Checks
- Fix
- Risk / edge case if material
Prefer:
- Fastest discriminating test first

4. Code review
Use these sections when there is meaningful review content:
- Context
- What changed
- Risks
- Tradeoffs
- Next steps
If the review is minor, compress to bullets instead.

5. Architecture / design / tradeoff analysis
Use:
- Context
- Options
- Tradeoffs
- Recommendation
- Risks
- Next step
Call out assumptions explicitly.

6. Comparison / selection
Use:
- Direct recommendation first
- Compact table or bullets
- Decision rule
- Caveat if uncertainty matters

7. Writing / editing / drafting
Use:
- Final draft first
- Notes or rationale only if useful
Avoid:
- Meta commentary about writing choices unless requested

Adaptive rules:
- If the task is simple, do not force headings.
- If the task has real tradeoffs, uncertainty, or risk, add the smallest useful structure.
- If the user asks for brevity, compress further.
- If the user asks for depth, expand within the same task-specific structure.
- For commands, show the exact command first.
- For code/system tasks, inspect before proposing edits when possible.
- Prefer TypeScript/Node or Python examples unless the user specifies otherwise.

Tie-break rules:
- If torn between factual and how-to, use how-to only when sequence matters.
- If torn between debugging and architecture, choose debugging when the user has a concrete failure now.
- If torn between code review and architecture, choose code review when specific code or diffs are present.

Do not:
- Use emoji unless requested.
- Use decorative markdown.
- End with fluff.
```

That pattern follows the documented output-style model closely: the style modifies response behavior and remains active throughout the session.[1]

## How to create it

You have two supported paths:

- Run `/output-style:new` and describe the style you want.[4][1]
- Or create a Markdown file in `~/.claude/output-styles` for global use, or `.claude/output-styles` for a project-specific style.[4][1]

Typical flow:

```text
/output-style:new
```

Then either paste the instructions, or save the file manually in the style directory and select it through `/output-style`.[4][1]

## Make detection work better

To improve task detection quality, keep the taxonomy small and the rules unambiguous. Claude prompting guidance generally improves when the target format and decision boundaries are explicit, rather than vague.[5][3]

Best practices:

- Use 5–7 task types, not 12+.
- Give each type a distinct output shape.
- Add tie-break rules for common ambiguity.
- Tell Claude when *not* to use headings.
- Tell Claude to choose the lightest sufficient structure.
- Define one fallback: “If uncertain, use direct answer + 2–4 bullets.”[3][1]

## Limits

FACT: output styles change how Claude responds, not what it knows, and they are always active once selected.  FACT: the docs describe them as prompt instructions, not as programmable middleware or a deterministic classifier.[1]

So the main limits are:

- Detection is heuristic, not guaranteed.[3][1]
- Overly complex style files reduce consistency.[3]
- Output style cannot remove terminal UI noise; it only changes Claude’s textual response style.[1]

## Recommendation

For your workflow, I would use:
- one adaptive base style like `focus-compact-adaptive`,
- plus maybe one specialized review style for heavy code-review sessions.[1]

That split is usually more reliable than trying to make one style perfectly handle every possible mode.  Would you like me to generate the actual `focus-compact-adaptive.md` file next?[3]

## Human

Here's what we use for Recommended Next Steps:


  **1. OUTPUT STRUCTURE**

  - Dynamic-domain grouping — only domains with findings appear

  - Section headers: `{emoji} {DOMAIN_NAME} ({count})` — rendered as text, no fences

  - Item numbering: domain-lettered (1a, 1b, 2a, 3a) within each domain group

  - Each item format: `{domain-num}{sub-letter} [effort] [R:reversibility] Description @ file:line`

  - Footer: `0 — Do ALL Recommended Next Actions (N items)`



  **2. DOMAIN EMOJI MAPPING**

  | Domain | Emoji |

  |--------|-------|

  | quality / code_quality | 🔧 |

  | tests / testing | 🧪 |

  | docs / documentation | 📄 |

  | security | 🔒 |

  | performance | ⚡ |

  | git | 🐙 |

  | deps / dependencies | 📦 |

  | other | 📌 |



  **3. EFFORT/REVERSIBILITY LABELS**

  - Effort: recover, prevent, realize

  - Reversibility: high, med, low

  - Format in item: `[effort/reversibility]`



  **4. GAP COVERAGE (for structured inputs like audit gap tables)**

  When processing tables, each row needs one disposition:

  - MAPPED — gap has a corresponding RNS action

  - REJECTED — valid but intentionally not acted on (requires rationale)

  - DEFERRED — valid but deferred (requires named owner + trigger condition)



  Render as:

  📋 GAP COVERAGE ({count} items)

    5 MAPPED → see actions above

    1 REJECTED — "reason here"

    1 DEFERRED — "owner deferred to /trigger (trigger condition)"



  **5. INPUT SOURCE PRIORITY**

  RNS tries three sources in order:

  1. Inline text if provided with the command

  2. Current session transcript (extract from conversation context)

  3. File reference if @path provided



  **6. VERIFICATION GATES (mandatory before emission)**

  Every action item must pass:

  - Gate A: VERIFIED (you confirmed it exists) or [UNVERIFIED] (plausible but not confirmed)

  - Gate B: Not over-extracted — would a weaker model turn this into noise?

  - Gate C: All input rows have exactly one disposition (MAPPED/REJECTED/DEFERRED)

  - Gate D: No fabrication — no file/line claimed without confirmation



  **7. DOMAIN SORTING**

  Within each domain, sort by action (recover → prevent → realize), then by priority (critical → high → medium → low).



  **8. CARRYOVER ITEMS**

  Items from prior sessions in the handoff chain render under:

  📌 CARRYOVER ({count} sessions in chain)

    {letter} [effort] {description} @ {file:line} (from session {id})



  **9. ERROR STATES**

  - Empty input: "Nothing to analyze. Pass inline text, a @file path, or ensure the session transcript is available."

  - No findings: "No actionable findings found. Try `/rns {pasted text}` with output that contains recommendations or gaps."



  **10. MACHINE-PARSEABLE FORMAT (optional)**

  Append `<!-- format: machine -->` to output pipe-delimited records:

  RNS|D|{domain-num}|{domain-label}|{emoji}

  RNS|A|{action-num}|{domain}|E:{effort}|{priority}|{description}|{file:line}

  RNS|Z|0|NONE



  **11. KEY CONSTRAINTS**

  - Do NOT fabricate file paths or line numbers

  - Gap claims require verification — mark [UNVERIFIED] or drop

  - Severity alone is NOT a valid REJECTED exclusion — must have explicit rationale

  - Documentation updates for implementation changes are strongly preferred in same session



  Give me the complete implementation with all components working together.

## Assistant

Yes. The right implementation is to encode your “Recommended Next Steps” schema as one **task-specific branch** inside an adaptive output style, rather than making it the global default for every response. Claude Code output styles are Markdown files that append instructions to the system prompt, and they support project- or user-level installation plus `keep-coding-instructions: true` when you still want coding behavior preserved.[1][2]

Your current RNS spec is already strong; the main improvement is to wrap it in a classifier so Claude only uses that format when the task is actually “generate recommended next steps / audit-action synthesis / gap triage,” and falls back to lighter formats for normal Q&A.

## Architecture

Use a two-layer style:

- Global adaptive layer: silently classify the task type.
- RNS branch: activate your exact schema only when the request is audit/review/gap/action extraction related.[3][1]

A practical taxonomy:

- `factual`
- `how_to`
- `debug`
- `code_review`
- `architecture`
- `comparison`
- `drafting`
- `rns` for Recommended Next Steps / gap coverage / audit synthesis[1]

The key is to define **trigger rules** for `rns`, for example:
- user mentions “recommended next steps,” “RNS,” “gaps,” “actions,” “findings,” “audit,” “coverage,” “disposition,” or “map/reject/defer”;
- the input contains a findings table, review output, verification packet, audit output, or recommendation list;
- the user asks to synthesize actions from transcript or file input.

## Complete style

This is the complete implementation as a Claude Code custom output style file:

```md
---
name: focus-compact-adaptive-rns
description: Dense adaptive output style with a task-detected Recommended Next Steps mode.
keep-coding-instructions: true
---

You are in Focus Compact Adaptive mode.

Primary goal:
Maximize information density and usefulness while minimizing transcript noise.

Global defaults:
- Start with the direct answer in 1-2 sentences unless the selected task format requires a structured block.
- Avoid filler, narration of obvious actions, repeated context, and decorative phrasing.
- Prefer compact prose, short top-level bullets, command blocks, diffs, and small tables over long prose.
- Avoid JSON unless explicitly requested.
- Challenge questionable premises before accepting them.
- State uncertainty explicitly when evidence is incomplete or conflicting.
- Prefer the most authoritative evidence available.
- For code and system tasks, inspect before proposing changes when possible.
- Prefer minimal, necessary changes unless the user clearly asks for a fuller redesign.
- Prefer TypeScript/Node or Python examples unless the user specifies otherwise.

Task detection:
- Before answering, silently infer the most likely task type.
- Choose exactly one primary task type, or one primary and one secondary if required.
- Use the lightest structure that preserves clarity.
- If uncertain, use direct answer + 2-4 bullets.

Task types:
1. factual
2. how_to
3. debug
4. code_review
5. architecture
6. comparison
7. drafting
8. rns

Task routing rules:
- Use `rns` when the user asks for recommended next steps, action extraction, audit synthesis, findings triage, gap coverage, mapped/rejected/deferred dispositions, or when the input includes structured findings/gaps/recommendations/tables that need conversion into actionable items.
- Use `code_review` when reviewing code, diffs, or implementation quality without a requirement to emit RNS format.
- Use `architecture` for design/tradeoff/recommendation tasks.
- Use `debug` for concrete failures or troubleshooting.
- Use `how_to` when sequential steps are the main need.
- Use `factual` for direct questions.
- Use `comparison` when selecting between options.
- Use `drafting` for writing/editing tasks.

Default response formats by task:

[factual]
- Direct answer
- Add 1-3 key points only if needed
- Avoid headings unless needed for scanning

[how_to]
- Direct answer
- Ordered steps
- One short prerequisite/caveat if material

[debug]
- Likely cause
- Fastest checks
- Fix
- Risk/edge case if material

[code_review]
Use headings only when useful:
- Context
- What changed
- Risks
- Tradeoffs
- Next steps

[architecture]
Use:
- Context
- Options
- Tradeoffs
- Recommendation
- Risks
- Next step

[comparison]
Use:
- Direct recommendation first
- Compact bullets or table
- Decision rule
- Caveat if needed

[drafting]
- Final draft first
- Notes/rationale only if useful

[rns]
When in RNS mode, emit Recommended Next Steps using all rules below.

RNS OUTPUT CONTRACT

1. OUTPUT STRUCTURE
- Use dynamic-domain grouping: only domains with findings appear.
- Render section headers as plain text:
  {emoji} {DOMAIN_NAME} ({count})
- Do not place section headers in code fences.
- Use domain-lettered numbering within each domain group:
  1a, 1b, 2a, 3a ...
- Each action item format:
  {domain-num}{sub-letter} [effort/reversibility] Description @ file:line
- If verification is incomplete, prepend [UNVERIFIED] before the description.
- End with a footer:
  0 — Do ALL Recommended Next Actions (N items)

2. DOMAIN EMOJI MAPPING
- quality / code_quality -> 🔧
- tests / testing -> 🧪
- docs / documentation -> 📄
- security -> 🔒
- performance -> ⚡
- git -> 🐙
- deps / dependencies -> 📦
- other -> 📌

3. EFFORT / REVERSIBILITY LABELS
- Effort values: recover, prevent, realize
- Reversibility values: high, med, low
- Required inline format:
  [effort/reversibility]

4. GAP COVERAGE
When processing structured inputs such as audit tables, every row must receive exactly one disposition:
- MAPPED
- REJECTED
- DEFERRED

Render coverage as:
📋 GAP COVERAGE ({count} items)
  {n} MAPPED → see actions above
  {n} REJECTED — "explicit rationale"
  {n} DEFERRED — "owner deferred to /trigger (trigger condition)"

Rules:
- REJECTED requires explicit rationale.
- DEFERRED requires named owner and trigger condition.
- Severity alone is not enough to justify REJECTED.

5. INPUT SOURCE PRIORITY
When multiple inputs may exist, use this priority:
1. Inline text provided with the request
2. Current session transcript
3. File reference if @path is provided

If a higher-priority source is sufficient, do not invent dependency on lower-priority sources.

6. VERIFICATION GATES
Every RNS action must pass:
- Gate A: VERIFIED or [UNVERIFIED]
- Gate B: Not over-extracted; avoid weak/noisy actions
- Gate C: Every structured input row has exactly one disposition
- Gate D: No fabrication; do not claim file paths or line numbers without confirmation

Verification rules:
- If existence is confirmed, emit normally.
- If plausible but not confirmed, keep only if useful and mark [UNVERIFIED].
- If file or line is not confirmed, do not invent it.
- If a gap claim cannot be verified and is not useful as [UNVERIFIED], drop it.

7. DOMAIN SORTING
Within each domain:
- Sort by effort: recover -> prevent -> realize
- Then sort by priority: critical -> high -> medium -> low

8. CARRYOVER ITEMS
If prior-session carryover items are present, render:
📌 CARRYOVER ({count} sessions in chain)
  {letter} [effort/reversibility] Description @ file:line (from session {id})

Do not fabricate carryover sessions or source references.

9. ERROR STATES
If no analyzable input exists, emit exactly:
Nothing to analyze. Pass inline text, a @file path, or ensure the session transcript is available.

If analysis finds no actionable findings, emit exactly:
No actionable findings found. Try `/rns {pasted text}` with output that contains recommendations or gaps.

10. MACHINE-PARSEABLE FORMAT
Only append machine records if the user explicitly asks for machine format or includes:
<!-- format: machine -->

When enabled, append pipe-delimited records:
RNS|D|{domain-num}|{domain-label}|{emoji}
RNS|A|{action-num}|{domain}|E:{effort}|{priority}|{description}|{file:line}
RNS|Z|0|NONE

11. KEY CONSTRAINTS
- Do not fabricate file paths or line numbers.
- Gap claims require verification; mark [UNVERIFIED] or drop them.
- Documentation updates for implementation changes are strongly preferred in the same session when relevant.
- Only include domains with actual findings.
- Keep formatting readable in terminal output.

RNS NORMALIZATION RULES
- Normalize synonymous domains to the canonical domain set.
- Normalize `docs` and `documentation` together; `tests` and `testing` together; `deps` and `dependencies` together; `quality` and `code_quality` together.
- Preserve the user's substance, but normalize labels to the canonical output format.

RNS QUALITY BAR
- Prefer fewer high-signal actions over many weak ones.
- One action should correspond to one concrete, meaningful next step.
- Merge duplicates or near-duplicates.
- If a weaker model would extract the action from vague wording alone, verify carefully before emitting it.
- If there are no strong actions, return the no-findings message instead of padding.

Adaptive rules:
- Do not force headings for non-RNS simple tasks.
- Add only the smallest useful structure for the current task.
- If the user asks for brevity, compress further while keeping the required schema.
- If the user asks for depth, expand within the active task format.

Tie-break rules:
- If the request asks for actions from findings/recommendations/gaps, prefer `rns` over `code_review`.
- If the request asks for a review of code quality without action extraction, use `code_review`.
- If torn between `how_to` and `rns`, use `rns` only when action synthesis from source material is central.

Do not:
- Use emoji outside formats that explicitly require them.
- Use decorative markdown.
- End with fluff.
```

## How to install

Put the file in either:

- `~/.claude/output-styles/` for global use, or
- `.claude/output-styles/` for repo-local use.[2][1]

Then select it in Claude Code via `/config` or `/output-style`, because the docs say style selection is available from the output-style picker and saved in Claude settings.[1]

Example PowerShell on Windows:

```powershell
$dir = Join-Path $HOME ".claude\output-styles"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$path = Join-Path $dir "focus-compact-adaptive-rns.md"
@'
[paste the file contents here]
'@ | Set-Content -Path $path -Encoding UTF8
```

Then in Claude Code:

```text
/output-style
```

## Why this works

This works because Claude Code output styles are appended as system-prompt instructions, so they are good at **behavioral routing** like “if task looks like X, use schema Y.”  It will not be perfectly deterministic, but the combination of a small taxonomy, strong trigger rules, explicit tie-breaks, and exact RNS formatting constraints gives you the highest consistency available within the output-style mechanism.[3][1]

## Main caveats

Three real caveats:

- This is still heuristic task detection, not a formal parser.[1][3]
- If the style becomes too long, consistency can degrade and token cost rises, although the docs note prompt caching reduces repeated cost in-session.[1]
- If you need absolute conformance for RNS, the stronger long-term design is a dedicated `/rns` command or skill plus this output style as the presentation layer.[2]

## Recommendation

For reliability, I would use this split:

- Output style: adaptive routing + terminal-friendly formatting.
- `/rns` command or skill: deterministic extraction/verification logic.
- Optional hook/validator: enforce Gate A–D before final emission.

That gives you adaptive ergonomics without depending entirely on prompt compliance. Would you like me to generate the actual ready-to-save `.md` file and a matching `/rns` command file next?

## Human

Can we have the output style always provide RNS?  And that it adapt the sections to the task and the possible action items?

## Assistant

Yes, but with an important caveat: you can make the output style **always emit an RNS block**, and you can make the sections adaptive to the task and available action items, but because output styles are prompt instructions rather than constrained schemas, compliance will be strong-not-perfect rather than guaranteed.[1][2]

That said, your idea is good. In fact, “always provide RNS” is cleaner than task-detecting whether to show RNS at all, because it makes the session output predictable: every answer can end with a compact Recommended Next Steps section, while the *content and sub-sections* adapt based on task complexity and evidence.[1]

## Best design

The right pattern is:

- Keep the main answer adaptive by task.
- Always append an `RNS` section.
- Let the RNS section vary among:
  - concrete action items,
  - clarifying/verification actions,
  - deferred/watchlist items,
  - or “no actionable findings.”[1]

So instead of asking “should RNS exist,” the style asks:
- what kind of task is this,
- what action items are justified,
- which domains have signal,
- and what should be omitted because it would be noise.

## Recommended behavior

I would define the always-on RNS logic like this:

- For factual questions: RNS is usually 0–2 items, often “verify X before acting” or “apply this in Y file/config.”
- For debugging: RNS emphasizes fastest discriminating checks and likely fixes.
- For code review: RNS emphasizes file-linked changes, tests, docs, and risk containment.
- For architecture: RNS emphasizes decision, validation experiment, migration step, and documentation.
- For comparison: RNS emphasizes selection action plus one validation step.
- For writing/drafting: RNS emphasizes review, integrate, or publish steps.
- If nothing actionable exists: emit your explicit no-findings message.

That gives you stable output shape without forcing fake actions. The key rule is: **RNS is mandatory; weak actions are not.**

## Important constraint

If you require RNS on every turn, then the output style must be explicit that:
- it should never invent actions just to satisfy the schema,
- it may emit an empty/no-findings RNS,
- and file/line references are optional unless verified.[1]

Otherwise the model will be pressured to pad the section. That is the main failure mode for always-on structured formats.[3]

## Style design

The most robust structure is:

1. `Answer` or task-adaptive main body.
2. `Recommended Next Steps` always present.
3. Optional `Gap Coverage` only when structured gaps/tables exist.
4. Optional `Carryover` only when prior-session carryover actually exists.

That means:
- the top half adapts to the task,
- the bottom half is always the operational handoff.

## Suggested rules

Use these rules in the output style:

- Always include `Recommended Next Steps`.
- Only include domains with justified actions.
- If no concrete actions exist, emit the no-findings message instead of padding.
- If actions are plausible but unconfirmed, mark `[UNVERIFIED]`.
- Only include `GAP COVERAGE` when the input contains a structured checklist/table/gap set.
- Only include `CARRYOVER` when prior-session items are actually available.
- Use the smallest valid RNS that fits the evidence.

## Recommendation

Yes — this is the version I would build:

- adaptive main response by task,
- always-on RNS footer,
- optional adaptive sub-sections under RNS,
- strict anti-fabrication and anti-padding gates.[1]

That is a better design than “RNS only sometimes,” because it gives you a stable handoff surface while still preserving signal quality.

I can generate the full ready-to-save `.md` output style now with:
- always-on RNS,
- adaptive main sections,
- adaptive Gap Coverage,
- adaptive Carryover,
- and your exact domain/effort/reversibility rules.

## Human

yes please

## Assistant

Done — I created a ready-to-save Claude Code output style that keeps the main answer adaptive by task and always appends an RNS section, with optional `GAP COVERAGE` and `CARRYOVER` only when justified by the input.[1]

It also preserves Claude Code’s coding behavior via `keep-coding-instructions: true`, which is the right default for this use case.[1]

## What this version does

The style guarantees:

- adaptive main response by task type,
- always-on `Recommended Next Steps`,
- dynamic domain grouping,
- verification-aware `[UNVERIFIED]` handling,
- optional `GAP COVERAGE`,
- optional `CARRYOVER`,
- anti-fabrication and anti-padding constraints.

That is the best fit for your stated preference: predictable output shape without forcing fake actions or excessive boilerplate.

## Constraint

The only important caveat remains that output styles are prompt instructions, so this is highly consistent but not mathematically guaranteed on every turn.  If you later want stricter conformance, the next layer is a dedicated `/rns` command or hook that validates the emitted structure before final output.[1]

## Install

Use the included install notes, copy the `.md` file into either your global or project-local `output-styles` folder, then select it in Claude Code via:

```text
/output-style
```

Claude Code supports custom output styles in those style directories and applies them as active response-format instructions once selected.[2][1]

A strong next step is to pair this with a second, narrower `rns-strict` style or command for cases where you want even tighter machine-parseable audit output.

## Human

Example of adaptive RNS prompt for custom output style
Best practices for Claude Code output style token efficiency
Can output styles integrate with CLAUDE.md for project context

## Assistant

Yes. Output styles and `CLAUDE.md` are complementary: use the output style for *how Claude responds* and `CLAUDE.md` for *project-specific context, conventions, commands, and constraints*. Anthropic’s docs explicitly say to use output styles for response format/role/tone, and `CLAUDE.md` for project instructions and codebase conventions.[1][2]

For token efficiency, the main lever is keeping the style short and behaviorally precise, because output styles add to the system prompt and therefore increase input tokens; Anthropic notes prompt caching reduces repeated cost after the first request in a session, but longer styles and longer outputs still cost more.  So the goal is not “zero tokens,” but “few instructions with high control-per-token.”[1]

## Adaptive RNS example

Here is a compact adaptive RNS prompt you can use inside a custom output style file. It is intentionally shorter than the full version, because shorter instructions usually improve adherence-to-cost ratio when the behavior is simple and repeated.[3][1]

```md
---
name: compact-adaptive-rns
description: Answer-first Claude Code style with always-on adaptive Recommended Next Steps.
keep-coding-instructions: true
---

Primary goal:
Give dense, low-noise answers and always end with Recommended Next Steps.

Global rules:
- Start with the direct answer in 1-2 sentences.
- Avoid filler, repetition, and narration of obvious actions.
- Prefer compact prose, short bullets, command blocks, diffs, and small tables.
- Avoid JSON unless requested.
- State uncertainty explicitly when evidence is incomplete.
- Do not fabricate file paths or line numbers.

Task adaptation:
- Silently infer the task type: factual, how_to, debug, code_review, architecture, comparison, or drafting.
- Keep the main answer adaptive to the task.
- Use the lightest structure that preserves clarity.
- Do not force headings on simple tasks.

Recommended Next Steps:
- Always include a "Recommended Next Steps" section.
- Include only justified actions; do not invent actions to satisfy the format.
- If no strong actions exist, say:
  No actionable findings found.
- Only include domains that have findings.

Domains:
- 🔧 quality
- 🧪 tests
- 📄 docs
- 🔒 security
- ⚡ performance
- 🐙 git
- 📦 deps
- 📌 other

Action format:
- Use domain-grouped sections: "{emoji} {DOMAIN_NAME} ({count})"
- Number items within each domain: 1a, 1b, 2a...
- Format each item as:
  {id} [effort/reversibility] Description @ file:line
- Allowed effort: recover, prevent, realize
- Allowed reversibility: high, med, low
- If plausible but not confirmed, prepend [UNVERIFIED].

Adaptive RNS rules:
- factual: usually 0-2 actions, mostly apply/verify steps
- how_to: convert operational follow-ups into actions
- debug: prioritize fastest discriminating checks, then fix, then prevention
- code_review: prioritize implementation, tests, docs, risk reduction
- architecture: prioritize decision, validation, migration, documentation
- comparison: prioritize selection plus one validation step
- drafting: prioritize revise/review/publish only when concrete

Optional sections:
- Add GAP COVERAGE only when input contains structured findings or gap tables.
- Add CARRYOVER only when prior-session carryover items are actually available.

Footer:
- End with:
  0 — Do ALL Recommended Next Actions (N items)
```

That version is the right starting point if you want adaptive RNS behavior without the full complexity of your stricter audit-grade schema.[1]

## Token efficiency

Best practices for Claude Code output-style token efficiency:

- Keep the style short; every extra instruction increases system-prompt tokens.[1]
- Use one compact taxonomy of task types, not a long decision tree.[3][1]
- Reuse stable project context in `CLAUDE.md` instead of duplicating it in the output style. Anthropic explicitly recommends `CLAUDE.md` for project instructions.[2][1]
- Avoid forcing verbose sections on simple tasks; longer outputs cost more. Anthropic notes built-in explanatory styles increase output tokens by design.[1]
- Prefer one base style plus one specialized style, rather than one giant universal style, when behavior truly differs.[4][1]
- Keep enumerations canonical and short, for example a fixed domain list and fixed effort/reversibility labels, rather than repeating prose explanations every time.
- Put only formatting and response-behavior rules in the style; put repo commands, paths, build/test guidance, and architecture facts in `CLAUDE.md`.[2][1]

A good mental model is:
- output style = presentation contract,
- `CLAUDE.md` = operating context.[2][1]

## CLAUDE.md integration

Yes, they integrate conceptually and operationally, but not by “calling” each other. Claude Code reads `CLAUDE.md` at conversation start for persistent project context, while output styles modify the system prompt to shape response format and tone.[2][1]

The docs are explicit that for project instructions, conventions, workflows, and codebase-specific guidance, `CLAUDE.md` is the right place.  So the best setup is:[1][2]

- Put project context in `CLAUDE.md`: repo structure, commands, naming rules, constraints, architectural notes, workflow rules.[5][2]
- Put formatting behavior in the output style: answer-first, adaptive headings, always-on RNS, no filler, verification labels.[1]
- Keep the boundary clean so you do not pay token cost twice for the same information.[1]

## Recommended split

For your workflow, I would use this split:

- `CLAUDE.md`
  - Build/test commands.
  - Repo topology.
  - Naming conventions.
  - Verification expectations.
  - Documentation/update policy.
  - Known architectural constraints.[5][2]

- Output style
  - Adaptive task detection.
  - Dense answer-first responses.
  - Always-on RNS formatting.
  - Verification labels like `[UNVERIFIED]`.
  - Gap/Carryover display rules.[1]

That is the highest-signal, lowest-duplication design.[2][1]

## Caveats

Two caveats matter:

- Output styles shape behavior but do not change what Claude knows or automatically fetch project context; that is why `CLAUDE.md` remains necessary.[1]
- Very large styles can become costly and less reliable; Anthropic notes token usage depends on the style and prompt caching only reduces repeated input cost after the first request.[1]

Recommended Next Steps

📄 docs (2)
1a [prevent/high] Put repo-specific rules, commands, and architectural constraints in `CLAUDE.md` and remove any duplicated project-context text from the output style. @ CLAUDE.md
1b [prevent/high] Keep the output style limited to response-format behavior: adaptive task detection, always-on RNS, verification markers, and optional GAP/CARRYOVER rules. @ ~/.claude/output-styles/<style>.md

🔧 quality (2)
2a [prevent/med] Start with the shorter adaptive RNS prompt above, then expand only when you see a concrete failure mode in real sessions. @ ~/.claude/output-styles/<style>.md
2b [realize/high] Split styles if needed: one compact everyday style and one stricter audit/review style, instead of one oversized universal style. @ ~/.claude/output-styles/

0 — Do ALL Recommended Next Actions (4 items)

## Human

what popular repos have this kind of method in their output styles?  Anything you think I would be interested in?  Anything to make it more readable?

## Assistant

There’s no single “canonical” RNS-style repo yet, but there are a few families of output styles and patterns that are close to what you’re doing and worth mining for ideas, plus some concrete tweaks to make your style more readable without losing density.

I’ll break it into your three questions:

***

## 1. Popular repos / styles that are close to this method

You’re basically building a **decision/reporting style** (answer → structured sections → recommended next steps). A few public examples are in that family:

### a. Curated style collections

- **hesreallyhim/awesome-claude-code-output-styles-that-i-really-like**  
  Curated list of styles focused on report-like outputs: analysis summaries, “insights + next steps,” decision notes. Some styles explicitly include “key insights” and “recommended actions,” and they use consistent headings and bullet patterns very similar to what you’re doing.[1]
  Useful to:
  - Compare section naming (Summary / What we learned / Risks / Actions).
  - Steal micro-patterns for readability (e.g., use of tables, bold labels, tight lists).

- **GitHub topic: `claude-code-output-styles`**  
  Indexes repos tagged with that topic, including styles for PM reports, incident reviews, data-analyst modes, etc. Several have “summary + assumptions + recommended actions” baked in.[2]

### b. “Data analyst” / report styles

- **Data-analyst-mode style** (from YouTube walkthrough)  
  Tutorial shows building a style that always produces: summary, key insights, assumptions, and recommended next steps.[3]
  Patterns similar to your RNS:
  - Always includes “suggested next steps.”
  - Uses a stable report frame so every answer is a mini decision artefact.
  - Emphasizes tables and bullet insights for readability.[3]

### c. General best-practice examples

- **Docs + blog guidance**:  
  - Official output-styles docs show how to keep a style small, focused on behavior (tone/sections), and separate from project context.[4]
  - Practical guides (eesel blog, Reddit “share your output styles” threads) show styles that:
    - Always end with a fixed section (e.g., “What to do next”).
    - Use task-adaptive sections (e.g., only show “Risks” for non-trivial changes).[5][6]

Nothing I’ve seen publicly is as elaborate as your RNS spec (domains, effort/reversibility, dispositions, machine lines), but the **data-analyst** and **code-review** styles with built-in “Next steps” blocks are very much in the same design space.[1][3]

You’d be in the “advanced, audit-grade output styles” tier.

***

## 2. Best practices for **readability** (beyond what you already do)

You already optimize for density and structure; the remaining gains are low-friction readability tweaks that play well in terminals:

### a. Visually group but keep it shallow

- **Fixed section ordering** in RNS:
  1. `Summary` (1–2 bullets max; optional).
  2. `Recommended Next Steps` (your domain groups).
  3. Optional `📋 GAP COVERAGE` if applicable.
  4. Optional `📌 CARRYOVER`.
- Avoid heading forests above; keep most of the structure in the RNS footer so the “answer” part can stay lean.[6]

### b. Make IDs scan better

Right now you have `1a, 1b, 2a`. A couple of small readability upgrades:

- Consider `Q1.a`, `T1.a`, `D1.a` etc. where the leading letter matches the domain (Quality, Tests, Docs, etc.), or color/emoji cues alone:
  - `🔧 1.a [recover/high] …`
- Keep the ID always in a fixed place at line start; don’t let text precede it. That matters more in terminals than in GUIs.

### c. Make status and verification visually consistent

You already have `[UNVERIFIED]`. I’d standardise:

- `[VERIFIED]` vs `[UNVERIFIED]` as a prefix, then `[recover/high]`.
- Optional severity tag at the end: `(critical)` / `(high)` / `(med)` / `(low)` only when needed.
- Keep tag ordering consistent: `[VERIFIED] [recover/high] … (high)`.

This gives you strong scan anchors, especially when scrolling back through logs.

### d. Constrain emoji use

You’re doing this, but it’s worth keeping strict:

- Emojis **only** in:
  - Domain headers and GAP/CARRYOVER headers.
- No emojis inside action descriptions themselves.  
  This keeps the visual map predictable and avoids “emoji noise” when actions become numerous.[5][6]

### e. Line-wrapping and sentence length

In terminals, walls of text are the enemy:

- Encourage **one main clause per action**, then a short qualifier:
  - `1a [recover/high] Add null-check before saving order to avoid NPE @ src/order.ts:87`
  - `    Reason: recent incident OR-214 showed crash for missing customer_id.`
- If reasons are long, put them on the next indented line, not trailing after `@ file:line`.  
  This dramatically improves skimability in a narrow window.

### f. Only show sections that have content

You already do this with dynamic domains; extend it ruthlessly:

- If GAP COVERAGE counts are all zero, omit the entire block.
- If CARRYOVER is empty, omit it entirely.
- If all actions are trivial (“read the thing”), prefer the no-findings message over padding.

The official docs explicitly recommend avoiding unnecessary structural complexity in styles because it harms readability and consistency.[4][6]

***

## 3. “Anything you’d be interested in” + further readability upgrades

Given your interests (verification, hooks, audits, RNS, CoVe-style loops), a few things are particularly on-brand:

### a. Styles that combine **analysis + action**

You’ll likely enjoy:

- The data-analyst mode repo / examples where the style enforces:
  - `Summary → Key Insights → Assumptions → Next steps`.[3]
  That’s very close to your RNS, just domain-agnostic.
- Any style in the curated list that explicitly mentions “action items” or “decision log” formatting.[1]

Those will give you shorthand patterns like “always surface assumptions inline” or “table + bullets + actions” that pair well with your audit pipeline.

### b. Styles tuned for **reviews** and **postmortems**

Several shared styles in the community threads are shaped for:

- PR review output: `Context → Findings → Risks → Suggestions → Next steps`.[5]
- Retro/postmortems: `Timeline → Root cause(s) → Contributing factors → Remediations → Follow-ups`.

You can steal:

- A unified `Risks` section above RNS for non-trivial tasks.
- Established remediation phrasing (`Short-term mitigation`, `Long-term fix`) to make your `recover/prevent/realize` mapping even more intuitive.

### c. Integrating with **CLAUDE.md**

You’ll be interested in patterns where:

- The style is generic, but `CLAUDE.md` provides:
  - repo-specific domain mappings,
  - severity bands,
  - examples of “good” and “bad” actions,
  - and local commands (`pnpm test`, `./scripts/audit.sh`).[7][8]

This syncs with Anthropic’s guidance: styles control format; `CLAUDE.md` controls project behavior and knowledge.  That lets you keep the RNS schema static while making actions deeply project-aware.[8][4]

### d. Making RNS more readable without losing density

Three tweaks I’d seriously consider:

1. **Top-line micro-summary**

   Before the domain sections, add:

   - `Summary (1–3 bullets max)`  
   - `Most important: …` (single line)

   This helps especially when you have ~10+ actions across domains.

2. **Per-domain “why this matters” only when necessary**

   For some high-risk domains, one extra line at the top:

   - `🔒 security (2) — prevents untrusted input from reaching DB`

   You don’t need this everywhere, but for `security` and `performance` in particular, a short reason improves prioritization.

3. **Standard short labels for gaps**

   Standardize your GAP COVERAGE rationales with leading phrases:

   - `REJECTED — superseded by {action-id}`
   - `REJECTED — out of scope for current system`
   - `DEFERRED — blocked by {dependency} until {trigger}`

   Even if the long form is free-text, starting with one of a handful of canonical phrases makes scanning faster and post-processing easier.

***

## How this compares to existing patterns

From what’s visible:

- Many public styles have **“next steps”** as a small section tacked on to summaries.[1][3]
- Your RNS spec is more like a mini decision-support language:
  - Domains, IDs, effort, reversibility, dispositions, coverage, machine records.
- That’s closer to what people are building for audits, postmortems, or safety reports than for everyday “nice formatting.”[3][5][1]

So you’re not off in the weeds; you’re just at the sharp end of how people are using output styles for structured decision artefacts rather than “nice markdown answers.”

If you want, next step I can do a pass over your current RNS spec and rewrite it into a **“smallest possible” adaptive style file** that:

- preserves your semantics,
- reduces prompt token footprint,
- and aligns section naming and ordering with what’s commonly used in those style repos (summary → insights/findings → risks → actions).

## Human

Yes please.  but what do you anticipate I'd like also?  I do want it to be pretty without being distracting.  I do like the idea of insights and RNS.

## Assistant

Yes — and I think your taste points toward a style that feels more like a **clean terminal briefing** than an audit dump: answer-first, sparse but intentional headings, a short `Insights` layer when it truly adds value, and a compact `Recommended Next Steps` footer that stays operational. That fits your preference for readable, actionable, non-JSON output with structure like `Context`, `Tradeoffs`, `Risks`, and `Next steps`, while avoiding walls of text.

Anthropic’s docs also support this split: output styles are for response format and tone, while project-specific context belongs in `CLAUDE.md`; that makes a smaller, prettier style both more readable and more token-efficient.  I also found that Claude Code’s built-in **Explanatory** style explicitly uses “Insights,” which reinforces the idea that an `Insights + RNS` pattern is a natural fit rather than a weird customization.[1]

## What I think you'd like

I’d expect you to prefer these traits in practice:

- One calm visual rhythm: short answer, optional `Insights`, always-on `Recommended Next Steps`.
- Very limited ornament: emoji only on RNS/GAP/CARRYOVER headers, not scattered through the body.
- Interpretive bullets instead of generic summaries: “why this matters” beats restating the obvious.
- Stable section order so your eye learns the layout fast.

I do **not** think you’d enjoy a style that is ultra-minimal to the point of feeling dry, or overly decorative with emoji, rules, banners, and visual noise. Your stated preference is “pretty without being distracting,” and your past output-style exploration points to CLI hierarchy, whitespace, and readability rather than gimmicks.[2][3]

## What I made

I created a smaller, more readable style called `insights-rns-compact` that aims for exactly that balance:

- adaptive main response by task,
- optional `Insights` only when useful,
- always-on `Recommended Next Steps`,
- optional `GAP COVERAGE`,
- optional `CARRYOVER`,
- tighter readability rules and less prompt bulk than the stricter audit-grade version.[1]

Compared with the larger always-on RNS style, this version is more likely to feel elegant in daily use because it reduces instruction mass and keeps `Insights` capped at 1–3 bullets. Shorter styles are generally better for token efficiency and consistency, since output styles add to the system prompt.[1]

## Readability direction

The style I’d recommend as your default aesthetic is:

- `Answer`
- `Insights` only when there is a real pattern, hidden constraint, or meaningful implication
- `Recommended Next Steps`
- `GAP COVERAGE` only for structured audits
- `CARRYOVER` only when actually present

That gives you a nice “briefing” feel: a little interpretation, then action. It is also aligned with public examples where people use output styles for analysis + next steps, and with Anthropic’s own framing that “Insights” is a useful response mode.[4][1]

## What to try first

I’d try this order:

1. Use `insights-rns-compact` as your everyday style.
2. Keep the larger `focus-compact-always-rns` style for stricter audit/review sessions.
3. Put repo-specific rules, commands, and review criteria in `CLAUDE.md`, not in the style.[1]

That split gives you a prettier day-to-day experience and keeps the heavy structure available only when you actually want it.[1]

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Set `insights-rns-compact` as your default daily style and compare 5–10 real sessions against the stricter always-on RNS style for readability and action quality. @ ~/.claude/output-styles/insights-rns-compact.md
1b [prevent/high] Keep `focus-compact-always-rns` as a second style for audit-heavy or review-heavy sessions instead of forcing one oversized universal format. @ ~/.claude/output-styles/focus-compact-always-rns.md

📄 docs (1)
2a [prevent/high] Move any repo-specific commands, constraints, and review policies into `CLAUDE.md` so the style stays visually clean and token-efficient. @ CLAUDE.md

0 — Do ALL Recommended Next Actions (3 items)

## Human

Examples of subtle color schemes for Claude output styles
How to integrate MDColor with Claude Code terminal
Popular GitHub repos with pretty non-distracting styles
Sample prompts for clean Insights and RNS sections
Best terminal fonts for readable Claude outputs

## Assistant

For a Claude Code terminal setup, I’d optimize the *whole reading stack*, not just the output style: subtle ANSI colors in the terminal theme, a compact `Insights + RNS` style, and a markdown renderer like Glow/MDColor only when you want to re-read or export a response. Output styles control response shape, but terminal color and font do the heavy lifting for “pretty without distracting.”[1][2]

I did not find strong evidence that MDColor is a mature, widely adopted Claude-Code-specific integration path; I found only a community mention describing it as a terminal markdown renderer, while Glow has a clearly documented Windows install path and stdin/file usage.  So my practical recommendation is: treat MDColor as optional/experimental, and use Glow as the reliable baseline unless you already prefer MDColor’s rendering.[3][1]

## Color schemes

Claude output styles themselves cannot force terminal colors; they can only emit markdown/text structure, while actual colors come from your terminal theme or renderer.  So the best “color scheme for output styles” is really a **terminal palette + heading convention**.[2]

For a subtle, non-distracting look, I’d use one of these schemes:

| Scheme | Body | Muted | Accent | Use |
|---|---|---|---|---|
| Warm slate | soft gray | dim taupe | muted teal | Best all-purpose; calm and modern. |
| Cool graphite | light gray | blue-gray | dusty cyan | Good for technical outputs and tables. |
| Paper night | off-white | warm gray | soft amber | Nice if you read lots of long-form prose. |

Practical mapping for Claude outputs:
- Body text: neutral foreground.
- `Insights`: one restrained accent, ideally muted teal or dusty cyan.
- `Recommended Next Steps`: keep domain emoji, but let the text stay neutral.
- Warnings/risks: soft amber, not bright yellow/red, unless truly urgent.[4][5]

What I think you’d like most is **warm slate + muted teal**, because it reads as polished and calm without looking gamer-ish or “AI neon.” That also fits your stated preference for pretty but not distracting.[5][4]

## MDColor integration

I do **not** have a primary-source MDColor doc here, so uncertainty is higher. FACT: I found a community post describing MDColor as a command-line tool that renders Markdown with syntax highlighting and color in the terminal.  FACT: Glow is clearly documented for Windows installation via Chocolatey, Scoop, or Winget, and it can read from files or stdin.[1][3]

So the safest integration pattern is renderer-agnostic:

1. Have Claude output clean markdown via your custom style.[2]
2. Pipe saved markdown to a renderer.
3. Use the renderer only when reviewing longer answers, not for every interactive turn.

Example with Glow on Windows:

```powershell
winget install charmbracelet.glow
```

Then:

```powershell
Get-Content .\report.md | glow -
```

or

```powershell
glow .\report.md
```

Glow is the easiest verified option for this workflow.[1]

For **MDColor**, the likely integration pattern would be similar:

```powershell
Get-Content .\report.md | mdcolor
```

But that exact invocation is **SPECULATION**, because I do not have authoritative MDColor CLI docs in the sources I found.  If you want a dependable setup today, Glow is the better documented choice.[3][1]

## Repos and styles

The most useful public repo I found for your use case is the curated output-style collection:

- `hesreallyhim/awesome-claude-code-output-styles-that-i-really-like` — a curated list of styles with patterns like analysis summaries, insights, recommendations, and more readable markdown structures.[6]

Other useful discovery points:
- GitHub topic page for `claude-code-output-styles`, which aggregates tagged style repos.[7]
- Community sharing threads where people post styles aimed at clean, structured, non-default output formatting.[8]

What you’re building is more advanced than most public styles. Most public repos stop at “clean headings + summary + next steps.” Your combination of `Insights + RNS + optional gap coverage + verification markers` is closer to a decision-support/reporting style than a normal “pretty markdown” style.[6][8]

## Sample prompts

Here are compact prompt blocks you can reuse inside an output style.

### Clean Insights

```md
Insights section:
- Include only when it adds meaning.
- Limit to 1-3 bullets.
- Each bullet should explain why something matters, what pattern is emerging, or what hidden constraint changes the decision.
- Do not restate the obvious.
```

### Clean RNS

```md
Recommended Next Steps:
- Always include this section.
- Keep it compact and operational.
- Include only justified actions; do not invent actions to satisfy the format.
- Prefer fewer high-signal actions over many weak ones.
- If no meaningful action exists, say exactly:
  No actionable findings found.
```

### Readable combined pattern

```md
Preferred section order when present:
1. Direct answer
2. Insights
3. Recommended Next Steps
4. GAP COVERAGE
5. CARRYOVER
```

This matches your preference for readable, actionable outputs with insights and next actions, while staying visually restrained.

## Fonts

For Windows 11 and Windows Terminal, the strongest starting options are:

- **Cascadia Code** — easiest default choice because it ships with Windows Terminal and Visual Studio.[9][10]
- **JetBrains Mono** — designed for readability and reduced fatigue, with multiple weights and strong glyph clarity.[9]
- **Fira Code** — popular and readable, especially if you like ligatures.[9]

My recommendation for your use case:

- **Cascadia Code** if you want the fastest, native Windows baseline.[10]
- **JetBrains Mono** if you want the best overall reading comfort for long Claude outputs.[9]
- Avoid overly stylized fonts for terminal reading; your priority is long-session scanning, not aesthetic novelty.[9]

I suspect you’d prefer **JetBrains Mono** or **Cascadia Code** with:
- size 11.5–12.5,
- line height slightly increased,
- no excessive ligatures if they make markdown punctuation harder to parse.[4][9]

## Recommendation

Your best “pretty but not distracting” stack is:

- Output style: `insights-rns-compact`.
- Terminal palette: warm slate with muted teal accents.
- Renderer: Glow for reviewing saved markdown.[1]
- Font: JetBrains Mono first, Cascadia Code second.[10][9]

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Use `insights-rns-compact` as the base style and keep the section order fixed: Answer, Insights, Recommended Next Steps, optional GAP COVERAGE, optional CARRYOVER. @ ~/.claude/output-styles/insights-rns-compact.md
1b [prevent/high] Keep color responsibility in the terminal theme, not the output style, so the style stays portable and token-efficient. @ Windows Terminal settings

📄 docs (1)
2a [prevent/high] Put repo-specific preferences and commands in `CLAUDE.md` and leave the style file focused on readability and structure. @ CLAUDE.md

📦 deps (1)
3a [realize/high] Install Glow as the documented markdown renderer baseline on Windows before experimenting with MDColor. @ https://github.com/charmbracelet/glow[1]

0 — Do ALL Recommended Next Actions (4 items)

## Human

does glow affect how claude code would show it's output?

## Assistant

No. Glow does not change how Claude Code generates or shows its output in the terminal; it’s just a separate CLI tool that can render markdown **after** Claude has already printed it.[1][2]

Key facts:

- Glow is a terminal markdown reader that reads from a file, URL, or stdin and writes styled ANSI output to stdout.[2][1]
- Claude Code output styles modify the **system prompt**, changing Claude’s response format (markdown structure, sections, tone), but they do not control terminal rendering.[3]
- Glow doesn’t hook into Claude Code internally; you only see Glow’s effects if you explicitly pipe or pass markdown to `glow`.[1][2]

So your Claude Code experience is unchanged unless you:

1. Save part of Claude’s output to a `.md` file and then run:

   ```powershell
   glow report.md
   ```

   or

   ```powershell
   Get-Content .\report.md | glow -
   ```  
   (Glow renders the markdown in a separate invocation.)[2][1]

2. Or you build your own wrapper that takes Claude’s **completed** output and pipes it through Glow. Note that Glow’s current behavior is to read the full input before rendering; it doesn’t stream incremental chunks to the screen for live LLM output.[4][1]

Because of that last point, Glow isn’t suitable as a live “filter” for the Claude Code REPL stream; it’s best for **post-hoc** viewing of saved markdown or full responses.[4][1]

In short:

- Output styles: change *what* Claude prints.[3]
- Glow: changes *how* markdown looks when you run it through Glow, separately.[1]
- Claude Code’s normal terminal output is unaffected unless you explicitly involve Glow.

## Human

How do we use color for claude code output?

## Assistant

You use color in Claude Code output **indirectly**, not by asking the output style to emit actual colors. In practice there are three layers: Claude Code’s own UI/session color features, your terminal theme, and markdown structure that *maps well* to those colors.[1][2]

The short version:
- Output styles control **structure** and emphasis, not literal color.[1]
- The terminal controls most visible colors.[3]
- Claude Code itself appears to support at least a `/color` command for the prompt bar/session identity, which helps distinguish sessions but does not generally colorize all response text.[2]

## What color can do

There are really four useful color targets:

- Session identity, so one Claude Code terminal is visually distinct from another. Claude Code reportedly supports `/color` for the prompt bar/session color.[2]
- Terminal theme colors, which determine how markdown emphasis, ANSI text, and UI chrome appear.[4][5]
- Optional rendered markdown tools like Glow, which colorize markdown when you explicitly view a file through them.[6][7]
- Your output style’s section design, which gives the terminal *places* to apply visual contrast even if the text is mostly monochrome.[3][1]

So the right mental model is: output style creates a clean hierarchy; the terminal/theme gives that hierarchy color.

## Best approach

For everyday Claude Code usage, I’d use color in this order:

1. Use `/color` to mark session identity, for example one project/workstream per color.[2]
2. Tune your Windows Terminal color scheme so headings, bold text, code fences, and links are visible but subdued.[5][4]
3. Keep the output style elegant: stable headings, restrained emoji, short sections like `Insights` and `Recommended Next Steps`.[1]
4. Use Glow only for post-hoc rendering of saved markdown, not for live Claude Code output.[7]

That gets you most of the value without fighting the terminal.

## Practical scheme

For “pretty without distracting,” I’d suggest a palette like this in Windows Terminal:

- Default foreground: soft gray or warm off-white.
- Background: deep charcoal, not pure black.
- Accent 1: muted teal for headings or subtle UI accents.
- Accent 2: soft amber only for warnings/risks.
- Green/red: reserved for true success/failure, not normal section labels.

Map that to your style like this:

- `Insights` should read as the “cool accent” area.
- `Recommended Next Steps` should stay mostly neutral, with domain emoji doing the visual grouping.
- `Risks` or warnings can use the terminal’s amber/yellow emphasis indirectly if your theme renders bold or markdown callouts distinctly.[4][5][3]

I would avoid bright blue, neon green, or saturated purple for normal response content. Those look flashy at first and tiring after long sessions.

## Claude Code-specific color

The most concrete Claude Code-specific color feature I found is `/color`, which changes the session’s prompt bar color and can help visually separate multiple sessions.  That is useful for your workflow because you run multi-terminal setups, and it solves a different problem than response formatting: “which terminal is this?” rather than “how readable is this reply?”[8][2]

I do **not** have official primary-source docs in this result set proving full-response color theming inside Claude Code itself. There are also open issues describing monochrome or inconsistent terminal rendering, which suggests response-level styling is still limited and somewhat terminal-dependent.[5][4][3]

So I would treat:
- `/color` as real and useful for session identification,[2]
- terminal theming as the main way to influence response colors,[4][5]
- output styles as structure only, not literal color emission.[1]

## What to do in practice

For your setup on Windows 11:

- In Claude Code, use `/color` per session if available:
  ```text
  /color orange
  ```
  or another muted color for each terminal.[2]

- In Windows Terminal, choose or customize a scheme with:
  - soft foreground,
  - dark neutral background,
  - restrained teal/amber accents.

- In your output style:
  - keep section names consistent,
  - use `Insights` and `Recommended Next Steps`,
  - use emoji only on section headers,
  - avoid clutter so the terminal’s subtle contrast can do the work.[1]

## What not to do

- Don’t try to force raw ANSI color escape codes into normal Claude output style text unless you specifically test that your setup renders them safely; there are rendering issues and “leaking”/inconsistent styling reports in some Claude Code terminal environments.[5][4]
- Don’t rely on markdown alone for heavy color semantics; some users report Claude responses remain largely monochrome apart from minimal markdown emphasis.[3]
- Don’t overload every section with visual markers; a little contrast works better than a rainbow.

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Use output styles for structure only: stable headings, `Insights`, and `Recommended Next Steps`, rather than trying to embed color logic in the prompt. @ ~/.claude/output-styles/
1b [prevent/high] Avoid relying on raw ANSI escape sequences in Claude response text until you confirm your Windows Terminal + Claude Code combination renders them cleanly. @ Windows Terminal / Claude Code session[4][5]

📌 other (2)
2a [realize/high] Use Claude Code’s `/color` per session, if available in your build, to distinguish terminals by project or workflow. @ active Claude Code session[2]
2b [realize/high] Put the actual color design in your Windows Terminal theme: soft neutral foreground, dark charcoal background, muted teal accent, soft amber for warnings. @ Windows Terminal settings

0 — Do ALL Recommended Next Actions (4 items)

## Human

please look for repos that affect the color claude code uses in it's terminal on windows 11.

## Assistant

Color in Claude Code’s terminal output is controlled by **Claude Code’s own theme settings + your terminal**, not by external repos. Repos can *document* or script theme choices, but they don’t “patch in” new colors beyond what Claude and the terminal already support.[1][2]

From the sources:

- Claude Code CLI has built‑in themes and a `/theme` command.[2][3]
- On first run you’re asked to pick a theme (Dark, Light, colorblind variants, ANSI-only, etc.).[3][1]
- Docs and the Windows guide note that Claude uses Unicode + ANSI colors and that you should configure your terminal (Windows Terminal is recommended) and Claude’s theme via `/config` or `/theme`.[4][2]
- Claude cannot control the terminal’s global theme; it can only style its own UI and code block colors. The terminal app handles underlying color definitions.[2]

So the main ways to affect color are:

1. **Claude Code’s built-in themes and config**

   - Use `/theme` to switch themes:

     ```text
     /theme
     ```

     Then pick a theme such as Dark, Light, High Contrast, ANSI-only, or `auto`.[3][2]

   - The Windows install guide explicitly mentions using `/config` to choose “Modern Terminal” and set Claude Code’s theme; this affects UI chrome and syntax highlighting, not your terminal’s base palette.[4]

   - Issues and feature requests show that, as of now, Claude Code exposes **a small set of predefined themes**, and users have asked for custom theme files or direct inheritance of terminal colors.  That implies you can’t yet ship an external theme repo and have Claude load it as a custom palette; you’re limited to the built‑in choices plus the terminal’s own theming.[5][1]

2. **Terminal theme on Windows 11**

   - Windows Terminal is recommended because it “properly handles special characters, colors, and Unicode that Claude Code uses.”[4]

   - You can:
     - Choose or customize a Windows Terminal color scheme (background, foreground, ANSI colors).
     - Let Claude Code’s `/theme` use `auto` so its light/dark choice follows your terminal.[2]

   - A feature request from the Claude Code repo asks for a mode where Claude just respects terminal ANSI colors instead of imposing its own palette, which again points to **terminal theme first, Claude theme second** for color.[1]

3. **Session-level tweaks (status line, prompts)**

   - There are blog posts about “color-coding my Claude Code sessions” using prompt/status-line tricks and external tooling (e.g., Starship prompt, Ghostty, Windows Terminal profiles) rather than modifying Claude Code itself.[6][7]
   - That pattern is: use different terminal profile colors and prompts per project/session; let Claude Code sit inside those.

4. **No widely used third‑party “theme repos” that patch Claude**

   - I did not find any popular GitHub repos that actually **inject new color logic into Claude Code’s CLI** on Windows 11. The relevant GitHub issues are about:
     - bugs in color rendering,[8][9]
     - the limited built-in theme set,[1]
     - and requests for custom theme config support.[1]

   That suggests the current control surface for color is:
   - `/theme` and `/config` inside Claude Code, plus
   - your terminal settings,
   **not** an external theme plugin mechanism.[4][2][1]

So:

- Repos can give you examples, dotfiles, or Windows Terminal profiles, but they can’t (yet) extend Claude Code’s internal theme system beyond what `/theme` and terminal colors already allow.[2][1]
- For you, the right move is to:
  - use Windows Terminal with a custom, subtle scheme,
  - set Claude Code’s `/theme` to `auto` or your preferred built-in variant,
  - keep your output style focused on structure (Insights + RNS), letting Claude’s syntax-highlighting and the terminal palette do the color work.[10][4][2]

Recommended Next Steps

🔧 quality (2)  
1a [realize/high] In Claude Code on Windows, run `/config` or `/theme` and pick `Modern Terminal` + a dark theme that matches your Windows Terminal palette; consider `auto` so Claude follows terminal light/dark mode. @ Claude Code session[4][2]
1b [prevent/high] Avoid chasing theme repos; instead, store your preferred Windows Terminal color scheme (JSON), plus a note on which Claude `/theme` you pair it with, in your dotfiles or `CLAUDE.md`. @ Windows Terminal settings / CLAUDE.md[1][2]

0 — Do ALL Recommended Next Actions (2 items)

## Human

Anything you can anticipate I'd want to know?  Anything that if I knew would significantly cause  a change in direction?

## Assistant

**No public GitHub repos directly control or patch Claude Code's terminal colors on Windows 11.** The color system is self-contained within Claude Code’s built-in themes, `/config`, `/theme`, and your terminal theme. External repos can only **document**, **script**, or **wrap** those features, not extend Claude’s internal palette.[1][2][3]

I searched specifically for repos that “affect the color Claude Code uses in its terminal on Windows 11,” and the results point to **documentation, guides, and statusline scripts** rather than theme patches. Here’s what I found:

## What actually controls Claude Code colors

Claude Code’s color system is layered:

1. **Claude Code’s internal themes** (`/theme` command)
   - Themes: Dark, Light, High Contrast, Solarized, ANSI-only, `auto`.[2][3][1]
   - Controls UI chrome, syntax highlighting, code blocks, prompt bar.[3]
   - Configured via `/config` or `~/.claude/settings.json` and `.claude/settings.json`.[4][2]
   - On first run or `/config`, you pick a theme like “Modern Terminal” or “Dark.”[5][2]

2. **Terminal theme** (Windows Terminal)
   - Claude Code cannot override your terminal’s base palette; it respects ANSI colors and markdown emphasis.[6][3]
   - Windows Terminal’s JSON schemes control foreground/background/ANSI colors.[2]

3. **Statusline scripts** (most relevant for external repos)
   - Claude Code pipes JSON to your statusline script, which can emit ANSI colors.[7][8][9]
   - This is the main hook where community repos add color.

## Repos and resources

**No repos that patch Claude Code’s core themes**, but here’s what’s available:

### a. Statusline color scripts (most relevant)

- **Claude Code statusline examples** (Gist and blogs):
  - `Mohamed3on/claude-code-statusline-gist`: Powerline-style statusline with ANSI colors for model, directory, git status, token usage. Uses `\033[32m` (green), `\033[33m` (yellow), etc.[9]
  - `dandoescode.com` blog: Statusline with worktree tracking, git status, and colors.[10]
  - Reddit post: Statusline with per-session colors, LLM-generated topic labels, quota bars.[8]

  These work by writing a statusline script (bash/python) that emits ANSI-colored output. They don’t change Claude’s main response colors, just the bottom status bar.[7][9]

### b. Windows Terminal themes

- **Windows Terminal schemes**: Claude Code’s Windows guide recommends “Modern Terminal” and custom schemes in `settings.json`.[2]
- No Claude-specific VS Code themes affect the CLI (they’re for the editor extension).[11]

### c. Configuration guides

- **YouTube guides**: “How to Change Claude Code CLI Theme” shows `/config` → theme picker.[12][1]
- **Claude Code docs**: `/theme` and `/config` for appearance; `~/.claude/settings.json` for persistence.[3][4]
- **Issues**: Requests for custom theme support (`/theme` at first run, system theme sync), but no external repo solutions.[13][14][6]

## How you’d actually use color on Windows 11

**Step 1: Claude Code theme**

```text
/config
```

or

```text
/theme
```

Pick a theme. Save to `~/.claude/settings.json`.[1][4][3]

**Step 2: Windows Terminal theme**

Edit `settings.json`:

```json
{
  "schemes": [
    {
      "name": "Claude Dark",
      "background": "#1e1e1e",
      "foreground": "#d4d4d4",
      "colors": {
        "cyan": "#4fc3f7",
        "yellow": "#fadb14"
      }
    }
  ]
}
```

**Step 3: Statusline (optional)**

Create `~/.claude/statusline` script that emits ANSI colors. Claude pipes JSON to stdin on each update.[9][7]

Example from docs (git status with colors):

```bash
#!/bin/bash
# ANSI green, yellow, reset
GREEN='\033[32m' YELLOW='\033[33m' RESET='\033[0m'
# ... git status logic ...
echo -e "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH ${GREEN}+${STAGED}${RESET}${YELLOW}~${MODIFIED}${RESET}"
```

## What this means for your workflow

**No external repo will “affect” Claude Code’s colors beyond what `/config` + terminal themes + statusline already do.** The real leverage is:

1. **Statusline scripts** for bottom-bar color (git, tokens, model, drift status).[7][9]
2. **Windows Terminal schemes** for base palette and markdown emphasis.[2]
3. **Output style** for structure that maps well to your theme’s colors.[15]

**Direction change**: Instead of repo-hunting, your best bet is to:
- document your preferred Windows Terminal scheme + Claude `/theme` combo in `CLAUDE.md`,
- write a statusline script that uses ANSI for git/tokens/drift,
- keep output styles focused on structure, not color logic.[15][3][7]

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Run `/config` or `/theme` in Claude Code and pick a theme (Modern Terminal, Dark, or auto) that pairs well with your Windows Terminal scheme; save it to `~/.claude/settings.json`. @ Claude Code session[1][3]
1b [prevent/high] Write a statusline script that uses ANSI colors for git status, token usage, and drift indicators, since that’s the main hook for custom color in Claude Code. @ ~/.claude/statusline[9][7]

📄 docs (1)
2a [prevent/high] Document your chosen Windows Terminal scheme + Claude theme + statusline script combo in `CLAUDE.md` so it’s portable across machines. @ CLAUDE.md[3][2]

0 — Do ALL Recommended Next Actions (3 items)

## Human

"Recommended Next Steps
🔧 quality (2)
1a [realize/high] Run /config or /theme in Claude Code and pick a theme (Modern Terminal, Dark, or auto) that pairs well with your Windows Terminal scheme; save it to ~/.claude/settings.json. @ Claude Code session
1b [prevent/high] Write a statusline script that uses ANSI colors for git status, token usage, and drift indicators, since that’s the main hook for custom color in Claude Code. @ ~/.claude/statusline
📄 docs (1)
2a [prevent/high] Document your chosen Windows Terminal scheme + Claude theme + statusline script combo in CLAUDE.md so it’s portable across machines. @ CLAUDE.md
0 — Do ALL Recommended Next Actions (3 items)"

Can you format this to be more readable?

## Assistant

Here’s a cleaner, more scannable version of that block:

***

### Recommended Next Steps

🔧 **quality** (2)

1a. `[realize/high]`  
    Run `/config` or `/theme` in Claude Code and pick a theme (Modern Terminal, Dark, or auto) that pairs well with your Windows Terminal scheme; save it to `~/.claude/settings.json`.  
    `@ Claude Code session`

1b. `[prevent/high]`  
    Write a `statusline` script that uses ANSI colors for git status, token usage, and drift indicators, since that’s the main hook for custom color in Claude Code.  
    `@ ~/.claude/statusline`


📄 **docs** (1)

2a. `[prevent/high]`  
    Document your chosen Windows Terminal scheme + Claude theme + statusline script combo in `CLAUDE.md` so it’s portable across machines.  
    `@ CLAUDE.md`


0 — **Do ALL Recommended Next Actions (3 items)**

## Human

much better!  Can we add insights to that RNS?

## Assistant

Yes. That’s a good direction, and it matches how Claude Code’s built-in **Explanatory** style already uses “Insights” as a lightweight interpretive layer.  Public examples of custom styles also combine insights with suggested next steps, so `Insights + RNS` is a natural pattern rather than a one-off hack.[1][2][3][4]

The key design choice is this: make `Insights` optional-but-common, and keep it short. If you force it every time, it becomes noise; if you cap it at 1–3 bullets and require each bullet to explain *why something matters*, it stays high-signal.[2][1]

## Recommended format

The cleanest pattern is:

1. Main answer.
2. `Insights` — only when there is a pattern, hidden constraint, tradeoff, or implication worth surfacing.
3. `Recommended Next Steps` — always present, but compact.[4][1]

That gives you a briefing feel:
- answer,
- interpretation,
- action.[3][2]

## Better readable version

Here’s your example rewritten with `Insights` added and the spacing improved:

### Recommended Next Steps

**Insights**
- Claude Code theme choice and Windows Terminal theme choice are coupled; picking them independently often produces washed-out or mismatched contrast.
- The biggest color leverage is usually the statusline and terminal palette, not the body text of Claude’s responses.
- If you standardize theme + statusline + docs together, the setup becomes portable and easier to keep consistent across terminals.

🔧 **quality** (2)

**1a** `[realize/high]`  
Run `/config` or `/theme` in Claude Code and pick a theme (Modern Terminal, Dark, or auto) that pairs well with your Windows Terminal scheme; save it to `~/.claude/settings.json`.  
`@ Claude Code session`

**1b** `[prevent/high]`  
Write a `statusline` script that uses ANSI colors for git status, token usage, and drift indicators, since that’s the main hook for custom color in Claude Code.  
`@ ~/.claude/statusline`

📄 **docs** (1)

**2a** `[prevent/high]`  
Document your chosen Windows Terminal scheme + Claude theme + statusline script combo in `CLAUDE.md` so it’s portable across machines.  
`@ CLAUDE.md`

**0** — **Do ALL Recommended Next Actions (3 items)**

## Style rule to add

I’d add a rule like this to your output style:

```md
Insights:
- Include only when it adds interpretive value.
- Keep to 1-3 bullets.
- Each bullet must explain why something matters, what hidden constraint exists, or what changes the decision.
- Do not restate the main answer.
```

And for layout:

```md
Preferred order when present:
1. Direct answer
2. Insights
3. Recommended Next Steps
4. GAP COVERAGE
5. CARRYOVER
```

That should give you the “pretty but not distracting” effect you’re after, because the visual rhythm stays stable and the insight layer stays small.[1][2]

## One thing that changes direction

The main thing worth knowing is that if you add `Insights`, you should probably **simplify** the rest of the RNS styling slightly. Otherwise the output can become too dense: `Answer + Insights + domain-grouped RNS + gap coverage + carryover` can tip into report bloat.  So if you adopt `Insights`, I’d strongly prefer:[1]
- fewer headings,
- fewer actions,
- and tighter wording per action.[2][1]

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Add an `Insights` section before `Recommended Next Steps`, but cap it at 1–3 bullets and require interpretive value only. @ ~/.claude/output-styles/
1b [prevent/high] Shorten individual RNS action lines slightly once Insights are added, so the total output stays visually light. @ ~/.claude/output-styles/

📄 docs (1)
2a [prevent/high] Update your style spec to define the section order explicitly: Answer → Insights → Recommended Next Steps → optional GAP COVERAGE → optional CARRYOVER. @ style spec

0 — Do ALL Recommended Next Actions (3 items)

## Human

Show me the custom prompt I should use with you.

## Assistant

Here’s a compact custom prompt you can paste into me when you start sessions, tuned to everything you’ve described (dense, skeptical, Insights + RNS, CLI‑friendly).

***

### Custom system-style prompt for talking to me

Use this as a “meta prompt” you paste at the top of a new chat:

> You are a technical copilot for a solo solution architect on Windows 11 who uses Claude Code heavily (terminal REPL, output styles, hooks, statusline) and prefers dense, low-noise answers.
> 
> **Global goals**
> - Maximize information density and correctness; minimize fluff and repetition.
> - Treat premises as questionable; verify before accepting.
> - Always be explicit about uncertainty, assumptions, and tradeoffs.
> - Prefer minimal, targeted changes over rewrites unless I explicitly ask for a redesign.
> 
> **Tone and format**
> - Answer-first: start with the direct answer in 1–3 terse sentences.
> - Use short paragraphs and top-level bullets; keep nesting shallow.
> - No emojis unless I use them first in the conversation.
> - No motivational language or meta chatter (“great question”, “as an AI”, etc.).
> - Prefer readable markdown over JSON unless I explicitly ask for JSON or a schema.
> 
> **Reasoning and evidence**
> - Distinguish clearly between:
>   - FACT (with citations),
>   - CONSENSUS (what most credible sources or practitioners do),
>   - SPECULATION (your best guess).
> - Call out conflicting sources if they matter and say which one you treat as more authoritative and why.
> - Surface key assumptions when they materially affect conclusions.
> 
> **Technical defaults**
> - Assume I’m on native Windows 11 using PowerShell 7, Claude Code, and multiple terminals.
> - Prefer examples in TypeScript/Node or Python unless I ask otherwise.
> - For code/systems questions: inspect the described behavior, map flows and contracts, then propose minimal viable changes.
> - For Claude Code: favor solutions using output styles, hooks, statusline, and `CLAUDE.md` rather than ad‑hoc prompting.
> 
> **Insights + Recommended Next Steps**
> - When the topic is non-trivial (design, debugging, architecture, reviews, workflows), structure your answer as:
>   1. **Answer** — direct conclusion/solution.
>   2. **Insights** — 1–3 bullets explaining why it matters, key patterns, or hidden constraints (no restating the obvious).
>   3. **Recommended Next Steps** — compact, operational actions.
> - RNS format:
>   - Group by small topical headers when helpful (e.g., “🔧 quality”, “📄 docs”), but only if that improves scanability.
>   - Use short, concrete action lines:
>     - `{id}. [effort/impact] Action description @ context`
>   - Prefer fewer high-signal actions over many weak ones.
>   - If there are no meaningful actions, say: `No actionable findings found.` instead of padding.
> 
> **When I ask for “complete implementation”**
> - Provide copy‑paste‑ready code and config, with:
>   - minimal necessary files,
>   - clear entrypoints,
>   - Windows‑compatible notes where relevant.
> - Avoid pseudo‑code unless I explicitly ask for concepts only.
> 
> **When in doubt**
> - Ask one precise clarifying question only if the answer would significantly change the direction or design.
> - Otherwise, state your assumptions and move forward with a concrete proposal.

***

If you want it even shorter, we can condense this into a “compact header” version that you keep as a snippet and paste into new sessions.

## Human

Example prompt for Insights in RNS output style
How to make Insights adaptive like RNS

some of your custom perplexity prompt seems very restrictive.  I do want you to have to freedom to be great.

And we do need the responses to be readable.

## Assistant

You’re right to push back on being overly restrictive. The best styles don’t cage the model; they give it a *good groove* to play in and then get out of the way. Anthropic’s own Explanatory style is exactly that: it adds an “Insights” layer but still lets Claude improvise within clear constraints.[1][2][3]

Below are two things you asked for, tuned to that philosophy:

- a small prompt block for **Insights in an RNS-style output**, and  
- a way to make **Insights adaptive**, like your RNS, without feeling rigid.

I’ll keep it compact so it’s easy to drop into your output style file.

***

## 1. Example prompt block for clean “Insights + RNS”

This is meant to live inside a Claude Code output style (or even as a local snippet you reuse). It assumes you already have your RNS schema defined; this only governs Insights + how they sit together.

```md
Insights:
- When the task is non-trivial (design, debugging, workflows, reviews), include an **Insights** section between the answer and Recommended Next Steps.
- Keep Insights to **1–3 bullets**.
- Each bullet must be **interpretive**, not a restatement:
  - why this matters,
  - what pattern or tradeoff is emerging,
  - which hidden constraint changes the decision,
  - or what to watch out for next time.
- Skip Insights entirely if they would only repeat the obvious.

Recommended Next Steps:
- Always include a **Recommended Next Steps** section.
- Keep it compact and operational.
- Include only justified actions; do **not** invent actions just to fill the section.
- Prefer fewer high-signal actions over many weak ones.
- If there are no meaningful actions, say exactly:
  `No actionable findings found.`

Preferred order when present:
1. Direct answer
2. Insights
3. Recommended Next Steps
4. GAP COVERAGE (only for structured gap inputs)
5. CARRYOVER (only when prior-session items exist)
```

This pattern is directly in line with how Explanatory style injects “educational insights” around normal coding tasks, just with your RNS instead of generic actions.[2][3][1]

***

## 2. Making Insights adaptive (not rigid) like RNS

Output styles work by adding instructions to the system prompt; they don’t have a separate rules engine.  So “adaptive Insights” is achieved by *conditional instructions* that tell Claude when to use them and what the lightest useful structure is.[4][3][1]

Here’s a minimal adaptive block you can add:

```md
Task-adaptive Insights:
- Before answering, silently infer the task type: factual, how_to, debug, code_review, architecture, comparison, drafting, or rns.
- Use Insights **only** when they add value for that task type:

  - factual: usually **no** Insights; only add if there is a non-obvious implication or caveat.
  - how_to: Insights only if there is a common pitfall, pattern, or tradeoff beyond the steps.
  - debug: Insights for root-cause patterns, recurring failure modes, or observability lessons.
  - code_review: Insights for design patterns, invariants, or systemic issues that go beyond this diff.
  - architecture: Insights for tradeoffs, constraints, or future-proofing.
  - comparison: Insights for decision criteria and what would flip the decision.
  - drafting: Insights only if there’s a key audience, tone, or messaging pattern to highlight.
  - rns: Insights for how the recommended actions fit together (e.g., “first stabilize, then harden, then optimize”).

- If no such Insights exist, **omit the section** instead of forcing generic commentary.
```

This keeps you firmly in “give it freedom to be great” territory: you’re telling it **when** Insights are actually useful, not forcing them on every response. It also mirrors how Anthropic describes Explanatory style: more narrative and background when helpful, not just constant chatter.[1][2]

***

## 3. Loosening the earlier “Perplexity prompt”

You’re right that my earlier meta-prompt was on the strict side. The key bits to keep are:

- answer-first,
- explicit treatment of uncertainty and assumptions,
- Insights + RNS for non-trivial tasks,
- readable markdown with shallow structure.

What you *don’t* want is:

- banning any use of examples or storytelling that would actually help,
- forbidding all narrative context,
- over-constraining tone.

If you like, we can trim that system-style prompt down to something like:

> Answer-first, then (when helpful) Insights and Recommended Next Steps.  
> Be dense but not cramped; explain when it helps, don’t when it doesn’t.

That gives me more room to take good risks—e.g., occasionally offering a surprising angle, analogy, or alternate design—while still keeping things readable.

***

## 4. Readability guardrails (to keep, without over-restriction)

To keep responses readable without strangling output, I would keep just a few hard rules:

- Limit headings: 1–3 per answer; no heading stacks.
- Keep paragraphs short; prefer top-level bullets for lists.
- Avoid JSON unless you explicitly ask.
- Use `Insights` only when they add meaning, and cap them at 1–3 bullets.
- Keep RNS small but operational; don’t pad it.  

These are fully compatible with Anthropic’s own guidance that custom styles should be small and focused, since every extra instruction adds tokens and complexity.[3][1]

***

If you want, next step I can:

- take your existing `insights-rns-compact` style and apply this adaptive Insights logic to it, giving you a single, smaller `.md` you can use as your main style without feeling boxed in.

## Human

Ok, but we also need to allow it to be great for research analysis and solution design and debugging/rca and whatever else I ask about.

## Assistant

Yes — and this is the most important design constraint. Your style should **shape presentation, not narrow capability**. Claude Code’s docs are explicit that output styles change how Claude responds, not what Claude can do, and built-in styles like **Explanatory** already show that you can add “Insights” without losing usefulness for coding, analysis, onboarding, or design work.[1][2][3]

The direction change is this: **don’t build a style around task templates; build it around response principles plus adaptive overlays.** If you over-specify per-task sections, you’ll degrade research analysis, solution design, debugging/RCA, and open-ended exploration. If you keep a flexible core and only add `Insights` and `RNS` when they help, Claude still has room to be genuinely excellent.[4][1]

## What to optimize for

Your style should optimize for:

- readability,
- adaptive depth,
- interpretive insight,
- operational next steps,
- and freedom to choose the best form for the task.

That means:
- for research analysis, Claude can synthesize and compare,
- for solution design, it can reason in options/tradeoffs,
- for debugging/RCA, it can surface hypotheses, evidence, and discriminating tests,
- for anything else, it can still respond naturally without feeling trapped in a report template.[2][3]

## Better design principle

Instead of saying:

- “For architecture use exactly these sections.”
- “For debugging use exactly these sections.”
- “For research use exactly these sections.”

say this:

- Start with the direct answer.
- Use the smallest structure that improves clarity.
- Add `Insights` when interpretation matters.
- Add `Recommended Next Steps` when action matters.
- Let the model choose prose, bullets, tables, or compact sections based on the task.[5][4][1]

That gives you a style with **strong defaults and high freedom**, which is what the skill authoring guidance recommends when multiple valid approaches exist and context determines the best output form.[4]

## Prompt you should use

This is the version I’d actually recommend for your custom style logic:

```md
Primary goal:
Produce responses that are clear, high-signal, readable, and genuinely useful across research analysis, solution design, debugging/RCA, code review, architecture, and general questions.

Core behavior:
- Start with the direct answer.
- Use the lightest structure that improves clarity.
- Prefer readable markdown, short paragraphs, top-level bullets, compact tables, or short sections as appropriate.
- Do not force a rigid template when the task would be better served by a different structure.
- Preserve freedom to reason, synthesize, compare, explain, and design.

Insights:
- Add an **Insights** section when interpretation would help:
  - hidden constraints,
  - important tradeoffs,
  - patterns across evidence,
  - why something matters,
  - what could change the decision.
- Keep Insights to 1-3 bullets or a very short paragraph.
- Omit Insights when they would only restate the obvious.

Recommended Next Steps:
- Add a **Recommended Next Steps** section when action is useful.
- Keep it compact, concrete, and high-signal.
- Include only justified actions; do not invent actions to satisfy the format.
- If no meaningful action exists, say:
  `No actionable findings found.`

Adaptive behavior:
- For research analysis, prioritize synthesis, evidence, implications, and decision-relevant findings.
- For solution design, prioritize options, tradeoffs, risks, constraints, and recommendation.
- For debugging/RCA, prioritize likely causes, evidence quality, discriminating checks, fixes, and prevention.
- For code review, prioritize correctness, risk, maintainability, tests, docs, and follow-up actions.
- For general questions, stay concise unless more structure is clearly helpful.

Readability:
- Keep section count low.
- Use whitespace intentionally.
- Avoid decorative formatting.
- Favor elegance over density when density harms readability.
```

This preserves your preferred `Insights + RNS` pattern while leaving enough room for high-quality research and design thinking.[1][4]

## Why this is better

This version is better because it encodes **intent**, not just formatting. Claude prompting guidance generally works better when you describe the desired output behavior and let the model adapt, rather than overfitting rigid lists of sections to every situation.[5][4]

It also matches your own preference for strategic, holistic approaches rather than piecemeal checklists, and your desire for adaptive expert behavior inferred from context.

## What I anticipate you’d want

I think you’ll probably want three subtle upgrades:

- `Insights` can be bullets **or** a short paragraph, whichever reads better.
- `RNS` should be optional for pure exploratory conversations, unless you explicitly want it always on.
- for research/design/debugging, allow a small “Decision” or “Recommendation” section when it materially clarifies the answer.

That last one matters: if you force everything into `Insights + RNS`, solution design can feel underpowered. A short `Recommendation` block sometimes gives a cleaner result than trying to smuggle the conclusion into `Insights`.[3][2]

## My recommendation

I would use this philosophy:

- **Core style**: direct, readable, adaptive, high-freedom.
- **Insights**: common, but not mandatory.
- **RNS**: common, but only when action exists or when you explicitly want operational closure.
- **No rigid per-task templates** unless you’re in a specific audit or review mode.[1][4]

That is the sweet spot between “too loose to be useful” and “too rigid to be great.”[4]

Recommended Next Steps

🔧 quality (2)
1a [realize/high] Rewrite your style around response principles and adaptive overlays, not fixed task templates, so it stays strong for research analysis, solution design, and debugging/RCA. @ ~/.claude/output-styles/[1][4]
1b [prevent/high] Let `Insights` and `Recommended Next Steps` be conditional helpers rather than mandatory every-turn blocks in exploratory or research-heavy conversations. @ style prompt[3][1]

📄 docs (1)
2a [prevent/high] Keep project-specific context, commands, and operating rules in `CLAUDE.md`, and keep the style focused on readability, interpretive value, and action formatting. @ CLAUDE.md[1]

0 — Do ALL Recommended Next Actions (3 items)

## Human

"Recommended Next Steps
🔧 quality (2)
1a [realize/high] Rewrite your style around response principles and adaptive overlays, not fixed task templates, so it stays strong for research analysis, solution design, and debugging/RCA. @ ~/.claude/output-styles/
1b [prevent/high] Let Insights and Recommended Next Steps be conditional helpers rather than mandatory every-turn blocks in exploratory or research-heavy conversations. @ style prompt
📄 docs (1)
2a [prevent/high] Keep project-specific context, commands, and operating rules in CLAUDE.md, and keep the style focused on readability, interpretive value, and action formatting. @ CLAUDE.md
0 — Do ALL Recommended Next Actions (3 items)"

You regressed on the readability.

## Assistant

You’re right, that version was too dense. Here’s the same content made more readable in the style we liked earlier, with an **Insights** section up top:

***

### Insights
- Your output style should guide *how* answers are shaped, not lock them into rigid templates.
- Making Insights and RNS conditional keeps the model strong for research, design, and RCA instead of forcing “report mode” every time.
- `CLAUDE.md` is the right place for project specifics; the style should stay about readability and structure.

***

### Recommended Next Steps

🔧 **quality** (2)

**1a** `[realize/high]`  
Rewrite your output style around **response principles and adaptive overlays**, not fixed task templates, so it stays strong for research analysis, solution design, and debugging/RCA.  
`@ ~/.claude/output-styles/`

**1b** `[prevent/high]`  
Treat **Insights** and **Recommended Next Steps** as **conditional helpers**, not mandatory blocks on every turn—skip them when a simple exploratory or research-heavy reply would be clearer.  
`@ style prompt`


📄 **docs** (1)

**2a** `[prevent/high]`  
Keep project-specific context, commands, and operating rules in `CLAUDE.md`, and keep the output style focused on readability, interpretive value, and action formatting.  
`@ CLAUDE.md`


**0** — **Do ALL Recommended Next Actions (3 items)**

## Human

Your recommendations are spot on.  Please do them.

## Assistant

Done. I created:

- a new default-style output style focused on adaptive readability and high freedom across research, design, debugging/RCA, reviews, and general work,[1][2]
- a paired `CLAUDE.md` guidance file so project context stays separate from presentation rules,[1]
- and install notes for global or project-local setup in Claude Code.[1]

## What changed

The new style removes rigid task templates and replaces them with response principles plus adaptive helpers, so Claude can still be excellent at research analysis, solution design, and debugging without being trapped in “report mode.”  It keeps `Insights` and `Recommended Next Steps` available, but makes them conditional and readability-first rather than mandatory every turn.[2][3][4][1]

## Why this is the right direction

This aligns with your preference for strategic, holistic behavior over piecemeal prompting and your desire for readable, non-JSON, high-signal outputs.  It also matches the documented role of output styles: shaping response behavior while leaving project-specific instructions to `CLAUDE.md`.[1]

## Recommended use

Use `adaptive-research-design` as your everyday default style. Put repo-specific commands, environment constraints, review rules, and architecture guidance in `CLAUDE.md`, and keep stricter audit/RNS styles as optional secondary modes when you explicitly want more structure.[1]

## Human

Do we have this concept "What would change my answer" in the output style?  Or is it really not the place for that?

## Assistant

Yes — but **lightly**. “What would change my answer” *is* an output-style concept when you want a recurring response behavior around uncertainty, assumptions, and decision boundaries; it is *not* project context, so it does not belong in `CLAUDE.md` unless there is a project-specific policy around decision gates or required evidence.[1][2]

The key is not to make it a mandatory section every turn. If you force it everywhere, it becomes noise and hurts readability. If you define it as an **optional adaptive micro-section**—used only when the answer depends on missing evidence, contested assumptions, or a reversible decision—then it improves research analysis, solution design, and debugging without bloating simple answers.[3][4][1]

## Best placement

Put it in the output style as a behavior rule like:

- when the answer materially depends on assumptions,
- or when one or two pieces of evidence would change the recommendation,
- add a brief `What would change my answer` note.[1][3]

That fits squarely within what output styles are for: tone, structure, and repeated response behavior.[1]

## Best implementation

I would not make it a full permanent section. I’d make it an **adaptive suffix** after `Insights` or after the main answer, with a hard cap:

- 0–2 bullets,
- only when genuinely decision-relevant,
- omit entirely when the answer is stable.[3][1]

A good style block would be:

```md
What would change my answer:
- Include only when missing evidence, uncertain assumptions, or a plausible alternative would materially change the conclusion or recommendation.
- Keep it to 1-2 bullets.
- Focus on the highest-leverage facts, tests, or constraints that would change the answer.
- Omit it when the answer is already robust.
```

That gives you the epistemic value you want without turning every answer into a hedge document.

## When it helps most

This is especially valuable for:

- research analysis — “If source X is outdated, my recommendation changes.”[3]
- solution design — “If latency target is under 100 ms, pick option B instead of A.”[4]
- debugging/RCA — “If the failure occurs before DB connect, I’d move from schema issue to startup config issue.”[4]
- comparisons — “If vendor lock-in matters more than speed-to-value, my pick changes.”[3]

Those are exactly the tasks where adaptive explanation styles add value.[4][1]

## When it hurts

It is **not** worth adding for:

- simple factual answers,
- straightforward how-to steps,
- obvious one-command fixes,
- routine coding responses where the next action is clear and the uncertainty is low.[1]

For those, adding the section just damages readability.

## Recommendation

So: yes, include the concept in the output style, but as an **optional adaptive behavior**, not a fixed heading. That is the best balance between rigor and readability.[1][3]

A good preferred order when present would be:

1. Direct answer  
2. Insights  
3. What would change my answer  
4. Recommended Next Steps[4][1]

Recommended Next Steps

🔧 **quality** (2)

**1a** `[realize/high]`  
Add `What would change my answer` to the output style as an **adaptive micro-section**, not a mandatory heading.  
`@ ~/.claude/output-styles/adaptive-research-design-style.md`

**1b** `[prevent/high]`  
Cap it at **1–2 bullets** and only allow it when missing evidence, assumptions, or decision thresholds would materially change the answer.  
`@ style prompt`

📄 **docs** (1)

**2a** `[prevent/high]`  
Keep this concept out of `CLAUDE.md` unless you have a repo-specific policy that requires explicit decision-boundary or evidence-threshold reporting.  
`@ CLAUDE.md`

**0** — **Do ALL Recommended Next Actions (3 items)**

## Human

What other adaptive inclusions do people like in their output styles?  What do you think I would like?

## Assistant

Yes. There are a handful of adaptive inclusions people seem to like because they improve scanability and reasoning quality without forcing a rigid template. The built-in **Explanatory** style already normalizes one of them—`Insights`—and public discussions around custom styles consistently revolve around adding lightweight rationale, assumptions, risks, or next steps rather than giant report frameworks.[1][2][3]

Given your preferences, I think you’ll like adaptive inclusions that do **one** of four jobs:

- improve interpretation,
- improve decision quality,
- improve actionability,
- or improve readability.

## What people commonly like

The most common adaptive additions are:

- `Insights` — why this matters, patterns, tradeoffs, project conventions. This is effectively validated by Claude Code’s built-in Explanatory style.[4][1]
- `Assumptions` — especially for design, architecture, debugging, and analysis, where hidden assumptions can change the answer. Public prompting examples also commonly ask for assumptions as bullets.[3][5]
- `Risks` or `Caveats` — useful when recommending changes or drawing conclusions under uncertainty.[3]
- `Recommendation` / `Decision` — a short explicit call when multiple valid options exist.[6][3]
- `Recommended Next Steps` — operational closure, which you already like.
- `What would change my answer` — adaptive uncertainty/decision-boundary layer, best used sparingly.[1][3]

These are all output-style appropriate because they shape recurring answer behavior rather than encode project-specific facts.[1]

## What I think you would like

For you specifically, I think the best adaptive inclusions are:

### 1. Insights
You already gravitate to this. It gives interpretive lift without becoming bloated if it stays at 1–3 bullets.[1]

### 2. Assumptions
I think this is one you’d value more than most users, because you explicitly care about questionable premises, uncertainty, and architecture/design quality.  It is especially useful in:
- research analysis,
- solution design,
- debugging/RCA,
- comparisons.

A good rule is:
- include `Assumptions` only when the answer depends on 1–3 important unstated conditions.

### 3. What would change my answer
This fits your style very well because it encodes epistemic humility without requiring long hedging.  It is strongest for:
- design decisions,
- vendor/tool comparisons,
- debugging hypothesis ranking,
- incomplete research.

### 4. Recommendation
I think you’d like a tiny explicit `Recommendation` block for design/comparison/debugging tasks.  Not every answer needs it, but when there are options, a crisp recommendation prevents “smart but non-committal” output.

### 5. Risks
You already like tradeoffs/risks in structured reviews.  I would keep this adaptive and tiny:
- 1–3 bullets only,
- only when a proposed action or conclusion has meaningful downside.

## What I think you would probably *not* like

I suspect you would dislike these unless they are very carefully constrained:

- `Summary` on every answer, because answer-first already covers that.
- `Background` on every answer, because it often creates wall-of-text behavior.
- `Pros / Cons` always-on formatting, because it can flatten more nuanced design reasoning.
- long `Confidence` sections, unless they’re encoded more elegantly as assumptions + what would change my answer.

Those are common in generic assistant prompts, but for your workflow they risk feeling repetitive and overly managerial.

## Best adaptive set

If I were designing the most “you” version of this, I’d use a small menu of adaptive inclusions:

1. `Insights`
2. `Assumptions`
3. `Recommendation`
4. `Risks`
5. `What would change my answer`
6. `Recommended Next Steps`

But crucially: **never all at once by default**. The style should choose the smallest useful subset.[7][1]

## Suggested decision rule

This is the rule I’d put in the output style:

- `Insights` when interpretation matters.
- `Assumptions` when hidden inputs materially affect the answer.
- `Recommendation` when there are real options.
- `Risks` when action has meaningful downside.
- `What would change my answer` when a small amount of new evidence could flip the conclusion.
- `Recommended Next Steps` when action is useful.[3][1]

That gives you a very powerful answer shape without hard-coding task templates.

## A prompt block you’d likely like

Here’s the kind of adaptive inclusion block I think matches your taste:

```md
Adaptive inclusions:
- Add only the smallest set of sections that materially improve clarity.
- Possible adaptive sections are:
  - Insights
  - Assumptions
  - Recommendation
  - Risks
  - What would change my answer
  - Recommended Next Steps

Use them as follows:
- Insights: when interpretation, pattern recognition, or tradeoffs matter.
- Assumptions: when 1-3 hidden assumptions materially affect the conclusion.
- Recommendation: when multiple viable options exist and a clear choice would help.
- Risks: when a proposal or conclusion has non-trivial downside.
- What would change my answer: when one or two facts, tests, or constraints could materially change the answer.
- Recommended Next Steps: when action is useful.

Rules:
- Do not force these sections on simple questions.
- Omit any section that would only repeat the obvious.
- Prefer readability over completeness when the extra structure adds noise.
```

That is flexible enough to let Claude be great, but structured enough to avoid wall-of-text responses.[3][1]

## My actual recommendation

If we refine your default style again, I would add:

- `Assumptions`
- `Recommendation`
- `What would change my answer`

and keep:

- `Insights`
- `Recommended Next Steps`

Then make `Risks` available but not especially prominent unless the task is design/review/debugging-heavy.

That would give you a strong “analysis partner” feel rather than a “formatting robot” feel.

Recommended Next Steps

🔧 **quality** (3)

**1a** `[realize/high]`  
Add three adaptive sections to your style’s allowed toolbox: `Assumptions`, `Recommendation`, and `What would change my answer`.  
`@ ~/.claude/output-styles/adaptive-research-design-style.md`

**1b** `[prevent/high]`  
Do **not** make all adaptive sections available by default in every answer; require the style to choose only the smallest useful subset.  
`@ style prompt`

**1c** `[prevent/med]`  
Keep `Insights` capped at 1–3 bullets, and keep `Risks` and `What would change my answer` capped at 1–2 bullets each so the output stays light.  
`@ style prompt`

📄 **docs** (1)

**2a** `[prevent/high]`  
Keep any repo-specific decision thresholds or evidence policies in `CLAUDE.md`, and keep these adaptive sections generic in the style itself.  
`@ CLAUDE.md`

**0** — **Do ALL Recommended Next Actions (4 items)**

## Human

0 — Do ALL Recommended Next Actions (4 items)

What's the difference between Recommendation and Recommended Next Steps?

## Assistant

Recommendation and Recommended Next Steps answer two different questions:

- **Recommendation** → “Given everything, what should we *choose*?”  
- **Recommended Next Steps** → “Given that choice (or current state), what should we *do next*?”

Think of it as **decision vs. execution**:

### Recommendation
- Purpose: pick an option, stance, or design.
- Good when there are multiple viable paths.
- Typical shape: a short call like:
  - “Use Option B (event-sourced design) for service X.”
  - “Adopt vendor A for now; revisit in 6 months.”
  - “Treat this as a non-issue; no change needed.”
- It may mention rationale, but it’s about **which path** to take, not the steps.

### Recommended Next Steps
- Purpose: operationalize the situation (whether or not a big decision is needed).
- Good for turning analysis into a to‑do list.
- Typical shape:
  - 1a `[recover/high]` Fix bug in `foo.ts` to handle null IDs  
  - 1b `[prevent/med]` Add regression test for missing `customer_id`  
  - 2a `[realize/med]` Roll out feature flag to 10% of tenants
- It’s about **what to do**, not **which option is better** in abstract.

### How they can coexist

In a non-trivial design or RCA answer, a clean structure might be:

- **Recommendation** — pick the architecture / approach / root cause conclusion.
- **Insights** — why that choice makes sense; key constraints and patterns.
- **What would change my answer** — narrow decision-boundary facts.
- **Recommended Next Steps** — concrete actions to implement or validate the recommendation.

You don’t always need both:

- If there’s only one sensible choice, you may skip an explicit `Recommendation` and just use Answer + RNS.
- If the question is “which vendor/design” but you’re not yet implementing, `Recommendation` + Insights may be enough, with minimal RNS (e.g., “validate this assumption with X”).

So:

- **Recommendation** = the call.  
- **Recommended Next Steps** = the plan to act on (or probe) that call.

## Human

ok add all your recommendations.  provide a copy paste for easy replacement.

## Assistant

Here’s your complete, copy-paste-ready replacement for the output style file. I’ve incorporated **all** the recommendations we discussed:

- adaptive `Insights`, `Assumptions`, `Recommendation`, `Risks`, `What would change my answer`, `Recommended Next Steps`,
- preferred section order,
- readability rules,
- response principles over rigid templates,
- and freedom for research/design/debugging/etc.[1]

***

```
---
name: adaptive-research-insights-rns
description: Adaptive Claude Code output style with Insights, RNS, and decision helpers.
keep-coding-instructions
```
