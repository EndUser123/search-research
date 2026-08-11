/**
 * Content script (WXT entrypoint) — workspace lifecycle + navigation relay.
 *
 * Auto-open: when settings.autoOpen is true (default), the workspace
 * mounts automatically on YouTube watch pages. The toolbar button
 * toggles it off/on. The setting persists across reloads.
 */

import { defineContentScript } from "wxt/utils/define-content-script";
import {
  mountWorkspace,
  detachWorkspace,
  renderVideoContext,
  getWorkspaceElement,
} from "../content/workspace-ui";
import { WORKSPACE_CSS } from "../content/workspace.css";
import {
  loadSettings,
  saveSettings,
  type WorkspaceSettings,
} from "../content/settings";
import {
  mountResizer,
  applyResize,
  clearResize,
  loadResizePreference,
  saveResizePreference,
} from "../content/resizer";

const STYLE_ID = "__yt_workspace_style";

function injectStyles(): void {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = WORKSPACE_CSS;
  document.head.appendChild(style);
}

function getCurrentVideoId(): string | null {
  try {
    const url = new URL(location.href);
    return url.searchParams.get("v");
  } catch {
    return null;
  }
}

function isYouTubeWatchPage(): boolean {
  try {
    const u = new URL(location.href);
    return (
      (u.pathname === "/watch" && u.searchParams.has("v")) ||
      u.pathname.startsWith("/shorts/")
    );
  } catch {
    return false;
  }
}

export default defineContentScript({
  matches: ["*://*.youtube.com/*"],
  runAt: "document_idle",
  async main() {
    injectStyles();

    const settings = await loadSettings();
    const resizePct = await loadResizePreference();

    const handleSettingsChange = (s: WorkspaceSettings) => {
      void saveSettings(s);
    };

    const handleResizeChange = (pct: number) => {
      void saveResizePreference(pct);
    };

    // Register message listener FIRST so we don't miss workspace-update
    chrome.runtime.onMessage.addListener((message) => {
      if (message?.type === "workspace-toggle") {
        if (message.open) {
          mountWorkspace(
            message.videoContext ?? null,
            settings,
            handleSettingsChange,
          );
          if (resizePct !== null) {
            applyResize(resizePct);
          }
          mountResizer(handleResizeChange);
        } else {
          detachWorkspace();
          clearResize();
        }
      } else if (message?.type === "workspace-update") {
        const workspace = getWorkspaceElement();
        if (workspace) {
          renderVideoContext(workspace, message.videoContext ?? null);
        }
      }
      return false;
    });

    // Determine whether workspace should be open
    let shouldOpen = false;

    try {
      const response = await chrome.runtime.sendMessage({
        type: "query-workspace-state",
      });
      if (response?.open) {
        shouldOpen = true;
      }
    } catch {
      // Background might not be ready yet
    }

    // If not explicitly opened, auto-open on watch pages
    if (!shouldOpen && settings.autoOpen && isYouTubeWatchPage()) {
      shouldOpen = true;
      try {
        await chrome.runtime.sendMessage({ type: "auto-open" });
      } catch {
        // Background might not be ready — mount anyway
      }
    }

    if (shouldOpen && isYouTubeWatchPage()) {
      // Mount the workspace immediately (shows "Loading...")
      mountWorkspace(null, settings, handleSettingsChange);
      if (resizePct !== null) {
        applyResize(resizePct);
      }
      mountResizer(handleResizeChange);

      // Request acquisition — the background will send workspace-update
      // with the VideoContext once MAIN-world eval completes
      try {
        await chrome.runtime.sendMessage({ type: "auto-open" });
      } catch {
        // If background fails, workspace stays in "Loading..." state
      }
    }

    document.addEventListener("yt-navigate-finish", () => {
      chrome.runtime
        .sendMessage({ type: "yt-navigate-finish", url: location.href })
        .catch(() => {});

      const workspace = getWorkspaceElement();
      if (workspace) {
        const videoId = getCurrentVideoId() ?? "unknown";
        const videoIdEl = workspace.querySelector('[data-field="video-id"]');
        if (videoIdEl) {
          videoIdEl.textContent = `videoId: ${videoId}`;
        }
      }
    });
  },
});
