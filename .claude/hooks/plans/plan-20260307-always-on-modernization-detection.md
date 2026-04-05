# Implementation Plan: Always-On Modernization Detection for /code Skill

**Date**: 2026-03-07
**Status**: REVISED (addressed adversarial review findings)
**Route**: Subagent implementation (3 parallel tracks + 2 new tasks)

## Overview

Implement automatic modernization detection in the `/code` skill's EXPLORE phase to identify library version updates, breaking changes, and modern pattern opportunities without requiring flags. The system will integrate Context7 for breaking change detection and enhance plan.md with a "Modernization Considerations" section, making modernization awareness a default behavior.

**Key Principles**:
- Detection is automatic (no flags required)
- Information is always presented in plan.md
- User makes informed choice based on presented options
- Default to codebase patterns for internal coherence

## Context Analysis

### Allowed APIs

**Context7 MCP Tools** (confirmed from documentation discovery):
```python
mcp__plugin_context7_context7__resolve-library-id
  - libraryName: str
  - query: str
  → Returns: library_id, versions list, source reputation

mcp__plugin_context7_context7__query-docs
  - libraryId: str  # Format: /org/project or /org/project/version
  - query: str
  → Returns: documentation with code examples
```

**Library Detection Methods** (confirmed patterns):
```python
# requirements.txt parsing
from pathlib import Path
requirements = Path("requirements.txt").read_text().splitlines()

# Import scanning
import ast
tree = ast.parse(source_code)
imports = [node.names for node in ast.walk(tree) if isinstance(node, ast.Import)]

# pyproject.toml reading
import tomli
config = tomli.loads(Path("pyproject.toml").read_text())
deps = config.get("project", {}).get("dependencies", [])
```

### Anti-Patterns to Avoid

1. **Don't invent Context7 query patterns** - Always use resolve-library-id first, then query-docs
2. **Don't assume version format** - Use semantic versioning parsing, not string comparison
3. **Don't hardcode library names** - Detect from imports and dependency files
4. **Don't bypass Context7 rate limits** - Implement proper throttling with shared rate limit tracker
5. **Modernization is NON-BLOCKING** - Detection never blocks EXPLORE phase, findings are recommendations only
6. **Don't assume all projects have dependencies** - Handle pure stdlib projects and non-Python projects

### Existing Implementation Discovery

**Current /code Skill Structure** (from `P:\.claude\skills\code\SKILL.md`):
- **Phase 3 (EXPLORE)**: Subagent discovery for existing patterns
- **Phase 4 (PLAN)**: Creates plan.md with 7 sections
- **Integration Points**:
  - PRE-FLIGHT: Dependency check (health check, checkpoint)
  - TDD: Library validation with library_checker
  - AUDIT: Quality checks (ruff, mypy, pylint)

**Current plan.md Template** (from `P:\.claude\skills\code\plan.md`):
7 sections: Overview, Architecture, Data Flow, Error Handling, Test Strategy, Standards Compliance, Ramifications

**Gap**: No modernization detection, no version trend analysis, no breaking change flags

### Test Discovery

**Required Test Coverage**:
1. **Library Detection Tests**:
   - Scan imports from Python files
   - Parse requirements.txt
   - Read pyproject.toml dependencies
   - Handle missing dependency files gracefully

2. **Version Comparison Tests**:
   - Semantic version parsing (1.2.3 → MAJOR.MINOR.PATCH)
   - Detect MAJOR version updates
   - Identify breaking changes via Context7

3. **Context7 Integration Tests**:
   - Successful library resolution
   - Breaking change query parsing
   - Error handling for unknown libraries
   - Rate limit handling
   - **Shared rate limit coordination across tracks** (NEW)

4. **Plan Enhancement Tests**:
   - Modernization Considerations section creation
   - Priority categorization (P0/P1/P2)
   - Migration option presentation
   - **User opt-out mechanism** (NEW)

5. **Integration Tests**:
   - EXPLORE phase workflow
   - plan.md generation with modernization findings
   - User choice handling in IMPLEMENT phase
   - **Pure stdlib project handling (no dependencies)** (NEW)
   - **Non-Python project handling** (NEW)
   - **User opt-out flow** (NEW)

## Proposed Solution

### Architecture

**3-Track Parallel Implementation**:

```
Track 1: Library Detection & Version Analysis
  ├─ ImportScanner (AST-based)
  ├─ DependencyFileParser (requirements.txt, pyproject.toml)
  └─ VersionComparator (semantic versioning)

Track 2: Context7 Breaking Change Detection
  ├─ LibraryResolver (resolve-library-id wrapper)
  ├─ BreakingChangeDetector (query-docs for changelogs)
  ├─ PriorityScorer (P0/P1/P2 categorization)
  └─ Context7RateLimitCoordinator (shared rate limit tracker across all tracks)

Track 3: Plan Template Enhancement
  ├─ ModernizationSectionGenerator
  ├─ RecommendationEngine (conservative vs aggressive)
  ├─ PlanIntegrator (injects into plan.md)
  └─ UserAcknowledgmentHandler (opt-out mechanism)
```

**Component Responsibilities**:

1. **ModernizationDetector** (orchestrator):
   - Coordinates 3 tracks
   - Merges findings
   - Generates modernization report

2. **LibraryDetectionPipeline**:
   - Scans codebase for library usage
   - Parses dependency files
   - Builds dependency graph

3. **Context7QueryPipeline**:
   - Resolves library IDs
   - Queries breaking changes
   - Caches results to avoid rate limits

4. **PlanEnhancer**:
   - Adds "Modernization Considerations" section
   - Formats findings with priorities
   - Presents user choice options

### Data Flow

```
EXPLORE Phase Start
    ↓
[Parallel Track 1] Library Detection
  ├─ Scan imports (AST)
  ├─ Parse dependency files
  └─ Build library list
    ↓
[Parallel Track 2] Context7 Queries
  ├─ Resolve library IDs
  ├─ Query breaking changes
  └─ Categorize by priority
    ↓
[Parallel Track 3] Plan Enhancement
  ├─ Detect modernization opportunities
  ├─ Generate recommendations
  └─ Format plan.md section
    ↓
Merge Findings
    ↓
Update plan.md with Modernization Considerations
    ↓
EXPLORE Phase Complete → Proceed to PLAN
```

**Error Handling**:

1. **Context7 Failures**:
   - Unknown library: Skip with warning (not blocking)
   - Rate limit: Retry with exponential backoff (coordinated via Context7RateLimitCoordinator)
   - Timeout: Fall back to version comparison only
   - Service unavailable: Continue with local version checking

2. **File Parse Errors**:
   - Missing requirements.txt: Continue with import scanning
   - Invalid pyproject.toml: Log warning, skip file
   - Unparseable Python file: Skip file, continue
   - No dependency files: Skip modernization detection gracefully (pure stdlib project)

3. **Version Comparison Errors**:
   - Non-semantic versions: Use string comparison
   - Missing version info: Mark as "unknown"

4. **Project Type Errors** (NEW):
   - Non-Python project (JS, Go, Rust): Skip Python-specific detection
   - Pure stdlib project: No dependencies → skip modernization
   - Malformed dependency files: Log warning, skip file, continue with import scanning

### Test Strategy

**Happy Path**:
1. Project with outdated libraries → All detected and categorized
2. Breaking changes found → Proper P0/P1/P2 assignment
3. plan.md generated → Modernization Considerations section present

**Edge Cases**:
1. No dependency files → Import scanning only
2. Unknown libraries → Graceful skip with warning
3. Context7 rate limit → Exponential backoff, partial results
4. Malformed dependency files → Error logged, file skipped
5. Pure stdlib project → Skip modernization detection gracefully (NEW)
6. Non-Python project (JS, Go, Rust) → Skip Python-specific detection (NEW)
7. User opts out → Modernization section not added to plan.md (NEW)

**Integration Tests**:
1. EXPLORE phase → plan.md contains modernization section
2. User selects modernization option → IMPLEMENT phase uses modern patterns
3. User selects existing patterns → IMPLEMENT phase uses codebase patterns
4. Breaking changes detected → P0 priority (recommendation only, never blocks)
5. No dependencies detected → Modernization skipped, EXPLORE continues (NEW)
6. User opts out → No Modernization Considerations section in plan.md (NEW)

## Standards Compliance

**Python Standards** (from `P:\.claude\skills\code-python\SKILL.md`):
- Type hints for all function signatures
- `uv` for dependency management
- `ruff` for linting (line length 100)
- `mypy` for type checking

**CSF NIP Standards**:
- Hooks in `P:\.claude\hooks\` directory
- Skills in `P:\.claude\skills\code\` directory
- Tests in `P:\.claude\skills\code\tests\` directory
- Documentation in SKILL.md files

**Error Handling Standards**:
- No stderr output from hooks (use stdout)
- Graceful degradation (modernization detection failure doesn't block EXPLORE)
- Evidence-based findings (source URLs for all Context7 queries)
- **Non-blocking guarantee**: Modernization detection NEVER blocks EXPLORE phase, findings are recommendations only (NEW)
- User choice: Modernization section includes opt-out mechanism (NEW)

## Ramifications

### Impact on Existing Code

**Enhanced Files**:
1. `P:\.claude\skills\code\SKILL.md` - Add EXPLORE phase modernization detection
2. `P:\.claude\skills\code\plan.md` - Add Modernization Considerations section template

**New Files**:
1. `P:\.claude\skills\code\utils\modernization_detector.py` - Main detector class
2. `P:\.claude\skills\code\utils\library_scanner.py` - Import and dependency scanning
3. `P:\.claude\skills\code\utils\context7_client.py` - Context7 query wrapper
4. `P:\.claude\skills\code\utils\version_comparator.py` - Semantic versioning
5. `P:\.claude\skills\code\tests\test_modernization_detector.py` - Test suite

**No Breaking Changes**:
- Modernization detection is additive, not replacing existing behavior
- Default behavior unchanged (codebase patterns still used by default)
- User choice preserved via plan.md selection

### Migration Path

**Phase 1**: Add detection (no behavior change)
- EXPLORE phase detects modernization opportunities
- Findings logged but not shown to user

**Phase 2**: Add plan.md section (informational)
- Modernization Considerations section added
- User can see findings but default unchanged

**Phase 3**: Add user choice (opt-in modernization)
- User can select modernization in plan.md
- IMPLEMENT phase respects selection

**Rollback Strategy**:
- Remove Modernization Considerations section from plan.md template
- Comment out modernization detection in EXPLORE phase
- Delete new utility files
- No data migration required (no state changes)

## Implementation Plan

### Task Breakdown (3 Parallel Tracks)

#### Track 1: Library Detection & Version Analysis (Effort: M)

**T1-1**: Create `library_scanner.py` module
- File: `P:\.claude\skills\code\utils\library_scanner.py`
- Actions:
  - Implement `ImportScanner` class (AST-based import detection)
  - Implement `DependencyFileParser` class (requirements.txt, pyproject.toml)
  - Implement `LibraryDetector` orchestrator
- Acceptance Criteria:
  - [ ] Scans Python files for import statements
  - [ ] Parses requirements.txt with versions
  - [ ] Reads pyproject.toml dependencies
  - [ ] Handles missing files gracefully
  - [ ] Returns unified library list with versions
- Verification: `pytest tests/test_library_scanner.py`

**T1-2**: Create `version_comparator.py` module
- File: `P:\.claude\skills\code\utils\version_comparator.py`
- Actions:
  - Implement semantic version parsing
  - Implement MAJOR/MINOR/PATCH detection
  - Implement version comparison logic
- Acceptance Criteria:
  - [ ] Parses "1.2.3" → (MAJOR=1, MINOR=2, PATCH=3)
  - [ ] Detects MAJOR version updates (1.x → 2.x)
  - [ ] Handles non-semantic versions gracefully
  - [ ] Compares current vs latest versions
- Verification: `pytest tests/test_version_comparator.py`

#### Track 2: Context7 Breaking Change Detection (Effort: M)

**T2-1**: Create `context7_client.py` wrapper
- File: `P:\.claude\skills\code\utils\context7_client.py`
- Actions:
  - Implement `Context7Resolver` (resolve-library-id wrapper)
  - Implement `BreakingChangeDetector` (query-docs for changelogs)
  - Implement rate limit handling with exponential backoff
  - Implement result caching
- Acceptance Criteria:
  - [ ] Resolves library names to Context7 IDs
  - [ ] Queries breaking changes from changelogs
  - [ ] Handles rate limits with backoff
  - [ ] Caches results to avoid duplicate queries
  - [ ] Returns structured breaking change data
- Verification: `pytest tests/test_context7_client.py`

**T2-2**: Create priority scoring system
- File: `P:\.claude\skills\code\utils\priority_scorer.py`
- Actions:
  - Implement P0/P1/P2 categorization logic
  - Define scoring rules (security, performance, API changes)
  - Implement confidence scoring
  - **Document that priorities are RECOMMENDATIONS, never blocks** (NEW)
- Acceptance Criteria:
  - [ ] P0: Security vulnerabilities, breaking API changes
  - [ ] P1: Major performance improvements, deprecated features
  - [ ] P2: Minor improvements, cosmetic changes
  - [ ] Returns priority with confidence score
  - [ ] Documentation clarifies non-blocking nature (NEW)
- Verification: `pytest tests/test_priority_scorer.py`

**T2-3**: Create Context7 rate limit coordinator (NEW)
- File: `P:\.claude\skills\code\utils\context7_rate_limiter.py`
- Actions:
  - Implement shared rate limit tracker across all modernization tracks
  - Implement batch query optimization (group similar queries)
  - Implement result caching across projects
  - Handle rate limit exhaustion gracefully
- Acceptance Criteria:
  - [ ] Coordinates Context7 queries across Track 1, Track 2, existing EXPLORE agents
  - [ ] Batches queries to reduce API calls
  - [ ] Caches results to avoid duplicate queries for same library
  - [ ] Falls back to local version checking when rate limit hit
  - [ ] Never blocks EXPLORE phase due to rate limits
- Verification: `pytest tests/test_context7_rate_limiter.py`

#### Track 3: Plan Template Enhancement (Effort: M)

**T3-1**: Create modernization section generator
- File: `P:\.claude\skills\code\utils\modernization_section_generator.py`
- Actions:
  - Implement `ModernizationSectionGenerator` class
  - Format findings into markdown section
  - Generate recommendation options
- Acceptance Criteria:
  - [ ] Creates "Modernization Considerations" section
  - [ ] Lists detected divergences with priorities
  - [ ] Provides clear recommendation (existing vs modern)
  - [ ] Formats user choice options
  - [ ] Includes migration links (Context7 URLs)
- Verification: `pytest tests/test_modernization_section_generator.py`

**T3-2**: Integrate into EXPLORE phase
- File: `P:\.claude\skills\code\SKILL.md`
- Actions:
  - Update Phase 3 (EXPLORE) documentation
  - Add modernization detection workflow steps
  - Document new integration points
- Acceptance Criteria:
  - [ ] EXPLORE phase documentation includes modernization detection
  - [ ] Workflow steps clearly defined
  - [ ] Integration points documented
  - [ ] Error handling specified
- Verification: Manual review of SKILL.md

**T3-3**: Update plan.md template
- File: `P:\.claude\skills\code\plan.md`
- Actions:
  - Add "Modernization Considerations" section after Section 7
  - Create template with subsections
  - Add user choice checkboxes
  - **Add opt-out mechanism** (NEW)
- Acceptance Criteria:
  - [ ] New section present in template
  - [ ] Subsections: Detected Divergences, Recommendation, Your Choice
  - [ ] Clear format for listing findings
  - [ ] User choice mechanism defined
  - [ ] Opt-out checkbox: "Skip modernization detection for this project" (NEW)
- Verification: Visual inspection of plan.md

**T3-4**: Create user acknowledgment handler (NEW)
- File: `P:\.claude\skills\code\utils\user_optout_handler.py`
- Actions:
  - Implement `UserOptoutHandler` class
  - Detect user opt-out preference in plan.md
  - Skip Modernization Considerations section if user opts out
  - Persist opt-out preference per project (if user wants)
- Acceptance Criteria:
  - [ ] Detects opt-out checkbox in plan.md
  - [ ] Skips modernization section generation when opted out
  - [ ] Respects user choice without re-prompting
  - [ ] EXPLORE phase continues normally when opted out
- Verification: `pytest tests/test_user_optout_handler.py`

#### Track 4: Integration & Testing (Effort: L)

**T4-1**: Create integration test suite
- File: `P:\.claude\skills\code\tests\test_modernization_integration.py`
- Actions:
  - Test EXPLORE phase with modernization detection
  - Test plan.md generation
  - Test user choice handling
- Acceptance Criteria:
  - [ ] EXPLORE phase detects modernization opportunities
  - [ ] plan.md contains Modernization Considerations
  - [ ] User selection is respected in IMPLEMENT phase
  - [ ] Error cases handled gracefully
- Verification: `pytest tests/test_modernization_integration.py`

**T4-2**: Update documentation
- File: `P:\CODEBASE_CONSISTENCY_VS_MODERNIZATION.md`
- Actions:
  - Add implementation status section
  - Link to this plan
  - Document lessons learned
- Acceptance Criteria:
  - [ ] Implementation status documented
  - [ ] Plan reference added
  - [ ] Key learnings captured
- Verification: Manual review

### Execution Order

**Parallel Execution** (Tracks 1, 2, 3 can run simultaneously):
- Week 1: T1-1, T1-2, T2-1, T2-2, T2-3, T3-1, T3-2, T3-3, T3-4 (9 tasks in parallel)
- Week 2: T4-1, T4-2 (integration and testing)

**Dependencies**:
- T4-1 depends on: T1-1, T1-2, T2-1, T2-2, T2-3, T3-1, T3-4
- T4-2 depends on: All other tasks

## Risks, Success Criteria, Dependencies

### Top Risks

1. **Context7 Rate Limiting** (Severity: MEDIUM, Mitigation: IMPLEMENTED):
   - Risk: High query volume triggers rate limits
   - Mitigation: Exponential backoff, result caching, batch queries
   - Owner: Track 2 (T2-1)

2. **False Positive Breaking Changes** (Severity: LOW, Mitigation: IMPLEMENTED):
   - Risk: Context7 returns non-breaking changes as breaking
   - Mitigation: Confidence scoring, user verification in plan.md, **priorities are recommendations not blocks** (CLARIFIED)
   - Owner: Track 2 (T2-2)

3. **User Choice Paralysis** (Severity: LOW, Mitigation: IMPLEMENTED):
   - Risk: Too many modernization options overwhelm user
   - Mitigation: Clear recommendations, P0/P1/P2 prioritization, **opt-out mechanism** (ADDED)
   - Owner: Track 3 (T3-4)

4. **Context7 Race Condition** (Severity: LOW, Mitigation: IMPLEMENTED):
   - Risk: Multiple tracks hit Context7 simultaneously, causing rate limit exhaustion
   - Mitigation: **Shared rate limit coordinator (T2-3)**, batch queries, result caching (ADDED)
   - Owner: Track 2 (T2-3)

5. **No Dependencies Fallback** (Severity: LOW, Mitigation: IMPLEMENTED):
   - Risk: Pure stdlib projects or non-Python projects cause detection failures
   - Mitigation: **Graceful skip when no dependencies detected, project type detection** (ADDED)
   - Owner: Track 1 (T1-1)

### Success Criteria

**Functional Requirements**:
- [ ] EXPLORE phase automatically detects library version updates
- [ ] Context7 queries return breaking change information
- [ ] plan.md includes Modernization Considerations section (with opt-out option)
- [ ] P0/P1/P2 prioritization is accurate
- [ ] User can choose between existing and modern patterns
- [ ] User can opt-out of modernization section entirely
- [ ] IMPLEMENT phase respects user choice

**Non-Functional Requirements**:
- [ ] Modernization detection is NON-BLOCKING (never prevents EXPLORE from completing) (NEW)
- [ ] Context7 rate limits handled gracefully with shared coordinator
- [ ] Detection failures don't block EXPLORE phase (graceful degradation)
- [ ] Pure stdlib projects handled correctly (skip modernization) (NEW)
- [ ] Non-Python projects handled correctly (skip Python-specific detection) (NEW)
- [ ] 95%+ test coverage for new code

**Quality Requirements**:
- [ ] No stderr output from hooks (use stdout)
- [ ] All findings include source URLs
- [ ] Type hints on all functions
- [ ] Ruff linting passes
- [ ] Mypy type checking passes
- [ ] P0/P1/P2 priorities are recommendations, never blocks (NEW)

### Dependencies

**External Dependencies**:
- Context7 MCP server must be available and configured
- `mcp__plugin_context7_context7__resolve-library-id` tool enabled
- `mcp__plugin_context7_context7__query-docs` tool enabled

**Internal Dependencies**:
- `/code` skill EXPLORE phase implementation
- plan.md template structure
- Existing utility infrastructure (`P:\.claude\skills\code\utils\`)

**Tool Dependencies**:
- Python 3.12+
- `pytest` for testing
- `ruff` for linting
- `mypy` for type checking

**Data Dependencies**:
- None (no state files or databases)

## Rollback Strategy

**Immediate Rollback** (if critical bugs found):
1. Comment out modernization detection in EXPLORE phase
2. Remove Modernization Considerations from plan.md template
3. Keep utility files (can be re-enabled later)
4. No data migration required

**Graceful Degradation** (if Context7 unavailable):
1. Detect library versions locally (pip index)
2. Skip breaking change detection
3. Log warning, continue with version comparison only
4. Modernization section shows version updates only

**Complete Removal** (if feature not useful):
1. Delete new utility files
2. Revert SKILL.md changes
3. Revert plan.md template
4. No residual state or configuration
