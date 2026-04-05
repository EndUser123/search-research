# Package Skill Rename CRUD Checklist

## Purpose

Complete checklist for renaming package skills (e.g., `loop-core` → `loop-code`). Package renames are **breaking changes** that require comprehensive CRUD operations across the codebase.

## When This Triggers

This checklist is triggered automatically when /gto detects:
- Chat transcript mentions renaming a package skill
- Discussion of moving or renaming skill directories
- Updates to skill metadata with new names
- Junction symlink modifications

## CRUD Operations Required (in order)

### 1. Skill Metadata Updates (SKILL.md frontmatter)

**Location**: `skills/{new-name}/SKILL.md`

**Updates needed**:
```yaml
---
name: {new-name}           # ✅ Update to new name
aliases:                   # ✅ Remove old aliases for breaking changes
  - /{old-name}            # OR update with new name if backward compatible
version: X.Y.Z             # ✅ Bump version
---
```

**Why this matters**:
- Wrong `name:` field causes command invocation failures
- Stale `aliases:` confuse users with commands that don't work
- No version bump breaks dependency tracking

---

### 2. ALL Documentation References

**Search for all references**:
```bash
# Find all documentation references
grep -r "/{old-name}" . --include="*.md" --include="*.py"
grep -r "skills/{old-name}" . --include="*.md" --include="*.py"
```

**Update references**:
- Command references: `/{old-name}` → `/{new-name}`
- File path references: `skills/{old-name}/` → `skills/{new-name}/`
- Import statements that reference old paths
- Test fixtures with old skill names
- Configuration files

**Common locations**:
- `README.md` - Quick start and usage examples
- `CONTRIBUTING.md` - Development workflows
- `docs/` - All documentation files
- `reports/` - Review bundles and analysis reports
- `tests/` - Test files and fixtures
- `CHANGELOG.md` - Add migration note
- Build scripts and CI/CD configs

**Bulk update command**:
```bash
# Count first to see scope
grep -r "/{old-name}" . --include="*.md" | wc -l

# Update all markdown files
find . -name "*.md" -exec sed -i 's|/{old-name}|/{new-name}|g' {} \;

# Update all Python files
find . -name "*.py" -exec sed -i 's|/{old-name}|/{new-name}|g' {} \;
```

**Why this matters**:
- Broken documentation confuses users
- Stale references cause "command not found" errors
- Inconsistent docs reduce trust in project quality

---

### 3. Directory Structure Rename

**Rename actual directory**:
```bash
# PRESERVES GIT HISTORY - Critical for project integrity
git mv skills/{old-name}/ skills/{new-name}/

# WRONG - Do NOT use regular mv command
mv skills/{old-name}/ skills/{new-name}/  # ❌ Loses git history
```

**Why this matters**:
- Using `git mv` preserves all commit history and blame information
- Using `mv` fragments history - breaks `git blame`, makes code archaeology impossible
- Git history is critical for understanding why changes were made

---

### 4. Junction Symlink Updates

**Check old junction**:
```bash
ls -la .claude/skills/{old-name}
# Should show: {old-name} -> /p/packages/{pkg}/skills/{old-name}
```

**Remove old junction**:
```bash
rm .claude/skills/{old-name}
```

**Create new junction**:
```bash
# Windows syntax (mklink)
mklink /D .claude\skills\{new-name} P:\packages\{pkg}\skills\{new-name}

# Unix symlink syntax
ln -s /p/packages/{pkg}/skills/{new-name} .claude/skills/{new-name}
```

**Verify new junction**:
```bash
ls -la .claude/skills/{new-name}
# Should show: {new-name} -> /p/packages/{pkg}/skills/{new-name}
```

**Why this matters**:
- Broken junctions cause "skill not found" errors
- Users can't invoke the renamed skill
- Skills appear in completions but fail when invoked

---

### 5. File Path References Throughout Codebase

**Search for path references**:
```bash
# Find imports and path references
grep -r "from.*{old-name}" . --include="*.py"
grep -r "import.*{old-name}" . --include="*.py"
grep -r "{old-name}" . --include="*.json" --include="*.yaml" --include="*.toml"
```

**Update references**:
- Python imports: `from skills.{old-name}` → `from skills.{new-name}`
- Configuration files: Update paths in JSON/YAML/TOML
- Test fixtures: Update skill path fixtures
- Build scripts: Update any hardcoded paths

**Common locations**:
- `__init__.py` files with imports
- `pyproject.toml` or `setup.py`
- Test configuration files
- CI/CD pipeline definitions
- Plugin manifests (`.claude-plugin/plugin.json`)

**Why this matters**:
- Broken imports cause `ImportError` at runtime
- Test failures with `ModuleNotFoundError`
- CI/CD pipelines fail with path resolution errors

---

## Complete Workflow Example

```bash
# 1. Update skill metadata
vim skills/{new-name}/SKILL.md  # Update name, remove aliases, bump version

# 2. Find ALL documentation references
grep -r "/{old-name}" . --include="*.md" | wc -l  # Count them first!

# 3. Update ALL references (bulk operation)
find . -name "*.md" -exec sed -i 's|/{old-name}|/{new-name}|g' {} \;
find . -name "*.py" -exec sed -i 's|/{old-name}|/{new-name}|g' {} \;

# 4. Rename directory (PRESERVES git history)
git mv skills/{old-name}/ skills/{new-name}/

# 5. Update junction symlink
rm .claude/skills/{old-name}
ln -s /p/packages/{pkg}/skills/{new-name} .claude/skills/{new-name}

# 6. Update imports and path references
# Manual review and update of Python files, configs, test fixtures

# 7. Verify everything
git status
git diff --stat

# 8. Test the renamed skill
/{new-name} --help

# 9. Commit all changes
git add -A
git commit -m "feat: Rename {old-name} to {new-name}

- Update skill metadata (name, version, remove old aliases)
- Update all documentation references
- Rename directory with git mv (preserves history)
- Update junction symlink
- Update imports and path references
- Add migration note to CHANGELOG

BREAKING CHANGE: /{old-name} renamed to /{new-name}
"
```

---

## Incomplete Update Consequences

When package renames are incomplete, they cause:

### User-Facing Issues
- **Commands that don't work**: Users invoke `/{old-name}` and get "skill not found"
- **Confusing documentation**: README shows `/{old-name}` but only `/{new-name}` exists
- **Broken examples**: Code snippets and tutorials fail to run

### Development Issues
- **Test failures**: Tests reference old skill names or paths
- **Import errors**: Python can't find modules at old paths
- **CI/CD breaks**: Pipelines fail with path resolution errors

### Project Health Issues
- **Fragmented git history**: Using `mv` instead of `git mv` loses blame information
- **Stale aliases**: Old skill names appear in completions but don't work
- **Inconsistent codebase**: Some files updated, others forgotten

---

## Detection Patterns

/gto automatically detects incomplete package renames by looking for:

1. **Skill renamed but junction not updated**:
   - Chat mentions: "rename {old-name} to {new-name}"
   - But no junction update commands

2. **Documentation updated but metadata not changed**:
   - Chat shows: "update all references to {new-name}"
   - But SKILL.md still has `name: {old-name}`

3. **Directory renamed with `mv` instead of `git mv`**:
   - Chat shows: "mv skills/{old-name} skills/{new-name}"
   - Instead of "git mv"

4. **Partial documentation updates**:
   - Chat mentions: "update README for rename"
   - But grep shows other files still reference old name

---

## Related Documentation

- **Git workflow**: `/git` - Proper git history preservation
- **Skill structure**: `/claude-hooks` - Understanding skill organization
- **Testing**: `/tdd` - Testing renamed skills
- **Documentation**: `/claude-md-management:revise-claude-md` - Updating project docs

---

## Version: 1.0

Last updated: 2026-03-15
