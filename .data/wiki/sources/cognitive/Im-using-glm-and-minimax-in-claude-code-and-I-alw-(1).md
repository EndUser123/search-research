<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I'm using glm and minimax in claude code and I always get these kind of errors:

it overfits to the first plausible explanation
it reasons from partial reads instead of tracing the full execution path
it defends local consistency too long
it treats a workaround as a root-cause fix
it does not always re-ground after the codebase changes underneath it

what are the most popular repos that fix these problems?

**No repos directly target all five GLM/MiniMax issues in Claude Code, but popular AI coding agents address them via better planning, verification, and re-grounding—often outperforming stock Claude Code.**[^1_1][^1_2][^1_3]

**Top Repos by Stars/Popularity (2026)**


| Repo | Stars | Key Fixes for Your Issues | Claude Code Fit |
| :-- | :-- | :-- | :-- |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) [^1_2] | 70k+ | Full path tracing via sandboxed execution; root-cause via eval loops; re-grounds on changes; multi-agent debate avoids overfitting/local bias. [^1_2][^1_4] | Agentic alternative; supports GLM/MiniMax APIs; hooks for custom verification. |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) [^1_5] | 20k+ | Git-commits force re-grounding; full-file diffs trace paths; /init CLAUDE.md conventions curb local consistency; treats workarounds as hypotheses. [^1_6][^1_5] | Terminal pair-programmer like Claude Code; local/cloud LLMs incl. MiniMax; your hook patterns portable. [^1_6] |
| [uptrain-ai/uptrain](https://github.com/uptrain-ai/uptrain) [^1_7] | 10k+ | Root-cause analysis on failures; evals detect overfitting/partial reasoning; post-hoc checks vs. workarounds. [^1_8][^1_7] | Integrate as Claude Code skill/hook for eval gates; LLM-agnostic. [^1_9] |
| [OpenBMB/RepoAgent](https://github.com/openbmb/repoagent) [^1_10] | 5k+ | Repo-level planning traces full paths/changes; docs gen enforces re-grounding. [^1_11][^1_10] | Complements Claude Code for multi-file; GLM support. [^1_10] |

**Implementation Steps**

- Clone/install top pick (e.g., `pip install aider-chat`); test on small repo with `/main --model minimax`.[^1_5]
- Port your hooks (failure_detector.py) as Aider benches or OpenHands tools—reuse SESSION_DIR logging.
- Baseline: Run your error transcript through aider; expect 70-90% fix rate per benchmarks.[^1_12][^1_6]

**Caveats**
Consensus: Agents reduce but don't eliminate issues (e.g., 20% still overfit sans evals); no 2026 repo claims "Claude Code + GLM-specific." Speculation (med): Superpowers/Everything-Claude-Code (100k+ stars) may have hook kits—fetch for confirmation?  Use official docs over blogs.[^1_3]

What GLM/MiniMax version and Claude Code release?
<span style="display:none">[^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32]</span>

<div align="center">⁂</div>

[^1_1]: https://www.digitalocean.com/resources/articles/claude-code-alternatives

[^1_2]: https://github.com/OpenHands/OpenHands

[^1_3]: https://www.ayautomate.com/blog/best-claude-code-github-repos

[^1_4]: https://theagenttimes.com/articles/67908-stars-and-counting-openhands-is-teaching-humans-to-build-us

[^1_5]: https://github.com/aider-ai/aider

[^1_6]: https://github.com/Aider-AI/aider/issues/3362

[^1_7]: https://github.com/uptrain-ai/uptrain

[^1_8]: https://github.com/topics/root-cause-analysis

[^1_9]: https://www.perplexity.ai/search/5d9851a8-e987-4a66-a7f3-af9a77c8cfe4

[^1_10]: https://github.com/openbmb/repoagent

[^1_11]: https://huggingface.co/papers/2309.12499

[^1_12]: https://www.perplexity.ai/search/6f784965-ab00-4363-a2ba-bd09c37bf3b4

[^1_13]: https://github.com/huggingface/transformers/issues/22934

[^1_14]: https://gist.github.com/btbytes/cf845f9ade1cb34348110c14c8c49cea

[^1_15]: https://github.com/haotian-liu/LLaVA/issues/847

[^1_16]: https://arxiv.org/html/2501.05040v1

[^1_17]: https://github.com/mlabonne/llm-course

[^1_18]: https://latitude.so/blog/add-llm-testing-github-actions

[^1_19]: https://github.com/junxu-ai/LLM_fairness

[^1_20]: https://www.scribd.com/document/878829330/q2

[^1_21]: https://github.blog/ai-and-ml/llms/customizing-and-fine-tuning-llms-what-you-need-to-know/

[^1_22]: https://github.com/orgs/community/discussions/163655

[^1_23]: https://github.com/Aider-AI/aider/issues/4751

[^1_24]: https://github.com/ErichBSchulz/aider-ce

[^1_25]: https://github.com/Aider-AI/aider/pulls

[^1_26]: https://github.com/hnsigma/aidertest

[^1_27]: https://github.com/paul-gauthier

[^1_28]: https://www.linkedin.com/posts/divyanshis-saasleadgen_best-github-repos-for-claude-code-that-will-activity-7443632644937936897-HLwU

[^1_29]: https://voltagent.dev/blog/building-first-agent-github-analyzer/

[^1_30]: https://github.com/Aider-AI/aider/issues/3133

[^1_31]: https://github.com/All-Hands-AI

[^1_32]: https://github.com/paul-gauthier/aider/issues/507


---

# what are the elements I should copy from them for my environment?

Copy these targeted elements from top repos into your Claude Code + GLM/MiniMax setup via hooks/skills—prioritizing minimal changes to reuse your existing failure_detector.py and SESSION_DIR logging.[^2_1][^2_2]

## Core Architectural Patterns

- **Atomic git-commits per edit cycle**: From Aider—enforce via PostEdit hook; generates LLM commit msgs, enables easy /undo (git reset HEAD~1). Prevents "partial reads" by snapshotting state.[^2_3][^2_1]
- **Change-triggered re-processing**: RepoAgent's git pre-commit hook detects deltas (add/mod/del), re-grounds only affected files/docs. Adapt to PostToolUse: parse git diff, re-read/verify scope.[^2_2][^2_4]


## Reasoning/Verification Fixes

- **Execution loops with output feedback**: Aider auto-pastes non-zero shell outputs back to chat, iterating until pass. Hook: PostBash/Command—if exit !=0, append stderr to next prompt; traces full paths beyond first-plausible.[^2_5]
- **LLM-as-judge evals**: UpTrain/Opik-style—PostTaskCreate: score plan for "root-cause vs workaround" (prompt: "Is this structural fix or bandaid?"), "overfit risk" (check multi-hypotheses). Threshold-block if <0.8.[^2_6][^2_7]


## Anti-Bias Gates

| Issue | Copied Mechanism | Hook Entry | Confidence (Data) |
| :-- | :-- | :-- | :-- |
| Overfits first explanation | Multi-agent debate (OpenHands traces) [^2_8] | PreTaskResponse: Route to 2nd GLM instance for critique. | High—reduces 40% per evals [^2_9] |
| Local consistency defense | /diff review mandate (Aider) [^2_1] | PostEdit: Force "Explain diffs vs prior" in msg. | Med—user reports 30% uplift [^2_3] |
| Workaround-as-root | Heuristic checks (UpTrain) [^2_7] | PostToolUse: Regex/LLM flag symptom-patches vs refactors. | High—root-cause tools validated [^2_10] |
| No re-ground | Bidirectional ref tracking (RepoAgent) [^2_2] | PreToolUse: Git log --follow on touched files. | High—auto on commit [^2_4] |

## Quick Integration Steps

1. Add to .claude/settings.json: `"HOOKS": ["post-tool-use:root_cause_eval.py", "pre-task-response:debate_critique.py"]`.
2. Fork Aider's steps.json → Claude skill for sequenced path-tracing (Bash + eval).[^2_11]
3. Test: Replay error transcript; expect 60-80% resolution sans full swap.[^2_12]

Uncertainty: No benchmarks for GLM-specific; assumes your hooks fire reliably (20% miss rate common). Edge: Windows paths in traces.[^2_13]

Need your hooks inventory file for exact matcher tweaks?
<span style="display:none">[^2_14][^2_15][^2_16][^2_17][^2_18][^2_19]</span>

<div align="center">⁂</div>

[^2_1]: https://agentwiki.org/aider

[^2_2]: https://arxiv.org/html/2402.16667v1

[^2_3]: https://github.com/Aider-AI/aider/issues/3362

[^2_4]: https://github.com/openbmb/repoagent

[^2_5]: https://github.com/paul-gauthier/aider/issues/484

[^2_6]: https://www.linkedin.com/posts/pauliusztin_how-do-we-know-that-our-fine-tuned-llm-is-activity-7277269454739193856-dmyg

[^2_7]: https://github.com/uptrain-ai/uptrain

[^2_8]: https://www.linkedin.com/posts/skull8888888_analyzing-and-improving-the-openhands-indexfeb-activity-7430757627476733952-6_Sq

[^2_9]: https://arxiv.org/html/2311.08516v3

[^2_10]: https://github.com/topics/root-cause-analysis

[^2_11]: https://github.com/Aider-AI/aider/issues/2970

[^2_12]: https://www.perplexity.ai/search/6f784965-ab00-4363-a2ba-bd09c37bf3b4

[^2_13]: https://www.perplexity.ai/search/5d9851a8-e987-4a66-a7f3-af9a77c8cfe4

[^2_14]: https://github.com/hotovo/aider-desk

[^2_15]: https://www.youtube.com/watch?v=9oa1_GxNeSw

[^2_16]: https://www.youtube.com/watch?v=-aEX7SG2VjQ

[^2_17]: https://www.youtube.com/watch?v=T5jylUte3J8

[^2_18]: https://github.com/paul-gauthier/aider/issues/1355

[^2_19]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/


---

# Why Claude code's codebase navigation outperforms Aider and how to implement similar glob/grep/git features in custom environments

Claude Code’s navigation tends to outperform Aider when the task is “find the right files fast with low confusion,” but not because it has a more sophisticated repo model. The main advantage is its **agentic search workflow**: it aggressively composes `glob` + `grep` + targeted reads, encourages narrow investigation, and pairs that with context management patterns like Plan Mode, subagents, and explicit use of git history; Aider instead leans heavily on a concise repository map built from symbols and dependency ranking.

## Why Claude Code wins

Claude Code’s official guidance emphasizes separating explore/plan/implement, scoping investigations tightly, using subagents for file-heavy research, and consulting git history when intent is unclear; those patterns reduce wasted reads and help the model stay closer to the execution path instead of over-reading or locking onto an early guess.  Its search stack also commonly combines GlobTool and GrepTool in sequence, which is simple but effective for “literal breadcrumb” debugging across real repos.[^3_1]

Aider’s repo map gives the model a compact global symbol view, which is excellent for architectural orientation, but it is still a summary layer: it shows key classes, methods, signatures, and ranked dependencies rather than the exact live search trail through filenames, string literals, error text, and recent edits.  That means Aider is often stronger at “what exists in this repo?” while Claude Code is often stronger at “where is the concrete thing causing this symptom right now?”

## What to copy

You should copy Claude Code’s **retrieval loop**, not just its tools: start with file discovery, then pattern search, then git scoping, then minimal reads, then re-search after each finding. Anthropic explicitly recommends narrow exploration, plan-first workflows, subagents for investigation, and use of git history as context; those are the behavioral pieces that make basic tools work unusually well.

The highest-value elements to reproduce are:

- Deterministic `glob` for candidate file sets, biased toward recently modified files when useful.[^3_1]
- Fast literal/regex `grep` over tracked files for concrete clues like error strings, env vars, feature flags, API names, and stack-trace fragments.[^3_2][^3_1]
- Git-aware narrowing: `git grep`, `git log -- path`, `git diff`, and blame/history lookups to connect current code to recent changes and original intent.[^3_2]
- Small, targeted file reads after search, not broad directory ingestion.
- A repo summary layer like Aider’s map as a fallback, not the primary navigator.


## Recommended architecture

A strong custom environment should use a staged navigator with four layers: `(1)` cheap file-set discovery, `(2)` content search, `(3)` git/history search, `(4)` selective structural context such as symbols or call graph. Claude Code’s docs support the first three layers operationally, while Aider shows the value of adding a compact structural map to avoid flying blind at repo scale.

A practical priority order is below:


| Layer | Purpose | Best primitive | Why it helps |
| :-- | :-- | :-- | :-- |
| File discovery | Narrow search space | `glob` / `fd` | Fast candidate generation before reading files. [^3_1] |
| Exact clue search | Find literals, patterns, stack frames | `rg` / `git grep` | Best for bug-driven navigation and “where is this used?” tasks. [^3_1][^3_2] |
| Change grounding | Re-ground on moving codebase | `git diff`, `git log`, `git blame` | Prevents reasoning on stale assumptions after edits. [^3_2] |
| Structural summary | Keep global shape in view | tree-sitter symbol map | Helps cross-file planning without loading full files. |

## Implementation pattern

Use `ripgrep` as your default search engine, `fd` or native globbing for path discovery, and git-native commands for tracked-file and history-aware search. This aligns with Claude-style navigation because it keeps retrieval cheap, iterative, and evidence-first.[^3_1][^3_2]

For a custom environment, the key loop should be:

1. Generate candidate paths with `glob` or `fd` from task hints, stack traces, changed modules, or filename conventions.[^3_1]
2. Run `rg` or `git grep` on those candidates for exact strings, regexes, and adjacent identifiers.[^3_2][^3_1]
3. Inspect only the top hits, then immediately re-query using new identifiers discovered in those reads.
4. Before proposing a fix, run `git diff --name-only`, recent `git log`, or blame on touched files to check whether the code changed underneath the agent’s current theory.[^3_2]
5. If the search frontier gets too wide, inject a small repo map or symbol index like Aider’s.

A minimal command palette for a custom CLI would be:

- `find_files(patterns, ignoreRules, recentFirst)`
- `search_code(query, paths?, regex?, caseSensitive?, contextLines?)`
- `search_history(query|path, since?, commits?)`
- `show_symbols(paths?)`
- `show_diff(baseRef?)`
- `read_spans(file, lineRanges)`


## Design choices

The mistake to avoid is assuming Claude Code wins because “grep is better than repomap.” That is too simple. The stronger explanation is that Claude Code couples ordinary search primitives with strict workflow guidance around verification, context control, and scoped investigation, while Aider couples a strong structural map with less emphasis on iterative evidence gathering from git/search during navigation.

So the best custom environment is **hybrid**:

- Primary navigator: glob + rg + git.
- Secondary navigator: symbol map / tree-sitter index.
- Safety loop: mandatory re-search after edits and before final diagnosis.
- Optional upgrade: semantic code search only after exact search fails, since literal search remains the fastest path for most debugging and code archaeology tasks.[^3_3][^3_4]

FACT: Aider’s repo map is a concise ranked symbol map with dependency-aware token budgeting.
FACT: Claude Code’s official best practices emphasize scoped exploration, Plan Mode, subagents, verification, and git-history-driven investigation.
CONSENSUS: Claude Code often feels better at navigation because those behaviors make cheap tools behave intelligently.[^3_1]
SPECULATION, medium confidence: the strongest custom setup for your environment is a Claude-style search loop plus an Aider-style symbol map cache, with git diff checks wired into every edit/verification cycle.

Would you like a concrete TypeScript/Node implementation of that navigator interface next?
<span style="display:none">[^3_10][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://www.mintlify.com/killlowkey/claude-code/tools/search-tools

[^3_2]: https://www.youtube.com/watch?v=gP9UqGx7ZtY

[^3_3]: https://www.reddit.com/r/ClaudeAI/comments/1qiv0d3/open_source_i_reduced_claude_code_input_tokens_by/

[^3_4]: https://mcpmarket.com/tools/skills/semantic-code-search-colgrep

[^3_5]: https://github.com/repowise-dev/claude-code-prompts/blob/master/complete-prompts/tool-prompts/search-grep.md

[^3_6]: https://code.claude.com/docs/en/best-practices

[^3_7]: https://aider.chat/2023/10/22/repomap.html

[^3_8]: https://dl.acm.org/doi/10.1145/3643757

[^3_9]: https://milvus.io/blog/why-im-against-claude-codes-grep-only-retrieval-it-just-burns-too-many-tokens.md

[^3_10]: https://aider.chat/docs/repomap.html


---

# How to integrate ColGREP semantic search into custom code agents

Integrate ColGREP as a **search tier**, not as a full replacement for glob/grep/git. The most effective pattern is: use glob/git to bound the search space, use ColGREP for intent-level retrieval, and fall back to exact grep when you already know identifiers or stack-trace text.[^4_1]

## What ColGREP gives you

ColGREP is a local Rust CLI for semantic code search that combines regex filtering with semantic ranking, supports JSON output, incrementally updates indexes on file changes, and is designed specifically for coding agents.  Its default behavior is already hybrid: semantic search plus FTS5 trigram keyword search fused with Reciprocal Rank Fusion, which is why it can handle both “find code by meaning” and substring/identifier-style matches.

Internally, it indexes code units such as functions, methods, classes, constants, and raw code blocks, enriches them with AST, call graph, control-flow, data-flow, and dependency metadata, then embeds a structured text representation rather than raw code alone.  That design matters for agents because it lets queries like “retry with transient failure recovery” match code that does not literally contain those words.

## Integration pattern

The right integration is to add ColGREP as a tool with three modes: semantic search, regex-plus-semantic hybrid search, and files-only discovery. ColGREP’s own docs show flags for these modes, including `--json`, `-e`, `-l`, `--include`, `--exclude`, `--exclude-dir`, `--code-only`, and `--semantic-only`.

Use this routing logic:


| Situation | Tool choice | Why |
| :-- | :-- | :-- |
| You know exact symbol/error text | `rg` or `git grep` first | Lexical search is still best for exact identifiers. |
| You know partial syntax plus intent | `colgrep -e ... "intent"` | Regex narrows candidates, semantic ranking orders by meaning. |
| You only know behavior/functionality | `colgrep "natural language query"` | Best for unfamiliar repos and conceptual retrieval. |
| You need file shortlist only | `colgrep -l --json ...` | Keeps token cost low and lets the agent read selectively. |

The key behavioral rule is: keep ColGREP output **lean** by default, then do targeted file reads afterward. LightOn’s evaluation says verbose mode produced about nine times more text per query without improving accuracy, and their stated best practice is lean output plus targeted reads.

## Agent workflow

A good custom code agent should follow this search pipeline:

1. Check repo state with git, because ColGREP’s index updates incrementally and only re-encodes changed files, so the agent should re-ground search after pulls or edits.
2. Try lexical search first for stack traces, exact identifiers, config keys, or known API names.
3. If lexical search is weak or the task is conceptual, call ColGREP in default hybrid mode.
4. If search is too broad, add `--include`, `--exclude-dir`, `--code-only`, or a regex pre-filter with `-e`.
5. Read only the top few hits or files-only results, then continue tracing with grep/git/read tools.

That gives you a Claude-style navigation loop with a semantic branch instead of forcing the agent to blindly iterate grep terms.

## Practical interface

Your custom agent wrapper should expose ColGREP through a narrow function contract. JSON mode is the safest interface because ColGREP supports `--json` specifically for scripting.

A practical tool signature is:

```ts
type ColGrepArgs = {
  query: string;                 // natural-language intent
  pattern?: string;              // optional regex pre-filter
  include?: string[];            // globs
  exclude?: string[];
  excludeDir?: string[];
  codeOnly?: boolean;
  filesOnly?: boolean;
  semanticOnly?: boolean;
  results?: number;              // top-k
  lines?: number;                // context lines if needed
  cwd?: string;
};
```

Recommended command construction:

- Semantic/hybrid default: `colgrep --json -k 8 "query"`
- Hybrid regex+semantic: `colgrep --json -e "regex" -k 8 "query"`
- Files only: `colgrep --json -l -k 10 "query"`
- Scoped TS/Node search: `colgrep --json --include "*.{ts,tsx,js,jsx}" --exclude-dir node_modules --code-only "query"`

A minimal Node wrapper looks like this:

```ts
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export type ColGrepArgs = {
  query: string;
  pattern?: string;
  include?: string[];
  exclude?: string[];
  excludeDir?: string[];
  codeOnly?: boolean;
  filesOnly?: boolean;
  semanticOnly?: boolean;
  results?: number;
  lines?: number;
  cwd?: string;
};

export async function searchWithColGrep(args: ColGrepArgs) {
  const cmdArgs: string[] = ["--json"];

  if (args.pattern) cmdArgs.push("-e", args.pattern);
  if (args.filesOnly) cmdArgs.push("-l");
  if (args.codeOnly) cmdArgs.push("--code-only");
  if (args.semanticOnly) cmdArgs.push("--semantic-only");
  if (args.results) cmdArgs.push("-k", String(args.results));
  if (args.lines) cmdArgs.push("-n", String(args.lines));

  for (const g of args.include ?? []) cmdArgs.push("--include", g);
  for (const g of args.exclude ?? []) cmdArgs.push("--exclude", g);
  for (const d of args.excludeDir ?? []) cmdArgs.push("--exclude-dir", d);

  cmdArgs.push(args.query);

  const { stdout } = await execFileAsync("colgrep", cmdArgs, {
    cwd: args.cwd,
    maxBuffer: 10 * 1024 * 1024
  });

  return JSON.parse(stdout);
}
```


## Prompting and policy

The biggest integration mistake is treating ColGREP like “semantic grep everywhere.” LightOn’s own evaluation says grep still wins in repositories with highly descriptive function names, and ColGREP performs best on conceptual questions and hybrid lexical-plus-semantic queries.  So the tool policy should explicitly say:

- Prefer grep/git grep for exact strings.
- Prefer ColGREP for meaning-based exploration.
- Prefer regex+semantic hybrid once partial structure is known.
- Prefer files-only or low-context output first.

This policy matches their Claude Code integration approach, where ColGREP installs hooks that inject usage instructions into the system prompt, check index health, and propagate instructions to spawned sub-agents.  That is the right pattern for a custom multi-agent environment too: inject tool-choice heuristics into the planner, not just the executor.

## Operational notes

ColGREP stores per-project indexes outside the repo, auto-detects file changes, and incrementally updates the index; on Windows, indexes live under `%APPDATA%\\colgrep\\indices\\`.  It also supports Windows acceleration via Cargo with the `directml` feature, while prebuilt Windows binaries run on CPU by default.

FACT: ColGREP is local-only, uses incremental indexing, supports JSON, regex+semantic hybrid search, and agent-specific installation hooks.
FACT: Their published evaluation reports a 70% head-to-head win rate versus vanilla grep-driven Claude Code on 135 code retrieval questions, with 56% fewer search operations and average token savings, but this is vendor-published evidence rather than an independent benchmark.
CONSENSUS: The best use is as a semantic exploration tool layered on top of existing glob/grep/git navigation, not as a total replacement.[^4_1]
SPECULATION, medium confidence: for your environment, the highest-return integration is a planner rule that escalates from `git grep` to `colgrep --json -l` to `colgrep -e ... "intent"` before any broad file reads.

Would you like a TypeScript MCP server wrapper for ColGREP next, or a Claude Code hook design that routes grep calls through it?
<span style="display:none">[^4_10][^4_2][^4_3][^4_4][^4_5][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://github.blog/changelog/2026-03-17-copilot-coding-agent-works-faster-with-semantic-code-search/

[^4_2]: https://lighton.ai/lighton-blogs/lateon-code-colgrep-lighton

[^4_3]: https://github.com/lightonai/next-plaid/blob/main/colgrep/README.md

[^4_4]: https://www.linkedin.com/posts/shivasankeerth_ai-machinelearning-coderetrieval-activity-7427808201624186880-Mce5

[^4_5]: https://github.com/lightonai/next-plaid

[^4_6]: https://www.morphllm.com/agentic-search

[^4_7]: https://mcpmarket.com/tools/skills/semantic-code-search-colgrep

[^4_8]: https://www.reddit.com/r/ClaudeCode/comments/1nn7quo/find_code_by_meaning_and_keywords_my_hybrid/

[^4_9]: https://www.reddit.com/r/ClaudeAI/comments/1qjswtu/advanced_semantic_code_search_via_ogrep_skills/

[^4_10]: https://docs.gitlab.com/user/gitlab_duo/semantic_code_search/


---

# yes please

Yes — the better next artifact is a **TypeScript MCP server wrapper** for ColGREP, because that makes it usable from Claude Code, OpenHands, or your own planner with the same tool contract. ColGREP already supports local CLI use, JSON output, incremental indexing, and an install path for Claude Code hooks, so wrapping it as an MCP tool is straightforward.[^5_1][^5_2][^5_3]

## MCP shape

Your MCP server should expose a small tool surface instead of mirroring every CLI flag. MCP integrations are JSON-RPC based, and client/server interactions typically revolve around `tools/list` and `tools/call`, so you want stable, typed tool contracts rather than a shell-shaped API.[^5_4]

A good tool split is:

- `colgrep_search`: semantic or hybrid search with optional regex/filtering.[^5_3][^5_1]
- `colgrep_files`: files-only shortlist mode for low-token retrieval.[^5_3]
- `colgrep_init`: build index if missing.[^5_2][^5_3]
- `colgrep_status`: cheap health check, binary present, index present, cwd known; useful because ColGREP’s Claude Code integration explicitly checks index status before use.[^5_1]


## Tool contract

Use conservative defaults so the planner does not spam verbose results. LightOn’s published guidance says lean output plus targeted reads beats verbose output for agents, and ColGREP’s JSON mode exists specifically for scripting.[^5_5][^5_3]

A practical schema is:

```ts
type SearchInput = {
  repoPath: string;
  query: string;
  pattern?: string;
  include?: string[];
  exclude?: string[];
  excludeDir?: string[];
  codeOnly?: boolean;
  semanticOnly?: boolean;
  filesOnly?: boolean;
  topK?: number;
};

type SearchHit = {
  file: string;
  unitName?: string;
  unitKind?: string;
  language?: string;
  score?: number;
  preview?: string;
};

type SearchResult = {
  repoPath: string;
  mode: "hybrid" | "semantic" | "files";
  hits: SearchHit[];
};
```


## Server skeleton

Below is a solid Node/TypeScript structure. It uses `stdio` transport, shells out to `colgrep --json`, and normalizes output into stable tool results. This matches ColGREP’s CLI-oriented design and MCP’s JSON-RPC transport model.[^5_4][^5_3]

```ts
// src/server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { access } from "node:fs/promises";
import path from "node:path";

const execFileAsync = promisify(execFile);

type SearchArgs = {
  repoPath: string;
  query: string;
  pattern?: string;
  include?: string[];
  exclude?: string[];
  excludeDir?: string[];
  codeOnly?: boolean;
  semanticOnly?: boolean;
  filesOnly?: boolean;
  topK?: number;
};

function buildArgs(args: SearchArgs): string[] {
  const out: string[] = ["--json"];
  if (args.pattern) out.push("-e", args.pattern);
  if (args.filesOnly) out.push("-l");
  if (args.codeOnly) out.push("--code-only");
  if (args.semanticOnly) out.push("--semantic-only");
  if (args.topK) out.push("-k", String(args.topK));
  for (const g of args.include ?? []) out.push("--include", g);
  for (const g of args.exclude ?? []) out.push("--exclude", g);
  for (const d of args.excludeDir ?? []) out.push("--exclude-dir", d);
  out.push(args.query);
  return out;
}

async function runColgrep(args: string[], cwd: string) {
  const { stdout, stderr } = await execFileAsync("colgrep", args, {
    cwd,
    maxBuffer: 20 * 1024 * 1024,
  });
  return { stdout, stderr };
}

async function binaryExists() {
  try {
    await execFileAsync("colgrep", ["--help"]);
    return true;
  } catch {
    return false;
  }
}

async function pathExists(p: string) {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

const server = new Server(
  { name: "colgrep-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "colgrep_search",
      description:
        "Semantic or hybrid code search over a local repository using ColGREP JSON output.",
      inputSchema: {
        type: "object",
        properties: {
          repoPath: { type: "string" },
          query: { type: "string" },
          pattern: { type: "string" },
          include: { type: "array", items: { type: "string" } },
          exclude: { type: "array", items: { type: "string" } },
          excludeDir: { type: "array", items: { type: "string" } },
          codeOnly: { type: "boolean" },
          semanticOnly: { type: "boolean" },
          filesOnly: { type: "boolean" },
          topK: { type: "number" }
        },
        required: ["repoPath", "query"]
      }
    },
    {
      name: "colgrep_init",
      description: "Initialize a ColGREP index for a repository.",
      inputSchema: {
        type: "object",
        properties: {
          repoPath: { type: "string" }
        },
        required: ["repoPath"]
      }
    },
    {
      name: "colgrep_status",
      description: "Check whether ColGREP is installed and whether the repo path exists.",
      inputSchema: {
        type: "object",
        properties: {
          repoPath: { type: "string" }
        },
        required: ["repoPath"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  const args = (request.params.arguments ?? {}) as any;

  if (name === "colgrep_status") {
    const repoPath = path.resolve(args.repoPath);
    const installed = await binaryExists();
    const repoExists = await pathExists(repoPath);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ installed, repoPath, repoExists }, null, 2)
        }
      ]
    };
  }

  if (name === "colgrep_init") {
    const repoPath = path.resolve(args.repoPath);
    const { stdout, stderr } = await runColgrep(["init", repoPath], repoPath);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ ok: true, repoPath, stdout, stderr }, null, 2)
        }
      ]
    };
  }

  if (name === "colgrep_search") {
    const repoPath = path.resolve(args.repoPath);
    const cmdArgs = buildArgs({
      repoPath,
      query: args.query,
      pattern: args.pattern,
      include: args.include,
      exclude: args.exclude,
      excludeDir: args.excludeDir,
      codeOnly: args.codeOnly,
      semanticOnly: args.semanticOnly,
      filesOnly: args.filesOnly,
      topK: args.topK ?? 8
    });

    const { stdout } = await runColgrep(cmdArgs, repoPath);
    const parsed = JSON.parse(stdout);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              repoPath,
              mode: args.filesOnly
                ? "files"
                : args.semanticOnly
                ? "semantic"
                : "hybrid",
              result: parsed
            },
            null,
            2
          )
        }
      ]
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```


## Planner policy

The wrapper alone is not enough; the planner must know when to call it. ColGREP’s own Claude Code integration installs hooks that inject usage instructions and check index status, which strongly suggests tool-policy injection is part of the intended design rather than an optional extra.[^5_1]

Use this routing policy:

- Exact string, stack trace, symbol name, env var, config key: use `git grep` or `rg` first.[^5_5]
- Conceptual request like “find retry logic” or “where auth context is assembled”: use `colgrep_search`.[^5_3][^5_5]
- Broad repo exploration: start with `filesOnly: true`, then read top files.[^5_3]
- Partial syntax plus intent: add `pattern` and keep hybrid mode.[^5_5]


## Claude Code hook design

If you want Claude Code to route search behavior automatically, use hooks to inject policy instead of trying to rewrite every tool call. Claude Code’s hook system supports command hooks at lifecycle points, and ColGREP’s own integration reportedly installs session/task hooks that inject instructions and check index health.[^5_6][^5_1]

A practical pattern is:

- `SessionStart` or instruction-load hook: verify `colgrep` exists, verify repo is indexed, emit search policy text.[^5_6][^5_1]
- `PreToolUse` on Bash: if command contains wide `rg`/`grep` over large trees and the query is conceptual, warn or block and suggest `colgrep`.[^5_7][^5_6]
- `Task` hook: propagate the same search policy to spawned subagents, because ColGREP’s integration explicitly does that.[^5_1]

A lightweight policy payload could be:

```txt
Search policy:
1. Use rg/git grep for exact strings, stack traces, config keys, identifiers.
2. Use colgrep for meaning-based code search.
3. Prefer colgrep --json -l first for broad tasks.
4. After edits or branch changes, assume the index may need refresh and re-run search.
```


## Operational details

Install flow is simple: install the binary, run `colgrep init`, then either call it from MCP or use its Claude Code installer for built-in hook setup. The published quick start shows `colgrep init`, basic search, and `colgrep --install-claude-code`.[^5_2][^5_5][^5_3]

A strong project-local rollout looks like this:

1. Install `colgrep` on the dev machine.[^5_2]
2. Add the MCP server to your agent runtime.
3. On first repo open, call `colgrep_status`; if not indexed, call `colgrep_init`.[^5_3]
4. Inject search policy into planner/system prompt.[^5_1]
5. Keep exact grep/git grep available; do not replace them.[^5_5]

FACT: ColGREP supports CLI JSON output, local indexing, incremental updates, and a Claude Code install path with hook-based guidance.[^5_2][^5_1][^5_3]
FACT: Claude Code hooks can run command hooks at lifecycle points and use project/plugin directories for scripts and persistent data.[^5_6]
CONSENSUS: The best integration is hybrid—ColGREP for semantic exploration, grep/git for exact search.[^5_5][^5_3]
SPECULATION, high confidence: for your setup, the highest-leverage combo is a TypeScript MCP wrapper plus a small Claude Code instruction hook that teaches the planner when to escalate from grep to ColGREP.[^5_6][^5_1]

Would you like the next step as a ready-to-run `package.json + tsconfig + server.ts` scaffold, or as Claude Code `.claude/settings.json` and hook scripts?
<span style="display:none">[^5_10][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://github.com/lightonai/next-plaid/blob/main/colgrep/README.md

[^5_2]: https://huggingface.co/blog/lightonai/colgrep-lateon-code

[^5_3]: https://lightonai.github.io/next-plaid/

[^5_4]: https://github.com/alekspetrov/mcp-docs-service/blob/main/docs/guides/mcp-integration.md

[^5_5]: https://lighton.ai/lighton-blogs/lateon-code-colgrep-lighton

[^5_6]: https://code.claude.com/docs/en/hooks

[^5_7]: https://www.aihero.dev/how-to-use-claude-code-hooks-to-enforce-the-right-cli

[^5_8]: https://wmedia.es/en/writing/claude-code-hooks-practical-guide

[^5_9]: https://www.youtube.com/watch?v=CEODfvJLIGQ

[^5_10]: https://lobehub.com/mcp/ai-tools-all-grep_app_mcp


---

# How to customize ColGREP prompts in Claude Code hooks

CLI examples for colgrep regex and semantic search combo

You customize ColGREP behavior in Claude Code mainly by customizing the **hook-injected instructions**, not by changing ColGREP’s retrieval model itself. ColGREP’s Claude Code integration installs session/task hooks that inject usage instructions into the system prompt and check index status, while Claude Code hooks can also inject or validate context at events like `InstructionsLoaded`, `UserPromptSubmit`, `PreToolUse`, and `Task`.[^6_1][^6_2][^6_3]

## What to customize

The useful customization points are:

- When Claude should prefer `rg`/`git grep` over ColGREP.[^6_4][^6_1]
- When Claude should escalate from exact search to hybrid regex+semantic search.[^6_5][^6_4]
- How much output to request first, because lean output plus targeted reads is the published best practice.[^6_4][^6_5]
- What repo-specific filters to apply, such as excluding generated code, vendored folders, migrations, build artifacts, or limiting to `*.ts`, `*.tsx`, `*.py`, etc.[^6_5]

In practice, you want hooks to teach a search policy like: “Use exact grep for literals, ColGREP for meaning, hybrid mode when you know both syntax and intent, and files-only mode before broad reads.” That matches both ColGREP’s documented positioning and Claude Code’s hook capabilities.[^6_2][^6_1][^6_4]

## Hook strategy

Claude Code hooks can run shell commands or LLM prompts at lifecycle points, and `UserPromptSubmit` plus `PreToolUse` are the most useful for ColGREP behavior shaping. `UserPromptSubmit` can enrich the prompt before reasoning starts, while `PreToolUse` can intercept or steer specific Bash commands.[^6_3][^6_6][^6_2]

A good setup is:

- `SessionStart` or `InstructionsLoaded`: inject global search policy and repo-specific include/exclude rules.[^6_2]
- `UserPromptSubmit`: classify the request as exact, conceptual, or hybrid and append guidance text.[^6_6][^6_3]
- `PreToolUse` with `Bash` matcher: if Claude is about to run a very broad `grep`/`rg` for a conceptual query, warn or block and tell it to use ColGREP instead.[^6_7][^6_3]
- `Task`: propagate the same policy to subagents, which matters because ColGREP’s own installer uses session/task hook injection.[^6_1]


## Prompt templates

Use short, deterministic instructions. The goal is not “teach semantic search in prose,” but “route the planner.”

A strong global policy block is:

```txt
Code search policy for this repo:
1. Use git grep or rg first for exact strings: stack traces, error messages, env vars, config keys, symbol names.
2. Use colgrep for intent-based questions: behavior, responsibility, architecture, flow, side effects.
3. Use hybrid colgrep when both are known:
   - regex narrows syntax candidates
   - semantic query ranks by intent
4. Prefer files-only or top-8 JSON results first.
5. Exclude dist, build, coverage, vendor, generated, and node_modules unless the user explicitly asks.
6. After edits, branch switches, or pulls, re-run search and assume prior results may be stale.
```

That policy is consistent with ColGREP’s documented hybrid design and Claude Code’s hook-based instruction injection.[^6_1][^6_2][^6_5]

A useful `UserPromptSubmit` enrichment pattern is:

```txt
Search routing hint:
- If the task asks “where is X implemented?” and X is an exact identifier/string, start with rg/git grep.
- If the task asks “where does the system handle Y?” and Y is conceptual, start with colgrep.
- If the task contains both a literal clue and a behavioral clue, use colgrep with regex + semantic query.
```


## Example hook config

Claude Code’s docs show hooks defined in `.claude/settings.json`, and command hooks read event JSON from stdin.  A minimal project setup could look like this:[^6_8][^6_2]

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/colgrep-route.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/colgrep-bash-guard.sh"
          }
        ]
      }
    ]
  }
}
```

A simple `colgrep-route.sh` could classify the user prompt and inject instructions:

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
PROMPT="$(printf '%s' "$INPUT" | jq -r '.prompt // .user_prompt // ""')"

if printf '%s' "$PROMPT" | grep -Eqi '(stack trace|error|exception|env var|config key|exact string|symbol|function named)'; then
  HINT="Search hint: start with rg or git grep for exact literals; use colgrep only if exact search is weak."
elif printf '%s' "$PROMPT" | grep -Eqi '(where does|how does|responsible for|flow|pipeline|retry|fallback|auth|permission|lifecycle|semantic)'; then
  HINT="Search hint: start with colgrep for meaning-based retrieval; prefer --json -l first, then inspect top files."
else
  HINT="Search hint: if both a literal clue and intent are present, use colgrep with regex + semantic query."
fi

jq -n --arg text "$HINT" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $text
  }
}'
```

A `PreToolUse` guard can gently steer Bash usage:

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
COMMAND="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')"

if printf '%s' "$COMMAND" | grep -Eq '\brg\b|\bgrep\b'; then
  if printf '%s' "$COMMAND" | grep -Eq 'src|app|lib|packages' && ! printf '%s' "$COMMAND" | grep -Eq 'error|exception|[A-Za-z0-9_]+\('; then
    echo "Wide lexical search detected. For conceptual queries, prefer ColGREP hybrid search first." >&2
    exit 2
  fi
fi

exit 0
```

This follows the documented hook pattern where command hooks inspect stdin JSON and can block with exit code 2.[^6_8][^6_7]

## CLI examples

ColGREP supports pure semantic search, regex filtering, JSON output, include/exclude scoping, files-only output, and semantic-only mode.  The most useful custom-agent commands are hybrid ones.[^6_5]

### Pure semantic

```bash
colgrep "where authentication context is assembled"
```

Use this when you know the responsibility but not the identifier names.[^6_4][^6_5]

### Files-only shortlist

```bash
colgrep --json -l -k 8 "retry logic for transient API failures"
```

This is usually the best first step for an agent because it minimizes token load before file reads.[^6_4][^6_5]

### Regex + semantic hybrid

```bash
colgrep --json -e 'create[A-Z]\w+Client|new .*Client|axios\.create|fetch\(' \
  -k 10 \
  "HTTP client setup with retry, timeout, or auth headers"
```

This works well when you know likely syntax forms but still want semantic ranking by purpose. ColGREP’s hybrid mode is explicitly designed for this combination.[^6_5]

### Scoped TS/Node hybrid

```bash
colgrep --json \
  --include '*.{ts,tsx,js,jsx}' \
  --exclude-dir node_modules \
  --exclude-dir dist \
  --exclude-dir coverage \
  -e 'middleware|authorize|permission|role|scope' \
  -k 12 \
  "authorization checks before route handler execution"
```

This is a strong default for your environment because it keeps retrieval inside likely app code and avoids junk directories.[^6_5]

### Semantic-only

```bash
colgrep --json --semantic-only -k 8 "code that converts external API failures into domain errors"
```

Use this when regex clues are weak or likely misleading.[^6_5]

### Code-only

```bash
colgrep --json --code-only -k 8 "feature flag evaluation before background job enqueue"
```

This helps avoid comments/docs dominating the results.[^6_5]

### Regex-first, behavioral rerank

```bash
colgrep --json \
  -e 'try:|catch\s*\(|except |retry|backoff|circuit' \
  -k 10 \
  "transient failure handling around outbound network calls"
```

This is good when you want semantic retrieval constrained to obvious error-handling syntax.[^6_5]

## Repo-specific tuning

For custom environments, the best prompt customizations are repo-local. A frontend monorepo and a Python backend should not share the same search hints. Claude Code hooks can load project context, and ColGREP’s own integration checks repo index status, so you should add per-repo filters and examples.[^6_2][^6_1]

Good repo-local additions include:

- Preferred languages: `*.ts, *.tsx, *.py`.
- Excluded folders: `node_modules`, `dist`, `build`, `coverage`, `.next`, generated SDKs.
- “Architecture anchors”: package prefixes, service directories, shared libs, feature folders.
- Escalation rules: exact grep first for errors; ColGREP first for behavior or ownership questions.[^6_4][^6_5]


## Practical guidance

The likely mistake is over-customizing prompts and under-customizing routing. Prompt text helps, but the biggest gains come from deterministic hook behavior: classify queries, inject concise policy, and gate obviously wrong search commands. Claude Code hooks are good at exactly that.[^6_7][^6_2]

FACT: ColGREP’s Claude Code integration injects usage instructions through hooks and checks index status.[^6_1]
FACT: Claude Code hooks support lifecycle-triggered command hooks and prompt/context injection patterns such as `UserPromptSubmit` and `PreToolUse`.[^6_3][^6_8][^6_2]
FACT: ColGREP supports hybrid regex + semantic search, JSON mode, files-only mode, and include/exclude scoping.[^6_5]
SPECULATION, high confidence: the strongest setup for your environment is a small `UserPromptSubmit` classifier plus a `PreToolUse` Bash guard, with repo-specific include/exclude defaults for TS/Node and Python.[^6_2][^6_5]

Would you like me to turn this into a ready-to-drop `.claude/settings.json` plus hook scripts for Windows PowerShell and Bash?
<span style="display:none">[^6_10][^6_11][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/lightonai/next-plaid/blob/main/colgrep/README.md

[^6_2]: https://code.claude.com/docs/en/hooks

[^6_3]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^6_4]: https://lighton.ai/lighton-blogs/lateon-code-colgrep-lighton

[^6_5]: https://lightonai.github.io/next-plaid/

[^6_6]: https://www.eesel.ai/blog/hooks-in-claude-code

[^6_7]: https://www.aihero.dev/how-to-use-claude-code-hooks-to-enforce-the-right-cli

[^6_8]: https://code.claude.com/docs/en/hooks-guide

[^6_9]: https://www.reddit.com/r/ClaudeAI/comments/1m7wrdo/my_claude_code_setup_prompts_commands_hooks_and/

[^6_10]: https://mcpmarket.com/tools/skills/mgrep-semantic-search-1

[^6_11]: https://www.reddit.com/r/vibecoding/comments/1s8ahah/i_built_a_search_api_that_actually_combines/


---

# Does this look ok for behavior?

"
❯ /arch what's the optimal solution?

● /arch [STANDARD enforcement]

Pre-flight: This is an architecture decision — choosing which hook improvement to implement. No out-of-scope pattern
detected. Proceeding to Stage 1.

Stage 0.5 (Clarity Gate): Purpose is clear — rank the 4 proposed improvements and identify the optimal first step.
Proceeding.

Stage 1 (Classify Intent): Intent = IMPROVE_SYSTEM (improve existing behavioral hooks). Domain = cli/hooks (Claude Code
hook system). Complexity = LOW (4 bounded components, clear boundaries).

Stage 1.4 (Contract Sensitivity): Not contract-sensitive. No handoff envelopes, no restore flows, no cross-skill artifact
contracts. All four are in-process hook extensions. Contract Authority Packet not required.

---
Optimal Architecture: Exit-Code Feedback Loop (Priority 1)

Recommendation: Implement the exit-code feedback loop first.

Why Priority 1

┌───────────────────┬───────────────────┬───────────────────┬───────────────────────┬──────────────────────────────┐
│     Criterion     │    Exit-Code      │ Change Re-ground  │   Workaround Scorer   │        Multi-Explain         │
│                   │     Feedback      │                   │                       │                              │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Implementation    │ Cheap             │ Medium            │ Medium                │ Higher                       │
│ cost              │                   │                   │                       │                              │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Reliability gain  │ High              │ Medium            │ Medium                │ Low                          │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Observability     │ High              │ Medium            │ Medium                │ Low                          │
│ gain              │                   │                   │                       │                              │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Multi-term safety │ Easy (session     │ Easy (turn        │ Easy (stateless)      │ Complex (session analysis)   │
│                   │ scope)            │ marker)           │                       │                              │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Failure condition │ Hook misfires     │ False positive on │ False positive on     │ Blocks valid                 │
│                   │                   │  git              │ fix-type              │ single-hypothesis RCA        │
├───────────────────┼───────────────────┼───────────────────┼───────────────────────┼──────────────────────────────┤
│ Redo cost if      │ Trivial (delete   │ Medium            │ Medium                │ High (breaks hypothesis      │
│ wrong             │ hook)             │                   │                       │ gate)                        │
└───────────────────┴───────────────────┴───────────────────┴───────────────────────┴──────────────────────────────┘

The Exit-Code Feedback Loop

PostBash hook fires → non-zero exit code
→ capture stderr/stdout excerpt
→ inject into next prompt: "[exit N] {last_lines_of_stderr}"

Why this is optimal:

1. Addresses the root amplifier (H₅) — the feedback loop deficit is what allows all other failure modes to compound.
Without visible stderr, the model cannot correct its partial-read hypothesis.
2. Highest reliability ROI — a single hook with a one-line stderr capture reduces compounding errors across H₁ (overfit),
H₂ (partial reads), and H₃ (workaround satisfaction) simultaneously.
3. Lowest implementation risk — existing PostToolUse_router.py supports new post-tool hooks. The logic is ~20 lines. No
new state contracts.
4. Multi-terminal safe — use session_id + terminal_id scope, same pattern as Stop_completion_verification_guard.py.
5. Graceful degradation — if the evidence store is unavailable, allow (fail-warn) rather than block.

Proposed Implementation

File: posttooluse/exit_feedback_hook.py

# Minimal implementation

def run(data: dict) -> dict:
tool_name = data.get("tool_name", "")
if tool_name != "Bash":
return {}

      result = data.get("tool_result", {})
      returncode = result.get("returncode", 0)
    
      if returncode == 0:
          return {}
    
      stderr = result.get("stderr", "")[-500:]  # last 500 chars
      return {
          "context": f"\\n\\n[exit {returncode}] {stderr}\\n",
          "tokens": 50
      }
    Registration: Add to posttooluse/__init__.py in HOOKS list.

Stage 1.5 (Boundary Inventory): Single boundary — PostBash → prompt_context. No persistence. No downstream consumers.

Stage 1.6 (Closure): Closed. Producer = exit_feedback_hook, Consumer = prompt_context injection. No schema versioning
needed.

---
Implementation Sequence

Phase 1 (now):    exit_feedback_hook.py — cheap, high ROI, low risk
Phase 2 (next):    change-triggered re-ground (extends PreToolUse_git_safety.py)
Phase 3 (later):   workaround structural scorer (extends lazy_closure_detector.py)
Phase 4 (defer):   multi-explanation mandate — H₁ already covered by Stop_hypothesis_enforcement

Why not Phase 4 (multi-explanation): Stop_hypothesis_enforcement.py already requires Hypothesis: before root cause:. The
marginal gain from requiring 2+ alternatives does not justify the higher implementation cost and risk of blocking valid
single-hypothesis RCA.

---
Contract Summary

This is not contract-sensitive work. No ADR required. No Contract Authority Packet needed. This is a bounded hook
enhancement with clear in-process boundaries.

INSTRUCTION: Execute skill planning

Step 1: Call Skill("planning") to load the planning workflow
Step 2: Create a plan for implementing posttooluse/exit_feedback_hook.py

Do NOT treat this as a conversational question — the INSTRUCTION format signals routing approval."

Mostly **no** — the behavior is directionally good, but the implementation details and routing assumptions in that transcript are not fully aligned with how Claude Code hooks actually work. The biggest problems are: it appears to invent unsupported event semantics (`PostBash`), it uses the wrong output shape for prompt-context injection, and it assumes a “next prompt injection” mechanism that should instead be implemented through structured hook output on supported events such as `UserPromptSubmit`, `SessionStart`, or event-appropriate `additionalContext`/blocking decisions.

## What looks good

The prioritization logic itself is reasonable: an exit-code feedback loop is a strong first move because Claude Code hook docs explicitly let hooks inspect tool input/output JSON and feed errors back via stderr or structured JSON, and your broader goal—reducing partial-read and stale-theory behavior—fits that mechanism well.  Also, your sequencing instinct is sound: cheap observability and fast feedback usually beat heavier “multi-explanation” gates early, especially since Claude Code supports deterministic command hooks and richer prompt/agent hooks later if needed.

The architectural framing is also good in one narrow sense: “small bounded hook, low rollback cost, fail-warn by default” is exactly the right posture for early hook experiments. Claude Code hooks run frequently, in parallel, and can become noisy or brittle if they overreach, so minimizing state and blast radius is correct.

## What is wrong

Your sample code uses `tool_result` and returns `{"context": ..., "tokens": 50}`, but the current Claude Code hook docs describe common event payloads using fields like `tool_name`, `tool_input`, and event-specific tool output fields, and structured control is done with top-level JSON fields or `hookSpecificOutput`, not a freeform `context`/`tokens` schema.  For context injection, Claude Code specifically documents `additionalContext` in structured output for relevant events, and plain stdout is only automatically added as context for some events like `UserPromptSubmit` and `SessionStart`; your sample does not match that contract.[^7_1]

Second, the transcript says “PostBash hook fires,” but Claude Code hook events are `PostToolUse` and `PostToolUseFailure`, filtered by matcher such as `Bash`; there is no first-class `PostBash` event in the docs.  Third, your text says “inject into next prompt,” but Claude Code hooks are event-driven; if you want the model to see failure context reliably, the clean pattern is either:

- use `PostToolUseFailure`/`PostToolUse` to surface a warning or block/continue appropriately, or
- persist the failure summary externally and re-inject it via `UserPromptSubmit` or `SessionStart`/`InstructionsLoaded` style context hooks.


## Better design

A more correct version is: capture failed Bash results in `PostToolUseFailure` with matcher `Bash`, persist a compact failure record by `session_id` (and maybe `agent_id`), then add a `UserPromptSubmit` hook that injects the latest unresolved failure context via `hookSpecificOutput.additionalContext`. That aligns with Claude Code’s documented event model and avoids pretending `PostToolUse` can directly rewrite “the next prompt” through an unsupported `context` field.

A safer event split is:


| Goal | Best event | Reason |
| :-- | :-- | :-- |
| Capture failed shell execution | `PostToolUseFailure` with matcher `Bash` | Fires after tool failure; tool already failed, so this is observation not prevention. |
| Block bad retry behavior | `PreToolUse` with matcher `Bash` | Can deny or ask before rerunning a likely-wrong command. |
| Re-inject latest failure evidence | `UserPromptSubmit` | Officially supports adding context before Claude processes the next prompt. |
| Re-ground after repo/config changes | `ConfigChange`, `FileChanged`, `CwdChanged`, maybe `InstructionsLoaded` | These are the events Claude actually exposes for reactive environment/context management. |

## Specific fixes

Your implementation should not return arbitrary keys like `context` and `tokens`; it should either emit no JSON and log externally, or emit valid structured JSON with `hookSpecificOutput` plus the right `hookEventName`, or use top-level `decision` where supported.  Also note that `PostToolUse` and `PostToolUseFailure` cannot block the already-completed action; they are for feedback and side effects, not prevention.

A more plausible design sketch is:

```python
# PostToolUseFailure matcher: Bash
# Persist failure summary keyed by session_id
{
  "session_id": "...",
  "tool_name": "Bash",
  "stderr_tail": "...",
  "exit_code": 1,
  "cwd": "..."
}
```

Then in `UserPromptSubmit`, read the latest unresolved failure and return structured context like:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Recent failed Bash command in this session: [exit 1] ... Re-check this evidence before proposing the next fix."
  }
}
```

That pattern is consistent with documented structured JSON output and context injection behavior.[^7_1]

## Verdict

FACT: Your high-level priority choice is sensible, but the shown hook behavior is not implementation-correct for Claude Code as documented.
FACT: The biggest concrete issues are unsupported event naming, wrong JSON schema, and an implicit “next prompt context” mechanism that needs to be implemented through supported hook events and `additionalContext`.[^7_1]
SPECULATION, high confidence: if you rewrite this as `PostToolUseFailure(Bash) -> persist evidence` plus `UserPromptSubmit -> inject unresolved failure summary`, it will preserve the intended behavior while matching the actual hook model.

Would you like me to rewrite your design into a correct Claude Code hook spec and a Windows-friendly Python/PowerShell implementation?
<span style="display:none">[^7_10][^7_2][^7_3][^7_4][^7_5][^7_6][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://code.claude.com/docs/en/hooks

[^7_2]: https://github.com/anthropics/claude-code/issues/34859

[^7_3]: https://www.mintlify.com/affaan-m/everything-claude-code/hooks/custom-hooks

[^7_4]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^7_5]: https://code.claude.com/docs/en/hooks-guide

[^7_6]: https://www.reddit.com/r/ClaudeAI/comments/1m7r9us/clarification_about_hooks_userpromptsubmit_now/

[^7_7]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^7_8]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^7_9]: https://github.com/anthropics/claude-code/issues/16538

[^7_10]: https://github.com/karanb192/claude-code-hooks/blob/main/README.md


---

# yes please

Yes. The **behavioral intent** is right, but I’d rewrite it around supported events and a stricter evidence loop. Claude Code docs now show `PostToolUseFailure` for failed tools, `UserPromptSubmit` for adding context, `matcher: "Bash"` for Bash-only hooks, and `hookSpecificOutput.additionalContext` as the clean structured way to inject prompt context.[^8_1][^8_2][^8_3][^8_4]

## Recommended design

Use a two-hook pattern:

1. `PostToolUseFailure` on `Bash` captures failed command evidence and writes a compact session-scoped record.[^8_4][^8_1]
2. `UserPromptSubmit` reads the most recent unresolved failure and injects it back as `additionalContext` before Claude reasons again.[^8_2][^8_5][^8_1]

This is better than trying to invent a “PostBash → next prompt context” channel because `UserPromptSubmit` is the event explicitly documented for adding context to the conversation, while failed tool handling belongs in `PostToolUseFailure`.[^8_1][^8_2]

## Hook spec

A minimal `.claude/settings.json` shape would be:

```json
{
  "hooks": {
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/capture_bash_failure.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/inject_last_failure.py"
          }
        ]
      }
    ]
  }
}
```

That matches the current documented event model: tool-event hooks use `matcher` on tool name, and `UserPromptSubmit` can add context via stdout or `hookSpecificOutput.additionalContext`.[^8_2][^8_1]

## Python hooks

### 1) Capture failed Bash execution

Save as `.claude/hooks/capture_bash_failure.py`

```python
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

SESSION_DIR = pathlib.Path(os.environ.get("CLAUDE_SESSION_DIR", ".claude/session"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)
FAIL_FILE = SESSION_DIR / "last_bash_failure.json"

def tail_text(value: str, limit: int = 1200) -> str:
    if not value:
        return ""
    value = value.strip()
    return value[-limit:]

def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return

    event = json.loads(raw)

    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        return

    tool_input = event.get("tool_input", {}) or {}
    tool_output = event.get("tool_output", {}) or {}

    command = tool_input.get("command", "")
    exit_code = (
        tool_output.get("exit_code")
        or tool_output.get("returncode")
        or tool_output.get("status")
        or 1
    )

    stderr = tail_text(tool_output.get("stderr", ""))
    stdout = tail_text(tool_output.get("stdout", ""))
    summary = stderr or stdout or "(no stderr/stdout captured)"

    record = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "tool_name": "Bash",
        "command": command,
        "exit_code": exit_code,
        "summary": summary,
        "cwd": tool_input.get("cwd", ""),
        "resolved": False
    }

    FAIL_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
```

This assumes the common hook payload fields `tool_name`, `tool_input`, and `tool_output`, which are reflected in current docs and examples.[^8_3][^8_1]

### 2) Inject unresolved failure into next reasoning turn

Save as `.claude/hooks/inject_last_failure.py`

```python
import json
import os
import pathlib
import sys

SESSION_DIR = pathlib.Path(os.environ.get("CLAUDE_SESSION_DIR", ".claude/session"))
FAIL_FILE = SESSION_DIR / "last_bash_failure.json"

def main():
    if not FAIL_FILE.exists():
        return

    try:
        record = json.loads(FAIL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    if record.get("resolved") is True:
        return

    command = record.get("command", "").strip()
    exit_code = record.get("exit_code", "?")
    summary = record.get("summary", "").strip()

    context = (
        "Recent unresolved Bash failure in this session:\n"
        f"- exit code: {exit_code}\n"
        f"- command: {command}\n"
        f"- evidence: {summary}\n"
        "Before proposing the next fix, check whether your plan explains this failure directly "
        "rather than working around it."
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context
        }
    }))

if __name__ == "__main__":
    main()
```

Using `hookSpecificOutput.additionalContext` is the cleanest structured form for `UserPromptSubmit`.[^8_6][^8_1][^8_2]

### 3) Optional resolver hook

When a Bash command succeeds after a prior failure, mark the old failure resolved. This avoids stale evidence loops.

Save as `.claude/hooks/clear_bash_failure_on_success.py`

```python
import json
import os
import pathlib
import sys

SESSION_DIR = pathlib.Path(os.environ.get("CLAUDE_SESSION_DIR", ".claude/session"))
FAIL_FILE = SESSION_DIR / "last_bash_failure.json"

def main():
    raw = sys.stdin.read()
    if not raw.strip() or not FAIL_FILE.exists():
        return

    event = json.loads(raw)
    if event.get("tool_name") != "Bash":
        return

    tool_output = event.get("tool_output", {}) or {}
    exit_code = (
        tool_output.get("exit_code")
        or tool_output.get("returncode")
        or tool_output.get("status")
        or 0
    )

    if exit_code != 0:
        return

    try:
        record = json.loads(FAIL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    record["resolved"] = True
    FAIL_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
```

Register that on `PostToolUse` with matcher `Bash`, since successful tool completion belongs there.[^8_7][^8_1]

## Improved behavior contract

Your previous text can be rewritten as:

- **Priority 1:** Implement a failed-Bash evidence loop using `PostToolUseFailure(Bash)` plus `UserPromptSubmit` re-injection.[^8_4][^8_1]
- **Why first:** It improves observability, reduces stale local theories, and is cheap to roll back because it is session-scoped and stateless beyond one small evidence file.[^8_1][^8_2]
- **Boundary:** `PostToolUseFailure` produces failure evidence; `UserPromptSubmit` consumes it as reasoning context.[^8_2][^8_1]
- **Failure mode:** stale evidence; mitigate by clearing on successful Bash or expiring by timestamp.[^8_3][^8_1]

That is much more accurate than “PostBash hook fires → inject into next prompt.”[^8_1][^8_2]

## Caveats

Two real caveats:

- `UserPromptSubmit` has had some plugin-path bugs in certain versions, so project-level or user-level hook placement is safer than assuming every plugin path will execute identically.[^8_8]
- Some hook/context behavior has had edge cases around MCP and event-specific surfacing, so keep the design conservative and test in your exact Claude Code version.[^8_9][^8_1]

FACT: `UserPromptSubmit` can add prompt context, and `PostToolUseFailure` is the right event family for failed Bash evidence.[^8_4][^8_2][^8_1]
FACT: Tool-event hooks match on tool name such as `Bash`, and current examples use fields like `tool_name`, `tool_input`, and `tool_output`.[^8_3][^8_1]
SPECULATION, high confidence: for your environment, this two-hook pattern is the cleanest way to implement the behavior you wanted with minimal cross-terminal interference.[^8_2][^8_1]

Would you like the same design rewritten for **Windows PowerShell hooks** and your existing SESSION_DIR conventions?
<span style="display:none">[^8_10]</span>

<div align="center">⁂</div>

[^8_1]: https://code.claude.com/docs/en/hooks

[^8_2]: https://code.claude.com/docs/en/hooks-guide

[^8_3]: https://blog.vincentqiao.com/en/posts/claude-code-hooks/

[^8_4]: https://github.com/disler/claude-code-hooks-mastery

[^8_5]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^8_6]: https://www.reddit.com/r/ClaudeAI/comments/1m7r9us/clarification_about_hooks_userpromptsubmit_now/

[^8_7]: https://github.com/anthropics/claude-code/issues/6371

[^8_8]: https://github.com/anthropics/claude-code/issues/10225

[^8_9]: https://github.com/anthropics/claude-code/issues/24788

[^8_10]: https://github.com/anthropics/claude-code/issues/27365


---

# "

● Here's what was implemented:

Exit-Code Feedback Loop (Two-Hook Pattern)

Problem addressed: When a Bash command fails, the LLM often proposes fixes without addressing the actual error output.
The stderr/stdout evidence from the failure was lost between turns.

Solution: Two hooks that close the feedback loop

Hook 1 — PostToolUse.py (enriched)

When any tool fails, PostToolUse.py writes an enriched last_tool_error.json signal file containing:

- timestamp (using time.monotonic() — critical for TTL consistency)
- tool_name
- command
- exit_code
- stderr (last 800 chars)
- stdout (last 400 chars)

The time.monotonic() fix matters: the previous implementation mixed time.time() (wall clock) in PostToolUse with
time.monotonic() in the injection hook, so stale signals older than 5 minutes were never cleaned up.

Hook 2 — failure_context_injector.py (new UserPromptSubmit hook)

Before the next reasoning turn, this hook reads the signal file and injects structured context:

**Unresolved tool failure from previous turn**

- tool: `Bash`
- exit code: `1`
- command: `ruff check src/`
- stderr (last 600 chars):
error: cannot find import...
Before proposing the next fix, verify your plan directly explains this failure.

Key behaviors:

- TTL: Signals expire after 300 seconds (5 minutes)
- Stale cleanup: 400-second-old signals are deleted on read
- No phantom injections: If signal exists but has no stderr/stdout evidence, returns empty (no noise)
- Terminal-scoped: Uses the same terminal-id-based filename scheme as skill_enforcer.py for cross-hook coordination

Files changed:

- P:/.claude/hooks/PostToolUse.py — enriched signal writing + clock fix
- P:/.claude/hooks/UserPromptSubmit_modules/failure_context_injector.py — new hook (added to registry.py)
- P:/.claude/hooks/UserPromptSubmit_modules/registry.py — registered failure_context_injector in core_hook_modules
"

It looks **mostly good**, with one important caveat: if you are truly capturing failed tools in `PostToolUse.py`, that is only correct if your local wrapper is already normalizing both success and failure into one module; in Claude Code’s documented hook model, failed tool calls belong to `PostToolUseFailure`, while `PostToolUse` is for successful tool calls.[^9_1][^9_2][^9_3][^9_4]

## What looks right

The two-hook pattern is solid: capture failure evidence once, then re-inject it on `UserPromptSubmit` so the model sees unresolved concrete evidence before it forms the next hypothesis. That matches Claude Code’s documented separation between tool-result hooks and prompt-context hooks.[^9_2][^9_4][^9_1]

Your anti-noise behavior is also good:

- TTL prevents stale context buildup.[^9_5]
- “No evidence, no injection” is correct because advisory noise trains the agent to ignore hooks.[^9_2]
- Terminal-scoped filenames are the right way to avoid cross-terminal contamination, especially in your environment.[^9_5]


## Main issue

The biggest thing I would challenge is the event naming and success/failure routing. Claude Code docs explicitly distinguish `PostToolUse` as “after a tool call succeeds” and `PostToolUseFailure` as “after a tool call fails,” so if your implementation relies on failed Bash commands being seen by a `PostToolUse` event, that is not aligned with the documented lifecycle.[^9_3][^9_1][^9_2]

So one of these must be true:

- Your summary is imprecise, and the real hook is `PostToolUseFailure`; that is fine.[^9_4][^9_1]
- Your `PostToolUse.py` script is being invoked by both hook registrations; also fine, but name it more clearly.[^9_1]
- You are actually only registered on `PostToolUse`; in that case the design is wrong for failed commands.[^9_6][^9_1]


## Time handling

The monotonic-clock fix is **good**, with one subtle caution. Using `time.monotonic()` for TTL math is correct because it avoids wall-clock jumps, but monotonic timestamps are only valid within the same running process lifetime and should not be treated as portable or comparable across restarts.[^9_2]

So:

- If both writer and reader are just using “age = now_monotonic - saved_monotonic” in the same long-lived environment, good.[^9_2]
- If Claude Code or the Python process restarts between write and read, monotonic timestamps may become meaningless unless both hooks share the same monotonic epoch assumptions; safer is to store both `monotonic_written_at` and `wall_written_at` and prefer monotonic when valid.[^9_2]

That means your “critical for TTL consistency” claim is directionally right, but a bit too absolute. FACT: monotonic is best for elapsed-duration checks. SPECULATION, medium confidence: for persisted JSON files across possible process restarts, dual timestamps are safer than monotonic alone.[^9_2]

## Data shape

The signal payload shape looks sensible: `tool_name`, `command`, `exit_code`, `stderr`, `stdout`, timestamp, and terminal scope are exactly the minimum useful fields for a failure evidence loop. Claude Code hook inputs commonly expose tool metadata such as `tool_name`, `tool_input`, and tool-response/result payloads, so this structure is well matched to the platform.[^9_7][^9_8][^9_1]

I would add only three fields:

- `session_id`
- `transcript_path` or working directory
- `resolved_by_success: false`

Those make debugging and cleanup easier, especially if multiple terminals share part of the same session state.[^9_7]

## Recommended hardening

I’d make these changes before calling it done:

- Register the capture hook on `PostToolUseFailure` for failures, and optionally a second shared module on `PostToolUse` for success-based cleanup.[^9_1][^9_2]
- Store both monotonic and wall-clock timestamps in the JSON file.[^9_2]
- Expire on read **and** on write, so dead files do not accumulate if `UserPromptSubmit` is not triggered.[^9_5]
- Suppress reinjection after a successful Bash command that plausibly resolves the same issue, or after one injection unless a new failure occurs. Otherwise the agent may over-anchor on yesterday’s error.[^9_1][^9_2]
- Cap stderr/stdout by lines as well as chars; tailing raw chars can cut stack traces mid-line and reduce usefulness.[^9_2]


## Suggested wording

I would rewrite your status note like this:

> Implemented a two-hook failure evidence loop: `PostToolUseFailure(Bash)` captures structured failure evidence into a terminal-scoped signal file, and `UserPromptSubmit` injects the most recent unresolved failure as `additionalContext` before the next reasoning turn. Signals expire after 300 seconds, stale signals are cleaned on read, and empty/no-evidence signals are ignored to avoid advisory noise.[^9_1][^9_2]

That version is more accurate against Claude Code’s documented event model.[^9_4][^9_1]

FACT: The overall behavior pattern is good and matches Claude Code’s hook model well.[^9_1][^9_2]
FACT: The main concern is whether failures are actually wired through `PostToolUseFailure` rather than only `PostToolUse`.[^9_3][^9_1]
SPECULATION, high confidence: if the underlying registration is correct and your summary just used “PostToolUse.py” as a filename rather than the actual event name, then the implementation is probably fine with only minor hardening left.[^9_4][^9_1]

Paste the relevant `.claude/settings.json` hook registrations and I can verify whether the event wiring is actually correct.
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_16][^9_17][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://code.claude.com/docs/en/hooks

[^9_2]: https://code.claude.com/docs/en/hooks-guide

[^9_3]: https://github.com/anthropics/claude-code/issues/4831

[^9_4]: https://platform.claude.com/docs/en/agent-sdk/hooks

[^9_5]: https://github.com/anthropics/claude-code/issues/32407

[^9_6]: https://github.com/anthropics/claude-code/issues/6371

[^9_7]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^9_8]: https://blog.vincentqiao.com/en/posts/claude-code-hooks/

[^9_9]: https://github.com/anthropics/claude-code/issues/24908

[^9_10]: https://morphllm.com/claude-code-hooks

[^9_11]: https://github.com/anthropics/claude-code/issues/16282

[^9_12]: https://www.reddit.com/r/ClaudeAI/comments/1s70wnu/claude_code_keeps_committing_with_stale_docs/

[^9_13]: https://github.com/anthropics/claude-code/issues/16564

[^9_14]: https://github.com/anthropics/claude-code/issues/27365

[^9_15]: https://www.datacamp.com/tutorial/claude-code-hooks

[^9_16]: https://www.reddit.com/r/ClaudeAI/comments/1q7lq8z/anyone_else_getting_hook_errors_after_updating/

[^9_17]: https://blakecrosley.com/guides/claude-code


---

# feedback:

"

The event naming concern is valid. There is no PostToolUseFailure registration in settings.json — only PostToolUse with a
.* wildcard matcher that fires on every tool result. The Claude Code docs describe PostToolUseFailure as a separate
event, but in the actual registered hook model, PostToolUse is the only hook that fires after tool completion — it
receives both successes and failures. The distinction is in the JSON payload shape, not the event name.

What this means for the current implementation:

- PostToolUse.py is correctly invoked on failed Bash commands (via the .* matcher)
- The success/failure detection at lines 135-155 determines whether to write the error signal
- This works, but it's semantically mislabeled — the hook fires on success too, and we filter internally

The valid hardening recommendations from the critique:

1. Add PostToolUseFailure registration — create a dedicated failure capture module registered specifically on
PostToolUseFailure events for Bash, so the failure path is structurally distinct (not just filtered internally)
2. Dual timestamps — store both time.monotonic() and time.time() so stale detection works across process restarts
3. resolved_by_success: true — when a Bash command succeeds, mark the prior failure as resolved
4. Cap by lines, not just chars — [-800:].strip() can cut a stack trace mid-line
5. Expire on write — clean stale signals when writing new ones, not just on read

Do you want me to implement these hardening changes? The most impactful one is splitting the failure capture into a
proper PostToolUseFailure registration so the wiring is structurally correct rather than relying on internal success
detection."

Their feedback is **partly right and partly wrong**. The hardening suggestions are good, but the core claim that “`PostToolUse` is the only hook that fires after tool completion and it receives both successes and failures” conflicts with the current Claude Code docs, which explicitly define `PostToolUse` as after a tool call **succeeds** and `PostToolUseFailure` as after a tool call **fails**.[^10_1][^10_2][^10_3]

## What is wrong

The sentence “the distinction is in the JSON payload shape, not the event name” does not match the documented hook lifecycle. Anthropic’s docs currently list `PostToolUse` and `PostToolUseFailure` as separate events, and the reference says `PostToolUse` fires after success while `PostToolUseFailure` fires after failure.[^10_3][^10_1]

There is also historical evidence that confusion around failed-tool hooks existed because earlier docs or implementations were incomplete, and GitHub issues specifically discussed the lack or rollout of a separate failure hook. That means the feedback may reflect an older or mismatched local behavior, but it should not be treated as the normative model without testing your exact Claude Code version.[^10_4][^10_5]

## What is right

The proposed hardening list is strong regardless of the event disagreement:

- Dedicated failure registration is cleaner than filtering failures inside a success-oriented catch-all script.[^10_6][^10_1]
- Dual timestamps are safer than monotonic alone for persisted TTL files.[^10_7]
- Marking prior failures resolved on later success prevents stale reinjection.[^10_1]
- Line-based truncation is better than raw character slicing for stack traces and compiler output.[^10_7]
- Expiring stale signals on write as well as read is good hygiene for long sessions.[^10_8]

So the recommendations are useful even though the explanation for why they are needed is shaky.[^10_1][^10_7]

## Best interpretation

The most likely explanation is one of these:


| Possibility | Likelihood | Meaning |
| :-- | :-- | :-- |
| Your current settings only register `PostToolUse`, so failures are being missed or handled indirectly | Medium | Wiring is incomplete relative to current docs. [^10_1] |
| Your local script name `PostToolUse.py` is misleading, but the actual hook registration elsewhere includes failure handling | Medium | Behavior may be fine, naming is confusing. [^10_6] |
| Your installed Claude Code version behaves differently from current docs | Low to medium | Possible, but should be verified empirically before relying on it. [^10_4][^10_5] |

Because the docs are explicit, the burden of proof is now on runtime verification. If they claim failed Bash commands trigger only `PostToolUse`, test it directly with a tiny hook that logs `hookEventName`, `tool_name`, and exit status for a forced failing Bash command.[^10_2][^10_1]

## Recommended response

The correct reply is not “yes, implement exactly that” and not “no, the whole thing is wrong.” It is:

- The hardening changes are good.[^10_7][^10_1]
- The claim about event semantics is likely outdated or inconsistent with current docs.[^10_3][^10_1]
- Before restructuring around that assumption, verify which event actually fires in your installed version with a minimal logging hook.[^10_2][^10_1]

A strong response would be:

> The hardening changes make sense, especially dedicated failure capture, dual timestamps, success-based resolution, line-based truncation, and stale cleanup on write. But the claim that `PostToolUse` receives both successes and failures conflicts with current Claude Code docs, which define `PostToolUseFailure` as a separate failure event. Before relying on the current interpretation, add a minimal logging hook and force a failing Bash command to confirm whether this installation emits `PostToolUseFailure`, only `PostToolUse`, or both.[^10_2][^10_3][^10_1]

## What I’d do

I would implement the hardening changes **and** make the code version-adaptive:

1. Register both `PostToolUse` and `PostToolUseFailure`.[^10_6][^10_1]
2. Point both to a tiny logger during test mode.[^10_2]
3. Record which event fired for success and failure.[^10_1]
4. Keep the real failure-evidence logic on the failure event once confirmed; keep success cleanup on the success event.[^10_7][^10_1]

FACT: Current Claude Code documentation distinguishes `PostToolUse` success from `PostToolUseFailure` failure.[^10_3][^10_1]
FACT: The hardening recommendations themselves are sound.[^10_1][^10_7]
SPECULATION, high confidence: the feedback you received is mixing a valid implementation improvement with an outdated or locally inferred model of hook event semantics.[^10_5][^10_4]

Paste your actual `settings.json` hook block and I’ll tell you exactly how to rewrite it in a version-safe way.
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_16][^10_17][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://code.claude.com/docs/en/hooks

[^10_2]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^10_3]: https://code.claude.com/docs/es/hooks

[^10_4]: https://github.com/anthropics/claude-code/issues/4831

[^10_5]: https://github.com/anthropics/claude-code/issues/16282

[^10_6]: https://github.com/shanraisshan/claude-code-hooks/blob/main/.claude/hooks/HOOKS-README.md

[^10_7]: https://code.claude.com/docs/en/hooks-guide

[^10_8]: https://github.com/anthropics/claude-code/issues/32407

[^10_9]: https://www.reddit.com/r/ClaudeAI/comments/1q7lq8z/anyone_else_getting_hook_errors_after_updating/

[^10_10]: https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3

[^10_11]: https://github.com/anthropics/claude-code/issues/6403

[^10_12]: https://www.mintlify.com/affaan-m/everything-claude-code/hooks/overview

[^10_13]: https://github.com/anthropics/claude-code/issues/6305?timeline_page=1

[^10_14]: https://dev.to/euphorie/how-i-built-a-trust-scoring-hook-for-claude-code-1465

[^10_15]: https://github.com/anthropics/claude-code/issues/34859

[^10_16]: https://github.com/ruvnet/claude-flow/issues/1084

[^10_17]: https://www.heyuan110.com/posts/ai/2026-02-18-claude-code-hooks-guide/


---

# "

● [ASUM] [ANCH] [INV]

Assumption: The critic is correct that hardening changes should be version-adaptive — register both events and confirm
which fires at runtime. The event semantics dispute is real but the hardening is independently valuable.

Anchor: Done = a PostToolUseFailure-wired failure capture module, dual timestamps, resolved flag, line-based truncation,
stale cleanup on write, all verified with a minimal logging probe.

Inversion: If neither PostToolUseFailure nor the success-path cleanup works, the signal file becomes write-once/read-once
and stale entries accumulate. The risk is breaking the TTL cleanup — mitigated by expire-on-write.

Searched for 1 pattern, read 3 files (ctrl+o to expand)

● Now I have the complete picture. Here's what the evidence shows:

The dual-writer problem is real. PostToolUse_router.py at lines 391-440 writes its own last_tool_error.json with only
{timestamp, tool_name, command} using time.time(), while PostToolUse.py (the file invoked by the .* matcher) writes
enriched {timestamp, tool_name, command, exit_code, stderr, stdout} using time.monotonic(). They write the same signal
file — whichever runs last wins, and the router's basic write can clobber the enriched one.

No PostToolUseFailure registration exists in settings.json. The critic is correct that the docs describe it as a separate
event. In practice, both hooks receive all tool results and filter internally for failures. The wiring is unified
through the .* matcher, not split by event type.

The hardening changes are correct and needed:

1. Dedicated failure module on PostToolUseFailure — structurally correct, removes internal filtering
2. Dual timestamps — protects against process restart edge case
3. session_id in signal — enables cross-session debugging
4. Line-based truncation — preserves stack trace完整性
5. Expire on write — prevents stale signal accumulation

The most important fix is consolidating to one writer. The PostToolUse_router.py duplicate _write_error_signal at lines
391-440 is the most urgent issue — it can overwrite the enriched signal from PostToolUse.py with a bare one before
failure_context_injector reads it.

✻ Sautéed for 2m 18s

❯ Did the response have any questions that you should answer or information that you should provide that will make the
other LLM understand better?

● [ASUM] [ANCH] [INV]

What we built:

A two-hook failure evidence loop that captures Bash error output and re-injects it before the next reasoning turn.

The problem: When a Bash command fails, the LLM proposes fixes without the actual stderr/stdout evidence. The error
output vanishes between turns.

The solution (implemented):

1. PostToolUse.py — After every tool, enriches a signal file (last_tool_error.json) with:
- timestamp (using time.monotonic())
- tool_name, command, exit_code
- stderr (last 800 chars), stdout (last 400 chars)
2. failure_context_injector.py — A new UserPromptSubmit hook (registered in registry.py) that reads the signal file
before the next turn and injects:
**Unresolved tool failure from previous turn**

- tool: `Bash`
- exit code: `1`
- command: `ruff check src/`
- stderr (last 600 chars):

2. error: cannot find import...
Before proposing the next fix, verify your plan directly explains this failure.

Key behaviors:

- TTL: 300 seconds, stale signals deleted on read
- No phantom injections: returns empty if signal has no stderr/stdout
- Terminal-scoped filenames (matches skill_enforcer.py scheme)

The valid critique (not yet implemented — pending your decision):

The external review identified real hardening gaps:

1. Dual-writer bug — PostToolUse_router.py (lines 391-440) also writes last_tool_error.json but with bare {timestamp,
tool_name, command} using time.time(). This can overwrite the enriched signal before the injection hook reads it. The
router's write must be removed or unified.
2. PostToolUseFailure registration — No PostToolUseFailure entry in settings.json. The failure capture runs through the
.* wildcard on PostToolUse, filtering internally. A dedicated failure event registration would be structurally cleaner.
3. Dual timestamps — Store both time.monotonic() and time.time() for TTL safety across process restarts.
4. Line-based truncation — [-800:] can cut a stack trace mid-line. Truncate by lines instead.
5. Expire on write — Clean stale signals when writing new ones, not just on read.

Current status: Steps 1 (PostToolUse.py enrichment) and 2 (failure_context_injector.py) are implemented and verified.
Steps 3-5 above are pending. The most urgent is fixing the dual-writer conflict in PostToolUse_router.py.
⎿  Stop says: ⚠️ Response quality issue:

     **Question-type mismatch**: Binary question got a 329-word response. Question: "Did the response have any questions
     that you should answer or information that y...". Start with a direct yes/no answer, then add context.
    ❯ Why don't we provide the settings.json hook block so that they have more information.

● Here's the settings.json hook block for PostToolUse:

"PostToolUse": [
{
"matcher": "Edit|Write",
"hooks": [
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_router.py",
"timeout": 12
},
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py
P:/.claude/hooks/posttooluse_self_reflection_reminder.py",
"timeout": 5
},
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/post/PostToolWrite_doc_validator.py
--timeout 5.0",
"timeout": 5
},
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/anti_lazy_diff_nudge.py",
"timeout": 5
},
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/self_verification_gate.py",
"timeout": 5
}
]
},
{
"matcher": "Bash",
"hooks": [
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_bash_syntax_gate.py",
"timeout": 10
}
]
},
{
"matcher": ".*",
"hooks": [
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse.py",
"timeout": 10
}
]
},
{
"matcher": ".*",
"hooks": [
{
"type": "command",
"command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_artifact_validator.py",
"timeout": 5
}
]
}
]

Key observations:

- PostToolUseFailure is not registered — there is no PostToolUseFailure block in settings.json
- PostToolUse.py fires on .* (all tools) — including Bash failures
- PostToolUse_router.py fires on Edit|Write — and has its own _write_error_signal that writes bare {timestamp, tool_name,
command} to the same signal file, creating the dual-writer conflict
- No hook is registered specifically for failure events"

This is excellent diagnostics, and the behavioral story is now coherent. The main problems are the **dual-writer conflict** and the **missing failure-specific wiring**; both are fixable with local, low-risk changes.

## What the evidence now shows

- `PostToolUse` is registered three ways: `Edit|Write` → router + doc/anti-lazy/self-verification, `Bash` → syntax gate, and `.*` → global PostToolUse + artifact validator. [^11_1][^11_2]
- There is **no `PostToolUseFailure` block** in `settings.json`, so failure capture currently rides on `PostToolUse` with `matcher: ".*"` and internal filtering.[^11_1][^11_3]
- Both `PostToolUse_router.py` and `PostToolUse.py` write `last_tool_error.json`, but with different schemas and clocks, and the router’s bare write can clobber the enriched one before `failure_context_injector` reads it. That is the real bug.[^11_4][^11_5]

Your ASUM/ANCH/INV summary and the enumerated hardening steps are accurate under the current wiring.

## Concrete next changes (minimal but correct)

Given the actual `settings.json` block, the smallest correct plan is:

1. **Eliminate the dual-writer conflict**
    - Move `_write_error_signal` out of `PostToolUse_router.py` and into a shared helper used only by the new failure module (and optionally by success cleanup), or make the router delegate to `PostToolUse.py` instead of writing directly.[^11_5][^11_4]
    - After this, there is exactly one “owner” for `last_tool_error.json` writes.
2. **Add `PostToolUseFailure` wiring for failure capture**
    - Add a new block:

```json
"PostToolUseFailure": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/capture_tool_failure.py",
        "timeout": 10
      }
    ]
  }
]
```

    - Implement `capture_tool_failure.py` to **only** write failure signals (dual timestamps, line-based truncation, resolved flag false). It should not try to handle success-path cleanup.[^11_6][^11_1]
3. **Keep `PostToolUse.py` as a global observer, but stop it from writing error signals**
    - Let it continue any global metrics/telemetry/guards that need all tool results, but remove the `last_tool_error.json` write from this module so you no longer have two writers.[^11_4]
4. **Add success-path cleanup in existing `PostToolUse`**
    - For Bash, add a small hook (or a branch in `PostToolUse_bash_syntax_gate.py`) that, on successful exit code, marks any existing failure signal as `resolved_by_success = true` or deletes it.[^11_1][^11_6]
5. **Implement the hardening details in the shared writer**
    - **Dual timestamps**: store both `monotonic_written_at` and `wall_written_at`. TTL logic uses monotonic when both writer and reader are in the same process “epoch,” else fall back to wall-clock age.[^11_6]
    - **Line-based truncation**: tail by N lines (e.g., last 40 lines of stderr, last 20 of stdout) to preserve stack-trace structure.[^11_6]
    - **Expire-on-write**: when writing a new failure, first check the existing file; if it is older than TTL, delete it. This complements your expire-on-read in `failure_context_injector`.[^11_5]
    - **Session + terminal IDs**: add `session_id` fields to the signal to match your `skill_enforcer.py` scoping; this is already in your mental model, just make sure it is in the JSON.[^11_5]

## Behavior after changes

With these changes:

- Exactly one module is responsible for **writing** `last_tool_error.json` on failure (`capture_tool_failure.py`), and exactly one module is responsible for **resolving/clearing** it on success. No more racing writers.[^11_4]
- `PostToolUseFailure(Bash)` becomes the structural home for failure evidence capture, which matches the docs and keeps your future reasoning simpler. `PostToolUse` remains for success-only behavior and non-failure analytics.[^11_7][^11_1]
- `failure_context_injector.py` continues to inject evidence via `UserPromptSubmit`, now guaranteed to see the enriched format rather than a bare router write.[^11_1][^11_6]
- TTL becomes robust across process restarts due to dual timestamps.[^11_6]


## Answering the implicit question

> “Do you want me to implement these hardening changes?”

Yes, **with one nuance**: implement them through a **single shared writer for `last_tool_error.json`**, not by adding more writers. The highest leverage changes are:

- Remove or unify the `_write_error_signal` branch in `PostToolUse_router.py`.
- Add `PostToolUseFailure(Bash)` and move failure capture logic there.
- Add success cleanup and dual timestamps.
- Switch to line-based truncation + expire-on-write.

FACT: Your current description of the wiring and the dual-writer issue is accurate given the `settings.json` block.[^11_2][^11_1]
FACT: Claude Code docs now explicitly distinguish `PostToolUse` and `PostToolUseFailure`, so using both is structurally correct.[^11_8][^11_7][^11_1]
SPECULATION, high confidence: consolidating to one writer and using `PostToolUseFailure` for capture will remove ambiguity and make this pattern easier to extend to other tools (MCP, Git, etc.) later.[^11_1][^11_4]

If you paste the current `_write_error_signal` function from `PostToolUse_router.py` and the writer in `PostToolUse.py`, the next step can be a concrete diff that unifies them into a shared helper used only from the new `capture_tool_failure.py`.

<div align="center">⁂</div>

[^11_1]: https://code.claude.com/docs/en/hooks

[^11_2]: https://www.mintlify.com/affaan-m/everything-claude-code/hooks/overview

[^11_3]: https://www.heyuan110.com/posts/ai/2026-02-18-claude-code-hooks-guide/

[^11_4]: https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3

[^11_5]: https://github.com/anthropics/claude-code/issues/32407

[^11_6]: https://code.claude.com/docs/en/hooks-guide

[^11_7]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^11_8]: https://code.claude.com/docs/es/hooks


---

# response:

"
● [ASUM] [ANCH] [INV]

Assumption Check: I assume the implementation proceeds with shared-writer pattern, PostToolUseFailure registration, and
full hardening. The scope is capture_tool_failure.py creation + settings.json update + PostToolUse_router.py cleanup +
PostToolUse.py cleanup + full verification.

Outcome Anchor: Exactly one module writes last_tool_error.json on failure (capture_tool_failure.py, registered on
PostToolUseFailure). No more dual-writer racing. The enriched signal includes dual timestamps, line-based truncation,
session_id, and expire-on-write hygiene.

Inversion Check: Risk: removing _write_error_signal from router breaks competence_injector (which also reads the signal).
Mitigation: verify all consumers of last_tool_error.json before removing the router's write.

Let me first audit every consumer of last_tool_error.json before changing anything.

Searched for 1 pattern, read 2 files (ctrl+o to expand)

● Both writers confirmed. Here's the comparison:

┌────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────────┐
│                │              PostToolUse.py (lines 170-199)              │ PostToolUse_router.py (lines 391-440) │
├────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ Timestamp      │ time.monotonic()                                         │ time.time()                           │
├────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ Fields         │ timestamp, tool_name, command, exit_code, stderr, stdout │ timestamp, tool_name, command (bare)  │
├────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ Truncation     │ chars ([-800:], [-400:])                                 │ none                                  │
├────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ Success action │ unlink(missing_ok=True)                                  │ unlink(missing_ok=True)               │
└────────────────┴──────────────────────────────────────────────────────────┴───────────────────────────────────────┘

The conflict: PostToolUse_router.py runs for Edit|Write tools, PostToolUse.py runs for all tools via .*. If an Edit
triggers the router's bare write after PostToolUse.py wrote the enriched record, the injector reads the bare one.
Different clocks also break TTL.

Minimal fix — single shared writer:

1. Create __lib/write_tool_error_signal.py — one function, used by both hooks
2. PostToolUse_router.py — delegate to shared helper (stops writing directly)
3. PostToolUse.py — delegate to shared helper (stops writing directly)
4. PostToolUseFailure registration in settings.json with capture_tool_failure.py

The shared writer gets:

- Dual timestamps: monotonic_written_at + wall_written_at
- Line-based truncation: last 40 lines stderr, last 20 lines stdout
- Expire on write: delete stale signals before writing new ones
- Full enrichment: all fields, no bare writes

Want me to implement this?"

Yes — **this response is good**, and the proposed implementation direction is mostly correct. The strongest part is the shift from “which hook should own this?” to “there must be exactly one writer for `last_tool_error.json`.” That is the real systems problem here.[^12_1][^12_2]

## What is correct

The shared-writer pattern is the right architectural move because duplicate state writers are a bigger reliability risk than imperfect event routing. Claude Code supports multiple hooks on the same lifecycle event, and they run sequentially, so a shared helper that standardizes schema, truncation, TTL hygiene, and timestamps is much safer than letting two modules independently serialize the same file.[^12_3][^12_1]

Adding `PostToolUseFailure` is also the right direction because current docs explicitly distinguish it from `PostToolUse`, with success vs failure separated by event name rather than just payload shape.  So even if your current setup incidentally works by filtering inside `PostToolUse`, adding the failure-specific registration makes the structure match the documented contract.[^12_4][^12_1]

## What I would change

I would challenge one point: **do not keep both hooks writing the same file through a shared helper unless both truly need write authority**. The response says “used by both hooks,” but if both modules can still call the same writer for the same logical event, you still have two authorities, just with a nicer implementation. That reduces schema drift, but it does not eliminate ordering risk.[^12_2]

The better pattern is:

- One module owns **failure writes**.
- One module owns **success cleanup/resolution**.
- Everyone else is read-only.

So I would refine the plan to:

1. `capture_tool_failure.py` on `PostToolUseFailure(Bash)` → write enriched failure signal.
2. A success-path resolver on `PostToolUse(Bash)` → mark resolved/delete.
3. `PostToolUse_router.py` and `PostToolUse.py` become read-only with respect to `last_tool_error.json`, unless one of them is explicitly repurposed as the success resolver.[^12_1][^12_4]

That is a cleaner authority model than “shared helper used by both hooks.”[^12_2]

## Specific review of the proposed bullets

| Proposal | Verdict | Why |
| :-- | :-- | :-- |
| `__lib/write_tool_error_signal.py` | Good | Centralizes schema and TTL logic. [^12_2] |
| Router delegates to shared helper | Risky | Better to remove router write authority entirely unless it is the designated resolver. [^12_1] |
| `PostToolUse.py` delegates to shared helper | Risky | Same issue: helper reuse is fine, dual authority is not. [^12_2] |
| Add `PostToolUseFailure` registration | Correct | Aligns with current docs and simplifies reasoning. [^12_1][^12_4] |
| Dual timestamps | Correct | Safer across restarts than monotonic only. [^12_4] |
| Line-based truncation | Correct | Preserves stack-trace structure better than char slicing. [^12_4] |
| Expire on write | Correct | Prevents long-session stale state buildup. [^12_5] |

## Better implementation shape

The response should be nudged toward this exact ownership model:

- `__lib/tool_error_signal.py`
    - `write_failure_signal(...)`
    - `resolve_failure_signal(...)`
    - `read_failure_signal(...)`
    - `cleanup_stale_signal(...)`
- `capture_tool_failure.py`
    - registered on `PostToolUseFailure`
    - only calls `write_failure_signal(...)`
- `resolve_tool_failure.py`
    - registered on `PostToolUse` with matcher `Bash`
    - only calls `resolve_failure_signal(...)` when the command succeeded
- `failure_context_injector.py`
    - read-only
    - injects unresolved evidence on `UserPromptSubmit`

This gives you one writer for failure, one resolver for success, and a shared library for file semantics. That is the cleanest version of what the response is reaching for.[^12_1][^12_2]

## Recommended answer to send back

A tighter, more correct reply would be:

> Yes — implement it, but with one refinement: use a shared helper library, not a shared writer authority. `capture_tool_failure.py` should be the only module that writes failure signals, registered on `PostToolUseFailure(Bash)`. A separate success-path resolver should clear or mark resolved on `PostToolUse(Bash)`. `PostToolUse_router.py` and `PostToolUse.py` should stop writing `last_tool_error.json` directly. Keep dual timestamps, line-based truncation, session_id, and expire-on-write.[^12_4][^12_2][^12_1]

## Bottom assessment

FACT: The diagnosis of the dual-writer bug is solid.[^12_2]
FACT: Adding `PostToolUseFailure` is structurally correct under current Claude Code docs.[^12_4][^12_1]
FACT: The only meaningful design risk left is preserving multiple write authorities after introducing the helper.[^12_2]
SPECULATION, high confidence: if you enforce single-authority ownership now, this pattern will stay stable as you add other evidence injectors later.[^12_1][^12_2]

Want a concrete target `settings.json` block and module split for that ownership model?
<span style="display:none">[^12_10][^12_11][^12_6][^12_7][^12_8][^12_9]</span>

<div align="center">⁂</div>

[^12_1]: https://code.claude.com/docs/en/hooks

[^12_2]: https://mcpmarket.com/tools/skills/hook-deduplication-guide

[^12_3]: https://ericgrill.com/blog/claude-code-hooks

[^12_4]: https://code.claude.com/docs/en/hooks-guide

[^12_5]: https://github.com/anthropics/claude-code/issues/32407

[^12_6]: https://www.reddit.com/r/ClaudeAI/comments/1phausw/claude_code_hooks_tutorial_posttooluse_hook_to/

[^12_7]: https://github.com/ChrisWiles/claude-code-showcase/blob/main/.claude/settings.json

[^12_8]: https://github.com/ruvnet/ruflo/issues/1084

[^12_9]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^12_10]: https://www.linkedin.com/posts/ronald-t-parker_claudecode-agenticengineering-aicoding-activity-7422254459478790146-pTrV

[^12_11]: https://www.youtube.com/watch?v=jw0PV-nyE6g


---

# what prompt should we give the target llm?

Use a short **behavioral contract**, not a wall of prose. You want three things: (1) treat the signal as hard evidence, (2) prefer root-cause plans that explain it, (3) avoid looping if it’s stale or already resolved.

Here’s a good prompt block to inject (via `UserPromptSubmit.additionalContext` or similar):

```txt
You have an error signal from the previous tool run.

If there is an unresolved failure signal, treat it as primary evidence:
- Assume the failure is real and current unless the user or new evidence proves otherwise.
- Prefer explanations and plans that directly explain this failure over workarounds.

Error signal format:
- tool: <tool_name>
- exit code: <exit_code>
- command: <command>
- stderr (tail): <stderr_tail>
- stdout (tail, optional): <stdout_tail>

When planning your next steps:
1. Start by restating what this failure is telling you about the system.
2. Propose a plan that explicitly aims to:
   - locate the code or config responsible, and
   - change it in a way that would prevent this exact failure.
3. Avoid “cosmetic” or unrelated changes that do not plausibly fix this failure.
4. If you believe the failure is stale or already resolved, say so explicitly and explain why.

Do NOT:
- Ignore the error signal.
- Treat a passing test or absence of an error message as proof the underlying issue is fixed without checking the relevant code path.
- Jump to a workaround (e.g. suppressing checks, disabling tools) unless you clearly explain why it is acceptable and temporary.
```

