---
thread_id: a4f2c8e1-7d30-4b9a-9e1c-3b8a5f2d6c04
parent_handoff_path: none
current_session_id: 019fb0c3-2ca7-7f22-9a2e-203130cb6e99
current_terminal_id: unknown
produced_at: 2026-07-29T21:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 665bcbf8d5337a6f5152426860fddae723e2b537
---

# Handoff: Fix mistral-medium-latest propagation across wiki pool files

## 1. Objective

Complete the propagation of the `mistral-medium-latest` spawn_subagent breakage (HTTP 422) across all wiki model-pool files, so no skill or dispatch logic recommends Mistral as a spawn_subagent target.

**Scope bounds:** 5 wiki concept files still reference Mistral as a valid spawn target. The `mechanical-model-pool.md` and `tool-fallbacks.md` are already fixed (done this session). Total affected files: 7; fixed: 2; remaining: 5.

## 2. Status

OPEN — documentation fix partially complete. 2 of 7 files corrected. 5 remain.

## 3. Producing context

- Date: 2026-07-29
- Session: `019fb0c3-2ca7-7f22-9a2e-203130cb6e99`
- Host: Grok Build
- Trigger: `/www` research run dispatched 4 `mistral-medium-latest` subagents for Chrome ACP research; all 4 failed identically with HTTP 422 (context injection ~26K tokens exceeds Mistral input limit). This was a known issue since 2026-07-21 but the mechanical-model-pool.md still recommended Mistral as Tier-1, causing the wasted dispatch.

## 4. Read-first list (ordered)

1. `~/.grok/tool-fallbacks.md` — the canonical known-broken manifest (already has Mistral 422 entry from 2026-07-21)
2. `P:/.data/wiki/capabilities/mechanical-model-pool.md` — ALREADY FIXED this session; pattern to follow for the remaining 5 files
3. `P:/.data/wiki/concepts/coding-model-pool-tier-1-tier-2.md` — STILL references Mistral as Tier-1 code pool, #2 fallback
4. `P:/.data/wiki/concepts/model-fleet-provider-pools.md` — STILL lists Mistral in code pool, mechanical pool, AND critic pool (3 refs)
5. `P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md` — STILL recommends Mistral for code generation
6. `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` — notes 422 but doesn't flag as broken for pools
7. `P:/.data/wiki/concepts/fleet-benchmark-results-2026-07-29.md` — benchmark data (FACTUAL, do not alter; just annotate if needed)

## 5. Verified facts

- [FACT] `mistral-medium-latest` fails via `spawn_subagent` with HTTP 422 on every attempt on this host (source: tool-fallbacks.md row dated 2026-07-21; re-confirmed 2026-07-29 with 4/4 failures, all 4 subagent_ids: `019fb172-8f8d-*`, `019fb172-8f8f-*`, `019fb172-8f90-*`, `019fb172-8f91-*`)
- [FACT] Root cause: AGENTS.md context injection (~26,481 input tokens per subagent prompt) exceeds Mistral's input limit (source: subagent error output showing `inputTokens: 26481` + 422 status)
- [FACT] `mistral-medium-latest` works via direct API (source: tool-fallbacks.md, fleet-benchmark-results showing 3.0s latency, 5/5 HumanEval)
- [FACT] `mechanical-model-pool.md` was fixed this session: Mistral moved from Tier-1 to "Broken via spawn_subagent" section with root cause and receipts
- [FACT] 5 wiki concept files still reference Mistral as a valid spawn_subagent pool member (source: `grep -r "mistral-medium-latest" P:/.data/wiki/concepts/` run 2026-07-29)
- [FACT] Mistral's direct-API capabilities are real and good: 5/5 code-exec, 12/13 reasoning, 6.9s latency (source: fleet-benchmark-results-2026-07-29.md, coding-model-pool-tier-1-tier-2.md)

## 6. Current state

**Done (this session):**
- `mechanical-model-pool.md` — Mistral removed from Tier-1, moved to "Broken via spawn_subagent" section, `nim-openai-gpt-oss-20b` promoted to speed recommendation
- `tool-fallbacks.md` — already had the entry from 2026-07-21; corroborated by pool file fix

**Not done (the 5 remaining files):**
- `coding-model-pool-tier-1-tier-2.md` — line 7 (Tier-1 summary), line 56 (benchmark table), line 61 (fallback recommendation #2)
- `model-fleet-provider-pools.md` — lines 425 (code pool), 433 (mechanical pool), 437 (critic pool)
- `model-role-assignment-public-vs-custom-benchmarks.md` — line 111 (code generation recommendation)
- `model-tool-calling-capability-matrix.md` — line 117 (notes 422 but doesn't flag for pool exclusion)
- `fleet-benchmark-results-2026-07-29.md` — benchmark data is FACTUAL; no change needed, but could add a note

## 7. Task packets

### MISTRAL-PROP-01: Annotate remaining pool files

- **goal:** Add a "broken via spawn_subagent" annotation to every wiki concept file that recommends `mistral-medium-latest` as a spawn/dispatch target, so no skill dispatches to it.
- **in scope:** the 5 files listed in section 6
- **out of scope:** `mechanical-model-pool.md` (already fixed), `tool-fallbacks.md` (already has entry), `fleet-benchmark-results-2026-07-29.md` (benchmark data is factual — no change to numbers; optional annotation only)
- **files / anchors:**
  - `P:/.data/wiki/concepts/coding-model-pool-tier-1-tier-2.md` lines 7, 56, 61
  - `P:/.data/wiki/concepts/model-fleet-provider-pools.md` lines 425, 433, 437
  - `P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md` line 111
  - `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` line 117
- **acceptance:** `grep -r "mistral-medium-latest" P:/.data/wiki/concepts/` returns results ONLY in: (a) benchmark data files (unchanged numbers), (b) entries explicitly marked as "broken via spawn_subagent" or "direct API only." No file recommends Mistral as a spawn_subagent target without the broken annotation.
- **falsifier:** any remaining file that lists Mistral in a pool/composition without the broken annotation → propagation incomplete.
- **verification level required:** STATIC_INSPECTION (grep after edits)
- **estimate:** 5 files × ~2 min each = ~10 min

### MISTRAL-CONFIG-02: Investigate config-level fix (optional)

- **goal:** Determine whether Grok Build has a config option to reduce or disable AGENTS.md injection for subagent dispatch, which would make Mistral usable via spawn_subagent.
- **in scope:** `~/.grok/docs/user-guide/16-subagents.md`, `~/.grok/config.toml`, any subagent context-injection settings
- **out of scope:** reducing AGENTS.md content itself (not desirable — the rules are load-bearing)
- **acceptance:** either (a) find a config option and document it, or (b) confirm none exists and close this packet as WONTFIX
- **falsifier:** if a config option exists and is undocumented, Mistral should pass a trivial spawn_subagent probe after applying it
- **verification level required:** LIVE_BEHAVIOR (spawn probe)
- **no_live_run_reason:** deferred — the documentation propagation (MISTRAL-PROP-01) is sufficient to prevent wasted dispatches; the config investigation is a nice-to-have, not a blocker

## 8. Open decisions

**Q: Should Mistral be removed from pool files entirely, or annotated as "direct API only"?**

- Option A: Remove from all pool compositions. Simple, no ambiguity. Loses a good direct-API model from the fleet documentation.
- Option B: Annotate as "direct API only, broken via spawn_subagent." Preserves the model's capabilities for deliberate use while preventing auto-dispatch.
- **Leads: Option B** — Mistral's direct-API capabilities are real (5/5 code-exec, 12/13 reasoning). The problem is the spawn path, not the model. Annotation preserves value while preventing the failure.
- Evidence that would change this: if Mistral's direct API also becomes unreliable, switch to Option A.

## 9. Hard constraints

- Do NOT alter benchmark numbers in `fleet-benchmark-results-2026-07-29.md` — those are factual measurements
- Do NOT reduce AGENTS.md content to fit Mistral's input limit — the rules are load-bearing for the fleet
- Follow the edit-then-verify protocol: read each file after editing to confirm the change persisted

## 10. Cross-reference couplings

- `mechanical-model-pool.md` (fixed) → `tool-fallbacks.md` (already had entry) — both must agree on Mistral status; they now do
- `coding-model-pool-tier-1-tier-2.md` → consumed by skills that select coding models for spawn — if this file still recommends Mistral, skills will dispatch to it and waste spawns
- `model-fleet-provider-pools.md` lines 425/433/437 → consumed by `model-pool-selection-policy-speed-quota-diversity.md` and any skill that reads pool compositions
- All pool files → `tool-fallbacks.md` is the canonical manifest; pool files must not contradict it

## 11. Other outstanding streams

- **Chrome ACP + Grok Build research** — completed this session; wiki concept at `chrome-acp-grok-build-browser-driven-agentic-clis.md`. The operator may want to proceed with implementation (Tier 0: ACP UI Desktop + `grok agent stdio`). Open.
- **Perplexity as MCP tool inside an ACP agent** — noted in the wiki concept as a gap (no ACP agent exists for Perplexity; `perplexity-web-mcp` already installed on this host). Not started.

## 12. Explicit non-goals

- Do NOT attempt to fix Mistral's provider-side input limit (not in our control)
- Do NOT write a wrapper that strips AGENTS.md for Mistral spawns specifically (fragile, brittle, violates single-writer)
- Do NOT remove Mistral from benchmark result files (factual data)
- Do NOT change `mechanical-model-pool.md` again (already fixed)

## 13. Resumption protocol

1. `grep -r "mistral-medium-latest" P:/.data/wiki/concepts/` — confirm the 5 files still have un-annotated references
2. For each file in section 6, read it, add the "broken via spawn_subagent — see tool-fallbacks.md" annotation next to the pool membership line, verify the edit
3. Re-run the grep — confirm every hit is either benchmark data or annotated as broken
4. Optional: investigate MISTRAL-CONFIG-02 (config-level fix)

## 14. Suggested next invocation

> "Complete the mistral-medium-latest propagation: annotate the 5 remaining wiki pool files that still recommend it for spawn_subagent. Use the pattern from mechanical-model-pool.md (move to 'broken via spawn_subagent' section, keep as 'direct API only'). Don't alter benchmark numbers. Verify with grep after editing."

## 15. Last user message (verbatim)

> "/handoff for fixing mistral"

## 16. Epistemic labels

- [FACT] All claims about the 422 failure, token counts, and file locations are verified via tool output this session
- [FACT] The 5 remaining files were identified via `grep -r` this session
- [INFERENCE] The config-level fix (MISTRAL-CONFIG-02) may not exist — Grok Build likely injects AGENTS.md unconditionally for all subagents. Would need to read `16-subagents.md` to confirm
- [UNKNOWN] Whether any skills (beyond `/www`) actually read the pool files at runtime to select models — if they don't, the propagation is documentation hygiene, not functional
