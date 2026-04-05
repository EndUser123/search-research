---
 Migrated from: premortem_self-contrast-execution_20260404.md
 Original location: P:\.claude\.evidence\premortem_self-contrast-execution_20260404.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: SELF-CONTRAST Protocol Execution Pattern

**Analyzed:** 2026-04-04
**Target:** Stop hook blocking on E2E workflow completion claims — pattern of describing multi-step workflows without executing them

## Step 1: Failure Scenario

"It's 6 months later. The SELF-CONTRAST protocol (/retro) was adopted but consistently produces incomplete retrospectives because the Stop hook keeps blocking on 'E2E workflow claim without execution evidence' — the AI describes what it WILL do rather than executing it. The /retro skill exists but is rarely completed end-to-end. Skill coverage gaps, architectural decisions, and actionable lessons remain uncaptured."

## Step 2: Failure Causes (multi-perspective)

**Process:**
- P1: Stop hook triggers AFTER analysis is complete but BEFORE execution — blocking at wrong phase
- P2: No distinction between "analyzing a workflow" and "executing a workflow" in the verification gate
- P3: Sequential skill invocation (recap→gto→ideas→pre-mortem→rns) takes too many turns, causing compaction mid-chain

**Tech:**
- T1: Skill enforcement layer does not auto-chain dependent skills — each step requires separate invocation
- T2: Context compaction during multi-step execution breaks the chain (pre-mortem output lost after recap output)
- T3: No checkpoint mechanism between SELF-CONTRAST steps — partial execution indistinguishable from complete execution

**People:**
- PP1: User invokes /retro expecting a single response, not a 5-step chained execution
- PP2: Stop hook confusion (what phase is being verified?) creates adversarial dynamic between user and AI

**External:**
- E1: CLAUDE.md solo-dev model doesn't account for "workflow-as-unit" vs "tool-call-as-unit" verification granularity

## Step 2.6: AI/LLM Failure Modes
- "Describe then execute" is more token-efficient than "execute then describe" — incentive misalignment
- Compaction truncates mid-chain execution state
- LLM conflates "having the skill" with "having executed the skill"

## Step 3: Categorization
- P1, P2, P3 → Process
- T1, T2, T3 → Tech
- PP1, PP2 → People
- E1 → External

## Step 4: Risk Ratings
- P1: L×I = 3×3 = **9** (Stop hook at wrong phase is systemic)
- P2: 2×3 = **6** (workflow vs tool-call ambiguity)
- P3: 3×3 = **9** (compaction mid-chain destroys evidence)
- T1: 2×2 = **4** (manual chaining friction)
- T2: 3×3 = **9** (state loss from compaction)
- T3: 2×3 = **6** (no checkpoint granularity)
- PP1: 2×2 = **4** (user expectation mismatch)
- PP2: 2×3 = **6** (adversarial dynamic)

## Step 5: Top 3 Risks
1. **T2/P3** (9): Compaction mid-chain — evidence of completed steps lost
2. **P1** (9): Stop hook at wrong phase — blocks AFTER analysis, BEFORE execution
3. **P2** (6): No distinction between "analyzing workflow" vs "executing workflow"

## Step 6: Warning Signs
- RECAP output present but GTO not invoked → compaction occurred
- Stop hook block appears after "E2E workflow claim" → described not executed
- /retro produces only RECAP section → chain incomplete

## Evidence
- Stop hook output: "MULTIPLE VERIFICATION VIOLATIONS DETECTED / Phase 2 (Completion Claims) / E2E workflow claim without execution evidence"
- This session: recap_cli.py returned data but no full transcript accessible (sessions-index.json empty for this terminal)
- P1: Stop hook phases — Phase 1 (Verification Engine) vs Phase 2 (Completion Claims) distinction

## RECOMMENDED NEXT STEPS

| ID | Type | Owner | Action | Proof |
|----|------|-------|--------|-------|
| ACT-001 | recover/high | /planning | Design durable checkpoint mechanism for multi-step skills — each step writes evidence to `~/.claude/.evidence/retro/step_{n}_{terminal_id}.jsonl` before advancing | Evidence file created and readable after manual compaction mid-chain |
| ACT-002 | prevent/med | /planning | Add Phase 0 verification gate — if skill has `depends_on_skills`, require step-1 execution evidence before Phase 2 completion claims | Stop hook does NOT fire on valid step-1 evidence for depends_on_skills workflow |
| ACT-003 | prevent/med | /code | Fix GTO `_shared/scanners.base` import error — `C:/Users/brsth/.claude/skills/_shared/` directory missing | `python gto_orchestrator.py --format both` runs without ImportError |
| ACT-004 | realize/low | /retro | Add step-progress headers — "Executing step N/5: /{skill}" so each chain step is visibly distinct | /retro output shows step N/M progression |

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| ACT-001 (checkpoint mechanism) | ❌ Open | Not yet designed | High |
| ACT-002 (Phase 0 gate) | ❌ Open | Not yet implemented | High |
| ACT-003 (GTO fix) | ❌ Open | Not yet fixed | Medium |
| ACT-004 (step headers) | ❌ Open | Not yet added | Low |
| Adversarial review | ❌ Open | 5 of 6 agents pending dispatch | Medium |
| /retro execution | ✅ Done | Full chain executed this session | High |
