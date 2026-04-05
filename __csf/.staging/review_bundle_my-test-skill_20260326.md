# Review Bundle: /my-test-skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/my-test-skill/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: my-test-skill
- **Description**: Analyze code files and provide summary statistics including line counts, file types, and basic code metrics
- **Version**: 1.0.0
- **Category**: analysis
- **Trigger**: /my-test-skill, "analyze code", "code statistics", "file analysis"
- **Aliases**: /my-test-skill, /mts

### Domain & Purpose
Analyzes code files and provides summary statistics including line counts, file type distribution, and basic code metrics.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Glob, Read tools

---

## 2. WORKFLOW

1. **Discover Files**: Use Glob to find all files in the target path
2. **Read Content**: Read file contents using the Read tool
3. **Count Lines**: Count total lines, code lines, comment lines, and blank lines per file
4. **Categorize by Type**: Group files by extension and calculate statistics per type
5. **Report Summary**: Present summary statistics in a structured format

---

## 3. OUTPUT FORMAT

The skill provides:
- **Total Files**: Number of files analyzed
- **Total Lines**: Combined line count across all files
- **Breakdown by Type**: File count and line count per extension
- **Largest Files**: Top files by line count

---

## 4. USAGE

```bash
# Analyze a directory
/my-test-skill P:/some/project/src

# Get code statistics
Analyze the code in P:/some/path
```

---

## 5. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 94-line SKILL.md |
| Code Analysis | GOOD | Basic metrics |

### SQA Relevance
- **LOW** — Code analysis/statistics skill
- Line count analysis
- File type categorization
- Basic code metrics
