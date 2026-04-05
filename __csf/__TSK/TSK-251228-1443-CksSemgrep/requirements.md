# Requirements: Hybrid Semgrep + ESLint Auto-Fix System

## Executive Decision
**Project files approach** - Store configs in `.semgrep.yml` and `.eslintrc.json` at project root, not in CKS database.

## Functional Requirements

### Python Requirements (Semgrep)

### FR-001: Semgrep Configuration File
- **Priority**: P0 (Required)
- **Description**: `.semgrep.yml` in project root with Python rules
- **Format**: Standard Semgrep YAML format
- **Acceptance**: File readable by Semgrep CLI

### FR-002: Semgrep Invocation
- **Priority**: P0 (Required)
- **Description**: Run Semgrep with --autofix on target path
- **Command**: `semgrep --config=.semgrep.yml --json --autofix <target>`
- **Acceptance**: Subprocess runs, output captured

### FR-003: Semgrep Result Parser
- **Priority**: P0 (Required)
- **Description**: Parse Semgrep JSON output into unified violation format
- **Acceptance**: Returns violations list, fixes_applied list

### FR-004: Python File Detection
- **Priority**: P0 (Required)
- **Description**: Detect Python files (.py extension)
- **Acceptance**: Routes to Semgrep runner

### TypeScript Requirements (ESLint)

### FR-005: ESLint Configuration File
- **Priority**: P0 (Required)
- **Description**: `.eslintrc.json` in project root with TypeScript rules
- **Format**: Standard ESLint JSON format with @typescript-eslint
- **Acceptance**: File readable by ESLint CLI

### FR-006: ESLint Invocation
- **Priority**: P0 (Required)
- **Description**: Run ESLint with --fix on target path
- **Command**: `eslint --config=.eslintrc.json --fix --format=json <target>`
- **Acceptance**: Subprocess runs, output captured

### FR-007: ESLint Result Parser
- **Priority**: P0 (Required)
- **Description**: Parse ESLint JSON output into unified violation format
- **Acceptance**: Returns violations list, fixes_applied list

### FR-008: TypeScript File Detection
- **Priority**: P0 (Required)
- **Description**: Detect TypeScript files (.ts, .tsx extensions)
- **Acceptance**: Routes to ESLint runner

### Unified Requirements

### FR-009: Orchestrator
- **Priority**: P0 (Required)
- **Description**: Single coordinator running both Semgrep and ESLint
- **API**: `detect_and_fix(changed_files: List[Path]) -> Dict`
- **Acceptance**: Routes by file type, aggregates results

### FR-010: Unified Violation Reporting
- **Priority**: P0 (Required)
- **Description**: Python and TypeScript violations in single report
- **Acceptance**: Consistent format and severity levels

### FR-011: Verification Loop
- **Priority**: P1 (Important)
- **Description**: Re-run both tools without auto-fix to confirm all violations resolved
- **Acceptance**: Returns verification status per language

## Non-Functional Requirements

### NFR-001: Performance
- **Startup overhead**: <500ms per tool invocation
- **Per-file check**: <100ms average

### NFR-002: Reliability
- **Graceful degradation**: Continue if tool not installed (log warning)
- **Error handling**: Parse errors don't crash orchestrator

### NFR-003: Compatibility
- **Windows 11**: subprocess invocation works on Windows
- **Python 3.12+**: No deprecated stdlib usage
- **Node.js**: Required for ESLint

### NFR-004: Maintainability
- **Project files**: Standard YAML/JSON, no database queries
- **Git versioned**: Config changes tracked in git
- **Team readable**: No JSON escaping of YAML needed

## Dependencies

| Dependency | Version | Required For |
|------------|---------|--------------|
| Semgrep CLI | Latest | Python detection + auto-fix |
| ESLint | Latest | TypeScript detection + auto-fix |
| @typescript-eslint/parser | Latest | TypeScript parsing |
| @typescript-eslint/eslint-plugin | Latest | TypeScript rules |
| Python stdlib | 3.12+ | subprocess, json, pathlib |

## Out of Scope

- CKS database storage (using project files instead)
- LibCST integration
- Web UI for rule editing
- Real-time monitoring
- Distributed execution

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Semgrep not installed | Medium | High | Log warning, skip Python checks |
| ESLint not installed | Medium | High | Log warning, skip TypeScript checks |
| Windows subprocess issues | Low | Medium | Use shutil.which() for path resolution |
| Config file missing | Low | Medium | Log error, return empty results |
| Rule conflicts | Low | Low | Document rule precedence |

## Success Criteria

1. `.semgrep.yml` and `.eslintrc.json` exist in project root
2. Orchestrator detects file language and routes correctly
3. Both tools run with auto-fix via subprocess
4. Results parsed into unified violation format
5. 95% of test violations auto-fixed
6. Verification loop confirms fixes
7. Works on Windows 11
8. Both Python and TypeScript handled in Phase 1
