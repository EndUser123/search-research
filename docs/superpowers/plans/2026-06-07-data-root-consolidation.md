# Data Root Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate runtime data under `P:\.data`, update code to read and write there, and remove stale duplicate copies from `P:\__csf`.

**Architecture:** Treat `P:\.data` as the only canonical runtime data root. Keep code changes limited to explicit path builders so existing behavior stays the same except for the base directory. Move only the unique live data into the canonical root, then delete stale duplicate databases and state files from the legacy tree after verifying the destination copies are present.

**Tech Stack:** PowerShell filesystem moves, Rust path constants, Python path builders, SQLite-backed runtime state.

---

### Task 1: Update canonical path builders

**Files:**
- Modify: `P:/packages/claude-history/src/cli.rs`
- Modify: `P:/__csf/scripts/build_cks_compressed_rag.py`

- [ ] **Step 1: Replace `P:/__csf/data/chat_history.db` with `P:/.data/chat_history.db` in the Rust default path.**
- [ ] **Step 2: Change the CKS database/index helper to resolve from the repo root into `P:/.data/cks.db` and `P:/.data/cks/memory_efficient_rag`.**
- [ ] **Step 3: Run a targeted search to confirm there are no remaining code references to the legacy `P:/__csf/data` paths.**

### Task 2: Move live data and prune redundant copies

**Files:**
- Move: `P:/__csf/data/*` into `P:/.data/`
- Move: `P:/__csf/.data/*` into `P:/.data/`
- Delete: redundant legacy files left behind in `P:/__csf/data` and `P:/__csf/.data`

- [ ] **Step 1: Move the large live databases and unique runtime state into `P:/.data`, preserving subdirectory structure where needed.**
- [ ] **Step 2: Keep the canonical copies in `P:/.data` when a stale duplicate exists in `P:/__csf`, and delete the stale duplicate only after the destination copy is confirmed present.**
- [ ] **Step 3: Delete the obsolete small `chat_history.db` duplicate and any other redundant left-behind files once the canonical data is in place.**

### Task 3: Verify the consolidation

**Files:**
- Test: `P:/packages/claude-history/src/cli.rs`
- Test: `P:/__csf/scripts/build_cks_compressed_rag.py`

- [ ] **Step 1: Run targeted path-search checks to confirm the only remaining live references point at `P:/.data`.**
- [ ] **Step 2: Confirm the moved SQLite files still open and expose the expected schemas from the new location.**
- [ ] **Step 3: Confirm `P:/__csf/data` and `P:/__csf/.data` no longer contain redundant data after the move.**
