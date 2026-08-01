# Claude Skill Decomposition → close-check Components

## Goal
Extract reusable verification components from unported Claude skills and wire them into `/close-check` as checks. Document the decomposition in the wiki skill graph.

## Session
019fb933-040b-7720-a257-e364f5df726f (2026-07-31 → 2026-08-01)

## Status
OPEN — decomposition analysis complete, implementation deferred to next session.

## Decomposition table

| Claude skill | Reusable component | close-check check name | Agent | Domain | Effort |
|---|---|---|---|---|---|
| `epistemic-check` | Claim-receipt validation: scan session output for [FACT] claims, verify each has a tool-call receipt | `claim-receipt-validation` | C (judgment) | lifecycle | ~15 lines |
| `rns` | Next-step red-team: adversarial pass on the "Next steps" recommendations | `next-step-red-team` | C (judgment) | review | ~10 lines |
| `snapshot` | Pre-close git snapshot: capture HEAD + dirty file list before close for recovery | `pre-close-snapshot` | A (mechanical) | lifecycle | ~10 lines |
| `commventional` | Commit message format validation | `commit-format-check` | A (mechanical) | verify | ~8 lines |

### Already covered (do NOT port)

| Claude skill | Covered by | Why redundant |
|---|---|---|
| `claude-audit` | `/config-audit` | Same function — config auditing |
| `skill-audit` | `/config-audit` + `/skill-prune` | Skill rubric + hygiene already exist |
| `skill-similarity` | `/skill-prune` | Duplicate detection exists |
| `doc-compiler` | — | Output generator, not a verification check |
| `inkwell/tidy` | `/doc-check` | Doc drift detection exists |
| `debrief` | `/aar` (absorbed this session) | Deleted, absorbed |
| `retro` | `/aar` | Deprecated by /debrief → /aar |
| `top-problems` | `/harvest` + `/todo` | Problem scanning exists |
| `cc-lazy-closure-debt` | `/harvest` scan-handoffs | Obligation tracking exists |
| `cc-aca-*` (8 plugins) | — | Claude-specific authority architecture, not portable |

## Implementation steps

### 1. Add 4 new checks to close-check.rhai

**Agent A (mechanical):**
- CHECK 7: `pre-close-snapshot` — `git rev-parse HEAD` + `git status --short` → write to `~/.grok/state/pre-close-snapshots/<session-id>.json`
- CHECK 8: `commit-format-check` — `git log --oneline --since="12 hours ago"` → validate each message follows conventional format (type(scope): description)

**Agent C (judgment):**
- CHECK 5: `claim-receipt-validation` — scan session output for `[FACT]` claims without tool-call citations. status=fail if any [FACT] lacks a receipt.
- CHECK 6: `next-step-red-team` — take the "Next steps" from the report, apply one adversarial pass ("what's wrong with these?"). Add counter-arguments.

### 2. Document decomposition in wiki

Write a wiki concept `claude-skill-decomposition-close-check-components.md` documenting:
- Which Claude skills were evaluated
- Which were extracted as components vs already covered vs skipped
- The domain mapping for each component
- The extraction rationale (technique, not shell)

### 3. Domain assignments for new components

| Component | Domain | Why |
|---|---|---|
| claim-receipt-validation | lifecycle | Session-quality check at close time |
| next-step-red-team | review | Adversarial evaluation of recommendations |
| pre-close-snapshot | lifecycle | Recovery safety net |
| commit-format-check | verify | Commit quality gate |

## Context
This session ported `/trace` and wired it into close-check as CHECK 4 (critical-code-trace). The same pattern applies to these 4 components: extract the technique, add as a CHECK block, don't port the full skill shell.

The decomposition was identified after scanning all Claude-side skills in `cc-skills-analysis/1.0.123` and `quickstop/plugins`. Of ~30 candidates evaluated, 4 had genuinely novel components not already covered by existing Grok skills.

## Key files
- close-check workflow: `~/.grok/workflows/close-check.rhai`
- close-check command: `~/.grok/commands/close-check.md`
- Skill catalog: `P:/.data/wiki/concepts/skill-catalog.md`
- Claude skills source: `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-analysis/1.0.123/skills/`
