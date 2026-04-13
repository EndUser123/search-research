### Test Selection Contract

Choose the smallest sufficient test mix for the change:

- **Unit tests** for pure logic, deterministic transforms, and local contracts.
- **Regression tests** for exact bug paths, restored behavior, and fixes that must not recur.
- **Integration tests** for boundaries, state, persistence, hooks, cross-module flows, or I/O that unit tests can mock away.
- **Smoke proofs** for hooks, routers, and resumable workflows where a mock could fake success.
- **Snapshot tests** for rendered output, generated docs, hook-injected text, and skill bodies; unit tests for the logic that produces that output.
- If the change is mostly local logic, start at unit level and only escalate when a boundary exists.
- If the change touches a boundary or state, do not stop at unit tests.
- If you are comparing plans, say which layer proves what and what a lower layer would miss.
