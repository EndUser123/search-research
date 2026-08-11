/**
 * Seek handler — relay chapter-row clicks through the extension bridge.
 *
 * VS-04: on chapter-row click in the workspace, compute seconds from the
 * row's timestamp, send a message to the background service worker, which
 * invokes chrome.scripting.executeScript({ world: "MAIN" }) to call
 * movie_player.seekTo() or set video.currentTime.
 */

import type { Chapter } from "../lib/video-context-store";

const WORKSPACE_ID = "__yt_workspace";

/**
 * Attach click handlers to chapter rows in the workspace.
 * Called after renderVideoContext populates the tab content.
 * Uses event delegation to avoid listener stacking on re-renders.
 */
export function attachSeekHandlers(
  workspace: HTMLElement,
  chapters: Chapter[],
): void {
  const contentEl = workspace.querySelector('[data-field="tab-content"]');
  if (!contentEl) return;

  // Remove any existing delegated click handler
  const existing = contentEl.getAttribute("data-seek-bound");
  if (existing) {
    contentEl.removeEventListener("click", seekClickHandler);
  }

  // Store chapters map on the content element for the handler to read
  contentEl.setAttribute("data-seek-bound", "true");

  function seekClickHandler(e: Event): void {
    const target = e.target as HTMLElement;
    const row = target.closest(".ytws-chapter-row") as HTMLElement | null;
    if (!row) return;

    const container = contentEl as HTMLElement;
    const rows = container.querySelectorAll(".ytws-chapter-row");
    const index = Array.from(rows).indexOf(row);
    const chapter = chapters[index];
    if (!chapter) return;

    const seconds = chapter.startSeconds;
    chrome.runtime
      .sendMessage({ type: "seek", seconds })
      .catch(() => {});
  }

  contentEl.addEventListener("click", seekClickHandler);
}
