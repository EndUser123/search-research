# Next SDLC Workstream Evaluation

**Date:** 2026-07-13
**Based on:** Corrected audit packet (P:/docs/sdlc-audit-final-corrected-packet.md), Debrief lifecycle investigation (P:/docs/debrief-evidence-lifecycle-investigation.md), Dream-state concurrency report (P:/docs/dream-state-concurrency-report.md)
**Repository HEAD:** `6807a6710277a1db2d897631ce74e55084c5b0cf`

---

## Candidate Evaluation

### C1: Recommendation ownership across /recap, /rns, /debrief chain, /go

| Dimension | Evidence |
|---|---|
| **User-facing failure** | None reproduced. All outputs are advisory chat. No programmatic consumer reads any of them. |
| **Consumed sources** | `/rns`: pure LLM skill (15KB SKILL.md, no runtime). `/recap`: `recap_v2.py:1557-1576` calls local `__lib/render_rns.py` for handoff formatting. `/go`: own prioritization via task queue, zero references to RNS. `/debrief chain`: LLM-driven protocol. |
| **Writer → Storage → Reader** | Multiple writers, all conversational/terminal-display. No machine-readable output from any. |
| **Freshness/scope** | Per-session. All outputs are ephemeral (re-created per invocation). |
| **Downstream consumer** | None programmatic. Only human user. |
| **Documented/source/live** | Source-visible (recap's render_rns.py docstring says "rns skill is being dissolved" but the skill is alive). Live behavior confirmed: /rns has no runtime = no machine output. |
| **Expected improvement** | None — no consumer collision exists. Outputs are advisory and terminal-display-only. |
| **Cost** | Low for docs, high for structural change (would require deciding /rns backend strategy). |
| **Safest failure** | Current behavior (continue). |

**Audit verdict:** `NO_CHANGE` — confirmed correct. No remaining work justifies investigation.

### C2: Readiness-routing clarity across /check, /risks, /review, /red-team, /epistemic-check

| Dimension | Evidence |
|---|---|
| **User-facing failure** | None reproduced. Each surface has distinct input scope (git diff vs proposal text vs code files vs adversarial multi-agent vs response format). SKILL.md files document relative positioning. |
| **Consumed sources** | `/check`: cc-skills-lab multi-phase runtime engine. `/risks`: cc-skills-sdlc, `allowed-tools: []` (no runtime). `/review`: cc-skills-sdlc LLM. `/red-team`: red-team plugin multi-agent engine. `/epistemic-check`: cc-skills-analysis LLM. |
| **Writer → Storage → Reader** | All conversational. No cross-consumption. |
| **Freshness/scope** | Per-invocation. Incompatible input domains prevent accidental misuse. |
| **Downstream consumer** | None programmatic. Only human user. |
| **Documented/source/live** | Source-documented. Each `/risks` SKILL.md positions itself relative to siblings (lines 24-30). |
| **Expected improvement** | Marginal — adding routing doc would not change behavior. User confusion not proven. |
| **Cost** | Low for documentation, zero for behavior. |
| **Safest failure** | Current behavior (continue). User invokes wrong surface → corrects via experience. |

**Audit verdict:** `NO_CHANGE` — confirmed correct.

### C3: Persistence and authority of design decisions

| Dimension | Evidence |
|---|---|
| **User-facing failure** | Source-visible risk only. `genius` produces design thinking but produces no artifact. No DecisionRecord schema exists. No consumer exists. |
| **Consumed sources** | `/design`: cc-skills-sdlc, LLM with templates, produces ADR-like output. `/genius`: cc-skills-thinking, pure LLM, conversational output with no artifact contract. `/council`: multi-LLM deliberation. `/improve`: artifact review. |
| **Writer → Storage → Reader** | `/design`: conversational (unless user copies output). `/genius`: conversational only. `/council`: deliberation transcript. No persistent DecisionRecord. |
| **Freshness/scope** | Per-session, all conversational. Lost on compaction. |
| **Downstream consumer** | None — no DecisionRecord schema exists for any consumer to read. |
| **Documented/source/live** | Source-documented as risk (corrected audit packet R1). No live failure reproduced. |
| **Expected improvement** | Unclear — no consumer exists. Adding schema would create a file without readers. |
| **Cost** | Low for schema document, high for consumer integration. |
| **Safest failure** | Current behavior (continue). Decisions made in chat are lost on compaction but can be re-derived from transcript. |

**Audit verdict:** `BLOCKED_EVIDENCE_INSUFFICIENT` — no consumer exists. Confirmed.

### C4: Loss of useful conversational outputs across compaction

| Dimension | Evidence |
|---|---|
| **User-facing failure** | This is the most plausible real friction. Session compaction drops most conversation context. The handoff template's "Resume Here" and "Decisions" sections explicitly exist to mitigate this, which proves the problem is acknowledged. But: |
| **Consumed sources** | Snapshot plugin (`PreCompact_snapshot_capture.py`) writes JSON handoff. `/recap` writes markdown handoff. Transcript (`.jsonl`) is authoritative. |
| **Writer → Storage → Reader** | JSON handoff: snapshot plugin → `~/.claude/state/handoff/` → chain walker (metadata only, ≤5min fresh). Markdown: /recap LLM → conversational → next session LLM (advisory, lossy). |
| **Downstream consumer** | JSON handoff: consumed by chain walker. Markdown: consumed by next session's LLM (through conversation history). |
| **Documented/source/live** | Live behavior — happens on every compaction. But this is a fundamental platform constraint (context window), not a skill topology issue. The existing mitigation (snapshot + handoff chain) is already in place and working by-design. |
| **Expected improvement** | Better handoff content fidelity would improve resume quality. But any improvement requires either: (a) changes to the snapshot plugin's capture scope, (b) changes to the chain walker's session boundary detection, or (c) changes to context window limits — all outside the SDLC topology scope. |
| **Cost** | High — touches snapshot plugin, session chain, and platform context management. |
| **Safest failure** | Current behavior (continue with lossy resume). |

**Verdict:** Out of scope for SDLC topology changes. This is a platform constraint managed by the snapshot plugin and session chain. No SDLC skill-surface change would materially improve it.

### C5: Dormant registration mechanisms (R4 from corrected packet)

| Dimension | Evidence |
|---|---|
| **User-facing failure** | None reproduced. Three registration mechanisms exist but all inspected hooks are either live (correctly registered) or dormant (correctly unregistered). No hook was accidentally double-registered or missed. |
| **Consumed sources** | settings.json → router.py (plugin), SKILL.md frontmatter (skill), hooks.json (skill). |
| **Writer → Storage → Reader** | All three mechanisms are documented in various SKILL.md files. No central index. |
| **Expected improvement** | A central hook registry would prevent future registration errors but would not fix any current failure. |
| **Cost** | Medium — would require an audit script and maintenance. |
| **Safest failure** | Current behavior (continue). Registration is manually inspected per hook. |

**Audit verdict:** `BLOCKED_EVIDENCE_INSUFFICIENT` — no live problem to fix.

---

## Ranking

| Rank | Candidate | Proof level | Expected impact | Cost | Verdict |
|---|---|---|---|---|---|
| 1 | C4 (compaction loss) | Live behavior (happens every session) | High (resume quality) | High (platform, not topology) | Out of scope |
| 2 | C3 (design decision persistence) | Source-visible risk only | Medium (fewer re-derivations) | Low schema + no consumers | No demand proven |
| 3 | C2 (readiness routing) | Source-documented only | Low (marginal improvement) | Low (docs only) | No failure |
| 4 | C5 (registration mechanisms) | Source-visible risk only | Low (future-proofing) | Medium | No current failure |
| 5 | C1 (recommendation ownership) | Source-visible + live confirmed | None (no consumer collision) | Low | Already by-design |

No candidate scores high on both impact and proven demand. The highest-impact candidate (C4) is out of scope for SDLC topology work. No candidate meets the bar for a new workstream.

---

## Conclusion

`NO_FURTHER_WORK_JUSTIFIED`

Every remaining candidate from the corrected SDLC topology audit and the debrief evidence-lifecycle investigation has been evaluated against the criteria:

- **Proven user or workflow impact:** None reproduced. All identified risks are source-visible or by-design.
- **Frequency:** Low — no recurring user-facing failure was found in any investigation.
- **Breadth of downstream effect:** All candidates affect only advisory outputs or dormant code.
- **Reversibility:** All proposed changes would be documentation or schema changes, which are reversible. But no change is justified because no failure exists to fix.
- **Implementation and attention cost:** The highest-value candidate (compaction loss) is a platform constraint outside the SDLC topology scope.

The two investigations (topology audit + lifecycle investigation) have exhausted the high-value candidates. The system works reliably in its critical paths. The dormant mechanisms duplicate active capabilities. The one reproducible race condition is benign under current consumers. No remaining workstream would materially improve user outcomes.

If conditions change (e.g., dream state gains an automated consumer, /rns gains a Python backend, transcripts become directly queryable at a scale that changes compaction tradeoffs), the relevant findings identify the conditions that would justify reinvestigation.
