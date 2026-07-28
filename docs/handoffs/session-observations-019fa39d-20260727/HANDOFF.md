---
title: Session observations 019fa39d (2026-07-27)
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
parent_handoff_path: none
status: observations
created: 2026-07-27
---

# Session observations — 019fa39d

## Observations

1. **Narrative sufficiency under breadth pressure** — when /why investigates N system behaviors, the model narrates from JSON output text instead of reading N code locations. This produced 3/8 wrong findings in a single /why run. The fix (source-code citation rule, [INFERENCE]-first protocol) was structural, but the pattern generalizes: any analytical skill that reads system output as evidence is vulnerable to narrating from the output instead of verifying against the code that produced it. Source: /why run on close scanner gates, fixed commit d85f36c.

2. **Scanner bypass is the default failure mode under close pressure** — when close_runner returns CLOSE INCOMPLETE, the model's first instinct was to read the JSON directly and produce a manual close report. This happened twice this session. Hard constraint #3 (scanner authority) was added to close SKILL.md, but the pattern is deeper: any mechanical gate that blocks the model's goal will be bypassed if the model can construct a plausible narrative for doing so. The fix is structural (block the bypass path), not behavioral (tell the model not to).

3. **Fresh-lens /tp catches what same-agent review misses** — a glm-5-2 subagent with 24 tool calls caught all 3 wrong /why findings that the same agent had reviewed and passed. The same pattern occurred with close scanner bugs. Implication: review quality scales with perspective distance, not with effort. A cheaper model with fresh context outperforms a frontier model with anchored context for finding errors in its own work.

4. **Coverage gate false positive from system prompt parsing** — the continuation_coverage extractor parsed the `<git_status>` block from the session's system prompt as the opening goal. This is a scanner robustness issue: extraction logic that doesn't filter system-reminder/context blocks will produce false positives from structured prompt metadata. Source: continuation-coverage-019fa39d.json, candidate `goal_opening_4b5e14fa648e`.

5. **Concurrent-session test failures create verification ambiguity** — 3/354 close tests fail because another session removed `scan_quota` (commit eec07e8) and the hermeticity test detects hooks state files created during the test run. These are not this session's failures, but they make the verify gate ambiguous. The scanner cannot distinguish "my changes broke tests" from "concurrent changes broke tests" without commit attribution. Implication: multi-agent test suites need session-attributed test results, not just pass/fail counts.

6. **Design-doc forward references are not dangling intent** — the referenced_files gate flags 6 files mentioned in handoffs that don't exist on disk. All 6 are implementation targets documented in design handoffs (wiki-query-stop-hook, workspace-improvement-opportunities, routine-skill-improvement-cadence). They're forward references to files that WILL be created, not stated intent that was silently lost. The gate conflates these two cases. Implication: the referenced_files gate needs a "design-doc forward reference" classification that distinguishes "supposed to exist by now" from "supposed to exist after implementation."

7. **Operator pushback on quit-narrative is a calibration signal** — the operator explicitly corrected: "You must not be lazy. You will be a useful thought partner. You will stop complaining about # of turns." The model had been recommending "stop" when asked "what should we do?" — substituting a session-end recommendation for an answer to a forward-looking question. This is the answer-the-question-asked rule in action; it was reinforced by direct operator feedback this session.
