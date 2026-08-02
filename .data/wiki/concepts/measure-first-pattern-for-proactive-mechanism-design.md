# Measure-First Pattern for Proactive Mechanism Design

**Provenance:** /design run 2088aada, 2026-08-02. Critical friend round 1 reframing of the LLM-Judge Stop Hook design.

**Host:** grok

## Decision

When designing a proactive mechanism (hook, auto-fire skill, automated injection) that will impose ongoing cost (latency, token budget, cognitive load), **measure the problem the mechanism solves BEFORE building the mechanism.** Ship a passive data-collection phase (zero behavioral change, zero API cost) that quantifies the gap. Only build the active mechanism if the measured gap justifies it.

## Why

The original design proposed building a two-stage LLM-judge Stop hook immediately, running it in shadow mode, then deciding whether to go live. The critical friend reframed this: shadow mode still pays the judge's API cost and assumes the problem exists. A passive log is cheaper and gives stronger evidence.

**Specifically for the observation-surfacing hook:**
- Phase 0 (passive): two log-only hooks record tool calls + agent output. Analysis script computes the missed-observation rate. Zero API cost, zero behavioral change, zero continuation budget consumed.
- Phase 1 (active): LLM judge is built ONLY if Phase 0 shows ≥0.5 missed observations per session.

## Alternatives rejected

1. **Build-and-shadow** (the original design): build the judge, run in shadow mode, decide later. Rejected because shadow mode pays API cost on every turn for a problem that may not exist. The passive log is free.
2. **Build-live-immediately** with conservative threshold. Rejected because cry-wolf fatigue is asymmetric: one noise observation trains the operator to ignore future ones (Chen et al. CHI 2025, preference drop 80→47% at higher frequency).

## Transferability

This pattern applies to ANY proactive mechanism design where:
- The mechanism imposes ongoing cost (latency, tokens, cognitive load)
- The problem it solves is unmeasured ("we think X happens ~60-70% of the time" but no data)
- A passive data-collection path exists that doesn't require the active mechanism

## Falsifier

This pattern is wrong if: the passive measurement phase takes so long (months) that the problem it would solve causes significant damage before data arrives. In that case, building the active mechanism with aggressive fail-safe defaults is the better trade-off.

## Related

- [[proactive-ai-volunteering-mechanisms]] — the three-mechanism ladder this design extends
- [[llm-judgment-hooks]] — hook-based LLM judge pattern
- [[behavioral-detection-approaches-practitioner-survey]] — two-stage filter evidence
- Design doc: `C:\Users\brsth\AppData\Local\Temp\grok-design-2088aada\grok-design-doc-2088aada.md`
