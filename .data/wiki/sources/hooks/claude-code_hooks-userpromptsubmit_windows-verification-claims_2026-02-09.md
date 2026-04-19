<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# in claude code on windows 11, can a Stop hook reliably detect "confident quantitative claim without prior observation"?

**No, a Stop hook in Claude Code on Windows 11 cannot reliably detect "confident quantitative claims without prior observation."**

Stop hooks fire after Claude finishes generating a response but before it is fully committed, receiving only metadata like `session_id`, `transcript_path`, `cwd`, `hook_event_name`, and `stop_hook_active`—no direct access to the response text itself. To check for claims, the hook must parse the latest entry from the `transcript_path` (a JSONL file), but this often contains stale data from prior turns since the current response isn't written yet.[^1_1][^1_2]

This timing issue makes detection unreliable, as confirmed in your past troubleshooting with hooks like `StopHook_reality_check.py` and community reports. On Windows 11, additional challenges like PowerShell execution and blocking inconsistencies compound the problem, though the core limitation is architectural.[^1_3][^1_4][^1_1]

## Workarounds

- **UserPromptSubmit hooks**: Inject verification rules (e.g., "Verify quantitative claims with prior observation or say 'Unconfirmed'") into every prompt before generation.[^1_5]
- **Prompt-based Stop hooks**: Use `type: "prompt"` with a model to analyze the transcript and block if needed, but still faces staleness.[^1_2]
- **Constitutional rules + PreToolUse**: Enforce Evidence-First in CLAUDE.md and block unverified searches/tools.[^1_6]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.perplexity.ai/search/cf9270bd-1f28-4b7f-8a90-4858520adbd9

[^1_2]: https://code.claude.com/docs/en/hooks

[^1_3]: tools.llm_and_os

[^1_4]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^1_5]: https://github.com/anthropics/claude-code/issues/4969

[^1_6]: https://www.perplexity.ai/search/49ebc49f-3b58-4eaf-9065-c8c2785fb76e

[^1_7]: https://www.perplexity.ai/search/e9875429-daf2-41de-b2a2-bd4b26ea9543

[^1_8]: https://www.reddit.com/r/Anthropic/comments/1qd1rto/finally_got_observability_working_for_claude_code/

[^1_9]: https://blog.promptlayer.com/understanding-claude-code-hooks-documentation/

[^1_10]: https://www.chatprd.ai/how-i-ai/workflows/automate-code-quality-and-fixes-with-ai-stop-hooks

[^1_11]: https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d

[^1_12]: https://code.claude.com/docs/en/hooks-guide

[^1_13]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^1_14]: https://www.lasso.security/blog/the-hidden-backdoor-in-claude-coding-assistant

[^1_15]: https://www.reddit.com/r/ClaudeAI/comments/1m8bys1/i_wrote_claudelog_a_tool_to_inspect/

[^1_16]: https://www.youtube.com/watch?v=o-pMCoVPN_k

[^1_17]: https://code.claude.com/docs/en/settings

[^1_18]: https://www.linkedin.com/posts/lewisowain_how-to-master-claude-code-hooks-activity-7351573925132206082-8jnp

[^1_19]: https://docs.langchain.com/langsmith/trace-claude-code


---

# ideas or repos that addess UserPromptSubmit hooks: Inject verification rules (e.g., "Verify quantitative claims with prior observation or say 'Unconfirmed'") into every prompt before generation.​

?

**Several repos and ideas leverage UserPromptSubmit hooks in Claude Code to inject verification rules, reducing hallucinations by prepending evidence checks or anti-agreement prompts before generation.**

These approaches parse JSON stdin for the `prompt` field, add custom instructions via stdout (which Claude sees as context), and use exit codes for blocking if needed—ideal for your Windows 11 setup with PowerShell adaptations.[^2_1][^2_2]

## Key Repos

- **disler/claude-code-hooks-mastery**: Comprehensive UserPromptSubmit examples for logging prompts, security validation, and context injection (e.g., project rules). Includes `user_prompt_submit.py` for validation flags like `--validate` to block risky prompts.[^2_2]
- **ruvnet/claude-flow**: Fixes and templates for UserPromptSubmit with `jq` to extract/modify prompts (e.g., git commit messages). Shows stdin parsing for prompt enhancement.[^2_3]
- **ljw1004's Gist (you_are_not_right.sh)**: Injects `<system-reminder>` to enforce "NEVER agree reflexively; verify claims first" by scanning recent transcript for overconfidence patterns.[^2_4]


## Implementation Ideas

Use a Python/PowerShell script in `.claude/settings.json`:

```
"hooks": {
  "UserPromptSubmit": [{
    "command": "python .claude/hooks/verify_inject.py"
  }]
}
```

**Sample verify_inject.py** (adapt from mastery repo):

```python
import sys, json
data = json.load(sys.stdin)
prompt = data.get('prompt', '')

# Inject verification rule
injection = """
<rules>
Verify ALL quantitative claims against prior observations/files/tools.
If unconfirmed: Respond 'Unconfirmed: [claim] lacks prior evidence.'
Cite sources: file:line or observation #[num].
NEVER assume unobserved facts.
</rules>
"""
print(injection)
print(prompt)  # Pass modified prompt
sys.exit(0)
```

This prepends rules to every prompt, building on your Evidence-First work.[^2_5][^2_2]

## Video Tutorial

**SkillBakery's "Rewrite Prompts on the Fly"**: Demonstrates prefixing prompts (e.g., "Make a joke about [user prompt]") with logging—directly adaptable for verification injections.[^2_6]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://code.claude.com/docs/en/hooks

[^2_2]: https://github.com/disler/claude-code-hooks-mastery

[^2_3]: https://github.com/ruvnet/claude-flow/issues/596

[^2_4]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^2_5]: https://www.perplexity.ai/search/e9875429-daf2-41de-b2a2-bd4b26ea9543

[^2_6]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^2_7]: https://code.claude.com/docs/en/hooks-guide

[^2_8]: https://github.com/dagger/container-use/issues/253

[^2_9]: https://claude.com/blog/how-to-configure-hooks

[^2_10]: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations

[^2_11]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^2_12]: https://www.reddit.com/r/ClaudeCode/comments/1qh3w37/claude_code_opus_45_keeps_ignoring_rules_and/

[^2_13]: https://www.reddit.com/r/ClaudeAI/comments/1kedj0p/how_do_you_prevent_claude_code_from_hallucinating/

[^2_14]: https://github.com/langgptai/awesome-claude-prompts

[^2_15]: https://github.com/ruvnet/claude-flow/wiki/hooks

[^2_16]: https://www.reddit.com/r/ClaudeAI/comments/1o0b9fv/ive_been_using_llms_since_2020_heres_how_i_used/


---

# How to write a UserPromptSubmit hook script to inject verification rules

Example repos on GitHub for Claude Code UserPromptSubmit hooks
Tutorial on rewriting prompts with UserPromptSubmit for fact-checking
Script to verify quantitative claims in Claude Code prompts

**UserPromptSubmit hooks in Claude Code intercept prompts via JSON stdin before processing, allowing rule injection via stdout prefixing—perfect for enforcing quantitative claim verification on Windows 11.**

Configure in `.claude/settings.json` under `"hooks": {"UserPromptSubmit": [{"command": "python .claude/hooks/verify_inject.py"}]}`; the script receives `{"prompt": "...", "transcript_path": "...", ...}` and prints injections followed by the original prompt on exit 0.[^3_1][^3_2]

## Writing the Hook Script

Hooks parse stdin JSON, check conditions (e.g., scan transcript for prior observations), inject rules, and control flow:

```python
#!/usr/bin/env python3
import sys, json, re

data = json.load(sys.stdin)
prompt = data['prompt']
transcript_path = data['transcript_path']

# Optional: Scan transcript for prior quantitative claims
with open(transcript_path) as f:
    lines = f.readlines()
recent = ''.join(lines[-10:])  # Last few turns
if re.search(r'\b\d+\b', recent):  # Has numbers? Inject reminder
    injection = """
<rules>
Verify quantitative claims (numbers, counts) against prior observations/files/tools.
If lacking evidence: 'Unconfirmed: [claim] – no prior observation.'
Cite: file:line or obs #[n]. Never fabricate.
</rules>
"""
    print(injection)
print(prompt)
sys.exit(0)  # Or 2 to block
```

This prepends rules Claude must follow; adapt for your regex patterns from empirical_claims_gate.py.[^3_3][^3_1]

## GitHub Repos

| Repo | Description | Key Feature |
| :-- | :-- | :-- |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) [^3_1] | Full UserPromptSubmit templates for logging, validation, context injection. | `--validate` flags; security blocks; stdout examples. |
| [iamrajiv/claude-code-hook-templates](https://github.com/iamrajiv/claude-code-hook-templates) [^3_4] | Lifecycle hook scripts with JSON I/O parsing. | Exit code controls; stdin examples. |
| [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) [^3_5] | Project configs including UserPromptSubmit for workflows. | Agents + hooks integration. |

## Tutorials

- **SkillBakery YouTube: "Rewrite Prompts on the Fly"**: Step-by-step Node.js example prefixing "Tell me a joke about [prompt]" with JSON.parse(stdin), logging original/modified, stdout rewrite for context addition.[^3_6]
- **DataCamp: "Claude Code Hooks Guide"**: Explains UserPromptSubmit for auto-context/prompt validation with input schema.[^3_7]

Test via `echo '{"prompt": "test"}' | python hook.py`; logs to `.claude/logs/` in mastery repo.[^3_1]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/disler/claude-code-hooks-mastery

[^3_2]: https://code.claude.com/docs/en/hooks

[^3_3]: https://www.perplexity.ai/search/e9875429-daf2-41de-b2a2-bd4b26ea9543

[^3_4]: https://github.com/iamrajiv/claude-code-hook-templates

[^3_5]: https://github.com/ChrisWiles/claude-code-showcase

[^3_6]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^3_7]: https://www.datacamp.com/tutorial/claude-code-hooks

[^3_8]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^3_9]: https://debugg.ai/resources/pre-prompt-middleware-claude-code-hooks-enforce-pm-and-coding-standards

[^3_10]: https://github.com/anthropics/claude-code/issues/10225

[^3_11]: https://www.reddit.com/r/ClaudeAI/comments/1o9t35o/built_a_hook_that_makes_claude_code_unvibe_your/

[^3_12]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^3_13]: https://www.producttalk.org/how-to-use-claude-code-features/

[^3_14]: https://gist.github.com/umputun/570c77f8d5f3ab621498e1449d2b98b6

[^3_15]: https://www.reddit.com/r/ClaudeAI/comments/1o2guza/claude_code_prompt_editing/

[^3_16]: https://code.claude.com/docs/ja/hooks


---

# feedback: C.ai's claims about Stop hooks are wrong. Here's what the code actually shows:

C.ai claimed: Stop hooks receive "only metadata like session_id, transcript_path" with "no direct access to the response text itself"
Actual code: Stop_router.py:339 — response_text = str(input_data.get("response") or ""). The Stop hook receives input_data["response"] directly. empirical_claims_gate.py:1455-1508 has extract_response() that pulls it from multiple fields including input_data.get("response", "").
C.ai claimed: The hook "must parse the latest entry from the transcript_path" and this "often contains stale data"
Actual code: empirical_claims_gate.py:1500-1502 — transcript parsing is a fallback, not the primary method. The primary method is the response field in input_data.
C.ai claimed: Stop hooks can't reliably detect confident quantitative claims
Actual code: Your Stop hooks do detect claims and did block me twice this conversation. The gap isn't architectural — it's that detect_claims() (empirical_claims_gate.py:1027) doesn't have patterns matching "Adds latency (seconds)" specifically.
Bottom line: C.ai was wrong about the architecture. Your Stop hooks have full access to response text and reliably block ungrounded claims. The gap is narrow: the claim pattern list doesn't cover all phrasings of confident quantitative assertions. But that's the same brittle-regex problem you already identified. The principle at CLAUDE.md:72 plus the structural enforcement (observation-required before claims) is the right approach — it just won't catch every creative phrasing.

Thanks for the detailed feedback and code references—your analysis of `Stop_router.py:339` and `empirical_claims_gate.py` clarifies the direct `input_data["response"]` access in Stop hooks, overriding prior assumptions about metadata-only inputs.[^4_1]

You're right: The primary extraction via `input_data.get("response", "")` enables reliable claim detection, with transcript as fallback only; recent blocks confirm it works architecturally. The brittleness is indeed in `detect_claims()` patterns (e.g., missing "latency (seconds)"), not access—aligning with your regex refinements and CLAUDE.md principles.[^4_2][^4_3]

## Next Steps

- **Pattern Expansion**: Add regex like `r"latency\s*\(\w+seconds?\)"` or semantic checks to line 1027; test on "Adds latency (seconds)".
- **Hybrid Enhancement**: Combine with UserPromptSubmit injections for proactive rules, per your ongoing work.
- **Version Check**: Verify in v2.1.29+ (your env); if `response` field evolved, document for community (e.g., disler repo).[^4_4]
<span style="display:none">[^4_5]</span>

<div align="center">⁂</div>

[^4_1]: https://www.perplexity.ai/search/42a81d6c-af3c-47b2-90aa-a3d61f598ba5

[^4_2]: https://www.perplexity.ai/search/503eaa00-484c-4b98-aecf-3b9e94a33185

[^4_3]: https://www.perplexity.ai/search/3e4f3477-6ed0-4109-a2da-e698839624d3

[^4_4]: projects.userpromptsubmit_hooks

[^4_5]: https://github.com/disler/claude-code-hooks-mastery


---

# that's not helpful for our problem.

You’re right to push back; my last reply didn’t move the needle on your actual problem.

Given your correction, the core facts for your setup are:

- Your Stop hooks **do** receive `input_data["response"]` (via `response_text = str(input_data.get("response") or "")`), and `empirical_claims_gate.extract_response()` correctly prioritizes that over transcript parsing.[^5_1][^5_2]
- Your empirical gate **already blocks** many quantitative claims and has successfully interrupted this session; the remaining failures are due to **pattern coverage**, not architectural limits in Stop.[^5_2]

So if the problem you’re trying to solve is:

> “Catch *confident quantitative claims without prior observation* more reliably in Stop, given we already have `response`.”

Then the levers you actually have are:

### 1. Broaden claim pattern detection (inside Stop)

Instead of hand-coding narrow regexes like `r"\b\d+(\.\d+)?\s*(ms|seconds)\b"`, you can:

- Add more **structure-aware patterns**:
    - Match “adds/introduces/incurs X [time/latency/overhead]” regardless of unit: `r"\b(adds?|introduces?|incurs?)\s+\d+(\.\d+)?\s*\w*\s*(seconds?|ms|milliseconds?|minutes?)\b"`.
    - Match “increases/decreases memory/CPU by X%”: `r"\b(increases?|decreases?|reduces?)\s+\w+\s+by\s+\d+(\.\d+)?\s*%\b"`.
- Separate “claim classification” from “grounding check”:
    - Phase 1: normalize and extract candidate claims from `response_text` (your `detect_claims()`).
    - Phase 2: for each candidate, run your **observation index** (files read, tools called, prior proven facts) and mark as grounded/un-grounded.

That keeps the brittleness confined to a smaller, testable classifier module instead of scattered regex in the main gate.

### 2. Use a compact LLM sub-checker for “is this a quantitative claim?”

If you’re willing to pay Haiku/GPT-cost inside the Stop path, you can:

- Feed `response_text` to a **local subagent** (via your existing tiered review pattern) with a very constrained prompt:

> “List all sentences that assert a *quantitative fact* (numbers, percentages, counts, timing, memory, throughput, ‘twice as fast’, etc.). Return JSON: `[{\"sentence\":..., \"is_quantitative\": true}]`.”

- Then have your Python hook treat every returned sentence as a “claim candidate” and run your observation-required logic there.

This offloads the “creative phrasings” problem to a model specialized at extraction rather than brittle regex, while keeping the enforcement (block vs allow) in your deterministic layer.[^5_3][^5_4]

### 3. Tighten the “prior observation” test

Right now, your mental model is “Stop should know if it saw evidence before the claim.” To make that less brittle:

- Maintain a **lightweight observation ledger** keyed by:
    - file:line + hash for code/data
    - tool name + parameters for tool outputs
    - maybe a small in-memory cache per session
- When Stop sees a quantitative claim in `response_text`, require a match in this ledger:
    - If none: classify as “confident, ungrounded quantitative claim” → block, emit correction prompt.
    - If match: allow.

That matches what your constitutional rule at `CLAUDE.md:72` wants, but with a more explicit data structure instead of fuzzy transcript guesses.[^5_5]

### 4. Use UserPromptSubmit only as a backstop, not the primary fix

Given that Stop already has `response`, UserPromptSubmit is more of a **booster** than a core solution here:

- Use it to inject: “If you are about to introduce a new number, you must either cite a prior observation in this session or explicitly say ‘Unconfirmed estimate’.”
- Let Stop remain the hard enforcement: “Did you actually do that? If not, block.”

That lets you keep the strong guarantees in Stop (where you already succeeded twice this convo) and use prompt-layer tweaks only to reduce how often Stop needs to intervene.

***

If you tell me which part is currently failing most (e.g., “throughput claims”, “latency in seconds”, “probabilities”, “counts of functions/files”), I can draft a focused `detect_claims_v2()` sketch that slots into `empirical_claims_gate.py` with minimal surgery.
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_18][^5_19][^5_20][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://github.com/anthropics/claude-code/issues/10610

[^5_2]: https://www.perplexity.ai/search/503eaa00-484c-4b98-aecf-3b9e94a33185

[^5_3]: https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/

[^5_4]: https://www.perplexity.ai/search/3e4f3477-6ed0-4109-a2da-e698839624d3

[^5_5]: https://www.perplexity.ai/search/e9875429-daf2-41de-b2a2-bd4b26ea9543

[^5_6]: projects.userpromptsubmit_hooks

[^5_7]: interests.computing.llm_verification

[^5_8]: https://code.claude.com/docs/en/hooks

[^5_9]: https://code.claude.com/docs/en/hooks-guide

[^5_10]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^5_11]: https://platform.claude.com/docs/en/agent-sdk/hooks

[^5_12]: https://www.angusyoung.org/arquivos/camel-new-website/public/components/3.16.x/eips/claimCheck-eip.html

[^5_13]: https://huggingface.co/biodatlab/score-claim-identification

[^5_14]: https://code.claude.com/docs/ja/hooks-guide

[^5_15]: https://routecloud.telogis.com/docs/reference/stop_response.html

[^5_16]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^5_17]: https://routerscan.io

[^5_18]: https://github.com/titipata/detecting-scientific-claim/blob/master/README.md

[^5_19]: https://www.reddit.com/r/ClaudeAI/comments/1odev4r/two_most_useful_hooks_stop_notification/

[^5_20]: https://docs.tokenrouter.io/responses-api/standard-request/


---

# “Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.

Filename requirements:

Include: product (claude-code), main feature (hooks), key hook (userpromptsubmit), platform if relevant (e.g. windows), and any special focus (e.g. async, debug).

Use kebab-case with underscores between major sections, and append today’s date as YYYY-MM-DD.

Return only one filename string.

Topic index requirements:

5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.

Each bullet: SectionTitle – short description.

Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

claude-code_hooks-userpromptsubmit_windows-verification-claims_2026-02-09

- ContextSetup – Overall goal: enforce evidence-first, anti-hallucination behavior in Claude Code via hooks on Windows 11.[^6_1]
- StopHook-Architecture – Reality of Stop input_data (response field, transcript fallback) versus earlier “metadata-only” assumptions.[^6_2][^6_3]
- EmpiricalClaimsGate – Design of empirical_claims_gate.py for detecting and blocking ungrounded quantitative claims.[^6_3]
- PatternDesign – Limitations of brittle regex patterns for claims and need to extend detect_claims() to cover phrasing like “adds latency (seconds)”.[^6_4][^6_3]
- EvidenceFirst-Rules – CLAUDE.md principles for observation-before-claim and how hooks enforce them deterministically.[^6_5][^6_6]
- UserPromptSubmit-Basics – How UserPromptSubmit hooks see prompts, control `continue`/`decision`, and inject additionalContext.[^6_7][^6_1]
- VerificationInjection – Strategies to prepend verification rules into every prompt (quantitative checks, “Unconfirmed” labeling) via UserPromptSubmit.[^6_8][^6_9]
- Repos-And-Examples – Key GitHub and gist examples for UserPromptSubmit and hook templates (disler, iamrajiv, showcase, ljw1004).[^6_10][^6_11]
- PromptRewriting-Tutorial – Video/tutorial patterns for rewriting prompts on the fly with UserPromptSubmit for logging and fact-checking.[^6_9][^6_12]
- HybridGuardrails – Combining prompt-layer rules, Stop empirical gates, and observation ledgers for multi-layer hallucination reduction.[^6_13][^6_14]
<span style="display:none">[^6_15][^6_16][^6_17][^6_18][^6_19][^6_20][^6_21][^6_22]</span>

<div align="center">⁂</div>

[^6_1]: https://code.claude.com/docs/en/hooks

[^6_2]: interests.computing.llm_verification

[^6_3]: https://docs.anthropic.com/en/docs/claude-code/hooks?asuniq=d8f8d9d0

[^6_4]: https://www.perplexity.ai/search/503eaa00-484c-4b98-aecf-3b9e94a33185

[^6_5]: https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/

[^6_6]: https://www.reddit.com/r/ClaudeAI/comments/1qcwckg/the_complete_guide_to_claude_code_v2_claudemd_mcp/

[^6_7]: https://www.perplexity.ai/search/e9875429-daf2-41de-b2a2-bd4b26ea9543

[^6_8]: https://anthropic.mintlify.app/en/docs/claude-code/hooks

[^6_9]: https://code.claude.com/docs/en/hooks-guide

[^6_10]: https://www.datacamp.com/tutorial/claude-code-hooks

[^6_11]: https://github.com/disler/claude-code-hooks-mastery

[^6_12]: https://github.com/iamrajiv/claude-code-hook-templates

[^6_13]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^6_14]: https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d

[^6_15]: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations

[^6_16]: https://github.com/tarekziade/claude-tools

[^6_17]: https://www.reddit.com/r/ClaudeAI/comments/1qfja1y/my_5part_framework_for_building_claude_prompts/

[^6_18]: https://www.reddit.com/r/ThinkingDeeplyAI/comments/1lixa6y/here_is_the_prompt_to_reduce_hallucinations_94_of/

[^6_19]: https://github.com/dagger/container-use/issues/253

[^6_20]: https://github.com/anthropics/claude-code/issues/11947

[^6_21]: https://www.reddit.com/r/ClaudeAI/comments/1m31k7b/new_hook_userpromptsubmit/

[^6_22]: https://www.reddit.com/r/ClaudeAI/comments/1qgccgs/25_claude_code_tips_from_11_months_of_intense_use/

