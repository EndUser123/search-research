/**
 * Overview panel — shows the video description + chapter table of contents.
 *
 * No AI-generated summary (that's Gate 3). This is the raw description
 * text formatted for readability, plus a chapter overview.
 */

import type { Chapter } from "../lib/video-context-store";

export function renderOverview(
  container: HTMLElement,
  data: { description: string | null; chapters: Chapter[]; title: string },
): void {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  const titleEl = document.createElement("div");
  titleEl.className = "ytws-overview-title";
  titleEl.textContent = data.title;
  container.appendChild(titleEl);

  if (data.chapters.length > 0) {
    const tocHeader = document.createElement("div");
    tocHeader.className = "ytws-overview-section";
    tocHeader.textContent = "Contents";
    container.appendChild(tocHeader);

    for (const ch of data.chapters) {
      const row = document.createElement("div");
      row.className = "ytws-overview-toc-row";

      const time = document.createElement("span");
      time.className = "ytws-chapter-time";
      time.textContent = ch.timeDisplay;
      row.appendChild(time);

      const title = document.createElement("span");
      title.className = "ytws-chapter-title";
      title.textContent = ch.title;
      row.appendChild(title);

      container.appendChild(row);
    }
  }

  if (data.description) {
    const descHeader = document.createElement("div");
    descHeader.className = "ytws-overview-section";
    descHeader.textContent = "Description";
    container.appendChild(descHeader);

    const desc = document.createElement("div");
    desc.className = "ytws-overview-description";
    desc.textContent = data.description;
    container.appendChild(desc);
  }

  if (!data.description && data.chapters.length === 0) {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "No overview data available";
    container.appendChild(empty);
  }
}
