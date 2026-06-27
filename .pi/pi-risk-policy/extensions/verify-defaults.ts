/**
 * Per-filetype default verifyCommand suggestions.
 *
 * The evidence-gate consults this so a sensible verification command is
 * suggested by the edited file's extension. None means the gate must
 * require the model/user to name a command explicitly.
 */

const TS = ["npm run typecheck && npm test", "npx tsc --noEmit"];
const PY = ["ruff check . && pytest -q", "pytest -q"];
const TF = ["terraform validate"];

const TABLE: Record<string, string[]> = {
	".ts": TS,
	".tsx": TS,
	".mts": TS,
	".cts": TS,
	".py": PY,
	".pyi": PY,
	".tf": TF,
	".tf.json": TF,
	".hcl": TF,
	".md": [],
	".markdown": [],
	".txt": [],
};

export function suggestVerifyCommandsForPath(path: string): string[] | null {
	const slash = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
	const filename = slash >= 0 ? path.slice(slash + 1) : path;
	const dot = filename.lastIndexOf(".");
	if (dot < 0) return null;
	const ext = filename.slice(dot);
	const list = TABLE[ext.toLowerCase()];
	if (!list) return null;
	// Substitute the file path into commands that carry the __FILE__ placeholder.
	return list.map((c) => c.replace(/__FILE__/g, path).replace(/__PATH__/g, path));
}

export function suggestVerifyCommands(extension: string): string[] | null {
	const ext = extension.toLowerCase();
	return TABLE[ext] ?? null;
}

export function suggestDefaultVerifyCommand(extension: string): string | null {
	const list = suggestVerifyCommands(extension);
	return list && list.length > 0 ? list[0] : null;
}
