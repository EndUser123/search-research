# go — SIGNATURE TOC

**Files:** 10 py, 4 sh, 25 json, 8 md


## FILE INDEX

  scripts\go_safe.py
  scripts\init_go_run.py
  scripts\loop-check.py
  scripts\pr-artifacts.py
  scripts\review-passes.py
  scripts\select-task.py
  scripts\validate_go_contracts.py
  scripts\verify-task.py
  scripts\write_dispatch_result.py
  tests\test_go_safe.py
  go-safe.sh
  ralph-go-loop.sh
  ralph-loop.sh
  scripts\go-safe.sh
  active-plan.json
  artifact-proof.json
  evals\2026-04-21_151727\logs\improve_iter_1.json
  evals\2026-04-21_151727\logs\improve_iter_2.json
  evals\2026-04-21_151727\logs\improve_iter_3.json
  evals\2026-04-21_151727\logs\improve_iter_4.json
  evals\2026-04-21_151727\results.json
  evals\evals.json
  examples\dispatch-decision_example.json
  examples\dispatch-result_example.json
  examples\run_example.json
  examples\selected-task_example.json
  schemas\active-task.schema.json
  schemas\block-state.schema.json
  schemas\code-result.schema.json
  schemas\dispatch-decision.schema.json
  schemas\dispatch-result.schema.json
  schemas\pr-ready.schema.json
  schemas\run-status.schema.json
  schemas\run.schema.json
  schemas\selected-task.schema.json
  schemas\task-result.schema.json
  schemas\tasks-file.schema.json
  schemas\verification-result.schema.json
  workflow-model.json
  .aid\go\go_full.md
  .aid\go\go_sig.md
  GO-CONFORMANCE.md
  GO-QUICK-REFERENCE.md
  IMPLEMENTATION-GUIDE.md
  proof-packet.md
  ROUTING.md
  SKILL.md

## SIGNATURE TOC


### scripts\go_safe.py

  def now_iso() -> str
  def write_json(path: Path, payload: dict) -> None
  def write_text(path: Path, content: str) -> None
  def run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]
  def die(error: str, artifact_dir: Path, run_id: str) -> None
  def require_file(path: Path, artifact_dir: Path, run_id: str) -> None
  def infer_args() -> tuple[str, str, str, str]
  def main() -> int

### scripts\init_go_run.py

  def now_iso() -> str
  def write_json(path: Path, payload: dict[str, Any]) -> None
  def write_text(path: Path, content: str) -> None
  def run_git(args: list[str], root_dir: Path) -> str
  class TaskCandidate
  def infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]
  def parse_plan_md(plan_path: Path) -> list[TaskCandidate]
  def parse_args() -> argparse.Namespace
  def build_explicit_task(args: argparse.Namespace) -> TaskCandidate
  def main() -> int

### scripts\loop-check.py

  # no functions/classes

### scripts\pr-artifacts.py

  # no functions/classes

### scripts\review-passes.py

  # no functions/classes

### scripts\select-task.py

  # no functions/classes

### scripts\validate_go_contracts.py

  def load_json(path: Path) -> Any
  def load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]
  def infer_schema_key(file_path: Path) -> str | None
  def validate_file(file_path: Path, schemas: dict[str, dict[str, Any]]) -> tuple[bool, str]
  def validate_directory(artifact_dir: Path, schemas: dict[str, dict[str, Any]]) -> int
  def main() -> int

### scripts\verify-task.py

  # no functions/classes

### scripts\write_dispatch_result.py

  def now_iso() -> str
  def update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None) -> None
  def update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str) -> None
  def emit_promise(final_status: str) -> None
  def main() -> int

### tests\test_go_safe.py

  def test_go_safe_importable()
  def test_go_safe_exit_1_when_invalid_args()

## SCHEMAS

  active-plan.json
  artifact-proof.json
  evals\2026-04-21_151727\logs\improve_iter_1.json
  evals\2026-04-21_151727\logs\improve_iter_2.json
  evals\2026-04-21_151727\logs\improve_iter_3.json
  evals\2026-04-21_151727\logs\improve_iter_4.json
  evals\2026-04-21_151727\results.json
  evals\evals.json
  examples\dispatch-decision_example.json
  examples\dispatch-result_example.json
  examples\run_example.json
  examples\selected-task_example.json
  schemas\active-task.schema.json
  schemas\block-state.schema.json
  schemas\code-result.schema.json
  schemas\dispatch-decision.schema.json
  schemas\dispatch-result.schema.json
  schemas\pr-ready.schema.json
  schemas\run-status.schema.json
  schemas\run.schema.json
  schemas\selected-task.schema.json
  schemas\task-result.schema.json
  schemas\tasks-file.schema.json
  schemas\verification-result.schema.json
  workflow-model.json