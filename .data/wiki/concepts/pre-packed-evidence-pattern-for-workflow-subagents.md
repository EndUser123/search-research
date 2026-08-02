---
title: "Pre-packed evidence pattern for workflow subagents"
created: 2026-08-01
source: session-019fb937 (close-check Phase 3 optimization)
sources:
  - internal: ~/.grok/workflows/close-check.rhai (Phase 3 context_bundle)
  - internal: ~/.grok/skills/tp/__lib/tp_dispatch.py (original context pre-packing)
  - internal: ~/.grok/skills/packet/__lib/file_extractor.py (AST extraction reused by tp_dispatch)
tags: [workflow-optimization, context-pre-packing, subagent-efficiency, tp-dispatch-pattern, close-check]
agent: grok
host: both
cognitive_load: 2
verification: single-session-verified
summary: >
  When a multi-phase workflow's early phases already gather evidence (transcript
  scans, git state, friction counts), later phases should pre-pack that evidence
  into subagent prompts instead of having each subagent re-discover it. This
  eliminates 5-10 redundant tool calls per subagent. The pattern originates from
  /tp's tp_dispatch.py (which pre-packs critique context for CLI agents) and
  was applied to close-check Phase 3, reducing remediation from 15+ minutes
  to an estimated ~5 minutes.
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: related
---

# Pre-packed evidence pattern for workflow subagents

## Decision context

**The problem:** close-check Phase 3 runs 5 lifecycle skills as subagents.
Each subagent independently reads the SKILL.md, scans the transcript,
checks existing capture, writes artifacts, and commits. With 5 skills,
that's 50-85 tool calls and 15+ minutes — mostly duplicating work Phase 1/2
already did.

**The pattern from /tp:** `/tp`'s `tp_dispatch.py` pre-packs all context
a CLI agent needs into a single file using `/packet`'s `file_extractor.py`
and `filter.py`. The agent reads one file instead of making 5-10 discovery
tool calls. This is the token-efficiency technique that makes cross-model
critique feasible.

**The adaptation:** instead of pre-packing to a file (tp_dispatch pattern),
close-check pre-packs to a string variable (`context_bundle`) built from
data Phase 1/2 already collected. Each Phase 3 subagent receives the
bundle in its prompt — zero discovery tool calls needed.

## The pattern

```
Phase 1: Sweep agents gather evidence (git state, friction counts, corrections)
Phase 2: Synthesize classifies findings + collects raw_evidence
Phase 3: Build context_bundle from Phase 1/2 data
         → Pass to each remediation subagent in its prompt
         → Subagent reads bundle + writes artifacts + commits
         → No transcript re-scan needed
```

**Key insight:** the evidence has already been gathered. The skills don't
need to re-gather it; they need to ACT on it. Pre-packing shifts the
subagent's job from "discover + analyze + write" to "analyze + write."

## The raw_evidence field

The classified findings alone are too lossy for the skills to act on.
"friction: 6 corrections" doesn't tell /capture WHAT the corrections were.
The fix: add a `raw_evidence` field to the sweep agent output schema that
carries the actual correction texts, error patterns, and work-stream
summaries. Phase 2 collects this alongside classified findings; Phase 3
packs both into the context_bundle.

## What this means for our workspace

Any multi-phase workflow where early phases gather data and later phases
act on it should use pre-packed evidence. The pattern:

1. Early phases return structured evidence (not just classified findings)
2. Mid phases collect and assemble the evidence into a bundle
3. Late phases receive the bundle in their prompts, skipping re-discovery

**Applicability:** close-check (Sweep → Remediate), /go (Discover →
Implement), /aar (Reconstruct → Analyze), /design (Research → Synthesize).
Any pipeline where the same data is read by multiple downstream consumers.

## Falsifier

This pattern is wrong if:
- The raw evidence is too large to fit in a prompt (context window overflow)
- The evidence goes stale between phases (concurrent sessions modify state)
- The skills genuinely need to re-read the transcript for quality (the
  pre-packed evidence misses signal the full scan would catch)

The first is mitigated by summarizing. The second by re-reading files
immediately before writes (already instructed). The third is the real
risk — accepted in exchange for 3x speedup.
