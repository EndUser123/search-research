import test from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, mkdir, readFile, readdir, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import {
  initReview,
  readRelayStatus,
  sha256,
  stableStringify,
  startOrJoinReview,
  submitTurn,
  tickReview,
  watchReview,
  writeHandoffCandidate,
} from "../src/review-relay.mjs";

const execFileAsync = promisify(execFile);
const relayCli = join(dirname(fileURLToPath(import.meta.url)), "..", "bin", "review-relay.mjs");

async function tempRoot(prefix = "codex-review-relay-") {
  return mkdtemp(join(tmpdir(), prefix));
}

function at(ms) {
  return () => ms;
}

async function setup({ maxTurns = null, firstActor = "codex", clock = at(Date.parse("2026-08-08T12:00:00.000Z")), leaseSeconds = 10, orphanGraceSeconds = 0 } = {}) {
  const root = await tempRoot();
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "# Proposal\n\nKeep the review bounded.\n", "utf8");
  const artifactRoot = join(root, "relay");
  const initialized = await initReview({
    artifactRoot,
    reviewId: "review-test",
    proposalPath,
    firstActor,
    maxTurns,
    leaseSeconds,
    ttlSeconds: 3600,
    orphanGraceSeconds,
    clock,
  });
  return { root, proposalPath, artifactRoot, initialized, clock };
}

async function writeResult(path, value = { status: "submitted", findings: [], unresolved: [] }) {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

test("init creates an isolated immutable snapshot and per-conversation event log", async () => {
  const fixture = await setup();
  const entries = await readdir(fixture.artifactRoot, { withFileTypes: true });
  assert.deepEqual(entries.map((entry) => entry.name).sort(), ["events", "manifest.json", "proposal-v1.snapshot"]);
  assert.equal(await readFile(join(fixture.artifactRoot, "proposal-v1.snapshot"), "utf8"), await readFile(fixture.proposalPath, "utf8"));
  const manifest = JSON.parse(await readFile(join(fixture.artifactRoot, "manifest.json"), "utf8"));
  assert.equal(manifest.write_policy.artifact_root_only, true);
  assert.match(manifest.event_layout, /events/);
  assert.equal((await readdir(join(fixture.artifactRoot, "events", "operator"))).length, 1);
  assert.equal(await readFile(fixture.proposalPath, "utf8"), "# Proposal\n\nKeep the review bounded.\n");
});

test("two relay roots remain isolated and concurrent claims have one winner", async () => {
  const first = await setup();
  const second = await setup();
  const [firstClaim, secondClaim] = await Promise.all([
    tickReview({ artifactRoot: first.artifactRoot, actor: "codex", clock: first.clock }),
    tickReview({ artifactRoot: second.artifactRoot, actor: "codex", clock: second.clock }),
  ]);
  assert.equal(firstClaim.status, "act");
  assert.equal(secondClaim.status, "act");
  assert.notEqual(firstClaim.attempt_id, secondClaim.attempt_id);
  assert.notEqual(firstClaim.input_path, secondClaim.input_path);

  const fixture = await setup();
  const claims = await Promise.all([
    tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock }),
    tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock }),
  ]);
  assert.equal(claims.filter((claim) => claim.status === "act").length, 1);
  assert.equal(claims.filter((claim) => claim.status === "waiting").length, 1);
  assert.ok(claims.find((claim) => claim.status === "waiting")?.reason === "another_attempt_claimed_turn" || claims.find((claim) => claim.status === "waiting")?.active);
});

test("concurrent initialization of the same review converges to one manifest", async () => {
  const root = await tempRoot("codex-review-relay-init-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "same proposal", "utf8");
  const artifactRoot = join(root, "relay");
  const results = await Promise.all([
    initReview({ artifactRoot, reviewId: "same-review", proposalPath, clock: at(Date.parse("2026-08-08T12:00:00.000Z")) }),
    initReview({ artifactRoot, reviewId: "same-review", proposalPath, clock: at(Date.parse("2026-08-08T12:00:00.000Z")) }),
  ]);
  assert.deepEqual(results.map((result) => result.status).sort(), ["already_exists", "created"]);
  const manifest = JSON.parse(await readFile(join(artifactRoot, "manifest.json"), "utf8"));
  assert.equal(manifest.review_id, "same-review");
});

test("filename-only start-or-join creates once and lets the other actor attach", async () => {
  const root = await tempRoot("codex-review-relay-auto-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "shared proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
    clock: at(Date.parse("2026-08-08T12:00:00.000Z")),
  };

  const created = await startOrJoinReview({ ...options, actor: "codex" });
  const attached = await startOrJoinReview({ ...options, actor: "grok" });

  assert.equal(created.status, "created");
  assert.equal(created.tick.status, "act");
  assert.equal(attached.status, "attached");
  assert.equal(attached.review_id, created.review_id);
  assert.equal(attached.tick.status, "waiting");
  assert.equal(attached.tick.expected_actor, "codex");
  assert.deepEqual(created.handoff.send_to_partner.input_paths, [proposalPath]);
  assert.equal(created.handoff.send_to_partner.input_set_hash, created.input_set_hash);
  assert.equal(created.handoff.current_turn.read_paths.turn_input, created.tick.input_path);
  assert.equal(created.handoff.current_turn.write_paths.result_input, created.tick.result_input_path);
  assert.equal(attached.handoff.receive_from_partner.status, "awaiting_partner_commit");
  assert.equal(attached.handoff.receive_from_partner.actor, "codex");
  assert.match(attached.handoff.receive_from_partner.result_path, /attempt-[^\\/]+\\result\.json$/);
  assert.match(attached.handoff.receive_from_partner.receipt_path, /attempt-[^\\/]+\\receipt\.json$/);
  const records = (await readdir(join(options.registryRoot, created.input_set_hash)))
    .filter((name) => name.endsWith(".json"));
  assert.deepEqual(records, [`${created.review_id}.json`]);
});

test("filename-only start-or-join reuses one matching terminal session", async () => {
  const root = await tempRoot("codex-review-relay-terminal-reuse-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "terminal proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
    maxTurns: 1,
  };

  const created = await startOrJoinReview({ ...options, actor: "grok" });
  await writeResult(created.tick.result_input_path);
  const submitted = await submitTurn({
    artifactRoot: created.artifact_root,
    actor: "grok",
    attemptId: created.tick.attempt_id,
    leaseId: created.tick.lease_id,
    resultPath: created.tick.result_input_path,
  });
  assert.equal(submitted.status, "submitted");

  const reused = await startOrJoinReview({ ...options, actor: "codex" });
  assert.equal(reused.status, "terminal");
  assert.equal(reused.reason, "matching_content_already_terminal");
  assert.equal(reused.review_id, created.review_id);
  assert.equal(reused.artifact_root, created.artifact_root);
  const records = (await readdir(join(options.registryRoot, created.input_set_hash)))
    .filter((name) => name.endsWith(".json"));
  assert.deepEqual(records, [`${created.review_id}.json`]);
});

test("turn budget is an emergency fuse and never claims convergence", async () => {
  const fixture = await setup({ maxTurns: 2 });
  const first = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(first.result_input_path);
  await submitTurn({
    artifactRoot: fixture.artifactRoot,
    actor: "codex",
    attemptId: first.attempt_id,
    leaseId: first.lease_id,
    resultPath: first.result_input_path,
    clock: fixture.clock,
  });

  const second = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "grok", clock: fixture.clock });
  await writeResult(second.result_input_path);
  await submitTurn({
    artifactRoot: fixture.artifactRoot,
    actor: "grok",
    attemptId: second.attempt_id,
    leaseId: second.lease_id,
    resultPath: second.result_input_path,
    clock: fixture.clock,
  });

  const status = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(status.status, "partial");
  assert.equal(status.reason, "turn_budget_exhausted");
  assert.equal(status.next_turn, 3);
  assert.equal(status.turns.length, 2);
  assert.equal((await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock })).status, "partial");
});

test("default relay continuation is not limited by an artificial turn count", async () => {
  const fixture = await setup({ maxTurns: null });
  for (let index = 0; index < 7; index += 1) {
    const actor = index % 2 === 0 ? "codex" : "grok";
    const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor, clock: fixture.clock });
    assert.equal(claim.status, "act");
    await writeResult(claim.result_input_path);
    await submitTurn({
      artifactRoot: fixture.artifactRoot,
      actor,
      attemptId: claim.attempt_id,
      leaseId: claim.lease_id,
      resultPath: claim.result_input_path,
      clock: fixture.clock,
    });
  }
  const status = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(status.status, "ready");
  assert.equal(status.next_turn, 8);
  assert.equal(status.max_turns, null);
});

test("converged is not an accepted partner result status", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(claim.result_input_path, { status: "converged", findings: [] });
  await assert.rejects(
    submitTurn({
      artifactRoot: fixture.artifactRoot,
      actor: "codex",
      attemptId: claim.attempt_id,
      leaseId: claim.lease_id,
      resultPath: claim.result_input_path,
      clock: fixture.clock,
    }),
    (error) => error.code === "malformed_result_input",
  );
});

test("filename-only start-or-join freezes multiple inputs as one hashed bundle", async () => {
  const root = await tempRoot("codex-review-relay-bundle-");
  const firstPath = join(root, "first.md");
  const secondPath = join(root, "second.md");
  await writeFile(firstPath, "first", "utf8");
  await writeFile(secondPath, "second", "utf8");
  const result = await startOrJoinReview({
    inputPaths: [secondPath, firstPath],
    actor: "codex",
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  });
  const manifest = JSON.parse(await readFile(join(result.artifact_root, "manifest.json"), "utf8"));
  const snapshot = JSON.parse(await readFile(join(result.artifact_root, "proposal-v1.snapshot"), "utf8"));

  assert.equal(manifest.proposal.input_set_hash, result.input_set_hash);
  assert.equal(manifest.proposal.source_paths.length, 2);
  assert.equal(snapshot.schema_version, "review-input-bundle.v1");
  assert.deepEqual(snapshot.files.map((file) => file.source_path), manifest.proposal.source_paths);
  assert.equal(snapshot.files.length, 2);
});

test("watch does not restart unchanged terminal content, but starts a new session after an update", async () => {
  const root = await tempRoot("codex-review-relay-watch-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "watch me", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
    maxTurns: 1,
  };

  const created = await watchReview({ ...options, actor: "codex" });
  assert.equal(created.status, "created");
  await writeResult(created.tick.result_input_path);
  const submitted = await submitTurn({
    artifactRoot: created.artifact_root,
    actor: "codex",
    attemptId: created.tick.attempt_id,
    leaseId: created.tick.lease_id,
    resultPath: created.tick.result_input_path,
  });
  assert.equal(submitted.status, "submitted");

  const unchanged = await watchReview({ ...options, actor: "grok" });
  assert.equal(unchanged.status, "terminal");
  assert.equal(unchanged.reason, "matching_content_already_terminal");
  assert.equal(unchanged.review_id, created.review_id);
  const repeated = await watchReview({ ...options, actor: "codex" });
  assert.equal(repeated.status, "terminal");
  assert.equal(repeated.review_id, created.review_id);

  await writeFile(proposalPath, "watch me after an update", "utf8");
  const changed = await watchReview({ ...options, actor: "codex" });
  assert.equal(changed.status, "created");
  assert.notEqual(changed.review_id, created.review_id);
  assert.notEqual(changed.input_set_hash, created.input_set_hash);
});

test("watch fails closed when unchanged content has multiple terminal sessions", async () => {
  const root = await tempRoot("codex-review-relay-watch-ambiguous-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "ambiguous terminal content", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
    maxTurns: 1,
  };

  const finish = async (reviewId) => {
    const created = await startOrJoinReview({ ...options, actor: "codex", reviewId });
    await writeResult(created.tick.result_input_path);
    await submitTurn({
      artifactRoot: created.artifact_root,
      actor: "codex",
      attemptId: created.tick.attempt_id,
      leaseId: created.tick.lease_id,
      resultPath: created.tick.result_input_path,
    });
    return created;
  };
  const first = await finish("review-terminal-one");
  const second = await finish("review-terminal-two");
  assert.notEqual(first.review_id, second.review_id);

  await assert.rejects(
    watchReview({ ...options, actor: "grok" }),
    (error) => error.code === "ambiguous_session" && error.details.candidates.length === 2,
  );
});

test("concurrent filename-only starts converge to one discoverable session", async () => {
  const root = await tempRoot("codex-review-relay-auto-race-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "race proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    actor: "codex",
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  };
  const results = await Promise.all([
    startOrJoinReview(options),
    startOrJoinReview(options),
  ]);

  assert.deepEqual(results.map((result) => result.status).sort(), ["attached", "created"]);
  assert.equal(new Set(results.map((result) => result.review_id)).size, 1);
  const records = (await readdir(join(options.registryRoot, results[0].input_set_hash)))
    .filter((name) => name.endsWith(".json"));
  assert.equal(records.length, 1);
});

test("multiple active sessions for the same inputs fail closed instead of choosing one", async () => {
  const root = await tempRoot("codex-review-relay-ambiguous-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "ambiguous proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    actor: "codex",
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  };
  await startOrJoinReview({ ...options, reviewId: "review-one" });
  await startOrJoinReview({ ...options, reviewId: "review-two" });

  await assert.rejects(
    startOrJoinReview(options),
    (error) => error.code === "ambiguous_session" && error.details.candidates.length === 2,
  );
});

test("changed input content never attaches to a stale relay session", async () => {
  const root = await tempRoot("codex-review-relay-stale-input-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "original", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  };
  const original = await startOrJoinReview({ ...options, actor: "codex" });
  await writeFile(proposalPath, "changed", "utf8");
  const changed = await startOrJoinReview({ ...options, actor: "grok" });

  assert.equal(changed.status, "created");
  assert.notEqual(changed.review_id, original.review_id);
  assert.notEqual(changed.input_set_hash, original.input_set_hash);
});

test("malformed discovery metadata fails closed instead of guessing a session", async () => {
  const root = await tempRoot("codex-review-relay-registry-corrupt-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "corrupt registry proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    actor: "codex",
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  };
  const created = await startOrJoinReview(options);
  await rm(created.registry_record_path);
  await writeFile(join(options.registryRoot, created.input_set_hash, "corrupt.json"), "{not-json", "utf8");

  await assert.rejects(
    startOrJoinReview(options),
    (error) => error.code === "malformed_registry_record",
  );
});

test("CLI accepts filename arguments and returns a structured join result", async () => {
  const root = await tempRoot("codex-review-relay-cli-");
  const firstPath = join(root, "first.md");
  const secondPath = join(root, "second.md");
  const registryRoot = join(root, "registry");
  const sessionRoot = join(root, "sessions");
  await writeFile(firstPath, "first cli input", "utf8");
  await writeFile(secondPath, "second cli input", "utf8");

  const result = await execFileAsync(process.execPath, [
    relayCli,
    "start-or-join",
    "--actor", "codex",
    "--registry-root", registryRoot,
    "--session-root", sessionRoot,
    firstPath,
    secondPath,
  ], { cwd: dirname(relayCli) });
  const payload = JSON.parse(result.stdout);

  assert.equal(payload.status, "created");
  assert.equal(payload.tick.status, "act");
  assert.equal(payload.input_set_hash.length, 64);
  assert.ok(payload.registry_record_path.endsWith(`${payload.review_id}.json`));
  assert.equal(payload.handoff.schema_version, "review-relay-handoff.v1");
  assert.deepEqual(payload.handoff.send_to_partner.input_paths, [firstPath, secondPath]);
  assert.equal(payload.handoff.current_turn.write_paths.result_input, payload.tick.result_input_path);

  const watcher = await execFileAsync(process.execPath, [
    relayCli,
    "watch",
    "--actor", "grok",
    "--registry-root", registryRoot,
    "--session-root", sessionRoot,
    firstPath,
    secondPath,
  ], { cwd: dirname(relayCli) });
  const watcherPayload = JSON.parse(watcher.stdout);
  assert.equal(watcherPayload.status, "attached");
  assert.equal(watcherPayload.review_id, payload.review_id);
  assert.equal(watcherPayload.tick.expected_actor, "codex");
});

test("handoff emits the committed prior result for the next actor", async () => {
  const root = await tempRoot("codex-review-relay-handoff-result-");
  const proposalPath = join(root, "proposal.md");
  await writeFile(proposalPath, "handoff result proposal", "utf8");
  const options = {
    inputPaths: [proposalPath],
    registryRoot: join(root, "registry"),
    sessionRoot: join(root, "sessions"),
  };
  const created = await startOrJoinReview({ ...options, actor: "codex" });
  await writeResult(created.tick.result_input_path);
  const submitted = await submitTurn({
    artifactRoot: created.artifact_root,
    actor: "codex",
    attemptId: created.tick.attempt_id,
    leaseId: created.tick.lease_id,
    resultPath: created.tick.result_input_path,
  });
  const grok = await startOrJoinReview({ ...options, actor: "grok" });

  assert.equal(grok.tick.status, "act");
  assert.equal(grok.tick.previous_result_path, submitted.result_path);
  assert.equal(grok.tick.previous_result_actor, "codex");
  assert.equal(grok.handoff.receive_from_partner.status, "committed_previous_turn");
  assert.equal(grok.handoff.receive_from_partner.result_path, submitted.result_path);
  assert.equal(grok.handoff.receive_from_partner.receipt_path, submitted.receipt_path);
  assert.equal(grok.handoff.current_turn.read_paths.previous_result, submitted.result_path);
});

test("non-owner waits, owner can continue, and result identity is validated", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  const other = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "grok", clock: fixture.clock });
  assert.equal(claim.status, "act");
  assert.equal(other.status, "waiting");
  assert.equal(other.expected_actor, "codex");
  const continued = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  assert.equal(continued.status, "continue");

  await writeResult(claim.result_input_path, { status: "submitted", review_id: "wrong-review" });
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock }),
    (error) => error.code === "stale_result",
  );
  await writeResult(claim.result_input_path);
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "grok", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock }),
    (error) => error.code === "identity_mismatch",
  );
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: "wrong-lease", resultPath: claim.result_input_path, clock: fixture.clock }),
    (error) => error.code === "identity_mismatch",
  );
});

test("successful submission commits an attempt, preserves hashes, and advances the baton", async () => {
  const fixture = await setup();
  const first = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(first.result_input_path);
  const submitted = await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: first.attempt_id, leaseId: first.lease_id, resultPath: first.result_input_path, clock: fixture.clock });
  assert.equal(submitted.status, "submitted");
  assert.equal(submitted.next_actor, "grok");
  const result = JSON.parse(await readFile(submitted.result_path, "utf8"));
  const receipt = JSON.parse(await readFile(submitted.receipt_path, "utf8"));
  assert.equal(result.base_proposal_hash, fixture.initialized.manifest.proposal.sha256);
  assert.equal(result.content_hash, sha256(stableStringify({ status: "submitted", findings: [], unresolved: [] })));
  assert.equal(receipt.result_hash, sha256(stableStringify(result)));
  assert.equal(receipt.validation.persistence, "pass");
  const status = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(status.status, "ready");
  assert.equal(status.expected_actor, "grok");
  assert.equal(status.previous_result_hash, receipt.result_hash);
  assert.ok(status.event_count >= 3);

  const second = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "grok", clock: fixture.clock });
  assert.equal(second.status, "act");
  assert.equal(second.previous_result_path, submitted.result_path);
  assert.equal(second.previous_result_actor, "codex");
  const secondInput = JSON.parse(await readFile(second.input_path, "utf8"));
  assert.equal(secondInput.previous_result_path, submitted.result_path);
  assert.equal(secondInput.previous_result_actor, "codex");
});

test("ready_for_parent_review cannot close the relay before every actor has submitted", async () => {
  const fixture = await setup({ maxTurns: 3, firstActor: "grok" });
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "grok", clock: fixture.clock });
  await assert.rejects(
    writeHandoffCandidate({ artifactRoot: fixture.artifactRoot, clock: fixture.clock }),
    (error) => error.code === "handoff_requires_terminal",
  );
  await writeResult(claim.result_input_path, { status: "ready_for_parent_review", findings: [{ id: "f1", severity: "low" }] });
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "grok", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock }),
    (error) => error.code === "premature_terminal_status" && error.details.missing_actors.includes("codex"),
  );
  const activeStatus = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(activeStatus.status, "waiting");
  assert.equal(activeStatus.active.actor, "grok");

  await writeResult(claim.result_input_path, { status: "submitted", findings: [{ id: "f1", severity: "low" }] });
  await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "grok", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock });
  const second = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  assert.equal(second.status, "act");
  await writeResult(second.result_input_path, { status: "ready_for_parent_review", findings: [{ id: "f1", severity: "low" }] });
  await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: second.attempt_id, leaseId: second.lease_id, resultPath: second.result_input_path, clock: fixture.clock });
  const status = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(status.status, "ready_for_parent_review");
  const candidate = await writeHandoffCandidate({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(candidate.status, "written");
  assert.equal(candidate.candidate.external_write_required, true);
  assert.equal(candidate.candidate.next_action, "Parent/user reviews the candidate and decides whether to accept or resume.");
});

test("checkpoint handoff is explicit and remains inside the relay root", async () => {
  const fixture = await setup();
  const candidate = await writeHandoffCandidate({ artifactRoot: fixture.artifactRoot, allowCheckpoint: true, clock: fixture.clock });
  assert.equal(candidate.status, "written");
  assert.equal(candidate.candidate.status, "ready");
  assert.equal(dirname(candidate.path), fixture.artifactRoot);
  assert.match(candidate.candidate.resume_command, /review-relay\.mjs/);
});

test("expired leases are orphaned and a new attempt can claim the same turn", async () => {
  let now = Date.parse("2026-08-08T12:00:00.000Z");
  const clock = () => now;
  const fixture = await setup({ clock, leaseSeconds: 5, orphanGraceSeconds: 0 });
  const expired = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock });
  now += 6000;
  const recovered = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock });
  assert.equal(recovered.status, "act");
  assert.notEqual(recovered.attempt_id, expired.attempt_id);
  const turnEntries = await readdir(join(fixture.artifactRoot, "turns", "0001"));
  assert.ok(turnEntries.some((name) => name === `orphaned-${expired.attempt_id}`));
});

test("malformed claims and malformed results fail closed, while temporary files are ignored", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeFile(join(fixture.artifactRoot, "turns", "0001", "active", "claim.json"), "{not-json", "utf8");
  await writeFile(join(fixture.artifactRoot, "turns", "0001", "active", ".claim.json.tmp-123"), "{not-json", "utf8");
  await assert.rejects(
    readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock }),
    (error) => error.code === "malformed_claim",
  );

  const second = await setup();
  const secondClaim = await tickReview({ artifactRoot: second.artifactRoot, actor: "codex", clock: second.clock });
  await writeResult(secondClaim.result_input_path);
  await writeFile(join(second.artifactRoot, "turns", "0001", "active", "result.json"), "{not-json", "utf8");
  await assert.rejects(
    submitTurn({ artifactRoot: second.artifactRoot, actor: "codex", attemptId: secondClaim.attempt_id, leaseId: secondClaim.lease_id, resultPath: secondClaim.result_input_path, clock: second.clock }),
    (error) => error.code === "malformed_result",
  );
  assert.equal(claim.status, "act");
});

test("duplicate submission is idempotent, but a conflicting committed payload is rejected", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(claim.result_input_path);
  const first = await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock });
  const duplicate = await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock });
  assert.equal(duplicate.status, "idempotent");
  assert.equal(duplicate.result_path, first.result_path);

  const committedInput = join(dirname(first.result_path), "result-input.json");
  await writeResult(committedInput, { status: "submitted", findings: [{ id: "changed" }] });
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: committedInput, clock: fixture.clock }),
    (error) => error.code === "conflicting_duplicate",
  );
});

test("concurrent identical submissions commit one immutable result", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(claim.result_input_path);
  const submissions = await Promise.all([
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock }),
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock }),
  ]);
  assert.deepEqual(submissions.map((result) => result.status).sort(), ["idempotent", "submitted"]);
  const status = await readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock });
  assert.equal(status.turns.filter((turn) => turn.turn_number === 1).length, 1);
});

test("event-log failure is surfaced without converting a committed submission into failure", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  const events = join(fixture.artifactRoot, "events");
  await rename(events, join(fixture.artifactRoot, "events-disabled"));
  await writeFile(events, "event storage unavailable", "utf8");
  await writeResult(claim.result_input_path);
  const submitted = await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock });
  assert.equal(submitted.status, "submitted");
  assert.equal(submitted.event.status, "failed");
  const receipt = JSON.parse(await readFile(submitted.receipt_path, "utf8"));
  assert.equal(receipt.event.status, "failed");
});

test("committed attempts require an intact receipt and submissions cannot read outside the relay root", async () => {
  const fixture = await setup();
  const claim = await tickReview({ artifactRoot: fixture.artifactRoot, actor: "codex", clock: fixture.clock });
  await writeResult(claim.result_input_path);
  await assert.rejects(
    submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: join(fixture.root, "outside-result.json"), clock: fixture.clock }),
    (error) => error.code === "scope_violation",
  );
  const submitted = await submitTurn({ artifactRoot: fixture.artifactRoot, actor: "codex", attemptId: claim.attempt_id, leaseId: claim.lease_id, resultPath: claim.result_input_path, clock: fixture.clock });
  await rm(submitted.receipt_path);
  await assert.rejects(
    readRelayStatus({ artifactRoot: fixture.artifactRoot, clock: fixture.clock }),
    (error) => error.code === "needs_review",
  );
});
