---
title: "Fallback paths defeat primary fix: the silent undermining pattern"
slug: fallback-paths-defeat-primary-fix-silent-undermining
created: 2026-08-10
source: session-20260810
tags: [anti-pattern, fallback, scoping, contamination, defensive-coding]
summary: >
  When a fix adds isolation or scoping, the fallback path (else branch, catch-all,
  default behavior) must be held to the same contract as the primary path. If the
  fallback silently relaxes the isolation, it re-introduces the exact failure mode
  the fix was meant to prevent — but only in edge cases, making it hard to detect
  in testing and devastating in production. This pattern recurs in session resolution,
  auth checks, path validation, and data filtering.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/caller-context-as-parameter-not-callee-discovery.md
    type: related
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: extends
---

# Fallback paths defeat primary fix

## The pattern

A fix adds isolation, scoping, or validation to the primary code path. The
fallback path (the `else` branch, the `except` block, the default case) is
left as-is — it predates the fix and was never updated to match the new
contract. The fallback silently relaxes the isolation, re-introducing the
exact contamination, bypass, or data leak the fix was meant to prevent.

**The one-line test:** does the fallback path hold the same contract as the
primary path? If the primary fails-closed but the fallback fails-open, the
fallback is a hole in the fix.

## Reference incident (2026-08-10)

The `/todo` scanner session-scoping fix added workspace filtering to the
filesystem session-ID resolver: `_filesystem_sid()` derives an `encoded_cwd`
from `os.getcwd()` and searches only `sessions/<encoded-cwd>/`. But when
that workspace-specific dir doesn't exist, the code falls back to
`sessions_root` — scanning ALL workspaces (2680 transcripts across 11+
prefixes). The `/review` correctness specialist found this empirically:

```python
# common.py:88-90
workspace_dir = sessions_root / encoded_cwd
search_root = workspace_dir if workspace_dir.exists() else sessions_root
#                                                                     ^^^^^^^^^^^^^^
#   THE HOLE: fallback scans all workspaces, defeating the isolation filter
```

The primary path (workspace_dir exists) is correctly scoped. The fallback
path (workspace_dir doesn't exist) silently relaxes to global scope. This
is the same contamination the fix was meant to prevent — but it only
triggers when the workspace dir is missing, so it passed initial testing
(the primary workspace always had a dir).

## Why this pattern is dangerous

1. **Hard to detect in testing.** The fallback only fires in edge cases
   (new workspace, worktree, CWD change). Tests typically run in the
   primary workspace where the dir exists.

2. **The fix "looks correct" in review.** The primary path is well-implemented.
   The fallback is a single line, easy to overlook.

3. **The failure is silent.** No error, no warning — just wrong results.
   The scanner returns items from a sibling workspace without any signal
   that the isolation was bypassed.

4. **It undermines trust in the fix.** The operator sees intermittent
   contamination and can't figure out why — the primary path is correct,
   so the intermittent cases look like random failures.

## How to catch it

**During implementation:** for every `if X: <primary> else: <fallback>`,
ask: does the fallback hold the same contract as the primary? If the
primary isolates, the fallback must isolate too — or fail-closed.

**During review:** check every `else` branch in code that was changed for
isolation/scoping/validation. The fallback is where the fix leaks.

**The structural fix:** fail-closed when the primary condition isn't met.
If the workspace dir doesn't exist, return None (no session ID resolved)
rather than searching globally. Better no result than a wrong result.

## What this means for our workspace

Every isolation/scoping fix in the fleet must audit its fallback paths.
The immediate action item: fix C-1 in `/todo` scanners (change `else
sessions_root` to `return None` — a 1-line fix tracked in the fleet-wide
handoff). The broader action: when reviewing ANY fix that adds filtering,
isolation, or scoping, the reviewer must check the fallback path holds
the same contract. This applies to session resolution, auth checks, path
validation, and data filtering across all skills.

## Receipts

- `C:/Users/brsth/.grok/skills/todo/__lib/scanners/common.py:88-90` — the
  `else sessions_root` fallback that defeats workspace scoping
- `C:/Users/brsth/.grok/skills/todo/__lib/scan_transcript.py:71-74` —
  identical duplicated fallback
- Review findings: `P:/.artifacts/console_627ecc81-a113-444b-a745-4ff510d4da72/grok-review/full-session-scope/20260810-185819/findings.json` — C-1 (HIGH, verified)
- Empirical evidence: 2680 `chat_history.jsonl` files under `sessions_root`
  across 11+ workspace prefixes (verified by correctness specialist)

## Related patterns

- [[caller-context-as-parameter-not-callee-discovery]]: a different class
  of fix-undermining — over-engineering the wrong layer. Here the fallback
  is a simpler version of the same class: the fallback relaxes the contract
  the primary establishes.
- [[multi-terminal-isolation-stale-data-immunity]]: the baseline requirement
  this fix was supposed to meet. The fallback path violates it.
- [[invariants-beat-environment-comfort]]: keeping dead fallbacks "for
  forward compatibility" is the same class — the code defends against a
  scenario that doesn't apply, at the cost of the actual contract.

## Falsifier

This concept is wrong if: the fallback path is genuinely needed (e.g., a
multi-workspace search is intentional for some use case), or if the
fallback includes its own isolation that matches the primary's contract.
On this host, the fallback to `sessions_root` serves no purpose — the
scanner should only ever see this workspace's sessions.

## Auto-related

- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[tool-fallbacks]]
- [[web-search-tool-routing]]
- [[youtube-workspace-sidebar-extension-build-research]]
- [[nvidia-vram-management-for-local-llm-inference]]

