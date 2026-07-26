---
thread_id: cross-transport-model-matrix-20260726
parent_handoff_path: P:/docs/handoffs/nemotron-spawn-failure-investigation-20260726/HANDOFF.md
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-26T21:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 137e338b288ac097b57588e9f6c7634611bc539b
---

# Cross-transport model capability matrix — test all host-pool models through OpenCode and PI, not just Grok Build + direct API

## Objective

Systematically test every model in the host pool through all three local transports (Grok Build `spawn_subagent`, OpenCode `opencode run`, PI `pi -p`) and record which (model × transport) combinations work for tool-grounded prompts. The current wiki matrix (`model-tool-calling-capability-matrix.md`) documents only Grok Build `spawn_subagent` and direct-API results — today's nemotron finding proved this skews the matrix: models marked "broken" may work fine via OpenCode/PI, and the operator wants the full picture before relying on the matrix for fleet routing decisions.

## Background (why this matters)

The 2026-07-26 nemorton investigation proved that Grok Build's serde is uniquely broken for nemotron (types `service_tier`/`system_fingerprint`/`logprobs` as `u32`; NVIDIA sends `null`). OpenCode and PI both handle the same responses correctly. The wiki was updated to reflect nemotron's three-transport status, but the rest of the matrix is still single-transport (Grok Build spawn only). The operator's directive: test all models through all three local transports and record the results.

The parent handoff (`nemotron-spawn-failure-investigation-20260726`) is the precedent — this handoff generalizes the cross-transport test methodology from one model to the whole host pool.

## Scope — the host pool to test

From `~/.grok/config.toml`. Group by provider for systematic coverage:

**Group A — Grok Build "free/provider-direct" tier** (NVIDIA direct, Google direct):
- `nvidia-nemotron-3-ultra` (already tested — see status table below)
- `nvidia-diffusiongemma-26b`
- `nvidia-inkling`
- `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`, `gemini-flash-latest`
- `gemma-4-31b-it`

**Group B — Grok Build "subscription/OpenCode-Go" tier** (zen/go prefix):
- `zen-big-pickle`, `zen-deepseek-v4-flash-free`, `zen-mimo-v2-5-free`, `zen-north-mini-code-free`, `zen-nemotron-3-ultra-free`
- `go-kimi-k3`, `go-kimi-k2-7-code`, `go-mimo-v2-5`, `go-mimo-v2-5-pro`, `go-deepseek-v4-pro`, `go-deepseek-v4-flash`, `go-qwen3-7-max`, `go-qwen3-7-plus`, `go-qwen3-6-plus`

**Group C — Grok Build "OpenRouter free" tier** (or- prefix):
- `or-nemotron-ultra-free`, `or-nemotron-super-free`, `or-hy3-free`, `or-laguna-m1-free`

**Group D — Grok Build "paid API" tier**:
- `minimax-m3`, `glm-5-2`, `mistral-medium-latest`

## Test protocol (mechanical — execute exactly)

For each model in scope, run **three** tests. Use the exact same prompt across all three transports so the only variable is transport.

### The canonical test prompt

```
Read the file at P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md using your read tool. Then tell me in one sentence what the concept is about. You MUST use the read tool — do not guess or refuse.
```

**Why this prompt:** (1) it forces a real tool call (read), (2) the file path exists and is readable by all three transports (it's in the workspace root, not `P:/tmp/` which has the sandbox-gap issue), (3) it's small enough to complete in <120s, (4) the answer is verifiable — if the model says "model tool calling matrix" or similar, it actually read the file.

**Caveat discovered today (2026-07-26):** OpenCode and PI have a filesystem-sandbox gap — they could not see `P:/tmp/nemotron_direct_smoke.py` even though Grok Build wrote it there. Using a workspace-root path (`P:/.data/wiki/...`) avoids this. If a transport still can't see the file, note it in the results — that's itself a finding.

### Test 1 — Grok Build `spawn_subagent`

```
spawn_subagent(
    model="<host-slug>",
    description="<model-slug> cross-transport test",
    prompt="<canonical test prompt>",
    subagent_type="general-purpose"
)
```

Wait via `get_command_or_subagent_output` (timeout 180000ms).

Record: exit code, duration, did it emit tool calls, did it return content, any error message verbatim.

### Test 2 — OpenCode `opencode run`

```powershell
cd P:/
opencode run -m opencode/<opencode-slug> "<canonical test prompt>" --format json
```

**OpenCode slug mapping:** most host slugs map directly with `opencode/` prefix (e.g., `glm-5-2` → `opencode/glm-5.2`, `zen-nemotron-3-ultra-free` → `opencode/nemotron-3-ultra-free`). Run `opencode models` first to confirm the exact slug — don't guess. If a host model has no OpenCode equivalent, mark `N/A — not in OpenCode pool` and skip.

Wait up to 240s (background task if needed).

Record: exit code, duration, tool-call count (parse JSON output for `"type":"tool_use"` events), content returned, any error.

### Test 3 — PI `pi -p`

```powershell
cd P:/
pi -p --provider <provider> --model <provider/model> --thinking off --no-session "<canonical test prompt>" --mode json
```

**PI provider/model mapping:** run `pi --list-models <name>` to find the exact `provider/model` pair. For example, nemotron → `--provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b`. Not all host models exist in PI's catalog — if missing, mark `N/A — not in PI catalog` and skip.

**Critical PI flags:** `--thinking off` is mandatory for nemotron-class models (PI hangs silently for >5 minutes with thinking on, verified today). `--no-session` avoids polluting the session store. `--mode json` gives structured output for parsing tool-call count.

Wait up to 180s (background task if needed — PI can be slow).

Record: exit code, duration, tool-call count (parse JSON `"type":"toolCall"` events), content returned, any error.

### Filesystem-sandbox check (mandatory per transport per model)

Before declaring "model couldn't read file," verify the transport can see the path. Run a one-line check first:

```powershell
opencode run -m opencode/<slug> "Does the file P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md exist? Reply YES or NO only — do not read it." --format json
# or
pi -p --provider <p> --model <m> --thinking off --no-session "Does the file P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md exist? Reply YES or NO only." --mode json
```

If the transport returns NO, that's a sandbox issue, not a model-capability issue — note separately and skip the tool-grounded test for that combination.

## Results table template (fill in for each model)

| Model (host slug) | Transport | Sandbox sees file? | Tool-grounded test result | Tool calls emitted | Duration | Error (if any) |
|---|---|---|---|---|---|---|
| `<host-slug>` | Grok Build spawn | Y/N | PASS / FAIL / N/A | N | Ns | `<verbatim error or none>` |
| `<host-slug>` | OpenCode | Y/N | PASS / FAIL / N/A | N | Ns | `<verbatim error or none>` |
| `<host-slug>` | PI | Y/N | PASS / FAIL / N/A | N | Ns | `<verbatim error or none>` |

**Already completed (2026-07-26, this session — nemotron only):**

| Model | Transport | Result | Tool calls | Duration | Notes |
|---|---|---|---|---|---|
| `nvidia-nemotron-3-ultra` | Grok Build spawn (trivial READY) | PASS | 0 | 3.65s | No-tool prompt only |
| `nvidia-nemotron-3-ultra` | Grok Build spawn (tool-grounded ~90k tok) | FAIL | — | 10.09s | `serialization error: invalid type: null, expected u32 at line 1 column 331` |
| `nvidia-nemotron-3-ultra` | OpenCode | PASS | 6 | 88.99s | Clean tool-call parsing |
| `nvidia-nemotron-3-ultra` | PI | PASS | 3 | 70.44s | Clean tool-call parsing; `--thinking off` mandatory |
| `nvidia-nemotron-3-ultra` | Direct API (urllib, no tools) | PASS | N/A | 52.55s | Bypasses framework serde entirely |

## Where to record results

Two places, in this order:

1. **Append each completed model's row to the matrix table** at `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` (the existing host-pool table around line 80). Add columns for OpenCode and PI results.
2. **Update the matrix's `summary:` frontmatter and the "finding (one line)" section** to reflect cross-transport reality once enough data is in (e.g., "Grok Build serde is the dominant transport-bug source; OpenCode and PI handle most null-field cases correctly").

## Wiki concepts to read first

- `model-tool-calling-capability-matrix.md` — the matrix being extended
- `model-fleet-provider-pools.md` — provider/key mapping
- `model-pool-not-chain.md` — pool-selection design (relevant if results show clear transport winners)
- `nemotron-spawn-failure-investigation-20260726/HANDOFF.md` — parent handoff, nemotron-specific precedent

## Decision points the next session should surface to the operator

After completing each model group (A/B/C/D), pause and report findings before continuing. Specifically surface:

1. **Any model that's broken on Grok Build but works on OpenCode or PI** — that's a transport-bug candidate (like nemotron). The operator may want to update skill pool tables (e.g., `/tp` pool, `/check` verifier pool) to route through OpenCode/PI for that model.
2. **Any model that's broken on all three transports** — that's a real model/API issue, not a transport issue. Different disposition (report to provider, find替代 model).
3. **Any model with significant latency differences across transports** — relevant for interactive routing decisions.
4. **The filesystem-sandbox gap pattern** — if it's consistent (OpenCode/PI can't see certain paths), document it as a known interoperability gotcha in a new wiki concept or extension to `model-tool-calling-capability-matrix.md`.

## Action budget

**Authorized:** one full pass through the host pool (~30 models × 3 transports = ~90 tests, estimated 2-3 hours wall-clock with parallel background tasks where safe).

**Not authorized without checking with operator first:**
- Paid-API models that consume per-token cost (Group D — minimax, glm, mistral). Test these last and only if the operator confirms budget.
- Models that rate-limit aggressively (kimi-k3, OpenRouter free tier) — pause between tests if 429s appear.
- Any model that shows >5 consecutive failures on one transport — stop and report rather than burning quota.

## Dependencies

- **Requires:** nothing — can start immediately. All three CLIs are installed and configured (`opencode` v1.2.27, `pi` v0.82.1, Grok Build native).
- **Blocks:** nothing directly. Indirectly blocks confident fleet-routing decisions that depend on the matrix being multi-transport.
- **Non-blocking to:** `/tp` pool selection, `/check` verifier selection, `model-benchmark` skill — all of which currently assume Grok Build spawn as the only transport.

## Cross-reference couplings

- `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` — the matrix to extend (lines 80-95 host-pool table; line 154 nemotron RESOLVED/PARTIAL caveat updated today)
- `C:/Users/brsth/.grok/config.toml` — model definitions, provider keys, the `stream_tool_calls = false` config workaround
- `C:/Users/brsth/.grok/tool-fallbacks.md` — operational failure table; update with any new transport-specific failures found
- `P:/docs/handoffs/nemotron-spawn-failure-investigation-20260726/HANDOFF.md` — parent handoff, nemotron-specific
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` lines 408-420 — `/tp` spawn pool table (may need updating if cross-transport testing reveals better options)

## Known sandbox gap (caveat — verify before assuming "model can't read file")

Both OpenCode and PI showed a filesystem-sandbox gap today: they could not see `P:/tmp/nemotron_direct_smoke.py` even though Grok Build wrote it there. PI's `find` returned exit 1; OpenCode's glob returned "No files found." The gap appears to be specific to certain paths (P:/tmp/), not all paths. The canonical test prompt uses `P:/.data/wiki/concepts/...` which should be visible to all transports — but verify with the sandbox check above before recording a "model couldn't read file" result as a model-capability failure.

## Read first (related wiki concepts)

- `model-tool-calling-capability-matrix.md` — primary target for results
- `model-fleet-provider-pools.md` — provider/key mapping
- `model-pool-not-chain.md` — pool design philosophy
- `nemotron-spawn-failure-investigation-20260726/HANDOFF.md` — parent handoff

## Other outstanding streams in this session (named, not handed off)

- **Scope-matching verification discipline rule adoption.** Revised concept at `P:/.data/wiki/concepts/scope-matching-verification-discipline.md` recommends scope-matching as AGENTS.md workflow step. `/tp` critique found the proposal inherits the prose-rule anti-pattern. Needs the three revisions named in the critique before adoption. Separate decision for the operator.
- **AAR Q11 extension for operator-catch feedback loop.** The systematization fix for the recurring near-miss pattern. Needs a read of the AAR skill's current Q11 implementation before editing.
- **`receipt-before-write-workflow-and-hook-20260726` handoff.** Deferred structural hook for wiki claims. Trigger: 3 recurrences in 10 sessions. Already handed off.

## Last user message (verbatim)

> /handoff create a handoff file, so that we test all models thru OpenCode and PI, and record the results, not jsut thru direct API and grok cli.

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b immediately after completing the nemotron cross-transport verification (Grok Build FAIL, OpenCode PASS, PI PASS, direct API PASS). The operator's directive generalizes the cross-transport test methodology from one model to the full host pool. The handoff is scoped to be mechanically executable by a fresh session without re-deriving the methodology.
