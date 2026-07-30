<think>
Now I have a comprehensive picture. Let me synthesize what I know:

**Constraint state:**
- I have only `read_file`, `grep`, `list_dir` — no web fetch, no write tool
- The cc-thinking-skills repo content (the 28 frameworks) is not cached locally
- `read_file` on a URL fails with OS error 123

**What our wiki already says about this specific repo:**
- `systematic-problem-anticipation-methods-and-existing-tools.md` flags cc-thinking-skills as "worth evaluating" but didn't enumerate the 28 frameworks
- The wiki hypothesizes it contains: second-order thinking, inversion, probabilistic thinking
- Marks FMEA, sensitivity analysis, MCTS as MISSING from our workspace
- Notes MCTS/LATS is "deferred unless we build an autonomous orchestration layer" (our decisions are low-frequency + reversible)

**Our existing framework inventory (with receipts):**
- Pre-mortem: /wargame, /red-team (referenced), /tp domain 3a
- Steelman + falsifier: /tp, /design Step 5.5, /red-team
- Disconfirmation: /www Round 3 (mandatory)
- Adversarial review: /red-team 8 specialist lenses
- Devil's advocate: /tp two-lens (fresh subagent)
- Double-loop learning: /tp problem framing, AAR Phase 4
- Cynefin, Inversion, Hanlon's Razor, Chesterton's Fence, Devil's Advocate (in /skeptic references)
- Six Thinking Hats, SCAMPER, Morphological analysis, Brainwriting (in brainstorming-ideation concept)
- Bias blind spot awareness (AGENTS.md rules, /why evidence tiers)
- Reference class forecasting: ❌ MISSING (per blind-spot-detection-methods wiki)
- External-validity audit: ❌ MISSING (per assumption-auditing wiki)
- Base-rate check: ❌ MISSING
- FMEA: ❌ MISSING (per systematic-problem-anticipation wiki)
- Sensitivity analysis: ❌ MISSING
- Probabilistic thinking/calibration: ❌ MISSING
- ACH (Analysis of Competing Hypotheses): PARTIAL in /why Step 11a

**Common critical-thinking frameworks I know of (from general knowledge, with [INFERENCE] labels):**
- Inversion (Munger/Stoics) — already used per multiple wiki refs
- Occam's Razor / Hanlon's Razor — referenced in /skeptic
- Chesterton's Fence — referenced in /skeptic
- Cynefin — referenced in /skeptic
- First Principles thinking — covered in brainstorming-ideation
- Second-Order Thinking — flagged as MISSING in mental-models-for-tp
- Steelmanning — covered in /tp
- Devil's Advocate — covered in /tp
- Red Team / Blue Team — covered in /red-team
- Five Whys — likely covered in debugging protocol
- Pre-Mortem — covered (multiple skills)
- Prospective Hindsight — same as pre-mortem
- Premortem (variant) — same
- SWOT Analysis — possibly in /design
- Eisenhower Matrix / Urgent-Important — possibly in some skill
- Cost-Benefit Analysis — possibly
- Decision Tree — referenced in catalog
- Bayesian Updating — not seen
- Confidence Calibration — partially in evidence tiers
- Reference Class Forecasting — explicitly MISSING
- Outside View — same as RCF
- SCAMPER — mentioned in brainstorming-ideation
- Six Thinking Hats — mentioned
- Morphological Analysis — mentioned
- MECE — mentioned
- Issue Trees — mentioned
- Porter's Five Forces — mentioned
- Jobs-to-be-Done — mentioned
- Pyramid Principle — mentioned
- First Principles — mentioned
- 80/20 (Pareto) — possibly
- Inversion — heavily referenced
- Falsification (Popper) — covered in /tp domain 3
- Map is Not Territory — possibly in some skill
- Goodhart's Law — possibly
- Lindy Effect — possibly
- Antifragility — possibly
- Skinner Box — possibly

That's already more than 28. The "28 mental models" claim by the repo probably overlaps substantially with what we already have.

**My honest assessment:**
Given the wiki's own analysis (which I'll cite), the repo is likely worth evaluating for:
1. Reference class forecasting (the wiki explicitly flags this as MISSING and the most valuable gap)
2. External-validity audit (the wiki flags this as MISSING)
3. Probabilistic thinking / calibration (per the wiki hypothesis)
4. Sensitivity analysis (per the systematic-problem-anticipation wiki)
5. Possibly ACH full matrix
6. Possibly Bayesian updating

The wiki ALSO explicitly says:
- "MCTS/LATS is research-grade, not production-ready for our use case. Our decisions are low-frequency (a few per session) and reversible (git). MCTS shines in high-frequency, irreversible decisions (game moves, robot control). Defer unless we build an autonomous orchestration layer."

This applies to ALL formal methods (MCTS, MDP, POMDP, model checking). They're the wrong tool for our use case.

**What I'll deliver:**
A prioritized list of framework categories (not 28 specific names — those I can't see) classified against the wiki's existing coverage, with:
- Receipts for what we have
- [INFERENCE] labels for what I'm inferring
- Clear statement that the full 28-enumeration needs operator-supplied README

I should also note I have no write tool — the file path the operator specified can't be written by me. They need to either copy my output or invoke me in a session with write capability.

Now let me write the response. I want to:
1. State my tool constraints upfront (with receipts)
2. Show what I found in the wiki that's directly relevant (with file paths and citations)
3. Give the prioritized framework-category list with classification
4. Be explicit about what's [FACT] vs [INFERENCE]
5. Note the deliverable file couldn't be written (no write tool)

Let me also think about format. The user asked for:
- Prioritized list of frameworks worth porting
- One-sentence rationale each
- Focus on frameworks that catch failure modes our existing skills miss

That's a pretty compact deliverable. I should aim for that form factor while being honest about my limitations.

One more thing — the user explicitly said "Output: a prioritized list of frameworks worth porting, with one-sentence rationale each." So the format is clear. They want a list. Let me give them the list, but with the caveats.

Let me also check the format rule from AGENTS.md:
> When the response recommends actions, options, or dispositions, use this format:
> ```
> ## Recommendation
> - **<Action>.** <One sentence stating the recommendation.> <One sentence with the why.> <Confidence: H/M/L.>
> ```

So each recommendation bullet should be a full sentence with a confidence label. That's the format to use.

Now let me also re-check what the user said about the wiki:
> Our workspace already has: pre-mortem (in /red-team, /tp, /wargame), steelman + falsifier (in /tp), disconfirmation search (in /www Round 3), adversarial review (in /red-team 8 specialist lenses)

Good — confirms what I found. The user is testing my ability to find OTHER missing frameworks.

Let me draft the response now. I'll structure it as:
1. Constraint statement + receipts
2. What the wiki already says about cc-thinking-skills
3. What we already have (mapped to the user's stated coverage)
4. Prioritized list of MISSING/PARTIAL frameworks with rationales
5. Note about the file write

Actually, I realize this is going to be a very long response if I include everything. Let me focus on the user's stated deliverable: "a prioritized list of frameworks worth porting, with one-sentence rationale each."

I'll keep it tight. The format the user wants is clear — the list IS the deliverable. I'll provide the list as the main answer, with brief framing context above and the constraint statement up front.
</think>

I have what I need. Let me state my situation clearly before delivering the prioritized list.

## Tool constraints (with receipts)

- **No web fetch:** `read_file` against `https://raw.githubusercontent.com/...` failed with OS error 123 (Windows tried to parse the URL as a path). My actual tools are only `read_file`, `grep`, `list_dir`.
- **No write tool:** I cannot create `P:/tmp/cc-thinking-skills-evaluation.md`. The list below is the deliverable; persistence requires copy-paste or a session with Write/Edit.
- **Repo not cached locally:** `grep` of `P:/.data/chs_archive` and `P:/tmp` for `cc-thinking|tjboudreaux|28 mental` returned **zero matches**. No prior session downloaded it.

**What I have instead** — direct evidence the workspace already evaluated this repo partially:

- `P:/.data/wiki/concepts/systematic-problem-anticipation-methods-and-existing-tools.md:131` explicitly names `cc-thinking-skills` as "28 mental-model and critical-thinking frameworks for Claude Code" and at line 200 calls it "worth evaluating — it may contain frameworks we don't have (second-order thinking, inversion, probabilistic thinking)." Lines 176-177 cite the URL as verified. **The wiki flagged three candidates the repo likely contains: second-order thinking, inversion, probabilistic thinking.**
- `P:/.data/wiki/concepts/mental-models-for-tp-and-brainstorming.md:168` lists **second-order thinking** as a medium-priority MISSING from `/tp` core domain 2.
- `P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md:160` lists **external-validity audit, reference-class forecasting, base-rate check, probabilistic calibration** as MISSING techniques with no workspace implementation.

What follows is the actual deliverable — the prioritized list — labeled by what's [FACT] (receipts in the wiki) vs [INFERENCE] (inferred from common critical-thinking literature + the wiki's hints about what the repo contains). **Without the actual 28 frameworks, this is a framework-category classification, not an item-by-item enumeration.** If you paste the README, I can produce the per-item table in one follow-up.

## Prioritized list — framework categories worth porting

Format follows AGENTS.md recommendation template (verb-first sentence, confidence label).

- **Reference-class forecasting / Outside View.** Add a `/decide <proposal>` step that greps past ADR-style wiki concepts for similar decisions and surfaces their resolved outcomes (right/wrong/why) before committing; this is the single technique the workspace doesn't have that the literature (Kahneman/Lovallo, Flyvbjerg) credits with curing the planning fallacy and the exact failure class that produced the CooperBench overgeneralization incident. **Confidence: H** — wiki explicitly flags as the largest blind-spot gap (`blind-spot-detection-methods.md:130`, `assumption-auditing-and-unknown-unknown-discovery.md:158`).
- **External-validity audit on cited findings.** Before `/www` or `/wiki` cites any study/benchmark, require a one-line "what population was tested / what conditions held / which axes differ from my context" gate; this would have caught the CooperBench overgeneralization, the "PROVEN on standalone module" verdict, and most factual-overstatement failures (Peters & Chin-Yee 2025 found 26–73% overgeneralization rates across 10 LLMs). **Confidence: H** — wiki explicitly ranks this as highest-leverage missing technique (`assumption-auditing-and-unknown-unknown-discovery.md:221`).
- **Probabilistic thinking / calibration gate (P(IK)).** Before any confident probability or "X% sure" claim, require the model to state its evidence tier (FACT/INFERENCE/UNKNOWN) AND a confidence 0–100 with base-rate anchor; Kadavath 2022 and Kaddour 2026 show calibration data materially reduces overconfidence, and adversarial framing reduces it by 15 percentage points. **Confidence: H** — wiki explicitly calls this MISSING (`assumption-auditing-and-unknown-unknown-discovery.md:159`), and the literature is direct.
- **Second-order thinking block in `/tp` core domain 2.** For each recommendation, force "first-order consequence → second-order → third-order → at which order does it become negative?"; would have caught the exec-gate friction cascade (block mutations → blocks all bash reads because run_terminal_command is gated → user disables the plugin). **Confidence: H** — wiki already designed the exact 4-question block (`mental-models-for-tp-and-brainstorming.md:128-138`) but hasn't shipped it.
- **Full ACH matrix (Analysis of Competing Hypotheses) in `/design` and `/review`.** Force the writer/reviewer to enumerate ≥3 design alternatives (or ≥3 root causes for a finding) AND evaluate each piece of evidence against each one, before converging; current `/why` Step 11a requires alternatives but not the evidence × hypothesis matrix that Heuer's ACH prescribes. **Confidence: M-H** — wiki confirms partial coverage and the structural fix (`blind-spot-detection-methods.md:129`).
- **FMEA (Failure Mode and Effects Analysis) as a pre-implementation gate.** Systematic component-level failure enumeration with severity × occurrence × detection scoring; Claude marketplace already has an `FMEA Risk Analysis` skill (verified URL in the wiki), so this is a "evaluate-before-build" port not a from-scratch build. **Confidence: M** — wiki flags as highest-value gap among formal methods (`systematic-problem-anticipation-methods-and-existing-tools.md:189`), but the marketplace skill may not fit our hook-based enforcement model.
- **Sensitivity analysis sweep for assumption-heavy decisions.** For any recommendation resting on >3 quantitative parameters (e.g., "this fix will save 2× quota over 3 weeks"), require a one-page sensitivity sweep naming which parameters the recommendation is most sensitive to; cheap to add, catches fragile recommendations. **Confidence: M** — wiki flags as second-priority formal-method gap (`systematic-problem-anticipation-methods-and-existing-tools.md:193`), directly applicable to our low-frequency reversible decision profile.
- **Inversion block as a default `/plan` step (not opt-in).** Force "what would guarantee this fails?" before any architectural commitment; current coverage is partial — Inversion appears in `/skeptic` references and `brainstorming-ideation-with-llms.md:37` but isn't a default-fire step in `/plan` or `/go`. **Confidence: M** — wiki says inversion is "highest-ROI for LLMs" (`brainstorming-ideation-with-llms.md:70`) but doesn't fire by default.
- **Hanlon's Razor + Chesterton's Fence as quick filters in `/review`.** "Never attribute to malice what a bug explains" (Hanlon) + "before removing code, find out why it was put there" (Chesterton) — both appear in the `/skeptic` references catalog (`What-domains-are-being-expressed...md:1425`) but aren't wired into `/review`'s mechanical gates. **Confidence: M** — low cost, high signal for the specific failure class of "deleted-then-broken-12-importers" incident documented in `cognitive-enforcement-patterns-for-ai-coding-agents.md:236`.

## What I'd defer, even if the repo contains them

- **MCTS / LATS / ToT / formal verification (TLA+, Alloy, model checking).** Research-grade, require reward functions / world models / expert time; our decisions are low-frequency (a few per session) and reversible (git history); MCTS shines in high-frequency irreversible decisions. Wiki explicitly says: "Defer unless we build an autonomous orchestration layer" (`systematic-problem-anticipation-methods-and-existing-tools.md:198`). **Confidence: H** that deferring is correct.
- **Six Thinking Hats, SCAMPER, Morphological Analysis, Brainwriting, Mind Mapping as standalone skills.** Already documented as the operator's natural brainstorming process (`brainstorming-ideation-with-llms.md:37`); would compete with `/brainstorming` and `/tp` domain 5 rather than complement them. **Confidence: M** — only worth porting if `/brainstorming` adopts Double Diamond framing first (per wiki design proposal `mental-models-for-tp-and-brainstorming.md:86-95`).
- **Porter's Five Forces, Pyramid Principle, McKinsey issue trees as standalone skills.** Industry-vertical or consulting-process frameworks; useful for specific `/design` Phase 0 industry analyses but not general-purpose for our solo-operator + AI-fleet context. **Confidence: L** — speculative; would only validate by reading the actual repo.

## Honest bottom line

The nine framework categories above (RCF, external-validity audit, calibration, second-order, ACH, FMEA, sensitivity, inversion-as-default, Hanlon/Chesterton) are the **gap-shaped priorities** — each one fills a documented failure class the wiki's own analyses flag. The two big unverified inputs are: **(a)** whether the repo actually contains these as first-class techniques vs. them being buried in prose, and **(b)** whether the repo contains anything I haven't named here (e.g., Bayesian updating, Goodhart's Law, Lindy Effect, Antifragility — none of which appear in our current wiki).

**To produce the exact 28-item table you asked for, paste the README content** (or invoke this task in a session with web fetch + write tools). The `cc-thinking-skills` repo content needs to land in this workspace before the per-framework classification can ship with `[FACT]` labels.

---

**Verification suggestion:** the cc-thinking-skills evaluation intersects with existing wiki concepts `systematic-problem-anticipation-methods-and-existing-tools.md` and `mental-models-for-tp-and-brainstorming.md` — recommend `/wiki` review against this draft before publishing the file, since two existing concepts should be updated with this evaluation's findings (per `~/.grok/AGENTS.md` decision-and-fix-documentation rule).