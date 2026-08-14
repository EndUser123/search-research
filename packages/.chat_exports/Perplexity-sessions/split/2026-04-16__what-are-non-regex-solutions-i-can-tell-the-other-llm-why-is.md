---
title: "What are non-regex solutions I can tell the other LLM?

'Why is the LLM so dumb?
'
● That's the bug. Key 3 (YT_API_KEY_3"
date: "2026-04-16"
mode: "COPILOT"
uuid: "38ab2cbd-2b9b-4066-9878-d535808c337b"
entry_count: 2
---

## Human

What are non-regex solutions I can tell the other LLM?

"Why is the LLM so dumb?
"
● That's the bug. Key 3 (YT_API_KEY_3) is sitting unused in the pool while Keys 1, 2, and 4 are all getting hammered together. The pool
  iterates in order and only marks a key exhausted when that specific key gets a 403/429 — but if all 3 configured keys belong to the same
  Google Cloud project, they share the same project-level quota and exhaust together.

  Key 3 isn't being used at all — it's not set, so it's filtered out of the pool entirely at line 86.

  The fix is straightforward: set YT_API_KEY_3 in the environment (or point YOUTUBE_API_KEY_3 at it) so it joins the active pool. Then when the
   next backfill runs, it has 4 keys to rotate through instead of 3 — and if Key 3 belongs to a different Google Cloud project, it has its own
  independent quota bucket.

  Want me to check the current .env or environment to see what's configured for YT_API_KEY_3?

✻ Cogitated for 1m 14s

❯ yes

● Bash(python3 -c "
      import os…)
  ⎿  YT_API_KEY_3: [REDACTED]
     YT_API_KEY_1: AIzaSyBDzOLSFoV1PeRA6oH9w...
     YT_API_KEY_2: AIzaSyBx8EXghdfnsRj1yC9fV...
     … +3 lines (ctrl+o to expand)

● Wait — YT_API_KEY_3 is set in the environment, so it should be in the pool. But during backfill only keys 1, 2, and 4 were used. Let me trace
   through the backfill script to find where key 3 got skipped.

● Bash(python3 - <<'EOF'
      import os, sys…)
  ⎿  Pool size: 4
       [0] AIzaSyBDzOLSFoV1PeRA6oH9wCeivJ...
       [1] AIzaSyBx8EXghdfnsRj1yC9fVmCIwc...
     … +2 lines (ctrl+o to expand)

● All 4 keys ARE in the pool — Keys 1, 2, 3, and 4 are all configured. My earlier statement was wrong.

  So the real question is why Key 3 shows zero requests in Google Cloud Console despite being in the pool rotation. Let me test the actual API
  behavior directly:

● Bash(python3 - <<'EOF'
      import sys, os…)
  ⎿  Error: Exit code 1
     Traceback (most recent call last):
       File "<stdin>", line 3, in <module>
     ImportError: cannot import name '_api_request_with_fallback' from 'csf.source_enumerator' (P:\packages/yt-is\csf\source_enumerator.py)

  Searched for 1 pattern (ctrl+o to expand)

● Bash(python3 - <<'EOF'
      import sys, os…)
  ⎿  [0] SUCCESS → Simpler Trading
     [1] SUCCESS → Simpler Trading
     [2] HTTP 400: {
     … +5 lines (ctrl+o to expand)

● Key 3 (YT_API_KEY_3) is expired — HTTP 400 "API key expired." That's why it's not in the active pool: the code detects the 400 and skips to
  the next key.

  So the actual situation:

  ┌──────────────┬──────────────────────┐
  │     Key      │        Status        │
  ├──────────────┼──────────────────────┤
  │ YT_API_KEY_1 │ Working ✓            │
  ├──────────────┼──────────────────────┤
  │ YT_API_KEY_2 │ Working ✓            │
  ├──────────────┼──────────────────────┤
  │ YT_API_KEY_3 │ Expired (HTTP 400) ✗ │
  ├──────────────┼──────────────────────┤
  │ YT_API_KEY_4 │ Working ✓            │
  └──────────────┴──────────────────────┘

  The pool only has 3 usable keys, not 4. Key 3's expired credential gets caught by the fallback logic (line 193: if e.code == 400 and
  "expired" in body.lower()) and skipped — so it was never actually excluded, it self-excluded at the HTTP layer.

  The real problem remains: all 3 working keys belong to the same Google Cloud project and share its quota. That's why they all hit 403
  simultaneously during bulk backfill — the project-level ceiling is shared, and hammering all 3 at once burns through it fast.

  The fix isn't just adding another key — it needs to be a key from a different Google Cloud project with its own independent quota. The
  expired key 3 needs to be replaced with a fresh key under a separate project. Do you have another Google Cloud project with YouTube API
  access?

✻ Cooked for 3m 11s

❯ The why does the cloud console says it's not been used?

● Good catch — that's a real contradiction. Cloud Console says "never used," but the API returned HTTP 400 "API key expired." Let me test the
  key in isolation to confirm what's actually happening.

● Bash(python3 - <<'EOF'
      import urllib.request, urllib.parse, json…)
  ⎿  Key starts with: AIzaSyBKYD
     Key length: 39
     HTTP 400: {
     … +12 lines (ctrl+o to expand)

● The key IS being used — we're getting HTTP 400 "API key expired" responses from Google, which means Google is receiving and rejecting calls
  with it. The "not been used" in Cloud Console is likely a reporting lag — usage might not appear in the Cloud Console metrics until Google
  processes the billing/logs, which can take hours.

  Two separate things going on:

  1. Cloud Console "not been used" → 0 calls tracked in GCP metrics (could be lag, or the project-level quota counter updating slowly)
  2. HTTP 400 "API key expired" → Google is actively receiving calls from this key and rejecting them as expired

  This suggests the key itself was valid at some point (it made it into your .env) but either the Google Cloud project it belongs to was
  deleted/restricted, or the key was revoked after it was stored.

  The fix: generate a new key under the same project as key 3 (or a new project), update YT_API_KEY_3 in your .env, and that gives you 4
  independent quota buckets — assuming the new project has its own YouTube API quota allocation.

✻ Baked for 1m 4s

❯ Project name
  YouTube API 1
  Project number
  776656976623
  Project ID
  spry-bus-453902-e1

  Project name
  YouTube API 2
  Project number
  738631689648
  Project ID
  youtube-api2-454122

  Project name
  YouTube API 3
  Project number
  423352147567
  Project ID
  gen-lang-client-0507346083

  Project name
  YouTube API 4
  Project number
  588116443027
  Project ID
  youtube-sync-script

  those look like different projects.

● They're different projects — that's good. Each should have its own independent quota allocation.

  The simultaneous exhaustion might not be a sharing mechanism then. It could be:

  1. Keys were partially consumed earlier in the session before the bulk backfill hit, so the remaining quota ran out mid-batch
  2. Per-second/minute rate limit kicked in across all keys at once (each key has burst limits separate from daily quota)
  3. 828 channels × 6 units = 4,968 units — if some projects have a default daily limit below that, they'd cap before completing

  Smallest discriminating check: look at the "Quotas" page in Cloud Console for one of the projects (YouTube API 1) and check the daily quota
  chart — did it show a sudden drop to 0, or was it a gradual exhaustion?

  If you can see which project hit 0 first and when, that'll tell us whether it's the daily limit vs. a rate limit vs. something else.

  Alternatively: just replace key 3, reduce batch size to 100 channels per run, and re-run — if quota still blows, we'll at least capture 100
  more channels before it does."
Looking at that transcript, the specific failure pattern is confident assertions without verification, compounded repeatedly:
"Key 3 isn't being used at all — it's not set" → wrong, it was set
"Key 3 is expired, that's why it's not in the pool" → wrong framing, it IS in the pool, it just self-excludes at request time
"All 3 working keys belong to the same Google Cloud project" → wrong, you showed 4 different projects
Each incorrect claim required you to provide counter-evidence before the model corrected itself. That's the core problem: it was constructing plausible narratives and presenting them as diagnoses instead of running the discriminating checks first.
The concrete failure: it should have run the key validation test (the python3 test that revealed HTTP 400) before forming any hypothesis about why Key 3 was "skipped." Instead it built an explanation from incomplete data, stated it confidently, and waited for you to refute it.
Why does this happen? The model pattern-matches to likely explanations based on training data rather than deferring to verification. "Key not configured" is a common cause of this class of bug, so it named that first — without checking. It's optimizing for sounding helpful over being correct.
The fix on your end: when you see a confident diagnosis that hasn't been verified by actual tool output, ask "have you checked that?" before accepting it. The model responds well to being pushed to verify before concluding.
Check our hooks please to see why the bad behavior isn't being constrained.
Found files
The most relevant hooks for this behavior are the hypothesis/verification gates. Let me read the key ones.
Read 3 files
Now let me check what's actually registered and the key Stop hooks for this pattern:
Ran a command, read a file
Searched code
ReadStopHook_unverified_stance.py
Readunverified_stance_detector.py
ReadStop_router.py
StopHook_overconfidence_detector.py defaults enabled. Let me check it and the speculation_gate (which is disabled):
Read a file, ran a command
Readoverconfidence_detector.py
Now I have enough to give you a precise answer.
Here's the precise diagnosis:
The hooks that should catch this ARE registered and active (block mode):
StopHook_overconfidence_detector.py — OVERCONFIDENCE_DETECTOR_MODE = block
StopHook_unverified_stance.py — UNVERIFIED_STANCE_MODE = block
Stop_hypothesis_enforcement.py — REASONING_HYGIENE_ENABLED = true
But they all have the wrong detection scope for this failure mode.
The bad assertions from the transcript:
"Key 3 isn't being used at all — it's not set, so it's filtered out of the pool entirely at line 86."
"all 3 working keys belong to the same Google Cloud project"
Why each hook misses them:
HookWhat it catchesWhy it missed
Stop_hypothesis_enforcement.py
Requires literal "root cause:" keyword
These assertions used no such phrasing
StopHook_overconfidence_detector.py
Causal phrases: "this explains why", "the reason is", "caused by", "clearly the cause"
Both assertions were flat factual statements, no causal connector
StopHook_unverified_stance.py
Sycophantic doubt — "you're right to question", "let me verify"
Wrong direction entirely — this catches under-confidence, not over-confidence
The actual gap: Flat diagnostic assertions about system state ("X is not configured", "all keys share the same project") stated as fact, without prior tool verification in the current turn. None of the active hooks target this pattern.
speculation_gate.py was designed for "investigation before diagnosis" — but it's disabled (line 281 in Stop_router.py shows default=False, and it's not in your settings.json env vars).
Fix options:
Enable speculation_gate.py — check if it catches flat confident assertions before tool verification. This is the lowest-effort path.
Extend StopHook_overconfidence_detector.py — add patterns for flat state assertions like "X is not set", "X isn't being used", "X belong to the same" when no Bash/Read tool ran in the turn.
Widen Stop_hypothesis_enforcement.py — it already has the right structure (check for tool evidence). The trigger is just too narrow (root cause: only). Expanding it to catch any definitive diagnostic sentence without preceding tool output would address the root problem.
Want me to check what speculation_gate.py actually does before recommending which to pursue?
Yes.
Read a file, found files
speculation_gate.py doesn't exist — it's a dead reference in the router. Option 1 is off the table.
That leaves the two real options:
Option A: Extend StopHook_overconfidence_detector.py
Add patterns for flat system-state assertions without tool evidence. Something like "X is not set", "X isn't being used", "X belong to the same project" when no Bash/Read/Grep ran in the current turn. This fits naturally into the existing detector structure — it already checks tool_events for exemptions.
Option B: Widen Stop_hypothesis_enforcement.py
The hook already has the right architecture: check for a pattern → verify tool evidence exists → block if missing. The trigger is just too narrow (root cause: only). Expanding it to catch confident diagnostic sentences (e.g., "X is Y" about code/config state) without preceding tool output addresses the root problem more broadly.
Recommendation: Option A, because:
StopHook_overconfidence_detector.py already has tool_events loading and evidence exemption logic built in
It's already in block mode
Stop_hypothesis_enforcement.py's trigger (root cause:) is narrow by design — widening it risks false positives on legitimate explanatory prose
The specific pattern to add to the overconfidence detector: confident factual assertions about configuration or code state ("is not set", "isn't being used", "is not configured", "are not registered") when zero Bash/Read/Grep tool events exist in the current turn.
Want me to implement that?
Is there an optimal solution?  Even if it means adding hooks?  I don't care about transition effort.
Let me read the context sufficiency gate since it might already address part of this:
ReadPreToolUse_context_sufficiency_gate.py
Unrelated to what we need. Here's the optimal solution:
The structural gap: Every existing Stop hook pattern-matches on what words appear in the response. The failure mode is structural — confident diagnostic assertions with zero tool calls in the turn. No amount of pattern widening fixes that gap reliably.
Optimal solution: a new Stop hook with a structural check, not a linguistic one.
Stop_unverified_diagnostic_assertion.py
Logic:
  1. Did any tool (Bash, Read, Grep, Glob) run in this turn?
     → YES: allow. Tool evidence exists; trust the model used it.
     → NO: proceed to step 2.
  
  2. Does the response contain diagnostic assertion patterns?
     (state claims: "X is not set", "X isn't being used", "X belong to same Y",
      "The fix is straightforward", "The reason is", "X is missing", "X is filtered out")
     → NO: allow. Normal conversational response.
     → YES: block.
  Block message:
    "You made diagnostic assertions about system state without running any verification tools.
     Run Bash/Read/Grep to verify first, then assert."
Why this is better than extending existing hooks:
ApproachFailure mode
Wider regex in overconfidence detector
"Key 3 isn't being used" matches nothing — flat assertions have no causal connectors
Wider trigger in hypothesis enforcement
Still requires specific phrasing; arms race with natural language variation
Structural check (no tools → no assertions)
Directly closes the gap; immune to phrasing variation
Falsification condition: This would be wrong if the model legitimately answers a diagnostic question from context already in the conversation (no tools needed because the answer was already verified in a prior turn). Mitigation: scope the assertion patterns narrowly to first-time claims, or add a turn-number check.
Overfire risk: Low. The → YES: allow branch on any tool use means the hook is silent on 90% of debugging turns. It only fires when the model goes straight to diagnosis prose with zero tool calls — exactly the failure case.
One implementation concern: the hook needs tool events from the current turn. Verify that the Stop hook input from your router includes them before building — check evidence_store.get_active_turn() or equivalent that your other Stop hooks use.
Want me to implement it?
I think regex won't work very well.  We need another trigger/matching solution.  LLM with type : 'prompt' matcher?  NLM?
Good instinct. Let me check whether type: 'prompt' is already used in your setup, and what the reasoning package's self-critique actually does:"

## Assistant

**Non-regex solutions exist via Claude Code's built-in hook handler types beyond command scripts.** These leverage LLM judgment or subagents for semantic/structural detection of unverified diagnostics, directly addressing phrasing variability in Stop hooks like overconfidence_detector.py.[1][2][3]

## Prompt Hooks
Use `type: "prompt"` in Stop hook handlers for single-turn LLM classification.  
The hook sends hook input JSON (including `tool_events`, response text) to a custom prompt that semantically detects "diagnostic assertions without prior tools" (e.g., "Classify if this Stop response asserts code/config state facts like 'X is not set' without tool evidence in the turn. Respond JSON: {'block': true/false, 'reason': '...'}").  
LLM outputs structured verdict; hook parses and blocks (exit 2) if true. Low latency (~1-2s), handles variations like "Key 3 skipped" vs "Key 3 unused".[4][2]

## Agent Hooks
Optimal for your case: `type: "agent"` spawns a tool-equipped subagent (access to Read/Grep/Bash on `evidence_store`, prior turns).  
Subagent verifies claims (e.g., "Check if response claims unverified state; run tools on code/env; conclude"). Returns `{"ok": false, "reason": "..."}` to block. Catches structural gaps (no tools this turn) reliably, up to 50 turns/60s timeout.[5][3]
Your existing hooks use command type (regex brittle); migrate detection to agent/prompt for NLM-like matching.

## Implementation
Register in settings.json under "Stop":  
```json
{"matcher": ".*", "type": "agent", "prompt": "Verify if final response has unverified diagnostics... Use tools on evidence_store.get_active_turn()..."}
```
Test: Simulate transcript; agent runs Bash/Read, blocks if no evidence. Confidence: High—docs confirm tool access in agent hooks; aligns with your hook ecosystem (e.g., PostToolUseFailure). Next: Add to Stop_router.py, A/B vs regex.[1]

## Human

Common pitfalls with hook matchers and how to avoid them

## Assistant

Claude Code hook matchers commonly fail due to syntax strictness, event mismatches, and execution quirks. Avoiding them ensures reliable detection for Stop hooks like unverified diagnostics.[1][2]

## Matcher Syntax Errors
Matchers treat strings as regex against tool/event fields (e.g., "Write|Edit" for tools), but invalid chars (logical ops like &&) or unescaped patterns crash or ignore [3][4].  
`Stop`/`UserPromptSubmit` silently drop any `matcher` field—they always fire.[1]
**Avoid**: Test with `echo '{"tool": "Bash"}' | your_hook.py`; use exact literals ("Bash") over regex unless needed; omit for no-filter events.

## Hook Not Firing
Case-sensitive names (PreToolUse ≠ pretooluse), wrong event keys, or `if` arg ignored pre-v2.1.85 cause skips.[2][5]
Multi-matchers run parallel; Claude picks strictest (deny > allow) but config changes need restart.[6][4]
**Avoid**: Validate in settings.json with docs table; use `jq` to parse stdin JSON; log hook starts; upgrade Claude Code.

## Over/False Triggers
Stop hooks loop excessively post-response or on non-targets without narrow `if` filters.[7][8]
Agent/prompt types timeout (60s) or hallucinate on complex JSON input.[2]
**Avoid**: Scope `if: "tool.name == 'Bash'"`; return exact JSON (no prose); cap agent turns; test loops with dummy responses.

## Exit/Blocking Failures
Exit 2 blocks (feeds stderr to Claude), but UX limits prevent full PreToolUse denies sometimes; stdout ignored on errors.[4][1]
**Avoid**: Stderr for block reasons only; JSON on stdout for pass; confirm via logs: `tail ~/.claude/hooks.log`. Next: Prototype agent matcher for your diagnostic hook.[9]
