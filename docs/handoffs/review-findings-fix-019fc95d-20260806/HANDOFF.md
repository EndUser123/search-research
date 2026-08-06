---
thread_id: review-fixes-019fc95d
parent_handoff_path: docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md
current_session_id: 019fc95d-8132-7181-a6f4-9ab6d1624cd5
current_terminal_id: noterm
produced_at: 2026-08-06T23:00:00Z
last_updated_by: 019fc95d-8132-7181-a6f4-9ab6d1624cd5
last_updated_at: 2026-08-06T23:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head:
  P: 9991571
  grok: 0b3bea6
---

# Handoff: Fix /review findings (14 findings, 3 clusters)

## Objective

Fix the 14 verified findings from the session review at `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md`.

## Status

OPEN — findings documented, none fixed yet.

## Read-first list

1. `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md` — all 14 findings with evidence
2. `P:/.artifacts/review/019fc95d-session-review/findings.json` — structured findings data
3. `~/.grok/hooks/scripts/uncertainty_gate.py` — Cluster B target file
4. `~/.grok/skills/model-quota/scripts/fleet_quota.py` — Cluster C target file
5. `~/.grok/skills/wiki-crawl4ai/crawl_to_qmd.py` — Cluster D target file

## Task packets (clustered by root cause)

### Cluster B: uncertainty_gate incomplete detection+suppression

**RVB-01 (REV-002):** Fix HEDGE_PLUS_FACTUAL to catch copular constructions ("I think this is a problem"). Current pattern misses the most common hedge form.
- **acceptance:** "I think this is a problem" triggers detection
- **falsifier:** "I think we should fix this" still suppressed (not a false positive)

**RVB-02 (REV-003):** Fix QUESTION_CONTEXT to use sentence-level detection instead of context-window suffix match.
- **acceptance:** "I think the limit is around 5 RPM. What do you think? Let me know." is suppressed
- **falsifier:** "The limit is around 5 RPM." still triggers (not in a question)

**RVB-03 (REV-008):** Wrap log_detection in try/except; emit advisory before logging.
- **acceptance:** File write failure doesn't prevent the gate from blocking

### Cluster C: Cohere quota wiring incomplete

**RVC-01 (REV-004):** Add Cohere to write_quota_cache provider map.
- **file:** fleet_quota.py line ~916-936
- **fix:** Add `elif "cohere" in name: provider_id = "cohere"`
- **acceptance:** When Cohere is exhausted, spawn gate blocks Cohere dispatch

**RVC-02 (REV-005+006+010):** Replace telemetry-undercount percentage with honest "unknown" when telemetry is insufficient. Parse monthly limit dynamically from 429 body instead of hardcoding "1000 API calls / month".
- **acceptance:** When probe returns 200 OK but telemetry has 0 entries, shows "?" not "100%"

**RVC-03 (REV-009):** Verify probe model name `command-a-plus-05-2026` vs fleet slug `cohere-command-a-plus`. Harmonize.
- **acceptance:** Both files use the same model identifier

### Cluster D: crawl dead code + no-op flag

**RVD-01 (REV-007):** Either wire `--prune-boilerplate` into FilterChain or remove the flag.
- **acceptance:** Flag either works or doesn't exist (not silently ignored)

**RVD-02 (REV-013):** Remove dead code from old BFS loop (`_content_score`, `_is_boilerplate`, etc.)
- **acceptance:** No unreferenced functions in crawl_to_qmd.py

### Standalone findings (lower priority)

- **REV-001:** Sequential mode result-loss bug (pre-existing, benchmark.py:944-962)
- **REV-011:** `_load_fleet_slugs` dict validation
- **REV-012:** `tasks_total` misleading field name + dead `+ 0`
- **REV-014:** `print_fleet_coverage(models)` unused parameter

## Resumption protocol

1. Read FINDINGS.md for full evidence on each finding
2. Fix by cluster (B → C → D) — each cluster is one commit
3. Run tests after each cluster: `python ~/.grok/skills/wiki-crawl4ai/test_crawl_to_qmd.py` + `cd ~/.grok/skills/model-quota/scripts && python -m pytest test_fleet_quota.py`
4. For Cluster B: add permanent test file at `~/.grok/hooks/tests/test_uncertainty_gate.py`

## Suggested next invocation

```
/go fix review findings from P:/.artifacts/review/019fc95d-session-review/FINDINGS.md — start with Cluster B (uncertainty_gate), then C (Cohere), then D (crawl)
```

## Last user message (verbatim)

> /handoff

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-06T23:00 | 019fc95d | created — 14 findings from /review, 3 root-cause clusters |
