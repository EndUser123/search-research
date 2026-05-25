---
description: "Bulk refactoring rule: git mv requirement, anti-patterns, evidence"
alwaysApply: false
---

# Refactoring Safety

## Bulk Refactoring Rule

When moving or renaming more than 2 files in a refactoring:
- **Use `git mv`** for all file moves — never manual copy+delete
- **Run tests after each logical group** of moves, not just at the end
- **Update imports immediately** after moving — don't batch across groups

## Anti-Patterns

| Pattern | Why It's Bad |
|---------|-------------|
| Copy file → edit copy → delete original | Loses git history, no `git blame` trail |
| Rename without `git mv` | Same as above |
| Move 10 files then run tests | Failures are hard to bisect |
| Move + refactor in one commit | Cannot distinguish move bugs from refactor bugs |

## Evidence

The SQA incident (2025-12) demonstrated that bulk refactoring without `git mv`
caused a 3-day recovery when 47 files were moved manually and git history was lost.
This rule was extracted from that post-mortem.
