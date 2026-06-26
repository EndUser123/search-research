/**
 * Best-effort extraction of a bash command's exit code from a tool_result
 * event. pi's BashToolDetails does not carry the exit code; on failure the
 * tool throws and the error text (containing "exited with code N") becomes
 * the result content. Returns 0 on success, the parsed code on failure, or
 * 1 if the code can't be parsed.
 *
 * Extracted from risk-policy-extension so it can be unit-tested directly
 * without spinning up an extension runtime.
 */
export function extractBashExitCode(event: { isError: boolean; content?: unknown }): number {
	if (!event.isError) return 0;
	const content = event.content;
	if (!Array.isArray(content)) return 1;
	const text = content
		.map((c) => (c && typeof c === "object" && "type" in c && c.type === "text" ? String(c.text) : ""))
		.join(" ");
	if (!text) return 1;
	const m = /exited with code (-?\d+)/.exec(text);
	if (m) return parseInt(m[1], 10);
	return 1;
}