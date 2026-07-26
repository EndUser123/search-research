---
title: "Design skill's write/review loop misses framing gaps — preflight is the remedy"
created: 2026-07-20
source: session-2026-07-20
tags: [design-skill, preflight, source-authority-discovery, framing-gap, review-loop, meta-finding]
summary: >
  The /design skill's writer→reviewer→revise loop is internally rigorous but never
  challenges its own framing. A source-authority-discovery (preflight) audit run
  AFTER 4 review rounds reached 0 open issues found 6 real gaps the loop missed:
  unaddressed alternatives, missing CLI capabilities, a Windows silent-failure bug,
  and an incorrect auth model. The design skill should mandate preflight before
  the first write round, not after the loop converges.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
---

## Summary

The design-doc-writer/reviewer loop catches internal inconsistencies, grounding failures, and cross-section contradictions. It does **not** catch framing gaps — missing alternatives, unprobed CLI capabilities, or incorrect assumptions about the environment. The preflight skill (`source-authority-discovery`, renamed to `preflight` 2026-07-20) is the structural remedy: it inventories the workspace for prior art and capability claims before design work begins.

## Key Findings

This session's `/design` invocation for `/mmx` and `/codex` Grok skills:

- **4 review rounds** converged with 0 open issues (21 issues addressed across 4 rounds).
- **Round 1** caught a critical security bug (`codex review --uncommitted` inherits `danger-full-access` — see [[cli-canonical-invocation-silent-failure-class]]).
- **Rounds 2–4** caught key leaks, producer/consumer carve-outs, absent-key branches.
- **After round 4 approved with 0 open**: a preflight audit found **6 more gaps** the loop never surfaced.

The 6 preflight gaps:

1. `cc-skills-ai-api` plugin ships a near-identical sibling skill set — unaddressed alternative (major)
2. `mmx auth login` supports OAuth, not just API key — auth model was over-engineered (major)
3. Bare `mmx` on Windows silently fails via `.cmd` shim — all invocation examples were broken (major)
4. `mmx search query` is a third mode — capability was missing from the design (major)
5. Codex exposes `sandbox_permissions` override, not just `sandbox_mode` (minor)
6. New skills must declare `host: grok` per the 2026-07-18 convention (minor)

The reviewer verified the design's claims about `/agy`, `codex`, and `mmx` CLIs. It did **not** verify the design's scope — that no competing implementation exists. That's not the reviewer's job; that's preflight's job, and preflight didn't happen until the user asked for a critical-friend review.

## Why the loop misses framing gaps

The writer and reviewer both operate **inside the design's framing**. The reviewer's job is to verify claims the writer makes, not to discover claims the writer should have made. Specifically:

- The reviewer checks "is this design grounded in `/agy/SKILL.md`?" — not "does `cc-skills-ai-api` already solve this?"
- The reviewer checks "are the `mmx` flags correct?" — not "does `mmx` have capabilities the design didn't probe?"
- The reviewer checks "is the security model sound?" — not "is the security model solving a harder problem than necessary?"

Preflight breaks this frame because it searches the **workspace** for prior art, not the design document for claims.

## Recommendation

The `/design` skill should run preflight **before** the first write round, not after the loop converges. The design handoff should include the preflight artifact as a required input. This adds ~10 minutes to the design process and prevents shipping a v0.1 with capability gaps, broken Windows invocations, and duplicated work.

The user's critical-friend review ("did we do the proper preflight?") is the right question to ask after any `/design` run that did NOT start with preflight.

## Related

- [[skill-rename-propagation-checklist]] — the rename of `source-authority-discovery` → `preflight` followed this session's design work
- [[cli-canonical-invocation-silent-failure-class]] — the codex review sandbox bug and mmx Windows shim bug are instances of the broader class
- [[multi-agent-correlated-errors]] — related but different: that's about persona diversity in review; this is about framing diversity (preflight brings a different frame, not a different persona)

## Auto-related

- [[multi-agent-correlated-errors]]

