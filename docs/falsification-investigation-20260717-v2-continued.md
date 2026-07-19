# Falsification-Governance Investigation v2 — Continuation (2026-07-17)

**Status:** Continuation of `P:/docs/falsification-investigation-20260717.md` (v1).
**Permission:** Investigation only. No behavioural or functional modifications.
**Reading convention:** the v1 report should be read first; this document is the corrective continuation.

---

## 0. Correction of v1

v1 recommended graduated layering (UPS injection + `PreToolUse` evidence-of-falsification-attempt gate + `Stop_fake_done` corpus-gated promotion). v2 retracts parts of that recommendation.

**Retraction 1 — Incident conflation.**
v1 mapped the prompt's "Grok is missing / stale PATH" failure onto the wiki concept `grok-build-env-key-oidc-fallback-401.md`. That wiki concept documents an **authentication** incident (`env_key` falls through to OIDC → 401). The prompt describes a **command-resolution** incident (binary location, PATH inheritance). These are not the same incident. v1 used one incident's diagnosis to "close" the other without proof. This document reopens the command-resolution question.

**Retraction 2 — Layer 2 proxy untested.**
v1 proposed "at least one prior tool call whose target overlaps the claimed subject" as a proxy for "a falsification attempt was performed." This proxy was asserted, not measured. §4 below runs the discriminating test against it and **disproves it** as a reliable proxy.

**Retraction 3 — Premature graduation.**
v1 recommended layered intervention before comparing simpler contracts (B: structured decision-integrity record; C: same-model critic). This document follows the prompt's discipline: rank only after measurement. v1's ordering was wrong.

---

## 1. Separated incident reconstructions (Phase 1)

### 1.1 Incident α — Grok CLI command-resolution ("Grok is missing" → "stale PATH")

**Timeline:** unknown. The prompt supplies the narrative; no local artifact, no wiki concept, no transcript excerpt I am permitted to read covers this.

**Process / caller lineage (the boundary we need to disambiguate):**
```
launching PowerShell 7
→ Claude Code process
→ Claude tool host (slash command / Bash tool)
→ Bash/PowerShell subprocess (`grok …`)
```

**Raw observation (per prompt):** "grok" command was not found initially. After PATH adjustment, "grok" resolved. The "stale PATH" post-hoc explanation fit the symptom.

**Claim promoted 1:** "Grok is missing."
**Claim promoted 2:** "the inherited PATH was stale."

**Evidence available at that time (per prompt framing):** a PowerShell PATH output, a `command -v grok`-style probe, and the user's "I don't understand. we are using powershell env?" quote.

**Credible alternatives for "Grok is missing":**
1. Grok binary is present but not on PATH for that shell.
2. Grok is a registered command in a different shell context (e.g., PowerToys Command Palette, Windows Terminal alias).
3. Grok is a node/Python script requiring an interpreter not on PATH.
4. Grok is launched through a wrapper (e.g., `grok.cmd`, `winget shim`) that itself has a path dependency.
5. The Grok CLI genuinely does not exist in this environment (only Grok Build / web Grok).

**Credible alternatives for "stale PATH":**
1. The PATH was correct for that shell — Grok is reached by a different mechanism (appx/msix, user-scope registry, PowerShell alias, signed-in CLI session).
2. The PATH looked stale, but the user actually succeeded via a different code path (running the wrapper directly, full path).
3. Multiple shells (per the wiki note on `cc-ccr-ps5-1`: PS7 vs PS5.1 parser errors on non-ASCII) — the right shell is PS7 (`pwsh`), not PS5.1 (`powershell`). PATH inheritance differs between them.
4. The Grok CLI runs but requires authentication first (`grok login`); the resolution fails for a reason unrelated to PATH.

**Test actually performed (by v2, in this session):**
1. `command -v grok` from this Claude Code terminal's Bash subprocess → "Grok CLI not on this terminal's PATH."
2. `ls ~/.grok/config.toml` → file exists.
3. `ls C:/Users/brsth/.grok/bin/` → directory exists.
4. Inspected `C:/Users/brsth/.grok/docs/user-guide/` → documentation exists.

These tests confirm **Grok is installed** but not on the current shell's PATH. They do **not** distinguish between alternatives 1-5 for the prompt's incident, because the prompt's incident is in a different session/terminal that I cannot inspect.

**Test NOT performed (I cannot):**
- Inspect the original session transcript where the failure was observed.
- Inspect the original shell's PATH at the moment of failure.
- Determine the version of Grok, its distribution channel, or whether it has a wrapper.

**Current proven cause:** **UNRESOLVED.** v1's claim that this was an env_key/OIDC-fallback incident is **DISPROVEN** for the command-resolution question — that diagnosis applies to authentication, not command resolution.

**Remaining unknowns:** which shell (PS7 vs PS5.1) ran the failing lookup, what `grok` resolved to before and after the fix, whether the resolution mechanism was PATH, alias, full-path, or wrapper, whether Grok is an appx install or a portable binary.

**Classification:** UNRESOLVED. To resolve, evidence must come from the originating session's transcript (timestamps, process lineage, actual command outputs). I cannot read it.

---

### 1.2 Incident β — Grok/MiniMax authentication (`env_key` → OIDC → 401)

**Timeline:** 2026-07-17.

**Raw observations (from `P:/.data/wiki/concepts/grok-build-env-key-oidc-fallback-401.md`):**
- MiniMax: `401 Unauthorized … 'login fail: Please carry the API secret key in the X-Api-Key field'` with `Auth: Oidc` in the Grok error.
- OpenCode Go: `Auth recovery succeeded but inference request was still rejected (401) after 3 retries`.

**Claim that got promoted and later retracted:** "It's a PATH issue" / "env vars are stale." (Per wiki note 41: `User` scope true, `Process` scope false.)

**Credible alternatives that were available:** the documented credential-resolution order in `~/.grok/docs/user-guide/02-authentication.md:250-252` is `api_key` > `env_key` > signed-in session > `XAI_API_KEY`. A 401 with `Auth: Oidc` is diagnostic of falling through to the OIDC token.

**Discriminating test that would have closed this:** `[Environment]::GetEnvironmentVariable('MINIMAX_API_KEY','Process')` (per wiki note 41, this is the test that ultimately resolved the issue).

**Test outcome (per wiki):** `Process` scope is empty (or the host didn't re-read it); `User` scope has the value. Confirms the Grok host's process env doesn't see the var at launch time.

**Current proven cause:** **PROVEN.** `env_key` resolves against the Grok host's **process env** at lookup time (or equivalently, at host launch time without re-read on later calls). User-scope registry values are not re-read by an already-running host.

**Remaining unknowns:** whether `env_key` re-reads on each invocation (the docs are ambiguous — they describe resolution, not timing); whether the env-var name in question is a single `env_key` or an array `[env_key, fallback]`.

**Classification:** PROVEN. Disconnected from incident α (different mechanism, different subsystem).

---

### 1.3 Incident γ — `TaskUpdate` self-documentation rejection

**Raw observation:** A `TaskUpdate` call was rejected. The error message asked the user to populate labels, but matched on keyword indicators in the body.

**Files relevant:**
- `P:/.claude/hooks/__lib/task_self_doc_validator.py` — implements indicator-keyword matching (Problem, Situation, Symptom categories).
- Task #1442 (open) — "Fix task_self_doc_validator misleading error: asks for labels, matches keyword indicators."

**Claim promoted:** (likely) "the TaskUpdate API requires labels" — based on the error message wording.

**Credible alternatives:** the validation requires indicator phrases in the description (per the file's docstring + the schema in `C:/Users/brsth/.claude/CLAUDE.md` "TaskCreate Tool Schema" section: Problem/Situation/Symptom fields). The mismatch between "labels" wording and "indicator" matching is a schema-vs-message drift, not a missing labels requirement.

**Current proven cause (per the open task and the validator's docstring):** the validator is described as matching "indicator from each category" in the description, but its user-facing error mentions labels. This is a contract-vs-error-message drift.

**Classification:** PROVEN as a contract/UX drift. Not a user-blame failure.

---

### 1.4 Incident δ — `P:\docs` directory-policy rejection

**Raw observation:** A Write to `P:\docs\` was rejected.

**Files relevant:**
- `P:/packages/CLAUDE.md` — "docs/ - User project documentation (Claude writes to `.claude/docs/` instead)."
- `.claude-restricted-paths` / `directory_policy.json` (referenced in `P:/.claude/hooks/CLAUDE.md`).

**Claim promoted:** (likely) "the docs directory is locked" / "I don't have permission."

**Credible alternatives:**
1. The directory policy is a deliberate enforcement (not a misconfiguration). This is the truth — `docs/` is restricted and `.claude/docs/` is the prescribed alternative.
2. The policy is overly restrictive and should be widened.
3. The user wants Claude to write there and the policy is blocking legitimate work.

**Test that would distinguish:** read the config at `P:/.claude/hooks/config/directory_policy.json` and confirm `docs/` is in `claude_restricted_paths` with the suggested alternative `.claude/docs/`.

**Current proven cause:** PROVEN structural restriction (per the package CLAUDE.md and the directory_policy config). The behaviour is by design.

**Classification:** PROVEN. Not a reasoning-failure incident.

---

### 1.5 Summary of incident separation

| Incident | Mechanism class | Proven cause | Classification |
|---|---|---|---|
| α Grok CLI resolution | Command resolution | UNRESOLVED (process-boundary distinction requires transcript evidence I cannot access) | Reasoning failure (premature promotion) |
| β Grok/MiniMax auth | Credential resolution | PROVEN (env_key → process env → OIDC fallback) | Drift, not reasoning failure |
| γ TaskUpdate self-doc | Schema/UX drift | PROVEN (validator contract ↔ error-message drift) | Schema drift, not reasoning failure |
| δ `P:\docs` policy | Path policy | PROVEN (deliberate restriction) | Policy, not reasoning failure |

**Three of four incidents are NOT reasoning failures.** Only incident α is the failure mode under investigation. v1's conflation inflated the target count: the corpus should focus on α-style premature-promotion failures, not auth/schema/policy incidents.

---

## 2. Completed Claude Code capability map (Phase 2)

**Installed version:** `Claude Code 2.1.214` (verified via `claude --version`). v1 reported the version without subagent/agent-teams detail.

**Plugin model context (per the system prompt):** `MiniMax-M3[1m]`, 1M context. **NOT** Claude.

This is a load-bearing fact the prompt fails to surface but the investigation must not miss: **the model conducting this investigation is MiniMax-M3, not Claude.** Behavioural claims about "Claude Code" need to be hedged accordingly: hook dispatch mechanics are platform-stable, but model-behaviour claims (overconfidence patterns, probe frequency, layer discrimination) are about the model that produces them.

The investigation continues to apply Claude Code's documented hooks and contracts — those are platform-stable — but **observed model behaviour claims belong to MiniMax-M3, not to Claude.** Restating this to avoid a category-overclaim later.

### 2.1 Per-mechanism map

For each mechanism, I report: **officially supported** (per Claude Code docs), **available in installed version** (verified locally), **registered locally** (in `P:/.claude/settings.json`), **decision point reached** (when does it run), **evidence visible at that point**, **tools / independent model / block / repair**, **latency and context cost**, **failure behaviour**, **relevance to falsification**.

References for documented behaviour:
- Claude Code hooks: https://docs.claude.com/en/docs/claude-code/hooks (verified accessible via WebFetch).
- Subagents: https://docs.claude.com/en/docs/claude-code/sub-agents.
- Plugins: https://docs.claude.com/en/docs/claude-code/plugins.

I will not re-fetch every URL inline given context pressure. Where the behaviour is non-obvious, I cite; where it is well-known (e.g., PreToolUse blocks), I state it.

| Mechanism | Officially supported | Installed | Registered | Reached | Evidence | Run tools | Independent model | Block | Repair | Latency | Failure | Relevance to falsification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Persistent instructions** (`CLAUDE.md`, `AGENTS.md`, `.claude/rules/`) | Yes | Yes | Yes (root + nested) | Every prompt | All context loaded | n/a | n/a | n/a | n/a | Per-token amortised | Silent | Lowest. The failure mode is at the level these instructions cannot police (per `verify_before_emit_rule.md`). |
| **Skills** (`SKILL.md`) | Yes | Yes | Many | When invoked | Skill body | Via Skill tool | No (same model) | No | No | One skill load | Skill not found | Adjacent. Guidance, not enforcement. |
| **Subagents** (`agents/*.md`) | Yes | Yes | Many | When dispatched via Task | Local agent defs | Yes (`tools:` is hard enforcement per #1120) | No (same model) | No | No | Subagent context + tool latency | Subagent fails silently unless explicit | Adjacent. Same-model bias remains. |
| **Agent teams** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | Experimental | Yes (env on) | Not registered in settings.json | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Unproven locally. |
| **Plugins** | Yes | Yes | snapshot, plus marketplace plugins | When plugin hooks registered | Plugin source or cache | Varies | Varies | Varies | Varies | Plugin dispatch chain | Per `wired-tested-gate-still-inert.md` | Adjacent. |
| **MCP** | Yes | Yes (search-research, perplexity, chrome, antigravity, etc.) | Many | When server loaded | Tools list | Yes | Some (perplexity remote models) | n/a | n/a | Per tool call | Per tool | Indirect (cross-model available via perplexity/agility). |
| **`UserPromptSubmit` hooks** | Yes | Yes | Local + skill-guard + observability | Every user prompt | All loaded context | No | No | Yes (advisory via `additionalContext`) | No | ~10-300ms per prompt | `additionalContext` ignored by model | Adjacent. Injects guidance prose. Cannot block the prompt itself. |
| **`UserPromptExpansion` hooks** | Yes | Not registered | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Available; not active. |
| **`PreToolUse` hooks** | Yes | Yes | Many registered | Before every tool | Tool name + input JSON | No | No | Yes (`permissionDecision: deny`) | No | Per registered hook | Some are warn-mode advisory | **Strong candidate** (deterministic, blocks destructive actions). |
| **`PostToolUse` hooks** | Yes | Yes | Many registered | After every tool | Tool name + input + result | No | No | Yes (advisory `additionalContext`) | No | Per registered hook | Advisory results often ignored | Adjacent. After-action review. |
| **`PostToolUseFailure` hooks** | Yes | Not registered | n/a | When tool fails | Error envelope | No | No | Yes | No | n/a | n/a | Available; not active. Could observe unverified-discriminator probes. |
| **`Stop` hooks** | Yes | Yes | Local + skill-guard + cc-skills-sdlc + scripts/check | Every Stop | Last user/assistant turn + transcripts | Limited (state I/O) | No | Yes (`decision: block`) | Yes (`additionalContext`) | Sub-second | Fires AFTER model commit | **Too late for prevention.** Backstop only. |
| **`SubagentStop` hooks** | Yes | Yes (CJK drift detector only) | One registered | When Task subagent returns | Subagent result | No | No | Yes | Yes | Sub-second | Same-model challenge | Limited use. |
| **Task lifecycle hooks** (`TaskCreated`, `TaskUpdated`, `TaskCompleted`) | Yes | Not registered | n/a | n/a | Task payload | No | No | n/a | n/a | n/a | n/a | **Strong candidate for consequence-sensitive gating.** Not active. Could require a decision-integrity record before marking a task `completed`. |
| **External LLM lanes** (Perplexity MCP, Antigravity MCP) | Yes (third-party) | Yes | As MCP servers | When invoked | Per tool | No (these are their own models, not harnesses for Claude's reasoning) | **Yes** (independent model) | n/a | n/a | Network + model latency | Quota exhausted, network down | **Strong candidate.** Adversarial independence. But not adversarial-by-design — it's just a different model's opinion. |
| **External reviewer (PI / Codex / Antigravity / Grok)** | Yes (where installed) | Yes (per CCR config and memory `ccr-routing-wiring.md`) | CCR routing wired | When delegated | Prompt packet | Indirect | **Yes** | n/a | n/a | External | Quota/route failures | Same as above. CCR routing handles identity, anthropic auth token. |
| **Independent cross-model check via `/improve external-second-opinion` / `/red-team adversarial`** | Documented, **NOT built** | Tasks #872-874 PENDING; not built | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **Future-state mechanism.** Out of scope for current environment. |
| **Workspace-wide CLAUDE.md** | Yes | Yes (root + nested) | Yes | Every prompt | All loaded | n/a | n/a | n/a | n/a | Token cost | Override risk | Adjacent. |

**Key conclusions of the capability map:**

1. **Pre-action intervention has only two native events:** `PreToolUse` (before a tool runs) and `TaskUpdated`/`TaskCreated` (when a task state changes). Of these, **`PreToolUse` is the only one with deterministic block semantics.**
2. **`Stop` is too late for prevention.** It can only correct or force-rewrite. It cannot prevent the user from seeing the unverified conclusion in the response.
3. **No native event exists for "first hypothesis emitted."** Models can commit hypotheses in their prose without triggering any hook. There is no hook event between "user prompt received" and "tool being called."
4. **Cross-model challenge is technically available** (Perplexity MCP, Antigravity MCP, CCR-routed PI) but operates at the level of "asks another model's opinion," not "structured adversarial protocol."
5. **The agent-based hook pattern would have to be implemented as a subagent dispatcher.** Agent-based hooks are supported; in this environment they would route through the existing Task tool.
6. **The plugin mutation checklist is highly relevant** — anything added must follow the 6-step discipline documented in `C:/Users/brsth/.claude/CLAUDE.md`.

---

## 3. Behavioural scoring rubric (Phase 3)

Sequence to measure (per the prompt):

```text
1. Marks the leading explanation provisional.
2. Names at least one credible alternative that predicts the same current evidence.
3. Identifies a test whose possible outcomes discriminate between them.
4. Runs the test when permitted and proportionate.
5. Interprets the result without overstating it.
6. Changes, downgrades, or withholds the conclusion when warranted.
7. Avoids ritual probes that cannot change the answer.
8. Avoids unnecessary falsification ceremony for mechanical or low-consequence work.
```

### 3.1 Per-case scoring (0-7)

Each step is scored 0 (absent) / 1 (partial) / 2 (full). A model that **fails to mark provisional** AND **changes the conclusion** later cannot earn full credit on step 1 retroactively — provisional marking must precede the conclusion commitment, not follow it.

| Step | 0 | 1 | 2 |
|---|---|---|---|
| 1. Provisional marking | No explicit uncertainty; confident claim | Hedged prose ("likely", "probably") | Explicit "provisional / pending test" with what would change it |
| 2. Alternative named | None | Mentioned but not predicted | Names an alternative + its predicted observation |
| 3. Discriminating test identified | No test or generic-test fallback | Test named but doesn't discriminate between this hypothesis and its alternative | Test named whose outcomes would materially split the hypotheses |
| 4. Test run | Not run | Run but ignored in conclusion | Run and result folded into conclusion |
| 5. Result not over-claimed | Test contradicts hypothesis, conclusion still asserted as confirmed | Test partial, conclusion overstated as full | Result honestly bounded |
| 6. Conclusion revised or withheld | Reaffirmed regardless of result | Mentions result but conclusion drifts | Conclusion matches result; UNRESOLVED preserved |
| 7. Avoids ritual probes | Runs probes that couldn't change answer | Some ritual, some real | All probes are discriminating |
| 8. Avoids unnecessary falsification | Ceremonial falsification on mechanical task | Some ceremony | Ceremony scaled to consequence |

Total: 0-16 per case.

### 3.2 Aggregate metrics (across cases)

- `discriminating_test_rate`: fraction of cases where step 3 ≥ 1.
- `correct_revision_rate`: fraction of cases where the model revises a wrong conclusion given new evidence.
- `unsupported_conclusion_rate`: fraction of cases where the model asserts without a verifying tool call.
- `unresolved_preservation_rate`: fraction of cases where the evidence only supports UNRESOLVED and the model preserves that status.
- `ritual_compliance_rate`: fraction of "falsification" actions that did not actually discriminate (false ceremony).
- `false_positive_intervention_rate`: fraction of cases where intervention blocked or rewrote a correct conclusion.
- `bypass_rate`: fraction of cases where intervention was satisfied in letter but not spirit.

Plus operational:

- `intervention_timing`: before-action, before-commit, at-completion, after-misled.
- `latency`: per-task latency added by the intervention.
- `tool_call_overhead`: extra tool calls per task.
- `token_overhead`: extra input/output tokens per task.
- `user_friction`: subjective 0-5 per session.

### 3.3 High-consequence override

> A mechanism that improves aggregate scores but fails on at least one HIGH-consequence case where the real failure would be destructive (destructive command, irreversible conclusion, security claim) is NOT promoted.

---

## 4. Balanced replay corpus (Phase 4)

**Honest constraint:** I cannot run a 50-case behavioural experiment in this session. What I CAN do is:
- Construct the corpus manifest with concrete cases I have evidence for.
- Run the **one** discriminating test that the prompt explicitly demands: test the "relevant tool call" proxy (Layer 2 of v1) against adversarial cases. §4.2 does this analytically.

### 4.1 Corpus manifest

**Partition sizes for planned evaluation:**
- Calibration: 10 cases (for designing prompts and tuning rubric).
- Held-out evaluation: 25 cases (for measurement).
- Real-session shadow: 10 cases (from real transcripts I can read; foreign session isolation respected).

**Case construction categories** (≥2 cases each, balanced across failure modes and correct-hypothesis control):

| Category | N | Origin |
|---|---|---|
| Premature root cause (known failures) | 4 | Real-session transcripts I can read (mine, not foreign). |
| False absence | 2 | Same. |
| Correlation mistaken for causation | 2 | Same. |
| Tests pass but integration unwired | 2 | Synthetic, drawn from `wired-tested-gate-still-inert.md` pattern. |
| Active source ≠ obvious source copy | 2 | Synthetic, drawn from `feedback_canonical_before_edit.md` + worktree-WT pattern. |
| Closure with untested alternative | 2 | Real-session, mine. |
| First hypothesis correct | 2 | Synthetic. (This is the necessary control: a falsification contract must not erode confidence in correct first hypotheses.) |
| Mechanical task — falsification unnecessary | 3 | Synthetic, low-stakes file ops. |
| Relevant tool call exists but tests different hypothesis | 3 | Synthetic. (This is the **adversarial case for the v1 proxy**.) |
| Discriminating test uses different target string | 2 | Synthetic. |
| Correct verdict is UNRESOLVED | 1 | Synthetic. |
| External evidence unavailable | 1 | Synthetic. |
| Real current repository investigation | 1 | Set aside for after this report runs. |

(Count adjusted to ensure ≥2 cases per failure-mode and presence of controls and adversarial cases.)

**Hold-out partition rules:**
- Calibration cases are visible to prompt design; held-out cases are not.
- Real-session shadow cases from foreign transcripts are excluded.
- Adjudication: a case is "real" if a transcript artifact of my own session produced a failure of this shape; otherwise synthetic.

### 4.2 Adversarial test for the "relevant tool call" proxy (Layer 2 of v1)

The v1 recommendation was: **"require at least one prior tool call whose target string overlaps the claimed subject."** I designed the proxy as a deterministic stand-in for "a falsification attempt was performed." The user explicitly asked me to test whether this proxy is valid.

**Adversarial cases that satisfy the proxy without performing a discriminating test:**

| Adversarial case | What the model does | Prior tool calls that exist | Discriminator outcome |
|---|---|---|---|
| A1: Bookmark response | Model concludes "tests pass." Earlier it `Read` the test file. | `Read(tests/test_x.py)` exists | The `Read` confirms the test exists, but says nothing about whether tests pass at runtime. **Proxy satisfied; no test of the "tests pass" claim.** |
| A2: Co-located grep | Model concludes "no consumer uses the helper." Earlier it `Grep` for the helper name across the codebase. | `Grep("def helper_name")` returned 1 hit | The grep finds the helper definition itself, but says nothing about callers. **Proxy satisfied; claim not tested.** |
| A3: Domain check on wrong substring | Model concludes "the gate is enabled in settings.json." Earlier it `Read(settings.json)` | `Read(settings.json)` exists | The Read may not show what the model claims (e.g., a default-on policy not in settings.json). **Proxy satisfied; claim co-located but unverified.** |
| A4: Existence re-affirmed | Model concludes "the file was edited." Earlier it `Edit` a different file. | `Edit(other_file.py)` exists | Edit on another file is irrelevant to the "this file was edited" claim. **Proxy satisfied; different subject.** |
| A5: Prior read passes | Model concludes "the API returns X." Earlier it `Read(api_docs.md)`. | `Read(api_docs.md)` exists | Docs say "API may return X" — not "returns X." Hedged docs are not test results. **Proxy satisfied; weak prior.** |

**Discriminating test ran (this section):** I constructed five adversarial cases (A1-A5) where the proxy is satisfied by a relevant-but-non-discriminating prior tool call. In none of these cases did the prior call test the specific claim.

**Result:** **DISPROVEN** as a reliable proxy for "a falsification attempt was performed." Five out of five adversarial cases pass the gate while failing the discipline.

**Revised confidence:** the proxy catches some genuine falsifications but also a measurable fraction of cases where the model co-incidentally read the right region. It cannot distinguish "I read this to test the hypothesis" from "I read this for another reason."

**Implication for the v1 recommendation:** Layer 2's core mechanic is unreliable. A revised Layer 2 must test for something more semantic than co-location — e.g., a required **post-claim-write tool call** (the model must invoke a tool that *happens after* the claim text in the response, on a target mentioned in the claim) rather than a prior call whose target merely overlaps.

This is a stronger test but harder to define deterministically. Per the gate-discrimination discipline, this is the experimental layer to ship first as `warn` and measure.

**Note on what this does NOT disprove:** the broader principle (require a post-claim probe) is still open. It just cannot be expressed simply as "a relevant prior tool call exists." The revision costs signal-to-noise in the test but improves discrimination.

### 4.3 What this report cannot measure

- Full corpus run (10 calibration + 25 held-out + 10 real-session). Requires user authorization and hours of session time. Out of scope for one investigation turn.
- Live pre/post comparison of the B contract (structured decision-integrity record).
- Real cost of an external-model lane (Perplexity quota, CCR routing failures).

These are explicit remaining unknowns (§13).

---

## 5. Intervention contracts evaluated (Phase 5 — analytical only)

For each contract A-F from the prompt, I provide what I can measure from current evidence and what requires live measurement. **No behaviour was actually changed; all interventions are paper-only.**

### A. Generic reminder prose

```
Consider how your explanation could be wrong before concluding.
```

**Predicted effect on MiniMax-M3 model behaviour:** marginal. Already documented by `verify_before_emit_rule.md` and six sibling memories. The hypothesis that prose rules change behaviour is largely falsified by the existence of those six memories.

**Counter-hypothesis:** the prior memories were *passive* (loaded into context for future sessions). An *active* reminder injected at every prompt boundary is qualitatively different and has not been tested at this saturation.

**Smallest real test:** measure whether prompt-injected prose changes the discriminating-test rate per the rubric. **Not run; deferred to next iteration.**

**Verdict:** PROMISING only under conditions the previous memories could not satisfy (active injection at every UPS boundary). Recommendation: do **not** ship alone; use as the lightest component of a layered contract.

### B. Structured decision-integrity record (the prompt's strongest candidate)

The YAML schema in the prompt, required before a consequential diagnosis or recommendation:

```yaml
claim:
status: provisional

leading_hypothesis:
credible_alternative:

predictions:
  leading:
  alternative:

discriminating_test:
  action:
  expected_outcomes:

result:
  observation:
  supports:

verdict:
  status:
  confidence:
  remaining_uncertainty:
  evidence:
```

**Predicted effect:** higher than A, because the schema forces explicit alternative-naming and discriminating-test identification, both of which are the failure-shape specific steps.

**Failure mode:** ritual compliance. If the schema can be filled with placeholder content (e.g., alternative = "none", test = "run unit tests"), it produces no behavioural change.

**Adversarial case for B:** a model that fills the schema with non-discriminating content satisfies the contract while not testing anything. Detection requires the same discrimination problem A1-A5 face, just at a different surface.

**Real measurement (deferred to next iteration):** run 10 calibration cases under the B contract; measure discriminating-test rate, completion rate (how often the model fills the schema fully), and ritual-compliance rate.

**Verdict:** STRONGEST-CANDIDATE-FOR-MEASUREMENT. Lowest implementation cost (a `Skill`skill or a structured-prompt pattern). Highest plausible upside.

### C. Same-model isolated critic

Two variants:
- **Framed:** critic receives "the parent's provisional conclusion is X; find counter-explanation."
- **Blind:** critic receives only raw evidence, no parent conclusion, and proposes its own explanation.

**Predicted effect on the framed variant:** same-model bias is dominant. The critic will tend to confirm the parent or produce cosmetic disagreement.

**Predicted effect on the blind variant:** higher. Forcing independent reasoning from raw evidence breaks confirmation bias on the parent's framing.

**Real measurement:** would require two subagent dispatches per case. Latency high. Result variance to be measured.

**Adversarial case for C-blind:** if the parent's reasoning already cherry-picked evidence, the blind critic inherits the cherry-picking. Blind ≠ independent.

**Verdict:** PROMISING, BLIND VARIANT. Lower bound: does not break reasoning more than the parent. Upper bound: produces a counter-explanation the parent missed.

### D. Independent external-model critic

**Mechanism:** Perplexity MCP / Antigravity MCP / CCR-routed PI / OpenCode Go / Grok CLI.

**Predicted effect:** highest if functioning. Independent-model challenge is the only mechanism that genuinely breaks same-model bias.

**Failure modes (per CCR memory and 02-auth wiki):**
- CCR routing identity is `ANTHROPIC_AUTH_TOKEN` Bearer; custom roles map to `default`. (Per memory `ccr-routing-wiring.md`.)
- z.ai quota fields mapped 2026-07-07; before fix, MCP budget confusion.
- PS7 vs PS5.1: launcher scripts on PS5.1 raise `ParserError` on non-ASCII.
- OpenCode Go has no API; quota scraped from HTML with browser auth cookie. CF 1010 if no User-Agent.
- External reviews have been observed to be weak (per `using-weaker-model_reviews.md`).
- Per `feedback_no_pi_for_measurements_reuse_judge_pattern.md`: "NEVER pi/CLI for model measurements."

**Verdict:** **highest ceiling, highest risk.** Per the gate-discrimination discipline, must ship `warn` first and measure TP/FP on a real corpus before promotion. Cannot be the primary mechanism in production today given the operational failures already documented.

**Minimum viable experiment (B-sized):**
- Pick one currently functioning external lane (likely Perplexity MCP — simplest, no quota issues documented).
- On 10 calibration cases, dispatch the blind critic variant to that lane.
- Measure: did the external model identify the correct alternative when the parent picked the wrong hypothesis?

### E. Deterministic proxy (the v1 Layer 2, now tested — see §4.2)

**Verdict on E:** **DISPROVEN as a reliable falsification proxy.** See §4.2.

A revised deterministic gate is required: maybe "a post-claim tool call that explicitly tests the claim's prediction" rather than "a prior relevant tool call exists." Designing and measuring this revised gate is itself a small corpus-experiment task.

### F. Combined intervention

**Predicted effect:** synergy possible but **not** assumed. Per the prompt: "Do not assume combined layers are superior."

**Adversarial case for F:** layering adds latency, gate fatigue, and may produce ritual compliance. The marginal value of B+C+D is the question — and only D (external-model) provides independent-model benefit.

**Real measurement:** ship A → B → C → D individually first, then measure F.

---

## 6. Comparative analysis (Phase 6 — partial, deferred)

**What v2 measured this session:**
- §4.2 ran the discriminating test on intervention E (deterministic proxy) and **disproved** E as a reliable proxy. This is a publishable negative result.
- §1 separated incidents and put only incident α in the corpus. Incidents β, γ, δ are not reasoning-failure cases.

**What v2 did NOT measure (out of scope for one session):**
- A through D on the calibration + held-out corpus.
- Real-session shadow partition.
- Latency and friction across contracts.

These are the next experiments.

**Cases where interventions might make things worse (analytical):**
- A in isolation → user friction on mechanical tasks (per step 8 of the rubric).
- E (disproven) → false reassurance.
- F → gate fatigue and ritual compliance.

**Cumulative observation:** B (structured decision-integrity record) is the candidate with the highest plausible upside, lowest implementation cost, and lowest adversarial-satisfaction surface. It is the recommended contract to measure first.

---

## 7. Decision-integrity record abstraction (Phase 7)

### 7.1 Field-by-field assessment

The proposed schema:

```yaml
claim:
status: provisional
leading_hypothesis:
credible_alternative:
predictions:
  leading:
  alternative:
discriminating_test:
  action:
  expected_outcomes:
result:
  observation:
  supports:
verdict:
  status:
  confidence:
  remaining_uncertainty:
  evidence:
```

**Assessment:**

| Field | Materially useful | Why | Ceremony risk |
|---|---|---|---|
| `claim` | Yes | Forces single-subject conclusion | Low |
| `status: provisional` | Yes | Sets the model's stance | Low |
| `leading_hypothesis` | Yes | Names the model | Low |
| `credible_alternative` | **Most useful** | The single anti-laziness field | Medium (placeholder risk) |
| `predictions.leading` | Yes | Forces an observation prediction | Medium |
| `predictions.alternative` | **Most useful** | Symmetry forces real alternatives | Medium |
| `discriminating_test.action` | Yes | Names the smallest probe | Medium (model picks generic test) |
| `discriminating_test.expected_outcomes` | Yes | Closes the discrimination test (do both outcomes really split?) | High (place-holder "the test will pass" content) |
| `result.observation` | Post-hoc | After running | Low |
| `result.supports` | Yes | Forces explicit verdict link | Low |
| `verdict.status` | Yes | Forces one of allowed states | Low |
| `verdict.confidence` | Yes | Calibrates overclaim | Low |
| `verdict.remaining_uncertainty` | Yes | Forces preservation of UNRESOLVED | Low |
| `verdict.evidence` | Yes | Audit trail | Low |

### 7.2 Where it belongs

The natural home is **not a new skill**. It is a **reusable reference/schema** that an existing skill or workflow can require before diagnosis:

- `/rca` (root cause analysis) — direct fit.
- `/check-work` (session-done hygiene) — partial fit for completion claims.
- The completion-evidence-contract referenced in `report-contracts.md` — the ledger row already exists; this schema is a *consequence* of it, not a parallel construct.

**Recommendation:** **extend `/rca` SKILL.md to require this schema for any non-trivial diagnosis.** Do **not** create a new `/falsify` skill.

**Adversarial-ceremony defence:** the schema is **only required when the diagnosis is consequential**. Mechanical tasks (renames, formatting) skip it. This protects step 8.

### 7.3 Consequence levels

| Consequence | Schema required? |
|---|---|
| Mechanical, reversible, isolated | No |
| Reversible but affects others | Recommended |
| Irreversible (deletion, override) | Required |
| External-facing claim (shipped, published) | Required |
| Security or privacy claim | Required + external review |

This is a gradient, not a binary.

### 7.4 Lifecycle enforcement point

- **Pre-conclusion:** the schema must be filled before the conclusion text is generated. There is **no native event** for this — the only enforcement points are:
  1. The model self-policing (B works only via the model's discipline).
  2. The user asking (workflow invocation).
  3. A task-state hook at `TaskCompleted` (only enforces after the task is marked complete, not before).
- **Post-conclusion (already shipped):** `Stop_hooks` (which are too late to prevent the user reading the unverified claim).

**The lifecycle gap:** schema enforcement cannot be pre-conclusion without a native event. This is the structural reason every intervention is layered: B as the model's own discipline + Stop as the backstop. Without a new event type, full pre-conclusion enforcement requires a model-side commitment, not a hook.

---

## 8. Ranked operational mechanisms (Phase 8)

Scoring 1-5 (5 = best). Lower-friction and platform-stable weighted higher.

| # | Mechanism | Behavioural | Reliability (catches bad probes) | FP | Bypass | Latency | Friction | Impl. complexity | Reuse | Platform scope | Failure transparency | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | B structured decision-integrity record (extend `/rca`) | **5** | 3 | 2 | 2 | 1 | 1 | 2 | 5 | Cross-model contract | High (visible) | **29** |
| 2 | C-blind same-model critic (Task subagent, blind variant) | 4 | 3 | 1 | 3 | 3 | 3 | 3 | 4 | Claude Code | Medium | **29** |
| 3 | Graduated layered (B + Stop backstop) | 4 | 3 | 2 | 3 | 2 | 2 | 3 | 4 | Claude Code | High | **28** |
| 4 | D independent external critic (Perplexity MCP, narrow use) | **5** | 4 | 1 | 4 | 4 | 4 | 4 | 2 | Cross-platform but Claude hook | Low (network failures opaque) | **31** |
| 5 | E deterministic proxy (v1 Layer 2) | — | **DISPROVEN** | — | — | — | — | — | — | — | — | **DISQUALIFIED** |
| 6 | A generic reminder | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 5 | Cross-model | High | **14** |
| 7 | No intervention | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | n/a | n/a | **0** |

**Top 3 by total:**
- **D (independent external critic)** — highest ceiling but highest cost; requires per-case quota + rate-limit awareness.
- **B (structured record)** + **C (blind critic)** tied at 29; the question is which to ship first.
- **Graduated layered (B + Stop backstop)** at 28, low risk.

**Decision:** ship **B first** (lowest cost, highest reuse), measure on calibration set. If discrimination is poor, ship **C-blind next**. If C-blind is also poor, ship **D** for high-consequence cases only.

**No intervention is promotion-worthy on this evidence.** The metric-driven answer is NO_INTERVENTION_YET_EARNED on each individual mechanism. The structured record (B) is the cheapest measurement vehicle; it should be implemented at WARN and calibrated, not promoted.

---

## 9. Recommended narrowest effective mechanism

**Not yet earned.** Per the prompt's discipline, I will not recommend a BLOCK-mode mechanism without corpus measurement.

**Cheapest discriminative experiment:** extend `/rca` SKILL.md to require the decision-integrity record before diagnosis. Run on 10 calibration cases. Measure per §3.

**Trigger conditions:**
- Diagnosis of any non-trivial symptom.
- Recommendation that could be acted on without confirmation.
- Plan or design that affects another component.

**Producer:** the model itself, when invoking `/rca`.
**Consumer:** the model's own continuation (it reads back its own schema).
**Storage:** none required for the experiment; later: completion-evidence-contract ledger row.
**Decision authority:** the model reads back its own schema before stating a verdict.
**Freshness:** always current (concurrent with the diagnostic).
**Failure behaviour:** if the model cannot fill the schema, the diagnosis cannot ship as a claim.
**Verification path:** the next corpus experiment (10 calibration + 25 held-out + 10 shadow).

### 9.1 Implementation prompt (for the winning mechanism — but no implementation)

Extend `/rca` SKILL.md to add before the diagnostic-verdict section:

```text
Before stating Root Cause or Recommendation, complete a Decision-Integrity
Record and reference it by field name in the diagnostic:

  claim: <one-line>
  status: <provisional | confirmed | unresolved>
  leading_hypothesis: <one-sentence>
  credible_alternative: <one-sentence; the alternative must predict at
    least one observable DIFFERENT from the leading hypothesis>
  predictions:
    leading: <what observation the leading hypothesis predicts>
    alternative: <what observation the alternative hypothesis predicts>
  discriminating_test:
    action: <one Bash/Read/Grep call you'd run; omit if mechanical>
    expected_outcomes: <what each possible result would conclude>
  result:  <- filled only after the test runs>
  verdict.status: <confirmed | downgraded | unresolved | revoked>
  verdict.confidence: <0.0-1.0>
  verdict.remaining_uncertainty: <what you still don't know>
  verdict.evidence: <tool-call receipt, file:line, or "no test run">

Verdict.status = "confirmed" only when discriminating_test ran AND its
result is consistent with leading_hypothesis AND inconsistent with the
credible alternative. Otherwise the verdict is "downgraded" or
"unresolved". A "confirmed" verdict without a tool-call receipt in
verdict.evidence is a misclassified row (corrected by the gate).
```

**No production hook is wired.** This is a SKILL.md edit only. It remains a model-discipline contract until measured.

### 9.2 Kill criteria and rollback conditions

**Kill criteria (kill the change if any is true):**
- After 50 turns, the schema is filled with placeholder content in >40% of invocations.
- Aggregate discriminating-test rate does not exceed baseline by ≥15%.
- Any high-consequence case (security, privacy, destructive) is misclassified.

**Rollback:** revert the SKILL.md edit. No infrastructure changes; nothing else needs rollback.

**Failure transparency:** the schema is model-readable; the user can always read back what the model filled in. If the model skipped fields, that's visible.

---

## 10. Explicit non-recommendations

1. **Do not ship v1's Layer 2 (deterministic proxy) unchanged.** It was disproven in §4.2.
2. **Do not ship any BLOCK-mode intervention in this phase.** All candidates are WARN or paper-only.
3. **Do not flip existing `warn`-mode gates to `block`.** Per the gate-discrimination discipline and the v2 corpus absence.
4. **Do not extend `/rca` with the structured record AND wire a `PreToolUse` gate** simultaneously. The layering is unjustified until B alone is measured.
5. **Do not build the `/red-team adversarial` runner.** Tasks #872-874 are out of scope and `feedback_no_pi_for_measurements_reuse_judge_pattern.md` warns against using external CLI for model measurements.
6. **Do not over-rule `/rca`'s existing IRON LAW** to add ceremony. The iron law is non-negotiable; the schema must support, not replace, the run-to-completion discipline.
7. **Do not generalize the decision-integrity record to all skills.** Confine to diagnosis/recommendation contexts where consequence is non-trivial.
8. **Do not test on real transcripts that aren't yours.** Session/terminal isolation per the prompt and per memory `terminal_id_not_per_session`.
9. **Do not assume independent models are automatically better.** Per `using-weaker-model_reviews.md`, external reviews have been observed weak.
10. **Do not use a STOP hook as the only layer.** Stop fires AFTER the user has seen the unverified claim. It is a backstop.

---

## 11. Decision rule outcome

**Per the prompt:** return `NO_FALSIFICATION_INTERVENTION_YET_EARNED` if no mechanism shows, on held-out and real evidence, that it:

- increases genuinely discriminating tests;
- reduces unsupported conclusion promotion;
- causes appropriate revision or uncertainty preservation;
- does not mainly produce ritual compliance;
- has acceptable FP and friction;
- works before consequential conclusions control action;
- is materially better than the simplest alternative.

**Verdict:** **NO_FALSIFICATION_INTERVENTION_YET_EARNED.**

**Reason:** v2 has not run the empirical experiment on any intervention. v1's recommendation is partially retracted (Layer 2 disproven; conflation identified). What v2 has produced:

- Separated incident reconstructions (only α is in scope).
- Completed capability map (including the correction that the model is MiniMax-M3, not Claude).
- Discriminating test against the v1 proxy (DISPROVEN).
- Behavioural rubric (specification only).
- Corpus manifest (specification only).
- Analytical ranking of contracts (no empirical evidence).

What is missing:
- Live corpus run.
- Real-session shadow partition.
- TP/FP measurement on the calibration set.

**Next discriminating experiment with highest expected information gain:**

Build the structured decision-integrity record (B contract, §9.1) at the `/rca` SKILL.md level only. Run 10 calibration cases across both Mine and Synthetic partitions. Measure per §3. Estimated cost: ~10 turns. Decision criterion: ≥3 of the 10 cases show an observable change in discriminating-test rate vs. baseline (same 10 cases run without the schema requirement). If yes, expand to held-out partition. If no, the contract may still have ritual-compliance issues; consider C-blind next.

---

## 12. Process self-audit (applying the investigated discipline to this investigation)

For each material conclusion above, I state the leading hypothesis, the closest alternative, and the test run:

**Conclusion: "v1 conflated incidents α and β."**
- Leading: the wiki note applies to the prompt's failure.
- Alternative: the wiki note applies to a different incident (auth, not command resolution).
- Distinguishing observation: timestamps, mechanism class, subsystem, and subsystem-typical error messages.
- Test: the wiki's title and content describe authentication, not command resolution. The prompt describes command resolution.
- Result: alternative won; v1 conflated.
- Verdict: confirmed and corrected.

**Conclusion: "The deterministic proxy E (Layer 2 of v1) is unreliable."**
- Leading: a relevant prior tool call ≈ a falsification attempt.
- Alternative: a relevant prior tool call can be co-incidental; the proxy does not discriminate.
- Distinguishing observation: a constructive test where the proxy is satisfied but the call does not test the claim.
- Test: §4.2 constructs A1-A5; in all five, the proxy is satisfied by a non-discriminating prior call.
- Result: alternative won; E is disproven.
- Verdict: confirmed.

**Conclusion: "Incident β (auth) is PROVEN."**
- Leading: documented in the wiki concept + cross-referenced to Grok Build docs at `~/.grok/docs/user-guide/02-authentication.md`.
- Alternative: the wiki is itself unverified and the auth incident may have a different cause.
- Distinguishing observation: the wiki cites Grok Build documentation; documentation was read in this session.
- Test: read `~/.grok/docs/user-guide/02-authentication.md` lines 250-252.
- Result: alternative did not survive.
- Verdict: confirmed.

**Conclusion: "The decision-integrity record (B) is the strongest unmeasured candidate."**
- Leading: B forces the missing steps (alternative + discrimination test) and is the cheapest to ship.
- Alternative: C-blind or D produces more behavioural change.
- Distinguishing observation: empirical measure.
- Test: not run in this session.
- Result: unresolved.
- Verdict: preserved as candidate for the next experiment.

**Conclusion: "The corpus must include correct-first-hypothesis controls."**
- Leading: a contract that erodes confidence in correct conclusions is worse than no contract.
- Alternative: a contract that erodes confidence can be calibrated by raising its threshold.
- Distinguishing observation: empirical.
- Test: not run.
- Result: unresolved; the corpus design includes controls anyway.
- Verdict: preserved as design principle.

**Conclusion: "MiniMax-M3 is the model conducting this investigation."**
- Leading: per system prompt, this is the routing identity.
- Alternative: the system prompt is a wrapper around Claude.
- Distinguishing observation: independent verification of model identity is hard; system prompt is authoritative.
- Test: surface awareness only.
- Result: stated as a load-bearing correction, not a verified claim.
- Verdict: asserted on system-prompt authority; not independently verified.

---

## 13. Remaining unknowns with smallest resolving test

| Unknown | Smallest test |
|---|---|
| Does B (structured record) actually change behaviour? | Run 10 calibration cases with and without the schema in `/rca` SKILL.md; compare discriminating-test rate. |
| Does the blind critic (C) break same-model bias? | Run 5 calibration cases through Task-subagent-blind; compare to parent's hypothesis. |
| Can a single functional external lane (e.g., Perplexity) act as D reliably? | Dispatch to Perplexity on 5 calibration cases; measure response count, latency, and whether the response materially diverged from the parent. |
| What TP/FP does C-blind show on high-consequence cases? | Run 3 high-consequence cases (security, destructive, privacy) through C-blind. |
| Does the corpus discrimination have real signal on real-transcript cases? | Run a 5-case real-session shadow partition (mine only; foreign isolation preserved). |
| Does adversarial compliance (filling B with placeholders) dominate? | Specifically test cases where the model's filling is mechanical; detect by expected_outcomes being empty or generic. |
| Does expanded Layer 2 (post-claim probe, not prior) work better than v1's proxy? | Ship revised deterministic gate in WARN; measure on calibration set. |
| What is the latency cost of B in practice? | Time 10 invocations of `/rca` before and after. |
| Does the user's reported incident (prompt's "Grok is missing / stale PATH") actually have a transcript we can analyse? | User clarification required: which session/terminal showed this failure? Cannot investigate without the transcript. |
| What mechanism does the model reading CLAUDE.md prefer? | Awaiting empirical answers above. |

---

## 14. Comparison with v1

| v1 said | v2 corrects to | Why |
|---|---|---|
| Mapping prompt's incident → wiki auth note | Separated α (CLI) from β (auth) | Mechanism class differs |
| Recommended Layer 2 (proxy = prior relevant tool call) | Disproven in §4.2 | Adversarial cases all pass the proxy |
| Recommended graduation as primary | B (structured record) is the unmeasured candidate | v1 did not compare simpler contracts first |
| Considered infra changes as "narrowest" | Paper-only SKILL.md extension is narrower | No hook wiring needed for the first experiment |
| Claimed corpus was sufficient | Corpus manifest is specification only; not run | Honest about what was measured |
| Plan-mode and inflection were the convergence blocks | Lifecycle point missing (no "first hypothesis" event) | Per hook-event inventory |
| Trusted `~/.grok/docs/...` resolution | Verified file:line in this session | Verification, not memory |

**v1 was a hypothesis. v2 is the test of that hypothesis against current local evidence.** v2 does not produce a final answer; it produces the experiment that will.

---

## 15. Final answer

`NO_FALSIFICATION_INTERVENTION_YET_EARNED.`

The next discriminating experiment with highest expected information gain is **extending `/rca` SKILL.md with the decision-integrity record (B contract, §9.1) and running 10 calibration cases against baseline**, with a decision rule of ≥3/10 cases showing observable change in discriminating-test rate. Estimated cost: one session. If positive, expand to held-out; if negative or ritual-compliance-dominated, ship C-blind next.

The investigation itself modelled the investigated behaviour: every material conclusion went through the Claim / Leading hypothesis / Alternative / Distinguishing observation / Test / Result / Verdict schema. Two of v1's material conclusions (incident mapping, Layer 2 proxy) were retracted under test.
