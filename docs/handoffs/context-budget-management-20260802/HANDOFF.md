---
thread_id: 019fa8f8-context-budget-20260802
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-02T08:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 0254a88
---

# Handoff: Subagent context budget management

## 1. Objective

Implement context-budget-aware spawning so subagents don't hit max_tokens_truncation on large review/critique tasks.

## 2. Status

OPEN — read-once discipline added to /review SKILL.md. Other items need investigation.

## 3. Producing context

This session's /why found that subagent failures were caused by context accumulation (re-reading files, accumulating tool-call context), not by model tier. The /tp review corrected the /why's wrong recommendation (use subscription models) and identified three viable solutions:

1. **Decompose review work per-file** when combined file size exceeds ~50K tokens — ALREADY in /review SKILL.md Step 4
2. **Enforce read-once discipline** — SHIPPED: added to /review SKILL.md
3. **Context-budget-aware model selection** — pick by context fit, not tier — NEEDS INVESTIGATION

## 4. Remaining work

### CTX-1: Context-budget-aware model selection
- **goal:** when spawning a subagent, estimate the required context (file sizes + prompt + expected output) and pick a model whose context window fits
- **context:** zen-deepseek has 256K context, or-ling-3 has ~128K. If the task needs 200K, don't pick or-ling-3. Currently pick_model.py checks quota and serde_broken but NOT context window fit.
- **acceptance:** pick_model.py or the spawn logic warns when the selected model's context window is smaller than the estimated task size
- **estimate:** 30 min
- **falsifier:** if decomposition (per-file spawning) eliminates the problem, context-budget selection is unnecessary

### CTX-2: Session-length early warning
- **goal:** surface a recommendation to start a fresh session when accumulated context exceeds a threshold
- **context:** this 99-hour session pushed every subsystem past its limits. Session length isn't the root cause but amplifies context accumulation.
- **acceptance:** a SessionStart or UserPromptSubmit hook that checks session age (hours, compaction count) and surfaces a non-blocking advisory
- **estimate:** 1 hour
- **falsifier:** if context-budget management per spawn eliminates truncation, session-length monitoring adds no value

## 5. Hard constraints

- Don't switch to more expensive models as the primary fix — decompose instead
- Free models work fine for normal-sized spawns; the problem is context accumulation, not model capability
- Read-once discipline is the highest-leverage fix (already shipped)
