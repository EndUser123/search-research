## Porting plan: Claude → Grok skill gaps by domain priority

### Priority 1 — Zero-coverage gaps (must port)

**Deployment/Ship (0 Grok skills)**

| Skill | What | Effort | Adaptation notes |
|---|---|---|---|
| `ship` | Deploy readiness + runtime snapshot | ~1h | Pre/post deployment validation. Adapt for Grok's `config.toml` + no Claude settings. |

### Priority 2 — Weak coverage gaps (high ROI)

**Testing/QA (2 skills, missing the "during" phase)**

| Skill | What | Effort | Adaptation notes |
|---|---|---|---|
| `tdd` | RED/GREEN cycle enforcement, mutation gate | ~1.5h | Grok has superpowers' `test-driven-development` but it's instructions-only; `tdd` enforces the cycle with gates. |
| `diagnose` | Structured diagnostic protocol (hypothesis testing) | ~1h | Complements `/debugging-and-error-recovery` with structured hypothesis ordering. |
| `trace` | Manual trace-through verification for code/skills/docs | ~1h | F7 control-flow trace pattern. Works on any host. |

**Design/Architecture (1 skill, needs depth)**

| Skill | What | Effort | Adaptation notes |
|---|---|---|---|
| `decision-tree` | SDLC decision engine (architecture, incidents, refactors) | ~1.5h | Routes to the right approach before implementation. No Claude deps. |
| `constraints` | Show active project constraints from AGENTS.md | ~30min | Parse AGENTS.md rules, surface as structured list. Simple. |
| `evolve` | Modernization workflow (working code → high-standard) | ~1.5h | Deeper than `/refactor`; includes test characterization. |

### Priority 3 — Moderate coverage gaps (worth porting)

**Implementation (4 Grok, missing core dev tools)**

| Skill | What | Effort | Adaptation notes |
|---|---|---|---|
| `code` | Feature dev mission control (single-task TDD engine under /go) | ~2h | Adapt for Grok's `/go` instead of Claude's task system. |
| `tldr-code` | Token-efficient code analysis (5-layer: AST, call graph, CFG, DFG, PDG) | ~2h | Pure Python analysis; no Claude deps. High value for large codebases. |
| `tldr-overview` | Token-efficient project overview | ~1h | Companion to `tldr-code`. |
| `tldr-deep` | Full 5-layer analysis of a specific function | ~1h | Companion to `tldr-code`. |
| `tldr-router` | Maps questions to the right tldr command | ~30min | Companion to `tldr-code`. |
| `tldr-stats` | Token usage, costs, TLDR savings | ~30min | Companion to `tldr-code`. |

### Priority 4 — Maintenance enhancements (identified earlier)

| Skill | What | Effort | Adaptation notes |
|---|---|---|---|
| `stale` | Find docs out of date vs code changes | ~1h | Compare wiki concept `created:` dates against git log for referenced files. |
| `skill-audit` | Audit skill against quality rubric | ~1.5h | Complements `/skill-prune`. Checks SKILL.md structure, references, triggers. |
| `skill-similarity` | Find similar skills by keywords/deps | ~1h | Powers `/skill-prune` dedup suggestions. |
| `snapshot` | Session snapshot capture/restore | ~1.5h | Grok has compaction but snapshots are point-in-time, not summarized. |
| `debt` | Lazy-closure-debt audit log viewer | ~30min | Read-only JSONL viewer. Simple. |
| `capture` | Extract durable knowledge from changes | ~1h | Overlaps with `/wiki`; may merge instead. |

### Priority 5 — Claude-specific (port with heavy adaptation or skip)

| Skill | Why it's hard | Recommendation |
|---|---|---|
| `cks` | Constitutional Knowledge System — Claude-specific state | Skip (use qmd + wiki instead) |
| `skill-write` | Unified create-side tooling | Merge into `/create-skill` |
| `sqa` | 11-layer quality pipeline with Claude-specific agents | Port if quality needs are high; large effort ~3h |
| `claude-automation-recommender` | Recommends Claude-specific automation | N/A for Grok |
| `video-vision` / `vision-analysis` / `yt-nlm` / `yt-is` / `yt-selenium` | Claude media pipeline | Already in `cc-skills-media` (disabled in Grok). Enable or port individually. |

### Totals

| Priority | Skills | Est. effort |
|---|---|---|
| P1 (must) | 1 | ~1h |
| P2 (high ROI) | 6 | ~6.5h |
| P3 (moderate) | 6 | ~6.5h |
| P4 (maintenance) | 6 | ~6h |
| P5 (heavy/skip) | ~7 | variable |
| **Total to port** | **19-26** | **~20-25h** |

### Recommended sequence

1. **This session (if continuing):** P1 (`ship`) + P2 constraints (`constraints` — 30min, simplest)
2. **Next session:** P2 batch (`tdd`, `diagnose`, `trace`, `decision-tree`, `evolve`) — 5 skills, ~6h
3. **Following session:** P3 batch (`tldr-*` family + `code`) — 6 skills, ~6.5h
4. **Maintenance session:** P4 batch — 6 skills, ~6h
5. **As needed:** P5 — evaluate case by case

This isn't a single-session job. It's 3-4 focused sessions at ~6h each, or a `/go` execution against a plan. Want me to write this as a handoff for the next session, or start on P1+P2 now?
