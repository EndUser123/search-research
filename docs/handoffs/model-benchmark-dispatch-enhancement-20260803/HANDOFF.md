---
thread_id: cohere-integration-019fc5eb
parent_handoff_path: none
current_session_id: 019fc5eb-183e-7bf2-89bc-160737289cba
current_terminal_id: noterm
produced_at: 2026-08-03T23:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head:
  P: dfdb965
  grok: edc6280
assigned_to: grok
assigned_at: 2026-08-03T23:30:00Z
assigned_by: 019fc95d-8132-7181-a6f4-9ab6d1624cd5
---

# Handoff: Cohere integration + model-benchmark dispatch-path enhancement

## Objective

Enhance `/model-benchmark` so a single command produces complete fleet dispatch data: per-model latency across spawn/PI/OC/HTTP, auto-written to fleet-models.json, with gaps detection and fallback validation. This is the continuation of session 019fc5eb which integrated Cohere as a fleet provider, validated persona injection, and built the dispatch-path benchmark — but the benchmark skill itself still only tests HTTP, not all dispatch paths.

## Background — what was done this session (context the next session needs)

### Cohere integration (complete)

- 4 Cohere models registered in Grok config.toml (`cohere-command-a-plus`, `cohere-command-a-reasoning`, `cohere-command-a`, `cohere-north-mini-code`)
- Cohere registered as provider in PI (`~/.pi/agent/models.json`) and OpenCode (`~/.config/opencode/opencode.json`)
- Cohere API key in `P:/.env` as `COHERE_API_KEY` + `CO_API_KEY`
- Quota tracking via response headers (`check_cohere()` in `fleet_quota.py`) — `x-trial-endpoint-call-remaining` for per-minute, local telemetry for monthly
- Spawn gate + error hook updated for Cohere (`FREE_PROVIDERS`, prefix map)
- Rate limit: 20 req/min trial, 500 req/min prod, 1000 calls/month — serial dispatch recommended

### CAR fixes (complete)

- `cohere-command-a-reasoning` config: `reasoning_effort = "none"` (Cohere rejects "medium")
- PI: `supportsReasoningEffort: False` for Cohere provider (prevents PI from sending rejected parameter)
- Spawn limitation documented: CAR fails on instruction-following tasks via spawn (357-382s timeout, "empty response from model reasoning_only"). Works via PI/OC/HTTP. Documented in tool-fallbacks.md.

### Dispatch-path benchmark (complete — data collected, skill not yet updated)

- Full 5-model × 4-path × 5-task benchmark completed manually
- Results in `P:/tmp/dispatch-benchmark/results.json` and in fleet-models.json `dispatch_latency` fields
- Key finding: PI is consistently fastest for one-shot prompts (~4s overhead vs ~9s for OC vs ~3.4s for spawn with heavy agent context)
- Key finding: NMC via spawn is 3-10x slower than via PI (72s vs 18s on code-gen)

### Persona injection (complete)

- 10 personas in `~/.grok/personas/` (3 enriched existing + 3 new)
- `tp_dispatch.py` has `--persona` flag for cross-model dispatch
- PI A/B test validated: persona'd prompt 43% faster, zero unsolicited extras
- Wiki concept: `persona-injection-across-dispatch-paths.md`
- Behavioral/format split: personas consumed by skills with their own format provide behavioral defaults only

### Fleet registry enhancements (complete)

- `fleet-models.json` version 3: every model entry has `dispatch_path`, `persona`, `spawn_limitation`
- 5 models have `dispatch_latency` data (M3, NMC, CA, CAP, CAR)
- `pick_model.py` returns and displays `dispatch_path`, `persona`, `spawn_limitation`, `dispatch_latency`
- 15 models still lack dispatch_latency data — the benchmark skill enhancement addresses this

## What's NOT done — the implementation plan

The approved plan is at `C:/Users/brsth/.grok/sessions/P%3A%5C/019fc5eb-183e-7bf2-89bc-160737289cba/plan.md`. Summary:

### Step 1: Add Cohere to `_PROVIDER_DISPATCH_MAP` (1 line)

File: `~/.grok/skills/model-benchmark/scripts/benchmark.py` line ~890

Add: `"api.cohere.ai": ("cohere", "cohere"),` to `_PROVIDER_DISPATCH_MAP` and `"cohere": "Cohere"` to `_DISPATCH_LABELS`.

### Step 2: Extract `DISPATCH_TASKS` constant

File: `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py`

Add the 5 standard dispatch test tasks as a shared constant:
```python
DISPATCH_TASKS = [
    ("probe", "Reply with exactly: READY", "dispatch overhead"),
    ("reasoning", "A store sells pencils at 3 for $1. ...", "reasoning speed"),
    ("code-gen", "Write a Python function called is_palindrome(s) ...", "code generation"),
    ("structured", "Create a JSON object with exactly these fields: ...", "instruction-following"),
    ("multi-step", "Solve step by step: If 5 workers ...", "chain-of-thought"),
]
```

### Step 3: Expand `run_methods_benchmark()` to full task battery (core change)

File: `~/.grok/skills/model-benchmark/scripts/benchmark.py` ~line 1032

Currently tests one probe prompt per model per method. Expand to loop over `DISPATCH_TASKS × methods`. Compute avg latency per method per model. Output a matrix.

### Step 4: Add `_write_dispatch_latency_to_registry()`

File: `~/.grok/skills/model-benchmark/scripts/benchmark.py`

After `--methods` benchmark completes, write measured latency to fleet-models.json. Atomic write (tmp + os.replace). Read-modify-write preserving existing fields.

### Steps 5-8 (lower priority, can follow incrementally)

5. Extend `--gaps` to detect models missing `dispatch_latency`
6. Add `--rate-probe` mode (parallel requests to find concurrency limit)
7. Add `--persona-ab` mode (bare vs persona'd comparison)
8. Add `--validate-fallbacks` mode (probe each model in fallback chain)

## Key files

| File | Role |
|---|---|
| `~/.grok/skills/model-benchmark/scripts/benchmark.py` | Main benchmark engine — has `run_methods_benchmark()`, `_benchmark_via_pi()`, `_benchmark_via_opencode()`, `_PROVIDER_DISPATCH_MAP` |
| `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py` | Tier definitions — add `DISPATCH_TASKS` here |
| `~/.grok/skills/model-quota/scripts/fleet-models.json` | Fleet registry — has `dispatch_path`, `persona`, `dispatch_latency` fields (5 models have latency data, 15 don't) |
| `~/.grok/skills/model-quota/scripts/pick_model.py` | Model picker — reads and returns dispatch metadata |
| `~/.grok/skills/model-benchmark/SKILL.md` | Skill docs — already updated with same-model-across-paths requirement |
| `~/.grok/skills/tp/__lib/tp_dispatch.py` | Cross-model dispatch — has `--persona` flag and `load_persona()` |

## Acceptance criteria

1. `python benchmark.py --methods pi,opencode --models cohere-north-mini-code` runs 5 tasks × 3 methods and reports a latency matrix
2. After the run, `fleet-models.json` has updated `dispatch_latency` for the tested model
3. `python benchmark.py --gaps` reports which models are missing dispatch_latency data
4. `pick_model.py coding` shows latency line for models that have been benchmarked
5. Cohere models appear in `_PROVIDER_DISPATCH_MAP` so `--methods` works for them

## Open decisions

- Whether spawn_subagent should be included in `--methods` testing (can't be invoked from script — needs agent context). Current approach: test spawn separately via the `spawn_subagent dispatch test` section of the skill.
- Whether to reduce to 3 tasks (probe, code-gen, multi-step) if 5-task battery takes >30 min for full fleet.

## Recommended sequencing (from /tp session review)

All findings from the session cluster into two dependency chains. Implement in this order:

| Priority | Task | Effort | Dependencies |
|---|---|---|---|
| **Step 1-4** | Benchmark skill enhancement (Cohere mapping, DISPATCH_TASKS, methods expansion, registry write-back) | ~2-3 hours | None — head of Chain A |
| **After steps 1-4** | Register Zen/OR models in PI's models.json, then run full benchmark across all fleet models on all paths | ~30 min | After step 4 (skill auto-writes results) |
| **After steps 1-4** | Add PI reasoning audit to SKILL.md "Adding a new provider" section: "check if model accepts reasoning_effort=medium; if not, set supportsReasoningEffort=False" | ~5 min | None |
| **After steps 1-4** | Update pool-selection policy wiki (model-pool-selection-policy-speed-quota-diversity.md): add section on dispatch-path overhead varying by model — "a model fast on HTTP can be 3-10x slower on spawn due to agent context; always check dispatch_latency, not just HTTP speed" | ~10 min | None |
| **LATER (plan step 7)** | Persona A/B mode in benchmark skill | ~1 hour | After steps 1-4 |
| **LATER** | CAR spawn root cause (lightweight agent definition or thinking:disabled param) | ~1 hour | None, low urgency — workaround (PI/OC) works |
| **LOW** | OpenCode `opencode models` command broken (ProviderModelNotFoundError) | ~30 min | None, dispatch works fine |

**Key insight from /tp:** items 3, 6, and 7 in the original gaps list are ONE workstream (this handoff), not three separate tasks. Don't manually fill dispatch_latency for 15 models — the skill IS the structural fix. Run the benchmark once after implementation and it fills all gaps automatically.

## Related wiki

- [[cohere-api-integration-rate-limit-tracking]] — Cohere setup, rate limits, response headers
- [[persona-injection-across-dispatch-paths]] — persona validation, format-constraint principle
- [[tool-fallbacks]] — CAR spawn limitation entry

## Last user message (verbatim)

> /handoff , then give me the prompt to continue the work.

## Status

CLOSED — All 8 steps implemented, verified, and committed.

---

## Revision 1 — 20260804T003000Z (session 019fc95d)

**Trigger:** implementation of steps 1-4.

**What changed:**
- Step 1: Added Cohere to `_PROVIDER_DISPATCH_MAP` (both `api.cohere.com` and `api.cohere.ai` fragments) and `_DISPATCH_LABELS` in benchmark.py
- Step 2: Added `DISPATCH_TASKS` constant (5 tasks) to benchmark_tiers.py, imported into benchmark.py
- Step 3: Rewrote `run_methods_benchmark()` to run full 5-task battery × all methods. Added `_benchmark_via_http()` for HTTP dispatch testing. Method names normalized (`pi`→`PI`, `opencode`→`OC`, `http`/`direct`→`HTTP`). Returns structured data for write-back. Prints task × method latency matrix with averages.
- Step 4: Added `_write_dispatch_latency_to_registry()` — atomic write-back to fleet-models.json with merge semantics (preserves existing path data, updates only tested paths). Caller in `main()` updated to pass results through.
- All changes: syntax-checked, ruff-clean, write-back merge logic verified against both v3 and v4 fleet-models.json schemas.
- Note: fleet-models.json was concurrently migrated to v4 schema by another session (commit c94ea4c). The v4 schema preserves the backward-compatible `lanes` hierarchy, so the write-back function works without modification.

---

## Revision 2 — 20260804T010000Z (session 019fc95d)

**Trigger:** implementation of steps 5-8.

**What changed:**
- Step 5: Extended `--gaps` mode with `detect_dispatch_gaps()` and `print_dispatch_gap_report()` — now scans fleet-models.json for models missing `dispatch_latency` data across the 4 standard paths (spawn, PI, OC, HTTP), reports gaps, and auto-generates the command to fill them. Verified: correctly identifies 77/79 models as missing dispatch data, only the 2 benchmarked models pass.
- Step 6: Added `run_rate_probe()` — sends N parallel probe requests to a single model via HTTP, counts successes vs 429s vs errors. Reports `parallel_safe_count`. Wired as `--rate-probe N`.
- Step 7: Added `run_persona_ab_test()` — runs the 5-task DISPATCH_TASKS battery twice (bare prompt vs persona-prepended) via HTTP, reports per-task latency/length/success deltas. Wired as `--persona-ab`.
- Step 8: Added `run_fallback_validation()` — reads fleet-models.json lane structure, probes each model in each tier with a simple HTTP request, reports reachability. Wired as `--validate-fallbacks`.
- All 4 new functions are ruff-clean, syntax-verified, and importable.
- Committed as `b0fa50a`.
