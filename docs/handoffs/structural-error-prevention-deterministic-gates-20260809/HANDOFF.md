---
thread_id: 019fe7e9-cd04-7a63-9436-1b446826024a
parent_handoff_path: none
current_session_id: 019fe7e9-cd04-7a63-9436-1b446826024a
current_terminal_id: grok-build-019fe7e9
produced_at: 2026-08-09T21:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Structural error prevention: deterministic gates + mandatory cross-model verification

## Objective

Implement the structural fixes that prevent the 5 error classes the agent made in session 019fe7e9 (fabricated constraints, strawman+capitulation, abstraction-level inheritance, ceremony-over-substance, over-process on reversible tasks). All 5 share one root cause: narrative closure pressure overriding evidence checks. All 5 have existing AGENTS.md prose rules that did not fire. The fix must be structural (hooks, gates, mandatory cross-model verification) because the research consensus is decisive that intrinsic self-correction does not reliably work.

## Status

ANALYSIS_COMPLETE_IMPLEMENTATION_NOT_STARTED — the `/tp {3}` critique + `/www` research produced a prioritized implementation plan. Nothing has been built yet. This handoff captures the plan for a fresh session to execute.

## Producing context

2026-08-09, session `019fe7e9-cd04-7a63-9436-1b446826024a`, Grok Build. Operator asked: "What durable changes can we make so that you don't make these classes of errors again?" Method: `/tp {3}` (3-lens critique: spawn returned substantive REVISE with 22 tool calls; codex+agy blocked by `Invoke-Expression` policy issue) + `/www` research (Chain-of-Verification arXiv:2309.11495, deterministic gates arXiv:2607.07405, LLM-as-judge survey Zylos 2026). Both converged on the same reframe: externalize verification out of the model's pattern-completion pathway.

## Read-first list

1. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` — the root-cause diagnosis. Documents why prose rules can't work and why the fix must externalize verification. Read first.
2. `P:/.data/wiki/concepts/premature-synthesis-without-reading-existing-capability.md` — specifies the ERR-PREVENT-02 hook design (lines 106-112). Design is ready; not built.
3. `P:/.data/wiki/concepts/scanner-driven-error-detection-mechanical-layer.md` — documents why ERR-PREVENT-05 can't be a hook. Read before proposing any mechanical fix for error 5.
4. `P:/.claude/hooks/Stop.py` lines 170-590, 1218-1305 — the existing gate dispatch chain. ERR-PREVENT-01 (the audit) greps these gates' log outputs against this session's transcript.
5. `P:/.data/wiki/concepts/playwright-connectovercdp-not-ruled-out.md` — the wiki concept written this session. Its "What this means for our workspace" section documents the error-class analysis.
6. The `/www` research findings from this session's transcript: CoVe (arXiv:2309.11495), deterministic gates (arXiv:2607.07405), LLM-as-judge survey (Zylos 2026). Not yet persisted to wiki — ERR-PREVENT-06 covers this.

## Verified facts

- [FACT] The agent made 5 distinct error classes in session 019fe7e9, verified against the session transcript (each has a specific turn reference in the producing context).
- [FACT] All 5 errors have existing AGENTS.md prose rules that name the exact failure mode. Receipt: each error maps to a specific rule (fabricated-constraints 2026-07-21, anti-binary-swing, evidence-scope, workspace-knowledge-primary, skip-decomposition-when-clear).
- [FACT] The root cause is documented in `[[reactive-pattern-matching-and-closure-pressure]]` (created 2026-07-24): "LLMs generate text by completing patterns, not by reasoning from evidence — and under closure pressure, the pattern-completion pathway shortcuts the evidence-verification pathway."
- [FACT] The wiki documents that self-applied rules are insufficient: "The same model that generates the claim also evaluates whether it has a receipt. The evaluator and the claimant share the same pattern-completion pathway. Under closure pressure, the evaluator can be captured too." (lines 88-96)
- [FACT] The `/tp` spawn lens (22 tool calls, REVISE verdict) found that Stop.py already has 8+ gates including `overconfidence_detector`, `affirmation_detector`, `narrative_intent_detector`. Two of the five errors (1+2) may already have structural coverage that didn't fire.
- [FACT] The wiki specifies the design for a `premature-synthesis-without-read` hook at `premature-synthesis-without-reading-existing-capability.md:106-112`. The design is ready; it hasn't been built.
- [FACT] The wiki explicitly states error 5 (over-process) has no tractable mechanical fix: "Errors 5-10 (false diagnosis, over-engineering, propagated unverified claims, defensive response, position reversal, over-processing) require LLM judgment. No regex can reliably catch 'defensive response' or 'over-processing'" (`scanner-driven-error-detection-mechanical-layer.md:42-44`).
- [FACT] The `/www` research found the 2025-2026 consensus: "Intrinsic self-correction — prompting a model to review and revise its own output without external grounding — does not reliably improve performance and often degrades it" (Huang et al. ICLR 2024; ACL 2025 "Dark Side of LLMs' Intrinsic Self-Correction"). Source: Zylos survey.
- [FACT] The `/www` research found deterministic pre-execution gates DO work: Reddy et al. arXiv:2607.07405 — four-gate suite raised tool-using agent success 29.6% → 42.0% (P=0.0012), effect concentrated where gates fired.
- [INFERENCE] Cross-model judging at boundaries would prevent errors 1, 2, 5 based on the Zylos survey pattern, but this is not yet tested on this workspace.

## Current state

**Done:**
- Identified the 5 error classes and their shared root cause
- Ran `/tp {3}` critique (spawn lens returned substantive; codex+agy blocked by dispatch issue)
- Ran `/www` research on structural prevention techniques
- Produced a prioritized 6-item implementation plan
- Wrote wiki concept `playwright-connectovercdp-not-ruled-out.md` (the Playwright abstraction-level error — related but not the error-prevention fix itself)

**Not done:**
- ERR-PREVENT-01: audit existing gate logs (did gates fire on errors 1+2?)
- ERR-PREVENT-02: build `premature-synthesis-without-read` hook
- ERR-PREVENT-03: build ceremony-ratio detector
- ERR-PREVENT-04: make cross-model verification mandatory before completion claims
- ERR-PREVENT-05: add reversibility decision tree to AGENTS.md
- ERR-PREVENT-06: write `error-class-coverage-matrix` wiki concept + research-persistence wiki concept

## Task packets

### ERR-PREVENT-01: Audit existing gate logs (investigation, blocking)
- **goal:** Determine whether existing gates (`overconfidence_detector`, `affirmation_detector`, `narrative_intent_detector`) fired on errors 1+2 during session 019fe7e9
- **in scope:** grep this session's transcript against `anti_sycophancy_violations.jsonl` and related gate logs
- **out of scope:** building new gates (that's ERR-PREVENT-02/03, informed by this audit's result)
- **files:** `P:/.claude/hooks/logs/` (or wherever gate logs land); session transcript at `C:\Users\brsth\.grok\sessions\P%3A%5C\019fe7e9-cd04-7a63-9436-1b446826024a\chat_history.jsonl`
- **acceptance:** documented answer to "did gates fire and get ignored, or not fire?" with receipt. This determines whether ERR-PREVENT-02/03 are the right fixes or whether the fix is presentation/posture.
- **falsifier:** gate logs are missing or empty for this session (can't determine whether gates fired)
- **verification level:** RUNTIME
- **why blocking:** the audit result may eliminate the need for ERR-PREVENT-02/03 (if gates fired and were ignored, the fix is making warnings load-bearing, not new gates)

### ERR-PREVENT-02: Build `premature-synthesis-without-read` hook
- **goal:** Implement the Stop hook specified at `premature-synthesis-without-reading-existing-capability.md:106-112` — detects capability-claim language without a recent file read
- **in scope:** new hook file, registration in Stop.py dispatch chain, shadow-mode logging for 5 sessions before BLOCK enablement
- **out of scope:** the ceremony-ratio detector (ERR-PREVENT-03 is separate)
- **files:** new `P:/.claude/hooks/Stop_premature_synthesis_gate.py`; `P:/.claude/hooks/Stop.py` (dispatch registration)
- **acceptance:** hook fires in shadow mode for 5 sessions; precision measured; if precision >80%, enable BLOCK; document in wiki
- **falsifier:** precision <80% after 5 sessions (too many false positives to enable BLOCK)
- **verification level:** RUNTIME
- **prevents:** error 3 (abstraction-level inheritance), partially error 4

### ERR-PREVENT-03: Build ceremony-ratio detector
- **goal:** Detect when wiki/grep/file-read query results don't appear in the synthesis response — the query was ceremony, not input
- **in scope:** extend the existing `external_fact_shadow.jsonl` emitter (Stop.py lines 200-260) to include a query-result-vs-response asymmetry score
- **out of scope:** the premature-synthesis hook (ERR-PREVENT-02)
- **files:** `P:/.claude/hooks/Stop.py` (extend existing emitter)
- **acceptance:** shadow mode 5 sessions; precision measured; enable BLOCK if precision holds
- **falsifier:** legitimate research queries get flagged as ceremony (false positive on genuine wiki-use)
- **verification level:** RUNTIME
- **prevents:** error 4 (ceremony-over-substance)

### ERR-PREVENT-04: Mandatory cross-model verification before completion claims
- **goal:** Make `/tp` (or lightweight `/agy`/`/codex` check) structurally required before responses claiming "done/complete/verified/fixed/ready/resolved"
- **in scope:** Stop hook detecting completion-claim language + checking for recent cross-model verification in tool-call window; operator decision on scope (every claim vs high-stakes only)
- **out of scope:** the deterministic gates (ERR-PREVENT-02/03)
- **files:** new Stop hook; possibly `/tp` SKILL.md update
- **acceptance:** hook implemented; scope per operator decision; tested on sample completion claims
- **falsifier:** the hook adds unacceptable latency to every turn, or `/tp` dispatch remains broken so cross-model verification can't fire
- **verification level:** RUNTIME
- **prevents:** errors 1, 2, 5 (the closure-pressure classes deterministic gates can't catch)
- **note:** depends on fixing the `/tp` dispatch `Invoke-Expression` issue (see Epistemic Labels) — if `/tp` can't reliably dispatch lenses, mandatory cross-model verification is unreliable

### ERR-PREVENT-05: Reversibility decision tree in AGENTS.md
- **goal:** Add a decision tree (NOT a hook) for when alternatives-framing is mandatory — if reversibility ≤1.25, default to one-line + one-verify
- **in scope:** AGENTS.md addition
- **out of scope:** any hook (the wiki documents this can't be a hook)
- **files:** `~/.grok/AGENTS.md`
- **acceptance:** decision tree added; operator approves wording
- **falsifier:** the decision tree itself becomes ceremony (agent doesn't apply it under closure pressure) — but this is the documented limit: no mechanical fix exists for error 5
- **verification level:** STATIC_INSPECTION
- **prevents:** error 5 (over-process on reversible tasks)
- **why not a hook:** `scanner-driven-error-detection-mechanical-layer.md:42-44` explicitly states over-processing requires LLM judgment

### ERR-PREVENT-06: Write wiki concepts (coverage matrix + research)
- **goal:** Write two wiki concepts: (a) `error-class-coverage-matrix` mapping each known error class to its gate/designed-gate/no-fix status; (b) the research consensus concept capturing CoVe + deterministic gates + LLM-as-judge findings
- **in scope:** two new wiki concepts
- **out of scope:** the hooks themselves
- **files:** `P:/.data/wiki/concepts/error-class-coverage-matrix.md`; `P:/.data/wiki/concepts/externalized-verification-over-intrinsic-self-correction.md` (or similar)
- **acceptance:** both validate; both committed; coverage matrix references all gates from ERR-PREVENT-02/03/04
- **falsifier:** wiki validator fails on either concept
- **verification level:** STATIC_INSPECTION

## Open decisions

- **ERR-PREVENT-04 scope:** mandatory cross-model verification before *every* completion claim (adds 60-120s latency per claim), or only high-stakes (irreversible, multi-file) claims? **Status: unresolved — needs operator input.**
- **Shadow-mode duration:** 5 sessions (proposed) or longer? The `keyword-detection-recommendations-falsified-67percent-fp.md` concept suggests FP rates are the silent killer — longer shadow mode is safer. **Status: unresolved — needs operator input.**
- **Priority ordering:** is the audit (ERR-PREVENT-01) the right first step, or should we ship ERR-PREVENT-02 immediately since the design is ready? **Status: unresolved — the spawn lens recommended audit-first; reasonable to disagree.**

## Hard constraints

- All fixes must **externalize** verification out of the model's pattern-completion pathway (per the research consensus that intrinsic self-correction doesn't work)
- New hooks must be idempotent under concurrent calls and fail-open on exceptions (per existing Stop.py patterns)
- New hooks must log to session-scoped JSONL, not shared state (per `multi-terminal-isolation-stale-data-immunity`)
- Error 5 cannot have a mechanical fix (per `scanner-driven-error-detection-mechanical-layer.md`) — proposing one is the same closure-pressure pattern being fixed
- Monitor gate cascade risk: Stop.py already runs 8+ gates; adding 2 more approaches the debugging threshold

## Cross-reference couplings

- The `/tp` dispatch `Invoke-Expression` issue affects ERR-PREVENT-04: if `/tp` can't reliably dispatch codex/agy lenses, mandatory cross-model verification is unreliable. Fix: run packer + execution as two separate `run_terminal_command` calls (the SKILL.md's "run the command verbatim" instruction means read-then-run, not chain-via-eval).
- The chrome-devtools-mcp handoff (`chrome-devtools-mcp-autoconnect-security-20260809`) is independent work from this handoff.
- Wiki concept `playwright-connectovercdp-not-ruled-out.md` (written this session) documents one instance of error 3; ERR-PREVENT-02 prevents its recurrence.

## Explicit non-goals

- Migrating `/model-web` off Puppeteer — separate workstream (the `/tp` verdict was REVISE not "switch")
- Building the browser-session-interface abstraction — separate architectural work
- Adding more AGENTS.md prose rules for errors 1-4 — the research consensus is these don't fire under closure pressure
- Self-reflection prompts ("before answering, check your work") — Huang et al. and ACL 2025 show this *degrades* performance

## Resumption protocol

1. Read this handoff + the 6 read-first files
2. Run ERR-PREVENT-01 (the audit) first — it's blocking and determines whether ERR-PREVENT-02/03 are even needed
3. Based on audit result, proceed with ERR-PREVENT-02/03/04 or pivot to presentation/posture fixes
4. ERR-PREVENT-05 (AGENTS.md decision tree) can proceed in parallel — it's not blocking on the audit
5. ERR-PREVENT-06 (wiki concepts) should be written after the implementation work is shaped, so the coverage matrix reflects what was actually built
6. Fix the `/tp` dispatch two-step pattern before ERR-PREVENT-04 depends on it

## Suggested next invocation

`/handoff claim P:/docs/handoffs/structural-error-prevention-deterministic-gates-20260809` then run ERR-PREVENT-01 (the gate-log audit).

## Last user message (verbatim)

> /handoff

## Epistemic labels

- The 5 error classes are `[FACT]` — each verified from the session transcript with a specific turn reference
- The root cause is `[FACT]` — documented in `[[reactive-pattern-matching-and-closure-pressure]]` with session evidence
- The research consensus (intrinsic self-correction fails) is `[FACT]` — two peer-reviewed papers (Huang ICLR 2024, ACL 2025) + the Zylos survey
- The deterministic-gates-work finding is `[FACT]` — Reddy et al. arXiv:2607.07405 with measured effect size and P-value
- The claim that cross-model judging prevents errors 1/2/5 is `[INFERENCE]` — the Zylos survey validates the pattern generally, but it's not tested on this workspace
- The audit result (did existing gates fire?) is `[UNKNOWN]` — ERR-PREVENT-01 exists to resolve this
- The `/tp` dispatch `Invoke-Expression` issue is `[FACT]` — I compressed packer + execution into one call; policy blocked it; codex found its input file missing and correctly refused to fabricate. Fix is documented in Cross-Reference Couplings.
