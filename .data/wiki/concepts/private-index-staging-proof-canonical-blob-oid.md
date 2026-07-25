---
title: "Private-index staging proof for canonical Git blob identity"
concept_type: "technique"
created: 2026-07-25
agent: grok
host: both
cognitive_load: 2
---

# Private-index staging proof for canonical Git blob identity

## Decision

Use `git update-index` in a temporary private index to compute the
authoritative canonical blob OID for a file, rather than `git hash-object`.

## Why

`git hash-object` exits 0 even when a clean filter fails — it logs the
error to stderr but stores the unfiltered blob. This produces a non-
authoritative OID that could falsely match a HEAD blob in foreign-overlap
detection.

Private-index staging (`GIT_INDEX_FILE=<temp> git update-index --add -- <path>`)
exercises the exact same filter pipeline as the real index. If a required
filter fails, `update-index` exits nonzero and no OID is emitted.

## Alternatives rejected

- `git hash-object` + stderr phrase matching: fragile, one English phrase,
  doesn't catch all failure modes
- `git hash-object --path=<relpath>`: still exits 0 on filter failure
- `--no-filters`: deliberately bypasses filters — opposite of what we want

## Falsifier

This approach is wrong if `update-index` in a private index applies different
filters than staging to the real index. No evidence of this found across
autocrlf (true/input/false), .gitattributes (text/eol/binary), custom clean
filters, and required-filter failures.

## Related

- [[external-silent-edit-and-shell-quoting-reports]] — the Class C quoting rule
- ADR-008 — worktree-per-session as the structural isolation fix
