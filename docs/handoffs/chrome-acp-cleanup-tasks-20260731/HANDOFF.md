---
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: 019fb933-040b-7720-a257-e364f5df726f
last_updated_at: 2026-08-01T13:10:44.070498
parent_session: none
produced_at: 2026-08-01T13:10:44.070498
status: open
handoff_type: investigation
---
# Chrome ACP — Remaining Cleanup Tasks

## Workstream
Chrome ACP extension maintenance and cleanup. All code work is complete and verified; these are housekeeping tasks for a future session.

## Session
019fb933-040b-7720-a257-e364f5df726f (2026-07-31)

## Status: OPEN (non-blocking — no urgency unless actively using Chrome ACP)

## Tasks

### 1. Delete old `C:\Users\brsth\chrome-acp\` copy
**When:** After confirming `P:\packages\chrome-acp\` works in Chrome (next time the extension is loaded/used).
**Why:** The old copy at `C:\Users\brsth\chrome-acp\` is redundant. All files were migrated to `P:\packages\chrome-acp\` (commit `7149393`). The old copy persists only as a safety net until the new path is confirmed live.
**Command:** `Remove-Item C:\Users\brsth\chrome-acp\ -Recurse -Force`
**Precondition:** Reload extension from `P:\packages\chrome-acp\` in `chrome://extensions` and confirm sidepanel connects + 5 buttons appear next to theme toggle.
**Risk if skipped:** Wastes ~40MB disk; no functional impact (Chrome loads from whichever path is registered).

### 2. Move test suite from `P:\tmp\acp-verify\` to `P:\packages\chrome-acp\tests\`
**When:** Before any `P:\tmp\` cleanup (tests are ephemeral there).
**Why:** The pytest suites (`test_patched_files.py` — 24 tests, `test_re_apply_patches.py` — 15 tests) are in `P:\tmp\acp-verify\` which is ephemeral. They should be tracked in git at `P:\packages\chrome-acp\tests\`.
**How:**
```powershell
New-Item -ItemType Directory -Path "P:/packages/chrome-acp/tests" -Force
Copy-Item "P:/tmp/acp-verify/test_patched_files.py" "P:/packages/chrome-acp/tests/"
Copy-Item "P:/tmp/acp-verify/test_re_apply_patches.py" "P:/packages/chrome-acp/tests/"
# Update SIDEPANEL_JS path constant in test_patched_files.py to point at P:/packages/chrome-acp/dist/
# Update SCRIPT and PATCH_DIR constants in test_re_apply_patches.py
cd P:\; git add packages/chrome-acp/tests/; git commit -m "chrome-acp: move test suite to tracked location"
```
**Note:** The test files reference hardcoded paths (`C:\Users\brsth\chrome-acp\dist\sidepanel-t6n74ra3.js` and `P:\packages\chrome-acp\re-apply-patches.ps1`). Update these to use `P:\packages\chrome-acp\dist\` paths after moving. The `SIDEPANEL_JS` constant in `test_patched_files.py` currently points at the user-dir copy — update to tracked copy.

### 3. (Optional) Live-verify the Feature 8 button placement
**When:** Next time Chrome ACP is actively used.
**What to check:**
- Reload extension from `P:\packages\chrome-acp\` in `chrome://extensions`
- On the disconnected screen, confirm 5 buttons appear next to the theme toggle: ↻ ⏻ 🔧 💡 ⤢
- If buttons don't appear, the "Toggle theme" text selector may need updating based on live DOM
- If `.acp-tc` class isn't on tool-result blocks, the collapse CSS won't apply — check DevTools

## What's already done (don't redo)
- Feature 8 consolidated (button injector next to theme toggle) — commit `661c4f2`
- IIFE extracted to `patches/sidepanel-iife.js` — commit `aa8596e`
- Re-apply script uses Python prepend helper — commit `aa8596e`
- All 4 sidepanel copies hash-identical (`2ebabb48…`)
- 39/39 pytest passing
- Extension moved to `P:\packages\chrome-acp\` — commit `7149393`
- Patch registry wiki updated

## Key files
- Extension source: `P:\packages\chrome-acp\`
- Tracked IIFE: `P:\packages\chrome-acp\patches\sidepanel-iife.js`
- Prepend helper: `P:\packages\chrome-acp\patches\prepend_iife.py`
- Re-apply script: `P:\packages\chrome-acp\re-apply-patches.ps1`
- Tests (ephemeral): `P:\tmp\acp-verify\test_patched_files.py`, `test_re_apply_patches.py`
- Patch registry: `P:/.data/wiki/concepts/chrome-acp-grok-build-setup-implementation.md`

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T13:10 | 019fb933-040... | backfilled session_id from transcript scan |
