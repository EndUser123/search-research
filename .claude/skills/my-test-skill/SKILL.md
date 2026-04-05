---
name: my-test-skill
description: Analyze code files and provide summary statistics including line counts, file types, and basic code metrics
version: 1.0.0
status: stable
category: analysis
triggers:
  - /my-test-skill
  - "code statistics"
  - "file analysis"
aliases:
  - /my-test-skill
  - /mts
suggest:
  - /similarity
  - /code-review
depends_on_skills: []
workflow_steps:
  - discover_files: Use Glob to find all files in the target path
  - read_content: Read file contents using the Read tool
  - count_lines: Count total lines, code lines, comment lines, and blank lines per file
  - categorize_by_type: Group files by extension and calculate statistics per type
  - report_summary: Present summary statistics in a structured format
enforcement: advisory
---

# Code Analysis Skill

## Purpose

Analyzes code files and provides summary statistics including line counts, file type distribution, and basic code metrics.

## When to Use

- When you need to understand the size and structure of a codebase
- Before refactoring or reviewing code
- When assessing project complexity
- When comparing different codebases or modules

## How to Use

**Command:**
```
/my-test-skill <path>
```

**Or describe what to analyze:**
```
Analyze the code in P:/some/path
Give me statistics about this codebase
```

## Workflow

1. **Discover Files**: Use Glob to find all files in the target path
2. **Read Content**: Read file contents using the Read tool
3. **Count Lines**: Count total lines, code lines, comment lines, and blank lines per file
4. **Categorize by Type**: Group files by extension and calculate statistics per type
5. **Report Summary**: Present summary statistics in a structured format

## Output Format

The skill provides:
- **Total Files**: Number of files analyzed
- **Total Lines**: Combined line count across all files
- **Breakdown by Type**: File count and line count per extension
- **Largest Files**: Top files by line count

## Examples

**Example 1: Analyze a directory**
```
/my-test-skill P:/some/project/src
```

**Example 2: Get code statistics**
```
Give me statistics about the codebase in P:/some/path
```

## Technical Details

- Uses Glob to discover files recursively
- Uses Read tool to read file contents
- Filters by common code file extensions (.py, .js, .ts, .md, etc.)
- Calculates blank lines, comment lines, and code lines where applicable
- Outputs structured summary for easy consumption

## Notes

- Analysis is read-only (no modifications to files)
- Large codebases may take longer to analyze
- Binary files are skipped during analysis
