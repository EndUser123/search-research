---
title: "claude code showed me this error and option:
 Issue 2: Stale Editable Install (MEDIUM PRIORITY)

  Python is importing"
date: "2026-01-25"
mode: "COPILOT"
uuid: "df1b5096-0c51-456d-99cb-416bb66d0b05"
entry_count: 1
---

## Human

claude code showed me this error and option:
 Issue 2: Stale Editable Install (MEDIUM PRIORITY)

  Python is importing from w1t1 worktree instead of w2t1 because user site-packages has a stale .pth file
  pointing to w1t1. The timeout fix IS in w1t1 (it was merged from main), so that's working, but you're
  running old code.

How do we fix this problem?  I want edits in teh worktree that Claude Code is owrking in.

## Assistant

I understand the issue—Claude Code is working in one worktree (`w2t1`) but Python is still importing the stale editable install from another worktree (`w1t1`). This is a classic `.pth` file mismatch problem. Here's how to fix it:

## The Problem

When you do `pip install -e .` in a worktree, it creates a `.pth` file in your `site-packages` that points to that specific worktree location. If you later create a new worktree and work there with Claude Code, Python still loads from the old `.pth` path.

## Solutions (in order of preference)

### Option 1: Use `pip install -e` in the Active Worktree (Cleanest)

```powershell
# In w2t1 (your current Claude Code worktree)
cd w2t1
pip install -e .
```

This overwrites the `.pth` file to point to `w2t1`. Verify it worked:

```powershell
# Check which path Python is using
python -c "import w1t1; print(w1t1.__file__)"
```

Should show `w2t1` path now.

***

### Option 2: Manually Clean the .pth File (If pip install fails)

Find and remove the stale `.pth` file:

```powershell
# Locate site-packages
python -c "import site; print(site.getsitepackages())"

# Then manually delete the .pth file pointing to w1t1
# It's usually named something like: w1t1.pth or w1t1-link.pth
# Location: C:\Users\YourUser\AppData\Local\Programs\Python\Python3.x\Lib\site-packages\
```

Then reinstall in w2t1:
```powershell
cd w2t1
pip install -e .
```

***

### Option 3: Use Virtual Environment Per Worktree (Most Robust)

If you're planning to frequently switch between worktrees, use separate venvs:

```powershell
# In w2t1
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

Then configure Claude Code to use that venv. This completely isolates dependencies.

***

### Option 4: Check the .pth File Directly

```powershell
# Find all .pth files
Get-Content (python -c "import site; print(site.getsitepackages()[0])")/*.pth | findstr w1t1
```

If found, edit or delete it to remove the `w1t1` reference.

***

## Quick Validation

After applying the fix, verify Python imports from the correct worktree:

```powershell
python -c "import sys; import w1t1; print(f'Importing from: {w1t1.__file__}')" 
# Should show w2t1 path

# Also check what's actually in sys.path
python -c "import sys; [print(p) for p in sys.path if 'w' in p.lower()]"
```

***

## Recommendation for Your Workflow

Given you run multiple Claude Code terminals (5-6 concurrent), **Option 3 with separate venvs** prevents future collision issues. Each worktree/Claude session gets its own isolated Python environment, so edits always apply to the active context.

Which approach fits your workflow best—quick fix now (Option 1) or preventing future issues (Option 3)?
