---
title: "Write wiki concept: execution receipts for executable artifacts (test before trust)"
created: 2026-08-02
source: session-019fc303
status: OPEN
yaml_status: open
assignee: unassigned
session: 019fc303-700f-7711-b376-12da1aff578a
tags: [wiki, knowledge-capture, verification, execution-receipts]
---

# Write wiki concept: execution receipts for executable artifacts

## Objective

Write a wiki concept at `P:/.data/wiki/concepts/execution-receipts-for-executable-artifacts.md` that captures the "test before trust" principle as a durable design decision with steelman + falsifier.

## Context

During session 019fc303, the operator asked how to catch the `/maintain` preflight defects earlier. The root cause: executable artifacts (skills, hooks, scripts) were declared "done" based on code inspection alone — never executed. The fix was added to AGENTS.md as "Execution receipts for executable artifacts (test before trust)" — a standing behavioral rule covering all executable artifacts, not just skills.

This handoff captures the wiki concept that should accompany the AGENTS.md rule. The concept needs:
1. The two-layer gate (static checks + runtime test-fire)
2. The per-artifact-type execution receipt table
3. Why it lives in AGENTS.md (not in `/create-skill` or `/go`)
4. Relationship to existing rules ("Claims require receipts," "Edit-then-verify," "Completion-language discipline")
5. Steelman: what's the argument AGAINST mandatory execution receipts? (Overhead for trivial changes, false confidence that "it ran" means "it works")
6. Falsifier: what observation would make this rule wrong?

## Acceptance criteria

- [ ] Wiki concept written at `P:/.data/wiki/concepts/execution-receipts-for-executable-artifacts.md`
- [ ] Passes `validate_wiki_entry.py`
- [ ] Cross-references to: `[[skill-lean-code-context-efficiency]]`, `[[code-output-passthrough-narration-over-script-output]]`
- [ ] Steelman names the rejected alternative (inspection-only for simple artifacts) and why it was reasonable
- [ ] Falsifier states what observation would disconfirm the rule
