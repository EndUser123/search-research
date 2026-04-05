# Architecture: Hybrid Semgrep + ESLint + Orchestrator

## System Context

```
┌────────────────────────────────────────────────────────┐
│         File Changed (Python or TypeScript)            │
└──────────────────────┬─────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼─────┐               ┌──────▼────┐
   │  Python  │               │TypeScript │
   │  (.py)   │               │(.ts, .tsx)│
   └────┬─────┘               └──────┬────┘
        │                            │
   ┌────▼──────────────┐    ┌───────▼──────────────┐
   │  Semgrep          │    │  ESLint              │
   │  .semgrep.yml     │    │  .eslintrc.json      │
   │  --autofix        │    │  --fix               │
   └────┬──────────────┘    └───────┬──────────────┘
        │                           │
        └───────────┬───────────────┘
                    │
        ┌───────────▼──────────────┐
        │  Orchestrator            │
        │  (orchestrator.py)       │
        │  - Normalize formats     │
        │  - De-duplicate          │
        │  - Report violations     │
        │  - Verify all fixed      │
        └───────────┬──────────────┘
                    │
        ┌───────────▼──────────────┐
        │  unified_analyzer        │
        │  (integration point)     │
        └───────────┬──────────────┘
                    │
        ┌───────────▼──────────────┐
        │  Claude Fallback         │
        │  (semantic violations)   │
        └──────────────────────────┘
```

## Configuration Files (Project Root)

```
P:/__csf.nip/
├── .semgrep.yml              # Python rules
├── .eslintrc.json            # TypeScript rules
├── src/
│   ├── quality/
│   │   ├── orchestrator.py   # Coordination engine
│   │   ├── unified_analyzer.py
│   │   └── claude_fallback.py # Optional semantic handler
│   └── ...
└── ...
```

## Why NOT CKS Storage

**Decision:** Use project files instead of CKS database for rule storage.

**Rationale:**
| Project Files | CKS Storage |
|---------------|-------------|
| No JSON escaping | YAML escaped in JSON |
| File I/O ~1ms | DB query ~50ms |
| Git history | Separate DB backups |
| `cat .semgrep.yml` | Connect to DB, query, parse JSON |
| Copy to other projects | Export/import scripts |

**When CKS would be right:**
- Approval workflow needed
- Feature flags required
- Environment-specific rules
- Multi-tenant (different rules per customer)

**Your requirements:** None of the above → **Project files optimal**

## Component Design

### 1. ViolationOrchestrator (New Class)

```python
class ViolationOrchestrator:
    """Run Semgrep + ESLint and aggregate results"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()

    def detect_and_fix(self, changed_files: List[Path]) -> Dict:
        """Run both tools, auto-fix, return results"""

    def _run_semgrep(self, files: List[Path]) -> Dict:
        """Run Semgrep with auto-fix"""

    def _run_eslint(self, files: List[Path]) -> Dict:
        """Run ESLint with auto-fix"""

    def verify_all_fixed(self) -> Dict:
        """Re-run both tools to verify all violations resolved"""
```

### 2. unified_analyzer Integration

```python
class UnifiedAnalyzer:
    # ... existing code ...

    def analyze_orchestrator(self, target: str) -> Dict:
        """New method: Run orchestrator for both languages"""
        orch = ViolationOrchestrator(Path(target))
        return orch.detect_and_fix(list(Path(target).rglob("*")))
```

## Data Flow

```
1. FILE DETECTION
   .py files → Python bucket
   .ts/.tsx files → TypeScript bucket

2. RUN SEMGREP (Python)
   semgrep --config=.semgrep.yml --autofix --json *.py
   → {results: [...], errors: []}

3. RUN ESLINT (TypeScript)
   eslint --config=.eslintrc.json --fix --format=json *.ts
   → [{messages: [...]}]

4. AGGREGATE RESULTS
   {
     "python": {detected: N, violations: [...]},
     "typescript": {detected: M, violations: [...]},
     "total": N + M
   }

5. VERIFY
   Re-run both tools without --autofix
   → {all_fixed: true/false}

6. FALLBACK (if violations remain)
   Generate Claude Code prompts for semantic violations
```

## Error Handling

| Error Type | Detection | Handling |
|------------|-----------|----------|
| Semgrep not installed | FileNotFoundError | Log warning, return empty Python results |
| ESLint not installed | FileNotFoundError | Log warning, return empty TS results |
| Config file missing | Path.exists() check | Log error, return empty results |
| Subprocess fails | returncode > 1 | Log stderr, return error in results |
| JSON parse fails | json.JSONDecodeError | Log error, skip this file |

## Integration Points

| Component | Integration Type | Contract |
|-----------|------------------|----------|
| .semgrep.yml | File read | YAML config for Python rules |
| .eslintrc.json | File read | JSON config for TS rules |
| unified_analyzer | Method addition | New `analyze_orchestrator()` method |
| Semgrep CLI | Subprocess | --config, --json, --autofix flags |
| ESLint CLI | Subprocess | --config, --fix, --format=json flags |
| claude_fallback | Optional | Generate prompts for semantic violations |

## Security Considerations

1. **Command Injection**: Use list argument to subprocess, not string concatenation
2. **Path Traversal**: Validate target path is within project
3. **Config Injection**: Validate YAML/JSON before running tools

## Performance

| Operation | Expected Time | Optimization |
|-----------|---------------|--------------|
| Read config files | <1ms | File system cache |
| Semgrep run | <500ms | Per-file caching |
| ESLint run | <200ms | Per-file caching |
| Verification | <700ms | Skip in fast mode |

Total: ~1.2 seconds for full scan with both languages
