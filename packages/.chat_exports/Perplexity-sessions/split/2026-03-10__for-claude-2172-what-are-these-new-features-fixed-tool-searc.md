---
title: "for claude 2.1.72, what are these new features?  Fixed tool search to activate… │
│                                    "
date: "2026-03-10"
mode: "COPILOT"
uuid: "34c7705c-e437-49a7-b385-e15117665690"
entry_count: 1
---

## Human

for claude 2.1.72, what are these new features?  Fixed tool search to activate… │
│                                                    │ Added `w` key in `/copy` to w… │
│  Sonnet 4.6 with medium effort · API Usage Billing │ Added optional description ar… │
│                         P:\\                        │ /release-notes for more

## Assistant

Claude Code 2.1.72 adds a couple of small but useful features plus a tooling fix, and in the same wave Anthropic is highlighting Sonnet 4.6’s new “effort: medium” behavior and billing.

### Claude Code 2.1.72 changes

For 2.1.72 specifically, the changelog items you’re seeing are:

- **“Fixed tool search to activate…”** – Tool search now works even when you’re pointing at a custom Anthropic base URL, as long as `ENABLE_TOOL_SEARCH` is set, instead of silently failing in that configuration.[1]
- **“Added `w` key in `/copy` to w…”** – In the `/copy` panel, pressing **`w`** writes the currently focused selection directly to a file, bypassing the clipboard; this is meant for SSH / TTY workflows where clipboard isn’t available or is annoying.[2][1]
- **“Added optional description ar…”** – `/plan` now takes an optional free‑text description like `/plan fix the auth bug`, which both enters plan mode and immediately starts a plan with that description, saving you a step.[2]
- There is also a new **`ExitWorktree` tool** so you can explicitly leave an `EnterWorktree` session and return to the parent workspace without manual path juggling.[2]

These are on top of the 2.1.x line’s broader skills/commands unification and worktree/tooling improvements, but the snippet you pasted is calling out just these incremental 2.1.7x additions.[3][1]

### Sonnet 4.6 with medium effort & billing

The “Sonnet 4.6 with medium effort · API Usage Billing” line is about the underlying model, not the desktop app UI:

- **Sonnet 4.6** is the new default Sonnet model, with better coding, long‑context reasoning (up to a 1M token context window in beta), and planning, at the same base price as Sonnet 4.5 (around 3 USD per million input tokens and 15 USD per million output tokens in the standard context range).[4][5]
- It introduces an **`effort` parameter**, and “medium effort” is the recommended setting for most workloads because it balances capability versus latency and cost; thinking tokens are billed as output tokens, so more effort means more billed output tokens.[6][4]
- For very large contexts (over roughly 200k input tokens), all tokens are billed at a higher “long context” rate (around 6 USD per million input and 22.5 USD per million output for Sonnet 4.6), which is what the “API Usage Billing” note is reminding you of.[4][6]

If you want, I can suggest concrete `effort` defaults (and maybe guards) for your main API use cases so you don’t get surprise thinking‑token bills—do you primarily care about coding, long RAG-style context, or agent-style planning?  
