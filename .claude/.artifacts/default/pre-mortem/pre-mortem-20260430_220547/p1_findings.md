# Phase 1 Consolidated Findings — /plugin-installer SKILL.md

**Target:** `P:/packages/plugin-installer/skills/plugin-installer/SKILL.md`
**Date:** 2026-04-30
**Specialists:** adversarial-critic, adversarial-compliance, adversarial-quality

## Finding Convergence

All 3 specialists converge on a single dominant issue: **enabledProps verification is applied inconsistently across install paths**. The refresh action has it; install, add, Full Setup, and bulk refresh do not.

## Consolidated Findings by Severity

### CRITICAL (1)

**F-001: Full Setup skips enabledProps verification** (AC-001, COMP-001, QUAL-003)
- Location: SKILL.md:126-132 (Full Setup step 5)
- Full Setup is the primary user entry point (no args) and reinstalls all plugins but never verifies enabledProps registration
- The skill's own Troubleshooting section documents this as "the most common cause of plugin installed but not loading"
- Users will see `claude plugin list` showing installed plugins that silently fail to load
- **Consensus: 3/3 specialists flag this**

### HIGH (3)

**F-002: install action lacks enabledProps verification** (AC-002, COMP-001, QUAL-002)
- Location: SKILL.md:178-200
- Runs `claude plugin install <name>@local` without verifying enabledProps
- Same silent failure mode as Full Setup
- **Consensus: 3/3 specialists flag this**

**F-003: add action lacks enabledProps verification** (AC-003)
- Location: SKILL.md:221-237
- Highest-risk moment: first time a plugin enters the system
- Runs install without the guard that refresh has
- **Consensus: 2/3 specialists flag this (critic + compliance)**

**F-004: Bulk refresh has asymmetric enabledProps handling** (AC-004)
- Location: SKILL.md:298-306
- Targeted refresh includes enabledProps verification; bulk refresh does not
- Bulk refresh is higher risk (multiple plugins simultaneously)
- **Consensus: 1/3 (critic only)**

### MEDIUM (5)

**F-005: enabledProps verification snippet duplicated 3 times verbatim** (QUAL-001)
- Same ~12-line Python block appears in refresh action, troubleshooting, and should appear in install/add
- Any schema change requires updating all copies in lockstep
- Drift between copies will cause behavioral inconsistency
- **Recommendation: Extract to plugin-audit-and-fix.py as --verify-enabled flag**

**F-006: Hardcoded absolute paths in 5 inline scripts** (QUAL-007)
- `C:/Users/brsth/.claude/` hardcoded at lines 76, 117, 269, 285, 335
- Non-portable — breaks on different machine/user/WSL
- **Recommendation: Replace with `os.path.expanduser('~/.claude/...')` or route through plugin-audit-and-fix.py**

**F-007: validate workflow_step description claims wrong mechanism** (COMP-002)
- Line 10 says "Runs claude plugin validate" but actual command is plugin-audit-and-fix.py --validate
- **Recommendation: Update description to match actual command**

**F-008: sync workflow_step description is stale** (COMP-003)
- Line 16 says "Syncs plugin-installer source changes to marketplace" but sync is now vestigial (junction-only)
- **Recommendation: Update to "Converts real-dir to junction (migration only)"**

**F-009: Marketplace Architecture contradiction** (AC-005)
- Lines 52-54 say "no sync needed" but sync action exists and Full Setup includes sync step
- **Recommendation: Clarify that sync is for migration only, not active syncing**

**F-010: Bulk refresh skips installed_plugins.json cleanup** (AC-006)
- Targeted refresh pops entries from installed_plugins.json; bulk refresh only rm -rf cache dir
- Stale JSON entries could reference deleted cache directories
- **Recommendation: Add JSON cleanup to bulk refresh**

### LOW (4)

**F-011: commands/plugin-installer.md missing refresh and bump** (QUAL-008)
- Commands file lists 7 sub-commands; SKILL.md has 9 actions
- Missing: refresh, bump
- Discovery gap for users reading commands file

**F-012: Arguments schema missing 'name' parameter** (COMP-005)
- audit, validate, refresh, add, remove, bump accept optional [name] argument
- Schema only declares 'action' parameter
- Schema-compliant tooling will not surface name argument

**F-013: enforcement field is inert** (QUAL-006, COMP-006)
- `enforcement: advisory` in frontmatter is not read by any hook or runtime
- Cosmetic only, but could mislead maintainers

**F-014: bump action unclear whether reinstall needed** (AC-008)
- Bump changes version number but doesn't explicitly reinstall
- Unclear if version change alone triggers cache rebuild

## Cross-Cutting Pattern

The root issue is **incomplete propagation of a known fix**. The enabledProps verification was added to refresh and troubleshooting but not to the other 4 install paths. The fix exists in the skill — it just needs to be applied everywhere installs happen, ideally extracted to a shared script to prevent future drift.

## Divergent Findings

No divergent findings. All specialists agree on the core issues. The only variation is scope (which actions are flagged).
