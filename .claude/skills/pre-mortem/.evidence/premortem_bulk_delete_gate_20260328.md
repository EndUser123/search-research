# Pre-Mortem: Bulk Delete Gate Fix (v1.0)

**Target:** `P:\.claude\hooks\PreToolUse_bulk_delete_gate.py`
**Changes:** Inline bypass detection + `.backup` safe pattern
**Date:** 2026-03-28

## Step 1: Failure Scenario

"It's 6 months later. The bulk delete gate fix FAILED — either users lost data due to over-permissive bypass, or the gate still blocks legitimate deletions causing workflow friction."

## Step 2: Failure Causes (12)

1. **Bypass injection via echo/comment** — `echo "BULK_DELETE_BYPASS=1" && rm -rf /important/` matches regex but doesn't actually set env var. Gate allows deletion. (Tech)
2. **Over-broad `.backup` match** — `r"\.backup\b"` matches `project.backup`, `code.backup.py`, any path containing `.backup`. Could skip gate on non-temporary directories. (Tech)
3. **Regex doesn't handle `BULK_DELETE_BYPASS='1'`** — Single-quoted value bypasses regex (expects unquoted 1). Users frustrated when bypass "doesn't work" with quotes. (Tech)
4. **No logging of bypass usage** — When bypass fires, no record of what was deleted or why. No audit trail for post-incident review. (Process)
5. **Gate disabled by stale env var** — `BULK_DELETE_BYPASS=1` left in environment from earlier session, silently disabling gate for all future deletions. (Tech)
6. **Safe patterns grow unchecked** — Each incident adds a new safe pattern. Over time, the list becomes so broad the gate rarely triggers. (Process)
7. **FILE_THRESHOLD=5 too low for large repos** — Deleting 6 generated files triggers gate meant for 23-script incidents. Friction on legitimate bulk operations. (Process)
8. **git tag creation fails silently** — On Windows, `creationflags` or permissions issues cause tag creation to fail. Users think they have recovery point but don't. (Tech)
9. **Race condition with concurrent terminals** — Two terminals deleting overlapping paths. Tag names include microseconds but same-second creation could collide. (Tech)
10. **Hook not in dispatch chain** — If `PreToolUse_bulk_delete_gate.py` is not registered in `PreToolUse.py` UNIVERSAL/TOOL_HOOKS, the fix never executes. (Process)
11. **LLM constructs bypass strings in commands** — Claude includes `BULK_DELETE_BYPASS=1` in bash commands after learning about the bypass from SKILL.md or CLAUDE.md context, bypassing gate unintentionally. (AI/LLM)
12. **Test passes but integration fails** — Unit tests mock `create_git_tag` but real git tag creation fails in production due to worktree state or detached HEAD. (Process)

## Step 2.5: Cascade Analysis (risks >= 6)

**Risk 1 → Risk 5 → Risk 4:**
Data loss via injection → no audit trail → no accountability

**Risk 11 → Risk 1:**
LLM learns bypass pattern → constructs injection commands → data loss

## Step 2.6: AI/LLM Failure Modes

- **Pattern memorization**: LLM reads hook source, learns bypass pattern, applies it proactively without user consent
- **Over-generalization**: LLM adds `BULK_DELETE_BYPASS=1` to ALL rm commands "just in case"
- **Context leakage**: Hook source visible in SKILL.md teaches bypass technique that gets applied to OTHER safety gates

## Step 2.7: Temporal Failure Modes

- **Stale env var**: `BULK_DELETE_BYPASS=1` set in session 1 persists into session 2 via shell profile
- **Forgotten context**: 50+ turns after reading hook source, LLM still applies bypass pattern
- **Safe pattern drift**: New safe patterns added in different sessions without coordination

## Step 3: Categorization

| # | Category | Risk |
|---|----------|------|
| 1 | Tech | Bypass injection |
| 2 | Tech | Over-broad `.backup` match |
| 3 | Tech | Quote handling |
| 4 | Process | No audit logging |
| 5 | Tech | Stale env var |
| 6 | Process | Safe pattern bloat |
| 7 | Process | Low threshold |
| 8 | Tech | Silent git tag failure |
| 9 | Tech | Race condition |
| 10 | Process | Not in dispatch chain |
| 11 | AI/LLM | Unintentional bypass |
| 12 | Process | Integration gap |

## Step 4: Risk Rating

| # | Likelihood | Impact | Score | Priority |
|---|-----------|--------|-------|----------|
| 1 | 2 (possible) | 3 (data loss) | **6** | HIGH |
| 5 | 2 (possible) | 3 (data loss) | **6** | HIGH |
| 11 | 2 (possible) | 3 (data loss) | **6** | HIGH |
| 2 | 2 (possible) | 2 (minor data loss) | **4** | MEDIUM |
| 8 | 2 (possible) | 2 (false confidence) | **4** | MEDIUM |
| 10 | 1 (unlikely) | 3 (silent failure) | **3** | LOW |
| 4 | 2 (possible) | 1 (no audit) | **2** | LOW |
| 3 | 1 (unlikely) | 2 (friction) | **2** | LOW |
| 6 | 1 (unlikely) | 2 (weakened gate) | **2** | LOW |
| 7 | 1 (unlikely) | 2 (friction) | **2** | LOW |
| 9 | 1 (unlikely) | 1 (minor) | **1** | LOW |
| 12 | 1 (unlikely) | 2 (false confidence) | **2** | LOW |

## Step 5: Top 3 Prevent + Actions

**P1 (Score 6): Bypass injection** → Restrict bypass to start of command only: `re.match(r"\s*BULK_DELETE_BYPASS\s*=\s*1\s", command)`

**P2 (Score 6): Stale env var** → Change env var to require explicit per-command opt-in only (remove parent env check)

**P3 (Score 6): Unintentional LLM bypass** → Remove bypass documentation from CLAUDE.md/SKILL.md. Bypass is developer-only escape hatch, not an LLM tool.

## Step 6: Warning Signs

- Gate allows >5 rm -rf operations in single session without blocks
- `pre-delete-*` git tags stop appearing
- `.backup` pattern matches on non-backup paths (check test corpus)

## Edge Case Evidence (from testing)

### Bypass Regex False Positives (CONFIRMED)
```
echo "BULK_DELETE_BYPASS=1 is set"  → MATCHES (SHOULD NOT)
# BULK_DELETE_BYPASS=1              → MATCHES (SHOULD NOT)
```

### .backup Pattern Acceptable Behavior
```
project/.backup       → safe (correct)
project/.backup/      → safe (correct)
project/backup_data   → NOT safe (correct)
project/my-backup     → NOT safe (correct)
project/.backup_old   → NOT safe (correct - \b boundary blocks)
```
