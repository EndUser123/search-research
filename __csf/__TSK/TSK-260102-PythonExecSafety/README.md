# TSK: Python Execution Safety via PreToolUse Hook

**Project ID:** TSK-260102-PythonExecSafety
**Created:** 2026-01-02
**Status:** In Progress
**Type:** Feature Implementation

## Problem Statement

**Issue:** Complex `python -c` commands frequently fail with **exit code 137 (SIGKILL)** on Windows/Git Bash environments.

**Root Cause:**
- Git Bash (MINGW64) provides an emulation layer
- Commands pass through: `bash → MINGW64 → Windows`
- Backslashes, quotes, and Windows paths create escaping nightmares
- Complex strings in `python -c "..."` get mangled during translation

**Impact:**
- Background tasks fail silently
- Long-running operations interrupted
- No clear error messages (just exit code 137)
- User must manually remember to use temp file pattern

## Solution: Automatic PreToolUse Hook

**Approach:** Create `PreToolUse_python_exec.py` hook that automatically converts unsafe `python -c` commands to safe temp file execution.

**Key Benefits:**
1. **Automatic** - No user action required
2. **Transparent** - Works without changing workflow
3. **Safe** - Uses deterministic temp file naming
4. **No cleanup needed** - temp/ directory already in .gitignore

## Project Artifacts

| Artifact | Status | Location |
|----------|--------|----------|
| Research Findings | ✅ Complete | `research.md` |
| Architecture Design | ✅ Complete | `arch.md` |
| Implementation Plan | ✅ Complete | `plan.md` |
| Hook Implementation | Pending | `PreToolUse_python_exec.py` |
| Tests | Pending | `tests/` |
| Documentation | Pending | `doc.md` |

## Tasks

- [x] Research: Verify PreToolUse hook can modify tool inputs
- [x] Document research findings
- [x] Design architecture
- [x] Create implementation plan
- [ ] Implement PreToolUse_python_exec.py hook
- [ ] Test hook with various python -c patterns
- [ ] Update CLAUDE.md with Background Task Safety section
- [ ] Document usage and troubleshooting

## References

- **Research Sources:** See `research.md` for full citation list
- **Related:** `P:/__csf.nip/scripts/exec_python.py` (helper script)
- **Issue:** Background task exit code 137 failures
