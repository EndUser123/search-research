---
thread_id: uncertainty-gate-meta-discussion-suppression-20260809
parent_handoff_path: none
current_session_id: 019fe664-f7c3-7441-89e3-aa181629cf1c
current_terminal_id: console
produced_at: 2026-08-09T20:36:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 5d9cb1c738f3c56a47a2f49e0274a067a443dd4f
---

# Uncertainty-gate meta-discussion suppression pattern

## Status
OPEN — one refinement identified, not yet implemented

## Objective
Add a meta-discussion suppression pattern to the `uncertainty_gate.py` Stop hook so it does not fire on agent-authored text that is *discussing* the hook (containing "hook", "gate", "false positive", "matched", "uncertainty", "fired") rather than making a real unverified claim.

## What now works
The `uncertainty_gate.py` hook now strips `Stop hook feedback:` envelope blocks and `*_GATE:` advisory lines (including continuation lines) before scanning — this fix shipped this session (commit `aa49c51`, ~/.grok main). The structural feedback loop (hook output → agent quotes block → hook re-matches block) is broken.

What remains: when an agent discusses the hook in its own prose and quotes the trigger phrase inline (e.g., "the hook fired on 'likely 10'"), the gate fires again on the inline quote. The current design keeps this as an "awareness-forcing feature" — the `/tp` analysis concluded the inline-quote match is agent-authored text that genuinely matches the pattern.

## Verified facts (with source paths)
- [FACT] The hook scans `event.get("lastAssistantMessage", "")` — the last assistant message only (source: `~/.grok/hooks/scripts/uncertainty_gate.py` line 224)
- [FACT] The hook strips code blocks (`IN_CODE_BLOCK`) and hook-feedback blocks (`HOOK_FEEDBACK`) but does NOT strip inline quotes in agent prose (source: same file, `detect_hedge_claim()` lines 143–150)
- [FACT] `/www` research found field consensus that Stop hooks should bias toward false negatives over false positives that degrade the session (source: `P:/.data/wiki/concepts/llm-uncertainty-hedging-detection-research-landscape.md` § "Extension: hook feedback loops and context stripping")
- [FACT] The `llm-dark-patterns` suite uses allow-clauses for legitimate cases (e.g., no-sycophancy allows praise when operator-requested) — the equivalent for uncertainty_gate would be allowing inline quotes when surrounding context is meta-discussion
- [INFERENCE] The inline-quote re-trigger is rare (one instance this session) and cheap to dismiss, so the case for suppression is about reducing operator friction, not fixing a bug

## The refinement

Add a suppression pattern alongside the existing `PROPOSAL_CONTEXT`, `_is_in_question`, `OPTION_CONTEXT`, and `ALREADY_LABELED` suppressions in `detect_hedge_claim()`:

```python
# Meta-discussion: agent is discussing the hook/gate itself, not making a claim
META_DISCUSSION = re.compile(
    r"(?i)\b(?:hook|gate|false positive|matched|uncertainty|fired|detection|hedge)\b"
)
```

When a hedge+number match is found and the surrounding context (±50 chars) contains a meta-discussion keyword, suppress the hit. This is the `llm-dark-patterns` allow-clause approach applied to our case.

## Acceptance criteria
- [ ] `META_DISCUSSION` suppression pattern added to `detect_hedge_claim()` in `uncertainty_gate.py`
- [ ] Test: agent prose discussing the hook ("the hook fired on 'likely 10'") does NOT trigger the gate
- [ ] Test: real unverified claim ("the rate is approximately 50 percent") still trigger the gate
- [ ] Test: mixed case (meta-discussion + real claim in same message) still catches the real claim

## Falsifier
The suppression is wrong if it hides a real unverified claim that happens to mention a hook/gate keyword. Example: "The hook detected that the failure rate is probably 15 percent" — this contains both "hook" and "probably 15" and the claim IS unverified. Mitigation: only suppress when the meta-discussion keyword is in the *immediate* context of the hedge+number match (±30 chars), not anywhere in the message.

## Suggested skills
- `/tp` — to stress-test the suppression pattern before shipping (does it over-suppress? does it under-suppress?)
- `/skill-dev measure` — to run the 6 static checks on the modified hook

## Last user message (verbatim)
"/wiki" (the auto-update mode fired from the `/handoff` invocation with no args; the operator's last substantive request was the `/handoff` that triggered this write)

## Cross-reference couplings
- `~/.grok/hooks/scripts/uncertainty_gate.py` — the hook to modify
- `P:/.data/wiki/concepts/llm-uncertainty-hedging-detection-research-landscape.md` — the `/www` research documenting the field consensus on false-negative bias
- `P:/.data/wiki/concepts/mechanical-tool-output-is-hypothesis-not-measurement.md` — the broader principle (scanner output is hypothesis, not measurement)

## Dependencies
- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** close-py design (if close-py's gates use uncertainty detection, this suppression pattern would apply)
