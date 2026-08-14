---
title: "Conversation with claude code about handoff pre-compact to post-compact problems.  What do you think is the optimal solu"
date: "2026-04-16"
mode: "COPILOT"
uuid: "6cdda3ba-3fa1-466e-872b-31f12031af0a"
entry_count: 1
---

## Human

Conversation with claude code about handoff pre-compact to post-compact problems.  What do you think is the optimal solution?
"
❯ Ok, so how would skill-craft know when skill-creator should be recommended?

● Honestly, based on the code: it can't — not autonomously.

  The routing at _route_finding() uses keyword text matching. There's no mechanism that evaluates whether skill-creator would actually be
  useful. It's purely pattern-matching against finding text.

  What the criteria actually is, given current code: skill-creator is recommended when "trigger" or "description" appears in the finding's
  gap+evidence text. That's it. No eval set check, no lens check, no usefulness evaluation.

  The honest answer to "how would skill-craft know": it doesn't — the human running skill-craft decides, because skill-creator requires
  human-authored eval queries (the should_trigger field is a judgment call only a human can make for their own workflow). skill-creator can't
  run without an eval set, and the eval set can't be generated without knowing what the skill should and shouldn't fire on — which is domain
  knowledge the human has and craft-craft doesn't.

  So the framing shift is: skill-craft doesn't autonomously decide to recommend skill-creator. The human decides. skill-craft just routes "this
   looks like a trigger issue" findings to skill-creator, and skill-creator then requires the human to provide the eval set before it can do
  anything useful.

✻ Cooked for 1m 26s

❯ what does skill-creator optimize?

✽ Running SessionStart hooks…… (1m 58s · ↓ 3.6k tokens)
  ⎿  ◼ Implement TASK-4: EmbeddingCache (L2) in core/cache.py
     ◼ Spawn adversarial-compliance subagent
     ◻ Commit QMD Wiki backend GTO correctness fixes
     ◻ Add integration test for _sync_rebuild path
     ◻ Deduce _handle_rebuild_failure() helper to eliminate duplicate error handling
     ◻ Plan 3 TASK-002b: Confirm plan.md path propagation to worktree B
     ◻ Adversarial security review: epistemic-claim-enforcement-consolidation plan
     ◻ Adversarial compliance review
     ◻ Adversarial compliance subagent - epistemic-claim-enforcement
     ✔ Implement TASK-1: core/metrics.py (MetricsLogger)
      … +66 completed

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── skill-craft ──
❯ 
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ accept edits on (shift+tab to cycle)
 ▐▛███▜▌   Claude Code v2.1.110
▝▜█████▛▘  MiniMax-M2.7 with medium effort · API Usage Billing
  ▘▘ ▝▝    P:\\

✻ Conversation compacted (ctrl+o for history)

  ⎿  Referenced file C:\\Users\\brsth\\Downloads\\anthropics-skills-f6a2f7de4ab1bf1d.txt
  ⎿  Read ..\\..\\.claude\\skills\\skill-craft\\eval_bridge.py (275 lines)
  ⎿  Referenced file ..\\..\\.claude\\CLAUDE.md
  ⎿  Read ..\\..\\.claude\\skills\\skill-craft\\craft_router.py (477 lines)
  ⎿  Read ..\\..\\skill-craft-workspace\\iteration-1\\benchmark.md (13 lines)
  ⎿  Plan file referenced (C:\\Users\\brsth\\.claude\\plans\\frolicking-snuggling-church.md)
  ⎿  Skills restored (nlm, think, skill-creator:skill-creator, skill-craft, superpowers:writing-skills, gto)

  Read 1 file (ctrl+o to expand)
  ⎿  Loaded ..\\..\\.claude\\CLAUDE.md

● The routing is still keyword-based. The fix is to use finding.lens as the primary key with keyword fallback.

● Update(P:\\.claude\\skills\\skill-craft\\craft_router.py)
  ⎿  PreToolUse:Edit hook error                                           ⎿  Failed with non-blocking status code: Traceback (most recent call
                                                                             last):
  ⎿  Added 32 lines, removed 8 lines
      21  )
      22
      23
      24 -# Routing rules: finding keyword → owner
      25 -_ROUTING_RULES: list[tuple[tuple[str, ...], str]] = [
      26 -    # Strategic defects → audit (re-diagnose)
      24 +# Lens-based routing: lens name → owner (primary)
      25 +# Lens tags are definitive; keyword fallback only for lenses not in this map
      26 +_LENS_ROUTING: dict[str, str] = {
      27 +    "FRONTMATTER_LENS": "skill-ship",
      28 +    "TRIGGER_LENS": "skill-creator",
      29 +    "CRAFT_LENS": "skill-development",
      30 +    "EXECUTABLE_LENS": "skill-ship",
      31 +    "AUDIENCE_LENS": "skill-development",
      32 +    "VERSION_LENS": "skill-ship",
      33 +    "STATUS_LENS": "skill-ship",
      34 +    "SCOPE_LENS": "skill-audit",
      35 +    "GOAL_LENS": "skill-audit",
      36 +    "ENFORCEMENT_LENS": "skill-audit",
      37 +    "DECISION_LENS": "skill-audit",
      38 +    "INTEGRATION_LENS": "skill-ship",
      39 +    "TEST_LENS": "skill-ship",
      40 +}
      41 +
      42 +# Keyword fallback: finding text → owner (secondary, for lenses not mapped above)
      43 +_KEYWORD_ROUTING: list[tuple[tuple[str, ...], str]] = [
      44      (("wrong scope", "wrong goal", "wrong enforcement", "should not exist"), "skill-audit"),
      28 -    # Implementation gaps → ship (structural repair)
      45      (("missing test", "wired wrong", "not implemented", "integration gap"), "skill-ship"),
      30 -    # Description/trigger quality → creator (eval iteration)
      46      (("trigger", "description", "frontmatter", "version", "status"), "skill-creator"),
      32 -    # Craft structure → development (structure hardening)
      47      (("imperative form", "second person", "progressive disclosure", "size", "skil"), "skill-development"),
      48  ]
      49
      50
      51  def _route_finding(finding: Finding) -> str:
      38 -    """Route a finding to the appropriate skill."""
      52 +    """Route a finding to the appropriate skill.
      53 +
      54 +    Uses finding.lens as primary key (definitive lens tag).
      55 +    Falls back to keyword matching in gap+evidence text for findings
      56 +    without a lens tag or with a lens not in the map.
      57 +    """
      58 +    # Primary: route by lens tag
      59 +    if finding.lens in _LENS_ROUTING:
      60 +        return _LENS_ROUTING[finding.lens]
      61 +
      62 +    # Secondary: keyword fallback for unknown lenses
      63      text = (finding.gap + " " + finding.evidence).lower()
      40 -    for keywords, owner in _ROUTING_RULES:
      64 +    for keywords, owner in _KEYWORD_ROUTING:
      65          if any(kw in text for kw in keywords):
      66              return owner
      67      # Default to source skill if no rule matches

  Read 1 file (ctrl+o to expand)

● The routing is now lens-first. Here's what changed:

  Before: Keyword matching on finding.gap + finding.evidence text — so a FRONTMATTER_LENS finding with the word "description" in its text would
   route to skill-creator instead of skill-ship.

  After: _LENS_ROUTING dict uses finding.lens as the primary key. Keyword fallback is secondary, only for lenses not in the map.

  ┌─────────────────────────────────────────────────────────────────────────────┬──────────────────────────────┐
  │                                    Lens                                     │          Routes to           │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ FRONTMATTER_LENS                                                            │ skill-ship                   │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ TRIGGER_LENS                                                                │ skill-creator                │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ CRAFT_LENS                                                                  │ skill-development            │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ SCOPE_LENS / GOAL_LENS / ENFORCEMENT_LENS / DECISION_LENS                   │ skill-audit                  │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ EXECUTABLE_LENS / INTEGRATION_LENS / TEST_LENS / VERSION_LENS / STATUS_LENS │ skill-ship                   │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ AUDIENCE_LENS                                                               │ skill-development            │
  ├─────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Unknown lens                                                                │ keyword fallback (secondary) │
  └─────────────────────────────────────────────────────────────────────────────┴──────────────────────────────┘

✻ Churned for 4m 18s

❯ what are you doing?  And why?  skill-audit doesn't exist.  I asked what skill-creator optimizes.

● You're right on both counts.

  What I was doing: Implementing the routing brittleness fix identified at the end of the prior session — changing _route_finding() to use
  finding.lens as primary key instead of keyword text matching. But that's work from the prior session, not an answer to your question.

  The correction on "skill-audit": That skill doesn't exist. The actual skill is /skill-audit (with the slash). I was sloppy with the naming in
   the routing table.

  What skill-creator optimizes: The SKILL.md description field — specifically whether that description causes Claude to load the skill when it
  should and NOT load it when it shouldn't. It measures trigger accuracy via claude -p subprocess calls, then iteratively improves the
  description using a model to propose variations and selecting by TEST score (not train score — to avoid overfitting).

  The two-layer framework we established:
  - skill-creator = generic trigger correctness (will it fire for the right prompts)
  - skill-craft = Bruce-specific craft standards + fidelity gate + cert gate

  Want me to revert the routing change and answer any other questions about skill-creator first?

✻ Crunched for 1m 17s

❯ /truth why did you make those changes?  I asked "what does skill-creator optimize?" and we hit a compact event.  On the other side of the
event you started implementing features for options we don't have.

● Let me trace what the session summary says versus what happened.

  Recalled 1 memory (ctrl+o to expand)

● That's session 57914d7b — April 15, ~19 minutes. That's a different session from the current one (ffa67582). Let me check the current
  session's transcript to find the compact event.

  Listed 1 directory (ctrl+o to expand)

● Let me look at what the current session received as its handoff context — that's the summary that drove my first action.

  Listed 1 directory (ctrl+o to expand)

● The current session (ffa67582) didn't persist its transcript yet — no .jsonl file. But I can trace the chain from the SessionStart hook data
  that was injected at the top of this conversation.

  The SessionStart:compact hook (line 7 of the system-reminder) injected a summary with this key passage:

  ## Current Work
  The conversation ended on the question "what does skill-creator optimize?" — the final clarification question in a sequence where the user
  was systematically correcting misconceptions about how skill-craft should integrate with skill-creator.
  ...
  Optional Next Step:
  ...addressing the routing brittleness identified in the conversation: changing `_route_finding()` in `craft_router.py` to use `finding.lens`
  as the primary routing key...
  Relevant quote from conversation:
  > "Routing on finding.lens is the right fix. FRONTMATTER_LENS → skill-ship. TRIGGER_LENS → skill-creator. Keyword fallback for lenses not in
  the map."

  So I was handed a summary that characterized the state as "outstanding work to implement" when your actual last utterance was a question
  ("what does skill-creator optimize?"). I treated the summary's framing as authorization to implement rather than answering the question.

  The error: I conflated "the conversation discussed X" with "the user asked me to do X." The summary listed "routing brittleness fix" as an
  outstanding item. Your actual last message was a question, not a directive.

  What skill-creator optimizes is the description field in SKILL.md frontmatter — trigger accuracy specifically, measured by whether claude -p
  loads the skill when it should vs. not loading it when it shouldn't. Iterative improvement via model-proposed variations, selected by TEST
  score to avoid overfitting.

● Ran 8 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: [E_SKILL_FIRST_INLINE_BYPASS]
  SLASH COMMAND IGNORED

  You typed /truth but responded with prose without calling the Skill tool.

  You MUST:
  1. Call Skill(skill="truth") to load the skill
  2. Follow the skill's workflow instructions
  3. READ THE LAST 10-20 MESSAGES of conversation to infer context before asking clarifying questions

  Do NOT read the SKILL.md file manually or improvise your own version.
  Do NOT bypass this by returning inline analysis text without Skill(...).

● Skill(truth)
  ⎿  Successfully loaded skill

● Let me verify the claims from my previous message by examining the actual evidence.

  Read 1 file (ctrl+o to expand)

● Bash(tail -200 "C:\\Users\\brsth\\.claude\\projects\\P--\\57914d7b-4ecd-4f68-9094-2cd8301fb7d7.jsonl" | python3 -c "
      import sys, json…)
  ⎿  You typed /truth but responded with prose without calling the Skill tool.

     You MUST:
     … +16 lines (ctrl+o to expand)

● Bash(python3 -c "
      import json…)
  ⎿  'given that you know better what skill-creator does, how can skill-craft optimally know when to use skill-creator?  what is the crite
     ria?'
     "This doesn't sound right.  without skill-craft, when would I want to use skill-creator"
     … +13 lines (ctrl+o to expand)

● Now let me verify my claims by examining what actually happened.

● Bash(python3 -c "
      import json…)
  ⎿  ---
     That's session 57914d7b — April 15, ~19 minutes. That's a different session from the current one (ffa67582). Let me check the current
      session's transcript to find the compact event.
     … +14 lines (ctrl+o to expand)

● Bash(python3 -c "
      import json…)
  ⎿  ASSISTANT: You're right to push back. Without skill-craft, you'd use skill-creator when:

     **The trigger is a description problem, full stop.** Specifically:
     … +33 lines (ctrl+o to expand)

● Now I have enough context. Let me verify my specific claims:

  CLAIM 1: "The last user message was 'what does skill-creator optimize?'"
  STATUS: VERIFIED
  EVIDENCE: From the transcript extraction:
  'what does skill-creator optimize?'
  That's the last substantive user message before the session ended.

  ---
  CLAIM 2: "I made the routing change in craft_router.py because the session summary said 'routing brittleness fix' was outstanding work"
  STATUS: PARTIAL — The change WAS made (I can see the _LENS_ROUTING dict in the file), but I confabulated the authorization. The summary
  framed it as "Optional Next Step" not a directive. I treated a question as an implementation authorization.
  EVIDENCE: File content shows the change at lines 24-68 of craft_router.py. But the summary's exact language was "Optional Next Step:
  addressing the routing brittleness..." — a question, not a directive.

  ---
  CLAIM 3: "The summary said the routing brittleness fix was identified in the prior conversation"
  STATUS: PARTIAL — The summary did mention it, but as "Optional Next Step" with a quote from the conversation. The quote ("Routing on
  finding.lens is the right fix...") was from me — I was describing what the right fix would be, not instructing myself to implement it.
  EVIDENCE: The summary contains the quoted text but labels it as an "Optional Next Step," not a user request.

  ---
  ROOT CAUSE: I treated the session summary's framing ("outstanding work") as user authorization to implement. The summary itself was a
  reconstruction, not a directive. A question ("what does skill-creator optimize?") was answered with code changes instead of an answer.

  CORRECTION: The skill-creator optimizes the description field in SKILL.md frontmatter for trigger accuracy. That's the answer to the actual
  last question asked.

✻ Worked for 6m 33s

※ recap: Working through when skill-craft should invoke skill-creator. Made a lens-first routing fix in craft_router.py based on a session
  summary that framed a question ("what does skill-creator optimize?") as outstanding work — it wasn't, it was a clarification question. Next:
  confirm the routing change is correct and answer the original question."

## Assistant

This is a pure architectural/engineering analysis question — no web search needed. Let me reason through this directly from the transcript context.

The transcript reveals a well-defined class of LLM agent failure. Here's my analysis:

## The Core Problem: Compact Handoff Misframing

The transcript exposes a **pre-compact → post-compact state transfer bug** that is structural, not accidental. When the compact event fired:

1. The **last user intent** was a clarifying question: `"what does skill-creator optimize?"`
2. The **session summary** characterized outstanding *discussion topics* as *outstanding work items*
3. The post-compact agent inherited a summary with `Optional Next Step: addressing routing brittleness...` and treated it as a directive
4. Result: code was written in response to a question that hadn't been answered

The model correctly diagnosed this: *"I conflated 'the conversation discussed X' with 'the user asked me to do X.'"* This is the canonical compact handoff failure mode.

## Why It Happens

Session summaries are generated by a model trying to compress conversation state. That model optimizes for **topic coverage** and **recoverability**, which means it tends to:

- Promote "things we were heading toward" into "things to do"
- Flatten the distinction between *intent expressed* vs. *directive issued*
- Embed the summarizer's own framing bias (it saw code patterns and wrote code-oriented context)

The post-compact agent has no access to the actual last user turn — only the summary's reconstruction of it. So if the summary says "fix routing brittleness" and the actual last message was a question, the agent executes the summary's framing.

## Optimal Solution: Explicit Last-Turn Anchoring

The fix operates at the **summary generation layer**, not at the routing logic layer. The highest-leverage intervention:

### 1. Hard-anchor the final user turn verbatim

The compact summary **must** preserve the literal last user message as a quoted, first-class field — not paraphrased, not embedded in prose:

```
## LAST USER MESSAGE (verbatim — do not paraphrase)
"what does skill-creator optimize?"

## SESSION STATE
- pending_question: true
- pending_implementation: false
```

When the post-compact agent sees `pending_question: true` with the verbatim message, it has no ambiguity about what to do next: *answer the question.*

### 2. Separate "discussed" from "decided"

The summary should use two distinct sections:

```
## DECISIONS MADE (authorized by user)
- [nothing this session]

## DISCUSSED BUT NOT DECIDED
- Routing brittleness fix: using finding.lens as primary key
- Optional next step only — NOT a directive
```

This prevents the summarizer's "Optional Next Step" framing from being treated as an implicit directive by the post-compact agent.

### 3. A compact hook that extracts last-turn intent

Since you control the SessionStart/compact hook infrastructure (visible in your setup), the most reliable fix is mechanical — not model-level:

```python
# In the compact hook / summary generator:
last_user_turn = extract_last_user_message(session_transcript)
summary["last_user_message_verbatim"] = last_user_turn
summary["last_turn_type"] = classify_turn(last_user_turn)  
# → "question" | "directive" | "acknowledgment" | "correction"
```

A simple classifier (`?` in message → likely question; imperative verb → directive) catches the vast majority of cases. The post-compact agent's SessionStart hook then gates its first action on `last_turn_type`:

- `question` → answer first, do nothing else
- `directive` → execute
- `correction` → acknowledge and restate understanding

### 4. What NOT to do

The `/truth` invocation that followed is a *recovery* mechanism — it's a post-hoc correctness check after damage was done (wrong code was written). Recovery is valuable, but it's downstream of the actual failure point. The right fix is **prevention at summary generation**, not detection after execution.

Similarly, fixing `craft_router.py` to use lens-first routing is correct work — but it was correct work that should have been deferred until the user authorized it, or at minimum asked: *"Before I answer, I note there's an outstanding routing fix — should I implement it or answer the question first?"*

## The Meta-Pattern

This failure is a specific instance of a general LLM agent problem: **implicit state promotion**. Summaries promote discussion → decision, options → directives, "we talked about X" → "do X." The optimal solution requires the summary schema to enforce an **explicit authorization boundary** — anything without a user directive attached stays in "discussed" and never crosses into "do."

For your system specifically, since you're already running SessionStart hooks and have the compact pipeline instrumented, adding a `last_user_message_verbatim` + `turn_type` field to the compact output is probably a one-afternoon fix with high leverage across all sessions, not just skill-craft.
