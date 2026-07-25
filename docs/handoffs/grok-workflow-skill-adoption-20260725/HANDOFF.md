---
thread_id: 9b7c1f4a-3e2d-4f8a-9c61-2a5e8d7b3f01
parent_handoff_path: none
current_session_id: 019f9b00-75fc-7290-9a2d-080c3d3c529b
current_terminal_id: noterm
produced_at: 2026-07-25T21:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 1ca97f48ed13f819488dba67283b621934e07975
---

# Handoff — Grok workflow adoption POC for 4 recommended skills

## Objective

Decide whether to add Grok workflow (`workflow` tool / Rhai scripts) as an **optional heavy-mode execution path** for four skills (`/www depth=deep`, `/debrief --deep`, `/refactor --budget N`, `/review --durable/--deep`), starting with a single proof-of-concept on `/www` that either proves the model and unlocks the other three, or refutes it and closes the thread.

**Scope bounds:** Work scope is one POC skill (`/www` depth=deep) plus three queued adopters. Total fleet is ~49 skills across user/workspace/project scopes; only 4 are candidates. The other ~45 were classified NOT-a-fit with verified reasons (see Explicit non-goals).

## Status

**OPEN** — analysis complete; implementation not started. Awaiting operator decision on whether to proceed with the `/www` POC, and on the falsifier threshold that defines "proves the model."

## Producing context

- Date: 2026-07-25
- Producing session: `019f9b00-75fc-7290-9a2d-080c3d3c529b` (Grok Build, model glm-5-2 inherited)
- Producing terminal: `noterm`
- Head at production: `1ca97f48ed13f819488dba67283b621934e07975` (note: `git rev-parse HEAD` at handoff time was `b20e09e7` — tree moved during the session from a wiki-commit `cbb1150`; re-verify cited SKILL.md line numbers before acting)
- Source work: `/www` run 3 on grok-build-workflows (community sentiment + security incident) followed by `/tp` two-lens critique on skill-fit classification

## Read-first list (ordered, with reasons)

1. `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` — **canonical concept**. Contains: what workflows are, when to use/not use, failure modes, Rhai dialect constraints, framework matrix, cost economics, community sentiment, security incident. Start here; everything below assumes this context.
2. `C:\Users\brsth\.grok\bundled\skills\create-workflow\SKILL.md` — **the authoring procedure + Rhai language reference**. Read before writing any `.rhai` script. This is what `/www` POC will use.
3. `C:\Users\brsth\.grok\skills\www\SKILL.md` — **the POC target**. Read Phase 2 (multi-round research), especially "Parallel subagent dispatch (for broad topics)" which already encodes the fan-out pattern in prose. The POC wraps this in Rhai.
4. `C:\Users\brsth\.grok\skills\debrief\SKILL.md` — **adopter #2**. Read "The 5-Phase Pipeline" (Phase 1 fan-out, Phase 3 verify, Phase 4 critic) and "Adaptive Modes" (`--deep` triggers 5 lens + verifier + critic).
5. `C:\Users\brsth\.grok\skills\refactor\SKILL.md` — **adopter #3**. Read Step 6 (Execute one seam) + Step 7 (Walk), and the `seams.json` schema (each seam has `verify_commands`, `end_to_end_verification`, `primary_owner`, `depends_on`).
6. `C:\Users\brsth\.grok\skills\review\SKILL.md` — **adopter #4 (highest drift risk)**. Read Step 0 (run directory), Step 4 (specialist pass), Step 5 (verify pass). Note the existing terminal-scoped `.artifacts` state machine — the pre-mortem (F7) flags this as the highest-transition-cost target.
7. `C:\Users\brsth\.grok\skills\tp\SKILL.md` — reference for the two-lens methodology that produced the classification. Not load-bearing for the POC but documents how the recommendations were derived.

**Wiki grounding (related concepts):** `[[grok-build-workflows-rhai-orchestration]]` (primary), `[[agentic-sdlc-skill-lifecycle-architecture]]` (skill lifecycle context), `[[llm-handoff-best-practices]]` (agent context isolation — the "clean focused context" property that workflows also provide).

## Verified facts (with source paths)

- [FACT] Grok workflows are Rhai scripts that fan out across subagents, run in background, return one synthesized report. Default budget 128 agents, max 1024. Saved to `.grok/workflows/<name>.rhai` (project) or `~/.grok/workflows/<name>.rhai` (user-global). Source: `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` lines 47-71.
- [FACT] The dominant failure mode is per-agent context-overhead cost explosion (~10× a normal session under fan-out), not the parallelism ceiling. Source: same concept, "Cost economics" section; corroborated by HN 48311705, r/ClaudeAI 1tq9ofy, avinashsangle.
- [FACT] `/www` SKILL.md already encodes parallel subagent dispatch in prose: "When the research topic spans ≥3 independent sub-areas, dispatch parallel subagents instead of serial /web calls… 4 parallel M3 subagents × 2-4 tool calls each = ~8-16 quota calls, ~90-140s wall time." Source: `C:/Users/brsth/.grok/skills/www/SKILL.md` Phase 2 "Parallel subagent dispatch" + Provenance section "Enhancement batch (2026-07-24b)".
- [FACT] `/debrief` SKILL.md has explicit adaptive modes: `--light` (1 model sequential), `--standard` (5 lens no critic), `--deep` (5 lens + verifier + critic). Token budget: ~2.5× single-model in Standard, ~4× in Deep. Source: `C:/Users/brsth/.grok/skills/debrief/SKILL.md` "Adaptive Modes" + "Implementation Notes".
- [FACT] `/refactor` seams.json schema includes per-seam `verify_commands`, `end_to_end_verification`, `primary_owner`, `depends_on`, `delete_or_close`. "Loop runnable seams" is Step 7. Source: `C:/Users/brsth/.grok/skills/refactor/SKILL.md` Step 4.4 + Step 7.
- [FACT] `/review` already has terminal-scoped run directories (`P:\.artifacts\$termSafe\grok-review\$slug\$ts\`), `FINDINGS.md` + `findings.json` + `_run.json` + `_manifest.json` + state.md. Adding a workflow journal file would be a 4th-6th state location. Source: `C:/Users/brsth/.grok/skills/review/SKILL.md` Step 0.
- [FACT] The `/tp` two-lens critique (subagent `019f9b13-34a8-7980-8b79-c058eca9b385`, 36.88s, 6 tool calls) produced 7 findings; 4 substantive disagreements with the primary classification, of which 3 survived verification (F1 `/refactor` promote, F2 `/review` demote on cost gate, F3 `/debrief` streaming matters). F4 `/marketplace-bridge` was refuted (HTTP fan-out, no model-judgment-in-loop — same class as `/model-benchmark`). Source: subagent transcript in session `019f9b00…`.
- [FACT] The Grok Build repo-upload security incident (Jul 12-16, 2026) means any credentials in repos touched by Grok Build pre-Jul-16 should be considered exposed. Verified across 5+ sources. Source: wiki concept "Vendor data-exfiltration incident" row in Failure modes table.

## Current state

**Analysis complete; no implementation started.** Specifically:

- ✅ Classification done: 4 skills recommended as "workflow as option for heavy mode"; ~45 classified NOT-a-fit with reasons
- ✅ Two-lens critique done; 3 of 4 substantive disagreements integrated
- ✅ POC target selected (`/www` depth=deep) with explicit rationale (lowest transition cost, parallel-dispatch logic already in SKILL, clear falsifier)
- ✅ Adoption order proposed: `/www` → `/debrief` → `/refactor` → `/review`
- ❌ No Rhai script written
- ❌ No `/www` workflow variant tested
- ❌ No falsifier threshold quantified (what counts as "proves the model"?)
- ❌ No decision on whether to claim the work for a specific host

## Task packets (one per bounded unit of residual work)

### AC-WWW-POC-01 — Author and smoke-test `/www` workflow variant

- **goal:** Produce a Rhai workflow script at `~/.grok/workflows/www-deep.rhai` that wraps `/www` Phase 2 (Round 1 gap-targeted research → Round 2 discovery → Round 2.5 ingestion → Round 3 disconfirmation) as a background-run workflow, then smoke-test it on one real research topic.
- **in scope:**
  - Read `create-workflow` SKILL.md end-to-end before writing any Rhai
  - Map `/www` SKILL.md Phase 2's multi-round structure to Rhai `phase()` calls
  - Use `parallel()` for the existing "Parallel subagent dispatch" pattern (M3 subagents per sub-area)
  - Preserve the disconfirmation pass as a mandatory final phase (per `/www` SKILL.md Round 3)
  - Output one synthesized wiki-ready concept (matching `/www` Phase 3 contract)
  - Smoke-test with `validate_only: true` first, then one real run
- **out of scope:**
  - Modifying `/www` SKILL.md itself (the workflow is a peer execution path, not a replacement)
  - Touching `/debrief`, `/refactor`, `/review` (those are AC-DEBRIEF-01, AC-REFACTOR-01, AC-REVIEW-01 — queued behind this POC's result)
  - Changing the default `/www` behavior (the workflow variant is `depth=deep` opt-in only)
- **files / anchors:**
  - New: `~/.grok/workflows/www-deep.rhai`
  - Reference: `C:/Users/brsth/.grok/skills/www/SKILL.md` Phase 2 (lines ~140-380)
  - Reference: `C:/Users/brsth/.grok/bundled/skills/create-workflow/SKILL.md` (full)
  - Reference: `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` "Rhai dialect specifics" (lines ~240-258) — the constraint list (no closures in parallel, no regex, no wall-clock, reserved keywords)
- **acceptance:**
  - Script passes `validate_only: true` smoke check (per `workflow` tool contract)
  - One real run completes end-to-end on a topic with ≥3 sub-areas
  - Run produces a wiki-ready concept with: (a) sources from ≥2 independent rounds, (b) explicit disconfirmation pass output, (c) decision-context section
  - Run is resumable: pause mid-run, resume, confirm no redo of committed host calls
  - Total wall-clock for the run is within 2× of the inline parallel-M3 dispatch baseline (~90-140s × 2-3 rounds = ~5-10 min budget)
- **falsifier:** The POC fails if any of: (a) workflow variant produces lower-quality output than inline dispatch on the same topic (judged by source-count, disconfirmation pass presence, decision-context completeness); (b) wall-clock exceeds 3× inline baseline; (c) resume-after-pause redoes committed host calls (violates journal contract); (d) the workflow cannot express the multi-round structure because of Rhai constraints (no closures in `parallel()`, no regex, etc.) — in which case document the specific blocker and close the thread.
- **verification level required:** LIVE_BEHAVIOR — must observe a real run, not just static inspection. Static `validate_only` is necessary but not sufficient.
- **estimate:** ~2-4h authoring (Rhai learning curve) + ~30min smoke test + ~10min real run = half-day to first result.
- **auth-expiry mitigation:** N/A — no auth-bound resources in `/www`'s path. NotebookLM Mode B (if used) needs `nlm login` but Round 2.5 is optional.

### AC-DEBRIEF-01 — Adopt workflow as `/debrief --deep` execution path (QUEUED, depends on AC-WWW-POC-01 success)

- **goal:** Wrap `/debrief` Phase 1 (5 parallel lens subagents) + Phase 3 (verifier) + Phase 4 (critic) as a Rhai workflow that runs in background for `--deep` mode on >100-turn sessions.
- **in scope:** Phase 1 fan-out as `parallel()`, Phase 3 verify as second phase, Phase 4 critic as third phase, Phase 2 synthesis as `complete()`. Preserve model-fallback chains (probe → fallback).
- **out of scope:** `--light` and `--standard` modes (stay inline). Streaming UX (the tradeoff is accepted for `--deep` because the user walks away).
- **files / anchors:** New `~/.grok/workflows/debrief-deep.rhai`; reference `C:/Users/brsth/.grok/skills/debrief/SKILL.md` Phase 1-4.
- **acceptance:** Background run on a >100-turn session produces the same finding schema as inline; journal resume survives a forced pause mid-Phase-1.
- **falsifier:** Workflow variant misses findings the inline version would have caught (judged by running both on the same session and diffing). Or: model-fallback chains cannot be expressed in Rhai (probe + retry pattern) — document blocker and defer.
- **verification level required:** LIVE_BEHAVIOR — A/B compare workflow vs inline on same session.
- **dependency:** Requires AC-WWW-POC-01 to have proven the model. If POC fails, this is cancelled.

### AC-REFACTOR-01 — Adopt workflow as `/refactor --budget N` execution path for independent seams (QUEUED, depends on AC-WWW-POC-01 success)

- **goal:** When `/refactor` is invoked with `--budget N` (N≥3) AND all seams have empty `depends_on`, run seams in parallel as a Rhai workflow with per-seam `verify_commands` as the verification gate.
- **in scope:** Parallel seam execution, per-seam verify gate (fail-closed blocks merge), `complete()` synthesis to RESULT.md. Each seam writes to its own worktree branch.
- **out of scope:** Sequential seam chains (any seam with non-empty `depends_on` stays inline). Single-seam `--slice` mode. Worktree cleanup logic (stays in `/refactor` parent).
- **files / anchors:** New `~/.grok/workflows/refactor-parallel-seams.rhai`; reference `C:/Users/brsth/.grok/skills/refactor/SKILL.md` Step 6-7 + seams.json schema.
- **acceptance:** Parallel run on a 3-seam independent plan completes all 3 with per-seam verify PASS; failed verify on one seam does not poison the others; RESULT.md correctly aggregates.
- **falsifier:** Parallel seams interfere (e.g., two seams touch the same file — must be caught at plan time by the dependency check, not at execute time). Or: per-seam worktree isolation cannot be expressed cleanly in Rhai.
- **verification level required:** LIVE_BEHAVIOR — real 3-seam plan with known-independent targets.
- **dependency:** Requires AC-WWW-POC-01 success. Higher transition cost than AC-DEBRIEF-01 because of worktree-per-seam isolation.

### AC-REVIEW-01 — Adopt workflow as `/review --durable`/`--deep` execution path (QUEUED, lowest priority, highest drift risk)

- **goal:** For `--durable` or `--deep` cross-package reviews, offer workflow as background-run option with journal resume.
- **in scope:** Step 4 specialist fan-out as `parallel()`, Step 5 verify as second phase, Step 5.4 root-cause clustering in synthesis. Bridge existing `.artifacts/$term/grok-review/...` paths into the workflow's packet handoff.
- **out of scope:** Default `/review` (stays inline — cost gate). `--lite` and `focused` tiers. The existing terminal-scoped state machine (workflow journal is additive, not replacement).
- **files / anchors:** New `~/.grok/workflows/review-deep.rhai`; reference `C:/Users/brsth/.grok/skills/review/SKILL.md` Step 0, 4, 5, 5.4.
- **acceptance:** Cross-package review completes in background; FINDINGS.md + findings.json produced at the existing paths; journal resume survives pause.
- **falsifier:** Pre-mortem F7 fires — workflow journal drifts from `FINDINGS.md` + `findings.json` + `_run.json` + state.md, creating a 4th-6th state location that consumers (`/check`, `/refactor`'s `findings_link.md`) cannot reconcile. If drift cannot be resolved by making the workflow journal the single source of truth (deprecating `_run.json`), defer this task indefinitely.
- **verification level required:** LIVE_BEHAVIOR + drift audit — must verify no state-location drift after 3 real runs.
- **dependency:** Requires AC-WWW-POC-01 success AND a deliberate decision to accept the drift risk. This is the task most likely to be deferred indefinitely.

## Open decisions (explicit, framed as questions)

### D1. What falsifier threshold defines "the POC proves the model"?

- **Question:** AC-WWW-POC-01's falsifier lists 4 failure modes. Which combination of survivors defines success?
- **Options:**
  - (A) All 4 must pass — strictest; POC must match inline quality AND speed AND resume AND expressibility
  - (B) Quality + expressibility must pass; speed and resume are nice-to-have — pragmatic; accepts some latency for durability
  - (C) Quality + resume must pass; speed is allowed to be 2-3× slower — prioritizes the async/journal value prop
- **Selection criterion:** the operator's actual reason for wanting workflows. If the reason is "I want to walk away from long research" → (C). If the reason is "I want faster research" → workflows are the wrong tool (per the wiki: workflows don't improve per-agent speed).
- **Currently leads:** (C) — the wiki research established that workflow's unique value is async + journal resume, not speed. But this is the operator's call.
- **Evidence that would change the lead:** if the operator says "I actually want speed," the recommendation inverts — workflows are the wrong tool and this handoff should be closed WONTFIX.

### D2. Does the operator want to claim this work for a specific host?

- **Question:** Should `assigned_to: grok` be set on this handoff, or leave it unclaimed for any host/agent to pick up?
- **Options:**
  - (A) Claim for `grok` — Grok Build is the workflow runtime host; only Grok can author/test Rhai scripts
  - (B) Leave unclaimed — let any host pick it up
- **Selection criterion:** whether non-Grok hosts (Claude, Codex) can usefully contribute. They cannot test Rhai scripts (no workflow runtime), so (A) is the principled answer.
- **Currently leads:** (A) — but leaving unset for now per the optional-assignment default. Operator can set it on pickup.

### D3. Should the POC be one run or three?

- **Question:** AC-WWW-POC-01 acceptance says "one real run." The wiki falsifier rule for the `/www` skill itself says "within 6 months, if consistently invoked as just /web, retire." Should the POC require 3 successful runs before unlocking AC-DEBRIEF-01?
- **Options:**
  - (A) One run is enough — if it passes all 4 falsifier checks, the model is proven
  - (B) Three runs on different topics — guards against topic-specific luck
- **Selection criterion:** cost of a false positive (proceeding to AC-DEBRIEF-01 on a lucky POC, then having it fail there) vs cost of delay (3 runs × ~10min = 30min extra).
- **Currently leads:** (B) — the wiki's own falsifier uses "consistently" language; one run is a weak signal. But (A) is defensible if the operator wants speed.

## Hard constraints

1. **No default-path replacement.** Workflow is an optional heavy-mode path for all 4 skills. The default invocation stays inline. Violating this 10×s the cost of every `/review`, `/debrief`, `/refactor` invocation.
2. **No state-location drift without deprecation.** If a workflow adds a journal file alongside existing state files (`FINDINGS.md`, `seams.json`, `_run.json`, state.md), the workflow journal must either (a) be the single source of truth with the old files deprecated, or (b) be purely additive with a documented reconciliation rule. Silent drift is the pre-mortem failure (F7).
3. **No re-implementing skill logic in Rhai.** The workflow wraps the skill's existing phases; it does not redefine the contract. `/www`'s disconfirmation pass stays mandatory; `/review`'s verify pass stays mandatory; `/refactor`'s per-seam `verify_commands` stay mandatory.
4. **POC gates the rest.** AC-DEBRIEF-01, AC-REFACTOR-01, AC-REVIEW-01 are all QUEUED behind AC-WWW-POC-01. If the POC fails, the thread closes and the other three are cancelled. Do not start them in parallel.
5. **Grok Build CLI is the only host.** Rhai workflows run only in Grok Build. Claude Code and Codex cannot author or test these. (Per `host: grok` convention in `~/.grok/AGENTS.md` § "Skill authoring host provenance.")
6. **Security incident context.** If the operator's repos were touched by Grok Build pre-Jul-16-2026, credentials should already be rotated. This is background, not a blocker — but flag if any POC run touches credentials.

## Cross-reference couplings

- `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` → the canonical concept. If it is updated (e.g., new failure mode discovered), re-read before POC. The "Rhai dialect specifics" section is load-bearing for AC-WWW-POC-01.
- `C:/Users/brsth/.grok/bundled/skills/create-workflow/SKILL.md` → the authoring reference. Bundled skill — reinstalled on Grok Build updates; check version if authoring breaks.
- `C:/Users/brsth/.grok/skills/www/SKILL.md` Phase 2 → the POC target. If `/www` is updated (e.g., Round 2.5 changes), the workflow variant must track the change or drift.
- `~/.grok/AGENTS.md` § "Alternatives before architectural implementation" → the gate that should fire before AC-WWW-POC-01 implementation. The POC IS an architectural decision (reversibility ≥1.75); the alternatives gate should evaluate (workflow vs. extend inline parallel-M3 vs. external orchestrator like LangGraph).
- `~/.grok/AGENTS.md` § "File editing protocol" → applies to writing the `.rhai` script (new file, use `write` tool directly, not shell).
- This handoff's `accurate_as_of_head` → `1ca97f48…`. `git rev-parse HEAD` at handoff time was `b20e09e7` (tree moved mid-session from wiki commit `cbb1150`). **Re-verify cited SKILL.md line numbers before acting** — the skills are under active development.
- `/tp` subagent transcript `019f9b13-34a8-7980-8b79-c058eca9b385` → the critique that produced the integrated classification. Not durable past session end; the integrated findings are in this handoff's "Verified facts."

## Other outstanding streams (not handed off)

- **Grok-build-workflows wiki concept run 3** — the `/www` run that preceded this handoff. Closed: concept updated, ledger run 3 appended, committed `cbb1150`. No outstanding work.
- **Security incident credential rotation** — if the operator has not yet rotated credentials for repos touched by Grok Build pre-Jul-16-2026, that is outstanding. Not this handoff's scope; flagged in Hard constraint #6.

## Explicit non-goals

- **Do NOT rewrite any skill onto workflows as the default path.** All 4 candidates are "workflow as option for heavy mode." Default stays inline.
- **Do NOT touch the ~45 skills classified NOT-a-fit.** Specifically: `/model-benchmark`, `/marketplace-bridge`, `/web`, `/search-fleet` (HTTP fan-out, no model-judgment-in-loop); `/tp`, `/plan`, `/plan-writer`, `/handoff`, `/wiki`, `/why`, `/close`, `/create-skill`, `/wargame`, `/prompt-patterns`, `/imagine`, `/help`, `/tasks` (sequential/interactive/single-phase); `/safe-git`, `/grok-route`, `/grok-discovery`, `/grok-verify` (synchronous preflight gates); `/notebooklm`, `/nlm-bulk-ingest` (rate-limited external API bottleneck); `/codex`, `/agy`, `/mmx` (single CLI invocations); `/aar`, `/design` (borderline — the /tp critique flagged `/aar` as a possible miss worth checking, but it is NOT in this handoff's scope; a separate investigation would be needed).
- **Do NOT start AC-DEBRIEF-01, AC-REFACTOR-01, or AC-REVIEW-01 before AC-WWW-POC-01 resolves.** They are explicitly queued. Parallel starts waste work if the POC fails.
- **Do NOT use workflows for any task where streaming intermediate results matters.** `/debrief --light`/`--standard` stay inline because the user inspects lenses mid-flight. `/review` default stays inline because the user is waiting on the verdict.
- **Do NOT treat the security incident as in-scope for this handoff.** It is context, not work. If credential rotation is needed, it is a separate stream.

## Resumption protocol

1. **Re-verify the tree.** Run `git -C P:/ rev-parse HEAD` and compare to `accurate_as_of_head: 1ca97f48…`. If drifted, re-read the 4 SKILL.md files to confirm line numbers in this handoff still resolve.
2. **Read the canonical concept:** `P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md` (especially "Rhai dialect specifics" and "Failure modes").
3. **Read the authoring reference:** `C:/Users/brsth/.grok/bundled/skills/create-workflow/SKILL.md` end-to-end.
4. **Resolve open decision D1** (falsifier threshold) with the operator before writing any Rhai. This determines what "done" means for AC-WWW-POC-01.
5. **Run the alternatives gate** per `~/.grok/AGENTS.md` § "Alternatives before architectural implementation." Options: (a) workflow, (b) extend inline parallel-M3 dispatch (status quo), (c) external orchestrator (LangGraph/symphony). Selection criterion: async-resume value vs. transition cost vs. host lock-in. Document the chosen option before authoring.
6. **Only after steps 4-5 resolve:** begin AC-WWW-POC-01 by creating `~/.grok/workflows/www-deep.rhai`.

## Suggested next invocation

Copy-paste for the next session:

```
I want to start the /www workflow POC from handoff P:\docs\handoffs\grok-workflow-skill-adoption-20260725\HANDOFF.md.

First: re-verify the cited SKILL.md line numbers against current HEAD (the
handoff notes the tree moved mid-session).

Second: help me resolve open decision D1 — what falsifier threshold defines
"the POC proves the model"? My current lean is option (C): quality + resume
must pass, speed allowed 2-3x slower, because I want the async/walk-away
value prop, not speed.

Third: once D1 is resolved, run the alternatives gate
(~/.grok/AGENTS.md § "Alternatives before architectural implementation")
for workflow vs. extend-inline vs. external-orchestrator before we author
any Rhai.

Do NOT start writing Rhai until D1 and the alternatives gate are resolved.
```

## Last user message (verbatim)

> "/handoff for the skills you do recommend considering."

## Epistemic labels per claim

- **[FACT]** All "Verified facts" are cited to specific files with line numbers or to the subagent transcript ID. Re-verify line numbers against current HEAD before acting (tree moved mid-session).
- **[INFERENCE]** The classification of ~45 skills as NOT-a-fit is inferred from reading their SKILL.md descriptions + the workflow-fit criteria in the wiki concept. The /tp subagent verified the borderline cases (`/refactor`, `/marketplace-bridge`, `/nlm-bulk-ingest`) — 3 of 4 substantive disagreements survived verification. The classification is high-confidence but not exhaustive; `/aar` and `/design` were flagged as possible misses not pursued.
- **[INFERENCE]** The adoption order (`/www` → `/debrief` → `/refactor` → `/review`) is inferred from transition-cost ascending + drift-risk ascending. It is a recommendation, not a verified optimum.
- **[INFERENCE]** "POC gates the rest" (Hard constraint #4) is inferred from the wiki's falsifier discipline ("within 6 months, if consistently invoked as just /web, retire") — one run is a weak signal, so queuing the others behind it prevents cascading waste.
- **[UNKNOWN]** Whether the operator's actual reason for wanting workflows aligns with the async/journal value prop (decision D1). This is the single highest-leverage unknown; resolving it determines whether the whole thread proceeds.
- **[UNKNOWN]** Whether `/aar` or `/design` have a workflow-fit shape the /tp critique missed. Flagged in Explicit non-goals as out-of-scope but worth a separate check.

## Falsifier (handoff-level)

This handoff is wrong if:

1. The operator's actual goal for workflows is **speed** (not async/journal) — in which case workflows are the wrong tool (per the wiki: workflows optimize throughput, not per-agent correctness or speed), and this entire thread should be closed WONTFIX.
2. The operator tries AC-WWW-POC-01 and the inline parallel-M3 dispatch already in `/www` SKILL.md is **already good enough** — in which case the workflow variant adds transition cost without marginal value.
3. The `/tp` critique missed a better POC candidate than `/www` (e.g., if `/aar` turns out to be a stronger fit) — in which case re-prioritize before authoring.
4. The security incident context turns out to be a live blocker (operator's credentials were not rotated and a POC run would touch them) — pause and rotate first.

If any pattern appears, close the handoff or re-scope before investing in Rhai authoring.
