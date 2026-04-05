# Migration Guide: From Separate Packages to Unified Monorepo

This guide helps you migrate from the original `prompt-enhancement` and `prompting-framework` packages to the new unified `prompting-toolkit` monorepo.

## Overview of Changes

| Before | After |
|--------|-------|
| `prompt-enhancement/` | `prompting-toolkit/packages/hook/` |
| `prompting-framework/` | `prompting-toolkit/packages/framework/` |
| Two separate repos | One unified monorepo |
| Separate documentation | Unified docs + preserved originals |

---

## For Users of `prompt-enhancement`

### What Changed?

| Old Path | New Path |
|----------|----------|
| `prompt-enhancement/hook/` | `prompting-toolkit/packages/hook/hook/` |
| `prompt-enhancement/pyproject.toml` | `prompting-toolkit/packages/hook/pyproject.toml` |
| `prompt-enhancement/README.md` | `prompting-toolkit/OLD_PROMPT_ENHANCEMENT_README.md` |

### Configuration Migration

**No changes needed!** Your existing configuration still works:

```json
// P:/.claude/settings.json (unchanged)
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
```

The hook router auto-discovers packages from:
- `P:/packages/` (local development)
- `~/.claude/hooks/_packages/` (production)

### Installation Migration

**Before (if you installed separately):**
```bash
# Old location
cp -r prompt-enhancement ~/.claude/hooks/_packages/
```

**After (monorepo):**
```bash
# New location
cp -r prompting-toolkit/packages/hook ~/.claude/hooks/_packages/prompt-hook
# OR just clone the monorepo to P:/packages/
git clone https://github.com/csf-dev/prompting-toolkit.git P:/packages/prompting-toolkit
```

### Code Migration

**No code changes!** The hook uses the same modules:

```python
# Still works (imports unchanged)
from hook.prompt_enhancement import prompt_enhancement
from hook.prompt_choice_state import ChoiceStateManager
```

---

## For Users of `prompting-framework`

### What Changed?

| Old Path | New Path |
|----------|----------|
| `prompting-framework/src/` | `prompting-toolkit/packages/framework/src/` |
| `prompting-framework/tests/` | `prompting-toolkit/packages/framework/tests/` |
| `prompting-framework/pyproject.toml` | `prompting-toolkit/packages/framework/pyproject.toml` |
| `prompting-framework/README.md` | `prompting-toolkit/OLD_PROMPTING_FRAMEWORK_README.md` |

### Installation Migration

**Before (PyPI - future):**
```bash
pip install prompting-framework
```

**After (monorepo):**
```bash
# Still works the same!
pip install prompting-framework

# Or install from local monorepo:
pip install -e packages/framework/
```

### Code Migration

**No code changes!** All imports remain the same:

```python
# All still work (imports unchanged)
from prompting_framework import PromptingOrchestrator
from prompting_framework import MetaPromptOptimizer
from prompting_framework.techniques import ChainOfVerificationTechnique
```

---

## Quick Migration Checklist

### Hook Users (`prompt-enhancement`)

- [ ] Update package location (if installing manually)
- [ ] Verify configuration in `P:/.claude/settings.json`
- [ ] Restart Claude Code
- [ ] Test with a prompt to verify hook runs
- [ ] Check OLD_PROMPT_ENHANCEMENT_README.md for preserved docs

### Framework Users (`prompting-framework`)

- [ ] Update installation path (if installing locally)
- [ ] Verify imports still work
- [ ] Run tests to ensure compatibility
- [ ] Check OLD_PROMPTING_FRAMEWORK_README.md for preserved docs

### Both Packages

- [ ] Read the new unified README.md
- [ ] Explore examples in `examples/`
- [ ] Update any hardcoded paths in scripts/docs
- [ ] Star the new repository on GitHub

---

## Breaking Changes

**None!** This migration is designed to be fully backward compatible.

### What's Preserved

- ✅ All module names and imports
- ✅ All configuration options
- ✅ All API endpoints and functions
- ✅ All environment variables
- ✅ All documentation (in OLD_*.md files)

### What's New

- ✨ Unified monorepo structure
- ✨ Cross-package examples
- ✨ Shared testing infrastructure
- ✨ Coordinated versioning
- ✨ Better organization

---

## Advanced: Custom Integrations

If you have custom integrations with the old packages:

### Updating Import Paths

```python
# Before (if you referenced full paths)
import sys
sys.path.insert(0, "/path/to/prompt-enhancement")
from hook.prompt_enhancement import prompt_enhancement

# After (monorepo)
import sys
sys.path.insert(0, "/path/to/prompting-toolkit/packages/hook")
from hook.prompt_enhancement import prompt_enhancement
```

### Updating CI/CD Pipelines

```yaml
# Before
- name: Install prompt-enhancement
  run: pip install prompt-enhancement

# After (monorepo - same!)
- name: Install prompting-toolkit
  run: pip install prompting-framework  # Still works!
  # OR: pip install -e packages/framework/
```

---

## Rollback Plan

If you need to rollback to the original packages:

```bash
# Clone original repos
git clone https://github.com/csf-dev/prompt-enhancement.git
git clone https://github.com/csf-dev/prompting-framework.git

# Use as before
```

All your code and configurations will work exactly as before!

---

## Support

### Migration Issues?

1. **Check OLD_*.md files** - Original documentation preserved
2. **Read examples/** - See new usage patterns
3. **Open GitHub issue** - Tag with `migration` label

### Common Issues

**Issue:** Import errors after migration
**Fix:** Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`

**Issue:** Hook not running
**Fix:** Verify package location: `ls P:/packages/prompting-toolkit/packages/hook/`

**Issue:** Tests failing
**Fix:** Update test paths: `pytest packages/framework/tests/`

---

## Timeline

| Date | Milestone |
|------|-----------|
| Now | Monorepo created |
| +1 week | Original packages archived (not deleted) |
| +1 month | PyPI publishing for `prompting-framework` |
| +2 months | Documentation updates |

Original packages will remain available but marked as "deprecated - see prompting-toolkit".

---

## Questions?

**FAQ:**

**Q: Do I have to migrate?**
A: No, original packages still work. But the monorepo offers better organization and new features.

**Q: Will the original packages be deleted?**
A: No, they'll be archived with a deprecation notice pointing to the monorepo.

**Q: Can I use both old and new?**
A: Yes, but not recommended. They're the same code - pick one approach.

**Q: What about my existing code?**
A: It works unchanged! All imports and APIs are identical.

---

## Summary

**Migrating is easy:**

1. **Hook users:** Update package location, verify config
2. **Framework users:** Update installation path, verify imports
3. **Both:** Read new README, explore examples

**Nothing breaks** - this is a reorganization, not a rewrite.

**Everything improves** - better structure, unified docs, cross-package examples.

---

**Welcome to the Prompting Toolkit monorepo!** 🎉
