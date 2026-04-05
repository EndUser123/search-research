# Pre-Mortem: adr_critic Agent Implementation

**Date:** 2026-04-02
**Target:** `P:\.claude\agents\adr_critic.md` (new agent) + `/arch` SKILL.md Stage 1.9 invocation
**Status:** COMPLETED

---

## Step 0: Project Constraints

From CLAUDE.md:
- Solo developer environment, 75-85% reliability target
- Hooks handle enforcement, document provides context
- Truthfulness > agreement, Evidence-first verification
- Subagent delegation for non-trivial work
- Contract Discipline: explicit validation of producer/consumer contracts

---

## Step 0.7: Kill Criteria

- If `adr_critic` cannot produce verifiable findings against actual ADR content → abandon agent pattern, use inline
- If Stage 1.9 invocation syntax doesn't work in Claude Code → revert to inline critic
- If agent output cannot be consumed by `/arch` (result envelope mismatch) → fix schema or abandon agent

---

## Step 1: Failure Scenario

**"It's 6 months later. The adr_critic agent failed. Why?"**

Scenario: `/arch` Stage 1.9 was enhanced with the critic agent. The agent runs but produces no useful output, or produces output that `/arch` cannot consume, or the agent's findings are consistently wrong.

---

## Step 1.5: Fix Side Effects

The proposed fix (creating `adr_critic` agent + Stage 1.9 invocation syntax) introduces:

1. **New entity to maintain**: `adr_critic.md` agent file must be kept in sync with Stage 1.9 rubric changes
2. **Result envelope dependency**: `/arch` must correctly consume the JSON artifact format
3. **Model selection risk**: `model="haiku"` may be insufficient for complex ADR analysis
4. **Context bloat risk**: Agent may return full analysis instead of following result envelope pattern

---

## Step 2: Brainstorm Causes (Multi-Perspective)

### People / Process
- P1: Agent reads stale version of rubric, applies wrong criteria
- P2: Result envelope written to wrong path, `/arch` can't find it
- P3: Agent skips mandatory verification step (Step 4), produces unverified findings
- P4: `/arch` doesn't wait for agent completion before proceeding to next stage

### Tech
- T1: `model="haiku"` lacks reasoning depth for complex ADR cross-checking
- T2: JSON artifact grows too large, exceeds context budget
- T3: Agent doesn't handle missing ADR file gracefully
- T4: File path with spaces or special characters breaks `adr_path` parameter
- T5: Agent uses wrong `subagent_type` (e.g., `subagent_type="haiku"` instead of `model="haiku"`)

### External
- E1: Concurrent terminal writes to same `adr_critic.json` (race condition)
- E2: Claude Code API change breaks Agent tool invocation syntax

### AI/LLM-Specific (Step 2.6)
- L1: Agent ignores Step 4 verification requirement, reports findings without checking actual ADR content
- L2: Agent produces verbose output instead of following result envelope constraint
- L3: Agent invents findings that don't exist in the actual ADR (hallucination)
- L4: Agent loses track of the 5 defect classes, wanders into stylistic criticism

### Temporal (Step 2.7)
- Temp1: Agent forgets the `verification_status` requirement after context overflow
- Temp2: `/arch` applies old Stage 1.9 rubric after skill update (version mismatch)

### Interruption / Handoff (Step 2.8)
- H1: Compaction separates agent dispatch from result consumption
- H2: Agent writes artifact but `/arch` doesn't read it after compaction
- H3: Producer (agent) completed but consumer (`/arch`) never validated result

---

## Step 2.5: Cascade Analysis

For Likelihood ≥ 2:

**T1 (haiku insufficient)** — Likelihood: 2, Impact: 2
- Cascade A: Agent produces wrong findings → `/arch` trusts wrong analysis → ADR shipped with defects → "sure" (60%)
- Cascade B: Agent times out on complex ADR → falls back to inline → feature works but agent unused → "maybe" (40%)

**P3 (skips verification)** — Likelihood: 3, Impact: 3
- Cascade A: Unverified findings passed as fact → ADR contains false claims → downstream skills build on wrong architecture → "sure" (75%)
- Cascade B: Critic flagged for producing unverifiable claims → user loses trust → agent abandoned → "maybe" (35%)

**L2 (verbose output)** — Likelihood: 3, Impact: 2
- Cascade A: Context overflow → agent response truncated → findings lost → "/arch operates on partial data" → "sure" (70%)

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| P1 | Agent reads stale rubric | Process |
| P2 | Result envelope wrong path | Tech |
| P3 | Skips verification step | Process |
| P4 | `/arch` doesn't wait | Process |
| T1 | haiku insufficient depth | Tech |
| T2 | JSON artifact too large | Tech |
| T3 | Missing ADR file | Tech |
| T4 | Path with special chars | Tech |
| T5 | Wrong model parameter | Tech |
| E1 | Concurrent write race | External |
| E2 | API change breaks syntax | External |
| L1 | Ignores verification req | AI/LLM |
| L2 | Verbose instead of envelope | AI/LLM |
| L3 | Hallucinates findings | AI/LLM |
| L4 | Wanders into style criticism | AI/LLM |
| Temp1 | Forgets verification after overflow | Temporal |
| Temp2 | Version mismatch after update | Temporal |
| H1 | Compaction separates dispatch/consume | Handoff |
| H2 | Artifact written but not read | Handoff |
| H3 | Producer complete, consumer silent | Handoff |

---

## Step 3.5: Reference Class Forecasting

Similar implementations: `adversarial-critic.md`, `code-critic.md`, `gto-code-critic.md`

From those patterns:
- Result envelope works when agent discipline is enforced
- haiku model sufficient for fixed-rubric tasks
- Verification step is the critical differentiator between useful and useless output

Base rate: 70% of agents follow result envelope correctly when instructed, 30% produce verbose output.

---

## Step 3.6: Success Theater Detection

**Specific check for adr_critic:**
- Agent produces findings that look detailed but aren't verified against actual ADR content
- `/arch` passes Stage 1.9 because agent ran, but findings are empty or wrong
- "adr_critic ran successfully" is treated as proof of quality, not actual finding accuracy

---

## Step 3.8: Operational Verification

Each HIGH risk finding requires:
- Test output showing actual failure mode, OR
- Code review excerpt showing the bug, OR
- Read of actual file:line proving the issue exists

Current evidence: The agent definition exists and follows the pattern. No operational test yet performed.

---

## Step 4: Risk Ratings

| ID | Risk | L | I | Score | Likelihood % | Confidence % |
|----|------|---|---|-------|--------------|---------------|
| P3 | Skips mandatory verification | 3 | 3 | **9** | 60% | 80% |
| L2 | Verbose output instead of envelope | 3 | 2 | **6** | 70% | 85% |
| L3 | Hallucinates findings | 2 | 3 | **6** | 40% | 70% |
| T1 | haiku insufficient for complex ADR | 2 | 2 | **4** | 35% | 75% |
| P2 | Result envelope wrong path | 2 | 2 | **4** | 30% | 80% |
| H1 | Compaction separates dispatch/consume | 2 | 2 | **4** | 40% | 65% |
| T2 | JSON artifact too large | 2 | 2 | **4** | 25% | 70% |
| L4 | Wanders into style criticism | 2 | 1 | **2** | 50% | 80% |

---

## Step 5: Prevent Top 3

**RISK-P3 (Skips mandatory verification)**
- Prevention: Agent definition explicitly lists verification as MANDATORY step with suppressed output rule
- Action: Add `verification_status` field to every finding, suppress CRITICAL findings without VERIFIED status
- Proof: Agent returns findings with `verification_status` on every item

**RISK-L2 (Verbose instead of envelope)**
- Prevention: Result envelope schema is in agent definition, return format specifies "≤3 short lines"
- Action: Agent definition explicitly limits summary to 200 chars
- Proof: Agent output contains only file path, no verbose content

**RISK-L3 (Hallucinates findings)**
- Prevention: Each finding must cite direct quote from ADR as `evidence` field
- Action: Step 3 requires direct quote + location (file:line or section)
- Proof: All findings have `evidence` field with actual ADR text

---

## Step 6: Warning Signs

**P3 (skips verification):**
- Warning: Agent findings have no `verification_status` field
- Detection: Read returned JSON, check for `verification_status` on each finding
- Trigger: If any finding missing `verification_status`, re-run agent with verification reminder

**L2 (verbose output):**
- Warning: Agent response exceeds 500 chars or contains prose analysis
- Detection: Count response length
- Trigger: If verbose, invoke `/arch` inline instead of agent

**L3 (hallucination):**
- Warning: Findings cite sections that don't exist in ADR
- Detection: Cross-check finding `location` against actual ADR structure
- Trigger: If cited section missing, suppress finding and note

---

## Step 7: Adversarial Validation

Dispatch 7 agents + critic. Source document: `P:\.claude\.evidence\pre-mortem\pm_adr_critic_20260402.md`

---

## Summary

The `adr_critic` agent follows an established pattern but has critical failure modes around:
1. **Verification discipline** — may produce unverified claims
2. **Output discipline** — may produce verbose output instead of result envelope
3. **Citation discipline** — may hallucinate findings not in actual ADR

These are addressable through explicit agent definition constraints and `/arch` consumption validation.