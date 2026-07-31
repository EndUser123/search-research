---
title: "List-before-claim for destructive-proposal actions"
created: 2026-07-31
source: session-019fb937 (/why + /tp on hook timeout RCA → inference-as-fact proposal)
sources:
  - internal: P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
  - internal: ~/.grok/AGENTS.md (List-before-claim rule, added 2026-07-31)
  - internal: ~/.grok/skills/why/SKILL.md (evidence-tier system, Step 4b)
tags: [inference-as-fact, destructive-proposal, verification, structural-fix, closure-pressure]
agent: grok
host: both
cognitive_load: 2
verification: single-session-verified
summary: >
  Before proposing to gitignore, git rm, untrack, or delete any file/directory,
  the agent MUST first run ls/git ls-files/Get-ChildItem on the target and cite
  the output. This prevents the class of error where the agent infers directory
  contents from a single script's output and proposes a destructive action that
  destroys irreplaceable data. Incident: proposing to gitignore .data/wiki/sources/
  as "8,646 stubs" when 87% were irreplaceable source transcripts — the ls was
  never run. The rule is scoped to the specific action class (removal proposals),
  not a general verification requirement, making it cheap to enforce and hard to
  skip.
relations:
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: caused-by
  - target: wiki/concepts/inference-chains-bare-numbers-destructive-write.md
    type: refines
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
---

# List-before-claim for destructive-proposal actions

## Decision context

**The incident:** a `/why` RCA on chronic hook timeouts identified `.data/wiki/sources/`
as containing "8,646 auto-generated stubs." The RCA proposed gitignoring the entire
directory. The claim was based on knowing that `index_skills.py` writes stubs there —
but the agent never listed the directory. When finally checked: 7,529 of 8,646 files
(87%) were irreplaceable source transcripts (YouTube, web pages, PDFs with provenance
chains backing wiki concept pages). The proposal would have destroyed the wiki's
entire evidence base on a fresh clone.

**The failure pattern:** the agent had a good narrative ("index_skills.py writes stubs
here → therefore everything here is a stub"), the operator was engaged, the fix felt
imminent. Under that closure pressure, the step that would have caught the error
("list the directory first") was skipped. This is the same closure-pressure failure
mode documented in [[reactive-pattern-matching-and-closure-pressure]] — the agent
pattern-matched to a familiar shape (regenerable stubs) without verifying.

**Why existing rules didn't catch it:** the `/why` skill has an evidence-tier system
("Emit [INFERENCE] first, upgrade to [FACT] only after reading the code"). The
AGENTS.md has "Claims require receipts." Both rules target CLAIMS about code state.
Neither specifically targets PROPOSALS about file removal. The agent's claim ("these
are stubs") felt verified because the script's output confirmed stubs exist — but
existence ≠ totality. The gap: no rule required listing the FULL directory contents
before claiming what the directory "is."

## The rule

**Before proposing to gitignore, `git rm`, untrack, or delete any file/directory:**
first run `ls`, `git ls-files`, or `Get-ChildItem` on the target and cite the output.

The claim "this directory contains only X" is `[INFERENCE]` until verified by a
directory listing. This prevents the specific class of error where the agent infers
directory contents from a single script's output.

**Scope:** destructive-proposal actions only (gitignore, rm, untrack, delete). Not a
general verification requirement — that would be too expensive to enforce on every
claim. The narrow scope makes the rule cheap to comply with and hard to rationalize
skipping.

## Why this is structural, not behavioral

A behavioral rule ("always verify before claiming") has a ~50% compliance ceiling under
closure pressure (see [[mechanical-enforcement-over-behavioral-reminder]]). This rule
is more structural because:

1. **The action class is narrow and mechanically detectable.** A hook could grep for
   `gitignore|rmdir|git rm|Remove-Item.*-Recurse` in tool inputs and require a prior
   `ls`/`Get-ChildItem` receipt — same pattern as the verification-receipts system.

2. **The verification is cheap.** One `ls` command. Not a full preflight, not a
   cross-model review. The cost of compliance is ~1 second.

3. **The failure mode is severe and irreversible.** Deleting irreplaceable source
   transcripts can't be undone without re-downloading/re-transcribing everything. The
   cost of skipping is catastrophic.

## Enforcement

**Current layer:** AGENTS.md rule (added 2026-07-31, `~/.grok/AGENTS.md` line 294).
This is a behavioral rule with the ~50% compliance ceiling.

**Potential mechanical layer:** a PreToolUse hook on `search_replace|write` that
detects gitignore/rm patterns in the file content and checks for a prior directory-listing
receipt. This would raise compliance above the behavioral ceiling. Not yet implemented.

## Falsifier

This concept is wrong if, within 12 months:
- **The rule fires too often on non-destructive changes** (false positives). If agents
  are listing directories before every edit, the scope is too broad.
- **The rule never fires** because agents already verify naturally. Then it's redundant
  with existing evidence-tier rules and should be retired.
- **A destructive proposal still ships without a listing** despite the rule. Then the
  behavioral layer is insufficient and the mechanical hook is needed.

## Related

- [[hook-evidence-collection-cost-vs-timeout-tradeoff]] — the incident that surfaced
  this pattern; the RCA proposed gitignoring irreplaceable files without listing them
- [[inference-chains-bare-numbers-destructive-write]] — same family of inference-as-fact
  failures, this concept refines by adding the directory-listing verification step
- [[reactive-pattern-matching-and-closure-pressure]] — the closure-pressure mechanism
  that caused the skip
- [[mechanical-enforcement-over-behavioral-reminder]] — why behavioral rules need
  mechanical backing to exceed ~50% compliance
