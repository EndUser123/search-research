---
title: External repo clone space convention
id: external-repo-clone-space-convention
category: convention
created: 2026-08-06
verified: 2026-08-06
accurate_as_of_head: untracked-wiki
tags: [convention, filesystem-layout, github, cloning]
---

## Rule

External GitHub repositories cloned for reference, study, or integration are cloned to:

```
P:/packages/.github_repos/<repo-name>
```

This is the **canonical clone space** on this host. When the operator says "clone it to our usual clone space," this is the path.

## Why centralized

- **Discoverability**: all cloned repos live in one place, not scattered across `P:/tmp/`, package directories, or the workspace root.
- **Hygiene**: keeps the workspace root clean; `.github_repos` is clearly a reference/material directory, not active project code.
- **Search consistency**: when looking for "that repo we cloned," grep one directory instead of the whole drive.

## Existing occupants (observed 2026-08-06)

| Repo | Path | Purpose |
|------|------|---------|
| stable-diffusion-webui (A1111) | `P:/packages/.github_repos/stable-diffusion-webui/` | Python compat research |
| agent-skills | `P:/packages/.github_repos/agent-skills/` | Claude agent skills reference |
| AI-Multichat-Extension | `P:/packages/.github_repos/AI-Multichat-Extension/` | Multi-LLM aggregator research |
| ParallelChat | `P:/packages/.github_repos/ParallelChat/` | Chinese LLM selectors research |
| big-AGI | `P:/packages/.github_repos/big-AGI/` | Beam merge/rank logic research |
| superpowers | `P:/packages/.github_repos/superpowers/` | Skills source (junction target) |
| i-have-adhd | `P:/packages/.github_repos/i-have-adhd/` | ADHD-friendly output skill |

## Notes

- These are **reference clones**, not active development trees. Active project work uses `P:/projects/` or `P:/worktrees/`.
- If a cloned repo becomes an active dependency (junction target, installed plugin source), note that in the relevant concept rather than moving the clone.
- The directory is dot-prefixed (`.github_repos`) to signal "material/staging" rather than first-class package.

## Related

- [[agent-config-directory-taxonomy]] — where skills/plugins live and what gets scanned
- [[multi-llm-aggregator-landscape]] — several occupants are aggregator research clones
