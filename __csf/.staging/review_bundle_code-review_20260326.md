# Review Bundle: /code-review Skill
**Generated**: 2026-03-26T18:50:00Z
**Scope**: P:/.claude/skills/code-review/
**File Count**: 7 files
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: code-review
- **Version**: 1.0.0
- **Category**: analysis
- **Trigger**: `/code-review`, `/review`, "review code", "review my code"
- **Enforcement**: advisory

### Domain & Purpose
Automates comprehensive code review workflows using parallel specialist agents. Dispatches security, logic, performance, and quality subagents to analyze code and synthesize actionable findings with severity ratings and health scores.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Python/markdown
- **Key Integration**: Subagent dispatch via Task tool

---

## 2. ARCHITECTURE OVERVIEW

```
                    ┌──────────────────────────────────────────┐
                    │            /code-review SKILL              │
                    │  6-Step Workflow: Target → Session →      │
                    │  Parallel Dispatch → Synthesis → Report   │
                    └──────────────┬───────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│adversarial-sec  │  │adversarial-logic│  │adversarial-perf │
│adversarial-io   │  │adversarial-qual │  │adversarial-test │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         └───────────────────┬┴───────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │     review.md (synthesis)   │
              │  Health Score + Findings    │
              └─────────────────────────────┘
```

### Specialist Agent Mapping

| Agent | Focus | Applies To |
|-------|-------|------------|
| `adversarial-security` | Auth, injection, data exposure | All code |
| `adversarial-logic` | Conditionals, operators, flow | All code |
| `adversarial-performance` | Loops, DB, N+1, hot paths | Python, DB-heavy |
| `adversarial-io-validation` | Path traversal, file ops, external calls | All code |
| `adversarial-quality` | Tech debt, maintainability | All code |
| `adversarial-testing` | Test coverage, edge cases | All code |

---

## 3. EXECUTION AND DATA FLOW

### Step 1: Capture Review Target
Priority order for target resolution:
1. Args specifies target
2. Recent session focus
3. Ask if ambiguous

Supported targets:
- Single file: `P:/path/to/file.py`
- Multiple files: `P:/path/to/*.py`
- Directory: `P:/path/to/project/`
- Glob pattern: `**/*.js`

### Step 2: Initialize Review Session
```bash
python -c "
from pathlib import Path
import uuid
session_id = str(uuid.uuid4())[:8]
session_dir = Path('P:/.claude/.evidence/code-review/') / session_id
session_dir.mkdir(parents=True, exist_ok=True)
..."
```
Creates: `{session_dir}/work.md`

### Step 3: Launch Parallel Specialist Agents
Dispatch via Task tool to `general-purpose` subagent:
```python
Task(
  subagent_type="general-purpose",
  description="Review code at: P:/{session_dir}/work.md for [domain]. Write findings to: P:/{session_dir}/specialists/[name].md"
)
```

### Step 4: Synthesize Findings
Read all specialist findings and create synthesized review:
```bash
cat "P:/{session_dir}/specialists/"*.md 2>/dev/null | head -500
```

### Step 5: Generate Report
Output to `P:/{session_dir}/review.md`:
```markdown
# Code Review Report
**Target:** {target}
**Date:** {date}
## Health Score: XX%
| Severity | Count |
|----------|-------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |
## Findings
[severity-tagged findings with file:line citations]
```

### Health Score Calculation
```
Health Score = 100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2), capped at 0-100
```

| Score Range | Interpretation |
|-------------|----------------|
| 80-100 | Healthy — Low risk, minor improvements |
| 50-79 | Warning — Significant issues, address HIGH first |
| Below 50 | Critical — Systemic problems, do not deploy |

---

## 4. COMPONENT INVENTORY

### Files

| File | Purpose |
|------|---------|
| SKILL.md | Main skill definition (200 lines), workflow, specialist mapping |
| phases/p1_specialist_dispatch.md | Phase 1 dispatch protocol |
| phases/p2_synthesis.md | Phase 2 synthesis protocol |
| lib/__init__.py | Package marker |
| lib/review_session.py | Review session management |
| tests/__init__.py | Package marker |
| tests/test_review_session.py | Session management tests |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Parallel specialist dispatch** — All agents run simultaneously
2. **Context-aware target resolution** — Args > session focus > ask
3. **Severity-tagged findings** — CRITICAL/HIGH/MEDIUM/LOW with file:line citations
4. **Health score metric** — Quantitative code quality assessment
5. **Session persistence** — Review sessions stored for later reference

### Things That Must NOT Change
- **Health score formula** — External tools may depend on calculation
- **Severity level names** — Report format consistency
- **Session directory structure** — Cleanup depends on predictable paths

---

## 6. KNOWN ISSUES

No known issues. Simple single-pass review with parallel agents.

---

## 7. INTEGRATION POINTS

### With Other Skills
- Uses `adversarial-*` agents for specialist analysis
- Complementary to `/adversarial-review` (which is more comprehensive)

### State Directory
- `P:/.claude/.evidence/code-review/{session_id}/`
- Contains: work.md, specialists/*.md, review.md

### Session Persistence
Sessions persist until manually removed (no automatic cleanup)

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | BASIC | 1 test file for session management |
| Error Handling | GOOD | Graceful missing-file handling |
| Multi-terminal Safety | GOOD | Session-scoped directories |
| Documentation | GOOD | 200-line SKILL.md with examples |
| Hook Integration | N/A | No hooks |
| Parallel Safety | GOOD | Independent specialist agents |

### SQA Relevance
- **HIGH** — This IS an SQA skill (Code Review)
- Automated multi-perspective review
- Quantitative health scoring
- Severity-ranked findings with citations
