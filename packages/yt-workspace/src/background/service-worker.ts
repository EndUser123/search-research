/**
 * Service worker logic — event wiring for acquisition + workspace toggle.
 *
 * Uses content-script-relayed yt-navigate-finish events instead of
 * chrome.webNavigation (avoids needing webNavigation permission).
 * The content script listens for yt-navigate-finish on the document
 * and messages the background to trigger re-acquisition.
 */

import { acquireVideoContext } from "./acquire";
import {
  getAuthoritativeVideoId,
  setAuthoritativeVideoId,
  clearTabState,
  getLastAccepted,
  readPersistedContext,
  type VideoContext,
} from "../lib/video-context-store";

const YOUTUBE_HOST_PATTERN = /^https?:\/\/([a-z0-9-]+\.)*youtube\.com\//i;

function isYouTubeWatchUrl(url: string): boolean {
  if (!YOUTUBE_HOST_PATTERN.test(url)) return false;
  try {
    const u = new URL(url);
    return (
      (u.pathname === "/watch" && u.searchParams.has("v")) ||
      u.pathname.startsWith("/shorts/")
    );
  } catch {
    return false;
  }
}

function extractVideoId(url: string): string | null {
  try {
    const u = new URL(url);
    return (
      u.searchParams.get("v") ??
      u.pathname.match(/^\/shorts\/([^/?#]+)/)?.[1] ??
      null
    );
  } catch {
    return null;
  }
}

export async function handleToolbarClick(tab: chrome.tabs.Tab): Promise<void> {
  if (!tab.id || !tab.url || !isYouTubeWatchUrl(tab.url)) {
    return;
  }

  const tabId = tab.id;
  const key = `workspace-open-${tabId}`;
  const stored = await chrome.storage.session.get(key);
  const isOpen = stored[key] ?? false;
  const nextState = !isOpen;

  await chrome.storage.session.set({ [key]: nextState });

  if (nextState) {
    const ctx = await acquireVideoContext(tabId);
    chrome.tabs
      .sendMessage(tabId, {
        type: "workspace-toggle",
        open: true,
        videoContext: ctx,
      })
      .catch(() => {});
  } else {
    chrome.tabs
      .sendMessage(tabId, { type: "workspace-toggle", open: false })
      .catch(() => {});
  }
}

export async function handleNavigationMessage(
  tabId: number,
  url: string,
): Promise<void> {
  if (!isYouTubeWatchUrl(url)) return;

  const videoId = extractVideoId(url);
  if (!videoId) return;

  const current = getAuthoritativeVideoId(tabId);
  if (current === videoId) return;

  setAuthoritativeVideoId(tabId, videoId, url);

  const key = `workspace-open-${tabId}`;
  const stored = await chrome.storage.session.get(key);
  if (stored[key] !== true) return;

  const ctx = await acquireVideoContext(tabId);
  if (ctx) {
    chrome.tabs
      .sendMessage(tabId, {
        type: "workspace-update",
        videoContext: ctx,
      })
      .catch(() => {});
  }
}

// Self-contained seek function for MAIN-world injection.
// Chrome serializes this — no closures, no external references.
function performSeek(seconds: number): boolean {
  const media = document.querySelector("video") as HTMLVideoElement | null;
  if (media) {
    try {
      media.currentTime = seconds;
      return true;
    } catch {
      /* fallthrough */
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

export async function handleSeekRequest(
  tabId: number,
  seconds: number,
): Promise<{ ok: boolean; beforeTime: number; afterTime: number }> {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return { ok: false, beforeTime: -1, afterTime: -1 };
  }

  let beforeTime = -1;
  let afterTime = -1;

  try {
    const [beforeInjection] = await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN" as chrome.scripting.ExecutionWorld,
      func: () => {
        const v = document.querySelector("video") as HTMLVideoElement | null;
        return v?.currentTime ?? -1;
      },
    });
    beforeTime = (beforeInjection?.result as number) ?? -1;
  } catch {
    /* proceed with seek anyway */
  }

  let seekOk = false;
  try {
    const [seekInjection] = await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN" as chrome.scripting.ExecutionWorld,
      func: performSeek,
      args: [seconds],
    });
    seekOk = (seekInjection?.result as boolean) ?? false;
  } catch {
    return { ok: false, beforeTime, afterTime: -1 };
  }

  try {
    const [afterInjection] = await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN" as chrome.scripting.ExecutionWorld,
      func: () => {
        const v = document.querySelector("video") as HTMLVideoElement | null;
        return v?.currentTime ?? -1;
      },
    });
    afterTime = (afterInjection?.result as number) ?? -1;
  } catch {
    /* afterTime stays -1 */
  }

  return { ok: seekOk, beforeTime, afterTime };
}

export function handleTabClosed(tabId: number): void {
  clearTabState(tabId);
  chrome.storage.session.remove(`workspace-open-${tabId}`).catch(() => {});
  chrome.storage.local.remove(`videoContext-${tabId}`).catch(() => {});
}

export async function handleQueryWorkspaceState(
  tabId: number,
): Promise<{ open: boolean; videoContext: VideoContext | null }> {
  const key = `workspace-open-${tabId}`;
  const stored = await chrome.storage.session.get(key);
  const open = stored[key] === true;
  const videoContext = open ? await readPersistedContext(tabId) : null;
  return { open, videoContext };
}

export { getLastAccepted, type VideoContext };
