# Cross-Host Cognition Migration Investigation — Final Report

**Date:** 2026-07-20
**Verdict:** `GROK_COGNITION_MIGRATION_PILOTS_JUSTIFIED`
**Governing question:** *Which real Claude Code cognition capabilities will produce enough incremental value in Grok to justify a Grok-native implementation, and what is the smallest credible way to prove it?*

**Headline:** The Claude Code cognition ecosystem is real and unevenly mature. Of ~50 distinct mechanisms inspected across 10 packages, **two address distinct, measured Grok `/tp` gaps with credible portable logic and bounded reversibility**: an **independent cross-model critic** (extracted from `anti_dodge_judge.py` + `Stop_semantic_critic.py`) and **minimal `/tp` outcome logging** (extract-pattern from `cc-aca-observability`'s JSONL evidence logging). Both are recommended as bounded pilots. Everything else is either already covered by `/tp` prose, lower-value per complexity, a stub, or Claude-Code-ceremony with no portable cognition. **No broad migration is justified; no new `/tp` doctrine is added.**

---

## 1. Freshness and authority preflight

### 1.1 Authoritative Grok `/tp` files (verified 2026-07-20)

| File | Bytes | SHA-256 | Status |
|---|---|---|---|
| `~/.grok/skills/tp/SKILL.md` | 13409 | `6fc12f04a334c9b7c3996c2668f55348d9723fd820cbf24774735353b11908e0` | Authoritative; post-stabilization state-grounding paragraph at lines 60–71 |
| `~/.grok/skills/tp/protocol.md` | 42714 | `6ffd3b08dec98d9ea32cea0016091678e858cc31c74edb80a01432f65c092220` | Deep reference; 18 sections; unchanged |
| `~/.grok/skills/tp/fixtures/replay-cases.md` | 47223 | `0750446bf1fe788a93f1776fc43cdf27e736ae0928c044205741a7f3fd1a3f90` | 658-line fixture corpus (Cases 1–2, A–U); unchanged |

No newer edit exists. The state-grounding edit applied 2026-07-19 (verified in the stabilization pass, verdict `TP_STATE_GROUNDING_VERIFIED`) is the current state. **No divergence.**

### 1.2 Authoritative Claude cognition roots

All under `P:\packages\.claude-marketplace\plugins\`. **All enabled** in `~/.claude/settings.json` (`enabledPlugins.*@local = True`).

| Plugin | Version | Files | Primary cognition surface |
|---|---|---|---|
| `cc-aca-epistemic` | 0.2.86 | 126 | Evidence contract, anti-sycophancy, semantic critic |
| `cc-aca-reasoning` | 0.1.23 | 36 | Reasoning-mode selection, drift sentinel, reflection gates |
| `cc-skills-thinking` | 1.0.19 | 339 | Tree-of-Thought, convergence, debate, `/s` + `/tot` skills |
| `cc-council` | 1.1.2 | 29 | Multi-model council (Karpathy-style) |
| `cc-aca-observability` | 0.1.32 | 102 | Hook framework, drift detection, reflexion verification |
| `cc-aca-authority` | 0.1.27 | 67 | Authority routing (out of cognition scope) |
| `cc-aca-investigation` | 0.2.10 | 22 | Investigation→implementation gates |
| `cc-aca-safety` | 0.1.15 | 23 | Safety/prompt classification |
| `cc-aca-session` | 0.1.18 | 29 | Session lifecycle |
| `cc-aca-sdlc` | 0.1.11 | 18 | SDLC discipline gates |

### 1.3 Active hook dispatch (verified in `settings.json`)

| Lifecycle | Plugins dispatched (matcher) |
|---|---|
| PreToolUse (`.*`) | cc-aca-safety, cc-aca-investigation, cc-aca-epistemic, cc-aca-authority, cc-aca-reasoning |
| PreToolUse (`Edit\|Write\|MultiEdit`) | cc-aca-sdlc |
| Stop (`.*`) | cc-aca-authority, cc-aca-reasoning, cc-aca-sdlc |
| UserPromptSubmit (`.*`) | cc-aca-safety, cc-aca-authority, cc-aca-reasoning |
| SessionStart | cc-aca-observability |
| PostToolUse | cc-aca-epistemic, cc-aca-observability |

**Critical dispatch truth:** the plugin `__lib/router.py` files are registered for some events, but **Stop and UserPromptSubmit mechanisms are mostly activated through in-process imports from `P:/.claude/hooks/Stop.py` and `P:/.claude/hooks/UserPromptSubmit_modules/*.py` compatibility wrappers** (using `importlib.util.spec_from_file_location`). This is the documented workaround for [anthropics/claude-code#16288](https://github.com/anthropics/claude-code/issues/16288). The router itself was pruned in task #815 (2026-07-19) to remove dispatch entries that produced no output.

### 1.4 Status taxonomy (not collapsed)

| Status | Meaning | Count (approx) |
|---|---|---|
| `implemented-and-active` | Code path verified from settings.json through to execution | ~12 mechanisms |
| `implemented-but-inactive` | File exists; no live dispatch path | ~8 mechanisms |
| `advisory-only` | Runs but cannot block (returns `approve` or injection only) | ~15 mechanisms |
| `stub` | Explicit placeholder comments; returns hardcoded values | ~5 mechanisms (incl. entire cc-council engine) |
| `reference-design` | Architecture documented but never shipped | ~3 mechanisms |
| `partially-implemented` | Some real logic, key piece missing | ~4 mechanisms |
| `real-with-host-wrapper` | Real portable core, host-specific caller | ~6 mechanisms |
| `dead-code-pruned` | Router entry removed; file persists | 3 stop hooks in cc-aca-reasoning |

**No `BLOCKED_CURRENT_STATE_DIVERGED`.** The state is stable and inspectable.

---

## 2. Claude cognition capability map

Organized by capability (not by repository). Each row cites the actual file inspected.

### A. Evidence and epistemic discipline

| Sub-capability | Implementation | Status |
|---|---|---|
| Section-contract enforcement (`[FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION]`) | `cc-aca-epistemic/__lib/epistemic_validator.py` (97135b, ~2000 LoC) | real-with-host-wrapper |
| Citation requirement in FACT bullets | same file, `check_fact_support` | real-with-host-wrapper |
| Causal/comparative claim section rules | same file, `check_causal_rules`, `check_comparative_rules` | real-with-host-wrapper |
| Local-summary grounding predicate | same file, `is_locally_grounded_in_this_turn` | real-with-host-wrapper |
| Retry-strategy classifier | same file, `classify_validator_outcome`, `apply_epistemic_policy` | real-with-host-wrapper |
| State grounding (inspect-before-recommend) | **`/tp` SKILL.md lines 60–71** (state-grounding paragraph, applied 2026-07-19) | prose; verified |
| Falsification / disconfirmation search | **`/tp` SKILL.md §Conditional disconfirmation** + `cc-aca-observability/__lib/posttooluse/falsification_assessor.py` | mixed |

### B. Critical-friend and anti-sycophancy behaviour

| Sub-capability | Implementation | Status |
|---|---|---|
| 10-category lazy-closure / capitulation / status-quo-defense / user-delegation detector | `cc-aca-epistemic/__lib/anti_sycophancy/lazy_closure_detector.py` (62847b, ~1355 LoC, 7 test files) | real-with-host-wrapper |
| Parallel-LLM "use vs mention" adjudicator | `cc-aca-epistemic/__lib/anti_dodge_judge.py` (9959b, ~250 LoC; MiniMax-M3 + Mistral first-valid-wins) | advisory-only, GATED OFF (`ANTI_DODGE_JUDGE_ENABLED=false`) |
| High/low-stakes user-challenge classifier + 3 escalation protocols | `cc-aca-epistemic/hooks/userpromptsubmit/anti_sycophancy_injector.py` (~352 LoC) | **implemented-but-inactive** (registry decorator has no dispatcher) |
| Six failure-mode diagnostic vocabulary | **`/tp` SKILL.md §Drift-correction tools** | prose; verified |
| Construct → challenge → converge contract | **`/tp` SKILL.md §Default /tp** | prose; verified |

### C. Reasoning-depth selection

| Sub-capability | Implementation | Status |
|---|---|---|
| 4-mode regex classifier (sequential/multi_agent/graph/two_stage) | `cc-aca-reasoning/hooks/start/Start_reasoning_mode_selector.py` (~95 LoC) | **reference-design / dead in production** (no SessionStart registration) |
| Unified detection via shared module | `cc-aca-reasoning/hooks/userpromptsubmit/reasoning_mode_selector.py` (delegates to `UserPromptSubmit_modules.unified_detection`) | advisory-only (live via compat wrapper) |
| Reasoning Contract (10 toggleable clauses) | `cc-aca-reasoning/hooks/userpromptsubmit/reasoning_contract.py` (6819b) | live; portable text-only |
| Think-profile registry (9 profiles + ULTRATHINK 4-lens) | `cc-aca-reasoning/hooks/userpromptsubmit/think_trigger.py` (33386b; 9 tests) | live via compat wrapper |
| Adaptive depth classifier | **Does not exist.** `cc-skills-thinking/reasoning/hooks/Start_reasoning_mode_selector.py` is a 28-line wrapper to non-existent `P:/packages/cc-aca-reasoning` (raises `ImportError`). Mode is config-time enum, not prompt-selected. | absent |

### D. Multi-perspective reasoning

| Sub-capability | Implementation | Status |
|---|---|---|
| Tree-of-Thoughts branch+converge aggregator | `cc-skills-thinking/skills/tot/tot_core.py` (14934b, 428 LoC); 5 personas, asyncio.gather, Jaccard self-consistency | **algorithm real; CLI shell stub** (`tot.py` admits "implementation pending") |
| Convergence complementarity scoring + strategy selection | `cc-skills-thinking/skills/s/lib/convergence/synthesizer.py` (28422b, ~820 LoC) | real-with-host-wrapper; live |
| Convergence pipeline (cluster→dedup→synth→rank→diversity) | `cc-skills-thinking/skills/s/lib/convergence/engine.py` (~565 LoC) | real; live |
| 3-phase brainstorm orchestrator (DIVERGE→DISCUSS→CONVERGE) | `cc-skills-thinking/skills/s/lib/orchestrator.py` (~1000+ LoC) | active via `/s` command |
| Persona agents (critic/synthesizer/innovator/etc.) | `cc-skills-thinking/skills/s/lib/agents/*.py` (~75 LoC each) | active; **same-provider role-prompting — no fresh-context independence** |
| Debate judge | `cc-skills-thinking/skills/s/lib/debate/judge.py` (~625 LoC) | **stub-quality**: scores are MD5-hash pseudo-random; verdict is 3-bucket threshold |
| Council engine (Karpathy-style 3-model deliberation) | `cc-council/council_core/engine/council.py` (2895b) + `policy/consensus.py` (1472b) | **Engine + consensus stub** (verbatim "Placeholder implementation for v1 scaffolding"; returns empty drafts/reviews/synthesis; `compute_consensus_ratio` returns hardcoded `0.5`). **But ~80% of the system is real**: `contracts/types.py` (164 LoC, ProviderAdapter ABC, state enum), `providers/aiapi.py` (158 LoC, 8-provider adapter), `persistence/store.py` (295 LoC, SQLite schema + CRUD), `policy/gating.py` (56 LoC, keyword+length+@council classifier), 6 agent prompts, 4 slash-command specs, `ARCHITECTURE.md` (133 LoC, full state machine + schema + provider model). Missing: `hooks/`, `scripts/`, entry points, tests, and the orchestration loop (~150-250 LoC of asyncio + LLM calls). `test.db` is empty (0 rows all tables) — engine has never been invoked in production. Never referenced at runtime by any other plugin. |

### E. Reflection and quality control

| Sub-capability | Implementation | Status |
|---|---|---|
| Drift sentinel (TF-IDF cosine similarity, warn/block modes) | `cc-aca-reasoning/hooks/stop/StopHook_drift_sentinel.py` (6560b) | real detector; env vars set (`ENABLED=true`, `MODE=block`) but invocation pipeline uncertain |
| Reasoning quality gate (overconfidence + 5 logical-gap dimensions + depth-mismatch) | `cc-aca-reasoning/hooks/stop/Stop_reasoning_quality_gate.py` (15705b; 7 tests) | implemented-and-active; **advisory only** |
| Self-reflection gate (contradiction pairs, unsupported definitive claims) | `cc-aca-reasoning/hooks/stop/Stop_self_reflection_gate.py` (~310 LoC) | **pruned**: always returns `approve`; output discarded by router |
| RCA reflector (4 anti-patterns: premature convergence, catch-22, evidence-free fix, zero-plan) | `cc-aca-reasoning/hooks/stop/StopHook_rca_reflector.py` (~260 LoC) | **pruned**: no `__main__`; `STATE_DIR` literal-`$CLAUDE_ROOT` bug |
| Circuit breaker | **`/tp` SKILL.md §Circuit breaker** | prose; invoked via `/tp check` |
| CJK drift detector | `cc-aca-observability/hooks/posttool/cjk_drift_detector.py` (5509b) | implemented-and-active; blocks on Stop, advisory on PostToolUse |

### F. Observability and outcome learning

| Sub-capability | Implementation | Status |
|---|---|---|
| Reflexion verifier (read-back-after-write + ast.parse + retry-with-self-heal) | `cc-aca-observability/__lib/posttooluse/reflexion_verifier.py` (~700 LoC) | implemented-and-active (production telemetry May 25–30, 2026) |
| Artifact scraper (records Read/Grep/Glob file paths to session JSONL) | `cc-aca-observability/hooks/posttool/PostToolUse_artifact_scraper.py` (~75 LoC; 13 tests) | active |
| In-process hook registry (40+ hooks, ABC + dispatcher) | `cc-aca-observability/__lib/posttooluse/{__init__,base}.py` | active |
| Cognition-outcome measurement (recommendation quality, evidence use, user correction) | **Does not exist.** Despite names like `outcome_validator` and `falsification_assessor`, all observability measures **tool events** (file persistence, error keywords, CJK text), not cognition outcomes. | **absent** |

### G. Delegation

| Sub-capability | Implementation | Status |
|---|---|---|
| Parallel external-LLM adjudicator with fail-open | `cc-aca-epistemic/__lib/anti_dodge_judge.py` (pattern; 15/15 eval claim) | gated off by default |
| 3-profile diagnostic LLM critic (software_rca / general_diagnostic / evaluative_recommendation) | `cc-aca-epistemic/hooks/stop/Stop_semantic_critic.py` (63930b, ~1450 LoC) | real-with-host-wrapper |
| Multi-provider adapter (z.ai, MiniMax, opencode-go, groq, mistral, cerebras, nvidia) | `cc-council/council_core/providers/aiapi.py` | implemented-but-unused (engine is stub) |
| Grok-native external-model CLIs | `agy` (Antigravity/Gemini), `mmx` (MiniMax), `codex` (OpenAI) — per `~/.grok/AGENTS.md` | Grok-native; not a Claude mechanism but relevant for delegation disposition |

---

## 3. Active implementation evidence

This task's premise — *the Claude Code cognition ecosystem is real and applied* — is confirmed with qualifications. Verified-active mechanisms with production evidence:

**cc-aca-epistemic** is the strongest cluster:
- `epistemic_validator.py` is imported in-process by `P:/.claude/hooks/Stop.py` at 5 sites (lines 470, 609, 891, 1027, 1312). 5+ dedicated test files. Real rule engine.
- `lazy_closure_detector.py` is imported by `StopHook_unverified_stance.py:121`, itself imported by `Stop.py:1027`. Cross-plugin consumption: `cc-lazy-closure-debt` also imports it. 7 dedicated test files with FP-replay corpora.
- `Stop_semantic_critic.py` is imported in-process by `Stop.py:517`. Live via dispatch table registration. Three LLM backends (GLM-5.2, MiniMax-M3, Mistral) with parallel calls.

**cc-aca-observability** has concrete production telemetry:
- `__lib/data/reflexion_verifications.jsonl` contains real entries 2026-05-25 through 2026-05-30 across 7+ files including sibling plugins.
- `__lib/data/semantic_compress_log.jsonl` shows ~80% compression ratios in real sessions.

**cc-skills-thinking** has two genuine algorithms actively wired through `/s`:
- `convergence/synthesizer.py` and `convergence/engine.py` are invoked by `BrainstormOrchestrator` which is invoked by `scripts/run_heavy.py` which is the `/s` command entry.
- `tot_core.py` has a real algorithm but `tot.py` CLI admits *"Full Tree-of-Thoughts implementation requires Agent tool integration… parallel subagent spawning is pending."*

**cc-council is ~80% of a real system with the orchestration loop missing.** The engine (`council.py:run_session()`) and consensus logic (`compute_consensus_ratio()` returns hardcoded `0.5`) are stubs — docstring verbatim "Placeholder implementation for v1 scaffolding." But the surrounding system is real and substantial: `contracts/types.py` (164 LoC — full data contracts, `ProviderAdapter` ABC, `CouncilState` enum), `providers/aiapi.py` (158 LoC — real adapter wrapping `cc-skills-ai-api` transport for z.ai/MiniMax/opencode-go/groq/mistral/cerebras/nvidia), `persistence/store.py` (295 LoC — real SQLite schema with sessions/drafts/reviews/synthesis tables + full CRUD + 5-minute stale-session recovery), `policy/gating.py` (56 LoC — real keyword + length + `@council` classifier), 6 agent prompt files (planner/pragmatist/futurist/critic/judge/synthesizer), 4 slash-command specs, and `ARCHITECTURE.md` documenting the full 5-stage Karpathy-style deliberation protocol (gating → 3 independent drafts → anonymized peer review → chairman synthesis → variance-based consensus). The missing piece is the orchestration loop — ~150-250 LoC of `asyncio.gather` + parallel LLM calls + state transitions.

**Runtime status (verified via full reference scan across `P:\packages\`, `P:\.claude\`, `P:\.grok\`):** `hooks/` directory does not exist despite README claiming it as an invocation path; `scripts/` does not exist; `pyproject.toml` declares no entry points; `tests/__init__.py` is empty; `test.db` has 5 tables with **0 rows in every table** (the engine has never produced a session in production); git history shows only 2 chore commits (last 2026-06-26, ~4 weeks stale); no other plugin invokes `council_core` at runtime. **All cross-references found are development provenance, not invocation:** `PreToolUse_investigation_gate.py:1053,1411` and `hook_state_manager.py:426` both document the same resolver bug observed *while developing* cc-council ("the cc-council transcript: resolver bug blocked all writes"); `Stop_fake_done_detector.py:353` uses `council_core/engine/council.py` as a test-fixture string; ~90 `P:/.claude/state/investigation_state_*.json` files mention cc-council paths in their `changed_paths` lists because the user was editing cc-council files around 2026-06-22/23 (consistent with the git commit dates). The `/council-debug` strings matched in those state files are file-path fragments (`cc-council/commands/council-debug.md`), not command invocations. **Inferred development history:** cc-council was the target of active development effort over 2026-06-22 to 2026-06-26, paused (possibly because the investigation-gate resolver bug blocked writes during that session), and has been dormant since. The design intent was serious enough to invest in — this slightly strengthens the Phase 2 case without changing the disposition.

**Assessment for Grok:** the capability (multi-model council with anonymized peer review and chairman synthesis) is real, distinct from the simpler independent-critic pattern, and well-documented enough to implement against. Its anonymization (drafts labeled A/B/C, reviewer blind to model identity) is a genuine innovation the independent-critic pattern cannot offer. Grok's `agy`/`mmx`/`codex` CLIs parallelize cleanly, making cross-model parallel drafts tractable. However, the council pattern costs 2.5-5× more per gated turn than the critic pattern, its frequency benefit is unmeasured (the /tp naturalistic eval never observed a framing-blind-spot failure that a council would uniquely catch), and no proven implementation exists on either host to port. Selected as **Phase 2 contingent on Pilot 1 evidence** (see §10, §13) rather than Phase 1.

**cc-aca-reasoning** is mixed:
- `Stop_reasoning_quality_gate.py` is live via `Stop.py:2088` in-process import; 7 tests pass.
- `StopHook_drift_sentinel.py` has a real TF-IDF detector; env vars set but invocation pipeline possibly broken (no in-process import found).
- Three stop hooks (`StopHook_rca_reflector`, `Stop_self_reflection_gate`, `Stop_reflect_integration`) were **pruned** in task #815 (2026-07-19) because they emitted only `approve/systemMessage` output the router discards.

---

## 4. Capability-versus-packaging analysis

For every serious candidate, the portable core vs host-specific packaging split:

| Mechanism | Portable core | Host-specific packaging | Disposition |
|---|---|---|---|
| `epistemic_validator.py` | Section-contract regex; citation rule; causal/comparative section rules; local-summary grounding; retry-strategy classifier (~95% of logic) | `Stop.py` import path; `CLAUDE_TERMINAL_ID` env var; `P:/.claude/hooks/logs/` paths | **extract-pattern** (high value, deferred — see §13) |
| `lazy_closure_detector.py` | 10-category pattern library; two-tier anchor/regex; FP-narrowing exemptions; sliding-window escalation | `P:/.claude/state/` JSON path; `__lib.anti_lazy_policy` ledger reader | **extract-pattern** (deferred — /tp failures weren't sycophancy-shaped) |
| `anti_dodge_judge.py` | Parallel-LLM adjudicator pattern; first-valid-wins; "use vs mention" prompt; fail-safe `unknown` return | Hardcoded `api.minimax.io`/`api.mistral.ai` endpoints; `P:/.env` key loading | **extract-pattern + adapt** → **Pilot 1** |
| `Stop_semantic_critic.py` | 3 critic profile prompts (`software_rca`, `general_diagnostic`, `evaluative_recommendation`); profile-selection regex | 10s Stop-hook hard-kill contract; 3 LLM endpoints; Claude transcript extraction | **extract-pattern** (critic prompts) → **Pilot 1** |
| `drift_sentinel.py` | TF-IDF cosine similarity + threshold (~30 LoC core) | `evidence_scope.load_scoped_tool_events` source-text loader; `cc_diagnostic_logger` | **extract-pattern** (deferred — /tp circuit breaker + state-grounding cover the relevant cases) |
| `reasoning_quality_gate.py` | 5-dimension logical-gap detector; overconfidence-without-evidence; depth-mismatch (over/underthinking) | Python-specific workaround patterns; `P:/.claude/logs/` path | **extract-pattern** (deferred — value not yet measured) |
| `reasoning_contract.py` | 10-clause toggleable reasoning rubric (text-only) | None — fully portable | **port-as-reference** (do not load into always-loaded SKILL.md; available for `/tp load`) |
| `think_trigger.py` | Profile registry dataclass + 9 profile templates + ULTRATHINK 4-lens routing | `UserPromptSubmit_modules` registry decorator | **extract-pattern** (deferred — overlaps /tp failure-mode vocabulary) |
| `tot_core.py` | 5 branch personas + asyncio.gather + regex parser + Jaccard self-consistency (428 LoC) | Pluggable `agent_tool_func` — **never bound in plugin** | **extract-pattern** (deferred — see §13, branch-and-aggregate) |
| `convergence/synthesizer.py` | Complementarity scoring (Jaccard + persona-difference + dimension-balance); strategy selection; conflict detection; LLM hybrid generation (820 LoC, one LLM seam) | Plugin-local dataclasses; `AgentLLMClient` provider registry | **extract-pattern** (deferred — pairs with tot_core if branching pilot fires) |
| `cc-council` engine + consensus + design | **Real (portable):** 5-stage deliberation protocol design; `ProviderAdapter` ABC; SQLite schema (sessions/drafts/reviews/synthesis); 6 agent prompts (planner/pragmatist/futurist/critic/judge/synthesizer); keyword gating classifier; anonymization pattern (drafts labeled A/B/C). **Stub:** engine orchestration loop, variance-based consensus computation. | `cc-skills-ai-api` transport dependency; missing `hooks/` directory despite README; Claude-Code slash-command convention; no entry points or scripts | **narrowly-reimplement (Phase 2)** — design + prompts + schema port; orchestration loop built net-new on Grok against ARCHITECTURE.md §Deliberation Protocol |
| `cjk_drift_detector.py` | Unicode-range regex + FP-control (strips code blocks/URLs/backticks) + dual enforcement mode | `cc_diagnostic_logger` (optional) | **reuse-directly** if Grok needs CJK enforcement (out of /tp scope) |
| `ReflexionVerifier` | Read-back-after-write + ast.parse + deferred-edit batching | `tool_input`/`tool_response` payload shape; `P:/.claude/state/` paths | **extract-pattern** (out of /tp scope; relevant to edit-verification skills) |
| `HookRegistry` + `PostToolUseHook` ABC | In-process dispatcher consolidating N hooks (184ms→5-10ms) | Claude Code PostToolUse payload; shared `__lib` modules | **extract-pattern** (architectural lesson; not a cognition mechanism) |
| `artifact_scraper` | Regex path extraction + session-keyed JSONL ledger | Shared `artifact_ledger` module | **extract-pattern** → informs **Pilot 2** (outcome logging) |

**Key capability-vs-packaging insight:** the GitHub #16288 hook-registration bug forced a workaround (in-process imports from `Stop.py` and compat wrappers). The workaround is **Claude-Code-specific packaging**, but the underlying mechanisms (detectors, validators, prompts) are portable. Cross-host origin is not disqualification — confirmed for at least 8 mechanisms.

---

## 5. Current Grok `/tp` coverage (from evidence)

Drawn from the naturalistic evaluation (12 cases, 8/12 /tp wins) and the state-grounding stabilization pass (17 regression cases + 7 controls, verdict `TP_STATE_GROUNDING_VERIFIED`).

| Capability | Coverage | Evidence |
|---|---|---|
| Construct → challenge → converge | **covered reliably** | Naturalistic eval: critical-friend value +1.25 over baseline; convergence +0.42 |
| Disciplined openness | **covered reliably** | Naturalistic eval: alternative quality +1.00; assumption handling +1.00 |
| Evidence-based closure | **covered reliably** | Same; constraint accuracy +0.75 |
| Goal–solution separation | **covered by prose** | SKILL.md §Default /tp step 1; no naturalistic counter-evidence |
| Constraint verification & classification (hard/verified vs implementation vs inferred) | **covered by prose** | protocol.md §18; naturalistic eval showed no failures here |
| Capability-vs-packaging reasoning | **covered by prose (deeply)** | protocol.md §18.4 with 7 dispositions; same vocabulary this task uses |
| Intervention neutrality | **covered by prose** | SKILL.md boundaries section |
| State grounding (inspect accessible state before recommending) | **covered by prose; recently verified** | Stabilization pass: 17 regression cases PASS; T1 improved 3/10 inspect-useful cases without regressing conceptual cases; S08 borderline-defensible |
| Correct closure / `NO_CHANGE` | **covered by prose** | SKILL.md allows `NO_CHANGE`; naturalistic eval included 3 cases shaped for restraint; /tp passed |
| Hard-boundary handling | **covered by prose** | SKILL.md; no counter-evidence |
| Evidence-producing next steps | **covered reliably** | SKILL.md §Default /tp step 7 |
| Conditional disconfirmation (Popperian web search) | **covered by prose** | SKILL.md §Conditional disconfirmation; uses `minimax-search__web_search` |
| **Independent critique (fresh-context or cross-model)** | **NOT COVERED — structural gap** | Naturalistic eval §10.2: *"Same model for responders and judges. Both use Grok 4 fast. Judges may share the responder's blind spots."* /tp construct+critique happens in one context window. |
| **Outcome observability** | **NOT COVERED — structural gap** | Naturalistic eval §10.6: *"No historical-outcome data. Cannot measure whether /tp's recommendations actually produce better real-world outcomes."* Stabilization pass §15.6 reiterates. |
| **Adaptive depth (proportionality)** | **PARTIALLY COVERED — borderline** | Naturalistic eval: proportionality +0.16 (near-tie), user-effort efficiency +0.16 (near-tie). C08 (disable path gate) and C10 (ship decision) showed structure adding ceremony to simple questions. |
| Anti-sycophancy at execution time | **covered by prose; not enforced** | Six failure modes are diagnostic vocabulary; no runtime detector. Naturalistic eval did NOT show sycophancy as /tp's failure pattern (failures were reasoning-as-substitute-for-tool-use, addressed by state-grounding edit). |
| Drift detection mid-session | **covered by prose; invoked only** | Circuit breaker fires via `/tp check` or self-detection. No automated detector. |

**Conceptual overlap is not equivalent outcome.** /tp's prose covers most capabilities behaviourally — but independence, outcome observability, and (to a lesser degree) adaptive proportionality are structural gaps prose cannot close.

---

## 6. Distinct Grok gaps

Three gaps are distinct, measurable, and not closable by adding more /tp prose:

### Gap 1 — Independent critique (highest structural significance)

**The gap:** /tp's construct and critique happen in one model context. The critic inherits the constructor's framing, training-data blind spots, and anchoring. The naturalistic evaluation's single-judge limitation (§10.1) and same-model limitation (§10.2) are the same structural problem at the evaluation layer; at the dialogue layer, /tp has the same problem.

**Why prose can't close it:** You cannot instruct a model to "think independently" — independence is a property of context separation, not of prompting. A fresh-context or cross-model critic is structurally different.

**Claude ecosystem coverage:**
- `anti_dodge_judge.py` — real parallel-LLM adjudicator with first-valid-wins and fail-safe `unknown`. Pattern is portable; needs LLM API access.
- `Stop_semantic_critic.py` — three-profile diagnostic LLM critic with worked examples. Prompts are portable.
- `cc-council` — stub. Not a real option.
- `cc-skills-thinking/agents/*` — same-provider role-prompting. **Not independent.**

**Grok-native enabler:** Grok has external-model CLI access (`agy`, `mmx`, `codex`) that Claude Code lacks in the same form. This is a Grok advantage.

### Gap 2 — Outcome observability (highest foundational significance)

**The gap:** There is no mechanism that measures /tp outcomes. The naturalistic evaluation was a one-shot blinded study; the stabilization pass was a fixture replay. Neither produces continuous signal. Without outcome data, every future cognition decision is made from one-shot evals or intuition.

**Why prose can't close it:** Measurement requires durable state, not dialogue.

**Claude ecosystem coverage:** **Does not exist.** `cc-aca-observability` measures tool events (file persistence, error keywords, CJK text), not cognition outcomes (recommendation quality, evidence use, user correction). This is a net-new capability on both hosts.

### Gap 3 — Adaptive depth (proportionality; lower significance)

**The gap:** /tp adds structure to simple questions (C08, C10 near-ties). The proportionality discipline is prose-encoded and relies on the model's self-judgment.

**Why prose partially closes it:** The state-grounding paragraph already says "tool use would add ceremony" for conceptual questions. A classifier might help, but the model's own judgment may be hard to beat.

**Claude ecosystem coverage:** `Start_reasoning_mode_selector.py` is a real regex classifier but dead in production. `think_trigger.py` profile registry is alive but overlaps /tp's vocabulary.

**Decision:** Not selected as a pilot. The marginal value of a classifier over the model's own proportionality judgment is unproven. Defer until outcome logging (Pilot 2) provides signal about whether proportionality failures are frequent enough to warrant automation.

---

## 7. Candidate architecture comparison

Five architectures compared on the governing axis: **incremental user outcome per unit complexity**.

| Axis | A: Prose-only /tp | B: /tp + helpers | C: Shared cognition layer | D: Delegated cross-model | E: Hybrid |
|---|---|---|---|---|---|
| User outcome (high-consequence decisions) | Baseline | +critic on gated cases | +critic + reusable | +independent challenge | +all |
| Independence | None (same context) | Optional critic | Optional critic | **High (cross-model)** | High when triggered |
| Evidence quality | Prose only | +structured critic output | +shared rubric | +cross-model verdict | Best |
| Latency | 0 | +1.4s on gated cases | +1.4s | +1.4–6s | +1.4s typical |
| Token/$ cost | 0 | ~$0.001–0.01/gated turn | +shared maintenance | ~$0.001–0.01/gated turn | Same |
| Implementation complexity | 0 | Low (~200 LoC + prompt) | Medium (~500 LoC + lib) | Low–Medium | Medium |
| Maintenance | Trivial | One variant + one prompt | Shared lib + consumers | One variant + dispatcher | Both |
| Failure containment | N/A | Fail-open; remove variant | Fail-open; remove lib | Fail-open; skip delegate | Fail-open |
| Portability | Already portable | Grok-native | Grok-native | Grok-native CLIs | Grok-native |
| Transparency | High (visible prose) | High (visible critic output) | Medium (lib indirection) | High (visible delegate output) | High |
| Reversibility | N/A | Remove variant; no state | Remove lib; no state | Remove delegate; no state | Both |
| Cognitive burden on user | None | `/tp critic` opt-in | Auto-routing (opaque) | Auto-routing (opaque) | Mixed |
| Host constraints | None | External CLI availability | None | External model availability | External availability |

**Selection: Option B (/tp with optional helper) is the strongest for Pilot 1.** It maximizes outcome-per-complexity, preserves user opt-in (transparent activation), and is the most reversible. Option D is appealing but adds opaque auto-routing that conflicts with /tp's "user invokes explicitly" boundary. Option C is premature without evidence that multiple skills need the same cognition library. Option E is a future state contingent on pilot evidence.

**Selection: Option B (or even simpler — a side-channel logger) for Pilot 2.** Outcome logging is measurement infrastructure, not user-facing cognition; it belongs beside /tp, not inside SKILL.md.

**Rejected:** Option A (prose-only) leaves the independence gap and outcome-observability gap structurally unaddressed. Option C (shared layer) is over-engineering until a second consumer appears. Option E (hybrid) is a destination, not a starting point.

---

## 8. Adaptive activation design

For Pilot 1 (independent critic), activation must be **explicit and opt-in** to preserve /tp's "user invokes; skill does not auto-fire" boundary.

**Activation criteria (any one):**
- User invokes `/tp critic` explicitly, OR
- User flags high consequence / difficult reversibility in the prompt (`/tp this migration`, `/tp this architecture change`, `/tp this is hard to reverse`), OR
- User requests independent review explicitly (`/tp challenge this from another angle`)

**Non-activation (default /tp):**
- Simple factual or low-consequence question
- Supplied evidence is decisive
- Direct action is obvious
- User explicitly requests a fast answer (`/tp quick`)
- Tool inspection is the real next step (the state-grounding paragraph already handles this)
- Conceptual / normative question with no framing sensitivity

**Why explicit over auto-routing:** /tp's naturalistic eval showed proportionality is the near-tie dimension. Adding an opaque auto-classifier risks more ceremony than benefit. Explicit activation respects user judgment about when independence matters. If outcome logging (Pilot 2) later shows users systematically under-invoking the critic on cases that need it, an auto-route can be added then — but that's a future decision contingent on evidence.

For Pilot 2 (outcome logging), activation is **every /tp invocation** with no gate. The logger is fail-open and side-channel; it does not change /tp behavior.

---

## 9. Ranked mechanism dispositions

Ranked by credible incremental value to Grok, descending:

| Rank | Mechanism | Disposition | Rationale |
|---|---|---|---|
| 1 | `anti_dodge_judge.py` pattern | **extract-pattern + adapt → Pilot 1** | Addresses independence gap; real pattern; Grok-native CLIs available |
| 2 | `Stop_semantic_critic.py` critic prompts | **extract-pattern → Pilot 1** | Three worked-example rubrics; portable text; pairs with #1 |
| 3 | `artifact_scraper` JSONL pattern | **extract-pattern → Pilot 2** | Informs minimal outcome-logger design |
| 4 | `reasoning_contract.py` | **port-as-reference** (available for `/tp load`, not in SKILL.md) | Useful deep-reference material; no always-loaded growth |
| 5 | `drift_sentinel.py` TF-IDF logic | **extract-pattern (deferred)** | Real detector; /tp circuit breaker + state-grounding cover relevant cases for now |
| 6 | `reasoning_quality_gate.py` detectors | **extract-pattern (deferred)** | 5-dimension logical-gap detector; value not yet measured |
| 7 | `convergence/synthesizer.py` | **extract-pattern (deferred)** | Real algorithm; only valuable if branch-and-aggregate pilot is later justified |
| 8 | `tot_core.py` | **extract-pattern (deferred)** | Real algorithm; pluggable agent-tool seam; same caveat as #7 |
| 9 | `think_trigger.py` profile registry | **extract-pattern (deferred)** | Overlaps /tp failure-mode vocabulary |
| 10 | `epistemic_validator.py` section contract | **extract-pattern (deferred)** | Mature but /tp's prose contract + state-grounding cover the relevant cases; porting adds complexity without measured benefit |
| 11 | `lazy_closure_detector.py` pattern library | **extract-pattern (deferred)** | /tp failures weren't sycophancy-shaped (C01/C02 were reasoning-as-substitute-for-tool-use, addressed by state-grounding edit) |
| 12 | `cjk_drift_detector.py` | **reuse-directly if needed** | Out of /tp scope; useful for output-policy skills |
| 13 | `ReflexionVerifier` read-back pattern | **extract-pattern if needed** | Out of /tp scope; relevant to edit-verification skills |
| 14 | `cc-council` (full system: design + stub engine + agent prompts + schema) | **narrowly-reimplement (Phase 2, contingent on Pilot 1 evidence)** | See §10 Pilot 1 expansion path and §13 for the full Phase 2 case. Engine + consensus are stubs, but ~80% of the system is real, the anonymization pattern is a genuine innovation, and Grok's multi-CLI access makes parallel cross-model drafts tractable. Deferred because the independence gap's *frequency* is unmeasured and the critic pattern is the cheaper discriminating test. |
| 15 | `cc-skills-thinking/agents/*` (personas) | **reject for migration** | Same-provider role-prompting; /tp prose already does this |
| 16 | `cc-skills-thinking/debate/judge.py` | **reject** | MD5-hash pseudo-random scores; 3-bucket threshold; not real judging |
| 17 | `cc-skills-thinking/Start_reasoning_mode_selector.py` | **reject** | 28-line broken wrapper to non-existent path |
| 18 | `cc-aca-reasoning/router.py` (Stop dispatch) | **reject** | Pure Claude-Code glue; workaround for #16288 |
| 19 | `cc-aca-epistemic/router.py` | **reject** | Pure dispatch glue |
| 20 | `cc-aca-observability` 40-hook surface | **reject as wholesale migration** | Too coupled to `P:/.claude/hooks/__lib__` ecosystem; cherry-pick patterns only |

---

## 10. Recommended pilots (maximum two)

### Pilot 1 — Independent cross-model critic (`/tp critic` variant)

**Target capability:** Independent critique for high-consequence, framing-sensitive decisions (Gap 1).

**Exact source implementation/pattern:**
- `anti_dodge_judge.py` (parallel-LLM adjudicator; first-valid-wins; fail-safe `unknown`; "use vs mention" prompt design)
- `Stop_semantic_critic.py` `CRITIC_PROMPTS` dict (three worked-example rubrics: `software_rca`, `general_diagnostic`, `evaluative_recommendation`)

**Grok-native form:**
- New `/tp critic` variant (parallel to `/tp check`, `/tp load`)
- On activation, /tp:
  1. Produces its normal construct→challenge→converge output
  2. Dispatches the construct + critique to one external model via `agy` (primary; Antigravity/Gemini) or `mmx` (secondary; MiniMax), with a critic prompt extracted from `Stop_semantic_critic.py`'s rubric (profile auto-selected by the same keyword/regex logic)
  3. The external model returns `{ok: bool, reason: str, missed_angle: str | null}` (structured JSON, fail-safe unknown on parse error)
  4. /tp synthesizes: if `ok=false`, surfaces the missed angle as a revised critique; if `ok=true`, confirms convergence; if `unknown`, notes the delegate was unavailable and proceeds
- Fail-open: if external CLI unavailable or times out, /tp proceeds normally with a one-line note

**Why /tp cannot already provide this reliably:**
The same-model construct+critique inherits framing blind spots. Independence is a property of context separation, not prompting. The naturalistic eval explicitly flagged same-model evaluation as a structural limitation (§10.2).

**Activation criteria:** Explicit (`/tp critic`) or user-flagged high consequence. See §8.

**User-visible behavior:** After /tp's normal output, a `## Independent critic (delegated)` section appears with the external model's verdict. If the critic surfaced a missed angle, /tp either revises the recommendation or explicitly defends against the critique.

**Failure mode:** External model returns low-quality or off-topic critique; adds latency without value.

**Fail-open behavior:** Timeout (e.g. 10s) → skip critic, note "critic unavailable". Parse error → skip, note "critic returned unparseable output". User can proceed regardless.

**Rollback:** Remove the `/tp critic` variant. No state changes. No SKILL.md growth (variant routing only).

**Implementation size estimate:** ~150–250 LoC (dispatcher wrapper + critic prompt templates + JSON parser + variant router) + one paragraph in SKILL.md's variant-routing table.

**Latency and cost:** One extra LLM call. `anti_dodge_judge.py` measured ~1.4s parallel; `agy`/`mmx` subprocess adds ~2–5s wall-time. Cost ~$0.001–0.02 per gated turn depending on model.

**Test corpus:** Re-use C01 and C02 (the naturalistic failures) + 6–8 new framing-sensitive high-consequence cases (architecture decisions, irreversible migrations, security boundaries).

**Comparison condition:** `/tp` vs `/tp critic`, blinded judges (≥2 per case). Identical prompts. Randomized A/B.

**Success metric:** Critic surfaces a material blind spot /tp missed on ≥30% of high-consequence cases; no proportionality regression on simple cases (re-use the stabilization control corpus).

**Kill criterion:** Critic surfaces nothing new on ≥80% of cases, OR adds >2× latency with no quality gain, OR >25% ceremonial use on cases judges rate as simple.

**What evidence would justify broader use:** ≥30% blind-spot surfacing rate sustained over 15+ cases; judge agreement ≥70%; user-visible revised recommendations on ≥20% of cases.

**Phase 2 expansion path (multi-model council):** If Pilot 1 proves cross-model independence adds value, the natural scaling is from 2 models (constructor + critic) to 3-5 (parallel independent drafts + anonymized review + chairman synthesis), implemented against the existing `cc-council` design (`ARCHITECTURE.md` §Deliberation Protocol, 5 stages, SQLite schema, 6 agent prompts). The council pattern's distinct advantages over the critic are: (a) 3+ independent framings instead of 1 critique of an existing framing — addresses anchoring as well as shared-training-data blind spots; (b) anonymization — drafts labeled A/B/C with model identities hidden from the reviewer, eliminating model-identity bias; (c) dedicated chairman synthesis role with explicit contradiction resolution. Costs scale accordingly: 3-5 LLM calls per gated turn (vs 2), ~$0.005-0.05/turn (vs ~$0.001-0.02), +5-15s latency (vs +2-5s). Grok's `agy`/`mmx`/`codex` parallelize cleanly via `asyncio.gather` over subprocess calls, making the parallel-drafts stage tractable. The ~150-250 LoC orchestration loop would be net-new on both hosts (the Claude-side engine is a stub). **Kill criterion for Phase 2:** if Pilot 1 shows <20% blind-spot surfacing on high-consequence cases, the independence gap is not frequent enough to justify the council's 2.5-5× cost — abandon Phase 2.

### Pilot 2 — Minimal /tp outcome logging

**Target capability:** Continuous outcome observability (Gap 2). Measurement infrastructure, not user-facing cognition.

**Exact source pattern:**
- `cc-aca-observability/hooks/posttool/PostToolUse_artifact_scraper.py` (regex extraction + session-keyed JSONL ledger)
- `cc-aca-observability/__lib/data/reflexion_verifications.jsonl` (production telemetry format)
- `cc-aca-observability/__lib/posttooluse/base.py` (`PostToolUseHook` ABC — fail-open, advisory-only pattern)

**Grok-native form:**
- A side-channel JSONL logger that appends one record per `/tp` invocation
- Record schema: `{timestamp, session_id, prompt_summary (first 200 chars), recommendation_summary (first 200 chars), tools_used: [name list], tools_count, user_followup_indicates_correction: bool (heuristic: next user turn contains "no", "wrong", "actually", "but", "revert", or restates the question)}`
- Stored at `~/.grok/state/tp/outcomes.jsonl`
- Updated by a small post-/tp hook or by /tp's own final step

**Why /tp cannot already provide this reliably:** Prose produces no durable signal. The naturalistic eval (one-shot) and stabilization pass (fixture replay) are not continuous.

**Activation criteria:** Every `/tp` invocation. No gate.

**User-visible behavior:** None. The logger is side-channel. /tp output is unchanged.

**Failure mode:** Logger misclassifies user follow-up as correction (false positive); logger misses corrections (false negative); log grows unbounded.

**Fail-open behavior:** Logger failure never blocks /tp. Log rotation at 5MB.

**Rollback:** Delete the log file and the logger. No behavior change.

**Implementation size estimate:** ~50–80 LoC (JSONL appender + user-followup heuristic + rotation).

**Latency and cost:** <10ms per turn. No extra LLM calls.

**Test corpus:** 20–30 natural /tp turns across diverse domains. No blinding needed (measurement infra).

**Comparison condition:** None (measurement infrastructure). The output is analyzed periodically for signal quality.

**Success metric:** Log produces actionable signal on ≥50 turns: user-correction rate, tool-use rate, recommendation-reversal rate, prompt-domain distribution. At least one of these rates differs materially between cases /tp wins vs loses (validating the signal).

**Kill criterion:** Log produces no actionable signal after 50 turns, OR signal is >50% noise (false-positive user-correction classifications), OR users find it invasive.

**What evidence would justify broader use:** Actionable signal validated; used to inform a future adaptive-depth classifier or to prioritize the next cognition pilot.

---

## 11. Pilot test and kill criteria

(Summary of §10's success/kill metrics, consolidated.)

| Pilot | Success metric | Kill criterion | Validation plan |
|---|---|---|---|
| **1: Independent critic** | ≥30% blind-spot surfacing on high-consequence cases; judge agreement ≥70%; no proportionality regression | <20% blind-spot surfacing; OR >2× latency with no gain; OR >25% ceremonial use | 10–12 naturalistic cases, /tp vs /tp critic, ≥2 blind judges, randomized A/B. Re-use C01/C02 + stabilization controls. |
| **2: Outcome logging** | Actionable signal on ≥50 turns (correction rate, tool-use rate, reversal rate) | No actionable signal after 50 turns; OR >50% noise; OR user finds invasive | 20–30 natural /tp turns; analyze log for signal quality. |

**Evidence standard (Step 10) applied to both:**
- Capability is real ✓ (both patterns inspected in source)
- Implementation/pattern is inspectable ✓ (hashes in §1 and per-row)
- Addresses a distinct Grok gap ✓ (Gap 1, Gap 2)
- Expected value is credible ✓ (independence: structural; observability: enables future decisions)
- Pilot is bounded and reversible ✓ (both rollback cleanly)
- Can produce evidence for adoption/rejection ✓ (concrete metrics above)

---

## 12. Placement decisions

| Capability | Placement | Rationale |
|---|---|---|
| Independent critic | `/tp critic` variant (Pilot 1) | User-facing; opt-in; preserves /tp's explicit-invocation boundary |
| Outcome logger | Side-channel file + post-/tp hook (Pilot 2) | Not user-facing; no SKILL.md growth; measurement only |
| `reasoning_contract.py` content | `/tp load` reference (optional) | Already-deep protocol.md covers similar ground; do not duplicate into SKILL.md |
| Drift sentinel, reasoning quality gate, lazy closure detector, epistemic validator | **Evaluation/observability only** (deferred) | May inform future evals; not loaded into /tp; not wired as hooks on Grok |
| Branch-and-aggregate (tot_core + convergence) | **Not implemented** (deferred) | Wait for Pilot 1 evidence; if cross-model value proves out, branching becomes the next candidate |
| Multi-model council (cc-council pattern) | **Phase 2, contingent on Pilot 1** | If Pilot 1 proves independence adds value, scale to 3-5 model parallel drafts + anonymized review + chairman synthesis, built against the cc-council design (agent prompts, schema, ARCHITECTURE.md). See §10 Pilot 1 Phase 2 expansion path. |
| Adaptive depth classifier | **Not implemented** (deferred) | Wait for Pilot 2 signal on whether proportionality failures are frequent |
| CJK drift, ReflexionVerifier, HookRegistry | **Out of /tp scope** | Belong in output-policy or edit-verification skills if those are built on Grok |

**Boundary respected:** No mechanism is added to the always-loaded `SKILL.md`. Pilot 1 adds one row to the variant-routing table (parallel to `/tp check`, `/tp load`). Pilot 2 adds nothing visible.

---

## 13. Rejected candidates and evidence

| Candidate | Rejected because | Credible reuse path assessed first |
|---|---|---|
| ~~`cc-council` engine~~ (moved to Phase 2) | Originally rejected as stub. **Corrected after deeper inspection:** ~80% of the system is real (types/provider/persistence/gating/prompts/ARCHITECTURE); only the engine orchestration loop and consensus computation are stubs. The capability (multi-model council with anonymized peer review) is distinct from the independent-critic and offers genuine innovations (parallel drafts, anonymization, chairman synthesis). Deferred to Phase 2 rather than rejected — see §10 expansion path. | Full re-inspection: types.py (164 LoC), aiapi.py (158 LoC), store.py (295 LoC), gating.py (56 LoC), 6 agent prompts, ARCHITECTURE.md (133 LoC). test.db empty (0 rows). Missing: hooks/, scripts/, entry points, tests. The orchestration loop is ~150-250 LoC of net-new work. |
| `cc-skills-thinking/agents/*` personas | Same-provider role-prompting; no fresh-context independence; /tp prose already does single-context role-switching | Tested as a latency optimization (parallel asyncio over HTTP) — not a reasoning primitive |
| `cc-skills-thinking/debate/judge.py` | MD5-hash pseudo-random scores; 3-bucket threshold; docstring admits MVP placeholder | The prompt-builder is real but the evaluator is vacuous |
| `cc-skills-thinking/Start_reasoning_mode_selector.py` | 28-line wrapper to non-existent `P:/packages/cc-aca-reasoning`; raises ImportError | Replaced by config-time Mode enum (also not a classifier) |
| `anti_sycophancy_injector.py` | Registry decorator has no dispatcher in this plugin; effectively dead | Patterns (high/low-stakes regex + 3 protocols) could be narrowly reimplemented if needed |
| `cc-aca-reasoning/router.py` and `cc-aca-epistemic/router.py` | Pure Claude-Code dispatch glue; no portable cognition | Inspected; confirmed |
| `lazy_closure_detector.py` for /tp | /tp's naturalistic failures (C01, C02) were reasoning-as-substitute-for-tool-use, not sycophancy | Would add complexity; state-grounding edit already addressed the actual failure pattern; defer until a sycophancy-shaped failure appears in Pilot 2 data |
| `epistemic_validator.py` section contract for /tp | /tp's `[FACT]/[INFERENCE]/[UNKNOWN]` prose contract (SKILL.md §9) is behaviourally adequate; naturalistic eval showed no contract violations | Would add ~2000 LoC of regex machinery for a problem not observed in /tp's evals |
| `cc-aca-observability` 40-hook wholesale migration | Too coupled to `P:/.claude/hooks/__lib__` ecosystem (`hook_ledger`, `evidence_store`, `artifact_ledger`, `stop_gate_telemetry`) | Patterns cherry-picked (artifact_scraper for Pilot 2); wholesale port rejected |
| Adaptive depth as Pilot 2 | Marginal value over model's own proportionality judgment; no evidence yet that a classifier would beat the model | Deferred pending Pilot 2 outcome data |
| Branch-and-aggregate as Pilot 1 | Real algorithms exist but independence is limited (same-provider) and Grok-side branching via `/tp` prose is already possible; the cross-model independence question is more fundamental and should be answered first | Deferred pending Pilot 1 evidence |

---

## 14. Risks, costs, and maintenance burden

### Pilot 1 (independent critic)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| External model unavailable (network, quota, key) | Medium | Low (fail-open) | Timeout + skip + note; user proceeds with normal /tp |
| Critic returns low-quality or off-topic critique | Medium | Medium (ceremony) | Structured JSON contract; fail-safe `unknown` on parse; judge eval weeds this out before adoption |
| Adds latency to gated turns | High | Low (~2–5s) | Acceptable for high-consequence decisions; explicit activation |
| Cost accumulates | Low | Low (~$0.001–0.02/turn) | Explicit activation; monthly review of usage |
| Critic and /tp share training-data blind spots (both modern LLMs) | Medium | Medium | Use a different model family (Gemini via agy vs Grok) to maximize divergence |
| User over-invokes critic on simple cases | Medium | Low (ceremony) | Activation criteria explicit; outcome logger (Pilot 2) monitors |

**Maintenance burden:** One variant dispatcher (~80 LoC), one critic-prompt template file (~150 lines), one JSON parser (~40 LoC), one paragraph in SKILL.md. Bounded.

### Pilot 2 (outcome logging)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| User-correction heuristic misclassifies | High | Low (signal noise) | Conservative heuristic; periodic manual audit of 50 random records |
| Log grows unbounded | Medium | Low | Rotation at 5MB; gzip old logs |
| Users find logging invasive | Low | Medium (trust) | Side-channel; no PII beyond prompt first-200-chars; document in `/tp` boundaries |
| Signal is not actionable | Medium | Medium (wasted effort) | Kill criterion: no actionable signal after 50 turns |

**Maintenance burden:** ~50–80 LoC, no external dependencies, no model calls. Trivial.

---

## 15. Remaining unknowns

1. **External model availability on Grok for Pilot 1.** The `agy` CLI is documented in `~/.grok/AGENTS.md` and the Multi-model tool availability section. `mmx` and `codex` are mentioned. **Not yet verified in this session** whether `agy` works on demand, what its latency/cost profile is, or whether JSON-structured output is reliable. The pilot's first step is a CLI preflight.

2. **Whether the independence gap is the highest-value gap to close.** The naturalistic eval flagged it structurally (§10.2), but did not measure its frequency in natural sessions. Pilot 2 (outcome logging) would produce this signal. **Sequencing:** Pilot 2 first would be more measurement-rigorous; Pilot 1 first is more user-value-forward. Recommendation: run both in parallel; they don't depend on each other.

3. **Critic prompt quality.** `Stop_semantic_critic.py`'s prompts are tuned for Claude Code's diagnostic-RCA context. They may need adaptation for /tp's broader thought-partner domain (decisions, designs, directions — not just software RCA). The pilot's first iteration should adapt the prompts, not copy them verbatim.

4. **Judge agreement baseline.** The naturalistic eval used 1 judge per case (documented limitation). Pilot 1 should use ≥2; the disagreement rate itself is a finding.

5. **Long-term effect of state-grounding edit.** The stabilization pass verified the edit on 17 regression cases. Whether it generalizes to natural sessions is unmeasured. Pilot 2's outcome logger would surface this.

6. **Whether cc-aca-reasoning's pruned stop hooks represent abandoned designs or paused work.** The task #815 prune commit suggests "inert output, removed for cleanliness." If the designs are revived on Claude, they may be worth re-evaluating. Out of scope for this investigation.

7. **The `unified_detection` module.** Referenced by 31 consumers in `P:/.claude/hooks/UserPromptSubmit_modules/` but not directly read in this investigation. If it contains a real prompt-classifier beyond the regex in `Start_reasoning_mode_selector.py`, it may be relevant to a future adaptive-depth pilot. Not investigated due to scope.

---

## 16. Final verdict

**`GROK_COGNITION_MIGRATION_PILOTS_JUSTIFIED`**

### Rationale

The Claude Code cognition ecosystem is real and applied, but unevenly mature. Of ~50 mechanisms inspected:

- **2 mechanisms** (`anti_dodge_judge.py` pattern + `Stop_semantic_critic.py` prompts) directly address Gap 1 (independent critique) with credible portable logic and have a Grok-native implementation path via external-model CLIs. → **Pilot 1**
- **1 pattern** (`artifact_scraper` JSONL ledger) directly informs Gap 2 (outcome observability), which is **not addressed by any Claude mechanism** and is net-new on both hosts. → **Pilot 2**
- **~8 mechanisms** are real and portable but address gaps /tp already covers behaviourally (state grounding, anti-sycophancy vocabulary, contract enforcement). Porting them would add complexity without measured benefit. → **Deferred / retain-as-reference**
- **1 system** (`cc-council`) is ~80% real design with a stub orchestration loop; the capability (multi-model council with anonymized peer review) is distinct and portable, but unproven and 2.5-5× more expensive than the critic pattern. → **Phase 2, contingent on Pilot 1 evidence** (corrected from an initial "reject-as-code" disposition that conflated the stub engine with the system's overall maturity)
- **~5 mechanisms** are stubs (judge.py scoring, Start_reasoning_mode_selector.py wrapper) or pure ceremony (router glue, broken state paths). → **Rejected**

The two pilots are bounded (≤250 LoC and ≤80 LoC respectively), reversible (remove variant; delete log), fail-open (external-model unavailable → proceed normally; logger failure → no behavior change), and produce concrete evidence for adoption or rejection (≥30% blind-spot surfacing; actionable signal on ≥50 turns). No new `/tp` doctrine is added; no mechanism is implemented in this task; no unrelated files are changed.

**The smallest credible way to prove it:** Pilot 1's blinded comparison on 10–12 framing-sensitive cases (re-using C01/C02 plus new high-consequence cases) with ≥2 judges is the minimal viable evidence. Pilot 2's 50-turn signal validation is the minimal viable measurement infrastructure. Together they cost ~330 LoC, ~2–5s latency on explicitly-gated turns, and ~$0.30–2 in external-model calls across the entire pilot — in exchange for resolving whether cross-model independence and outcome observability are worth building further.

### Governing question answered

> *Which real Claude Code cognition capabilities will produce enough incremental value in Grok to justify a Grok-native implementation, and what is the smallest credible way to prove it?*

**Independent cross-model critique** (extracted from `anti_dodge_judge.py` + `Stop_semantic_critic.py`) is the single highest-value capability, because it addresses /tp's most fundamental structural limitation (same-model construct+critique) and Grok has native external-model CLI access that makes the implementation path uniquely favorable. **Minimal outcome logging** is the necessary measurement complement, without which neither this pilot nor any future cognition decision can be evidence-based. Both are justified as bounded pilots; broader migration is not.

---

## Artifacts

- **This report:** `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md`
- **Prior /tp evaluation evidence (cited):**
  - `P:\docs\tp-naturalistic-evaluation-2026-07-19\FINAL_REPORT.md`
  - `P:\docs\tp-naturalistic-evaluation-2026-07-19\MAPPING_AND_SCORES.md`
  - `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_JUDGE_SCORES.md`
  - `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_C01_C02_FAILURE_CASES.md`
  - `P:\docs\tp-grounding-eval-2026-07-19\FINAL_REPORT.md`
  - `P:\docs\tp-grounding-eval-2026-07-19\RAW_RESPONSE_OBSERVATIONS.md`
  - `P:\docs\tp-stabilization-2026-07-19\FINAL_REPORT.md`
  - `P:\docs\tp-stabilization-2026-07-19\01_control_corpus.json`
- **Source-of-truth files inspected (with hashes in §1 and §2):** all 12 mechanisms cited by row, plus 4 `/tp` files.
- **Subagent inspection transcripts:** 4 explore subagents (IDs `019f7e22-4e7c-…`, `019f7e22-4e7d-…`, `019f7e22-4e7f-…`, `019f7e22-4e80-…`) — each read 26–73 files; their full findings are preserved in this session's transcript.
