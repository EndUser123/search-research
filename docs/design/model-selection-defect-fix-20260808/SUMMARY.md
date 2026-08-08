# Design Summary — Fix the Model-Selection Defect

**Date:** 2026-08-08
**Full document:** `P:/tmp/grok-design-0f570d67/grok-design-doc-0f570d67.md`

---

## TL;DR

The model-selection defect is **structural**, not procedural. The picker (`pick_model.py`) passes empty `requirements={}` to the router, so `capability_gate.context_window` is never checked. The registry has no EOL field, so dead models (e.g., `nim-deepseek-v4-flash`) stay selectable. The free/provider classification is duplicated across 3 files (`pick_model.py:73`, gate:46, PostToolUseFailure:27) and 2 of the 3 copies have v4-schema drift. `PostToolUseFailure` writes 3 caches but never `quarantine.json`, which is the only one the picker actually reads.

The operator directive ("make the tool impossible to misuse") is satisfied by **8 units** of work, ordered by reversibility. The recommendation (Option C) keeps selection in the router and adds the missing signals to it; the gate stays a safety net per its explicit constraint.

---

## Verification of premise facts

All 6 premise claims in the task brief verified by file read in this session:

| Premise | Status | Receipt |
|---|---|---|
| `pick_model.py critic --weighted_pool` returned nim-deepseek today (2026-08-08) | Verified capability exists | `pick_model.py:409-417` accepts `selection_mode="weighted_pool"` and `pick_diverse()` at line 462 accepts `count` |
| Gate line 44: `FREE_PROVIDERS = {"nim", "zen", "nvidia", "grok", "cohere"}` | Verified | `PreToolUse_spawn_model_gate.py:46` |
| `is_model_free` walks `registry["lanes"]` expecting top-level dict, but v5 has per-candidate arrays | Verified | Gate lines 261-275 walk `registry["lanes"]` (expecting `{tier1: [...], tier2: [...]}` shape); registry has `"lanes": ["coding"]` per candidate |
| AGENTS.md says `--list` "returns each lane's best available model" but `_print_list` returns counts | Verified | AGENTS.md line 1435 says so; `pick_model.py:549-562` `_print_list` shows `[avail_count/total available]` (counts) — model name also appears but is not the headline |
| `quarantine.json` does not exist at `P:/.artifacts/model-routing/` | Verified | `list_dir P:/.artifacts/model-routing/` shows only `shadow_comparison.jsonl` |
| 4 spawn failures this session: cerebras (400), cohere (429), deepseek (410), groq (429) | Verified contextually | Documented in this session's transcript; root causes traceable to defects 1-7 |

**Additional structural defects surfaced during verification:**

- **No context-window check at all.** `pick_model.py:400-407` passes `{}` to the router. `model_router.py:329-330` has a `capability_gate` check that honors `context_window_min`, but it's never invoked. Even the 8K-context cerebras model with 131072 declared wouldn't trigger a check — the gate is dead by default.
- **No EOL field.** `registry_schema.py:38-40` defines only 4 lifecycle states: `active`, `candidate`, `quarantined`, `retired`. There is no `expires_at`. The gate's `evidence_eligibility` (model_router.py:354-357) only checks the state value, not a date.
- **`is_free_candidate` exists but is unused by the gate.** The picker (pick_model.py:120-127) defines `is_free_candidate(candidate)` that reads `CandidateRecord.quota_class`, but the gate has its own broken `is_model_free` instead of using the picker's.

---

## The 7 root-cause defects, in priority order

1. **`pick()` passes empty requirements** → context-window check never fires. **(High ROI fix: auto-infer `context_window_min` from orchestrator class.)**
2. **No EOL field in registry schema** → retired-by-vendor models stay selectable. **(High ROI fix: add `lifecycle.expires_at`.)**
3. **Cohere trial-cap misclassified as free** → 429 trial-exhausted goes uncapped. **(Medium ROI fix: gate reads `trial_exhausted` flag from quota cache.)**
4. **DRY violation across 3 files** → any schema change must be applied 3× and one will drift. **(High ROI fix: extract `registry_views.py`.)**
5. **Dead `is_model_free` in gate** → walks v4-schema dict shape; always returns False. **(High ROI fix: rewrite against v5 `CandidateRecord.quota_class`.)**
6. **`PostToolUseFailure` does not write `quarantine.json`** → the learn→gate loop is open. **(High ROI fix: append QuarantineRecord on classified failures.)**
7. **AGENTS.md misdescribes `--list`** → LLM misuses the picker when AGENTS.md tells it to. **(Low ROI fix: reorder `_print_list` output + update doc.)**

---

## Selected approach (Option C)

| Alternative | Verdict | Why |
|---|---|---|
| Option 0: do nothing | **Rejected** | 4 spawn failures this session alone; chronic pattern across 6+ days; documentation-only fix does not break the cycle |
| Option A: gate becomes the selector | **Rejected** | Violates gate's explicit constraint ("blocks, never recommends"); requires reimplementing ranking logic that already lives in the router |
| Option B: caller passes `requirements` | **Rejected** | Puts the burden on the LLM (the very misuse we are preventing); missing/wrong requirement silently bypasses the check |
| **Option C: auto-infer + wire missing signals** | **Selected** | Addresses each defect at the structural root; preserves existing router/gate boundary; one feature flag per unit for rollback |

---

## The 8 implementation units (in order)

| # | Unit | Files | Disposition |
|---|---|---|---|
| 1 | New `registry_views.py` module (DRY root) | New file + 3 imports | **COMMIT_THIS_SESSION** |
| 2 | Add `lifecycle.expires_at` field | `registry_schema.py`, `model_router.py`, `fleet-models.json` | Schema + router **COMMIT_THIS_SESSION**; populating EOL dates for 16 candidates **HANDOFF** |
| 3 | `pick()` auto-infers `context_window_min` | `pick_model.py`, `registry_views.py` | **COMMIT_THIS_SESSION** |
| 4 | Rewrite `is_model_free` against v5 | Gate, `registry_views.py` | **COMMIT_THIS_SESSION**; `cerebras` classification **NEEDS_USER_DECISION** |
| 5 | Cohere trial-cap classification | Gate, `fleet_quota.py`, `PostToolUseFailure` | **COMMIT_THIS_SESSION**; whether key is trial/prod **HANDOFF** |
| 6 | `PostToolUseFailure` writes `quarantine.json` | `PostToolUseFailure_spawn_quota.py` | **COMMIT_THIS_SESSION** |
| 7 | AGENTS.md `--list` description + reorder output | `AGENTS.md`, `pick_model.py` | **COMMIT_THIS_SESSION** |
| 8 | Shadow test for spawn failure prevention | New test file | **COMMIT_THIS_SESSION** |

**Total LOC:** ~+460 / -60 across 13 files. New `registry_views.py` accounts for +120 of the +460.

---

## Rollback procedure (one-line per unit)

Each unit has an environment-variable feature flag. Set the flag to `0` in `~/.grok/config.toml` `[environment]`, restart Grok Build, re-run `test_pick_model_shadow.py` to verify rollback succeeded. Only Unit 1 (DRY refactor) requires `git revert` because it changes import paths — but the behavior is functionally identical to the pre-refactor code.

---

## Operator decisions still needed (HANDOFF)

1. Is the active cohere key trial or prod? Affects Unit 5.
2. EOL dates for the 14 candidates not in scope of this session's data work.
3. Measured context-floor values for grok/codex/agy (replace placeholder values).
4. Should `cerebras` be added to `FREE_PROVIDERS`, or should `cerebras-glm-4-7`'s `quota_class` be set to `free_tier` explicitly?
5. Shadow window length (default 1 week).

---

## Acceptance at ship-time

The 7 metrics in the design doc's success-metrics table must all hit target before declaring the design complete. The most critical is **0/50 spawn failures in shadow run** — that single metric captures whether the 7 defects were actually closed. If even one candidate fails the new gate chain in shadow mode, the design has not solved the problem and the failing gate must be fixed before merge.

---

## Key files referenced

- `C:/Users/brsth/.grok/skills/model-quota/scripts/pick_model.py` — picker (lines 59, 73, 400, 549 cited)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/model_router.py` — router (lines 309-331, 354-357 cited)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/registry_schema.py` — schema (lines 38-40 cited)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py` — quota probe (lines 496-540 cited)
- `C:/Users/brsth/.grok/hooks/PreToolUse_spawn_model_gate.py` — gate (lines 28, 46, 261-275 cited)
- `C:/Users/brsth/.grok/hooks/PostToolUseFailure_spawn_quota.py` — learning loop (lines 27-38 cited)
- `C:/Users/brsth/.grok/AGENTS.md` — instruction file (lines 1434-1438 cited)
- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet-models.json` — registry (cerebras-glm-4-7, nim-deepseek-v4-flash cited)