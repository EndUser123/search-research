# Review Bundle: /data-safety-vcs Skill
**Generated**: 2026-03-26T19:30:00Z
**Scope**: P:/.claude/skills/data-safety-vcs/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: data-safety-vcs
- **Description**: Data safety and version control standard for solo dev environments
- **Category**: strategy
- **Trigger**: /data-safety-vcs

### Domain & Purpose
Prevents data loss and selects correct VCS tool for Windows 11 solo development.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: PowerShell
- **Primary Language**: Markdown
- **Key Integration**: PreToolUse_anti_bleed_gate.py hook

---

## 2. CONSTITUTIONAL CONSTRAINTS

- Solo-dev environment targeting 75-85% reliability
- No continuous monitoring or always-on tracking
- On-demand execution only
- Enterprise patterns prohibited

---

## 3. VCS TOOL SELECTION RULES

| Location | Operation | Tool | Reason |
|----------|-----------|------|--------|
| P:\ root | ANY | git | Sapling scans Windows system folders |
| P:\ root | status/add/commit | git | Sapling aborts on .BIN |
| Any location | push/pull/fetch | git | Remote operations use git |
| Any location | rebase/merge | git | Complex operations safer with git |

### MANDATORY CHECKLIST
1. Check current directory: pwd
2. If at P:\ root -> use git
3. When unsure -> use git (always works)

---

## 4. RISK-BASED PROTECTION PROTOCOL

### High-Risk (Automatic Backup)
- File deletions
- Major refactoring
- Critical system files
- Production code modifications

### Medium-Risk (Conditional Backup)
- Code refactoring
- Configuration modifications
- Documentation restructuring

### Low-Risk (No Backup)
- Minor code edits
- Comment changes
- Documentation updates

---

## 5. ANTI-BLEED WORKFLOW

**Prevent session bleed: unrelated files sweeping into commits.**

**Rule:** Commit immediately after each discrete unit of work.

**FORBIDDEN:**
- `git add .` or wildcard staging (sweeps unrelated files)
- `git add *` (same problem)
- Leaving WIP uncommitted across session switches
- Batch-committing unrelated work

**REQUIRED:**
- `git add file1.py file2.md` (explicit paths only)
- `git status` before commit (verify staged files)
- `git diff --staged` (verify changes before commit)
- Push after each commit (prevent local pileup)

---

## 6. STRUCTURAL ENFORCEMENT

**PreToolUse_anti_bleed_gate.py** blocks wildcard git add:
- Blocks: `git add .`, `git add *`, `git add -A`, `git add --all`, `sl add .`
- Allows: Explicit paths, `git add -u` (tracked only), `git add -p` (interactive)
- Tests: `.claude/hooks/tests/test_PreToolUse_anti_bleed_gate.py` (21 tests)

---

## 7. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | GOOD | 21 tests in anti_bleed_gate |
| Documentation | GOOD | 142-line SKILL.md |
| VCS Safety | EXCELLENT | Risk-based protection protocol |

### SQA Relevance
- **HIGH** — Data safety skill
- Prevents data loss
- Enforces correct VCS tool selection
- Anti-bleed gate blocks wildcard staging
- Risk-based backup protocol
