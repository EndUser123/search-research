---
title: "Session observations — 019fca0e (2026-08-04)"
current_session_id: 019fca0e-9f40-7110-919b-6ee89333f804
parent_handoff_path: none
status: closed
work_status: OBSERVATIONS CAPTURED
created: 2026-08-04
---

# Session observations — plugin evaluation and skill infrastructure

## Observations

1. **Parallel-structure-building tendency.** When building `/ask` (skill router), the agent's first instinct was to create a hardcoded seed table mapping keywords to skills — a parallel structure to the skill graph that already existed in the wiki. The operator caught this: "why use a seed table instead of a wiki?" The root pattern: the agent builds new infrastructure instead of querying existing infrastructure. This is the same class as replacement-before-investigation.

2. **Receipt enforcement gap.** `/ship`'s receipt had LLM-filled fields ("not run", "n/a") that could be skipped without mechanical verification. The fix was receipt-file enforcement (`check_skill_receipts()` searches for `check-run.json` and `FINDINGS.md` files instead of trusting LLM text). This generalizes: any enforcement gate that relies on LLM-filled text fields is advisory, not mechanical. The fix is always to check for artifacts on disk.

3. **Wikilink convention for skill-to-wiki discoverability.** The skill graph builder extracts `[[wikilinks]]` lexically from SKILL.md files. File paths in prose are invisible to it. Convention: use `[[slug]]` wikilinks, not file paths, when referencing wiki concepts in SKILL.md prose. This was added to AGENTS.md as a standing rule and to `/skill-dev`'s create-protocol.

4. **SIE (Signal-Based Intent Expansion) as reusable component.** The `/ask` skill missed `/ship` because keyword extraction was single-domain. The fix was SIE: 3-signal preprocessing (conversation + workspace state + session arc) before routing. SIE was extracted as a wiki concept (`signal-based-intent-expansion.md`) and referenced via `[[wikilinks]]` in `/ask`, `/todo`, `/tp`, `/close`, `/handoff`.

5. **Scanner self-improvement loop.** Running `/skill-dev` on `/skill-dev` revealed that Check 8 (craft quality) was prose-instructed but not scanner-enforced. The fix (Check 7 for LLM-fillable detection, Check 8 sub-checks) was added to `script_scan.py` mechanically. The meta-pattern: skills that instruct scanning should themselves be scanned.

6. **Plugin evaluation methodology.** The mattpocock-skills plugin was evaluated by: install → compare each skill against native fleet → disable duplicates → port useful concepts natively → absorb overlapping functionality. 10 skills disabled, 3 absorbed (`/ask` from ask-matt, `/skill-dev --from-url` from skill-gen, craft quality checks from create-skill). This methodology is reusable for future plugin evaluations.

7. **Display reliability pattern.** `/todo` output had all findings on one line instead of each on its own line. Root cause: LLM hand-formatting markdown is unreliable. Fix: agent emits data (list of dicts), Python renderer formats. Documented in `adaptive-risk-assessment-single-pass-first-architecture.md` § "Display reliability."
