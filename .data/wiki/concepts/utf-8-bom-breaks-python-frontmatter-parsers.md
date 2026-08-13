---
title: "UTF-8 BOM Breaks Python Frontmatter Parsers"
date: 2026-08-13
tags: [gotcha, python, frontmatter, encoding, bom, skill-scanning]
host: both
confidence: SUPPORTED
source_quality: multi-source
---

# UTF-8 BOM Breaks Python Frontmatter Parsers

## Context

Discovered 2026-08-13 during `/ship-py` run. The `/www` SKILL.md had a UTF-8 BOM
(byte order mark, bytes `EF BB BF`) at the start of the file. This silently broke
`script_scan.py`'s frontmatter parser, producing a false `CRAFT-NO-HOST` finding
on every ship-py run.

## The pattern

Python frontmatter parsers that use `content.startswith("---")` fail when the
file starts with a BOM (`\xef\xbb\xbf---` instead of `---`). The BOM is invisible
in most editors and terminal displays, making it hard to spot. The parser never
enters the frontmatter block, so no fields are detected — producing false
positives for every field check (missing `host:`, missing `name:`, etc.).

## Detection

Check raw bytes, not string content:
```python
bytes = open(path, 'rb').read(3)
if bytes == b'\xef\xbb\xbf':
    print("UTF-8 BOM detected")
```

## Fix

Strip the BOM and write without it:
```python
content = open(path, 'r', encoding='utf-8-sig').read()  # utf-8-sig strips BOM
open(path, 'w', encoding='utf-8', newline='').write(content)
```

Or in PowerShell:
```powershell
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    [System.IO.File]::WriteAllBytes($path, $bytes[3..($bytes.Length - 1)])
}
```

## Prevention

- Write files with `encoding='utf-8'` (no BOM), not `encoding='utf-8-sig'`
- In the scanner, use `content.lstrip('\ufeff').startswith("---")` or read with
  `encoding='utf-8-sig'` to handle BOM-prefixed files gracefully
- Add a BOM check to the scanner itself: if BOM detected, strip it before parsing
  and note it as a finding

## Impact

This was a latent defect — the BOM was pre-existing (predated the session's
edits). Every `/ship-py` run on `/www` was hitting the false positive, but
the skill was always valid. The scanner wasted cycles on a non-defect while
the real validation passed.

## Sources

- ship-py skill-dev phase output (session 019ffb95, 2026-08-13)
- Python docs: `utf-8-sig` codec handles BOM on read/write
- Microsoft docs: PowerShell default encoding historically includes BOM
