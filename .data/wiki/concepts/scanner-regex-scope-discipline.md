---
title: "Scanner regex-scope discipline: match the data field, not the full file body"
created: 2026-08-05
source: session-019fcd47 (two false-positive bugs found in /todo scanner)
tags: [scanner-design, regex-scope, false-positive, mechanical-validation, transferable-pattern]
agent: grok
host: both
cognitive_load: 1
verification: session-verified
summary: >
  Mechanical scanners that use regex to detect patterns in files must scope
  their regex to the specific data field (verdict line, status header, JSON
  field), not the full file body. Two /todo scanner functions had the same
  bug: scan_critique_log() searched the auto command's formatted stdout for
  outcome keywords, and scan_check_failures() searched the entire file body
  for "FAIL|INCOMPLETE". Both matched instructional/template text ("End with
  VERDICT: PASS or VERDICT: FAIL") instead of actual verdicts, producing
  false positives. The fix: match only the verdict line or the JSON field
  that contains the authoritative data.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: related
  - target: wiki/concepts/mechanical-as-input-not-mechanical-as-frame
    type: related
---

# Scanner regex-scope discipline

## The pattern

When a mechanical scanner uses regex to detect a condition in a file, the regex
must be scoped to the **specific data field** that contains the authoritative
value — not the full file body.

**Correct:** `re.search(r"\*\*Verdict:\*\*\s*CHECK\s+(FAIL|INCOMPLETE)", content)`
— matches only the verdict line.

**Incorrect:** `re.search(r"FAIL|INCOMPLETE", content)` — matches any occurrence
of "FAIL" anywhere in the file, including instructional text, template examples,
and verifier packet descriptions.

## Reference incidents

### Incident 1: scan_check_failures() (2026-08-05)

The `/todo` scanner's `scan_check_failures()` used `re.search(r"FAIL|INCOMPLETE", content)`
on the full file body. Verifier packet templates in the same directory contain
text like `"End with VERDICT: PASS or VERDICT: FAIL"` as instructions to the
verifier agent. The regex matched this instructional text, producing 2 false
positives for every PASS verdict that had verifier packets.

**Fix:** changed to match only the verdict line: `re.search(r"\*\*Verdict:\*\*\s*CHECK\s+(FAIL|INCOMPLETE)")`.
Result: 3 findings → 1 real FAIL (the other 2 were false positives from template text).

### Incident 2: scan_critique_log() (2026-08-05)

The `/todo` scanner's `scan_critique_log()` parsed the `tp_critique_log.py auto`
command's formatted stdout, then filtered by keyword (`"likely-ignored"`,
`"acted-on"`, etc.). But the `auto` command's output format didn't include all
outcome values, so some resolved entries appeared as unresolved.

**Fix:** rewrote to read the raw JSONL directly and filter by the `outcome` field
presence — any entry with an outcome is resolved, regardless of the specific
value. Result: 7 false positives → 0.

## When it applies

Any mechanical scanner that:
1. Reads a file or command output
2. Applies regex or string matching to detect a condition
3. The file contains both data fields AND instructional/template text

## How to prevent it

| Rule | Implementation |
|------|---------------|
| Scope regex to the data field | Use line-level matching, not full-body matching |
| Prefer structured data over text scraping | Read JSONL/JSON fields directly instead of parsing formatted output |
| Test against known-good files | Run the scanner against files that should NOT match (PASS verdicts with verifier packets) |
| Include a false-positive check in the test | If the scanner finds results in a known-clean file, the regex is too broad |

## Falsifier

This pattern is wrong if the files being scanned don't contain instructional
or template text that could trigger false matches. In that case, full-body
regex is fine.

## Cross-references

- [[code-orchestrates-model-judges-skill-scale]] — scanners are deterministic code; their output quality depends on regex precision
- [[mechanical-as-input-not-mechanical-as-frame]] — scanner output feeds model evaluation; false positives erode trust in the mechanical layer
