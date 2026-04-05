---
name: gto_v2
description: GTO v2 - Chat-only gap analysis (deprecated, use /gto for v4)
category: analysis
enforcement: strict
triggers:
  - /gto_v2
  - "chat analysis v2"
  - "conversation review v2"
suggest:
  - /r
  - /q
  - /reflect
workflow_steps:
  - analyze_session_context
  - detect_gaps_and_issues
  - generate_checklist
  - recommend_next_steps
hooks:
  PostToolUse:
    - file: hooks/validate_format.py
      description: "Validate /gto_v2 output format compliance and track checklist items"
  Stop:
    - file: hooks/checklist_gate.py
      description: "Remind about pending /gto_v2 checklist items before session ends"
  SessionEnd:
    - file: hooks/session_summary.py
      description: "Show session summary and cleanup state files"
---

# /gto_v2 - Chat Session Gap Analysis (GTO v2)

## Purpose

Analyze the current chat session to identify **G**aps, **T**asks, and **O**pportunities from chat context.

**GTO = Gaps, Tasks, Opportunities**

**Key distinction**: This skill does NOT scan files or code. It analyzes the chat transcript only.

**Perfect for**: Picking up work after a break, overnight, or when you've lost context. Tracks plans, cleanup, partial work, and follow-ups.

## ⚡ EXECUTION DIRECTIVE

**When invoked, execute:**

```bash
python "{{skill_dir}}/gto_orchestrator.py" --terminal-id {{terminal_id}} --format {{format}}
```

**Parameters:**
- `terminal_id`: Terminal identifier for artifact naming (default: "console")
- `format`: Output format - "compact" (default) or "verbose"

**Compact mode (default):**
- Shows health score, gap count, git status
- Lists artifact paths for selective reading
- Protects orchestrator context by delegating heavy analysis to subagents

**Verbose mode (--verbose or --format verbose):**
- Includes compact snapshot plus detailed gap analysis
- Shows first 50 lines of gap findings
- Full details available in artifacts

**MANDATORY:**
1. Run the orchestrator script - do NOT perform inline analysis
2. Return the script output to the user
3. For detailed findings, guide user to read artifact files

**DO NOT:**
- Perform inline gap detection (use subagents instead)
- Include full artifact content in output (show paths only)
- Skip subagent delegation (context protection is mandatory)

## Usage Examples and Decision Tree

### Decision Tree: Which Output Format Should I Use?

```
Start: What's your goal with /gto?
│
├─ Quick status check? → Compact mode (default)
│  └─ Just run: /gto
│
├─ Need full audit trail? → Verbose mode
│  ├─ Learning opportunities detected? → Verbose mode
│  ├─ Multiple issues to investigate? → Verbose mode
│  └─ Run: /gto --verbose or /gto -v
│
└─ Not sure? → Start with compact mode
   └─ Can add --verbose later if needed
```

### When to Use Each Mode

**Compact Mode (default)** - Use for:
- Quick status checks before/after breaks
- Resuming work after overnight/weekend
- Getting oriented after context switch
- Checking what's blocking progress
- Final verification before session end
- Situations with < 5 issues identified

**Verbose Mode** - Use for:
- Learning opportunities (user corrections detected)
- Complex multi-issue sessions (> 5 gaps)
- Full audit trail needed
- Pattern repetitions to document
- Anti-patterns detected (workaround over root cause)
- Post-mortem analysis of failed sessions
- Comprehensive review before major commits

### Usage Examples

**Example 1: Quick Status Check (Compact Mode)**
```bash
/gto
```
**Expected Output:**
```
=== GTO SNAPSHOT ===
- Sessions analyzed: 1
- Status: 🟡 Health 72/100, 8 gaps found
- Git: dirty (uncommitted changes)

**Session Resume**
- Last active work: Implementing TASK-023 (security component)
- Resume command: /code --continue OR pick up at TASK-024
- Context budget: 45% used - safe

**Status Details**
- 🔴 Critical: ImportError in test_auth.py line 15
- 🟡 High: User corrected authentication flow 3 times
- 🟡 High: 3 uncommitted file(s) detected
- 🟢 Medium: 2 warnings about deprecated API usage
- 🔵 Low: Typo in README.md

**Detailed Analysis Artifacts:**
- Gaps: .evidence/gap_finder_console.md
- Git: .evidence/git_context_console.md
- Health: .evidence/health_console.md

**Recommended Next Steps**

1 (Git) - Commit uncommitted changes
- 1a: Review changes with git status → Manual check - Run `git status --porcelain` to see all changes
- 1b: Create commit with descriptive message → Use `/git` OR `github-ready:commit` - Include TASK-023 context in commit message
- 1c: Verify commit succeeded → Manual check - Run `git status` post-commit to confirm clean state

2 (Testing) - Fix test failures
- 2a: Fix ImportError → Manual check - Install missing dependency (pip install pyjwt)

0 - Do ALL Recommended Next Steps
```

**Example 2: Full Audit (Verbose Mode)**
```bash
/gto --verbose
```
**Expected Output:**
```
=== GTO SNAPSHOT ===
[Compact snapshot as above]

**TL;DR Session Context**
Session focused on security component implementation. User corrected authentication approach 3 times, indicating learning gap. 8 gaps detected (2 critical, 3 high, 2 medium, 1 low).

**Detailed Severity Breakdown**

### Critical Gaps (2)
### Turn 15: ImportError
- test_auth.py line 15: No module named 'jwt'
- Impact: Tests cannot run
- Action: Install pyjwt dependency

### Turn 23: Hook Import Failure
- .claude/hooks/PreToolUse.py: IMPORT_FAIL
- Impact: Hook blocks tool execution
- Action: Fix function() call - pass code object

[... continues with all gaps in detail ...]

**Production Readiness**
- Tests: ❌ 2/5 passing (40%)
- Docs: ⚠️ SKILL.md outdated
- Breaking Changes: None detected
- Performance: No concerns
- Security: ⚠️ Missing JWT validation

**Recommended Next Steps**
1 (Testing) - Fix test failures
- 1a: Install pyjwt → Manual check - pip install pyjwt
- 1b: Fix hook import → Use /trace - Debug PreToolUse.py line 45

2 (Documentation) - Update SKILL.md
- 2a: Document authentication flow → Manual check - Add learning pattern

0 - Do ALL Recommended Next Steps
```

**Example 3: Picking Up Work After Break**
```bash
/gto
```
**Use Case:** You've been away from the keyboard for a few hours and need to quickly get oriented.

**Expected Output:**
```
=== GTO SNAPSHOT ===
- Status: 🟢 Health 85/100, 2 gaps found
- Git: clean

**Session Resume**
- Last active work: Completed TASK-022 (database migration)
- Resume command: /code --continue OR pick up at TASK-023
- Context budget: 62% used - safe

**Status Details**
- 🟡 High: Missing migration rollback test
- 🔵 Low: TODO comment in migration.sql

**Did You Forget Anything?**
- 🟋 Tests for rollback procedure
- 🟋 Update CHANGELOG.md

**Recommended Next Steps**
1 (Testing) - Add rollback test
- 1a: Write rollback test → Use /tdd - Test migration rollback

2 (Documentation) - Update docs
- 2a: Update CHANGELOG → Manual check - Add migration entry

0 - Do ALL Recommended Next Steps
```

**Example 4: Investigating Recurring Issues (Verbose Mode)**
```bash
/gto -v
```
**Use Case:** User has corrected the same issue 3+ times - you need full context to understand the pattern.

**Expected Output:**
```
=== GTO SNAPSHOT ===
- Status: 🔴 Health 55/100, 12 gaps found
- Git: dirty (uncommitted changes)

**Learning Opportunities Detected**

### Pattern: User Corrections on Authentication Flow
**Turn 15, 23, 41**: User corrected approach to JWT validation
- **Pattern**: "That's backwards" / "Wrong again" / "Still wrong"
- **Root Cause**: Misunderstanding of JWT validation order
- **Impact**: 3 implementation attempts wasted
- **Action**: Document pattern in SKILL.md

**Session Flow Analysis**
- Dropped topics: None detected
- Context switches: 3 (medium frequency)
- Anti-patterns: ⚠️ Workaround over root cause detected (turn 23-28)

**Recommended Next Steps**
1 (Learning) - Capture pattern
- 1a: Document JWT validation order → Use /reflect - Capture learning
- 1b: Update SKILL.md → Manual check - Add authentication pattern

2 (Implementation) - Fix root cause
- 2a: Read JWT docs → Use /context7 - Get fresh documentation
- 2b: Fix validation order → Use /code - Implement correct flow

0 - Do ALL Recommended Next Steps
```

### Scope Decision: Terminal vs Session

**Terminal Scope (default)** - Analyzes current terminal only
- Use when: Working on a single feature/task
- Example: `/gto` (default)

**Session Scope** - Analyzes entire session (all terminals)
- Use when: Need complete picture across multiple terminals
- Example: `/gto --session` or `/gto --quick`

**Note:** Session scope is typically only needed when:
- Using multiple terminals for different parts of a project
- Context switching between different workstreams
- Full session review before major milestones

## Scope Comparison

| Situation | Use This Skill | Why |
|-----------|----------------|-----|
| Analyze chat conversation for errors/feedback | `/gto` | Chat session analysis only |
| Technical root cause analysis of specific issue | `/debugRCA` | Deep technical investigation |
| Comprehensive code review with 3-11+ agents | `/uci` | Multi-angle code analysis with mode-based operation |
| Quick quality check (did we do the right thing?) | `/q` | Strategic quality assessment |
| Code omissions and deterministic improvements | `/r` | Code-focused analysis |
| Test coverage and execution | `/t` | Testing analysis |
| Strategic recommendations and next steps | `/nse` | Next step recommendations |

## Skill Mapping Reference

When suggesting next steps, recommend specific skills based on the domain:

| Domain | Recommended Skill | When to Use |
|--------|------------------|-------------|
| Git operations | `/git`, `github-ready:commit` | Committing, pushing, PRs |
| Testing | `/tdd`, `/t` | Test-driven development, coverage analysis |
| Quality check | `/q` | Strategic "did we do the right thing?" |
| Code review | `/adversarial-review`, `code-review:code-review` | Comprehensive PR review (8 perspectives) |
| Documentation | `/claude-md-management:revise-claude-md` | Auto-update CLAUDE.md with learnings |
| Memory capture | `/learn`, `/reflect` | Capture patterns or full session reflection |
| Root cause analysis | `/debugRCA` | Deep technical investigation |
| Next steps planning | `/nse` | Strategic recommendations |
| Architecture decisions | `/arch` | Architecture design and patterns |
| Plan execution | `/code` | Continue implementation plan |
| Deploy readiness | `/ship` | Pre-deployment checklist |
| Test verification | `/tdd --verify` | Verify tests cover requirements |
| **Verification** | `/verify` | 4-tier verification after code changes (checklist → component → integration → e2e) |
| **Risk analysis** | `/pre-mortem` | Pre-implementation failure analysis for significant changes |
| **Discovery** | `/search`, `/library-first` | Find existing implementations before building new code |
| **Session audit** | `/timeline` | View timeline of tool usage to understand what happened in session |
| **Context management** | `/context-status` | Check context usage statistics when approaching limits |
| **Knowledge hygiene** | `/garden` | Clean up CKS and SKILL.md after learning sessions |
| **Manual verification** | `/trace` | Deep manual trace-through verification for complex changes |
| **Handoff prep** | `/handoff` | Create handover documentation before ending session |

## Skill Discovery System (Automatic)

**⚡ NEW**: `/gto` now includes automatic skill discovery via `skill_cache.py` with delta detection and caching. This eliminates the need to manually update skill recommendations when new skills are added to the system.

### How It Works

1. **Automatic Discovery**: When `/gto` runs, it automatically:
   - Scans all skill directories in `.claude/skills/`
   - Parses YAML frontmatter from SKILL.md files
   - Extracts `name`, `description`, `suggest`, `triggers`, and `category` fields
   - Builds recommendations based on actual skill metadata

2. **Delta Detection + Caching**: System uses smart caching to avoid rescanning:
   - **Cache file**: `.claude/skills/gto/.skill_cache.json`
   - **Cache hit** (99% of calls): <0.01s - returns cached metadata
   - **Cache miss** (new/modified skills): 0.1-0.5s - rescans and rebuilds
   - **Invalidation**: Automatic when SKILL.md files change (mtime comparison)

3. **Graceful Degradation**: If YAML parsing fails:
   - Falls back to defaults (name from directory, generic description)
   - Never crashes on malformed frontmatter
   - Logs warnings for debugging

### Integration with Manual Mappings

The automatic discovery system **complements** the manual mapping table above:

- **Manual mappings**: Common domains with high-confidence recommendations (Git, Testing, Quality, etc.)
- **Automatic discovery**: All 199+ skills in the system, including newly added ones
- **Best of both**: Manual guidance for common domains + automatic coverage for everything else

### Cache Management

**View cache stats**:
```bash
python .claude/skills/gto/skill_cache.py
# Shows: cache_exists, cache_age_seconds, skill_count
```

**Force cache rebuild** (if needed):
```python
from skill_cache import invalidate_cache
invalidate_cache()  # Deletes cache file, forces rebuild on next run
```

**Performance**: Cache overhead is <0.1s (well below target), so automatic discovery adds no perceptible latency to `/gto` execution.

### Example: Automatic Discovery

When analyzing a session with "performance issues", `/gto` will:

1. **Check manual mappings** → Suggests `/adversarial-performance` (from Performance domain)
2. **Check automatic discovery** → Finds related skills:
   - `/perf` (Performance tracing wrapper)
   - `/optimize-claude-md` (Evidence-based CLAUDE.md optimizer)
   - `/context-status` (Context usage statistics)
3. **Combine recommendations** → Provides comprehensive coverage

## Analysis Scope

**Quick Overview**: Analyze entire chat history for the terminal (from session start to now) for:
1. Error & Warning Detection
2. User Feedback Patterns
3. Learning Signals
4. Session Flow Issues
5. Task Tracker References
6. **Plan Status** - Active plans and outstanding steps
7. **Cleanup Needs** - Temporary files, debug code, git state
8. **Broken Windows** - Partial work that needs completion or rollback
9. **Follow-Ups** - Research/investigation items noted but not pursued
10. **Context State** - Hooks disabled, config changes, dependencies added
11. **Decisions** - Approaches taken, alternatives considered, rationale
12. **Common Omissions** - Documentation, tests, git commits, configs, dependencies, breaking changes, performance/security implications, **package skill junction updates**

**For detailed patterns**, see:
- `references/error-patterns.md` - Complete error detection reference with examples
- `references/conversation-patterns.md` - User feedback and flow analysis guide

## Subagent Architecture

**Context Protection**: /gto uses subagent architecture to protect orchestrator context from verbose analysis output.

### How It Works

Instead of performing heavy analysis directly in the orchestrator context, /gto dispatches work to focused subagents:

1. **GapFinder Subagent** - Reads transcript, detects errors/gaps, writes artifact
2. **HealthCalculator Subagent** - Calculates health score from gaps, writes artifact
3. **GitContext Subagent** - Extracts git repository state, writes artifact

Each subagent:
- Performs heavy analysis work
- Writes detailed output to `.evidence/` directory
- Returns lightweight JSON envelope with status, artifact path, summary, and metrics

### Result Envelope Specification

```python
{
    "status": "done" | "blocked" | "retry",
    "artifact": ".evidence/gap_finder_{terminal_id}.md",
    "summary": "Found 8 gaps: 2 critical, 3 high, 2 medium, 1 low",
    "metrics": {
        "gaps_found": 8,
        "critical": 2,
        "high": 3,
        "medium": 2,
        "low": 1
    }
}
```

### Benefits

- **50-70% context reduction** - Orchestrator only receives envelopes, not verbose output
- **Parallel execution** - GapFinder and GitContext run concurrently
- **Selective artifact reading** - Orchestrator reads artifacts only when needed
- **All findings preserved** - Detailed analysis available in `.evidence/` files

### Module Structure

```
lib/
├── __init__.py
├── subagents.py          # GapFinder, HealthCalculator, GitContext
└── result_envelope.py    # Result envelope specification
```

### Usage Example

```python
from lib.subagents import GapFinderSubagent, HealthCalculatorSubagent, GitContextSubagent

# Launch subagents
gap_finder = GapFinderSubagent()
gap_result = gap_finder.run(transcript_path, "terminal", terminal_id, working_dir)

git_agent = GitContextSubagent()
git_result = git_agent.run(working_dir, terminal_id)

# Calculate health (depends on gaps)
health_agent = HealthCalculatorSubagent()
health_result = health_agent.run(gaps, git_result, terminal_id)

# Consume envelopes (no verbose output in context)
print(gap_result["summary"])  # "Found 8 gaps: 2 critical, 3 high..."
print(health_result["summary"])  # "Health: 72/100 - Fair..."
```

## Output Format

**⚠️ CRITICAL FORMATTING REQUIREMENT:**
Every section header MUST be in **bold** text. This is not optional.

**Example of REQUIRED format:**
```markdown
**Status Details**

**Implementation**

**Tests:** [summary]

**Notes**

**Recommended Next Steps**
```

**IMPORTANT**: This skill has **two output modes**:

### Mode 1: Compact Snapshot (Default)

**Terminal-friendly, focus on "now"** — Use for quick status checks and picking up work.

```markdown
=== GTO SNAPSHOT ===
- Status: [one-line summary with emoji]
- Tests: [X/X passing]
- Next Action ([date]):
  [exact command or step]
  [decision needed]

**Session Resume**
- Last active work: [task/plan from chat]
- Resume command: [e.g., `/code --continue` OR pick up at TASK-XXX]
- Context budget: [XX% used - safe/CAUTION/near limit]

**Status Details**
- 🔴 Critical: [short desc]
- 🟡 High: [short desc]
- 🟢 Medium: [short desc]
- 🔵 Low: [short desc]

**Implementation**
- [file.py]: [key change]
- [file.py]: [key change]

**Tests:** [summary]

**Notes**
- [Key decision/approach]
- [Text continued]

**Did You Forget Anything?**
- 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)
- 🟋 Tests for new/modified code
- 🟋 Git commit for completed work
- 🟋 Configuration changes documented
- 🟋 Dependencies verified before use
- 🟋 Breaking changes noted
- 🟋 Performance/security implications considered
- 🟦 **Code quality skills not recently used** - Checks if code quality skills have been run on this project:

  **Quality skills tracked**: verify, uci, simplify, q, r, refactor, adversarial-review, adversarial-performance, adversarial-security, adversarial-testing, adversarial-quality, tdd, trace

  **How to check**: Run the quality log reader to get current status:
  ```bash
  python P:/.claude/skills/gto/quality_log_reader.py
  ```

  Or use programmatically:
  ```python
  from quality_log_reader import format_quality_status
  print(format_quality_status(days=7))
  ```

  **Recommendation**: Run quality skills if not used within 7 days:
  - `/verify` - 4-tier verification (checklist → component → integration → e2e)
  - `/uci` - Unified Code Inspection (multi-dimensional code analysis)
  - `/simplify` - Code simplification for clarity and maintainability
  - `/adversarial-review` - 9-agent stress testing for comprehensive review
  - `/q` - Strategic quality check (did we do the right thing?)

- 🟦 **Package media & documentation check** - If working in a package directory (has SKILL.md, pyproject.toml, package.json, or .claude-plugin/) and files were modified/created:

  **Check if package has media assets that need updating:**
  - `assets/banners/` - Banner image (1200x630) for GitHub social preview
  - `assets/infographics/` - Architecture diagrams showing system structure
  - `assets/videos/` - Explainer videos (PBS format: Problem → Behavior → Solution)

  **Check if package documentation needs updating:**
  - `README.md` - Quick Start, installation, usage examples
  - `CHANGELOG.md` - Add entry for this version
  - `CLAUDE.md` - If package has one (skills/plugins)
  - `SKILL.md` - For skill packages
  - API docs - If package has auto-generated API reference

  **Check if CI/CD badges need updating:**
  - Coverage badges in README.md (pytest, ruff, etc.)
  - CI status badges (.github/workflows/)
  - Version badges

  **How to check:** Run `git status` and `git diff --stat` to see what changed, then review relevant sections above
- 🟦 **Package skill rename CRUD checklist** - If renaming a package skill (e.g., `loop-core` → `loop-code`):

  See **`references/package-rename-crud-checklist.md`** for complete 5-step workflow:
  1. Skill metadata updates (name, aliases, version)
  2. ALL documentation references (bulk search/replace)
  3. Directory rename (git mv to preserve history)
  4. Junction symlink updates (.claude/skills/)
  5. File path references (imports, configs, tests)
- 🟦 **Uncommitted files check** - Before ending a session:

  **Check for uncommitted changes:**
  1. **Uncommitted files detection**: Run `git status --porcelain` — if any output, you have uncommitted changes
     - **Risk**: Uncommitted work may be lost if workspace is cleaned or system crashes
     - **Fix**: Review changes with `git diff` and commit with `/git` or `github-ready:commit`

  **How to check:**
  ```bash
  # Quick check for any uncommitted changes
  git status --porcelain

  # Review staged changes
  git diff --staged

  # Review unstaged changes
  git diff

  # Review untracked files
  git status --short | grep "^??"
  ```

  **Recommended Next Step when files are uncommitted:**
  ```markdown
  1 (Git) - Commit uncommitted changes
  - 1a: Review changes with git status → Manual check - Run `git status --porcelain` to see all changes
  - 1b: Create commit with descriptive message → Use `/git` OR `github-ready:commit` - Include context in commit message
  - 1c: Verify commit succeeded → Manual check - Run `git status` post-commit to confirm clean state
  ```

  **When to skip:** Only skip if workspace was intentionally left dirty for next session

- 🟦 **Git state hygiene check** - Before ending a session with commits:

  **CRITICAL checks that MUST be verified:**
  1. **Detached HEAD detection**: Run `git symbolic-ref -q HEAD` — if it returns non-zero exit code, you're on a detached HEAD
     - **Risk**: Commits on detached HEAD are orphaned and can be garbage collected
     - **Fix**: `git checkout -b <branch-name>` to create branch at current commit

  2. **Orphaned commit detection**: Run `git branch --contains HEAD` — if empty or no branch listed, commit is orphaned
     - **Risk**: Work is not reachable from any branch, may be lost
     - **Fix**: Create branch immediately with `git branch <branch-name>`

  3. **Pre-existing test failures**: If session mentions "X pre-existing failures" or "unchanged from before this session"
     - **Risk**: Broken tests accumulate technical debt and hide new failures
     - **Action**: Document in plan or create ticket; don't leave unacknowledged

  **How to check:**
  ```bash
  # Check for detached HEAD (non-zero exit = detached)
  git symbolic-ref -q HEAD && echo "On branch" || echo "DETACHED HEAD"

  # Check if current commit is on any branch
  git branch --contains HEAD

  # If no branch listed above, commit is orphaned - CREATE BRANCH NOW
  ```

  **When to skip:** Only skip if no commits were made in the session

- 🟦 **Core library README check** - If modifying core library code (files in `src/`, `lib/`, public API directories):

  **Purpose:** Check if public API changes require README updates. Unlike packages (which have SKILL.md/pyproject.toml), core libraries need targeted README checking.

  **Detection criteria:**
  - Modified files are in public API directories (`src/llm/`, `src/knowledge/`, etc.)
  - A README.md exists at project root or package level
  - Changes affect public interfaces (classes, functions with `__all__`, non-`_` prefixed names)

  **What to check:**
  1. Run `git diff --stat` to identify changed files
  2. For each changed file in public API directories:
     - Use AST analysis to detect public API changes (added/removed/modified public classes/functions)
     - Search README.md for references to changed APIs
  3. If README mentions changed APIs → suggest README update
  4. If README doesn't mention APIs → no action needed (internal change)

  **Example workflow:**
  ```bash
  # 1. Check what changed
  git diff --stat

  # 2. If src/llm/providers/config.py changed:
  #    - Check if ProviderConfig class or its public attributes changed
  #    - Search README for "ProviderConfig"
  #    - If found → suggest update; if not → skip

  # 3. Use /search or grep to find README references:
  grep -n "ProviderConfig" README.md
  ```

  **When to skip:**
  - Private/internal code changes (files with `_` prefix, private classes)
  - Test-only changes (test files, fixtures)
  - Documentation-only changes (.md files)
  - No README exists at relevant level

  **How to verify:** Use git diff to identify changed files, then AST analysis to detect public API changes

**Recommended Next Steps**
1. [Domain: Topic]
   1a. [Specific action] - [brief context]
   1b. [Alternative action] - [when relevant]

2. [Domain: Topic]
   2a. [Specific action] - [brief context]
   2b. [Specific action] - [brief context]

3. [Domain: Topic]
   3a. [Specific action] - [brief context]
```

**Rules**:
- **Snapshot first**: 5 lines max, most important info
- **Section headers**: EXACT format with **bold** text:
  ```markdown
  **Status Details**

  **Implementation**

  **Tests:** [summary]

  **Notes**

  **Recommended Next Steps**
  ```
- **Key-value bullets**: Use `file: change` format
- **Icons**: 🟢 done, 🟡 medium, 🔴 critical, 🕒 scheduled
- **Dates**: Use ISO or "Mar 15" format
- **Compress history**: One line per file/action
- **No walls of text**: Cut rationale unless critical
- **End with Notes**: 1-3 lines on approach/decisions
- **Recommended Next Steps**: Organize by domain with alpha-numeric options (1a, 1b, 2a, 2b)

**Recommended Next Steps format** (MANDATORY):

**CRITICAL: Comprehensive action mapping is required**

For each gap identified, map it to ALL its implied actions:
- **Direct fixes**: The obvious solution (commit the file, fix the bug)
- **Verification steps**: Tests, checks, validation to ensure the fix works
- **Documentation updates**: CHANGELOG, README, SKILL.md, CLAUDE.md, plan docs
- **Hygiene actions**: Git status post-commit, tagging, cleanup, verification
- **Plan-level actions**: Queue subsequent tasks, sanity-check helpers, verify integration

**Example: Gap = "Uncommitted SKILL.md changes"**

❌ **WRONG** (incomplete):
```markdown
1 (Git) - Commit changes
- 1a: Commit SKILL.md → Use `/git` - Uncommitted changes
```

✅ **CORRECT** (comprehensive):
```markdown
1 (Git) - Commit TASK-023 documentation changes
- 1a: Create commit with message → Use `/git` - Include TASK-023 in commit message
- 1b: Verify commit succeeded → Manual check - Run `git status` post-commit
- 1c: Optional: Tag commit → Manual check - Annotate with TASK-023 for traceability

2 (Documentation) - Update meta-docs
- 2a: Update CHANGELOG.md → Manual check - Add TASK-023 completion entry
- 2b: Update plan doc → Manual check - Mark TASK-023 as done in plan.md
- 2c: Update TASKS.md → Manual check - Remove TASK-023 from pending list

3 (Testing) - Verify no regressions
- 3a: Run test suite → Use `/t` - Ensure docs changes didn't break tests
- 3b: Verify evidence tracking → Manual check - Confirm TASK-023 evidence exists

4 (Plan Workflow) - Continue autonomous loop
- 4a: Continue to TASK-024 → Use `/code --loop` - Verify security component references
- 4b: Queue TASK-025-028 → Manual check - Prepare upcoming tasks
- 4c: Sanity-check helpers → Manual check - Verify Ralph Loop invocation scripts

0 - Do ALL Recommended Next Steps
```

**Mapping template:**

```markdown
**Recommended Next Steps**

1 (DOMAIN NAME) - Brief domain description
- 1a: [Action name] → Use `/skill-name` OR Skill('skill-name') - [context]
- 1b: [Alternative action] → [Alternative skill/command] - [context]

2 (DOMAIN NAME) - Brief domain description
- 2a: [Action name] → [Skill suggestion] - [context]
- 2b: [Action name] → [No skill applies - manual check] - [context]

3 (DOMAIN NAME) - Brief domain description
- 3a: [Action name] → [Skill suggestion] - [context]

0 - Do ALL Recommended Next Steps
```

**When NO next steps (conditional format):**

```markdown
**Recommended Next Steps**

No next steps required - all tasks complete.

0 - Nothing left to do
```

**MANDATORY FORMAT REQUIREMENTS**:
- Line 1: `1 (DOMAIN) - description` format
- Lines 2+: `- 1a: Action → Use Skill OR manual - context` format (note the dash prefix)
- **Skill recommendations**: Use arrow syntax `→ Use /skill-name` when applicable
- **Manual actions**: Use `→ Manual check` or `→ No skill applies` when no skill exists
- **Conditionally end with**:
  - If next steps exist: `0 - Do ALL Recommended Next Steps`
  - If NO next steps: `0 - Nothing left to do` (prevents accidental execution)
- Domains must be numbered 1, 2, 3...
- Actions must be lettered a, b, c... under each domain
- Dash prefix required for all action lines

**Example**:
```markdown
1 (Testing) - Write tests for new hooks
- 1a: Create test for verification gate → Use `/tdd` - Test claim detection
- 1b: Create test for tool check → Use `/tdd` - Test parameter validation

2 (Git) - Commit and document
- 2a: Create git commit → Use `/git` OR `github-ready:commit` - Include all 5 mechanisms
- 2b: Update CLAUDE.md → Use `/claude-md-management:revise-claude-md` - Auto-update with learnings

3 (Documentation) - Review project docs
- 3a: Check README → Manual check - No skill applies for README review
- 3b: Update CHANGELOG → Manual check - Add entry for this version

0 - Do ALL Recommended Next Steps
```

**Example (when no next steps)**:
```markdown
**Recommended Next Steps**

No next steps required - all tasks complete.

0 - Nothing left to do
```

**Selection behavior**:
- **Domain number** (e.g., "3") → Do ALL actions in that domain (3a, 3b, 3c...)
- **Specific option** (e.g., "3b") → Do just that action
- **Mixed selection** (e.g., "1, 3b, 5") → Do all of domain 1, just action 3b, all of domain 5
- **"0"** → Do ALL Recommended Next Steps (execute everything in all domains)
- **No selection** → Skip all (user opts out by not picking any option)

**Example domains**:
- Implementation: Code changes, feature work
- Testing: Test coverage, verification
- Documentation: README, SKILL.md, CLAUDE.md
- Infrastructure: Hooks, config, dependencies
- Learning: `/reflect`, pattern capture
- Cleanup: Temp files, git state, processes

### Mode 2: Verbose Analysis (--verbose flag)

**Comprehensive deep-dive** — Use for complex sessions with multiple issues, learning opportunities, or when you need full context.

Includes ALL sections from verbose analysis (TL;DR, User Feedback, Session Flow, Task Tracker, Recommendations, Completed Actions, Next Steps, Plan Status, Production Readiness, Risk Assessment, Cleanup, Broken Windows, Follow-Ups, Context State, Decisions & Rationale, Learning Opportunities, Reflect Recommendation) PLUS the compact snapshot sections.

**Ends with**: Recommended Next Steps section (same format as compact mode)
- TL;DR session context
- Detailed severity breakdowns (Critical/High/Medium/Low)
- User feedback summary (positive/negative signals)
- Session flow analysis (dropped topics, context switches, anti-patterns)
- Task tracker summary
- Recommendations with rationale/impact/effort
- Completed actions vs. pending next steps
- Plan status with blockers
- **Production Readiness** - Tests, docs, breaking changes, performance, security
- **Risk Assessment** - Breaking changes, test coverage, performance, security
- **Learning Opportunities** - Suggest `/learn` or `/reflect` for patterns
- Cleanup checklist (files, code, git, processes)
- Broken windows (partial work)
- Follow-up items (research, investigate, technical debt)
- Context state (hooks, config, dependencies)
- Decisions & rationale
- Reflect recommendation (when appropriate)

**When to use verbose mode**:
- User corrections detected (learning opportunities)
- Complex multi-issue sessions
- Need full audit trail
- Pattern repetitions to document
- Anti-patterns detected (workaround over root cause)

**Example trigger**: `/gto --verbose` or `/gto -v`

### Verbose Section Templates

See **`references/verbose-mode-templates.md`** for complete template reference:
- Production Readiness (tests, docs, breaking changes, performance, security)
- Risk Assessment (breaking changes, test coverage, performance, security)
- Learning Opportunities (pattern detection, `/learn` or `/reflect` recommendations)
- Unblocking Actions (debug, requirements, context, root cause, architecture)
- TL;DR, User Feedback, Session Flow, Task Tracker summaries
- Recommendations with rationale/impact/effort
- Cleanup checklist, Broken Windows, Follow-ups, Context State, Decisions

## Optional Git Context

**When git repository is detected**, /gto automatically enhances gap analysis with git state awareness.

See **`references/git-context-integration.md`** for details on:
- Current branch + dirty state detection
- Recent commits analysis (last 10 with metadata)
- Modified files tracking (staged + unstaged + untracked)
- Commit pattern classification (BUGFIX, FEATURE, REFACTOR, etc.)
- Development activity level (HIGH/MEDIUM/LOW)
- Multi-terminal safety (no caching, fresh reads)

**Example Output**:
```markdown
### Git Context
- Branch: main (dirty: 3 modified files)
- Recent commits: 10 (FEATURE focus detected)
- Activity: HIGH
- Modified: src/git_context.py, SKILL.md, tests/test_git.py
- Commit types: 4 FEATURE, 3 REFACTOR, 2 BUGFIX, 1 TEST
```

## Severity Classification

**Critical** (must fix now):
- Broken hooks blocking system
- Security vulnerabilities
- Data loss risks
- Import errors

**High** (should fix soon):
- User-facing bugs
- Incomplete features in use
- Repeated user corrections
- Test failures

**Medium** (should fix eventually):
- Warnings that don't break functionality
- Dropped topics (non-critical)
- Context switches
- Ambiguous requirements

**Low** (nice to have):
- Style improvements
- Minor conversation flow issues
- Cosmetic problems

## Example Finding Entry

```markdown
### 1. Error - Hook Import Failure
- **Severity**: Critical
- **Location**: `P:\.claude\hooks\UserPromptSubmit.py`
- **Description**: IMPORT_FAIL - TypeError: function() argument 'code' must be code, not str
- **Impact**: Hook fails to load at SessionStart, breaking user prompt processing
- **Recommended Action**: Fix the function() call - pass code object instead of string
- **Error Source**: SessionStart hook diagnostic
```

```markdown
### 2. Gap - User Repeated Same Correction 3 Times
- **Severity**: High
- **Location**: Session context (turns 15, 23, 41)
- **Description**: User corrected approach to X three times - indicates learning gap
- **Impact**: User frustration, wasted time
- **Recommended Action**: Document pattern in SKILL.md to prevent recurrence
- **Learning Opportunity**: "Do X instead of Y" pattern should be captured
```

## Common Anti-Patterns to Detect

### Workaround Over Root Cause

**Pattern**: Proposing workarounds, patches, or additional layers instead of fixing the underlying issue.

**Examples:**
- Creating hookify rules to "prevent" an error instead of fixing the hook that causes it
- Adding configuration flags to disable broken behavior instead of fixing the breakage
- Creating wrapper functions to hide errors instead of resolving the root cause
- Adding Try/Catch to suppress exceptions instead of fixing what throws them

**User Feedback Signals:**
- "why don't you figure out what's actually broken?"
- "stop adding patches and fix the root cause"
- "this is a workaround, not a fix"

**Detection:**
- User explicitly redirects from workaround to investigation
- Proposed solution adds complexity without addressing source
- "fix" that doesn't actually resolve the problem

**Root Cause Investigation Process:**
1. **Identify the blocking component** (which hook, which file, which function)
2. **Read the source code** to understand actual behavior
3. **Trace the execution path** to find where failure occurs
4. **Fix at the source** (modify the hook, fix the logic, correct the error)
5. **Verify the fix** works (test the actual scenario)

**Example from Session:**
- **Anti-pattern**: Attempted to create hookify rule to exempt SKILL.md files from blocking
- **User correction**: "stop. why don't you figure out what hook(s) need fixing rather than slapping on another patch?"
- **Correct approach**: Read PreToolUse.py, found skill-first gate at lines 208-338, added targeted exemption
- **Result**: Fixed in 1 place, no workaround needed

**Severity**: High - workarounds accumulate technical debt and make systems harder to maintain

## Important Constraints

- **TL;DR is mandatory**: Always fill out the TL;DR section at the top - this is your main context summary for next session
- **Chat scope is mandatory**: Only analyze work from the CURRENT conversation - do NOT include findings from other terminals/sessions
- **Comprehensive action mapping is MANDATORY**: When you identify a gap, map it to ALL its implied actions, not just the obvious ones. Each gap should expand to multiple action items covering:
  - Direct fixes (the obvious action)
  - Verification steps (tests, checks, validation)
  - Documentation updates (CHANGELOG, README, SKILL.md, CLAUDE.md)
  - Hygiene actions (git status, tagging, cleanup)
  - Plan-level/workflow actions (queue subsequent tasks, sanity-check helpers)
  - **Anti-avoidance rule**: Do NOT skip action items to "avoid overwhelming the user" - the user invoked /gto for comprehensive analysis
- **"Did You Forget Anything?" checklist is MANDATORY**: Check EVERY item on the checklist (lines 192-228), not just the ones that seem obvious. This includes:
  - Documentation updates (CLAUDE.md, README.md, SKILL.md, CHANGELOG.md)
  - Tests for new/modified code
  - Git commits for completed work
  - Configuration changes documented
  - Dependencies verified before use
  - Breaking changes noted
  - Performance/security implications considered
  - Package media & documentation checks (if applicable)
- **GROUNDED CLAIMS ONLY**: Never invent organizational policies, project conventions, or team practices that are not grounded in the current conversation. If unsure whether something is a real convention, omit it rather than qualify it with "typically" or "often." Example of what NOT to do: "Skip if micro-fix policy applies — many hook fixes go undocumented; your call." (invented; no such policy exists)
- **Cite evidence**: Every finding must have a turn number or clear context from the conversation
- **Prioritize**: Not every issue is critical - use judgment on what to report, but don't skip action items for reported gaps
- **Be specific**: "Fix the function" is not helpful; "Add error handling to `process_data()` line 145" is
- **Stay in scope**: Don't analyze code files - that's what /r, /q, /t are for

## Integration Notes

- **For fresh sessions** with no tool use, report "No findings - session just started"
- **Check recent tool outputs** for failures or warnings from THIS session
- **Read the full transcript** from `transcript_path` to analyze complete terminal history

## When to Use

```bash
/gto                    # Compact snapshot (default) - entire terminal history
/gto -v                 # Verbose analysis (all sections)
/gto --verbose          # Same as -v
/gto --session          # Analyze entire session transcript (not just this terminal)
/gto --quick            # Same as --session (shorthand)
```

**When to use verbose mode**:
- User corrections detected (learning opportunities)
- Complex multi-issue sessions
- Need full audit trail
- Pattern repetitions to document
- Anti-patterns detected (workaround over root cause)

---

**When invoked**: The user wants a comprehensive analysis of what needs attention in the current chat session. Provide actionable, prioritized findings with specific references to conversation context.

---

## Self-Verifying Hooks

The /gto skill is supported by three hooks that enforce proper usage:

### PostToolUse Format Validator (`PostToolUse_gto_format_validator.py`)

**Purpose**: Validates /gto output format after execution.

**Enforces**:
- **Status Details** section with bold headers
- **Recommended Next Steps** section with domain/action format
- Terminator: "0 - Do ALL Recommended Next Steps" or "0 - Nothing left to do"
- Domain headers: "1 - Description" or "1 (DOMAIN) - Description"
- Action lines: "- 1a: Action description"

**Side Effects**:
- Saves session state to `P:/.claude/state/gto_session_{terminal_id}.json`
- Extracts checklist items for Stop hook tracking
- Saves checklist state to `P:/.claude/state/gto_checklist_{terminal_id}.json`

**Configuration**:
- Environment: `GTO_FORMAT_VALIDATOR_ENABLED` (default: `true`)

### Stop Checklist Gate (`stop/Stop_gto_checklist_gate.py`)

**Purpose**: Reminds about pending checklist items before session ends.

**Behavior**:
- Loads checklist state from PostToolUse validator
- Shows pending items when Stop event fires
- Allows bypass with `--skip-gto-checklist` flag

**Configuration**:
- Environment: `GTO_CHECKLIST_GATE_ENABLED` (default: `true`)

**Example Output**:
```
📋 PENDING GTO CHECKLIST ITEMS

The following items from /gto have not been addressed:
  • 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)
  • 🟋 Tests for new/modified code

To skip this check: Add --skip-gto-checklist to your message
```

### SessionEnd Reminder (`SessionEnd_gto_reminder.py`)

**Purpose**: Session summary and cleanup at session end.

**Behavior**:
- Shows whether /gto was invoked during session
- Lists pending and addressed checklist items
- Cleans up state files

**Configuration**:
- Environment: `GTO_SESSION_REMINDER_ENABLED` (default: `true`)

**Example Output**:
```
📋 **GTO SESSION SUMMARY**

✅ /gto was invoked this session

⚠️ **Pending checklist items:**
  • 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)

Run /gto to check session status anytime.
```

### Terminal Safety

All hooks use terminal-scoped state files (`_{terminal_id}.json`) for multi-terminal safety. Each terminal/session maintains independent state.

---

## Test Coverage

### Test Case 1: Empty Session
**Input**: Fresh session with no conversation history
**Expected Output**: "No findings - session just started"
**Validation**: Should handle empty conversation gracefully

### Test Case 2: Python Error Detection
**Input**:
```
User: Fix the import error
Assistant: I'll fix it.
Traceback (most recent call last):
  File "test.py", line 5
ImportError: No module named 'requests'
```
**Expected Output**: Critical issue detected with proper categorization
**Validation**: Should identify ImportError, file:line, and severity

### Test Case 3: User Feedback Patterns
**Input**:
```
User: That's wrong.
Assistant: Let me fix it.
User: No, that's backwards.
Assistant: Sorry, let me reverse it.
User: Still wrong.
```
**Expected Output**: High priority issue - repeated user corrections
**Validation**: Should detect frustration pattern and count repetitions

### Test Case 4: Task Tracker Integration
**Input**:
```
Conversation mentions #1234, #5678, #9012
```
**Expected Output**: Task tracker summary with status for each mentioned task
**Validation**: Should extract task IDs and report current status

### Test Case 5: Scope Boundary
**Input**: User asks to analyze code files
**Expected Output**: Politely redirect to `/r`, `/q`, or `/t` as appropriate
**Validation**: Should not scan files, only analyze chat transcript

### Test Case 6: Uncommitted Files Detection
**Input**: Git repository with uncommitted changes
**Expected Output**: High-severity gap added to health score
**Validation**: Should detect uncommitted files and include file names in message

### Test Case 7: File List Truncation
**Input**: Many uncommitted files (>5)
**Expected Output**: Single gap with truncated file list
**Validation**: Should show "5 files (+N more)" format, not N separate gaps

## Development Guidelines

When modifying /gto behavior or adding new features, follow these guidelines to prevent common mistakes:

### 1. Unit Test Coverage (MANDATORY)

**Rule**: Every new feature or behavior change MUST include corresponding unit tests.

**Why**: Tests prevent regressions and verify edge cases work correctly.

**When to add tests**:
- Adding new gap detection logic → Add test in `test_health_integration.py`
- Modifying health scoring → Add test for new scoring behavior
- Adding synthetic gaps (like uncommitted files) → Add test for gap generation

**Test file location**: `.claude/skills/gto/test_health_integration.py`

**Example**: Adding uncommitted files detection required these tests:
- `test_uncommitted_files_gap()` - verifies gap is added and counted
- `test_uncommitted_files_with_many_files()` - verifies truncation logic

### 2. Gap Message Details (MANDATORY)

**Rule**: Gap messages MUST include relevant details to help users understand and fix the issue.

**Why**: Generic messages like "uncommitted changes" don't help users identify what needs action.

**Required details**:
- **File names**: When a gap relates to specific files, include them
- **Counts**: Show how many items are affected
- **Truncation**: For long lists, show first N items + "more" indicator
- **Context**: Include relevant context (branch, directory, etc.)

**Examples**:
- Good: `"3 uncommitted file(s): SKILL.md, health_scoring.py, gto_orchestrator.py"`
- Bad: `"Uncommitted changes detected"`
- Good: `"5 files (+3 more): file1.py, file2.py, file3.py, file4.py, file5.py"`
- Bad: `"8 files have changes"` (doesn't say which ones)

**Implementation pattern** (from `health_scoring.py`):
```python
if modified_files:
    file_list = ", ".join(modified_files[:5])  # Show up to 5 files
    if len(modified_files) > 5:
        file_list += f" (+{len(modified_files) - 5} more)"
    message = f"{len(modified_files)} uncommitted file(s): {file_list}"
```

### 3. Synthetic Gap Counting (MANDATORY)

**Rule**: Synthetic gaps (system-detected issues like uncommitted files) MUST be added BEFORE categorization.

**Why**: If added after categorization, they won't be counted in overall totals, causing inconsistency between category scores and overall totals.

**Correct order**:
1. Add synthetic gaps to gap list
2. Categorize ALL gaps (user + synthetic)
3. Calculate scores from categorized gaps
4. Count totals from ALL gaps

**Implementation location**: In `HealthScoringEngine.calculate_health_score()`, before calling `_categorize_gaps()`.
