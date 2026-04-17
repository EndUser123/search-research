# Plugin Agent Registry

> **Single source of truth** for valid `plugin:agent` subagent_type strings.
> Referenced by: `cco`, `simplifier`, any skill that spawns agents via the Task tool.
> Last verified: 2026-03-14

## ⚠️ Critical Rules

1. **Never invent agent names.** Every valid string is in the table below.
2. **Syntax is `plugin-name:agent-name`** — derived from the `.md` filename inside the plugin's `agents/` directory.
3. **Single-agent plugins are not namespaces.** `code-simplifier` has exactly ONE agent (`code-simplifier:code-simplifier`). You cannot append `:efficiency-reviewer`, `:code-quality-reviewer`, etc.
4. **User agents use bare names.** Agents in `P:/.claude/agents/*.md` are invoked by filename only (e.g. `adversarial-performance`, `simplifier`). Never prefix them with a plugin namespace.

---

## Installed Plugin Agents

| `subagent_type` | Plugin | Purpose |
|---|---|---|
| `code-simplifier:code-simplifier` | code-simplifier | Code clarity, consistency, maintainability |
| `feature-dev:code-architect` | feature-dev | Feature architecture design |
| `feature-dev:code-explorer` | feature-dev | Deep codebase exploration and analysis |
| `feature-dev:code-reviewer` | feature-dev | Code review for correctness and standards |
| `pr-review-toolkit:code-reviewer` | pr-review-toolkit | PR-focused code review |
| `pr-review-toolkit:code-simplifier` | pr-review-toolkit | Code simplification in PR context |
| `pr-review-toolkit:comment-analyzer` | pr-review-toolkit | Analyze PR comments and discussions |
| `pr-review-toolkit:pr-test-analyzer` | pr-review-toolkit | Analyze test coverage in PRs |
| `pr-review-toolkit:silent-failure-hunter` | pr-review-toolkit | Find swallowed errors and silent failures |
| `pr-review-toolkit:type-design-analyzer` | pr-review-toolkit | Type system and interface design |
| `agent-sdk-dev:agent-sdk-verifier-py` | agent-sdk-dev | Verify Python agent SDK usage |
| `agent-sdk-dev:agent-sdk-verifier-ts` | agent-sdk-dev | Verify TypeScript agent SDK usage |
| `plugin-dev:agent-creator` | plugin-dev | Create new plugin agents |
| `plugin-dev:plugin-validator` | plugin-dev | Validate plugin structure |
| `plugin-dev:skill-reviewer` | plugin-dev | Review skill definitions |
| `claudit:audit-ecosystem` | claudit | Ecosystem-wide audit |
| `claudit:audit-global` | claudit | Global configuration audit |
| `claudit:audit-project` | claudit | Project-level audit |
| `claudit:research-core` | claudit | Core research tasks |
| `claudit:research-ecosystem` | claudit | Ecosystem research |
| `claudit:research-optimization` | claudit | Optimization research |

---

## User Agents (bare name, no namespace)

Scan live list: `ls P:/.claude/agents/*.md`

Key agents for code tasks:

| `subagent_type` | Purpose |
|---|---|
| `simplifier` | Language-agnostic code simplification (delegates Python to `python-simplifier`) |
| `python-simplifier` | Python 3.12+ simplification (ruff, type hints, modern patterns) |
| `adversarial-performance` | Performance bottleneck analysis |
| `adversarial-review` | Adversarial correctness review |
| `adversarial-quality` | Quality-focused adversarial review |
| `adversarial-security` | Security-focused adversarial review |
| `code-critic` | Critical code analysis |
| `architect` | Architecture review |
| `qa-engineer` | QA and test coverage |
| `rca-specialist` | Root cause analysis |
| `researcher` | General research |

---

## Task Type → Agent Selection

| Task Domain | Primary | Secondary |
|---|---|---|
| **Code Review** | `feature-dev:code-reviewer`, `pr-review-toolkit:code-reviewer` | `code-critic` |
| **Code Simplification** | `code-simplifier:code-simplifier`, `pr-review-toolkit:code-simplifier` | `feature-dev:code-reviewer` |
| **Architecture** | `feature-dev:code-architect`, `architect` | `feature-dev:code-explorer` |
| **Standards/Quality** | `qa-engineer`, `adversarial-quality` | `feature-dev:code-reviewer` |
| **Research/Analysis** | `researcher` | `feature-dev:code-explorer` |
| **Refactoring** | `code-simplifier:code-simplifier`, `pr-review-toolkit:code-simplifier` | `feature-dev:code-reviewer` |
| **Testing** | `tdd-test-writer`, `qa-engineer` | — |
| **Root Cause** | `code-critic`, `rca-specialist` | `feature-dev:code-explorer` |
| **Silent Failures** | `pr-review-toolkit:silent-failure-hunter` | `feature-dev:code-reviewer` |
| **Type Safety** | `pr-review-toolkit:type-design-analyzer` | `feature-dev:code-reviewer` |
| **Security** | `adversarial-security` | `feature-dev:code-reviewer` |

---

## Runtime Discovery

If plugins have been updated since this file was last edited, run:

```bash
find "C:/Users/brsth/.claude/plugins/cache" -name "*.md" -path "*/agents/*" \
  | sed 's|.*/cache/[^/]*/\([^/]*\)/[^/]*/agents/\([^.]*\)\.md|\1:\2|' \
  | sort -u | grep -v "^skill-creator\|^huggingface"
```

Then update the table above.
