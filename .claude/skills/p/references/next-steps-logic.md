# Completion Detection and Context-Aware Next Steps Reference

## Step 5.5: Dual-Nature Skill Metadata Validation (After P2 Only)

**When to run:** After P2 (Review) completes for dual-nature packages (has both `pyproject.toml` AND `skill/SKILL.md`).

**Purpose:** Validate skill metadata without blocking the package pipeline. Python code is primary; skill interface is secondary.

**Detection check (before running):**
```bash
ls pyproject.toml skill/SKILL.md skills/*/SKILL.md 2>&1
# If pyproject.toml AND (skill/SKILL.md OR skills/*/SKILL.md) exist -> dual-nature detected
```

**Validation scope (non-blocking warnings only):**
1. **SKILL.md frontmatter validation:**
   - Required fields: `name`, `description`, `category`, `triggers`
   - Valid categories: documentation, development, testing, analysis, automation
   - Trigger syntax: `/{command-name}` format

2. **Trigger consistency check:**
   - Trigger in SKILL.md matches any CLI entry point in package
   - Aliases (if present) reference valid triggers

3. **Documentation completeness:**
   - Has `## Purpose` section
   - Has `## Your Workflow` or usage section
   - No empty sections (placeholder content only)

**Run validation:**
```bash
# Determine skill path
SKILL_PATH=""
if [[ -f "skill/SKILL.md" ]]; then
  SKILL_PATH="skill/SKILL.md"
elif [[ -f "skills/"*/SKILL.md ]]; then
  SKILL_PATH=$(ls skills/*/SKILL.md 2>/dev/null | head -1)
fi

Read "$SKILL_PATH" and validate against the checks above.
Report any issues as non-blocking warnings with format:
  SKILL-{category}-{number}: {description} (NON-BLOCKING) - $SKILL_PATH:{line}
```

**Example output:**
```
[Dual-Nature Check] Validating skill metadata...

Found 2 skill metadata issues (non-blocking):
  SKILL-FRONTMATTER-001: Missing 'category' field (NON-BLOCKING) - skill/SKILL.md:4
  SKILL-DOC-001: Empty '## Your Workflow' section (NON-BLOCKING) - skill/SKILL.md:45

[Dual-Nature] Skill metadata validation complete
   2 non-blocking warnings (package pipeline continues)
```

## Step 5.75: Completion Detection

```python
def is_work_complete(target: str, phase: int, findings: dict) -> tuple[bool, str]:
    """
    Detect if work is complete and no next steps are needed.

    Returns:
        (complete, reason): complete=True means show "COMPLETE" status
    """
    from pathlib import Path

    has_pyproject = Path(target).joinpath("pyproject.toml").exists()
    has_package_json = Path(target).joinpath("package.json").exists()
    has_go_mod = Path(target).joinpath("go.mod").exists()
    is_infrastructure = not (has_pyproject or has_package_json or has_go_mod)

    tests_pass = (findings.get("test_failures", 0) == 0)
    no_blocking = (findings.get("blocking_findings", 0) == 0)
    no_non_blocking = (findings.get("non_blocking_findings", 0) == 0)

    if is_infrastructure and tests_pass and no_blocking and no_non_blocking:
        return (True, "Infrastructure code complete (tests pass, no findings)")

    if phase == 5 and tests_pass and no_blocking and no_non_blocking:
        return (True, "Package pipeline complete (all phases passed)")

    return (False, "")
```

## Step 6: Context-Aware Next Steps

```python
def get_next_steps(target: str, phase: int, findings: dict, what_was_done: str) -> dict:
    """
    Generate context-aware next steps based on actual situation.

    Returns:
        {
            "status": "complete" | "continue" | "blocked",
            "title": "Pipeline Status: COMPLETE" | "Next Steps",
            "options": [
                {"action": "/p", "description": "...", "recommended": bool},
                ...
            ]
        }
    """
    from pathlib import Path

    complete, reason = is_work_complete(target, phase, findings)
    if complete:
        return {"status": "complete", "title": "Pipeline Status: COMPLETE", "options": []}

    has_pyproject = Path(target).joinpath("pyproject.toml").exists()
    has_package_json = Path(target).joinpath("package.json").exists()
    has_go_mod = Path(target).joinpath("go.mod").exists()
    is_infrastructure = not (has_pyproject or has_package_json or has_go_mod)

    blocking = findings.get("blocking_findings", 0)
    non_blocking = findings.get("non_blocking_findings", 0)
    test_failures = findings.get("test_failures", 0)

    if blocking > 0 or test_failures > 0:
        if is_infrastructure:
            options = _get_infrastructure_blocked_options(target, what_was_done, findings)
        else:
            options = _get_package_blocked_options(findings)
    elif non_blocking > 0:
        if is_infrastructure:
            options = _get_infrastructure_nonblocking_options(target, what_was_done, findings)
        else:
            options = _get_package_nonblocking_options(findings)
    else:
        next_phase = phase + 1
        if next_phase <= 5:
            options = [{"action": f"/p --phase={next_phase}", "description": f"Continue to Phase {next_phase}", "recommended": True}]
        else:
            return {"status": "complete", "title": "Pipeline Status: COMPLETE", "options": []}

    return {
        "status": "continue" if blocking == 0 and test_failures == 0 else "blocked",
        "title": "Next Steps",
        "options": options
    }
```

### Helper Functions for Blocked/Non-Blocked Options

```python
def _get_infrastructure_blocked_options(target, what_was_done, findings):
    options = []
    if "fix" in what_was_done.lower():
        options.append({"action": "git diff", "description": "Review the fix you just applied", "domain": "Review Changes", "recommended": True})
        options.append({"action": "/p", "description": "Re-run pipeline to verify fix", "domain": "Continue Pipeline", "recommended": False})
    if findings.get("test_failures", 0) > 0:
        options.append({"action": f"pytest {target} -v", "description": "Run tests to see failures", "domain": "Testing", "recommended": False})
    if findings.get("type_errors", 0) > 0:
        options.append({"action": f"mypy {target}", "description": "Check type errors", "domain": "Testing", "recommended": False})
    return options


def _get_package_blocked_options(findings):
    test_failures = findings.get("test_failures", 0)
    blocking = findings.get("blocking_findings", 0)
    options = []
    if test_failures > 0:
        options.append({"action": "/tdd Fix test", "description": f"Fix {test_failures} failing tests", "domain": "Fix Tests", "recommended": True})
    if blocking > 0:
        options.append({"action": "/tdd Fix CRITICAL", "description": f"Fix {blocking} blocking findings", "domain": "Fix Findings", "recommended": test_failures == 0})
    options.append({"action": "/tdd Fix all", "description": "Fix all findings (iterative fixing loop)", "domain": "Fix Findings", "recommended": False})
    return options


def _get_infrastructure_nonblocking_options(target, what_was_done, findings):
    options = []
    non_blocking = findings.get("non_blocking_findings", 0)
    if non_blocking > 0:
        options.append({"action": "/p --fix", "description": f"Auto-fix safe issues ({non_blocking} findings)", "domain": "Fix Issues", "recommended": False})
    options.append({"action": "/p", "description": "Continue to next phase (issues are non-blocking)", "domain": "Continue Pipeline", "recommended": True})
    return options


def _get_package_nonblocking_options(findings):
    options = []
    options.append({"action": "/p", "description": "Continue to next phase (recommended)", "domain": "Continue Pipeline", "recommended": True})
    medium = findings.get("medium_findings", 0)
    low = findings.get("low_findings", 0)
    if medium > 0:
        options.append({"action": "/tdd Fix MEDIUM", "description": f"Fix {medium} MEDIUM severity findings", "domain": "Fix Findings", "recommended": False})
    if low > 0:
        options.append({"action": "/tdd Fix LOW", "description": f"Fix {low} LOW severity findings", "domain": "Fix Findings", "recommended": False})
    return options
```

### Output Formatting

```python
# Step 6: Report What's Next
next_steps = get_next_steps(target, phase, findings, what_was_done)

print(f"## {next_steps['title']}")
print()

if next_steps['status'] == 'complete':
    print("**Status:** WORK COMPLETE")
elif next_steps['options']:
    print("**Recommended Next Steps**")
    print()
    domains = {}
    for opt in next_steps['options']:
        domain = opt.get('domain', 'General')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(opt)

    domain_num = 1
    for domain, options in domains.items():
        print(f"{domain_num}. [{domain}]")
        for i, opt in enumerate(options, start=ord('a')):
            option_letter = chr(i)
            rec = " (recommended)" if opt.get('recommended', False) else ""
            print(f"   {domain_num}{option_letter}. `{opt['action']}` - {opt['description']}{rec}")
        domain_num += 1

    print()
    print("**0 -- Do ALL Recommended Next Steps**")
```

### Recommended Next Steps Template

The "Recommended Next Steps" section is a **reusable component** used across all phase outputs (P1-P5).

**Pattern:**
```markdown
**Recommended Next Steps**

1. [Domain Name]
   1a. `command` - Brief description
   1b. `command` - Brief description

2. [Domain Name]
   2a. `command` - Brief description

**0 -- Do ALL Recommended Next Steps**
```

**Rules:**
1. **Domain-organized**: Group related actions under domain headers
2. **Alphanumeric hierarchy**: Use numbered domains (1, 2, 3...) with alpha sub-options (1a, 1b...)
3. **Selection behavior**: Domain number -> do all in domain; specific option -> just that; "0" -> do everything
4. **Commands in backticks**, descriptions plain text
5. **Priority-ordered**: most critical domains first
6. **"0" always last** -> The "do all" option is the final line

**Common Domains by Target Type:**

Infrastructure code:
1. [Testing] - Run tests, check types
2. [Review Changes] - Git diff, verify fixes
3. [Continue Pipeline] - Re-run /p

Package code:
1. [Fix Tests] - Run TDD for failing tests
2. [Fix Findings] - TDD for CRITICAL/HIGH findings
3. [View Details] - Show full findings JSON
