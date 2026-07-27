---
thread_id: review-consolidation-20260727
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T21:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 97ed62d
---

# Enhance /review and consolidate review-type skills

## Objective

Enhance `/review` as the primary review engine and consolidate the overlapping review-type skills, plugins, and Claude-only aliases into a coherent routing system so the operator never has to guess which review tool to use.

## Status

OPEN — scoping complete; ready for a fresh session to design + implement.

## Producing context

Date: 2026-07-27. Session: 019fa48a. Host: Grok Build.

## Read-first list

1. `C:/Users/brsth/.grok/skills/review/SKILL.md` — the current /review skill (the primary engine to enhance)
2. `C:/Users/brsth/.grok/skills/check/SKILL.md` — session-grounded verification (complementary, not redundant)
3. `P:/.data/wiki/concepts/skill-domain-map.md` — Domain 5 (Review/Audit) shows 4 Grok skills + 3 Claude-only gaps
4. `C:/Users/brsth/.grok/AGENTS.md` § "Review skill routing" — the routing table the operator already uses
5. `C:/Users/brsth/.grok/AGENTS.md` § "Proactive verification suggestions" — when to suggest /check vs /review
6. `P:/.artifacts/grok-build-terminal/grok-review/packet/20260727-154541/FINDINGS.md` — the /review run from this session (demonstrates the current pipeline)

## The problem (decomposed)

### Track A: Enhance /review

The current `/review` skill is strong (multi-agent specialists, verify pass, FINDINGS.md on disk, root-cause clustering). But it has gaps:

- **No `--second-opinion` cross-model integration** — the skill describes it (Step 5.5) but it's not wired to `/agy`, `/codex`, `/mmx`
- **No automatic specialist model selection** — it should query the wiki pool (like `/tp` does) rather than inheriting parent Grok
- **CORR fixes from this session's earlier /review run are not yet applied** to the skills reviewed (the /packet bugs are documented but not fixed)
- **No "review the reviewer" loop** — when /review produces findings, there's no automatic check that the findings themselves are correct

### Track B: Consolidate overlapping review tools

The workspace has **many** review-type skills across Grok, Claude, and plugins:

| Skill | Scope | Host | Overlap with /review |
|---|---|---|---|
| `/review` | Code/package review with verified findings | Grok ✓ | **The primary** |
| `/check` | Session-grounded verification ("did I do what I said?") | Grok ✓ | Complementary — NOT redundant (see wiki `check-vs-review-complementary-not-redundant.md`) |
| `/red-team` | Adversarial multi-perspective review | Grok ✓ | Heavier than /review; `/review --adversarial` already absorbs this |
| `/tp` | Critical-friend premise critique | Grok ✓ | Different posture (dialogue, not artifact) |
| `/code-review` | Claude Code PR review | Claude-only | Alias absorbed by /review per AGENTS.md routing table |
| `/code-review-and-quality` | Multi-axis code review | .agents | Overlaps /review lenses |
| `code-review` (plugin) | Claude Code Review (Team/Enterprise) | Claude-only | Paid product pattern /review copies from |
| `requesting-code-review` | Post-implementation review trigger | superpowers | Workflow trigger, not a review engine |
| `receiving-code-review` | Process review feedback | superpowers | Workflow handler, not a review engine |
| `verification-before-completion` | Pre-claim verification | superpowers + .agents | Overlaps /check |
| `review_bundle` | Decision-ready review bundles for external architectural review | Claude-only | Overlaps /review Step 6 (durable copy) |
| `risks` | Fast pessimistic pass on un-actioned proposal | Claude-only | Overlaps /red-team pessimistic-pass mode |
| `review-pr` | Multi-agent PR review (Claude) | Claude-only | DEPRECATED already; absorbed by /review |
| `skill-audit` | Audit skill against quality rubric | Claude-only | Worth porting for /skill-prune |
| `epistemic-check` | Validate Q&A against epistemic contract | Claude-only | Niche; defer |
| `sqa` | 11-layer sequential quality analysis | Claude-only | Heavy; defer |

**The consolidation decision:** which of these should /review absorb, which stay independent, and which get deprecated/aliased?

### Track C: Routing clarity

The operator already has a routing table in AGENTS.md (`/review` for code, `/check` for session verification, `/tp` for framing, `/red-team` for adversarial). But:

- `/code-review` is listed as an alias for `/review` — is this wired?
- `/check` auto-escalates to `/review` when triggers fire — is the handoff clean?
- The superpowers `verification-before-completion` overlaps `/check` — should it be deprecated?

## Verified facts

- [FACT] `/review` SKILL.md already documents `--adversarial` mode that absorbs `/red-team` functionality (read this session)
- [FACT] `/review` SKILL.md already documents `--second-opinion` for cross-model critique (Step 5.5) but it's not wired to the CLI dispatch skills
- [FACT] `/check` SKILL.md auto-escalates to `/review` when load-bearing triggers fire (Step 6.2)
- [FACT] AGENTS.md has a "Review skill routing" table that already maps user intent → skill
- [FACT] Domain 5 (Review/Audit) has 4 Grok skills enabled + 3 Claude-only gaps (`skill-audit`, `sqa`, `epistemic-check`)
- [FACT] The `/review` run this session produced verified findings with root-cause clustering (FINDINGS.md at the run_dir)

## Task packets

### RC-01: Wire `--second-opinion` to CLI dispatch skills

- **goal:** When `--second-opinion` is passed, /review dispatches to `/agy`, `/codex`, or `/mmx` for cross-model critique, writing results to `run_dir/critics/`
- **in scope:** /review SKILL.md Step 5.5, the conductor pattern from `/agy`/`/codex`/`/mmx` skills
- **out of scope:** changing the specialist spawn pool (that's /tp's domain)
- **acceptance:** `/review --second-opinion` produces at least one critic file under `run_dir/critics/` from a non-Grok model
- **falsifier:** `--second-opinion` fails silently or produces no critic files

### RC-02: Add automatic specialist model selection

- **goal:** /review queries the wiki pool for specialist models (like /tp Step 2a) instead of inheriting parent Grok for all specialists
- **in scope:** /review Step 4 specialist spawning
- **out of scope:** the pool itself (managed by /tp's wiki-driven selection)
- **acceptance:** specialists run on non-parent models when available; fallback to parent-inherited is disclosed
- **falsifier:** all specialists run on parent-inherited model despite pool members being available

### RC-03: Consolidate review routing

- **goal:** Formalize which review tools are primary, alias, or deprecated
- **in scope:** AGENTS.md routing table, skill descriptions, deprecation notices
- **out of scope:** removing skills (deprecation notices only; physical removal is operator-gated)
- **acceptance:** a fresh session reading AGENTS.md knows unambiguously which review tool to use for each intent
- **falsifier:** operator asks "which review tool should I use?" and the routing table doesn't answer

### RC-04: Port `skill-audit` from Claude to Grok

- **goal:** Port the skill-audit skill (audit a skill against a quality rubric) for use with /skill-prune
- **in scope:** `P:/packages/.claude-marketplace/plugins/cc-skills-analysis/.../skills/skill-audit/`
- **out of scope:** porting sqa or epistemic-check (deferred — niche)
- **acceptance:** `/skill-audit <skill-name>` works on Grok Build and produces a quality report
- **falsifier:** skill-audit fails on Grok due to Claude-specific dependencies

## Open decisions

### OD-1: Should /review absorb /red-team entirely?

- **Options:** (A) keep /red-team as a standalone skill, (B) deprecate it and make `/review --adversarial` the only path, (C) keep both but document the overlap explicitly
- **Selection criterion:** operator cognitive load (fewer skills to remember) vs. specialization (dedicated adversarial tool may be deeper)
- **Current lead:** (C) — keep both, document overlap. /red-team is explicitly heavier (planner→specialists→critic→clustering); /review --adversarial is lighter. Let the operator choose based on stakes.
- **What would change:** if /red-team is never invoked independently (check via /tp critique log), absorb into /review

### OD-2: Should `verification-before-completion` (superpowers) be deprecated in favor of /check?

- **Options:** (A) deprecate it, (B) keep as a lightweight inline reminder that complements /check
- **Selection criterion:** does the superpowers skill add value /check doesn't?
- **Current lead:** (A) deprecate — /check is strictly more capable (multi-concern, verifier subagents, PASS/FAIL verdict)
- **What would change:** if the superpowers skill fires in contexts /check doesn't cover

## Hard constraints

- `/check` and `/review` must remain distinct (per wiki concept `check-vs-review-complementary-not-redundant.md`)
- `/tp` must remain distinct (dialogue posture, not artifact-producing)
- No auto-removal of skills (deprecation notices only)
- Honor the operator's "not tied to spawn_subagent" directive for Nemotron routing in any specialist pool work

## Cross-reference couplings

- `AGENTS.md` "Review skill routing" table → names /check, /review, /red-team, /tp. All exist; no dangling reference.
- `/check` Step 6.2 auto-escalation → calls /review. If /review changes its invocation interface, /check must update.
- `/tp` Step 2a wiki pool query → same pool /review should use for specialists. Shared dependency on `[[model-tool-calling-capability-matrix]]`.

## Other outstanding streams

- **AGENTS.md refactor** (`agents-md-refactor-20260727`) — the routing table lives in AGENTS.md; the refactor will tighten it
- **qmd replacement** (`qmd-fts5-replacement-20260727`) — /review uses qmd for wiki pattern queries (Step 0.5); a qmd replacement must preserve the query interface
- **/packet bug fixes** — CORR-001/002/003/004 from this session's /review run on /packet need fixing before /packet is reliable

## Explicit non-goals

- Do NOT merge /check into /review — they serve different SDLC stages
- Do NOT port sqa or epistemic-check in this work — defer until /review consolidation is proven
- Do NOT rewrite /review's pipeline from scratch — enhance, don't rebuild

## Resumption protocol

1. Read the 6 files in the Read-first list
2. For RC-01: read the `/agy`, `/codex`, `/mmx` SKILL.md files to understand the conductor pattern; wire it into /review Step 5.5
3. For RC-02: read /tp Step 2a for the wiki-pool query pattern; adapt for /review specialists
4. For RC-03: read the AGENTS.md routing table; propose the consolidation mapping
5. For RC-04: read the skill-audit SKILL.md in cc-skills-analysis; port to Grok

## Suggested next invocation

```
/go enhance /review with --second-opinion cross-model dispatch (RC-01) and automatic specialist model selection (RC-02), then consolidate the review routing table (RC-03)
```

## Last user message (verbatim)

> /handoff I'd like to enhance '/review' and consolidate the other skills and plugins for various types of review.

## Epistemic labels

- The overlap analysis is [FACT] (read from skill catalog this session)
- The routing recommendations are [INFERENCE] (based on reading the skills, not on operator confirmation)
- Whether /red-team should be absorbed is [UNKNOWN] (needs usage data from /tp critique log)
