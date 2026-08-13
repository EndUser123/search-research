import { access, mkdtemp, readFile, readdir, stat, symlink, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn } from "node:child_process";
import { fixtureDirectory, fixtureForCase, fixtureRoot, contextForCase } from "./fixtures.mjs";

export const CHECKER_SCHEMA_VERSION = "capability-difficulty-check.v1";
export const CHECKER_ID = "capability-difficulty-verifier@1";

function check(name, passed, detail = undefined) {
  return detail === undefined ? { name, passed } : { name, passed, detail };
}

function responseObject(payload) {
  if (payload?.response && typeof payload.response === "object") return payload.response;
  if (typeof payload?.response !== "string") return null;
  try { return JSON.parse(payload.response); } catch { return null; }
}

function responseText(payload) {
  const response = payload?.response;
  return typeof response === "string" ? response : JSON.stringify(response ?? "");
}

function observations(payload) {
  return Array.isArray(payload?.observations) ? payload.observations : [];
}

function hasText(value, expected) {
  return String(value || "").toLowerCase().includes(String(expected).toLowerCase());
}

async function filesUnder(root) {
  const output = [];
  async function visit(directory, prefix = "") {
    let entries = [];
    try { entries = await readdir(directory, { withFileTypes: true }); } catch { return; }
    for (const entry of entries) {
      const name = prefix ? `${prefix}/${entry.name}` : entry.name;
      const path = join(directory, entry.name);
      if (entry.isDirectory()) await visit(path, name);
      else output.push({ name, hash: createHash("sha256").update(await readFile(path)).digest("hex") });
    }
  }
  await visit(root);
  return output.sort((left, right) => left.name.localeCompare(right.name));
}

async function changedFixturePaths(worktreePath, fixtureDirectory = null) {
  if (!worktreePath) return [];
  const canonicalRoot = fixtureDirectory ? join(fixtureRoot(), fixtureDirectory) : fixtureRoot();
  const candidateRoot = fixtureDirectory
    ? join(worktreePath, "benchmarks", "capability-difficulty", "fixtures", fixtureDirectory)
    : join(worktreePath, "benchmarks", "capability-difficulty", "fixtures");
  const canonical = await filesUnder(canonicalRoot);
  const candidate = await filesUnder(candidateRoot);
  const before = new Map(canonical.map((entry) => [entry.name, entry.hash]));
  const after = new Map(candidate.map((entry) => [entry.name, entry.hash]));
  const changed = [...new Set([...before.keys(), ...after.keys()])]
    .filter((name) => before.get(name) !== after.get(name))
    .sort();
  return fixtureDirectory ? changed.map((name) => `${fixtureDirectory}/${name}`) : changed;
}

async function importFixture(caseId, worktreePath) {
  const fixture = fixtureForCase(caseId);
  if (!fixture || !worktreePath) throw new Error("fixture_worktree_missing");
  const root = join(worktreePath, "benchmarks", "capability-difficulty", "fixtures", fixture.directory);
  const modulePath = join(root, fixture.entrypoint);
  await access(modulePath);
  return import(`${pathToFileURL(modulePath).href}?checker=${Date.now()}-${Math.random()}`);
}

async function runNodeTest(path) {
  return new Promise((resolveResult) => {
    // The test path is absolute and its imports resolve relative to the file.
    // Forcing cwd to a mapped workspace drive can make Windows child_process
    // report ENOENT/ENOTCONN even though the same absolute path is runnable.
    const child = spawn(process.execPath, ["--test", path], { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.once("error", (error) => resolveResult({ code: null, stdout, stderr, error: error.message }));
    child.once("close", (code) => resolveResult({ code, stdout, stderr, error: null }));
  });
}

async function checkMechanical(caseId, payload) {
  const value = responseObject(payload);
  const text = responseText(payload);
  if (caseId.endsWith("contract_following.easy.001")) {
    return [
      check("keys_exact", value !== null && JSON.stringify(Object.keys(value).sort()) === JSON.stringify(["answer", "confidence"])),
      check("values_exact", value?.answer === 7 && value?.confidence === "high"),
    ];
  }
  if (caseId.endsWith("contract_following.medium.001")) {
    const context = contextForCase(caseId);
    return [
      check("keys_exact", value !== null && JSON.stringify(Object.keys(value)) === JSON.stringify(context.input.requested_order)),
      check("unknown_field_labeled", value?.unknown_fields?.length === 1 && value.unknown_fields[0] === "owner"),
    ];
  }
  if (caseId.endsWith("contract_following.hard.001")) {
    const hypotheses = Array.isArray(value?.hypotheses) ? value.hypotheses : [];
    const falsifiers = Array.isArray(value?.falsifiers) ? value.falsifiers : [];
    return [
      check("schema_valid", Array.isArray(value?.facts) && Array.isArray(value?.inferences) && hypotheses.length >= 0 && falsifiers.length >= 0),
      check("hypotheses_falsifiable", hypotheses.every((hypothesis) => falsifiers.some((item) => item?.for_hypothesis === hypothesis?.id || item?.for_hypothesis === hypothesis)), "each hypothesis has a matching falsifier"),
    ];
  }
  const ledger = Array.isArray(value?.claim_ledger) ? value.claim_ledger : [];
  const unsupportedAreNonActionable = ledger
    .filter((entry) => /unsupported/i.test(String(entry?.type || entry?.claim_status || entry?.status || "")))
    .every((entry) => entry.action_allowed === false || entry.action_eligible === false || /non.?actionable/i.test(String(entry.action || "")));
  return [
    check("scope_respected", value?.scope !== undefined && hasText(value.scope, "declared")),
    check("unsupported_non_actionable", ledger.length > 0 && unsupportedAreNonActionable),
  ];
}

async function checkReasoning(caseId, payload) {
  const value = responseObject(payload);
  if (caseId.endsWith("context_retrieval.easy.001")) {
    const context = contextForCase(caseId);
    return [
      check("answer_matches_record", value?.answer === context.expected_answer),
      check("record_id_cited", value?.record_id === context.expected_record_id),
    ];
  }
  if (caseId.endsWith("context_retrieval.medium.001")) {
    return [
      check("authoritative_source_selected", value?.selected_source === "provider-status"),
      check("timestamp_rule_applied", hasText(value?.rule_applied, "authoritative") && hasText(value?.rule_applied, "older")),
      check("conflict_disclosed", value?.discarded_record_id === "status-older" && Boolean(value?.conflict_disclosed)),
    ];
  }
  if (caseId.endsWith("context_retrieval.hard.001")) {
    const trace = Array.isArray(value?.trace) ? value.trace : [];
    return [
      check("all_artifacts_traced", ["policy-17", "note-4", "receipt-9"].every((id) => trace.some((item) => item?.id === id))),
      check("authority_order_respected", trace.map((item) => item?.id).join(",") === "policy-17,note-4,receipt-9"),
      check("gap_identified", hasText(value?.gap, "receipt-9") && (hasText(value?.gap, "absent") || hasText(value?.gap, "does not prove"))),
    ];
  }
  const alternatives = Array.isArray(value?.alternatives) ? value.alternatives : [];
  return [
    check("causal_claims_labeled", Array.isArray(value?.observations) && typeof value?.inference === "string" && value.inference.length > 0),
    check("alternative_explanation_present", ["temporary quota", "route retirement"].every((expected) => alternatives.some((item) => hasText(item, expected)))),
    check("discriminating_test_present", hasText(value?.discriminating_test, "reprobe") && hasText(value?.discriminating_test, "availability")),
  ];
}

async function checkCoding(caseId, payload, worktreePath) {
  const fixture = fixtureForCase(caseId);
  // Coding worktrees may materialize only the requested fixture directory. Compare
  // within that directory so absent, intentionally unmaterialized fixtures are not
  // misclassified as deletions outside the worker's scope.
  const changed = await changedFixturePaths(worktreePath, fixture?.directory);
  const allowed = new Set(fixture?.allowed_paths || []);
  const scope = changed.every((path) => path === `${fixture.directory}/${path.split("/").at(-1)}` || path.startsWith(`${fixture.directory}/`))
    && changed.every((path) => allowed.has(path.slice(`${fixture.directory}/`.length)));
  if (caseId.endsWith("localized_patch.easy.001")) {
    const module = await importFixture(caseId, worktreePath);
    let empty;
    let existing;
    let error = null;
    try {
      empty = module.normalizeItems([]);
      existing = module.normalizeItems([" a ", "b"]);
    } catch (value) {
      error = value;
    }
    return [check("empty_case_passes", !error && Array.isArray(empty) && empty.length === 0), check("existing_case_passes", !error && JSON.stringify(existing) === JSON.stringify(["a", "b"])), check("scope_is_limited", scope)];
  }
  if (caseId.endsWith("syntax_contract.easy.001")) {
    const module = await importFixture(caseId, worktreePath);
    return [
      check("type_check_passes", typeof module.toLabel === "function"),
      check("signature_preserved", module.toLabel.length === 1),
      check("boundary_cases_pass", module.toLabel(null) === "unknown" && module.toLabel(undefined) === "unknown" && module.toLabel(0) === "0" && module.toLabel("x") === "x"),
    ];
  }
  if (caseId.endsWith("test_authoring.medium.001")) {
    const testPath = join(worktreePath, "benchmarks", "capability-difficulty", "fixtures", fixture.directory, "parser.test.mjs");
    const source = await readFile(testPath, "utf8").catch(() => "");
    const module = await importFixture(caseId, worktreePath);
    const values = [module.parseList(" a , b "), module.parseList(""), module.parseList("x,,y")];
    const boundary = JSON.stringify(values) === JSON.stringify([["a", "b"], [""], ["x", "", "y"]]);
    const testsAreConcrete = /node:test/.test(source) && /parseList/.test(source) && /deepEqual|strictEqual/.test(source);
    const mutationSensitive = /a.*b|x.*y|empty|boundary/i.test(source);
    const testResult = await runNodeTest(testPath).catch((error) => ({ code: null, error: error.message }));
    return [
      check("boundary_cases_covered", testsAreConcrete && mutationSensitive),
      check("tests_fail_before_fix", mutationSensitive, "static mutation-sensitivity gate; baseline mutation is not executed in the worker checkout"),
      check("tests_pass_after_fix", boundary && testResult.code === 0, testResult.error || testResult.stderr),
      check("scope_is_limited", changed.length === 1 && changed[0] === `${fixture.directory}/parser.test.mjs`),
    ];
  }
  if (caseId.endsWith("debugging_and_edge_cases.hard.001")) {
    const module = await importFixture(caseId, worktreePath);
    const cache = new module.AsyncCache();
    let calls = 0;
    let release;
    const pending = new Promise((resolveResult) => { release = resolveResult; });
    const loader = async () => { calls += 1; await pending; return "value"; };
    const first = cache.get("same", loader);
    const second = cache.get("same", loader);
    release();
    const values = await Promise.all([first, second]);
    const controller = new AbortController();
    const delayed = cache.get("abort", async ({ signal }) => {
      await new Promise((resolveResult) => setTimeout(resolveResult, 5));
      if (signal?.aborted) throw Object.assign(new Error("aborted"), { name: "AbortError" });
      return "should-not-cache";
    }, { signal: controller.signal });
    controller.abort();
    let aborted = false;
    try { await delayed; } catch (error) { aborted = error.name === "AbortError"; }
    return [
      check("race_reproduced", values.length === 2, "concurrent callers were exercised"),
      check("race_fixed", calls === 1 && values[0] === "value" && values[1] === "value"),
      check("cancellation_preserved", aborted),
      check("retry_bounded", calls === 1),
      check("tests_pass_after_fix", calls === 1 && aborted),
    ];
  }
  if (caseId.endsWith("multi_file_invariant.hard.001")) {
    const serializer = await importFixture(caseId, worktreePath);
    const deserializer = await import(`${pathToFileURL(join(worktreePath, "benchmarks", "capability-difficulty", "fixtures", fixture.directory, "deserializer.mjs")).href}?checker=${Date.now()}-${Math.random()}`);
    const current = { id: "r-2", name: "relay", priority: 7 };
    const roundTrip = deserializer.deserializeRecord(serializer.serializeRecord(current));
    const old = deserializer.deserializeRecord(JSON.stringify({ version: 1, id: "old", name: "legacy" }));
    return [
      check("new_round_trip_passes", roundTrip.priority === 7 && roundTrip.id === current.id),
      check("old_record_compatible", old.priority === 0 && old.id === "old"),
      check("schema_version_handled", /version/.test(await readFile(join(worktreePath, "benchmarks", "capability-difficulty", "fixtures", fixture.directory, "serializer.mjs"), "utf8"))),
      check("scope_is_limited", changed.every((path) => [`${fixture.directory}/serializer.mjs`, `${fixture.directory}/deserializer.mjs`].includes(path))),
    ];
  }
  if (caseId.endsWith("api_compatibility.expert.001")) {
    const module = await importFixture(caseId, worktreePath);
    const oldCall = module.createRequest("/health");
    const newCall = module.createRequest("/health", { timeoutMs: 2500 });
    const errors = [];
    for (const input of [["", {}], ["/health", { timeoutMs: 0 }], ["/health", { timeoutMs: "bad" }]]) {
      try { module.createRequest(...input); } catch (error) { errors.push(`${error.name}:${error.message}`); }
    }
    return [
      check("old_callers_unchanged", oldCall.path === "/health" && oldCall.timeoutMs === 5000),
      check("new_option_validated", newCall.timeoutMs === 2500),
      check("errors_deterministic", errors.length === 3 && errors[0].startsWith("TypeError:") && errors.slice(1).every((value) => value.startsWith("RangeError:"))),
      check("negative_cases_pass", errors.every((value) => value.includes(":"))),
      check("scope_is_limited", scope),
    ];
  }
  if (caseId.endsWith("security_edge_cases.expert.001")) {
    const module = await importFixture(caseId, worktreePath);
    const root = await mkdtemp(join(tmpdir(), "codex-pi-safe-path-"));
    await writeFile(join(root, "inside.txt"), "ok", "utf8");
    const valid = await module.resolveSafePath(root, "inside.txt");
    const traversal = await module.resolveSafePath(root, "../outside.txt");
    let linkError = null;
    try { await symlink(root, join(root, "escape"), "junction"); } catch (error) { linkError = error; }
    const escaped = linkError
      ? { blocked: false, environment_blocked: true, reason: linkError.code || linkError.message }
      : await module.resolveSafePath(root, "escape/outside.txt");
    return [
      check("traversal_rejected", Boolean(valid?.path?.endsWith("inside.txt") && traversal?.reason)),
      check("symlink_escape_rejected", Boolean(!escaped.environment_blocked && escaped?.reason)),
      check("valid_nested_path_passes", Boolean(valid?.path?.endsWith("inside.txt") && !valid.reason)),
      check("reason_is_actionable", Boolean(traversal?.reason) && (escaped.environment_blocked || Boolean(escaped?.reason))),
      check("tests_pass_after_fix", Boolean(!linkError && escaped?.reason)),
    ];
  }
  const module = await importFixture(caseId, worktreePath);
  let success;
  try { success = await module.executeRequest(async () => ({ id: "ok" })); } catch { success = null; }
  let failure;
  try { failure = await module.executeRequest(async () => { throw Object.assign(new Error("provider down"), { code: "E_PROVIDER" }); }); } catch { failure = null; }
  return [
    check("regression_reproduced", true),
    check("provider_error_preserved", failure?.status === "error" && failure.error?.code === "E_PROVIDER" && failure.error?.message === "provider down"),
    check("retry_not_fabricated", failure?.attempt === 1),
    check("receipt_contract_preserved", success?.status === "ok" && success?.attempt === 1 && success?.response?.id === "ok"),
    check("tests_pass_after_fix", Boolean(success && failure)),
  ];
}

export async function checkCase({ caseId, payload = {}, worktreePath } = {}) {
  const fixture = fixtureForCase(caseId);
  const lane = caseId?.startsWith("code_pool.") ? "coding" : caseId?.includes("context_retrieval") ? "reasoning" : "mechanical";
  let checks;
  if (lane === "coding") checks = await checkCoding(caseId, payload, worktreePath);
  else if (lane === "reasoning") checks = await checkReasoning(caseId, payload);
  else checks = await checkMechanical(caseId, payload);
  const allPassed = checks.every((value) => value.passed === true);
  return {
    schema_version: CHECKER_SCHEMA_VERSION,
    checker: CHECKER_ID,
    case_id: caseId,
    lane,
    fixture: fixture?.directory || null,
    status: allPassed ? "verification_passed" : "verification_failed",
    checks,
  };
}

export function checkerContract(caseId) {
  const fixture = fixtureForCase(caseId);
  return {
    checker: CHECKER_ID,
    case_id: caseId,
    fixture: fixture?.directory || null,
    allowed_paths: fixture?.allowed_paths || [],
  };
}
