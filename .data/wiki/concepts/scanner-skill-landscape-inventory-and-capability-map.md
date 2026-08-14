---
title: "Scanner skill landscape: inventory and capability map"
created: 2026-08-13
source: session-019ffc5c
tags: [scanner, skill-landscape, capability-map, inventory, todo, insight, review, check, risk, discovery, fmea, trace, aar, why]
agent: grok
host: grok
cognitive_load: 3
verification: workspace_verified
summary: >
  Complete inventory of all scanning skills in the fleet, organized by
  domain. Each entry documents what the skill scans, how (mechanical vs
  LLM), and what it feeds. The skill dependency graph (skill-graph.md)
  cannot represent scanning relationships — only capability nodes can.
  This concept serves as the human-readable map; the corresponding
  capability nodes (scan-workspace-state, scan-code-quality, scan-session-
  transcript, scan-risk) serve as the machine-readable contracts.
relations:
  - target: wiki/concepts/capability-node-architecture.md
    type: extends
  - target: wiki/concepts/skill-graph-representational-limits.md
    type: documents-gap
  - target: wiki/concepts/scanner-to-handoff-gap-discovered-work-not-persisted.md
    type: related
  - target: wiki/concepts/scanner-driven-error-detection-mechanical-layer.md
    type: related
  - target: wiki/concepts/discover-first-prompt-patterns-for-unbiased-work-item-discovery.md
    type: related
---

# Scanner skill landscape: inventory and capability map

## Why this exists

The skill dependency graph (`skill-graph.md`) represents who-calls-who and
what-provider-is-used. It **cannot** represent: what does each skill scan?
Which scanner feeds `/todo`? What's the overlap between `/insight` and
`/aar` on transcript scanning? This concept fills that gap with a
human-readable inventory plus machine-readable capability nodes.

## The scanning domains

Every scanning skill falls into one of 7 domains. A skill may span domains
(e.g., `/todo` is both workspace-state and session-transcript).

### 1. Workspace state (what's open in the filesystem)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/todo` Step 0 | 16 sources: handoffs, git, review, check, critique, research, debt, wiki_markers, dreams, transcript patterns, user_problems, finding_coverage, dangerous_python_c, tool_failures, protocol_violation, skill_scripts, propagation | `scan_functions.py` + `scan_transcript.py` (mechanical regex, ~5 min) | `/todo` output list |
| `/maintain` | Git state, skill catalog, wiki vault, config, hook dispatch, plugin enable-state | Composable checks (DIAGNOSE/ACT/PREVENT) | Fleet health report |
| `/skill-prune` | Skill catalog + wiki concepts for stale, duplicate, drifted entries | Grep + LLM | Merge/archive/promote proposals |

### 2. Code quality (is the code correct?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/review` | Local diff, branch, PR, or package path — correctness, integrity, maintainability, security, architecture | Multi-model parallel review | FINDINGS.md on disk |
| `/check` | Session work for verification completeness | Session-scoped scan | PASS/FAIL verdict |
| `/grok-verify` | Code changes for scope, tests, runtime path | Evidence-first gate | Block or allow "done" |
| `/trace` | Code/skills/workflows/documents for logic errors | Manual trace-through with state tables | Findings list |

### 3. Session transcript (what happened in the conversation?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/todo` Step 0.5 | Session transcript for unactioned items, tacit knowledge, friction, near-misses | Parallel `/insight` + `/aar` subagents (LLM) | Merged into `/todo` output |
| `/insight` | 10 categories: corrections, friction, decisions, gaps, near-misses, successes, unactioned items, unverified assertions, cognitive load | LLM reads transcript | Dual-stream routing (knowledge vs improvement) |
| `/aar` | Session for value accounting, episode ledger, root causes, opportunities, uncaptured knowledge | Evidence-grounded reconstruction | AAR report + handoffs |
| `/triage` | Session output for blockers, errors, inefficiencies, risks, opportunities | Category-bounded review | Structured findings |

### 4. Discovery (what exists before we change it?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/preflight` | Existing implementations, callers, registrations, state consumers, caches, tests, worktrees, competing plans | `discovery_audit.py` evidence packet | Evidence packet (JSON) |
| `/grok-discovery` | Same as `/preflight` (shared infrastructure) | Same | Same |

### 5. Risk (what could go wrong?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/risk` | Code diff, plan, decision, config change, commit | Adaptive: inline scan → critique → attack specialists | Risk assessment report |
| `/tp` | Decision, proposal, design, direction for framing flaws | Two-lens critical-friend (fresh subagent + synthesis) | PROCEED/REVISE/BLOCK verdict |

### 6. Pipeline/process (is the pipeline safe?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/fmea` | Python pipeline scripts for I/O boundaries, external APIs, state files, subprocess calls | FMEA table per boundary (severity × occurrence × detection) | FMEA report |
| `/doc-check` | Diff/commits against README, CHANGELOG, ADRs, docstrings, broken links, wikilink resolution | Documentation readiness check | Findings list |

### 7. Root cause (why did this fail?)

| Skill | What it scans | How | Feeds into |
|-------|--------------|-----|------------|
| `/why` | A specific failure for root cause | Evidence-tiered RCA with wiki pattern query | Root cause analysis |
| `/behave` | Past incidents for verdict-transition integrity | Post-hoc diagnostic | Behavioral assessment |

## The aggregation hub

`/todo` is the aggregation hub for workspace-state + session-transcript
scanning. It reads from 16 mechanical sources (Step 0) AND invokes two
LLM-based depth scanners (`/insight` + `/aar`) as parallel subagents
(Step 0.5). No other skill aggregates across both domains.

## Capability nodes for scanning relationships

The following capability nodes make scanning relationships machine-readable
(so `/ask`, `/todo`, and future routing skills can query them):

| Node | What it represents | Created |
|------|-------------------|---------|
| `scan-workspace-state` | Scanning filesystem for open work (handoffs, git, review, etc.) | ✅ This session |
| `scan-code-quality` | Scanning code diffs/files for defects, correctness, coverage | ✅ This session |
| `scan-session-transcript` | Scanning conversation for unactioned items, tacit knowledge, friction | ✅ This session |
| `scan-risk` | Scanning changes/proposals for what could go wrong | ✅ This session |

Skills that provide these capabilities declare them in frontmatter:
`provides: [scan-workspace-state, scan-session-transcript]`. The graph
script reads this as ground truth.

## Scanner overlap map (deduplication)

Three skills scan the session transcript: `/todo` Step 0.5, `/insight`,
and `/aar`. The division of labor:

| Scanner | Focus | Overlap with others |
|---------|-------|-------------------|
| `/todo` Step 0 `/insight` subagent | Categories 4, 5, 8, 9 (gaps, near-miss, unactioned, unverified) | Deduplicates against scanner output before merging |
| `/todo` Step 0 `/aar` subagent | Phase 2 open defects, Phase 5 unrealized value, Phase 6 opportunities, Phase 8.5 tacit knowledge | Deduplicates against scanner output before merging |
| `/insight` standalone | All 10 categories, dual-stream routing, coverage check | When invoked standalone (not via `/todo`), runs the full scan |
| `/aar` standalone | Full evidence-grounded reconstruction | When invoked standalone, writes full report + wiki promotion |

The deduplication happens at the `/todo` merge step (Step 0.5.6): findings
that duplicate scanner items are skipped. Only net-new findings enter the
output list.

## Falsifier

This inventory is wrong if:
- A scanning skill exists that isn't listed here (inventory incomplete)
- A skill listed here doesn't actually scan (false classification)
- The overlap map is wrong (skills produce more or less overlap than documented)
- The capability nodes don't get consumed by `/ask` or routing (nodes are dead weight)

## Auto-related

- [[close-scanner-unavailable-fallback-session-observations-handoff]]
- [[skill-graph]]
- [[claude-https-code]]
- [[mechanical-as-input-not-mechanical-as-frame]]
- [[coupling-inventory-as-mandatory-design-section]]

