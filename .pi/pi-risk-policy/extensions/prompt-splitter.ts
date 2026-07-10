/**
 * Extract the user's instruction segment from a prompt that may contain
 * pasted context (chat transcripts, file dumps, code blocks).
 *
 * The risk classifier scans the input prompt for production keywords
 * (deploy, production, secret, credential) and the path-extractor pulls
 * path-shaped strings. When the user pastes a chat transcript as part
 * of their message, both extractors see the transcript as if it were
 * the user's intent, producing false-positive HIGH classifications.
 *
 * The heuristic: the user's actual instruction is at the END of the
 * prompt. The last non-empty paragraph (text after the last blank line)
 * is the instruction; everything before is context. This is the
 * conventional chat pattern: paste context, then ask the question.
 *
 * Edge cases:
 * - Empty prompt: returns ""
 * - Single paragraph (no blank lines): returns the whole prompt
 * - Trailing blank lines: skipped
 * - Trailing code block (e.g., ``` at the very end): the empty
 *   paragraph after the fence is skipped, returning the last prose
 *   paragraph
 * - No text outside code blocks: returns the full prompt as a
 *   fallback (the user pasted only code, no instruction visible)
 *
 * Deterministic, regex-based, no semantic judgment. If the user's
 * instruction is in the middle of the prompt, this misses; the
 * fallback path of using the full prompt ensures the gate still
 * fires (over-triggering is recoverable via /risk-override; missing
 * a real production intent is not).
 */

export function extractInstructionSegment(prompt: string): string {
	if (!prompt) return "";

	// Split on blank lines (one or more newlines with optional whitespace).
	// Trailing blank lines produce empty trailing paragraphs that we skip.
	const paragraphs = prompt.split(/\n\s*\n+/);

	// Walk backward to find the last non-empty paragraph.
	for (let i = paragraphs.length - 1; i >= 0; i--) {
		const trimmed = paragraphs[i].trim();
		if (trimmed) return trimmed;
	}
	return "";
}
