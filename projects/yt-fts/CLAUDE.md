# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/code) when working with this repository.

## Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | User guide, installation, features |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flows, decisions |
| [PRD.md](PRD.md) | Product requirements, roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [P:/.claude/skills/tdd/SKILL.md](P:/.claude/skills/tdd/SKILL.md) | TDD workflow |
| [docs/REFACTORING.md](docs/REFACTORING.md) | Refactoring best practices |
| [docs/TEST_PATTERNS.md](docs/TEST_PATTERNS.md) | Test patterns and conventions |

## Scoping Rules (Critical)

**Session Context is Terminal Context:**
- This terminal's conversation history = the work context for this session
- "Review recent work" = what was discussed/changed IN THIS TERMINAL, not git history
- Do NOT conflate with other projects (CSF NIP, ralph-wiggum, etc.) even if they share a parent directory
- If scope is ambiguous, ASK: "Do you mean git commits, this session's changes, or something else?"

**Project Boundary:**
- IN scope: `projects/yt-fts/` files, commits, issues
- OUT of scope: `__csf.nip/`, `ralph-wiggum-python/`, `.claude/` (those are separate projects)
- When user says "yt-fts", they mean THIS project only

**Before Expanding Scope:**
1. Confirm the user wants broader scope
2. Explain why you're expanding (e.g., "Found related file in __csf.nip, include it?")
3. Get explicit approval

## Key Architecture Points for Claude

- **3-tier download**: RSS → yt-api → yt-dlp (quota optimization)
- **Dual-sink logging**: JSON file logs + clean console output
- **Database**: SQLite with FTS5, schema in ARCHITECTURE.md
- **Continue-on-error**: Batch processing doesn't stop on single failures

## When Making Changes

1. **Read ARCHITECTURE.md first** - understand the data flow
2. **Check PRD.md** - is there a requirement for this?
3. **Use TDD** - Write tests BEFORE changing code
   - For NEW features: Write test for desired behavior, then implement
   - For REFACTORING: Write test capturing current behavior, then restructure
4. **Update CHANGELOG.md** - document the change
5. **Run tests**: `pytest`

### Critical: TDD is Mandatory

Before changing any code (new or existing):
1. **WRITE TESTS FIRST** - Define expected behavior
2. Change code (implement or refactor)
3. **VERIFY** - Run tests to ensure they pass

**See:** `P:/.claude/skills/tdd/SKILL.md` for the complete TDD workflow.
- `docs/REFACTORING.md` for refactoring patterns and examples
- `docs/TEST_PATTERNS.md` for test conventions

### Refactoring Guidelines

Before refactoring any function:

1. Check cyclomatic complexity to identify candidates
2. Write characterization tests to capture current behavior
3. Extract in small steps - make one change, verify tests pass, repeat
4. Verify code flow using grep to trace execution

See docs/REFACTORING.md for complete refactoring workflow.

### Refactoring Workflow (/refactor skill)

When using the `/refactor` skill for multi-file refactoring:

**Expected behavior with "continue":**
- When you invoke `/refactor continue`, the skill will execute ALL priority levels (P0→P1→P2→P3) without stopping
- P0: Bugs & Race Conditions (fixed first)
- P1: Error Handling (bare except, swallowed errors)
- P2: DRY Violations (duplicate code)
- P3: Conventions (type hints, formatting)

**Stopping conditions:**
- The skill ONLY stops when: user explicitly says "stop", question requires user input, or all findings processed
- The skill does NOT stop after completing one priority level
- After P0 completes, it automatically continues to P1, then P2, then P3

**Example:**
```
/refactor src/yt_fts/download/
# Analyzes and presents findings
/refactor continue
# Executes RED→REFACTOR→REGRESSION for P0
# Automatically continues to P1 (no stop)
# Automatically continues to P2 (no stop)
# Automatically continues to P3 (no stop)
# Stops when all findings processed
```

**Dry-run mode:**
- `/refactor --dry-run` stops after presenting findings (does not make changes)
- This is the only mode that stops before execution



### Task Completion Verification (MANDATORY)

**CRITICAL**: Before closing any task (bd, GitHub issue, etc.), you MUST independently verify completion.

**Prohibited Pattern**: Closing tasks based solely on agent/subagent reports without verification.

**Required Workflow**:

1. **Read the actual changes** - Verify file content with Read tool
2. **Run tests yourself** - Execute pytest/test commands independently
3. **Cite evidence** - Reference file:line or actual test output
4. **THEN close** - Only after independent verification

**Verification Checklist**:

- [ ] Did I read the actual file/code that was changed?
- [ ] Did I run the tests myself (not just trust agent report)?
- [ ] Can I cite specific evidence (file:line, test output)?

**If ANY answer is NO → Do NOT close the task**

## File Locations

- CLI: `src/yt_fts/core/cli.py`
- Downloads: `src/yt_fts/download/`
- Database: `src/yt_fts/core/database.py`
- Search: `src/yt_fts/core/search.py`
- Tests: `tests/`
- Logs: `logs/` (dev) or `~/.config/yt-fts/logs/` (prod)
