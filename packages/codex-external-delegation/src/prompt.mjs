import { RESULT_MARKER_END, RESULT_MARKER_START } from "./contract.mjs";

function list(value) {
  return Array.isArray(value) && value.length > 0 ? value.map((item) => `- ${item}`).join("\n") : "- none specified";
}

function schemaExample(type) {
  if (type === "array") return [];
  if (type === "object") return {};
  if (type === "number" || type === "integer") return 0;
  if (type === "boolean") return false;
  return type === "string" ? "" : null;
}

function outputSchemaDetails(schema) {
  const properties = schema?.properties;
  if (!properties || typeof properties !== "object" || Array.isArray(properties)) return [];
  return Object.entries(properties).map(([name, definition]) => ({
    name,
    type: definition?.type || "unspecified",
  }));
}

export function renderPrompt(packet) {
  const schemaDetails = outputSchemaDetails(packet.output_schema);
  const resultExample = {
    status: "ok",
    result_payload: Object.fromEntries((packet.output_schema.required ?? []).map((key) => [
      key,
      schemaDetails.find((entry) => entry.name === key)?.type
        ? schemaExample(schemaDetails.find((entry) => entry.name === key).type)
        : null,
    ])),
  };

  return [
    "You are a bounded delegated worker. Execute only the task below.",
    "Do not broaden scope, edit files in read-only mode, run unrelated commands, or invent verification results.",
    "If the task cannot be completed safely, return status=blocked in the required result marker.",
    "",
    `Task ID: ${packet.task_id}`,
    `Mode: ${packet.mode}`,
    `Working directory: ${packet.isolated_cwd || packet.cwd}`,
    `Objective: ${packet.objective}`,
    "",
    "Allowed paths:",
    list(packet.allowed_paths),
    "",
    "Forbidden actions:",
    list(packet.forbidden_actions),
    "",
    "Required output fields:",
    list(packet.output_schema.required),
    ...(schemaDetails.length > 0 ? [
      "Required output field types:",
      schemaDetails.map(({ name, type }) => `- ${name}: ${type}`).join("\n"),
    ] : []),
    "",
    "Verification commands to run or report as unavailable:",
    list(packet.verification.commands),
    "",
    "Return exactly one structured result marker. Do not claim success outside the marker:",
    `${RESULT_MARKER_START}${JSON.stringify(resultExample)}${RESULT_MARKER_END}`,
  ].join("\n");
}

export function extractResultPayload(text) {
  if (typeof text !== "string") return null;
  const escapedStart = RESULT_MARKER_START.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const escapedEnd = RESULT_MARKER_END.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = [...text.matchAll(new RegExp(`${escapedStart}([\\s\\S]*?)${escapedEnd}`, "g"))];
  // Pi can echo the prompt example and cumulative stream fragments before
  // emitting the final result. Prefer the last parseable marker so an earlier
  // placeholder cannot mask the worker's actual structured response.
  for (const match of matches.reverse()) {
    try {
      const parsed = JSON.parse(match[1]);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) return parsed;
    } catch {
      // Keep looking: a quoted or partial marker is not the result.
    }
  }
  return null;
}

export function extractJsonEventText(text) {
  if (typeof text !== "string") return "";
  const parts = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const event = JSON.parse(line);
      if (event?.type === "text" && typeof event.part?.text === "string") parts.push(event.part.text);
      if (event?.type === "message_update" && event.assistantMessageEvent?.type === "text_delta" && typeof event.assistantMessageEvent.delta === "string") {
        parts.push(event.assistantMessageEvent.delta);
      }
    } catch {
      // Preserve the raw parser path for non-JSON workers.
    }
  }
  // Streaming deltas can split protocol tokens themselves. Do not insert a
  // newline between deltas or `<external-delegation-result>` can become
  // unparsable even though the worker emitted the complete marker.
  return parts.join("");
}
