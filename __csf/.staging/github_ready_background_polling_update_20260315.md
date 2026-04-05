# GitHub-Ready Skill Update: Background Polling & Video Quality Control

**Date**: 2026-03-15
**Package**: github-ready skill
**Version**: v5.7.0 (proposed)

## Summary

Updated `/github-ready` skill to support background polling for long-running NotebookLM asset generation and improved video quality control to prevent marketing language.

## Changes Made

### 1. Background Polling for Long-Running Assets (NEW SECTION)

**Location**: PHASE 4.7 Media Generation, new subsection "Background Polling for Long-Running Assets"

**What it does**:
- Spawns background polling process that runs for up to 30 minutes
- Polls every 10 seconds to check artifact status
- Downloads each artifact immediately when it completes
- Writes polling progress to state file: `.claude/state/github-ready/polling_state.json`
- Returns immediately after spawning, allowing main skill to continue
- Non-blocking workflow - video generation doesn't block skill completion

**Key features**:
- State file tracking with JSON format
- Auto-download of completed assets
- Progress monitoring via `tail -f .claude/state/github-ready/polling.log`
- Manual download fallback if polling fails
- PID tracking for background process

**State file format**:
```json
{
  "notebook_id": "eddc3d67-d89f-4ec6-b5a8-61d8cd89cad4",
  "package_name": "handoff",
  "started_at": "2026-03-15T00:24:34Z",
  "status": "polling",
  "checks_completed": 18,
  "artifacts": {
    "infographic": {"status": "completed", "id": "...", "downloaded": true},
    "video": {"status": "in_progress", "id": "...", "downloaded": false},
    "slide_deck": {"status": "completed", "id": "...", "downloaded": true}
  }
}
```

### 2. Enhanced Video Brief (UPDATED)

**Problem**: NotebookLM was ignoring the original video brief and generating marketing-heavy scripts with "game changing", "revolutionary", etc.

**Solution**: Made video brief **much more explicit** with:
- **FORBIDDEN WORDS** section listing specific marketing phrases to avoid
- **MANDATORY CONSTRAINTS** section with required technical tone
- **EXAMPLE OF GOOD SCRIPT** showing proper technical language
- **EXAMPLE OF BAD SCRIPT** showing what NOT to do

**Forbidden phrases explicitly listed**:
- "Game changing", "game-changer"
- "Revolutionary", "revolutionize"
- "Seamless", "seamlessly"
- "Transformative", "transform"
- "Empower", "empowering"
- "Leverage", "leverages", "leveraging"
- "Imagine", "picture this", "envision"
- "Gone are the days", "never again"
- 20+ more marketing phrases

**Required tone**:
- Technical, precise, concrete
- Use specific file paths, function names, command examples
- Show actual workflow step-by-step
- Explain what actually happens, not vague benefits

### 3. Video Quality Checklist (NEW)

**Location**: PHASE 4.7, "Quality verification" section

**What it adds**:
- Explicit checklist for video script review
- Forbidden language verification
- Technical content verification
- Regeneration instructions if quality fails

**Quality checklist items**:
- [ ] No "game changing", "revolutionary", "seamless", "transformative"
- [ ] No "empower", "leverage", "harness", "elevate", "streamline"
- [ ] No "imagine", "picture this", "envision"
- [ ] Uses specific file paths, function names, command examples
- [ ] Explains actual workflow, not vague benefits
- [ ] Technical summary ending, NOT call-to-action

### 4. Corrected Asset Generation Commands (FIXED)

**Issue**: Invalid style/format options in original commands

**Fixes**:
- Changed `--style documentary` to `--style whiteboard` (documentary not valid)
- Changed `--slide-format detailed_deck` to `--format detailed_deck` (wrong flag name)
- Added comments explaining valid options

### 5. Updated Duration and Execution Flow (CLARIFIED)

**Changes**:
- Execution flow now includes "Background polling (30min max, non-blocking)"
- Duration updated to show quick assets (2-5min) vs video (5-30min, background)
- Clarifies that video doesn't block workflow completion

## Usage Examples

### Starting background polling

```bash
# After uploading sources and generating assets
# The skill now automatically spawns background polling:
nohup bash .claude/state/github-ready/poll_notebooklm.sh \
  "$NOTEBOOK_ID" "package_name" "/path/to/package" \
  > .claude/state/github-ready/polling.log 2>&1 &

# Monitor progress
tail -f .claude/state/github-ready/polling.log
cat .claude/state/github-ready/polling_state.json | jq
```

### Checking video quality

```bash
# Download and review video
VIDEO_ID=$(cat .claude/state/github-ready/polling_state.json | jq -r '.artifacts.video.id')
nlm download video "$NOTEBOOK_ID" --id "$VIDEO_ID" --output /tmp/review.mp4

# If quality is poor (marketing language), regenerate
# Edit video brief to be more explicit, then:
nlm video delete "$NOTEBOOK_ID" --id "$VIDEO_ID"
nlm video create "$NOTEBOOK_ID" --format explainer --style whiteboard --confirm
```

## Benefits

1. **Non-blocking workflow**: Video generation no longer blocks skill completion
2. **Better video quality**: Explicit brief prevents marketing language
3. **Progress visibility**: State file and log show polling progress
4. **Auto-download**: Assets downloaded immediately when ready
5. **Manual fallback**: Can download manually if polling fails
6. **Quality control**: Checklist ensures videos meet technical standards

## Testing

Tested with handoff package:
- ✓ Background polling script created successfully
- ✓ State file tracking works
- ✓ All assets (infographic, slides, video) downloaded successfully
- ✓ Video brief updated to prevent marketing language
- ✓ Quality checklist added for verification

## Future Improvements

Possible enhancements:
1. Add progress bar display during polling
2. Send notification when all assets complete
3. Auto-cleanup temporary notebook after successful download
4. Add video quality validation with vision API
5. Support custom polling intervals and timeout values

## Files Modified

- `P:/.claude/skills/github-ready/SKILL.md`
  - Added "Background Polling for Long-Running Assets" subsection (~150 lines)
  - Updated "Video Brief" section with explicit forbidden language (~100 lines)
  - Updated "Quality verification" section with checklist (~30 lines)
  - Fixed asset generation command syntax
  - Updated execution flow and duration sections

## Status

✅ **COMPLETE**: Background polling implementation finished and tested
✅ **COMPLETE**: Video quality controls added with explicit brief
✅ **READY**: Skill is ready for use with updated background polling workflow
