const WORKERS = new Set(["pi", "opencode"]);
const MODES = new Set(["read_only", "write"]);
const STATUSES = new Set(["ok", "failed", "blocked"]);
const PROPERTY_TYPES = new Set(["string", "number", "integer", "boolean", "object", "array", "null"]);

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isValidPropertyDefinition(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const keys = Object.keys(value);
  return keys.length === 1 && keys[0] === "type" && PROPERTY_TYPES.has(value.type);
}

function observedSchemaType(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number") return Number.isInteger(value) ? "integer" : "number";
  if (typeof value === "string") return "string";
  if (typeof value === "boolean") return "boolean";
  return "object";
}

function isSafeRelativeScope(value) {
  if (!isNonEmptyString(value)) return false;
  const normalized = value.replaceAll("\\", "/");
  if (normalized.startsWith("/") || /^[A-Za-z]:\//.test(normalized)) return false;
  return !normalized.split("/").includes("..");
}

function packetErrors(packet, { allowWorktreeRequest = false } = {}) {
  const errors = [];
  const required = [
    "schema_version",
    "task_id",
    "worker",
    "model",
    "objective",
    "cwd",
    "mode",
    "output_schema",
    "verification",
  ];

  for (const key of required) {
    if (packet?.[key] === undefined || packet[key] === null || packet[key] === "") {
      errors.push(`missing_${key}`);
    }
  }

  if (packet?.schema_version !== "2") errors.push("unsupported_schema_version");
  if (!WORKERS.has(packet?.worker)) errors.push("invalid_worker");
  if (!isNonEmptyString(packet?.model)) errors.push("invalid_model");
  if (!isNonEmptyString(packet?.objective)) errors.push("invalid_objective");
  if (!isNonEmptyString(packet?.cwd)) errors.push("invalid_cwd");
  if (!MODES.has(packet?.mode)) errors.push("invalid_mode");

  if (packet?.mode === "write") {
    if (!Array.isArray(packet.write_scope) || packet.write_scope.length === 0) {
      errors.push("missing_write_scope");
    } else if (packet.write_scope.some((entry) => !isSafeRelativeScope(entry))) {
      errors.push("invalid_write_scope");
    }
    const deferredWorktree = allowWorktreeRequest
      && packet.worktree_request
      && typeof packet.worktree_request === "object"
      && !Array.isArray(packet.worktree_request);
    if (!isNonEmptyString(packet.isolated_cwd) && !deferredWorktree) {
      errors.push("missing_isolated_cwd");
    }
  }

  if (!Array.isArray(packet?.verification?.commands) || packet.verification.commands.length === 0) {
    errors.push("missing_verification_commands");
  }

  if (!Array.isArray(packet?.output_schema?.required) || packet.output_schema.required.length === 0) {
    errors.push("missing_output_schema_required");
  } else if (packet.output_schema.required.some((entry) => !isNonEmptyString(entry))) {
    errors.push("invalid_output_schema_required");
  }

  if (packet?.output_schema?.properties !== undefined) {
    const properties = packet.output_schema.properties;
    if (!properties || typeof properties !== "object" || Array.isArray(properties)) {
      errors.push("invalid_output_schema_properties");
    } else {
      for (const [name, definition] of Object.entries(properties)) {
        if (!isNonEmptyString(name) || !isValidPropertyDefinition(definition)) {
          errors.push("invalid_output_schema_properties");
          break;
        }
      }
    }
  }

  return errors;
}

export function validateResultPayloadSchema(payload, schema) {
  const errors = [];
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return errors;
  const properties = schema?.properties;
  if (!properties || typeof properties !== "object" || Array.isArray(properties)) return errors;
  for (const [field, definition] of Object.entries(properties)) {
    if (!Object.prototype.hasOwnProperty.call(payload, field)) continue;
    if (!definition || typeof definition !== "object" || !PROPERTY_TYPES.has(definition.type)) continue;
    const observed = observedSchemaType(payload[field]);
    if (definition.type !== observed) {
      errors.push({ field, expected_type: definition.type, observed_type: observed });
    }
  }
  return errors;
}

export function validatePacket(packet, options = {}) {
  const errors = packetErrors(packet, options);
  return errors.length > 0 ? { ok: false, errors } : { ok: true, packet };
}

export function validateResult(result) {
  const errors = [];
  if (!STATUSES.has(result?.status)) errors.push("invalid_status");
  if (typeof result?.failure_class !== "string") errors.push("missing_failure_class");
  if (result?.status === "ok" && (typeof result.result_payload !== "object" || result.result_payload === null)) {
    errors.push("missing_result_payload");
  }
  return errors.length > 0 ? { ok: false, errors } : { ok: true, result };
}

export const RESULT_MARKER_START = "<external-delegation-result>";
export const RESULT_MARKER_END = "</external-delegation-result>";
