# Support Plan: unified-search → search-research Migration

**Last Updated:** 2026-03-06
**Support Period:** 2026-03-06 to 2026-09-01

## Support Commitment

We are committed to supporting users during the migration period from `unified-search` to `search-research`.

## Support Scope

### What We Support

✅ **Migration Issues:**
- Import path updates
- API differences
- Breaking changes
- Performance regressions
- Documentation clarifications

✅ **Bug Fixes:**
- Critical bugs in new package
- Migration blockers
- Data loss risks
- Security vulnerabilities

✅ **Questions:**
- How to migrate specific code patterns
- Feature parity questions
- Best practices for new API
- Configuration assistance

### What We Don't Support

❌ **Out of Scope:**
- Feature requests for deprecated package
- Performance optimizations for old code
- New features in unified-search
- Custom development work

## Support Channels

### 1. Documentation

**First Stop:** [MIGRATION.md](MIGRATION.md)
- Step-by-step migration guide
- Code examples
- Common issues and solutions

**Reference:** [DEPRECATION.md](DEPRECATION.md)
- Deprecation timeline
- Feature comparison
- Q&A section

### 2. Issue Tracking

**GitHub Issues:** Report bugs and migration problems
- Label: `migration:` for migration-specific issues
- Label: `bug:` for bugs
- Label: `documentation:` for docs issues

**Response Time:**
- Critical bugs: 24-48 hours
- Migration issues: 48-72 hours
- Documentation: 1 week

### 3. Rollback Support

If migration causes issues:

**Immediate Rollback:**
```bash
# Uninstall new package
pip uninstall search-research

# Old code continues to work
python -m __csf.src.cli.nip.search_enhanced "test"
```

**Report Problem:**
1. Document the issue (error messages, behavior)
2. File issue with `migration:` label
3. Include minimal reproduction case
4. We'll respond within 48-72 hours

**Continue Using Old System:**
- Old system works until EOL (2026-09-01)
- No rush to migrate
- Migrate at your own pace

## Priority Levels

### P0 - Critical (Response: 24-48 hours)

**Definition:**
- Data loss or corruption
- Security vulnerabilities
- Complete system failure
- Migration blockers for multiple users

**Examples:**
- "Migrating broke my search completely"
- "I lost data after migrating"
- "Security issue in search-research"

### P1 - High (Response: 48-72 hours)

**Definition:**
- Significant functionality broken
- Performance regression >2x
- Migration confusing or unclear

**Examples:**
- "Feature X doesn't work after migration"
- "Search is much slower now"
- "Documentation is unclear about Y"

### P2 - Medium (Response: 1 week)

**Definition:**
- Minor functionality issues
- Documentation improvements
- Non-blocking questions

**Examples:**
- "How do I do X in the new API?"
- "Documentation could be clearer about Y"
- "Minor edge case doesn't work"

### P3 - Low (Response: 2 weeks)

**Definition:**
- Nice-to-have improvements
- Feature requests
- Non-urgent questions

**Examples:**
- "Would be nice if feature X existed"
- "Can you add Y?"
- "Question about future plans"

## Known Issues and Workarounds

### Issue #1: Import Path Confusion

**Problem:** Users confused about which import to use

**Workaround:** Follow migration guide step-by-step
**Fix:** Improved warnings in deprecated package (✅ Fixed)
**Status:** RESOLVED

### Issue #2: Backend Name Changes

**Problem:** Backend names changed from uppercase to lowercase

**Workaround:** Update backend names to lowercase (CDS → cds)
**Fix:** Documentation updated (✅ Fixed)
**Status:** RESOLVED

### Issue #3: API Key Configuration

**Problem:** Web providers require API key setup

**Workaround:** See provider setup in README
**Fix:** Documentation added (✅ Fixed)
**Status:** RESOLVED

## Issue Reporting Template

When reporting issues, please include:

```markdown
### Issue Description
[Brief description of the problem]

### Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### Environment
- Python version:
- OS:
- search-research version:
- Code snippet showing the issue:

### Error Messages
[Paste any error messages or stack traces]

### Impact
- How many users affected?
- Blocking migration? (Y/N)
- Data loss risk? (Y/N)
- Security risk? (Y/N)
```

## Migration Support Timeline

| Date | Support Level |
|------|--------------|
| 2026-03-06 to 2026-04-01 | Full support (all priority levels) |
| 2026-04-01 to 2026-06-01 | P0 and P1 issues only |
| 2026-06-01 to 2026-09-01 | P0 critical bugs only |
| After 2026-09-01 | No support (EOL) |

## Getting Help Fast

### For Critical Issues (P0)

1. **Immediate:** Check if rollback fixes it
2. **Document:** Gather error messages and reproduction steps
3. **Report:** File issue with `migration:` + `P0` labels
4. **Workaround:** Use old system until fix is ready

### For Non-Critical Issues (P1-P3)

1. **Read:** Check documentation first (MIGRATION.md, DEPRECATION.md)
2. **Search:** Check existing GitHub issues
3. **Report:** File new issue with appropriate priority
4. **Wait:** Response within SLA timeframe

## Commitment to Users

We are committed to:

✅ **Clear Communication**
- Transparent about deprecation timeline
- Regular updates on migration progress
- Prompt responses to issues

✅ **Quality Support**
- Helpful, respectful responses
- Actionable solutions
- Follow-through on fixes

✅ **Smooth Migration**
- Comprehensive documentation
- Working migration paths
- Rollback safety net

## Contact Information

- **Issues:** [GitHub Issues](https://github.com/yourusername/search-research/issues)
- **Documentation:** [README.md](README.md), [MIGRATION.md](MIGRATION.md)
- **Deprecation:** [DEPRECATION.md](DEPRECATION.md)

---

**Remember:** The old system works until 2026-09-01. There's no rush to migrate. Take your time, test thoroughly, and reach out if you need help.
