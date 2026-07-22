---
title: "QMD patch durability — extend existing patch convention, not wrapper/vendor/swap"
created: 2026-07-20
source: /design run 10d616f8 on 2026-07-20 (4 review rounds, 33 issues addressed)
tags: [qmd, patch-management, durability, design-decision, grok-build, sessionstart-hook, wiki]
summary: >
  When QMD site-packages patches needed a durability story, the design loop
  converged on extending the user's existing `.patch` + reinstall-protocol
  convention (already used for qmd_fts5_patch.patch) rather than introducing
  a wrapper script, vendoring, forking, or replacing the library. The
  wrapper approach was rejected because it imports from an internal module
  path (same fragility class as the original patches) and solves a scenario
  the operator has explicitly prevented (qmd is pinned at 0.1.1; do not
  auto-upgrade). The design adds two new `.patch` files, extends the wiki
  CLAUDE.md reinstall protocol, and adds a Grok-native SessionStart
  verification hook so silent regressions get caught automatically every
  session.
agent: grok
cognitive_load: 3
verification: design-loop-verified
relations:
  - target: wiki/concepts/qmd-semantic-search-requires-llm-backend
    type: supersedes-context
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: depends-on
host: both
---

# QMD patch durability — extend existing patch convention, not wrapper/vendor/swap

## The decision

For durable QMD semantic-search patches (the three documented in
[[qmd-semantic-search-requires-llm-backend]]), **extend the existing
`.patch` + reinstall-protocol convention** rather than introducing a
wrapper script, vendoring, forking, swapping libraries, or rewriting
in-house.

Concretely:

- Add `qmd_cli_main.patch` and `qmd_llm_sentence_tf.patch` next to the
  existing `qmd_fts5_patch.patch` at
  `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/`.
- Extend the wiki CLAUDE.md "Reinstall protocol" paragraph (currently
  documents only the FTS5 patch) to name all three patches with their
  `git apply` lines.
- Add a parametrized verification test
  (`test_qmd_patches_applied.py`) that asserts each patch's marker
  string is present in the installed source.
- Add a Grok-native SessionStart hook at
  `~/.grok/hooks/scripts/qmd_patches_session_start.py` that runs the
  verification check every session start, prints one-line PASS/FAIL/SKIP
  on stderr, and exits 0 (warning, not block). Closes the silent-regression
  gap that the manual-demand protocol alone left open.

## Why this over the alternatives

### Wrapper script (Option A) — rejected

The wrapper would live at `P:/scripts/qmd-search` (a mixed-purpose
directory), require a `$PROFILE` PATH entry, and import
`SentenceTransformerBackend` from `qmd.llm.sentence_tf` — an **internal**
module path not in `qmd.__all__`. That import is the load-bearing piece
of the wrapper, and it's the same fragility class as the original
site-packages patches: code that depends on internal layout that upstream
can change at will.

The wrapper's value proposition ("survives `pip install -U`") also solves
a scenario the operator has explicitly prevented: qmd is pinned at 0.1.1
with a documented "do not auto-upgrade" rule.

### Vendor / fork / library swap / in-house rewrite — rejected (with caveat)

Negative ROI under the round-4 trade-off matrix. Vendoring absorbs the
upstream-death risk (which Option I inherits) but adds a multi-CD-LOC
maintenance surface. Fork is blocked because upstream is unreachable
(GitHub `chengzhag/qmd-py` returns 404 as of 2026-07-20). Library swap
and in-house rewrite are positive-ROI in principle but transition-costly.

**Caveat (R1/R2 from the inline critical friend):** the matrix weighting
("consistent with existing convention" at 3×) may under-credit the
upstream-death risk. If QMD upstream remains unreachable for 12+ months
(the current state), Option I's value proposition decays: the operator
accumulates `.patch` files against a tombstone, and every new bug requires
reverse-engineering against 0.1.1 source the operator doesn't have. An
"exit criteria" section (re-evaluate Option B/F if N+1 patches needed or
upstream unreachable for M months) was identified as a follow-up but not
yet added to the design.

## Why this is durable

The existing convention (`qmd_fts5_patch.patch` + wiki CLAUDE.md reinstall
protocol + qmd pin) has been in place since April 2026 and is documented
in `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/CLAUDE.md`
lines 47-53. Extending it costs ~150 LOC and reuses the operator's
existing mental model: "if you reinstall qmd, re-apply the .patch files
from `__lib/`." The SessionStart hook adds automation the existing
convention lacked.

## Key invariant

**Patches in site-packages are the runtime state; `.patch` files are the
source of truth.** The verification test asserts the runtime state matches
the source of truth. If they diverge, the SessionStart hook reports FAIL
on the next session start — the operator re-applies the `.patch` files per
the wiki CLAUDE.md protocol.

## What this decision does NOT cover

- Upstream is not identified. If `qmd==0.2.0` is ever published, the
  Upgrade Playbook (design §13) governs the transition.
- The broken QMD MCP server is not fixed (zero callers verified at every
  host level — `~/.grok/`, `~/.claude/`, `~/.claude.json`).
- Vendoring / in-house rewrite remain on the table as future options if
  the patch set grows or upstream stays unreachable.

## Falsifier

This decision is wrong if, within 6 months, **any** of:

- QMD upstream renames `qmd.search`'s `llm_backend` parameter AND the
  operator wants to upgrade → `.patch` files cannot be rebased without
  source. (Mitigation: §13 Upgrade Playbook.)
- A new patch site is needed but is not added as a `.patch` file → silent
  regression. (Mitigation: any future QMD patch MUST follow the
  convention; the wiki CLAUDE.md protocol paragraph makes this explicit.)
- The SessionStart hook fails to fire under a future Grok Build config
  change → regression sits undetected. (Mitigation: the hook is
  Grok-native at `~/.grok/hooks/`, the documented surface; verify with
  the negative test in design §11.1 R-6.)
- Upstream remains dead for 12+ months AND a Python breaking change
  requires qmd code modification → patches cannot be re-authored.
  (Mitigation: trigger Option B/F re-evaluation — see open follow-up R2.)

## Implementation status (2026-07-20)

Design loop complete (4 rounds, 33 issues addressed, 0 open). PR plan:

1. **PR-1.5** — Timeout consistency fix in `wiki_contradiction_scan.py`
   (isolated from PR-1 per scope discipline)
2. **PR-1** — Two `.patch` files + wiki CLAUDE.md extension
3. **PR-2** — Verification test + smoke test
4. **PR-4** — Grok-native SessionStart hook
5. **PR-3** — Upstream investigation (secondary, independent)

Recommended merge order: PR-1.5 → PR-1 → PR-2 → PR-4 → PR-3.

## Open follow-ups (critical friend, deferred)

- **R1 (major):** Re-weight the trade-off matrix or justify why
  "consistent with existing convention" dominates "future maintenance
  over 5 years" and "exit cost if QMD upstream dies."
- **R2 (major):** Add §14 "Exit criteria" to the design — trigger
  Option B/F re-evaluation if N+1 patches needed or upstream unreachable
  for M months.
- **R3 (minor):** Hook should default to silent-on-PASS (matching the
  existing `active-surface` hook pattern), print only on FAIL/SKIP.

These are framing improvements, not correctness blockers. The core
architecture is sound and implementation-ready.

## Source

`/design` run `10d616f8` on 2026-07-20. Full design doc was at
`C:/Users/brsth/AppData/Local/Temp/grok-design-10d616f8/grok-design-doc-10d616f8.md`
(OS-reaped temp; copy was not preserved). Review file:
`grok-design-review-10d616f8.md`. Critique file:
`grok-design-critique-10d616f8.md`.
