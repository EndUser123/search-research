# Skills Infrastructure and Metadata Survey

**Completed:** 2026-03-09
**Agent:** Config Reader
**Task:** #1554 - Infrastructure and metadata survey

---

## Executive Summary

The CSF (Constitutional Skills Framework) uses a **documentation-driven skill architecture** where SKILL.md files ARE the handlers—not references to separate code. Skills are markdown documents that Claude reads and follows directly, with built-in tools called inline.

### Key Finding
Skills follow the **Claude Code native pattern**: SKILL.md files are both documentation and implementation. No separate handler Python files are needed for simple workflows.

---

## 1. Skills Architecture

### 1.1 Core Pattern: Documentation-Driven Execution

**Principle:** SKILL.md IS the handler

```markdown
WRONG: /skill → skill_handler.py → executes code → returns result
RIGHT: /skill → Skill tool loads SKILL.md → Claude reads workflow → Claude calls tools directly → returns result
```

**Evidence:**
- `/task` skill: 200-line SKILL.md that calls TaskList/TaskCreate/TaskUpdate directly
- No task_handler.py needed—deleted during research phase
- See `claude_skills_operational_guide.md` Section 1.5 for full comparison

### 1.2 Skill Structure

**Directory Layout:**
```
.claude/skills/
├── SKILL_SCHEMA.md          # Metadata schema
├── SKILL_TEMPLATE.md        # New skill template
├── INTEGRATION_VERIFICATION_README.md  # Integration testing guide
├── skill-name/
│   └── SKILL.md             # Router + implementation
└── skill-with-variants/
    ├── SKILL.md             # Router
    └── resources/           # Implementation templates
        ├── variant1.md
        ├── variant2.md
        └── variant3.md
```

**SKILL.md Frontmatter:**
```yaml
---
name: skill-name
description: Human-readable description
category: workflow|analysis|quality
triggers:
  - /skill-name
  - /alias
internal: true  # Optional: hides from discovery
---
```

### 1.3 Skill Implementation Patterns

| Pattern | Use Case | Structure | Discovery |
|---------|----------|-----------|-----------|
| **Monolithic** | Simple workflows, <200 lines | Single SKILL.md | Single entry |
| **Resource Templates** | Variants with shared structure | SKILL.md + resources/*.md | Single entry |
| **Skill Dispatch** | Independent testing needed | Multiple skill-* directories | All visible |
| **Hybrid** | Complex with simple variants | Router + selective dispatch | Controlled |

---

## 2. Testing Infrastructure

### 2.1 Test Configuration

**pytest.ini (pyproject.toml):**
```toml
[tool.pytest.ini_options]
testpaths = ["src", ".claude/hooks/tests"]
pythonpath = ["src"]
addopts = "-p no:cacheprovider"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration",
    "unit: marks tests as unit",
]
```

### 2.2 Test Patterns

**Anti-Mock Stance** (see `testing_patterns.md`):
- Prefer real objects over mocks
- Functional verification: import and call actual code
- Test failures should mean actual bugs

**Test Location Conventions:**
```
src/
├── module/
│   ├── __init__.py
│   └── tests/
│       ├── test_module.py
│       └── fixtures/
└── tests/
    ├── test_shared.py
    └── conftest.py
```

### 2.3 Test Count Analysis

**Summary:**
- 500+ test functions across 100+ test files
- Heavy coverage in: CKS, CHS, CLI, code intelligence
- Integration tests use real components, not mocks

**Notable Test Areas:**
- `src/cks/tests/` - Constitutional Knowledge System
- `src/chs/hypergraph/test_*.py` - Chat History Search
- `src/cks/integration/test_*.py` - Integration tests
- `.claude/hooks/tests/` - Hook validation

---

## 3. Validation Infrastructure

### 3.1 Documentation Validation

**Key File:** `INTEGRATION_VERIFICATION_README.md`

**Protocol:** When agents generate code requiring new files:
1. Check SKILL.md / documentation first
2. Verify mechanism exists (script vs agent vs inline)
3. Cross-check codebase
4. Validate test expectations against reality

**Evidence Hierarchy (most → least authoritative):**
1. User's explicit statement
2. SKILL.md / documentation
3. Existing implementation patterns
4. Agent inferences
5. Test expectations

### 3.2 Hook-Based Validation

**Hook Types:**
- `PreToolUse_*` - Before tool execution
- `PostToolUse_*` - After tool execution
- `Stop_*` - Behavior gates

**Examples:**
- `PreToolUse_file_existence_guard.py` - File operations validation
- `Stop_behavior_gates.py` - Behavioral constraints
- `PostToolUse_evidence_validator.py` - Output validation

### 3.3 Quality Gates

**Skills with built-in validation:**
- `/q` - Strategic quality assessment
- `/p` - Tactical quality pipeline (with phase enforcement)
- `/docs-validate` - Documentation validation
- `/package` - Package creation with validation

---

## 4. Documentation Conventions

### 4.1 Core Documentation Files

| File | Purpose | Location |
|------|---------|----------|
| `CLAUDE.md` | Project context and workflow | `/p/__csf/CLAUDE.md` |
| `DEVELOPMENT_WORKFLOW.md` | Director + AI workforce model | `/p/__csf/DEVELOPMENT_WORKFLOW.md` |
| `claude_skills_operational_guide.md` | How-to implementation patterns | `/p/__csf/docs/` |
| `claude_skills_and_agentic_patterns.md` | Theoretical foundations | `/p/__csf/docs/` |
| `SKILL_SCHEMA.md` | Metadata schema | `/.claude/skills/` |
| `SKILL_TEMPLATE.md` | New skill template | `/.claude/skills/` |

### 4.2 Documentation Patterns

**Progressive Disclosure:**
- Default: Fast/simple path
- User requests depth: Switch to detailed
- User asks for alternatives: Show options

**Evidence-Based Documentation:**
- Show actual runs, test output
- Not summaries or "should work"
- Verification over claims

### 4.3 README Conventions

**Project README Structure:**
```markdown
# Project Name

## Purpose
## Architecture
## Development Style (✅/❌ patterns)
## Key Files
## Dependencies
## Quick Reference
## Development Philosophy
```

---

## 5. Configuration and Metadata

### 5.1 Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | pytest configuration, markers |
| `tdd_pipeline_config.yaml` | TDD workflow settings |
| `.claude/settings.json` | Claude Code settings, hook registration |

### 5.2 Skill Metadata Schema

**Required Fields:**
```yaml
---
name: skill-name
description: One-line description
category: workflow|analysis|quality|research
triggers:
  - /skill-name
---
```

**Optional Fields:**
```yaml
internal: true        # Hide from discovery
deprecated: true      # Mark as deprecated
version: "1.0.0"      # Skill version
author: "name"        # Skill author
```

### 5.3 Resource Templates

**Template Format:**
```markdown
# Variant Name

## Analysis Steps
1. Step one
2. Step two

## Output Format
Expected structure...
```

**Router Logic:**
```markdown
## Stage 1: Classify Intent
Determine variant based on keywords

## Stage 2: Include Template
Read(file_path="P:/.claude/skills/skill-name/resources/variant1.md")
```

---

## 6. Anti-Patterns to Avoid

### 6.1 Standalone Handler Anti-Pattern

**WRONG:**
```python
# task_handler.py - NEVER CALLED by Claude
def handle_add(subject):
    return TaskCreate(subject=subject)
```

**RIGHT:**
```markdown
# SKILL.md - THIS IS the handler
## Sub-Command: add
1. Parse subject
2. Call TaskCreate(subject="...", status="pending")
```

### 6.2 Enterprise Anti-Patterns

**Avoid (from DEVELOPMENT_WORKFLOW.md):**
- Background autonomous services
- Self-healing systems without approval
- Real-time monitoring dashboards
- Team approval gates for solo dev
- Lock-free multi-terminal coordination
- CI/CD for single person

### 6.3 Testing Anti-Patterns

**Don't:**
- Mock when real objects work
- Test unused handler files
- Create tests that don't fail on bad code
- Use complex fixtures unnecessarily

**Do:**
- Import and test actual code
- Verify functional behavior
- Use integration tests for workflows
- Keep tests simple and focused

---

## 7. Development Workflow Patterns

### 7.1 Director + AI Workforce

**Your Role:**
- Technical director/architect
- Provide requirements
- Review work
- Guide direction

**AI Role:**
- Primary developer
- Write code, tests, docs
- Under your direction
- Not autonomous

### 7.2 Quality-First Approach

**Thoroughness > Speed:**
- Functional verification matters
- Import modules, call functions, assert results
- "Does it work correctly?" is first question
- Evidence over speculation

**Decision Support Tools:**
- Risk engines (what to test based on changes)
- Context models (module criticality)
- Integration flows (YAML-defined workflows)

### 7.3 When Separate Code IS Appropriate

**Only when:**
1. External API integration (async/complex)
2. Heavy computation (Python better than markdown)
3. Independent testing needed (unit tests outside Claude)

**Even then, consider:**
- Can a hook handle this?
- Can a sub-skill handle this?
- Can SKILL.md document this?

---

## 8. Tool and API Usage

### 8.1 Built-in Claude Code Tools

| Tool | Purpose | Used In Skills |
|------|---------|----------------|
| `TaskCreate` | Create task | /task |
| `TaskUpdate` | Update task | /task |
| `TaskList` | List tasks | /task |
| `TaskGet` | Get task details | /task |
| `Read` | Read file | Most skills |
| `Write` | Write file | Most skills |
| `Edit` | Edit file | Most skills |
| `Bash` | Execute command | Many skills |
| `Skill` | Invoke other skill | Router skills |
| `Glob` | Find files | Discovery skills |
| `Grep` | Search files | Search skills |

### 8.2 MCP Server Integration

**Available MCP Servers:**
- **NotebookLM** - Research, note-taking, artifact generation
- **Context7** - Library documentation
- **Perplexity** - Web search, research
- **Tavily** - Web crawling, extraction
- **Exa** - Code context search

### 8.3 Knowledge Systems

| System | Purpose | Location |
|--------|---------|----------|
| **CKS** | Constitutional Knowledge System | `src/knowledge/systems/cks/` |
| **CHS** | Chat History Search | `src/knowledge/systems/chs/` |
| **CDS** | Code Documentation Search | Integrated |

---

## 9. Shared Infrastructure

### 9.1 Shared Libraries

**Location:** `src/shared_libs/`

**Purpose:** Reusable infrastructure for:
- Research operations
- Handoff management
- Tracking and state
- Testing utilities

### 9.2 Test Colocation

**Pattern:** Tests near code

```
src/
├── module/
│   ├── __init__.py
│   ├── main.py
│   └── tests/
│       └── test_main.py
```

**Rationale:** Tests as documentation, easier maintenance

### 9.3 Conftest Patterns

**Purpose:** Shared fixtures and configuration

**Location:** `src/conftest.py`

---

## 10. Key Findings and Recommendations

### 10.1 Strengths

1. **Clear Architecture:** Documentation-driven pattern is well-defined
2. **Comprehensive Documentation:** Operational guide, patterns guide
3. **Anti-Pattern Awareness:** Explicit documentation of what NOT to do
4. **Testing Infrastructure:** pytest with markers, functional verification
5. **Validation Framework:** Hooks, evidence-based documentation

### 10.2 Areas for Improvement

1. **Test Coverage Gaps:** Some modules lack comprehensive tests
2. **Skill Discovery:** No automated inventory of 210+ skills
3. **Integration Tests:** Need more end-to-end workflow tests
4. **Documentation Sync:** Some docs may not match current implementation

### 10.3 Recommendations for Skills Review

**For Categorization (#1553):**
- Use `category:` frontmatter field
- Check `internal:` flag for user-facing vs internal
- Look for `resources/` directories for template-based skills

**For Dependency Scanning (#1555):**
- Scan SKILL.md for tool invocations
- Check for `Skill()` calls (skill dependencies)
- Look for hook references
- Check MCP server usage patterns

**For Testing:**
- Functional verification: import and test
- No mocks unless necessary
- Integration tests for workflows
- Evidence-based test expectations

---

## 11. File Inventory

### 11.1 Configuration Files
- `/p/__csf/pyproject.toml` - pytest configuration
- `/p/__csf/tdd_pipeline_config.yaml` - TDD settings
- `/p/.claude/settings.json` - Claude Code settings

### 11.2 Core Documentation
- `/p/__csf/CLAUDE.md` - Project context
- `/p/__csf/DEVELOPMENT_WORKFLOW.md` - Workflow patterns
- `/p/__csf/docs/claude_skills_operational_guide.md` - How-to
- `/p/__csf/docs/claude_skills_and_agentic_patterns.md` - Theory
- `/p/.claude/skills/SKILL_SCHEMA.md` - Metadata schema
- `/p/.claude/skills/SKILL_TEMPLATE.md` - New skill template

### 11.3 Testing Infrastructure
- `/p/__csf/src/tests/` - 500+ test functions
- `/p/__csf/src/conftest.py` - Shared fixtures
- `/p/.claude/hooks/tests/` - Hook tests

### 11.4 Skills Directory
- `/p/.claude/skills/` - 210+ skills
- Mix of monolithic, template-based, and dispatch patterns

---

## Summary

The CSF skills infrastructure is **mature and well-documented**, with a clear documentation-driven architecture. The key insight is that SKILL.md files ARE the implementation—not references to separate code. Testing emphasizes functional verification over mocks, and validation occurs through hooks and evidence-based documentation.

**For the skills review bundle:**
- Use this survey to understand skill patterns
- Refer to operational guide for implementation details
- Check SKILL_SCHEMA.md for metadata conventions
- Look for testing patterns in test files
- Verify dependencies by scanning tool invocations
