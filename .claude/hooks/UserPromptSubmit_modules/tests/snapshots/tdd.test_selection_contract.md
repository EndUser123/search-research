## Test Selection Contract

Choose the smallest sufficient test mix before writing assertions:

- Use **unit tests** for pure logic, deterministic transforms, and local contracts that do not need I/O or shared state.
- Use **regression tests** for every bug fix or restored behavior. Reproduce the exact failure path first, then prove that same path no longer fails.
- Use **integration tests** when behavior crosses modules, hooks, state, persistence, replay/resume, compaction, filesystem, or other I/O boundaries.
- Use a **real smoke proof** for hooks, routers, or resumable workflows so mocks cannot fake success.
- Use **snapshot tests** for rendered output, generated docs, hook-injected text, and skill bodies; use unit tests for the logic that chooses or computes that output.
- Do not add integration tests when a unit test can prove the same contract.
- Do not stop at unit tests when the defect lives at a boundary, through state, or across processes.
- Before locking the plan, say which layer proves what and what a lower layer would miss.
