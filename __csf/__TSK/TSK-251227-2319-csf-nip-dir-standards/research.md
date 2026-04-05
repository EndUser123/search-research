# Research Intelligence: CSF NIP Directory Standards

## Existing Infrastructure Analysis

### PathValidator Architecture

The existing `PathValidator` class in `P:/.claude/hooks/path_validator.py` provides a solid foundation:

**Key Classes:**
- `DirectoryPolicy`: Loads and provides access to `directory_policy.json` (single source of truth)
- `PathValidator`: Validates paths against policy using `is_path_safe(file_path) -> (is_safe, violation_type)`

**Policy Structure** (already has `csf_nip_directory` section):
```json
{
  "csf_nip_directory": {
    "allowed_subdirectories": [...],
    "allowed_root_files": [...],
    "blocked_root_patterns": [...]
  }
}
```

**Current Policy Coverage** (from directory_policy.json):

| Category | Count | Examples |
|----------|-------|----------|
| Allowed subdirectories | 18 | src, commands, config, data, docs, tests, scripts, tools, reports, logs, .staging, .speckit, backups, research, examples, external-tools, plans, production, exports |
| Blocked root patterns | 14 | test_*.py, *_test.py, *_report*.json, *.log, *.db, fix_*.py, clean_*.py, simple_*.py, *_report.md, *_deployment*.md |
| Allowed root files | 11 | pyproject.toml, requirements.txt, .env, pytest.ini, mypy.ini, .gitignore, .pre-commit-config.yaml, .python-version |

### Current Gap

**51 directories exist, but only 18 are explicitly allowed in policy:**

| Status | Count | Examples |
|--------|-------|----------|
| **Explicitly allowed** | 18 | src, commands, config, data, docs, tests, scripts, tools, reports, logs, .staging, .speckit, backups, research, examples, external-tools, plans, production, exports |
| **Not in policy (need categorization)** | 33+ | diag, deployment-test, knowledge_store, models, root, tsk, .aid, .archived, .cks, .cache, .evidence, .github, .mypy_cache, .ruff_cache, .sl, .taskmaster, .venv, logs_backup, .data, model_cache, __csf.nip (nested), deployment, migrations, monitoring |

### Consolidation Opportunities

**Duplicates identified:**

| Sources | Target | Files to move |
|---------|--------|---------------|
| `.data/` + `model_cache/` | `data/` | TBD (scan needed) |
| `logs_backup/` | `logs/` | TBD (scan needed) |

**Questionable directories requiring manual review:**

| Directory | Recommendation | Rationale |
|-----------|----------------|-----------|
| `__csf.nip/__csf.nip/` | Remove | Accidental nesting |
| `root/` | Evaluate | Unclear purpose, possibly legacy |
| `diag/` | Keep or merge | Diagnostic outputs, consider merging with monitoring/ |
| `models/` | Merge to data/ | ML models are data files |
| `deployment-test/` | Keep | Deployment testing environment |
| `knowledge_store/` | Evaluate | May duplicate CKS functionality |
| `production/` | Keep | Production artifacts |
| `migrations/` | Add to policy | Database migrations - valid but not listed |
| `monitoring/` | Add to policy | Monitoring outputs - valid but not listed |

## Extension Strategy

### Option A: Extend Existing Policy (RECOMMENDED)

Add missing directories to `directory_policy.json`:

```json
{
  "csf_nip_directory": {
    "allowed_hidden_directories": [
      {"path": ".cache", "purpose": "Cache files"},
      {"path": ".cks", "purpose": "CKS data"},
      {"path": ".venv", "purpose": "Python virtual environment"},
      {"path": ".speckit", "purpose": "Speckit registry"},
      {"path": ".staging", "purpose": "Temporary work area"},
      {"path": ".archived", "purpose": "Archived items"},
      {"path": ".taskmaster", "purpose": "Task management"},
      {"path": ".aid", "purpose": "AI assistance data"},
      {"path": ".evidence", "purpose": "Evidence tracking"},
      {"path": ".ruff_cache", "purpose": "Ruff cache"},
      {"path": ".mypy_cache", "purpose": "MyPy cache"},
      {"path": ".sl", "purpose": "Sapling data"},
      {"path": ".github", "purpose": "GitHub integration"}
    ],
    "allowed_operational_directories": [
      {"path": "migrations", "purpose": "Database migrations"},
      {"path": "monitoring", "purpose": "System monitoring"},
      {"path": "diag", "purpose": "Diagnostic outputs"}
    ],
    "consolidation_rules": [
      {
        "sources": [".data", "model_cache"],
        "target": "data",
        "strategy": "move",
        "priority": "HIGH"
      },
      {
        "sources": ["logs_backup"],
        "target": "logs",
        "strategy": "merge",
        "priority": "HIGH"
      }
    ]
  }
}
```

**Pros:**
- Single source of truth maintained
- No duplicate infrastructure
- Leverages existing PathValidator

**Cons:**
- Policy file grows larger

### Option B: Separate Policy File

Create `__csf.nip_directory_policy.json` that imports/extends base policy.

**Pros:**
- Separation of concerns
- Can evolve independently

**Cons:**
- Duplicate loading logic
- Potential for drift between policies

### Recommendation: Option A

Extend `directory_policy.json` in place with:
1. New `allowed_hidden_directories` section
2. New `allowed_operational_directories` section
3. New `consolidation_rules` section

## Interactive Approval Design

### Workflow

```
User creates: P:/__csf.nip/new_dir/file.py
                        ↓
    deny_root_write.py hook intercepts
                        ↓
    PathValidator.is_path_safe() returns (False, "UNKNOWN_DIR")
                        ↓
    csf_nip_deny_violations.py handles violation
                        ↓
    ┌─────────────────────────────────────┐
    │ Violation: Unknown directory       │
    │ Path: P:/__csf.nip/new_dir/file.py │
    │                                    │
    │ Options:                           │
    │ [1] Approve & add to policy        │
    │ [2] Suggest correct location       │
    │ [3] Deny                            │
    │ Choice: _
    └─────────────────────────────────────┘
```

### Implementation Pattern

```python
class CSFNIPViolationHandler:
    def handle_unknown_directory(self, file_path: str) -> None:
        dir_name = Path(file_path).parent.name

        print(f"\n❌ BLOCKED: Unknown directory")
        print(f"   Path: {file_path}")
        print(f"   Directory '{dir_name}' is not in the allowed list")

        choice = self._prompt_choice()

        if choice == "1":
            self._approve_and_update_policy(dir_name)
        elif choice == "2":
            self._suggest_location(file_path)
        else:
            sys.exit(2)  # Block

    def _approve_and_update_policy(self, dir_name: str) -> None:
        policy_path = Path("P:/.claude/hooks/config/directory_policy.json")

        # Backup
        backup_path = policy_path.with_suffix(".json.backup")
        shutil.copy(policy_path, backup_path)

        # Load, modify, save
        policy = json.loads(policy_path.read_text())
        policy["csf_nip_directory"]["allowed_subdirectories"].append({
            "path": dir_name,
            "purpose": "User-approved via interactive workflow"
        })
        policy_path.write_text(json.dumps(policy, indent=2))

        print(f"✅ Added '{dir_name}' to policy. Operation allowed.")
        sys.exit(0)  # Allow
```

## Implementation Priority

### Phase 1: Policy Update (Immediate)

1. Add `allowed_hidden_directories` to `csf_nip_directory` in `directory_policy.json`
2. Add `allowed_operational_directories` for migrations, monitoring, diag
3. Add `consolidation_rules` section

### Phase 2: Validation (Quick)

1. Test PathValidator with updated policy
2. Verify all 51 directories are categorized
3. Run `python path_validator.py --validate`

### Phase 3: Interactive Approval (Core Feature)

1. Create `csf_nip_deny_violations.py`
2. Integrate with existing `deny_root_write.py`
3. Test approve/suggest/deny flows

### Phase 4: Consolidation Tool (Later)

1. Create `consolidate_directories.py`
2. Dry-run mode first
3. User confirmation required
4. Execute only after verification

## Key Findings

1. **Infrastructure exists**: PathValidator and DirectoryPolicy are production-ready
2. **Policy is incomplete**: Only 18 of 51 directories explicitly allowed
3. **Blocked patterns work**: test_*.py, *.log, *.db already blocked
4. **No interactive approval**: Current system is block-only
5. **Consolidation needed**: .data/, model_cache/, logs_backup/ are duplicates
6. **Nested issue**: __csf.nip/__csf.nip/ exists (cleanup needed)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking imports | HIGH | Scan references before consolidation |
| Policy corruption | MEDIUM | Backup before update |
| False positive blocks | MEDIUM | Interactive approval override |
| Missing directory | LOW | Add to policy via approve option |

## Next Steps

1. ✅ Research complete (this document)
2. → Phase 2: Architecture Analysis (/arch)
3. → Phase 3: Implementation Planning (/plan)

---

**TSK ID**: TSK-251227-2319-csf-nip-dir-standards
**Step**: 3 - Research Intelligence
**Status**: Complete
