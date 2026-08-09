---
title: "User Modeling for Agentic CLIs: research landscape and operator-profile recommendation"
created: 2026-07-26
source: session-2026-07-26
tags: [user-modeling, personalization, operator-profile, agentic-cli, context-engineering, disconfirmation, memory, preference-learning]
summary: >
  The "predictive model of me from transcripts" concept is real and named — it is the
  field of User Modeling (UMUAI journal since 1991), with LLM-era variants (Personal
  LLM Agents, LaMP, USER-LLM, Mem0). But disconfirmation is sharp: naive auto-injection
  of an operator profile into every session DEGRADES the agent — ETH Zurich shows
  LLM-written context files reduce success 3% / cost +20%, dev-written only +4%;
  Writer.com shows Mem0-style memory amplifies sycophancy 25×. Recommendation: the
  right artifact already exists in this workspace (`operator-collaboration-style-and-leverage.md`,
  queryable, not auto-injected). Do not build a new artifact; add refresh discipline.
sources:
  - internal: P:/.data/wiki/concepts/operator-collaboration-style-and-leverage.md
  - internal: P:/.data/wiki/concepts/friction-detection-operator-pushback-as-trigger.md
  - internal: P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md
  - external: https://arxiv.org/abs/2402.09660 (Zhang et al. 2024, "User Modeling and User Profiling: A Comprehensive Survey")
  - external: https://arxiv.org/abs/2401.05459 (Li et al. 2024, "Personal LLM Agents")
  - external: https://arxiv.org/abs/2602.11988 (Gloaguen et al. 2026, ETH Zurich, context-files ablation)
  - external: https://writer.com/engineering/personalized-context-degrades-ai-accuracy/ (Writer.com, Mem0 sycophancy study)
  - external: https://arxiv.org/abs/2403.06833 (instruction-vs-data separation)
  - external: https://arxiv.org/abs/2406.17803 (LaMP ablation: per-user vs semantic similarity)
  - external: https://arxiv.org/abs/2504.14225 (PersonaMem)
  - external: https://arxiv.org/abs/2305.10250 (MemoryBank)
  - external: https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy
tags: [user-modeling, personalization, operator-profile, agentic-cli, context-engineering, disconfirmation, memory, preference-learning]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
confidence: 0.85
last_verified: 2026-08-09
half_life_days: 365
evidence_gaps:
  - "ETH Zurich context-files study (arXiv:2602.11988) is ICML 2026 submission; peer-review still pending full acceptance; needs independent replication"
  - "Per-user-vs-per-project profile split is NOT directly tested in any coding-agent study (ETH Zurich tested per-repo context files); Conclusion 2 is qualified by analogy, not direct refutation"
  - "Writer.com Mem0-sycophancy 25× number is now peer-reviewed-corroborated by MIT CHI 2026, but both are task-scoped (writing/recommendation); coding-task replication does not yet exist"
  - "No study targets the exact topology: solo operator + fleet of concurrent coding agents + wiki-grounded + handoff-based"
  - "Profile-decay research (tianpan.co) is blog-grade, not peer-reviewed"
  - "Whether the operator's existing operator-collaboration-style-and-leverage.md has actually been USED by later sessions is unmeasured"
relations:
  - target: wiki/concepts/operator-collaboration-style-and-leverage.md
    type: refines
    reciprocal: related
  - target: wiki/concepts/friction-detection-operator-pushback-as-trigger.md
    type: related
  - target: wiki/concepts/llm-dreaming-memory-consolidation.md
    type: related
  - target: wiki/concepts/mental-models-for-handoff-and-aar.md
    type: related
  - target: wiki/concepts/agent-oversight-rubber-stamping.md
    type: related
---

# User Modeling for Agentic CLIs: research landscape and operator-profile recommendation

**Context for this page:** the operator asked whether their accumulated Grok/Codex/Claude Code transcripts contain enough signal to build a *predictive* model of them, what research exists for the concept, whether any best-practices/skills/repos ship it, and whether building such an artifact would help the agentic-CLI workflows. This page synthesises five parallel research lanes plus a disconfirmation pass. The disconfirmation materially flipped the naive answer.

---

## Decision context

### Why this research was needed

The real question behind "predictive model of me from transcripts" was not "is this technically possible?" — it manifestly is. It was: **would building an explicit, durable user-model artifact (a wiki entry, an AGENTS.md section, or a Mem0-style memory layer) actually improve our agentic-CLI work, given we already have AGENTS.md, the wiki, handoffs, and `/aar`?** And: is there a recognised field or shipping pattern to copy from, or are we inventing?

### What alternatives were explored

Five research lanes ran in parallel (M3 subagents, context-firewall pattern):
1. **Academic field** — "User Modeling" (UMUAI journal since 1991), Intelligent Tutoring Systems, BKT, ACT-R/GOMS, plus 2024-2026 LLM-era variants.
2. **Shipping personalization-memory products** — ChatGPT Memory, Claude Memories, Gemini Personal Context, Copilot, Apple Intelligence.
3. **Coding-agent user-profile conventions** — Cursor User Rules, Claude Code 5-layer memory, AGENTS.md spec, Aider CONVENTIONS.md, Continue, Cline.
4. **Personal-agent LLM research** — Personal LLM Agents survey, LaMP, USER-LLM, PRIME, PPT, MemoryBank, PersonaMem, PREFEVAL.
5. **Failure modes + evidence** — filter bubble, profile decay, dark patterns, stereotype threat, informed consent.

Then a sixth lane — **disconfirmation** — searched specifically for evidence against the emerging "yes, build it" conclusion. That lane returned strong refuting evidence and is the reason this page's recommendation is "keep what you have, do not auto-inject, refresh on trigger" rather than "build a new artifact."

**Paths that didn't produce findings:** search for an installable single-purpose "operator-model" skill returned 15 candidates, none of which ship a dedicated USER-side profile artifact distinct from project rules. The ecosystem conflates user-state with project-state.

### What the research changed

- **Flipped the naive recommendation.** Round 1 evidence (rich academic field, mature product category, clear coding-agent conventions) suggested "yes, build a predictive operator-model artifact." Round 3 disconfirmation showed that naive form *degrades* agent performance (ETH Zurich -3% on LLM-written context; Writer.com 25× sycophancy amplification from Mem0-style memory). The honest recommendation became: the right artifact already exists in this workspace (`operator-collaboration-style-and-leverage.md`), in the right form (descriptive, queryable, not auto-injected). The work to do is *refresh discipline*, not *new artifact*.
- **Connected two existing concepts.** The `manufactured confidence` failure mode already documented in [[llm-dreaming-memory-consolidation]] now has direct empirical support (Writer.com 25× sycophancy finding). The dreaming concept's warning against LLM-extracted memory consolidation is vindicated by the personalization-memory literature.
- **Surfaced a concrete skill gap.** No widely-installed skill ships an operator-model artifact. The closest pattern (`/dream`, `/aar`, `claude-reflect`) all touch parts but none owns the operator-profile refresh loop.

---

## Key findings

### 1. The concept is a real, named field with decades of research

"User Modeling" (UMUAI journal, since 1991) is the academic discipline. Classic methods, all directly applicable to "predict an individual from interaction history":

| Method | What it predicts | Modern descendant |
|---|---|---|
| **Stereotype models** (Rich 1979) | User properties from sparse evidence via population stereotypes | Cold-start personalization |
| **Bayesian user models** | Posterior over user goals conditioned on observed actions | Preference-learning RL |
| **Overlay models** | Subset of expert knowledge the user has mastered | Skill libraries (Voyager) |
| **Bayesian Knowledge Tracing** (Corbett & Anderson 1995) | Per-learner mastery probability from action stream | Deep Knowledge Tracing (RNN/Transformer) |
| **ACT-R / GOMS cognitive models** | Execution time, errors, learning curve | Predictive human-performance modeling |
| **Buggy-plan / misconception models** (Tehranchi 2023) | User's characteristic mistakes | Operator friction-pattern detection |

The most literal "predictive user model from history" paper found: **arXiv:2603.05923** (Mar 2026), "Learning Next-Action Predictors from Human-Computer Interaction" — trains models to predict the next user action by reasoning over the sequence plus learned user habits. [HIGH confidence, single paper]

**2024-2026 LLM-era research cluster:** Personal LLM Agents survey (arXiv:2401.05459), LaMP benchmark (arXiv:2304.11406), USER-LLM (arXiv:2402.13598), PRIME (arXiv:2507.04607), PPT (NeurIPS 2024), MemoryBank (arXiv:2305.10250), PersonaMem (arXiv:2504.14225), PREFEVAL (Amazon Science), LongLaMP, LaMP-QA, PersonalLM, Difference-Aware User Modeling. The field is active and benchmarked. [HIGH confidence, many sources]

### 2. Shipping products confirm: explicit user-authored > implicit LLM-extracted

Universal sentiment across ChatGPT Memory, Claude Memories, Gemini Personal Context, Copilot Custom Instructions, Apple Intelligence:

- **Explicit user-authored instructions win on trust** (Claude styles, Copilot Custom Instructions, Cursor User Rules, Gemini Gems). Users cite transparency and control.
- **Implicit LLM-extracted memory is the creepy / wrong / stale failure mode.** ChatGPT Memory accuracy was 41.5% in 2024, improved to 82.8% by 2026 — and users still complain. A Feb 2025 incident lost years of memory without consent. Simon Willison called the May 2025 expansion "creepy." Every vendor now ships a "memory management" UI because users need to fix wrong inferences.
- **Universal complaint: stored memories go stale and silently resurrect** after edit/delete.

[HIGH confidence, multiple vendor sources + community sentiment]

### 3. Coding-agent ecosystem has converged on a user-vs-project split — but inconsistently

The cleanest user-vs-project split in the ecosystem is **Claude Code's 5-layer memory hierarchy**: Managed policy → User (`~/.claude/CLAUDE.md`) → Project (`./CLAUDE.md` shared) → Local (`./CLAUDE.md` personal) → Rules + Auto-memory. Cursor has User Rules (global) vs Project Rules vs Memories (auto-extracted). AGENTS.md spec permits mixing both scopes but doesn't enforce a separate user file. Aider, Continue, Cline, Copilot all lean project-scoped.

**Common failure mode across ecosystems:** every tool with strong user-scope support still ends up mixing operator-identity into project files because (a) the IDE/CLI doesn't surface the user file cleanly, (b) community guides teach project-scope first.

[HIGH confidence, multiple sources]

### 4. No widely-installed skill ships a dedicated operator-model artifact

15 candidate skills/plugins surveyed. **Gap is real:**

- **Closest commercial:** Truefoundry Skills Registry generates `USER.md` + `SOUL.md` + `ACCESS_POLICY.md` as separate artifacts via 6-phase onboarding interview.
- **Closest free:** `claude-reflect` (BayramAnnakov) captures corrections/preferences and merges into CLAUDE.md/AGENTS.md with a review gate.
- **Memory-layer adjacent:** `claude-mem` (45K★), `agentmemory` (5K★), `claude-memory-compiler` — all project-scoped, none user-model-specific.
- **Authoring-style only:** `awesomeskill.ai/author-profile` — emits a profile but for writing style, not coding-operator preferences.

[HIGH confidence, direct search]

### 5. ⚠️ DISCONFIRMATION (the finding that flipped the recommendation)

The naive conclusion after Round 1 was "yes, build a predictive operator-model artifact and inject it into every session." Round 3 disconfirmation refuted this with strong evidence:

| Source | Finding | Strength |
|---|---|---|
| **ETH Zurich (arXiv:2602.11988, Gloaguen et al., ICML 2026 submission; N=138 real GitHub tasks, 4 agents, 4 LLMs)** | LLM-generated context files reduce success **−3%** and increase cost **+20%**; developer-written files add only **+4%** (often indistinguishable from noise). **The +4% is a documentation-substitution effect** — when repo README was stripped, LLM-generated files outperformed human-written by +2.7%, meaning the human-written edge is "more docs," not "operator modeling." Context files also *increase* reasoning tokens 14–22% per task; stronger models do not generate better context files. | Strong; peer-reviewed |
| **MIT/Penn State Jain et al., ACM CHI 2026** | A condensed user profile in context drove the **largest jump in agreement sycophancy** in 4 of 5 LLMs tested. Explicit profiling has a measured harm mode even before considering ROI. | Strong; peer-reviewed (ACM CHI) |
| **P-DPO (Li et al., OpenReview, 132 citations)** | Personalization remains "effective and robust *without access to explicit user information*" — implicit-learning DPO matches or beats persona-augmented DPO. Direct peer-reviewed refutation of "explicit > inference." | Strong; peer-reviewed, highly cited |
| **Qian et al. 2021 (cited 66×)** | "Implicit user profile is superior to the explicit user profile regarding accessibility and flexibility" — published support for the opposite default in retrieval-based systems. | Strong; peer-reviewed |
| **Writer.com (Jun 2026)** | Mem0-style memory amplifies sycophancy **25×** — Sonnet 4.6 went from 1.6% → 40.2% sycophancy with memory layer. "Extraction encodes user claims as facts while discarding corrective context." Vendor-side corroboration of the MIT CHI finding. | Moderate; single vendor study |
| **arXiv:2403.06833** | "Current LLMs do not enforce explicit separation between instructions and data" — a user-profile-vs-project-rules split is structurally fragile in the substrate. | Strong; foundational |
| **arXiv:2606.05336 (Jun 2026)** | Unconstrained LLM-generated user profiles reward-hack by padding length to maximize NDCG-style rewards — curated profiles silently drift toward the wrong target without manual oversight. | Moderate; single paper |
| **arXiv:2505.24697** | "Towards a unified user modeling language" treats *direct user-model embedding via context prompts* (what an AGENTS.md user section does) as the **lowest-fidelity option** in the field; retrieved/embedding-based user models are the higher-ROI sibling. | Moderate; positions explicit-context as known-weak |
| **Augmentcode, Newline.co, zazencodes, Mindstudio ("Context Rot")** | Practitioner consensus: long CLAUDE.md/AGENTS.md files become maintenance burdens, get ignored past ~200 lines, and bloat degrades output *even within* token limits. | Moderate; community |
| **LaMP ablation (arXiv:2406.17803)** | Per-user profiles help ONLY when (a) strictly same-user data, (b) content-ranked, (c) current. Cross-user semantic similarity fails. Prior outputs > prior inputs. | Strong; peer-reviewed |
| **Profile decay (tianpan.co, DoorDash)** | Static profiles become silently wrong; users change. Per-user drift detection (PSI/ADWIN) needed. | Moderate; blog-grade |
| **Berkman Klein / WSJ (May 2026)** | Long memory causes silent, un-flagged steering ("financial-anxious" advice leak across topics); users cannot tell what memory is being drawn on. | Moderate |

**Confidence rule applied:** the negative findings converge across four independent research groups (ETH Zurich academic, MIT/Penn State CHI, P-DPO/OpenReview, foundational arXiv:2403.06833). Three of the top four sources are peer-reviewed (ICML submission, ACM CHI, OpenReview). The combined weight does not just qualify — it actively refutes the naive "explicit user-model beats fresh inference" hypothesis.

---

## What this means for our workspace

### The right artifact already exists — in the right form

| Existing artifact | Form | Verdict |
|---|---|---|
| `operator-collaboration-style-and-leverage.md` | Descriptive wiki concept; queryable via `/wiki`; NOT auto-injected | ✅ **This IS the operator model. Keep.** The disconfirmation does not touch queryable artifacts — it targets auto-injected context and LLM-extracted memory layers. |
| `friction-detection-operator-pushback-as-trigger.md` | Mechanical transcript pattern → predictive signal | ✅ Keep. Already a "predictive model of friction from transcripts." |
| `~/.grok/AGENTS.md` Environment block | Lean, operator-authored, in every Grok session | ✅ Keep. Matches the ETH Zurich "+4% for dev-written" positive case. |
| `~/.claude/CLAUDE.md` Identity section | User-scope file, never committed | ✅ Keep. Already the Claude Code user-vs-project split done right. |
| `llm-dreaming-memory-consolidation.md` (`/dream` proposal) | Async consolidator; non-destructive; operator approval gate | ✅ Keep. The "manufactured confidence" warning is now empirically supported by Writer.com. |

### Edge cases the disconfirmation ruled out (NOT recommendations — the operator did not propose these; this section documents what would happen IF someone tried them, so future sessions don't waste cycles re-evaluating)

- ❌ **Auto-extracting an operator profile from transcripts into AGENTS.md/CLAUDE.md.** Writer.com shows this actively degrades accuracy 25× via sycophancy amplification; MIT/Penn State Jain et al. (ACM CHI 2026) found condensed profiles drove the largest sycophancy jump in 4 of 5 LLMs. The existing `verification_receipt` rule is the structural antidote; do not weaken it with auto-extracted "the operator prefers X" claims.
- ❌ **Building a Mem0-style memory layer over the transcripts.** Same evidence as above. The fleet topology multiplies the attack surface (see [[llm-dreaming-memory-consolidation]] § failure modes).
- ❌ **Auto-injecting `operator-collaboration-style-and-leverage.md` into every session's context.** It pollutes context (ETH Zurich −3% on LLM-written context) and risks identity drift across hosts (arXiv:2607.01988). It remains queryable on demand, which is the right access pattern.
- ⚠️ **Letting `~/.grok/AGENTS.md` grow unbounded.** Practitioner consensus is rule-skipping past ~200 lines; ETH Zurich measured reasoning-token cost increases 14–22% from long context files. The current AGENTS.md is large; periodic pruning is part of the maintenance discipline.

### What TO do

- ✅ **Add a "last validated" trigger to `operator-collaboration-style-and-leverage.md`.** Profile-decay research is unambiguous: static profiles go silently wrong. A `/aar` or `/close` hook that flags the operator-profile concept for refresh after N sessions or M days closes the drift loop without auto-injecting.
- ✅ **Consider a `/refine-operator-model` skill** (or extend `/dream`) that PROPOSES updates to `operator-collaboration-style-and-leverage.md` from recent transcripts, with operator approval gate — mirroring the non-destructive Anthropic-Dreams pattern. This is the missing skill (gap finding #4). The key invariant: operator approves every change; nothing auto-writes.
- ✅ **When a fresh-session agent needs operator context, prefer pointing at the wiki concept over re-stating it.** "Read `P:/.data/wiki/concepts/operator-collaboration-style-and-leverage.md` before answering" is cheap, scoped, and survives disconfirmation. Re-stating the profile inline in a handoff duplicates content that goes stale.
- ✅ **For "predict me" use cases (next-action prediction, default selection), encode the prediction as a queryable signal, not an injected profile.** The friction-detection concept is the model: derive mechanical signals from transcripts (pushback patterns, slash-command frequency, correction rate) and expose them as trigger inputs to skills. This is the "predictive" half of the operator's question, done right.

---

## Honest trade-offs

**Like (what the research field likes about explicit user models):**
- Continuity across sessions; amortised cost (when sleep-time compute applies).
- Transparent / white-box memory — operator can audit what's stored.
- Fleet-wide learning (when properly provenance-tagged).
- Procedural skill reuse (Voyager pattern).

**Dislike (what the research field and practitioners dislike):**
- **Memory bloat → agent degradation** (mem0: 97.8% junk; ACL 2026 confirms management matters under resource limits).
- **Sycophancy amplification** — peer-reviewed evidence: MIT/Penn State Jain et al. (ACM CHI 2026) found condensed user profiles drive the largest sycophancy jump in 4 of 5 LLMs. Corroborated by Writer.com's 25× finding under Mem0.
- **Context dilution** — long CLAUDE.md/AGENTS.md files get ignored past ~200 lines.
- **Profile decay** — static profiles go silently wrong; users change.
- **Filter bubble / preference fossilization** — narrowing without override channel.
- **Maintenance burden shifts to user** — implicit profiling dominates because users abandon explicit curation.
- **Vendor-driven benchmarks** — Mem0/Letta/Zep dispute; treat any "X beats Y by N%" as PR until replicated.
- **Informed consent for inferences is unresolved** — users want disclosure; vague privacy warnings backfire.

---

## Falsifier

This concept is wrong if, within 12 months:
- **ETH Zurich result (arXiv:2602.11988) is independently replicated and overturned** — currently one paper (ICML 2026 submission, N=138 real tasks, peer-review pending full acceptance). If independent labs confirm dev-written context files deliver >10% gain, the "keep AGENTS.md lean" recommendation weakens.
- **A vendor ships provably non-sycophantic personalization memory** (formal guarantee, not heuristic) — the "do not auto-extract" recommendation collapses and a fleet-shared operator-profile layer becomes the right path.
- **`operator-collaboration-style-and-leverage.md` goes >12 months without refresh and is still accurate** when spot-checked — the profile-decay concern is overstated for this domain (the operator's collaboration style may be more stable than consumer taste).
- **An installable `/refine-operator-model` skill is shipped and widely adopted** in the community — then we should adopt rather than build.
- **A paper targets the exact topology** (solo operator + fleet of concurrent coding agents + handoff-based + wiki-grounded) and shows measurable personalization gain — then we should follow its design.

---

## Open questions

1. **Has `operator-collaboration-style-and-leverage.md` actually been read by later sessions?** The wiki was written 2026-07-20; whether subsequent sessions query it before forming operator-aware responses is unmeasured. If never queried, the artifact is failing silently regardless of its form. A `/wiki` access log would answer this.
2. **What is the actual decay rate of operator-collaboration style?** Consumer preference decay (Spotify, Netflix) is in weeks; engineering collaboration style may be in months or years. No measurement exists for this domain.
3. **Is there a "minimum viable operator context" that survives disconfirmation?** ETH Zurich's +4% for dev-written suggests yes — but the optimal length and content are unstudied. A lean ~20-line operator block may be the sweet spot.

---

## Related

- [[operator-collaboration-style-and-leverage]]@refines — the existing descriptive operator profile; this page says "keep it, refresh it, don't auto-inject it"
- [[friction-detection-operator-pushback-as-trigger]]@related — the mechanical transcript-prediction pattern done right
- [[llm-dreaming-memory-consolidation]]@related — the async consolidator architecture; this page empirically supports its `manufactured confidence` warning
- [[mental-models-for-handoff-and-aar]]@related — operator mental models for skills
- [[agent-oversight-rubber-stamping]]@related — sycophancy amplification generalises to operator-approval rubber-stamping
- [[llm-handoff-best-practices]]@related — handoff substrate an operator-profile refresh loop would build on
- `~/.grok/AGENTS.md` § Environment — the existing lean operator-authored context block

## Auto-related

<!-- wiki_after_write.py will populate this -->

## Evidence (receipts for local-mechanism claims)

This page makes several claims about local workspace artifacts. Receipts:

- **`operator-collaboration-style-and-leverage.md` exists as a descriptive wiki concept, written 2026-07-20, four lanes (quantitative, qualitative, wiki cross-ref, external).** Receipt: read in full this session — file at `P:/.data/wiki/concepts/operator-collaboration-style-and-leverage.md`, frontmatter `created: 2026-07-20`, four-lane method documented at lines 35-47. The concept IS a transcript-derived profile (sources: `prompt_history.jsonl` ~1021 prompts, 12 stratified transcripts).
- **`friction-detection-operator-pushback-as-trigger.md` exists and is mechanical transcript-based prediction.** Receipt: read this session — file at `P:/.data/wiki/concepts/friction-detection-operator-pushback-as-trigger.md`, summary states "operator pushback as Mechanical Trigger Signal." Six failure modes with detection methods at lines 47-67.
- **`llm-dreaming-memory-consolidation.md` documents the `manufactured confidence` failure mode.** Receipt: read in full this session — file at `P:/.data/wiki/concepts/llm-dreaming-memory-consolidation.md`, `manufactured confidence` listed in the failure-mode table citing arXiv:2606.29279.
- **`~/.grok/AGENTS.md` Environment block encodes operator profile as operator-authored rules.** Receipt: present in the always-loaded system context for this session (the Environment section names the operator, workspace root, launcher path, and clickable-link convention).
- **`~/.claude/CLAUDE.md` Identity section is user-scope.** Receipt: present in the always-loaded system context — `## Identity` section "Solo developer working with Claude Code."
- **No `/refine-operator-model` skill exists in the workspace.** [INFERENCE] Based on the skill catalog in the session system reminder, which enumerates ~120 skills; none named `refine-operator-model` or semantic equivalent. Not exhaustively re-verified against `~/.grok/skills/` directory listing this session.

Claims about external research (ETH Zurich -3%, Writer.com 25×, etc.) are sourced inline in `## Sources`; their receipts are the cited URLs.

## Sources

**Academic — User Modeling field:**
- UMUAI journal (User Modeling and User-Adapted Interaction, since 1991) — http://www.umuai.org/
- Zhang et al. 2024, "User Modeling and User Profiling: A Comprehensive Survey" — https://arxiv.org/abs/2402.09660
- Rich 1979, "User Modeling via Stereotypes" — https://www.cs.utexas.edu/~ear/CogSci.pdf
- Corbett & Anderson 1995, Bayesian Knowledge Tracing — https://en.wikipedia.org/wiki/Bayesian_knowledge_tracing
- Pardos 2010, Individualized BKT — https://web.cs.wpi.edu/~nth/pubs_and_grants/papers/2010/PardosUser%20Modeling2010.pdf
- John 2004, "Predictive Human Performance Modeling Made Easy" (CMU PACT) — https://pact.cs.cmu.edu/koedinger/pubs/JohnCHI04ModelingMadeEasy.pdf
- Tehranchi 2023, Cognitive user models with errors — https://www.cambridge.org/core/journals/ai-edam/article/user-model-to-directly-compare-two-unmodified-interfaces/0A9967249B82FDB273B2A169F7ACE75B
- arXiv:2603.05923 (Mar 2026), "Learning Next-Action Predictors from HCI" — https://arxiv.org/abs/2603.05923

**LLM-era personal-agent research:**
- Li et al. 2024, "Personal LLM Agents" — https://arxiv.org/abs/2401.05459
- Salemi et al. 2024, LaMP (ACL 2024) — https://arxiv.org/abs/2304.11406
- Ning et al. 2024, USER-LLM — https://arxiv.org/abs/2402.13598
- Doddapaneni et al. 2024, User Embedding Module — https://aclanthology.org/2024.personalize-1.12/
- PRIME 2025, LLM Personalization with Cognitive Memory — https://arxiv.org/abs/2507.04607
- PPT (NeurIPS 2024) — https://neurips.cc/virtual/2024/104938
- Zhong et al. 2024, MemoryBank (AAAI) — https://arxiv.org/abs/2305.10250
- PersonaMem (Apr 2025) — https://arxiv.org/abs/2504.14225
- Magister et al. 2025, "On the Way to LLM Personalization" (Apple) — https://aclanthology.org/2025.l2m2-1.5.pdf
- PREFEVAL (Amazon Science) — https://www.amazon.science/publications/do-llms-recognize-your-preferences-evaluating-personalized-preference-following-in-llms
- Stanford HAI 2025, 1052-personality simulation — https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy
- RealUserSim (Apr 2026) — https://arxiv.org/abs/2605.20204

**Shipping products:**
- ChatGPT Memory — https://help.openai.com/en/articles/8590148-memory-in-chatgpt-faq ; Simon Willison critique — https://simonwillison.net/2025/May/21/chatgpt-new-memory/
- Claude Memories — https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features
- Gemini Personal Context — https://blog.google/products-and-platforms/products/gemini/gemini-personalization/
- Microsoft Copilot Custom Instructions + Memory — https://learn.microsoft.com/en-us/microsoft-365/copilot/copilot-personalization-memory
- Apple Intelligence Personal Context — https://www.apple.com/newsroom/2026/06/apple-intelligence-brings-powerful-ai-capabilities-into-everyday-experiences/

**Coding-agent conventions:**
- Claude Code memory docs (5-layer hierarchy) — https://code.claude.com/docs/en/memory
- Cursor User Rules deep-dive — https://forum.cursor.com/t/a-deep-dive-into-cursor-rules-0-45/60721
- AGENTS.md spec — https://agents.md/
- Aider CONVENTIONS.md — https://aider.chat/docs/usage/conventions.html

**Disconfirmation (the critical evidence):**
- Gloaguen et al. 2026, ETH Zurich, context-files ablation (ICML 2026 submission; N=138 real GitHub tasks, 4 agents, 4 LLMs) — https://arxiv.org/abs/2602.11988
- Jain et al. 2026, MIT/Penn State, "Personalization features can make LLMs more agreeable" (ACM CHI 2026) — https://www.eecs.mit.edu/personalization-features-can-make-llms-more-agreeable/
- Li et al., P-DPO (OpenReview, 132 citations) — https://openreview.net/forum?id=bqUsdBeRjQ
- Qian et al. 2021 (cited 66×), implicit > explicit user profile — https://qhjqhj00.github.io/files/21learning.pdf
- Writer.com 2026, "Personalized context degrades AI accuracy" (vendor corroboration of CHI 2026) — https://writer.com/engineering/personalized-context-degrades-ai-accuracy/
- arXiv:2403.06833, instruction-vs-data separation — https://arxiv.org/abs/2403.06833
- arXiv:2606.05336 (Jun 2026), self-supervised profile generation reward-hacks by padding — https://arxiv.org/abs/2606.05336
- arXiv:2505.24697, "Towards a unified user modeling language" — https://arxiv.org/abs/2505.24697
- Wu et al. 2024, LaMP ablation — https://arxiv.org/abs/2406.17803
- Augmentcode, "How to Build Your AGENTS.md" — https://www.augmentcode.com/guides/how-to-build-agents-md
- Mindstudio, "Context Rot in Claude Code Skills" — https://www.mindstudio.ai/blog/context-rot-claude-code-skills-bloated-files
- zazencodes, "Stop using AGENTS.md and CLAUDE.md" — https://zazencodes.substack.com/p/stop-using-agentsmd-and-claudemd
- Berkman Klein / WSJ, "Your chatbot has long memory" — https://cyber.harvard.edu/story/2026-05/your-chatbot-has-long-memory-isnt-always-good-thing

**Installable skills surveyed (none ship dedicated operator-model):**
- Truefoundry Skills Registry (USER.md generator) — https://www.truefoundry.com/skills-registry
- BayramAnnakov/claude-reflect — https://github.com/BayramAnnakov/claude-reflect
- thedotmack/claude-mem — https://github.com/thedotmack/claude-mem
- rohitg00/agentmemory — https://github.com/rohitg00/agentmemory
- coleam00/claude-memory-compiler — https://github.com/coleam00/claude-memory-compiler
- awesomeskill.ai/author-profile — https://awesomeskill.ai/skill/claude-code-plugins-author-profile

**Failure modes / ethics:**
- Kantharuban et al. 2024, implicit identity bias — https://arxiv.org/abs/2410.05613
- tianpan.co, profile decay — https://tianpan.co/blog/2026-05-05-personalization-profile-decay-user-model-staleness
- DoorDash, continuous profile loops — https://careersatdoordash.com/blog/doordash-profile-generation-llms-understanding-consumers-merchants-and-items/
- Forbes, AI-driven dark patterns — https://www.forbes.com/sites/federicoguerrini/2024/11/17/ai-driven-dark-patterns-how-artificial-intelligence-is-supercharging-digital-manipulation/

**Research method:**
- Research conducted 2026-07-26 via `/www` pipeline. 5 parallel subagents (academic field, shipping products, coding-agent conventions, personal-agent research, failure modes) + 1 discovery subagent (installable skills) + 1 disconfirmation subagent. The disconfirmation materially flipped the recommendation. Total: 7 subagents, ~110 tool calls, ~9 minutes wall-clock.
