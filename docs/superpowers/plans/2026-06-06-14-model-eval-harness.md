# 14-Model Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable 14-model benchmark harness that scores reasoning/architecture and coding separately, then writes a stable leaderboard artifact for routing decisions.

**Architecture:** Keep the existing `bf_agent.py` transport and compare code intact. Add a small benchmark suite module that owns case definitions, scoring, aggregation, and artifact writing. Reuse `run_domain_benchmark()` for the reasoning lane, but make the new harness call it explicitly and keep its outputs separate from the coding lane, which must run against isolated fixtures with hidden tests and `run_code()`.

**Tech Stack:** Python, pytest, existing `bf_agent.py` runtime, plugin-owned `skills/ai-api` package, temp workspaces, JSON/Markdown artifacts.

---

### Task 1: Add a benchmark suite module for lane-level orchestration

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/benchmark_suite.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_benchmark_suite.py`

- [ ] **Step 1: Write the failing tests for suite metadata and aggregation**

```python
def test_suite_builds_two_lanes_and_preserves_model_order():
    suite = build_model_eval_suite(models=["M3", "qwen3-coder", "moonshotai/kimi-k2.6"])
    assert [lane.name for lane in suite.lanes] == ["reasoning", "coding"]
    assert suite.models == ["M3", "qwen3-coder", "moonshotai/kimi-k2.6"]


def test_suite_aggregates_lane_scores_separately():
    summary = aggregate_suite_results([
        {"model": "M3", "lane": "reasoning", "score": 0.9},
        {"model": "M3", "lane": "coding", "score": 0.4},
    ])
    assert summary["models"]["M3"]["reasoning_score"] == 0.9
    assert summary["models"]["M3"]["coding_score"] == 0.4
```

- [ ] **Step 2: Run the focused test file and confirm it fails before implementation**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: FAIL because `benchmark_suite.py` and the suite helpers do not exist yet.

- [ ] **Step 3: Implement the suite object, result schema, and aggregation helpers**

```python
def build_model_eval_suite(models: list[str]) -> BenchmarkSuite:
    return BenchmarkSuite(
        models=list(models),
        lanes=[
            BenchmarkLane(name="reasoning"),
            BenchmarkLane(name="coding"),
        ],
    )

def aggregate_suite_results(results: list[dict]) -> dict:
    summary: dict[str, dict] = {"models": {}}
    for result in results:
        model_bucket = summary["models"].setdefault(
            result["model"],
            {"reasoning_score": None, "coding_score": None, "cases": []},
        )
        model_bucket["cases"].append(result)
        if result["lane"] == "reasoning":
            model_bucket["reasoning_score"] = result["score"]
        elif result["lane"] == "coding":
            model_bucket["coding_score"] = result["score"]
    return summary

def write_suite_artifacts(output_dir: Path, summary: dict, results: list[dict]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "model-eval-suite.json"
    markdown_path = output_dir / "model-eval-suite.md"
    json_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
    markdown_path.write_text(render_suite_markdown(summary, results), encoding="utf-8")
    return json_path, markdown_path
```

- [ ] **Step 4: Re-run the focused tests and verify the new module is importable from `bf_agent.py`**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: PASS with stable lane separation and artifact paths under `.data/ai-api/benchmarks`.

### Task 2: Wire the reasoning lane to the existing domain benchmark runner

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/benchmark_suite.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_benchmark_suite.py`

- [ ] **Step 1: Add failing coverage for the reasoning lane calling `run_domain_benchmark()`**

```python
def test_reasoning_lane_uses_domain_benchmark_runner(monkeypatch):
    calls = []

    def fake_run_domain_benchmark(domain, models=None, route="auto", max_tokens=None, cases=None, persist=True):
        calls.append((domain, tuple(models or []), route, persist))
        return {"ok": True, "domain": domain, "models": models or [], "summary": []}

    monkeypatch.setattr(bf_agent, "run_domain_benchmark", fake_run_domain_benchmark)
    suite = build_model_eval_suite(models=["M3"])
    result = suite.run_reasoning_lane()
    assert calls[0][0] in {"architecture", "planning"}
    assert result["ok"] is True
```

- [ ] **Step 2: Run the tests to verify the lane is not yet wired**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: FAIL until the reasoning lane forwards the right cases and model list.

- [ ] **Step 3: Implement the reasoning lane as a thin wrapper over the existing benchmark cases**

```python
reasoning_domains = ["architecture", "planning"]
for domain in reasoning_domains:
    lane_results[domain] = bf_agent.run_domain_benchmark(
        domain,
        models=models,
        route=route,
        cases=cases_by_domain[domain],
        persist=True,
    )
```

- [ ] **Step 4: Re-run the tests and verify the lane results stay separate from the coding lane**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: PASS with per-domain reasoning outputs and no synthetic merge into a single benchmark score.

### Task 3: Add the coding lane with isolated fixtures and hidden tests

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/fixtures/model_eval/basic_bug/`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/fixtures/model_eval/basic_bug/tests/test_basic_bug.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/fixtures/model_eval/basic_bug/target.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/fixtures/model_eval/portability_fix/`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/fixtures/model_eval/portability_fix/tests/test_portability_fix.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/benchmark_suite.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_benchmark_suite.py`

- [ ] **Step 1: Write the failing coding-lane tests for fixture isolation and hidden test execution**

```python
def test_coding_lane_copies_fixture_to_temp_workspace(monkeypatch, tmp_path):
    suite = build_model_eval_suite(models=["M3"])
    copied = []

    def fake_copy_fixture(*args, **kwargs):
        copied.append(True)
        return tmp_path / "workspace"

    monkeypatch.setattr(suite, "_copy_fixture_to_workspace", fake_copy_fixture)
    result = suite.run_coding_lane()
    assert copied
    assert result["lane"] == "coding"


def test_coding_lane_scores_by_test_success(monkeypatch):
    suite = build_model_eval_suite(models=["M3"])
    monkeypatch.setattr(suite, "_run_hidden_tests", lambda *args, **kwargs: {"passed": True, "score": 1.0})
    result = suite.run_coding_lane()
    assert result["summary"][0]["coding_score"] == 1.0
```

- [ ] **Step 2: Run the focused tests and confirm the coding lane is still missing**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: FAIL until the fixture copy, hidden test invocation, and scoring exist.

- [ ] **Step 3: Implement isolated fixture copying, `run_code()` execution, and hidden test scoring**

```python
def _copy_fixture_to_workspace(self, fixture_path: Path, temp_root: Path) -> Path:
    workspace = temp_root / fixture_path.name
    shutil.copytree(fixture_path, workspace)
    return workspace

def _run_hidden_tests(self, workspace: Path, test_command: list[str]) -> dict:
    completed = subprocess.run(test_command, cwd=workspace, capture_output=True, text=True)
    return {
        "passed": completed.returncode == 0,
        "score": 1.0 if completed.returncode == 0 else 0.0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }

def run_coding_lane(self) -> dict:
    results = []
    for model in self.models:
        workspace = self._copy_fixture_to_workspace(self.primary_fixture_path, self.temp_root / model)
        patch_result = bf_agent.run_code(self.primary_prompt, model=model, route=self.route)
        test_result = self._run_hidden_tests(workspace, self.test_command)
        results.append({
            "model": model,
            "lane": "coding",
            "score": test_result["score"],
            "tests_passed": test_result["passed"],
            "patch": patch_result,
        })
    return {"lane": "coding", "results": results, "summary": aggregate_suite_results(results)}
```

- [ ] **Step 4: Add the smallest fixture that proves the scoring path works end to end**

```python
def answer():
    return 41
```

and a hidden test that expects `42` after the model patches it.

- [ ] **Step 5: Re-run the test file and verify coding results are execution-backed**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: PASS with a failed hidden test on the unmodified fixture and a passing score after the model-generated patch.

### Task 4: Add a runner script and document the benchmark entrypoint

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/scripts/run_model_eval_suite.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/bf_agent.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_benchmark_suite.py`

- [ ] **Step 1: Write the failing test for the script entrypoint**

```python
def test_runner_emits_json_and_markdown_paths(tmp_path, monkeypatch):
    class FakeSuite:
        def __init__(self, models):
            self.models = models

        def run(self, output_dir):
            json_path = output_dir / "model-eval-suite.json"
            markdown_path = output_dir / "model-eval-suite.md"
            json_path.write_text("{}", encoding="utf-8")
            markdown_path.write_text("# suite", encoding="utf-8")
            return {"json_path": json_path, "markdown_path": markdown_path}

    monkeypatch.setattr(
        "benchmark_suite.build_model_eval_suite",
        lambda models: FakeSuite(models=models),
    )
    result = run_model_eval_suite(models=["M3"], output_dir=tmp_path)
    assert result["json_path"].exists()
    assert result["markdown_path"].exists()
```

- [ ] **Step 2: Run the test to verify the entrypoint does not exist yet**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: FAIL before the script wraps the suite and writes artifacts.

- [ ] **Step 3: Add the script wrapper and skill documentation**

```python
from benchmark_suite import run_model_eval_suite

if __name__ == "__main__":
    run_model_eval_suite()
```

Update the skill doc to explain:
- the two lanes
- the 14-model target list
- the artifact location
- how to run the benchmark locally

- [ ] **Step 4: Run the suite tests plus a smoke invocation of the runner**

Run:
`python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -q`
Expected: PASS

Run:
`python P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py --help`
Expected: shows the benchmark runner usage without importing the whole compare stack.

---

### Task 5: Validate the full 14-model path on a small sample first

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/tests/test_benchmark_suite.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-ai-api/skills/ai-api/benchmark_suite.py`

- [ ] **Step 1: Add a smoke test that runs 2 models across both lanes**

```python
def test_small_smoke_run_survives_one_failed_case(monkeypatch):
    suite = build_model_eval_suite(models=["M3", "moonshotai/kimi-k2.6"])

    monkeypatch.setattr(suite, "run_reasoning_lane", lambda: {"lane": "reasoning", "results": [{"model": "M3", "lane": "reasoning", "score": 0.8}]})
    monkeypatch.setattr(suite, "run_coding_lane", lambda: {"lane": "coding", "results": [{"model": "M3", "lane": "coding", "score": 0.0, "tests_passed": False}]})

    result = suite.run()
    assert result["summary"]["models"]["M3"]["reasoning_score"] == 0.8
    assert result["summary"]["models"]["M3"]["coding_score"] == 0.0
```

- [ ] **Step 2: Run the smoke test and verify partial failure does not abort the suite**

Run: `python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py -k smoke -v`
Expected: PASS with one failing case recorded in the artifact and the rest of the suite continuing.

- [ ] **Step 3: Expand the configured model list to all 14 OpenCode Go models**

```python
DEFAULT_EVAL_MODELS = [
    "opencode-go/glm-5",
    "opencode-go/glm-5.1",
    "opencode-go/kimi-k2.5",
    "opencode-go/kimi-k2.6",
    "opencode-go/mimo-v2.5",
    "opencode-go/mimo-v2.5-pro",
    "opencode-go/minimax-m2.5",
    "opencode-go/minimax-m2.7",
    "opencode-go/minimax-m3",
    "opencode-go/qwen3.6-plus",
    "opencode-go/qwen3.7-plus",
    "opencode-go/qwen3.7-max",
    "opencode-go/deepseek-v4-pro",
    "opencode-go/deepseek-v4-flash",
]

def test_default_eval_model_list_has_fourteen_models():
    assert len(DEFAULT_EVAL_MODELS) == 14
    assert DEFAULT_EVAL_MODELS[0] == "opencode-go/glm-5"
    assert DEFAULT_EVAL_MODELS[-1] == "opencode-go/deepseek-v4-flash"
```

- [ ] **Step 4: Run the full suite and inspect the generated leaderboard artifact**

Run: `python P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py`
Expected: JSON and Markdown artifacts written under `.data/ai-api/benchmarks`, with separate reasoning and coding ranks.
