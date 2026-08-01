---
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
last_updated_by: 019f96f5-dc4a-79d0-9e17-396f2a582186
last_updated_at: 2026-07-26T18:53:32.968075
parent_session: none
produced_at: 2026-07-26T18:53:32.968075
status: open
handoff_type: investigation
---
# Handoff: /www research findings — Stop-hook self-correction loop + /go optimization evidence

**Thread ID:** www-research-findings-stop-hook-20260726
**Created:** 2026-07-26
**Status:** OPEN
**Parent handoff:** none

## Objective

Persist two research findings from session 019f9d1f to the wiki and implement the evidence-backed fixes.

## Situation

This session ran multiple `/www` research cycles on two topics:
1. How to make `/go` adaptive and intelligent (ceremony reduction, prompt enhancement)
2. How to fix the Stop-hook self-correction loop (agent stops instead of continuing after a block)

The research produced findings that need durable persistence and follow-through.

## Finding 1: Stop-hook self-correction loop — the delivery mechanism matters, not the message

### What was researched
The Stop hook blocks the agent, Grok Build re-prompts (continuation), but the agent sometimes stops and waits for the operator instead of acting on the feedback.

### Key evidence (from HN thread "Claude 4.7 is ignoring stop hooks", 90+ comments)

- **niyikiza (HN):** "Two things get called hooks. Exit code 2 + stderr is a real control. JSON in stdout degrades to a string in the model's tool-result context, where the model is correctly trained to resist instructions because that's where prompt injections show up."
- **hashmap (HN):** "If the original problem happened because it ignored something you told it, telling it to not ignore something is a category error. The determinism isn't added by the message you're sending it, it's in the enforcement mechanism."
- **neckardt (HN):** "If these hooks show up as tool results context, something like 'You must do XYZ now' would be exactly the thing the model is trained to ignore."
- **agentic-patterns.com:** "If criteria fail, inject feedback and continue agent execution. If criteria pass, return control to user." (The pattern assumes the runtime forces continuation, not that the model chooses to comply.)
- **Arthur AI:** "The system feeds the flagged issue back to the LLM with a targeted correction prompt, the agent retries." (Self-correction loop — the retry is structural, not advisory.)

### Proposed fix (REFUTED by evidence)
Making the Stop-hook error message more directive ("act now", "do not wait for operator"). Evidence shows message wording doesn't reliably change behavior — the delivery mechanism does.

### What actually needs to happen
1. **Verify how Grok Build delivers Stop-hook stderr feedback** — as user-prompt-equivalent (authoritative) or tool-result-equivalent (untrusted). This is the key unknown.
2. **If delivered as authoritative:** the fix is behavioral — AGENTS.md rule: "Stop-hook feedback is a same-turn continuation instruction. Act immediately."
3. **If delivered as untrusted:** the fix is structural — need a different delivery mechanism or a system-prompt injection.
4. **Wiki concept:** persist the finding that "Stop-hook feedback delivery mechanism determines model compliance, not message wording."

## Finding 2: /go delegation-packet classifier — data-validated, needs live testing

### What was researched
Whether `/go`'s ceremony is wasted on well-specified prompts (delegation packets).

### Key evidence (from transcript scan of 1,074 sessions)
- 83% of 66 `/go` invocations scored as delegation packets (score >=4)
- Pushback correlated 100% with execution-mode tasks
- Zero `--lite` or `--skip-*` flags used across all invocations
- Signal is bimodal and stable — no learning loop needed

### What was implemented
- Delegation-packet classifier in `/go` SKILL.md (6-signal scorer)
- Adaptive prompt enhancement (gap analysis + confidence-gated application)
- Announcement compression for delegation packets
- Mandatory wiki query for shared-infrastructure tasks
- Subagent spawn template
- Reference material split (model routing tables → `reference/model-routing.md`)

### What needs to happen next
1. **Live test:** verify the delegation-packet classifier actually fires on the next `/go` invocation (RISK-001 from `/review`)
2. **Prompt testing (TDD for prompts):** create 10-case golden test set (handoff exists at `P:/docs/handoffs/go-prompt-testing-20260726/HANDOFF.md`)
3. **Wiki concept:** persist the adaptive orchestration finding (already written at `P:/.data/wiki/concepts/adaptive-orchestration-task-shape-classification.md`)

## Finding 3: Cross-session learning ledger — REFUTED by data

### What was researched
Whether a learning ledger tracking `/go` outcomes across sessions would improve routing.

### Key evidence
- The signal is stable from session 1, bimodal, no drift to learn from
- 83% at score 5-6, 15% at score 0-1, almost nothing in between
- No ambiguous middle ground where learning would help

### Conclusion
Do NOT implement a learning ledger. The classifier alone is sufficient.

## Scope

### In scope (next session)
1. Verify Grok Build's Stop-hook feedback delivery mechanism
2. Write wiki concept: "Stop-hook feedback delivery: message wording doesn't matter, delivery mechanism does"
3. Live-test the delegation-packet classifier
4. Create the prompt-testing golden dataset (existing handoff)

### Out of scope
- Learning ledger (refuted)
- LangGraph integration (wrong tool)
- Stop-hook retry/re-read (problem doesn't exist)

## Acceptance criteria

1. Wiki concept written for Stop-hook delivery finding
2. `/go` delegation-packet classifier verified on at least 3 real invocations
3. Delivery mechanism verified (user-prompt vs tool-result) — even if the answer is "can't determine"

## Evidence locations

- HN thread: https://news.ycombinator.com/item?id=47895029
- Arthur AI: https://www.arthur.ai/column/what-is-a-self-correction-loop-for-ai-agents
- Agentic patterns: https://www.agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
- Transcript scan: `P:/tmp/go_learning_evidence.json`
- Existing wiki: `P:/.data/wiki/concepts/stop-hook-scope-binding-fix-design-decisions.md`
- Existing wiki: `P:/.data/wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md`
- Grok Build hooks doc: `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md` line 262

## Exact next executable action

1. Read `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md` lines 248-265 to understand delivery mechanism
2. Test: trigger a Stop-hook block and observe whether Grok Build injects the stderr as user-prompt or tool-result
3. Write wiki concept based on finding
4. On next `/go` invocation: verify delegation-packet classifier fires

## Open questions

- Does Grok Build deliver Stop-hook stderr as authoritative instruction or untrusted tool-result? (This is the key unknown that determines which fix path to take.)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-26T18:53 | 019f96f5-dc4... | backfilled session_id from transcript scan |
