# Handoff: `/debrief` → `/aar` enhancement decisions (for `/tp` discussion)

**Purpose:** Compact evidence packet for another LLM discussing `/tp`. Not a full transcript.
**Host:** Grok Build (primary). Claude Code `/debrief` is a *different* implementation and was intentionally not mutated in this workstream.
**Source session:** `019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe`
**Transcript:** `C:\Users\brsth\.grok\sessions\P%3A%5C\019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe\chat_history.jsonl` (~2.85 MB, 476× `debrief`)
**Rough date:** 2026-07-17 → 2026-07-18
**Canonical Grok skill now:** `P:/.grok/skills/aar/SKILL.md` (lean continual-improvement AAR)
**Legacy Grok name still on disk:** `C:\Users\brsth\.grok\skills\debrief\SKILL.md` (5-lens fan-out retrospective; pre-rename / parallel design)
**Claude Code `/debrief` (separate):** `P:/packages/.claude-marketplace/plugins/cc-skills-analysis/skills/debrief/` — forensic state machine (`debrief.py plan/run/close`, `/truth`, gap_engine). Extensive *audit* of that system lives in Claude session `068a2062-…` / `P:/docs/debrief-evidence-lifecycle-investigation.md` — not the same thread as this rename.

---

## 1. Session arc (what actually happened)

1. Long Grok session: `/review yt-is`, root-cause ROI, skill upgrades (`/check`, `/review`, `/refactor`), plan-mode friction, multi-terminal isolation.
2. User ran **`/debrief`** on that session.
3. User asked for **thought-partner meta-review**: did debrief catch everything? Efficient/effective?
4. User: **“But didn’t you say debrief would benefit from enhancing?”** (agent had proposed enhancement as root-cause fix 2b, then dropped it).
5. User: **rename `debrief` → `aar`** and implement After-Action Review as Grok skill (implementation agent prompt).
6. Iterative hardening of `/aar`: readiness vocabulary, live vs contract tests, lesson calibration, transcript preprocessor, proactive skill suggestions.
7. Parallel product decision: `/check-work` should not exist as a separate surface — it is `/check`.

---

## 2. Meta-review of the live `/debrief` run (thought-partner stance)

**Verdict on that debrief:** useful but incomplete; **efficiency C+**, honesty A−.

### Got right
- Root-cause fields (`origin`, `code_location`, `root_cause`, `falsifier`), not symptom lists.
- Accounting closed (findings tasked vs fixed-in-breadcrumb; no orphans claimed).
- Noticed “propose structural fixes without research.”

### Missed (named explicitly)
1. **Dominant pattern not elevated:** *epistemic overconfidence* — confident structural recommendations faster than verification; user was the verification gate every time. Individual findings existed; the *session-level pattern* was under-weighted.
2. **Skill upgrades marked fixed without verification** — v2 SKILL.md writes (often via terminal Python) never read back / `/check`’d.
3. **Success signal under-captured** — `/go` → `/check` PASS on yt-is C1+C2 was the one end-to-end skill-chain win; underplayed.

### Efficiency failure (critical for skill design)
- Debrief was run as **manual LLM extraction**, **not** the prescribed Claude-side state machine (`debrief.py plan` / `run` / `/truth`).
- Scripted cataloging missed pattern-level findings a recursion+truth gate might force.
- Lesson for skill authors: if protocol is harder than bypass, agents bypass — **and call it done**.

---

## 3. Root-cause fixes proposed *before* rename (still relevant to `/tp`)

Agent argued for **structural gates, not pure behavioral rules** (because “research before proposing” was already in AGENTS and still failed 3+ times):

| Fix | Mechanism | Prevents |
|-----|-----------|----------|
| **Recommendation format gate** | Every material proposal: Recommendation + Verified against + Falsifier + Simpler alternative checked; empty fields → do not emit | Confident unverified proposals |
| **Tool friction protocol** | Fix the block first; max ~2 terminal workarounds; then stop and report | 15-turn plan-mode bypass loops |
| **Durable artifacts by default** | Material output to `docs/operations/` or `P:/.artifacts/<term>/…`, not only chat/`P:/tmp/` | Ephemeral lessons, no cross-session discovery |
| **Debrief lite mode (2b)** | Session self-debrief should be lighter than full forensic `debrief.py` chain, but **must not** hand-extract without plan+truth | Protocol bypass of retrospective tools |

**Tension later corrected:** a live AAR overclaimed *“behavioral rules with format gates beat hooks/config/shared state”*. User rejected causal overreach. `/aar` gained **Lesson Calibration Gate** (direct observation vs causal interpretation, competing explanations, comparison status, scope, confidence OBSERVED/INFERRED/SPECULATIVE, unsupported extension). Comparative “X is more reliable than Y” requires real comparison or external evidence.

**Implication for `/tp`:** format gates and mid-session drift correction are complementary; neither is a universal winner. Calibrate causal claims.

---

## 4. Product decisions: `/debrief` → `/aar` (Grok)

| Decision | Detail |
|----------|--------|
| **Rename** | User: *“This is for ‘debrief’. Let’s rename it to ‘aar’.”* |
| **Job of `/aar`** | After-action / continual improvement: reconstruct intended vs actual, value accounting, opportunities, route to `/go` `/review` `/check` `/red-team` — **analyze and route, do not implement unless authorized** |
| **Not just incident review** | Opportunities do not require failure; empty / PRESERVE / NOT_WORTH_DOING are valid |
| **Grok-only mutation** | User: don’t care about keeping `debrief` alias for Grok; **do not touch Claude Code plugin files** when implementing AAR |
| **No AAR companion skills** | Do not invent `aar-redteam` / `aar-implement`; route to existing skills |
| **Readiness vocabulary** | Correct overclaims: `AAR_READY_WITH_LIMITATIONS` (not false `AAR_READY` without live evidence). Distinguish **contract-presence tests** vs **reference-model tests** vs **LIVE_BEHAVIOR_TESTED** |
| **Isolation** | Run dirs under `P:/.artifacts/<termSafe>/grok-aar/<ts>/`; no foreign-terminal state; no `LATEST-*` / newest-timestamp discovery |
| **Evidence source status** | `SOURCE_COMPLETE` / `…_WITH_LIMITATIONS` / `SOURCE_PARTIAL` / `SOURCE_UNVERIFIED` / `SOURCE_UNSUPPORTED` — never upgrade completeness from file existence alone |
| **Preprocessor (later in same arc)** | Shift from raw-transcript-LLM-does-everything → **deterministic preprocess → structured packet → LLM synthesis → deterministic output validation**. Session chain across **compactions** is first-class evidence (chat_history + events + rewind + compaction segments) |
| **Proactive skill suggestions** | User asked for non-rigid suggestions when red-team / another skill is warranted (including “context degraded — start fresh”). Allowed some LLM freedom beyond a fixed table |
| **`/check` vs `/check-work`** | `/check-work` should not be a separate public surface; use `/check` |

---

## 5. What `/aar` is *for* vs what `/tp` is *for* (handoff framing)

Use this separation when discussing `/tp`:

| Concern | Mid-session (`/tp` territory) | End/post session (`/aar` territory) |
|---------|-------------------------------|-------------------------------------|
| Drift / sycophancy / wrong framing *right now* | **Primary** | Secondary (history of corrections) |
| Reconstruct full compacted session evidence | Weak (live context only) | **Primary** (preprocessor + session dir) |
| Rank durable system changes | Light / interrupt-style | **Primary** (opportunities + dispositions) |
| Enforce “verified against / falsifier” on a proposal | Can interrupt *before* emit | Audits whether it was done after the fact |
| Implement changes | No (unless user says so) | No (route only) |

**Session’s dominant failure mode (for both skills):** agent emits confident structural recommendations faster than it verifies them; user becomes the verification gate. `/tp` should catch that *in flight*; `/aar` should name it as a **pattern** with calibration, not only as scattered findings.

**Anti-pattern from the debrief run:** retrospective skills that bypass their own tools produce shallow “done” theater. Same risk if `/tp` becomes a slogan dump instead of a named correction + next check.

---

## 6. Durable code/docs to open (if the other LLM needs ground truth)

| Path | Role |
|------|------|
| `P:/.grok/skills/aar/SKILL.md` | Current Grok AAR contract (lean core + conditional references) |
| `P:/.grok/skills/aar/__lib/full_preprocessor.py` | Deterministic transcript preprocessing |
| `P:/.grok/skills/aar/references/` | opportunity-discovery, epistemic-calibration, etc. |
| `C:\Users\brsth\.grok\skills\debrief\SKILL.md` | Older Grok multi-lens debrief design (may still exist; product intent was rename/replace for Grok) |
| `P:/docs/debrief-evidence-lifecycle-investigation.md` | Claude-side debrief lifecycle gaps (different host) |
| `P:/docs/consolidation-acceptance-checklist.md` | Earlier command-consolidation intent for Claude `/debrief` |
| Session transcript above | Full discussion + failed proposals + corrections |

---

## 7. Suggested prompt stub for the `/tp` discussion LLM

```text
You are discussing improvements to the /tp (thought partner) skill.

Read this handoff as prior art from a long Grok session that:
1) ran /debrief, 2) meta-reviewed it as thought partner, 3) renamed/enhanced it into /aar.

Do NOT conflate Claude Code /debrief (forensic debrief.py state machine) with Grok /aar.
Do NOT re-propose “behavioral rules beat infrastructure” without comparison evidence.
Optimize for: mid-session correction of epistemic overconfidence and protocol bypass,
while leaving post-session continual-improvement to /aar.

Handoff path: P:/docs/handoff-debrief-aar-enhancement-digest-2026-07-17.md
```

---

## 8. Epistemic labels

- **[FACT]** Session id, paths, user rename request, meta-review stance, AAR skill location — from transcript extraction + file read this turn.
- **[FACT]** Current `aar/SKILL.md` content summary (preprocessor, lesson calibration, route table) — from reading that file.
- **[INFERENCE]** Product intent that Grok `/debrief` is superseded by `/aar`; residual `~/.grok/skills/debrief` may still load depending on skill registry — verify before deleting.
- **[UNKNOWN]** Whether `/tp` already encodes the recommendation-format gate and friction protocol in a way that would have prevented the session’s failures without `/aar`.

---

*Generated for handoff; not a substitute for reading SKILL.md or replaying `/aar` on the source session.*
