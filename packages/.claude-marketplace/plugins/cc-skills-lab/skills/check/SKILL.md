---
name: check
description: "Multi-tier post-task gate: verify, secret scan, git hygiene, test-coverage guard, typecheck, drift check, code-review, re-verify. --standard (daily) / --strict / --deep / --apply."
version: 2.0.0
status: stable
category: quality
enforcement: advisory
triggers:
  - /check
argument-hint: "[--standard] [--strict] [--deep] [--apply]"
workflow_steps:
  - verify
  - secret_scan
  - git_hygiene
  - test_coverage_guard
  - typecheck
  - drift_check
  - code_review
  - docs_freshness
  - re_verify
---

# /check

Multi-tier post-task gate. Each tier enables more phases. Default is lightweight
(verify + types + code-review). --standard is the recommended daily driver for SDLC.

## Mode Hierarchy

```
/check                    # VERIFY + TYPECHECK + CODE-REVIEW (report-only)
/check --standard         # +SECRET SCAN + GIT HYGIENE + TEST-COVERAGE GUARD
/check --strict           # +DRIFT CHECK + DOCS FRESHNESS
/check --deep             # +ARCHITECTURE CONSISTENCY SCAN
/check --apply            # APPEND to any mode: auto-fix + re-verify (requires verify baseline)
```

Modes compose: `/check --standard --apply` = standard checks + auto-fix.

## Phase-to-Mode Matrix

| # | Phase | Default | --standard | --strict | --deep | --apply |
|---|---|---|---|---|---|---|
| 1 | Verify | YES | YES | YES | YES | YES |
| 1.2 | Secret scan (gitleaks) | - | YES | YES | YES | YES |
| 1.3 | Git hygiene | - | YES | YES | YES | YES |
| 1.4 | Test-coverage guard | - | YES | YES | YES | YES |
| 1.5 | Typecheck | YES | YES | YES | YES | YES |
| 1.7 | Config/cache drift | - | - | YES | YES | YES |
| 2 | Code review | YES | YES | YES | YES | var* |
| 2.3 | Doc freshness | - | - | YES | YES | YES |
| 2.5 | Post-fix re-verify | - | - | - | - | YES |
| 2.7 | Architecture consistency | - | - | - | YES | - |

  * code-review is report-only in default/--standard/--strict/--deep; --apply triggers --fix.

## Output format

Every invocation MUST emit, in this order:

1. **Mode banner** -- first line: `=== check [mode] ===` (e.g. `=== check --apply ===` or `=== check STRICT ===`)
2. **Verdict line** -- one-line: `check verdict: <VERDICT>` (CLEAN | FINDINGS | ERROR | BLOCKED)
3. **Per-phase details** -- free text, one paragraph per phase that ran
4. **Phase table** -- rows only for phases that actually ran (skip blocked/skipped rows)
5. **Next steps** -- 1-2 actionable items
6. **Timer + personality** -- after everything actionable

### Verdict mapping

| Outcome | Verdict |
|---|---|
| All phases pass/clean | CLEAN |
| Code-review / hygiene / secret / guard produced findings (non-blocking) | FINDINGS |
| A stopping phase failed | ERROR |
| Verify was blocked (no test harness) and --apply was requested | BLOCKED |

### Next steps guidance

After the phase table, emit 1-2 lines:

- **CLEAN:** nothing to do
- **FINDINGS (report-only):** review findings above; run `/check --standard --apply` to fix automatically
- **APPLY + CLEAN:** changes applied and re-verified. Run `git diff` to review
- **APPLY + FINDINGS (re-verify passed):** auto-fixes applied and verified. Run `/check` to confirm
- **ERROR:** fix the reported issue first, then re-run `/check`
- **BLOCKED:** verify has no harness. Fix findings manually or skip /check for this task

## Phase 1: Verify (always on)

Invoke `/verify` (Skill tool, name `verify`). Let it run to completion.

- If `/verify` exits with failures: STOP. Verdict=ERROR.
- If `/verify` returns blocked (no harness): **BOTH modes stop.** Verdict=BLOCKED.
  --apply is NOT allowed without a verify baseline.
- If `/verify` passes: continue.

## Phase 1.2: Secret Scan (--standard+)

Scan the diff for leaked secrets (API keys, tokens, credentials). Uses the installed
gitleaks binary with a custom config tuned for Anthropic key patterns.

**Command:**

```bash
git diff HEAD --cached -- . | ' + GITLEAKS + r' stdin --config=' + GITLEAKS_CONF + r' --report-path .claude/.check-gitleaks-report.json 2>&1
```

**Quirk workaround:** gitleaks stdout is ANSI-colorized and grep-unfriendly. The
authoritative signal is stderr containing `leaks found: N`. Read the JSON report when
leaks are detected (`leaks found` with N>0).

- If leaks found: **STOP.** Verdict=ERROR. Report each finding with file:line and
  secret type. The user must scrub before proceeding. Do NOT continue to code-review.
- If gitleaks is unavailable or the subprocess fails: WARN but CONTINUE
  (fail-open -- the tool may not be on PATH in the shell).
  Note: gitleaks is at `C:\Users\brsth\AppData\Local\Microsoft\WinGet\Links\gitleaks.exe` and
  the winget shim is NOT on PATH in non-interactive shells.
- If no leaks found: continue.

**Cleanup:** remove `.claude/.check-gitleaks-report.json` after reading it.

## Phase 1.3: Git Hygiene (--standard+)

Scan the diff for common quality signals that indicate incomplete or careless work.
Only scan changed lines (git diff HEAD) -- not the whole codebase.

**Candidates to flag (WARN, not STOP by default):**

| Pattern | What it indicates |
|---|---|
| `<<<<<<<` / `=======` / `>>>>>>>` | Merge conflict markers left in code |
| `console\.(log|warn)\(` | Debug logging left in production code |
| `print\(["'](DEBUG|debug)` | Python debug prints |
| `pdb\.set_trace\(\)` / `ipdb\.set_trace\(\)` | Debugger breakpoint left in |
| `\.only\s*\(` | test.only() / it.only() -- test isolation |
| `\.skip\s*\(` | test.skip() / it.skip() -- might be intentional, flag anyway |
| `FIXME` / `HACK` / `XXX` | Known-incomplete markers in new code |

- If any match: **WARN.** List each finding. Do NOT stop -- these are often intentional
  during development. The user should confirm before committing.
  In --apply mode: also WARN (never auto-fix debug markers).
- If no matches: continue cleanly.

## Phase 1.4: Test-Coverage Guard (--standard+)

Check that production code changes are accompanied by test changes. Uses git diff to
compare the file list.

**Logic:**

```
prod_files = git diff --name-only HEAD -- :!**/test_* :!**/tests/*
test_files = git diff --name-only HEAD -- **/test_* **/tests/*
if prod_files and not test_files: WARN
```

- If prod changed and no test changed: **WARN** with the list of prod files.
  The user should confirm tests aren't needed before proceeding.
  In --apply mode: WARN only (never auto-create tests).
- If no prod change, or test files also changed: continue cleanly.

## Phase 1.5: Typecheck (always on)

Between verify and code-review, run static type checking if a typechecker is available for the
changed files.

**Discovery rule:** enumerate changed files from `git diff --name-only HEAD` (or `git diff` if
HEAD looks synthetic -- fail open either way). For each changed file, find the nearest ancestor
directory containing a typecheck config marker. Deduplicate by config path.

| Config marker | Command to run |
|---|---|
| `mypy.ini` or `.mypy.ini` | `mypy <changed_files_in_project>` (nearest ancestor config) |
| `pyproject.toml` with `[tool.mypy]` | `mypy <changed_files_in_project>` |
| `tsconfig.json` | `tsc --noEmit --pretty` (in that directory) |

If no config is found for any changed file, skip silently -- this is an advisory gate, not a
required one.

If the typechecker reports errors: **STOP.** Verdict=ERROR. Do not proceed to code-review while
there are type errors -- they produce noise (the reviewer comments on type hacks that should be
structural fixes).

**Extensibility:** when a new language emerges (`.clj`, `.go`, `.rs`, ...), add its config
marker and command to the discovery table above. The structure is stable: ancestor config,
dedup, run.

## Phase 1.7: Config/Cache Drift (--strict+)

Check for known-broken states in plugin configuration: source edited but cache not rebuilt.

**Logic:** for any changed file matching a plugin path (`plugin.json`, `.claude-plugin/`),
check whether the version-keyed cache has a matching version. Simple heuristic: version
in `plugin.json` vs version in `~/.claude/plugins/cache/local/<plugin-name>/`.

- If drift detected: **WARN** (non-blocking). The user should run `/reload-plugins`.
  In --strict mode, this is a warning, not a stop -- the user may have run it already
  from another terminal.
- If no drift or no plugin files changed: continue cleanly.

## Phase 2: Code Review (always on)

Invoke `/code-review` (Skill tool, name `code-review`). Reviews the diff for correctness
bugs, reuse, simplification, and efficiency issues.

**Default / --standard / --strict / --deep (report-only):** invoke at base effort. Show findings.
Do NOT apply. Verdict=FINDINGS if any findings reported.

**`--apply` mode:** invoke with `args: "--fix"` to auto-apply. Only allowed when verify
passed (regression baseline exists). If verify was blocked, abort with Verdict=BLOCKED.

If `/code-review` is unavailable or errors, fall back to reviewing `git diff`
(or `git diff HEAD`) manually for correctness, reuse, simplification, and efficiency; do not
abort.

## Phase 2.3: Documentation Freshness (--strict+)

Check whether changed code affects public interfaces without corresponding documentation
updates. Advisory only -- never blocking.

**Logic:**

```
if def_interface_changed:  # new def/class/function added in diff
    and not md_file_changed:  # no .md file in the diff
    SUGGEST: doc update
```

Heuristic: check if the diff adds `def ` (Python), `public function` / `export function`
(TypeScript), or `interface` / `type ` (TypeScript). If yes and no `.md` file changed,
suggest updating documentation.

- On match: SUGGEST (not WARN, not STOP). Add to the phase table as an FYI.
- Otherwise: continue.

## Phase 2.5: Post-fix Re-Verify (--apply only)

Only runs when `--apply` was passed AND code-review made changes AND verify passed in Phase 1.
Re-runs `/verify` once.

Bounded to **one** re-run -- fail and stop if it regresses, do not loop.

When default (report-only) or verify was blocked/skipped, re-verify does not run.

## Phase 2.7: Architecture Consistency Scan (--deep only)

Delegates to `/improve-codebase-architecture` for a lightweight architectural review.
Checks whether the diff introduces the kind of shallow modules / deepening violations the
skill is designed to catch.

**Invocation:** (Skill tool, name `improve-codebase-architecture`). Let it scan the diff
and report findings.

- If findings: REPORT in the phase table as advisory. Do not block.
- Otherwise: continue.

**Opt-in only (--deep)** because this is the most expensive phase -- it consumes LLM tokens
for the delegated call.

## Phase Behavior Summary

| Phase outcome | Default | --standard | --strict | --deep | --apply (on top) |
|---|---|---|---|---|---|
| Verify fails | STOP ERROR | STOP ERROR | STOP ERROR | STOP ERROR | STOP ERROR |
| Verify blocked | STOP BLOCKED | STOP BLOCKED | STOP BLOCKED | STOP BLOCKED | STOP BLOCKED |
| Secret scan leak | SKIP | STOP ERROR | STOP ERROR | STOP ERROR | STOP ERROR |
| Git hygiene match | SKIP | WARN continue | WARN continue | WARN continue | WARN continue |
| Test guard violation | SKIP | WARN continue | WARN continue | WARN continue | WARN continue |
| Typecheck fails | STOP ERROR | STOP ERROR | STOP ERROR | STOP ERROR | STOP ERROR |
| Drift detected | SKIP | SKIP | WARN continue | WARN continue | WARN continue |
| Code-review findings | report-only | report-only | report-only | report-only | auto-fix + re-verify |
| Docs stale | SKIP | SKIP | SUGGEST | SUGGEST | SUGGEST |
| Re-verify fails | SKIP | SKIP | SKIP | SKIP | STOP ERROR |
| Arch findings | SKIP | SKIP | SKIP | SUGGEST | SUGGEST |

## What check does NOT do

- It does not replace a full PR review pipeline
- It does not run mutation tests, QA gates, or adversarial review
- It does not duplicate /go STEP 3-6 (on tasks where /go already ran those)
- It does not scope code-review from git diff -- let each built-in see the full tree
- It does not write persistent state artifacts -- stateless by design for multi-terminal safety
  (except gitleaks JSON report, which is cleaned up after reading)
- It does not auto-create tests, docs, or git commits -- diagnostic and advisory only

## Rejected designs (do not re-litigate)

| Feature | Rejected because |
|---|---|
| **Severity-based gating** (/code-review does not emit parseable severity) | Verified 2026-07-10: the built-in outputs no severity field. Strict=report-only, not severity-gated. |
| **Pre-flight change assessment** (git diff-based scoping of code-review) | Git is unreliable (index-lock re-fires, cross-terminal ambiguity). Let built-ins see the full tree. |
| **Idempotency guard / no-op exit** | Same root cause: auto-commit fires at Stop, not mid-check. |
| **Structured machine-parseable output** | No consumer. Speculative before contract exists. |
| **`/simplify-enhanced` inclusion** | Deliberately removed. /code-review already covers reuse/simplification/efficiency. |
| **Dependency diff scanner** | Too many lockfile formats in monorepo; fragile. |
| **License compliance scan** | Not relevant (all MIT/open-source-internal). |
| **Semantic version bump checker** | Codebase does not use formal SemVer globally. |
| **E2E orchestrator** | That is a CI job, not a post-task gate. |
| **Parallel phase execution** | Phases are sequential by design (stop-on-fail). |

