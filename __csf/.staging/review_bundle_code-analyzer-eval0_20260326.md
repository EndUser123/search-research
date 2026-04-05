# Review Bundle: /code-analyzer-eval0 Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/code-analyzer-eval0/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: code-analyzer-eval0
- **Description**: Analyzes code files and directories to extract structure, identify patterns, and provide insights using AI Distiller
- **Version**: 1.0.0
- **Category**: analysis
- **Trigger**: /code-analyzer-eval0, "analyze code", "analyze this file", "what does this code do", "code analysis"
- **Aliases**: /code-analyzer-eval0, /ca

### Domain & Purpose
Analyzes code files and directories to extract structure, identify patterns, and provide actionable insights. Uses AI Distiller for efficient code distillation and pattern detection.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: AI Distiller, /critique, /search, /tdd

---

## 2. WORKFLOW

### Step 1: Identify Target
Determine the file or directory to analyze:
- Single file: Use absolute path
- Directory: Analyze all relevant files recursively

### Step 2: Distill Code
Use AI Distiller to extract code structure:
- `distill_file`: For single file analysis
- `distill_directory`: For directory-wide analysis

### Step 3: Analyze Patterns
Identify:
- Function/class definitions
- Import dependencies
- Code patterns (async/await, decorators, etc.)
- Architecture indicators

### Step 4: Summarize Findings
Provide structured insights:
- Key components identified
- Dependencies and relationships
- Potential issues or improvements
- Recommendations for further analysis

---

## 3. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 74-line SKILL.md |
| Code Analysis | EXCELLENT | AI Distiller integration |

### SQA Relevance
- **MEDIUM** — Code analysis skill
- Pattern detection and dependency analysis
- AI Distiller for efficient code distillation
- Useful for code review and understanding
