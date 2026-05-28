# Removal Protocol

When removing a module, system, plugin, or feature from the codebase, follow this protocol before declaring completion.

## Pre-Removal Audit

Before deleting anything, discover the full scope:

1. **Grep imports**: `grep -r "import <module>" --include="*.py"` — find all importers
2. **Grep references**: `grep -r "<module_name>" --include="*.py"` — find all usages
3. **Glob files**: `glob "<module>*"` or `glob "**/<module>*"` — find all related files
4. **Check tests**: `glob "tests/test_<module>*"` — find test files
5. **Check data**: `glob "**/<module>*.json*"` — find data/state/log files

## Execution

6. Delete all discovered files (code, tests, data, compiled bytecode)
7. Remove all import statements and references from consuming files
8. Remove registration entries (settings.json, hooks.json, router files, marketplace.json)

## Verification (mandatory before declaring done)

9. `grep -r "import <module>" --include="*.py"` — must return zero results
10. `grep -r "<module_name>" --include="*.py"` — must return zero results (or only unrelated matches)
11. Verify no files remain: `glob "**/<module>*"` — must return empty

Only after all three verification checks pass may you state "removal complete" or "cleanup complete".

## Anti-Patterns

- **Dormant code**: Disabling with early returns or comments instead of deleting. Delete it.
- **Fallback preservation**: Keeping old code "in case we need it". Delete it. Git has history.
- **Premature declaration**: Claiming "cleanup complete" before running verification grep. Run the grep first.
