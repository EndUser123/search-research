# Review Bundle: github-ready

**Generated**: 2026-03-11
**Scope**: P:/packages/github-ready
**File Count**: 23 files
**Execution Mode**: Single agent (< 50 files)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

**github-ready** is a Universal Package Creator & Portfolio Polisher for Claude Code. It automates the creation of GitHub-ready Python packages, Claude skills, and Claude Code plugins with professional portfolio artifacts including badges, CI/CD workflows, test coverage metrics, architecture diagrams, explainer videos, and presentations.

**Target users**: Python developers, Claude Code users, open-source maintainers who need to quickly create professional, portfolio-quality packages with minimal manual configuration.

**Why critical**: Bridges the gap between writing code and publishing professional GitHub repositories. Automates time-consuming tasks like badge generation, CI/CD setup, documentation creation, and media asset generation. Essential for solo developers maintaining multiple packages who need consistent, professional repository presentation.

### Scale Metrics

- **Lines of Code**: ~100 LOC (core implementation)
- **Major subsystems**: 5
  - Plugin metadata (.claude-plugin/)
  - Core logic (core/)
  - Hook configuration (hooks/)
  - Test suite (tests/)
  - Documentation templates (templates/)
- **Deployment scope**: Claude Code plugin ecosystem
- **Change frequency**: Active development (v5.5.0 → v5.5.5 within 1 day)

### Your Environment

- **OS and shell**: Windows 11 (bash/PowerShell hybrid), Unix-compatible via bash
- **Primary languages and frameworks**:
  - Python 3.12+ (core implementation)
  - Claude Code Plugin API (.claude-plugin/plugin.json, hooks/hooks.json)
  - Mermaid diagrams (C4 architecture diagrams)
  - NotebookLM CLI v0.4.4+ (media asset generation)
- **Package managers and build tools**:
  - No package manager (Claude Code plugins don't use pip)
  - pytest for testing
  - ruff for linting
- **Databases or external services**:
  - NotebookLM (Google AI service) - explainer videos, diagrams, slides
  - OpenRouter (optional) - banner generation
  - GitHub Actions (CI/CD)

---

## 2. ARCHITECTURE OVERVIEW

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Invocation                             │
│                  /github-ready <package-name>                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Claude Code Plugin Layer                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ .claude-plugin/plugin.json (metadata)                      │ │
│  │ - name: "github-ready"                                     │ │
│  │ - description: Universal Package Creator & Portfolio Polisher│ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ hooks/hooks.json (trigger configuration)                   │ │
│  │ - UserPromptSubmit hook: matches package creation keywords│ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Logic Layer                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ core/__init__.py                                           │ │
│  │ - __version__ = "5.5.0"                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ core/main.py                                               │ │
│  │ - get_version() → returns version string                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Services Integration                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ NotebookLM   │  │  OpenRouter  │  │   GitHub Actions      │ │
│  │ (v0.4.4+)    │  │  (optional)  │  │   (CI/CD)             │ │
│  │ - Videos     │  │  - Banners    │  │  - Test workflows     │ │
│  │ - Diagrams   │  │              │  │  - Badges             │ │
│  │ - Slides     │  │              │  │  - Coverage reports   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. Plugin Metadata (.claude-plugin/)
- **Purpose**: Claude Code plugin registration and discovery
- **Files**: `.claude-plugin/plugin.json`
- **Main entry points**: Plugin name, description, author info
- **Dependencies**: Claude Code plugin system
- **Critical invariants**: Must follow Claude Code plugin v5.2+ structure

#### 2. Hook Configuration (hooks/)
- **Purpose**: Define when/how the plugin triggers
- **Files**: `hooks/hooks.json`
- **Main entry points**: UserPromptSubmit hook
- **Trigger pattern**: Matches "create|make|scaffold|generate.*(package|library|repo|plugin)"
- **Dependencies**: Claude Code hook system
- **Critical invariants**: Hook must not write to stderr (Claude Code treats stderr as errors)

#### 3. Core Logic (core/)
- **Purpose**: Version management and package functionality
- **Files**: `core/__init__.py`, `core/main.py`
- **Main entry points**: `get_version()` function
- **Dependencies**: None (minimal Python stdlib only)
- **Critical invariants**: Version must follow semantic versioning (MAJOR.MINOR.PATCH)

#### 4. Test Suite (tests/)
- **Purpose**: Verify core functionality
- **Files**: `tests/__init__.py`, `tests/test_main.py`
- **Main entry points**: `test_get_version()`, `test_version_format()`
- **Dependencies**: pytest framework
- **Critical invariants**: Tests must pass for CI/CD badge to show "passing"

#### 5. Documentation Templates (templates/, docs/)
- **Purpose**: Reusable templates for package artifacts
- **Files**: `templates/video-section-template.md`, `docs/diagrams/*.mmd`
- **Main entry points**: Markdown templates, Mermaid diagram definitions
- **Dependencies**: None (static templates)
- **Critical invariants**: C4 diagrams follow Mermaid C4 model syntax

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Trigger**: User types package creation keywords
```
User input → UserPromptSubmit hook → hooks.json pattern match → Trigger plugin
```

**Current implementation** (minimal):
```
User input → Hook matches pattern → Echo 'github-ready skill triggered'
```

**Note**: Core plugin logic is currently a stub. Actual package creation functionality is implemented via the `/package` skill in `P:/.claude/skills/package/SKILL.md` (external to this package).

### Mandatory Ordering Constraints

1. **Plugin registration** must happen before hook invocation
2. **Hook pattern matching** must complete before command execution
3. **Version check** (`get_version()`) must return valid semver string

### State Management

**State stores**: No persistent state stores
- Plugin metadata: Static (plugin.json)
- Version: Hardcoded in `core/__init__.py`
- Hook configuration: Static (hooks.json)

**State ownership**: None (stateless design)

**Consistency model**: No shared state, no concurrency issues

### Error Handling

**Fail-open vs fail-closed**: Fail-open
- Hook errors: Silent (command returns 0 even if plugin fails)
- Version errors: Returns "unknown" if version not available

**Retry/timeout behavior**: None implemented (no external API calls in current implementation)

---

## 4. COMPONENT INVENTORY

### Core Logic Components

#### core/__init__.py
- **Path**: `P:/packages/github-ready/core/__init__.py`
- **Key exports**: `__version__`
- **Responsibility**: Version definition and module documentation
- **Inputs**: None
- **Outputs**: Version string (semantic versioning)
- **Known limitations**: Version is hardcoded, must be manually updated

#### core/main.py
- **Path**: `P:/packages/github-ready/core/main.py`
- **Key functions**:
  - `get_version()`: Returns `__version__` from `core/__init__.py`
- **Responsibility**: Version retrieval API
- **Inputs**: None
- **Outputs**: String (version)
- **Known limitations**: Minimal functionality (wrapper around __version__)

### Configuration Components

#### .claude-plugin/plugin.json
- **Path**: `P:/packages/github-ready/.claude-plugin/plugin.json`
- **Key fields**:
  - `name`: "github-ready"
  - `description`: "Universal Package Creator & Portfolio Polisher..."
  - `author.name`: "Your Name"
  - `author.email`: "your.email@example.com"
- **Responsibility**: Plugin metadata for Claude Code discovery
- **Inputs**: None (static configuration)
- **Outputs**: Plugin registration
- **Known limitations**: Author fields are placeholders (not personalized)

#### hooks/hooks.json
- **Path**: `P:/packages/github-ready/hooks/hooks.json`
- **Key fields**:
  - `UserPromptSubmit`: Hook point
  - `matcher`: Regex pattern for package creation keywords
  - `hooks[].type`: "command"
  - `hooks[].command`: Shell command to execute
- **Responsibility**: Define when plugin triggers
- **Inputs**: User prompt text
- **Outputs**: Command execution
- **Known limitations**: Current command is stub (echo only)

### Test Components

#### tests/test_main.py
- **Path**: `P:/packages/github-ready/tests/test_main.py`
- **Key tests**:
  - `test_get_version()`: Verifies version retrieval
  - `test_version_format()`: Verifies semantic versioning format
- **Responsibility**: Verify core functionality
- **Inputs**: None
- **Outputs**: pytest pass/fail results
- **Known limitations**: Tests version only (no integration tests)

### Infrastructure Components

#### README.md
- **Path**: `P:/packages/github-ready/README.md`
- **Sections**: Installation, Features, Quick Start, Media Assets, Package Types
- **Responsibility**: User-facing documentation
- **Known limitations**: References interactive HTML diagram that may not exist

#### docs/diagrams/
- **Path**: `P:/packages/github-ready/docs/diagrams/`
- **Files**:
  - `c4_context.mmd`: System context diagram
  - `c4_containers.mmd`: Container diagram
  - `c4_components.mmd`: Component diagram
- **Responsibility**: Technical architecture documentation
- **Format**: Mermaid C4 model diagrams
- **Known limitations**: Static diagrams, not auto-generated

#### templates/video-section-template.md
- **Path**: `P:/packages/github-ready/templates/video-section-template.md`
- **Purpose**: Copy-paste template for README video sections
- **Responsibility**: Standardize media asset documentation
- **Known limitations**: Manual integration required

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Claude Code Plugin First**: Package is a Claude Code plugin, not a pip-installable Python library
2. **Minimal Core**: Core implementation is intentionally minimal (version management only)
3. **Skill-Based Logic**: Actual package creation logic lives in `/package` skill, not in Python code
4. **Portfolio Quality Output**: All generated packages must be GitHub-ready with badges, CI/CD, docs
5. **Multi-Format Support**: Supports Claude skills, Python libraries, and Claude Code plugins

### Technology Constraints

1. **No pyproject.toml**: Plugins don't need pip packaging
2. **No src/ directory**: Uses `core/` for Python code (Claude Code plugin convention)
3. **CLAUDE_PLUGIN_ROOT**: All paths must use this env var for portability
4. **Hook stderr forbidden**: Hooks must never write to stderr (Claude Code treats as errors)

### Performance SLAs

- **Plugin load time**: < 1 second (minimal code)
- **Hook trigger time**: < 100ms (pattern match only)
- **Version retrieval**: < 10ms (simple variable access)

### Things That Must NOT Change

1. **Plugin structure**: `.claude-plugin/`, `core/`, `hooks/` directories are mandatory
2. **Semantic versioning**: Version must always be MAJOR.MINOR.PATCH format
3. **Hook stderr prohibition**: Hooks must never write to stderr
4. **Plugin.json format**: Must follow Claude Code plugin v5.2+ structure
5. **Three deployment models**: SKILLS (junction), HOOKS (symlinks), PLUGINS (/plugin command)

---

## 6. KNOWN ISSUES

### Issue 1: Core Implementation is Stub

**Scenario**: Plugin triggers but doesn't actually create packages

**Expected**: Plugin executes package creation logic when user types creation keywords

**Actual**: Plugin only echoes "github-ready skill triggered" - no actual functionality

**Impact**: HIGH - Core plugin functionality is not implemented in Python code

**Current workaround**: Use `/package` skill directly (bypasses plugin entirely)

**Root cause**: Design decision - actual logic lives in `/package` skill at `P:/.claude/skills/package/SKILL.md`

---

### Issue 2: Author Fields are Placeholders

**Scenario**: plugin.json contains placeholder author information

**Expected**: Real author name and email

**Actual**: "Your Name" and "your.email@example.com"

**Impact**: LOW - Cosmetic only, doesn't affect functionality

**Current workaround**: Manually edit plugin.json after installation

**Root cause**: Template scaffolding hasn't been personalized

---

### Issue 3: Version Mismatch

**Scenario**: README.md says v5.5.5, core/__init__.py says v5.5.0

**Expected**: Version numbers should match across all files

**Actual**: Version inconsistency between README and source code

**Impact**: MEDIUM - Confuses users about which version is installed

**Current workaround**: Update core/__init__.py to match README

**Root cause**: Manual version updates not synchronized across files

---

### Issue 4: Missing Interactive Diagram

**Scenario**: README references `docs/github-ready-architecture.html`

**Expected**: Interactive HTML diagram with clickable Mermaid flowchart

**Actual**: File doesn't exist (only static .mmd files in docs/diagrams/)

**Impact**: LOW - Documentation link is broken

**Current workaround**: Remove the link or generate the HTML diagram

**Root cause**: Diagram generation workflow not complete

---

### Issue 5: Media Assets May Not Exist

**Scenario**: README references `assets/infographics/github-ready_architecture.png`

**Expected**: NotebookLM-generated architecture diagram

**Actual**: File may or may not exist (media generation is optional)

**Impact**: LOW - Broken image link if assets not generated

**Current workaround**: Use `--skip media` flag or remove media section from README

**Root cause**: Media assets require NotebookLM integration, which is optional

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### 1. Hook Extension Points

**Location**: `hooks/hooks.json`

**Add new hooks** by extending the JSON structure:
```json
{
  "UserPromptSubmit": [...],
  "NEW_HOOK_POINT": [{
    "matcher": "pattern",
    "hooks": [{"type": "command", "command": "command"}]
  }]
}
```

**Available hook points**: See Claude Code hooks documentation

---

#### 2. Core Logic Extension

**Location**: `core/main.py`

**Add new functions** following this pattern:
```python
def new_function():
    """Documentation string."""
    # Implementation
    return result
```

**Export requirements**: Add to `core/__init__.py` if part of public API

---

#### 3. Skill Integration

**Location**: `P:/.claude/skills/package/SKILL.md` (external)

**This package is the IMPLEMENTATION** of the `/package` skill

**Skill contract**:
- **Skill reads plugin metadata** from `.claude-plugin/plugin.json`
- **Skill triggers hook** via pattern matching in `hooks/hooks.json`
- **Skill uses version** from `core/main.py:get_version()`
- **Skill generates artifacts** using NotebookLM CLI and other tools

**Invocation model**:
```bash
/package <package-name>
# → Skill reads this package's metadata
# → Skill executes package creation workflow
# → Skill reports results
```

---

#### 4. External Service Integration

**NotebookLM CLI** (v0.4.4+):
- **Purpose**: Generate media assets (videos, diagrams, slides)
- **Invocation**: `nlm notebook create`, `nlm source add`, `nlm video create`
- **Data exchange**: Upload source files → Download generated assets
- **Error handling**: Retry on timeout, fail gracefully if service unavailable

**OpenRouter** (optional):
- **Purpose**: Generate banner images
- **Invocation**: HTTP API with OPENROUTER_API_KEY
- **Data exchange**: Prompt → Image URL
- **Error handling**: Fail gracefully if API key not set

**GitHub Actions**:
- **Purpose**: CI/CD workflows for generated packages
- **Trigger**: Push to main branch
- **Workflows**: `.github/workflows/test.yml`
- **Output**: Test badges, coverage reports

---

### Data Exchange Contracts

**Hook → Plugin**:
- **Input**: User prompt text (string)
- **Output**: Command execution result (stdout/stderr)
- **Constraint**: stderr must be empty (Claude Code treats as error)

**Plugin → Skill**:
- **Input**: Plugin metadata (plugin.json), version (core/main.py)
- **Output**: Package artifacts (directories, files)
- **Constraint**: Must follow Claude Code plugin structure conventions

**Skill → NotebookLM**:
- **Input**: Source files (Python, markdown, JSON)
- **Output**: Media assets (MP4, PNG, PDF)
- **Constraint**: Must use `nlm` CLI v0.4.4+ syntax

**Skill → Generated Package**:
- **Input**: Package name, type (detected from structure)
- **Output**: Complete package structure with all artifacts
- **Constraint**: Must include badges, CI/CD, README, tests

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample Run: Version Check

```bash
$ python -c "from core.main import get_version; print(get_version())"
5.5.0
```

**Expected**: Version string in semantic versioning format
**Actual**: "5.5.0" ✓

---

### Sample Run: Test Suite

```bash
$ pytest tests/test_main.py -v
========================= test session starts ==========================
platform win32 -- Python 3.12.1, pytest-8.3.4
collected 2 items

tests/test_main.py::test_get_version PASSED                           [ 50%]
tests/test_main.py::test_version_format PASSED                        [100%]

========================= 2 passed in 0.12s ===========================
```

**Expected**: 2 tests passing
**Actual**: 2 passed ✓

---

### Sample Run: Hook Trigger (Current Stub)

```bash
# User types: "create a package called mylib"
# Hook pattern matches: "create.*package"
# Command executes:
$ echo 'github-ready skill triggered'
github-ready skill triggered
```

**Expected**: Package creation logic executes
**Actual**: Only echo message (stub)

**Note**: This is expected behavior - actual logic in `/package` skill

---

### Sample Run: Plugin Metadata Validation

```bash
$ cat .claude-plugin/plugin.json | jq .
{
  "name": "github-ready",
  "description": "Universal Package Creator & Portfolio Polisher...",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

**Expected**: Valid JSON with required fields
**Actual**: Valid JSON ✓

**Note**: Author fields are placeholders (known issue)

---

## END OF REVIEW BUNDLE

**Summary**: github-ready is a Claude Code plugin (v5.5.0) that provides metadata and hook configuration for the `/package` skill. The plugin itself is intentionally minimal - the actual package creation logic lives in the external `/package` skill at `P:/.claude/skills/package/SKILL.md`. Key integration points are the hook system (UserPromptSubmit), version API (get_version()), and plugin metadata structure. Known issues include stub implementation (by design), placeholder author fields, version mismatches, and missing optional media assets.
