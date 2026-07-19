# Option A Design: Successful Local Coding on Ornith

**Status:** design only — not authorized for live `config.json` or production behavior change  
**Updated:** 2026-07-16  
**Parent:** `P:/docs/ccr-model-routing-optimization-handoff.md`  
**Runtime pin:** CCR `@musistudio/claude-code-router@2.0.0` (re-verified: custom non-null route → `scenarioType="default"`)  
**Discovery:** `P:/tmp/source-discovery-option-a.json` (`needs_review` = mechanical multi-file grouping, not a competing active plan)

This document is the agreed program after Option A selection plus a later
routing-contract critique. It contains only positions accepted for planning.
Disagreements and deferred items are listed in §12 so they are not silent.

---

## 1. Goal (agreed)

> Maximize **successful** local coding work on Ornith—without sacrificing role
> quality, causing context failures, or making terminal lifecycle unpredictable.

**Optimization target:** successful local coding rate (local completion that
does not require rework on a stronger model), **not** raw Ornith utilization.

“Use Ornith as much as possible” remains a useful **constraint** (prefer local
when safe and role-correct). It must not become the objective function, or the
router will inflate local share via misclassification or marginal contexts.

Supporting constraints:

- Ornith is **coding-only** (role gate), not “anything that fits.”
- Prefer local when the request is affirmatively coding **and** total capacity
  admits it **and** lifecycle is healthy.
- Degrade deliberately, visibly, and without same-route retry or silent privacy
  boundary crossings.
- Original Claude request stays immutable for cloud / CCR fallback; any local
  projection is provider-local only.

Non-goals:

- Permanent “best model” leaderboard without task-shaped benchmarks.
- Promoting Nemotron Ultra/Super (or other candidates) from availability probes.
- Mutating `req.body` in `ccr-custom-router.js` before CCR fallback inherits it.
- Optimizing for local route count alone.

---

## 2. Verified runtime facts (agreed authority)

| Fact | Evidence | Implication |
|---|---|---|
| Ornith is in `fallback.background` | Live `config.json`: `llama-cpp,ornith-1.0-9b` | Violates coding-only contract |
| Unrecognized work defaults to `coding` | `ccr-custom-router.js` `inferTaskType` → `return "coding"` | “Coding only” is weaker than intended |
| CCR `tokenCount` is input-side (messages/system/tools), not `max_tokens` | CCR 2.0.0 dist tokenizer path | Local 90% gate does not prove comfortable fit |
| Local admit uses `tokenCount <= maxContext * threshold` (aggressive 0.90) | custom router ~L588–591 | ~58,982 / 65,536 leaves ~6.5k headroom if input alone—output ignored |
| Admission proxy adds `max_tokens` but cloud ceiling path; Ornith is outside cloud-route set | `ccr-admission-proxy.js` + `ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY` | Neither gate alone proves Ornith fit |
| Custom router non-null → `scenarioType="default"` | CCR 2.0.0 middleware | Error recovery mostly uses `fallback.default` |
| `fallback.default` starts with DeepSeek; same string as `LOCAL_FAIL_FALLBACK` | Live config + custom router | DeepSeek can be primary and first error-recovery candidate |
| NVIDIA appears in automatic `fallback.longContext` | Live config | Privacy/policy risk without sensitivity gate |
| Phase 0 wait grace + routingMode display helpers exist; unit tests pass | `cc-ccr.ps1`, 12/12 Pester | Automated only; live cold-start visual still required for “finished” |

---

## 3. Required-now gaps (agreed)

| Priority | Gap | Required direction |
|---|---|---|
| Required now | Ornith in non-coding fallback (`background`) | Remove Ornith from every non-coding primary and fallback chain |
| Required now | Default-to-coding classification | Require **affirmative** coding evidence; low-confidence → role-appropriate cloud |
| Required now | Local admission ignores requested output | Admit on **total budget**: input + output allowance + measured margin |
| Required now | 90% heuristic as “comfortable fit” | Replace with explicit per-request capacity calculation (margin measured, not dogma) |
| Required now | Structured observability | One fallback reason enum (see §5) |
| Required now | Hidden `routingMode` default | Make `routingMode: aggressive` **explicit** in config (after human checkpoint) |
| Required now | Phase 0 “finished” claim | True cold-start **visual** + concurrent two-terminal acceptance before calling lifecycle work done |
| Before pilot | `cc-ccr` can globally kill Ornith launchers / watchers / `llama-server` | Single machine-scoped lifecycle owner; terminals request/observe, do not free-kill by cmdline match |
| Before pilot | State lacks ownership fields | Owner PID, generation ID, state, endpoint, timestamps, last failure |
| Before production | Fixtures incomplete vs live `DEAD → STUCK/BROKEN → LOADED` | Capture live transitions → regression + concurrency tests |
| Later | Monitor not routing-aware | Surface last route decision / fallback reason / light throughput—render authority, do not invent it |

---

## 4. Role policy (agreed operating baseline)

Baselines for **normal** routing—not proof that each model is globally “best.”

| Role | Primary | Normal escalation | Notes |
|---|---|---|---|
| **Coding** | Ornith when affirmatively coding + total-budget eligible + local healthy | DeepSeek V4 Flash for **local-fail** paths (busy/unavailable/over-context under current cost policy) | Explicit user pin `claude-local-ornith` always allowed |
| Reasoning / planning | GLM 5.2 | M3 | Never Ornith merely because tokens fit |
| General / default | MiniMax M3 | GLM or free M3 (visible degradation) | — |
| Background / fast | DeepSeek V4 Flash | M3 when low-stakes assumption fails | Ornith **never** automatic background recovery |
| Long context | Preserve underlying **role** model | Role-matched cloud (M3/GLM) | Context size alone does not redefine role (see §12 on MiMo) |
| NVIDIA Ultra/Super | No automatic role | Manual non-confidential canary only | Demote from automatic `longContext` fallback at config checkpoint |

**Coding-only enforcement (agreed):**

- Primaries: only coding / explicit local pin.
- Fallbacks: Ornith must not appear on background/think/longContext/default recovery chains unless the recovery policy is explicitly “retry local coding pack” (future, not current).
- Live violation today: `fallback.background → llama-cpp,ornith-1.0-9b`.

---

## 5. Routing-contract hardening (agreed first implementation slice)

Do this **before** coding-pack projection and before multi-terminal pilot.

### 5.1 Work items

1. **Config (human checkpoint, precise diff before apply)**  
   - Remove Ornith from non-coding fallbacks (minimum: `fallback.background`).  
   - Set explicit `"routingMode": "aggressive"` (or chosen mode) in CCR config so display and code agree.  
   - Prefer also demoting NVIDIA from automatic `longContext` recovery in the same checkpoint (privacy).

2. **Classification**  
   - Affirmative coding signals only for automatic Ornith.  
   - Low-confidence / unrecognized → cloud role default (M3 general), **not** Ornith and **not** silent “coding.”  
   - Preserve explicit Ornith model/pin override.  
   - Accept temporary drop in raw local rate until classifier calibration; success rate is the KPI.

3. **Total-context local admission**

   ```text
   input_tokens                    # CCR tokenCount or better tokenizer
   + requested_output_budget       # max_tokens / local output cap policy
   + tokenizer_serialization_margin
   <= live_Ornith_n_ctx
   ```

   - Fail closed when uncertain; log “would have been local” for margin tuning.  
   - Do not permanently hardcode 90% or a blind 16k reserve without measuring utilization cost.  
   - If Claude often requests large `max_tokens` but uses little, measure rejected opportunity, then consider a **documented local output cap** rather than weakening safety.

4. **Structured fallback reasons** (single enum in route log)

   `non-coding` | `low-confidence` | `busy` | `unavailable` | `over-context` | `probe-failure`

   (Plus future: `pack-insufficient`, `queue-timeout` when pack/queue land.)

5. **Tests**  
   - Unit/integration for classification defaults, Ornith exclusion from non-coding paths, total-budget boundary cases.  
   - Do not treat green unit tests as cold-start visual acceptance.

### 5.2 Error-recovery constraint (agreed, config-limited)

CCR 2.0 still maps custom-router hits to `fallback.default` and does not strip the failed route. Therefore:

- Normal local-fail **primary** may remain DeepSeek for cost.  
- **Error recovery** must not assume `fallback.think` / `longContext` protect custom-routed traffic.  
- Same-route DeepSeek retry remains a real risk until exclusion or a safer `fallback.default` is applied under checkpoint.  
- Reorder of `fallback.default` is optional Phase 0.5 hygiene (see §9); it is not a substitute for total-budget admission or classification.

---

## 6. Lifecycle ownership (agreed before pilot)

Current `cc-ccr` global cleanup of processes matching launcher/llama cmdline patterns is a **tactical** fix for duplicate supervisors. It is **not** a durable ownership model.

Target:

- One authoritative Ornith supervisor per machine (restartable/disposable—not a frozen SPOF).  
- Machine-scoped mutex / ownership record.  
- Generation ID + owner PID + endpoint + state + timestamps + last failure.  
- Operations: start, observe, restart, stop—owned by supervisor.  
- `cc-ccr` is a **client**: probe → request start if absent → wait → continue.  
- Never kill processes solely because the command line contains a matching filename.

Acceptance for this slice:

- True cold-start visual run (monitor alignment, readiness messages truthful).  
- Concurrent two-terminal test without double-supervisor races or cross-terminal kills.

Keep existing cleanup only until the owner path exists; do not delete tactical cleanup without replacement.

---

## 7. Coding pack (agreed Phase 1 after contract hardening)

Still required: long Claude sessions make full-transcript `tokenCount` exclude Ornith even when the **task** fits.

```text
immutable original ──► cloud / CCR fallback always
        │
        └─ affirmative coding + total-budget on PACK (not full session)
              → route-specific llama-cpp projection only
```

Pack contents, PackManifest, sufficiency, and comfort-window canaries (24k/32k/48k measured—not arithmetic “49k”) remain as previously designed. Hard invariant: cloud must never inherit only the reduced pack.

**Sequencing (agreed):** routing-contract hardening → cold-start/concurrency gate → coding pack pilot → lifecycle owner at scale → scorecard tuning.

Without the pack, contract hardening improves correctness of *who* goes local but still under-uses Ornith on fat terminals.

---

## 8. Scorecard (agreed)

Primary KPI: **successful local coding rate**  
(local completion without forced stronger-model rework)

Also track:

- Coding requests eligible for local  
- Eligible actually routed local  
- Fallback counts by reason enum  
- Context-limit errors  
- Local latency / throughput  
- Escalations / retries to stronger models  
- Duplicate-process incidents  
- Cold-start readiness time  
- Estimated cloud usage avoided (secondary)

A local route that must be redone on M3/GLM is **not** a saving.

---

## 9. Fallback arrays — design only (agreed direction)

Not applied live. Shown for checkpoint-ready diffs later.

| Array | Agreed direction | Why |
|---|---|---|
| `fallback.background` | Remove Ornith; prefer M3 then free M3 (or DeepSeek-compatible cloud only) | Coding-only contract |
| `fallback.longContext` | Remove automatic NVIDIA | Privacy / unproven auto use |
| `fallback.default` | Prefer no same-route DeepSeek-first when DeepSeek is a common primary | Error recovery hygiene under `scenarioType=default` |
| `fallback.think` | Leave quality-preserving M3/free chain unless evidence says otherwise | Built-in think path only |

Precise live diff requires human approval before edit.

---

## 10. Phase plan (agreed order)

### Phase 0 — Launcher readiness (in tree; not fully accepted)

- [x] Wait grace for cold-start DEAD/STUCK/BROKEN; LOADED sufficient  
- [x] routingMode empty → `aggressive (default)` display; Pester 12/12  
- [ ] Live visual cold-start acceptance  
- [ ] Concurrent two-terminal acceptance  

### Phase 0.5 — Routing-contract hardening (next code slice)

- [ ] Affirmative coding classification + tests  
- [ ] Total-budget local admission + tests  
- [ ] Structured fallback reasons in route log  
- [ ] Config diff prepared for human checkpoint (Ornith out of background; explicit routingMode; NVIDIA demotion preferred)  

### Phase 1 — Coding pack

- [ ] Packer + manifest + sufficiency  
- [ ] Provider-local projection; immutable original for cloud  
- [ ] Discriminating tests (80k session / 15k pack → local, etc.)  

### Phase 2 — Lifecycle owner

- [ ] Supervisor ownership record + client-mode `cc-ccr`  
- [ ] Remove free global kill-by-name once owner is proven  

### Phase 3 — Route-aware error recovery + honest ceilings

- [ ] Failed-route exclusion; context-class handling  
- [ ] Demote unverified 1M labels; measure operational ceilings  

---

## 11. Red-team notes (agreed)

- Positive coding classification may reduce Ornith use initially—acceptable until calibrated.  
- Total-budget admission may over-reject when `max_tokens` is inflated—measure opportunity cost; prefer local output cap over weak safety.  
- Monitor must render authoritative state/events, never invent a second source of truth.  
- Keep-warm vs idle shutdown is an explicit user policy, not accidental process death.  
- Legacy noncanonical launchers (e.g. conflicting 32k assumptions) must leave the operational path or be clearly marked noncanonical.

---

## 12. Not adopted or only partially accepted

These were proposed or previously sketched; they are **not** treated as agreed plan of record.

| Item | Stance | Why |
|---|---|---|
| MiMo as default long-context **primary** | **Not adopted** | Availability/spec ≠ retrieval/tool proof; long-context keeps **role** model until measured |
| Coding escalation always DeepSeek even when pack insufficient for hard multi-file work | **Partial** | DeepSeek OK for local-fail/cost; hard coding that fails *sufficiency* may need M3—policy split by **reason**, not one forever path |
| “Use Ornith as much as possible” as the optimization objective | **Rejected** | Inflates utilization; success rate is the objective |
| Blind permanent 16k output reserve or permanent 90% | **Rejected** | Measure margin; capacity formula may *include* a tuned margin |
| Coding pack as the *first* change | **Reordered** | Contract hardening first; pack remains mandatory later |
| Pure fallback reorder as the solution | **Rejected as sufficient** | Needed hygiene only; does not fix classification, total budget, or custom→default recovery |
| Deleting global cleanup before owner exists | **Rejected** | Keep tactical cleanup until client/owner path is proven |
| Nemotron auto emergency roles | **Not adopted** | Manual non-confidential canary only |

---

## 13. Claim ledger

| Claim | Type | Action allowed |
|---|---|---|
| Ornith is background fallback | verified fact | Config change after human checkpoint |
| Unknown work defaults to coding | verified fact | Classification hardening under tests |
| tokenCount excludes max_tokens; 90% does not prove fit | verified fact | Total-budget admission design → implement |
| Successful local coding rate is the right KPI | agreed policy | Scorecard |
| Custom route → fallback.default | verified fact (CCR 2.0.0) | Recovery design must not assume think/longContext |
| One lifecycle owner eliminates races | hypothesis | Implement + adversarial two-terminal test |
| Live visual cold-start is correct | unverified | Required acceptance run |
| Coding pack raises successful local rate on fat sessions | hypothesis | Phase 1 after contract hardening |

---

## 14. Authorization boundary

**Allowed now:** design/doc updates; tests against non-live behavior; prepare config diffs.  

**Requires explicit human OK:**

1. Apply live `config.json` (Ornith/background, routingMode, NVIDIA, optional default fallback reorder).  
2. Implement Phase 0.5 code in `ccr-custom-router.js` / related.  
3. Implement coding pack projection.  
4. Lifecycle owner replacing global kill.  

**Not authorized:** silent production config edits; request-body rewrite in the custom-router return path; Nemotron/MiMo promotion.

---

## 15. Recommended next move

Bounded **routing-contract hardening** under tests, then one true cold-start and a concurrent two-terminal test. Production `config.json` changes shown as a precise diff before apply.
