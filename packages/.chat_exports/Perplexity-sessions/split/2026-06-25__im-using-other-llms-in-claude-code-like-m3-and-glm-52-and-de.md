---
title: "I'm using other LLMs in claude code, like M3 and GLM-5.2 and DeepSeek-v4-Flash.  Why do I keep getting these errors?
'
"
date: "2026-06-25"
mode: "COPILOT"
uuid: "aae04e36-c408-4416-9f26-36cfc76c13af"
entry_count: 1
---

## Human

I'm using other LLMs in claude code, like M3 and GLM-5.2 and DeepSeek-v4-Flash.  Why do I keep getting these errors?
"
❯ /compact
  ⎿  Error during compaction: API Error: The model has reached its context window limit.
"

And how can I either fix or avoid them?

## Assistant

I now have a thorough picture of what's happening. Let me compile the answer.

## Root Cause: Third-Party APIs Misreport Their Context Windows

The core issue is a **mismatch between what GLM/GLM-5.2, DeepSeek-v4-Flash, and similar third-party models *tell* Claude Code their context window is, and what they actually support**.

When you run `/compact`, Claude Code asks the model's API endpoint what its context window size is. Zhipu's API (GLM models) has a known bug where it **incorrectly reports 1M tokens** when the real limit is ~200K tokens. Claude Code trusts that number, attempts to fit the entire conversation history into a compaction request, and the model promptly rejects it because the actual window can't hold that much. The result is exactly what you're seeing: `Error during compaction: API Error: The model has reached its context window limit.`[1]

DeepSeek and other third-party providers accessed via `ANTHROPIC_BASE_URL` routing face the same class of problem — Claude Code's auto-detection of context window size fails or over-estimates for non-native models.[2]

***

## The Direct Fix: Override the Window Size

### Environment Variable Approach

Set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` to force Claude Code to use a specific token budget for compaction calculations, regardless of what the API reports:[3]

```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70"
  }
}
```

This caps compaction calculations at 150K tokens (safely within the real 200K window for GLM/DeepSeek), and triggers it at 70% utilization (~105K tokens) instead of the default 95%. Pair this with the per-provider launcher aliases you're likely already using, e.g.:[4]

```bash
# .zshrc / .bashrc
alias glmc='ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
  ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY" \
  CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000 \
  CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70 \
  claude'

alias dsc='ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic" \
  ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY" \
  ANTHROPIC_MODEL="deepseek-chat" \
  CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000 \
  CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70 \
  claude'
```

### Workaround When Already Stuck Mid-Session

If you hit the error during an active session:[5]
1. Close the terminal entirely
2. Open a new terminal, run `claude --resume`, and pick the conversation
3. Type `/model` and switch to an actual Claude model (e.g., `sonnet`)
4. Trigger `/compact` — it will succeed on a model that handles it correctly
5. Use `/model` again to switch back to GLM/DeepSeek and continue

***

## Proactive Avoidance Strategies

### Compact Early and Explicitly

Don't let auto-compaction trigger at all — run `/compact` yourself before the session fills up, with instructions on what to preserve:[6][7]

```
/compact keep the current task state, file paths modified, and pending decisions
```

Target this at 50–60% context utilization, not 90%+. The `/context` command shows you exactly where you are.[4]

### Disable Auto-Compact Entirely

When using third-party models, auto-compact is unreliable because it can fire at the wrong threshold based on the bad window report. You can disable it in settings:[8][9]

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_AUTO_COMPACT": "1"
  }
}
```

Then manage compaction manually. This also reduces session startup context overhead significantly.[9]

### Use `/clear` + Handoff Document

For longer sessions, Anthropic's own engineers recommend **not relying on compaction at all** for third-party models. Instead:[4]

1. Before you expect to hit limits, have the model write a structured handoff to a file: completed work, remaining tasks, specific file paths
2. Run `/clear` (wipes everything except CLAUDE.md)
3. Load the handoff file as your first message in the new session

This is more reliable than compaction across any model and avoids "context rot" entirely.[10]

### Keep Sessions Smaller

The underlying design principle: sessions with third-party models should be scoped to single coherent tasks. Each feature/phase gets its own `/clear` + task-specific CLAUDE.md context. The filesystem acts as shared memory across sessions, not the context window.[11]

***

## Summary of the Variable Hierarchy

| Variable | What it does |
|---|---|
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Overrides the token budget used for compaction threshold calculations [3] |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Sets compaction trigger as % of the window (default 95%) [4] |
| `CLAUDE_CODE_DISABLE_AUTO_COMPACT` | Disables automatic compaction entirely [8] |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Removes 1M model variants and caps window to 200K [4] |

The most targeted fix for GLM/DeepSeek is `CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000` — it tells Claude Code to treat the effective window as 150K without disabling any features, and it applies per-launch so you can scope it to individual provider aliases.
