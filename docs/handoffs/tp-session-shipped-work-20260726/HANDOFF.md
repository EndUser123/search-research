---
thread_id: tp-pool-composition-review-20260723
parent_handoff_path: P:\docs\handoffs\tp-pool-composition-review-20260723\HANDOFF.md
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
current_terminal_id: console
produced_at: 2026-07-26T18:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: a60238f
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8b39-95e3-7121-a8de-4e3f117e511a\chat_history.jsonl
---

# Handoff: /tp improvement session shipped work + pool investigation update

## Objective (one sentence)

Session 019f8b39 shipped /tp improvements (adversarial domain + VS + recap + plan-writer consolidation), and the pool composition investigation needs updating because the pool has been significantly rewritten since the original handoff.

## Status

**OPEN** — pool investigation still needed, but the pool state has changed substantially since the original handoff.

## What this session shipped

| Artifact | Repo | Commit | Description |
|---|---|---|---|
| /web mandatory fan-out recipe | `~/.grok/` | `cab6bf7` | NON-NEGOTIABLE recipe (minimax + web-search-prime + DDG) |
| tool-fallbacks.md nemotron failure row | `~/.grok/` | `5ced2df` | Real-prompt serialization error documented |
| tp-pool-composition handoff (original) | `P:/` | `e981ab7` | Investigation handoff |
| tool-fallbacks.md + handoff update | `P:/` | `5b7b4bc` | Updated for ccr-ornith removal |
| /tp session-state carve-out | `~/.grok/` | `1b16759` | Session-state questions route inline |
| plan-writer consolidated skill | `~/.grok/` | `5d51031` | Merged writing-plans + /plan |
| plan-writer rename + /plan disable | `~/.grok/` | `001d9ae` | Renamed to plan-writer, disabled old copies |
| /tp recap variant | `~/.grok/` | `496ff9c` | Mid-session status + open decisions |
| /tp 3-layer improvement spec (adversarial + VS + comparison) | `~/.grok/` | `a60238f` | All 3 independently-revertible layers |
| tp-parallel-improvement-solution-space wiki | `P:/` | (in tree) | Research findings on parallel /tp |
| plan-execution-consolidation-question wiki | `P:/` | `89bf151` | Evidence-gated, not urgent |
| tp-frame-mutation-verbalized-sampling spec (rev 2) | `P:/` | `e9b9d3c` | Post-red-team revised design |

## Pool state has changed (update to original handoff)

The original handoff (2026-07-23) documented pool = `[nemotron, glm-5-2, mimo, parent]` with nemotron failing on real prompts. **The pool has since been substantially rewritten by concurrent sessions:**

**Current pool (from SKILL.md, verified 2026-07-26):**
- Pool is now **criteria-based**, not a hardcoded list
- `nvidia-nemotron-3-ultra` — **RE-PROMOTED 2026-07-26** (streaming serde fix: `stream_tool_calls = false`)
- `glm-5-2` — reliable subscription fallback
- `nvidia-inkling` — NEW member (free, 2.9s, spawn-only)
- `go-mimo-v2-5` — reliable cross-family
- `go-kimi-k3` — **HARD EXCLUSION** (cost + reliability policy)
- Parent-inherited — weakest lens, last resort

**What this means for the investigation:**
1. The original "why isn't the choice random?" question may be partially answered — the criteria-based pool adapts membership. But selection is still deterministic within the pool.
2. The nemotron serialization issue was root-caused and fixed (streaming serde null-typed-as-u32). The original handoff's "nemotron unreliable on real prompts" finding is now stale.
3. The pool has grown from 4→5 active members (inkling added).

## What remains for the pool investigation

1. **Deterministic vs random selection** — still open. The pool is criteria-based now, but selection within the pool is still "try in order, first success wins."
2. **Pool size sweet spot** — 5 active members (was 4). Is this enough diversity?
3. **Real-prompt probe of inkling** — it's new to the pool; hasn't been /tp-tested on a real critique.
4. **Pool activation telemetry** — the `log_spawn.py` telemetry was added but needs accumulated data before patterns emerge.

## Read-first list (ordered)

1. This handoff
2. Original handoff: `P:\docs\handoffs\tp-pool-composition-review-20260723\HANDOFF.md`
3. `/tp/SKILL.md` Step 2 (current pool section — criteria-based)
4. `~/.grok/tool-fallbacks.md` (current spawn_subagent compatibility)
5. Wiki: `tp-parallel-improvement-solution-space.md` (solution space research)

## Last user message (verbatim)

> "write the required handoff / do a web run / /tp review execute-plan/executing-plans consolidation"

## Other outstanding streams

- **execute-plan/executing-plans consolidation** — wiki concept filed (`plan-execution-consolidation-question.md`), evidence-gated, not urgent
- **VS layer validation** — the 3-layer /tp improvement (adversarial + VS + comparison) has never been exercised on a live critique; first real `/tp` run will produce the first VS data
- **/web mandatory fan-out validation** — recipe shipped but never exercised on a fresh `/web` invocation
