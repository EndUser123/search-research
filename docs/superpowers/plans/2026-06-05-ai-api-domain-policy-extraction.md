# ai-api Domain Policy Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the shared prompt/domain policy out of `bf_agent.py`, add `/ai-cli`-compatible task aliases to `ai-api`, and keep all existing behavior stable under regression tests.

**Architecture:** Move the prompt/domain profile logic into a focused helper module so `bf_agent.py` stops owning policy tables, prompt contracts, and domain inference. Keep transport, compare orchestration, validation, and benchmarking in `bf_agent.py` for now. Add `/ai-cli` task aliases as domain normalization aliases so `ai-api` can accept the same task vocabulary without duplicating domain profiles.

**Tech Stack:** Python, pytest, existing `bf_agent.py` runtime, plugin-owned `skills/ai-api` package.

---

### Task 1: Extract prompt/domain policy helpers

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/prompt_policy.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`

- [ ] **Step 1: Add regression coverage for prompt/domain policy behavior**

```python
def test_domain_profile_aliases_map_ai_cli_task_names():
    assert bf_agent._normalize_domain_name("code_review") == "code"
    assert bf_agent._normalize_domain_name("debugging") == "code"
    assert bf_agent._normalize_domain_name("documentation") == "general"
```

- [ ] **Step 2: Run the focused test to verify it fails before extraction**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -k domain_profile_aliases_map_ai_cli_task_names -v`
Expected: FAIL because the alias coverage does not yet exist in the extracted policy module.

- [ ] **Step 3: Move the prompt/domain policy tables and helpers into `prompt_policy.py`**

```python
from prompt_policy import (
    DomainProfile,
    WorkerRole,
    _DOMAIN_PROFILES,
    _MODE_PROMPT_CONTRACTS,
    _build_worker_system_prompt,
    _infer_domain_from_prompt,
    _normalize_domain_name,
    _prompt_contract_for_mode,
    _resolve_domain_profile,
    _role_prompt,
    system_prompt_for_mode,
)
```

- [ ] **Step 4: Run the focused test and the full `bf_agent` test file**

Run:
`python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -q`
Expected: PASS with the extracted module preserving the same prompt behavior.

### Task 2: Add /ai-cli task aliases to the ai-api domain adapter

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/prompt_policy.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`

- [ ] **Step 1: Extend domain normalization so ai-cli task names map cleanly**

```python
aliases = {
    "code_review": "code",
    "code_generation": "code",
    "debug": "code",
    "debugging": "code",
    "refactor": "code",
    "testing": "code",
    "documentation": "general",
    "evaluation": "general",
    "architecture_review": "architecture",
    "system_design": "architecture",
    "planning": "planning",
    "plan": "planning",
}
```

- [ ] **Step 2: Update the skill text so the supported domain/task vocabulary is explicit**

```markdown
`ai-api` accepts both the native domains (`code`, `architecture`, `planning`, `general`) and `/ai-cli`-style task aliases (`code_review`, `debugging`, `refactor`, `testing`, `documentation`, `evaluation`) through the same domain adapter.
```

- [ ] **Step 3: Add tests proving the aliases resolve to the expected domain profile**

```python
def test_ai_cli_task_aliases_resolve_to_expected_domains():
    assert bf_agent._normalize_domain_name("code_review") == "code"
    assert bf_agent._normalize_domain_name("debugging") == "code"
    assert bf_agent._normalize_domain_name("planning") == "planning"
    assert bf_agent._normalize_domain_name("documentation") == "general"
```

- [ ] **Step 4: Run the full plugin test file again**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -q`
Expected: PASS with the alias coverage in place.

### Task 3: Verify the refactor is no-loss

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_bf_agent.py`

- [ ] **Step 1: Add one regression that exercises `run_compare()` with a domain alias**

```python
def test_run_compare_accepts_ai_cli_task_domain_alias(monkeypatch):
    result = bf_agent.run_compare("review the plugin", models=["M3"], domain="code_review")
    assert result["domain"] == "code"
```

- [ ] **Step 2: Run the comparison tests and confirm the public result shape is unchanged**

Run:
`python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -q`
Expected: PASS, and `run_simple`, `run_compare`, and `run_code` still return the same top-level fields.

- [ ] **Step 3: Keep the extraction no-loss by not removing transport, compare, benchmark, or code-mode behavior**

```text
Preserve: direct routing, Bifrost routing, compare fan-out, critique, local validation, benchmark registry, and code-mode tool loop.
Remove only the duplicated policy definitions after the new module is proven equivalent.
```

