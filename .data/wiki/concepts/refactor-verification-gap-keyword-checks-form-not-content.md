---
title: "Refactor verification gap — keyword checks verify form, not content"
created: 2026-07-28
source: session-019fa48a (/tp review agents.md)
tags: [verification, refactor, keyword-check, semantic-diff, evidence-scope, generalizable]
host: both
agent: grok
verification: observed
cognitive_load: 2
summary: >
  When verifying that a refactor preserved all content, keyword-presence checks (grep
  for "filter-branch", "typed ownership", etc.) confirm that the keyword EXISTS in the
  file but not that the surrounding CONTEXT survived. A refactor that strips a rule's
  worked examples, operator-domain knowledge, or reference incidents passes keyword
  verification while losing load-bearing content. The /tp critique of the AGENTS.md
  refactor caught 8 such losses that 20/20 keyword verification missed. The fix is
  semantic diff: compare old vs new section by section, not keyword by keyword.
relations:
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: related
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: related
---

# Refactor verification gap — keyword checks verify form, not content

## Decision context

**Why this was needed:** during the AGENTS.md refactor (1,679 → 620 lines), I verified that all rules survived by checking 20 critical keywords and 35 section headers. Both checks passed (20/20, 35/35). Then `/tp review agents.md` spawned a fresh subagent that read both the old and new files and found 8 specific content losses the keyword check missed: `filter-repo` dropped from the forbidden git list, `typed ownership` / `automation orchestration` / `enterprise integration patterns` dropped from the operator profile, 6 worked examples in the receipt rule removed, and reference incidents that anchored pattern-recognition rules deleted.

## The pattern

Keyword verification answers: "Does the string X appear in the file?" It confirms **form** — the rule's name or key phrase exists.

Content verification answers: "Is the full context around X preserved?" It confirms **substance** — the rule's body, evidence, examples, and qualifiers survived.

These are different checks. A refactor that strips the "why" from every "what" passes keyword verification while producing a file where every rule is a bare statement without the context the model needs to apply it correctly under pressure.

Concrete example from this session: the keyword "Self-verification prohibition" existed in both the old and new files (keyword check PASS). But the *body* of that rule — the session reference (`019fa5a1`), the CooperBench example, and the "why" paragraph explaining that self-assessment shares the pattern-completion pathway — was silently deleted. The keyword survived; the evidence base didn't. Under session pressure, a bare rule statement without its evidence anchor fires less reliably than the same statement with a concrete instance of the failure it prevents.

## Why this matters

The AGENTS.md refactor is the specific instance, but the pattern generalizes to any refactor of always-loaded context:
- SKILL.md files condensed for progressive disclosure
- Config files consolidated
- Wiki concepts merged or split
- Any edit that claims "all content preserved" based on keyword checks

The verification gap is most dangerous when the refactor author is also the verifier. The author knows what they intended to keep, so their keyword list is biased toward what survived. A fresh reviewer doesn't know what was supposed to be there — they compare actual content, not intended content.

## The fix: semantic diff

After a refactor, compare old vs new section by section:

```powershell
# Extract sections from both files, diff them
$old = Get-Content backup.md -Raw
$new = Get-Content current.md -Raw

# For each section header in the old file:
# 1. Extract the section body (header to next header)
# 2. Check if the same header exists in the new file
# 3. Compare the bodies — are the key sentences preserved?
# 4. Flag any section where the body shrank >50% without a corresponding rule consolidation
```

This is more expensive than keyword grep (~5 minutes vs ~30 seconds) but catches what keyword checks structurally cannot.

The `/tp` critique is a lighter-weight alternative: spawn a fresh subagent with both old and new files and ask "what content was lost?" The subagent reads semantically, not lexically — it compares meaning, not just strings. Cost: ~140 seconds. This is what caught the 8 losses in the AGENTS.md refactor that 20/20 keyword verification missed.

## Connection to existing principles

This is a specific instance of the evidence-scope discipline rule already in AGENTS.md: "passing unit tests does not prove live activation." The refactor variant: "keyword presence does not prove content preservation." Both are surface-property checks that don't verify deeper properties.

The `/tp` critique is the structural fix — a fresh lens reading both files catches what the author's own keyword check cannot, because the author knows what they intended to preserve and the keyword check confirms intent, not outcome. This is why the `/tp` skill's two-lens architecture (fresh subagent + verification) is structurally stronger than self-review for refactoring verification: the fresh subagent has no anchoring bias toward what "should" be there.

## What this means for our workspace

For future AGENTS.md or SKILL.md refactors:
1. **Always run `/tp <file>` after the refactor** — the fresh subagent reads both versions and catches content losses
2. **Keyword checks are necessary but not sufficient** — they catch lost rule *statements* but not lost rule *bodies*
3. **Track what was lost and restored** — the /tp critique found 8 items; 1 was a safety-critical loss (`filter-repo`), 3 were operator-context losses, 4 were pattern-recognition anchor losses
4. **The verification cost asymmetry is real** — keyword checks take 30 seconds; `/tp` critique takes ~140 seconds. But the cost of shipping a silently-broken refactor (lost safety rules, degraded pattern recognition) is measured in future session corrections. The 110-second difference is false economy.

The deeper lesson is about **verification method matching**: the verification method must test the property being claimed. "All content preserved" is a content claim; keyword presence is a form check. The method doesn't match the claim. This is the same structural mismatch as "tests pass" (form) being used to claim "live activation works" (content) — the evidence-scope discipline rule already in AGENTS.md.

## Falsifier

This finding is wrong if keyword checks reliably catch all content losses. Test: on the next refactor, run keyword checks, then run `/tp` critique, and compare. If `/tp` finds 0 additional losses beyond what keyword checks caught, keyword verification is sufficient and this concept should be retired.

## Receipts

- Session 019fa48a: 20/20 keyword check passed, then `/tp` subagent (019faa40) found 8 losses via reading both files
- Lost items confirmed via grep: `filter-repo`, `typed ownership`, `automation orchestration`, `enterprise integration patterns`, `CooperBench`, `019fa5a1`, `cc-council`, `close-lighter` — all present in backup, absent in refactored file
- Fix: all 8 items restored after `/tp` critique flagged them
- The `/check` verifier (subagent 019fab91) later confirmed all restored items present in the final file

## Relations

- [[agents-md-construction-best-practices]] — the refactor that exposed this gap
- [[enforcement-hierarchy-and-compaction-strategy]] — the compaction framework used for the refactor
- evidence-scope-discipline — the general principle this is a specific instance of (surface-property checks don't verify deeper properties)
