---
title: "Workspace improvement cycle: 6-stage decomposition and implementation priorities"
created: 2026-07-29
source: session-019fa276 (/tp exploration on system improvement)
tags: [improvement-cycle, self-improvement, system-design, sense-remember-decide, transcript-mining, harvest, measurement-gap, prioritization]
agent: grok
host: both
cognitive_load: 3
verification: observed
summary: >
  The workspace improves through a 6-stage cycle: SENSE (detect failures)
  → REMEMBER (persist discoveries) → DECIDE (prioritize) → ACT (execute)
  → VERIFY (confirm fix) → MEASURE (did it help?). Layers 1-5 are partially
  built. Layer 6 (MEASURE) does not exist — the system gets bigger but we
  don't know if it gets better. The cross-session transcript scanner
  (implemented 2026-07-29) was the highest-leverage gap: it connects the
  SENSE layer to the REMEMBER layer automatically, turning harvest from a
  manual notepad into an automatic recovery system.
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/cross-session-transcript-mining-continuous-improvement.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Workspace improvement cycle: 6-stage decomposition

## Decision context

**The problem:** the operator asked "what are all the things we would want
to do to improve our system so that it keeps getting better?" The question
requires a structural answer — not a list of 50 items, but a framework that
identifies which investments compound and which are dead ends.

**The decomposition:** the improvement system itself has stages. Each stage
transforms signals into actions. If a stage is missing or broken, the stages
downstream starve. The framework identifies where to invest.

## The 6-stage cycle

```
SENSE → REMEMBER → DECIDE → ACT → VERIFY → MEASURE
  │        │         │       │      │         │
  │        │         │       │      │         └─ does the improvement help?
  │        │         │       │      └─ did the fix work?
  │        │         │       └─ execute the improvement
  │        │         └─ prioritize what to act on
  │        └─ persist the discovery
  └─ detect failures and opportunities
```

### Layer 1: SENSE — detecting what's wrong or possible

**What works:**
- /aar analyzes one session deeply (event timeline, value accounting, lessons)
- /tp session scans transcripts for friction patterns (exit codes, corrections)
- Compaction segment analysis via subagent-per-segment pattern (committed
  2026-07-29) ensures ground truth, not lossy summaries

**What was missing (now built):**
- **Cross-session transcript scanner.** `analyze_session_patterns.py` was
  extended to extract 9 mechanical signal types from the full session chain.
  Found 38 obligations across 6 sessions on first run. Writes to
  `P:/.data/harvest/pending/` for automatic harvest discovery. Receipt:
  `P:/.agents/scripts/analyze_session_patterns.py`, commit `efe8891`.

**Still missing:**
- Live state probes (databases, queues, auth) are not routinely queried
- The scanner finds mechanical signals but doesn't extract semantic
  obligations (e.g., "operator asked for X, was it done?") — that requires
  LLM analysis per session, which is expensive

### Layer 2: REMEMBER — persisting what was learned

**What works:**
- Wiki concepts: durable, well-structured, validator-enforced quality
- AGENTS.md: accumulated correction rules (though they fire ~66%)
- Harvest event store: lifecycle-tracked obligations with claim-based concurrency

**What's broken:**
- **Harvest was a manual notepad.** All items hand-typed. The cross-session
  scanner fix (Layer 1) now feeds it automatically, but the scanner only
  writes mechanical signals. Semantic obligations still require manual capture.
- **Nothing decays.** 400+ wiki concepts, 151+ handoffs, 989 skills, 13+
  harvest items. All equally weighted. In a year, the store will be
  unscannable. cass-memory has confidence-decay with half-life; our harvest
  has the `--half-life` flag but nobody sets it.
- **AGENTS.md rules fire ~66%.** We keep adding behavioral rules. The wiki
  documents this at `llm-instruction-non-compliance-activation-gap-2026`.
  We keep adding rules anyway.

### Layer 3: DECIDE — prioritizing what to act on

**What works:**
- /todo produces a prioritized list (though output quality needed fixing)
- Harvest orders by value/hour

**What was fixed (2026-07-29):**
- /todo SKILL.md gained 10 concrete synthesis rules with wrong/correct examples
- Harvest gained `--cost-of-inaction` field (what happens if we do nothing?)

**Still missing:**
- All harvest items default to 5.0 value/hour. No real differentiation.
- No improvement kata (weekly bottleneck + experiment routine)

### Layer 4: ACT — executing the improvement

**What works:**
- /go implements. Skills are operational. Execution is the strongest layer.

**What's broken:**
- Items never reach execution. The sensing/remembering/deciding layers don't
  route items to execution reliably. The quality-gate timeout fix had a
  handoff for 1 day and didn't move. 6 problem-prediction skills had a
  handoff for 2 days and didn't move.

### Layer 5: VERIFY — confirming the fix worked

**What works:**
- edit-then-verify, /check, /review, quality_gate hook — mechanical and reliable

**What's broken:**
- Harvest's arm→verify→collect chain is unused. Items are closed with
  `harvest close` (no verification), not `harvest collect` (requires passing
  verification). "Closed" means "I decided it was done," not "verified done."

### Layer 6: MEASURE — did the improvement actually help?

**Nothing exists here.**

The system has 989 skills, 400+ wiki concepts, 151 handoffs, 100+ AGENTS.md
rules. Zero measurement of whether any improved outcomes. We add, add, add.
We never measure.

- Did the "exploration vs execution" rule reduce action-bias incidents? Unknown.
- Did the compaction-segment-analysis fix produce better session reviews? Unknown.
- Did the /tp opportunity scan gate reduce the research-to-execution loop? Unknown.
- Are the 400+ wiki concepts being read and applied, or write-only? Unknown.

recursive-improve (from the ecosystem survey) comes closest with before/after
benchmarking on code tasks. But system-level improvement measurement — "did
this rule/hook/skill edit make the fleet better?" — nobody has built.

## What was implemented this session

| Stage | What was built | Commit |
|-------|---------------|--------|
| SENSE | Cross-session transcript scanner (9 signal types, compaction-aware) | `efe8891` |
| REMEMBER | Scanner writes to pending/ for harvest auto-discovery | `efe8891` |
| DECIDE | /todo synthesis rules + cost-of-inaction field | `f47eaff` |
| VERIFY | (No change — arm→verify→collect still unused) | — |
| MEASURE | (Nothing — still the deepest gap) | — |

## Prioritization rationale

The cross-session scanner was prioritized first because it's the **pipeline
connector**. Without it, the REMEMBER layer (harvest) is manually fed, and
the DECIDE layer (/todo) sees only what was hand-captured. With it, the
SENSE layer automatically feeds REMEMBER, which feeds DECIDE. The pipeline
runs end-to-end for mechanical signals.

The MEASURE layer was deprioritized because measurement design is genuinely
hard — you need before/after baselines, control groups, and a definition of
"better" that's measurable. Starting that before the pipeline works would be
premature optimization.

## Falsifier

This framework is wrong if:
- The mechanical signals the scanner extracts are too noisy to be useful
  (38 items from 6 sessions — if 35 are false positives, the scanner adds
  noise, not signal)
- Harvest's store becomes a graveyard that nobody reads (the manual-notepad
  problem repeats at larger scale)
- The pipeline works mechanically but the DECIDE layer can't prioritize
  effectively (all items still look equally urgent)
- The MEASURE gap turns out to be unbridgeable for agent fleets (no clean
  definition of "better")

## Receipts

- Cross-session scanner: `P:/.agents/scripts/analyze_session_patterns.py`
  extended 2026-07-29, commit `efe8891`. First run: 38 items across 6 sessions.
- /todo synthesis rules: `~/.grok/skills/todo/SKILL.md`, commit `f47eaff`
- Harvest cost-of-inaction: `~/.grok/skills/harvest/scripts/harvest.py`,
  commit `f47eaff`
- Ecosystem survey validating the 3-layer architecture:
  [[cross-session-transcript-mining-continuous-improvement]]
- Huang 2024 caveat (external signal requirement):
  [[self-improving-agent-systems-techniques-and-workspace-gaps]]
- Behavioral rules fire ~66%, justifying mechanical enforcement:
  [[mechanical-enforcement-over-behavioral-reminder]]
- Harvest value gap (manual notepad, not automatic recovery):
  [[research-to-execution-ratio-self-reinforcing-pattern]]
