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

export function handleTabClosed(tabId: number): void {
  clearTabState(tabId);
  chrome.storage.session.remove(`workspace-open-${tabId}`).catch(() => {});
  chrome.storage.local.remove(`videoContext-${tabId}`).catch(() => {});
}

export { getLastAccepted, type VideoContext };
