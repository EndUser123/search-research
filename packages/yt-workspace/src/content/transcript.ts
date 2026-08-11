/**
 * Transcript panel — fetches and displays caption track text.
 *
 * Uses the caption track baseUrl from the VideoContext to fetch
 * the raw timedtext XML from YouTube, parses it into timestamped
 * segments, and renders a scrollable transcript.
 */

import type { CaptionTrack } from "../lib/video-context-store";

interface TranscriptSegment {
  startMs: number;
  text: string;
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

function parseTimedTextXml(xml: string): TranscriptSegment[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, "text/xml");
  const segments: TranscriptSegment[] = [];

  const textNodes = doc.querySelectorAll("text");
  textNodes.forEach((node) => {
    const start = parseFloat(node.getAttribute("start") ?? "0");
    const text = (node.textContent ?? "").trim();
    if (text) {
      segments.push({ startMs: start * 1000, text });
    }
  });

  return segments;
}

export async function fetchTranscript(
  tracks: CaptionTrack[],
): Promise<{ segments: TranscriptSegment[]; trackLabel: string } | null> {
  if (tracks.length === 0) return null;

  const track =
    tracks.find((t) => t.languageCode === "en" && t.kind !== "asr") ??
    tracks.find((t) => t.languageCode.startsWith("en")) ??
    tracks[0];

  if (!track) return null;

  try {
    const response = await fetch(track.baseUrl);
    if (!response.ok) return null;
    const xml = await response.text();
    const segments = parseTimedTextXml(xml);
    if (segments.length === 0) return null;
    return {
      segments,
      trackLabel: track.name || track.languageCode,
    };
  } catch {
    return null;
  }
}

export function renderTranscript(
  container: HTMLElement,
  data: { segments: TranscriptSegment[]; trackLabel: string } | null,
): void {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  if (!data || data.segments.length === 0) {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "No transcript available for this video";
    container.appendChild(empty);
    return;
  }

  const header = document.createElement("div");
  header.className = "ytws-transcript-header";
  header.textContent = `Track: ${data.trackLabel} (${data.segments.length} segments)`;
  container.appendChild(header);

  for (const seg of data.segments) {
    const row = document.createElement("div");
    row.className = "ytws-transcript-row";

    const time = document.createElement("span");
    time.className = "ytws-transcript-time";
    time.textContent = formatTimestamp(seg.startMs);
    row.appendChild(time);

    const text = document.createElement("span");
    text.className = "ytws-transcript-text";
    text.textContent = seg.text;
    row.appendChild(text);

    container.appendChild(row);
  }
}
