---
title: "for claude code, what hooks allow type: 'prompt'?"
date: "2026-02-26"
mode: "COPILOT"
uuid: "36adcb20-b0e5-457d-8789-13a9d22cf881"
entry_count: 2
---

## Human

for claude code, what hooks allow type: "prompt"?

## Assistant

**All hook events in Claude Code support the "prompt" hook type.**

Hooks in Claude Code have three possible types: "command" (default, runs shell commands), "prompt" (sends input to a Claude model for yes/no decisions), and "agent" (spawns a subagent with tools).[1]

The "prompt" type works across every lifecycle event, including SessionStart, UserPromptSubmit, PreToolUse, Stop, Notification, and others listed in the full reference.[2][1]

## Key Events
- **Blocking events**: PreToolUse, UserPromptSubmit, Stop, PermissionRequest – use "prompt" for model-based approval/denial.
- **Post-action events**: PostToolUse, PostToolUseFailure – add feedback via model reasoning.
- **Session events**: SessionStart, SessionEnd – inject context dynamically.

## Prompt Type Details
For "type": "prompt", provide a "prompt" field with $ARGUMENTS placeholder for event JSON; optional "model" (defaults to fast like Haiku).[1]

Example for Stop event:
```
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Check if tasks complete. If not: {\"ok\": false, \"reason\": \"remaining work\"}."
      }]
    }]
  }
}
```
Model returns {"ok": true/false, "reason": "..."}; false blocks and feeds reason back.[2]

## Human

"I'll barely remember to use the word think. I'll never remember to use the other parameters like why, decide, arc, risk, premortem, etc. Can't we have those used intelligently and automatically?
Fair point. The explicit THINK WHY: syntax is a power-user interface nobody will actually use. Let me reconsider.
The original hook had auto-detection via ML embeddings (sentence-transformers), which was heavy and over-triggered. But we can do keyword-based auto-detection that's fast and precise — the archived code already had PROFILE_KEYWORDS for this. The trick is being selective enough to avoid false positives.
Here's what I'm thinking:
Keep the explicit THINK [PROFILE]: as an override, but add automatic profile detection that fires when the prompt doesn't start with THINK but clearly matches a profile:
ProfileAuto-triggers when prompt contains...
debug_rca
2+ of: debug, root cause, crash, broken, failure, error, investigate, "what happened", flaky
tradeoff_decision
2+ of: "should I", "option A", choose, vs, tradeoff, "which is better", recommend, decide
architecture
2+ of: architecture, design pattern, boundary, module, "extract", "separate service", refactor + structure
pre_commit_risk
2+ of: risk, deploy, ship, release, rollback, "blast radius", migration, "before we"
The 2+ keyword threshold is what keeps it from over-triggering — a single word like "error" or "deploy" won't fire it. You'd need to say something like "debug why this error keeps happening" or "should we deploy this migration" to trigger a profile.
And a cooldown (say 60 seconds) prevents it from firing on every follow-up message in a debugging conversation.
The quick triage profile would NOT auto-trigger — that would fire on everything. It stays explicit-only (THINK: with no alias).
Want me to add the auto-detection layer?"

 Can we use the type prompt to help with this auto detection question?

## Assistant

Yes, Claude Code's "prompt" hook type is ideal for implementing keyword-based auto-detection of THINK profiles (like debug_rca or tradeoff_decision) without relying solely on explicit syntax.[1]

## How It Works
Place a "prompt" hook on UserPromptSubmit to analyze incoming prompts via Claude model before processing. The model checks for 2+ keywords (e.g., "debug", "root cause" for debug_rca), decides the profile, and returns structured JSON like {"profile": "debug_rca", "ok": true, "inject": "THINK debug_rca: ..."}.[1]

If matched, inject rewritten prompt (e.g., prepend "THINK debug_rca: ") into stdin or block with feedback; cooldown via simple timestamp check in script wrapper. This auto-triggers selectively, avoiding over-firing on single words.[2][3]

## Example Hook Config
```
{
  "hooks": {
    "UserPromptSubmit": [{
      "type": "prompt",
      "prompt": "Analyze prompt: {{$ARGUMENTS.prompt}}. Match profiles if 2+ keywords:\n- debug_rca: debug, root cause, crash, error, investigate\n- tradeoff_decision: should I, choose, vs, tradeoff\nIf match, return {\"profile\": \"debug_rca\", \"inject\": \"THINK debug_rca: {{prompt}}\", \"ok\": true}. Else {\"ok\": true}. Cooldown: skip if recent.",
      "model": "claude-3.5-haiku@2024-10-22"
    }]
  }
}
```
Model output feeds back; parse in PostToolUse hook for injection. Test in your multi-terminal setup—aligns with your SessionStart/PreCompact patterns for context preservation.[4]
