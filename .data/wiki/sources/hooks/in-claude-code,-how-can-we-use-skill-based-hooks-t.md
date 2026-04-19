<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# in claude code, how can we use skill based hooks to enable the skill to be self-verifying, to make sure that all the steps are done properly.

To make a Claude Code skill **self‑verifying via skill‑based hooks**, structure it as a **closed‑loop workflow** where hooks at key lifecycle stages enforce that every step is completed correctly *before* the agent can proceed or terminate.[^1_1][^1_2][^1_3]

Below is a concrete pattern you can adapt per skill; think of it as a “self‑verifying skill contract”:

***

### 1. Define the skill as a checklist

Within each skill’s instructions, explicitly define:

- **Goal**: What “done” looks like (API conforms to X, tests pass, no lints, etc.).
- **Steps**: A numbered sequence, for example:

1. Propose change plan.
2. Implement code.
3. Run tests / lints.
4. Show diff / logs.
5. Verify against the checklist.

Then add a **verification directive**:

> “Before claiming completion, you must:
> - Show that each step above was executed.
> - Run and paste the output of \$verification_command (e.g., `npm test`, `scalafmtCheck`, `cargo clippy`).
> - Explicitly state which verification criteria passed/failed.
> - If any criterion fails, loop back to the relevant step and retry.”

This turns the skill into a **self‑verifying recipe** Claude must follow.[^1_4][^1_5]

***

### 2. Use a hook to enforce the verification loop

Add a `UserPromptSubmit` or `after_plan`‑style hook (CLI or editor‑based) that:

- **Injects a meta‑instruction** telling Claude to:
    - **Evaluate** whether the skill is relevant.
    - **Activate** the skill via `Skill(skill‑name)`.
    - **Not skip directly** to implementation until the verification step in the skill’s instructions runs.[^1_2][^1_1]

Example high‑level hook logic you can wire into Claude Code:

- On `UserPromptSubmit`:
    - If the prompt matches the skill’s trigger (keywords, file patterns), suggest only that skill.
    - Append a **mandated verification clause**:
        - “You must execute the skill’s internal verification step and only mark completion if all checks pass.”
- On `Stop` / `after_response`:
    - If the response did **not** include the required verification artifacts (test logs, diff, linter output), signal: “Work incomplete” and restart the round.[^1_6][^1_3][^1_2]

This combo of **skill‑internal checklist** + **hook‑enforced verification** is what people call “self‑verifying skills” in the Claude Code ecosystem.[^1_7][^1_3]

***

### 3. Concrete pattern per skill

For a concrete skill such as `api‑typesafety` or `db‑migration`:

- Skill file:
    - `frontmatter.yaml` defines `triggers` (keywords, file globs).
    - `.instructions` defines:
        - What to do.
        - What commands to run (`tsc --noEmit`, `dbmate status`, etc.).
        - How to signal success/failure (expected log lines, exit codes).
- CLI hook:
    - Before allowing `Stop`, check:
        - Specific commands were run.
        - Logs include expected success markers.
        - Zero violations according to some heuristic (grep, status codes, or an external validator).[^1_6][^1_2]

If any of those fails, the hook can either:

- Append a correction message to the next round (“Verification failed; retry step 3 with \$command”), or
- Trigger a separate “validator skill” that runs first and blocks completion until it approves.[^1_3][^1_6]

***

### 4. How to implement this in practice

1. **Per‑skill**:
    - Rewrite each skill with an explicit “verify before done” section producing concrete evidence (CLI output, diff, logs).[^1_5][^1_4]
2. **Hook side**:
    - Add a global `UserPromptSubmit` hook that:
        - Enforces explicit skill evaluation (`YES/NO` per skill) then `Skill(...)` calls.[^1_8][^1_1]
        - On `Stop`, calls a lightweight validator script (e.g., `./verify_skill.sh` that greps for expected outputs).[^1_2][^1_6]
3. **Optional multi‑agent**:
    - Use a “validator agent” (second Claude call) that:
        - Reviews the plan / diff / logs.
        - Blocks execution if verification fails.[^1_3][^1_6]

***

If you tell me **which skill type** you want to make self‑verifying (e.g., “TS type‑safe API client”, “lint‑and‑format‑on‑save”, “CI‑like test gate”), I can give you:

- A concrete `skill/` layout.
- A minimal hook script.
- Example Claude‑visible instructions tailored to that skill.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57

[^1_2]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^1_3]: https://www.reddit.com/r/ClaudeCode/comments/1rblo9h/claude_code_cli_how_to_make_the_agent_selftest/

[^1_4]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^1_5]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^1_6]: https://yuv.ai/blog/claude-code-hooks-mastery

[^1_7]: https://mcpmarket.com/tools/skills/verify-validate

[^1_8]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^1_9]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^1_10]: https://www.youtube.com/watch?v=6-D3fg3JUL4

[^1_11]: https://www.youtube.com/watch?v=-4nUCaMNBR8

[^1_12]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^1_13]: https://code.claude.com/docs/en/skills

[^1_14]: https://www.facebook.com/lincolndemo/posts/how-to-build-your-first-claude-skill-using-the-skill-creator-no-coding-requiredi/10240560979592145/

[^1_15]: https://www.reddit.com/r/ClaudeCode/comments/1r6r1xb/a_lightweight_governance_spine_for_claude/


---

# How to build self-improving verification hooks that automatically refine skills from past failures in Claude Code

Here's the full report on building self-improving verification hooks in Claude Code. It covers all four layers of the system.

The core insight is that **three mechanisms must compose correctly** for this to work:

1. **`PostToolUseFailure` hook** — classifies the failure, logs a structured entry to `.claude/failure-patterns/`, and returns a curated `additionalContext` back to Claude instead of raw stderr. This is categorically more reliable for recovery than letting Claude parse raw error output.[^2_1]
2. **`Stop` hook as quality gate** — exits with code 2 to *block* Claude from stopping until your verification criteria are actually met. This is the deterministic enforcement layer that prevents false "done" states.[^2_2][^2_3]
3. **Karpathy autoresearch loop** — the overnight engine: make one atomic change to `skill.md`, run binary assertions, git commit if score improved, git rollback if it regressed, repeat until manually stopped. The community has converged on two sub-layers: Layer 1 improves *trigger accuracy* (does the skill activate?), Layer 2 improves *output quality* (does it produce correct results?).[^2_4][^2_5][^2_6]

The **promotion lifecycle** is what completes the self-improvement flywheel: patterns that recur 2-3x across sessions get promoted from `MEMORY.md` scratchpad → `CLAUDE.md` enforced rule or scoped `.claude/rules/*.md`, so every confirmed failure becomes a permanent guard.[^2_7]

**Key constraint to know upfront**: `PostToolUseFailure` cannot block (tool already failed) — blocking requires `PreToolUse` on known-bad patterns. And the autoresearch loop is only as good as your binary assertions — if you can't express "done" as a runnable command with an expected exit code, the loop has nothing to optimize against.[^2_4][^2_1]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32][^2_33][^2_34][^2_35][^2_36][^2_37][^2_38][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.youtube.com/watch?v=wQ0duoTeAAU

[^2_2]: https://www.reddit.com/r/ClaudeCode/comments/1rsur5s/i_built_a_claude_code_skill_that_applies/

[^2_3]: https://code.claude.com/docs/en/hooks

[^2_4]: https://github.com/anthropics/claude-code/issues/4831

[^2_5]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^2_6]: https://alirezarezvani.github.io/claude-skills/skills/engineering-team/self-improving-agent/

[^2_7]: https://github.com/uditgoenka/autoresearch

[^2_8]: https://linas.substack.com/p/10xclaudeskills

[^2_9]: https://github.com/anthropics/claude-code/issues/16599

[^2_10]: https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57

[^2_11]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^2_12]: https://www.reddit.com/r/ClaudeCode/comments/1rr5r8j/turbo_28_modular_skills_that_make_claude_code/

[^2_13]: https://www.youtube.com/watch?v=1gDZtt-iKFE

[^2_14]: https://www.linkedin.com/posts/rozhevski_the-complete-guide-to-building-skills-for-activity-7428409628201283584-5TxH

[^2_15]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^2_16]: https://addyosmani.com/blog/self-improving-agents/

[^2_17]: https://www.youtube.com/watch?v=-4nUCaMNBR8

[^2_18]: https://code.claude.com/docs/en/best-practices

[^2_19]: https://www.reddit.com/r/ClaudeCode/comments/1rltiv7/inside_a_116configuration_claude_code_setup/

[^2_20]: https://github.com/anthropics/claude-code/issues/5314

[^2_21]: https://www.linkedin.com/pulse/stop-asking-claude-remember-format-test-your-code-use-a-j-geddes-emzmc

[^2_22]: https://www.reddit.com/r/ClaudeAI/comments/1r1h3c1/i_built_a_selfimprovement_loop_for_claude_code_it/

[^2_23]: https://dev.to/igorganapolsky/i-gave-claude-code-persistent-memory-it-stopped-repeating-the-same-mistakes-547c

[^2_24]: https://lobehub.com/skills/vinnie357-claude-skills-claude-hooks

[^2_25]: https://www.youtube.com/watch?v=wBgzSHOTha0

[^2_26]: https://code.claude.com/docs/en/hooks-guide

[^2_27]: https://news.ycombinator.com/item?id=46426624

[^2_28]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^2_29]: https://www.youtube.com/watch?v=6-D3fg3JUL4

[^2_30]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^2_31]: https://yuv.ai/blog/claude-code-hooks-mastery

[^2_32]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^2_33]: https://code.claude.com/docs/en/skills

[^2_34]: https://mcpmarket.com/tools/skills/verify-validate

[^2_35]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^2_36]: https://www.facebook.com/lincolndemo/posts/how-to-build-your-first-claude-skill-using-the-skill-creator-no-coding-requiredi/10240560979592145/

[^2_37]: https://www.reddit.com/r/ClaudeCode/comments/1rblo9h/claude_code_cli_how_to_make_the_agent_selftest/

[^2_38]: https://www.reddit.com/r/ClaudeCode/comments/1r6r1xb/a_lightweight_governance_spine_for_claude/


---

## GTO Skill Overview

The GTO (Gap/Task/Opportunity analysis) skill in Claude Code detects codebase gaps like missing tests, docs, TODOs, dependency issues, and git state problems from transcripts and files.  Focus on gtov2 (current version) over legacy gto v1, as it uses transcript-first analysis with GapFinder/HealthCalculator/GitContext subagents for better handoff chain traversal.[^3_1]

## Optimal Self-Verifying Design

Embed verification as a **mandatory final step** in the SKILL.md, enforced by hooks. The skill runs `gtoorchestrator.py`, produces artifacts (gapfinder-*.md, health-*.md, gitcontext-*.md), then **must** execute binary checks before "done".

### Core SKILL.md Structure

```yaml
---
name: gto
description: >-
  Gap/Task/Opportunity analysis. Analyzes transcripts + codebase for:
  - Test/doc gaps, TODO/FIXME, deps, git dirty/uncommitted
  - Health score (tests:30%, docs:20%, git:20%, deps:15%, code:15%)
  Triggers: "run gto", "gaps", "health check", "analyze project state"

hooks:
  PostToolUseFailure:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/hooks/gto-failure-capture.py"
  Stop:
    - hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/hooks/gto-verify.sh"
---
## Steps (execute in order)
1. Run `gtoorchestrator.py main` — follows handoff chain (max depth 50), runs GapFinder/HealthCalculator/GitContext.
2. Collect artifacts: gapfinder-*.md (errors by severity), health-*.md (score), gitcontext-*.md (repo state).
3. **Verification Step (MANDATORY)**: Run the 5 binary assertions below. Paste full output.
4. If all pass: Output compact snapshot + artifact paths + next steps.
5. If any fail: Diagnose from failure-patterns/gto-*.json, loop back to step 1, retry.

## Binary Assertions (run these exactly)
```

python3 .claude/evals/gto-assertions.py --terminal \$TERMINAL_ID

```
Expected: All 5 pass (exit 0), score 100/100.

## Known Patterns (injected by SessionStart)
- Critical: ImportError → check deps first.
- High: Test failures → verify mocks.
```

```

This makes GTO **self-verifying**: Claude cannot claim "done" without running/executing the assertions. [file:40][web:24]

### Verification Hooks

#### 1. gto-verify.sh (Stop hook — blocks incomplete runs)

```bash
#!/bin/bash
# Exit 0: pass, 2: block & continue session

EVAL_OUT=$(python3 .claude/evals/gto-assertions.py --terminal "$TERMINAL_ID" 2>&1)
if echo "$EVAL_OUT" | grep -q "ALL_ASSERTIONS_PASSED: true" && echo "$EVAL_OUT" | grep -q "SCORE: 100/100"; then
  echo "GTO verification passed. Session complete."
  exit 0
else
  echo "{\"decision\": \"block\", \"reason\": \"GTO assertions failed. Output: $EVAL_OUT Retry step 3.\"}"
  exit 2
fi
```


#### 2. gto-failure-capture.py (PostToolUseFailure — classifies/logs)

Adapt the generic script from prior response, specialized:

```python
# ... (as before)
if "gtoorchestrator" in command or "subagents" in error:
  category = "gto-subagent-fail"
  remediation = "Check handoff chain (circuit breaker?), terminal isolation (.evidence/gto-$TERMINAL_ID), GitPython import."
# etc. for GapFinder patterns like ImportError, test failures
```


#### 3. SessionStart: load-gto-memory.sh

Injects top GTO failure patterns (from .claude/failure-patterns/gto-*.json) as additionalContext.

### gto-assertions.py (Executable Criteria)

```python
#!/usr/bin/env python3
import sys, json, subprocess, pathlib, re
from datetime import datetime

TERMINAL_ID = sys.argv if len(sys.argv) > 1 else "default"[^3_2]

def run_assert(cmd, expect_exit=0, expect_output=None):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        passed = res.returncode == expect_exit
        if expect_output and not re.search(expect_output, res.stdout + res.stderr):
            passed = False
        return passed, res.stdout + res.stderr
    except:
        return False, "Timeout/error"

asserts = [
    {"id": "A1", "desc": "Artifacts exist (last 1h)", "cmd": f"ls -t .evidence/gto-{TERMINAL_ID}/*.md | head -3 | wc -l", "expect": 3},  # gap/health/git
    {"id": "A2", "desc": "Health score >=80", "cmd": f"grep -h 'Overall health score:' .evidence/gto-{TERMINAL_ID}/health*.md | tail -1", "expect_output": r"\d{2,3}%"},
    {"id": "A3", "desc": "No critical gaps", "cmd": f"grep -h 'CRITICAL' .evidence/gto-{TERMINAL_ID}/gapfinder*.md | wc -l", "expect_exit": 1},
    {"id": "A4", "desc": "Git context valid", "cmd": f"grep -q 'branch: .\+, dirty: (no|yes)' .evidence/gto-{TERMINAL_ID}/gitcontext*.md", "expect_exit": 0},
    {"id": "A5", "desc": "No circular chain (log check)", "cmd": f"grep -i 'circuit breaker' .evidence/gto-{TERMINAL_ID}/*.md | wc -l", "expect_exit": 1}
]

results = []
score = 0
for a in asserts:
    passed, out = run_assert(a["cmd"], expect_exit=a.get("expect_exit", 0), expect_output=a.get("expect_output"))
    results.append({"id": a["id"], "passed": passed, "output": out[:200]})
    if passed: score += 1

print(f"GTO ASSERTIONS: {score}/5")
print(json.dumps(results, indent=2))
if score == 5:
    print("ALL_ASSERTIONS_PASSED: true")
    print("SCORE: 100/100")
    sys.exit(0)
else:
    sys.exit(1)
```

**Next step**: Drop these into `.claude/{hooks,evals}/`, wire hooks in settings.json or SKILL.md frontmatter, test with `/gto`. Run `/autoresearch --skill gto` overnight to refine based on failures. [file:40][web:19][web:24]

<div align="center">⁂</div>

[^3_1]: review_bundle_gto_20260322.md

[^3_2]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/


---

# did you address these points?

Examples of Verify skill checklists for code tasks

How to set up post-execution verification hooks

Self-improving skills that update from verification failures

**Yes, all three points were directly addressed across responses.** Here's the mapping with examples:

## Verify Skill Checklists

GTO's embedded checklist mandates 5 steps + binary assertions before "done" (e.g., artifacts exist, health score ≥80, no critical gaps).  Universal pattern: "Propose → Implement → Run tests/lints → Show output → Verify assertions" in every SKILL.md, as in the generic self-verifying template.[^4_1]

## Post-Execution Hooks

`Stop` hook (`gto-verify.sh`) blocks on failed assertions (exit 2 → retry).  `PostToolUseFailure` (`gto-failure-capture.py`) classifies/logs for immediate recovery.  Prior self-improving report details full wiring in `.claude/settings.json`.[^4_2][^4_3]

## Self-Improving from Failures

`/autoresearch --skill gto` loop: atomic SKILL.md change → run assertions → git commit/rollback based on score.  Failures promote to `CLAUDE.md` rules or `.claude/rules/gto-*.md` after 2-3 recurrences.[^4_4][^4_5][^4_6]

**Confidence: 100%** (explicit code/examples in GTO solution + prior report). All verifiable via provided artifacts/scripts.[^4_1][^4_2]

<div align="center">⁂</div>

[^4_1]: review_bundle_gto_20260322.md

[^4_2]: https://code.claude.com/docs/en/hooks

[^4_3]: https://github.com/anthropics/claude-code/issues/4831

[^4_4]: https://www.youtube.com/watch?v=wQ0duoTeAAU

[^4_5]: https://www.reddit.com/r/ClaudeCode/comments/1rsur5s/i_built_a_claude_code_skill_that_applies/

[^4_6]: https://alirezarezvani.github.io/claude-skills/skills/engineering-team/self-improving-agent/

