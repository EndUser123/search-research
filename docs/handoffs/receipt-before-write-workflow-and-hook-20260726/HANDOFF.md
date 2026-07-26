# HANDOFF: receipt-before-write workflow + pre-write hook (deferred structural fix)

**Status:** DEFERRED — workflow fix adopted; structural hook deferred until trigger fires
**Created:** 2026-07-26
**Session:** 019f9bfe
**Priority:** MEDIUM — chronic pattern, but workflow fix may be sufficient
**Assignee:** future session (when trigger fires)
**Parent handoff:** none
**Thread:** receipt-before-write-20260726

---

## Objective (one sentence)

Decide whether the receipt-before-write workflow (behavioral rule reinforcement) is sufficient to prevent the vocabulary-mismatch grep fallacy, or whether a structural pre-write hook is needed.

## Why deferred (not done now)

The workflow fix (reinforcing the existing rule + adding the vocabulary-mismatch sub-pattern to the wiki concept) was adopted this session. Behavioral mitigations sometimes suffice; sometimes they decay under closure pressure. The decision to escalate to a structural hook should wait until we have evidence about whether the workflow fix holds.

**The pattern this addresses is chronic** (3+ instances in session 019f9bfe alone, documented across multiple prior sessions). Per the operator's correction (2026-07-26): "this happens all the time across all sessions." Deferring without a handoff would be silent abandonment; this handoff exists to make the deferral explicit and the trigger mechanical.

## Scope

### In scope
1. Validate whether the workflow fix (rule + sub-pattern + `/www`-always-available) reduces the pattern rate over the next 10-20 sessions
2. If pattern rate stays high, design and implement the pre-write hook
3. If pattern rate drops, close this handoff with the workflow fix as the permanent disposition

### Out of scope
- The vocabulary-mismatch grep fallacy wiki concept (already added to `causal-mechanism-claims-require-source-receipts-before-durable-write`)
- The `/www` always-available rule (already added to AGENTS.md)
- The Recommendation format rule (already added to AGENTS.md)

---

## The trigger condition (when to un-defer)

**Un-defer and build the hook when:** the vocabulary-mismatch grep fallacy (or any instance of the receipt-before-write pattern) recurs **3 more times** across the next 10 sessions despite the workflow fix.

**Keep deferred when:** the pattern recurs 0-2 times across the next 10 sessions — the workflow fix is sufficient.

**How to count:** `/aar` Q11 (mandatory blind-spot sub-check) already flags "operator-flagged items without resolution." Any instance where the operator catches a claim that should have had a receipt counts as one recurrence. Track via the AAR's `opportunity_candidate` episodes or the `/tp` critique log.

## The structural fix (if the trigger fires)

A `PreToolUse` hook on `write`/`edit` calls targeting `P:/.data/wiki/concepts/*.md`. The hook would:

1. Intercept the write
2. Scan the file content for mechanism-shaped claims (regex: `\b(because|mechanism|reads only|does not traverse|can't see|scanner|gate|hook)\b`)
3. Check whether each mechanism claim has a `## Receipts` or `## Evidence` section citing a source path + line range
4. Deny (exit 2 with stderr message) if mechanism claims lack receipts

**Technical feasibility: confirmed.** Grok Build supports `PreToolUse` hooks that can deny (`~/.grok/docs/user-guide/10-hooks.md` line 11). Precedent: `~/.grok/hooks/scripts/quality_gate.py`, `verification_receipt_writer.py`, `receipt_shadow_evaluation.py` — all are receipt-enforcement hooks on tool calls.

**Estimated cost:** ~150-200 LOC for the hook script + registration in `~/.grok/hooks/*.json`. Pattern follows existing receipt hooks.

## Evidence

| Claim | Tier | Receipt |
|---|---|---|
| Pattern is chronic (3+ instances session 019f9bfe) | Tier 1 | Session transcript: crawl4ai upgrade claim, `/tp quick` misrecommendation, `/close`-`/aar` false gap |
| Existing rule didn't fire despite documentation | Tier 1 | Wiki concept `causal-mechanism-claims-require-source-receipts` was written 2026-07-25; recurred 2026-07-26 |
| Pre-write hook is technically feasible | Tier 2 | `~/.grok/docs/user-guide/10-hooks.md` line 11; existing hooks at `~/.grok/hooks/scripts/` |
| `_has_code_writes` extended to cover `.md` files | Tier 1 | `close_accounting.py` lines 400-422 (committed this session) |

## Acceptance criteria

The handoff closes when EITHER:
- **Workflow fix suffices:** 10 sessions pass with 0-2 recurrences. Close with disposition "workflow fix adopted as permanent; hook not needed." Update the wiki concept with the outcome.
- **Hook needed:** 3 recurrences in 10 sessions. Build the hook, validate it fires correctly on test wiki writes, deploy. Close with disposition "structural hook adopted; workflow fix remains as defense-in-depth."

## Files to read first

- `P:/.data/wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md` — the rule and the vocabulary-mismatch sub-pattern
- `C:/Users/brsth/.grok/AGENTS.md` § "Claims require receipts" and § "Chronic patterns don't get deferred"
- `~/.grok/docs/user-guide/10-hooks.md` — PreToolUse hook API
- `~/.grok/hooks/scripts/quality_gate.py` — precedent for the hook pattern

## Related work

- `qmd-viability-evaluation-20260725` handoff — separate workstream (qmd architecture), unrelated
- `tp-adhd-prototype-20260725` handoff — separate workstream, unrelated
