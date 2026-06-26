/**
 * Extract candidate paths from a user prompt.
 *
 * Deterministic: pulls out slash-delimited paths and filenames with
 * known code/doc extensions. Ignores URLs. Returns unique normalized
 * forward-slash paths only.
 */

const FILE_EXTENSIONS = [
	"ts",
	"tsx",
	"js",
	"jsx",
	"mjs",
	"cjs",
	"py",
	"rb",
	"go",
	"rs",
	"java",
	"kt",
	"swift",
	"cpp",
	"hpp",
	"md",
	"mdx",
	"json",
	"yml",
	"yaml",
	"toml",
	"ini",
	"sh",
	"bash",
	"zsh",
	"tf",
	"sql",
	"html",
	"css",
	"scss",
	"vue",
	"svelte",
];

const EXT_PATTERN = FILE_EXTENSIONS.join("|");

// Slash-delimited path segments (incl. dotfiles like .github/workflows/ci.yml).
// Stops at whitespace, quotes, parens, brackets, commas, semicolons, pipes.
const PATH_TOKEN_RE = new RegExp(
	`(?:\\.{0,2}/)?(?:\\.{1,2}/|[\\w.\\-]+/)+[\\w.\\-]*\\.(?:${EXT_PATTERN})\\b`,
	"g",
);

// Bare filename (no slash) with a known extension.
const BARE_FILENAME_RE = new RegExp(`\\b[\\w.\\-]+\\.(?:${EXT_PATTERN})\\b`, "g");

// URL detector: skip anything that looks like http(s)://, ftp://, file://, etc.
const URL_RE = /\b[a-z][a-z0-9+.-]*:\/\/[^\s<>"'`)\]]+/gi;

function normalizePath(p: string): string {
	return p.replace(/\\/g, "/").replace(/^\.\//, "").replace(/^\/+/, "");
}

export function extractCandidatePaths(text: string): string[] {
	if (!text) return [];

	// Mask URL regions with spaces so path regexes can't see inside them.
	// Keep original text length so match indices remain valid (unused after masking,
	// but we only collect normalized strings, not indices).
	let masked = text.replace(URL_RE, (m) => " ".repeat(m.length));

	const slashPaths = new Set<string>();
	const bareFilenames = new Set<string>();

	const collect = (regex: RegExp, sink: Set<string>) => {
		for (const m of masked.matchAll(regex)) {
			sink.add(normalizePath(m[0]));
		}
	};

	collect(PATH_TOKEN_RE, slashPaths);
	collect(BARE_FILENAME_RE, bareFilenames);

	// When a slash path is present, drop any bare filename that is a suffix of it.
	for (const p of slashPaths) {
		const slashIdx = p.lastIndexOf("/");
		if (slashIdx >= 0) {
			const suffix = p.slice(slashIdx + 1);
			bareFilenames.delete(suffix);
		}
	}

	return [...slashPaths, ...bareFilenames];
}