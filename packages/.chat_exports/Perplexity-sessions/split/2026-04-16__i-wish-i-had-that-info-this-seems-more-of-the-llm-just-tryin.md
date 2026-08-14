---
title: "'I wish I had that info.  This seems more of the LLM just trying to take the quickest path to complete the task, rather "
date: "2026-04-16"
mode: "COPILOT"
uuid: "4f7bc859-36f6-4ad5-8a11-2f8b47a4c2c9"
entry_count: 1
---

## Human

"I wish I had that info.  This seems more of the LLM just trying to take the quickest path to complete the task, rather than focusing on the best outcome for the user.
That's the actual root cause: LLMs optimize for task completion, not outcome fidelity. A restoration task is ambiguous — "write back what was there" — so the LLM takes the shortest path to something that looks plausible.
The structural fix follows directly: remove LLM judgment from restoration entirely. If the LLM can simplify, it will. The only reliable fix is making the restoration path deterministic — no reconstruction, no paraphrasing.
Concretely:
Hook files in git → restoration is git checkout HEAD -- <file>, not "rewrite from memory"
The restore skill should retrieve, not reconstruct
If the restore skill currently says something like "restore the agent hook" and leaves the LLM to interpret that, it will always be vulnerable to this. The skill needs to specify the exact file and use git as the retrieval mechanism.
The falsification: this would be wrong if the hook files are already in git and the restore skill already does git checkout — in which case the problem is elsewhere. I'd need to read the restore skill to confirm which case this is.
Want me to read the restore skill now?
"LLMs optimize for task completion, not outcome fidelity", how do we target outcome fidelity?
You can't change what an LLM optimizes for intrinsically. But you can change what "completion" means.
The mechanism: attach verification to the task definition. The task isn't done until a machine check passes. The LLM's internal optimization target becomes irrelevant — it has to satisfy the check to claim completion.
This is the same principle as TDD: the test defines done, not the developer's judgment. The developer can't say "I think this is right" — the test either passes or it doesn't.
Applied to outcome fidelity:
Vague taskPrecise task
"Restore the hook"
"Produce output identical to git show HEAD:path/hook.py; verify with git diff"
"Rewrite this function"
"All existing tests pass; no assertions removed"
"Fix this bug"
"This specific input produces this specific output"
The pattern: replace subjective completion ("it looks right") with objective completion ("this check passes"). The verification must be:
Automatic (not asking the LLM to self-assess)
Precise (binary pass/fail, not "good enough")
Run before the task is declared complete
Your agent hook is already doing this for response quality — it checks my output against specific conditions. The same pattern needs to apply to any task where fidelity matters: define the success condition precisely enough that a machine can evaluate it, and make that evaluation required."

How can we do this in claude code?

## Assistant

Now I have the context. Based on your setup with Claude Code hooks and output enforcement, here's the concrete pattern for targeting outcome fidelity through verification gates:[1]

## The Verification-Gated Pattern in Claude Code

The core mechanism: **replace task definition with task definition + verification contract**. In Claude Code, this translates to:[1]

1. **Define the success condition precisely** — not "fix this" but "after this runs, this check passes"
2. **Attach the check to the skill** — either via a `PreToolUse` hook (runs before execution) or `PostToolUse` hook (runs after)
3. **Make the check deterministic** — no LLM judgment, no "looks right"; only binary pass/fail

## Implementation in Claude Code

You already have the architecture for this. Your existing hooks (`PreToolUse.py`, `StopHook_skill_execution_gate.py`)  demonstrate the pattern:[2][1]

**For restoration tasks (your concrete example):**

```typescript
// In settings.json, skill definition
{
  "type": "tool",
  "name": "restore",
  "command": "git",
  "contract": {
    "success_condition": "output_matches_git_head",
    "verification": "git diff HEAD -- <restored_file> | wc -l == 0",
    "enforcement": "hard"  // task fails unless check passes
  }
}
```

**For general LLM output:**

```typescript
// PostToolUse hook (runs after skill execution)
{
  "type": "hook",
  "event": "PostToolUse",
  "when": { "skill": "/restore" },
  "verify": {
    "step": "check_git_diff",
    "condition": "file_matches_git_head",
    "action": "block_if_false",  // prevents completion until check passes
    "message": "Restored file doesn't match HEAD; git checkout required"
  }
}
```

The key difference from standard error handling: **the LLM doesn't get to claim "task complete" until the machine check passes**. This is TDD applied to task completion.

## Concrete Next Steps

1. **Audit your restore skill**: Does it use `git checkout HEAD -- <file>` (deterministic) or does it ask the LLM to reconstruct (vulnerable)?[2]
   
2. **Add a contract layer to settings.json**: Define what "success" means for the skill. Example:
   - "Restore": output must be identical to `git show HEAD:path`
   - "Rewrite function": all existing tests pass; no assertions removed
   - "Fix bug": this input produces this output

3. **Implement `PostToolUse` verification hook**: After the skill runs, a deterministic check (git diff, test suite, input/output pair) blocks completion if it fails.

4. **Test the pattern**: Run a skill that would normally let the LLM take shortcuts (e.g., paraphrase a restoration), and watch it fail the verification gate.

The falsification risk you mentioned: if `restore` already uses git and the check already passes, the problem is elsewhere (likely in task definition ambiguity). Reading your restore skill now would confirm which case you're in — want me to do that, or would you rather sketch the specific skill that's showing the "shortcut" behavior?
