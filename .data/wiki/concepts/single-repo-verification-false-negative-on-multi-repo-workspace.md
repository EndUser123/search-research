---
title: "Single-repo verification false-negative on multi-repo workspaces"
concept_type: "anti-pattern"
created: 2026-07-27
agent: grok
host: both
cognitive_load: 2
verification: session-verified
sources:
  - session 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e (2026-07-27 /tp re-review)
tags: [verification, multi-repo, git, false-negative, receipt-discipline, search-topology, anti-pattern]
summary: >
  When a workspace spans multiple git repositories (e.g., P:/ for the
  project repo and ~/.grok/ for skills/hooks source), verifying a cited
  commit hash, file path, or artifact against only ONE of those repos
  produces a false "unverifiable" / "does not exist" verdict. The verifier
  concludes the citation is fabricated or stale when in fact it lives in a
  sibling repository the verifier never queried. Both human reviewers and
  LLM critics exhibit this pattern. The fix is structural: verification
  commands must enumerate all workspace repositories by default, not just
  the parent workspace.
relations:
  - target: P:/AGENTS.md § "Search Topology"
    type: extends — that rule covers files across multi-root workspaces; this concept extends it to git history (commits, hashes, branches)
  - target: wiki/concepts/evidence-scope-discipline
    type: related — both are about not inflating verification scope
  - target: wiki/concepts/narrative-as-signal
    type: related — the false "unverifiable" verdict is a plausible narrative substituting for multi-repo verification
---

# Single-repo verification false-negative on multi-repo workspaces

## The anti-pattern

A workspace contains multiple git repositories. A reviewer (human or LLM)
receives a citation: "commit `c4e9897` shows X." The reviewer runs
`git log c4e9897` or `git show c4e9897` against ONE repository — typically
the parent workspace repo (`P:/`) — and receives "unknown revision." The
reviewer concludes the citation is fabricated, stale, or unverifiable.

**The conclusion is wrong.** The commit exists in a sibling repository
(e.g., `~/.grok/`, where skills/hooks source-of-truth lives per the
"Skill locations" table in `~/.grok/AGENTS.md`). The reviewer queried the
wrong repo and treated the negative result as proof of absence.

## Observable signature

```
verifier:   git log <hash>    # in parent repo only
git:        fatal: ambiguous argument '<hash>': unknown revision
verifier:   "the cited commit is unverifiable — likely fabricated or stale"
reality:    commit exists in sibling repo at ~/.grok/ or ~/.claude/
```

## Why this is dangerous

1. **It produces false refutations of correct claims.** A document citing
   a cross-repo commit gets its load-bearing evidence rejected. The
   reviewer's downstream verdict is then wrong (e.g., a REVISE/BLOCK
   critique of a proposal that was actually correctly evidenced).

2. **Both humans and LLM critics exhibit it.** LLM critics are more prone
   because their default `git` invocation runs against CWD without
   `-C <repo>` scoping.

3. **The "Skill locations" rule in AGENTS.md already warns about this for
   files**, but does not explicitly extend to git history. Reviewers
   inherit the file-level rule but miss that commits/hashes need the same
   multi-repo scope.

4. **The failure compounds.** A document author who CAN'T reproduce the
   reviewer's "unverifiable" verdict (because they remember the commit
   exists) must push back; the pushback itself becomes a turn of
   meta-argument that delays the substantive work. In session
   019fa111, this consumed an entire critique cycle before the
   multi-repo root cause was identified.

## The structural fix

**Multi-repo scope by default.** Verification commands for commits,
hashes, branches, and tags must enumerate all workspace repositories:

```powershell
# WRONG (single-repo — produces false negatives on cross-repo citations):
git log <hash>
git show <hash>

# RIGHT (multi-repo — covers parent + sibling repos):
git -C P:/ log <hash>
git -C C:/Users/brsth/.grok log <hash>
git -C C:/Users/brsth/.claude log <hash>
```

For this workspace specifically, the three repos that may hold cited
artifacts:

| Repo path | What lives there |
|-----------|------------------|
| `P:/` | Project workspace (docs, packages, .data/wiki, .agents, .claude/hooks) |
| `~/.grok/` | User-scope skills source (`~/.grok/skills/<name>/`), user-scope hooks (`~/.grok/hooks/`), user config |
| `~/.claude/` | Claude compat-layer source, claude plugins cache source |

## When this fires

Apply multi-repo scope whenever verifying:
- A commit hash (`git show`, `git log`, `git diff`)
- A file path under `~/.grok/` or `~/.claude/` (already covered by the
  "Skill locations" rule, but easy to forget under time pressure)
- A branch name that might live in a sibling repo
- A tag or release identifier
- A `git blame` result for a path that might be cross-repo

**Skip multi-repo scope** for:
- File paths unambiguously under `P:/` (single-repo is sufficient)
- Commits already verified to exist in `P:/`
- Operations on the current repo (CWD is the right scope)

## Falsifier

This pattern is wrong if a single `git log` against `P:/` is sufficient
to verify every cited commit/hash/branch in this workspace's documents.
That would mean all documents cite only parent-repo artifacts. Empirical
check (session 019fa111, 2026-07-27): one document cited `c4e9897`
from `~/.grok/`; single-repo verification produced a false refutation
that consumed a full critique cycle to correct. Pattern confirmed.

## Reference incident

**Session 019fa111 (2026-07-27):** a `/tp` critique of a 14-item
recommendations document asserted that the document's load-bearing
evidence (commit `c4e9897`) was "unverifiable from the parent
workspace." Both the orchestrator and a 100-tool-call fresh subagent
ran `git log c4e9897` against `P:/` only and received "unknown revision."
The verdict was tagged `REFUTED_AS_EVIDENCE` and propagated to the
operator.

The operator's rebuttal ran `git -C C:\Users\brsth\.grok show c4e9897`
and the commit resolved immediately, modifying
`skills/close/__lib/close_accounting.py`,
`skills/close/tests/test_mutation_receipts.py`, and
`skills/close/tests/test_scanner.py` — exactly the artifacts the
document claimed. The critique's `REVISE` verdict was grounded partly
in this false refutation.

**Root cause:** the AGENTS.md "Search Topology" rule covers file
existence across multi-root workspaces but does not extend to git
history. The critics applied the file-level pattern (correctly, when
checking file existence) but missed that commit hashes need the same
multi-repo scope.

## Relation to existing rules

- **AGENTS.md § "Search Topology"** — establishes the multi-root search
  principle for files. This concept extends it to git history.
- **AGENTS.md § "Claims require receipts; narrative sufficiency is not
  verification"** — the false "unverifiable" verdict is itself a
  narrative-as-signal failure (plausible conclusion substituting for
  multi-repo verification).
- **AGENTS.md § "Narrative-as-signal"** — same class: a plausible story
  ("the commit doesn't exist in `P:/`, therefore it's unverifiable")
  substitutes for the actual verification command (`git -C <each repo>`).

## Prevention

Two layers, applied together:

1. **Behavioral (this concept).** When verifying a commit hash, file
   path, or branch cited in a document, enumerate all workspace
   repositories by default. The "Skill locations" table in
   `~/.grok/AGENTS.md` is the canonical list of repo roots.

2. **Tooling (future).** A `multi_repo_git_lookup.sh <hash>` helper that
   runs `git -C <repo> log <hash>` across `P:/`, `~/.grok/`, and
   `~/.claude/` and reports which repo (if any) contains the hash. This
   would have caught the 019fa111 false refutation in <1 second instead
   of a full critique cycle. Candidate for `P:/.agents/scripts/` or the
   prior-art manifest generator proposed in the same session.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
