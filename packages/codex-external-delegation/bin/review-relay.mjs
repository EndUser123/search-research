#!/usr/bin/env node
import {
  RelayError,
  heartbeatTurn,
  initReview,
  readRelayStatus,
  startOrJoinReview,
  submitTurn,
  tickReview,
  watchReview,
  writeHandoffCandidate,
} from "../src/review-relay.mjs";

const COMMANDS = new Set(["init", "start-or-join", "watch", "tick", "heartbeat", "submit", "status", "handoff-candidate"]);
const ALLOWED_OPTIONS = {
  init: new Set(["artifact_root", "review_id", "proposal", "actors", "first_actor", "max_turns", "lease_seconds", "ttl_seconds", "orphan_grace_seconds"]),
  "start-or-join": new Set(["actor", "registry_root", "session_root", "review_id", "first_actor", "max_turns", "lease_seconds", "ttl_seconds", "orphan_grace_seconds"]),
  watch: new Set(["actor", "registry_root", "session_root", "review_id", "first_actor", "max_turns", "lease_seconds", "ttl_seconds", "orphan_grace_seconds"]),
  tick: new Set(["artifact_root", "actor"]),
  heartbeat: new Set(["artifact_root", "actor", "attempt_id", "lease_id"]),
  submit: new Set(["artifact_root", "actor", "attempt_id", "lease_id", "result_file"]),
  status: new Set(["artifact_root"]),
  "handoff-candidate": new Set(["artifact_root", "allow_checkpoint"]),
};

function usage() {
  return `Usage:
  node bin/review-relay.mjs init --artifact-root <path> --review-id <id> --proposal <path> [options]
  node bin/review-relay.mjs start-or-join --actor <codex|grok> <file> [file...]
  node bin/review-relay.mjs watch --actor <codex|grok> <file> [file...]
  node bin/review-relay.mjs tick --artifact-root <path> --actor <codex|grok>
  node bin/review-relay.mjs heartbeat --artifact-root <path> --actor <id> --attempt-id <id> --lease-id <id>
  node bin/review-relay.mjs submit --artifact-root <path> --actor <id> --attempt-id <id> --lease-id <id> --result-file <path>
  node bin/review-relay.mjs status --artifact-root <path>
  node bin/review-relay.mjs handoff-candidate --artifact-root <path> [--allow-checkpoint]

Options for init:
  --actors codex,grok             Exactly two actor IDs (default: codex,grok)
  --first-actor <id>              Actor that claims turn 1 (default: first actor)
  --max-turns <n>                 Optional explicit turn fuse (default: unlimited)
  --lease-seconds <n>             Claim lease duration (default: 120)
  --ttl-seconds <n>               Review expiry (default: 604800)
  --orphan-grace-seconds <n>      Grace for a claim directory before orphaning (default: 30)

Options for start-or-join:
  --registry-root <path>         Shared discovery registry (default: P:/tmp/review-relay/registry)
  --session-root <path>          Session artifact parent (default: P:/tmp/review-relay/sessions)
  --review-id <id>               Attach/create a specific review when supplied
  --first-actor <id>             Actor that claims turn 1 (default: current actor)
  --max-turns <n>                Optional explicit turn fuse (default: unlimited)
  --lease-seconds <n>            Claim lease duration (default: 120)
  --ttl-seconds <n>              Review expiry (default: 604800)
  --orphan-grace-seconds <n>     Grace for a claim directory before orphaning (default: 30)

Options for watch:
  --registry-root <path>         Shared discovery registry (default: P:/tmp/review-relay/registry)
  --session-root <path>          Session artifact parent (default: P:/tmp/review-relay/sessions)
  --review-id <id>               Attach/create a specific review when supplied
  --first-actor <id>             Actor that claims turn 1 (default: current actor)
  --max-turns <n>                Optional explicit turn fuse (default: unlimited)
  --lease-seconds <n>            Claim lease duration (default: 120)
  --ttl-seconds <n>              Review expiry (default: 604800)
  --orphan-grace-seconds <n>     Grace for a claim directory before orphaning (default: 30)

All commands emit one JSON object. Relay artifacts are written only below the
declared artifact root; source, worktree, config, credential, handoff, and wiki
paths are outside the relay write scope.`;
}

function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!command || command === "--help" || command === "-h") return { help: true };
  if (!COMMANDS.has(command)) throw new RelayError("invalid_command", `unsupported command: ${command}`);
  const options = { command, inputs: [] };
  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (!token.startsWith("--")) {
      if (command === "start-or-join" || command === "watch") {
        options.inputs.push(token);
        continue;
      }
      throw new RelayError("invalid_argument", `unexpected argument: ${token}`);
    }
    const key = token.slice(2).replaceAll("-", "_");
    if (!ALLOWED_OPTIONS[command].has(key)) throw new RelayError("invalid_argument", `--${key.replaceAll("_", "-")} is not valid for ${command}`);
    if (key === "allow_checkpoint") {
      options[key] = true;
      continue;
    }
    const value = rest[index + 1];
    if (!value || value.startsWith("--")) throw new RelayError("invalid_argument", `${token} requires a value`);
    options[key] = value;
    index += 1;
  }
  return options;
}

function required(options, key) {
  if (typeof options[key] !== "string" || options[key].length === 0) throw new RelayError("invalid_argument", `--${key.replaceAll("_", "-")} is required`);
  return options[key];
}

function integer(options, key, fallback) {
  if (options[key] === undefined) return fallback;
  const value = Number(options[key]);
  if (!Number.isInteger(value)) throw new RelayError("invalid_argument", `--${key.replaceAll("_", "-")} must be an integer`);
  return value;
}

async function execute(options) {
  if (options.help) return { status: "help", usage: usage() };
  const artifactRoot = options.artifact_root;
  switch (options.command) {
    case "init": {
      const actors = String(options.actors || "codex,grok").split(",").map((value) => value.trim()).filter(Boolean);
      return initReview({
        artifactRoot: required(options, "artifact_root"),
        reviewId: required(options, "review_id"),
        proposalPath: required(options, "proposal"),
        actors,
        firstActor: options.first_actor || actors[0],
        maxTurns: integer(options, "max_turns", null),
        leaseSeconds: integer(options, "lease_seconds", 120),
        ttlSeconds: integer(options, "ttl_seconds", 7 * 24 * 60 * 60),
        orphanGraceSeconds: integer(options, "orphan_grace_seconds", 30),
      });
    }
    case "start-or-join":
      return startOrJoinReview({
        inputPaths: options.inputs,
        actor: required(options, "actor"),
        registryRoot: options.registry_root,
        sessionRoot: options.session_root,
        reviewId: options.review_id,
        firstActor: options.first_actor,
        maxTurns: integer(options, "max_turns", null),
        leaseSeconds: integer(options, "lease_seconds", 120),
        ttlSeconds: integer(options, "ttl_seconds", 7 * 24 * 60 * 60),
        orphanGraceSeconds: integer(options, "orphan_grace_seconds", 30),
      });
    case "watch":
      return watchReview({
        inputPaths: options.inputs,
        actor: required(options, "actor"),
        registryRoot: options.registry_root,
        sessionRoot: options.session_root,
        reviewId: options.review_id,
        firstActor: options.first_actor,
        maxTurns: integer(options, "max_turns", null),
        leaseSeconds: integer(options, "lease_seconds", 120),
        ttlSeconds: integer(options, "ttl_seconds", 7 * 24 * 60 * 60),
        orphanGraceSeconds: integer(options, "orphan_grace_seconds", 30),
      });
    case "tick":
      return tickReview({ artifactRoot: required(options, "artifact_root"), actor: required(options, "actor") });
    case "heartbeat":
      return heartbeatTurn({ artifactRoot: required(options, "artifact_root"), actor: required(options, "actor"), attemptId: required(options, "attempt_id"), leaseId: required(options, "lease_id") });
    case "submit":
      return submitTurn({ artifactRoot: required(options, "artifact_root"), actor: required(options, "actor"), attemptId: required(options, "attempt_id"), leaseId: required(options, "lease_id"), resultPath: required(options, "result_file") });
    case "status":
      return readRelayStatus({ artifactRoot: required(options, "artifact_root") });
    case "handoff-candidate":
      return writeHandoffCandidate({ artifactRoot: required(options, "artifact_root"), allowCheckpoint: options.allow_checkpoint === true });
    default:
      throw new RelayError("invalid_command", `unsupported command: ${options.command}`);
  }
}

try {
  const result = await execute(parseArgs(process.argv.slice(2)));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
} catch (error) {
  const payload = {
    status: "error",
    code: error.code || "relay_error",
    message: error.message,
    ...(error.details ? { details: error.details } : {}),
  };
  process.stderr.write(`${JSON.stringify(payload, null, 2)}\n`);
  process.exitCode = error.exitCode || 20;
}
