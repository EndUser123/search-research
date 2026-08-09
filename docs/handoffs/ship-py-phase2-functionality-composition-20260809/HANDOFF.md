# Handoff — ship-py Phase 2: functionality composition improvements

## Status
PHASE 1 + PHASE 2 SHIPPED + PUSHED. Open items are documentation, testing,
and coordination with a sibling session working on cross-model validation.

## ⚠️ Coordination flag

**Another session is working on ship-py's review phase.** See:
`P:/docs/handoffs/cross-model-validation-middleware-20260808/HANDOFF.md`

That work proposes replacing the LLM-controlled review with orchestrator-
spawned cross-model validation (direct HTTP/Pi subprocess). If that lands,
it supersedes our P2-1 (cross-model diversity PAUSE_INSTRUCTIONS edit) —
the orchestrator would handle model dispatch directly.

**Before any further ship-py review-phase work:**
1. Check if the cross-model-validation-middleware handoff is resolved
2. If resolved: align with its architecture
3. If still open: coordinate to avoid conflicting edits to run_all.py and
   the review phase

## What shipped this session (session 019fe403)

### Phase 1 — defect fixes + new phases (all pushed)
- `abort` subcommand + aborted phase gate
- `secret-scan` phase (gitleaks, session-scoped)
- `fmea-scan` phase (component-level I/O failure mode analysis, category-gated)
- Verdict staleness check (session-scoped, not absolute HEAD)
- Hook state sync (save_state writes both state.json AND ship-phase-py.json atomically)
- all_merged logic fix
- Merge-unreachable bug fix (verdict phase="complete" → "merge-ready")
- Secret-scan fail-open masking fix (consult exit code, not just parsed findings)
- 8 Phase 1 feature tests (55 total passing)

### Phase 2 — functionality composition (all pushed)
- P2-5: Design conformance check (conditional phase, design-check + design-check-record)
- P2-4: PR babysit post-publish (optional phase, babysit + babysit-record)
- P2-3: /why grounding in fix phase (PAUSE_INSTRUCTIONS edit, RAG-APR evidence-backed)
- P2-2: Version bump in publish (--version-bump flag, SKILL.md semver + changelog)
- P2-1: Cross-model review diversity (PAUSE_INSTRUCTIONS edit, ⚠️ may be superseded by cross-model-validation-middleware handoff)

### Design-choice audit pattern (cross-skill, all pushed)
- Wiki concept: design-choice-audit-challenge-every-decision-against-first-principles.md
- Wired into 6 skills: /tp, /go, /design, /refactor, /risk, /plan-writer
- RCA: /tp didn't ask design-discipline questions the operator had to supply

### Research wiki concepts (all pushed)
- RAG-APR evidence (4 peer-reviewed papers validating /why-in-fix)
- Resolution throughput > verification discovery (agy's pipeline-imbalance reframing)

### Pipeline: 18 phases
```
detect → refactor-scan → fmea-scan → skill-dev → auto-fix → secret-scan →
refactor → check → design-check → review → risk → fix → verify → doc-check →
verdict → merge → publish → babysit
```

## Open items (not blocking — documentation and testing)

1. **Tests for Phase 2 features** — design_check, babysit, publish version-bump,
   /why-in-fix PAUSE_INSTRUCTIONS, cross-model review PAUSE_INSTRUCTIONS
2. **Enrich changelog generation** — include commit messages (currently only
   version bumps and file counts)
3. **design-check doc-matching** — improved heuristic landed but may still
   produce false positives on common skill names
4. **Document design-choice audit as AGENTS.md rule** — currently only in
   wiki concept + 6 skills, not in the governing rules file

## Commits (both repos pushed)

### ~/.grok repo
- `0ae38d3` abort subcommand + aborted phase gate
- `b0ad5af` secret-scan phase (gitleaks)
- `a4e6fb5` verdict staleness + hook I/O hardening
- `fe8fc40` ruff format (auto-fix phase)
- `14e3802` SKILL.md 14-phase + CRAFT fix + 8 Phase 1 tests
- `f4b2ab3` ruff F401/F841 in test file
- `dbc0f0c` merge-unreachable + secret_scan fail-open masking fixes
- `a7bd2aa` session-scoped staleness + atomic hook sync + all_merged
- `6f9f18f` FMEA phase (cmd_fmea_scan)
- `33993fe` design-choice audit /tp + /go
- `c1f39f9` design-choice audit /design + /refactor + /risk
- `f7715b9` design-choice audit /plan-writer
- `b88de35` Phase 2 — 5 functionality enhancements (18-phase pipeline)
- `1481915` fix: 5 /risk findings from Phase 2 scan
- `d5b4d7a` SKILL.md 18-phase update v2.5.0
- `90c2176` design-check heuristic improvement
- `8c9da05` design-choice audit /refactor (final)

### P:/ repo
- `462f108` Phase 2 handoff (initial)
- `711f96d` Phase 2 handoff update with /www verdicts
- `b904df9` wiki: design-choice audit concept
- `e5e7987` wiki: RAG-APR + resolution-throughput concepts
- `f59dcb8` wiki: design-choice audit update
