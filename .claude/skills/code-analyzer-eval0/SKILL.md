---
name: code-analyzer-eval0
description: Analyzes code files and directories to extract structure, identify patterns, and provide insights using AI Distiller
version: 1.0.0
category: analysis
status: stable
triggers:
  - /code-analyzer-eval0
  - "analyze code"
  - "analyze this file"
  - "what does this code do"
  - "code analysis"
aliases:
  - /code-analyzer-eval0
  - /ca
suggest:
  - /critique
  - /search
  - /tdd
depends_on_skills: []
enforcement: advisory
workflow_steps:
  - identify_target: Identify the code file or directory to analyze
  - distill_code: Use AI Distiller to extract code structure
  - analyze_patterns: Identify patterns, dependencies, and architecture
  - summarize_findings: Provide actionable insights and recommendations
---

# /code-analyzer-eval0 — Code Analysis Skill

## Purpose

Analyze code files and directories to extract structure, identify patterns, and provide actionable insights. Uses AI Distiller for efficient code distillation and pattern detection.

## When to Use

- Understanding unfamiliar code
- Quick code review and pattern identification
- Finding dependencies and relationships
- Extracting code architecture

## Workflow

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

## Output Format

Use Template 2 (Executive Summary) for findings presentation.
