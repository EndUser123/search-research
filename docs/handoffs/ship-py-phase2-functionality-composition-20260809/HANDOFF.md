# Handoff — ship-py Phase 2: functionality composition improvements

## Status
OPEN — design + implementation. Phase 1 (defect fixes) is DONE; this is Phase 2 (feature composition).

## Objective

Wire ship-py to compose with existing workspace skills/plugins at each pipeline phase.
Phase 1 (abort subcommand, secret-scan phase, verdict staleness, hook I/O hardening,
review-found merge-unreachable bug) shipped in session 019fe403. Phase 2 is about
making ship-py *more valuable* by leveraging tools the fleet already has.

## What Phase 1 shipped (context)

- `0ae38d3` abort subcommand + aborted phase gate
- `b0ad5af` secret-scan phase (gitleaks, 14-phase pipeline)
- `a4e6fb5` verdict staleness HEAD check + hook concurrent-I/O hardening
- `dbc0f0c` fix: merge-unreachable bug (verdict set phase="complete") + secret_scan fail-open masking
- `fe8fc40` ruff format (auto-fix phase)
- `14e3802` SKILL.md 14-phase docs + 8 Phase 1 feature tests (55 total passing)

## Phase 2 workstream (4 items, each needs a spike before wiring)

### P2-1: Wire review-relay into the review phase

**Current:** review phase spawns 2 generic agents, collects findings. Same-model, same-blind-spots, no convergence protocol.

**Target:** ship-py review phase calls review-relay for multi-model convergence (immutable snapshots, bounded turns, leases, explicit convergence/divergence signal, parent verification).

**Spike needed (S effort):**
- Read `~/.grok/skills/review-relay/SKILL.md` for its dispatch contract
- Understand how bounded-turn protocol interacts with ship-py's pause_for pattern
- Determine if review-relay's snapshot/lease model fits the orchestrator's polling loop
- Check capability_mode concern (review agents currently have execute — does review-relay change this?)

**Implementation (M effort):**
- Add a `--review-backend` flag to the review phase (default: current spawn model; optional: review-relay)
- When review-relay is selected, dispatch through it instead of spawning directly
- Record review-relay's convergence signal in state["review_convergence"]

### P2-2: Integrate version-bump into the publish phase

**Current:** publish phase is `git push origin main` + optional `--tag`. No semver, no manifest sync, no changelog, no GitHub release.

**Target:** publish phase calls the claude-mem `version-bump` skill for full release lifecycle.

**Spike needed (S effort):**
- Read `version-bump` SKILL.md to understand its manifest assumptions (npm? plugin.json?)
- Verify it handles this workspace's package structure (P:/packages, ~/.grok/skills, plugin manifests)
- Determine what args it needs (version bump type? tag name?)

**Implementation (M effort):**
- Add version-bump invocation before `git push` in cmd_publish
- Pass the appropriate version-bump type (patch/minor/major) from detect-phase analysis
- Record version-bump output in state["publish_results"]

### P2-3: Add /why grounding to the fix phase

**Current:** fix phase spawns a fix agent that does symptomatic patches.

**Target:** fix agent queries the wiki for known failure patterns before proposing fixes.

**Spike needed (S effort):**
- Read `/why` SKILL.md to understand its wiki-query interface
- Design the prompt that the fix phase gives to the spawned fix agent
- Determine how /why's findings integrate into the fix-loop state

**Implementation (M effort):**
- Modify the fix-phase pause instruction to include /why grounding
- The fix agent runs /why first, then proposes fixes informed by wiki patterns
- Record which wiki patterns informed each fix in state["fix_patterns_consulted"]

### P2-4: Add pr-babysit post-publish loop

**Current:** pipeline stops at publish. CI failures, review comments, and merge conflicts are unhandled.

**Target:** optional post-publish phase that invokes pr-babysit to close the loop.

**Spike needed (S effort):**
- Read `pr-babysit` SKILL.md for its monitoring contract
- Determine if it works for direct-to-main pushes or only PRs
- Check if it needs a GitHub PR number or can auto-detect

**Implementation (M effort):**
- Add an optional `babysit` phase after publish in PHASE_ORDER
- Only runs when `--babysit` flag is passed to run-all or publish
- Invokes pr-babysit with the pushed branch/commit info

## Remaining Phase 1 items (from review agent 1 findings)

These are lower-severity items the review agent found that weren't fixed in Phase 1:

- **all_merged mis-capture** (merge.py:153) — mixed skip+merge case produces false failure
- **abort_at timestamp** (abort.py:40) — uses _saved_at instead of wall-clock
- **missing cwd on gitleaks subprocess** (secret_scan.py:124) — relative path resolution issue
- **gitleaks fail-open risk** — missing binary silently disables secret gate in automated runs

## Acceptance criteria

- Each P2 item ships with a spike (read the target skill, verify compatibility) before implementation
- Tests cover the new composition (mock the target skill's interface)
- SKILL.md documents the new flags/modes
- Integration test: run the full pipeline with each composition enabled
