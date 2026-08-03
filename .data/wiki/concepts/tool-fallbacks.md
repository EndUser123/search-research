---
title: "Tool fallbacks: known-broken combinations and CLI fallbacks"
slug: tool-fallbacks
created: 2026-07-18
updated: 2026-08-01
tags: [tool-fallbacks, model-pool, spawn-subagent, cli-fallback, mcp, rate-limit, transferable-technique]
host: grok
summary: >
  Fast-decision index of known-broken model×tool combinations and CLI fallbacks.
  Records observed failures only (optimistic bias: assume working unless listed).
  Each entry cross-references wiki authority for root cause. When this table
  and a wiki concept disagree, the wiki concept wins — update this table.
---

# Tool fallbacks: known-broken combinations and CLI fallbacks

> Multi-model environment. Different models have different tool availability.
> This manifest records **known-broken** combinations only (optimistic bias:
> assume a tool works unless listed here). CLI fallbacks (`mmx`, `agy`, `codex`)
> work regardless of model — they're external processes invoked via shell.

## CLI fallback table

When a built-in tool fails (429, 401, "not available", silent no-op, etc.), use
the CLI equivalent **before retrying the built-in**:

| Built-in | CLI fallback | Notes |
|---|---|---|
| `web_search` | `mmx search query "<q>"` | MiniMax API quota — separate pool from Grok team rate limit |
| `image_gen` | `mmx image generate "<prompt>"` | MiniMax image API |
| `image_edit` | `mmx image ...` (check `mmx image --help`) | TBD — verify subcommand |
| vision / image understanding | `mmx vision describe <path>` | MiniMax vision API |
| speech / TTS | `mmx speech synthesize ...` | MiniMax TTS (cloud) |
| speech / TTS (local) | `speak "file.txt" --voice jon --emotion excited` | Parler-TTS local (`P:\scripts\speak.cmd`, Python 3.12 venv at `P:\packages\tts-reader\`) |
| code execution / second opinion | `agy -p "<prompt>"` or `codex exec "<cmd>"` | External CLIs; independent of current model |
| research / deep search | `agy -p "<prompt>"` or `mmx search query` | Both work; agy gives Gemini's lens |
| video generation | `mmx video generate ...` | MiniMax video API |

**Reflex pattern:** built-in fails → check this table → run CLI equivalent → continue. Don't retry the built-in more than once.

**Entry classification (mandatory on every entry):**

Every entry must classify the failure type and specify when to re-test:

| Type | Definition | Examples | Re-test rule |
|---|---|---|---|
| **STRUCTURAL** | Won't self-heal. Architecture/format incompatibility, hardware cap, API design change. | Nemotron serde format incompatibility, Groq TPM limit, slug routing mismatch | Re-test only after the underlying system changes (serde update, config change, provider API revision). State the trigger: "Re-test after: <event>." |
| **TRANSIENT** | Will self-heal. Rate-limit window, credit exhaustion, intermittent outage, CDN block. | Reddit API rate-limit, firecrawl credits, Cloudflare intermittent, 429 under parallel load | **Re-test every session.** Try once before skipping. State: "Re-test: try once each session before falling back." If it works, remove the entry. |

**The staleness rule:** a TRANSIENT entry that hasn't been updated in 7+ days should be re-tested before being trusted. If the re-test passes, remove the entry. STRUCTURAL entries stay until their stated re-test trigger fires.

**Why this matters:** without classification, transient failures (Reddit rate-limit) get treated identically to structural failures (Nemotron serde). Future sessions skip working tools based on stale entries — worse than the original problem.

## Known-broken combinations

**Optimistic bias:** absence from this table means "assume working." Don't pre-emptively mark tools broken without evidence. Each row has: symptom (1 line), workaround (1 line), wiki authority (for full detail).

### spawn_subagent exclusions (model cannot be spawned)

These models are **excluded from all auto-pools and spawn_subagent dispatch**. They may work for direct API calls or CLI invocation — see the wiki authority for each.

**IMPORTANT:** Each entry below must cite a specific error receipt. The former `serde_broken` list in fleet-models.json was cleared 2026-08-01 after testing proved all 10 entries were false positives (missing prerequisite services, quota exhaustion misclassified as serde, slug format mismatch). New entries require: (1) the actual error text, (2) the access path tested, (3) whether it's transient or permanent.

| Model(s) | Symptom (1 line) | Workaround | Wiki authority |
|---|---|---|---|
| **All Groq models** (`groq-gpt-oss-120b`, `groq-llama-3-1-8b-instant`, `groq-qwen3-6-27b`) | HTTP 413 TPM limit (8000 cap, ~54K system prompt). Fails instantly (0.7s, 0 tool calls). | **NOT IN ANY POOL.** Direct API only for short tasks (<6K tokens total). | [[groq-free-tier-tpm-limit-6000]], [[coding-model-pool-tier-1-tier-2]], [[model-benchmark-testing-quirks]] Quirk 5 |
| **go-kimi-k3** + **go-kimi-k2-7-code** | Spawn-path transport/header failure (not `top_p`, not body shape — unresolved). Both fail identically. K3 also costs ~20% monthly OpenCode-Go quota per spawn test. | **NOT IN ANY POOL.** Manual/deliberate only (`--model go-kimi-k3`). Direct API works. Testing deferred until ~2026-08-07. | [[model-tool-calling-capability-matrix]] § go-kimi-k3 |
| **nvidia-nemotron-3-ultra** (NVIDIA direct) | Serde error: `null, expected u32` on `service_tier`/`system_fingerprint`/`logprobs`. Affects **tool-grounded spawn only**; trivial no-tool prompts pass. Verified 2026-07-26 via dual cross-transport test (Grok Build FAIL, OpenCode PASS, PI PASS — same model, same prompt). | **Never spawn for tool-grounded work.** Use opencode CLI (`opencode run -m opencode/nemotron-3-ultra-free`) or PI CLI. `stream_tool_calls=false` in all 4 config sections as defense-in-depth. | [[model-tool-calling-capability-matrix]] § Nemotron routing preference |
| **zen-nemotron-3-ultra-free** (OpenCode Zen) | Serde error: `missing field id`. Same class as NVIDIA direct. | **Never spawn.** Same routing as above. | Same as above |
| **or-nemotron-ultra-free** (OpenRouter) | Works but slow (19.2s). | **Explicit-only spawn** — only when opencode/PI unavailable AND operator approves OpenRouter. | Same as above |
| `gemini-2` | HTTP 404 "model does not exist or your team does not have access." Listed in catalog but 404 on actual call. | Use `grok-4.5` for critical-friend spawns. Probe before committing. | (this table only — no wiki concept yet) |
| **mistral-medium-latest** | HTTP 422 context-too-large on spawn_subagent. | **NOT IN ANY POOL.** Direct API only. | (fleet-models.json spawn_broken) |

### spawn_subagent limitations (model spawns but has constraints)

| Model | Symptom | Workaround | Wiki authority |
|---|---|---|---|
| **MiniMax-M3** | `max_tokens_truncation` on large structured output tasks (multi-file review + JSON write). | Decompose into smaller pieces (per-file specialists, two-pass findings). Small tasks fine. | `/review` SKILL.md Step 4 |
| **MiniMax-M3** (`resume_from` after 2+ rounds) | `max_tokens_truncation` — accumulated transcript context exceeds output budget. | Launch fresh subagent instead of resuming when round_count ≥ 2. | `/design` Step 5 |
| **MiniMax-M3** (`finish_reason: "error"` on specific prompts) | Grok Build deserializer fails: `unknown variant 'error', expected one of 'stop', 'length', ...`. M3 returned `finish_reason: "error"` because the model errored internally on one specific prompt. NOT a systemic serde incompatibility — M3 works fine on other prompts (7 successful spawns in same session). | Retry with a different prompt or smaller context. Do NOT add to serde_broken. Error classifier now distinguishes this (transient) from true serde (field type mismatch). | This session, hook fix commit 40bce90 |
| **nvidia-inkling** (as interactive/primary model) | Produces one-word garbage ("UBS", "Savings") via Grok Build interactive dispatch. Works fine via spawn_subagent delegation + direct API. | **Do not use as interactive/primary.** DO use as spawn delegation target (/tp pool, /check verifier). | [[model-benchmark-testing-quirks]] |
| **nvidia-diffusiongemma-26b** | Empty content via spawn_subagent (parameter conflict with thinking mode). Works via direct API. | Use `P:/.agents/scripts/models/dgemma_read.py` for file reads. Never spawn. | [[diffusiongemma-direct-api-howto]] |
| **or-ling-3-flash-free** (parallel dispatch) | 429 rate limit after 3+ concurrent agents (OpenRouter 20 RPM shared across all free-model calls). 4 of 7 agents failed in session 2026-08-01. | **Use `pick_model.py --count N` for diverse providers.** Don't reuse the same free-tier model for all parallel agents. | [[coding-model-pool-tier-1-tier-2]], [[agent-consolidation-in-parallel-workflows]] |
| **or-ling-3-flash-free** (single-agent, non-completion) | Ran 375s / 53 tool calls without completing in session 019fb933 /tp critique. Same model also failed twice as `fmea` (115s, 207K tokens) and `friction` (39s, 626K tokens) in close-check Phase 2/3 of session 019fb933 -- `state: failed`, no successful output. | **Do not dispatch or-ling-3-flash-free as a single critical-path agent.** Use it only as a low-stakes parallel filler or after confirming a healthy recent run. | [[pick-model-stale-spawn-notes-failure-pattern]], [[agent-consolidation-in-parallel-workflows]] |

### Session-attested new failures (2026-08-01 close-check sweep)

Provisional entries -- each must be re-tested before promoting to "Known-broken" tier.

| Model(s) | Symptom | Workaround | Wiki authority |
|---|---|---|---|
| **nim-deepseek-ai-deepseek-v4-flash** | Serde failure on Grok Build (slug has `ai-` prefix, distinct from `nim-deepseek-v4-flash` which PASSED 4s in the [[serde-broken-false-positive-sweep-20260801]]). Same provider, different slug -- likely a routing-table mismatch between NIM aliases. | **Do not dispatch until slug aliasing is investigated.** Use `nim-deepseek-v4-flash` (without `ai-` prefix) if a NIM deepseek variant is needed. | [[serde-broken-false-positive-sweep-20260801]], [[pick-model-stale-spawn-notes-failure-pattern]] |
| **nim-openai-gpt-oss-20b** (pick_model.py returned stale "spawn OK") | Direct spawn PASSED (41s) in [[serde-broken-false-positive-sweep-20260801]], but pick_model.py returned it as spawn-OK during the same session when prior session evidence suggests intermittent failure. Discrepancy suggests pick_model.py spawn_notes may be stale. | **Probe before dispatch.** Run a 1-token no-tool spawn test to verify, OR use a different OpenAI-OSS option. | [[pick-model-stale-spawn-notes-failure-pattern]] |

### web_search rate limiting

| Model | Symptom | Workaround | Wiki authority |
|---|---|---|---|
| **GLM-5.2** (and any model via built-in) | HTTP 429 team rate limit (2/2 RPS fleet-wide, `grok-4.20-multi-agent-0309`). | Serialize searches (~1/sec) OR use `mmx search query` CLI. | [[web-search-tool-routing]], AGENTS.md § Web-search tool selection |
| **MiniMax-M3** (same 429 mechanism) | Same 429 under parallel load. | Same: serialize or `mmx search query`. | Same |
| **web-search-prime** MCP | API Error 1027 `new_sensitive` — content moderation blocks query/results. | Rephrase to avoid trigger words, or use `mmx search query` (different moderation path). | [[web-search-tool-routing]] |

### CLI caller errors (not model bugs)

| Tool | Symptom | Resolution |
|---|---|---|
| mmx CLI (benchmark) | "33% success" was `caller_error` — FileNotFoundError (PATH) + missing `--message` flag. | Model is 100% reliable when called correctly. Resolved in telemetry. |
| codex CLI (benchmark) | "50% success" was `transport_error` — FileNotFoundError (PATH). | Same — reliable when PATH is correct. |

### MCP tool failures (parent-agent tools)

| Tool | Symptom (1 line) | Type | Workaround | Re-test |
|---|---|---|---|---|
| `reddit__search_reddit` | **RESOLVED 2026-08-02** — OAuth credentials wired. Working at 60 QPM. | ~~STRUCTURAL~~ → RESOLVED | Use Reddit MCP directly (browse, search, get_post_details). DDG site-search only if MCP returns 429. | N/A — working |
| `reddit__get_post_details` | **RESOLVED 2026-08-02** — same OAuth fix. Full threads + comments. | ~~STRUCTURAL~~ → RESOLVED | Use Reddit MCP directly. Fallback: DDG or reddit-rss MCP (disabled, re-enable if needed). | N/A — working |
| `firecrawl_scrape` | "Insufficient credits to perform this request" | TRANSIENT (monthly credit refresh) | Use `web_fetch` (built-in) for page content, or DDG for search. Check quota dashboard for current credit count. | Try when quota dashboard shows credits >0 |
| `web_fetch` (Cloudflare-protected sites) | "Just a moment..." on perplexity.ai, pcmag.com, etc. | TRANSIENT (intermittent CDN block) | Use DDG to find blog aggregators or mirrors. Or `firecrawl_scrape` (when credits available). For Reddit: `old.reddit.com` (dying) → switch to RSS MCP. | Try once each session — Cloudflare blocks are intermittent |

## MCP server availability

MCP servers listed at session start may or may not be callable per-model. **Treat the session-start list as a catalog, not a guarantee.** Probe with a cheap no-op before relying on an MCP in a given turn.

| MCP | Status | Notes |
|---|---|---|
| `chrome-devtools` | WORKING via `--autoConnect` (2026-07-31) | Connects to user's real Chrome session. See [[chromium-cdp-websocket-origin-restriction]] for Chrome 136+ setup details. |
| `firecrawl` | WORKING — OAuth-gated MCP, auth resolved 2026-07-19 | 26 tools when live. **Auth flow:** TUI `/mcps` → firecrawl row → `i` → browser OAuth → `~/.grok/mcp_credentials.json`. Verify: `grok mcp doctor firecrawl`. |
| `perplexity` | TBD — known to disconnect mid-session | Observed disconnect 2026-07-18 |
| `minimax-search` | REMOVED 2026-07-28 | Claude compat artifact. Use `mmx search query` + `mmx vision describe` instead. |
| `episodic-memory` | WORKING — fix applied 2026-07-19 | 2 tools. **Caveat:** plugin's `.mcp.json` ships Codex-form relative paths; patched to absolute. Future reinstall reverts patch. |
| `web-search-prime` | DISABLED 2026-07-28 | Uses GLM coding plan quota. Re-enable: remove from `disabled_mcp_servers`, restart. |
| `tasks` | TBD — probe on first use | 6 tools when live |
| `context7` | Typically reliable | Uses `npx`; environment-independent |

## CLI auth + bulk recipes

### `nlm` (NotebookLM CLI) — auth recovery

**Symptom:** `nlm notebook list` returns `✓ Authentication Error`.

**Misleading probe:** `nlm login --check` returns `network_error: ClientAuthenticationError`. Do NOT treat this as expired — it's a probe failure. Verified 2026-07-25.

**Recipe:** `nlm login --profile <name>` — launches Chrome silently via CDP, reuses saved Google login, writes cookies. ~10s, no prompt.

**Default profile:** `codex`. See [[notebooklm-cli-operational-gotchas]] for full auth recovery protocol.

### `nlm` — bulk source add

`nlm source add <nb-id> --youtube u1 --youtube u2 ...` — `--youtube` and `--url` are repeatable for bulk in a single CLI invocation. One call per notebook, not per video. See [[notebooklm-cli-operational-gotchas]].

## How to use this manifest

1. Before spawn_subagent, check **spawn_subagent exclusions** — models listed there CANNOT be spawned.
2. Before relying on a built-in tool, check **Known-broken** for the model you're using.
3. If a tool fails, reflex to the CLI equivalent in the **Fallback table** before retrying.
4. When you observe a new failure, add a row with: symptom (1 line), workaround (1 line), wiki authority (create a wiki concept if the root cause is complex).
5. Bias toward optimism: don't pre-emptively mark tools broken without observed evidence.
6. **Before assigning `model=` to spawn_subagent, read [[coding-model-pool-tier-1-tier-2]] for the current pool.** Do not rely on memory or this table alone — pool membership changes.
7. **For parallel dispatch (3+ agents):** use `python pick_model.py <lane> --count N` to get N models from diverse providers. Don't reuse the same free-tier model for all agents. See [[agent-consolidation-in-parallel-workflows]].
8. Periodically prune entries that no longer reproduce.
9. **Provenance requirement (mandatory — added 2026-08-01):** every new exclusion entry must include the actual error text observed, not just the symptom category. The `PostToolUseFailure_spawn_quota.py` hook now captures error receipts in `learned-serde-broken.json`. If adding an entry manually, cite: (a) the error message, (b) the access path tested (spawn/codex/pi/opencode), (c) whether it's transient or permanent. Entries without receipts are subject to removal during verification sweeps.
10. **Serde vs rate-limit mutual exclusivity (mandatory — added 2026-08-01):** the PostToolUseFailure hook now treats serde and rate-limit as mutually exclusive. A rate-limit error (429, quota, throttle) will NEVER trigger serde-broken learning, even if the error text happens to contain a serde-like substring. This prevents the false-positive class that populated the former serde_broken list.

## Decision context

Moved from `~/.grok/tool-fallbacks.md` to the wiki vault on 2026-08-01 (session 019fba58). Root cause: the file lived outside the wiki vault, so `/wiki` queries and `/www` contradiction checks couldn't surface it. The OpenRouter parallel rate-limit failure (3 agents 429'd) was documented in [[agent-consolidation-in-parallel-workflows]] but never reached tool-fallbacks because nothing connected the two knowledge stores. Moving to the wiki makes it discoverable via `/wiki <query>` and subject to wiki lifecycle tracking.

**serde_broken false-positive sweep (2026-08-01, session 019fb933):** all 10 entries in the former `serde_broken` list in fleet-models.json were tested and found to be false positives. Root causes: (1) missing prerequisite services (codex-bridge not running for GPT models), (2) quota exhaustion misclassified as serde by the PostToolUseFailure hook's overly broad `"Error from provider"` pattern, (3) slug format mismatch (`gpt-5-6-*` dashes vs `gpt-5.6-*` dots expected by codex), (4) inherited labels from unknown prior sessions with no error receipts. The list was cleared. The hook was fixed: `"Error from provider"` removed from SERDE_BROKEN_PATTERNS, serde/rate-limit made mutually exclusive, error receipts now captured in learn_serde_broken().

The `~/.grok/tool-fallbacks.md` file is now a redirect pointer to this concept.

## Cross-references

- [[coding-model-pool-tier-1-tier-2]] — which models pass code-exec benchmarks
- [[agent-consolidation-in-parallel-workflows]] — max 2-3 concurrent agents per free-tier provider
- [[groq-free-tier-tpm-limit-6000]] — Groq exclusion root cause
- [[model-tool-calling-capability-matrix]] — per-model tool-calling capability
- [[web-search-tool-routing]] — search backend selection policy
- [[notebooklm-cli-operational-gotchas]] — nlm auth recovery
- [[tool-fallbacks-as-index-not-authority]] — design philosophy of this table
- [[chromium-cdp-websocket-origin-restriction]] — chrome-devtools MCP setup

## Falsifier

This table is wrong if:
- Entries persist after the underlying issue is fixed (stale data degrades trust)
- New failure modes aren't added here because agents don't know to check the wiki (discoverability regression vs the old file path)
- The wiki concept grows too large for fast scanning (the table format is the value — if it becomes prose-heavy, split into per-category concepts)
