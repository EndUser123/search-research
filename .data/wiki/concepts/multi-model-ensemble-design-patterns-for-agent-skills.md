---
title: "Multi-model ensemble design patterns for agent skills"
created: 2026-08-04
source: session-019fcdd2 (/risks v1-v4 improvement cycle)
tags: [skill-design, multi-model, ensemble, cross-model, pattern-catalog, pattern-propagation, subagent-dispatch, host-context, threat-model, adaptive-escalation]
summary: >
  Seven reusable design patterns developed during the `/risks` skill
  improvement cycle (4 iterations, session 019fcdd2). Each pattern solves
  a specific failure mode in skills that spawn subagents for analysis,
  review, or critique. Patterns are abstracted from `/risks` (the reference
  implementation) and mapped to 6+ other skills that have the same gaps.
  This concept is the source of truth for pattern propagation: `/skill-dev`
  Step 0.5 queries it, `/todo` can scan against it, and future skill authors
  read it before designing subagent dispatch logic.
agent: grok
host: grok
cognitive_load: 3
verification: observed (first-run evidence from /risks v1)
relations:
  - target: wiki/concepts/adaptive-risk-assessment-single-pass-first-architecture.md
    type: documents — the architecture of /risks, which implements all 7 patterns
  - target: wiki/concepts/skill-development-portfolio.md
    type: complements — portfolio covers technique-level patterns; this covers dispatch-level patterns
  - target: wiki/concepts/deferred-skill-improvements-registry.md
    type: related — tracks what was deferred; this tracks what should propagate
  - target: wiki/concepts/costa-kallick-critical-friend.md
    type: extends — the cross-model requirement operationalizes the "different lens" principle
---

# Multi-model ensemble design patterns for agent skills

## Why this exists

During the `/risks` skill improvement cycle (session 019fcdd2, 4 iterations),
we developed 7 reusable design patterns for skills that spawn subagents.
The patterns solve real failure modes observed in the first run — not
theoretical concerns. Without this catalog, the patterns are trapped in
`/risks`'s SKILL.md body while 6+ other skills have the same gaps.

**This concept is the source of truth for pattern propagation.** When a
pattern is applied to one skill, scan other skills for the same gap using
the applicability matrix below.

## The 7 patterns

### P1: Host-context requirement

**Problem:** Subagents spawned for analysis default to the most adversarial
threat model available when they don't know what kind of system they're
analyzing. A critique of a multi-agent LLM system reads as a multi-tenant
security analysis, producing adversarial findings (weaponization, injection)
that don't match the actual threat model (unreliable agents making mistakes).

**Pattern:** Every subagent prompt MUST include host system context: (1)
what kind of agents operate here (LLM, human, untrusted code), (2) what
trust model applies (operator-authorized, autonomous, sandboxed), (3) any
wiki concepts relevant to the target domain.

**Evidence:** Session 019fcdd2, `/risks` v1 critique — 3 of 14 findings
(M1, M3, partially R1) used an adversarial threat model that didn't match
the host's unreliable-agent reality. Root cause: the critique subagent
lacked host context and defaulted to enterprise-security analysis.

**Applicability:** ANY skill that spawns subagents for analysis, review, or
critique.

### P2: Cross-model diversity requirement

**Problem:** Same-model critique shares the scan's blind spots. The Costa &
Kallick (1993) "cannot refocus your own glasses" principle: a self-applied
critique thinks harder through the same lens, which is structurally weaker
than a critique from a different lens. Same-model-family critique is
self-critique in disguise.

**Pattern:** Every critique/verification subagent MUST use a different model
family from the parent that ran the analysis AND from each other. With 7+
free families available (OpenRouter/ling, GLM, Zen/DeepSeek, MiniMax, Cohere,
Qwen, NVIDIA), there is no cost constraint — only the diversity matters.

**Evidence:** Session 019fcdd2, `/risks` v1 — the cross-family critique
(or-ling-3-flash-free) found structural gaps the parent Grok model missed.
If the critique had used parent-inherited Grok, it would have shared the
same adversarial-security bias and missed the same things.

**Applicability:** ANY skill that spawns subagents for critique or review.
Includes `/review`, `/tp`, `/red-team`, `/check`.

### P3: Adaptive panel sizing

**Problem:** Fixed-size panels (always 1 critic, always 3 specialists) don't
match the target's stakes. A reversible config change needs less verification
than an irreversible architecture decision. Using the same depth for both
wastes resources on low-stakes targets and under-protects high-stakes ones.

**Pattern:** Panel size adapts to the target's severity and reversibility:

| Condition | Panel size | Why |
|---|---|---|
| HIGH severity + reversible | 2 critics | Verify the HIGH; one may miss |
| HIGH severity + irreversible | 3 critics | Can't undo — maximize coverage |
| MEDIUM severity only | 1 critic | Standard verification sufficient |
| CRITICAL stakes + any risk | 3 critics | Maximum diversity |

**Evidence:** Session 019fcdd2 — the `/risks` v1 run had CRITICAL stakes
(LAEFS enforcement layer) but only 1 critic. The panel should have been 3.

**Applicability:** Skills with panel/roster dispatch — `/review`,
`/red-team`, `/risks`. Not applicable to single-critic skills like `/tp`
(which dispatches 1 fresh subagent).

### P4: Disagreement-as-signal

**Problem:** When multiple critics from different model families are used,
their output must be synthesized. The standard approach — "if any critic
flags it, escalate" — treats all criticism equally. But critics from
different families disagreeing IS signal: it indicates genuine ambiguity
that warrants deeper investigation.

**Pattern:** Panel synthesis uses disagreement patterns:

| Pattern | Meaning | Action |
|---|---|---|
| All confirm HIGH risk | High confidence | Escalate |
| Critics split (confirm/downgrade) | Ambiguity | Escalate — the disagreement IS the signal |
| All downgrade | Overcounting | Stop (report downgraded) |
| All find new HIGH | Blind spot confirmed | Escalate |

**Evidence:** Theoretical — derived from the decorrelated-ensemble principle
in ML theory. Not yet empirically validated on this host (first `/risks` v4
run needed).

**Applicability:** Multi-critic panels — `/risks`, `/review` (if it adopts
multi-critic), `/red-team`.

### P5: Adaptive lens assignment

**Problem:** Fixed specialist rosters dispatch the same specialists
regardless of what the scan found. A target with security + state risks
gets the same 6 specialists as a target with performance + workflow risks.
This wastes slots on irrelevant lenses and may miss relevant ones.

**Pattern:** Specialist selection is driven by the scan's findings — not a
fixed roster. For each risk category confirmed, dispatch a specialist for
that lens. Always include meta/self-reflection. Invent specialists for
categories not in the standard roster.

**Evidence:** Session 019fcdd2 — the `/risks` scan found risks in
"alternatives not considered" and "threat surface coverage" categories.
A fixed roster would have dispatched a security specialist (irrelevant for
a decision target) instead of a scope/gap specialist (highly relevant).

**Applicability:** Skills with specialist dispatch — `/risks`, `/review`,
`/red-team`.

### P6: Threat-model classification

**Problem:** Risk/analysis skills scan for risks without classifying what
kind of threat model is appropriate. This leads to adversarial findings
(weaponization, deliberate evasion) on targets that only have accidental
failure modes (LLM mistakes, operator errors).

**Pattern:** Phase 0 classifies the threat model before scanning:

| Threat model | When | Risk types |
|---|---|---|
| unreliable-agent | LLM agents following instructions, making mistakes | Accidental, pattern-matching gaps, state contamination |
| adversarial-agent | Untrusted code, autonomous agents with goals | Weaponization, evasion, injection |
| external-attacker | Internet-facing systems, untrusted input | Injection, privilege escalation, data exfiltration |
| operator-error | Human operator making manual changes | Misconfiguration, wrong path, wrong command |

**Evidence:** Session 019fcdd2 — the `/risks` v1 scan and critique both
treated the LAEFS target as adversarial-agent when it was unreliable-agent.
3 of 14 findings were threat-model-inflated. Pattern added in v2.

**Applicability:** ANY skill that analyzes risk or security — `/risks`,
`/review`, `/check`. Also relevant to `/handoff` (threat model shapes what
"safe to merge" means).

### P7: Deduplication before reporting

**Problem:** Duplicate findings inflate the risk count and distort
severity-based escalation thresholds. Two findings with different surface
descriptions but the same underlying mechanism are one finding, not two.

**Pattern:** Before reporting, merge findings that share a root cause. State
the deduplication in the output so the reader can verify.

**Evidence:** Session 019fcdd2 — `/risks` v1 produced R1 (subprocess bypass)
and R4 (pattern matching insufficient) as separate HIGH risks. They were the
same root cause with different citations. The inflated count (4 HIGH instead
of 3) made the escalation threshold fire differently. `[UNVERIFIED PATTERN — N=1]`

**Applicability:** ANY skill that produces ranked findings — `/risks`,
`/review`, `/red-team`, `/why`.

## Applicability matrix

| Skill | P1 Host-ctx | P2 Cross-model | P3 Panel | P4 Disagree | P5 Adaptive lens | P6 Threat model | P7 Dedup |
|---|---|---|---|---|---|---|---|
| **`/risks`** | ✅ v4 | ✅ v4 | ✅ v4 | ✅ v4 | ✅ v4 | ✅ v2 | ✅ v2 |
| **`/review`** | ❌ Missing | ❌ Single model | ❌ Fixed roster | ❌ N/A | ❌ Fixed | ❌ Missing | ❌ Missing |
| **`/tp`** | Partial | ✅ Has pool | ❌ N/A (1 critic) | ❌ N/A | ❌ N/A | ❌ Missing | ❌ N/A |
| **`/red-team`** | ❌ Missing | Partial (1 cross) | ❌ Fixed 3-6 | ❌ Missing | ❌ Fixed | ❌ Missing | ❌ Missing |
| **`/www`** | ❌ Missing | ❌ Same model | ❌ N/A | ❌ N/A | ❌ N/A | ❌ Missing | ❌ N/A |
| **`/check`** | ❌ Missing | ❌ Same model | ❌ N/A | ❌ N/A | ❌ N/A | ❌ Missing | ❌ N/A |
| **`/go`** | ❌ Missing | Partial (pool) | ❌ N/A | ❌ N/A | ❌ N/A | ❌ Missing | ❌ N/A |

**Reading the matrix:** ✅ = pattern implemented. ❌ = gap. Partial =
incomplete implementation. N/A = pattern doesn't apply to this skill's
architecture.

## Reference implementation

`/risks` (at `~/.grok/skills/risks/SKILL.md`) implements all 7 patterns as
of v4 (session 019fcdd2). When propagating a pattern to another skill, read
`/risks`'s implementation of that pattern for the reference form.

## How to use this concept

### For skill authors

Before writing subagent dispatch logic in a new skill, read this concept.
Check which patterns apply to your skill's architecture. Implement them from
the start rather than retrofitting.

### For `/skill-dev`

`/skill-dev` Step 0.5 queries this concept to find applicable patterns. Step 7
(graph projection) uses the applicability matrix to identify which other
skills need a pattern that was just applied to the target skill.

### For pattern propagation (mechanical)

When a pattern is applied to a skill, scan the applicability matrix. For each
skill with a gap in that pattern's column, the matrix surfaces it. This makes
propagation mechanical — no need for the operator to remember to ask.

Example: "P1 (host-context) applied to `/risks`. Matrix shows `/review`,
`/red-team`, `/www`, `/check`, `/go` all missing P1. Recommend
`/skill-dev improve /review` next."

## Falsifier

This concept is wrong if:
1. The patterns don't generalize beyond `/risks` — if applying P1 (host-context)
   to `/review` produces no measurable improvement in finding quality.
2. The patterns are too granular — if they're really just one pattern
   ("use diverse models wisely") split into 7 sub-patterns for catalog
   aesthetics rather than independent applicability.
3. The applicability matrix is wrong — if a skill marked "Missing" actually
   implements the pattern in a way the matrix missed.

## What this means for our workspace

1. **`/risks` is the reference implementation** — all 7 patterns are live in
   its SKILL.md. Use it as the template when propagating.
2. **`/review` is the highest-value propagation target** — it has the most
   gaps (7/7) and is the most frequently invoked analysis skill.
3. **Pattern propagation should be tracked** — when a pattern is applied to
   a new skill, update the matrix in this concept.
4. **The `/skill-dev` Check 9 (subagent dispatch compliance) should scan
   against this catalog** — mechanical enforcement over behavioral reminder.
