# Dependency Update Preparation Checklist

## Before Starting Updates

### ✅ Completed (2026-03-06)

- [x] **Git tag created**: `pre-dependency-update-20260306`
  - Rollback point established
  - Command: `git tag -a pre-dependency-update-20260306 -m "Backup before dependency updates - Task #1358"`

- [x] **Dependency tree mapped**
  - Saved to: `.dependency-tree-backup.json` (11,426 lines)
  - Tool: `pipdeptree --json > .dependency-tree-backup.json`

- [x] **Integration tests verified**
  - Found existing tests in: `tests/test_batch.py`, `tests/integration/`
  - Download pipeline tests: Present
  - Database schema tests: Need verification

- [x] **Task #1358 updated with pre-mortem findings**
  - Top 6 risks identified and mitigated
  - Realistic time estimate: 5-10 hours

### 🔄 Pending

#### Environment Setup

- [x] **Install pip-audit** (for CVE detection)
  ```bash
  pip install pip-audit
  ```

- [x] **Install pipdeptree** (for dependency tree analysis)
  ```bash
  pip install pipdeptree
  ```

- [x] **Document baseline state**
  - Save `pip list` output: `pip list > baseline-packages.txt`
  - Note: No need for separate venv or worktree (git tag + commits provide isolation)

#### Risk Assessment

- [ ] **Identify high-severity packages** (38 packages)
  ```bash
  pip list --outdated --format=json | python -c "
  import json, sys
  outdated = json.load(sys.stdin)
  for pkg in outdated:
    current = pkg['version'].split('.')[0]
    latest = pkg['latest_version'].split('.')[0]
    if current != latest:
      print(f\"{pkg['name']}: {pkg['version']} → {pkg['latest_version']} [MAJOR]\")
  "
  ```

- [ ] **Check for version conflicts**
  ```bash
  pipdeptree
  ```

- [ ] **Review breaking changes for top 10 packages**
  - Check GitHub release notes
  - Check CHANGELOG files
  - Document API changes

#### Update Strategy

- [ ] **Plan update batches** (10-20 packages per batch)
  - Batch 1: 38 high-severity packages (may need multiple sub-batches)
  - Batch 2: 50 medium-severity packages
  - Batch 3: Remaining packages

- [ ] **Set time box**: 10 hours maximum
  - Stop after time box, reassess approach
  - Document progress and blockers

- [ ] **Prepare rollback procedure**
  ```bash
  # Rollback to git tag
  git checkout pre-dependency-update-20260306

  # Rollback database schema (if needed)
  # [Database-specific rollback commands]
  ```

## During Updates

### Per Batch Checklist

- [ ] **Backup current state**
  ```bash
  git commit -am "Snapshot before dependency batch update"
  ```

- [ ] **Update packages in batch**
  ```bash
  pip install --upgrade package1 package2 package3 ...
  ```

- [ ] **Check for breaking changes**
  - Review changelogs
  - Look for deprecation warnings
  - Check for API changes

- [ ] **Run integration tests**
  ```bash
  pytest tests/integration/ -v --tb=short
  ```

- [ ] **Run download pipeline tests**
  ```bash
  pytest tests/test_batch.py -v --tb=short
  ```

- [ ] **Test critical functionality**
  - Download a test video
  - Extract metadata
  - Run search query
  - Verify database integrity

- [ ] **Document changes**
  - List updated packages
  - Note any breaking changes
  - Record test results

- [ ] **Commit if successful**
  ```bash
  git commit -am "Update batch N of dependencies: package1, package2, ..."
  ```

- [ ] **Rollback if failed**
  ```bash
  git reset --hard HEAD
  pip install -r requirements.txt  # Restore original versions
  ```

## After Updates

### Verification

- [ ] **Run full test suite**
  ```bash
  pytest tests/ -v --cov=src/yt_fts
  ```

- [ ] **Check for remaining outdated packages**
  ```bash
  pip list --outdated
  ```

- [ ] **Run security audit**
  ```bash
  pip-audit
  ```

- [ ] **Verify dependency tree**
  ```bash
  pipdeptree
  ```

### Documentation

- [ ] **Update CHANGELOG.md**
  - List all updated packages
  - Document breaking changes
  - Note any API changes

- [ ] **Update README.md**
  - Update dependency versions
  - Document any new requirements

- [ ] **Create migration guide** (if needed)
  - For breaking API changes
  - For database schema changes
  - For configuration changes

### Final Commit

- [ ] **Create comprehensive commit message**
  ```bash
  git commit -am "Update all outdated dependencies (Task #1358)

  - Updated 38 high-severity packages (major version bumps)
  - Updated 171 medium/low-severity packages
  - All tests passing
  - No breaking changes in yt-fts functionality
  - See CHANGELOG.md for full details"
  ```

- [ ] **Create git tag for new version**
  ```bash
  git tag -a v1.2.0 -m "Dependency updates complete"
  ```

## Warning Signs to Monitor

### ⚠️ Critical Indicators (Stop Immediately)

- Integration test failures → Rollback batch
- Database corruption → Rollback immediately, investigate
- Silent failures → Investigate before continuing
- Version conflicts → Resolve before proceeding
- Time per batch > 2 hours → Reassess approach

### ⚠️ Warning Indicators (Monitor Closely)

- Test warnings increasing → Investigate
- Performance degradation → Profile before continuing
- New dependencies appearing → Review necessity
- Documentation gaps → Document before proceeding

## Success Criteria

✅ **All outdated packages updated** (0 remaining)
✅ **All tests passing** (100% pass rate)
✅ **No security vulnerabilities** (pip-audit clean)
✅ **No breaking changes** (yt-fts fully functional)
✅ **Documentation updated** (CHANGELOG, README)
✅ **Rollback tested** (can revert if needed)

## Time Tracking

- **Started**: 2026-03-06
- **Estimated**: 5-10 hours
- **Time Box**: 10 hours maximum
- **Actual**: TBD

---

**Reference**: Task #1358, Pre-mortem analysis (2026-03-06)
