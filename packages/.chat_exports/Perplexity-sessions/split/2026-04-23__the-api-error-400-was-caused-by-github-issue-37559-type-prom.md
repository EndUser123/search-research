---
title: "The API Error 400 was caused by GitHub issue #37559 — type: 'prompt' Stop hooks are broken across all Claude Code versio"
date: "2026-04-23"
mode: "COPILOT"
uuid: "cf5280d1-9840-40da-8404-968bee695431"
entry_count: 2
---

## Human

The API Error 400 was caused by GitHub issue #37559 — type: "prompt" Stop hooks are broken across all Claude Code versions
  (confirmed up to v2.1.117). The feature cannot work until Anthropic fixes the underlying platform bug.

---

is it true but this github issue is still not fixed today.

## Assistant

Based on the search results, I can confirm the situation regarding GitHub issue #37559:

**Issue #37559 remains open and unfixed as of today (April 22, 2026).**  The issue, titled "Stop hooks broken, prompt hooks can't inject context, capabilities undocumented per event type," was reported on March 21, 2026, and the search results show it's still actively referenced in multiple related bug reports.[1][2][3]

**The problem is broader than initially stated.** Your description of "prompt Stop hooks are broken across all Claude Code versions" is accurate, but the issue encompasses multiple related failures:[1]

- Stop hooks (both prompt-type and plugin-type) failing to execute or execute correctly
- Prompt hooks unable to inject context into Claude's reasoning
- Incomplete/undocumented capabilities varying by event type

**Evidence of ongoing impact:**

Multiple downstream issues confirm this remains broken:
- Issue #29767 (Feb 27, 2026): Plugin Stop hooks never execute despite registration[4]
- Issue #32608 (Mar 8, 2026): Prompt-type Stop hooks return `{"ok": false}` but don't actually stop execution[5]
- Issue #38651 (Mar 24, 2026): Stop hooks cause empty results in print mode[3]
- Issue #46468 (Apr 9, 2026): PostToolUse hook exit codes don't block or undo operations[2]

The most recent related bug report is from April 9, 2026—just 13 days ago—indicating Anthropic has not yet resolved the underlying platform issue.  There's no indication in the search results of a fix being released or scheduled for v2.1.117 or later versions.[2]

**Bottom line:** Yes, the claim is true, and the issue remains unfixed as of today. This is a confirmed, high-impact platform-level bug affecting the hook system's core functionality.

## Human

is it only prompt hooks or is it also type agent hooks?

## Assistant

**Both prompt hooks and agent hooks are broken, but in different ways.**[1][2]

## Prompt hooks: Stop hooks specifically broken

The issue #37559 you cited focuses on `type: "prompt"` hooks where Stop hooks can't execute properly.[3]

## Agent hooks: Fundamentally broken across events

Agent hooks (`type: "agent"`) are experiencing broader failures:[4][5]

- **Issue #39184 (Mar 24, 2026)**: Agent-type hooks error with generic "hook error" on all event types tested (not just Stop)[4]
- **Issue #22637 (Feb 1, 2026)**: Agent-type hooks are "fundamentally broken for PreToolUse" with no reliable workaround beyond command-type hooks[5]
- **Issue #24920 (Feb 10, 2026)**: Agent hooks in Stop events have their `prompt` field silently stripped from `settings.json`, leaving broken configurations[6]

## The distinction matters

According to Anthropic's official docs:[2]
- **Prompt hooks** make a single LLM call to Claude for yes/no decisions based on input data alone
- **Agent hooks** spawn a subagent that can read files, run commands, and use tools for deeper verification

**Bottom line:** The problem extends beyond prompt-type Stop hooks. Agent hooks are experiencing platform-level failures across multiple event types, with additional issues like silent field corruption. The underlying bug is systemic, affecting the hook infrastructure at a deeper level than just prompt-based Stop behavior.
