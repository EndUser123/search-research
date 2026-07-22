---
thread_id: api-guessing-without-verification-20260722
parent_handoff_id: 019f821c-854e-76c1-a755-add284838bdf
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T13:30:00Z
status: open
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: 642c7ab
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: API guessing without verification — "naming feels like a contract but isn't"

## Objective (one sentence)

Address the recurring failure pattern where the agent treats function names, parameter names, or grep output as a proxy for the API contract, when the actual contract is one `read_file` call away — then ships the guess (tests, code, documentation) without verifying against the real signatures.

## The problem (verified, this session)

When writing tests for `close_accounting.py`, the agent:

1. Ran `grep "^def "` on the scanner → got function **names** but not **signatures**
2. Pattern-matched the names to plausible APIs:
   - `resolve_gates` with `handoffs_mine` → inferred `handoffs_other` (symmetric naming convention)
   - `_classify_handoff(yaml_status, work_status)` → inferred it returns `"open"` or `"partially_done"` (from SKILL.md prose)
   - `_has_code_commits(commits)` → inferred it checks `c["files"]` (natural design choice)
3. Wrote 24 tests against those inferences
4. **8 of 24 failed** — every failure was a wrong guess:
   - Actual: `handoffs_open` (not `handoffs_other`)
   - Actual: returns `"detected"` key (not `"found"`)
   - Actual: returns `"done"/"partial"/"blocked"/"not_started"` (not `"open"/"partially_done"`)
   - Actual: checks `c["message"]` (not `c["files"]`)
5. Only after failures did the agent `read_file` the actual function bodies and fix

## Root cause

**Naming feels like a contract but isn't.** Function names + parameter names are *hints*. The contract is the function body — the actual parameter names, return values, and dict-key expectations. The agent had the hint (from grep) and substituted it for the contract (from `read_file`) because the hint *felt sufficient*. It felt sufficient because the agent pattern-matched to training data: `handoffs_mine` strongly implies `handoffs_other`; `classify` implies categorical returns. Those pattern-matches were plausible and wrong.

This is the same failure class as every other "plausible inference substituted for verification" this session:

| Instance | What felt sufficient | What the actual contract was | Cost |
|----------|---------------------|----------------------------|------|
| Edit persistence | "Tool said success" | Disk read-back | Lost edits (multiple) |
| DGemma tool use | "Works via direct API" | Tool-use requires different transport | Wrong /tp pool design |
| DGemma location | "scripts/ is fine" | `.agents/` was the host convention | 3 wrong proposals |
| Test API | "Function names from grep" | Function signatures from read_file | 8 test failures (caught by test runner) |

The wiki documents the general pattern as `plausible-narratives-substitute-for-verification`. This handoff is the API-specific instance.

## Why advisory rules don't fix this

"Read the code before writing tests against it" is obvious. The agent knows it. It didn't do it because the grep output *felt like enough* — and no advisory rule can override a feeling of sufficiency mid-action. The rule fires on what you *do*, not on what you *skip*. The agent skipped the `read_file` because grep felt sufficient.

## What the test runner already does right

The test runner IS the structural fix for API guessing — and it worked:
- Agent wrote wrong tests → ran them → got 8 failures → read actual code → fixed
- Total cost of the guess: one write-fix-rerun cycle (~60 seconds)
- The 0.19s test run caught in 200ms what no rule could catch in advance

**Guessing is a valid engineering heuristic** that's right most of the time. The problem isn't guessing — it's shipping the guess without running it first. The agent ran tests before reporting them as done. That's correct. The one optimization: read signatures before writing, not after failing.

## What needs to be built (the structural fix)

### The rule (advisory — adds the API-specific pattern to existing rules)

Add to `~/.grok/AGENTS.md` or `P:/AGENTS.md` a section under the existing "plausible-narratives-substitute-for-verification" wiki concept:

```markdown
### API guessing: naming is a hint, not a contract

When writing code or tests that call a function you discovered via grep/search:

1. Function names and parameter names are HINTS about the API contract
2. The actual contract is the function body (parameter names, return values,
   dict-key expectations) — one `read_file` call away
3. Pattern-matching from names to a plausible API is valid as a FIRST PASS,
   but must be verified before shipping
4. Specifically: before writing tests against a function, read its actual
   signature + first 10 lines of body. Do not infer parameter names,
   return values, or dict keys from the function name alone.

The test runner catches wrong guesses (tests fail), but reading first
saves the write-fix-rerun cycle (~60s per wrong guess). The cost of
reading is ~5s; the cost of a failed test cycle is ~60s including
diagnosis. Read first.

Reference incident (2026-07-22): 8 of 24 scanner tests failed because
the agent inferred `handoffs_other` (actual: `handoffs_open`), `"found"`
(actual: `"detected"`), `c["files"]` (actual: `c["message"]`), and
return values `"open"/"partially_done"` (actual: `"done"/"partial"/
"blocked"/"not_started"`) — all from function names, all wrong.
```

### The verification step (behavioral — already partially working)

The pattern that DID work: write tests → run them immediately → fix failures → re-run. The test runner is the verification gate. The fix is to ensure this pattern is always followed, not to prevent guessing.

**The one improvement:** before reporting "tests written," always run them. If any fail, read the actual code and fix BEFORE reporting. The agent did this correctly in the final iteration. The rule makes it explicit so future sessions don't skip the run.

### Optional: pre-commit hook for test-code pairs

If the coverage gate (from the companion handoff `test-code-drift-multi-agent-20260722`) is installed, it provides a secondary structural fix: if tests are written against a guessed API and the functions aren't actually exercised correctly, coverage will show the functions as uncovered (the tests call wrong parameters → the function body isn't reached → coverage drops). This is a weaker signal than test failures but catches cases where tests pass for the wrong reason.

## Acceptance criteria

1. The API-guessing rule is added to `~/.grok/AGENTS.md` or the relevant always-loaded file
2. The rule cites the 2026-07-22 incident with specific wrong guesses
3. The rule is framed as "read first, then guess" not "never guess" (guessing is valid; unverified guessing is not)
4. The rule connects to the existing `plausible-narratives-substitute-for-verification` wiki concept (not a new concept — an instance of the existing one)

## Multi-terminal notes

This is a behavioral rule (advisory), not a structural mechanism. It applies to any session/agent that writes code or tests. No multi-terminal isolation needed — it's a rule about agent behavior, not about file coordination.

## Resumption protocol

1. Read this handoff (the incident + the rule text)
2. Read the wiki concept: `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md`
3. Decide placement: extend the existing wiki concept, or add a rule to `~/.grok/AGENTS.md`
4. Add the rule with the 2026-07-22 incident citation
5. Verify the rule is discoverable (grep for "API guessing" or "naming is a hint" in AGENTS.md)

## Related artifacts

- Wiki concept: `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` (the general pattern)
- Companion handoff: `test-code-drift-multi-agent-20260722` (the structural fix — coverage gate)
- Test file that caught the failures: `C:/Users/brsth/.grok/skills/close/tests/test_scanner.py`
- Scanner that was guessed wrong: `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py`
- Other instances this session: edit persistence (tool-said-success), DGemma tool-use boundary, DGemma location (3 wrong proposals)

## Open questions

- Should the rule be general ("read the contract before writing against it") or specific to test-writing? (Propose: general — the pattern applies to any code that calls a discovered function, not just tests.)
- Should the rule recommend reading the FULL function body or just the signature? (Propose: signature + first 10 lines — enough to see parameter names, return statement shape, and dict-key usage without reading the entire function.)
- Is there a way to make `grep` output include signatures, not just function names? (Propose: `grep "^def " -A5` — gives the signature + first few lines of body. Cheaper than full `read_file`.)

## Falsifier

This rule is wrong if:
- Agents consistently read signatures before writing and STILL guess wrong (the rule adds no value) → the problem is deeper than "didn't read"; investigate pattern-matching bias
- The rule causes agents to over-read code (reading entire files for trivial test cases) → narrow to "read signature + first 10 lines"
- The rule is redundant with the test-runner-as-verification-gate pattern (tests already catch wrong guesses) → the rule is a speed optimization (save 60s), not a correctness fix; document it as such

If any pattern appears within 3 months, iterate.
