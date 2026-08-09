# Review-Relay Improvements Design — Summary

**Design doc:** `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-doc-b1abe493.md` (585 lines, 77KB)
**Verdict:** Reviewer PROCEED (0 critical/major/minor/nit) · Critical friend round 2 PROCEED (1 implementer caveat R2-N1, 6 trackable concerns)
**Rounds:** 2 (write → review → revise → re-review → critical friend REVISE → revise → re-review → critical friend PROCEED)

## Headline recommendation

Three architectural improvements to review-relay, all preserving the dumb-pipe invariant (relay stays byte-identical, 0 LoC in `src/review-relay.mjs`):

1. **Finding lifecycle tracking** — sidecar `findings.jsonl` with state machine (open/rebutted/upheld/resolved/superseded), partners read/write via existing scratchpad
2. **Continuous convergence score** — skill-side weighted score (0.5 overlap + 0.3 coverage + 0.2 depth), advisory only, written to `convergence_history.jsonl`
3. **Per-section parallel review** — skill-side `splitProposal` + N independent relay sessions + `mergeReviews`, with coupling detection (≥30% threshold → fallback to whole-doc)

## Key decisions (13)

| DEC | Decision | Rationale |
|---|---|---|
| DEC-1 | findings.jsonl in bucket, partners read+write via scratchpad | Sidecar preserves dumb pipe |
| DEC-2 | State machine validated in skill, not relay | Relay stays findings-agnostic |
| DEC-3 | Score in `__lib/convergence.mjs`, sidecar file | Dumb pipe invariant |
| DEC-4 | Weights 0.5/0.3/0.2 (overlap/coverage/depth) | Overlap is strongest convergence signal |
| DEC-5 | Section split via skill, N independent relays | Preserves dumb pipe |
| DEC-6 | Zero relay code changes | Invariant preservation |
| DEC-7 | Coordinator may override score | Score is advisory |
| DEC-8 | Default N=4 sections, max 6 | Median for workspace design docs |
| DEC-9 | Weights exposed as DEFAULT_WEIGHTS + env override | Tunability |
| DEC-10 | splitProposal accepts opts.session_id | Parallel-session collision avoidance |
| DEC-11 | Missing previous_findings_path = soft-failure | Partners must not crash on absence |
| DEC-12 | Ship dumb-pipe first; promote to smart-pipe only after 30-day production bottleneck | Graceful migration path |
| DEC-13 | Score MUST NOT be sole coordinator signal | Unvalidated weights shouldn't drive decisions alone |

## Open questions (7)

1. **[RESOLVED via source grep]** `write_policy.forbidden_writes` — partners CAN write findings.jsonl (`allowed_writes` includes `turns/**` at review-relay.mjs:964). Variant A is workable.
2. **[NEEDS_USER_DECISION — U-10]** Convergence score in result.json or sidecar only? Default: sidecar only.
3. **[INFERENCE]** Pattern citations (ReviewingAgents/POIROT/GPT Researcher) are research-only; helpers use generic names.
4. **[INFERENCE]** Section headings assumed stable across iterations.
5. **[OPEN]** Phase 1.5 weight tuning — what if <3 historical sessions exist?
6. **[OPEN]** Dashboard null-handling for missing sidecars.
7. **[OPEN — R2-N1]** `previous_findings_path` as tick input field implies 1-2 relay lines OR a coordinator-side sidecar resolution. Critical friend flagged: tick inputs are built with explicit named fields from relay state, no controller-injection mechanism. Three resolutions: (a) coordinator-side sidecar = true 0 relay lines, (b) acknowledge 1-2 relay lines, (c) generic pass-through mechanism. **Must pick before implementation.**

## Implementation plan (15 units, 4 phases)

| Unit | Description | Disposition |
|---|---|---|
| U-1 | findings.mjs lifecycle FSM + tests | COMMIT_THIS_SESSION |
| U-2 | convergence.mjs score + tests | COMMIT_THIS_SESSION |
| U-3 | split.mjs + merge.mjs + tests | COMMIT_THIS_SESSION |
| U-4 | SKILL.md documentation | COMMIT_THIS_SESSION |
| U-5 | Partner prompt update + test | COMMIT_THIS_SESSION |
| U-6 | Relay source changes | N/A (zero, by design) |
| U-7 | Existing tests pass unchanged | COMMIT_THIS_SESSION |
| U-8 | Wiki concept revision | HANDOFF |
| U-9 | End-to-end 4-section test run | DEFERRED |
| U-10 | Score location decision | NEEDS_USER_DECISION |
| U-11 | dashboard.mjs (consolidates 4 files → 1) | COMMIT_THIS_SESSION |
| U-12 | Partner adoption instrumentation | COMMIT_THIS_SESSION |
| U-13 | split.analyzeCoupling (≥30% threshold) | COMMIT_THIS_SESSION |
| U-14 | schema.mjs versioning | COMMIT_THIS_SESSION |
| U-15 | Per-helper rollback language | COMMIT_THIS_SESSION |

**Phases:**
- Phase 1: Ship dormant helpers (U-1, U-2, U-11, U-14)
- Phase 1.5: Validate weights on ≥3 historical sessions (gate before Phase 2)
- Phase 2: Partner adoption (U-4, U-5, U-12) — default-on
- Phase 3: Section split (U-3, U-13)
- Phase 4: Measure metrics, decide promote-to-smart-pipe

**Estimated LoC:** ~1830 new (6 helpers + 8 test files + SKILL.md updates); 0 in src/review-relay.mjs

## File references

- Design doc: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-doc-b1abe493.md`
- Review file: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-review-b1abe493.md`
- Critique round 1: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-critique-b1abe493.md`
- Critique round 2: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-critique-b1abe493-round2.md`
- Premise verification: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/premise-verification-brief.md`
- Evidence brief: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/evidence-brief.md`
- Domain knowledge: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/domain-knowledge-brief.md`
- Preflight inventory: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/preflight-inventory.json`

Note: scratch dir is in OS temp (`C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/`). Files will be reaped by Windows Storage Sense. Copy to durable location if you want to keep them.