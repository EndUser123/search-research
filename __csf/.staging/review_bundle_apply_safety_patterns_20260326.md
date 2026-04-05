# Review Bundle: /apply-safety-patterns Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/apply_safety_patterns/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: apply_safety_patterns
- **Description**: Constitutionally compliant safety pattern application with proven success rates
- **Category**: safety
- **Trigger**: /apply-safety-patterns, "safety patterns", "apply safety patterns"
- **Aliases**: /apply-safety-patterns

### Domain & Purpose
Applies proven safety patterns to resolve systematic issues with full developer control and immediate file-based effects.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown + Python
- **Key Integration**: /comply, /bug-hunt, /validate-safety-patterns

---

## 2. CONSTITUTIONAL COMPLIANCE

- **Singular Decision Authority** - Developer maintains 100% control
- **No Background Services** - All functionality is command-driven
- **No Required Consensus** - No organizational decision requirements
- **Direct File Editing** - All changes are immediate file modifications
- **User Control** - Opt-out available for all features

---

## 3. SAFETY CATEGORIES

| Category | Success Rate | Pattern | Issues Resolved |
|----------|-------------|---------|-----------------|
| database | 95% | `ensure_database()` before operations | `sqlite3.OperationalError` |
| path | 90% | Cross-platform path normalization | Windows/Unix path inconsistencies |
| json | 98% | `safe_parse_json()` with error handling | `json.JSONDecodeError` |
| import | 92% | Robust import handling | `ModuleNotFoundError` |
| hook | 100% | Clean JSON input handling | PostToolUse execution failures |

---

## 4. WORKFLOW

1. **Issue Detection** - Automatic detection with evidence scoring
2. **Pattern Recommendation** - Evidence-based recommendations with success rates
3. **Interactive Approval** - User must approve each individual change
4. **Backup Creation** - Automatic backup before modifications
5. **Pattern Application** - Apply safety patterns to target files
6. **Validation and Reporting** - Comprehensive validation and reporting

---

## 5. VALIDATION RULES

### Prohibited Actions
- **NEVER apply changes without user approval** - interactive mode required
- **NEVER skip backup creation** - always preserve original state
- **NEVER claim fix without evidence** - show success rate data

### Required Output
- List detected issues with severity
- Show recommended patterns with success rates
- Confirm user approval before applying
- Report validation results after application

---

## 6. USAGE EXAMPLES

```bash
# Apply all safety patterns with interactive approval
/apply-safety-patterns --interactive

# Apply specific category with user confirmation
/apply-safety-patterns --category=database --confirm

# Apply with dry-run to preview changes
/apply-safety-patterns --dry-run --verbose
```

---

## 7. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Documentation | GOOD | 126-line SKILL.md with success rates |
| Safety Enforcement | EXCELLENT | Constitutional compliance |

### SQA Relevance
- **HIGH** — Safety validation skill
- Proven success rates for each pattern category
- User approval required before changes
- Automatic backup creation
- Integrates with /validate-safety-patterns for verification
