/**
 * Session-scoped change-set from the session ledger.
 *
 * Reads `ctx.sessionManager.getBranch()` and filters for write/edit tool
 * calls made in this session. NEVER reads the working tree, NEVER runs
 * `git diff`. The branch is the session's own edit ledger.
 *
 * Each session's branch is append-only / immutable; this module does not
 * mutate state, only reads.
 *
 * Per the handoff (Option A): "Reading a file's current content to enrich
 * a diff is acceptable ONLY if keyed to a path the session itself edited
 * — never to discover what changed." We never do file reads at all —
 * the entry shape carries enough.
 */

import type { ExtensionContext } from "@earendil-works/pi-coding-agent";

export interface ChangeSetEntry {
	readonly toolName: "edit" | "write";
	readonly path: string;
	readonly before: string | undefined;
	readonly after: string;
	readonly entryId: string;
	readonly entryTimestamp: number;
}

export interface ChangeSet {
	readonly entries: readonly ChangeSetEntry[];
	readonly distinctPaths: readonly string[];
	readonly source: "session-ledger";
	readonly note: string;
}

interface AnyToolCall {
	type: "toolCall";
	name?: string;
	toolName?: string;
	arguments?: Record<string, unknown>;
}

interface AnyMessageEntry {
	role: string;
	content?: Array<{ type: string } & Record<string, unknown>>;
}

interface AnyEntry {
	id?: string;
	type?: string;
	timestamp?: number;
	message?: AnyMessageEntry;
}

function asToolCalls(entry: AnyEntry | undefined): AnyToolCall[] {
	if (!entry || entry.type !== "message") return [];
	const msg = entry.message;
	if (!msg || !Array.isArray(msg.content)) return [];
	const out: AnyToolCall[] = [];
	for (const block of msg.content) {
		if (block && (block as { type?: string }).type === "toolCall") {
			out.push(block as unknown as AnyToolCall);
		}
	}
	return out;
}

function buildEditEntry(
	entry: AnyEntry,
	tc: AnyToolCall,
	idx: number,
): ChangeSetEntry | null {
	const args = (tc.arguments ?? {}) as { path?: unknown; edits?: unknown; content?: unknown };
	if (typeof args.path !== "string") return null;
	if (tc.name === "edit" || tc.toolName === "edit") {
		if (!Array.isArray(args.edits) || args.edits.length === 0) return null;
		const merged: { before: string[]; after: string[] } = { before: [], after: [] };
		for (const e of args.edits as Array<{ oldText?: unknown; newText?: unknown }>) {
			if (typeof e.oldText === "string") merged.before.push(e.oldText);
			if (typeof e.newText === "string") merged.after.push(e.newText);
		}
		return {
			toolName: "edit",
			path: args.path,
			before: merged.before.length > 0 ? merged.before.join("\n--- next edit ---\n") : undefined,
			after: merged.after.join("\n--- next edit ---\n"),
			entryId: (entry.id as string | undefined) ?? `branch-idx-${idx}`,
			entryTimestamp: (entry.timestamp as number | undefined) ?? 0,
		};
	}
	if (tc.name === "write" || tc.toolName === "write") {
		return {
			toolName: "write",
			path: args.path,
			before: undefined,
			after: typeof args.content === "string" ? args.content : "",
			entryId: (entry.id as string | undefined) ?? `branch-idx-${idx}`,
			entryTimestamp: (entry.timestamp as number | undefined) ?? 0,
		};
	}
	return null;
}

export function getSessionChangeSet(ctx: ExtensionContext): ChangeSet {
	const sm = (ctx as { sessionManager?: { getBranch?: () => unknown[] } }).sessionManager;
	const branch = typeof sm?.getBranch === "function" ? sm.getBranch() : null;
	if (!Array.isArray(branch)) {
		return {
			entries: [],
			distinctPaths: [],
			source: "session-ledger",
			note: "sessionManager.getBranch() not available",
		};
	}
	const entries: ChangeSetEntry[] = [];
	for (let i = 0; i < branch.length; i++) {
		const entry = branch[i] as AnyEntry;
		const toolCalls = asToolCalls(entry);
		for (const tc of toolCalls) {
			const cs = buildEditEntry(entry, tc, i);
			if (cs) entries.push(cs);
		}
	}
	const distinctPaths = Array.from(new Set(entries.map((e) => e.path)));
	return {
		entries,
		distinctPaths,
		source: "session-ledger",
		note: `read ${branch.length} branch entries, ${entries.length} write/edit found`,
	};
}

const MAX_PROMPT_FIELD_CHARS = 2000;

function truncate(s: string, max: number): string {
	if (s.length <= max) return s;
	return `${s.slice(0, max)}\n... [truncated ${s.length - max} chars]`;
}

export function buildChangeSetPrompt(cs: ChangeSet): string {
	if (cs.entries.length === 0) return "(no changes recorded in this session)";
	return cs.entries
		.map(
			(e, i) =>
				`[${i}] ${e.toolName} @ ${new Date(e.entryTimestamp).toISOString()} -> ${e.path}\n` +
				`    before: ${truncate(e.before ?? "(none)", MAX_PROMPT_FIELD_CHARS)}\n` +
				`    after: ${truncate(e.after, MAX_PROMPT_FIELD_CHARS)}`,
		)
		.join("\n");
}
