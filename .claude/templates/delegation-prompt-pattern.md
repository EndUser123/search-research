# Delegation Prompt Pattern

One template, factored: an **invariant core** plus two orthogonal **axis
blocks**. Compose a concrete prompt by taking the core and picking one option
from each axis. Do not maintain standalone per-use-case templates — they
drift apart like any duplicated document.

Growth rule (Replacement Default applied to templates): a new **axis** earns
a change to this file; a new **instance** is just a new pick of existing
switches. Add nothing until an actual delegation fails under the current
factoring.

---

## The 2×2

|                | Executor (deliver artifacts)      | Thought partner (deliver decisions) |
|----------------|-----------------------------------|-------------------------------------|
| **Simple model** | ✅ procedure-heavy                | ❌ don't — judgment-dense contract, judgment-poor delegate |
| **Peer model**   | ✅ context-heavy                  | ✅ context-heavy + position-taking  |

Three viable cells = the three observed use cases (2026-07-09 session:
audit-cleanup prompt, git-setup delegate, root-cause conversation).

---

## Invariant core (every prompt, every cell)

1. **Evidence-cited claims.** Every factual claim names its artifact
   (file:line, command output, tool result). "Command ran ≠ result correct"
   is a property of the world, not of the model — peers produce silently
   truncated writes too.
2. **Explicit boundaries.** What is in scope, what is off-limits, and the
   authorization level (proceed / propose-then-wait), stated in the prompt,
   scaled by reversibility.
3. **Written residue.** A report at a known path: everything changed or
   concluded, everything skipped or deferred, one-line justification each.
   The residue is how you audit the delegate without replaying its session,
   and the requirement itself suppresses silent skipping.
4. **A legitimate "I don't know."** An explicit, non-penalized way to mark
   unknowns and hand items back. Models fabricate hardest when the prompt
   leaves no dignified exit.
5. **Spec-anchored review.** Before any self-review or scope change, re-quote
   the original acceptance criteria from this prompt. A scope cut is a SPEC
   DEVIATION, stated as "spec requires X; propose dropping X because Y" —
   never folded silently into an "MVP" framing. Minimalism's guard clause
   applies: never simplify away the explicitly requested thing.
   (Origin: backlog #20 — a review cut block/warn outcome tracking, the
   module's entire purpose, and called it discipline.)
6. **Reproduce-first + risk register.** A fix for a reported symptom must
   cite the captured failing artifact (rc/stdout/stderr) it is designed
   against; if you cannot reproduce it, say so and stop — do not hedge.
   The residue ends with a RISK REGISTER: each open assumption with severity
   and its smallest falsifier, and a closure pass — close every cheaply
   closable risk (read-only checks, scoped commits) before handoff.
   "Expected", "transient", or "known limitation" without a citation is
   prohibited; the hedge is the tell.
   (Origin: backlog #21 — an unreproduced fix targeted the wrong output
   channel and the residual was narrated as "expected".)

---

## Axis 1 — Capability (what the prompt must supply)

**SIMPLE → supply judgment (procedure-heavy):**
- Detector-driven scope: anchor every task to an existing tool's output;
  the detector defines done, the model cannot expand or shrink scope.
- Classification buckets: pre-enumerate finding categories with a mechanical
  rule each, always including a "report, don't decide" bucket.
- Fix the generator, never hand-edit derived artifacts.
- One change per Read→Edit→Verify cycle; batch failures compound silently.
- Verification command spelled out per task, verbatim.

**PEER → supply context (context-heavy):**
- Context transfer is the bulk of the prompt: what was tried, why it failed,
  which constraints are spec vs preference, and environmental traps
  ("the mount truncates writes ~11.6KB — checksum after copy"; "sandbox is
  3.10, prod 3.13 — syntax findings are provisional").
- Objective, not task list: state the goal and let the peer decompose.
- Decision criteria instead of buckets ("prefer delete over gate; a kept
  fallback needs explicit justification"), plus a **decision log**: every
  judgment call recorded with rationale.
- Invariants instead of procedure ("no unverified state at handoff"), and
  reversibility-scaled authorization instead of a flat don't-touch list.
- Cheapest tool that answers the question (extends Cost Tiering):
  mechanical questions (count, locate, cross-reference, scan) get scripts
  whose output lands in a file; semantic questions (why, intent,
  correctness) get targeted reads of the excerpts the scripts point at.
  GUARDRAIL: token economy changes HOW you look, never WHETHER you look —
  it can shrink a read, never replace an investigation with an assumption.
  Anti-overhead: if the script costs more than reading 100 lines, read.
  Keep analysis scripts until the report ships — script-derived claims are
  re-runnable at review; context-derived claims are not.

---

## Axis 2 — Contract (what the deliverable is)

**EXECUTOR → artifacts, verified:**
- Detector defines done: baseline the detector before, re-run after, compare.
- Act-then-verify by default within authorized scope.
- Success = detector output, never self-report.

**THOUGHT PARTNER → decision material, evidenced:**
- Evidence defines assertability: no audit script can score a framing, so
  verification moves from the output to the reasoning — claims cite
  artifacts, unknowns stay labeled, gaps are named instead of narrated over.
- Investigation is still mandatory: a partner who hasn't read the evidence
  is a rubber duck. "Stop at findings" ≠ "don't go looking."
- **Position-taking is mandatory:** a committed recommendation with the
  decision criterion named, plus the falsifier — what evidence would flip
  it. Symmetric option lists are skipped work. The "I don't know" exit
  survives only as "I recommend X, contingent on unverified Y."
- **Disagreement is a deliverable:** state where the requester's framing or
  question is wrong before answering it. Sycophancy is this contract's
  version of silent skipping.
- Action boundary hardens to Documentation Boundary: investigate, stop at
  findings, act only on explicit "do it."

---

## Composed skeletons (worked examples, not separate sources of truth)

### A. Simple executor  (core + SIMPLE + EXECUTOR)
```
You are working in <root>. Your job is mechanical cleanup driven by
<detector>. Do not redesign anything. One file per Read->Edit->Verify cycle;
never claim fixed without re-running the check that detected it.

SETUP: run <detector>; save baseline to <path>.

TASK n — <finding category>
  - <mechanical rule, or buckets a/b/c where one bucket is
    "needs human decision — do not modify">
  - Verify each fix: <exact command>

FINISH: re-run <detector>, save to <path>, compare to baseline. Write
<report path>: counts before/after, every change, every skipped item with
one-line justification. Do NOT touch: <explicit list>.
```

### B. Peer executor  (core + PEER + EXECUTOR)
```
OBJECTIVE: <goal, not task list>.

CONTEXT: <what was tried and why it failed; constraints that are spec;
environmental traps with the verification that catches each>.

DECISION CRITERIA: <e.g., prefer delete over gate; solo-appropriate over
enterprise; cheapest model that does the job>. Keep a decision log: every
judgment call, one line of rationale.

AUTHORIZATION: trivial/reversible — proceed; breaking/irreversible —
propose and wait. Invariant: no unverified state at handoff.

DONE = <detector/check> passes; baseline it first. Residue: <report path>
with changes, decisions, deferrals, unknowns.
```

### C. Peer thought partner  (core + PEER + PARTNER)
```
QUESTION: <the decision to be made, and why it's live now>.

CONTEXT: <evidence available and where; what's already been considered;
constraints that are spec vs preference>.

INVESTIGATE FIRST: ground claims in artifacts (file:line, command output).
Label unknowns as unknowns; name what you did NOT check.

DELIVER: (1) where my framing or question is wrong, if it is;
(2) a committed recommendation with the decision criterion named;
(3) the falsifier — what evidence would flip your recommendation;
(4) decision log for any judgment calls made while investigating.

BOUNDARY: stop at findings. No implementation without explicit "do it".
```

---

## Failure modes -> countermeasures

| Failure | Countered by |
|---------|--------------|
| Claims success without checking | core #1 + executor: detector defines done |
| Invents scope | simple: detector-driven scope · peer: objective + authorization |
| Guesses on ambiguous cases | simple: escape-hatch bucket · peer: decision log |
| Hand-edits generated artifacts | simple: fix the generator |
| Batch corruption caught late | simple: one change per cycle · peer: no-unverified-handoff invariant |
| Silently skips hard items | core #3: skips must appear in residue |
| Cold-start context loss (peer) | peer: context transfer + trap documentation |
| Option-list hedging (partner) | partner: mandatory position + falsifier |
| Sycophantic framing polish (partner) | partner: disagreement is a deliverable |
| Armchair analysis (partner) | partner: investigation mandatory, evidence-cited |
| Thrift as laziness ("skipped reading to save tokens") | peer: guardrail — economy shrinks reads, never skips investigation |
| Script-blindness (semantic question answered mechanically) | peer: question-type rule — why/intent/correctness requires reading |
| Scope cut dressed as minimalism | core #5: re-quote spec; cuts are named deviations |
| Fix designed from assumed model, not the failure | core #6: reproduce-first — cite the captured artifact |
| Residual failure narrated as "expected" | core #6: risk register — falsifier or silence, never a hedge |

Origin: 2026-07-09 session. Companion:
P:/.claude/templates/llm_behavior_contract.md (behavior contract the
delegate operates under).
