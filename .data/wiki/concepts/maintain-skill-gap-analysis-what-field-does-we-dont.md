---
title: "Maintain skill gap analysis — what the field does that our /maintain doesn't"
created: 2026-08-08
source: session-019fdf3d
tags: [maintain, skill-design, gap-analysis, workspace-hygiene, maintenance, fleet-management]
summary: >
  /www research comparing our /maintain skill's action classes against what
  the field does (zclean, auto-optimization, LobeHub workspace-hygiene, Ona
  codebase-health-automations). Our skill covers file cleanup, log rotation,
  artifact purge, and handoff audit. The field adds: zombie process cleanup,
  scheduled-job health monitoring, credential rotation awareness, stale branch
  cleanup, complexity auditing of the maintenance system itself, and sentinel-
  file reliability over cron status. Six actionable gaps identified. Extends
  [[fleet-maintenance-skill-design]] with practitioner additions. Complements
  [[check-and-fix-skills-verification-skills-should-fix-what-they-can]].
  Relates to [[sibling-session-collision-dominant-file-loss-vector]].
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://github.com/TheStack-ai/zclean (TheStack-ai, 2026) — zombie process cleanup
  - https://github.com/p3nchan/auto-optimization (p3nchan, 2026) — four-tier scheduled maintenance
  - https://lobehub.com/skills/t2english-cursor-skills-workspace-hygiene (LobeHub, 2026) — workspace-hygiene skill
  - https://ona.com/stories/codebase-health-automations (Ona, 2026) — automated codebase health
  - https://dxrf.com/blog/2026/03/25/identifying-and-cleaning-up-stale-github-repos/ (DXRF, 2026) — stale repo cleanup
relations:
  - target: wiki/concepts/fleet-maintenance-skill-design.md
    type: extends
  - target: wiki/concepts/check-and-fix-skills-verification-skills-should-fix-what-they-can.md
    type: related
  - target: wiki/concepts/sibling-session-collision-dominant-file-loss-vector.md
    type: complements
---

# Maintain skill gap analysis — what the field does that our /maintain doesn't

## Decision context

The operator asked: "What else should we have in our maintain skill? Look at
every class of action we have, and what other people like and suggest."

This is a gap analysis: map our /maintain's action classes against the field's
best practices to identify what we're missing.

## What our /maintain already does (DIAGNOSE + ACT + PREVENT)

| Layer | Action class | What it does |
|---|---|---|
| DIAGNOSE | workspace-health checks | Skills, wiki, git, handoffs, disk, .data/ root |
| ACT | Log rotation | >50MB → .old |
| ACT | .data/ root organization | Telemetry/logs to subdirs |
| ACT | Artifact purge | >7 days, no active session |
| ACT | Temp cleanup | P:/tmp, _tmp_*.py |
| ACT | P:\ root cleanup | Stale JSON/scripts |
| ACT | Handoff audit | >30 days open → flag |
| ACT | Wiki re-index | Concept count drift |
| ACT | Scheduled checks | Upstream PR/issue tracking |
| PREVENT | Growth thresholds | Skill count, wiki count, handoff count |
| PREVENT | File location conventions | Telemetry/logs/skills/scripts locations |
| PREVENT | Claude-ism conformance check | Claude-specific patterns in Grok hooks |

## What the field does that we DON'T (6 gaps)

### Gap 1: Zombie process cleanup (zclean)

**What zclean does:** finds and kills orphaned AI coding runtime processes —
MCP servers, sub-agents, headless browsers, dev servers, Python helpers left
behind when an agent crashes or a terminal closes. Uses dry-run-first, PID
identity verification, and confidence scoring.

**Why it matters for us:** this host runs 15+ concurrent sessions. When a
session crashes (context overflow, quota exhaustion, human abort), it leaves
behind Python processes, MCP servers, and headless browser instances. These
hold memory, ports, and file handles. The operator has no visibility into
zombie accumulation.

**How to add:** a DIAGNOSE check that scans for orphaned processes whose
parent session has ended. Advisory-only initially; operator kills manually.
No auto-kill until precision is measured.

### Gap 2: Scheduled-job health monitoring (auto-optimization)

**What auto-optimization does:** daily script scans `jobs.json` for
`consecutiveErrors > 0`, catching silently failing scheduled jobs. "We
discovered 5 broken jobs only through a manual health check."

**Why it matters for us:** we have scheduler_create items and cron-like jobs.
If one fails silently, nobody notices until the operator wonders why a
monthly task didn't run.

**How to add:** a DIAGNOSE check that scans the Grok Build scheduler
(`scheduler_list`) for jobs with recent failures. Advisory output.

### Gap 3: Sentinel-file reliability over cron status (auto-optimization)

**What auto-optimization discovered:** "Checking 'did the job write its
success marker?' is more reliable than checking 'did cron run the job?'
because cron can run a job that fails silently."

**Why it matters for us:** /maintain's scheduled_checks.py tracks job status,
but doesn't verify the job actually produced output. A scheduled job that
"ran" but produced no artifact is a silent failure.

**How to add:** after each scheduled_check, verify the expected output file
exists and is non-empty. If missing → flag as "ran but produced no output."

### Gap 4: Complexity auditing of the maintenance system itself (auto-optimization)

**What auto-optimization does:** "The maintenance system itself needs limits.
We set hard caps on the rules file (250 lines), maintenance directory
(15 files), and cron jobs (5). When the system to maintain the system gets
too complex, it's time to simplify."

**Why it matters for us:** our /maintain SKILL.md is 460 lines. The
scheduled_checks.json grows. The maintenance system could itself become
the bloat problem.

**How to add:** a PREVENT check: if /maintain SKILL.md exceeds 500 lines,
or scheduled_checks.json has >20 items, flag for simplification.

### Gap 5: Stale worktree cleanup (Claude Code changelog, zclean)

**What Claude Code does:** "Stale worktree cleanup removes worktrees whose
PR was squash-merged." zclean detects abandoned worktrees from crashed
sessions.

**Why it matters for us:** we use worktrees for /go implementation waves and
/refactor seams. When a session crashes mid-worktree, the worktree stays.
The /go skill checks worktree lifecycle receipts at GO DONE, but if the
session crashes before GO DONE, the worktree is orphaned.

**How to add:** a DIAGNOSE check: `git worktree list` → flag worktrees with
no active session and no recent activity (>7 days). Advisory output.

### Gap 6: Error deduplication to prevent alert fatigue (auto-optimization)

**What auto-optimization does:** "Same warning pattern suppressed until 3rd
consecutive occurrence, preventing alert blindness. Without dedup, a
non-critical warning fires every hour forever."

**Why it matters for us:** our /maintain runs monthly. But growth thresholds
and convention violations fire every run even when nothing changed. The
operator learns to ignore them — the same "prose ceiling" problem applied
to advisory output.

**How to add:** record the last N maintenance reports. If a finding is
identical to the prior run's finding, suppress it (or mark "unchanged from
prior run"). Only surface NEW findings or findings that changed severity.

## What the field does that we ALREADY do better

| Capability | Our /maintain | Field equivalent |
|---|---|---|
| File cleanup | ✅ .data/ root, P:\ root, temp, artifacts | zclean: cache dirs only |
| Log rotation | ✅ 50MB threshold | auto-optimization: 14-day TTL (we have both) |
| Growth thresholds | ✅ skill count, wiki count, handoff count | auto-optimization: file count, memory note count |
| Handoff audit | ✅ >30 days open | None in field (our unique capability) |
| Scheduled checks | ✅ upstream PR/issue tracking | auto-optimization: cron health (different scope) |
| Fleet-aware isolation | ✅ never touch current terminal | zclean: protects active parent sessions |
| Composition with other skills | ✅ delegates to workspace-health/skill-prune | auto-optimization: standalone scripts |

## What this means for our workspace

The six gaps are additive — each fits into an existing layer (DIAGNOSE,
ACT, or PREVENT) without restructuring the skill:

| Gap | Layer | Effort | Priority |
|---|---|---|---|
| 1 — Zombie processes | DIAGNOSE | ~1 hour (process scan script) | HIGH — 15+ sessions, orphans accumulate |
| 2 — Scheduled-job health | DIAGNOSE | ~30 min (scheduler_list scan) | MEDIUM — few scheduled jobs currently |
| 3 — Sentinel reliability | DIAGNOSE | ~30 min (output-file check) | MEDIUM — only matters when jobs fail |
| 4 — Self-complexity audit | PREVENT | ~15 min (line count + item count) | LOW — 460 lines is under threshold |
| 5 — Stale worktree cleanup | DIAGNOSE | ~30 min (git worktree list scan) | HIGH — worktrees accumulate from crashes |
| 6 — Error dedup | PREVENT | ~45 min (report diff) | MEDIUM — prevents alert fatigue |

**Priority:** gaps 1 (zombie processes) and 5 (stale worktrees) are the
highest-leverage additions — they address real workspace degradation that
the operator currently has no visibility into.

## Falsifier

These gaps are not real if: (a) zombie processes don't accumulate on this
host (measure: scan for orphaned processes whose parent session has ended);
(b) stale worktrees are already cleaned by another mechanism (check: git
worktree list shows no orphans); (c) the operator doesn't experience alert
fatigue from repeated maintenance findings (ask: "do you skip the growth
threshold section because it never changes?").

## Sources

- [zclean (TheStack-ai, 2026)](https://github.com/TheStack-ai/zclean) — AI coding runtime hygiene: zombie process cleanup, confidence scoring, dry-run-first
- [auto-optimization (p3nchan, 2026)](https://github.com/p3nchan/auto-optimization) — Four-tier scheduled maintenance: scripts do deterministic work, AI handles judgment; sentinel files, error dedup, self-complexity limits
- [LobeHub workspace-hygiene skill](https://lobehub.com/skills/t2english-cursor-skills-workspace-hygiene) — Quick Sweep + Deep Clean modes; archives completed feature specs
- [Ona codebase-health-automations](https://ona.com/stories/codebase-health-automations) — Auto-remediate CVEs, close stale PRs, remove dead feature flags
- [DXRF stale repo cleanup](https://dxrf.com/blog/2026/03/25/identifying-and-cleaning-up-stale-github-repos/) — Auditing thousands of repos at scale

## Receipts

- `~/.grok/skills/maintain/SKILL.md` — current /maintain (460 lines, three-layer architecture)
- `P:/.data/wiki/concepts/fleet-maintenance-skill-design.md` — original /www research (2026-07-28)

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[research-applicability-checking-dont-cite-without-verifying-assumptions]]
- [[deep-research-systems-and-web-upgrade]]
- [[research-vs-design-vs-architect-skills-and-www-self-assessment]]

