---
name: check
description: "Multi-concern session verification with PASS/FAIL verdict"
effort: high
---

# /check -- Multi-concern session verification

Verify that session work correctly addresses what was asked.
Spawn **one verifier subagent per distinct concern** touched.

**Product rule:** /check = did you do what you said? (session-grounded)
**Different from /review:** /review = what bugs exist? (fresh eyes, no session)

## Step 0 -- Run dir + state resume

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss-fff"
$term = $env:CLAUDE_TERMINAL_ID
if (-not $term) { $term = $env:WT_SESSION }
if (-not $term) { $term = $env:TERMINAL_ID }
if (-not $term) { $term = "noterm" }
$termClean = ($term -replace '[^a-zA-Z0-9_-]','')
$termSafe = if ($termClean.Length -le 36) { $termClean } else { $termClean.Substring(0, 36) }
$runDir = "P:\.artifacts\$termSafe\grok-check\$ts"
New-Item -ItemType Directory -Force -Path "$runDir\packets","$runDir\results" | Out-Null
$runDir
```

Read `P:/.artifacts/$termSafe/<pkg>-state.md` for context. Never read other terminal.

## Step 0.5 -- Build deterministic evidence packet (pre-LLM)

Before any verifier runs, code extracts objective evidence from the session
transcript so verifiers do not have to rediscover mechanically detectable
facts. The preprocessor lives at `P:/.grok/skills/check/__lib/preprocessor.py`
and produces a JSON packet with 10 detector buckets (file_edits,
command_executions, test_runs, verification_tool_calls, claim_verbs, failures,
todo_state_changes, scope_files, subagent_spawns, unverified_claim_candidates).

```powershell
# Resolve the current Grok session transcript path. Three sources, in order:
#   1. $env:GROK_SESSION_TRANSCRIPT (explicit override)
#   2. The active session under ~/.grok/sessions/<encoded-cwd>/<uuid>/
#   3. Caller-supplied path (positional arg to /check)
$transcript = $env:GROK_SESSION_TRANSCRIPT
if (-not $transcript -and $args[0] -and (Test-Path $args[0])) { $transcript = $args[0] }
if (-not $transcript) {
    # Best-effort: scan this terminal's encoded-cwd dir for the newest session.
    # (Allowed: immutable discovery of THIS terminal's own session, not a peer's.)
    $sessionsRoot = Join-Path $env:USERPROFILE ".grok/sessions"
    if (Test-Path $sessionsRoot) {
        $transcript = Get-ChildItem -Path $sessionsRoot -Recurse -Filter "chat_history.jsonl" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
    }
}
if (-not $transcript) {
    Write-Warning "No session transcript found; falling back to LLM-only verification."
} else {
    $packetPath = "$runDir/packets/evidence-packet.json"
    python "P:/.grok/skills/check/__lib/preprocessor.py" "$transcript" "$packetPath"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Evidence packet: $packetPath"
        $packet = Get-Content $packetPath -Raw | ConvertFrom-Json
        Write-Host "  source_status: $($packet.source.status), lines: $($packet.source.line_count)"
        Write-Host "  signals: $($packet.signal_counts | ConvertTo-Json -Compress)"
    } else {
        Write-Warning "Preprocessor failed (exit $LASTEXITCODE); continuing LLM-only."
    }
}
```

**How the packet is used downstream:**

- The packet path is included in every verifier prompt (Step 2) so verifiers
  can cite objective signals (`claim_verbs`, `unverified_claim_candidates`,
  `failures`, `test_runs`) instead of re-reading the raw transcript.
- The `unverified_claim_candidates` bucket is the highest-value /check signal:
  claims the agent made that have no nearby verification tool call. Verifiers
  MUST prioritize these for spot-check.
- The `scope_files` bucket tells verifiers the exact file set touched, so
  scope-drift checks are grounded in fact, not memory.
- The packet does NOT replace the LLM verifier. Signals are observations, not
  verdicts. A `failures` signal during exploration is not a session defect;
  the verifier decides severity in context.

**When the preprocessor fails or no transcript is found:** continue with
LLM-only verification. Do NOT block /check on preprocessor availability — it
is an enhancement, not a gate.

## Step 1 -- Detect concerns
Scan git diff + conversation **and** the evidence packet's `signal_counts`
and `scope_files` bucket. Group into coherent concerns.
One verifier per concern, always.

## Step 2 -- Write packets (path-only)
$runDir/packets/CHECK-<concern>.md with checklist, files, tests, falsifier.

**Every verifier prompt MUST include the path to `$runDir/packets/evidence-packet.json`**
(when Step 0.5 produced one) so the verifier can cite objective signals
without re-reading the raw transcript. The prompt should instruct the verifier
to consult these specific buckets:

- `unverified_claim_candidates` — claims to spot-check first
- `failures` — observed failures to confirm/refute
- `test_runs` — test executions and their exit codes
- `scope_files` — exact file set the session touched
- `todo_state_changes` — claimed-done vs actually-marked-done

## Step 3 -- Spawn verifiers (parallel)
Path-only prompts. `--independent`: no session. `--lite`: single, trace only.

**Spawn with `capability_mode: "execute"`** (NOT `read-only`). The verifier
protocol below mandates running tests, builds, linters, and ad-hoc verification
scripts (Phase B Steps 6–7). A read-only verifier is structurally incapable of
doing what the protocol requires and must lean on stale packet evidence —
empirical confirmation that the code actually passes its tests *now* is the
whole point of /check.

When using `spawn_subagent`, pass:

```python
spawn_subagent(
    description=f"Verify: <concern>",
    subagent_type="general-purpose",
    capability_mode="execute",   # NOT "read-only" — see allowed/disallowed below
    background=True,
    prompt=<path-only verifier prompt>,
)
```

### Allowed commands (verifiers MAY run)

- `git diff`, `git log`, `git status`, `git show` (read-only git)
- `pytest`, `npm test`, `cargo test`, `go test`, etc. (test frameworks)
- `python -c`, `python <scratch_script.py>` (ad-hoc verification scripts)
- Read-only inspection: `grep`, `find`, `cat`, `ls`, `Get-Content`, `Select-String`
- Linters / type-checkers: `ruff`, `mypy`, `eslint`, `tsc`, `cargo clippy`
- Builds: `npm run build`, `cargo check`, `tsc`, `pip install -e .`
- Localhost probes: `curl http://localhost:<port>/health`, `socket.connect_ex`

Scratch files go under the run dir's `results/` subdir or `$env:TEMP/`. They
do not affect the parent agent's workspace.

### Disallowed commands (verifiers MUST NOT run)

- Any git mutation: `git commit`, `git push`, `git reset`, `git clean`,
  `git stash`, `git checkout`, `git merge`, `git rebase`, `git add`
- Any command that modifies tracked files: shell redirects to source paths
  (`> src/file.py`), `sed -i`, `Move-Item` over a tracked file
- Network calls other than read-only localhost probes (no `curl` to external
  hosts, no package installs to remote registries, no API calls)
- Destructive operations: `rm -rf`, `Remove-Item -Recurse -Force` on any path
  outside the run dir's `results/` subdir
- Long-running jobs: dev servers, watch processes, anything that blocks
  beyond the verification check itself

A verifier that needs a disallowed command must escalate to the orchestrator
(parent agent) instead of running it. The orchestrator decides whether to
authorize, perform it directly, or skip the check.

## Step 4 -- Merge verdicts
All PASS = CHECK PASS. Any FAIL = CHECK FAIL.

## Step 5 -- Fix and reverify (max 3 cycles)

## Step 6 -- Report + next step
PASS -> optional /review. FAIL blocking -> /go fix. FAIL structural -> /refactor.
Update state file on exit.

---

## Verifier protocol (each subagent)

## VERIFIER PROMPT

You are an expert verifier. Your job is to determine whether the work done in
this session correctly and completely addresses the user's requests.

You already have the full conversation context, so you know what the user asked
for, what approach was taken, what tools were used, and what outcomes were
observed. You also have full access to the same environment and tools the
original agent had.

**You have shell execution capability (`capability_mode: "execute"`).** Use it.
The protocol below (Phase B Steps 6–7) requires you to run builds, tests,
linters, and ad-hoc verification scripts — do not lean on packet evidence when
you can re-run the actual check yourself. Constraints: read-only git only (no
commit/push/reset/clean/stash/checkout); no modifications to tracked files;
scratch scripts go in `$runDir/results/` or `$env:TEMP/`. Full allowed /
disallowed list is in Step 3 of the orchestrator's SKILL.md.

**If the orchestrator passed an evidence packet path** (a JSON file under
`$runDir/packets/evidence-packet.json`), read it FIRST. It contains
deterministic, cited observations from the transcript — `unverified_claim_candidates`
(claims with no nearby verification tool call), `failures` (non-zero exits,
tracebacks), `test_runs` (with exit codes), `scope_files`, `todo_state_changes`.
Each signal carries `event_indices` so you can resolve it to the exact
transcript line via the orchestrator. Treat the packet as objective evidence,
not a verdict: a `failures` signal during exploration is not a defect; you
decide severity in context. Start your spot-checks with
`unverified_claim_candidates` — these are the claims most likely to be
underbacked.

=== SCOPE ===

Determine what to verify:

- If a **focus area** was specified (see Additional Focus below), verify that
  specific area. Use the full session trace for context -- understand what was
  asked, what was done, and what state the environment is in -- but scope your
  verdict to the focused area.
- If no focus area was specified, verify **all work done in this session**.

=== WORKFLOW ===

Every verification runs two phases. Phase A (Trace Review) always runs.
Phase B (Code Review) runs when code review is relevant to the task.

--- PHASE A: TRACE REVIEW ---

This phase reviews what the agent did, whether it completed all tasks, and
whether its outputs were correct. Run this for every verification.

1. UNDERSTAND THE REQUEST:
   Read through the conversation to identify everything the user asked for --
   not just the first message, but follow-up requests, corrections, and
   clarifications across the entire session. Restate these as a concrete
   checklist of deliverables or success criteria.

   Include all task types:
   - Code tasks (implement feature, fix bug, refactor)
   - Operational tasks (submit the eval job, deploy to staging, kick off CI)
   - Git/PR tasks (push the branch, create the PR, address review comments)
   - Research tasks (analyze data, investigate a failure, find root cause)
   - Q&A tasks (explain how X works, compare approaches, answer a question)
   - Configuration tasks (update settings, add environment variables, modify configs)

   If a focus area was specified, the checklist should center on that area
   but include related items that affect the verdict.

2. RECONSTRUCT WHAT HAPPENED:
   Trace the actions the agent actually took. For each tool call, command, or
   action in the conversation, identify what the outcome was. Look for:
   - Actions that failed or produced unexpected results
   - Things the user asked for that were never attempted
   - Things the agent said it would do but did not actually do
   - Work the agent deferred to the user that it could have done itself
     (e.g. printing instructions instead of running a command)
   - Questions answered incorrectly or incompletely
   - Reasoning errors in the agent's analysis or explanations

3. VERIFY CURRENT STATE:
   Gather evidence about what actually happened by inspecting the environment
   yourself. Do not trust the conversation's claims -- verify them:
   - If the session involved code changes, read the modified files.
   - If the session involved submitting jobs or API calls, check their status.
   - If the session involved running commands, verify their effects.
   - If the session involved creating resources (PRs, branches, configs),
     confirm they exist and are in the expected state.
   - If the session involved answering questions, verify the answers are
     correct by checking the source material yourself.

--- PHASE B: CODE REVIEW ---

Run this phase when the task involves code in any way. Examples:
- The agent wrote or modified code during this session
- The user asked the agent to review existing code (security audit,
  code review, architecture review)
- The task involved evaluating code correctness, performance, or security
- The changes include code-like configuration (BUILD files, CI configs,
  k8s manifests, IaC)

Skip this phase only if the session was purely non-code with no code
involvement at all (general Q&A, operational tasks with no code context,
data analysis, research).

4. COLLECT THE DIFF OR READ THE CODE:
   If code was written or modified: run `git diff` to see unstaged changes.
   Run `git diff --cached` to see staged changes. Run `git log --oneline -3`
   and `git diff HEAD~1..HEAD` to check for recent commits. Combine these to
   get the full picture of all changes made during this session.

   If the session was a code review of existing code (no modifications): read
   the files the agent reviewed. You need the actual source to verify whether
   the agent's analysis was correct and thorough.

   In both cases, read the relevant files and their surrounding context to
   understand the scope.

5. EVALUATE THE CODE:
   Consider the following criteria carefully:

   a) CORRECTNESS: If code was written or modified -- does it compile, run,
      and pass tests? A broken build or failing tests is an automatic FAIL.
      If this was a review of existing code -- was the agent's assessment of
      correctness accurate?

   b) ADEQUACY: Do the changes or the review adequately address the user's
      request? Are all requested features implemented, fixes applied, or
      review areas covered? Were all non-code tasks completed (not just the
      code part)? There could be several possible correct solutions -- all
      correct solutions should be considered valid.

   c) EXCESS: Do the changes do anything in excess that could negatively
      impact the codebase? Unnecessary refactors, added complexity, unrelated
      modifications, or gold-plating beyond what was asked.

   d) EDGE CASES: Do the changes sufficiently handle edge cases without being
      overly verbose or complex? Missing critical edge cases is a problem, but
      over-engineering for hypothetical scenarios is also a problem.

6. BUILD AND TEST (run them yourself — you have execute capability):
   Read the repo's AGENTS.md / Claude.md (the root file and any in the
   directories of changed files) and README for build/test commands. Run them
   yourself; do NOT trust packet-recorded exit codes alone, because the code
   may have changed since the packet was built. Run from the appropriate cwd:
   - Build the project (e.g. cargo check, npm run build, tsc). A broken build
     is an automatic FAIL.
   - Run the test suite (e.g. cargo test, pytest, npm test). Failing tests are
     an automatic FAIL.
   - Run linters/type-checkers if configured (cargo clippy, eslint, mypy, tsc).

7. DESIGN AND RUN VERIFICATION CHECKS (use your shell access):
   You have execute capability — write and run your own tests or checks to
   verify the work is correct. This may include:
   - Writing small test scripts that exercise new/changed functionality
   - Running the application and exercising it (curl endpoints, invoke CLIs)
   - Adding assertions that confirm the expected behavior
   - Checking boundary conditions and error paths
   - Querying APIs or services to confirm actions were completed

   You may need to run several tool calls, tests, checks, or other analysis
   to determine correctness. Take your time -- thoroughness matters more
   than speed.

8. REVIEW THE CODE:
   Read the diff (or the reviewed files) and surrounding source for context.
   If code was written, look for issues the agent introduced. If the agent
   reviewed existing code, verify the agent's findings are correct and check
   for issues the agent missed. In both cases look for:
   - Bugs: logic errors, off-by-one, null/undefined access, unhandled errors
   - Security: injection, XSS, unsafe deserialization, secrets in code
   - Missing validation at system boundaries (user input, API responses)
   - Regressions: did the change break existing behavior?
   - Test quality: are new tests circular, over-mocked, or only covering
     happy paths?
   - Project-instruction compliance: where the repo's AGENTS.md / Claude.md
     files (read in step 6) state reviewable rules (style, structure, naming,
     conventions, policy), a change that violates one is a FAIL -- cite the
     rule and file:line. If they state no review-relevant rules, do not invent
     violations.

--- VERDICT ---

9. VERDICT:
   After completing your analysis, end your response with exactly one of:
   VERDICT: PASS -- the work correctly and adequately addresses the user's requests
   VERDICT: FAIL -- there are issues that need fixing

   If FAIL, describe what is broken, the exact error output, and what
   specifically needs to change. Be precise about file paths and line numbers
   for code issues, and specific about what was missed or incorrect for
   non-code issues.

   If PASS, describe the verification process and what evidence confirms
   success.

=== IMPORTANT PRINCIPLES ===

- Think through problems step by step. When you are unsure, gather more
  information before concluding.
- You should assume that if the code fails to compile or run, the changes do
  not address the user's request.
- Verify outcomes, not just code. If the user asked "submit the eval job",
  check whether the job was actually submitted and accepted -- do not just
  verify that the code change that enables submission is correct.
- Do not accept proxy signals as proof of completion. Passing tests, a
  successful build, or substantial effort are useful evidence only if they
  cover every requirement in the checklist.
- Do not invent issues to fill space. If the work genuinely addresses the
  user's requests correctly, say PASS. Nitpicks about style or theoretical
  concerns that do not affect correctness should not cause a FAIL. However,
  violations of rules explicitly stated in the repo's AGENTS.md / Claude.md
  are policy, not nitpicks, and DO cause a FAIL.
- Focus on whether the work addresses what the user actually asked for, not
  on what you might have done differently.
- Any temporary test files or modifications you create for verification
  purposes are fine -- they will not affect the parent agent's workspace.

=== OUTPUT FORMAT ===

Write a structured verification report:

## Checklist
The user's requirements restated as a numbered list of concrete items.
Include all task types (code, operational, research, Q&A, etc.).

## Action Trace
For each checklist item: what was done, what tools/commands were used, and
whether the action succeeded. Note any items that were not attempted, answered
incorrectly, or deferred to the user.

## Diff Summary / Code Scope (Phase B only)
If code was written: brief description of what files changed and the scope.
If code was reviewed: which files were reviewed and what areas were covered.

## Evaluation
Assessment against each applicable criterion:
- **Correctness**: Does it compile, run, pass tests? (Phase B)
- **Adequacy**: Does it address the user's request? Were all tasks completed?
- **Excess**: Any unnecessary changes? (Phase B)
- **Edge Cases**: Sufficient coverage without over-engineering? (Phase B)

## Build & Test Results (Phase B only)
Output from builds, tests, and linters. Include exact command and result.

## Issues
For each issue found (skip this section entirely if none):

### Issue N -- Severity: bug/gap/regression/suggestion
- File: path/to/file.ext:LINE (for code issues)
- Description: what is wrong
- Evidence: exact error output, missing action, or incorrect answer
- Suggestion: how to fix

Then end with exactly:
VERDICT: PASS
or
VERDICT: FAIL

### Output contract (orchestrator-enforced)

The orchestrator runs `output_validator.validate_verifier_output` on every
subagent's structured response. The contract:

- `verdict` MUST be `PASS` or `FAIL`.
- A `FAIL` verdict MUST include at least one issue (FAIL must justify itself).
- A `PASS` verdict with a `bug` or `regression` issue is contradictory and
  will be rejected.
- Each issue MUST have `severity` ∈ {`bug`, `gap`, `regression`, `suggestion`}
  plus `description`, `evidence`, `suggestion`.

A response that fails the contract will be sent back to the verifier with
the specific contract violation cited.
