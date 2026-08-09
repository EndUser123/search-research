import { createHash, randomUUID } from "node:crypto";
import {
  link,
  mkdir,
  readdir,
  readFile,
  rename,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";

export const RELAY_SCHEMA_VERSION = "review-relay.v1";
export const TURN_INPUT_SCHEMA_VERSION = "review-turn-input.v1";
export const RESULT_SCHEMA_VERSION = "review-result.v1";
export const RECEIPT_SCHEMA_VERSION = "review-receipt.v1";
export const EVENT_SCHEMA_VERSION = "review-event.v1";
export const REGISTRY_SCHEMA_VERSION = "review-relay-registry.v1";
export const HANDOFF_SCHEMA_VERSION = "review-relay-handoff.v1";
export const DEFAULT_REGISTRY_ROOT = "P:/tmp/review-relay/registry";
export const DEFAULT_SESSION_ROOT = "P:/tmp/review-relay/sessions";

const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const DEFAULT_LEASE_SECONDS = 120;
const DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60;
const DEFAULT_ORPHAN_GRACE_SECONDS = 30;
// New reviews are unbounded by turn count. An explicit max_turns value remains
// accepted as an operator-selected emergency fuse and for older manifests.
const DEFAULT_MAX_TURNS = null;
const REGISTRY_LOCK_SECONDS = 30;
const REGISTRY_WAIT_ATTEMPTS = 80;
const REGISTRY_WAIT_INTERVAL_MS = 25;
const CONTINUING_STATUS = "submitted";
const TERMINAL_RESULT_STATUSES = new Set([
  "needs_fix",
  "partial",
  "blocked",
  "failed",
  "timed_out",
  "ready_for_parent_review",
  "expired",
  "needs_review",
]);
const RESULT_STATUSES = new Set([CONTINUING_STATUS, ...TERMINAL_RESULT_STATUSES]);

export class RelayError extends Error {
  constructor(code, message, details = undefined, exitCode = 30) {
    super(message);
    this.name = "RelayError";
    this.code = code;
    this.details = details;
    this.exitCode = exitCode;
  }
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function assertObject(value, code, message) {
  if (!isObject(value)) throw new RelayError(code, message);
}

function assertSafeId(value, field) {
  if (typeof value !== "string" || !ID_PATTERN.test(value)) {
    throw new RelayError("invalid_identity", `${field} must be a safe identifier`);
  }
  return value;
}

function assertAbsolutePath(value, field) {
  if (typeof value !== "string" || !isAbsolute(value)) {
    throw new RelayError("invalid_path", `${field} must be an absolute path`);
  }
  return resolve(value);
}

function resolveInputPath(value) {
  if (typeof value !== "string" || value.length === 0) throw new RelayError("invalid_path", "input_path must be a non-empty path");
  return resolve(value);
}

function nowMs(clock = Date.now()) {
  return typeof clock === "function" ? clock() : clock;
}

function iso(ms) {
  return new Date(ms).toISOString();
}

function parseTimestamp(value, field) {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new RelayError("invalid_timestamp", `${field} is not a valid timestamp`);
  return parsed;
}

function safeDatePart(ms) {
  return iso(ms).slice(0, 10);
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (isObject(value)) {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
  }
  return value;
}

export function stableStringify(value) {
  return JSON.stringify(stableValue(value));
}

export function sha256(value) {
  const input = Buffer.isBuffer(value) ? value : String(value);
  return createHash("sha256").update(input).digest("hex");
}

function withoutHash(value, key) {
  const copy = { ...value };
  delete copy[key];
  return copy;
}

function normalizedPath(value) {
  return resolve(value).replaceAll("\\", "/").toLowerCase();
}

async function readInputSet(inputPaths) {
  if (!Array.isArray(inputPaths) || inputPaths.length === 0) {
    throw new RelayError("invalid_input", "at least one input file is required");
  }
  const sourcePaths = inputPaths.map(resolveInputPath);
  const seen = new Set();
  const files = [];
  for (const sourcePath of sourcePaths) {
    const identityPath = normalizedPath(sourcePath);
    if (seen.has(identityPath)) throw new RelayError("duplicate_input", "input files must be unique", { path: sourcePath });
    seen.add(identityPath);
    let before;
    try {
      before = await stat(sourcePath);
    } catch (error) {
      throw new RelayError("input_read_error", `Could not stat input file ${sourcePath}: ${error.message}`, { path: sourcePath }, 20);
    }
    let content;
    try {
      content = await readFile(sourcePath);
    } catch (error) {
      throw new RelayError("input_read_error", `Could not read input file ${sourcePath}: ${error.message}`, { path: sourcePath }, 20);
    }
    let after;
    try {
      after = await stat(sourcePath);
    } catch (error) {
      throw new RelayError("input_read_error", `Could not restat input file ${sourcePath}: ${error.message}`, { path: sourcePath }, 20);
    }
    if (before.size !== after.size || before.mtimeMs !== after.mtimeMs) {
      throw new RelayError("input_changed_during_capture", `Input file changed while it was being frozen: ${sourcePath}`, { path: sourcePath }, 40);
    }
    files.push({
      source_path: sourcePath,
      identity_path: identityPath,
      size: content.length,
      sha256: sha256(content),
      content,
    });
  }
  files.sort((left, right) => left.identity_path.localeCompare(right.identity_path));
  const inputSetHash = sha256(stableStringify(files.map(({ identity_path, size, sha256: contentHash }) => ({ identity_path, size, sha256: contentHash }))));
  return { files, inputSetHash };
}

function inputSnapshot(inputSet) {
  if (inputSet.files.length === 1) return inputSet.files[0].content;
  const files = inputSet.files.map(({ source_path, size, sha256: contentHash, content }) => {
    const text = content.toString("utf8");
    const isUtf8 = Buffer.from(text, "utf8").equals(content);
    return {
      source_path,
      size,
      sha256: contentHash,
      encoding: isUtf8 ? "utf8" : "base64",
      content: isUtf8 ? text : content.toString("base64"),
    };
  });
  return Buffer.from(stableStringify({ schema_version: "review-input-bundle.v1", input_set_hash: inputSet.inputSetHash, files }), "utf8");
}

export function isWithin(child, parent) {
  const childPath = normalizedPath(child);
  const parentPath = normalizedPath(parent).replace(/\/$/, "");
  return childPath === parentPath || childPath.startsWith(`${parentPath}/`);
}

function assertWithin(child, parent, field = "path") {
  if (!isWithin(child, parent)) {
    throw new RelayError("scope_violation", `${field} escapes artifact_root`, { path: child, artifact_root: parent }, 40);
  }
}

function paddedTurn(turnNumber) {
  return String(turnNumber).padStart(4, "0");
}

function turnPath(root, turnNumber) {
  return join(root, "turns", paddedTurn(turnNumber));
}

function activePath(root, turnNumber) {
  return join(turnPath(root, turnNumber), "active");
}

function attemptPath(root, turnNumber, attemptId) {
  return join(turnPath(root, turnNumber), `attempt-${attemptId}`);
}

async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

async function readJson(path, code = "malformed_json") {
  let text;
  try {
    text = await readFile(path, "utf8");
  } catch (error) {
    throw new RelayError("artifact_read_error", `Could not read ${path}: ${error.message}`, { path }, 20);
  }
  try {
    return JSON.parse(text.replace(/^\uFEFF/, ""));
  } catch (error) {
    throw new RelayError(code, `Malformed JSON at ${path}: ${error.message}`, { path }, 40);
  }
}

async function atomicWrite(path, content) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${randomUUID()}`;
  try {
    await writeFile(temporary, content, { encoding: "utf8", flag: "wx" });
    await rename(temporary, path);
  } catch (error) {
    try { await rm(temporary, { force: true }); } catch { /* best effort */ }
    throw error;
  }
}

async function atomicWriteJson(path, value) {
  await atomicWrite(path, `${JSON.stringify(value, null, 2)}\n`);
}

async function atomicCreateJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${randomUUID()}`;
  try {
    await writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
    try {
      await link(temporary, path);
      return true;
    } catch (error) {
      if (error.code === "EEXIST") return false;
      throw error;
    }
  } finally {
    try { await rm(temporary, { force: true }); } catch { /* best effort cleanup */ }
  }
}

async function writeTextIfMissing(path, content) {
  await mkdir(dirname(path), { recursive: true });
  try {
    await writeFile(path, content, { encoding: "utf8", flag: "wx" });
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
  }
}

async function listDirectories(path) {
  let entries;
  try {
    entries = await readdir(path, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name);
}

async function turnNumbers(root) {
  return (await listDirectories(join(root, "turns")))
    .filter((name) => /^\d+$/.test(name))
    .map((name) => Number(name))
    .filter((number) => Number.isSafeInteger(number) && number > 0)
    .sort((left, right) => left - right);
}

async function waitForFile(path, attempts = 80, intervalMs = 25) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (await exists(path)) return true;
    await new Promise((resolvePromise) => setTimeout(resolvePromise, intervalMs));
  }
  return await exists(path);
}

async function writeEvent(root, actor, eventType, details, clock = Date.now()) {
  const safeActor = assertSafeId(actor || "system", "actor");
  const eventId = randomUUID();
  const event = {
    schema_version: EVENT_SCHEMA_VERSION,
    event_id: eventId,
    review_id: null,
    actor: safeActor,
    event_type: eventType,
    occurred_at: iso(nowMs(clock)),
    details: details || {},
  };
  const manifestPath = join(root, "manifest.json");
  if (await exists(manifestPath)) {
    const manifest = await readJson(manifestPath);
    event.review_id = manifest.review_id;
    event.manifest_hash = manifest.manifest_hash;
  }
  const directory = join(root, "events", safeActor, safeDatePart(nowMs(clock)));
  await atomicWriteJson(join(directory, `${eventId}.json`), event);
  return event;
}

async function recordEvent(root, actor, eventType, details, clock = Date.now()) {
  try {
    const event = await writeEvent(root, actor, eventType, details, clock);
    return { status: "recorded", event_id: event.event_id, path: join(root, "events", event.actor, safeDatePart(nowMs(clock)), `${event.event_id}.json`) };
  } catch (error) {
    return {
      status: "failed",
      failure_class: "event_write_error",
      code: error.code || "event_write_error",
      message: error.message,
    };
  }
}

function actorIds(manifest) {
  return manifest.actors.map((actor) => typeof actor === "string" ? actor : actor.id);
}

function actorDescriptor(manifest, actorId) {
  return manifest.actors.find((actor) => (typeof actor === "string" ? actor : actor.id) === actorId) || null;
}

function expectedActor(manifest, turnNumber) {
  const ordered = [manifest.first_actor, ...actorIds(manifest).filter((actor) => actor !== manifest.first_actor)];
  return ordered[(turnNumber - 1) % ordered.length];
}

function terminalStatus(status) {
  return TERMINAL_RESULT_STATUSES.has(status);
}

function validateManifestShape(manifest, root) {
  assertObject(manifest, "invalid_manifest", "manifest must be an object");
  if (manifest.schema_version !== RELAY_SCHEMA_VERSION) throw new RelayError("invalid_manifest", `schema_version must equal ${RELAY_SCHEMA_VERSION}`);
  assertSafeId(manifest.review_id, "review_id");
  if (manifest.mode !== "alternating") throw new RelayError("invalid_manifest", "manual relay mode must be alternating");
  if (!Array.isArray(manifest.actors) || manifest.actors.length !== 2) throw new RelayError("invalid_manifest", "exactly two actors are required");
  const ids = actorIds(manifest);
  ids.forEach((id) => assertSafeId(id, "actor"));
  if (new Set(ids).size !== ids.length) throw new RelayError("invalid_manifest", "actor IDs must be unique");
  assertSafeId(manifest.first_actor, "first_actor");
  if (!ids.includes(manifest.first_actor)) throw new RelayError("invalid_manifest", "first_actor must be one of actors");
  if (manifest.max_turns !== null && (!Number.isInteger(manifest.max_turns) || manifest.max_turns < 1)) throw new RelayError("invalid_manifest", "max_turns must be null or a positive integer");
  if (!Number.isInteger(manifest.lease_seconds) || manifest.lease_seconds < 5 || manifest.lease_seconds > 86400) throw new RelayError("invalid_manifest", "lease_seconds must be 5..86400");
  if (!Number.isInteger(manifest.orphan_grace_seconds) || manifest.orphan_grace_seconds < 0 || manifest.orphan_grace_seconds > 3600) throw new RelayError("invalid_manifest", "orphan_grace_seconds must be 0..3600");
  parseTimestamp(manifest.created_at, "created_at");
  parseTimestamp(manifest.expires_at, "expires_at");
  if (!isObject(manifest.proposal)) throw new RelayError("invalid_manifest", "proposal metadata is required");
  assertSafeId(manifest.proposal.snapshot, "proposal.snapshot");
  assertWithin(join(root, manifest.proposal.snapshot), root, "proposal.snapshot");
  if (!/^[a-f0-9]{64}$/.test(manifest.proposal.sha256)) throw new RelayError("invalid_manifest", "proposal.sha256 must be a SHA-256 digest");
  if (manifest.proposal.input_set_hash !== undefined && !/^[a-f0-9]{64}$/.test(manifest.proposal.input_set_hash)) {
    throw new RelayError("invalid_manifest", "proposal.input_set_hash must be a SHA-256 digest");
  }
  if (manifest.proposal.source_paths !== undefined) {
    if (!Array.isArray(manifest.proposal.source_paths) || manifest.proposal.source_paths.length < 1 || manifest.proposal.source_paths.some((path) => typeof path !== "string" || !isAbsolute(path))) {
      throw new RelayError("invalid_manifest", "proposal.source_paths must contain absolute paths");
    }
  }
  if (manifest.write_policy?.artifact_root_only !== true) throw new RelayError("invalid_manifest", "artifact_root_only write policy is required");
  const expectedManifestHash = sha256(stableStringify(withoutHash(manifest, "manifest_hash")));
  if (manifest.manifest_hash !== expectedManifestHash) throw new RelayError("stale_manifest", "manifest hash does not match its contents", { expected: expectedManifestHash, actual: manifest.manifest_hash }, 40);
}

async function readManifest(artifactRoot) {
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const manifestPath = join(root, "manifest.json");
  const manifest = await readJson(manifestPath, "malformed_manifest");
  validateManifestShape(manifest, root);
  const snapshotPath = join(root, manifest.proposal.snapshot);
  const snapshot = await readFile(snapshotPath);
  const actualHash = sha256(snapshot);
  if (actualHash !== manifest.proposal.sha256) throw new RelayError("stale_proposal", "proposal snapshot hash does not match manifest", { expected: manifest.proposal.sha256, actual: actualHash }, 40);
  return { root, manifest, manifestPath, snapshotPath };
}

async function readClaim(path) {
  const claim = await readJson(path, "malformed_claim");
  assertObject(claim, "malformed_claim", "claim must be an object");
  if (claim.schema_version !== "review-claim.v1") throw new RelayError("malformed_claim", "claim schema is invalid", { path }, 40);
  assertSafeId(claim.attempt_id, "attempt_id");
  assertSafeId(claim.lease_id, "lease_id");
  assertSafeId(claim.actor, "actor");
  for (const key of ["review_id", "manifest_hash", "base_proposal_hash", "turn_id"]) {
    if (typeof claim[key] !== "string" || claim[key].length === 0) throw new RelayError("malformed_claim", `claim.${key} is required`, { path }, 40);
  }
  if (!Number.isInteger(claim.turn_number) || claim.turn_number < 1) throw new RelayError("malformed_claim", "claim turn_number is invalid", { path }, 40);
  parseTimestamp(claim.expires_at, "claim.expires_at");
  return claim;
}

async function readResult(path, expected, root) {
  const result = await readJson(path, "malformed_result");
  assertObject(result, "malformed_result", "result must be an object");
  if (result.schema_version !== RESULT_SCHEMA_VERSION) throw new RelayError("malformed_result", "result schema is invalid", { path }, 40);
  for (const key of ["review_id", "manifest_hash", "base_proposal_hash", "turn_id", "attempt_id", "lease_id", "actor", "status", "content_hash"]) {
    if (typeof result[key] !== "string" || result[key].length === 0) throw new RelayError("malformed_result", `result.${key} is required`, { path }, 40);
  }
  if (!Number.isInteger(result.turn_number) || result.turn_number !== expected.turn_number) throw new RelayError("stale_result", "result turn_number does not match its attempt", { path }, 40);
  if (result.review_id !== expected.review_id || result.manifest_hash !== expected.manifest_hash || result.base_proposal_hash !== expected.proposal_hash) {
    throw new RelayError("stale_result", "result identity or proposal hash does not match the active review", { path }, 40);
  }
  if (result.turn_id !== `turn-${paddedTurn(expected.turn_number)}` || result.attempt_id !== expected.attempt_id || result.lease_id !== expected.lease_id || result.actor !== expected.actor) {
    throw new RelayError("stale_result", "result turn identity does not match its attempt", { path }, 40);
  }
  if (!RESULT_STATUSES.has(result.status)) {
    throw new RelayError("malformed_result", `unsupported result status: ${result.status}`, { path }, 40);
  }
  const content = result.review ?? {};
  const expectedHash = sha256(stableStringify(content));
  if (result.content_hash !== expectedHash) throw new RelayError("stale_result", "result content hash does not match", { path }, 40);
  assertWithin(path, root, "result path");
  return result;
}

async function readReceipt(path, expected, root) {
  const receipt = await readJson(path, "malformed_receipt");
  assertObject(receipt, "malformed_receipt", "receipt must be an object");
  if (receipt.schema_version !== RECEIPT_SCHEMA_VERSION) throw new RelayError("malformed_receipt", "receipt schema is invalid", { path }, 40);
  for (const key of ["receipt_id", "review_id", "manifest_hash", "base_proposal_hash", "turn_id", "attempt_id", "lease_id", "actor", "result_hash"]) {
    if (typeof receipt[key] !== "string" || receipt[key].length === 0) throw new RelayError("malformed_receipt", `receipt.${key} is required`, { path }, 40);
  }
  if (receipt.review_id !== expected.review_id || receipt.manifest_hash !== expected.manifest_hash || receipt.base_proposal_hash !== expected.proposal_hash || receipt.turn_id !== `turn-${paddedTurn(expected.turn_number)}` || receipt.attempt_id !== expected.attempt_id || receipt.lease_id !== expected.lease_id || receipt.actor !== expected.actor || receipt.result_hash !== expected.result_hash) {
    throw new RelayError("stale_receipt", "receipt identity or result hash does not match its attempt", { path }, 40);
  }
  assertWithin(path, root, "receipt path");
  return receipt;
}

async function completedAttempts(root, turnNumber, manifest) {
  const directory = turnPath(root, turnNumber);
  const names = await listDirectories(directory);
  const completed = [];
  const malformed = [];
  for (const name of names.filter((entry) => entry.startsWith("attempt-"))) {
    const path = join(directory, name);
    const claimPath = join(path, "claim.json");
    const resultPath = join(path, "result.json");
    const receiptPath = join(path, "receipt.json");
    if (!(await exists(resultPath)) && !(await exists(receiptPath))) continue;
    if (!(await exists(resultPath)) || !(await exists(receiptPath))) {
      malformed.push({ path, code: "receipt_missing", message: "committed attempts require both result.json and receipt.json" });
      continue;
    }
    try {
      const claim = await readClaim(claimPath);
      const result = await readResult(resultPath, {
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        turn_number: turnNumber,
        attempt_id: claim.attempt_id,
        lease_id: claim.lease_id,
        actor: claim.actor,
      }, root);
      const resultHash = sha256(stableStringify(result));
      const receipt = await readReceipt(receiptPath, {
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        turn_number: turnNumber,
        attempt_id: claim.attempt_id,
        lease_id: claim.lease_id,
        actor: claim.actor,
        result_hash: resultHash,
      }, root);
      completed.push({ path, claim, result, receipt, receipt_path: receiptPath });
    } catch (error) {
      malformed.push({ path, code: error.code || "malformed_attempt", message: error.message });
    }
  }
  return { completed, malformed };
}

async function enforceParentReviewGate(root, manifest, turnNumber, actor) {
  const observedActors = new Set([actor]);
  for (let priorTurn = 1; priorTurn < turnNumber; priorTurn += 1) {
    const prior = await completedAttempts(root, priorTurn, manifest);
    if (prior.malformed.length) {
      throw new RelayError(
        "needs_review",
        "cannot evaluate the parent-review gate because a prior turn is malformed",
        { turn_number: priorTurn, malformed: prior.malformed },
        40,
      );
    }
    if (prior.completed.length !== 1) {
      throw new RelayError(
        "needs_review",
        "cannot evaluate the parent-review gate because a prior turn is not committed",
        { turn_number: priorTurn, completed_attempts: prior.completed.length },
        40,
      );
    }
    observedActors.add(prior.completed[0].claim.actor);
  }

  const missingActors = actorIds(manifest).filter((requiredActor) => !observedActors.has(requiredActor));
  if (missingActors.length) {
    throw new RelayError(
      "premature_terminal_status",
      "ready_for_parent_review requires a committed turn from every declared actor",
      {
        turn_number: turnNumber,
        observed_actors: [...observedActors],
        required_actors: actorIds(manifest),
        missing_actors: missingActors,
      },
      40,
    );
  }
}

async function activeClaim(root, turnNumber, manifest, clock = Date.now) {
  const directory = activePath(root, turnNumber);
  if (!(await exists(directory))) return null;
  const claimPath = join(directory, "claim.json");
  if (!(await exists(claimPath))) {
    const metadata = await stat(directory);
    const ageSeconds = (nowMs(clock) - metadata.mtimeMs) / 1000;
    if (ageSeconds >= manifest.orphan_grace_seconds) {
      const destination = join(turnPath(root, turnNumber), `orphaned-missing-claim-${randomUUID()}`);
      try {
        await rename(directory, destination);
      } catch (error) {
        if (error.code === "ENOENT") return null;
        throw error;
      }
      await recordEvent(root, "system", "orphaned_missing_claim", { turn_number: turnNumber, path: destination }, clock);
      return null;
    }
    return { directory, pending: true, claim: null };
  }
  const claim = await readClaim(claimPath);
  if (claim.review_id !== manifest.review_id || claim.manifest_hash !== manifest.manifest_hash || claim.base_proposal_hash !== manifest.proposal.sha256 || claim.turn_number !== turnNumber || claim.turn_id !== `turn-${paddedTurn(turnNumber)}` || !actorIds(manifest).includes(claim.actor) || claim.actor !== expectedActor(manifest, turnNumber)) {
    throw new RelayError("stale_claim", "active claim belongs to another review revision", { turn_number: turnNumber }, 40);
  }
  return { directory, claim };
}

async function finalizeActive(root, turnNumber, active) {
  const destination = attemptPath(root, turnNumber, active.claim.attempt_id);
  if (await exists(destination)) {
    if (!(await exists(active.directory))) return destination;
    throw new RelayError("duplicate_attempt", "attempt destination already exists", { destination }, 40);
  }
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      await rename(active.directory, destination);
      return destination;
    } catch (error) {
      if ((error.code === "ENOENT" || error.code === "EPERM" || error.code === "EACCES") && await exists(destination)) return destination;
      if (error.code === "ENOENT" || error.code === "EPERM" || error.code === "EACCES") {
        await new Promise((resolvePromise) => setTimeout(resolvePromise, 10));
        continue;
      }
      throw error;
  }
  }
  if (await exists(destination)) return destination;
  throw new RelayError("finalize_race", "could not finalize the active attempt after concurrent rename retries", { destination }, 40);
}

async function recoverExpiredActive(root, turnNumber, active, clock = Date.now()) {
  const expires = parseTimestamp(active.claim.expires_at, "claim.expires_at");
  if (expires > nowMs(clock)) return false;
  const destination = join(turnPath(root, turnNumber), `orphaned-${active.claim.attempt_id}`);
  try {
    await rename(active.directory, destination);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
    return false;
  }
  await recordEvent(root, "system", "orphaned_expired_attempt", {
    turn_number: turnNumber,
    attempt_id: active.claim.attempt_id,
    lease_id: active.claim.lease_id,
  }, clock);
  return true;
}

async function inspectState(root, { clock = Date.now() } = {}) {
  const { manifest } = await readManifest(root);
  const currentMs = nowMs(clock);
  const turns = [];
  for (let turnNumber = 1; ; turnNumber += 1) {
    if (Number.isInteger(manifest.max_turns) && turnNumber > manifest.max_turns) {
      return {
        status: "partial",
        reason: "turn_budget_exhausted",
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        next_turn: turnNumber,
        turns,
      };
    }
    const active = await activeClaim(root, turnNumber, manifest, clock);
    if (active?.pending) {
      turns.push({ turn_number: turnNumber, status: "claim_pending", directory: active.directory });
      return {
        status: "waiting",
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        next_turn: turnNumber,
        expected_actor: expectedActor(manifest, turnNumber),
        active: { pending: true, directory: active.directory, turn_number: turnNumber },
        turns,
      };
    }
    if (active && await exists(join(active.directory, "result.json"))) {
      const result = await readResult(join(active.directory, "result.json"), {
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        turn_number: turnNumber,
        attempt_id: active.claim.attempt_id,
        lease_id: active.claim.lease_id,
        actor: active.claim.actor,
      }, root);
      const receipt = {
        schema_version: RECEIPT_SCHEMA_VERSION,
        receipt_id: `receipt-${sha256(`${manifest.review_id}:${result.attempt_id}:${sha256(stableStringify(result))}`)}`,
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        base_proposal_hash: manifest.proposal.sha256,
        turn_id: result.turn_id,
        attempt_id: result.attempt_id,
        lease_id: result.lease_id,
        actor: result.actor,
        result_hash: sha256(stableStringify(result)),
        validation: { identity: "pass", schema: "pass", content_hash: "pass", persistence: "pass" },
        created_at: result.submitted_at || iso(currentMs),
      };
      if (!(await exists(join(active.directory, "receipt.json")))) await atomicCreateJson(join(active.directory, "receipt.json"), receipt);
      await finalizeActive(root, turnNumber, active);
    }
    const refreshedActive = await activeClaim(root, turnNumber, manifest, clock);
    if (refreshedActive?.pending) {
      turns.push({ turn_number: turnNumber, status: "claim_pending", directory: refreshedActive.directory });
      return {
        status: "waiting",
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        next_turn: turnNumber,
        expected_actor: expectedActor(manifest, turnNumber),
        active: { pending: true, directory: refreshedActive.directory, turn_number: turnNumber },
        turns,
      };
    }
    if (refreshedActive) {
      if (await recoverExpiredActive(root, turnNumber, refreshedActive, clock)) {
        if (currentMs >= parseTimestamp(manifest.expires_at, "expires_at")) {
          return { status: "expired", review_id: manifest.review_id, manifest_hash: manifest.manifest_hash, proposal_hash: manifest.proposal.sha256, next_turn: turnNumber, expected_actor: expectedActor(manifest, turnNumber), turns };
        }
        return {
          status: "ready",
          review_id: manifest.review_id,
          manifest_hash: manifest.manifest_hash,
          proposal_hash: manifest.proposal.sha256,
          next_turn: turnNumber,
          expected_actor: expectedActor(manifest, turnNumber),
          previous_result_hash: turns.at(-1)?.result_hash || null,
          turns,
        };
      }
      const claim = refreshedActive.claim;
      turns.push({ turn_number: turnNumber, actor: claim.actor, attempt_id: claim.attempt_id, lease_id: claim.lease_id, status: "working", expires_at: claim.expires_at });
      return {
        status: "waiting",
        review_id: manifest.review_id,
        manifest_hash: manifest.manifest_hash,
        proposal_hash: manifest.proposal.sha256,
        next_turn: turnNumber,
        expected_actor: expectedActor(manifest, turnNumber),
        active: claim,
        turns,
      };
    }
    const completed = await completedAttempts(root, turnNumber, manifest);
    if (completed.malformed.length) {
      throw new RelayError("needs_review", "a committed turn contains malformed or stale artifacts", { turn_number: turnNumber, malformed: completed.malformed }, 40);
    }
    if (completed.completed.length > 1) {
      throw new RelayError("needs_review", "multiple committed attempts exist for one turn", { turn_number: turnNumber, attempts: completed.completed.map((entry) => entry.claim.attempt_id) }, 40);
    }
    if (completed.completed.length === 1) {
      const entry = completed.completed[0];
      turns.push({ turn_number: turnNumber, actor: entry.claim.actor, attempt_id: entry.claim.attempt_id, lease_id: entry.claim.lease_id, status: entry.result.status, result_path: join(entry.path, "result.json"), result_hash: sha256(stableStringify(entry.result)) });
      if (terminalStatus(entry.result.status)) {
        return { status: entry.result.status, review_id: manifest.review_id, manifest_hash: manifest.manifest_hash, proposal_hash: manifest.proposal.sha256, next_turn: turnNumber + 1, turns };
      }
      continue;
    }
    if (currentMs >= parseTimestamp(manifest.expires_at, "expires_at")) {
      return { status: "expired", review_id: manifest.review_id, manifest_hash: manifest.manifest_hash, proposal_hash: manifest.proposal.sha256, next_turn: turnNumber, expected_actor: expectedActor(manifest, turnNumber), turns };
    }
    return {
      status: "ready",
      review_id: manifest.review_id,
      manifest_hash: manifest.manifest_hash,
      proposal_hash: manifest.proposal.sha256,
      next_turn: turnNumber,
      expected_actor: expectedActor(manifest, turnNumber),
      previous_result_hash: turns.at(-1)?.result_hash || null,
      turns,
    };
  }
}

async function ensureTurnDirectory(root, turnNumber) {
  await mkdir(turnPath(root, turnNumber), { recursive: true });
}

/**
 * Derive a stable review key from input file paths (not content).
 * This key persists across content revisions — editing the proposal
 * creates a new revision within the same review, not a new review.
 */
function reviewKeyFromPaths(inputPaths) {
  const sorted = inputPaths.map(resolveInputPath).map(normalizedPath).sort();
  return sha256(stableStringify(sorted)).slice(0, 16);
}

function registryBucket(root, reviewKey) {
  return join(assertAbsolutePath(root, "registry_root"), `rk-${reviewKey}`);
}

function registryRecordPath(root, reviewKey, reviewId) {
  return join(registryBucket(root, reviewKey), `${reviewId}.json`);
}

function registryLockPath(root, reviewKey) {
  return join(registryBucket(root, reviewKey), ".create-lock.json");
}

function validateRegistryRecord(record, path) {
  assertObject(record, "malformed_registry_record", "registry record must be an object");
  if (record.schema_version !== REGISTRY_SCHEMA_VERSION) throw new RelayError("malformed_registry_record", "registry record schema is invalid", { path }, 40);
  assertSafeId(record.review_id, "registry.review_id");
  if (!/^[a-f0-9]{64}$/.test(record.input_set_hash)) throw new RelayError("malformed_registry_record", "registry.input_set_hash is invalid", { path }, 40);
  assertAbsolutePath(record.artifact_root, "registry.artifact_root");
  if (!Array.isArray(record.actors) || record.actors.length !== 2) throw new RelayError("malformed_registry_record", "registry.actors must contain two actors", { path }, 40);
  record.actors.forEach((actor) => assertSafeId(actor, "registry.actor"));
  parseTimestamp(record.created_at, "registry.created_at");
  parseTimestamp(record.expires_at, "registry.expires_at");
  if (record.state !== "creating" && record.state !== "active") throw new RelayError("malformed_registry_record", "registry.state is invalid", { path }, 40);
  return record;
}

async function readRegistryRecord(path) {
  return validateRegistryRecord(await readJson(path, "malformed_registry_record"), path);
}

function isTerminalRelayState(status) {
  return terminalStatus(status) || status === "expired";
}

async function listRegistryRecords({ registryRoot, sessionRoot, inputSet, inputPaths, actor, reviewId, clock }) {
  // Use reviewKey (path-derived) instead of inputSetHash (content-derived)
  const rKey = reviewKeyFromPaths(inputPaths || inputSet.files.map((f) => f.source_path));
  const bucket = registryBucket(registryRoot, rKey);
  const names = await readdir(bucket, { withFileTypes: true }).catch((error) => error.code === "ENOENT" ? [] : Promise.reject(error));
  const records = [];
  for (const entry of names) {
    if (!entry.isFile() || !entry.name.endsWith(".json") || entry.name === ".create-lock.json" || entry.name.startsWith(".orphaned-lock-")) continue;
    const path = join(bucket, entry.name);
    const record = await readRegistryRecord(path);
    // Match by reviewId if given, otherwise match by input_set_hash for same-revision
    // or include all records under the same review key (prior revisions)
    if (reviewId && record.review_id !== reviewId) continue;
    if (!reviewId && record.input_set_hash !== inputSet.inputSetHash) continue;
    if (!record.actors.includes(actor)) continue;
    if (record.state === "creating") {
      if (parseTimestamp(record.expires_at, "registry.expires_at") > nowMs(clock)) records.push({ ...record, path, pending: true, state: { status: "creating" } });
      continue;
    }
    if (!isWithin(record.artifact_root, sessionRoot)) throw new RelayError("scope_violation", "registry artifact_root escapes session_root", { artifact_root: record.artifact_root, session_root: sessionRoot }, 40);
    let manifest;
    try {
      ({ manifest } = await readManifest(record.artifact_root));
    } catch (error) {
      throw new RelayError("registry_candidate_invalid", `registry candidate cannot be read: ${error.message}`, { path, review_id: record.review_id, cause: error.code || "unknown" }, 40);
    }
    if (manifest.review_id !== record.review_id || manifest.manifest_hash !== record.manifest_hash || manifest.proposal.input_set_hash !== inputSet.inputSetHash || stableStringify(manifest.actors) !== stableStringify(record.actors)) {
      throw new RelayError("stale_registry_record", "registry record does not match its manifest", { path, review_id: record.review_id }, 40);
    }
    const state = await inspectState(record.artifact_root, { clock });
    records.push({ ...record, path, state, pending: false });
  }
  return records;
}

async function listRegistryCandidates({ registryRoot, sessionRoot, inputSet, inputPaths, actor, reviewId, clock }) {
  const records = await listRegistryRecords({ registryRoot, sessionRoot, inputSet, inputPaths, actor, reviewId, clock });
  return records.filter((record) => record.pending || !isTerminalRelayState(record.state.status));
}

async function acquireRegistryLock(registryRoot, rKey, actor, clock) {
  const bucket = registryBucket(registryRoot, rKey);
  await mkdir(bucket, { recursive: true });
  const path = registryLockPath(registryRoot, rKey);
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const currentMs = nowMs(clock);
    const lock = {
      schema_version: REGISTRY_SCHEMA_VERSION,
      lock_id: randomUUID(),
      review_key: rKey,
      actor,
      created_at: iso(currentMs),
      expires_at: iso(currentMs + REGISTRY_LOCK_SECONDS * 1000),
    };
    if (await atomicCreateJson(path, lock)) return { status: "acquired", path, lock };
    if (!(await exists(path))) continue;
    let existing;
    try {
      existing = await readJson(path, "malformed_registry_lock");
    } catch (error) {
      if (error.code === "artifact_read_error") continue;
      if (error.code === "malformed_registry_lock") {
        try {
          await rename(path, join(bucket, `.orphaned-lock-${randomUUID()}.json`));
        } catch (renameError) {
          if (renameError.code !== "ENOENT") throw renameError;
        }
        continue;
      }
      throw error;
    }
    let expiresAt;
    try {
      expiresAt = parseTimestamp(existing.expires_at, "registry lock.expires_at");
    } catch (error) {
      if (error.code !== "invalid_timestamp") throw error;
      try {
        await rename(path, join(bucket, `.orphaned-lock-${randomUUID()}.json`));
      } catch (renameError) {
        if (renameError.code !== "ENOENT") throw renameError;
      }
      continue;
    }
    if (expiresAt <= currentMs) {
      try {
        await rename(path, join(bucket, `.orphaned-lock-${randomUUID()}.json`));
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
      }
      continue;
    }
    return { status: "held", path, lock: existing };
  }
  return { status: "held", path };
}

async function releaseRegistryLock(lock) {
  if (!lock?.path || !lock.lock?.lock_id) return;
  try {
    const current = await readJson(lock.path, "malformed_registry_lock");
    if (current.lock_id === lock.lock.lock_id) await rm(lock.path, { force: true });
  } catch (error) {
    if (error.code !== "artifact_read_error" && error.code !== "ENOENT") throw error;
  }
}

export async function initReview({
  artifactRoot,
  reviewId,
  proposalPath,
  proposalPaths,
  actors = ["codex", "grok"],
  firstActor = actors[0],
  maxTurns = DEFAULT_MAX_TURNS,
  leaseSeconds = DEFAULT_LEASE_SECONDS,
  ttlSeconds = DEFAULT_TTL_SECONDS,
  orphanGraceSeconds = DEFAULT_ORPHAN_GRACE_SECONDS,
  clock = Date.now,
} = {}) {
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  assertSafeId(reviewId, "review_id");
  const inputSet = await readInputSet(proposalPaths || (proposalPath ? [proposalPath] : []));
  const source = inputSet.files[0].source_path;
  if (!Array.isArray(actors) || actors.length !== 2) throw new RelayError("invalid_manifest", "exactly two actors are required");
  actors.forEach((actor) => assertSafeId(actor, "actor"));
  if (new Set(actors).size !== actors.length) throw new RelayError("invalid_manifest", "actor IDs must be unique");
  assertSafeId(firstActor, "first_actor");
  if (!actors.includes(firstActor)) throw new RelayError("invalid_manifest", "first_actor must be one of actors");
  if (maxTurns !== null && (!Number.isInteger(maxTurns) || maxTurns < 1)) throw new RelayError("invalid_manifest", "max_turns must be null or a positive integer");
  if (!Number.isInteger(leaseSeconds) || leaseSeconds < 5 || leaseSeconds > 86400) throw new RelayError("invalid_manifest", "lease_seconds must be 5..86400");
  if (!Number.isInteger(ttlSeconds) || ttlSeconds < leaseSeconds || ttlSeconds > 90 * 24 * 60 * 60) throw new RelayError("invalid_manifest", "ttl_seconds must contain the lease and be <= 90 days");
  if (!Number.isInteger(orphanGraceSeconds) || orphanGraceSeconds < 0 || orphanGraceSeconds > 3600) throw new RelayError("invalid_manifest", "orphan_grace_seconds must be 0..3600");
  const currentMs = nowMs(clock);
  const proposal = inputSnapshot(inputSet);
  const proposalHash = sha256(proposal);
  await mkdir(dirname(root), { recursive: true });
  try {
    await mkdir(root);
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    const existingPath = join(root, "manifest.json");
    if (!(await waitForFile(existingPath))) throw new RelayError("artifact_root_exists", "artifact_root exists without a manifest; refusing to adopt it", { artifact_root: root }, 40);
    const existing = await readJson(existingPath, "malformed_manifest");
    validateManifestShape(existing, root);
    if (existing.review_id !== reviewId || existing.proposal.sha256 !== proposalHash) throw new RelayError("review_id_conflict", "artifact_root belongs to a different review or proposal", { artifact_root: root, existing_review_id: existing.review_id, requested_review_id: reviewId }, 40);
    return { status: "already_exists", artifact_root: root, review_id: reviewId, manifest: existing };
  }
  const manifestWithoutHash = {
    schema_version: RELAY_SCHEMA_VERSION,
    review_id: reviewId,
    mode: "alternating",
    actors,
    first_actor: firstActor,
    max_turns: maxTurns,
    lease_seconds: leaseSeconds,
    ttl_seconds: ttlSeconds,
    orphan_grace_seconds: orphanGraceSeconds,
    created_at: iso(currentMs),
    expires_at: iso(currentMs + ttlSeconds * 1000),
    proposal: {
      snapshot: "proposal-v1.snapshot",
      sha256: proposalHash,
      source_path: source,
      source_paths: inputSet.files.map((file) => file.source_path),
      input_set_hash: inputSet.inputSetHash,
      file_count: inputSet.files.length,
    },
    write_policy: {
      artifact_root_only: true,
      controller_registry_record: true,
      allowed_writes: ["manifest.json", "proposal-v1.snapshot", "turns/**", "events/**", "handoff-candidate.v1.json"],
      forbidden_writes: ["source files", "repositories", "worktrees", "configs", "credentials", "P:/docs/handoffs", "P:/.data/wiki"],
    },
    event_layout: "events/<actor>/<YYYY-MM-DD>/<event_id>.json",
  };
  const manifest = { ...manifestWithoutHash, manifest_hash: sha256(stableStringify(manifestWithoutHash)) };
  await atomicWrite(join(root, "proposal-v1.snapshot"), proposal);
  await atomicWriteJson(join(root, "manifest.json"), manifest);
  const event = await recordEvent(root, "operator", "review_initialized", { review_id: reviewId, proposal_hash: proposalHash }, clock);
  return { status: "created", artifact_root: root, review_id: reviewId, manifest, event };
}

function buildRelayHandoff({ inputSet, actor, reviewId = null, artifactRoot = null, registryRecordPath = null, manifestHash = null, tick = null }) {
  const root = artifactRoot ? resolve(artifactRoot) : null;
  const proposalSnapshot = root ? join(root, "proposal-v1.snapshot") : null;
  const active = tick?.status === "waiting" && tick.active && !tick.active.pending ? tick.active : null;
  const partnerActive = active && active.actor !== actor && Number.isInteger(active.turn_number) && typeof active.attempt_id === "string";
  const committedRoot = partnerActive ? attemptPath(root, active.turn_number, active.attempt_id) : null;
  const previousResultPath = tick?.previous_result_path || null;
  const previousResultRoot = previousResultPath ? dirname(previousResultPath) : null;
  const receiveFromPartner = previousResultPath
    ? {
      status: "committed_previous_turn",
      actor: tick?.previous_result_actor || null,
      turn_number: tick?.turn_number ? tick.turn_number - 1 : null,
      attempt_id: null,
      result_path: previousResultPath,
      receipt_path: join(previousResultRoot, "receipt.json"),
    }
    : partnerActive
      ? {
        status: "awaiting_partner_commit",
        actor: active.actor,
        turn_number: active.turn_number,
        attempt_id: active.attempt_id,
        result_path: join(committedRoot, "result.json"),
        receipt_path: join(committedRoot, "receipt.json"),
      }
      : {
        status: tick?.status === "act" || tick?.status === "continue" ? "not_waiting_for_partner" : "awaiting_controller_state",
        actor: tick?.expected_actor || null,
        turn_number: tick?.next_turn || tick?.turn_number || null,
        attempt_id: null,
        result_path: null,
        receipt_path: null,
      };

  return {
    schema_version: HANDOFF_SCHEMA_VERSION,
    actor,
    send_to_partner: {
      input_paths: inputSet.files.map((file) => file.source_path),
      input_set_hash: inputSet.inputSetHash,
      review_id: reviewId,
      instruction: "Invoke the relay skill with these exact input paths; do not choose a newest file or a different session.",
    },
    receive_from_partner: receiveFromPartner,
    current_turn: {
      status: tick?.status || "not_started",
      read_paths: {
        turn_input: tick?.input_path || null,
        proposal_snapshot: tick?.proposal_snapshot || proposalSnapshot,
        previous_result: previousResultPath,
      },
      write_paths: {
        result_input: tick?.result_input_path || null,
      },
    },
    session: {
      review_id: reviewId,
      artifact_root: root,
      registry_record: registryRecordPath,
      manifest: root ? join(root, "manifest.json") : null,
      proposal_snapshot: proposalSnapshot,
      manifest_hash: manifestHash,
    },
  };
}

async function returnAttachedCandidate(candidate, inputSet, actor, clock) {
  const tick = await tickReview({ artifactRoot: candidate.artifact_root, actor, clock });
  return {
    status: "attached",
    review_id: candidate.review_id,
    artifact_root: candidate.artifact_root,
    registry_record_path: candidate.path,
    input_set_hash: inputSet.inputSetHash,
    manifest_hash: candidate.manifest_hash,
    actor,
    tick,
    handoff: buildRelayHandoff({
      inputSet,
      actor,
      reviewId: candidate.review_id,
      artifactRoot: candidate.artifact_root,
      registryRecordPath: candidate.path,
      manifestHash: candidate.manifest_hash,
      tick,
    }),
  };
}

async function listMatchingTerminalRecords({ registryRoot, sessionRoot, inputSet, inputPaths, actor, reviewId, clock }) {
  const records = await listRegistryRecords({ registryRoot, sessionRoot, inputSet, inputPaths, actor, reviewId, clock });
  return records.filter((record) => !record.pending && isTerminalRelayState(record.state.status));
}

async function returnTerminalCandidate(candidate, inputSet, actor) {
  return {
    status: "terminal",
    reason: "matching_content_already_terminal",
    review_id: candidate.review_id,
    artifact_root: candidate.artifact_root,
    registry_record_path: candidate.path,
    input_set_hash: inputSet.inputSetHash,
    manifest_hash: candidate.manifest_hash,
    actor,
    state: candidate.state,
    handoff: buildRelayHandoff({
      inputSet,
      actor,
      reviewId: candidate.review_id,
      artifactRoot: candidate.artifact_root,
      registryRecordPath: candidate.path,
      manifestHash: candidate.manifest_hash,
      tick: candidate.state,
    }),
  };
}

export async function startOrJoinReview({
  inputPaths,
  proposalPaths,
  actor,
  registryRoot = DEFAULT_REGISTRY_ROOT,
  sessionRoot = DEFAULT_SESSION_ROOT,
  reviewId,
  actors = ["codex", "grok"],
  firstActor,
  maxTurns = DEFAULT_MAX_TURNS,
  leaseSeconds = DEFAULT_LEASE_SECONDS,
  ttlSeconds = DEFAULT_TTL_SECONDS,
  orphanGraceSeconds = DEFAULT_ORPHAN_GRACE_SECONDS,
  clock = Date.now,
} = {}) {
  assertSafeId(actor, "actor");
  const inputSet = await readInputSet(inputPaths || proposalPaths);
  const registry = assertAbsolutePath(registryRoot, "registry_root");
  const sessions = assertAbsolutePath(sessionRoot, "session_root");
  if (!Array.isArray(actors) || actors.length !== 2 || !actors.includes(actor)) throw new RelayError("invalid_manifest", "actor must be one of the two relay actors");
  const inputPathList = inputPaths || proposalPaths || [];
  const candidates = await listRegistryCandidates({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
  if (candidates.length > 1) {
    throw new RelayError("ambiguous_session", "multiple active relay sessions match these input files", {
      input_set_hash: inputSet.inputSetHash,
      candidates: candidates.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state || "creating" })),
    }, 40);
  }
  if (candidates.length === 1 && !candidates[0].pending) return returnAttachedCandidate(candidates[0], inputSet, actor, clock);
  if (candidates.length === 0) {
    const terminals = await listMatchingTerminalRecords({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
    if (terminals.length > 1) {
      throw new RelayError("ambiguous_session", "multiple terminal relay sessions match these input files", {
        input_set_hash: inputSet.inputSetHash,
        candidates: terminals.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state })),
      }, 40);
    }
    if (terminals.length === 1) return returnTerminalCandidate(terminals[0], inputSet, actor);
  }
  if (candidates.length === 1 && candidates[0].pending) {
    for (let attempt = 0; attempt < REGISTRY_WAIT_ATTEMPTS; attempt += 1) {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, REGISTRY_WAIT_INTERVAL_MS));
      const ready = await listRegistryCandidates({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
      if (ready.length > 1) throw new RelayError("ambiguous_session", "multiple active relay sessions match these input files", { input_set_hash: inputSet.inputSetHash, candidates: ready.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state || "creating" })) }, 40);
      if (ready.length === 1 && !ready[0].pending) return returnAttachedCandidate(ready[0], inputSet, actor, clock);
    }
    return {
      status: "joining",
      reason: "session_creation_in_progress",
      input_set_hash: inputSet.inputSetHash,
      actor,
      handoff: buildRelayHandoff({ inputSet, actor, tick: { status: "joining" } }),
    };
  }

  const rKey = reviewKeyFromPaths(inputSet.files.map((f) => f.source_path));
  const lock = await acquireRegistryLock(registry, rKey, actor, clock);
  if (lock.status === "held") {
    for (let attempt = 0; attempt < REGISTRY_WAIT_ATTEMPTS; attempt += 1) {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, REGISTRY_WAIT_INTERVAL_MS));
      const ready = await listRegistryCandidates({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
      if (ready.length > 1) throw new RelayError("ambiguous_session", "multiple active relay sessions match these input files", { input_set_hash: inputSet.inputSetHash, candidates: ready.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state || "creating" })) }, 40);
      if (ready.length === 1 && !ready[0].pending) return returnAttachedCandidate(ready[0], inputSet, actor, clock);
    }
    return {
      status: "joining",
      reason: "session_creation_in_progress",
      input_set_hash: inputSet.inputSetHash,
      actor,
      handoff: buildRelayHandoff({ inputSet, actor, tick: { status: "joining" } }),
    };
  }

  try {
    const afterLock = await listRegistryCandidates({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
    if (afterLock.length > 1) throw new RelayError("ambiguous_session", "multiple active relay sessions match these input files", { input_set_hash: inputSet.inputSetHash, candidates: afterLock.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state || "creating" })) }, 40);
    if (afterLock.length === 1 && !afterLock[0].pending) return returnAttachedCandidate(afterLock[0], inputSet, actor, clock);
    if (afterLock.length === 0) {
      const terminals = await listMatchingTerminalRecords({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPathList, actor, reviewId, clock });
      if (terminals.length > 1) {
        throw new RelayError("ambiguous_session", "multiple terminal relay sessions match these input files", {
          input_set_hash: inputSet.inputSetHash,
          candidates: terminals.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state })),
        }, 40);
      }
      if (terminals.length === 1) return returnTerminalCandidate(terminals[0], inputSet, actor);
    }
    const id = reviewId || `review-${inputSet.inputSetHash.slice(0, 12)}-${randomUUID().slice(0, 8)}`;
    assertSafeId(id, "review_id");
    const artifactRoot = join(sessions, id);
    const initialized = await initReview({
      artifactRoot,
      reviewId: id,
      proposalPaths: inputSet.files.map((file) => file.source_path),
      actors,
      firstActor: firstActor || actor,
      maxTurns,
      leaseSeconds,
      ttlSeconds,
      orphanGraceSeconds,
      clock,
    });
    const recordPath = registryRecordPath(registry, rKey, id);
    const record = {
      schema_version: REGISTRY_SCHEMA_VERSION,
      state: "active",
      review_id: id,
      input_set_hash: inputSet.inputSetHash,
      input_files: inputSet.files.map(({ source_path, size, sha256: contentHash }) => ({ source_path, size, sha256: contentHash })),
      artifact_root: initialized.artifact_root,
      session_root: sessions,
      manifest_hash: initialized.manifest.manifest_hash,
      actors,
      creator_actor: actor,
      created_at: initialized.manifest.created_at,
      expires_at: initialized.manifest.expires_at,
    };
    await atomicWriteJson(recordPath, record);
    const tick = await tickReview({ artifactRoot, actor, clock });
    return {
      status: "created",
      review_id: id,
      artifact_root: artifactRoot,
      registry_record_path: recordPath,
      input_set_hash: inputSet.inputSetHash,
      manifest_hash: initialized.manifest.manifest_hash,
      actor,
      tick,
      handoff: buildRelayHandoff({
        inputSet,
        actor,
        reviewId: id,
        artifactRoot,
        registryRecordPath: recordPath,
        manifestHash: initialized.manifest.manifest_hash,
        tick,
      }),
    };
  } finally {
    await releaseRegistryLock(lock);
  }
}

/**
 * Poll-safe entry point for a host scheduler.
 *
 * Unlike startOrJoinReview, this operation will not start a duplicate review
 * after the exact input bundle has already reached a terminal state. A new
 * session is created only when the current source bytes produce an input-set
 * hash that has no existing session. This makes a recurring file watcher safe
 * across restarts while still detecting a changed proposal automatically.
 */
export async function watchReview({
  inputPaths,
  proposalPaths,
  actor,
  registryRoot = DEFAULT_REGISTRY_ROOT,
  sessionRoot = DEFAULT_SESSION_ROOT,
  reviewId,
  actors = ["codex", "grok"],
  firstActor,
  maxTurns = DEFAULT_MAX_TURNS,
  leaseSeconds = DEFAULT_LEASE_SECONDS,
  ttlSeconds = DEFAULT_TTL_SECONDS,
  orphanGraceSeconds = DEFAULT_ORPHAN_GRACE_SECONDS,
  clock = Date.now,
} = {}) {
  assertSafeId(actor, "actor");
  const inputSet = await readInputSet(inputPaths || proposalPaths);
  const registry = assertAbsolutePath(registryRoot, "registry_root");
  const sessions = assertAbsolutePath(sessionRoot, "session_root");
  const records = await listRegistryRecords({ registryRoot: registry, sessionRoot: sessions, inputSet, inputPaths: inputPaths || proposalPaths || [], actor, reviewId, clock });
  const active = records.filter((record) => !record.pending && !isTerminalRelayState(record.state.status));
  if (active.length > 1) {
    throw new RelayError("ambiguous_session", "multiple active relay sessions match these input files", {
      input_set_hash: inputSet.inputSetHash,
      candidates: active.map((candidate) => ({ review_id: candidate.review_id, artifact_root: candidate.artifact_root, state: candidate.state })),
    }, 40);
  }
  if (active.length === 1) return returnAttachedCandidate(active[0], inputSet, actor, clock);

  const pending = records.filter((record) => record.pending);
  if (pending.length > 0) {
    return startOrJoinReview({
      inputPaths: inputSet.files.map((file) => file.source_path),
      actor,
      registryRoot: registry,
      sessionRoot: sessions,
      reviewId,
      actors,
      firstActor,
      maxTurns,
      leaseSeconds,
      ttlSeconds,
      orphanGraceSeconds,
      clock,
    });
  }

  if (records.length > 1) {
    throw new RelayError("ambiguous_session", "multiple terminal relay sessions match these unchanged input files; refusing to restart one", {
      input_set_hash: inputSet.inputSetHash,
      candidates: records.map((record) => ({ review_id: record.review_id, artifact_root: record.artifact_root, state: record.state })),
    }, 40);
  }
  if (records.length === 1) {
    const terminal = records[0];
    return {
      status: "terminal",
      reason: "matching_content_already_terminal",
      review_id: terminal.review_id,
      artifact_root: terminal.artifact_root,
      registry_record_path: terminal.path,
      input_set_hash: inputSet.inputSetHash,
      manifest_hash: terminal.manifest_hash,
      actor,
      state: terminal.state,
    };
  }

  return startOrJoinReview({
    inputPaths: inputSet.files.map((file) => file.source_path),
    actor,
    registryRoot: registry,
    sessionRoot: sessions,
    reviewId,
    actors,
    firstActor,
    maxTurns,
    leaseSeconds,
    ttlSeconds,
    orphanGraceSeconds,
    clock,
  });
}

async function claimTurn(root, actor, state, clock = Date.now) {
  const { manifest } = await readManifest(root);
  if (state.status !== "ready") return { status: state.status, ...state };
  if (state.expected_actor !== actor) return { status: "waiting", reason: "not_this_actor", ...state };
  if (Number.isInteger(manifest.max_turns) && state.next_turn > manifest.max_turns) return { status: "partial", reason: "turn_budget_exhausted", ...state };
  await ensureTurnDirectory(root, state.next_turn);
  const directory = activePath(root, state.next_turn);
  const attemptId = randomUUID();
  const leaseId = randomUUID();
  try {
    await mkdir(directory);
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    return { status: "waiting", reason: "another_attempt_claimed_turn", ...(await inspectState(root, { clock })) };
  }
  const currentMs = nowMs(clock);
  const previousTurn = state.turns.at(-1);
  const claim = {
    schema_version: "review-claim.v1",
    review_id: manifest.review_id,
    manifest_hash: manifest.manifest_hash,
    base_proposal_hash: manifest.proposal.sha256,
    turn_id: `turn-${paddedTurn(state.next_turn)}`,
    turn_number: state.next_turn,
    attempt_id: attemptId,
    lease_id: leaseId,
    actor,
    claimed_at: iso(currentMs),
    expires_at: iso(currentMs + manifest.lease_seconds * 1000),
    previous_result_hash: state.turns.at(-1)?.result_hash || null,
  };
  const input = {
    schema_version: TURN_INPUT_SCHEMA_VERSION,
    review_id: manifest.review_id,
    manifest_hash: manifest.manifest_hash,
    proposal_revision: 1,
    base_proposal_hash: manifest.proposal.sha256,
    proposal_snapshot: join(root, manifest.proposal.snapshot),
    turn_id: claim.turn_id,
    turn_number: claim.turn_number,
    attempt_id: claim.attempt_id,
    lease_id: claim.lease_id,
    actor,
    previous_result_hash: claim.previous_result_hash,
    previous_result_path: previousTurn?.result_path || null,
    previous_result_actor: previousTurn?.actor || null,
    output_path: join(directory, "result-input.json"),
    forbidden_writes: manifest.write_policy.forbidden_writes,
    stop_condition: "Write one structured result, then stop; do not modify the proposal or shared state.",
  };
  await atomicWriteJson(join(directory, "claim.json"), claim);
  await atomicWriteJson(join(directory, "input.json"), input);
  const event = await recordEvent(root, actor, "turn_claimed", { turn_number: claim.turn_number, attempt_id: attemptId, lease_id: leaseId }, clock);
  return {
    status: "act",
    review_id: manifest.review_id,
    turn_number: claim.turn_number,
    turn_id: claim.turn_id,
    attempt_id: attemptId,
    lease_id: leaseId,
    expires_at: claim.expires_at,
    previous_result_path: previousTurn?.result_path || null,
    previous_result_actor: previousTurn?.actor || null,
    input_path: join(directory, "input.json"),
    result_input_path: join(directory, "result-input.json"),
    proposal_snapshot: join(root, manifest.proposal.snapshot),
    event,
  };
}

export async function tickReview({ artifactRoot, actor, clock = Date.now } = {}) {
  assertSafeId(actor, "actor");
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const { manifest } = await readManifest(root);
  if (!actorIds(manifest).includes(actor)) throw new RelayError("invalid_actor", "actor is not declared in the review manifest");
  const state = await inspectState(root, { clock });
  if (state.status !== "ready") {
    if (state.status === "waiting" && state.active?.actor === actor) {
      const previousTurn = state.turns.at(-1);
      return {
        status: "continue",
        reason: "active_lease",
        review_id: manifest.review_id,
        turn_number: state.next_turn,
        attempt_id: state.active.attempt_id,
        lease_id: state.active.lease_id,
        expires_at: state.active.expires_at,
        previous_result_path: previousTurn?.result_path || null,
        previous_result_actor: previousTurn?.actor || null,
        input_path: join(activePath(root, state.next_turn), "input.json"),
        result_input_path: join(activePath(root, state.next_turn), "result-input.json"),
      };
    }
    return { status: state.status, review_id: manifest.review_id, next_turn: state.next_turn, expected_actor: state.expected_actor || null, active: state.active || null, turns: state.turns || [] };
  }
  return claimTurn(root, actor, state, clock);
}

export async function heartbeatTurn({ artifactRoot, actor, attemptId, leaseId, clock = Date.now } = {}) {
  assertSafeId(actor, "actor");
  assertSafeId(attemptId, "attempt_id");
  assertSafeId(leaseId, "lease_id");
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const { manifest } = await readManifest(root);
  for (const turnNumber of await turnNumbers(root)) {
    const active = await activeClaim(root, turnNumber, manifest, clock);
    if (!active || active.pending) continue;
    if (active.claim.attempt_id !== attemptId) continue;
    if (active.claim.actor !== actor || active.claim.lease_id !== leaseId) throw new RelayError("identity_mismatch", "heartbeat identity does not match the active lease", undefined, 40);
    const currentMs = nowMs(clock);
    if (parseTimestamp(active.claim.expires_at, "claim.expires_at") <= currentMs) throw new RelayError("lease_expired", "cannot heartbeat an expired lease", undefined, 40);
    const heartbeat = {
      schema_version: "review-heartbeat.v1",
      review_id: manifest.review_id,
      manifest_hash: manifest.manifest_hash,
      base_proposal_hash: manifest.proposal.sha256,
      turn_id: active.claim.turn_id,
      turn_number: turnNumber,
      attempt_id: attemptId,
      lease_id: leaseId,
      actor,
      observed_at: iso(currentMs),
      lease_expires_at: active.claim.expires_at,
    };
    await atomicWriteJson(join(active.directory, "heartbeat.json"), heartbeat);
    const event = await recordEvent(root, actor, "heartbeat", { turn_number: turnNumber, attempt_id: attemptId, lease_id: leaseId }, clock);
    return { status: "ok", ...heartbeat, heartbeat_path: join(active.directory, "heartbeat.json"), event };
  }
  throw new RelayError("attempt_not_found", "active attempt was not found", { attempt_id: attemptId }, 40);
}

export async function submitTurn({ artifactRoot, actor, attemptId, leaseId, resultPath, clock = Date.now } = {}) {
  assertSafeId(actor, "actor");
  assertSafeId(attemptId, "attempt_id");
  assertSafeId(leaseId, "lease_id");
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const { manifest } = await readManifest(root);
  const suppliedPath = assertAbsolutePath(resultPath, "result_path");
  assertWithin(suppliedPath, root, "result_path");
  const currentMs = nowMs(clock);
  for (const turnNumber of await turnNumbers(root)) {
    const active = await activeClaim(root, turnNumber, manifest, clock);
    if (!active || active.pending) continue;
    if (active.claim.attempt_id !== attemptId) continue;
    if (active.claim.actor !== actor || active.claim.lease_id !== leaseId) throw new RelayError("identity_mismatch", "submission identity does not match active lease", undefined, 40);
    const expectedInputPath = join(active.directory, "result-input.json");
    if (normalizedPath(suppliedPath) !== normalizedPath(expectedInputPath)) throw new RelayError("scope_violation", "result_path must be the active turn result-input.json", { expected: expectedInputPath, actual: suppliedPath }, 40);
    const supplied = await readJson(suppliedPath, "malformed_result_input");
    assertObject(supplied, "malformed_result_input", "result input must be an object");
    if (typeof supplied.status !== "string" || !RESULT_STATUSES.has(supplied.status)) throw new RelayError("malformed_result_input", "result.status is unsupported");
    const activeResultPath = join(active.directory, "result.json");
    if (await exists(activeResultPath)) {
      const existing = await readJson(activeResultPath, "malformed_result");
      const existingContentHash = existing.content_hash;
      const incomingContentHash = sha256(stableStringify(supplied));
      if (existingContentHash === incomingContentHash) {
        const existingResultHash = sha256(stableStringify(existing));
        const receipt = makeReceipt(manifest, existing, currentMs);
        if (!(await exists(join(active.directory, "receipt.json")))) await atomicCreateJson(join(active.directory, "receipt.json"), receipt);
        const completedPath = await finalizeActive(root, turnNumber, active);
        return { status: "idempotent", review_id: manifest.review_id, turn_number: turnNumber, attempt_id: attemptId, result_path: join(completedPath, "result.json"), result_hash: existingResultHash };
      }
      throw new RelayError("conflicting_duplicate", "a different result already exists for this attempt", { attempt_id: attemptId }, 40);
    }
    if (parseTimestamp(active.claim.expires_at, "claim.expires_at") <= currentMs) throw new RelayError("lease_expired", "cannot submit after the lease expires", undefined, 40);
    if (supplied.review_id && supplied.review_id !== manifest.review_id) throw new RelayError("stale_result", "result review_id does not match manifest", undefined, 40);
    if (supplied.base_proposal_hash && supplied.base_proposal_hash !== manifest.proposal.sha256) throw new RelayError("stale_result", "result base_proposal_hash does not match manifest", undefined, 40);
    if (supplied.status === "ready_for_parent_review") await enforceParentReviewGate(root, manifest, turnNumber, actor);
    const result = {
      schema_version: RESULT_SCHEMA_VERSION,
      review_id: manifest.review_id,
      manifest_hash: manifest.manifest_hash,
      proposal_revision: 1,
      base_proposal_hash: manifest.proposal.sha256,
      turn_id: active.claim.turn_id,
      turn_number: turnNumber,
      attempt_id: attemptId,
      lease_id: leaseId,
      actor,
      status: supplied.status,
      submitted_at: iso(currentMs),
      content_hash: sha256(stableStringify(supplied)),
      review: supplied,
    };
    const resultCreated = await atomicCreateJson(activeResultPath, result);
    if (!resultCreated) {
      const existing = await readJson(activeResultPath, "malformed_result");
      if (existing.content_hash !== result.content_hash) throw new RelayError("conflicting_duplicate", "a different result won the concurrent submission race", { attempt_id: attemptId }, 40);
      const receipt = makeReceipt(manifest, existing, currentMs);
      if (!(await exists(join(active.directory, "receipt.json")))) await atomicCreateJson(join(active.directory, "receipt.json"), receipt);
      const completedPath = await finalizeActive(root, turnNumber, active);
      return { status: "idempotent", review_id: manifest.review_id, turn_number: turnNumber, attempt_id: attemptId, result_path: join(completedPath, "result.json"), result_hash: sha256(stableStringify(existing)) };
    }
    const completedPath = attemptPath(root, turnNumber, attemptId);
    const event = await recordEvent(root, actor, "turn_submitted", { turn_number: turnNumber, attempt_id: attemptId, lease_id: leaseId, status: supplied.status, result_path: join(completedPath, "result.json") }, clock);
    const receipt = makeReceipt(manifest, result, currentMs, event);
    await atomicWriteJson(join(active.directory, "receipt.json"), receipt);
    await finalizeActive(root, turnNumber, active);
    return { status: "submitted", review_id: manifest.review_id, turn_number: turnNumber, attempt_id: attemptId, result_path: join(completedPath, "result.json"), receipt_path: join(completedPath, "receipt.json"), next_actor: terminalStatus(supplied.status) ? null : expectedActor(manifest, turnNumber + 1), event };
  }
  const state = await inspectState(root, { clock });
  const existing = state.turns.find((turn) => turn.attempt_id === attemptId);
  if (existing) {
    const committedInputPath = existing.result_path ? join(dirname(existing.result_path), "result-input.json") : null;
    if (committedInputPath && await exists(committedInputPath) && await exists(suppliedPath) && normalizedPath(committedInputPath) === normalizedPath(suppliedPath)) {
      const committedResult = await readJson(existing.result_path, "malformed_result");
      const incoming = await readJson(suppliedPath, "malformed_result_input");
      if (sha256(stableStringify(incoming)) !== committedResult.content_hash) throw new RelayError("conflicting_duplicate", "a different result was supplied for a committed attempt", { attempt_id: attemptId }, 40);
    }
    return { status: "idempotent", review_id: manifest.review_id, turn_number: existing.turn_number, attempt_id: attemptId, result_path: existing.result_path || null };
  }
  throw new RelayError("attempt_not_found", "active attempt was not found", { attempt_id: attemptId }, 40);
}

export async function readRelayStatus({ artifactRoot, clock = Date.now } = {}) {
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const { manifest } = await readManifest(root);
  const state = await inspectState(root, { clock });
  const eventRoot = join(root, "events");
  let eventCount = 0;
  async function count(dir) {
    for (const name of await readdir(dir, { withFileTypes: true }).catch((error) => error.code === "ENOENT" ? [] : Promise.reject(error))) {
      const path = join(dir, name.name);
      if (name.isDirectory()) await count(path);
      else if (name.isFile() && name.name.endsWith(".json")) eventCount += 1;
    }
  }
  await count(eventRoot);
  return { ...state, artifact_root: root, review_id: manifest.review_id, manifest_hash: manifest.manifest_hash, event_count: eventCount, expires_at: manifest.expires_at, max_turns: manifest.max_turns };
}

export async function writeHandoffCandidate({ artifactRoot, allowCheckpoint = false, clock = Date.now } = {}) {
  const root = assertAbsolutePath(artifactRoot, "artifact_root");
  const { manifest } = await readManifest(root);
  const state = await inspectState(root, { clock });
  if (!allowCheckpoint && !terminalStatus(state.status)) throw new RelayError("handoff_requires_terminal", "handoff candidate requires a terminal review state or explicit checkpoint mode", { status: state.status }, 30);
  const candidate = {
    schema_version: "review-relay-handoff-candidate.v1",
    review_id: manifest.review_id,
    manifest_hash: manifest.manifest_hash,
    proposal_hash: manifest.proposal.sha256,
    status: state.status,
    artifact_root: root,
    proposal_snapshot: join(root, manifest.proposal.snapshot),
    created_at: iso(nowMs(clock)),
    resume_command: `node "P:/packages/codex-external-delegation/bin/review-relay.mjs" tick --artifact-root "${root}" --actor <codex|grok>`,
    turns: state.turns,
    unresolved: state.turns.flatMap((turn) => turn.result_path ? [] : [{ turn_number: turn.turn_number, reason: "no committed result" }]),
    external_write_required: true,
    external_write_target: "P:/docs/handoffs/<review-relay-review-id>/HANDOFF.md",
    next_action: state.status === "ready" || state.status === "waiting" ? `Wait for ${state.expected_actor || "the active actor"} and invoke the relay tick.` : "Parent/user reviews the candidate and decides whether to accept or resume.",
    note: "This is a scratchpad candidate only. A human must explicitly invoke Grok /handoff to write a durable handoff.",
  };
  await atomicWriteJson(join(root, "handoff-candidate.v1.json"), candidate);
  const event = await recordEvent(root, "operator", "handoff_candidate_written", { status: state.status }, clock);
  return { status: "written", path: join(root, "handoff-candidate.v1.json"), candidate, event };
}

function makeReceipt(manifest, result, clock = Date.now, event = { status: "not_recorded", failure_class: "not_attempted" }) {
  const resultHash = sha256(stableStringify(result));
  return {
    schema_version: RECEIPT_SCHEMA_VERSION,
    receipt_id: `receipt-${sha256(`${manifest.review_id}:${result.attempt_id}:${resultHash}`)}`,
    review_id: manifest.review_id,
    manifest_hash: manifest.manifest_hash,
    base_proposal_hash: manifest.proposal.sha256,
    turn_id: result.turn_id,
    attempt_id: result.attempt_id,
    lease_id: result.lease_id,
    actor: result.actor,
    result_hash: resultHash,
    validation: { identity: "pass", schema: "pass", content_hash: "pass", persistence: "pass" },
    event,
    created_at: result.submitted_at || iso(nowMs(clock)),
  };
}

export { inspectState, readManifest, expectedActor, terminalStatus };
