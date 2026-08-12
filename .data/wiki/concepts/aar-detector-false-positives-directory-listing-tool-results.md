---
title: "AAR detector false positives from directory-listing tool results"
created: 2026-08-12
source: session-019ff1a0
tags: [aar, detectors, false-positives, tool-result-filtering, transferable-technique]
summary: >
  The AAR unused_capability detector scans tool_result text for executable-shaped
  tokens (foo.py, bar.sh) and flags any that the assistant never subsequently
  invokes. Directory-listing tools (list_dir, Get-ChildItem, glob, find) return
  filenames that match this regex but are NOT discovered capabilities -- they're
  just the contents of a directory the agent browsed. This produced 70/92 (76%)
  and 137/248 (55%) false-positive rates across two AAR runs. Fix: build a
  tool_call_id to tool_name map from assistant turns and skip tool_results
  produced by directory-listing tools. Transferable: any detector that pattern-matches
  against tool_result content must filter by producing tool_name.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/close-scanner-false-positive-resolved-handoff-references.md
    type: related
  - target: wiki/concepts/serde-broken-false-positive-sweep-20260801.md
    type: related
---

# AAR detector false positives from directory-listing tool results

## Decision context

The AAR skill's `detect_unused_capability` detector (Spec Section 19) flags
tool-result content that mentions a discovered capability (CLI script,
executable) which the assistant never subsequently invokes or references.
The detector scans all `TOOL_RESULT` events for executable-shaped tokens
matching `\b([A-Za-z_][A-Za-z0-9_-]*\.(?:py|sh|js|ts|ps1|mjs))\b`.

Two AAR runs in the same session produced extreme false-positive rates:
- Run 1: 70 of 92 opportunity signals (76%) were unused_capability false positives
- Run 2: 137 of 248 signals (55%) were unused_capability false positives

Every false positive traced to the same root cause: the agent ran `list_dir`
to browse a skill's `__lib/` directory, and every `.py` file in the listing
was flagged as a "discovered but unused capability."

## Root cause

Directory-listing tools (`list_dir`, `Get-ChildItem`, `glob`, `find`)
return filenames as their result text. These filenames match the capability
regex because they ARE executable-shaped tokens (`resolve.py`, `verdict.py`,
etc.). But they are not capabilities the agent "discovered" in the sense
the spec intends -- the agent was browsing a directory, not encountering
a tool or script it should consider using.

The detector had no mechanism to distinguish:
1. A `run_terminal_command` result that says "Available scripts: foo.py, bar.py" (genuine discovery)
2. A `list_dir` result that says "foo.py, bar.py, baz.py" (directory contents)

Both produce text that matches the regex. Only (1) represents a discovered
capability.

## Fix

Added a `_DIR_LISTING_TOOLS` frozenset and a `tool_call_id -> tool_name`
map built from assistant turns. Before scanning a tool_result's text,
the detector checks whether the producing tool was a directory-listing
tool and skips it entirely.

Source receipt: `~/.grok/skills/aar/__lib/detectors.py`, function
`detect_unused_capability`, lines 1185-1215 (added 2026-08-12, commit 6b73818).

The fix also checks `CanonicalEvent.tool_name` (set by the preprocessor)
as a fallback when `tool_call_id` linkage is unavailable.

## What this means for our workspace

This pattern generalizes beyond `detect_unused_capability` to ANY AAR
detector or analysis tool that pattern-matches against tool_result text:

- **detect_duplicate_capability_references** -- could also fire on filenames
  seen in directory listings that happen to match tool names used later
- **Any future detector** that scans tool_result content for patterns

The transferable technique: **always build a tool_call_id to tool_name map
and filter by producing tool before scanning tool_result text.** Directory-
listing tools produce structurally different results from command-execution
tools, and treating them the same way produces false positives.

Related false-positive patterns in this workspace:
- [[close-scanner-false-positive-resolved-handoff-references]] -- close
  scanner flags file paths in resolved handoffs (same class: scanner doesn't
  understand context)
- [[serde-broken-false-positive-sweep-20260801]] -- serde_broken labels
  were 100% false positives from misclassified root causes (same class:
  mechanical classification without context)
- [[agent-improvement-loop-patterns-automated-learning-from-traces]] --
  AAR's 32-detector engine is our detection layer in the improvement loop;
  false-positive-heavy detectors reduce trust in the loop

## Falsifier

This fix would be wrong if directory-listing results sometimes DO contain
genuine capability discoveries -- for example, if an agent runs `ls` on a
`bin/` directory and one of the scripts listed is a tool the agent should
have used but didn't. In that case, skipping all directory-listing results
would suppress a real signal. The current fix accepts this tradeoff because
the false-positive rate (55-76%) vastly exceeds the hypothetical true-positive
rate from directory browsing. If a future AAR shows agents missing
capabilities they saw in directory listings, re-evaluate the filter.

## Receipts

- **Detector implementation**: `~/.grok/skills/aar/__lib/detectors.py`, function `detect_unused_capability`, lines 1173-1240 (the regex + tool filter)
- **Fix commit**: `6b73818` (2026-08-12) -- added `_DIR_LISTING_TOOLS` filter + `call_id_to_tool` map
- **Test suite**: `~/.grok/skills/aar/tests/test_opportunity_detectors.py` -- 16/16 pass after fix
- **AAR report 1**: `P:/.artifacts/grok-aar/console_console_ff229e6d-d51c-4749-a738-b39b/20260811-aar/aar-report.md` (70/92 false positives)
- **AAR report 2**: `P:/.artifacts/grok-aar/console_console_ff229e6d-d51c-4749-a738-b39b/20260812-aar/aar-report.md` (137/248 false positives)

## Sources

- AAR report 1: `P:/.artifacts/grok-aar/console_console_ff229e6d-d51c-4749-a738-b39b/20260811-aar/aar-report.md` (70/92 false positives)
- AAR report 2: `P:/.artifacts/grok-aar/console_console_ff229e6d-d51c-4749-a738-b39b/20260812-aar/aar-report.md` (137/248 false positives)
- Fix commit: `6b73818` (2026-08-12)

## Auto-related

- [[model-tool-calling-capability-matrix]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[skill-catalog]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[router-proxy-tool-calling-normalization-patterns]]

