const AUTH_PATTERNS = [
  /api\s*key/i,
  /unauthori[sz]ed/i,
  /forbidden/i,
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
];

const IDENTITY_PATTERNS = [
  /agent .* is a subagent, not a primary agent/i,
  /falling back to default agent/i,
  /requested .* agent .* was not used/i,
];

function contains(patterns, text) {
  return patterns.some((pattern) => pattern.test(text));
}

export function classifyFailure({ error = null, exitCode = null, timedOut = false, stdout = "", stderr = "" } = {}) {
  if (timedOut) return "timeout";
  if (error?.code === "ENOENT") return "command_missing";

  const combined = `${stderr}\n${stdout}`;
  if (contains(IDENTITY_PATTERNS, combined)) return "identity_mismatch";
  if (contains(AUTH_PATTERNS, combined)) return "auth_or_quota";
  if (contains(CONTEXT_PATTERNS, combined)) return "context_limit";
  if (contains(PROVIDER_PATTERNS, combined)) return "provider_unavailable";
  if (exitCode === 0) return "protocol_error";
  return "worker_failed";
}
