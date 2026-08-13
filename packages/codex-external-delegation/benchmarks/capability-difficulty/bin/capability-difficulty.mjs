#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { BENCHMARK_MANIFEST } from "../src/manifest.mjs";
import { aggregateRuns, evaluateRun } from "../src/evaluate.mjs";
import { checkCase } from "../src/checkers.mjs";
import { writeCapabilityRun } from "../src/adapter.mjs";

function usage() {
  console.log(`Usage:
  capability-difficulty manifest [--out <manifest.json>]
  capability-difficulty evaluate --run <run.json> [--manifest <manifest.json>] [--out <result.json>]
  capability-difficulty aggregate --runs <runs.json> [--manifest <manifest.json>] [--out <result.json>]
  capability-difficulty check --case <case-id> --payload <payload.json> [--worktree <package-root>] [--out <result.json>]
  capability-difficulty collect --batch-summary <summary.json> --binding <binding.json> --run-id <id> [--manifest <manifest.json>] [--out <run.json>]

All commands are offline. No provider, quota, or registry endpoint is called.`);
}

function option(args, name) {
  const index = args.indexOf(name);
  return index === -1 ? null : args[index + 1];
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function emit(value, outPath) {
  const text = `${JSON.stringify(value, null, 2)}\n`;
  if (outPath) await writeFile(outPath, text, "utf8");
  else process.stdout.write(text);
}

async function loadManifest(path) {
  return path ? readJson(path) : BENCHMARK_MANIFEST;
}

const [command, ...args] = process.argv.slice(2);
if (!command || command === "--help" || command === "-h") {
  usage();
  process.exit(0);
}

if (command === "manifest") {
  await emit(BENCHMARK_MANIFEST, option(args, "--out"));
  process.exit(0);
}

if (command === "evaluate") {
  const runPath = option(args, "--run");
  if (!runPath) {
    usage();
    process.exit(2);
  } else {
    const result = evaluateRun({ manifest: await loadManifest(option(args, "--manifest")), run: await readJson(runPath) });
    await emit(result, option(args, "--out"));
    if (result.status === "invalid") process.exitCode = 1;
  }
  process.exit(process.exitCode ?? 0);
}

if (command === "aggregate") {
  const runsPath = option(args, "--runs");
  if (!runsPath) {
    usage();
    process.exit(2);
  } else {
    const payload = await readJson(runsPath);
    const runs = Array.isArray(payload) ? payload : payload?.runs;
    const result = aggregateRuns({ manifest: await loadManifest(option(args, "--manifest")), runs });
    await emit(result, option(args, "--out"));
    if (result.status === "invalid") process.exitCode = 1;
  }
  process.exit(process.exitCode ?? 0);
}

if (command === "check") {
  const caseId = option(args, "--case");
  const payloadPath = option(args, "--payload");
  const worktreePath = option(args, "--worktree");
  if (!caseId || !payloadPath) {
    usage();
    process.exit(2);
  } else {
    try {
      const result = await checkCase({ caseId, payload: await readJson(payloadPath), worktreePath });
      await emit(result, option(args, "--out"));
      if (result.status !== "verification_passed") process.exitCode = 1;
    } catch (error) {
      await emit({
        schema_version: "capability-difficulty-check.v1",
        checker: "capability-difficulty-verifier@1",
        case_id: caseId,
        status: "verification_blocked",
        failure_class: "harness",
        message: error.message,
      }, option(args, "--out"));
      process.exitCode = 2;
    }
  }
  process.exit(process.exitCode ?? 0);
}

if (command === "collect") {
  const summaryPath = option(args, "--batch-summary");
  const bindingPath = option(args, "--binding");
  const runId = option(args, "--run-id");
  const outPath = option(args, "--out");
  if (!summaryPath || !bindingPath || !runId || !outPath) {
    usage();
    process.exit(2);
  } else {
    try {
      const run = await writeCapabilityRun(outPath, {
        batchSummary: await readJson(summaryPath),
        binding: await readJson(bindingPath),
        runId,
        manifest: await loadManifest(option(args, "--manifest")),
        checker: checkCase,
      });
      process.stdout.write(`${JSON.stringify({ status: "collected", run_id: run.run_id, out: outPath }, null, 2)}\n`);
    } catch (error) {
      process.stderr.write(`${error.message}\n`);
      process.exitCode = 2;
    }
  }
  process.exit(process.exitCode ?? 0);
}

usage();
process.exitCode = 2;
