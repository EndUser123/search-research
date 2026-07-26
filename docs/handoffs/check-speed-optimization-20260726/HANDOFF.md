---
thread_id: check-speed-optimization-20260726
parent_handoff_path: P:/docs/handoffs/session-019f9f48-shipped-work-20260726/HANDOFF.md
current_session_id: 019f9f48-5ad0-7a01-9f1e-e70d0788d383
current_terminal_id: grok-019f9f48
produced_at: 2026-07-26T21:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 90bdf23
---

# /check speed optimization — diagnose and fix slow verifier subagents

## Objective

Diagnose why `/check` verifier subagents are slow (13+ minutes wall clock this session) and implement targeted speedups. The issue is not that `/check` is fundamentally slow — it's that specific verifier behaviors inflate tool-call count and per-call latency, especially when verifying contract/config concerns that involve large files.

## Evidence (this session's /check run — hard data)

Three verifiers ran in parallel against session 019f9f48:

| Concern | Duration | Tool calls | s/call | Notes |
|---|---|---|---|---|
| Python validator (code) | 212s (3.5min) | 19 | 11.2 | Ran pytest + manual tests; reasonable |
| Contract/config | **802s (13.4min)** | **57** | **14.1** | **SLOWEST — 5.3x longer than wiki verifier** |
| Wiki + handoffs (doc) | 151s (2.5min) | 37 | 4.1 | Read many small files; reasonable |
| **Wall clock (parallel)** | **~802s = 13.4min** | 113 total | — | Contract verifier gated the wall clock |

For comparison, the AAR subagent this session: 1126s, 86 calls, 13.1s/call.

**The contract verifier is the bottleneck.** It took 5.3x longer than the wiki verifier despite doing less conceptual work. The wall clock is gated by the slowest verifier (parallel execution).

## Root cause hypotheses (ranked by likelihood)

### H1: Repeated reads of large files (HIGHEST LIKELIHOOD)

The contract verifier read `AGENTS.md` (~20KB) and `close/SKILL.md` (~30KB) multiple times across its 57 tool calls. Each `read_file` of a 20-30KB file costs ~3-5s (tool overhead + context injection). If the verifier read each file 3-5 times, that's 20-50s of redundant I/O alone.

**Evidence:** the contract verifier's output mentions reading AGENTS.md at "line 446", "line 233", "lines 442, 460" — suggesting multiple targeted reads rather than one full read cached in context. The wiki verifier, by contrast, read each concept file once (4 concepts × 1 read each = ~16s of I/O for the full set).

**Fix:** the verifier prompt should instruct: "Read each file ONCE. If you need to reference a specific line later, cite it from your context — do not re-read the file."

### H2: Overly broad concern scope (MEDIUM LIKELIHOOD)

The contract verifier was asked to verify 3 files (AGENTS.md, CLAUDE.md, close/SKILL.md) across 5 acceptance criteria. That's a broad scope for one verifier. The wiki verifier also had broad scope (4 concepts + 4 handoffs across 6 criteria) but finished 5.3x faster because each file was small and the verification was structural (schema check, cross-ref check) rather than semantic (does this rule contradict that rule).

**Fix:** split contract/config concerns by file, not by concern-type. One verifier per file, not one verifier for "all contract/config changes." This parallels better and keeps each verifier's context smaller.

### H3: Semantic verification is inherently slower than structural (MEDIUM)

The contract verifier had to check "does the new AGENTS.md rule contradict any existing rule in the same file?" — a semantic check that requires reading the full file and reasoning about consistency. The wiki verifier's checks were mostly structural (frontmatter present? sections exist? links resolve?). Semantic verification takes longer per tool call because the model has to reason, not just match patterns.

**Fix:** this is partly inherent. But the verifier can be told to use `grep` for contradiction patterns (e.g., "search for rules that say X, then check if the new rule says not-X") rather than reading the full file and reasoning linearly.

### H4: Preprocessor packet not utilized effectively (LOW)

The evidence packet (`evidence-packet.json`) was provided to each verifier. But the verifiers may not have read it efficiently — the packet has `scope_files`, `claim_verbs`, `unverified_claim_candidates` that could short-circuit many checks without reading source files at all.

**Fix:** the verifier prompt should say: "Read the evidence packet FIRST. For each acceptance criterion, check whether the packet already contains the evidence you need. Only read source files when the packet is insufficient."

### H5: Deterministic pre-check not utilized (LOW)

The `/check` skill has a deterministic pre-check step (Step 0.9) that runs ruff/pyright on changed `.py` files before spawning verifiers. But this session's contract/config changes were not `.py` files — so the deterministic pre-check didn't run for them. If there were a deterministic pre-check for config/contract files (e.g., YAML linting, frontmatter validation), it could short-circuit some verifier work.

**Fix:** add deterministic pre-checks for non-Python files (markdown linting, YAML validation, cross-reference checking). These are sub-second and can eliminate the need for an LLM verifier to do structural checks.

## Open questions

### 1. Is 13 minutes acceptable for /check?

**Depends on use case.** At session close (the current pattern), 13 minutes is tolerable — the operator is winding down anyway. Mid-session (if the skill-recommendation hook fires `/check` earlier), 13 minutes is too long — it breaks flow.

**Target:** <5 minutes wall clock for a 3-verifier run. <3 minutes for a 1-verifier run. This requires cutting the slowest verifier's time by ~60%.

### 2. Should /check have a `--quick` mode?

A `--quick` mode could:
- Skip Phase B (code review) — Phase A only (trace review)
- Skip the evidence packet — LLM-only verification
- Run 1 verifier instead of N (collapse concerns)
- Skip auto-/review escalation

**Trade-off:** `--quick` is less thorough. But for mid-session checks (the skill-rec-hook use case), less thorough + faster is better than more thorough + too slow to be useful.

**Recommendation:** add `--quick` mode. Default stays standard (thorough). `--quick` is the mid-session option.

### 3. Should verifiers be model-tiered more aggressively?

The `/check` SKILL.md already has model tiering (doc → M3, code → parent/glm-5-2, security → glm-5-2). But this session's verifiers all inherited the parent model (Grok). If the wiki verifier had used M3 instead, it would have been cheaper (but possibly similar speed — M3 latency is ~4-6s/call vs Grok's ~10-14s/call).

**Recommendation:** enforce the model tiering. Doc-only verifiers → M3. Code verifiers → parent. This alone could cut the wiki verifier's time from 151s to ~60s.

### 4. Can the evidence packet be richer to reduce verifier file reads?

The current packet has `scope_files` but not file *contents*. If the packet included the actual diff or file-content excerpts for changed files, verifiers could skip the `read_file` call entirely for files that are fully captured in the packet.

**Trade-off:** larger packet = more context injected per verifier = higher per-call token cost. But fewer calls = lower total latency.

**Recommendation:** add `changed_file_excerpts` to the packet — the diff or the changed sections only (not full file contents). This is the highest-leverage packet enhancement.

## Scope

### What this handoff covers

- Diagnosis of /check slowness (root cause hypotheses with evidence)
- Targeted speedups (read-once discipline, per-file verifier splitting, model tiering, `--quick` mode, richer evidence packet)

### What this handoff does NOT cover

- Replacing /check with a different verification system
- Removing the parallel-verifier architecture (it's correct; the issue is per-verifier efficiency)
- The skill-recommendation hook (separate handoff at `skill-recommendation-hook-20260726`)

## Acceptance criteria

1. /check wall clock <5 minutes for a typical 3-verifier run (currently ~13min)
2. No verifier exceeds 4 minutes (currently the slowest is 13.4min)
3. `--quick` mode exists: <2 minutes wall clock, Phase A only, 1 verifier
4. Evidence packet includes `changed_file_excerpts` (diff or changed sections)
5. Verifier prompt includes "read each file ONCE" instruction
6. Model tiering enforced: doc verifiers use M3, code verifiers use parent/glm-5-2
7. Regression: the current 28-test validator suite still passes after changes

## Recommended approach

1. **Measure first.** Before optimizing, add timing instrumentation to the verifier spawner (log start/end time per verifier). This confirms which hypothesis is correct.
2. **Read-once discipline.** Add to the verifier prompt template: "Read each file ONCE. Cite line numbers from context for subsequent references."
3. **Split contract/config by file.** One verifier per file, not one verifier for all contract changes.
4. **Enforce model tiering.** Route doc verifiers to M3 via `spawn_subagent(model="minimax-m3")`.
5. **Add `--quick` mode.** Phase A only, 1 verifier, skip auto-/review.
6. **Enrich evidence packet.** Add `changed_file_excerpts` with diff content.
7. **Re-measure.** Confirm wall clock <5 minutes.

## Evidence

- **Latency data:** this session's `/check` run — 3 verifiers, 802s wall clock (parallel), 113 total tool calls
- **Slowest verifier:** contract/config — 802s, 57 tool calls, 14.1s/call (5.3x slower than wiki verifier)
- **Comparison data:** AAR subagent same session — 1126s, 86 calls, 13.1s/call
- **Evidence packet:** `P:\.artifacts\console_6218e218-6bc3-4357-bdc6-0a94\grok-check\20260726-151049-605\packets\evidence-packet.json`
- **Check run dir:** `P:\.artifacts\console_6218e218-6bc3-4357-bdc6-0a94\grok-check\20260726-151049-605\`

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** the skill-recommendation hook (`skill-recommendation-hook-20260726`) — if /check stays at 13min, mid-session recommendations to run /check will be impractical
- **Non-blocking to:** all other work

## Read-first list

1. `P:/.grok/skills/check/SKILL.md` — the skill spec (Step 0.9 deterministic pre-check, Step 2 verifier packets, Step 3 model tiering, Step 6.2 auto-/review triggers)
2. `P:/.grok/skills/check/__lib/preprocessor.py` — the evidence-packet builder (add `changed_file_excerpts` here)
3. This session's evidence packet: `P:\.artifacts\console_6218e218-6bc3-4357-bdc6-0a94\grok-check\20260726-151049-605\packets\evidence-packet.json`
4. Latency analysis script: `P:/tmp/check_latency_analysis.py` (data + hypotheses)

## Status

OPEN. Not started. Diagnosis captured with hard data; implementation deferred.

## Related wiki concepts

- `advisory-vs-mandatory-triggers` — /check is mandatory at close; the speed issue affects whether it can also be advisory mid-session
- `model-pool-selection-policy-speed-quota-diversity` — model tiering for verifiers

## Decisions made

- **The bottleneck is per-verifier efficiency, not the parallel architecture.** Parallel execution is correct; the issue is that the slowest verifier (contract/config, 802s) gates the wall clock.
- **Read-once discipline is the highest-leverage fix.** Repeated reads of large files (AGENTS.md, close/SKILL.md) inflate tool-call count and per-call latency. One instruction in the verifier prompt could cut 30-50% of the contract verifier's time.
- **`--quick` mode is necessary for mid-session use.** If the skill-recommendation hook recommends /check mid-session, 13 minutes is too long. A 2-minute `--quick` mode (Phase A only, 1 verifier) makes mid-session /check practical.

## Last user message (verbatim)

> /handoff for how to speed up "/check". Something about this particular situation is causing the skill and subagent to be really slow.

## Falsifier

This handoff is wrong if:
- The root cause is not re-reads but something else (e.g., model latency, network, quota throttling). Measure before optimizing.
- The speedup targets (<5min wall clock) are unreachable without architecture changes. If read-once + model tiering + packet enrichment don't get to <5min, the parallel-verifier model may need rethinking.
- The `--quick` mode produces too many false PASSes to be useful. If it passes work that standard /check would fail, it's not a useful mode.

If any pattern appears, iterate this handoff.
