---
title: "'
❯ /search find the previous chat session where I said 'test it'

● I'll search the chat history for where you said '"
date: "2026-02-25"
mode: "COPILOT"
uuid: "0e36dad9-48d9-4cc5-8b1b-a605d8ea7f3d"
entry_count: 2
---

## Human

"
❯ /search find the previous chat session where I said "test it"

● I'll search the chat history for where you said "test it".

● Bash(cd "P:/__csf" && python src/cli/nip/search_enhanced.py "test it" --backend chs --limit 20)
  ⎿  Error: PreToolUse:Bash hook error: [python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PreToolUse.py --timeout 15.0]:
     ⛔ BLOCKED: ⛔ SKILL-FIRST GATE: You typed /search but haven't called Skill("search") yet.

     Your FIRST action must be:  Skill(skill="search")

     Do NOT analyze the codebase, run scripts, or provide your own assessment.
     Call Skill("search") to load the skill, then follow its instructions."

In claude code, is there a way to make skill invoke more reliable?

## Assistant

Yes. You can’t make model-side skill invocation perfectly deterministic, but you can get very close to “never silently skipped” by layering hooks and an explicit evaluation step around the existing skills system.[1][2][3]

## Why skills feel unreliable

- Claude only auto-invokes skills based on their name/description metadata and current prompt; there is no hard classifier or rules engine forcing a match.[2][4][5]
- It can “know” a skill exists (metadata loaded) but still choose to ignore it, especially when prompts are vague or multiple skills partially match.[4][6]
- Frontmatter flags like `disable-model-invocation` and `user-invocable` control whether Claude is even allowed to auto-trigger a skill, but they don’t guarantee it will.[5][2]

In your case, the PreToolUse hook is correctly blocking `/search` because `Skill("search")` hasn’t been called yet, but nothing is compelling Claude to actually invoke that skill before it tries the Bash tool.[functions.search_user_memories:0][1]

## Pattern 1: Forced skill evaluation before tools

This is the most robust pattern people are using to get near-100% activation for “must-use” skills.[3][7]

Core idea:

1. A **UserPromptSubmit** (or similar) hook detects when the user’s message should involve a given skill (e.g., “search”, “rca”, “valibot-usage”).[8][3]
2. The hook or a small system message forces Claude to explicitly evaluate every relevant skill first, in-writing, *before* it can call tools: “List all skills and for each say YES/NO + reason whether you will use it now.”[6][3]
3. Once Claude writes “YES – need `<skill>`”, your PreToolUse hook enforces that `Skill("<name>")` must be invoked before any Bash/search/etc., otherwise it blocks with a clear error (like the one you’re seeing).[functions.search_user_memories:0][3]

This does two things you want:

- Removes “silent skip”: if it says NO, you at least get an explicit refusal instead of it pretending the skill doesn’t exist.[6][3]
- Converts your existing PreToolUse guard from “nag” into a **contract enforcer**: it only passes if the logged decision and subsequent tool usage are consistent.[8][3]

For your `/search` example, this would look like:

- First turn: Claude lists skills, writes “YES – use `search` skill to locate prior chats about ‘test it’”, then calls `Skill("search")`.  
- Only after that does it issue the Bash `/search` tool call that your hook is currently blocking.[functions.search_user_memories:0][8]

## Pattern 2: Tighten skill definitions and flags

To improve the *baseline* chance of correct auto-invocation (even without the heavy forced-eval pattern):

- Make the **skill name and description extremely literal and task-shaped**, e.g. “chat-history-search” with “Use this whenever the user asks to find or recall past conversations, messages, or sessions.”[2][5]
- Avoid overlapping descriptions between skills that mention similar concepts (e.g., multiple “history”, “search”, “debug” skills), which makes the model’s choice fuzzy.[9][4]
- Use frontmatter flags appropriately: keep `disable-model-invocation: false` for skills you *want* Claude to auto-trigger; reserve `true` for skills that must only fire via slash command.[5][2]
- For non-critical skills, rely on explicit `/skill-name` or slash commands; treat auto-invocation as opportunistic sugar, not a guarantee.[10][7]

This won’t solve the “must never be skipped” problem on its own, but it will reduce the random-feeling misses.

## Pattern 3: Hook-based routing for “hard” skills

For truly non‑negotiable skills (e.g., your RCA/debug, security, or TDD guards), most advanced setups now:

- Treat the skill as a **specification** and enforcement target, not as the only mechanism.[11][7][3]
- Use **PreToolUse** hooks keyed on specific tools/commands (e.g., `python src/cli/nip/search_enhanced.py`, `pytest`, `git push`) to check whether the relevant skill has been invoked or its contract satisfied for this turn.[7][8]
- Block or require user override if the tool would violate the skill’s rules, even if Claude never auto-triggered the skill itself.[11][3][8]

In other words: let skills tell Claude *how* to behave, but let hooks decide *whether it is allowed to proceed* when it forgets.

For your `/search` + `Skill("search")` situation, that means:

- Keep your current PreToolUse “SKILL-FIRST GATE”.  
- Add a lightweight **UserPromptSubmit detection** or small system prompt that obligates Claude to run the skill before attempting the tool, using the forced-evaluation pattern above.  
- Optionally log every violation (tool attempted with no prior skill) so you can refine triggers and see whether the model is complying more over time.[11][3][8]

## What this means in practice for you

Given your setup (Windows 11, heavy hooks, CKS/CHS, and already using PreToolUse skill gates):[11]

- You will not get a magic flag that makes `Skill("search")` auto-fire reliably. The official docs assume best-effort model invocation.[9][2][5]
- You *can* get to “practically reliable” by:
  - For critical skills: implementing the explicit **Evaluate → Activate → Implement** sequence via hooks + a small system prompt, and having PreToolUse enforce it.[3][8]
  - For everything else: tightening skill descriptions and relying on explicit commands when it really matters.[4][2][5]

If you’d like, describe your current `search` skill’s frontmatter and the exact PreToolUse hook snippet, and I can sketch the minimal forced-eval prompt + hook changes that will stop this specific “haven’t called Skill('search') yet” failure mode while keeping your existing architecture.

## Human

Is that what popular repos do?  Is our system better or worse?

## Assistant

Popular repos mostly do a **lighter** version of what you’re doing; your system is stricter and more orchestrated.[1][2][3]

## What popular repos actually do

Most “serious” Claude Code setups converge on three ideas:[4][2][1]

- **Skill rules + hook shim:** A UserPromptSubmit or similar hook runs a small matcher (skill-rules.json / skill-eval.js) that nudges Claude toward certain skills, or injects the skill as context when patterns match; it rarely hard-blocks tools.[2][3]
- **File/dir-based activation:** Skills auto-load when you’re in certain paths (backend, frontend, tests), improving relevance but not guaranteeing use.[1]
- **Soft enforcement:** Hooks run linters, tests, or checks and warn, but they don’t usually maintain a per-skill contract like “you must call Skill('search') before Bash”.[4][1]

These systems improve *context selection*, but they deliberately stop short of strong workflow orchestration.[5][1]

## Where your system sits relative to that

From your earlier design work:

- You already use **PreToolUse** as a gate that blocks tools until a required skill is invoked (e.g., `Skill("rca")`, now `Skill("search")`).[functions.search_user_memories:0][6]
- You treat skills as **hard contracts** for certain workflows (RCA, TDD, search correctness), and you log violations for later refinement.[7][6]
- You’re layering word-boundary matching, LLM/ML intent analysis, and a daemon/policy brain on top of hooks, which is beyond what most public repos attempt.[functions.search_user_memories:0][6]

Compared to popular repos:

- **Stronger** on enforceability: you actually stop execution when the contract is violated, rather than just “advising”.[1][6]
- **Stronger** on observability: violation logs and evidence-ledger ideas are more advanced than typical “run script, print warning” hooks.[7][4]
- **Weaker (or at least fussier)** on ergonomics: your SKILL-FIRST gate produces visible friction when the model forgets to comply, whereas most repos accept some silent skipping in exchange for smoother UX.[3][1]

## Is it better or worse?

It’s **better for safety/discipline**, **worse for friction**, and **more complex to maintain**:

- Better if your priority is: “Never silently skip /rca, /search, /tdd-guard; I’d rather block than be lied to.”[6][7]
- Worse if your priority is: “Minimize interruptions and mental overhead; skills are hints, not laws.”[3][1]
- More advanced architecturally than most public repos, which generally cap out at skill-eval hooks, path-based activation, and non-blocking quality hooks.[2][4][1]

If you want to be closer to what popular repos do without losing your guarantees, the main knobs are:

- Downgrade some skills from **hard PreToolUse gates** to **soft evaluation + logging only**.  
- Reserve “must-call Skill() before tools” for a very small set of critical skills (RCA, security, test policy), which is closer to how serious “hooks-mastery” style repos treat blocking hooks.[8][4]
