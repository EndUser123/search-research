---
title: "Pre-presentation self-check gate: catching predictable failures before the operator does"
date: 2026-08-13
provenance:
  - source: session-019fee3d
  - source: operator-directive
  - source: Gawande-Checklist-Manifesto
  - source: MARS-Hou-2026-ACL
tags: [meta-cognition, quality-gate, known-failure-classes, cognitive-load-reduction]
host: both
---

# Pre-presentation self-check gate

## The problem

The operator functions as the system's quality gate. Every time the operator catches something wrong — a field mismatch, a polling timeout, a system context extraction bug — they are doing work the system should have done before presenting. This is unrecoverable cognitive cost: the operator cannot relax because they must audit every output.

The failures are **predictable**: they fall into known classes that have recurred across multiple sessions. The agent has the knowledge to catch them but doesn't apply it before presenting.

## The solution

Before declaring any substantive output "done," "fixed," "complete," or "working," the agent runs a self-check against the known failure classes. This is the Gawande Checklist Manifesto pattern: structured checklists catch predictable failures that expertise alone misses under cognitive load.

## The 5-question self-check

1. **Execution receipt:** Did I run this (not just inspect it)? Reading code is inspection; running code is verification. For executable artifacts, the receipt is a command output, not a code review.

2. **Producer-consumer field match:** If I changed or wrote code that produces data consumed by another component, do the field names match? Check the consumer's code against the producer's actual output shape.

3. **Propagation check:** If I changed a name, path, model slug, or convention, did I grep all referencing files and update them? A change in one file is not complete until all consumers are updated.

4. **Known failure-class scan:** Does this output match any known failure class? (See the class catalog below.)

5. **Confidence surface:** What am I least sure about? State it. The operator focuses questioning on the soft spots.

## Known failure-class catalog

These are the recurring classes extracted from operator catches across sessions. Each class includes the pattern, how to detect it, and a reference session.

### FC-01: Field name mismatch (producer-consumer schema drift)

**Pattern:** Producer code emits fields under one name (e.g., `materiality`); consumer code reads under a different name (e.g., `material`). The consumer silently gets default values and produces wrong behavior.

**Detection:** When writing code that reads from another component's output, verify the field names by reading the producer's actual output — not the consumer's assumed schema.

**Reference:** Session 019fee3d — handoff_resolve.py used `material`/`covered`; scanner produced `materiality`/`terminal_disposition`. Caused CLOSE INCOMPLETE on every run.

### FC-02: System context contamination

**Pattern:** Scanners or extractors that process user messages treat host-injected system context blocks (`<rules>`, `<user_info>`, `<git_status>`, compaction summaries) as real user content. This produces false-positive candidates, goals, or friction signals.

**Detection:** Any code that extracts from transcripts or user messages must strip known system context tags before processing.

**Reference:** Session 019fee3d — `<rules>` block extracted as "user goal"; compaction summary extracted as "opening goal."

### FC-03: Missing execution receipt

**Pattern:** Agent declares an executable artifact "done" based on code inspection alone, without running it. The code looks correct but fails at runtime for reasons inspection can't catch (dependency issues, path resolution, runtime config).

**Detection:** For executable artifacts (scripts, hooks, pipelines, skills), the receipt must be a command output, not a code review. "I read the code and it looks right" is not a receipt.

**Reference:** Session 019fee3d — poll timeout fix shipped without re-running the pipeline. Multiple prior sessions (documented in AGENTS.md).

### FC-04: Polling/timeout misconfiguration

**Pattern:** Polling loops with timeouts set to maximum-wait rather than expected-completion. A single failed dispatch hangs for 30 minutes instead of 5.

**Detection:** Poll timeout should be ≤5x expected completion time. If expected completion is 60s, timeout should be 300s max. Any timeout >600s for a model dispatch is almost certainly wrong.

**Reference:** Session 019fee3d — close-py poll timeout was 1800s for ~60s dispatches.

### FC-05: Stale references after consolidation

**Pattern:** After files are moved, renamed, or consolidated, handoffs and docs still reference the old paths. The scanner finds these as "needs_attention" gates.

**Detection:** After any file move/rename/consolidation, grep all handoffs and docs for the old path. Update before declaring done.

**Reference:** Session 019fee3d — `/close/__lib/close_accounting.py` referenced after move to `close-py/__lib/_scanners/`.

### FC-06: Specification gaming (hand-authored evidence)

**Pattern:** Agent writes findings JSON by hand instead of letting the orchestrator produce it from model dispatch. The evidence looks valid but bypasses the anti-fabrication architecture.

**Detection:** Findings files must have a `_dispatch_path` provenance stamp. Any findings without a stamp are rejected by `check_provenance()`.

**Reference:** Documented in ship-py design; the `write_findings.py` helper was removed to prevent this.

### FC-07: Dirty-tree scope contamination

**Pattern:** Scope-detection falls back to `git status` on a multi-agent host. Sibling-session changes contaminate the current session's scope, producing irrelevant findings.

**Detection:** Scope must default to session-scoped (hunk log → session commits → diff hash). Dirty tree is LAST RESORT and must be marked unreliable.

**Reference:** Session 019fdf3c — documented in AGENTS.md multi-terminal isolation rule.

### FC-08: Shell quoting corruption (Class C)

**Pattern:** Agent emits shell syntax that doesn't match the executing shell. Command exits 0 while corrupting or never applying. Most common with `python -c` with nested quotes in PowerShell.

**Detection:** For multi-line or nested-quote payloads, write to a temp file and invoke against the file. Never `@'...'@` in Bash. Never large inline strings in `python -c`.

**Reference:** Documented in AGENTS.md Class C shell quoting rule; recurred throughout session 019fee3d.

### FC-09: Missing propagation after policy/config changes

**Pattern:** Agent changes a model slug, routing rule, or gate state in one file but doesn't update all referencing files. The next session dispatches with the old value and fails.

**Detection:** After changing any model slug, routing preference, gate-state constant, hook event name, file path, or skill name: run `propagation_check.ps1` or grep all standard paths.

**Reference:** Session 019f9f4f — documented in AGENTS.md propagation check rule.

### FC-10: Narrative closure without behavioral consequence

**Pattern:** Agent declares "done" with closure narrative ("the system is now fully operational") but the declaration doesn't correspond to a verifiable state change. The operator has to ask "does it actually work?"

**Detection:** "Done" claims must cite a specific verifiable artifact: a test that passes, a command that succeeded, a file that exists. Narrative sufficiency is not verification.

**Reference:** Documented in AGENTS.md claims-require-receipts rule.

## How the self-check fires

The self-check is **procedural, not behavioral**. It specifies a mechanical step the agent takes before presenting, not a disposition it should have. The difference:

- Behavioral: "be careful and check your work" (decays under pressure)
- Procedural: "before saying 'done,' answer these 5 questions with receipts" (mechanical)

The self-check section appears at the END of substantive outputs, before any "done" claim. Format:

```
**Self-check:**
- Executed: [receipt or "NOT VERIFIED — only inspected"]
- Field match: [verified or N/A]
- Propagation: [grep results or N/A]
- Known failure classes: [none match] or [FC-XX: addressed]
- Least confident about: [one sentence]
```

## What this replaces

This replaces the pattern where the operator asks "did you verify it?" after every output. The agent volunteers the verification state, so the operator can focus on the unverified parts instead of auditing everything.

## Connection to MARS (Metacognitive Agent Reflective Self-improvement)

MARS (Hou et al., ACL 2026) clusters failures by type and synthesizes principle-based improvements. The known failure-class catalog above is the fleet's failure clustering. Each class is a cluster; the self-check is the principle synthesized from the cluster. New classes get added as the operator catches new failure modes — extending the catalog is the system learning from its mistakes.

## Falsifier

This pattern is wrong if:
- The self-check becomes theater (the agent fills it in without actually checking)
- The 5 questions don't catch the failures the operator would have caught
- The operator still has to ask "did you verify it?" after every output
- The known failure-class catalog stops growing (new failure modes aren't being captured)
