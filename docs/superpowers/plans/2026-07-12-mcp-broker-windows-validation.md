# MCP Broker Windows Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove whether `mcp-mux` can safely provide one shared MCP backend process for Claude Code, Codex, PI, and OpenCode on Windows before changing any real client configuration.

**Architecture:** Keep each client connected to a normal stdio MCP shim. Let the shim connect over the mcp-mux Windows named pipe to one broker, and let the broker own shared or per-session backend processes. First prove the transport and lifecycle with a fixture, then a real harmless MCP server, then isolated client configurations. Do not add mcp-broker control-plane features until the runtime passes the decision gate.

**Tech Stack:** Node.js 24, PowerShell 7, `mcp-mux` commit `f39e910`, Node test runner, Windows named pipes, temporary MCP configurations, one inspected stateless real MCP server, and one filesystem MCP server constrained to per-session temporary directories.

## Global Constraints

- No Docker.
- Do not modify Claude Code, Codex, PI, or OpenCode production configuration until the limited-integration gate passes.
- Use the pinned checkout `P:\tmp\mcp-broker-review\mcp-mux` at commit `f39e910`.
- Keep MCP diagnostics on stderr; stdout must contain only MCP protocol traffic.
- Never place API keys or secret values in repository files, test fixtures, command output, or logs.
- Shared mode is permitted only for stateless, harmless tools; browser, filesystem, database, project-stateful, and session-bound tools default to per-session.
- Every process-count claim must be derived from a PowerShell process snapshot or an equivalent captured artifact.
- Every run has a UUID `run_id` propagated into fixture environment/command lines and evidence filenames; never count unowned or pre-existing processes.
- Every failure must be classified as environment, protocol, lifecycle, security, or client compatibility.
- Preserve the current `cc-ccr` behavior; do not add automatic AgentGateway startup.
- Shared eligibility is initially restricted to MCP servers using tools/list and tools/call only; servers requiring server-to-client requests, roots, sampling, elicitation, subscriptions, progress, or cancellation remain per-session or disabled until separately proven.
- Broker/config identity must include more than the config path: candidate version, config content hash, and server-policy hash must be visible in status/evidence or integration is blocked.
- The named pipe must have a documented local-user security posture. If the Node implementation cannot establish an adequate ACL, credential-bearing shared servers remain prohibited and production readiness is blocked.

---

### Task 0: Inspect authority and protocol boundaries before writing tests

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\source-audit.md`
- Inspect: `P:\tmp\mcp-broker-review\mcp-mux\src\config.mjs`
- Inspect: `P:\tmp\mcp-broker-review\mcp-mux\src\shim.mjs`
- Inspect: `P:\tmp\mcp-broker-review\mcp-mux\src\broker.mjs`
- Inspect: `P:\tmp\mcp-broker-review\mcp-mux\src\server-manager.mjs`

**Interfaces:**
- Consumes: the read-only candidate at commit `f39e910`.
- Produces: a source-backed authority map and a go/no-go decision for the fixture design.

- [ ] **Step 1: Trace shim identity end to end**

Record that `shim.mjs` creates a UUID, sends it in `shim_hello`, includes it in `tool_call`, and that `server-manager.mjs` keys per-session instances by `serverName:shimId`. Record collision behavior, reconnect behavior, and whether identity is trusted or authenticated.

- [ ] **Step 2: Trace the supported MCP surface**

Record the handled paths for initialize, initialized, tools/list, tools/call, ping, notifications, cancellation, progress, roots, sampling, elicitation, and server-to-client requests. The current source contains `forward not implemented`; treat server-to-client request routing as unsupported unless implementation and tests change.

- [ ] **Step 3: Trace broker/config identity and startup collision behavior**

Record that the pipe hash is derived from the absolute config path, while config contents and candidate version are not part of the current pipe identity. Test or inspect what happens when two processes use the same config path with different contents. Record which first broker wins and how the second shim detects a mismatch.

- [ ] **Step 4: Trace named-pipe security**

Record the exact pipe name, user/session namespace, and whether `node:net.createServer().listen()` applies an explicit ACL in this implementation. Do not claim the pipe is secure merely because it is local. If ACL ownership cannot be established, mark credential-bearing shared-server integration blocked.

- [ ] **Step 5: Stop on an unbounded architecture gap**

Stop with `needs_fix` if the source and a focused runtime trace cannot establish identity ownership, broker/config collision behavior, or the supported shared protocol subset. Do not proceed to PID tests as if they proved safety.

---

### Task 0.5: Resolve broker startup ownership before broader validation

**Files:**
- Modify in a dedicated worktree only: `P:\tmp\mcp-broker-review\mcp-mux\src\shim.mjs`
- Modify in a dedicated worktree only if required: `P:\tmp\mcp-broker-review\mcp-mux\src\broker.mjs`
- Create in the validation worktree: `test\cold-start-ownership.test.mjs`
- Preserve evidence: `P:\tmp\mcp-broker-review\mcp-mux-validation\source-audit.md`

**Interfaces:**
- Consumes: Task 0 source audit and the external cold-start harness.
- Produces: one deterministic broker owner, protected PID/status metadata, and a focused regression test.

- [ ] **Step 1: Reproduce the race against the unmodified candidate**

Run the external cold-start test with two shims launched concurrently and capture the broker log. Expected failure evidence is a same-endpoint `EADDRINUSE` race or an equivalent ambiguous owner/status result.

- [ ] **Step 2: Choose the smallest ownership mechanism**

Compare a shim-side single-flight/start handshake with a broker-side lock/owner handshake. The mechanism must satisfy all of these invariants:

1. only one broker owns the endpoint;
2. a losing starter waits for and connects to the winner;
3. a losing starter cannot remove the winner's PID/status metadata;
4. stale metadata cannot block a clean start;
5. failure is bounded and visible to the client.

- [ ] **Step 3: Write the focused regression test first**

The test must start two shims at the same time against a unique config, assert one broker process and one endpoint owner, and fail if either broker reports a bind collision or the PID file disappears while the winner remains alive.

- [ ] **Step 4: Implement the minimal fix in an isolated worktree**

Do not change tool routing, MCP capability handling, server classification, or credential behavior in this task. Keep the fix limited to startup ownership and metadata cleanup.

- [ ] **Step 5: Verify the fix**

Run the focused cold-start regression three times consecutively, then run the existing candidate suite:

```powershell
node --test test/cold-start-ownership.test.mjs
npm test
```

Expected: each cold-start run has exactly one broker owner, no unowned duplicate, no PID metadata deletion by a loser, and the existing suite remains green. If not, report `needs_fix` and do not continue to real-server or client probes.

---

### Task 0.6: Bind broker ownership to configuration identity

**Files:**
- Modify in a dedicated worktree only: `src/config.mjs`, `src/shim.mjs`, and/or `src/broker.mjs`
- Create in the validation worktree: `test/config-identity.test.mjs`
- Preserve evidence: `P:\tmp\mcp-broker-review\mcp-mux-validation\source-audit.md`

**Interfaces:**
- Consumes: the startup-owned broker from Task 0.5.
- Produces: deterministic rejection or endpoint separation when config contents,
  policy, or candidate version differ for the same path/endpoint.

- [x] **Step 1: Preserve the failing collision probe**

Run the external config-collision probe against the fixed worktree. Expected current result is `silent_config_mismatch`; retain that result as the red test.

- [x] **Step 2: Choose the identity contract**

Bind the broker handshake/status to an identity containing at least the normalized config-content hash, candidate version, and server-policy hash. A mismatch must either use a distinct endpoint or return a visible refusal; it must not silently expose the first broker's tools.

- [x] **Step 3: Add same-path and same-endpoint regression cases**

Cover changed server names/commands, changed shared/per-session mode, changed candidate version, and unchanged config identity. Assert that unchanged identity reuses the broker and changed identity refuses or separates deterministically.

- [x] **Step 4: Verify collision behavior**

Run the focused identity test and the full candidate suite. Do not proceed to backend-death, real-server, or client tests until the collision probe no longer reports `silent_config_mismatch`.

**Evidence:** isolated commit `bfabe3b`; `npm test` reports 15 passed and 0
failed; the shared/per-session harness reports 2 passed and 0 failed; the
collision probe exits 0 with `rejected_or_distinct`. The focused identity
assertion is in `test/config.test.mjs`; the external live collision probe is
`P:\tmp\mcp-broker-review\mcp-mux-validation\config-collision-probe.mjs`.

**Remaining limitation:** the identity is conservative because it hashes raw
config bytes, and rejected shims may remain connected until their client closes
the session. Test this in the failure-recovery branch.

---

### Task 0.7: Validate broker and backend failure ownership

**Files:**
- Modify only the external validation harness under
  `P:\tmp\mcp-broker-review\mcp-mux-validation\`
- Preserve evidence in `source-audit.md` and `HANDOFF.md`

**Interfaces:**
- Consumes: isolated candidate commit `bfabe3b`.
- Produces: bounded evidence for broker death, backend death, reconnect,
  shutdown, cleanup, and stale PID/lock handling.

- [x] **Step 1: Kill the broker with two shims connected**
- [x] **Step 2: Kill a shared backend and observe bounded failure/restart**
- [x] **Step 3: Disconnect shims and verify idle shutdown has no orphans**
- [x] **Step 4: Record recovery evidence and classify any failure**

Stop before real-server or client probes if recovery is silent, unbounded,
leaves orphans, misidentifies ownership, or contaminates shim stdout.

**Evidence:** the first recovery run found an `EPERM` startup-lock race during
broker death. Commit `69b6b69` changed lock creation to a single atomic Windows
`writeFileSync(..., { flag: 'wx' })` operation. Two fresh full lifecycle runs
then passed 5/5, and `npm test` passed 15/15.

---

### Task 0.8: Validate one real harmless MCP server

**Files:**
- Modify only the external validation harness/config under
  `P:\tmp\mcp-broker-review\mcp-mux-validation\`
- Preserve package/version and evidence in `source-audit.md` and `HANDOFF.md`

**Interfaces:**
- Consumes: isolated candidate commit `69b6b69`.
- Produces: runtime evidence that the shared and lifecycle claims are not
  fixture-only.

- [x] **Step 1: Select a locally available or pinned real MCP server**
- [x] **Step 2: Run shared initialization, tools/list, and harmless calls**
- [x] **Step 3: Run disconnect/cleanup and record process evidence**
- [x] **Step 4: Classify remaining protocol/security limitations**

Do not install unpinned dependencies, use credentials, use Docker, or modify
client configuration in this task.

**Evidence:** the pinned local filesystem server (`2026.1.14`) initializes,
lists 14 tools, performs a read-only `get_file_info` call, and cleans up through
the broker. An earlier timeout was a validation-probe defect: missing
`jsonrpc: "2.0"` was tolerated by the fixture but rejected by the real SDK.

---

### Task 0.9: Validate adversarial protocol semantics

**Files:**
- Modify only the external validation harness under
  `P:\tmp\mcp-broker-review\mcp-mux-validation\`
- Preserve evidence in `source-audit.md` and `HANDOFF.md`

**Interfaces:**
- Consumes: isolated candidate commit `69b6b69` and the real-server harness.
- Produces: evidence for semantics beyond ordinary tools/list and tools/call.

- [ ] Notifications are not misrouted or silently duplicated
- [ ] Cancellation has bounded, visible behavior
- [x] Server-to-client requests are explicitly observed as unsupported with a bounded timeout
- [x] Error and capability fields are checked; backend `sampling` capability is not preserved

Stop before client probes if semantic behavior is silently lost or the
security/failure scope remains ambiguous. Current result: server-to-client
requests are bounded but unsupported; full MCP adoption remains blocked.

The next decision is whether to implement those semantics or define and enforce
a tools-only profile that rejects incompatible servers.

---

### Task 1: Freeze the candidate and create an isolated test workspace

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\README.md`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\config\shared-fixture.json`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\config\per-session-fixture.json`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\evidence\README.md`

**Interfaces:**
- Consumes: the pinned mcp-mux checkout at `P:\tmp\mcp-broker-review\mcp-mux`.
- Produces: a reproducible test root with no dependency on live client configuration.

- [ ] **Step 1: Record the candidate commit and runtime versions**

Run:

```powershell
git -C P:\tmp\mcp-broker-review\mcp-mux rev-parse HEAD
node --version
npm --version
pwsh --version
```

Expected: the commit resolves to `f39e910`; the version output is saved in the validation README.

- [ ] **Step 2: Run the unmodified candidate suite**

Run:

```powershell
npm test
```

Expected: `13 passed, 0 failed`. If this fails, stop with classification `environment` or `candidate regression`; do not begin new implementation.

- [ ] **Step 3: Define isolated config roots**

Use a unique UUID run directory under `P:\tmp\mcp-broker-review\mcp-mux-validation\runs\<run_id>`. Store only redacted config and captured process evidence there. The validation README must state that no production client config is read or written.

- [ ] **Step 4: Preserve reproducibility**

Keep the upstream checkout read-only. Create a dedicated worktree/branch from `f39e910` for committed validation tests, or keep all harness code in the validation root and invoke the candidate by absolute path. Record upstream commit, validation commit if any, clean-tree status, and lockfile status.

### Task 2: Add deterministic shared/per-session protocol fixtures

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\fixtures\mcp-test-server.mjs`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\windows-lifecycle.test.mjs`
- Modify: validation-only package/test harness files, never the read-only candidate checkout.

**Interfaces:**
- Consumes: mcp-mux stdio shim and `.mcp-mux.json` server definitions.
- Produces: test tools `get_instance_id`, `get_session_value`, and `set_session_value`; the fixture must write diagnostics only to stderr and use a unique PID-derived instance ID.

- [ ] **Step 1: Write the complete cold-start test**

The test must launch two independent shim child processes concurrently against the same shared config, send `initialize`, `tools/list`, and `tools/call`, and assert that both responses are valid JSON-RPC responses. Capture each child stdout and stderr separately.

Run:

```powershell
npm test -- --test-name-pattern="cold concurrent startup"
```

Expected: a failure caused by an unmet routing/lifecycle assertion, not a zero-test or missing-file result. A missing test is not a valid red phase.

- [ ] **Step 2: Implement the fixture and minimal test helpers**

The fixture must implement line-delimited JSON-RPC over stdin/stdout, respond to `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`, and exit on stdin close. `get_instance_id` returns the fixture PID. `get_session_value` and `set_session_value` operate only on in-memory state within that process.

The test helper must:

1. Launch both shims without awaiting either startup first.
2. Wait for both initialization responses.
3. Call `get_instance_id` through both shims.
4. Count only processes matching the current `run_id`, fixture executable path, parent/broker relationship, and expected role with `Get-CimInstance Win32_Process` or an equivalent PowerShell process query.
5. Fail if the shared backend count is not exactly one.

- [ ] **Step 3: Add the per-session isolation test**

Launch two shims with per-session configuration, set different values through each, read them back, and assert that values do not cross. Assert exactly two fixture PIDs.

- [ ] **Step 4: Add protocol virtualization checks**

Use the same JSON-RPC request IDs from both shims, overlap delayed calls, use different initialize capability sets, and test one disconnect while the other remains active. Add notification/cancellation/progress cases only for features the source audit says are claimed. If the candidate cannot route server-to-client requests, mark those server capabilities ineligible for shared mode rather than silently accepting them.

- [ ] **Step 5: Run the focused tests**

Run:

```powershell
node --test P:\tmp\mcp-broker-review\mcp-mux-validation\windows-lifecycle.test.mjs
```

Expected: cold shared startup produces one backend; per-session startup produces two backends; no stdout contamination is detected.

### Task 3: Prove routing, recovery, and orphan cleanup

**Files:**
- Modify: `P:\tmp\mcp-broker-review\mcp-mux-validation\windows-lifecycle.test.mjs`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\helpers\process-tree.ps1`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\evidence\lifecycle-test-schema.md`

**Interfaces:**
- Consumes: Task 2 fixture and test helpers.
- Produces: process snapshots and bounded failure assertions for broker and backend death.

- [ ] **Step 1: Add concurrent call correlation**

Send calls with distinct correlation payloads through both shims concurrently, including identical request IDs. Assert every response ID and payload returns to the initiating shim. Include at least one delayed fixture response to force overlap. Define expected cancellation/progress behavior before asserting it.

- [ ] **Step 2: Add broker-death recovery**

Identify the broker PID from the mcp-mux status or process tree, terminate it with `Stop-Process -Force`, and reconnect a new shim. Assert the next connection starts or finds exactly one replacement broker and does not create duplicate shared backends.

- [ ] **Step 3: Add backend-death recovery**

Terminate the shared fixture backend. For the initial safe policy, assert that the initiating call returns a bounded, understandable error; do not add transparent retries unless the operation is explicitly idempotent and the retry policy is documented. Issue a later call and assert one clean backend restart, not an uncontrolled process fan-out.

- [ ] **Step 4: Add disconnect and idle cleanup**

Disconnect one shim while another remains connected; assert the shared backend remains. Use a test-only `idleTimeoutMs` of 1000 ms, disconnect all shims, and assert the broker and backend exit within 2x that interval. Capture the parent/child process tree before and after cleanup.

- [ ] **Step 5: Run the lifecycle suite**

Run:

```powershell
node --test P:\tmp\mcp-broker-review\mcp-mux-validation\windows-lifecycle.test.mjs
```

Expected: all lifecycle assertions pass and the evidence directory contains before/during/after PID snapshots. Any orphan is a stop condition.

### Task 4: Validate with one real harmless MCP server

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\config\real-server.json`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\real-server-run.ps1`
- Modify: `P:\tmp\mcp-broker-review\mcp-mux-validation\README.md`

**Interfaces:**
- Consumes: the Task 3 harness and a temporary directory root.
- Produces: evidence that a real MCP implementation, not only the fixture, passes shared-process routing.

- [ ] **Step 1: Select and pin a harmless real server**

Use two real servers with different purposes: an inspected and pinned intrinsically stateless server for the shared-mode proof, and the real MCP filesystem server restricted to separate newly created temporary directories for the per-session proof. Resolve and record exact package versions before the run. Do not use an existing project root or a server with credentials. Do not treat a read-only filesystem call as proof that filesystem sharing is safe.

- [ ] **Step 2: Run the stateless server through two shared shims**

Use a harmless operation supported by the inspected stateless server. Assert both shims receive correct results and the real server process count is exactly one.

- [ ] **Step 3: Run filesystem only in per-session mode**

Give the two per-session instances separate temporary roots, perform a harmless read/write probe, and assert separate PIDs, separate roots, and no cross-session visibility. Keep filesystem sharing prohibited unless a later dedicated review changes that decision.

- [ ] **Step 4: Verify stdout discipline**

Capture shim stdout byte-for-byte. Parse every line as MCP/JSON-RPC and fail on any non-protocol output. Capture diagnostics separately from stderr.

- [ ] **Step 5: Record the real-server evidence**

Save the redacted config, resolved version, commands, PID snapshots, and result summary under the validation evidence directory.

### Task 5: Build isolated client compatibility probes

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\client-probes\README.md`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\client-probes\probe-results.json`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\client-probes\run-probes.ps1`

**Interfaces:**
- Consumes: the proven mcp-mux stdio command and the harmless real-server config.
- Produces: client-by-client compatibility results without editing production configuration.

- [ ] **Step 1: Discover isolated configuration mechanisms**

Run the local help commands:

```powershell
claude --help
codex --help
pi --help
opencode --help
```

Document the supported temporary config or project-local config mechanism for each client. Verify the exact config path consumed, precedence, global-config merging, inherited MCP/plugin definitions, write-back behavior, authentication source, and client version. If a client has no safe isolated mode, mark it `blocked` rather than writing its real config.

- [ ] **Step 2: Probe each client individually**

For each client, connect only the mcp-mux shim and harmless real server. Verify startup, tool discovery, one call, clean shutdown, and no duplicate broker/backend processes.

- [ ] **Step 3: Run two different clients simultaneously**

Start two isolated clients concurrently and repeat the shared-process count and call-correlation checks. Record which client initiated each call.

- [ ] **Step 4: Run the full target topology**

After individual probes pass, start Claude Code, Codex, PI, and OpenCode concurrently in isolated configurations. Exercise overlapping calls, one-client exit while three continue, and one all-four restart cycle. A pairwise pass is not evidence for the four-client target.

- [ ] **Step 5: Produce the client matrix**

Each result must contain: client/version, isolated config mechanism, shim command, broker PID, backend PID(s), call result, stdout check, cleanup result, and classification if blocked.

### Task 6: Classify intended MCP servers and prepare reversible integration

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\server-classification.md`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\rollback-plan.md`
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\server-contract.schema.json`
- Modify: `P:\tmp\mcp-broker-review\HANDOFF.md`

**Interfaces:**
- Consumes: real-server and client-probe evidence.
- Produces: an explicit server mode matrix and a go/no-go recommendation.

- [ ] **Step 1: Inventory the user’s intended MCP servers**

Read the existing MCP settings only for inventory and comparison. Do not modify them. Record command, transport, credentials source, working directory, statefulness, mutation capability, and intended clients.

- [ ] **Step 2: Assign an evidence-backed mode**

Assign exactly one of `shared`, `per-session`, or `disabled` to each server. Record protocol features, identity inputs, credential scope, cwd sensitivity, mutation risk, restart behavior, idle-shutdown behavior, client coverage, and evidence run IDs. Default browser, filesystem, database, project-local, OAuth-stateful, and mutating servers to `per-session` or `disabled` until a specific isolation test proves sharing safe.

- [ ] **Step 3: Define backup and rollback**

For each client, record the exact config path, backup command, restore command, and health check. The rollback plan must restore the previous configuration and stop the broker without deleting user data.

- [ ] **Step 4: Update the handoff with the decision**

Report `proceed`, `needs_fix`, or `blocked` using the governing decision gate. Do not report production readiness if any client or server classification remains untested.

### Task 6.5: Apply the explicit decision gate

**Files:**
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\decision-gate.md`

**Interfaces:**
- Consumes: all prior evidence artifacts.
- Produces: a binary, reviewable authorization for limited integration.

- [ ] **Step 1: Require deterministic protocol/lifecycle evidence**

Require three consecutive cold concurrent fixture runs with one broker, correct shared/per-session counts, request correlation, recovery, no orphan processes, clean stdout, and no state bleed.

- [ ] **Step 2: Require security and identity evidence**

Require documented pipe identity, ACL/security posture, stale-pipe behavior, config/version collision behavior, run ownership, and status/PID evidence. If credential-bearing shared servers cannot meet this, authorize only non-credential test servers.

- [ ] **Step 3: Separate authorization levels**

Record separate outcomes for protocol viability, one-client pilot, multi-client pilot, and all-four production readiness. A blocked client or unsupported protocol feature narrows scope; it does not silently pass.

- [ ] **Step 4: Human approval checkpoint**

Do not auto-enter Task 7. Stop after writing the gate and require explicit user approval for limited integration based on the evidence packet.

### Task 7: Limited client integration, only if the gate passes

**Files:**
- Modify: only the explicitly approved client MCP config files after backup.
- Create: `P:\tmp\mcp-broker-review\mcp-mux-validation\integration-record.md`

**Interfaces:**
- Consumes: Task 5 client matrix, Task 6 classification, and rollback plan.
- Produces: reversible limited integration for the approved stateless server subset.

- [ ] **Step 1: Pin the broker and shim**

Use a local checkout or fixed package reference; do not use `latest`, an unpinned GitHub branch, or a floating `npx` invocation.

- [ ] **Step 2: Back up each approved client config**

Create timestamped backups and verify they can be parsed before editing. Record backup paths in `integration-record.md`.

- [ ] **Step 3: Add only the shared stateless subset**

Leave all unproven or session-bound servers on their existing configuration. Add one mcp-mux shim entry per approved client.

- [ ] **Step 4: Re-run the cold-start and multi-client checks**

Verify exactly one broker, exactly one backend per shared server, no orphaned processes, and understandable failures.

- [ ] **Step 5: Exercise rollback**

Restore every backup, stop the broker, and verify each client returns to its pre-integration MCP state.

## Final self-review gate

Before reporting completion, verify:

- The real-server test passed, not only the fixture tests.
- Cold concurrent startup and process counts are captured.
- Broker death and backend death were tested.
- No stdout contamination or session-state bleed occurred.
- Every client result is individually recorded.
- Every intended server has a mode classification.
- Backups and rollback were exercised.
- Broker/shim versions are pinned.
- Any remaining inference is clearly labeled and does not drive production adoption.
