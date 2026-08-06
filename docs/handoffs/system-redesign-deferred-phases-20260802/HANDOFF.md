---
thread_id: 019fc0a7-redesign-deferred
parent_handoff_path: none
current_session_id: 019fc0a7-b736-7eb3-8974-ede7d60cc647
parent_session: none
current_terminal_id: grok-019fc0a7
produced_at: 2026-08-02T05:30:00Z
last_updated_by: 019fc0a7-b736-7eb3-8974-ede7d60cc647
last_updated_at: 2026-08-02T05:30:00Z
status: closed
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Handoff: System Redesign — Deferred Phases

## Objective

Continue the system-redesign implementation by picking up Phases 2-5 when their triggering conditions are met. Each phase has an explicit deferral trigger and abandonment criterion.

## Status

CLOSED — Phase 2 completed and answered the scope question. Phases 3-5 closed as no-value: the tree-sitter graph solves neither a performance problem nor a correctness problem in this workspace. No trigger condition has fired across any session since the original handoff. See Revision 3 for the full rationale.

## Producing context

- Session: 019fc0a7 (2026-08-01 to 2026-08-02)
- Work completed: architecture review, audit, minimal-bias hook, command-surface map, dead-entry cleanup, /www + /research alias, Phase 1 (investigation persistence via handoff extension), tree-sitter evaluation, red-team review of proposal, Phase 1 implementation + /review + fixes
- Commits (~/.grok): `0e867ae` (hook), `f21e847` (dead entries), `012034d`+`d04c5be` (alias), `653db5b` (Phase 1), `faf5c8f` (review fixes)
- Commits (P:/): `4cd6e6b` (command map), `5f79d98` (codegraph eval), `a309fa5` (investigations dir removal)

## Read-first list (ordered)

1. `P:/docs/designs/command-surface-map.md` — the 7-command intent-level architecture
2. `P:/docs/plans/system-redesign-three-workstreams-2026-08-01.md` — the three-track plan with checkboxes
3. `P:/docs/audits/system-redesign-authority-and-behavior-audit-2026-08-01.md` — 50-session audit (evidence base)
4. `P:/docs/audits/codegraph-evaluation-2026-08-01.md` — tree-sitter PoC evaluation
5. `P:/tmp/tree_sitter_poc.py` — the working PoC (gitignored; may need rebuild from evaluation doc)
6. `P:/.artifacts/review/019fc0a7/20260802/FINDINGS.md` — review findings (5 bugs found and fixed)
7. `~/.grok/skills/why/SKILL.md` — updated with --persist → handoff routing + staleness check
8. `~/.grok/skills/handoff/references/core-fields.md` — updated with investigation_state: block
9. `~/.grok/hooks/scripts/minimal_bias_gate.py` — shipped hook

## Verified facts

- [FACT] The minimal-bias hook is shipped, tested (12/12), reviewed, and all review bugs fixed (commit `faf5c8f`)
- [FACT] Investigation persistence works via handoff extension with `investigation_state:` block — no separate artifact type (Phase 1 complete)
- [FACT] Tree-sitter PoC proved sub-ms queries on 7,806 files / 605,936 call sites (62s cold build)
- [FACT] Red-team review found 29 findings across 5 specialists; 11 BLOCKs identified; all Phase 1 BLOCKs addressed
- [FACT] The original /www→/research rename was reverted; /www is primary, /research is alias (operator decision)
- [FACT] The `cited_source_files` field was added to investigation_state schema for staleness-check input
- [FACT] The staleness check has a known multi-root blind spot (ARCH-10): git diff from P:/ cwd can't see ~/.grok changes. Use `accurate_as_of_head` SHA comparison instead of date-based diff when implementing the fix.

## Current state

**Shipped and verified:**
- Phase 0 (hook, cleanup, alias, evaluation) — complete
- Phase 1 (investigation persistence via handoff extension) — complete, reviewed, fixed

**Not started (deferred by design):**

### Phase 2: Tree-sitter scope definition (~1 day)
- **Trigger:** operator feels grep's limitations on cross-module structural queries ("who calls X across all packages")
- **What to do:** Write `P:/docs/designs/codegraph-scope.md` defining `ROOT_SCOPES` with explicit filter exclusions (venv, site-packages, node_modules, __pycache__, .tox, *.egg-info). Measure filtered file count. Benchmark cold build time.
- **Abandonment criterion:** If filtered file count >50,000 or cold build >5 min, fall back to per-package on-demand graphs.
- **Files:** New design doc. May need to rebuild PoC from `codegraph-evaluation-2026-08-01.md` if `P:/tmp/tree_sitter_poc.py` was cleaned.

### Phase 3: Tree-sitter production graph (~3 days)
- **Trigger:** Phase 2 complete (scope defined)
- **What to do:** Promote PoC to `P:/.agents/scripts/call_graph.py` with concurrency hardening (atomic writes, build lock, mmap sharing, cache metadata with schema_version/build_id/per_root_heads/per_file_mtime_map). Add SessionStart hook for staleness detection. Drop redundant forward index. Add string interning.
- **Red-team findings to address:** PERF-001 (venv filter), PERF-002 (memory 250-350 MB, need mmap), PERF-003 (multi-root fingerprint), STATE-3 (no file locking), STATE-5 (persist full graph not summary)
- **Abandonment criterion:** If memory >500 MB per load even with interning and single-index, switch to sqlite backend.
- **Files:** New script + new SessionStart hook

### Phase 4: Alias resolution + declared consumers (~2 days)
- **Trigger:** Phase 3 complete (production graph exists)
- **What to do:** Add alias resolution (import→binding mapping). Benchmark cross-package queries. Wire /go preflight and /refactor to read callers_of. Update command-surface-map.md with tree-sitter as shared infrastructure.
- **Abandonment criterion:** If alias resolution cannot resolve >80% of cross-module calls, document limitation and use grep for unresolved.
- **Files:** `call_graph.py` update + `/go` SKILL.md H3 step + `/refactor` SKILL.md + `command-surface-map.md`

### Phase 5: Archival + lifecycle (~1 day)
- **Trigger:** Phases 1 + 4 in production use for ≥1 month
- **What to do:** Add `/maintain investigations-compact` for archiving resolved investigation handoffs >90 days. Add quarterly graph rebuild verification. Add size budget on live investigation handoffs (cap 200, auto-archive oldest resolved).
- **Files:** New /maintain subcommand or script

### AGENTS.md routing table updates
- **Trigger:** operator explicitly requests it (bypasses "don't edit AGENTS.md in normal runs" rule)
- **What to do:** Update routing tables in `~/.grok/AGENTS.md` to reflect the /research alias for /www. Add /why as user-invocable internal mechanism in the command-surface-map. Document investigation_state: block in the handoff schema section.
- **Files:** `~/.grok/AGENTS.md` (operator-approved edit)

## Task packets

### TASK-1: Tree-sitter scope definition (Phase 2)
- **Goal:** Define what gets scanned before building the production graph
- **In scope:** ROOT_SCOPES dict, filter exclusions, file count measurement, build time benchmark
- **Out of scope:** Production graph code, alias resolution, consumer wiring
- **Files/anchors:** New `P:/docs/designs/codegraph-scope.md`
- **Acceptance:** Scope doc exists with measured file count and build time. Decision recorded: global graph vs per-package.
- **Falsifier:** If file count measurement shows >50K files even after filtering, the global-graph approach is wrong — switch to per-package.
- **Verification level required:** STATIC_INSPECTION (doc + measurement output)
- **No live run reason:** N/A

### TASK-2: AGENTS.md routing update
- **Goal:** Reflect /research alias and investigation_state: extension in AGENTS.md routing tables
- **In scope:** Web-search tool selection table, review skill routing table, command-surface references
- **Out of scope:** Skill content changes, hook changes
- **Files/anchors:** `~/.grok/AGENTS.md`
- **Acceptance:** `/www` and `/research` both documented. `investigation_state:` block mentioned in handoff schema section. `/why --persist` routing documented.
- **Falsifier:** If a session reads AGENTS.md and still confuses /www with /research, the routing table update failed.
- **Verification level required:** STATIC_INSPECTION
- **No live run reason:** N/A

## Open decisions

### Decision 1: When to start tree-sitter production work
- **Question:** Start Phases 2-4 now, or wait until grep limitations are felt?
- **Options:**
  - A: Start now — 6 days of effort for a confirmed problem ("I fight it with you often")
  - B: Wait — let the operator feel grep's limitations directly, then start with clear evidence
- **Selection criterion:** cost of delayed capability vs cost of premature build
- **Currently leads:** Option B (deferred per /tp recommendation). The operator confirmed the problem is real but the specific failure shape (which queries grep can't answer) hasn't been measured.
- **What would change the lead:** operator reports a specific instance where grep couldn't answer a cross-module structural query and it caused rework

## Hard constraints

1. The minimal-bias hook is shipped — do not remove or disable it without operator approval
2. /www is the primary skill; /research is an alias — do not rename again
3. Investigation persistence uses the handoff schema — do not create a separate P:/docs/investigations/ directory
4. The hook's escape hatch requires explicit "not" — do not make negation optional again (CORR-1)
5. cited_source_files is part of the investigation_state schema — the staleness check depends on it

## Cross-reference couplings

- `~/.grok/hooks/scripts/minimal_bias_gate.py` → registered in `~/.grok/hooks/minimal-bias-gate.json` → fires on Stop event
- `~/.grok/skills/why/SKILL.md` Step 14 → routes to `~/.grok/skills/handoff/SKILL.md` (depends_on includes handoff)
- `~/.grok/skills/handoff/references/core-fields.md` investigation_state block → consumed by /why Step 0.5 staleness check
- `P:/docs/designs/command-surface-map.md` → references all 7 intent-level commands; /www and /research listed
- `P:/docs/audits/codegraph-evaluation-2026-08-01.md` → references `P:/tmp/tree_sitter_poc.py` (gitignored, may not persist)

## Other outstanding streams

- **Minimal-bias hook problem-existence check:** the hook catches "is minimal optimal?" but not "is the problem real?" — consider adding a companion check (surfaced in /tp, not yet implemented)
- **Orphaned session_search.sqlite:** `~/.grok/sessions/session_search.sqlite` exists but no Python script references it — either rehydrate or delete (audit finding, not yet actioned)

## Explicit non-goals

- Do NOT restructure the command surface further (2/50 selection errors — problem is minor)
- Do NOT build new KB infrastructure (wiki with 810 concepts already exists)
- Do NOT build a unified retrieval router (/search-fleet already exists)
- Do NOT create a separate investigation artifact type (extend handoffs instead)
- Do NOT rename /www again (it's primary; /research is the alias)

## Resumption protocol

1. Check whether the operator has felt grep's limitations on cross-module structural queries since this session
2. If yes → start Phase 2 (tree-sitter scope definition)
3. If no → check whether the hook has fired (grep `~/.grok/state/hook_failures.jsonl` for `minimal_bias_gate` entries)
4. Check whether any /why --persist handoffs have been written (grep for `investigation_state:` in `P:/docs/handoffs/`)
5. If the operator asks to update AGENTS.md routing tables → do TASK-2

## Suggested next invocation

```
/todo
```

Or if the operator wants to start tree-sitter:
```
/go Phase 2: tree-sitter scope definition
```

Or if the operator wants to update routing tables:
```
/go update AGENTS.md routing tables to reflect /research alias and investigation_state extension
```

## Last user message (verbatim)

> "/handoff for What was NOT done (deferred by design):
> • Phases 2-4 (tree-sitter production graph, alias resolution, consumer wiring) — deferred until grep limitations are felt directly
> • Phase 5 (archival and lifecycle) — deferred until 1 month of usage data
> • AGENTS.md routing table updates — deferred per the "don't edit AGENTS.md in normal runs" rule"

## Epistemic labels per claim

- [FACT] All shipped work is committed and verified (commits cited above)
- [FACT] The tree-sitter PoC evaluation proved sub-ms queries at PoC scale (codegraph-evaluation-2026-08-01.md)
- [INFERENCE] The deferred phases are correctly prioritized — the /tp analysis showed the problem is real but the specific failure shape hasn't been measured for tree-sitter
- [UNKNOWN] Whether grep limitations have been felt in sessions since this one (check on resume)
- [UNKNOWN] Whether the minimal-bias hook has fired in production (check hook_failures.jsonl on resume)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:30 | 019fc0a7 | created |
| 2026-08-03T01:00 | 019fc0a7 | revision — post-/review + wiki + /check updates |

---

## Revision 1 — 2026-08-03T01:00Z (session 019fc0a7)

**Trigger:** post-/review PASS + wiki concept capture + /check PASS. Updating handoff to reflect final session state.

**What changed since the original:**

1. **Minimal-bias hook reviewed and fixed.** /review found 5 bugs (escape hatch inverted, consolidat typo, false positives on review output, blocked-pending-evidence, bare step). All fixed in commit `faf5c8f`. 12/12 tests pass. Problem-existence check added to framing question (commit `92762b2`).

2. **Two wiki concepts written** (commit `f9231ab`, validation fixes `b492431`):
   - `minimal-change-bias-detection-via-stop-hook` — the Stop-hook pattern for enforcing behavioral rules
   - `extend-existing-artifact-types-not-parallel` — extend handoff schema instead of creating parallel artifact types

3. **/review and /check both PASS.** FINDINGS.md at `P:/.artifacts/review/019fc0a7/20260802/FINDINGS.md`. All verified bugs fixed.

4. **Session is complete.** All work streams are either shipped+committed or deferred-by-design (captured in this handoff). Ready for `/close`.

**Status update:** unchanged — all phases still deferred by design. The session's shipped work is verified and reviewed.

**New open items:** none. The hook's multi-root staleness blind spot (ARCH-10) was already documented in the handoff's Verified Facts section.

---

## Revision 2 — 2026-08-03T19:00Z (session 019fc927)

**Trigger:** Phase 2 completed in a follow-up session. Scope defined, measured, decision recorded.

**What changed since Revision 1:**

1. **Phase 2 (tree-sitter scope definition) is COMPLETE.** Measured full-workspace scope: 6,402 .py files after filtering (11 ROOT_SCOPES, 12 exclusion patterns). Cold build: 58.73s, 0 parse errors, 63K defs / 400K call sites. Both abandonment criteria pass with 80%+ headroom. Decision: global single graph.

2. **Key finding:** `plugins/` is 66% vendored dependencies. The PoC counted 7,806 .py files there; with proper exclusions only 2,687 are operator source. The real codebase is 3× smaller than the PoC suggested.

3. **Deliverables committed:** `4025d04` — `P:/docs/designs/codegraph-scope.md` (design doc), `P:/tmp/codegraph_scope_measure.py` (measurement script), `P:/tmp/codegraph_scope_results.json` (raw results).

4. **Phase 3 trigger is now met** (Phase 2 complete) but remains deferred by operator decision — grep limitations have not been felt in any session since the handoff was written.

**Status update:** Phase 2 = COMPLETE. Phases 3-5 remain deferred by design. TASK-2 (AGENTS.md routing update) completed in same session.

**Updated open items:** none new. Phase 3 can proceed whenever the operator wants it; the scope and numbers are defined.

---

## Revision 3 — 2026-08-03T19:30Z (session 019fc927) — CLOSING

**Trigger:** Post-Phase-2 assessment of whether Phases 3-5 provide real value. Conclusion: they do not, and this handoff is closed.

**Decision: Phases 3-5 closed as no-value.** After completing Phase 2 (scope definition) and evaluating the business case for the production graph, the operator and agent jointly determined there is no real value to justify building it:

1. **No performance problem solved.** `/preflight`'s actual bottleneck is file discovery and evidence assembly, not the grep queries. Tree-sitter would improve interactive query latency from ~50ms to <1ms — for a query pattern (cross-module "who calls X") that hasn't been issued in any session.

2. **No correctness problem solved.** The PoC's "grep returns 0 hits" result was a *scope* problem (PoC only scanned `plugins/`, function lived in `research_runtime/`), not a structural grep limitation. Full-workspace grep finds it fine. The substring-matching disambiguation problem (call vs def vs comment vs import) is theoretical in this workspace — Python function names are specific enough that substring matches are accurate, and no session has reported false positives/negatives from grep on a structural query.

3. **No trigger condition fired.** A transcript scan of all post-handoff sessions (40 grep tool calls across 3 main sessions) found zero cross-module structural queries. Every grep was a text search scoped to a single directory or file. The trigger — "operator feels grep's limitations on cross-module structural queries" — has not been felt.

4. **No consumer waiting.** `/preflight`, `/refactor`, and `/go` discovery all work correctly with their current grep-based approaches. `/refactor`'s `code_analysis.py` already does AST-based import graph analysis per package using stdlib `ast`. No skill has reported a correctness failure traceable to grep limitations.

5. **Phase 2 was the right stopping point.** It answered "could we?" (yes) and "how big?" (6,402 files, 59s build — manageable). But the answer to "should we?" is no, given the above. The scope doc remains on disk (`P:/docs/designs/codegraph-scope.md`) if the situation ever changes.

**What to do if circumstances Change.** If a future session hits a grep wall on a real cross-module structural query that causes rework, the scope doc from Phase 2 has the numbers to build the graph in ~3 days. Reopen this handoff or create a fresh one at that point.

**Final disposition of all phases:**
- Phase 0 (hook, cleanup, alias, evaluation) — COMPLETE (session 019fc0a7)
- Phase 1 (investigation persistence via handoff extension) — COMPLETE (session 019fc0a7)
- Phase 2 (tree-sitter scope definition) — COMPLETE (session 019fc927, commit `4025d04`)
- Phase 3 (tree-sitter production graph) — CLOSED, no-value
- Phase 4 (alias resolution + consumer wiring) — CLOSED, no-value
- Phase 5 (archival + lifecycle) — CLOSED, no-value
- TASK-2 (AGENTS.md routing update) — COMPLETE (session 019fc927, commit `517c185`)
