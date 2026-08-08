# Grok fleet benchmark normalization — 2026-08-06

Status: evidence report only. No routing change is made by this report.

## Scope and authority

This report normalizes the current Grok model-fleet evidence for use by the
Codex-to-Pi selector. The authoritative inputs are:

- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json`
- `P:/docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md`
- `C:/Users/brsth/.grok/skills/model-benchmark/SKILL.md`
- `P:/packages/codex-external-delegation/src/model-selector.mjs`
- `C:/Users/brsth/.cache/opencode/fleet-quota-cache.json` for the current
  dynamic quota snapshot only

The registry was written by `model-benchmark` through `registry_writer.py`;
its recorded provenance is `2026-08-06T04:18:05Z`. The quota cache used here
was updated at `2026-08-07T01:02:46Z`.

Transport labels have deliberately different meanings:

| Label | Meaning | Use in Codex-to-Pi routing |
|---|---|---|
| `PI` | Pi CLI dispatch | Directly relevant |
| `OC` | OpenCode CLI dispatch | Evidence for the explicit OpenCode mode; not automatic fallback |
| `HTTP` | Direct provider/API benchmark | Useful provider/model evidence, but not a worker-harness latency |
| `spawn` | Grok Build native `spawn_subagent` | Grok Build evidence only; not a Codex/Pi route |

In particular, `spawn` must not be interpreted as Pi latency. It is included
only to preserve what Grok Build measured for its own native delegation path.

## Normalization rules

The registry has 20 direct model entries and 23 non-empty lane rows across
coding, reasoning, mechanical, and critic lanes. A model can intentionally
have different latency records in different lanes.

The primary table below follows the current Codex selector's effective lookup:
it merges the direct model entry with the first matching lane row. This makes
the table reproduce current selector behavior, while the lane table preserves
all role-specific records. Direct-only models use their direct record.

Each path value is the arithmetic mean of the available dispatch battery
tasks (`probe`, `reasoning`, `code-gen`, `structured`, `multi-step`,
`tool-call`); the parenthesized value is `available tasks / 6`. Missing values
are not treated as zero. Spawn commonly has only a `probe` measurement, so its
average is not comparable to a complete PI/OC average.

Quality values are the registry's reported quality scores, generally from the
HTTP quality benchmark. They are not evidence that quality is identical across
PI, OpenCode, HTTP, and Grok spawn.

## Full direct-model matrix

| Model slug | Provider | Lanes / tier | PI avg (s) | OC avg (s) | HTTP avg (s) | Grok spawn avg (s) | HTTP quality | Current quota snapshot | Lane rows | Lane conflicts |
|---|---|---|---:|---:|---:|---:|---|---|---:|---|
| `cohere-north-mini-code` | cohere | coding / 1 | 11.5 (6/6) | 31.0 (6/6) | 8.9 (5/6) | 32.1 (5/6) | — | 0% rem | 1 | none |
| `or-ling-3-flash-free` | openrouter | coding, reasoning, mechanical / 1 | 5.8 (6/6) | 23.3 (6/6) | 2.5 (6/6) | 8.0 (1/6) | 1.00 (13/13) | $23.15 balance | 3 | PI, OC, HTTP |
| `nim-openai-gpt-oss-20b` | nim | coding, mechanical, critic / 1 | 5.3 (6/6) | 12.0 (6/6) | 1.1 (6/6) | 7.5 (1/6) | 1.00 (13/13) | static; no published limit | 3 | PI, OC, HTTP |
| `minimax-m3` | minimax | coding, mechanical / 2 | 5.4 (6/6) | 20.8 (6/6) | 2.7 (6/6) | 16.0 (5/6) | 0.85 (13/13) | 99% rem | 2 | PI, OC, HTTP |
| `zen-deepseek-v4-flash-free` | zen | coding, reasoning, critic / 2 | 6.5 (6/6) | 25.5 (6/6) | 6.4 (6/6) | 4.0 (1/6) | 1.00 (13/13) | static; no published limit | 3 | PI, OC, HTTP |
| `zen-north-mini-code-free` | zen | coding / 2 | 12.5 (6/6) | 31.7 (6/6) | 17.7 (5/6) | 13.1 (1/6) | 1.00 (13/13) | static; no published limit | 1 | none |
| `glm-5-2` | zai | coding / 2 | 9.5 (6/6) | 25.1 (6/6) | 4.3 (6/6) | 5.8 (1/6) | 0.92 (13/13) | 75% rem | 1 | none |
| `nvidia-nemotron-3-ultra` | nvidia | reasoning / 1 | 8.9 (6/6) | 28.2 (6/6) | 3.2 (6/6) | — (`serde_broken`) | 1.00 (13/13) | static; ~40 RPM soft limit | 1 | none |
| `or-arcee-ai-trinity-large-thinking` | openrouter | reasoning / 2 | 5.6 (6/6) | 16.9 (6/6) | 2.5 (6/6) | 3.4 (1/6) | 0.77 (13/13) | $23.15 balance | 1 | none |
| `cohere-command-a-reasoning` | cohere | reasoning / 2 | 6.6 (6/6) | 25.6 (6/6) | 0.8 (6/6) | 10.6 (5/6, `context_overrun`) | — | 0% rem | 1 | none |
| `cohere-command-a-plus` | cohere | reasoning / 2 | 5.9 (6/6) | 20.4 (6/6) | 1.6 (6/6) | 9.5 (5/6) | 1.00 (5/5) | 0% rem | 1 | none |
| `nvidia-nemotron-3-super-120b` | nvidia | mechanical / 2 | 7.5 (5/6) | 22.4 (6/6) | 6.4 (6/6) | 5.3 (1/6) | 0.92 (13/13) | static; ~40 RPM soft limit | 1 | none |
| `zen-big-pickle` | zen | mechanical / 2 | 5.7 (6/6) | 21.1 (6/6) | 2.5 (6/6) | 4.6 (1/6) | 0.92 (13/13) | static; no published limit | 1 | none |
| `go-deepseek-v4-pro` | opencode-go | — | — | — | — | — | — | 100% rem | direct | none |
| `go-deepseek-v4-flash` | opencode-go | — | — | 5.6 (6/6) | — | — | — | 100% rem | direct | none |
| `go-kimi-k2-7-code` | opencode-go | — | — | — | — | — | — | 100% rem | direct | none |
| `go-kimi-k3` | opencode-go | — | — | — | — | — | — | 100% rem | direct | none |
| `nim-deepseek-ai-deepseek-v4-flash` | nim | coding, reasoning, critic / 2 | 8.6 (6/6) | 29.8 (6/6) | 5.5 (6/6) | 6.7 (1/6) | 1.00 (13/13) | static; no published limit | 3 | PI, OC, HTTP |
| `nim-deepseek-ai-deepseek-v4-pro` | nim | — | 8.2 (6/6) | 16.8 (6/6) | 10.2 (6/6) | 8.8 (1/6) | 1.00 (2/2) | static; no published limit | direct | none |
| `mistral-medium-latest` | mistral | — | — | 44.8 (4/6) | — (`context_overrun`) | 1.00 (13/13) | static; free tier | direct | none |

## Role-specific lane records

These are retained because collapsing them would erase the benchmark's role
conditioning. The `spawn` column remains Grok Build-only evidence.

| Lane / tier | Model | PI avg (s) | OC avg (s) | HTTP avg (s) | Grok spawn avg (s) | Quality |
|---|---|---:|---:|---:|---:|---|
| coding / 1 | `cohere-north-mini-code` | 11.5 | 31.0 | 8.9 | 32.1 | — |
| coding / 1 | `or-ling-3-flash-free` | 5.8 | 23.3 | 2.5 | 8.0 | 1.00 (13/13) |
| coding / 1 | `nim-openai-gpt-oss-20b` | 5.3 | 12.0 | 1.1 | 7.5 | 1.00 (13/13) |
| coding / 2 | `minimax-m3` | 5.4 | 20.8 | 2.7 | 16.0 | 0.85 (13/13) |
| coding / 2 | `zen-deepseek-v4-flash-free` | 6.5 | 25.5 | 6.4 | 4.0 | 1.00 (13/13) |
| coding / 2 | `nim-deepseek-ai-deepseek-v4-flash` | 8.6 | 29.8 | 5.5 | 6.7 | 1.00 (13/13) |
| coding / 2 | `zen-north-mini-code-free` | 12.5 | 31.7 | 17.7 | 13.1 | 1.00 (13/13) |
| coding / 2 | `glm-5-2` | 9.5 | 25.1 | 4.3 | 5.8 | 0.92 (13/13) |
| reasoning / 1 | `or-ling-3-flash-free` | 7.4* | 30.1* | 2.8 | 8.0 | — |
| reasoning / 1 | `nvidia-nemotron-3-ultra` | 8.9 | 28.2 | 3.2 | — | 1.00 (13/13) |
| reasoning / 1 | `zen-deepseek-v4-flash-free` | 16.3* | 30.7* | 4.9* | 4.0 | — |
| reasoning / 1 | `nim-deepseek-ai-deepseek-v4-flash` | 14.8* | 21.0* | 4.6* | 6.7 | — |
| reasoning / 2 | `or-arcee-ai-trinity-large-thinking` | 5.6 | 16.9 | 2.5 | 3.4 | 0.77 (13/13) |
| reasoning / 2 | `cohere-command-a-reasoning` | 6.6 | 25.6 | 0.8 | 10.6 | — |
| reasoning / 2 | `cohere-command-a-plus` | 5.9 | 20.4 | 1.6 | 9.5 | 1.00 (5/5) |
| mechanical / 1 | `or-ling-3-flash-free` | 7.4* | 30.1* | 2.8 | 8.0 | — |
| mechanical / 1 | `nim-openai-gpt-oss-20b` | 7.3* | 27.4* | 1.7* | 7.5 | — |
| mechanical / 1 | `minimax-m3` | 9.0* | 26.7* | 2.0* | 16.0 | — |
| mechanical / 2 | `nvidia-nemotron-3-super-120b` | 7.5* | 22.4 | 6.4 | 5.3 | 0.92 (13/13) |
| mechanical / 2 | `zen-big-pickle` | 5.7 | 21.1 | 2.5 | 4.6 | 0.92 (13/13) |
| critic / 1 | `zen-deepseek-v4-flash-free` | 16.3* | 30.7* | 4.9* | 4.0 | — |
| critic / 1 | `nim-deepseek-ai-deepseek-v4-flash` | 14.8* | 21.0* | 4.6* | 6.7 | — |
| critic / 1 | `nim-openai-gpt-oss-20b` | 7.3* | 27.4* | 1.7* | 7.5 | — |

`*` indicates that the lane record did not contain all six battery tasks; the
reported average is over the available five (or fewer) tasks.

## What this changes in our understanding

1. The full fleet is materially broader than the six models currently in
   `MODEL_CANDIDATES` in `src/model-selector.mjs`. The current Codex pool does
   not expose GPT OSS, Ling, Arcee, Cohere, Zen Big Pickle, Nemotron Super,
   DeepSeek v4 Pro, or the Kimi models as candidates.
2. Pi speed alone would favor different models by role. For example, the
   coding lane is led by GPT OSS and MiniMax in this snapshot, while the
   reasoning lane has Arcee and Cohere Command A Plus near the front. That is
   evidence, not a routing decision: role fit, quality, quota ownership,
   configuration, context, and provider failure history still gate use.
3. The old handoff's OpenCode Go exhaustion is historical. The current quota
   cache reports OpenCode Go at 100% remaining. This does not retroactively add
   missing Pi benchmark data for the Go models; it only changes current
   availability evidence.
4. The registry is not yet a single clean canonical table. Five multi-lane
   models have conflicting lane-specific latency records, and the selector's
   first-lane lookup hides those conflicts. Any adaptive routing work should
   consume an explicit role-specific record, not blindly take the first row.
5. Grok `spawn` evidence cannot be used to rank Codex Pi models. It is valuable
   for Grok's own `/go`, `/check`, `/review`, and `/tp` paths, including its
   known serialization/context failures, but it answers a different runtime
   question.

## Decision and next action

Decision: keep routing unchanged for now. This report is evidence collection,
not adaptive routing.

The next implementation-worthy step is a small registry adapter that returns
role-specific, transport-specific records with provenance and freshness, then
expands the Codex candidate catalog only after each added model has a Pi
configuration check and a live Pi smoke. It must keep Grok `spawn` metadata in
its own field and must not treat Grok Build availability as evidence that the
Codex Pi path works.

