---
title: "Mental Models for Handoff and AAR: What Our Skills Use and What They Should Use"
created: 2026-07-20
source: session-2026-07-20 (/www research on mental models for handoff + AAR)
tags: [mental-models, handoff, aar, double-loop-learning, progressive-disclosure, progressive-crystallization, cognitive-offloading, knowledge-management]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Five mental models underpin our handoff and AAR skills. Three are already
  implemented (progressive disclosure, progressive crystallization, cognitive
  offloading via artifacts). Two are missing and would materially improve
  outcomes: double-loop learning (challenging assumptions, not just actions)
  and the OODA loop (observe-orient-decide-act as a faster retrospective
  cycle). The most impactful change is adding double-loop questions to the
  AAR's Phase 4 pattern synthesis — currently the AAR asks "what went wrong"
  but not "why did we think this was the right thing to do."
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: related
  - target: wiki/concepts/skill-step-downgraded-from-action-to-note
    type: related
  - target: wiki/concepts/parallel-safe-solution-decomposition
    type: related
---

## Summary

Our handoff and AAR skills are built on several mental models — some explicit, some implicit. This research maps each model to where it appears in the skills, rates its implementation quality, and identifies the two models that would most improve outcomes if added.

## Five mental models and where they appear

### 1. Progressive Disclosure (explicit — well-implemented)

**What it is:** Load information into context only when the current task requires it, not all at once. Start with a minimal entry point and expand as needed.

**Where we use it:**
- `/aar` SKILL.md: lean-core + conditional references (`references/*.md` loaded only when triggers fire)
- `/design` SKILL.md: Step 0.5/0.6 domain research loaded only when triggered
- Handoff files: YAML frontmatter (minimal entry) → body (detail) → referenced files (deep context)
- `AGENTS.md` / `CLAUDE.md`: table of contents pointing to deeper sources, not a monolithic manual

**Quality:** Strong. The AAR's trigger system is the most sophisticated implementation — references load based on evidence-detected conditions, not on a fixed schedule.

**Source:** Anthropic Skills system; GitHub Spec Kit; Addy Osmani's "good spec" guide. The pattern was adopted industry-wide in 2026.

### 2. Progressive Crystallization (explicit — well-implemented)

**What it is:** Validated agent behaviors and lessons are converted into cumulative, reusable patterns over time. Each session contributes to a growing knowledge base rather than starting from scratch.

**Where we use it:**
- `/aar` Phase 9.5: automatic wiki promotion of headline lessons (lessons meeting scope + confidence criteria are promoted to durable wiki concepts)
- `/www` Phase 3: distill findings into wiki concepts, retire superseded ones
- Wiki lifecycle: `wiki_state.py` tracks the `discovered → ingesting → linking → linting → complete` state machine
- Handoff chain: `parent_handoff_path` creates a lineage that accumulates context across sessions

**Quality:** Strong. The lifecycle-tracked disposition system (`ACT_NOW`, `MONITOR`, `INVESTIGATE`, `PRESERVE`, `DEFER`, `REJECT`) prevents premature promotion while ensuring durable findings survive.

**Source:** OpenAI harness engineering ("capture human taste once, then enforce continuously"); LMsys paper on progressive crystallization as a lifecycle.

### 3. Cognitive Offloading via Artifacts (implicit — well-implemented)

**What it is:** Externalize cognitive state into durable artifacts (files, structured data) so the agent doesn't need to hold everything in working memory. This reduces context window pressure and enables cross-session continuity.

**Where we use it:**
- Handoff files: `current_session_id`, `parent_handoff_path`, `work_status`, `objective` — structured fields that reconstruct session state without re-reading the transcript
- `/close` scanner: 13 gates resolved mechanically, evidence collected into a JSON summary — the orchestrator reads the summary, not the raw session data
- Wiki concepts: distill session findings into reusable knowledge (distillation = offloading)
- `/go` state files: `P:/.artifacts/<termSafe>/<pkg>-state.md` carries Backlog, Last Verify, Open Questions across sessions

**Quality:** Strong. The handoff chain is the primary mechanism; each handoff encodes what the next session needs without requiring it to re-derive from the transcript.

**Source:** Distributed cognition theory (Grinschgl et al., 2022); AI agent memory systems (mem0, Letta, state files).

### 4. Double-Loop Learning (MISSING — would materially improve AAR outcomes)

**What it is:** Single-loop learning asks "How can we do what we are doing better?" Double-loop learning asks "Why do we think this is the right thing to do?" — it challenges the underlying assumptions and mental models, not just the actions.

**Where we DON'T use it (but should):**
- `/aar` Phase 4 (pattern synthesis + layered root-cause) asks "what caused this failure?" but doesn't ask "why did we believe the approach that led to this failure was correct?"
- The AAR's epistemic calibration (Phase 9) asks for "competing explanations" but frames them as alternative causal hypotheses, not as challenges to the governing assumptions
- The critical friend (Step 5.5 in `/design`) does double-loop learning for design docs — but the AAR itself doesn't do it for session retrospectives

**The gap:** Our AAR is excellent at single-loop learning (what happened, why, what to fix). It's weak at double-loop learning (why did we think this was the right approach? What assumption governed the decision? Is that assumption still valid?).

**What it would look like in the AAR:** Add a "Double-Loop Questions" block to Phase 4 or Phase 5:

```
## Double-Loop Analysis (mandatory when a CORRECTION or REVERSAL was identified)

For each significant correction or reversal:
1. What did we believe was true when we made the original decision?
2. What assumption governed that belief?
3. Is that assumption still valid? If not, what changed?
4. What would we have done differently if we'd known then what we know now?
5. What signal would have alerted us to the wrong assumption earlier?
```

This is exactly what this session needed when I proposed architectures without reading sources. The single-loop question was "what should we build?" The double-loop question was "why did we think proposing without reading was acceptable?" The `/tp` dialogue eventually surfaced this — but the AAR's Phase 4 wouldn't have asked it.

**Source:** Chris Argyris (double-loop learning, 1976); Esther Derby ("Promoting Double Loop Learning in Retrospectives"). The connection to agent AARs is novel — no external source applies double-loop learning to LLM agent retrospectives.

### 5. OODA Loop (MISSING — would improve AAR speed)

**What it is:** Observe → Orient → Decide → Act. A faster decision cycle that compresses retrospective into the four-step loop rather than treating it as a separate post-hoc activity.

**Where we could use it:** The AAR's 9 phases are thorough but slow (5-8 LLM turns for FULL). The OODA loop is a faster cycle:
- **Observe:** what happened (the preprocessor already does this)
- **Orient:** what does it mean (Phase 1-4 do this)
- **Decide:** what to do about it (Phase 6-7 opportunity dispositions)
- **Act:** implement the decision (Phase 8 routing)

The OODA framing wouldn't replace the AAR's phases — it would compress them for LITE-tier sessions. Instead of running all 9 phases, a LITE AAR runs one OODA cycle: observe (preprocessor), orient (§ten-questions), decide (one-paragraph verdict), act (routing). This is structurally what the adaptive-depth design proposes for LITE — the OODA loop is the mental model that justifies it.

**Source:** John Boyd (OODA loop, military strategy, 1976); adapted for business by multiple strategy consultants.

## What our handoff skills do well (validated by research)

| Pattern | Source | Our implementation |
|---|---|---|
| Structured handoff with typed fields | GitHub 2,500-repo study on AGENTS.md | Handoff YAML frontmatter (current_session_id, parent_handoff_path, status, work_status) |
| Session observations separate from tasks | USAID AAR guide ("uninvolved note-taker") | Session-observations handoff written by `/close` |
| Decision log inside the artifact | Augment Code "living specs" | `/aar` Phase 3 (decision history) + design doc Decision Log section |
| Stale-data immunity | Our own `wiki_state.py` lifecycle | Handoff chain integrity check in `/close` |
| Cross-session context without transcript replay | Distributed cognition (Grinschgl 2022) | Handoff `parent_handoff_path` lineage |

## What our AAR skill does well

| Pattern | Source | Our implementation |
|---|---|---|
| Typed episodes (not generic findings) | USAID AAR guide; Argyris double-loop | Phase 2 typed episode ledger (8 types) |
| Layered root-cause (not just proximate) | Incident response best practices | Phase 4 OBSERVED_FAILURE → IMMEDIATE_TRIGGER → PROXIMATE_CAUSE → CONTRIBUTING_CONDITIONS → SYSTEMIC_REUSABLE_CAUSE |
| Lesson calibration gate | Evidence-based medicine (confidence levels) | Phase 9: scope, confidence, counterexample, competing explanations |
| Value accounting (success amplification) | AAR for AI (Dodge et al., 2021) | Phase 5: seven-category value ledger + 8 success-amplification questions |
| Auto-promotion of durable lessons | Progressive crystallization (LMsys) | Phase 9.5: automatic wiki promotion for PROBLEM_CLASS/GENERAL + OBSERVED/INFERRED |

## What's missing and worth adding

| Gap | Impact | Effort | Priority |
|---|---|---|---|
| **Double-loop questions in AAR Phase 4** | High — catches the "why did we think this was right?" failure that single-loop misses | Low — one paragraph of questions added to Phase 4 | 1 |
| **OODA framing for LITE-tier AAR** | Medium — justifies the compressed depth and gives it a theoretical basis | Low — reframe the LITE description, no code change | 2 |
| **Handoff freshness signal** | Medium — currently handoffs don't indicate whether the session context they encode is still current | Low — add a `context_valid_until` or `head_drift_detected` field | 3 |
| **Cross-session memory consolidation** | High but complex — the wiki does this manually; automating it would compound learning | High — requires a consolidation agent + conflict resolution | 4 (Phase 2) |

## Related

- [[mandatory-step-enforcement-code-over-prose]] — the prose-vs-code distinction is itself a double-loop finding (why did we think prose rules would bind?)
- [[skill-step-downgraded-from-action-to-note]] — single-loop would ask "how to make the step fire"; double-loop asks "why did we think advisory steps would work?"
- [[parallel-safe-solution-decomposition]] — DSM/CPM decomposition is itself a mental model that should be in the handoff (so the next session knows the parallel structure)

## Sources

- Chris Argyris, "Double Loop Learning in Organizations" (Harvard Business Review, 1976)
- Esther Derby, "Promoting Double Loop Learning in Retrospectives" — https://estherderby.com/promoting-double-loop-learning-in-retrospectives/
- John Boyd, OODA Loop (military strategy, 1976)
- Dodge et al., "After-Action Review for AI (AAR/AI)" (Oregon State, 2021)
- USAID, "After-Action Review" guide — https://fs-prod-nwcg.s3.us-west-1.amazonaws.com/s3fs-public/2023-06/usaid-aar-guide.pdf
- Wharton, "After-Action Reviews: A Simple Yet Powerful Tool" — https://executiveeducation.wharton.upenn.edu/thought-leadership/wharton-at-work/2021/07/after-action-reviews-simple-tool/
- Grinschgl et al., "Distributed Cognition Today and in an AI-Enhanced Future" (PMC, 2022)
- Progressive disclosure: Anthropic Skills; GitHub Spec Kit; Addy Osmani
- Progressive crystallization: LMsys paper; OpenAI harness engineering

## Auto-related

- [[handoff-pre-compact-problems]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
