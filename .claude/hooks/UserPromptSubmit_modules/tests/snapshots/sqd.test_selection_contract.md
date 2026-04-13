## Test Selection Contract

Choose the smallest sufficient test mix for the target:

- Use **unit tests** for pure logic, local invariants, and deterministic transforms.
- Use **regression tests** for exact bug paths, restored behavior, and fixes that must not recur.
- Use **integration tests** for boundaries, state, persistence, hooks, cross-module flows, or I/O that unit tests can mock away.
- Use **smoke proofs** for hooks, routers, resumable workflows, and workflow-infrastructure boundaries.
- Use **snapshot tests** for rendered quality reports, generated docs, hook-injected text, and skill bodies; use unit tests for the logic that produces that output.
- If the issue is mostly local logic, start at unit level and only escalate when a boundary exists.
- If the issue crosses a boundary or state, do not stop at unit tests.
- Before rendering advice, say which layer proves what and what a lower layer would miss.
