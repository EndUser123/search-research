# Learning & Patterns: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Step**: 12 (Learning)

## Technical Learnings

### 1. ast-grep Pattern Syntax Duality

**Discovery**: ast-grep has two fundamentally different pattern syntaxes:

**YAML Rule Files**:
- Supports variables: `$VAR`, `$$ARGS`
- Supports negation: `!await`
- Supports multi-line patterns with structural matching
- Used in: `sgconfig.yml`, rule files
- Example:
  ```yaml
  pattern: |
    try:
      $BODY
    except:
      $HANDLER
  ```

**CLI -p Flag**:
- Simple string patterns only
- Limited wildcards: `$` for single token
- No structural matching
- Used in: `ast-grep run -p "pattern"`
- Example:
  ```bash
  ast-grep run -l python -p "except:"
  ```

**Lesson**: When writing patterns for CLI use, keep them simple. Complex patterns belong in YAML rule files.

### 2. Graceful Degradation Pattern

**Pattern Used**:

```python
# Import with fallback
try:
    from code_intelligence.integration import CodeIntelligenceExplorer
    CODE_INTEL_AVAILABLE = True
except ImportError as e:
    print(f"[EXPLORER] Code Intelligence integration not available: {e}")
    CODE_INTEL_AVAILABLE = False
    CodeIntelligenceExplorer = None

# Conditional initialization
if CODE_INTEL_AVAILABLE and CodeIntelligenceExplorer:
    self.code_intelligence_explorer = CodeIntelligenceExplorer(config)
else:
    self.code_intelligence_explorer = None
```

**Benefits**:
- System continues working even if tools unavailable
- Clear error messages for debugging
- Feature flags easy to add

**Applicable To**:
- Optional dependencies
- Feature flags
- Multi-environment deployments

### 3. Pattern Library as Code

**Pattern Used**:

```python
class PatternLibrary:
    PYTHON_PATTERNS = {
        "pattern_id": {
            "pattern": "cli-pattern",
            "severity": Severity.ERROR,
            "message": "Human-readable",
            "fix": "suggested fix"
        }
    }
```

**Benefits**:
- Version controlled alongside code
- Easy to add/remove patterns
- Self-documenting
- Type-safe (can be validated)

**Applicable To**:
- Code quality rules
- Validation rules
- Search patterns

## Process Learnings

### 1. CWO12 Workflow Effectiveness

**What Worked Well**:
- Structured approach prevented missed steps
- Quality gates caught issues early
- Documentation captured knowledge
- Task tracking provided visibility

**Improvements for Next Time**:
- Start CWO12 before implementation (this was retrospective)
- Add automated testing in quality gate
- Include performance benchmarks

### 2. Testing Strategy

**Manual Testing Proved Effective**:
- Quick feedback loop
- Easy to reproduce issues
- Caught pattern syntax problems early

**Opportunities**:
- Add pytest test suite
- Automate health check validation
- Add pattern regression tests

### 3. Documentation Strategy

**What Worked**:
- Separate documents for different audiences (users, developers)
- Architecture diagrams for context
- Code examples for understanding

**Improvements**:
- Add API documentation generation
- Include more troubleshooting examples
- Add video tutorials for complex features

## Patterns to Reuse

### 1. Tool Health Check Pattern

```python
def check_tool_health() -> dict:
    """Check availability of all tools"""
    tools = {}
    for tool_name, tool_check in tool_checks.items():
        try:
            available = tool_check()
            tools[tool_name] = {"available": available}
        except Exception as e:
            tools[tool_name] = {"available": False, "error": str(e)}

    return {
        "tools": tools,
        "available": sum(1 for t in tools.values() if t["available"]),
        "total": len(tools)
    }
```

### 2. Configuration Validation Pattern

```python
def validate_config(config: dict) -> tuple[bool, list[str]]:
    """Validate configuration, return (valid, errors)"""
    errors = []

    required_keys = ["project_path", "enable_lsp", "enable_ast_grep"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    return len(errors) == 0, errors
```

### 3. Async Interface Pattern

```python
class Explorer:
    async def explore(self, query: str, options: dict) -> dict:
        """Main exploration interface"""
        results = {}

        # Run searches concurrently
        tasks = [
            self._lsp_search(query, options.get("path")),
            self._pattern_search(query, options.get("path")),
            self._graph_search(query, options)
        ]

        outputs = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for i, output in enumerate(outputs):
            if not isinstance(output, Exception):
                results.update(output)

        return results
```

## Anti-Patterns to Avoid

### 1. YAML Pattern Syntax in CLI

**Don't**:
```python
"bare_except": {
    "pattern": "try:\n    $BODY\nexcept:\n    $HANDLER"  # YAML syntax
}
```

**Do**:
```python
"bare_except": {
    "pattern": "except:"  # CLI syntax
}
```

### 2. Hard-Coded Paths

**Don't**:
```python
config_path = "P:/__csf.nip/config.json"
```

**Do**:
```python
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
config_path = project_root / "config.json"
```

### 3. Silent Failures

**Don't**:
```python
try:
    initialize_tool()
except:
    pass  # Silent failure
```

**Do**:
```python
try:
    initialize_tool()
except Exception as e:
    logger.warning(f"Tool initialization failed: {e}")
    self.tool_available = False  # Track state
```

## Knowledge Graph Connections

This work connects to:
- **CKS (Knowledge Storage)**: Stores discovery results
- **CWO12 (Workflow)**: Uses CWO12 process
- **Code Intelligence**: LSP, ast-grep, graph database
- **Quality Assurance**: Quality gate validation

## Recommendations for Future Work

### Short Term
1. Add automated unit tests
2. Replace print statements with logging module
3. Add performance benchmarks

### Medium Term
1. Add YAML rule file support for complex patterns
2. Implement pattern result caching
3. Add custom pattern definition UI

### Long Term
1. Machine learning for pattern suggestion
2. Integration with CI/CD pipelines
3. Pattern marketplace for sharing

## Team Insights

### For Developers
- "Keep patterns simple for CLI, complex for YAML files"
- "Always implement graceful fallback for optional features"
- "Test patterns against real code, not just syntax"

### For Maintainers
- "CWO12 workflow is effective for retrospective documentation"
- "Health checks are essential for multi-tool systems"
- "Documentation is as important as code"

### For Users
- "Use /discover for code exploration, not just search"
- "Check tool health before relying on specific features"
- "Report pattern false positives to improve quality"

---

**Document Version**: 1.0
**Last Updated**: 2025-12-24
**Author**: CWO12 Workflow
