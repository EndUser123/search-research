---
thread_id: c8c91746-71fb-486f-97e1-4b0a918fe594
parent_handoff_path: none
current_session_id: 019fa94d-5608-7b21-b8d7-dbe609f92df3
current_terminal_id: console_38b8d474-5cd0-4bf1-a306-6a77
produced_at: 2026-07-28T17:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: fb4716e99714855fc7746b11e116cc5e2a4fcc0a
assigned_to: grok
assigned_at: 2026-07-28T17:30:00Z
assigned_by: 019fa94d-5608-7b21-b8d7-dbe609f92df3
---

# Auto model switch on rate limit (no user intervention)

## Objective

When a model (e.g. **glm-5-2**) hits a **rate limit / 429 / capacity halt**, automatically continue work on another model or transport **without the operator manually switching**, across both (1) **parent session** turns and (2) **spawn_subagent / skill-dispatched** children.

## Status

OPEN — partial patterns exist (skill-prose pools, tool-fallbacks, StopFailure observation); **no fleet-wide mechanical parent-session failover** verified. Implementation needs design choice + wiring.

## Producing context

- **Date:** 2026-07-28  
- **Session:** `019fa94d-5608-7b21-b8d7-dbe609f92df3`  
- **Operator question (verbatim intent):** hit rate limit on glm-5.2 and got halted; how to auto-switch so user intervention is not required  
- **Related prior arc:** session 019f821c Token Plan 429s made `/tp` degrade to inline every time → handoff `tp-model-pool-not-inline-fallback-20260722` (pool-before-inline for **spawn only**)

## Read-first list

1. `C:\Users\brsth\.grok\tool-fallbacks.md` — known-broken model×tool combinations; 429 workarounds  
2. `C:\Users\brsth\.grok\skills\tp\SKILL.md` Step 2 — **spawn model pool** (try glm-5-2 → mimo → parent inherit → inline last)  
3. `P:/.data/wiki/concepts/model-pool-not-chain.md` — pool peers, not single ranked chain  
4. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — quota/speed/diversity rules; GLM 5h quota note  
5. `P:/.data/wiki/concepts/model-selection-from-pool-decision-framework.md` — 6-element selection  
6. `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` — which models work via spawn  
7. `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md` — **StopFailure** event, matcher `rate_limit` (observation-only today)  
8. `C:\Users\brsth\.grok\docs\user-guide\11-custom-models.md` — **manual** model switch (`/model`, Ctrl+M); no documented auto-failover  
9. Prior handoff: `P:/docs/handoffs/tp-model-pool-not-inline-fallback-20260722/HANDOFF.md` (spawn pool; status historically “not started” but current `/tp` SKILL.md **already describes pool**)  
10. Adjacent: `P:/docs/handoffs/tp-pool-composition-review-20260723/HANDOFF.md`, `P:/docs/handoffs/cross-transport-model-matrix-20260726/HANDOFF.md`

## Related wiki concepts

- [[model-pool-not-chain]]  
- [[model-pool-selection-policy-speed-quota-diversity]]  
- [[model-selection-from-pool-decision-framework]]  
- [[model-tool-calling-capability-matrix]]  
- [[model-fleet-provider-pools]]  
- [[automated-model-routing-in-ai-coding]] (external product patterns; gateway-style routing)  

## Verified facts

### Two different failure surfaces (do not conflate)

| Surface | What 429s | Who “halts” | Auto-switch today? |
|---------|-----------|-------------|--------------------|
| **A. Parent session model** | Orchestrator turn (main chat = glm-5-2 or Grok) | Whole session stops waiting for human `/model` | **No** documented automatic parent switch `[FACT: user-guide 11-custom-models = manual]` |
| **B. Child spawn / skill model=** | `spawn_subagent(model=glm-5-2)` in /tp, /check, /review | That spawn fails; skill may inline or retry | **Partial:** skill prose says try next pool member; success depends on orchestrator **obeying** prose under pressure `[FACT: /tp SKILL.md Step 2 pool]` |
| **C. Built-in tools on a model** | e.g. `web_search` 429 under GLM | Tool fails; model may continue | **Documented** tool→CLI fallback in `tool-fallbacks.md` `[FACT]` |

### What already exists

- [FACT] `/tp` Step 2 is designed as a **model pool**, not inherit-or-fail: try pool members on 429/401/serialization/empty before Step 4 inline (`C:/Users/brsth/.grok/skills/tp/SKILL.md`). Default table lists `glm-5-2` early as subscription reasoning fallback.  
- [FACT] `~/.grok/tool-fallbacks.md` records GLM-5.2 + parallel `web_search` → 429 team rate limit (2026-07-18); workaround serialize or use other search backends.  
- [FACT] Grok emits **StopFailure** with `error: rate_limit` (capacity 503/529 folded in). Hook is **observation-only** — cannot change model by itself today (`user-guide/10-hooks.md`).  
- [FACT] Operator model switch is **manual**: `/model` or Ctrl+M (`user-guide/11-custom-models.md`).  
- [FACT] Fleet policy already prefers **pool over chain** and separate provider quotas (wiki model-pool-*).  
- [FACT] CLI second opinions (`/agy`, `/codex`, `/mmx`) are **outside** spawn_subagent and use independent quotas — valid escape hatch when spawn path is rate-limited.  
- [INFERENCE] If the **parent** is glm-5-2 and the **session** halted on 429, skill-level spawn pools never get a chance to run until something can still execute tool calls.

### What does **not** exist (gap)

- [FACT] No verified Grok Build runtime config that says “on parent 429, automatically continue with model X.”  
- [UNKNOWN] Whether Grok TUI has an undocumented env/config for provider failover (not found in user-guide skim). Discriminating test: search Grok source/config for `rate_limit` failover or read StopFailure samples for recovery hooks.  
- [UNKNOWN] Exact error surface in this halt (parent vs spawn; full error text; provider). Operator said “glm-5.2” + rate limit; capture next time for receipt.

## Current state

| Layer | State |
|-------|--------|
| Spawn pool in `/tp` skill text | Present |
| Spawn pool mechanical helper (shared by all skills) | Missing / incomplete |
| Parent-session auto model switch | Missing |
| StopFailure → action | Observe only |
| tool-fallbacks for tools | Present |
| Operator unblocking today | Manual `/model` / Ctrl+M / new session / different skill model= |

## Answer (cold-start summary)

**You cannot fully “not need user intervention” today for a parent-session glm-5.2 429** without new plumbing. What you *can* do:

1. **For skill children (already designed):** never pin a single model; on 429 try the next pool peer (`go-mimo-v2-5`, parent-inherited, free local, CLI `/agy`/`/codex`). Make that **mechanical** (shared helper + log), not hope the LLM remembers skill prose.  
2. **For parent halt:** add a **StopFailure hook** that logs + optionally **prompts a non-interactive model switch** *if* the runtime exposes a switch API; otherwise hook can only notify and leave a sticky “resume with model=Y” instruction. Confirm API exists before claiming auto-parent-switch. **Parent failover must use orchestrator-eligible models only** (see role matrix below) — not MiniMax M3.  
3. **For tool 429s:** keep using `tool-fallbacks.md` (tool/transport change, not always model change).  
4. **Gateway option (harder, optimal long-term for multi-provider):** route completions through a gateway (CCR / LiteLLM-class) with failover policies — rate-limit on provider A → provider B without TUI model picker. Higher setup cost; true no-touch.

### Role matrix (operator directive 2026-07-28) — not all models are orchestrator-safe

Auto-switch and pools **must not treat every spawn-capable slug as a valid parent/main orchestrator.** Roles differ:

| Role | Job | Model bar | Examples (operator signal) |
|------|-----|-----------|----------------------------|
| **Main orchestrator** (parent TUI session) | Plan, route, synthesize, obey AGENTS/skills, long multi-step judgment | Stable, low-chaos, high instruction-following | **Grok 4.5 — good quality; paid.** GLM-5.2 — often used; can rate-limit. |
| **Spawn / specialist / mechanical child** | Bounded critique, review lens, doc check, one-shot task | Can be cheaper/faster; chaos more tolerable if scoped | `minimax-m3` OK for **doc-only / high-volume parallel** per `/check` routing; **not** main orchestrator |
| **CLI second opinion** | Cross-family external opinion | Separate quota | `/agy`, `/codex`, `/mmx` |

**Hard operator signals (this update):**

- **MiniMax M3 is chaotic** — do **not** auto-failover the **main orchestrator** to M3 when glm-5.2 (or Grok) rate-limits. Using M3 as parent would “continue” the session in name while degrading judgment and skill obedience.  
- **Grok 4.5 is good for orchestrator** but **costs money** — valid parent fallback when subscription/paid path is the trade-off the operator accepts; not free. Prefer: demote rate-limited orchestrator → **another orchestrator-grade** model (Grok 4.5 / other verified stable), **not** free-chaotic.  
- **Spawn pools may still use M3** where skill tables already assign it (e.g. doc-only `/check` verifiers) — that is child role, not parent role.

## Task packets

### AMS-01 — Classify the halt (instrument next incident)

- **goal:** Capture whether 429 is parent turn vs spawn vs tool.  
- **acceptance:** one row in `tool-fallbacks.md` or `tp_spawn_failures.jsonl` with: slug, surface (parent|spawn|tool), error string, time.  
- **falsifier:** still only “we got halted” with no classification.  
- **verification level required:** LIVE_BEHAVIOR (next 429)  
- **estimate:** S  

### AMS-02 — Shared spawn pool helper (mechanical, no user intervention for children)

- **goal:** One script/module used by `/tp`, `/check`, `/review`, `/go` that: ordered pool → spawn → on 429/401/serde/empty try next → log each failure → only then inline/degrade.  
- **in scope:** `P:/.agents/scripts/` or `~/.grok/skills/*/__lib/spawn_pool.py`; update skill Step 2 text to call helper; wire `log_spawn.py --failure-reason`.  
- **out of scope:** parent TUI model auto-switch.  
- **acceptance:**  
  1. Simulated 429 on first slug still produces child result from second slug without user action.  
  2. Disclosure lists failed + winning slug.  
- **falsifier:** first slug 429 → immediate inline without trying peer.  
- **verification level required:** LIVE_BEHAVIOR  
- **risk_of_change:** M  
- **end_to_end_verification:** run a skill that spawns with `model=glm-5-2` while that slug is rate-limited (or mock); confirm second model runs  

### AMS-03 — Parent-session recovery path (research + implement if API exists)

- **goal:** On StopFailure `rate_limit`, automatically continue without Ctrl+M.  
- **steps:**  
  1. Research Grok Build for programmatic model switch / resume-on-other-model.  
  2. If API exists: StopFailure hook invokes switch to a configured **orchestrator-eligible** fallback only (see role matrix). **Default candidate: Grok 4.5 (paid, quality).** Explicit denylist for parent: **`minimax-m3` / M3 (chaotic — operator 2026-07-28).** Do **not** use free-local or code-lane-only models as silent parent fallback without operator policy.  
  3. If no API: document **honest limit** + best-available (auto-write resume packet + preferred `/model` slug; optional external supervisor that restarts session with different **orchestrator-grade** model).  
- **acceptance:** either (auto parent switch works once to an orchestrator-eligible slug) or (wiki + AGENTS state “parent 429 requires user/supervisor; children auto-pool”).  
- **falsifier:** claim “automatic parent switch” without a working receipt; **or** auto-switch parent to M3.  
- **verification level required:** LIVE_BEHAVIOR or STATIC_INSPECTION with explicit UNKNOWN  

### AMS-03b — Maintain orchestrator-eligible allowlist / denylist

- **goal:** Durable list of models allowed as **parent orchestrator** vs **spawn-only** vs **never auto**.  
- **in scope:** handoff → wiki concept or section in `tool-fallbacks.md` / model-pool policy; consumed by AMS-02 (spawn) and AMS-03 (parent).  
- **seed (operator 2026-07-28):**  
  - Orchestrator-OK: Grok 4.5 (good, paid); GLM-5.2 (usable, rate-limit prone)  
  - Orchestrator-DENY for auto-failover: MiniMax M3 (chaotic)  
  - Spawn-OK: M3 for doc/mechanical per skill tables; mimo/local/etc. per matrix  
- **acceptance:** allowlist file or wiki table exists; AMS-02/03 reference it; tests refuse parent failover to denylisted slug.  
- **falsifier:** parent failover path has no role check and can select M3.  
- **verification level required:** UNIT_TEST or STATIC_INSPECTION  

### AMS-04 — Default pool composition when glm-5-2 is rate-limited

- **goal:** Do not put a hot-rate-limited slug first when recent telemetry shows 429s.  
- **in scope:** read spawn telemetry / critique log; prefer different provider/quota before glm-5-2 under pressure; update `/tp` and `/check` model tables. **Spawn pool ≠ orchestrator pool** — children may use M3; parent may not.  
- **acceptance:** under documented glm-5.2 429 period, first successful **spawn** is non-glm without user action; **parent** failover (if any) only hits orchestrator-eligible list.  
- **verification level required:** LIVE_BEHAVIOR  

### AMS-05 — Optional gateway failover (long-term)

- **goal:** Provider-level failover (CCR/LiteLLM-class) so rate limit on ZAI/OpenRouter path fails over to another provider.  
- **acceptance:** design note + ADR or wiki concept; implement only if operator chooses this track.  
- **end_to_end_verification:** request against rate-limited backend succeeds via alternate backend without TUI model change  
- **risk_of_change:** L  

## Open decisions

1. **Scope of “automatic”:**  
   - (a) Children only (AMS-02/04) — high ROI, fits existing skill architecture  
   - (b) Parent session too (AMS-03) — needs API proof  
   - (c) Gateway (AMS-05) — infrastructure  
   - **Lead:** **(a) now**, research **(b)** same week, **(c)** only if multi-provider brownouts dominate  

2. **Fallback when glm-5-2 429s — split by role:**  
   - **Spawn/child:** `go-mimo-v2-5`, free local, `/agy`/`/codex` CLI, M3 only for roles that already allow it (doc/mechanical).  
   - **Parent/orchestrator:** **Grok 4.5** (good quality, **paid**) or other orchestrator-eligible model — **never auto M3**.  
   - Criterion: for parent, **stability + instruction-following first**, then cost; for spawn, separate quota + reliability.  
   - **Lead:** spawn → non-glm peer; parent → Grok 4.5 (accept cost) or explicit operator-configured orchestrator allowlist — **not** “cheapest available.”  

3. **Should rate-limited slug be temporarily demoted in pools?**  
   - **Lead:** yes, short TTL demotion from telemetry (15–60 min) — pool-not-chain still applies  

4. **Is paid Grok 4.5 acceptable as automatic parent failover?**  
   - Trade-off: quality vs money.  
   - **Lead (operator signal):** Grok 4.5 is **good** for orchestrator; cost is real. Prefer configurable: `orchestrator_fallback = grok-4.5` with optional “ask before paid failover” flag if API allows. Default auto-paid is operator preference — **ask once at implement time** if not already set.  

## Hard constraints

- Do not invent session/model IDs.  
- Do not put **go-kimi-k3** or broken nemotron spawn paths in auto-pools (operator policy).  
- Prefer **mechanical** pool try over behavioral “remember to switch model.”  
- Inline fallback for `/tp` is **structurally weaker** (same lens); disclose if used; do not pretend it is auto-model-switch.  
- Soft-fail logging must not block primary workflow (same as `/agy` fail-open).  
- **Role gate (operator 2026-07-28):** **not every model is orchestrator-grade.** Auto parent failover **must not** select **MiniMax M3** (chaotic). **Grok 4.5** is orchestrator-OK but **paid** — use only as deliberate parent fallback, not silent unlimited spend. Spawn/specialist pools may still use M3 where skills already assign it for bounded tasks.  

## Cross-reference couplings

- `/tp` SKILL.md pool ↔ this handoff AMS-02 (implement shared helper so check/review share it)  
- `tool-fallbacks.md` ↔ AMS-01/04 demotion data  
- StopFailure hooks (`user-guide/10-hooks.md`) ↔ AMS-03  
- Prior `tp-model-pool-not-inline-fallback-20260722` ↔ **spawn-only** predecessor; this handoff **widens** to parent halt  
- `/check` model routing tables (minimax/glm for verifiers) ↔ AMS-04  

## Explicit non-goals

- Do not “fix” a rate limit by retry-spamming the same model.  
- Do not silently run inline `/tp` and call it multi-model failover.  
- Do not re-open Keep-Smaller-Copy product work.  

## Resumption protocol

1. Read this handoff + `/tp` SKILL.md Step 2 + hooks StopFailure section.  
2. AMS-01: if you have the glm-5.2 halt log from this session, classify surface; else instrument next 429.  
3. Implement AMS-02 (shared spawn pool helper) first — highest ROI for “no user intervention” on multi-agent skills.  
4. AMS-03 research only after AMS-02 ships.  
5. Update wiki + tool-fallbacks with receipts.  

## Suggested next invocation

```text
Read P:/docs/handoffs/auto-model-switch-on-rate-limit-20260728/HANDOFF.md (incl. role matrix).
1) AMS-03b: orchestrator allowlist/denylist (deny M3 as parent; Grok 4.5 OK but paid).
2) AMS-02: shared spawn pool helper with try-next on 429 — children may use M3 only for spawn-OK roles.
3) AMS-03: parent recovery only to orchestrator-eligible models; no silent M3 parent.
Do not claim parent auto-/model until AMS-03 proves a runtime API.
```

## Last user message (verbatim)

> /handoff we hit a rate limit on glm-5.2 and got halted.  How can we switch to another model automatically so that we don't need user intervention?

## Epistemic labels

Used above. Parent auto-switch feasibility remains **[UNKNOWN]** until runtime API is confirmed or denied with a receipt.

## Dependencies

- **Requires:** nothing to start AMS-02  
- **Blocks:** true zero-touch parent recovery (AMS-03) depends on Grok runtime capability  
- **Non-blocking to:** product handoffs; vulture-in-check (done)  

## Falsifier (handoff obsolete)

A cold start can (1) spawn children that survive glm-5-2 429 without user action, and (2) either parent auto-continues after rate_limit **or** docs honestly state parent still needs switch/supervisor — both proven with receipts.

---

## Revision 1 — 20260728T173500Z (session 019fa94d)

**Trigger:** operator: "M3 is chaotic, so not all models are good for the main orchestrator role. Grok 4.5 is good but costs money."

**What changed:**
- Added **role matrix**: main orchestrator vs spawn/specialist vs CLI second opinion.
- **Denylist for auto parent failover:** MiniMax M3 (chaotic).
- **Orchestrator-OK:** Grok 4.5 (quality, paid); GLM-5.2 usable but rate-limit prone.
- Split fallback decision by role (spawn vs parent).
- New task **AMS-03b** (allowlist/denylist).
- Hard constraints + AMS-03/04 + open decisions + next invocation updated.

**Status update:** OPEN — policy refined; implementation still pending.


---

## Revision 2 — 20260729T020000Z (session 019fa94d /handoff auto)

**Trigger:** /handoff auto-update at session close.

**What changed since Revision 1:**
- Spawn pool helper handoff created (spawn-pool-helper-ams02-20260728) — AMS-02 is now a separate tracked workstream.
- log_spawn.py extended with --error-type + spawn_failures.jsonl (committed fae5c2a).
- /check Step 6.2 now surfaces /review latency upfront.
- No implementation progress on AMS-02 (spawn_pool.py) or AMS-03 (parent auto-switch).

**Status update:** OPEN — design complete; implementation deferred to fresh session.
