# Quality Gates Architecture

Architecture decisions and file structure for the quality system.

---

## Overview

The Quality Gates system provides code quality validation through multiple phases:
- Structure validation
- Duplicate detection
- Governance/compliance
- Architecture analysis
- Security scanning
- API/Service validation
- Code review
- Performance analysis
- Final pre-deployment checks

---

## Core Architecture

```
qual-gate.py                 # Main CLI entry point
    ├── enhanced_execution.py # Enhanced phases with discover/zen adapters
    ├── unified_analyzer.py   # Facade for tool execution
    │   └── tool_orchestrator.py # Real subprocess execution (ruff/mypy/bandit)
    └── architectural_analyzer.py # Design and structure analysis
```

---

## File Responsibilities

### `qual-gate.py`
**Purpose**: Main CLI entry point
**Key Functions**:
- `execute_phase()` - Runs a specific quality gate phase
- `execute_command()` - Executes external commands
- Handles phase-aware routing and result aggregation

### `unified_analyzer.py`
**Purpose**: Facade for quality analysis tools
**Key Functions**:
- `analyze_comprehensive(target, phase, focus_areas)` - Main entry point
- `analyze_ruff(target)` - Ruff linting
- `analyze_mypy(target)` - Mypy type checking
- `analyze_bandit(target)` - Bandit security scanning

**CRITICAL**: No fake fallback! Direct import of ToolOrchestrator only.

### `tool_orchestrator.py` (NEW)
**Purpose**: Real subprocess execution of quality tools
**Key Methods**:
- `_run_ruff(target_path)` - Executes ruff with `--output-format=json`
- `_run_mypy(target_path)` - Executes mypy, parses output
- `_run_bandit(target_path)` - Executes bandit with `-f json`
- `analyze(target, analyzers, parallel)` - Main entry point

**Returns**: `AnalyzerResult` with real issue counts and details

### `enhanced_execution.py`
**Purpose**: Enhanced quality execution with discover/zen adapters
**Key Functions**:
- `execute_architecture_phase()` - Architecture validation
- `execute_security_phase()` - Security scanning
- `execute_cognitive_review_phase()` - LLM-based review

**BUG FIXED**: Line 623 now checks `isinstance(count, str)` before `"error" in count`

### `architectural_analyzer.py`
**Purpose**: Design and structure analysis
**Key Functions**:
- `analyze()` - Returns architecture quality score
- Checks: modules, dependencies, layers, patterns, documentation

---

## Data Flow

```
User runs: /quality <target>
         ↓
qual-gate.py parses args
         ↓
Phase execution (structure → governance → architecture → ...)
         ↓
For each phase:
    1. Enhanced execution (discover/zen adapters)
    2. Unified analyzer (ruff/mypy/bandit)
    3. Result aggregation
         ↓
Final report with pass/fail per gate
```

---

## Database Integration

### Canonical Database
**Path**: `P:/.speckit/taskmaster/tasks.db`
**Schema**: v2 (migrated from v1)
**Tables**:
- `tasks` - Quality tasks with status, priority, etc.
- `projects` - Project tracking
- `evidence` - Evidence collection for gate results

### TaskMaster Integration
- `DatabaseManager` - Unified CRUD operations
- `TMCommand` - CLI orchestrator for `/tm` commands
- `get_context_aware_tsk_path()` - Returns canonical path

---

## Quality Gate Phases

| Phase | Name | Tools Used | Purpose |
|-------|------|------------|---------|
| 0 | Constitutional | qual-constitution-tree.py | CSF NIP compliance |
| 1 | Structure | qual_foundation.py | Project structure validation |
| 2 | Duplicates | cq (code quality) | Code duplication detection |
| 3 | Governance | qual-constitution-tree.py | Constitutional tree validation |
| 4 | Architecture | ArchitecturalAnalyzer | Design and structure analysis |
| 5 | Security | Bandit, Safety, Semgrep | Security vulnerability scanning |
| 6 | APIs & Services | API validators | External service validation |
| 7 | Code Review | Zen-Code-Review | Multi-LLM semantic review |
| 8 | Performance | Performance analyzers | Scalability validation |
| 9 | Final Check | Comprehensive | Pre-deployment validation |

---

## Configuration

### Quality Gate Config (`.qual-gate.json`)
```json
{
  "gates": {
    "code_review": {
      "review_mode": "mid",
      "focus_areas": ["security", "performance", "bugs"]
    }
  },
  "verify_findings": true,
  "cost_tracking": true,
  "compress_results": false
}
```

### Environment Variables
- `QUAL_GATE_VERIFY_FINDINGS=true` - Enable finding verification
- `QUAL_GATE_COST_TRACKING=true` - Track LLM costs
- `QUAL_GATE_REVIEW_MODE=mid` - Gate 6 review mode

---

## Anti-Patterns (DO NOT DO)

1. **Fake fallback data** - Never return empty/hardcoded results
2. **100/100 PASSED for no code** - Return SKIPPED status instead
3. **Project-specific database paths** - Use canonical `P:/.speckit/taskmaster/tasks.db`
4. **Unchecked iteration** - Always validate types before `in` operator
5. **Silent failures** - Log errors and return proper status codes

---

## Integration Points

| System | Integration Point |
|--------|-------------------|
| CKS | Semantic search, pattern detection |
| Discover | Code intelligence, health checks |
| Zen-Code-Review | Multi-LLM semantic review |
| TaskMaster | Task tracking, evidence collection |
| CWO12 | Workflow orchestration |
