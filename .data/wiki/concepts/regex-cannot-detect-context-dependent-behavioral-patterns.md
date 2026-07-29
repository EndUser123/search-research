# Regex Cannot Detect Context-Dependent Behavioral Patterns

**Host provenance:** grok
**Date:** 2026-07-29
**Status:** OBSERVED — documented limitation

## Finding

Regex-based behavioral detection hooks cannot distinguish phrases that are violations in one context but correct in another. This is a structural limitation of syntactic pattern matching, not a bug in any specific regex.

## Concrete example

The `behavioral_check.py` NARRATIVE_CLOSURE pattern detected:
- "This session was productive"
- "Session is ready to close"
- "The work is complete"

These phrases are violations when they appear in a normal response (narrative closure without behavioral consequence). They are **correct and expected** when they appear in a `/close` or `/aar` report (where closure IS the task).

The regex matched in both contexts. Result: 5 detections, 0 true positives (100% FP rate). The pattern fired exclusively in close reports where the phrases are appropriate.

## Resolution options

1. **Delete the pattern** (chosen for NARRATIVE_CLOSURE) — accept the detection gap
2. **Contextual filtering** — check whether the response is a skill output (e.g., `/close` template). Requires the hook to know what skill generated the response, which Grok Build's Stop payload does not expose.
3. **Two-layer LLM judge** — regex prefilter + LLM evaluates whether the match is in a violation context or a legitimate context. Adds ~200ms per detection. Documented as a Phase 4 upgrade in the design doc.

## What this means for hook design

Regex is effective for patterns that are **unconditionally violations**:
- "Should I proceed?" — always unnecessary confirmation on reversible actions
- "I'll write that" (without immediate write) — always deferred persistence

Regex fails for patterns that are **conditionally violations**:
- Session-end language (correct in close reports)
- Deferral language (correct in handoff planning, AAR analysis)
- Fatigue language (correct when describing telemetry about fatigue patterns)

The rule: **if a phrase can legitimately appear in a `/close`, `/aar`, `/handoff`, or `/wiki` skill output, regex cannot reliably detect it as a violation.**

## Detection gap

The following behavioral categories are NOT detectable by regex Stop hooks:

| Category | Why regex fails | Covered by |
|----------|----------------|------------|
| Narrative closure | Phrase correct in close reports | AGENTS.md "Completion-language discipline" |
| Session-end recommendation | Phrase correct in AAR retrospectives | AGENTS.md "Answer-the-question-asked" |
| Deferred persistence discussion | Phrase correct in handoff planning | AGENTS.md "No deferred persistence" |

These are covered by prompt-level rules in AGENTS.md. The hook cannot add enforcement value for these categories without contextual awareness.

## Related concepts

- [[behavioral-detection-approaches-practitioner-survey]] — two-layer regex→LLM-judge as the upgrade path
- [[enforcement-hierarchy-and-compaction-strategy]] — prompt vs hook vs MCP classification
- [[fabricated-fatigue-llm-session-end-recommendations]] — the original fatigue pattern that prompted the hook
