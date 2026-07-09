# Delegation Prompt Pattern — handing mechanical work to a simpler LLM

Purpose: a template for writing prompts that let a cheaper/simpler model do
mechanical cleanup safely. The core idea: **the prompt supplies the judgment;
the model supplies only the labor.** If a task still requires judgment after
the prompt is written, it was the wrong task to delegate.

## When to delegate (and when not)

Delegate: work driven by an existing detector or checklist — lint/audit
findings, renames, format conversions, catalog generation, reference updates.
The common property: correctness is machine-checkable after each step.

Do not delegate: anything requiring design taste, root-cause reasoning,
policy interpretation, or irreversible actions. If you can't write a
verification command for the outcome, don't hand it off.

## The seven elements

1. **Detector-driven scope.** Anchor every task to an existing tool's output
   ("run the audit; fix what it flags"), never to the model's own assessment
   of what needs fixing. The detector defines done; the model can't expand or
   shrink scope.

2. **Verification closes every task.** Each task ends with re-running the
   exact check that found the problem ("re-run ast.parse", "CATALOG_DRIFT
   must go to 0"). The model cannot claim unverified success because success
   is defined as detector output, not self-report. Baseline before, compare
   after.

3. **Classification buckets with an escape hatch.** For findings that need
   any judgment, pre-enumerate the categories (fixture/renamed/truly-gone)
   with a mechanical rule for each, and always include a "report, don't
   decide" bucket ("needs human decision — do not modify"). Simpler models do
   the most damage when forced to decide; give them a dignified way out.

4. **Explicit don't-touch list.** Name the files and directories that are
   off-limits, including recently-fixed work and anything the detector did
   not flag. "Only what the audit flagged" beats "be careful."

5. **Fix the generator, not the output.** When the deliverable is derived
   (catalogs, generated docs, lockfiles), the instruction is: write/repair
   the generator until the derived artifact validates — never hand-edit the
   artifact. Hand-edits recreate the drift the task exists to remove.

6. **One change per verification cycle.** Sequential file operations with a
   check between each ("never modify more than one file between verification
   runs"). Batch failures in a simple model are silent and compounding.

7. **Mandatory written residue.** Require a report listing every change,
   every skipped item, and every "needs human" item with one-line
   justification, saved to a known path. The report is how you audit the
   delegate without replaying its session — and the requirement itself
   suppresses silent skipping.

## Template skeleton

```
You are working in <root>. Your job is mechanical cleanup driven by
<detector>. Do not redesign anything. Rules: state planned changes before
making them; one file per Read→Edit→Verify cycle; never claim fixed without
re-running the check that detected it.

SETUP: run <detector>, save baseline output to <path>.

TASK n — <category from detector output>
  - For each finding: <mechanical rule, or classification buckets a/b/c
    where one bucket is always "report, don't decide">
  - Verify each fix with: <exact command>

FINISH:
  - Re-run <detector>, save to <path>, compare to baseline.
  - Write <report path>: baseline vs after counts, every change, every
    skipped/needs-human item with one-line justification.
  - <commit/handoff step>
  - Do NOT touch: <explicit list>.
```

## Failure modes this prevents

| Failure | Countered by |
|---------|--------------|
| Claims success without checking | #2 — detector defines done |
| Invents scope ("also refactored…") | #1, #4 — detector-driven + don't-touch |
| Guesses on ambiguous cases | #3 — escape-hatch bucket |
| Hand-edits generated artifacts | #5 — fix the generator |
| Batch corruption, caught late | #6 — one change per cycle |
| Silently skips hard items | #7 — skips must appear in the report |

Origin: 2026-07-09 session — pattern extracted from the hooks_audit cleanup
delegation prompt. Companion: P:/.claude/templates/llm_behavior_contract.md
(behavior contract for the delegate to operate under).
