# Handoff: Mechanism-Inventory Manifest — Review for a Fresh LLM

**Date:** 2026-07-04
**Status:** Shipped, live, smoke-tested. Awaiting independent review.
**One-line ask:** Did shipping a permanent mechanism-injection hook actually fix the demonstrated fault, or did it add ceremony?

---

## 1. Why this exists (the fault it claims to fix)

The user reported two failures from a *different* LLM session running `/prospect`:

- **Fault A** — "I had to manually run `/prospect` to surface useful information." (Access problem: relevant knowledge wasn't reaching the model unprompted.)
- **Fault B** — "I had to follow up with 'I know we also have non-regex solutions'… because it was too narrow in its search." The other LLM defaulted to "expand the regex list" when `epistemic_validator`, `semantic_critic`, and `anti_dodge_judge` — non-regex detectors — already existed in the repo. (Mechanism-inventory blindness: nothing in the model's context said which mechanisms already exist.)

**Fault A** was already addressed earlier in the session by the CKS auto-injection hook (`cks_context.py`) and a migrated CKS DB. **Fault B** is what this handoff is about.

The shipped hook (`mechanism_manifest`) injects a short, glossed pointer-list of existing detection/retrieval mechanisms into every prompt, unconditionally, so the model knows what to reach for before proposing a new one.

---

## 2. What shipped

**Files touched (2):**

| File | Change |
|------|--------|
| `P:/.claude/hooks/UserPromptSubmit_modules/mechanism_manifest.py` | NEW. ~50 lines. Registers a UPS hook at priority 9.5 that emits the manifest as `additionalContext`. Kill-switch: `MECHANISM_MANIFEST_ENABLED=true` (default on). |
| `P:/.claude/hooks/UserPromptSubmit_modules/registry.py` | One line added to `core_hook_modules` list (~line 802): `"mechanism_manifest"`. |

**Injected content (603 chars):**

```
## MECHANISM INVENTORY — check before proposing new gates/detectors
Non-regex detection: epistemic_validator (Stop claim check), semantic_critic (cheap-model reasoning review), anti_dodge_judge (external judge for hook answers)
Claim gates: cross_validator (evidence for "fixed"/"done"), unverified_stance (empty hedges/doubt), fabrication_detector (fake tool-use), cks_quality_gate (LLM gate on CKS ingest)
Adversarial reviews: /red-team, /pre-mortem, /adversarial-review, /code-review
Search before assuming unreachable: /search, /prospect, sr MCP
Proposing a new gate/retriever? Grep this repo first.
```

**Design decisions the reviewer should pressure-test:**

1. **Unconditional inject** (not trigger-gated). Justified because Fault B struck on a general `/prospect` — trigger keywords like "gate/detector/enforce" would NOT have fired. The counter-cost is 603 chars on every prompt.
2. **Listed, not retrieved** (no RAG). Justified by the RAG-MCP scaling cliff (~10–20 tools): at ~12 mechanisms, listing wins; retrieval loses selection accuracy at this scale.
3. **Glosses added** (name + 4–6 word purpose). Justified by MCP/function-calling convention: a bare name tells the model a mechanism exists; a gloss tells it *when* to reach for each.
4. **Not in the weak-model skip list.** Justified because weak models are the population most prone to Fault B (defaulting to regex).
5. **Scaling-cliff comment** added in-module so future-us migrates to daemon-backed retrieval past ~20 mechanisms instead of appending forever.

---

## 3. What was rejected (and why) — the reviewer should confirm these calls

| Proposal | Rejected because |
|----------|------------------|
| **Step 1: daemon-hybrid retrieval for `cks_context`** | The premise was stale. A prior session claimed `cks_context` was "keyword-only" and the daemon was "0ms." Verified false this session: `_query_hybrid_corrections` (cks_context.py:193) and `_query_semantic_corrections` (line 96) already exist, gated behind `CKS_CORRECTION_SEMANTIC=false`. The daemon is irrelevant — the hook uses `CKS.search()` in-process. Deferred to the existing #1096/#1100 telemetry verdict rather than building on a wrong premise. |
| **Step 2: extend RAG injection to wiki + CHS** | Over-build. Fault B is a mechanism-inventory problem, not an access problem. RAG-injecting wiki prose is a gamble that the right page ranks; a short curated manifest aims directly at the fault. |
| **ToolRAG / Tool2Vec** | Scale not justified. We're at ~12 mechanisms; RAG-MCP's evidence says retrieval wins only past ~20. |
| **Memory file for the manifest** | The module docstring captures the why; a memory entry would duplicate it. |

---

## 4. Verification evidence (this session)

- `run_hooks({'user_prompt':'x'}, 'x')` returns the manifest alongside all other UPS hooks. `registered: True`, `priority: 9.5`, `chars: 603`, `has_glosses: True`.
- Kill-switch verified: `MECHANISM_MANIFEST_ENABLED=false` → manifest not emitted.
- `python -m py_compile mechanism_manifest.py registry.py` → `COMPILE_OK`.
- Live injection confirmed: the glossed block appeared in the *next* UserPromptSubmit's hook context after each edit (visible in the system-reminder injections during this session).
- Local hook loads from source — no plugin version bump or cache rebuild needed (per the repo's own "local hooks load from source" rule).

---

## 5. What the reviewer should actually check (ranked)

1. **Are the glosses accurate?** Each gloss is inferred from reading the mechanism's source this session, not from authoritative doc. Verify each against the actual source:
   - `epistemic_validator` → `Stop.py:554` (`_run_epistemic_contract`, the unified gate). NOTE: gloss corrected from "Stop claim check" to "Stop warn-mode structural/causal/claim checks" after verifying `Stop.py:779` ("owns structural, citation, causal, and comparative checks") and `test_epistemic_validator.py:14-16` (default mode = warn). `Stop.py:418` is only `build_local_summary_guidance`, one helper inside the contract flow.
   - `semantic_critic` → `Stop.py:456` (`_run_semantic_critic`, M3+Mistral per repo docs)
   - `anti_dodge_judge` → `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/anti_dodge_judge.py`
   - `cks_quality_gate` → `P:/.claude/hooks/scripts/cks/quality_gate.py` (built earlier this session, per handoff context)
   - `cross_validator`, `unverified_stance`, `fabrication_detector` → documented in `P:/.claude/hooks/CLAUDE.md` hook tables
2. **Is the manifest's mechanism set complete?** Are there non-obvious mechanisms the list omits that a model would reach for? (Candidate additions: `intent_artifact_alignment`, `observable_effect_verifier`/SEV, `/debrief`, `recursive_failure_detector`.) The list is deliberately curated, not exhaustive — but the curation line is a judgment call.
3. **Is unconditional inject the right call vs. the 603-char/prompt cost?** The honest counterexample: if `CLAUDE.md`'s hook table is already salient every turn, the manifest is redundant tokens. The defense is *salience + trigger* — the manifest co-locates inventory with "grep first." If injection-cost telemetry (#1100) later shows the manifest is being skipped or ignored, that's the cut signal.
4. **Is the scaling-cliff number sound?** "~20" comes from RAG-MCP (arXiv 2505.03275). Confirm our mechanism count is actually ~12 and the cliff claim is cited correctly in-module.
5. **Does this hook belong in the weak-model skip list?** (We said no.) Verify against `_DEFAULT_WEAK_MODEL_SKIP` in `registry.py`.
6. **Is #1122 scoped correctly?** The Stop-hook false positive that fired on a pure research-synthesis turn (see §6).

---

## 6. Open task

**#1122 — Fix Stop-hook Part C.1 false positive.** The `cc-aca-authority` Stop router fired `POLICY VIOLATION: Forbidden autonomous/background pattern detected (Part C.1)` on a research-synthesis turn that contained no `ScheduleWakeup`/`Monitor`/`CronCreate`/`run_in_background` and *explicitly recommended against* building an autonomous retriever. `ARCHITECTURE.md:106,164` maps Part C.1 to "unparseable command gate / Fundamental Unsolvability" — not autonomous/background — so the hook's label is mismatched or it's substring-matching prose like "daemon could index mechanism docs." The task scopes the fix: read the FORBIDDEN rule source, find the matcher, apply the shared `_indicator_match` lookaround fix (per memory `posttooluse_indicator_substring_rca.md`), verify against the triggering turn.

---

## 7. Falsification conditions (what would change the answer)

- The manifest is the **wrong** shape if Fault B recurs *despite* it — i.e., a model still proposes a new gate/retriever without grepping. That's the discriminating test; it will play out over subsequent sessions.
- Unconditional inject is **wrong** if injection-cost telemetry shows the manifest is tuned out (ceremony) — then cut glosses back to bare names or move to trigger-gating.
- Listing is **wrong** past ~20 mechanisms — then migrate to daemon-backed retrieval (the comment in-module names this path).
- The glosses are **wrong** if any one is inaccurate — fix the single line; don't re-derive the whole list.

---

## 8. Prior-session context the reviewer may need

This session also shipped (separate work, not part of this handoff's review scope but referenced by the manifest):
- **CKS DB migration** out of `P:/__csf/data/` into the search-research plugin `data/` dir.
- **`cks_quality_gate`** — capture-side LLM judge (cheap pool: pi/M3/glm) fronting all CKS ingest, calibrated against a known-junk negative corpus (109/109 rejected) and a curated-chunk positive corpus. This is one of the mechanisms the manifest lists. Plugin `search-research` bumped to 0.1.39.

---

## 9. Key files for the reviewer to open

- `P:/.claude/hooks/UserPromptSubmit_modules/mechanism_manifest.py` (the shipped hook)
- `P:/.claude/hooks/UserPromptSubmit_modules/registry.py:748-803` (`core_hook_modules` list)
- `P:/.claude/hooks/UserPromptSubmit_modules/cks_context.py:96-201` (the existing hybrid retrieval that made Step 1 unnecessary)
- `P:/.claude/hooks/CLAUDE.md` (hook tables — authoritative mechanism descriptions)
- `P:/.claude/hooks/ARCHITECTURE.md` (Part C.1 mapping — the #1122 mismatch)
