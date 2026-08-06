# Insight Skill Improvement Directions

**Date:** 2026-08-07
**Session:** 019fd820
**Status:** ACTIVE — research findings, implementation pending
**Research method:** `/www` (wiki baseline → web research → wiki persist)

## Context

`/insight` consolidates `/capture` + `/friction` + `/harvest` into a unified
improvement-finding skill with 4 modes (default, --skills, --fleet, --coverage).
This concept documents research-backed directions for making it find more
improvements and produce higher-quality findings.

## Sources

1. **Augment Code — Agent Learning Flywheel** (2026-05): 4-stage architecture
   (execute → coach → distill → improve) for turning agent experience into
   reusable knowledge. Identifies 5 architectural properties of learnable agents.
2. **Datagrid — 7 Tips for Self-Improving AI Agents** (2025-07): architectural
   patterns for safe feedback loops, including reflection-safe architecture and
   goal alignment preservation.
3. **agent-patterns.readthedocs.io — Reflection Pattern**: generate-critique-refine
   cycle with explicit reflection criteria and role separation.
4. **SLIM (arxiv 2605.10923)** — already in workspace via `/skill-dev`.
5. **Generative Agents (arxiv 2304.03442)** — recency + importance + relevance
   retrieval scoring.
6. **Reflexion (arxiv 2303.11366)** — verbal reflection on feedback signals stored
   in episodic memory: 91% pass@1 on HumanEval vs 80% baseline.
7. **CoALA (arxiv 2309.02427)** — 4 memory types, verification gates on
   procedural writes.

## What `/insight` already does well

- 9 categories with dual-stream routing (knowledge vs improvement)
- Friction markers enriched into categories 1-2
- Pre-compaction recovery (full-session evidence window)
- Coverage check (did capture skills run?)
- Post-output routing (every friction finding needs a resolution artifact)
- Self-improvement boundary (Rung 5 forbidden — consumer-only wiki reads)

## Improvement directions (ranked by expected impact)

### Direction 1: Environmental signal scanning (HIGH impact)

**Gap:** `/insight` scans transcript *text* for correction/friction patterns but
doesn't systematically consume *environmental signals* — tool exit codes, retry
patterns, timing data, quota denials.

**Research basis:** Augment Code flywheel Stage 2 identifies three coaching
signal types: human feedback, automated coaching, and **environmental signals**
(task outcomes as reward signals without human annotation). The current `/insight`
uses only the first type (human corrections in transcript text).

**Proposal:** Add a pre-scan step before the transcript scan:
```powershell
# Extract environmental signals from tool-call metadata
rg.exe '"exit_code": [^0]' <session>/chat_history.jsonl   # failed tool calls
rg.exe '"error":' <session>/chat_history.jsonl              # error messages
rg.exe 'timeout|timed out' <session>/chat_history.jsonl     # timeouts
```
Feed these into the existing friction categories. A tool that failed 3 times
before succeeding is friction even if the operator never said "wrong" — the
environmental signal is the evidence.

**Expected effect:** catches friction that operators tolerate silently (retries,
workarounds, slow commands). Operators stop noticing friction they've habituated
to; environmental signals don't habituate.

### Direction 2: Heuristic distillation with trigger conditions (HIGH impact)

**Gap:** `/insight` captures findings as wiki concepts or handoffs, but doesn't
distill them into reusable **trigger → action heuristics** that future sessions
can retrieve at decision time.

**Research basis:** Augment Code flywheel Stage 3 (Distill) specifies: "after
each task, the agent generates an analysis identifying what led to success or
failure, then produces a guideline with explicit trigger conditions and
recommended actions." This is the **structured heuristics** distillation target —
inspectable, retrievable, no weight updates required.

**Proposal:** Add a Step 4.5 (after routing, before summary) that identifies
findings appearing in ≥2 sessions and distills them into heuristic format:
```
TRIGGER: <condition that recurs across sessions>
ACTION: <recommended response>
EVIDENCE: <sessions where this pattern appeared>
FALSIFIER: <what would prove this heuristic wrong>
```
Write these to `P:/.data/wiki/concepts/` as retrievable heuristics, not just
narrative findings.

**Expected effect:** findings become actionable at decision time in future
sessions, not just documented. A heuristic that says "when tool X fails with
error Y, use workaround Z" is more useful than a wiki concept that says "tool X
sometimes fails."

### Direction 3: Missed-skill detection (MEDIUM-HIGH impact)

**Gap:** Coverage check asks "did skills run?" but doesn't ask "did the agent
fail to invoke a skill that would have helped?"

**Research basis:** Augment Code's narrow-scope principle — specialist agents
that accumulate dense feedback outperform generalists. The corollary: if a
specialist skill exists and its trigger conditions were met but it wasn't
called, that's a missed opportunity. The SLIM framework measures marginal
contribution — a skill with high MEC that didn't fire is a high-cost miss.

**Proposal:** Add a Step 1.5 (between coverage check and transcript scan):
```
For each active skill with HIGH MEC:
  - Read its when-to-use / description field
  - Scan transcript for points where trigger conditions were met
  - If the skill was NOT invoked at those points → missed invocation
```
Surface missed invocations as improvement findings: "Skill /X would have helped
at turn N but wasn't invoked."

**Expected effect:** catches the class of improvement where the system has the
capability but failed to activate it — the highest-leverage gap because the fix
already exists.

### Direction 4: Multi-signal scoring for --fleet mode (MEDIUM impact)

**Gap:** `--fleet` clusters by frequency (pattern appears in N sessions) but
doesn't score by recency, importance, or relevance.

**Research basis:** Generative Agents (arxiv 2304.03442) uses a three-signal
retrieval score: `recency × importance × relevance`. ExpeL's documented failure
(concatenating all insights into every prompt regardless of relevance)
demonstrates what happens when retrieval architecture is neglected.

**Proposal:** Replace flat frequency counting in `--fleet` with:
```
score = recency_weight × importance_weight × frequency
  recency_weight: 1.0 for sessions <7 days, 0.5 for <30 days, 0.2 for >30 days
  importance_weight: based on whether the pattern caused a session failure (2.0),
    a correction (1.5), or was just friction (1.0)
```
This surfaces *recent important* patterns over *old frequent* ones.

**Expected effect:** `--fleet` surfaces the patterns most worth acting on now,
not the ones that have been around longest.

### Direction 5: Counterfactual reasoning (MEDIUM impact, experimental)

**Gap:** `/insight` finds what went wrong and what was corrected. It doesn't
ask "what if the agent hadn't done X? Would the session have been better?"

**Research basis:** SLIM's leave-one-out validation applied to session *actions*
(not skills). The counterfactual question surfaces unnecessary steps, wasted
work, and actions that introduced problems.

**Proposal:** Add an optional Step 2.5 (counterfactual pass):
```
For each major action in the session:
  - Would the outcome have been the same or better without it?
  - Did the action introduce a problem that required correction?
  - Did the action consume significant time/tokens without proportional value?
```
Surface as: "Action X (turn N) appears to have been unnecessary — the same
outcome could have been reached without it."

**Expected effect:** catches waste and unnecessary complexity — a category
neither corrections nor friction cover. [INFERENCE] — this is experimental;
needs production evidence to validate.

### Direction 6: Reflection-safe scanning (MEDIUM impact, structural)

**Gap:** `/insight` scans its own session with the same model that produced the
work — same blind-spot risk documented in the workspace's self-verification
prohibition rule.

**Research basis:** Datagrid Tip 6: "Separate reflection from execution through
a dual-component setup." The workspace already documents this principle
(`[[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]`:
self-assessment fails under closure pressure because the assessing faculty
shares the pattern-completion pathway that produced the work).

**Proposal:** When `/insight` runs inside `/close` or `/close-check`, the scan
should use a fresh subagent (or cross-model via `/agy`, `/codex`) rather than
the same model that did the work. The close-check Rhai workflow already
dispatches `/insight` as a subagent — this is structurally sound. But when
`/insight` runs standalone, document that a fresh-lens pass produces better
results than self-scanning.

**Expected effect:** reduces the blind-spot rate where `/insight` fails to find
improvements because the scanning model shares the working model's assumptions.

## What NOT to do (rejected directions)

- **Fine-tuning distillation target** — the Augment Code flywheel lists
  fine-tuning as a distillation target, but our workspace operates on
  prompt/context-level knowledge only. No training infrastructure. Rejected.
- **Autonomous self-modification** — the self-improvement boundary (Rung 5)
  is already documented and enforced. `/insight` recommends; the operator
  decides. Rejected by existing invariant.
- **Front-loaded context loading** — the Augment Code article shows
  front-loading degrades performance (context rot). `/insight` should NOT
  grow its prompt with accumulated heuristics. Heuristics go to wiki concepts
  retrieved on demand, not into the SKILL.md body.

## Falsifier

This concept's recommendations are wrong if:
- Environmental signal scanning produces mostly noise (tool failures that are
  expected/normal rather than friction) — the signal-to-noise ratio is too low
- Heuristic distillation produces heuristics that are never retrieved by future
  sessions — the wiki is already a graveyard of documented-but-unused patterns
- Missed-skill detection has a high false-positive rate (flags skills that
  wouldn't have actually helped) — becomes noise the operator ignores
- Counterfactual reasoning produces ungrounded speculation — LLM judgment about
  hypothetical alternatives is too unreliable to be actionable

## Implementation priority

| Direction | Impact | Effort | Priority |
|-----------|--------|--------|----------|
| 1. Environmental signals | HIGH | LOW (grep pre-scan) | **Do first** |
| 2. Heuristic distillation | HIGH | MED (new output format) | **Do second** |
| 3. Missed-skill detection | MED-HIGH | MED (trigger matching) | **Do third** |
| 4. Multi-signal --fleet | MED | LOW (scoring formula) | **Do fourth** |
| 5. Counterfactual | MED | MED (new step) | Experimental — needs evidence |
| 6. Reflection-safe | MED | LOW (documentation) | **Document now, wire later** |

## Related

- `[[insight-skill-consolidates-capture-friction-harvest]]` — the consolidation decision
- `[[proactive-improvement-opportunity-scanner]]` — the original /capture concept
- `[[self-improving-agent-systems-techniques-and-workspace-gaps]]` — research survey
- `[[compound-skill-improvement-patterns]]` — how skills improve over time
- `[[mechanical-enforcement-of-llm-skill-steps-2026]]` — enforcement patterns
- `[[research-quality-principle-efficiency-not-censorship]]` — quality is the constraint
