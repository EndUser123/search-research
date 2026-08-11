/**
 * Seek handler — relay chapter-row clicks through the extension bridge.
 *
 * VS-04: on chapter-row click in the workspace, compute seconds from the
 * row's timestamp, send a message to the background service worker, which
 * invokes chrome.scripting.executeScript({ world: "MAIN" }) to call
 * movie_player.seekTo() or set video.currentTime.
 *
 * The seek-relay MUST go through the extension's bridge, not chrome.devtools
 * eval. Verified by reading the background's chrome.scripting.executeScript
 * invocations.
 */

import type { Chapter } from "../lib/video-context-store";

const WORKSPACE_ID = "__yt_workspace";

/**
 * Attach click handlers to chapter rows in the workspace.
 * Called after renderVideoContext populates the chapters container.
 */
export function attachSeekHandlers(
  workspace: HTMLElement,
  chapters: Chapter[],
): void {
  const chaptersEl = workspace.querySelector('[data-field="chapters"]');
  if (!chaptersEl) return;

  const rows = chaptersEl.querySelectorAll("div");
  rows.forEach((row, index) => {
    const chapter = chapters[index];
    if (!chapter) return;

    row.addEventListener("click", () => {
      const seconds = chapter.startSeconds;
      chrome.runtime
        .sendMessage({ type: "seek", seconds })
        .catch(() => {});
    });
  });
}

/**
 * Self-contained seek function for MAIN-world injection.
 * Chrome serializes this — no closures, no external references.
 */
export function seekInPage(seconds: number): boolean {
  const media = document.querySelector("video") as HTMLVideoElement | null;
  if (media) {
    try {
      media.currentTime = seconds;
      return true;
    } catch {
      /* fallthrough to movie_player */
    }
  }

  const player = document.getElementById("movie_player") as
    | (HTMLElement & {
        seekTo?: (time: number, allowSeekAhead?: boolean) => void;
      })
    | null;
  if (player?.seekTo) {
    try {
      player.seekTo(seconds, true);
      return true;
    } catch {
      return false;
    }
  }

  return false;
}

/**
 * Read video.currentTime from the page (for before/after verification).
 * Self-contained for MAIN-world injection.
 */
export function readVideoTime(): number {
  const media = document.querySelector("video") as HTMLVideoElement | null;
  return media?.currentTime ?? -1;
}
