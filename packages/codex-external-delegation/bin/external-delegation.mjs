#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { buildCommand, commandName, spawnSpec } from "../src/commands.mjs";
import { validatePacket } from "../src/contract.mjs";
import { runPacket, workerEnvironment } from "../src/runner.mjs";
import { compilePacket } from "../src/packet.mjs";
import { classifyTask } from "../src/policy.mjs";
import { getLane } from "../src/registry.mjs";
import { batchExitCode, routeBatch, runBatch } from "../src/batch.mjs";

function option(args, name) {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : null;
}

async function readPacket(value) {
  let text;
  if (value === "-") {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    text = Buffer.concat(chunks).toString("utf8");
  } else {
    text = await readFile(value, "utf8");
  }
  return JSON.parse(text.replace(/^\uFEFF/, ""));
}

function exitCodeFor(result) {
  if (result.status === "ok") return 0;
  if (result.status === "blocked" || result.failure_class === "contract_error") return 30;
  return 20;
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

async function main(argv = process.argv.slice(2)) {
  const [command, ...args] = argv;
  if (!command || command === "--help" || command === "-h") {
    print({
      usage: "node bin/external-delegation.mjs <run|classify|check> ...",
      commands: {
        run: "run --packet <path|-> [--dry-run]",
        classify: "classify --packet <path|->",
        route: "route --input <path|->",
        batch: "batch <route|run> --manifest <path> [--dry-run]",
        check: "check --worker <pi|opencode|all>",
      },
    });
    return 0;
  }

  if (command === "check") {
    const requested = option(args, "--worker") || "all";
    const workers = requested === "all" ? ["pi", "opencode"] : [requested];
    const checks = workers.map((worker) => {
      const commandNameValue = commandName(worker);
      const launch = spawnSpec(commandNameValue, ["--version"]);
      const result = spawnSync(launch.command, launch.args, {
        encoding: "utf8",
        windowsHide: true,
        shell: false,
        env: workerEnvironment({ worker }),
        // Windows .cmd wrappers can cold-start their bundled/managed Node
        // runtime noticeably slower than a warm invocation.
        timeout: 30_000,
      });
      return {
        worker,
        command: commandNameValue,
        available: result.status === 0,
        exit_code: result.status,
        version: `${result.stdout || ""}${result.stderr || ""}`.trim().split(/\r?\n/)[0] || null,
        error: result.error?.code || result.error?.message || null,
      };
    });
    print({ status: checks.every((item) => item.available) ? "ok" : "failed", checks });
    return checks.every((item) => item.available) ? 0 : 20;
  }

  if (command === "batch") {
    const [batchCommand, ...batchArgs] = args;
    if (batchCommand !== "route" && batchCommand !== "run") {
      print({ status: "blocked", failure_class: "invalid_batch_command", message: "batch command must be route or run" });
      return 30;
    }
    const manifestPath = option(batchArgs, "--manifest");
    if (!manifestPath) {
      print({ status: "blocked", failure_class: "invalid_input", message: "--manifest is required" });
      return 30;
    }
    let manifest;
    try {
      manifest = await readPacket(manifestPath);
    } catch (error) {
      print({ status: "blocked", failure_class: "invalid_input", message: error.message });
      return 30;
    }
    const dryRun = batchCommand === "route" || batchArgs.includes("--dry-run");
    const result = batchCommand === "route"
      ? await routeBatch(manifest)
      : await runBatch(manifest, { dryRun });
    const output = { ...result };
    delete output.plans;
    print(output);
    return batchExitCode(output);
  }

  if (command !== "run" && command !== "classify" && command !== "route") {
    print({ status: "blocked", failure_class: "invalid_command", message: `Unknown command: ${command}` });
    return 30;
  }

  if (command === "route") {
    const inputPath = option(args, "--input");
    if (!inputPath) {
      print({ status: "blocked", failure_class: "invalid_input", message: "--input is required" });
      return 30;
    }
    let input;
    try {
      input = await readPacket(inputPath);
    } catch (error) {
      print({ status: "blocked", failure_class: "invalid_input", message: error.message });
      return 30;
    }
    const classification = classifyTask(input);
    const lane = getLane(classification.lane) || null;
    if (!classification.eligible) {
      print({ status: "ok", classification, lane, packet: undefined });
      return 0;
    }
    const { packet } = compilePacket(input);
    if (packet.model_selection?.status === "no_eligible_candidate" || packet.model_selection?.confidence === "unverified") {
      print({
        status: "blocked",
        failure_class: packet.model_selection?.status === "no_eligible_candidate" ? "no_eligible_external_candidate" : "unverified_model_selection",
        classification,
        lane,
        selection: packet.model_selection,
      });
      return 20;
    }
    print({ status: "ok", classification, lane, packet });
    return 0;
  }

  const packetPath = option(args, "--packet");
  if (!packetPath) {
    print({ status: "blocked", failure_class: "invalid_packet", message: "--packet is required" });
    return 30;
  }

  let packet;
  try {
    packet = await readPacket(packetPath);
  } catch (error) {
    print({ status: "blocked", failure_class: "invalid_packet", message: error.message });
    return 30;
  }

  if (command === "classify") {
    // Classification happens before run-time worktree provisioning. Accept a
    // valid worktree_request here, but keep runPacket strict after it resolves
    // isolated_cwd and validates the actual Git identity.
    const validation = validatePacket(packet, { allowWorktreeRequest: true });
    print(validation.ok
      ? { status: "ok", packet: validation.packet, isolation: packet.mode === "write" && !packet.isolated_cwd ? "deferred_worktree_provision" : "validated" }
      : { status: "blocked", failure_class: "contract_error", errors: validation.errors });
    return validation.ok ? 0 : 30;
  }

  if (args.includes("--dry-run")) {
    const validation = validatePacket(packet);
    if (!validation.ok) {
      print({ status: "blocked", failure_class: "contract_error", errors: validation.errors });
      return 30;
    }
    const commandSpec = buildCommand(packet, "[rendered prompt omitted in dry-run]");
    print({ status: "dry_run", command: commandSpec.command, args: commandSpec.args, cwd: commandSpec.cwd });
    return 0;
  }

  const result = await runPacket(packet);
  print(result);
  return exitCodeFor(result);
}

main().then((code) => { process.exitCode = code; }).catch((error) => {
  print({ status: "failed", failure_class: "bridge_error", message: error.message });
  process.exitCode = 20;
});

export { main };
