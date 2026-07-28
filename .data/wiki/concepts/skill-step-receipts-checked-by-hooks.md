---
title: "Skill-step receipts checked by hooks: what they catch, what they miss"
created: 2026-07-27
source: session-019fa276 (/www on receipt-checked skill steps)
tags: [receipt, skill-enforcement, stop-hook, mandatory-step, closure-pressure, lexical-vs-semantic, ceremony-cost, micro-scale]
summary: >
  Design analysis: if skills wrote receipts for their critical steps and a
  Stop hook checked whether the receipts existed, would that ensure proper
  skill usage? Answer: YES for the specific failure class it targets
  (skipping steps under closure pressure — the /www Phase 3 skip this
  session is the canonical example). NO for the failure class it doesn't
  target (doing steps badly — a thin wiki concept passes the receipt check
  but isn't good). We already have the infrastructure (quality_gate.py,
  verification_receipt_writer.py, wiki_state.py lifecycle); the gap is
  extending it from code-change receipts to skill-step receipts at the
  micro-scale (per code-orchestrates-model-judges-skill-scale). Three
  concrete proposals, with the ceremony-cost tradeoff from
  fabrication-ceremony-tax-compounding-cost.
agent: grok
host: grok
cognitive_load: 3
verification: cross_referenced_to_workspace
sources:
  - "P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md" (the foundational principle)
  - "P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md" (micro-scale gap)
  - "P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md" (visible output for silent steps)
  - "P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md" (receipts prove "ran" not "correct")
  - "P:/.data/wiki/concepts/wiki-lifecycle-state-file.md" (existing skill-step state tracking)
  - "P:/.data/wiki/concepts/fabrication-ceremony-tax-compounding-cost.md" (ceremony cost warning)
  - "P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md" (existing hook infrastructure)
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: applies
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: implements
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: extends
  - target: wiki/concepts/lexical-vs-semantic-verification-gap.md
    type: acknowledges_limitation
---

# Skill-step receipts checked by hooks

## Decision context

**Why this analysis was needed:** during this session, the agent invoked
`/www` twice. Both times, it completed Phase 1 (query) and Phase 2
(research) but asked "want me to persist?" instead of executing Phase 3
(write to wiki). The operator corrected: "I used the /www skill, thus it
should have already been persisted." The question is whether a hook that
checks for skill-step receipts would have caught this automatically.

## The honest answer: yes, for what it targets. No, for what it doesn't.

### What receipt-checking hooks WOULD catch

The failure mode is **step skipping under closure pressure** — the model
wants to finish, so it downgrades a mandatory step (Phase 3 = "write wiki
concept") to an optional step ("want me to persist?"). This is the exact
failure class documented in [[mandatory-step-enforcement-code-over-prose]]:

> "Prose instructions are advisory — they can be downgraded, softened, or
> skipped under context momentum."

A hook that checks "was `/www` invoked this session? If yes, does a wiki
concept file exist with today's date?" would have blocked the Stop event
with "Phase 3 receipt missing: no wiki concept written for this /www run."
The model would have been forced to either write the concept or explicitly
explain why it's deferring.

**This works because the check is mechanical, not interpretive.** The hook
doesn't need to evaluate whether the concept is good — it only checks
whether it exists. That's a file-system operation, not an LLM judgment.

### What receipt-checking hooks WOULD NOT catch

Per [[lexical-vs-semantic-verification-gap]], a receipt proves the step
**ran**, not that it was **done correctly**:

| What the receipt proves | What it doesn't prove |
|---|---|
| A wiki concept file was created | The concept is non-thin (≥80 lines, ≥3 wikilinks) |
| The file has the right frontmatter | The sources are real and verified |
| The file passed validate_wiki_entry.py | The disconfirmation pass actually ran |
| A handoff was written | The handoff has actionable next steps |

The receipt catches the "didn't do it at all" failure (the `/www` Phase 3
skip). It does NOT catch the "did it badly" failure (wrote a thin summary
instead of a wiki concept). The validator (`validate_wiki_entry.py`) is the
partial defense for the latter — but it only checks structure, not content
quality.

**The implication:** receipt-checking is necessary but not sufficient. It
raises the floor (can't skip entirely) without raising the ceiling (can't
guarantee quality). Both layers matter; they catch different failure
classes.

## We already have the infrastructure

This is not a new idea on this workspace. It's an extension of existing
patterns to a new scale:

| Layer | What exists | What it checks | Source |
|---|---|---|---|
| **Code-change receipts** | `verification_receipt_writer.py` (PostToolUse) + `quality_gate.py` (Stop) | Modified file → verifier command → receipt with scope | [[instruction-to-state-closure-gap-obligation-ledger]] |
| **Wiki lifecycle state** | `wiki_state.py` | `discovered → ingesting → linking → linting → complete` state machine | [[wiki-lifecycle-state-file]] |
| **Close accounting** | `close_accounting.py` | Scans handoffs, wiki, git, temp for evidence of completion | [[code-orchestrates-model-judges-skill-scale]] |
| **AAR enforcement** | Scanner checks for AAR completion receipts | Was `/aar` run before `/close` declares done? | [[close-auto-invokes-aar]] |

The gap, per [[code-orchestrates-model-judges-skill-scale]], is at the
**micro-scale**: within a single skill, where the helper script should gate
the model through the skill's own mandatory steps. Our hooks cover code
changes (meso-scale) and the close pipeline checks overall completion
(close-scale). No hook currently checks: "was `/www` Phase 3 completed?"

## Three concrete proposals (ascending complexity)

### Proposal A: Skill invocation tracking + Stop hook check (simplest)

1. When a skill is loaded (detected via the system-reminder mechanism),
   write a `.artifacts/<session>/skill-invocations.jsonl` entry:
   `{"skill": "www", "invoked_at": "<timestamp>", "phases": [1,2,3]}`
2. When each phase completes, update the entry with the phase number +
   receipt (file path, command output, etc.)
3. The Stop hook (or `/close` scanner) reads the invocations file and
   checks: for each invoked skill, are all declared phases marked complete?
4. If not, block with "Skill `www` Phase 3 receipt missing."

**Cost:** ~50 lines of new code (invocation tracker + Stop hook extension).
**Ceremony cost:** one additional file read per Stop event (~5ms).
**Catches:** step skipping under closure pressure.

### Proposal B: Per-skill state files (like wiki_state.py)

1. Each skill that has mandatory steps declares a state schema:
   `/www`: `{phase1_complete: bool, phase2_complete: bool, phase3_complete: bool}`
2. The skill writes to `.artifacts/<session>/<skill>-state.json` as it
   progresses
3. The Stop hook checks: for each skill-state file that exists, are all
   required phases marked true?
4. If not, block with the specific missing phase

**Cost:** ~30 lines per skill (state writer) + ~40 lines hook extension.
**Ceremony cost:** one file read per skill per Stop event.
**Catches:** step skipping; partial completion.
**Already proven:** `wiki_state.py` does this for `/wiki` operations.

### Proposal C: Micro-scale orchestrator (per code-orchestrates-model-judges)

1. Each skill with mandatory steps gets a `__lib/<skill>_accounting.py`
   that scans for evidence of step completion
2. The accounting script is called by the Stop hook for any skill invoked
   this session
3. The script resolves each step to a state (`satisfied`, `needs_attention`,
   `blocked`) and returns a loop decision
4. The Stop hook blocks if any step is `blocked`

**Cost:** ~150 lines per skill (accounting script) + ~60 lines hook extension.
**Ceremony cost:** one subprocess call per skill per Stop event (~100ms).
**Catches:** step skipping; partial completion; evidence quality (if the
accounting script checks for evidence depth, not just existence).
**This is what `/close` already does** — `close_accounting.py` is the
reference implementation.

## The ceremony-cost tradeoff

Per [[fabrication-ceremony-tax-compounding-cost]], the workspace already
has a large ceremony layer (15 close-scanner gates, 4 validators, receipt
rules). Adding per-skill receipt checking increases that cost. The design
question is: **which skills' steps are worth the ceremony?**

| Skill | Critical step that gets skipped | Worth receipt-checking? |
|---|---|---|
| `/www` | Phase 3 (persist to wiki) | ✅ YES — observed skip this session |
| `/check` | Verify claims against evidence | ✅ YES — the whole point of the skill |
| `/wiki` | Validate before persisting | ✅ Already enforced (wiki_state.py) |
| `/handoff` | Write handoff file (not just say "I'll write it") | ✅ YES — observed non-write failures |
| `/red-team` | Root-cause clustering before verdict | ⚠ Maybe — high ceremony cost per run |
| `/tp` | Verification against session evidence | ⚠ Maybe — the critique is the value |
| `/go` | H6 verify before "GO DONE" | ✅ Already partially enforced |
| `/close` | All 14 gates | ✅ Already enforced (close_accounting.py) |

**Recommendation:** start with Proposal A (simplest) for the three skills
with observed skip failures (`/www` Phase 3, `/handoff` write, `/check`
verify). Measure whether the hook catches real skips vs false positives.
If it earns its cost, extend to Proposal B/C for broader coverage.

## Falsifier

Receipt-checking hooks are over-engineering if:
- The step-skip rate is low enough that prose rules suffice. **Observed:**
  `/www` Phase 3 was skipped 2/2 times this session. The rate is not low.
- The hook fires false positives (blocks when the step was legitimately
  skipped — e.g., research produced no unique findings). **Mitigation:**
  the hook should allow the model to explicitly mark "Phase 3 deferred:
  research produced no unique findings" with a reason field.
- The ceremony cost exceeds the value. **Testable:** track false-positive
  blocks vs real-skip catches over 3 months. If the ratio is <1:3, the
  ceremony isn't earning its cost.

## Receipts

All claims about existing infrastructure are from wiki concepts verified
in this session:

- **"quality_gate.py already checks receipts for code changes":**
  receipt — `P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md`
  line 83: "quality_gate.py (this workspace) Stop hook: verification receipts,
  scope binding, obligation tracking"
- **"wiki_state.py already does lifecycle tracking":**
  receipt — `P:/.data/wiki/concepts/wiki-lifecycle-state-file.md` documents
  the `discovered → ingesting → linking → linting → complete` state machine
  with `wiki_ingest.py` refusing exit-0 on lifecycle tracking failure.
- **"close_accounting.py is the micro-scale reference implementation":**
  receipt — `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md`
  line 91: "Skill's __lib/*.py gates the LLM through mandatory steps; refuses
  to advance until coverage exists"
- **"the /www Phase 3 skip happened twice this session":**
  receipt — this session's transcript; the operator's correction "I used
  the /www skill, thus it should have already been persisted" was the
  second instance.

## Sources

- `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` —
  the foundational principle: move enforcement from prose to code
- `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` —
  the micro-scale gap: skill helper scripts should gate the model
- `P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md` —
  silent steps have zero friction to skip
- `P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md` —
  receipts prove "ran" not "correct"; the critical limitation
- `P:/.data/wiki/concepts/wiki-lifecycle-state-file.md` —
  existing skill-step state tracking (the proven pattern)
- `P:/.data/wiki/concepts/fabrication-ceremony-tax-compounding-cost.md` —
  ceremony cost warning; the workspace already has a large ceremony layer
- `P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md` —
  existing Stop hook infrastructure and the additionalContext feedback mechanism

## Auto-related

- [[mandatory-step-enforcement-code-over-prose]] — the principle this implements
- [[code-orchestrates-model-judges-skill-scale]] — the micro-scale gap this fills
- [[visible-output-contracts-for-behavioral-skill-steps]] — silent steps need visible output
- [[lexical-vs-semantic-verification-gap]] — the limitation of receipt-based enforcement
- [[wiki-lifecycle-state-file]] — the existing pattern to extend
- [[fabrication-ceremony-tax-compounding-cost]] — the cost tradeoff
