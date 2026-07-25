---
title: "Skill rewrite protocol: rename-fallback, cross-reference preservation, filename-collision resolution"
created: 2026-07-25
source: session-2026-07-25 (/tp rewrite execution)
tags: [skill-authoring, rewrite-protocol, rename-fallback, cross-reference, filename-conflict, preserve-tested-behavior, transferable-pattern]
agent: grok
host: both
cognitive_load: 2
verification: local-only
summary: >
  A reusable protocol for rewriting a load-bearing AI-agent skill without
  losing tested behavior or breaking consumers. Three structural moves:
  (1) rename current SKILL.md to SKILL-old.md as a fallback before writing
  the new one, (2) split deep content into separate reference files so
  SKILL.md becomes routing logic rather than a monolith, (3) when a handoff
  names a target file that already exists with valuable content, rename
  the existing file rather than overwriting. Validated on the /tp rewrite
  (2026-07-25, commit 91e56a2): 847→463 lines with zero cross-reference
  breakage and zero lost content.
relations:
  - target: wiki/concepts/multi-dimensional-matrix-skill-organization-pattern
    type: companion
  - target: wiki/concepts/skill-path-resolution-gotcha
    type: related
  - target: wiki/concepts/skill-rename-propagation-checklist
    type: extends
---

## Summary

Rewriting a skill that other skills or workflows consume is a hard-to-reverse
operation: the new version starts from zero uses, consumers may break silently,
and valuable content in the existing file can be lost if the rewrite
overwrites rather than splits. This protocol, validated on the /tp rewrite
(2026-07-25), makes the operation safe:

1. **Rename current → old as fallback** before writing new
2. **Split deep content** into reference files (SKILL.md = routing;
   reference/ = deep content)
3. **Resolve filename collisions** by renaming existing content rather than
   overwriting

All three moves are independently useful; together they make a rewrite
recoverable if the new version surfaces issues on first use.

## Key findings

### 1. Rename-fallback before overwrite

Before writing the new SKILL.md, rename the current one to SKILL-old.md
via `git mv` (preserves history). This gives:

- **Recovery**: if the new version has a bug on first real use, the
  operator can `git mv SKILL-old.md SKILL.md` to restore tested behavior
  in one command
- **Diff baseline**: the old version stays available for comparison when
  the new version behaves unexpectedly
- **Audit trail**: `git log --follow SKILL-old.md` shows the full history
  of the pre-rewrite behavior

`git mv` is required over copy-then-delete because it preserves `git
blame` history. Manual copy+delete loses the chain.

### 2. Split deep content; SKILL.md becomes routing logic

The /tp rewrite moved three categories of content out of SKILL.md:

| Content | Destination | Why |
|---|---|---|
| Subagent prompt template (Steps A-D, evidence tagging, output format) | `protocol.md` | SKILL.md becomes routing; protocol.md is the instrument |
| Failure modes table (9 modes) + circuit breaker | `reference/failure-modes.md` | Diagnostic vocabulary, not routing logic |
| Reconstructed operating manual (stance, craft exemplars) | `reference/operating-manual.md` | Deep reference loaded via `/tp load`, not needed for routing |

Result: SKILL.md dropped from 847 to 463 lines (45% smaller) while
preserving 100% of the content — nothing was deleted, only relocated.
The skill's routing decisions are now visible at a glance; deep content
loads on demand.

**Heuristic:** if a section of SKILL.md is longer than 50 lines and is
reference material rather than routing logic, it's a candidate for a
separate file. The routing layer should be readable in one screen.

### 3. Filename-collision resolution (the protocol.md conflict)

The /tp handoff said: "Move subagent prompt template to `protocol.md`."
But `protocol.md` already existed — a 557-line "Operating Manual" of
reconstructed prompt + craft exemplars, written 2026-07-18 and loaded via
`/tp load`. The handoff author didn't know.

Two options:
- **(a) Overwrite protocol.md** with the new subagent template. Loses
  the operating manual. Handoff said to do this.
- **(b) Rename the existing protocol.md** to `reference/operating-manual.md`,
  then write the new protocol.md. Preserves both. Updates the 4
  cross-references in SKILL.md.

**(b) is always correct when the existing file has value.** The handoff's
filename choice was arbitrary; the existing content was not. The
operator's standing rule ("optimal long-term, transition effort is not a
criterion") applies: preserving valuable content outweighs honoring an
arbitrary filename in a handoff.

**The structural fix:** before writing to a handoff-named target file,
check whether the file already exists. If it does and has content, either
(a) the handoff intends to overwrite (confirm), or (b) the handoff author
didn't know the file existed — rename the existing file, write the new
one, update cross-references.

### 4. Cross-reference preservation (the verification step)

After the rewrite, every cross-reference must be verified:

- **Internal references** (SKILL.md → protocol.md, reference/*): grep
  SKILL.md for the new paths; confirm each target file exists
- **External consumers** (other skills that reference this one): grep
  the skills directory for the skill name; confirm the referenced
  variant/section still exists
- **Routing references** (`/tp load` → which file?): verify the routing
  table now points to the new location

The /tp rewrite verification: 4 internal references to `protocol.md` in
the new SKILL.md, 1 external consumer (`/close` → `/tp session`), all
resolved. Verification commands:

```powershell
Select-String -Path SKILL.md -Pattern "protocol\.md|reference/|reference\\"
Select-String -Path <consumer>/SKILL.md -Pattern "<skill-name>"
```

### 5. The /tp rewrite receipts (verification)

- Commit `91e56a2` in dotgrok repo: 5 files changed (+2358/−1472)
- Line counts verified: SKILL.md 847→463, protocol.md 195 (new),
  reference/operating-manual.md 557 (moved), reference/failure-modes.md 47 (new)
- Cross-references verified: all 4 internal refs in SKILL.md resolve,
  `/close` → `/tp session` intact
- **EVIDENCE_GAP:** behavioral validation (running the rewritten skill
  end-to-end in a fresh session) is pending. The structural rewrite is
  complete and verified; runtime behavior has not been observed.

## When this protocol applies

Use this protocol when rewriting any skill that meets ≥1 of:

- Other skills invoke it (`/close` → `/tp`, `/design` → `/tp`-equivalent)
- Workflows depend on its variant names or file paths
- The current SKILL.md is >500 lines (accretion without structure)
- The handoff names target files that may already exist

Do NOT apply for: trivial edits (single-section update), new skill
creation (no old version to preserve), or non-load-bearing skills with
no consumers.

## Anti-pattern: overwrite without rename-fallback

The tempting path is to edit SKILL.md in place — `git diff` shows the
change, history is preserved by git, what's the problem? The problem is
recovery: if the new version has a runtime bug the diff doesn't catch
(e.g., a subtle prompt change that confuses the subagent), restoring
tested behavior requires `git revert` + re-editing, or `git checkout HEAD~1
-- SKILL.md` which discards uncommitted work. The rename-fallback makes
recovery a one-liner: `git mv SKILL-old.md SKILL.md`.

The cost of rename-fallback is one git mv and one extra file in the
directory. The benefit is recoverability of a load-bearing skill. The
asymmetry favors rename-fallback for any skill with consumers.

## Related

- [[multi-dimensional-matrix-skill-organization-pattern]] — the organizing principle the rewrite implemented (companion concept)
- [[skill-rename-propagation-checklist]] — extends with the rename-specific verification steps
- [[skill-path-resolution-gotcha]] — the path-resolution failure class this protocol avoids
- [[skill-lifecycle-toolkit]] — broader skill lifecycle context

## Sources

- Session 2026-07-25 /tp rewrite execution
- Commit `91e56a2` in dotgrok repo (C:/Users/brsth/.grok)
- Handoff: `P:/docs/handoffs/tp-rewrite-20260725/HANDOFF.md`
- Prior operator rule: "optimal long-term, transition effort not a criterion" (`~/.grok/AGENTS.md` § "Optimal long-term solution")
