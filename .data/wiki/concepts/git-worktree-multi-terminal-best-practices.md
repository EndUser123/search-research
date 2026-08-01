---
title: "Git worktree best practices for multi-terminal AI fleets: do's, don'ts, alternatives"
created: 2026-07-21
source: session-2026-07-21
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
tags: [worktrees, git, multi-terminal, parallel-development, ai-agents, isolation, best-practices, alternatives]
summary: >
  Holistic guide to using git worktrees in a multi-terminal / multi-agent environment.
  Synthesizes official git docs, practitioner blogs (small/medium repos), and one
  large-monorepo skeptical source. Confirms worktrees as the right tool for multi-terminal
  AI fleets, surfaces the dependency-install bottleneck (the real cost), and compares
  alternatives (stash, clones, GitButler virtual branches, containers, pre-warmed pools).
  The unique value is the disconfirmation + alternatives analysis, not the basics.

---

# Git worktree best practices for multi-terminal AI fleets

## Context

The wiki already documents worktree *failure modes* — [[worktree-writes-dont-sync-to-canonical]],
[[auto-commit-authority-isolation]] (ADR-008 worktree-per-session), [[file-edit-failures-two-classes]],
[[mcp-server-sharing-multi-terminal]]. What was missing: the holistic "when to use worktrees,
how to organize them, what the alternatives are, and where they bite back" concept. This page
fills that gap, grounded in 7 external sources scored via CREDIBLE-lite (all ≥8/12).

## When worktrees are the right answer `[HIGH confidence, multi-source]`

| Signal | Use worktrees? | Source |
|---|---|---|
| ≥2 terminals/agents working the same repo concurrently | **Yes** — structural isolation is the point | git-scm.com, ADR-008 |
| Long-running task blocks starting a new task | **Yes** — each gets its own branch + working dir | understandingdata.com, itdepends.be |
| Speculative work / A-B comparison / throwaway spike | **Yes** — failed experiments delete cleanly | understandingdata.com |
| Single terminal, quick context switch (<1h) | **No** — `git stash` is lighter | reifenrath.dev, joshtune.com |
| Human in one IDE splitting changes into multiple PRs | **No** — GitButler virtual branches have less friction | blog.gitbutler.com |
| Need fully isolated `.git` / different OS / different toolchain | **No** — use full clones or containers | stackoverflow, general consensus |

**Decision rule (from joshtune.com):** use worktrees when you want *parallel focus* (two branches
at once) and you're okay managing multiple folders. Skip them if your tooling or dependency setup
gets messy with duplicate installs.

## Do's `[HIGH confidence]`

1. **One worktree per thread of work, per terminal.** Never share a worktree across concurrent
   sessions. Sharing reintroduces the collision you were trying to avoid. (ADR-008, joshtune)
2. **Consistent naming: `../<repo>-<type>-<description>`** (e.g., `../myapp-agent-auth`,
   `../myapp-exp-graphql`, `../myapp-review-pr-123`). Makes `git worktree list` scannable.
   (understandingdata.com, mskadu.medium)
3. **Create worktree + new branch in one step**: `git worktree add -b feature/X ../path`. Avoids
   the "branch already checked out elsewhere" error. (GitButler, understandingdata)
4. **Remove via `git worktree remove`, never `rm -rf`**; follow with `git worktree prune`.
   Manual deletion leaves stale refs in `.git/worktrees/<name>/` that corrupt future operations.
   (joshtune, official docs)
5. **For durable artifacts (wiki, handoffs, ADRs), write via absolute paths that resolve to the
   canonical workspace**, not worktree-relative paths. This is the lesson of
   [[worktree-writes-dont-sync-to-canonical]]. Worktree writes do not propagate.
6. **Isolate mutable shared state per-worktree**: separate DB connections
   (`DATABASE_URL=...myapp_${PWD##*/}`), separate ports (`PORT=3000+N`). The #1 runtime conflict
   in parallel worktrees is shared DB/port. (understandingdata, direnv pattern)
7. **Keep `.env` shared (symlink)** but `node_modules`/`.venv`/build artifacts per-worktree.
   Config is constant; deps may diverge per branch.
8. **For fleets: build a tiny `wt` helper** (PowerShell function) that creates worktree + opens
   new terminal tab + launches the agent in one command. The itdepends.be post has working
   PowerShell + Nushell scripts; daveschumaker built a `wt` CLI. Removes friction; "spin up a
   parallel agent" becomes 2 seconds, not 30.
9. **Periodic `git worktree prune` + `git worktree list` audit.** Stale worktrees accumulate
   disk + metadata; pool slots drift behind `main`. (joshtune, daveschumaker)

## Don'ts `[HIGH confidence]`

| Don't | Symptom | Source |
|---|---|---|
| Delete the worktree folder by hand | Stale `.git/worktrees/<name>` entries; confusing `git worktree list` | joshtune, official docs |
| Check out the same branch in two worktrees | Hard error: `'feature/X' is already checked out at '...'`. Use `-b new` or `--detach` | official docs, HN |
| Reuse generic branch names (`temp`, `test`, `wip`) across worktrees | You will forget which is which; `git worktree list` becomes useless | understandingdata, daveschumaker |
| Symlink `node_modules`/`.venv` from main in dep-heavy repos | Vitest/Vite/Python module resolution follows symlinks and breaks | daveschumaker |
| Let worktrees share a DB connection or port | Silent data corruption; one agent's test writes visible to another | understandingdata |
| Write durable artifacts to worktree-relative paths | Wiki pages/handoffs vanish when worktree is removed — see [[worktree-writes-dont-sync-to-canonical]] | local wiki (2026-07-19 incident) |
| Accumulate stale worktrees "in case I need them" | Disk exhaustion; pool drift; merge-conflict surface grows | daveschumaker, joshtune |
| Treat worktrees as a substitute for merging discipline | "Isolation makes merge conflicts invisible until merge time" — Scott Chacon | GitButler |

## The dependency-install bottleneck (the real cost) `[HIGH confidence, named numbers]`

The most cited disconfirmation: in dependency-heavy repos (JS monorepos, 750k+ files in
`node_modules`), **the worktree itself is instant; the `yarn install` / `npm ci` / `pip install`
per fresh worktree is the bottleneck** (daveschumaker, ~10 min per worktree in a Yarn workspaces
monorepo).

Failed approaches daveschaker documented:
- **Symlinked `node_modules`** — breaks Vitest/Vite module resolution
- **Yarn `hardlinks-global` mode** — still creates 750k filesystem entries; file-count is the bottleneck, not bytes
- **APFS copy-on-write (`cp -c`)** — same problem; metadata operations dominate

**Resolution for the P:\ fleet:** this is a **scope disagreement keyed on repo size + dep weight**.
P:\ is mixed Python/MD with no 750k-file dep tree. **Create-on-demand is optimal here** — your
bottleneck is model inference, not dep install. The pre-warmed pool pattern (daveschumaker's `wt`,
or `git-stint`) is the right answer only when `install` dominates.

## Alternatives comparison

| Alternative | When it beats worktrees | When worktrees win |
|---|---|---|
| `git stash` | Quick context switch (<1h), single terminal, coming right back | Anything parallel or long-running |
| WIP commit on a branch | Want a recoverable checkpoint; single terminal | You'd accumulate dozens of WIP commits across N terminals |
| Multiple full clones | Need fully isolated `.git` (rare); air-gapped experiments | Always — worktrees share `.git`, strictly cheaper |
| GitButler virtual branches | Human in one IDE splitting changes into multiple PRs | Any multi-process scenario (AI agents, dev servers, separate dep trees) |
| Work Trunk / similar UX-layer tools | Want parallel-branch freedom without learning worktree mechanics | Need real filesystem isolation |
| Containers (docker/devcontainer) | Need full environment isolation (different OS, different toolchain) | Overkill for branch isolation; slower to spin up |
| **Pre-warmed worktree pool** (`wt` CLI, `git-stint`) | Large monorepo where `install` dominates | Small/medium repos where install is trivial — adds complexity for no gain |

**Bottom line for the P:\ fleet:** nothing beats worktrees. The alternatives either trade away
real isolation (stash, virtual branches) or add cost without benefit (containers, full clones).
The one alternative worth watching is `git-stint` (reddit.com/r/git/comments/1rj1wev) — it
automates the worktree+branch lifecycle at fleet scale.

## Conflicts in the literature

**⚠️ Lifecycle strategy — create-on-demand vs pre-warmed pool:**
- *Create-on-demand, delete-when-done* (understandingdata, itdepends): clean, tidy, works in small/medium repos.
- *Pre-warmed pool of recycled worktrees* (daveschumaker): 6 fixed slots with deps pre-installed, rotate branches through them, only reinstall when lockfile changes.
- **Resolution:** scope disagreement keyed on repo size. Both are correct for their scope.

**⚠️ GitButler virtual branches vs worktrees:**
- Scott Chacon (GitHub co-founder) argues virtual branches have less friction for "two files → two branches from one working dir."
- He concedes worktrees win when you need process-level isolation (separate dev servers, AI agents, separate dep trees).
- **Resolution:** for multi-terminal AI fleets, worktrees unambiguously win — virtual branches are a human-in-one-IDE tool, not a multi-process tool.

## Fleet-specific notes (ahead of public literature)

- Public sources top out at ~5 parallel agents. ADR-008's "worktree-per-session architecture"
  is already ahead of the public literature for >10 concurrent agents.
- Windows-specific gotchas (junction/symlink-vs-worktree interaction) are better covered in the
  local wiki ([[windows-gitbash-hook-invocation]]) than in any external source found.
- For the auto-commit authority problem (concurrent sessions on the same repo), worktree-per-session
  is the structural fix; [[auto-commit-authority-isolation]] is the bridge until ADR-008 enforcement ships.

## Related

- [[worktree-writes-dont-sync-to-canonical]]@supports — the missing-artifact failure mode this page prevents
- [[auto-commit-authority-isolation]]@supports — concurrent-session fail-closed; worktrees are the structural fix
- [[file-edit-failures-two-classes]]@related — atomic write ≠ collision protection; worktrees sidestep the multi-writer problem
- [[mcp-server-sharing-multi-terminal]]@related — what to share vs isolate per terminal (analogous decision)
- [[windows-gitbash-hook-invocation]]@related — Windows-specific git behaviors relevant to worktree operations

## Sources

- Official git docs: https://git-scm.com/docs/git-worktree (git-worktree 2.54.0, 2026-04-20) — authority=3, recency=3, evidence=3, bias=3 → **12/12**
- Scott Chacon (GitHub co-founder), GitButler: https://blog.gitbutler.com/git-worktrees (2024-03-04) — **10/12** (mild vendor bias toward GitButler virtual branches)
- James Phoenix, understandingdata.com: https://understandingdata.com/posts/git-worktrees-parallel-dev/ (2026-07) — **10/12** (practitioner + AI agents, mild book-promo bias)
- itdepends.be: https://blog.itdepends.be/parallel-workflows-git-worktrees-agents/ (2025-11-08) — **10/12** (decade of worktree use, working PS+Nushell scripts)
- Josh Tune: https://joshtune.com/posts/git-worktree-pros-cons/ (2026-01-18) — **10/12** (clean pros/cons/gotchas)
- Dave Schumaker: https://daveschumaker.net/use-git-worktrees-they-said-itll-be-fun-they-said/ (2026-03-14, updated 2026-05-05) — **11/12** (large-monorepo skeptic; named numbers; documented failed approaches)
- René Reifenrath: https://blog.reifenrath.dev/the-ultimate-guide-to-git-multitasking-58b2970b5b22 (2025-06) — **8/12** (partial — Medium paywall, only intro read)
- HN thread on the "can't checkout same commit twice" gotcha: https://news.ycombinator.com/item?id=39596742 — community signal
- `git-stint` (worktree/branch lifecycle automation for parallel AI coding): https://www.reddit.com/r/git/comments/1rj1wev/gitstint_automates_worktree_and_branch_lifecycle/

**Source diversity:** 1 official, 1 vendor-with-alternative, 5 independent practitioners (including 1 large-monorepo skeptic), 2 community threads. No LOW-QUALITY sources.

## Provenance

Researched via `/www` (wiki-web-wiki compound skill) on 2026-07-21 in Grok Build session
019f8082. Phase 1 (wiki query) surfaced 7 related concepts, all failure-mode-specific — no
holistic concept existed. Phase 2 (web research): 5 parallel searches across minimax-search
and firecrawl, 7 sources scraped, CREDIBLE-lite scored, 2 conflicts detected and resolved.
Phase 2 synthesis: parent-inherited model. Phase 3: this page.

## Auto-related

- [[auto-commit-authority-isolation]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
