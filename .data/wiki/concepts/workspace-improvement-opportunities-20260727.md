---
title: "Workspace improvement opportunities from session-019fa39d research (8 opportunities, fresh-lens /tp scan)"
created: 2026-07-27
source: session-019fa39d (/tp fresh-lens opportunity scan via glm-5-2)
tags: [skill-improvement, workspace-architecture, dry-violation, evidence-tiers, wiki-gate, skill-consolidation, contract-drift, enforcement-architecture, cross-host]
summary: >
  Fresh-lens /tp scan (glm-5-2, 19 tool calls, 414s) identified 8
  improvement opportunities from the session's research that the session
  itself missed. Top 5 are high-confidence: (1) Extract the wiki-gate
  into a shared __lib/wiki_gate.py — duplicated as prose in 15 skills
  with divergent criteria (5/6/7); the keystone extraction that makes
  all other decompositions easier. (2) Make the evidence-tier system
  workspace-wide, not /why-internal — the session proved it's needed
  (8 findings, 3 wrong) but left it in the one skill that can't enforce
  it on itself. (3) Instrument and measure Step 0.5 hit rate — never
  measured despite the concept's own falsifier requiring it; 3 more
  skills added Step 0.5 without measuring the existing ones. (4) Set
  up the routine-improvement cadence as scheduler_create — the session
  recommended a cadence but didn't create the scheduled task; the
  session's own research predicts decay without structural enforcement.
  (5) Run /review --focus maintainability on the analytical skills
  themselves — /tp (819 lines), /review (743), /design (718), /go (643)
  are approaching the 1000-line threshold; nobody has run the
  maintainability lens on the maintainability skills. The keystone
  insight: #1 is the first extraction to do because it establishes the
  shared-library pattern that #2 and the /debrief consolidation would
  extend.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "Fresh-lens /tp subagent 019fa690-1c03-73b0-b282-58c778b100cc (glm-5-2, 19 tool calls, 414s)"
  - "Direct verification: skill line counts (Get-Content | Measure-Object), wiki-gate duplication (Select-String across 15 skills), __lib absence (grep across all .py files)"
  - "P:/.data/wiki/concepts/routine-skill-improvement-cadence.md (same session)"
  - "P:/.data/wiki/concepts/wiki-integrated-skills-query-save-pattern.md (documents the pattern but prescribes per-skill implementation, not extraction)"
  - "P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md (mandates code-enforced gates, not prose)"
  - "P:/.data/wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md (predicts the /close↔/aar bug class)"
relations:
  - target: wiki/concepts/routine-skill-improvement-cadence
    type: extends — identifies the specific extractions and measurements the cadence would prioritize
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern
    type: refines — that concept documents the pattern per-skill; this concept proposes extracting it into shared code
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: applies — that concept mandates code-enforced gates; this concept identifies the specific gate to convert
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains
    type: instance-of — the /close↔/aar bugs are an instance of this pattern
---

# Workspace improvement opportunities from session-019fa39d

## Decision context

**Why this scan was needed.** The session produced 7 wiki concepts and
extensive research across 5 clusters (error-handling, design speedup,
close-scanner failures, routine skill improvement, lifecycle validation).
But the session never stepped back to ask: what opportunities did the
research surface that the session itself didn't act on? The /tp fresh-lens
scan (glm-5-2) read the actual skill source files and wiki concepts to
find structural debt, missed abstractions, and combination opportunities.

**What was done.** A fresh subagent (no shared framing anchor) read 15+
SKILL.md files, the session's wiki concepts, and the workspace structure.
It identified 8 opportunities across 5 categories: decomposition (4),
higher abstractions (2), uncertainty (3), missed combinations (4), and
structural debt (4). The parent verified the key claims by direct
measurement (line counts, grep for duplication, __lib absence).

## Receipts

- **[FACT]** Wiki-gate pattern (Step 0.5 query + mechanical gate + save)
  appears in 15 skills — receipt: `Select-String -Pattern
  "wiki-worthy|mechanical gate|Step 0.5|wiki_save" across all SKILL.md
  files → 15 hits`
- **[FACT]** No shared `__lib/wiki_gate.py` exists — receipt: `grep for
  wiki_gate|mechanical_gate|wiki_save across all .py files → 0 matches`
- **[FACT]** Evidence-tier system exists only in /why — receipt: grep for
  "Tier 1|Tier 2|Tier 3|Tier 4|weakest.link" across SKILL.md files → only
  why/SKILL.md matches
- **[FACT]** Step 0.5 hit rate has never been measured — receipt: no
  instrumentation code found; the concept's own falsifier requires it
- **[FACT]** Skill line counts: tp=819, review=743, design=718, go=643,
  dream=514, aar=498, close=450, handoff=435, why=428 — receipt:
  `Get-Content | Measure-Object -Line`
- **[FACT]** scheduler_create tool is available but no task exists for the
  routine-improvement cadence — receipt: scheduler_list returns empty for
  skill-improvement topics
- **[INFERENCE]** The wiki-gate extraction is the keystone — derived from
  the pattern: it's the most duplicated (15 skills), has the clearest
  criteria divergence, and creates the __lib substrate other extractions
  extend

## The 8 opportunities

### High-confidence (verified, ready to act)

#### 1. Extract wiki-gate into shared `__lib/wiki_gate.py` (THE KEYSTONE)
The Step 0.5 query + mechanical gate + save-or-skip logic is copy-pasted
as prose in 15 skills with divergent criteria (5 in /why, 6 in /debrief,
7 in /review). No shared Python module exists. Extract one module that
all skills import. Canonicalize the criteria. Convert the gate from prose
to code. This is the single highest-ROI extraction: eliminates 15× DRY
violation, stops criteria divergence, makes the gate enforceable.
**Confidence: H.** Test: write the module, migrate /why first, run on a
real failure, confirm the gate fires and the query emits a receipt.

#### 2. Make evidence-tier system workspace-wide
/why's four-tier system (Tier 1-4, weakest-link) is the structural fix
for all five behavioral failure modes researched this session. But it
exists only in /why. /aar, /debrief, /review, /risk all make causal
claims without tiers. The session proved the tier system is needed (8
findings, 3 wrong) but left it in the one skill that can't enforce it
on itself. Extract the tier definitions into a shared reference; add a
Stop-hook check for [FACT] claims without tier citations.
**Confidence: H.** Test: add tier labels to /aar's episodes on 3 runs;
measure whether false-positive claims drop.

#### 3. Instrument and measure Step 0.5 hit rate
The wiki-query step exists in 5+ skills but its hit rate has never been
measured. The concept's own falsifier requires measurement after 20 runs.
3 more skills added Step 0.5 in the last 2 days without measuring the
existing ones. If the hit rate is near-zero, every Step 0.5 is ceremony.
Add a hit/miss counter; log query + keywords + hit count; report after
20 invocations.
**Confidence: H.** Test: the instrumentation itself IS the test.

#### 4. Set up routine-improvement cadence as `scheduler_create`
The session recommended a monthly/quarterly cadence but didn't create
the scheduled task. The session's own research predicts decay without
structural enforcement (the rule-not-fired pattern). Use scheduler_create
to schedule monthly /skill-dev measure + quarterly /risk.
**Confidence: H.** Test: create the task, observe whether it fires and
produces findings over 3 months.

#### 5. Run /review --focus maintainability on analytical skills
/tp (819 lines), /review (743), /design (718), /go (643) are approaching
the 1000-line threshold. Nobody has run the maintainability lens on the
skills that define maintainability. The quality-enforcement skills are
accumulating structural debt that undermines their authority.
**Confidence: H.** Test: run /review --focus maintainability on /tp;
observe findings.

### Medium-confidence (worth exploring)

#### 6. Consolidate /debrief into /aar --parallel
/debrief's analytical output is a strict subset of /aar's. The only
unique capability is 5-lens parallel dispatch. Either merge as /aar
--parallel, or extract a shared retrospective-base. Two skills
independently accreting the same features (Step 0.5, wiki-save,
root-cause) without a shared base doubles maintenance.
**Confidence: M.** Test: prototype /aar --parallel; run both on the same
session; compare coverage.

#### 7. Cluster the 4 /close↔/aar bugs as contract drift
The 4 bugs from cluster 3 (continuation_coverage gate, temp_files gate,
close_runner dead code, /aar output validator) likely share one root
cause: no shared schema or integration test between /close and /aar.
The existing producer-consumer-contract-drift concept predicts this.
Fixing them individually leaves the drift unaddressed.
**Confidence: M.** Test: run clustering; if ≥3 collapse into one
structural fix (shared schema + integration test), root cause confirmed.

#### 8. Name the three-layer enforcement architecture
The workspace already has hooks (hard), AGENTS.md rules (soft), and
validators (adaptive). The session re-derived this taxonomy from external
research but didn't map it onto the existing internal infrastructure.
Naming it as a framework would anchor future enforcement recommendations
to specific existing layers.
**Confidence: M.** Test: after documenting the framework, check whether
enforcement proposals cite the specific layer rather than proposing
generic "add enforcement."

## The keystone insight

Opportunity #1 (wiki-gate extraction) is the keystone because:
- It's the most duplicated pattern (15 skills vs 5 for evidence tiers)
- It has the clearest divergence (5/6/7 criteria — which is authoritative?)
- It converts prose to code in one move (the code-orchestrates-model-judges mandate)
- It creates the `__lib` substrate that #2 (evidence tiers) and #6 (/debrief consolidation) would naturally extend
- Every other decomposition becomes easier once the shared-library pattern is established for one cross-cutting concern

## What the session missed (meta-observation)

The session produced strong research but never stepped back to ask
"what did we miss?" until the operator explicitly invoked /tp with this
prompt. The routine-improvement cadence (opportunity #4) would make this
step automatic — but the cadence itself needs structural enforcement
(opportunity #4's own prediction). This is a recursive dependency: the
cadence that would catch missed opportunities needs a trigger that the
cadence itself would provide. The fix: create the scheduler task NOW
(opportunity #4), even before the other opportunities are addressed.

## Falsifier

These opportunities are wrong if:
- The wiki-gate extraction produces no improvement over prose (the code
  version is equally gameable) — would mean the problem is model behavior,
  not code structure
- The evidence-tier system doesn't reduce false-positive claims when
  applied workspace-wide — would mean the tier concept itself is wrong
- Step 0.5 hit rate is already high (>50%) — would mean the query works
  and the concern is misplaced
- The /debrief consolidation produces no quality gain — would mean the
  two skills serve genuinely different purposes despite overlapping output

## Related

- [[routine-skill-improvement-cadence]] — the cadence that would make these scans routine
- [[wiki-integrated-skills-query-save-pattern]] — documents the pattern per-skill; this concept proposes extraction
- [[code-orchestrates-model-judges-skill-scale]] — mandates code-enforced gates
- [[producer-consumer-contract-drift-in-skill-chains]] — predicts the /close↔/aar bug class
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
