---
title: "Multi-subagent orchestration skill workflow failure patterns"
created: 2026-07-29
source: session-019fa48a
tags: [skill-design, subagent-orchestration, failure-patterns, design-skill, workflow]
summary: >
  Five distinct failure modes observed during a /design run that wasted ~30 minutes:
  (1) writer spawned read-only silently failed to persist output, (2) reviewer resume
  hit max_tokens_truncation after 2 rounds on MiniMax-M3, (3) model slug from catalog
  returned 404 on actual API call, (4) critical-friend reframe left stale appendix
  references, (5) full mode used instead of --fast for a well-scoped design. Each has
  a durable fix applied to the design skill and tool-fallbacks.md.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/stop-hook-lastassistantmessage-payload-field-2026.md
    type: related
  - target: wiki/concepts/regex-cannot-detect-context-dependent-behavioral-patterns.md
    type: related
---

# Multi-subagent orchestration skill workflow failure patterns

## Decision context

A `/design` run for the search-before-proposing hook (run d8173a98, 2026-07-29) surfaced five distinct workflow failures that are structural to any skill that orchestrates multiple subagents across rounds. Each failure was diagnosed, root-caused, and fixed durably. This concept documents the patterns so future skill authors can prevent them.

## The five failure patterns

### 1. Read-only writer silently fails to persist

**Symptom:** The writer subagent "completed" (exit 0) but the design document on disk was unchanged — it still had the old content.

**Root cause:** The orchestrator spawned the writer with `capability_mode="read-only"`. The writer needed to write files (`<design_doc_file>`, `<summary_file>`) but couldn't. The subagent produced its output in-context (thinking/reasoning) but the write tool calls silently failed.

**Durable fix:** SKILL.md Step 1 now explicitly warns: "capability_mode: must NOT be 'read-only' — the writer needs write access." Added the failure date (2026-07-29) as evidence.

**Generalization:** Any skill that spawns a subagent expected to write files must specify `capability_mode="read-write"` or omit the parameter (defaults to all). Read-only is only safe for pure reviewers and verifiers.

### 2. Reviewer resume hits max_tokens_truncation

**Symptom:** After 2 review rounds (42 findings + 11 findings addressed), resuming the reviewer subagent failed with `max_tokens_truncation`. The accumulated transcript from prior rounds exceeded MiniMax-M3's output budget.

**Root cause:** `resume_from` carries the full prior transcript into the new invocation. For multi-round skills (design review, code review, AAR), the transcript grows monotonically. After 2+ rounds, it can exceed the model's context window.

**Durable fix:** SKILL.md Step 5 now includes resume failure recovery: "if the resumed reviewer fails with `max_tokens_truncation`, launch a fresh subagent (no `resume_from`). The fresh reviewer re-reads artifacts from disk — it does not need the prior transcript." Also added to tool-fallbacks.md.

**Generalization:** Any skill using `resume_from` across ≥2 rounds is at risk. The pattern: if resume fails with truncation, switch to fresh launch. The fresh agent re-reads on-disk artifacts instead of relying on transcript memory.

### 3. Model slug in catalog returns 404 on API call

**Symptom:** `gemini-2` listed in the session-start model catalog. Spawning a subagent with `model="gemini-2"` returned HTTP 404: "model does not exist or your team does not have access."

**Root cause:** The catalog lists models that exist in the provider's API, but team-level access may differ. The catalog is a registry of what COULD be available, not a guarantee of what IS accessible.

**Durable fix:** Added to tool-fallbacks.md known-broken table. The general rule: "probe with a trivial task before committing to a model for a multi-minute subagent run."

**Generalization:** Never trust the session-start model list as a guarantee for `model=` parameters. The list changes between sessions and team access may be revoked without notice.

### 4. Critical-friend reframe leaves stale appendix references

**Symptom:** The critical friend returned REVISE, requesting a fundamental reframe (drop `prior_decision` category, change title from "mechanical enforcement" to "restore and instrument"). The writer revised the body (§1-13) but left the old framing in appendices (§14-15). The symbol drift checker flagged 47 references.

**Root cause:** Per-issue revision is local to each finding's section. A framing-level change (like the critical friend's REVISE) sweeps across the entire document, but the writer only revises the sections it's told about. The consistency sweep (Step 4.5) was not run after the critical-friend routing.

**Durable fix:** SKILL.md Step 5.5 REVISE routing now mandates a consistency sweep: "run a consistency sweep (Step 4.5: emit symbols_changed + drift check) after addressing the critical friend's findings."

**Generalization:** Any multi-round skill with a "reframe" step (where the framing changes, not just details) needs a consistency sweep after the reframe. The sweep catches stale references that per-issue revision misses.

### 5. Full mode used instead of --fast for well-scoped design

**Symptom:** The design extended an existing system (PGM plugin) with a concrete bug as the primary driver. This is exactly the `--fast` profile (2 rounds suffice). Instead, full mode ran (3+ rounds), adding ~15 minutes.

**Root cause:** The quick-fit screening listed `--fast` as an option but didn't recommend it strongly enough for the "extends existing system" case. The orchestrator defaulted to full mode.

**Durable fix:** SKILL.md quick-fit screening now states: "Default recommendation when: the design extends an existing system (not greenfield), has a concrete bug or gap as the primary driver, or the user provided a specific file/plugin/component to modify."

**Generalization:** Skill depth tiers should default based on the design's shape, not the operator's expertise. "Extends existing system with bug fix" is a `--fast` signal regardless of the operator's seniority.

## Receipts

- `~/.grok/skills/design/SKILL.md` — 4 edits (capability warning, resume recovery, post-CF sweep, --fast recommendation)
- `~/.grok/tool-fallbacks.md` — 2 entries (gemini-2 404, MiniMax-M3 resume truncation)
- Commit `740761c` — all 5 fixes

## Falsifier

These fixes are wrong if, within 3 months:
- A read-only writer subagent successfully persists files (the capability_mode constraint was unnecessary)
- Resume_from works reliably after 3+ rounds on MiniMax-M3 (the truncation was transient)
- The model catalog becomes a reliable guarantee of API access (probing becomes unnecessary)

## What this means for skill design

These five patterns are not specific to `/design` — they apply to any skill that orchestrates multiple subagents across rounds (`/review`, `/debrief`, `/risks`, `/aar`). The common thread: orchestration skills assume their subagents behave as instructed, but the harness layer (capability modes, resume mechanics, model catalogs) can silently violate those assumptions.

**Skill authoring checklist (from this incident):**

1. Every spawn that writes files → verify `capability_mode` is not `read-only`
2. Every skill with `resume_from` across rounds → add resume-failure recovery (launch fresh)
3. Every `model=` parameter → document that probing is needed before multi-minute runs
4. Every reframe/redirect step → mandate a consistency sweep afterward
5. Every depth tier → default based on design shape, not operator expertise

These map to the broader principle from [[mechanical-enforcement-over-behavioral-reminder]]: the fixes are mechanical (skill text edits), not behavioral (hoping the orchestrator remembers). Skill text is the enforcement layer; prompting alone is the reminder layer.

## Related concepts

- [[stop-hook-lastassistantmessage-payload-field-2026]] — same session, different bug class
- [[regex-cannot-detect-context-dependent-behavioral-patterns]] — same session, structural regex limitation
- [[mechanical-enforcement-over-behavioral-reminder]] — why skill text fixes are more durable than behavioral rules
- [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]] — companion finding from same session
