---
title: "Check-and-fix skills — verification skills should fix what they can, not just report"
created: 2026-08-08
source: session-019fdf3d
tags: [skill-design, verification, auto-fix, doc-check, ship-py, architectural-decision]
summary: >
  Verification skills (doc-check, skill-dev, future gates) should auto-fix
  deterministic findings instead of only reporting them and waiting for manual
  intervention. The principle: if the fix is deterministic, the skill should
  apply it. If the fix needs human judgment, the skill should report only.
  This inverts the old "check skills never modify files" rule.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/pipeline-session-scoping-each-layer-independently.md
    type: complements
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
  - target: wiki/concepts/narrative-sufficiency-awareness-enforcement-gap-2026.md
    type: related
---

# Check-and-fix skills — verification skills should fix what they can

## Decision context

Doc-check had a hard rule: "Never modify files — this is a check, not a fix."
The operator pointed out: if the fix is deterministic (add `host: both`, close
a code fence, convert a wikilink to prose), the skill should do it — not report
it and wait for manual intervention. Manual intervention for deterministic
fixes is operator cognitive load with no value added.

## The decision

**Verification skills auto-fix findings with deterministic solutions.** The
boundary is clear:

| Finding type | Fix? | Why |
|---|---|---|
| Missing `host:` frontmatter | ✅ Fix — add `host: both` | Deterministic, no judgment needed |
| Unclosed code fence | ✅ Fix — append closing ``` | Deterministic |
| Unresolved `/wikilink` | ✅ Fix — convert to `/slug` prose | Deterministic (the link doesn't resolve; prose reference is always safe) |
| Broken HTTP link | ❌ Report — needs human decision (link may be transient, or replacement needed) | Judgment required |
| Stale README reference | ❌ Report — needs human judgment (is the reference still relevant?) | Judgment required |
| Missing CHANGELOG entry | ❌ Report — needs commit context the script doesn't have | Context required |

## The principle

**If a finding's fix is a pure function of the finding itself (no external
context, no judgment, no trade-off), the skill applies it.** If the fix
requires information the skill doesn't have or a trade-off the operator should
make, the skill reports only.

This is the same principle behind `ruff --fix` (auto-fixes F841, I001, etc.
but NOT F401 without --unsafe-fixes) and `black` (formats deterministically
without asking). The verification skill becomes a check-AND-fix skill, not
a check-only skill. This aligns with [[mechanical-enforcement-over-behavioral-reminder]]:
if the fix is mechanical, the system should do it, not just remind the operator.
The same philosophy drives the trajectory-validity gate ([[reasoning-first-search-never-claim-without-checking]])
which enforces rather than advises.

## Steelman of the rejected alternative (check-only)

The check-only rule existed for a good reason: **predictability.** A check
skill that modifies files is surprising — the operator runs `/doc-check`
expecting a report, and files change unexpectedly. The check-only rule
guaranteed separation of concerns: detection is safe, modification is explicit.

**Why the steelman loses here:** the operator explicitly asked for auto-fix.
The surprise factor is mitigated by: (1) the `--fix` flag is opt-in (default
remains check-only when invoked standalone), (2) the JSON output includes an
`auto_fixed` field listing which files were modified, (3) the re-run after
fixing shows the post-fix verdict. The operator can see exactly what changed.

## What this means for our workspace

- Doc-check now has `--fix` mode (auto-fixes frontmatter, fences, wikilinks)
- Ship-py passes `--fix` automatically so doc-check fixes before reporting
- Skill-dev scanner findings could follow the same pattern (auto-add `host:`,
  auto-suppress intentional cross-skill deps with noqa) — future work
- The old rule "never modify files" is replaced with "fix deterministic
  findings, report judgment-required findings"

## Falsifier

This decision is wrong if auto-fix introduces regressions — e.g., adding
`host: both` to a skill that was intentionally `host: grok` (because it uses
Grok-native features that don't work on Claude). Mitigation: the default is
`host: both`, and skills that need a specific host already declare it (the
frontmatter check only fires when `host:` is entirely absent). If the
false-positive rate of auto-fix exceeds 10% in practice, revert to check-only
and make `--fix` opt-in only.

## Receipts

- `doc-check/scripts/check.py:fix_skill_frontmatter()` — adds `host: both`
  after the description block in the frontmatter
- `doc-check/scripts/check.py:fix_code_fences()` — appends closing ```
- `doc-check/scripts/check.py:fix_wikilinks()` — converts `/slug` to
  `/slug` when no candidate file resolves
- `doc-check/SKILL.md` — rule 1 removed, auto-fix section added
- `ship-py/__lib/ship_orchestrator.py:cmd_doc_check` — passes `--fix` flag

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[scope-matching-verification-discipline]]
- [[close-scanner-verification-gap-stale-read]]

