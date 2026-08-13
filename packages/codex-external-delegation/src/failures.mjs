const AUTH_PATTERNS = [
  /api\s*key/i,
  /unauthori[sz]ed/i,
  /access denied/i,
  /permission denied/i,
  /quota/i,
  /billing/i,
  /rate\s*limit/i,
  /429\b/,
  /401\b/,
  /403\b/,
];

const CONTEXT_PATTERNS = [
  /context\s*(window|length|limit)/i,
  /too many tokens/i,
  /maximum prompt/i,
  /input is too large/i,
];

const PROVIDER_PATTERNS = [
  /connection refused/i,
  /connection reset/i,
  /network error/i,
  /fetch failed/i,
  /econn(refused|reset|aborted)/i,
  /service unavailable/i,
  /gateway timeout/i,
  /timed out/i,
  /regionerror/i,
  /invalid_request_error/i,
  /failed to deserialize/i,
];

const IDENTITY_PATTERNS = [
  /agent .* is a subagent, not a primary agent/i,
  /falling back to default agent/i,
  /requested .* agent .* was not used/i,
];

const RETIRED_ROUTE_PATTERNS = [
  /(?:model|route)\s+(?:not found|does not exist|is discontinued|is deprecated|is retired|was removed)/i,
  /(?:model|route).*(?:discontinued|deprecated|retired|removed)/i,
  /no longer (?:available|supported)/i,
];

function contains(patterns, text) {
  return patterns.some((pattern) => pattern.test(text));
}

export function classifyFailure({ error = null, exitCode = null, timedOut = false, stdout = "", stderr = "", payload = null } = {}) {
  if (timedOut) return "timeout";
  if (error?.code === "ENOENT") return "command_missing";

  // A successful structured result may legitimately quote words such as
  // "quota", "billing", or "rate limit" while inspecting source or logs.
  // Once the worker has produced a valid payload, classify provider failures
  // from stderr only; otherwise task content can masquerade as infrastructure
  // failure. Unsuccessful/unstructured runs still use stdout for diagnostics.
  const combined = payload && exitCode === 0 ? stderr : `${stderr}\n${stdout}`;
  if (contains(IDENTITY_PATTERNS, combined)) return "identity_mismatch";
  if (contains(AUTH_PATTERNS, combined)) return "auth_or_quota";
  if (contains(RETIRED_ROUTE_PATTERNS, combined)) return "provider_unavailable";
  if (contains(CONTEXT_PATTERNS, combined)) return "context_limit";
  if (contains(PROVIDER_PATTERNS, combined)) return "provider_unavailable";
  if (exitCode === 0) return "protocol_error";
  return "worker_failed";
}

function durationMs(value, unit) {
  const multipliers = {
    ms: 1,
    millisecond: 1,
    milliseconds: 1,
    s: 1000,
    sec: 1000,
    secs: 1000,
    second: 1000,
    seconds: 1000,
    m: 60 * 1000,
    min: 60 * 1000,
    mins: 60 * 1000,
    minute: 60 * 1000,
    minutes: 60 * 1000,
    h: 60 * 60 * 1000,
    hr: 60 * 60 * 1000,
    hrs: 60 * 60 * 1000,
    hour: 60 * 60 * 1000,
    hours: 60 * 60 * 1000,
    d: 24 * 60 * 60 * 1000,
    day: 24 * 60 * 60 * 1000,
    days: 24 * 60 * 60 * 1000,
  };
  return Number.isFinite(Number(value)) && multipliers[unit.toLowerCase()]
    ? Math.round(Number(value) * multipliers[unit.toLowerCase()])
    : null;
}

function retryAfterMs(text) {
  const patterns = [
    /\bretry[- ]?after\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(milliseconds?|ms|seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d)\b/i,
    /\b(?:retry|try again)\s+(?:in|after)\s*(\d+(?:\.\d+)?)\s*(milliseconds?|ms|seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d)\b/i,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      const parsed = durationMs(match[1], match[2]);
      if (parsed !== null) return parsed;
    }
  }
  const header = text.match(/\bretry-after\s*:\s*(\d+(?:\.\d+)?)\b/i);
  return header ? durationMs(header[1], "s") : null;
}

function providerErrorTypes(text) {
  const types = new Set();
  for (const match of text.matchAll(/["'](?:error[_-]?)?type["']\s*:\s*["']([^"']+)["']/gi)) {
    if (/_error$|rate_limit|quota/i.test(match[1])) types.add(match[1]);
  }
  return [...types].sort();
}

function signalList(text, { failureClass, timedOut = false } = {}) {
  const signals = new Set();
  if (/\b429\b|rate[_ -]?limit|too many requests/i.test(text)) signals.add("rate_limit");
  if (/quota|usage limit|monthly limit|token plan|credits/i.test(text)) signals.add("quota_exhausted");
  if (/\b401\b|\b403\b|unauthori[sz]ed|access denied|api\s*key|permission denied/i.test(text)) signals.add("authentication_or_permission");
  if (timedOut || /timed out|timeout/i.test(text)) signals.add("timeout");
  if (/context\s*(window|length|limit)|too many tokens|maximum prompt|input is too large/i.test(text)) signals.add("context_limit");
  if (/connection refused|connection reset|network error|fetch failed|econn(refused|reset|aborted)|service unavailable|gateway timeout/i.test(text)) signals.add("provider_unavailable");
  if (RETIRED_ROUTE_PATTERNS.some((pattern) => pattern.test(text))) signals.add("route_retired");
  if (failureClass === "protocol_error") signals.add("protocol");
  return [...signals].sort();
}

/**
 * Preserve the existing coarse failure class while exposing safe recovery
 * facts for benchmark analysis. This deliberately does not authorize a
 * retry; the caller still owns retry, quota, and fallback policy.
 */
export function failureDiagnostics({ failureClass, error = null, exitCode = null, timedOut = false, stdout = "", stderr = "" } = {}) {
  // Match classifyFailure: successful structured output can quote words such
  // as "quota" while discussing a task. For a valid success, only transport
  // stderr is diagnostic evidence.
  const text = `${stderr}\n${failureClass === "none" ? "" : stdout}\n${error?.message || ""}`;
  const signals = signalList(text, { failureClass, timedOut });
  const retryable = !signals.includes("route_retired")
    && !signals.includes("authentication_or_permission")
    && (signals.includes("rate_limit")
    || signals.includes("quota_exhausted")
    || signals.includes("timeout")
    || signals.includes("provider_unavailable"));
  let recoveryState = "manual_investigation";
  if (!failureClass || failureClass === "none") recoveryState = "not_applicable";
  else if (signals.includes("route_retired")) recoveryState = "route_retired";
  else if (signals.includes("authentication_or_permission")) recoveryState = "account_or_permission_action";
  else if (signals.includes("rate_limit") || signals.includes("quota_exhausted")) recoveryState = "defer_until_provider_reset_or_capacity";
  else if (signals.includes("timeout") || signals.includes("provider_unavailable")) recoveryState = "retryable_transient";
  else if (signals.includes("context_limit")) recoveryState = "reduce_input_or_route_to_larger_context";
  else if (signals.includes("protocol")) recoveryState = "harness_protocol_fix";
  else if (failureClass === "command_missing") recoveryState = "environment_command_fix";
  return {
    failure_class: failureClass || null,
    signals,
    provider_error_types: providerErrorTypes(text),
    retryable,
    retry_after_ms: retryAfterMs(text),
    internal_retry_count: (stdout.match(/"type"\s*:\s*"auto_retry_start"/g) || []).length,
    exit_code: exitCode,
    recovery_state: recoveryState,
  };
}
