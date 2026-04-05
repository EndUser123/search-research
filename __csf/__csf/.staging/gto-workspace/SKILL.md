---
name: gap-task-opportunities
description: Analyze the current session chain and conversation context to identify gaps, unfinished work, TODO/FIXME markers, and actionable improvement opportunities. Use when user asks about "what's next", "what did I miss", "gaps in my code", "unfinished tasks", "TODO items", "test coverage gaps", "workflow friction", or "what should I work on next". Automatically runs session analysis, pattern detection, CKS integration, dependency mapping, friction analysis, test verification, and trend analysis to provide comprehensive gap detection and actionable next steps.
tools: Read, Glob, Grep, Bash, Write, Skill
---

# /gto - Gap Task Opportunities

Analyze the current session for gaps, unfinished work, and actionable improvement opportunities. Provides a comprehensive view of what's missing, what needs attention, and what to do next.

## Purpose

/gto performs session-scoped analysis (current conversation only, not global state) to identify:
- TODO/FIXME markers in code and conversation
- Unfinished work and incomplete tasks
- Test coverage gaps
- Workflow friction and blockers
- Dependency cascades and impacts
- Actionable quick-fix commands

## Core Modules

### 1. SessionAnalyzer (`scripts/session_analyzer.py`)
**Purpose**: Extract TODOs, detect unfinished work, and analyze conversation patterns.

**Key Methods**:
- `extract_todos(text)` - Find TODO/FIXME markers with word-boundary matching
- `detect_unfinished_work(conversation)` - Identify incomplete tasks
- `analyze_session()` - Generate structured session report

**Output**:
```python
{
    "todos": ["TODO: Fix auth.py line 45", "FIXME: Handle edge case"],
    "unfinished_work": ["start working on it now"],
    "session_metrics": {"todo_count": 2, "unfinished_count": 1}
}
```

### 2. CKSIntegrator (`scripts/cks_integrator.py`)
**Purpose**: Store discovered patterns in CKS for cross-session learning.

**Key Methods**:
- `store_pattern(pattern, category, metadata)` - Store single pattern
- `store_session_gaps(session_report)` - Store all gaps from session
- `search_similar_patterns(query)` - Find related patterns

**CKS Integration**: Gracefully degrades if CKS unavailable.

### 3. QuickActionsGenerator (`scripts/quick_actions.py`)
**Purpose**: Generate one-command fixes for common gaps.

**Key Methods**:
- `generate_todo_fixes(todos)` - Create edit commands for TODOs
- `generate_test_commands(test_gaps)` - Create test commands
- `format_actions_menu(actions)` - Display as numbered menu

**Output Example**:
```
Quick Actions Menu:
1. 🔴 Create tests for auth_module
   Command: pytest-test-create auth_module
2. 🟡 Address TODO: Fix auth.py line 45
   Command: edit auth.py
```

### 4. DependencyAnalyzer (`scripts/dependency_analyzer.py`)
**Purpose**: Map file dependencies and detect cascading impacts.

**Key Methods**:
- `build_dependency_map(files)` - Map imports to file dependencies
- `detect_cascading_impacts(changed_file, dep_map)` - Find impacted files
- `analyze_modified_files(modified_files)` - Full dependency analysis

### 5. FrictionDetector (`scripts/friction_detector.py`)
**Purpose**: Analyze conversation for blocks, corrections, and rework.

**Key Methods**:
- `detect_blocks(conversation)` - Find blocking patterns
- `detect_corrections(conversation)` - Find correction events
- `analyze_conversation(conversation)` - Full friction analysis

**Friction Levels**: `low`, `medium`, `high` (based on weighted score)

### 6. TestMatrixGenerator (`scripts/test_matrix.py`)
**Purpose**: Cross-reference code changes with test status.

**Key Methods**:
- `find_test_files()` - Locate all test files
- `find_source_files()` - Locate all source files
- `generate_matrix()` - Create test verification matrix

**Output**:
```python
{
    "total_sources": 50,
    "total_tests": 30,
    "covered_count": 25,
    "coverage_rate": 0.5
}
```

### 7. TrendAnalyzer (`scripts/trend_analyzer.py`)
**Purpose**: Compare current session to historical patterns.

**Key Methods**:
- `compare_to_baseline(current_metrics, baseline)` - Detect trends
- `detect_pattern_emergence(current_gaps, historical_patterns)` - Find recurring gaps

## Workflow

### Phase 1: Session Analysis
1. Initialize `SessionAnalyzer` with current conversation transcript
2. Extract TODO/FIXME markers from conversation and codebase
3. Detect unfinished work statements
4. Generate session metrics

### Phase 2: Enhancement Pipeline (Parallel)
1. **CKS Integration** - Store discovered patterns in CKS
2. **Quick Actions** - Generate one-command fixes
3. **Dependency Graph** - Map file dependencies
4. **Friction Detection** - Analyze conversation for blockers
5. **Test Matrix** - Cross-reference test coverage
6. **Trend Analysis** - Compare to historical patterns

### Phase 3: Report Generation
1. Aggregate all enhancement outputs
2. Prioritize by impact/effort score
3. Format as actionable report with quick actions menu

## Usage Examples

### Basic Session Analysis
```bash
/gto
```
Output: Full gap analysis with TODOs, unfinished work, and recommendations

### Focus on Test Gaps
```bash
/gto what test coverage am I missing?
```
Output: Test verification matrix with uncovered modules

### After Getting Blocked
```bash
/gto I keep getting blocked by hooks
```
Output: Friction analysis with block patterns and severity

### Quick Actions Menu
```bash
/gto show me quick fixes
```
Output: Numbered menu of one-command fixes

## Session-Scoped Behavior

**Important**: /gto analyzes ONLY the current conversation session, not global state or project history. For historical analysis, explicitly provide context or use trend analyzer with baseline data.

## Error Handling

All modules implement graceful degradation:
- CKS unavailable → Pattern storage skipped (warning logged)
- Git not initialized → Skip git-based features
- No tests found → Report 0% test coverage
- Empty conversation → Report "No conversation data available"

## Output Format

Structured report with sections:
1. **Summary** - High-level gap count and severity
2. **TODOs Found** - List with file locations
3. **Unfinished Work** - Incomplete tasks
4. **Quick Actions** - One-command fixes (prioritized)
5. **Dependency Analysis** - File impacts
6. **Friction Score** - Workflow issues detected
7. **Test Coverage** - Coverage matrix
8. **Trend Analysis** - Historical comparisons

## Success Criteria

/gto is successful when:
- All 6 enhancements produce output (no silent failures)
- Quick actions generate valid commands
- CKS integration persists patterns (when available)
- Test matrix identifies coverage gaps
- Friction detection flags blockers
- Dependencies are mapped correctly

## Integration Points

- **CKS**: `knowledge.systems.chs.unified.CKS` for pattern storage
- **/serena**: Semantic code analysis for dependency graph (optional)
- **Git**: Test status detection, modified files
- **Session History**: Conversation transcript analysis

## Testing

Run tests with:
```bash
pytest test_session_analyzer.py test_enhancements.py -v
```

Expected: 21 tests passing (7 session_analyzer + 14 enhancements)
