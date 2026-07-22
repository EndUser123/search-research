---
title: "Gemini API vs agy CLI: when to use which"
created: 2026-07-21
source: session-2026-07-21
tags: [gemini, agy, antigravity, api, cli, routing, fleet, grok-build, second-opinion]
summary: >
  On this host two Gemini surfaces exist: the Gemini API (OpenAI-compat, called via
  Grok picker / spawn_subagent model= slug) and the agy CLI (Antigravity, invoked via
  /agy skill or shell). Use the API for cheap parallelizable inference inside a Grok
  wave (Flash lane members, multimodal capability). Use agy when you want a full agent
  harness — tools, sandbox, long session, Google subscription identity, independent
  second opinion. Same model family, different harness; not interchangeable.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/gemini-google-api-models-2026-07
    type: refines
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: related
  - target: wiki/concepts/llm-council-and-model-fusion
    type: related
  - target: wiki/concepts/multi-agent-correlated-errors
    type: related
---

# Gemini API vs agy CLI: when to use which

## The two surfaces

| Surface | What it is | How Grok invokes it | Identity / quota |
|---------|------------|---------------------|------------------|
| **Gemini API** | `generativelanguage.googleapis.com/v1beta/openai` (OpenAI-compat) + native Generative Language API | Picker (`/model gemini-3.6-flash`), `spawn_subagent(model=...)`, `run_terminal_command` curl/Python | `GEMINI_API_KEY` in `P:/.env` (3 keys). **Free-tier per-model quotas**; Pro class often limit=0 |
| **agy CLI** | Antigravity binary (`~/.gemini/antigravity-cli/`, formerly Gemini CLI) | `/agy` skill (conductor) or shell `agy -p … --dangerously-skip-permissions --print-timeout 10m` | Google login / AI Pro-Ultra subscription; separate quota pool from API key |

Both ultimately call Gemini models. The **harness** differs, not the weights.

## Authority sources (scored)

| Source | Score | Why |
|--------|-------|-----|
| [Google Cloud: Choosing Antigravity or Gemini CLI](https://cloud.google.com/blog/topics/developers-practitioners/choosing-antigravity-or-gemini-cli) (2026-02-04) | 12 | Official Google comparison; pre-sunset of Gemini CLI |
| [Google Developers Blog: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/) (2026-05-19) | 12 | Official sunsetting + migration statement |
| [The New Stack: Gemini CLI vs Antigravity](https://thenewstack.io/gemini-cli-antigravity-replacement/) (2026-06-20) | 10 | Practitioner write-up; verifies write/tool capability split |
| [augmentcode.com comparison](https://www.augmentcode.com/tools/google-antigravity-vs-gemini-cli) | 9 | Third-party; corroborates Google's framing |
| Host skill `~/.grok/skills/agy/SKILL.md` | 11 | Verified conductor contract on this host |

## Quick decision table

| You want… | Use | Why |
|-----------|-----|-----|
| Cheap parallel inference inside a Grok wave (panel member, spawn lane, mechanical work) | **Gemini API** (picker / `spawn_subagent`) | Latency, cost, no extra CLI process, Grok owns synthesis |
| Multimodal in-process (image/audio/video understanding, embeddings) | **Gemini API** | Native API surface; agy adds harness overhead you don't need |
| Independent second opinion / cross-family critic on a hard decision | **`/agy`** | Conductor contract (assignment adequacy, run record, outcome labels); harness is the product |
| Long-horizon agent task (multi-file refactor, research with tool loops, sandboxed code execution) | **`/agy`** | Antigravity has full agent harness: tools, repo map, skills, hooks |
| Bulk scaffolding delegated to Gemini with write access | **`/agy`** (write pipeline: dedicated branch/worktree + conductor `git diff` review) | API is inference-only; agy is the write-capable surface |
| Google subscription quota (AI Pro/Ultra) instead of API free-tier | **`/agy`** | Separate identity → separate quota; API key tied to free-tier limits |
| Headless / CI / automation script | **Gemini API** (or agy `-p` mode if you want agent harness) | API is simpler for pure inference; agy `-p` for harness in a pipe |
| Streaming token-level UX | **Gemini API** | agy `-p` is single-shot text blob |
| Antigravity-native features (Agent Skills, Hooks, Subagents, Extensions, repo maps) | **`/agy`** | API does not expose these |

## Do's and don'ts

### Do

- **Default to the API** for inference inside Grok pipelines. It's a model slug, not a separate process.
- **Default to `/agy`** when the value is a different agent harness, not just a different model. Second opinions, cross-family critique, write-capable delegation all want the harness.
- **Pass absolute paths** to `/agy` and put `--model` **before** `-p` (flag order traps verified in `agy/SKILL.md`).
- **Use `/agy` for research** where the conductor contract (assignment adequacy, outcome labels, independent verification) is the structural guarantee.
- **Treat agy output as advisory.** Conductor verifies material claims before adopting.
- **Use the API for cross-family council diversity.** Cheaper than a CLI round-trip when you only need the model's answer.

### Don't

- **Don't** use `/agy` for a single fact Grok can answer from session context. Round-trip cost exceeds value (skill's own `DELEGATION_NOT_WORTHWHILE`).
- **Don't** expect JSON or structured output from `agy -p`. It's a text blob.
- **Don't** trust agy's self-reported "tests passed" without re-running gates locally.
- **Don't** conflate the two quota pools. If Gemini API Pro free-tier is exhausted, that does not mean agy is exhausted (and vice versa).
- **Don't** run agy without `--dangerously-skip-permissions` headless; it hangs or fails closed.
- **Don't** use agy for parallel fan-out inside a `/go` wave. Use `spawn_subagent(model=gemini-*)` — one process, many slugs.
- **Don't** route write authority through the API. It is read/inference only on this host.

## General API-vs-CLI pattern (transfers beyond Gemini)

The same shape applies to MiniMax (`minimax-m3` API vs `mmx` CLI), OpenAI (API vs `codex`), and others.

| Axis | API / MCP / picker | CLI (`agy`, `mmx`, `codex`) |
|------|--------------------|-----------------------------|
| Latency | Lowest — direct inference | Process spawn + harness boot |
| Cost | Token-priced | Same tokens + process overhead |
| Harness | None — model only | Tools, sandbox, repo map, skills, hooks |
| Write authority | None (on this host) | Possible with explicit auth + review pipeline |
| Independent quota | Per provider key | Often subscription-tier, separate pool |
| Conductor contract | None — caller owns | Skills like `/agy`, `/codex`, `/mmx` add run records, outcome labels, verification gates |
| Best for | Parallel fan-out, lane members, in-process inference | Second opinion, cross-family critique, write delegation, agent loops |
| Streaming UX | Native | Usually single-shot `-p` |

**Rule of thumb:** API when you want the model's answer; CLI when you want a different agent's process.

## Failure triage (host-specific)

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `spawn_subagent(model="gemini-*")` → 401 quota | Free-tier Pro limit=0 | Switch to Flash/Lite, or escalate to agy (subscription quota) |
| agy hangs | Missing `--dangerously-skip-permissions` | Re-run with mandatory flags |
| agy `--model` sent as prompt | Flag order wrong (`-p` consumes next arg) | Put `--model "NAME"` before `-p` |
| agy quota exhausted | Google AI Pro/Ultra cap hit | Switch to API (different pool) or pause delegation; `INVOCATION_FAILED`, no blind retry |
| Gemini API 429 under parallel load | Free-tier rate window | Serialize or use `minimax-search`/`firecrawl` for search; switch code lane to Ornith/DiffusionGemma |

## Cross-host note

This page is `host: grok`. Under Claude Code, `/agy` exists as a plugin skill (`cc-skills-ai-api/skills/agy`) and the conductor contract is the same. The Gemini API surface (OpenAI-compat) is host-agnostic.

## Relationship to existing concepts

- **Refines** [[gemini-google-api-models-2026-07]] — adds the "which surface" decision the catalog doesn't address.
- **Related** [[model-picker-as-failover-not-router]] — API/picker is the recommendation layer; `/agy` is a separate harness invocation, not a second router.
- **Related** [[llm-council-and-model-fusion]] — Fusion panels can use API Gemini as a budget member; `/agy` is the second-opinion path when the conductor contract matters.
- **Related** [[multi-agent-correlated-errors]] — cross-family diversity via API (Gemini Flash in a panel) or via CLI (`/agy`) achieve the same decorrelation goal through different surfaces.

## Sources

- https://cloud.google.com/blog/topics/developers-practitioners/choosing-antigravity-or-gemini-cli (2026-02-04)
- https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ (2026-05-19)
- https://thenewstack.io/gemini-cli-antigravity-replacement/ (2026-06-20)
- https://www.augmentcode.com/tools/google-antigravity-vs-gemini-cli
- `~/.grok/skills/agy/SKILL.md` (verified conductor contract on this host)
- Live probes this session: Gemini API OpenAI-compat chat (see `gemini-google-api-models-2026-07.md`)

## Staleness

Google is actively migrating Gemini CLI → Antigravity CLI (announced 2026-05-19; ongoing through 2026). Re-check official comparison if >3 months old. agy skill flag knowledge is verified per-session in `~/.grok/skills/agy/SKILL.md`.

## Auto-related

- [[solo_operator_adr_best_practices]]
- [[plan-then-execute-pattern]]

