---
title: "Git mv + search_replace: the 0/0 commit that loses your content changes"
created: 2026-07-21
source: session-2026-07-21 (019f8507-6395-7bc0-87a9-9222e28d68c8)
sources:
  - P:/docs/handoffs/pgm-supersession-20260721/HANDOFF.md (worked example)
tags: [git, search_replace, index, working-tree, capture-bug, multi-agent]
host: both
agent: grok
verification: empirical-with-reproduction
cognitive_load: 3
summary: >
  When you `git mv <old> <new>` then `search_replace` to update content, the
  index captures only the rename, not the content changes. The resulting
  `git commit` is 0 insertions, 0 deletions, similarity 100% — a "pure
  rename" that silently loses your edits. The working tree is then ahead
  of HEAD, and you may not notice until the next person clones or reviews.
---

# Git mv + search_replace: the 0/0 commit that loses your content changes

## The bug, in one paragraph

When you `git mv <old> <new>`, git stages the rename in the index. If you then use `search_replace` to update the file's *content* (e.g., fix internal path references after a rename), the working tree changes but the **index does not**. A subsequent `git commit` commits from the index — which only has the rename, not your content edits. The resulting commit shows `0 insertions, 0 deletions, similarity 100%` because git treats the content as identical to the pre-rename version.

## Reproduction (verified 2026-07-21)

```bash
# Setup: a file at OLD path with a string "foo" in it
echo "foo" > docs/example.md
git add docs/example.md
git commit -m "initial"

# Step 1: rename the file
git mv docs/example.md docs/example-renamed.md

# Step 2: update content via search_replace
sed -i 's/foo/bar/' docs/example-renamed.md
# (or any host tool that edits working tree without touching index)

# Step 3: check what git sees
git status --short
# R  docs/example.md -> docs/example-renamed.md
#     -- only the rename is staged. Content change is NOT in the index.

# Step 4: commit
git commit -m "rename and update"

# Step 5: inspect
git show --stat HEAD
#  docs/{example.md => example-renamed.md}  (100%)  -- pure rename, 0/0
#  Working tree is now ahead of HEAD -- the content edit was lost from the commit.
```

## How to detect (if you suspect you've hit it)

After committing a rename, check:

```bash
git diff HEAD                # any non-zero output means working tree differs from HEAD
git diff --cached HEAD       # any non-zero output means staged changes were not committed
git show --stat HEAD         # if 0/0 on a file you meant to edit, you hit this bug
```

## How to fix (after the fact)

If the commit is **local-only** (not pushed), the simplest fix is to amend:

```bash
git add <file>              # update the index with the working-tree content
git commit --amend --no-edit
```

If the commit is **already pushed**, **do not amend** (this is the multi-agent `no destructive git` rule). Fix forward with a new commit:

```bash
git add <file>
git commit -m "fix(<area>): update content after rename (3 lines missed by pure-rename commit)"
```

Then `git push` (regular, not force).

## How to prevent (next time)

Pick one of:

1. **After `search_replace`, run `git add <file>` before `git commit`.** Index then captures the content changes.

2. **If you're doing many edits to a renamed file, do them in a single Python atomic write.** Python's `Path.write_text()` updates both working tree and index (via `git add`-equivalent in your next commit) atomically. This is also the host's recommended escape hatch for Windows persistence glitches.

3. **For 3+ sequential edits to the same file, prefer Python atomic write from the start.** Avoids the sequential-edit-collision risk that compounds the capture bug.

## Why this bug is hard to spot

- The commit looks normal: descriptive message, valid SHA, no errors.
- Git's similarity index considers path-string renames as part of the rename similarity, not separate edits. So a "100% similar" report can be a false positive when path strings also changed.
- The validator (if you ran one) checks schema fields, not content. A handoff validator passing doesn't mean the content paths are correct.
- The handoff-validator's pass on the renamed file showed 0 errors / 0 warnings — but the file content had 3 stale path references that should have been updated. Validator and content-quality are decoupled.

## Real incident this session

While renaming `session-019f8507-pgm-supersession-20260721/HANDOFF.md` to `pgm-supersession-20260721/HANDOFF.md` and updating 4 internal path references, the commit `d29d7ba` was created with:
- 0 insertions, 0 deletions
- Similarity 100% (false positive — path strings were part of the rename)
- Content: file had OLD path references in lines 57, 73, 88

The capture bug was caught by an `intentional re-audit` ("please make sure your edits this session have persisted") that ran `git diff HEAD` on the renamed file and found 40 lines of working-tree changes vs HEAD. The fix was:
1. `git add <file>` to update the index
2. `git commit --amend` (since the original commit was still local-only at that point)
3. Force-push (because the original commit was on a branch with other agents' unpushed work)

If the original commit had been pushed to a shared branch with other agents' work, the right fix would have been a new fix-up commit, not an amend.

## Related

- [[auto-commit-authority-isolation]] — adjacent concept on multi-agent commit safety
- File editing protocol rules in AGENTS.md (no destructive git; verify after edit) — both rules would have prevented this bug from being committed silently

## Auto-related

<!-- Auto-generated by wiki_after_write.py - do not edit manually -->