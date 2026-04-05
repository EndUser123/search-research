# Feature Certification Flow

A strict quality gate to certify features before release.

## ⚡ EXECUTION DIRECTIVE

**Apply phases in order. Stop on failure.**

---

## STEP 0: TRIAGE (Pre-Routing)

**Objective:** Assess certification scope and determine target from THIS SESSION.

### Session Scope (REQUIRED)

> **ONLY analyze changes from THIS terminal session conversation.**

**PROHIBITED:**
- `git status` - accumulates stale changes from multiple sessions
- Analyzing files not discussed in this conversation
- Reporting on unrelated projects

**USE INSTEAD:**
- Conversation history - what was discussed/implemented
- Read/Edit tool calls from THIS session
- Test outputs seen in THIS session
- Current working directory only

### 1. Determine Target (Session-Based)

**If target provided as argument:** Use it directly.

**If no target provided:** Auto-detect from THIS SESSION:

| Priority | Detection Method | Source |
|----------|------------------|--------|
| **1** | Conversation context | What was discussed/implemented |
| **2** | Read/Edit tools in THIS session | Files touched in this chat |
| **3** | Working directory | `pwd` for current project |
| **4** | Test outputs seen | Test results in this conversation |

**Session scope filtering:**
```
INCLUDE: Files discussed/edited in THIS conversation
EXCLUDE: .claude/sessions/, __csf/, unrelated projects, stale git changes
```

**Example detection workflow:**
```python
# Check THIS SESSION only
conversation_mentions = ["yt_fts", "db", "videos"]  # From chat history
recent_edits = ["src/yt_fts/db/videos.py"]  # From Read/Edit tools in THIS session
# Inferred target: yt_fts/db/videos.py
```

### 2. Check Test Infrastructure

**Before running tests, verify what's available:**

| Check | Command | Purpose |
|-------|---------|---------|
| Has pytest? | `python -m pytest --version` | Verify pytest available |
| Has tests? | `ls tests/ 2>/dev/null || ls test_*.py 2>/dev/null` | Find test files |

**Test strategy:**

| Infrastructure | Use This Approach |
|----------------|-------------------|
| pytest available | `python -m pytest tests/ -v --tb=short` |
| No test infrastructure | Manual code review + static analysis |

### 2. Analyze Request Scope

    - Is this a single-file bug fix? → **FAST PATH** (Phase 1 Sanity only).
    - Is this a new feature? → **STANDARD PATH** (Phase 1-3).
    - Is this a release candidate? → **CAREFUL PATH** (Full Audit + Security).

---

## Phase 1: SANITY (Smoke Test & Security)

**Objective:** Fail fast on broken or insecure builds.

### Test Strategy Selection

**Run pytest directly:**

```bash
# Verify pytest is available
python -m pytest --version

# Run tests with coverage
python -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

# Security audit with bandit (if available)
python -m bandit -r src/ -f screen -ll
```

### Option B: No test infrastructure

1. **Static analysis:**
    ```bash
    python -m ruff check src/     # Linting
    python -m mypy src/           # Type checking (if configured)
    ```

2. **Manual code review** - Check for:
   - Import errors
   - Undefined variables
   - Syntax issues
   - Security vulnerabilities (SQL injection, command injection, etc.)

**Exit Criteria:** Tests pass OR manual review finds no critical issues.

---

## Phase 2: E2E (Browser Automation)

**Objective:** Verify critical user paths.

**Note:** Uses `notebooklm`'s browser factory for robust automation.

1.  **Select Scenario:**
    - Use `resources/e2e_scenarios_template.md` to define steps.
2.  **Execute Path:**
    > "Using the browser tool, navigate to [Local URL]. Perform [Core Action]. Verify [Success State]."

**Exit Criteria:** User story verified with visual evidence.

---

## Phase 3: CHAOS (Fuzz & Stress)

**Objective:** Find hidden crashes.

1.  **Property-Based Fuzzing:**
    ```bash
    python -m pytest tests/ --hypothesis-seed=0 -v
    ```
2.  **API Schema Fuzzing (if schemathesis available):**
    ```bash
    schemathesis run http://localhost:8000/docs --hypothesis-seed=0
    ```
3.  **Concurrency Stress (if locust available):**
    ```bash
    locust -f locustfile.py --headless -u 10 -r 5 -t 30s
    ```

**Exit Criteria:** No unhandled exceptions or 5xx errors.

---

## Phase 4: REPORT

**Objective:** Document certification verdict.

1.  **Generate `qa_report.md`:**
    - Aggregate test results.
    - Embed coverage report.
    - Attach E2E screenshots/logs.
2.  **Verdict:**
    - **PASS:** Certified for release.
    - **FAIL:** Blocked. Return to `/build`.

---

## Guardrails

- **Zero Tolerance:** Any smoke, security, or coverage failure stops the line.
- **Evidence:** Must screenshot UI success state for E2E.
- **Context:** Running in `context: fork` to prevent main session bloat.
- **Session Scope:** ONLY analyze changes from THIS terminal session conversation.
  - PROHIBITED: `git status` for scope detection (accumulates stale changes)
  - USE INSTEAD: Conversation history, Read/Edit tools from THIS session

**Next Steps** (pick one):

1. [Passed - Release] `/deploy` (or `/maintain` to cleanup)
2. [Passed - Optimize] `/evolve` (Refactor safely)
3. [Failed] `/build` (Return to fix bugs)

Reply with a number, or describe what you need.
