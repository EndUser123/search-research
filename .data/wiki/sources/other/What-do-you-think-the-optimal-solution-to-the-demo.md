<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# What do you think the optimal solution to the demonstrated problem is?

"
● Searched for 1 pattern (ctrl+o to expand)

● Now let me read the active UserPromptSubmit hook and check for investigation/coherence gates.

● Searched for 1 pattern, read 1 file (ctrl+o to expand)
⎿  Loaded .claude\\hooks\\CLAUDE.md

● Now let me look at what's in the UserPromptSubmit registry and check for the "first_tool_coherence" and
"investigate_before_explain" gates.

● Searched for 2 patterns, read 1 file (ctrl+o to expand)

● Now let me check what the UserPromptSubmit registry actually runs, and look at the Stop hooks for any
explicit-instruction enforcement.

● Searched for 2 patterns, read 1 file (ctrl+o to expand)

● Now I have enough evidence. Let me check one more thing - the operating_rules to see if "fetch don't ask" is enforced:

● Searched for 2 patterns (ctrl+o to expand)

● I now have sufficient evidence for a complete RCA. Here's the diagnosis:

---
RCA: No Explicit Instruction Execution Tracker Exists

Confidence: 90% (Tier 1-2, code inspection + architectural analysis)

---
Root Cause

The hooks never blocked this because no hook in this system enforces explicit user directives — the pattern "user said
'do X', LLM responded without doing X" has no detector.

What Actually Happened (Evidence)

The failure chain across two turns:

┌──────┬─────────────────────────────────────────────┬───────────────────────────────────────────────┬──────────────┐
│ Turn │               What user said                │                 What LLM did                  │     Was      │
│      │                                             │                                               │  detected?   │
├──────┼─────────────────────────────────────────────┼───────────────────────────────────────────────┼──────────────┤
│ N    │ "find them in chat history if you can't     │ Recreated from scratch, no Read tool call to  │ NO           │
│      │ find on disk"                               │ transcript                                    │              │
├──────┼─────────────────────────────────────────────┼───────────────────────────────────────────────┼──────────────┤
│ N+1  │ "Did you find them in chat history?"        │ Admitted it didn't                            │ NO           │
├──────┼─────────────────────────────────────────────┼───────────────────────────────────────────────┼──────────────┤
│ N+2  │ "Yes. Clearly I told you to."               │ Apologized, still didn't do it immediately    │ NO           │
└──────┴─────────────────────────────────────────────┴───────────────────────────────────────────────┴──────────────┘

---
Why Each Existing Hook DIDN'T Catch It

1. StopHook_cross_validator.py — checks for fabricated action claims ("I tried searching but got 429"). The LLM never
claimed to have searched — it silently skipped it. The cross-validator only catches claims of action, not omission of
required action. STATUS: INFERRING_FROM_CODE
2. investigate_before_explain.py — ARCHIVED (P:/.claude/hooks/_archive/). Not in the registry. Even if it were active, it
only triggers on skill-question patterns like "why didn't /debugRCA do X?", not on "find the instructions in chat
history." STATUS: TESTED_IN_ENV (confirmed not in core_hook_modules list at registry.py:601-632)
3. INVESTIGATE_BEFORE_EXPLAIN_ENABLED=true in settings.json is a dead env var — the hook it controlled was archived. This
is a latent confusion hazard. STATUS: TESTED_IN_ENV
4. StopHook_skill_execution_gate.py — detects /command usage where prose was produced instead of invoking Skill(). The
prior conversation wasn't a slash command being ignored; it was a free-form directive to search the transcript.
5. declaration_reminder.py + PreToolUse_arch_first_enforcer.py — detects LLM declarations ("I'll update the template")
and blocks tools until done. This requires the LLM to declare intent first. In this case, the LLM didn't declare it would
search — it just didn't.
6. The MEMORY.md quick rule "Fetch, don't ask" is a guideline, not an enforcement hook. There is no Stop hook that checks
"user said 'find X', did any Read/Glob/Grep tool run targeting that resource?"

---
The Structural Gap

Your system has coverage for:

- ✅ LLM fabricating actions it didn't take
- ✅ LLM declaring "I'll do X" then not doing it (arch enforcer)
- ✅ LLM bypassing /skill invocation
- ✅ LLM making unverified claims

It has no coverage for:

- ❌ User-issued directive + LLM silent omission — "search Y" → LLM responds without searching Y

The pattern user.explicit_directive("read transcript") → llm.response_without_read_tool() needs a Stop hook that:

1. At UserPromptSubmit: detects "fetch/search/read/check [resource]" directives and stores them as pending obligations
2. At Stop: verifies tool evidence exists (Read/Glob/Grep against the referenced resource)

This is architecturally similar to your existing declaration_reminder system but reversed: user-issued obligations
instead of LLM-declared obligations.

---
Fix Recommendation

A new two-component hook: User Directive Obligation Tracker

Component 1 (UserPromptSubmit): Detect explicit user directives like:

- "search the [chat|transcript|history]"
- "find it in [location]"
- "read [file/path]", "check [file]"

Store as pending_obligation_{terminal_id}.json with the required tool and resource.

Component 2 (Stop): Check if a pending obligation exists. Verify tool evidence (Read/Glob/Grep/Bash against the
resource). Block if no matching tool call found in this turn.

This mirrors exactly how declaration_reminder + arch_first_enforcer work, just triggered by user directives rather than
LLM declarations.

---
Action Graph

┌──────┬────────────────────────────┬───────────────────┬─────────────────────────────────────────────┬─────────────┐
│ Step │           Action           │     Expected      │                   Actual                    │ Divergence? │
├──────┼────────────────────────────┼───────────────────┼─────────────────────────────────────────────┼─────────────┤
│ 1    │ Read settings.json hooks   │ See what runs     │ Found 12 active hooks, no directive tracker │ No          │
├──────┼────────────────────────────┼───────────────────┼─────────────────────────────────────────────┼─────────────┤
│      │ Check UserPromptSubmit     │ See all           │ investigate_before_explain NOT in           │             │
│ 2    │ registry                   │ registered        │ core_hook_modules                           │ No          │
│      │                            │ modules           │                                             │             │
├──────┼────────────────────────────┼───────────────────┼─────────────────────────────────────────────┼─────────────┤
│ 3    │ Check archived hooks       │ Find if relevant  │ investigate_before_explain.py archived but  │ No          │
│      │                            │ hook exists       │ only covers skill questions                 │             │
├──────┼────────────────────────────┼───────────────────┼─────────────────────────────────────────────┼─────────────┤
│ 4    │ Check Stop hooks           │ See if omission   │ Only fabrication detection, not omission    │ No          │
│      │                            │ detection exists  │                                             │             │
├──────┼────────────────────────────┼───────────────────┼─────────────────────────────────────────────┼─────────────┤
│      │ Compare to                 │ Understand        │ Similar mechanism but LLM-declared only,    │             │
│ 5    │ declaration_reminder       │ closest analog    │ not user-directed                           │ No          │
│      │ system                     │                   │                                             │             │
└──────┴────────────────────────────┴───────────────────┴─────────────────────────────────────────────┴─────────────┘

---
Summary: The hooks worked as designed — they simply weren't designed for this failure mode. The specific pattern (user
gives explicit "go find X" directive → LLM ignores it silently) has no enforcement hook. The investigate_before_explain
hook that came closest is archived and was narrower in scope anyway.

✻ Baked for 3m 35s

❯ Unknown skill: search-research

● Args from unknown skill: is there a best practice for this sort of problem?

❯ /research is there a best practice for this sort of problem?

● Bash(cd "P:/" \&\& python -m search_research.cli "LLM explicit instruction following enforcement hooks AI agents" --mode
auto 2>/dev/null | head -5 || echo "CLI not av…)
⎿  Query: LLM explicit instruction following enforcement hooks AI agents
Mode: auto
Sources: zai-web-search
Processing time: 18.12s

● Bash(cd "P:/" \&\& python -m search_research.cli "LLM explicit instruction following enforcement hooks AI agents" --mode
auto 2>/dev/null)
⎿  Query: LLM explicit instruction following enforcement hooks AI agents
Mode: auto
Sources: zai-web-search
… +33 lines (ctrl+o to expand)
⎿  (timeout 45s)

● Bash(cd "P:/" \&\& python -m search_research.cli "AI agent task completion verification stop hook obligation tracking"
--mode tavily 2>/dev/null)
⎿  Query: AI agent task completion verification stop hook obligation tracking
Mode: tavily
Sources: tavily
… +25 lines (ctrl+o to expand)
⎿  (timeout 45s)

● Bash(cd "P:/" \&\& python -m search_research.cli "Claude Code Stop hook verify user intent compliance enforcement pattern"
--mode exa 2>/dev/null)
⎿  Query: Claude Code Stop hook verify user intent compliance enforcement pattern
Mode: exa
Sources: exa
… +63 lines (ctrl+o to expand)
⎿  (timeout 45s)

● Bash(cd "P:/" \&\& python -m search_research.cli "LLM instruction omission silent failure detection guardrail" --mode
tavily 2>/dev/null)
⎿  Query: LLM instruction omission silent failure detection guardrail
Mode: tavily
Sources: tavily
… +23 lines (ctrl+o to expand)
⎿  (timeout 45s)

● Bash(cd "P:/" \&\& python -m search_research.cli "agentic AI obligation tracking checklist verification pattern user
directive enforcement" --mode exa 2>/dev/null)
⎿  Query: agentic AI obligation tracking checklist verification pattern user directive enforcement
Mode: exa
Sources: exa
… +54 lines (ctrl+o to expand)
⎿  (timeout 45s)

● Bash(cd "P:/" \&\& python -m search_research.cli "agentic-patterns.com stop hook auto-continue" --mode webreader
--fetch-urls 2 2>/dev/null | head -100)
⎿  (No output)

● Bash(cd "P:/" \&\& python -m search_research.cli "Guardrails AI NeMo instruction following verification loop" --mode tavily
2>/dev/null)
⎿  Query: Guardrails AI NeMo instruction following verification loop
Mode: tavily
Sources: tavily
… +23 lines (ctrl+o to expand)
⎿  (timeout 30s)

● Good. I have enough signal from research. Here's the synthesis:

---
Research Findings: Best Practices for This Problem

The Problem Class

This is called "instruction omission" or "silent task elision" in the agentic AI literature — distinct from fabrication
(claiming to do something you didn't) and hallucination (stating false facts). The LLM silently skips a required action
without claiming to have done it or explaining why.

What the Research Says

1. Stop Hook Auto-Continue Pattern (most directly applicable)
The agentic-patterns community has documented this exact use case. The canonical pattern:

▎ "You can define a stop hook that says: if the tests don't pass, don't let the agent stop." — Shannon Lal (Anthropic,
cited in agentic-patterns.com)

Applied to your problem: "if the user said 'search X' and no Read/Bash/Glob tool ran against X, don't let Claude stop."
This is exactly how your existing declaration_reminder + arch_first_enforcer works — just for LLM-declared obligations,
not user-directed ones.

2. Industry terminology: "Closing the verification loop" (Datadog, 2026)
The pattern they document: Observability-driven harnesses — intercept agent completion events and verify required actions
were taken. Their architecture is:
3. Intent capture at prompt submission
4. Action tracking via tool events
5. Completion gate that verifies intent → action satisfaction before allowing the agent to stop

This is a 3-layer architecture identical to what your declaration_reminder system does, applied upstream to user
directives.

3. Guardrails AI / NeMo approach
These frameworks treat instruction-following as an output rail: validate that specific content/actions appear in the
response before releasing it. For Claude Code hooks, the equivalent is the Stop hook layer — validate tool usage before
allowing the turn to complete.
4. The "Pre/Post Hook" pattern (from Medium/claudefa.st)
The standard Claude Code pattern documented in multiple community posts:

- UserPromptSubmit: Extract intent / store obligation
- Stop hook: Verify obligation was satisfied, block with corrective message if not

Your existing arch_first_enforcer is a variation — but it's a PreToolUse (not Stop) variant that blocks BEFORE the wrong
action. The choice between "block before wrong action" vs "block at stop if required action missing" depends on how well
you can detect the obligation type in advance.

The Key Insight: Two Subcategories of This Problem

┌─────────────────────────┬───────────────────────────┬────────────────────────────────────────────────────────────┐
│       Subcategory       │      Detection Point      │                          Example                           │
├─────────────────────────┼───────────────────────────┼────────────────────────────────────────────────────────────┤
│ Wrong action taken      │ PreToolUse (block before) │ "Search transcript" → LLM opens a file instead             │
├─────────────────────────┼───────────────────────────┼────────────────────────────────────────────────────────────┤
│ Required action omitted │ Stop (block after)        │ "Search transcript" → LLM generates prose with no tool use │
└─────────────────────────┴───────────────────────────┴────────────────────────────────────────────────────────────┘

Your system already catches the first (arch_first_enforcer). What failed here was the second — omission detection at the
Stop gate.

Recommended Pattern (Industry Consensus)

The Stop hook is the right place. The pattern:

# UserPromptSubmit: Detect directive, store obligation

patterns = [
r"(?:find|search|check|read|look).*(?:chat.history|transcript|jsonl)",
r"(?:find|search).*in.*(?:history|previous|prior|earlier)",
]
if matches(prompt, patterns):
store_obligation(terminal_id, resource=extracted_resource, tool_type="Read|Bash|Glob")

# Stop hook: Verify

if pending_obligation := load_obligation(terminal_id):
tool_events = load_tool_events(session_id, terminal_id)
if not any(matches_obligation(e, pending_obligation) for e in tool_events):
block("You were asked to search [resource] but no search tool was used.")

This is the same pattern already implemented in your ecosystem for arch declarations and skill enforcement. The gap is
that user-issued fetch directives are not covered.

One Caveat from Research

The Reddit thread on "stop hook triggering too often" highlights the main risk: false positives. Pattern-matching on
"find it" or "check" can be too broad. The recommendation: narrow the patterns to high-confidence directives with a
specific resource reference (e.g., "find in transcript", "search the chat history", "check the JSONL") rather than any
use of "find" or "check".
"

The **optimal solution** is the pattern you’ve already sketched—**a Stop‑hook–driven “User‑Directive Obligation Tracker”** that mirrors your existing `declaration_reminder` + `arch_first_enforcer` system, but targets *user‑issued* “fetch / search / read” directives instead of LLM‑declared obligations.[^1_1][^1_2][^1_3][^1_4]

Below is a tightened, “best‑practices‑aligned” version of that design.

***

### 1. Core insight: treat user directives as obligations

Research into instruction‑omission and “silent task elision” confirms that:

- LLMs systematically fail to follow *explicit* directives when verification is not baked into the harness.[^1_5][^1_1]
- The most robust fixes are **structural**: hooks that enforce “intent → action → verification” at the platform level, not just prompt engineering.[^1_2][^1_6][^1_4]

Your existing architecture already does this for:

- LLM‑declared obligations (`declaration_reminder` → `arch_first_enforcer`).[^1_2]
- Task‑completion checks (`stop_hook`–based quality gates).[^1_3][^1_7]

Extending this to **user‑directed fetch/search instructions** is the natural, minimal‑delta fix.

***

### 2. Optimal architecture

Two tightly coupled pieces:

#### A. `UserPromptSubmit` obligation extractor

At prompt submission, run a lightweight regex / rule engine and stash pending obligations:

```python
patterns = [
    r"(?:find|search|check|read|look|parse|extract|get|inspect|review).*?(?:chat\.history|transcript|jsonl|log|dump|output)",
    r"(?:in|from|within|on|at|off|inside|inside of|the|this).*?(?:chat|history|transcript|previous|earlier|earlier message|earlier turn|history excerpt|jsonl)",
    r"(?:find|search|check|look|parse|extract|get|inspect|review).*?(?:file|path|directory|folder|git|repo|codebase|directory listing)",  # e.g., user‑named resources
]
```

- If a match includes a concrete resource (e.g., “chat history”, “JSONL”, a file path), store:

```json
{
  "session_id": "...",
  "terminal_id": "...",
  "turn": N,
  "directive": "search transcript",
  "required_resource": "chat history / transcript / jsonl",
  "required_tool_types": ["Read", "Glob", "Bash(grep)", "Logcat"],
  "created_at": <timestamp>
}
```

- If the match is ambiguous (e.g., “check it” with no referent), *do not* create an obligation. This avoids over‑blocking.[^1_8][^1_4]

This is the “intent capture” layer documented in industry observability‑driven agent harnesses: record what the user *said* they wanted done.[^1_6][^1_1]

#### B. Stop‑hook obligation verifier

At `Stop` (or `TaskCompleted` / `TeammateIdle` if you want to gate those too), correlate:

1. Load all pending obligations for `session_id` / `terminal_id` for this turn.[^1_7][^1_3]
2. Load tool events for the turn (Read, Bash, Glob, etc.).[^1_4][^1_3]
3. For each obligation, check:
```python
any(
    t["tool_type"] in obligation["required_tool_types"]
    and matches_resource(t, obligation["required_resource"])
    for t in tool_events
)
```

If **no** matching tool event exists:

```json
{"decision": "block", "reason": "User asked to search [resource] but no search tool was used. Please Read/Glob/Bash the relevant resource before responding."}
```

If at least one relevant tool event exists, allow the turn to stop.

This is the canonical **“stop‑hook auto‑continue pattern”** used elsewhere in agentic‑pattern ecosystems: “if the tests (obligations) don’t pass, don’t let the agent stop.”[^1_3][^1_4]

***

### 3. Why this is optimal

- **Minimal new mechanisms**: You reuse:
    - `UserPromptSubmit` for intent capture,
    - `Stop` for enforcement,
    - Existing tool‑event parsing and logging infrastructure.[^1_7][^1_2]
- **Strong alignment with best practice**:
    - It implements a “verification loop” explicitly tied to user intent.[^1_1][^1_6]
    - It targets *omission* (no tool event) rather than *fabrication* (wrong claim), which your current cross‑validator already covers.[^1_9][^1_2]
- **False‑positive control**:
    - Narrow, high‑confidence patterns (with explicit resource mention) reduce over‑blocking.[^1_8][^1_4]
    - You can tune thresholds (e.g., “require at least one Read/Glob/Bash over a path that matches the resource regex”) post‑deployment.

***

### 4. Implementation‑level tweaks worth baking in

- **Per‑session obligation lifetime**
    - Expire obligations after a few turns or if the conversation visibly moves on to unrelated topics. This avoids creeping obligations.[^1_10][^1_9]
- **Structured logging**
    - Log obligation creation / satisfaction / blocking decisions in a dedicated file (e.g., `.claude/obligations.log`) so you can retro‑trace where the pattern fails.[^1_1][^1_3]
- **Meta‑hook self‑repair**
    - When the hook blocks, offer a structured “next step” skill (e.g., `/obligate_read transcript` or `/obligate_grep <pattern>`) so the user can re‑express the directive in a way the pattern will catch.[^1_6][^1_2]

***

### 5. Things that are *not* optimal here

- **Re‑relying on “ask the model to self‑detect omission” in‑context**
    - Instruction‑omission literature shows this is unreliable at scale; LLMs easily miss their own omissions.[^1_5][^1_1]
- **Burying checks inside MCP tools**
    - MCP tools are great for runtime discovery, but they are not the right place for *cross‑turn compliance verification*; that belongs in the harness / hook layer.[^1_2][^1_6]

***

If you want, the next step can be a concrete code sketch (e.g., `obligation_tracker_user_directive.py` for `UserPromptSubmit` and `stop_hook_obligation_verifier.py`) with your existing hook layout so you can drop‑in‑compatible snippets.

Do you want me to ground this against your current `declaration_reminder` / `arch_first_enforcer` code paths (e.g., naming, file loc, and diff‑style patch)?

- Yes, fit into existing declaration_reminder style
- Yes, but keep it abstract and generic
- No, just keep this high‑level
<span style="display:none">[^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://arxiv.org/html/2601.03269v1

[^1_2]: https://www.reddit.com/r/ClaudeCode/comments/1orz5as/stop_teaching_your_ai_agents_make_them_unable_to/

[^1_3]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^1_4]: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/stop-hook-auto-continue-pattern.md

[^1_5]: https://arxiv.org/html/2502.04362v1

[^1_6]: https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

[^1_7]: https://code.claude.com/docs/en/hooks

[^1_8]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^1_9]: https://papers.ssrn.com/sol3/Delivery.cfm/5729082.pdf?abstractid=5729082\&mirid=1

[^1_10]: https://www.europarl.europa.eu/RegData/etudes/IDAN/2024/754450/EXPO_IDA(2024)754450_EN.pdf

[^1_11]: https://www.facebook.com/groups/aisaas/posts/3489582294694494/

[^1_12]: https://news.ycombinator.com/item?id=47340079

[^1_13]: https://commons.allard.ubc.ca/cgi/viewcontent.cgi?article=1372\&context=ubclawreview

[^1_14]: https://www.facebook.com/groups/703007927897194/posts/860471698817482/

[^1_15]: https://github.com/anthropics/claude-code/issues/10732


---

# Are there popular repos that already cover this for claude code/

No, there are **no widely known, popular public repos** that ship a *Claude‑Code‑specific* “user‑directive obligation tracker” (i.e., “user said ‘search X’, LLM must actually call Read/Glob/Bash on X”) out of the box.[^2_1][^2_2][^2_3]

However, there are several **relevant, hook‑heavy repos** you can crib from:

### 1. Closest “pattern‑adjacent” repos

- **`decider/claude-hooks`**
General-purpose hook library for Claude Code that already leans heavily on `Stop`, `PreToolUse`, and `PostToolUse` for validation, notifications, and quality gates.[^2_1]
    - You can mirror its structure (universal dispatcher, hook registration, per‑event handlers) and add your own `UserDirectiveObligationTracker` module.[^2_4][^2_1]
- **Code‑review / design‑audit / task‑completion stop hooks**
Several stop‑hook examples (e.g., “block if tests don’t pass”, “block if task marker file missing”) are published as standalone hooks; they all wire into `Stop` in the same way you’d wire obligation‑verification.[^2_5][^2_6][^2_4]


### 2. What’s missing in existing repos

- **Explicit user‑directive enforcement**
    - The broader ecosystem focuses on:
        - Test‑gate / build‑gate stop hooks,
        - Code‑quality / lint / style enforcement,
        - Package‑age checks,
        - Notifications,
but not “user said ‘search transcript’, verify a Read/Glob tool was used.”[^2_2][^2_4][^2_1]
    - Anthropic’s own issue tracker even has threads about “repeatedly ignoring explicit user instructions,” which is exactly your failure mode, but the discussion is bug‑/feature‑focused, not a reusable hook repo.[^2_3][^2_2]


### 3. Practical recommendation

Given that, the **optimal path** is:

- **Fork / vendor a solid hook scaffold** (e.g., `decider/claude-hooks`) to reuse infra (event dispatch, logging, config).[^2_7][^2_1]
- **Add your own `UserDirectiveObligationTracker`** as a new hook bundle:
    - `UserPromptSubmit` obligation extractor (regex + storage),
    - `Stop` obligation verifier (tool‑event correlation).[^2_8][^2_9][^2_5]

If you want, I can draft a *concrete repo‑style layout* (directory structure, entry‑point names, and minimal `settings.json` wiring) that would slot into something like `decider/claude-hooks` while remaining Claude‑Code‑generic.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_21][^2_22]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/decider/claude-hooks

[^2_2]: https://github.com/anthropics/claude-code/issues/28868

[^2_3]: https://github.com/anthropics/claude-code/issues/32163

[^2_4]: https://smartscope.blog/en/generative-ai/claude/claude-code-hooks-guide/

[^2_5]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^2_6]: https://www.reddit.com/r/ClaudeCode/comments/1qapiw2/a_smart_and_automated_code_review_stop_hook/

[^2_7]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^2_8]: https://code.claude.com/docs/en/hooks-guide

[^2_9]: https://www.eesel.ai/blog/hooks-reference-claude-code

[^2_10]: https://code.claude.com/docs/en/hooks

[^2_11]: https://www.reddit.com/r/ClaudeCode/comments/1qlzzzf/claude_codes_most_underrated_feature_hooks_wrote/

[^2_12]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^2_13]: https://www.dotzlaw.com/insights/claude-hooks/

[^2_14]: https://github.com/anthropics/claude-code/issues/10732

[^2_15]: https://www.linkedin.com/posts/nickciubotariu_ai-claude-code-activity-7371607369665097729-JAk5

[^2_16]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^2_17]: https://github.com/anthropics/claude-code/issues/19659

[^2_18]: https://github.com/disler/claude-code-hooks-mastery

[^2_19]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^2_20]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^2_21]: https://www.linkedin.com/posts/fallonjensen_i-hate-telling-claude-code-to-stop-making-activity-7432905002014117888-b80_

[^2_22]: https://tldrsec.com/p/tldr-sec-316


---

# I'm wondering if there are ideas from those repos that would be useful to us, I'm not interested in replacing everything we have done.

Yes—there are several concrete **ideas and patterns** from popular Claude‑Code‑hooks repos that would integrate cleanly into your existing system without replacing anything.[^3_1][^3_2][^3_3]

Here are the most useful ones:

***

### 1. Dispatcher‑style hook router (from `decider/claude-hooks`)

- They use a **central dispatcher** (e.g., `universal-submit.py`, `universal-pretooluse.py`, `universal-stop.py`) that reads matching hooks from config and runs appropriate handlers.[^3_1]
- You can adopt the same shape for your new `UserDirectiveObligationTracker`:
    - `UserPromptSubmit` → `universal-submit.py` stashes `pending_obligation_{terminal_id}.json` for your directive detector.[^3_4][^3_1]
    - `Stop` → `universal-stop.py` runs obligation‑verification as one of several checks, alongside your existing cross‑validators and arch‑enforcers.[^3_2][^3_1]

**Why it’s useful for you:**

- Keeps your existing hooks intact; just appends a new responsibility‑track‑style check.[^3_2][^3_1]

***

### 2. Hierarchical config / per‑dir behavior

- `decider/claude-hooks` uses layered configs (root `.claude/hooks.json`, directory‑specific overrides) so different parts of a monorepo can tune package‑age windows, linting rules, etc.[^3_1]
- You can reuse this pattern to:
    - Enable / disable user‑directive enforcement per project or directory (e.g., stricter on infra‑ops repos).[^3_5][^3_1]
    - Parameterize patterns (e.g., “strict” vs “loose” resource regex) without touching the core obligation‑tracker code.[^3_6][^3_2]

***

### 3. “PreToolUse is for blocking, Stop is for final checks” discipline

- Docs and write‑ups consistently强调:
    - `PreToolUse` is the only place that can block tools; ideal for security / wrong‑action gates.[^3_7][^3_2]
    - `Stop` is the final quality‑gate layer (e.g., “did we pass tests / did we touch the right files?”).[^3_4][^3_2]

**How you can use this:**

- Keep your current `arch_first_enforcer`‑style pre‑blockers in `PreToolUse`.[^3_2][^3_1]
- Put obligation‑verification for *omission* in `Stop`:
    - “User said ‘search X’ → did any Read/Glob/Bash hit X in this turn?”
This cleanly separates:
    - **Wrong‑action** prevention (`PreToolUse`),
    - **Missed‑action** detection (`Stop`),
which is exactly the dichotomy you already identified.[^3_8][^3_2]

***

### 4. Structured logging + “hook introspection”

- Several repos (including `decider/claude-hooks`) emit structured JSON logs for each hook run and provide a way to introspect “which hooks fired for this file/event.”[^3_9][^3_1]
- You can piggyback on this:
    - Log every obligation creation / satisfaction / blocking decision in a dedicated stream (e.g., `.claude/obligations.log`), so you can later:
        - Understand why a directive was skipped,
        - Retrain your regex patterns,
        - Detect false positives.[^3_8][^3_1]

***

### 5. Light‑weight pattern libraries and environment variables

- Community repos use environment variables (e.g., `MAX_AGE_DAYS`, `CLAUDE_HOOKS_TEST_MODE`) to tune behavior without touching code.[^3_1][^3_2]
- You can similarly:
    - Add `USER_DIRECTIVE_OBLIGATION_MODE=strict|loose|disabled`.
    - Add `OBLIGATION_TIMEOUT_TURNS=3` so obligations don’t leak forever.[^3_10][^3_1]

***

### 6. Prompt‑style hooks for semantic judgment (optional)

- Some guides show using `type: "prompt"` hooks for decisions that need semantic understanding (e.g., “is this a user‑directive worth enforcing?”).[^3_5][^3_4]
- That’s not mandatory for your case, but you could later:
    - Use a small prompt‑hook in `UserPromptSubmit` to do a soft‑check:
        - “Was this user instruction clearly a ‘go fetch X’ directive?”
        - Helps refine your regex patterns without hard‑blocking.[^3_4][^3_5]

***

### 7. “Don’t block gratuitously” philosophy

- Multiple write‑ups and issue threads warn about hooks that trigger too often or block harmless behavior.[^3_11][^3_2]
- Your existing plan of:
    - Only obligating when a directive names a concrete resource (e.g., “chat history”, “transcript”, a file path),
    - Being permissive otherwise,
is exactly in line with their advice.[^3_12][^3_11]

***

### Shape this would take in *your* stack

If you want to stay minimal, you only need to absorb:

- **Architecture**: dispatcher + JSON‑based storage for obligations, next to your existing hooks.[^3_2][^3_1]
- **Lifecycle discipline**: `UserPromptSubmit` → `Stop`, with `PreToolUse` reserved for wrong‑action blocking.[^3_7][^3_2]
- **Config pattern**: layered config and env vars so you can tune obligation‑tracker strictness per repo.[^3_5][^3_1]

If you’d like, the next step can be:

- A minimal diff sketch of your current registry + one new `UserDirectiveObligationTracker` module that plugs into that dispatcher pattern.
<span style="display:none">[^3_13][^3_14][^3_15][^3_16][^3_17][^3_18][^3_19]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/decider/claude-hooks

[^3_2]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^3_3]: https://github.com/disler/claude-code-hooks-mastery

[^3_4]: https://code.claude.com/docs/en/hooks-guide

[^3_5]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^3_6]: https://www.datacamp.com/tutorial/claude-code-hooks

[^3_7]: https://code.claude.com/docs/en/hooks

[^3_8]: https://arxiv.org/html/2601.03269v1

[^3_9]: https://blog.promptlayer.com/understanding-claude-code-hooks-documentation/

[^3_10]: https://tldrsec.com/p/tldr-sec-316

[^3_11]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^3_12]: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/stop-hook-auto-continue-pattern.md

[^3_13]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^3_14]: https://mcpmarket.com/tools/skills/react-hooks-best-practices

[^3_15]: https://github.com/anthropics/claude-code/issues/24327

[^3_16]: https://www.youtube.com/watch?v=09dggS8KwBc

[^3_17]: https://github.com/anthropics/claude-code/issues/6305

[^3_18]: https://www.youtube.com/watch?v=J5B9UGTuNoM

[^3_19]: https://www.youtube.com/watch?v=8T0kFSseB58


---

# How to set up TDD enforcement hooks without full rewrite

You can bolt on **TDD‑enforcement hooks** without rewriting your existing hook stack by treating TDD enforcement as a thin “test‑gate” layer running on top of what you already have.[^4_1][^4_2][^4_3]

Here’s how to set it up in place, step‑by‑step:

***

### 1. What “TDD enforcement” actually means for hooks

For Claude Code, TDD enforcement usually collapses into a few concrete checks:

- **Red‑phase**: Before implementation, a relevant test should exist and fail.[^4_2][^4_4]
- **Green‑phase**: Before marking “done”, tests must pass.[^4_3][^4_5]
- **Optional**: No implementation‑only file changes without a test file touched.[^4_6][^4_2]

You do **not** need to reconstruct your whole architecture; you just add one or two new hooks that emit `{ "decision": "block" }` when these are violated.[^4_7][^4_3]

***

### 2. Use `Stop` for TDD‑gate (minimal‑impact)

Re‑use the pattern from the “force task completion” STOP‑hook:

- On every stop, run tests and inspect the result.[^4_8][^4_3]

A minimal example:

```bash
# in ~/.claude/stop_hook_tdd.sh
# (or project‑local .claude/stop_hook_tdd.sh)

#!/usr/bin/env bash

# If we’re already in a forced‑continuation loop,
# interventions like this are about to happen.
# Decide if you want to skip extra checks here.
# (You can mirror your existing stop‑hook logic.)
if [ "$stop_hook_active" = "true" ]; then
  echo "{\"decision\": \"allow\", \"reason\": \"already in stop_hook_active\"}"
  exit 0
fi

# Run your test suite (or the relevant subset for this turn)
cd "$project_root" || exit 1
make test  # or pytest, rspec, etc.

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "{\"decision\": \"allow\", \"reason\": \"tests pass\"}"
else
  echo "{\"decision\": \"block\", \"reason\": \"TDD‑gate: tests did not pass before stopping. Please fix failures or add failing tests first.\"}"
fi
```

- Drop this into your existing `Stop` hook chain (next to your current task‑completion / lint / build hooks).[^4_9][^4_3]
- It **does not** displace your existing hooks; it just adds one more “must‑pass” criterion.[^4_3][^4_8]

***

### 3. Use `PreToolUse` to catch “implementation first” patterns

If you want stricter red‑phase enforcement (i.e., “don’t implement until there’s a test”), slot a TDD‑gate into `PreToolUse`:

```bash
# ~/.claude/pretooluse_tdd_guard.sh

#!/usr/bin/env bash

# If this is a test‑writing operation, let it through
if echo "$tool_type" | grep -qE "^(Read|Write|MultiEdit)$" && \
   echo "$args" | grep -qE "test|spec|Test|Spec"; then
  echo "{\"decision\": \"allow\"}"
  exit 0
fi

# If this is an implementation‑only file change,
# verify that a test file was touched in this session
if echo "$tool_type" | grep -qE "^(Write|MultiEdit)$" &&
   echo "$args" | grep -qE "src|lib|app"; then
  # Check whether any test file was written in this session
  # (you can reuse the same history / log file your existing hooks use)
  if cat "$session_dir/tdd_events.log" | grep -qE "test|spec|Test|Spec"; then
    echo "{\"decision\": \"allow\"}"
  else
    echo "{\"decision\": \"block\", \"reason\": \"TDD‑gate: implementation file change without a corresponding test file in this session. Add failing tests first.\"}"
  fi
fi
```

This is the kind of logic used in `tdd‑guard`‑style setups, but you can share its event‑log with your existing hooks instead of duplicating plumbing.[^4_10][^4_1][^4_2]

***

### 4. Compose cleanly with your existing stack

You **do not** need to replace anything if you:

- **Add new hooks**, not replace existing ones:
    - `PreToolUse`: `pretooluse_tdd_guard.sh`
    - `Stop`: `stop_hook_tdd.sh`
- **Share a common log / registry** (e.g., `tdd_events.log`, `obligations.json`) that both your TDD‑gate and your existing user‑directive / obligation‑tracker hooks can read.[^4_1][^4_2]

This is exactly how popular TDD‑hook projects like `tdd‑guard` are structured: they layer on top of `PreToolUse` / `Stop` and do not rewrite core Claude Code behavior.[^4_10][^4_1]

***

### 5. Optional: make TDD‑enforcement optional per repo

To avoid breaking workflows where TDD is not desired:

- Use environment‑style flags similar to existing hook projects:

```bash
# ~/.claude/stop_hook_tdd.sh
if [ "${TDD_GATE_ENABLE:-false}" != "true" ]; then
  echo "{\"decision\": \"allow\", \"reason\": \"TDD‑gate disabled\"}"
  exit 0
fi
```

- Or layer config per‑project (like `decider/claude‑hooks` does), so only certain repos are TDD‑enforced.[^4_11][^4_8]

***

If you tell me roughly how your current `Stop` / `PreToolUse` plumbing is wired (e.g., dispatcher names, log locations), I can sketch a **concrete diff‑style patch** that adds TDD‑gate hooks into your existing files without touching your existing logic.
<span style="display:none">[^4_12][^4_13][^4_14][^4_15][^4_16]</span>

<div align="center">⁂</div>

[^4_1]: https://www.reddit.com/r/ClaudeAI/comments/1mbhmwp/building_a_tdd_enforcement_hook_for_claude_code/

[^4_2]: https://nizar.se/tdd-guard-for-claude-code/

[^4_3]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^4_4]: https://stevekinney.com/courses/ai-development/test-driven-development-with-claude

[^4_5]: https://news.ycombinator.com/item?id=44839023

[^4_6]: https://www.reddit.com/r/Anthropic/comments/1mza0go/is_there_a_way_to_stop_claude_from_hacking_tests/

[^4_7]: https://code.claude.com/docs/en/hooks

[^4_8]: https://www.datacamp.com/tutorial/claude-code-hooks

[^4_9]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^4_10]: https://www.claudelog.com/claude-code-mcps/tdd-guard/

[^4_11]: https://github.com/decider/claude-hooks

[^4_12]: https://github.com/nizos/tdd-guard

[^4_13]: https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/

[^4_14]: https://mcpmarket.com/tools/skills/test-driven-development-workflow

[^4_15]: https://www.youtube.com/watch?v=CEODfvJLIGQ

[^4_16]: https://mcpmarket.com/tools/skills/tdd-enforcement-agent

