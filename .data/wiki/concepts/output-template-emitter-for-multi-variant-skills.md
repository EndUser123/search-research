---
title: "Output-template emitter: deterministic skeleton generation for multi-variant skills"
created: 2026-08-03
source: session-2026-08-03 (tp_output_template.py format conflation fix)
sources:
  - P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md (parent pattern)
  - P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md (companion)
  - P:/.data/wiki/concepts/code-output-passthrough-narration-over-script-output.md (related)
tags: [skill-design, output-format, format-conflation, code-orchestrates-model-judges, multi-variant, template-emitter, transferable-pattern]
agent: grok
host: both
cognitive_load: 2
verification: local-only
confidence: 1.0
last_verified: 2026-08-03
half_life_days: 365
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: refines
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps
    type: related
  - target: wiki/concepts/code-output-passthrough-narration-over-script-output
    type: related
---

# Output-template emitter: deterministic skeleton generation for multi-variant skills

## Summary

When a skill has multiple variants (e.g., `/tp session`, `/tp improve`, `/tp explore`, `/tp recap`), the LLM frequently conflates output formats — producing session format when asked for improve format, or mixing sections across variants. The structural fix: a deterministic Python script emits the output skeleton for the requested variant, and the LLM fills in the judgment content (findings, analysis). Code owns the format; the LLM owns the judgment.

## The problem

**Format conflation** occurs when a multi-variant skill produces the wrong variant's output structure. Observed in session 019fa8f8 (2026-08-02): `/tp improve` produced `/tp session`'s NOTED table + actionable recommendations format instead of the 4-dimension improvement table. The LLM had all variants in its SKILL.md context; under cognitive load, it picked the most-recently-seen format rather than the correct one.

This is the same failure class as prose-rule bypasses under closure pressure: the SKILL.md describes the correct format, but the LLM's generation pathway doesn't reliably follow prose instructions when multiple valid formats are in context.

## The structural fix

An **emitter script** (`__lib/<skill>_output_template.py`) generates mode-specific output skeletons:

```bash
python __lib/tp_output_template.py --mode improve
```

Output is a fill-in-the-blanks template with `___` placeholders:

```
## Improvement analysis: session chain ___

### Efficiency (___ items)
1. **<improvement>** — <root cause>. Effort: ___. Confidence: ___. Chronicity: ___.
   Rejected: <alternative> because <reason>.

findings_total: ___, surfaced: ___, omitted: 0
```

The LLM presents this skeleton as its response, then fills each placeholder with actual findings. This is the "code-orchestrates-model-judges" principle applied at the **output-format layer** rather than the **gate layer**:

| Layer | What code owns | What LLM owns | Pattern |
|-------|---------------|---------------|---------|
| Gate (step gating) | Whether to advance (conditional edge) | Judgment fields (ACCOUNTING buckets) | `code-orchestrates-model-judges-skill-scale` |
| Output format (this concept) | Which skeleton to produce | Findings content | This concept |

## When to apply

A skill is a candidate for an output-template emitter when ANY of:

1. **Multiple output formats in one skill** — the skill has ≥2 variants with structurally distinct output shapes (different section headers, different list formats, different required fields)
2. **Observed format conflation** — the model has produced the wrong variant's format at least once
3. **Format precision matters** — downstream consumers parse specific sections (e.g., `/close` parses `/tp session`'s actionable recommendations, `/harvest` scans for completeness counters)
4. **Completeness counters or structured footers** — the output must end with `findings_total: N, surfaced: N, omitted: 0` or similar machine-checkable fields

## How to build one

1. **Extract the output format** from SKILL.md into a Python template string per variant
2. **Use fill-in-the-blanks placeholders** (`___`, `<placeholder>`) — not generated content
3. **Add argparse** with `--mode <variant>` so the LLM can request the right skeleton
4. **Wire the SKILL.md** to reference the emitter in each variant's section ("Run the template emitter...")
5. **Add tests** that verify each mode produces the required structural markers (section headers, completeness counters, specific fields)
6. **Update the variant table** in SKILL.md to mention the emitter for each variant

## What this prevents

- **Format conflation**: the LLM starts from the correct skeleton, not from memory
- **Missing required sections**: the template includes all mandatory sections; the LLM can't accidentally omit one
- **Completeness counter omission**: the template includes the `findings_total` footer
- **Wrong variant dispatched**: the `--mode` flag is explicit; there's no ambiguity about which format to produce

## What this does NOT prevent

- **Wrong content in the right format**: the LLM can still fill placeholders with incorrect findings. The emitter fixes structure, not judgment.
- **Missing variants**: if a variant doesn't have a template in `_MODES`, it falls back to prose-guided output. The emitter only covers registered variants.
- **Stale templates**: if the SKILL.md format changes but the template isn't updated, the emitter produces outdated format. Test both together.

## Instance: tp_output_template.py

File: `~/.grok/skills/tp/__lib/tp_output_template.py`

4 modes: `improve`, `session`, `explore`, `recap`. 7 tests in `__lib/tests/test_tp_output_template.py`.

The emitter was added in session 019fa8f8 (2026-08-02) to fix format conflation between `/tp improve` and `/tp session`. Before the emitter, `/tp improve` produced `/tp session`'s NOTED + actionable recs format instead of the 4-dimension table. After the emitter, each variant starts from a code-generated skeleton, eliminating the conflation.

## Falsifier

This pattern is wrong if:
- The LLM produces correct output format equally well without the emitter (the conflation was a one-time incident, not a recurring pattern)
- The emitter's template drifts from the SKILL.md format (maintenance burden exceeds conflation cost)
- The LLM fills the template with the wrong content despite having the right skeleton (the problem is judgment, not format)

## Related

- [[code-orchestrates-model-judges-skill-scale]] — the parent pattern; this concept is the output-format application
- [[visible-output-contracts-for-behavioral-skill-steps]] — companion: visible contracts make step compliance checkable
- [[code-output-passthrough-narration-over-script-output]] — related: when code produces complete output, bypass the LLM entirely
