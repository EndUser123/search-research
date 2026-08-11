/**
 * Ask panel — keyword search over the transcript.
 *
 * Full AI Q&A is Gate 3 (needs a model backend). This panel provides
 * a simple search: type keywords, see matching transcript segments.
 * The search box appears when a transcript is loaded.
 */

import type { CaptionTrack } from "../lib/video-context-store";

interface SearchResult {
  startMs: number;
  text: string;
  query: string;
}

function formatTimestamp(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function renderAsk(
  container: HTMLElement,
  transcriptSegments: Array<{ startMs: number; text: string }> | null,
): void {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  if (!transcriptSegments || transcriptSegments.length === 0) {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "Ask requires a transcript. No caption tracks available for this video.";
    container.appendChild(empty);
    return;
  }

  const searchBox = document.createElement("input");
  searchBox.type = "text";
  searchBox.placeholder = "Search transcript...";
  searchBox.className = "ytws-ask-input";
  container.appendChild(searchBox);

  const resultsContainer = document.createElement("div");
  resultsContainer.className = "ytws-ask-results";
  container.appendChild(resultsContainer);

  const hint = document.createElement("div");
  hint.className = "ytws-ask-hint";
  hint.textContent = `Searching ${transcriptSegments.length} transcript segments. AI-powered Q&A coming soon.`;
  resultsContainer.appendChild(hint);

  searchBox.addEventListener("input", () => {
    const query = searchBox.value.trim().toLowerCase();
    while (resultsContainer.firstChild) {
      resultsContainer.removeChild(resultsContainer.firstChild);
    }

    if (!query) {
      hint.textContent = `Searching ${transcriptSegments.length} transcript segments. AI-powered Q&A coming soon.`;
      resultsContainer.appendChild(hint);
      return;
    }

    const terms = query.split(/\s+/);
    const matches: SearchResult[] = [];

    for (const seg of transcriptSegments) {
      const textLower = seg.text.toLowerCase();
      if (terms.every((t) => textLower.includes(t))) {
        matches.push({ startMs: seg.startMs, text: seg.text, query });
      }
    }

    if (matches.length === 0) {
      const noResults = document.createElement("div");
      noResults.className = "ytws-empty";
      noResults.textContent = `No matches for "${query}"`;
      resultsContainer.appendChild(noResults);
      return;
    }

    const countHeader = document.createElement("div");
    countHeader.className = "ytws-ask-hint";
    countHeader.textContent = `${matches.length} match${matches.length > 1 ? "es" : ""} for "${query}"`;
    resultsContainer.appendChild(countHeader);

    const maxResults = matches.slice(0, 50);
    for (const match of maxResults) {
      const row = document.createElement("div");
      row.className = "ytws-transcript-row";

      const time = document.createElement("span");
      time.className = "ytws-transcript-time";
      time.textContent = formatTimestamp(match.startMs);
      row.appendChild(time);

      const text = document.createElement("span");
      text.className = "ytws-transcript-text";

      const lowerText = match.text.toLowerCase();
      let lastIdx = 0;
      for (const term of terms) {
        const idx = lowerText.indexOf(term, lastIdx);
        if (idx >= 0) {
          if (idx > lastIdx) {
            text.appendChild(document.createTextNode(match.text.slice(lastIdx, idx)));
          }
          const mark = document.createElement("mark");
          mark.textContent = match.text.slice(idx, idx + term.length);
          mark.className = "ytws-ask-highlight";
          text.appendChild(mark);
          lastIdx = idx + term.length;
        }
      }
      if (lastIdx < match.text.length) {
        text.appendChild(document.createTextNode(match.text.slice(lastIdx)));
      }

      row.appendChild(text);
      resultsContainer.appendChild(row);
    }
  });
}
