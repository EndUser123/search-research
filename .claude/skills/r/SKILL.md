---
name: r
description: Deterministic remember/refine pass with GoT+ToT enhancement - decomposed DUF checks, mode decision, context writing, memory refinement analysis, and branching reflection paths. Finds what was forgotten, validates plans, proposes predictable low-risk improvements, decides mode, and writes context for downstream skills; escalates to /s when needed.
version: 1.0.0
status: stable
category: quality
triggers:
  - /r
  - "what did we forget"
  - "remember pass"
  - "deterministic improvements"
aliases:
  - /r
suggest:
  - /q
  - /s
  - /p

---

# /r - Remember + Refine

## Purpose

Run a deterministic second-thought pass after `/q`:
- surface omissions (`forgotten_items`)
- run deterministic pre-mortem checks (inversion, rollback readiness, state-integrity basics)
- validate implementation-vs-plan when plan intent is present in the prompt/context
- produce predictable low-risk improvements (`deterministic_improvements`)
- auto-generate a structured file-by-file analysis task plan via `aid_deep_file_analysis`
- use `aid_suggest_refactoring` + `aid_best_practices` as deterministic improvement sources
- decide if escalation to `/s` is warranted

## Decomposition Ownership

`/r` owns deterministic parts of 10+ removed skills (opt, oops, opts, value, val, verify, analysis-audit, analysis-profile, analysis-logs) and integrated checks from `/slc`, `/read-before-write`, `/library-first`, and `/investigate`.

See `references/decomposition-ownership.md` for the full source-to-check mapping.

`/r` does NOT own: exploratory multi-option strategy (`/s`), promotion gates (`/p*`).

## GoT + ToT Enhancement (v2.2)

`/r` integrates Graph-of-Thought (finding relationships, cycle detection) and Tree-of-Thought (branching reflection scenarios) reasoning. Both enabled by default.

**Quick reference:**
- GoT: extracts finding nodes, detects supports/contradicts/depends relationships, warns on circular dependencies
- ToT: branches memory/refinement/escalation decisions into sure/maybe/unlikely paths with confidence scores
- Opt-out: `R_NO_GOT=true` / `R_NO_TOT=true`

See `references/got-tot-integration.md` for node types, relationship types, branch types, and example outputs.

## Workflow

1. Read `/q` context if available.
2. Build omission checklist from context/session activity.
3. Classify change scope (`trivial|moderate|significant|major`) from session evidence.
4. Run deterministic DUF-derived checks appropriate for that scope.
5. **[From /slc]** Solo-dev compliance: complexity justified? complete solutions? evidence verified? local/portable?
6. **[From /read-before-write]** SRPI: Searched? Read working code? Planned minimal? Using Edit/Write?
7. **[From /library-first]** Existing-solution: registry checked? stdlib available? codebase pattern reuse? justification for new?
8. **[From /investigate]** Evidence: absence claims verified? git history checked? docs vs implementation compared?
9. Run `aid_deep_file_analysis` automatically; fold high-signal items into `forgotten_items` and `must_fix_now/can_do_soon`.
10. If plan intent present, run deterministic plan validation pass.
11. If command/skill metadata files in scope, run deterministic standards audit.
12. If verification/certification in scope, run tier-completeness audit (Tier 1 syntax, Tier 2 type/lint, Tier 3 tests).
13. Run value completeness gate: list excluded items, assign `HIGH|MEDIUM|LOW`, enforce disclosure rule.
14. Run deterministic improvement passes (`aid_suggest_refactoring`, `aid_best_practices`) on resolved scope.
15. If audit/profile/log signals present, produce deterministic follow-ups.
15.5 **[Context-Aware Filtering]** Filter findings against `.claude/config/solo-dev-context.yaml`. See `references/context-filtering.md`.
16. Generate deterministic improvements with clear rationale.
17. Emit `escalate_to_s: yes/no + reason`.
18. Recommend next commands.

## Execution Directive

```bash
python P:/.claude/skills/r/scripts/run_deterministic.py \
  --topic "{{USER_PROMPT}}" \
  --output "{{json|markdown|text}}" \
  {{--strict-stale if requested}}
```

Run on every `/r` invocation:

```bash
aid_deep_file_analysis(target_path=<resolved_scope_path>)
aid_suggest_refactoring(target_path=<resolved_scope_path>, refactoring_goal="improve readability")
aid_best_practices(target_path=<resolved_scope_path>)
```

**Conflict/failure handling:** If any AID call is unavailable or times out, continue `/r` and emit an explicit degraded-analysis item.

**Integration rules:**
- Run once per `/r` invocation (no per-file repetition).
- Do not duplicate items already present from deterministic checks.
- Promote only actionable findings with concrete file references.

## CKS Pattern Ingestion

`/r` stores discovered patterns and learnings to CKS for cross-session knowledge accumulation.

See `references/cks-pattern-ingestion.md` for:
- Query CKS before analysis (loading historical patterns)
- Store patterns to CKS after analysis (PATTERN, REFACTOR, DEBT, DOC, OPT types)
- Metadata schema per finding type
- Error handling (graceful degradation, always proceed with analysis)
- Best practices (query before analyze, store high-value only, idempotent storage)

## Output Contract

Required sections:
- `forgotten_items`
- `classification`, `checks_run`
- `deterministic_improvements`
- `plan_validation` (when plan intent exists)
- `must_fix_now`
- `can_do_soon`
- `value_exclusions` (item, value_level, reason, disclosed)
- `escalate_to_s`
- `next_commands`
- `topic_source`, `topic_confidence`

## Escalation Rules

Set `escalate_to_s: yes` when:
- architecture/migration/rewrite scope is implied
- multiple high-risk signals are present
- deterministic pass has low confidence or conflicting tradeoffs

## Usage

```bash
/r
/r "what did we forget in this auth migration?"
/r --strict-stale
```

## Reference Files

| File | Contents |
|------|----------|
| `references/got-tot-integration.md` | GoT node/relationship types, ToT branch types, combined flow, opt-out flags |
| `references/context-filtering.md` | Step 15.5 filter implementation, metrics logging, backward compatibility |
| `references/cks-pattern-ingestion.md` | CKS query/store patterns, metadata schema, error handling, best practices |
| `references/decomposition-ownership.md` | Full source-skill-to-check mapping for all consolidated skills |
