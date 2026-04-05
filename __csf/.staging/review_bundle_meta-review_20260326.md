# Review Bundle: /meta-review Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/meta-review/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: meta-review
- **Description**: Cross-file meta-review system for Python packages with security, performance, and quality analysis
- **Category**: execution
- **Trigger**: /meta-review
- **Enforcement**: advisory

### Domain & Purpose
Comprehensive cross-file analysis for Python packages that goes beyond single-file reviews. Detects architectural issues like circular dependencies, path traversal vulnerabilities, documentation inconsistencies, and import-time side effects.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: `/package`, `/p`, code analyzers

---

## 2. PERSPECTIVES

| Perspective | Analyzers | Detects |
|-------------|------------|----------|
| `security` | path_traversal | Path traversal via user input, bypass techniques |
| `performance` | import_graph | Circular deps, disk I/O at import, side effects |
| `quality` | doc_consistency | Missing docstrings, outdated docs |
| `architecture` | import_graph | Layering violations, circular dependencies |
| `all` | All analyzers | Comprehensive analysis |

---

## 3. ANALYZERS

### Path Traversal Analyzer (Security)
Detects path traversal via user input with taint propagation.

### Import Graph Analyzer (Architecture/Performance)
Detects:
- Circular dependencies
- Layering violations
- Disk I/O at import time
- Module-level side effects

### Doc Consistency Analyzer (Quality)
Detects:
- Missing docstrings
- Outdated documentation

---

## 4. INTEGRATION

### `/package` PHASE 4.5
Meta-review is automatically integrated into `/package` validation.

### `/p` PHASE 4.5
Meta-review is also integrated into `/p` Python package validation.

---

## 5. OUTPUT FORMAT

```json
{
  "context": "# Meta-Review Analysis: mypackage\n...",
  "findings": [
    {
      "analyzer": "path_traversal",
      "type": "taint_flow",
      "severity": "HIGH",
      "message": "User input flows to filesystem sink without validation",
      "file_path": "src/handler.py"
    }
  ],
  "token_usage": {
    "budget": 8000,
    "used": 2341,
    "remaining": 5659
  }
}
```

---

## 6. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | EXCELLENT | 312-line SKILL.md |
| Cross-File Analysis | EXCELLENT | Multi-analyzer framework |

### SQA Relevance
- **HIGH** — Meta-review skill
- Cross-file architectural analysis
- Path traversal detection with taint propagation
- Import graph for circular dependency detection
- Doc consistency checking
- Perspective-based analysis (security, performance, quality, architecture)
