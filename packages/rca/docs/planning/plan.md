# rca v2.4.1 - Prescriptive Search Templates Implementation

**Date:** 2026-02-28
**Version:** v2.4.0 → v2.4.1
**Type:** Documentation enhancement

## Objective

Add prescriptive search templates to Step 1.5: Multi-Angle Search to prevent mechanism-only search misses.

## Problem Statement

In a previous bug session, rca v2.4 required only a **mechanism search** (`grep("Progress(")`) which found 4 Rich Progress contexts but missed the **functional search** (`grep("yt-api:")`) that would have found 2 manual stdout writes. This caused a 2-iteration bug.

Current v2.4 describes multi-angle search but doesn't provide **prescriptive templates** for each symptom type, leaving it to human judgment.

## Solution

Add **mandatory search templates** for 5 common symptom types to Step 1.5 in SKILL.md:
1. PERFORMANCE (slow/flashing/timeouts)
2. ERROR (exceptions/crashes)
3. INTEGRATION (cross-component/API)
4. INTERMITTENT (flaky/race conditions)
5. SECURITY (auth/vulnerability)

Each template specifies:
- Mechanism search (how is it implemented?)
- Functional search (what produces visible symptom?)
- Temporal search (what changed recently?)
- Contextual search (what calls it/related code?)

## Acceptance Criteria

- [ ] Add 5 search templates to Step 1.5 in SKILL.md
- [ ] Each template includes 3-4 search angles with concrete examples
- [ ] Templates reference the actual bug session as example
- [ ] Update version from 2.4.0 to 2.4.1
- [ ] No breaking changes to existing functionality

## Tasks

### Task 1: Add Search Templates Section
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** After "### Step 1.5: Multi-Angle Search" (around line 405)
**Change:** Insert new subsection with 5 symptom templates

### Task 2: Update Version
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** Line 6 (version field)
**Change:** Update `version: 2.4.0` → `version: 2.4.1`

## Verification

- [ ] Read updated SKILL.md and confirm all 5 templates present
- [ ] Confirm examples reference the yt-api flashing bug
- [ ] Confirm no existing functionality broken

## Risk Assessment

**Risk Level:** LOW
- Documentation-only change
- No code changes
- No breaking changes to existing workflow
- Templates are additive guidance, not enforced automation

## Rollback

If templates prove ineffective:
- Revert SKILL.md to v2.4.0
- Remove template section
- No code rollback needed
