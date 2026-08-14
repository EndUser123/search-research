# Handoff: Session improvement backlog from 019ffb95

## Status
OPEN — not started

## Objective

Implement 4 improvement items identified in /tp improve analysis that need
design work beyond this session's scope.

## Items

### 1. Wire pick_model.py into ship-py dispatch infrastructure
**Effort:** M. **Confidence:** H.

The orchestrator dispatches models via `dispatch_base.py` and `*_dispatch.py`
files with hardcoded or manually-passed slugs. These should call
`pick_model.py <lane>` programmatically to select models at dispatch time.

**Files:** `ship-py/__lib/dispatch_base.py`, `ship-py/__lib/*_dispatch.py`

### 2. Add cross-cutting pattern escalation to /tp meta-checkpoint
**Effort:** S. **Confidence:** M.

The /tp meta-checkpoint should ask: "did this session apply the same fix to
multiple instances? Is there a pattern worth capturing?" This session had 4
instances of value-conditional automation before I recognized the pattern.

**Files:** `tp/SKILL.md` (meta-checkpoint section, AGENTS.md)

### 3. Add severity-conditioned action manifest
**Effort:** M. **Confidence:** H.

From XMPro deontic pattern: Low→allow+log, Medium→ask+recommend,
High→deny+alert. Maps to AGENTS.md action manifest table.

**Files:** `~/.grok/AGENTS.md` (action manifest section)

### 4. PreToolUse hook for python -c nested quote detection
**Effort:** L. **Confidence:** M.

Detect Class C quoting hazard before execution and auto-rewrite to temp
script. Hit 3 times this session.

**Files:** New hook in `~/.grok/hooks/`

## Acceptance criteria

- [ ] dispatch_base.py calls pick_model.py for lane selection
- [x] /tp SKILL.md includes explicit pick_model.py critic spawn procedure (DONE — commit c43dde2)
- [ ] /tp meta-checkpoint includes cross-cutting pattern question
- [ ] AGENTS.md action manifest has severity dimension
- [ ] PreToolUse hook detects and rewrites python -c nested quotes

---

## Revision 1 — 2026-08-13T22:35:00Z (session 019ffb95)

**Trigger:** auto-update — item 3 partially completed this session.

**What changed:**
- ✅ **Item 3 (pick_model.py into /tp):** DONE. Added explicit procedural step to /tp SKILL.md Step 2 spawn table: "Run pick_model.py critic --selection-mode weighted_pool and parse the returned slug." Fixed non-existent `--exclude-self` flag. Commit `c43dde2`.
- ⏳ **Item 1 (pick_model.py into ship-py dispatch):** Not started. Still the root cause of the refactor-phase dispatch failure (unresolvable model `or-nvidia-nemotron-nano-9b-v2-free`).
- ⏳ **Item 2 (cross-cutting pattern escalation):** Not started.
- ⏳ **Item 3b (AGENTS.md severity manifest):** Not started.
- ⏳ **Item 4 (python -c quoting hook):** Not started.
