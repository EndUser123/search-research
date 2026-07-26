---
thread_id: agentic-rules-not-firing-enforcement-investigation-20260726
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-07-26T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: unknown
---

# Handoff: investigate enforcement for agentic-rules-not-firing (AGENTS.md discipline skipped under generative load)

## Objective

Investigate why the model skips mandatory rules in AGENTS.md under generative load, and design **enforcement mechanisms** (not just more prose) that actually fire at the moment of need. The 2026-07-25 session provided direct evidence: two specific rules (search_replace 3-line read-back, Class C temp-`.py` for f-strings) were both documented in `~/.grok/AGENTS.md` and both skipped within the same session. The pattern is not "the rule doesn't exist" — it is "the rule exists and the model doesn't surface it under pressure."

**The operator's framing (verbatim):** *"we need to enforce it somehow."* A wiki concept was shipped (`verify-against-existing-state-before-defensive-mechanisms`) but the operator correctly identified that as more prose, not enforcement. This handoff targets the enforcement layer.

## Why this matters

This is the binding constraint on AGENTS.md effectiveness. AGENTS.md is ~800 lines and growing. Every session adds rules. The model already skips rules under pressure; adding more rules without enforcement increases the surface area that gets skipped. Without a structural fix:

- The wiki-concept approach ("codify the principle so it's one rule to remember") is the same shape as the problem it documents — a model that skips rules will skip the rule about not skipping rules
- More prose in AGENTS.md increases skip rate (the file is already over a typical attention budget for rule-lookup mid-task)
- The "rule-not-fired" failure mode is invisible to the model (it doesn't know it skipped the rule) and only visible to the operator (who catches the downstream error)

## Evidence for the gap

### Direct evidence from session 019f9a89 (2026-07-25)

- **search_replace 3-line read-back rule:** documented at `~/.grok/AGENTS.md` § "File editing protocol." I used search_replace to delete a Falsifier bullet accidentally (old_string matched; I didn't read the surrounding lines after the edit). Caught by read-back on a separate concern; the deletion was already done.
- **Class C temp-`.py` rule:** documented at `~/.grok/AGENTS.md` § "Class C: shell quoting." I wrote inline Python with f-strings + backslash escapes; syntax error aborted the script. Per the rule, I should have written to a temp `.py` from the start. I retried inline first, failed, then switched to temp `.py`. The rule was on the books; I ignored it under time pressure.
- **Staging proposal (over-engineering):** I proposed staging for the wiki feedback loop without checking whether synchronous review already covered the contamination concern. The `verify-against-existing-state` principle (which I then wrote a wiki concept for) was violated by my own proposal in the same session.

### Pattern (inferred from session + wiki)

The wiki already documents this class: `rule-not-fired-vs-rule-doesnt-exist`, `reactive-pattern-matching-and-closure-pressure`, `mandatory-step-enforcement-code-over-prose`. The pattern is: rules exist, are correct, and are skipped. The fix is not more rules.

## Scope

**In scope:**
- Root cause analysis of why AGENTS.md rules are skipped under generative load (attention? context-budget? rule-lookup cost? rule-shape?)
- Design of **enforcement mechanisms** — not prose. Specifically:
  - Pre-edit hooks (PreToolUse on search_replace / write) that mechanically require read-back
  - Pre-command hooks that detect Class C patterns (f-string + backslash) and block inline execution
  - Skill-step integration (a "/pre-action" check that fires before any proposal)
  - Compaction of AGENTS.md into fewer, higher-leverage rules (reducing lookup cost)
  - Hook-based AGENTS.md rule injection (the relevant rule surfaces at the relevant moment, not as a 800-line wall)
- Evaluation: which mechanisms are actually enforceable on Grok Build (hook types: `command`, `http` only — per `~/.grok/docs/user-guide/10-hooks.md`)

**Out of scope:**
- Backfilling more wiki concepts (the prose layer is addressed)
- Rewriting AGENTS.md (separate workstream if recommended)
- Model training / fine-tuning (not available to the operator)

## Acceptance criteria

1. **Root cause identified** — why do rules get skipped? (attention budget? rule-lookup latency? rule-shape? rule-volume? something else?)
2. **At least 2 enforcement mechanisms designed**, each with:
   - Specific Grok Build hook type it would use (`command` / `http`)
   - Detection logic (lexical / semantic / hybrid)
   - False-positive risk assessment (with proposed mitigation)
   - Steelman of "don't enforce, keep prose-only"
   - Falsifier (what evidence would prove this enforcement is unnecessary or harmful)
3. **Recommendation**: which mechanism to ship first, or "no enforcement — prose is the ceiling on this host"
4. **AGENTS.md compaction analysis** — is the file too long? If yes, propose a restructure that surfaces the right rule at the right moment (e.g., section-based loading, or a hook that injects the relevant section based on tool being used)

## Read-first list

1. `~/.grok/AGENTS.md` § "File editing protocol" + § "Class C: shell quoting" (the specific rules that were skipped)
2. `~/.grok/docs/user-guide/10-hooks.md` (what hook types are available on Grok Build — `command`, `http` only; this constrains the design space)
3. `~/.grok/active-surface.last.md` (what hooks are currently firing; what's disabled)
4. `P:/.data/wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md` (the named pattern)
5. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` (the existing analysis of prose-vs-code enforcement)
6. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` (the behavioral root)
7. `P:/.data/wiki/concepts/verify-against-existing-state-before-defensive-mechanisms.md` (the wiki concept the operator correctly identified as "more prose, not enforcement")
8. `P:/.data/wiki/concepts/llm-judgment-hooks.md` (researched pattern for semantic hook enforcement — two-layer regex+LLM)
9. `P:/.claude/hooks/` directory listing (existing hook patterns to learn from)
10. `P:/packages/.claude-marketplace/plugins/` — existing PreToolUse hooks (e.g., `PreToolUse_win32_path_gate`, `PreToolUse_investigation_gate`) as reference implementations

## Hypotheses to investigate

- **H1 — AGENTS.md is too long to surface the right rule under load.** ~800 lines exceeds typical attention budget for mid-task rule-lookup. The model optimizes for the immediate task; rules not in the current attention window don't fire. Fix: compaction, or section-based injection.
- **H2 — The rules are correct but their trigger shape is wrong.** "After every Edit, read the surrounding 3 lines" is a post-action rule. The natural moment to enforce is a PreToolUse gate that blocks the next action until read-back is observed. Fix: convert post-action prose rules to pre-action hooks.
- **H3 — Class C quoting specifically is lexically detectable.** A regex/parser can detect `python -c` with f-strings + backslashes and block before execution. This is the easiest enforcement and a good first test case.
- **H4 — search_replace read-back is detectable but harder.** A PostToolUse hook on search_replace that requires a subsequent `read_file` of the edited region before allowing the next mutation would mechanically enforce the 3-line read-back. Detection: tool-call sequence pattern.
- **H5 — The "verify-against-existing-state" principle is semantic, not lexical.** No regex can detect "did you audit existing gates before proposing a defensive mechanism?" This needs LLM-judgment hooks (per `llm-judgment-hooks` wiki concept) or cannot be enforced mechanically.
- **H6 — Enforcement friction is itself a risk.** Hooks that block mid-flow may cause the model to route around them (write to different paths, use different tools). The enforcement must be tighter than the workaround.

## Constraints

- Do NOT implement hooks in this handoff. Investigation + recommendation only. Implementation is a separate workstream.
- Do NOT rewrite AGENTS.md without explicit operator decision. Propose, don't execute.
- All proposed hooks must respect Grok Build hook types (`command`, `http`) and Windows path conventions.
- Hooks must have descriptive stderr on block (per `~/.grok/AGENTS.md` hook development rules).

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** future AGENTS.md discipline work (this investigation's recommendation gates whether to add more rules or to switch to enforcement)
- **Non-blocking to:** other skill improvements

## Related

- **Sibling handoff:** `missed-decisions-wiki-capture-investigation-20260725` (also about discipline-skipped-at-moment-of-need, but at close-time not mid-action)
- **Wiki concept:** `verify-against-existing-state-before-defensive-mechanisms` (the prose layer this investigation supersedes)
- **Wiki pattern:** `mandatory-step-enforcement-code-over-prose` (the existing principle: code enforcement beats prose rules)

## Status

OPEN — ready for investigation in a fresh session

## Next steps

1. Read the read-first list (especially `10-hooks.md` — the design space is constrained by what Grok Build actually supports)
2. Test the hypotheses (especially H3 — lexical detection of Class C quoting — as the easiest first enforcement)
3. Design 2+ enforcement mechanisms with the criteria above
4. Recommend which to ship first
5. Hand off to implementation

## Last user message (verbatim)

"Please turn this problem into a handoff. [the problem statement] we need to enforce it somehow."

## Operator intent (explicit)

The operator wants **enforcement**, not more documentation. The wiki concept was shipped but the operator correctly identified it as insufficient. The handoff must target the enforcement layer (hooks, mechanical detection) — not additional prose. If the investigation concludes that enforcement is not feasible on this host, that is an acceptable finding (label it honestly); but "ship another wiki concept" is not an acceptable recommendation.
