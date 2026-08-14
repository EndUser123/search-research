---
title: "'Rules and skills paths: frontmatter now accepts a YAML list of globs', for claude code, what does this mean?"
date: "2026-03-26"
mode: "COPILOT"
uuid: "908beac4-2ba9-41ee-ac66-f5cb03a37bae"
entry_count: 1
---

## Human

"Rules and skills paths: frontmatter now accepts a YAML list of globs", for claude code, what does this mean?

## Assistant

In Claude Code, that changelog line means:

> The `paths:` field in rule and skill frontmatter now accepts a **YAML list of glob patterns**, not just a single string or comma‑separated list.

### What this changes

- **Old style** (roughly): in `.claude/rules/foo.md` or skills you might have written something like:
  ```yaml
  ---
  paths: src/**/*.ts,tests/**/*.ts
  ---
  ```
  i.e., paths as a single comma‑separated string.

- **New style**: you can now use true YAML lists:
  ```yaml
  ---
  paths:
    - "src/**/*.ts"
    - "tests/**/*.ts"
    - "packages/*/src/**/*.py"
  ---
  ```
  This is more flexible and cleaner, especially when you want multiple, readable, or complex globs.[1][3][4]

### What “globs” means here

- A **glob** is a shell‑style pattern like:
  - `*.md` → all Markdown files.  
  - `src/**/*.ts` → all `.ts` files anywhere under `src/`.[3][4]
- The `paths:` list tells Claude:  
  “only apply this rule / skill when files matching any of these glob patterns are in context.”[4][5]

### Practical implication for you

- You can now write more explicit, multi‑line, and readable path scopes in your rules and skills without squeezing everything into one comma string.
- Example use case:
  ```yaml
  ---
  paths:
    - "src/api/**/*.ts"
    - "src/shared/validation/**/*.ts"
  ---
  ```
  This rule then only fires when Claude is working with files in those API/validation directories.[3][4]

If you want, I can sketch a concrete `rules` and `skills` example tailored to your mono‑repo layout.
