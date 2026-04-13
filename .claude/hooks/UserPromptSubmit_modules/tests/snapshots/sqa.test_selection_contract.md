## Test Selection Contract

Choose the smallest sufficient test mix for the target and layer:

- Use **unit tests** for pure logic, local invariants, and deterministic transforms.
- Use **regression tests** for exact bug paths, restored behavior, and fixes that must not recur.
- Use **integration tests** for boundaries, state, persistence, hooks, cross-module flows, or I/O that unit tests can mock away.
- Use **smoke proofs** for hooks, routers, resumable workflows, and workflow-infrastructure boundaries.
- Use **snapshot tests** for rendered reports, generated docs, hook-injected text, and skill bodies; use unit tests for the logic that produces that output.
- If a defect can be falsified by a smaller layer, do not jump to a larger one.
- If a defect crosses a boundary or state, do not stop at unit tests.
- Before presenting a plan, say which layer proves what and what a lower layer would miss.
