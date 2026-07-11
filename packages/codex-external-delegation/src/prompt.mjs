import { RESULT_MARKER_END, RESULT_MARKER_START } from "./contract.mjs";

function list(value) {
  return Array.isArray(value) && value.length > 0 ? value.map((item) => `- ${item}`).join("\n") : "- none specified";
}

export function renderPrompt(packet) {
  const resultExample = {
    status: "ok",
    result_payload: Object.fromEntries((packet.output_schema.required ?? []).map((key) => [key, null])),
  };

  return [
    "You are a bounded delegated worker. Execute only the task below.",
    "Do not broaden scope, edit files in read-only mode, run unrelated commands, or invent verification results.",
    "If the task cannot be completed safely, return status=blocked in the required result marker.",
    "",
    `Task ID: ${packet.task_id}`,
    `Mode: ${packet.mode}`,
    `Working directory: ${packet.cwd}`,
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
  const match = text.match(new RegExp(`${escapedStart}([\\s\\S]*?)${escapedEnd}`));
  if (!match) return null;
  try {
    const parsed = JSON.parse(match[1]);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}
