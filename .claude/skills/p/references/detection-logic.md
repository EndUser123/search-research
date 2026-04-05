# Detection and Scope Inference Reference

## Step 0: Scope Inference (Chat-Context First)

**Critical:** When invoked without arguments, `/p` infers scope from conversation context before touching the filesystem. This prevents expensive full-codebase scans.

**Inference order (multi-terminal safe, no git, no TTL):**

1. **Explicit argument** (highest priority):
   ```
   /p .claude/hooks/                   -> Use literal path directly
   /p cleanup                         -> Target the cleanup skill directory (includes ALL its files)
   /p /cleanup                        -> Same as above (skill name with or without /)
   /p P:\.claude\skills\cleanup        -> Explicit path to skill directory
   /p package skill, and files        -> Resolve "package" skill to its directory
   /p the auth module                  -> Natural-language: resolve auth-related files
   ```

   **Skill targeting rule (CRITICAL):**
   - When argument is a skill name (e.g., "cleanup", "p", "testing-skills"):
     - **First check:** `P:\packages\<skill_name>\pyproject.toml` (actual package code)
     - **Then check:** `P:\.claude\skills\<skill_name>\SKILL.md` (skill interface)
     - **Target priority:**
       - If `P:\packages\<skill_name>\pyproject.toml` exists -> Target package (primary) with full pipeline (P1-P6)
       - Else if `P:\.claude\skills\<skill_name>\SKILL.md` exists -> Target skill directory only (P0-Skill validation)
   - When argument is a literal path: use it directly
   - When argument is natural language: resolve to actual paths using Glob/Grep/ls

   **NEVER fabricate file lists or test results.**

2. **Chat context** (last 10 turns):
   ```
   Read: P:\.claude\hooks\investigation-ledger\ledger.py
   Edit: P:\.claude\skills\p\SKILL.md
   -> Scope: .claude/hooks/investigation-ledger/, .claude/skills/p/
   ```

3. **Session ledger** (fallback):
   ```
   Query: get_files_read() from investigation-ledger
   -> Returns: ["src/auth.py", "src/handler.py"]
   -> Scope: src/
   ```

4. **Ask user** (no context found):
   ```
   "No clear scope from conversation or session.
    What should /p analyze?

    Options:
    - /p <path>        # Specific directory
    - /p all           # Full codebase (rare, slow)
    - /p .             # Current directory only"
   ```

**Why chat-first?**
- LLM just worked on X files -- they're the obvious test target
- Avoids expensive full-codebase scans (was causing 7500+ test collection)
- Works in multi-terminal (each session has own chat history)
- No git dependency (user: "git is not reliable in multi-terminal")
- No TTL/stale data issues (current session only)

## Step 1: Detect Current State (PARALLEL)

**OPTIMIZATION (Fast Path for Rich Chat Context) - WITH STALENESS DETECTION:**

See `references/session-state-tracking.md` for fast-path state management and staleness detection.

**Otherwise (standard path):**

**MANDATORY:** You MUST use the Task tool and Bash tool to gather real data. NEVER synthesize, estimate, or fabricate detection results.

Run detection commands concurrently for faster startup. Launch 2 parallel Agent subagents:
- `subagent_type="general-purpose"` (required)
- `model="haiku"` (for speed optimization)

**Important:** Never use `subagent_type="haiku"` - "haiku" is a model parameter, not an agent type.

**First, check for flags:**
- `--quick`: Only analyze files from chat context
- `--publish`: Halt on warnings in P3
- `--evidence <path>`: Write structured JSON results to path

**Launch these 2 subagents simultaneously:**

**Subagent 1 -- Test Detection:**
```
Run these commands and report all output:
  pytest --collect-only -q 2>&1 | head -5
  python -c "import subprocess; result = subprocess.run(['pytest', '--version'], capture_output=True, text=True); print(f'pytest available: {result.returncode == 0}')"
Report: test count from collect-only, and whether pytest is available

NOTE: Do NOT run the full test suite in detection - this causes 48GB+ memory usage.
Detection only checks if tests exist and pytest works. Actual test execution happens in P1.
```

**Subagent 2 -- File & Marker Detection:**
```
Run these commands and report all output:
  ls README.md LICENSE 2>&1
  ls .github/workflows/*.yml 2>&1
  ls pyproject.toml setup.py 2>&1
  ls SKILL.md skills/*/SKILL.md 2>&1
Report: which files exist (especially SKILL.md for skill detection)
```

**Wait for both subagents to complete, then merge their results.**

## Step 2: Determine Next Action (3-Tier Priority System)

**Priority 1: Check for truly empty projects**
- No pyproject.toml AND no SKILL.md AND no src/ AND no tests/ -> Run P0 (Scaffold)

**Priority 2: Check test status (applies to ALL targets)**

| Signal | Phase |
|--------|-------|
| No tests or tests failing | P1 (Build) |
| Tests pass, never reviewed | P2 (Review) |
| Tests pass, files changed since review | P2 (Re-review) |
| Reviewed, never validated | P3 (Validate) |
| Validated, no README | P4 (Publish) |
| Published, not certified | P5 (Certify) |
| Certified, never security scan | P6 (Security) |
| All complete, no changes | Report "Ready" |

**Priority 3: Check project type (only if test status is unclear)**

| Signal | Pipeline |
|--------|----------|
| SKILL.md exists, no pyproject.toml, scaffold incomplete | P0-Skill |
| pyproject.toml AND skill/SKILL.md | Dual-nature: Package + skill metadata check |
| pyproject.toml exists | Package pipeline (P1-P6) |
| package.json exists | Node package pipeline (P1-P6) |
| go.mod exists | Go module pipeline (P1-P6) |
| None of the above | P0 (Scaffold) |

**Review markers:**
- `.claude/findings/adversarial-review-{terminal_id}.json` exists = reviewed
- `.claude/state/review-complete.marker` exists = reviewed

**Validation markers:**
- `.claude/state/validation-complete.marker` exists = validated
- `.claude/reports/validation-report.md` exists = validated

**If review markers exist, check for changes since review:**
1. Compare file mtimes vs marker mtime
2. If any scope files have mtime > marker mtime -> files changed since review -> run P2 again
