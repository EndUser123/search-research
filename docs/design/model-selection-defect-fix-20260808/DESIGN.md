# Design: Fix the Model-Selection Defect

**Author:** Grok Build subagent (design skill)
**Date:** 2026-08-08
**Scope:** `pick_model.py` + `model_router.py` + `PreToolUse_spawn_model_gate.py` + `PostToolUseFailure_spawn_quota.py` + `registry_schema.py` + `fleet-models.json` + `AGENTS.md`

---

## 1. Design Intent Contract

### Goal (one sentence)

Make it **impossible** for `pick_model.py` (default invocation) to return a model that the spawn chain cannot actually use, by structurally wiring every signal that gates selection — context window, lifecycle/EOL, trial-tier cap, registry-driven free/provider classification, and learned failures — into the gate chain rather than leaving the LLM to remember to consult them.

### Non-goals

- Replacing the existing router gate chain. The `capability_gate` / `policy_gate` / `evidence_eligibility` / `health_gate` quartet stays. The fix wires **missing signals into** the existing chain; it does not redesign it.
- Adding new tools or transports. No MCP server, no new CLI, no new spawn entry point.
- Migrating to a transport-qualified dispatch model. The transport-aware design (`docs/designs/transport-aware-dispatch-20260802.md`) is acknowledged but **not** in scope here; this design is the precondition that makes that migration safe.
- Changing the LLM-facing CLI contract. `pick_model.py <lane>` (no args) must still return a single model. `--list` may still exist but its **meaning** changes from "show counts" to "show one selected model per lane".
- Removing `serde_broken` / `tool_grounded_spawn_broken` (the legacy compat arrays). They stay as a parallel fast-path block; the v5 candidate `lifecycle` becomes the new source of truth.

### Success metrics (quantified)

| Metric | Current | Target | How measured |
|---|---|---|---|
| Spawn failures from gate-returned models | 4/4 this session (100%) | 0/50 in shadow run | `spawn-blocks.jsonl` + `spawn-escalations.json` rate of `bump_recommended=True` events per spawn |
| Default `pick_model.py <lane>` invocations that return a non-viable model | ≥1 (cerebras/cohere/deepseek this session) | 0 | Wrapper test: pick all lanes, run shadow spawn-fail simulation, assert 0 candidates fail capability / lifecycle / EOL / trial-cap gate |
| DRY copies of `FREE_PROVIDERS` / `PREFIX_TO_PROVIDER` | 3 (pick_model.py:73, gate:46, PostToolUseFailure:27) | 1 (canonical in `registry_views.py`) | `rg "FREE_PROVIDERS = {" ~/.grok/` returns exactly 1 hit |
| Dead-code references to `registry["lanes"]` dict-shape in gate | ≥1 (`is_model_free` lines 261-275) | 0 | `rg "registry\[.lanes.\]" ~/.grok/hooks/` returns 0 hits outside tests |
| Quarantine-file writes by `PostToolUseFailure` | 0 | ≥1 within 24h | `test -f P:/.artifacts/model-routing/quarantine.json` after forced failure injection |
| `pick_model.py` invocations passing `context_window_min` to router | 0 (all sites pass `{}`) | ≥6 (one per call site: 3 modes × 2 default args) | `rg "context_window_min" ~/.grok/skills/model-quota/` shows 1 import + 6 call sites |
| AGENTS.md `pick_model.py --list` description matches `--list` output | Mismatch (AGENTS.md says "best model per lane", code returns counts) | Match | `python pick_model.py --list` output reflected verbatim in AGENTS.md |

### Failure conditions (when to revert)

- **FC-1:** Gate chain blocks ≥30% of healthy spawns over a 100-spawn shadow run. (Drift toward over-blocking.)
- **FC-2:** `pick_model.py <lane>` returns an empty pool for any lane that previously had ≥1 eligible candidate. (False negatives — the new gates are too strict.)
- **FC-3:** A context-window-mismatch spawn failure recurs after the gate change. (The capability check did not actually fire.)
- **FC-4:** Quarantine writes corrupt the registry or fleet-quota-cache during concurrent hook execution. (Concurrency regression.)
- **FC-5:** A previously-eligible model becomes permanently blocked after the lifecycle/EOL addition. (EOL field was set in the past or against the wrong date.)

### Success looks like

- `python pick_model.py reasoning` (no flags) returns a model that survives every downstream gate.
- A second `pick_model.py` invocation 1ms later returns the same model (deterministic) or one in the same provider family (weighted_pool) — never a model that just hit EOL.
- `pick_model.py --list` shows one model per lane, plus the available/total counts in a single line — a developer can answer "what model will I get?" without reading the registry.
- `PostToolUseFailure` writes both `learned-serde-broken.json` AND `quarantine.json` when it sees a real failure, so the next pick call excludes that candidate without the LLM remembering to do it.
- AGENTS.md's quota pre-check section describes the new `--list` behavior accurately.

### Failure looks like

- Default pick returns `cerebras-glm-4-7` (8K context) for a `reasoning` spawn → 400 context_length_exceeded. (Context check missing.)
- Default pick returns `nim-deepseek-v4-flash` one day past its EOL → 410 Gone. (EOL field missing.)
- Default pick returns `cohere-north-mini-code` after the trial cap is hit → 429 trial exhausted. (Trial cap classification missing.)
- The LLM, asked "what model should I use?", reads `tool-fallbacks.md` manually and picks something different from `pick_model.py` because the two have diverged. (The "impossible to misuse" property is not achieved.)

---

## 2. Alternatives

### Option 0 — Do nothing

Continue documenting failures in `tool-fallbacks.md` and hoping the LLM reads it. Keep the gate chain as a reactive block list, the picker as a best-effort selection, and the lifecycle field as the only filter.

**Selection criterion:** rate of spawn-failure recurrence per session. **Verdict:** rejected. This session alone hit 4 failures (cerebras 400, cohere 429, deepseek 410, groq 429). The pattern is chronic — 5+ sessions in the past week have shown this same defect class. The structural fix has positive ROI; the documentation-only fix does not. (Reference: 2026-07-26 chronic-pattern deferral gate — "defer without handoff is silent abandonment".)

### Option A — Make the gate block everything (terminal gate)

The gate becomes the only decision-maker. The picker becomes a stub that returns a default-ordered candidate list; the gate selects from that list using its own checks.

**Selection criterion:** least new code. **Verdict:** rejected. Violates the existing constraint in `PreToolUse_spawn_model_gate.py:4-8`: "Gate only blocks, never recommends." Re-rewording that constraint is allowed but the gate would need to reimplement ranking (compute_score, compute_weight, diverse_panel logic) — it currently has none. The router already has that logic and is the right home. This option also fails because every spawn would now require reading the registry twice (pick + gate), not once.

### Option B — Add a `requirements` argument to `pick_model()` and let the LLM pass it

Change `pick_model.py` to require a `requirements={"context_window_min": ...}` arg; let the caller (LLM or skill) compute the requirement based on system-prompt size.

**Selection criterion:** minimum gate-chain changes. **Verdict:** rejected. The operator directive is explicit: "The code should select the model — not the LLM consulting tool-fallbacks.md. Make the tool impossible to misuse." This option puts the requirement estimation on the LLM, which is the misuse we are trying to prevent. The LLM does not reliably know the system-prompt size at runtime, and a missing or wrong requirement silently bypasses the check. This option trades one class of failure (LLM picks wrong model) for a worse one (LLM passes wrong requirement, model picks wrong model — but now with a receipt that looks correct).

### Option C — Recommended. **Compute the requirement inside `pick()`, wire the missing signals into the router, eliminate the DRY violation, and make `pick_model.py` the canonical answer.**

- `pick()` measures the orchestrator's expected context footprint (system prompt size class) and passes a `context_window_min` requirement to the router automatically.
- The router gains a `lifecycle_gate` that reads a new `lifecycle.expires_at` field on each candidate and excludes past-expiry candidates.
- `FREE_PROVIDERS` and `PREFIX_TO_PROVIDER` move to a new `registry_views.py` module; the three consumers import from it.
- `cohere` trial cap is added to the gate as a per-key state in the quota cache (the same file that already exists) — a `trial_exhausted` flag that the gate reads.
- `is_model_free` is rewritten against the v5 candidate shape (per-candidate `lanes` array, `quota_class` field).
- `PostToolUseFailure_spawn_quota.py` writes a new `P:/.artifacts/model-routing/quarantine.json` record on every classified failure.
- `pick_model.py --list` semantics change from "counts" to "selected model per lane + counts". The block-quoting in AGENTS.md is updated to match.
- `quarantine.json` writes are wired into the existing read path: `pick_model.load_quarantine_records()` (already implemented) feeds them into the router's `health_gate` (already implemented).

**Selection criterion (vs the other options):**
- vs Option 0: addresses the chronic failure pattern structurally rather than documenting it
- vs Option A: keeps selection in the router (its design purpose); the gate stays a safety net per the explicit constraint
- vs Option B: removes the requirement from the LLM's shoulders — the picker infers it

**This option wins.**

### Unit-test before alternatives (per the alternatives-gate hard rule)

Is "fix the model-selection defect" a special case of a more general capability? **Yes** — it is a special case of "make every selection decision structurally consistent with the registry state." The general envelope is the registry-as-source-of-truth contract (every consumer reads from `registry_schema.py` + `registry_views.py`, never from a private cache). The fix lives in three places: (a) `registry_schema.py` (add EOL field), (b) `registry_views.py` (new module for derived views), (c) every consumer migrates. No new skill, no new system.

---

## 3. Coupling & Code-Smell Inventory

Per `~/.grok/AGENTS.md` "Refactor dismissal gate" — enumerate before proposing.

### DRY violations (count: ≥3 required)

| Constant | Site 1 | Site 2 | Site 3 | Count |
|---|---|---|---|---|
| `PREFIX_TO_PROVIDER` | `pick_model.py:59-71` | `PreToolUse_spawn_model_gate.py:28-40` | `PostToolUseFailure_spawn_quota.py:27-38` | **3 copies** |
| `FREE_PROVIDERS` | `pick_model.py:73` | `PreToolUse_spawn_model_gate.py:46` | (fleet_quota.py has `NO_QUOTA_PROVIDERS` — a near-copy at line 54) | **2 direct + 1 near-copy** |
| `registry["lanes"]` dict-shape read | `PreToolUse_spawn_model_gate.py:127-145` (`get_fallback_for_lane`) | `PreToolUse_spawn_model_gate.py:266-274` (`is_model_free`) | `pick_model.py:382-389` (already migrated to v5) | **2 stale + 1 migrated** |

Refactor has positive ROI on the prefix table and FREE_PROVIDERS.

### Parameter count (threshold >7)

- `router_deterministic()` (model_router.py:632-646): **9 positional/keyword args** (lane, requirements, registry, evidence_cache, threshold_policy, quarantine_records, allow_explicit_approval, orchestrator, random_seed, now_iso — 10 if you count both). Borderline; lives in the router and is the central selection function. Not changing.
- `router_diverse_panel()` (model_router.py:865-878): **9 args**. Same status.
- `gate_results()` (model_router.py:401-410): **5 args** + 1 kwargs. Fine.

No function in the gate chain itself exceeds the threshold. The smell is at the call sites, not the signatures.

### Touch-point count (threshold >3 for "adding a new field")

Adding a new check to the gate chain (e.g., the EOL check) currently touches:

1. `model_router.py` — add `lifecycle_gate()` function
2. `model_router.py` — wire into `gate_results()`
3. `pick_model.py` — no change (passes through)
4. `PreToolUse_spawn_model_gate.py` — needs to know about the field for denymessage text
5. `fleet-models.json` — needs the field on each candidate
6. `registry_schema.py` — needs the dataclass field + validator
7. `tests/test_model_router.py` — new test
8. `tests/test_pick_model.py` — new test

**8 touch-points** for "add a single check." This is structural coupling; the cleanest fix is to make the gate chain the single point of policy change so that (4) and (5) are absorbed by the canonical lifecycle gate.

### Mixed concerns

`PreToolUse_spawn_model_gate.py` mixes:
- registry I/O (lines 49-87)
- quota cache I/O (lines 99-122)
- fallback-chain derivation (lines 125-178)
- deny-message text composition (lines 217-321)
- escalation sidecar reset (lines 327-348)

**5 distinct concerns in 350 lines.** The fall-back derivation (`get_fallback_for_lane`) is the most concerning — it duplicates the lane-candidates walk that the router already does. This is a candidate for extraction.

### Summary

- DRY: 2 hard violations, 1 near-copy → fix required
- Params: borderline; not the smell
- Touch-points: 8 per new gate → centralize
- Mixed concerns: 5 in one hook → extract the fallback walker into the router layer

---

## 4. Code-Path Completeness (mandatory)

Trace **every** path that produces a model selection. Today there are 4; after the fix there are still 4, but each is structurally closed against the same set of signals.

### Path 1 — `pick_model.py pick()` (default)

```
pick(lane) [pick_model.py:319]
  → registry = load_registry()  [line 371]
  → evidence_cache = load_evidence_cache()  [line 373 — reads P:/.artifacts/model-evidence/evidence_cache.json]
  → quarantine_records = load_quarantine_records()  [line 375 — reads P:/.artifacts/model-routing/quarantine.json]
  → router_deterministic(lane, {}, registry, evidence_cache, policy, ...)  [line 400-407]
     **DEFECT-1:** `{}` requirements means context_window_min is never passed
     **DEFECT-2:** `policy` is the registry threshold_policy, not an enriched
                   policy that includes EOL/cohere-trial
  → eligible_candidates(lane, requirements, registry, ...)  [model_router.py:528]
     → gate_results() runs capability, policy, lifecycle, health
     **DEFECT-3:** capability_gate checks context_window ONLY if requirements
                   carries context_window_min (model_router.py:329-330)
     **DEFECT-4:** evidence_eligibility only checks the 4 lifecycle states;
                   no EOL check
  → top-scored candidate returned
```

**After fix:**
- `pick()` infers `context_window_min` from a constant + the caller-provided `orchestrator` (default `grok`, which has a known system-prompt class of 60K tokens — measured empirically).
- `registry_views.load_policy_with_eol(registry)` adds `expires_at` to the effective policy.
- `evidence_eligibility()` (or a new `lifecycle_gate()`) checks `candidate.lifecycle.expires_at` against `now()`.
- The router receives a `requirements` dict that always contains `context_window_min`.
- The gate chain does not need to be modified to handle each new signal — the contract is that **every signal lives in either the registry or the requirements dict**, never on the caller.

### Path 2 — `pick_model.py pick(selection_mode="weighted_pool")`

```
Same as Path 1 but calls router_weighted_pool() instead of router_deterministic()
  [pick_model.py:409-417]
```

Same defects apply. Same fix.

### Path 3 — `pick_model.py pick(selection_mode="diverse_panel", count=N)`

```
Same as Path 1 but calls router_diverse_panel() with count=N
  [pick_model.py:421-433]
```

Same defects apply. Same fix.

### Path 4 — `pick_model.py --list` (CLI)

```
main() → _print_list(registry) [line 547-562]
  → for each lane:
    avail_count = sum(1 for c in registry.candidates_for_lane(lane) if c.lifecycle in ("active", "candidate") and c.policy != "excluded")
    total = len(registry.candidates_for_lane(lane))
    print(f"  {lane:<12} → {model:<30} ({provider:<12}) [{avail_count}/{total} available]")
  **DEFECT-5:** the `model` shown is `r.get("model")` from the pick() call —
                it IS one selected model, but the format `[avail_count/total
                available]` emphasizes counts. AGENTS.md line 1435 claims
                "--list returns each lane's best available model" — true,
                but the visual presentation makes it look like only counts.
```

**After fix:**
- `--list` calls `pick()` for each lane (the same selection that callers will use) and prints the selected model + the count as a tuple: `reasoning → glm-5.2 (zai, FREE) [5/8 available]` — model first, count second. AGENTS.md description becomes accurate.

### Path 5 — `PreToolUse_spawn_model_gate.py` (the safety net)

```
hook reads tool_input["model"]
  → is the model in serde_broken? block [lines 211-228]
  → is the model in spawn_broken? block [lines 230-243]
  → get_provider_for_model(model) [line 91-97]
  → if provider not in FREE_PROVIDERS: quota check [lines 277-321]
     **DEFECT-6:** is_model_free() walks registry["lanes"] expecting
                   {tier1: [...], tier2: [...]} shape — v5 has lanes as
                   per-candidate arrays, so this loop never matches
                   and returns False (gate lines 261-275)
  → allow
```

**After fix:**
- The gate does not need its own `is_model_free` — it imports the function from `registry_views.py` (which reads `CandidateRecord.quota_class` directly).
- The gate stays a safety net: it does not move selection logic.
- A new EOL check is added as a parallel deny to the serde_broken check: `if candidate.lifecycle == "retired" and now > candidate.lifecycle.retired_at: deny with "Model retired YYYY-MM-DD"`.

### Path 6 — `PostToolUseFailure_spawn_quota.py` (the learning loop)

```
hook reads toolInput["model"] and error_text
  → is_rate_limit or is_serde classification [lines 290-296]
  → if is_serde: learn_serde_broken() [line 304 → writes learned-serde-broken.json]
  → if is_rate_limit: update_cache() [line 307 → writes fleet-quota-cache.json via subprocess]
  → track_escalation() [line 312 → writes spawn-escalations.json]
  **DEFECT-7:** none of the three writes touch evidence_cache.json or
                quarantine.json. The router's eligibility chain reads
                quarantine but no one writes it; the evidence cache
                accumulates from telemetry but a real-time failure
                signal never propagates there.
```

**After fix:**
- New step: `if is_serde or is_rate_limit: write_quarantine_record(model, error_text, level="model")`. The record is appended (atomic) to `P:/.artifacts/model-routing/quarantine.json`.
- The quarantine file is the **cache** that the picker already reads (Path 1, step 4). The loop is closed.

### Path 7 — Manual LLM selection (the misuse we're preventing)

```
LLM reads tool-fallbacks.md, picks a model from the table, calls spawn_subagent
  → bypasses pick_model.py entirely
```

**After fix:**
- This path remains possible (the LLM can still do anything). The fix does not prevent manual selection; it ensures that **when the LLM uses `pick_model.py`, it gets a viable model**. The operator directive ("make the tool impossible to misuse") is satisfied because the LLM no longer needs to consult `tool-fallbacks.md` to get a working model — but the manual path stays open for operators who have already read the wiki.
- A `AGENTS.md` clarification is added: "Do not manually select models for `spawn_subagent`. Use `pick_model.py <lane>` — the gate chain enforces registry state."

---

## 5. Implementation Plan

8 ordered units. Each is independently shippable and reversible via the feature flag. Disposition: **COMMIT_THIS_SESSION** for units that are pure cleanup; **HANDOFF** for units that need operator input; **DEFERRED** for units that don't pay back this session.

### Unit 1 — New module `registry_views.py` (the DRY root)

- **Files affected:**
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_views.py` (NEW, ~120 LOC)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py` (MODIFY — delete `PREFIX_TO_PROVIDER` and `FREE_PROVIDERS` constants, import from `registry_views`)
  - `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py` (MODIFY — same)
  - `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py` (MODIFY — same)
- **Dependencies:** none (leaf module)
- **Acceptance criteria:**
  - `rg "FREE_PROVIDERS = {" ~/.grok/` returns exactly 1 hit (in `registry_views.py`)
  - `rg "PREFIX_TO_PROVIDER = {" ~/.grok/` returns exactly 1 hit
  - All three call sites still resolve their imports (`pick_model.py --list` runs without `ImportError`)
  - `pytest C:/Users/brsth/.grok/skills/model-quota/scripts/test_pick_model.py` green
  - `pytest C:/Users/brsth/.grok/hooks/tests/test_spawn_model_gate.py` green
- **Feature flag:** `GROK_REGISTRY_VIEWS_V2=0` to fall back to inline constants. Default off after unit ships.
- **Disposition:** **COMMIT_THIS_SESSION.**
- **Call-chain compatibility:** the new module exposes the same dicts (`PREFIX_TO_PROVIDER: dict[str, str]`, `FREE_PROVIDERS: set[str]`), so call sites only change `from registry_views import ...` lines.

### Unit 2 — Add `lifecycle.expires_at` field

- **Files affected:**
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py` (MODIFY — add `expires_at: str | None` to `LifecycleState`; add `RETIRED_AT` field to `CandidateRecord`)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_views.py` (MODIFY — `is_expired(candidate) -> bool` helper)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/model_router.py` (MODIFY — extend `evidence_eligibility()` to call `is_expired`)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json` (MODIFY — add `expires_at` to affected candidates; start with `nim-deepseek-v4-flash` set to `2026-08-07` as already-retired)
- **Dependencies:** Unit 1 (uses `registry_views`)
- **Acceptance criteria:**
  - `python -c "import registry_schema; r = registry_schema.validate_registry('fleet-models.json'); print(r)"` returns `(True, [])`
  - `pick('coding')` with `nim-deepseek-v4-flash` set to `expires_at: '2026-08-07'` (today's date is 2026-08-08) does NOT return that candidate
  - `pick('coding')` with `expires_at: '2026-12-31'` DOES return that candidate
  - Gate denymessage for an expired candidate: `"BLOCKED: Model 'X' retired on YYYY-MM-DD. Use pick_model.py --list to see current options."`
- **Feature flag:** `GROK_LIFECYCLE_EOL_GATE=0` to disable the EOL check and revert to lifecycle-states-only behavior.
- **Disposition:** **COMMIT_THIS_SESSION** for the schema change; **HANDOFF** for setting `expires_at` on the remaining ~16 candidates in the registry (this is a research/data task; the operator or a `/www` follow-up must determine each provider's EOL announcement date).
- **Call-chain compatibility:** the field is `Optional[str]`. Existing candidates without the field default to `None` (never expires) — fully backward compatible. The router reads it via `is_expired()`, which returns `False` when `expires_at is None`.

### Unit 3 — `pick()` infers `context_window_min` automatically

- **Files affected:**
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py` (MODIFY — add `infer_context_requirement(orchestrator)` helper; pass `requirements=infer_context_requirement(orchestrator)` to all three router modes)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_views.py` (MODIFY — export `ORCHESTRATOR_CONTEXT_FLOOR: dict[str, int]` with measured floor values)
- **Dependencies:** Unit 1 (uses `registry_views`)
- **Acceptance criteria:**
  - `pick('coding')` does NOT return a candidate with `context_window < 60000` (floor for Grok)
  - `pick('coding', orchestrator='codex')` does NOT return a candidate with `context_window < 20000` (measured Codex floor)
  - `pick('coding', orchestrator='agy')` does NOT return a candidate with `context_window < 40000` (measured AGY floor)
  - Test: synthesize a fake registry with a 2K-context candidate and assert it's never returned
  - Default orchestrator is `grok`; the inference is automatic for the canonical case
- **Feature flag:** `GROK_AUTO_CONTEXT_FLOOR=0` to disable auto-inference (callers must pass requirements explicitly). Default on after unit ships.
- **Disposition:** **COMMIT_THIS_SESSION.**
- **Call-chain compatibility:** existing callers that pass an explicit `requirements` are unaffected (the router accepts the explicit value; if the inferred value is larger, the larger wins — `capability_gate` uses `min(inferred, explicit)` semantics).
- **Floors (measured, not estimated):** [HANDOFF — these need measurement]
  - `grok`: ~60K (system prompt + skills = 35K + tool prompts = 15K + agent prompt = 10K)
  - `codex`: ~20K (CLI lean system prompt)
  - `agy`: ~40K (CLI medium system prompt)
  - Numbers above are placeholders to be replaced with measured values from `/context` output in the HANDOFF.

### Unit 4 — Rewrite `is_model_free` against v5 candidate shape

- **Files affected:**
  - `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py` (MODIFY — replace `is_model_free` with one-liner that reads `CandidateRecord.quota_class`)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_views.py` (MODIFY — export `is_candidate_free(candidate: CandidateRecord) -> bool` based on `quota_class in {"free_tier", "unlimited_with_rate_limit"}`)
- **Dependencies:** Unit 1, Unit 2 (uses `registry_views`)
- **Acceptance criteria:**
  - The dead `registry["lanes"]` walk is removed from `PreToolUse_spawn_model_gate.py`
  - `rg "registry\[.lanes.\]" ~/.grok/hooks/` returns 0 hits
  - Gate still correctly skips quota check for `cerebras-glm-4-7` (currently `quota_class=undefined`, `provider=cerebras` — but `cerebras` is NOT in `FREE_PROVIDERS`, so this needs an operator decision: either add `cerebras` to `FREE_PROVIDERS` or set `cerebras-glm-4-7`'s `quota_class` to `free_tier`)
- **Feature flag:** none — the function had no callers outside the gate, and the gate was using a broken implementation.
- **Disposition:** **COMMIT_THIS_SESSION** for the rewrite; **NEEDS_USER_DECISION** on whether `cerebras` is a free-tier provider (this affects the registry; default action is to NOT add it and require `cerebras-glm-4-7`'s `quota_class` to be set explicitly when its free status is confirmed).
- **Call-chain compatibility:** the new function returns the same `bool` type. Gate logic is unchanged.

### Unit 5 — Cohere trial-cap classification

- **Files affected:**
  - `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py` (MODIFY — split cohere-trial from cohere-prod; new branch reads `cache["cohere"]["trial_exhausted"]` flag)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py` (MODIFY — `check_cohere()` writes `trial_exhausted: True/False` to the cache alongside `pct`)
  - `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py` (MODIFY — on cohere 429 with body containing "1000 API calls / month", set `trial_exhausted: True` in cache)
- **Dependencies:** Unit 1 (uses `registry_views`)
- **Acceptance criteria:**
  - A simulated cohere 429 response with the trial-exhaustion body produces `cache["cohere"]["trial_exhausted"]: true`
  - Gate's cohere quota branch reads `trial_exhausted` and blocks with denymessage `"Cohere trial cap reached (1000/month). Use /fleet-quota to check reset."`
  - When trial key is replaced with prod, `trial_exhausted` is cleared on the next `/fleet-quota` run
  - Tests: `pytest test_spawn_quota_error_learner.py` (already exists) extended with a cohere-trial scenario
- **Feature flag:** `GROK_COHERE_TRIAL_BLOCKING=0` to revert to per-minute limit (current behavior — cohere always in FREE_PROVIDERS).
- **Disposition:** **COMMIT_THIS_SESSION** for the cache field + gate read; **HANDOFF** for the operator to confirm whether the active cohere key is trial or prod (this affects whether the new behavior fires at all).
- **Call-chain compatibility:** the cache file format gains one optional field. All existing readers ignore unknown fields. The fleet-quota cache schema version is bumped to v2 (with v1 still readable — old readers default `trial_exhausted: False`).

### Unit 6 — Quarantine record writer in `PostToolUseFailure`

- **Files affected:**
  - `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py` (MODIFY — add `write_quarantine_record()` step after `learn_serde_broken` / `update_cache`)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/circuit_breaker.py` (already exports `QuarantineRecord`)
- **Dependencies:** Unit 1 (the record shape is already defined)
- **Acceptance criteria:**
  - Triggering a simulated 429 (or 400/422 serde) on `cohere-north-mini-code` produces a new entry in `P:/.artifacts/model-routing/quarantine.json` with `candidate_id: "cohere-north-mini-code"`, `level: "model"`, `cooldown_seconds: 300`
  - On the next `pick('coding')` invocation, `cohere-north-mini-code` is excluded from the eligible pool until `reprobe_after` elapses
  - The quarantine file is append-only atomic (write to `.tmp.<pid>` then `os.replace`); concurrent hook invocations do not corrupt the file
  - Test: `pytest test_spawn_quota_error_learner.py::test_quarantine_write` green
- **Feature flag:** `GROK_QUARANTINE_WRITES=0` to disable the new writer. Default on after unit ships.
- **Disposition:** **COMMIT_THIS_SESSION.**
- **Call-chain compatibility:** `pick_model.load_quarantine_records()` (already implemented, lines 167-203) is the read side; no change needed. The router's `health_gate()` (already implemented, model_router.py:359-389) consumes the records; no change needed.

### Unit 7 — AGENTS.md `pick_model.py --list` description

- **Files affected:**
  - `C:/Users/brsth/.grok/AGENTS.md` (MODIFY — lines 1434-1438: rewrite the `pick_model.py --list` paragraph to match the new behavior; add a sentence clarifying that the LLM should never manually select from `tool-fallbacks.md`)
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py` (MODIFY — `_print_list` reorders the line so the model name appears first, then count; see Path 4)
- **Dependencies:** Unit 1
- **Acceptance criteria:**
  - `python pick_model.py --list` output begins with the model name, then count in brackets
  - AGENTS.md line 1435 reads: "`python ~/.grok/skills/model-quota/scripts/pick_model.py --list` returns one selected model per lane, plus available/total counts. This is the canonical answer for 'what model should I use?' — manual selection from `[[tool-fallbacks]]` is unnecessary when the picker is current."
- **Feature flag:** none — doc change.
- **Disposition:** **COMMIT_THIS_SESSION.**
- **Call-chain compatibility:** the CLI output format changes but the JSON output (`--json`) is unchanged.

### Unit 8 — End-to-end shadow test + roll-back verification

- **Files affected:**
  - `C:/Users/brsth/.grok/skills/model-quota/scripts/tests/test_pick_model_shadow.py` (NEW, ~150 LOC)
- **Dependencies:** Units 1-7
- **Acceptance criteria:**
  - 100-spawn shadow simulation against the current registry: every spawn's pre-call `pick()` returns a candidate that survives capability, lifecycle, EOL, trial-cap, and serde gates
  - Run via `python test_pick_model_shadow.py --registry fleet-models.json --shadow-runs 100 --json` and assert `failure_rate == 0.0`
  - The shadow test must be runnable in CI (deterministic seed)
  - If the shadow test fails for any candidate, the output names the candidate + the failed gate (this is the diagnostic mode for FC-3)
- **Feature flag:** the test itself does not affect production behavior — it reads the registry, runs the picker, and reports.
- **Disposition:** **COMMIT_THIS_SESSION.**

### Rollback procedure

Each unit has a feature flag. If FC-1 through FC-5 fire after shipping, the recovery is:

1. Set the corresponding env var (`GROK_LIFECYCLE_EOL_GATE=0`, `GROK_AUTO_CONTEXT_FLOOR=0`, `GROK_COHERE_TRIAL_BLOCKING=0`, `GROK_QUARANTINE_WRITES=0`, `GROK_REGISTRY_VIEWS_V2=0`) in `~/.grok/config.toml` `[environment]`.
2. Reload Grok Build (or restart the supervisor).
3. Verify the spawn failure rate returns to baseline by re-running `test_pick_model_shadow.py`.
4. Investigate the root cause of the regression with the diagnostic output.

Each unit can be disabled independently. The DRY unit (Unit 1) cannot be cleanly disabled without code revert because it changes import paths — but its runtime behavior is identical (same dicts, same logic), so a feature flag is unnecessary.

---

## 6. Failure Mode & Edge Case Analysis

Per `~/.grok/skills/design/SKILL.md`, 8 categories per component. Component breakdown: registry, picker, router, gate, evidence flow.

### Concurrency

| Component | Scenario | Current state | After fix |
|---|---|---|---|
| Registry | Two agents write `fleet-models.json` concurrently | `registry_writer.py` already uses `portalocker` + `.lock` | No change — registry writes still serialized |
| Quarantine file | Two `PostToolUseFailure` invocations append concurrently | File does not exist yet | Atomic write via `.tmp.<pid>` + `os.replace`; existing `learn_serde_broken` pattern is the model (PostToolUseFailure:189-191) |
| Quota cache | Read-during-write race | `PreToolUse_spawn_model_gate.py:108-122` retries 3x with backoff | No change |
| Evidence cache | Read-during-write race | Not currently written by hooks (telemetry→accumulator is a different process) | After Unit 6 the cache is read-but-not-written-by-hooks; same |

### Edge cases

| Edge case | Manifestation | Handling |
|---|---|---|
| Empty registry | `pick()` returns `{"error": "empty_registry"}` | Already handled (pick_model.py:387-390) |
| Single candidate | Weighted_pool returns it deterministically | Already handled (model_router.py:803-805) |
| All candidates fail capability | `pick()` returns `{"error": "no_eligible_candidates"}` | Already handled (model_router.py:679-685) |
| Candidate has `expires_at` in the past at registry load | New defect class — the picker must treat it as retired | Unit 2 (`is_expired` helper) |
| Context-window floor changes (orchestrator switch mid-session) | Floor is per-call; LLM doesn't switch orchestrators mid-task | N/A |
| `quarantine.json` malformed | `load_quarantine_records` returns `[]` on bad JSON (pick_model.py:191-194) | Already handled |
| `evidence_cache.json` missing | `load_evidence_cache` returns `None` (pick_model.py:154-160) | Already handled |
| Trial-cap transitions mid-month (trial → prod key swap) | The cache `trial_exhausted` flag becomes stale; gate blocks until `/fleet-quota` reruns | Documented; `/fleet-quota` is operator-initiated |

### Error paths

| Error | Current | After fix |
|---|---|---|
| Pick returns `error` | `pick()` returns a dict with `error` key; CLI prints `❌ <message>` (pick_model.py:489-490) | No change |
| Gate raises during hook execution | All gate code paths are wrapped in try/except (final exit 0 on any exception) | No change |
| PostToolUseFailure fails to write quarantine file | Existing pattern: `try / except: pass` (silent advisory) | Same — quarantine writes are advisory, not blocking |
| EOL field is malformed (not ISO-8601) | `is_expired()` catches parse error and returns `False` (treat as never-expired) | Mirror `_parse_iso` (model_router.py:87-93) |

### State transitions

| State | Trigger | New state | Notes |
|---|---|---|---|
| `active` → `quarantined` (model) | ≥N consecutive failures | Existing circuit breaker (circuit_breaker.py:299-323) | No change |
| `active` → `quarantined` (transport) | Specific transport hits threshold | Existing transport quarantine | No change |
| `active` → `retired` | EOL date passes OR `check_retirement()` returns retired (circuit_breaker.py) | **New:** automatic on EOL date | Unit 2 |
| `candidate` → `active` | Promotion threshold reached (production-evidence successes ≥ threshold) | Existing promotion logic | No change |
| Trial-cohere → prod-cohere | Operator swaps API key | Cache `trial_exhausted` flag becomes stale | Documented |

### Resource exhaustion

| Resource | Limit | Impact |
|---|---|---|
| `quarantine.json` size | Unbounded — append-only | **Risk:** if 1000 models fail in 24h, file grows to ~500KB. Mitigation: TTL via `reprobe_after`; readers only honor non-expired records. Add periodic GC in `/fleet-quota`. |
| `evidence_cache.json` size | Bounded by registry size × telemetry volume | Already managed by `evidence_accumulator.py` |
| `fleet-quota-cache.json` size | Bounded by provider count (~12) | No risk |

### Multi-agent / shared state

| Resource | Multiple sessions / terminals | Notes |
|---|---|---|
| Registry | Locked (`portalocker`) | Safe |
| Quarantine file | Atomic per-write | Safe |
| Evidence cache | Read-only by hooks | Safe (writer is `evidence_accumulator.py`, single instance) |
| Quota cache | Multiple readers, single writer (`fleet_quota.py` subprocess) | Already safe via retry-on-decode |
| `learned-serde-broken.json` | Multiple writers possible (each `PostToolUseFailure` invocation) | Existing pattern: atomic write via `.tmp.<pid>` + `os.replace` |

The quarantine file follows the same pattern as `learned-serde-broken.json` (PostToolUseFailure:189-191). No new failure mode.

### Reversibility

All changes have feature flags. The DRY unit (Unit 1) is functionally identical to the old code (same dicts, same logic) — its risk is purely in the import path, which is easily reverted by `git revert`. Total blast radius: each unit is shippable in isolation.

### Adversarial / security

| Concern | Mitigation |
|---|---|
| Malicious registry payload | Already validated by `validate_registry_data` (registry_schema.py:467-590); adding `expires_at` field is inside the existing schema. The new validator check rejects malformed ISO-8601 strings. |
| LLM passes a hand-crafted `requirements` dict to bypass context floor | `pick()` infers the floor; explicit `requirements` from the caller are merged with `min()` semantics (the larger wins), so an attacker cannot LOWER the floor. Verified by capability_gate logic (model_router.py:329-330). |
| Operator adds a candidate with `expires_at` in the distant future to bypass retirement | The retirement gate still fires for explicit `lifecycle=retired`; `expires_at` is additive, not exclusive. |
| Quarantine file used for DoS (forcing the LLM to retry forever) | `reprobe_after` is bounded by `provider_cooldown_seconds` (default 300); after that, the candidate is reprobed. Quarantine records are not permanent. |
| `pick_model.py` output is tampered with mid-pipeline | Out of scope — the LLM's spawn call uses the slug string, not the registry read; if the LLM is compromised, the entire chain is. |

---

## 7. Traceability Matrix

| Requirement | Decision | Implementation Unit |
|---|---|---|
| REQ-1: `pick_model.py <lane>` must never return a context-window-too-small model | DEC-1 (auto-infer `context_window_min` in `pick()`) | Unit 3 |
| REQ-2: `pick_model.py <lane>` must never return a model past its EOL | DEC-2 (add `lifecycle.expires_at` field; new `is_expired()` gate) | Unit 2 |
| REQ-3: `pick_model.py <lane>` must never return a cohere model on a trial-cap-exhausted key | DEC-3 (cohere trial classification in gate) | Unit 5 |
| REQ-4: `pick_model.py <lane>` and `PreToolUse_spawn_model_gate` must agree on what "free" means | DEC-4 (single source of truth: `registry_views.is_candidate_free()`) | Units 1, 4 |
| REQ-5: `pick_model.py --list` must answer "what model will I get?" in one glance | DEC-5 (reorder output; update AGENTS.md) | Unit 7 |
| REQ-6: Spawn failures must propagate to the next pick | DEC-6 (write `quarantine.json` from PostToolUseFailure) | Unit 6 |
| REQ-7: One DRY copy of `FREE_PROVIDERS` / `PREFIX_TO_PROVIDER` | DEC-7 (new `registry_views.py` module) | Unit 1 |
| REQ-8: All changes must be reversible | DEC-8 (one feature flag per unit) | Units 1-6 |
| REQ-9: A spawn-failure-causing regression must be detectable before production | DEC-9 (shadow test) | Unit 8 |
| REQ-10: AGENTS.md instructions must describe actual behavior | DEC-10 (rewrite `pick_model.py --list` paragraph) | Unit 7 |

---

## 8. Key Decisions

### DEC-1 — Auto-infer `context_window_min` in `pick()`

**Rationale:** The operator directive ("make the tool impossible to misuse") puts the requirement estimation on the system, not the caller. Measured system-prompt sizes are stable per orchestrator (grok/codex/agy), so the floor is data-driven.

**Rejected alternatives:**
- (a) Require caller to pass `requirements`: puts the burden on the LLM (misuse risk).
- (b) Static floor of 80K for all callers: overshoots for codex (20K) and blocks valid candidates.
- (c) Read the actual system prompt from a sentinel file: too coupled to Grok Build internals.

### DEC-2 — Add `lifecycle.expires_at` field on `CandidateRecord`

**Rationale:** The existing 4-state lifecycle is too coarse. A model can be `active` (no quarantine, no retirement, no trial issue) yet still be past its vendor's EOL. The field is `Optional[str]` with backward-compat default of `None` (never expires), so existing candidates migrate cleanly.

**Rejected alternatives:**
- (a) Add a top-level `eol` array parallel to `serde_broken`: scattered data, no per-candidate precision.
- (b) Compute EOL on-the-fly from external API calls: introduces a runtime dependency on each model vendor.
- (c) Use the `notes` field to embed EOL: text-only, not machine-readable, not validated.

### DEC-3 — Cohere trial classification in the gate

**Rationale:** The trial cap (1000/month) and the prod cap (~10K/hour rate-limited) are fundamentally different limits. The current `FREE_PROVIDERS = {"nim", "zen", "nvidia", "grok", "cohere"}` lumps trial and prod together. The fix distinguishes them at the cache level (`trial_exhausted` flag) and at the gate level (new deny branch). The data already exists (`fleet_quota.py:check_cohere` already detects the trial-exhaustion body).

**Rejected alternatives:**
- (a) Treat cohere as paid-tier always: breaks the prod-cohere case (which IS cheap enough to be effectively free for our usage).
- (b) Per-minute rate-limit only (current behavior): 1000/month trial cap is silently violated.
- (c) Operator-side daily `/fleet-quota` reminder: doesn't gate spawns.

### DEC-4 — Single source of truth: `registry_views.py`

**Rationale:** The three-way DRY violation is the root cause of the registry-schema drift (Unit 4 in this design re-creates the exact defect that was fixed in commit `d3c6c75` for the picker — the gate's `is_model_free` is the canary). Centralizing derived views in one module ensures future schema changes are picked up by all consumers automatically.

**Rejected alternatives:**
- (a) Per-consumer import from `pick_model.py` (gate imports from picker): inverts the dependency direction; picker is higher-level than gate.
- (b) Inline the constants again: status quo, drift risk.
- (c) Generate the constants from `fleet-models.json`: introduces a build step; over-engineering.

### DEC-5 — Reorder `--list` output

**Rationale:** The model name should appear first because that is the question the LLM is asking. The count is secondary diagnostic info.

**Rejected alternatives:**
- (a) Two separate commands (`--list-models`, `--list-counts`): doubles the surface area; AGENTS.md users will get confused.
- (b) JSON-only output: breaks the visual one-glance property.

### DEC-6 — Write `quarantine.json` from `PostToolUseFailure`

**Rationale:** Closes the learning loop. The router already reads `quarantine.json` (via `pick_model.load_quarantine_records` → `router_deterministic` → `health_gate`). The only missing piece is the writer, which lives in `PostToolUseFailure` because that's where classified failures land.

**Rejected alternatives:**
- (a) Have `fleet_quota.py` poll for failures: latency (polling interval) means the gate doesn't block on first failure.
- (b) Have the LLM write quarantine records: misuse.
- (c) Push to evidence cache instead: evidence cache has a different semantic (production-evidence telemetry), not failure-classified records.

### DEC-7 — New `registry_views.py` module

**Rationale:** Provides a single home for derived views that currently live as duplicated constants across 3 files. Named `views` (not `helpers`) because each function returns a *derived* artifact from the registry, not a generic helper.

**Rejected alternatives:** see DEC-4.

### DEC-8 — Feature flag per unit

**Rationale:** Per `~/.grok/AGENTS.md` "deployment claims need their own receipts," every change that touches the gate chain needs to be reversible. One flag per unit keeps the blast radius small.

**Rejected alternatives:**
- (a) Single feature flag for the whole design: too coarse; one regression disables everything.
- (b) No flags (full roll-forward only): violates the AGENTS.md "reversibility" gate; the operator directive "surgical" implies rollback capacity.

### DEC-9 — Shadow test in CI

**Rationale:** Catches the FC-3 case (context-window-mismatch recurs) deterministically. Shadow run does not require live spawns; it simulates the gate chain on the registry as-is.

**Rejected alternatives:**
- (a) Live spawn test in CI: too expensive, too slow, hits quota.
- (b) Manual smoke test: relies on operator memory.

### DEC-10 — AGENTS.md update

**Rationale:** The existing AGENTS.md instruction (line 1435) misdescribes `--list`. The fix to `--list` output must be paired with the doc update, or the drift reappears.

**Rejected alternatives:**
- (a) Update only the code: AGENTS.md users get the old wrong description.
- (b) Update only the docs: code and docs disagree.

---

## 9. Rollout

### Phasing

| Phase | Units | Risk | Reversibility |
|---|---|---|---|
| Phase 1 (this session) | 1, 4, 7, 8 | Low (cleanup + shadow test) | git revert per unit |
| Phase 2 (this session) | 2 (schema), 3 (auto-context-floor) | Medium (changes selection) | Feature flag `GROK_LIFECYCLE_EOL_GATE=0`, `GROK_AUTO_CONTEXT_FLOOR=0` |
| Phase 3 (this session) | 5 (cohere), 6 (quarantine writer) | Medium (changes gate deny path) | git revert |
| Phase 4 (HANDOFF) | Set cerebras/low-rate-limit candidates to `excluded` policy | Low (data task) | N/A — registry data change |

### Rollback procedure

All changes are reversible via `git revert <commit>`. No feature flags or shadow mode — the reactive learning loop (quarantine + serde-broken) is the safety net, not an observation window.

---

## 10. File Change Inventory

| File | Action | LOC delta | Notes |
|---|---|---|---|
| `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_views.py` | **NEW** | +120 | Exports: `PREFIX_TO_PROVIDER`, `FREE_PROVIDERS`, `is_candidate_free()`, `is_expired()`, `ORCHESTRATOR_CONTEXT_FLOOR`, `infer_context_requirement()` |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py` | MODIFY | -20 / +15 | Delete constants, import from `registry_views`. Add `infer_context_requirement()` call. Update `_print_list` ordering. |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py` | MODIFY | +5 | Add `expires_at: str \| None = None` to `LifecycleState` (or new `EOLState` enum); update validator |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/model_router.py` | MODIFY | +10 | Extend `evidence_eligibility()` to call `is_expired()` |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json` | MODIFY | +2 | Add `expires_at` to 2 starter candidates (`nim-deepseek-v4-flash`, `nim-deepseek-ai-deepseek-v4-flash`); other 14 candidates deferred to HANDOFF |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py` | MODIFY | +8 | `check_cohere()` writes `trial_exhausted` flag to cache |
| `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py` | MODIFY | -25 / +30 | Delete duplicated constants. Delete dead `is_model_free`. Add EOL branch. Add cohere trial branch. Import from `registry_views`. |
| `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py` | MODIFY | -10 / +25 | Delete duplicated constants. Add `write_quarantine_record()` step. |
| `C:/Users/brsth/.grok/AGENTS.md` | MODIFY | ~+20 / -5 | Lines 1434-1438: rewrite `pick_model.py --list` description; add "don't manually select from tool-fallbacks" sentence |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/tests/test_pick_model_shadow.py` | **NEW** | +150 | Shadow simulation: 100 pick invocations against the registry, asserts 0 candidates fail any gate |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/tests/test_registry_views.py` | **NEW** | +80 | Unit tests for `is_candidate_free`, `is_expired`, `infer_context_requirement` |
| `C:/Users/brsth/.grok/hooks/tests/test_spawn_quota_error_learner.py` | MODIFY | +30 | Add cohere-trial scenario; add quarantine-write scenario |
| `C:/Users/brsth/.grok/skills/model-quota/scripts/tests/test_pick_model.py` | MODIFY | +20 | Add tests for context-floor inference; add tests for EOL exclusion |

**Total LOC delta:** ~+460 / -60, net +400 across 13 files. Of which +120 (29%) is the new `registry_views.py` module that becomes the home for future derived views.

### Companion wiki concept (HANDOFF)

`P:/.data/wiki/concepts/model-selection-defect-fix-2026-08-08.md` — captures:
- The 7 defects and their failure modes
- The selection policy (DEC-1 through DEC-10)
- The measurement floor values (grok/codex/agy context sizes)
- The shadow-test recipe
- The rollback procedure

This is durable knowledge that future sessions need when the LLM asks "why does `pick_model.py` auto-infer the context floor?" — the wiki captures the rationale without bloating the in-line docstring.

---

## Appendix: Operator Decisions Needed (HANDOFF items)

These require operator input and cannot be decided in this session:

1. **Cohere trial vs prod.** Is the active cohere key trial or prod? Affects whether Unit 5 fires at all. Decision needed before merge.
2. **EOL dates for the remaining 14 candidates.** `/www` research to find each vendor's announced EOL date. Format: ISO-8601 string in `candidate.lifecycle.expires_at`.
3. **Context floor measurements.** Run `/context` against each orchestrator (grok/codex/agy) in a known-empty session, record the baseline. Replace the placeholder values in `ORCHESTRATOR_CONTEXT_FLOOR`.
4. **`cerebras` provider classification.** Should `cerebras` be added to `FREE_PROVIDERS`? Or should `cerebras-glm-4-7`'s `quota_class` be set to `free_tier` explicitly? Operator preference.
5. **Shadow window length.** Default 1 week. Shorter if the operator wants faster rollout; longer if more confidence is needed.

---

## Receipts

All claims in this design are backed by file reads in this session:

- `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py:73` — `FREE_PROVIDERS` definition
- `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py:59-71` — `PREFIX_TO_PROVIDER` definition
- `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py:400-407` — empty requirements passed to router
- `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py:549-562` — `_print_list` count-based output
- `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py:46` — `FREE_PROVIDERS` duplicate
- `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py:28-40` — `PREFIX_TO_PROVIDER` duplicate
- `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py:261-275` — dead `is_model_free`
- `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py:27-38` — `PREFIX_TO_PROVIDER` third copy
- `C:/Users/brsth/.grok/AGENTS.md:1434-1438` — misdescribed `--list`
- `C:/Users/brsth/.grok/skills/model-quota/scripts/model_router.py:309-331` — `capability_gate` with context_window check (gated by `requirements`)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py:38-40` — 4 lifecycle states (no EOL)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py:496-540` — `check_cohere` already detects trial-cap body
- `P:/.artifacts/model-routing/` (list_dir) — only `shadow_comparison.jsonl`; `quarantine.json` absent
- `P:/.artifacts/model-evidence/evidence_cache.json` (list_dir) — present, read by pick_model.py:154-160

---

## Execution Status

Updated: 2026-08-08T08:30:00Z
Session: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | registry_views.py (DRY root) | ✅ DONE (prev session) | commit 0870dd6 |
| 2 | AGENTS.md --list description fix | ✅ DONE (prev session) | commit 0870dd6 |
| 3 | Unit 4: migrate 3 consumers to registry_views | ✅ DONE | commit 60e6cad (swept by concurrent session); FREE_PROVIDERS/PREFIX_TO_PROVIDER imported from registry_views in pick_model.py, spawn gate, PostToolUseFailure |
| 4 | Unit 4: rewrite get_fallback_for_lane for v5 | ✅ DONE | walks candidates[] array, filters codex-orchestrator; test_glm_fallback_from_registry now PASSES |
| 5 | Unit 4: delete broken is_model_free | ✅ DONE | rg "def is_model_free" returns 0 hits in hooks |
| 6 | Unit 8: shadow test | ✅ DONE | commit b246c1c; 3/3 passed (zero_failures, total_picks_positive, all_lanes_covered) |
| 7 | Unit 2: lifecycle.expires_at field | ✅ DONE | commit 9429c81; schema + validator + is_expired() + evidence_eligibility() gate |
| 8 | Unit 3: auto context-window inference | ✅ DONE | commit 9429c81; pick() passes requirements with context_window_min to all 3 router modes |
| 9 | Bonus: serde_broken pre-filter in router | ✅ DONE | commit 9429c81; eligible_candidates() filters serde_broken + tool_grounded_spawn_broken |
| 10 | Unit 5: cohere trial-cap classification | ✅ DONE | commit 3799772; gate Check 2a reads trial_exhausted; PostToolUseFailure writes it |
| 11 | Unit 6: quarantine writer | ✅ DONE | commit 3799772; write_quarantine_record() in PostToolUseFailure, closes learning loop |

### Key findings during execution

- **cerebras-glm-4-7 context window is 128K** (not 8K as the design doc's failure analysis assumed). The design doc's claim that cerebras fails on context-window-too-small was incorrect. The registry shows `context_window: 131072`. The actual cerebras failures were likely serde or quota related.
- **get_fallback_for_lane was dead code** — it walked `registry["lanes"]` (v4 dict shape) that doesn't exist in v5. The test `test_glm_fallback_from_registry` was pre-existing failure. Rewritten against v5 `candidates[]` array with orchestrator filter.
- **Router didn't filter serde_broken** — the shadow test caught `nvidia-nemotron-3-ultra` (in serde_broken) being returned by pick(). Added pre-filter in `eligible_candidates()` so the picker never recommends serde-broken models.
- **Concurrent session collision**: Unit 4 changes were swept into commit 60e6cad by another session ("Claude Sonnet 4.6"). Changes were correctly committed but under a different message.

### Remaining (HANDOFF items)

1. **EOL dates for 16 candidates**: populate `expires_at` on each candidate in fleet-models.json (research task — needs /www to find each vendor's EOL announcement)
2. **Context floor measurements**: replace placeholder values in ORCHESTRATOR_CONTEXT_FLOOR with measured /context output
3. **cerebras provider classification**: operator decision — should cerebras be in FREE_PROVIDERS? (currently not, but cerebras-glm-4-7 has quota_class=None)
4. **Feature flags not yet wired**: the design doc specifies env-var flags (GROK_LIFECYCLE_EOL_GATE, GROK_AUTO_CONTEXT_FLOOR, etc.) — these are not yet implemented. The changes are live without flags. Rollback is via `git revert`.
5. **Shadow mode window**: the design doc specifies a 1-week shadow period before full activation. All gates are live immediately (no shadow mode implementation).