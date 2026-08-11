/**
 * Content script (WXT entrypoint) — workspace lifecycle + navigation relay.
 *
 * VS-03 + UX features: font size settings, resize handle.
 * Handles: workspace-toggle, workspace-update messages from background.
 * Relays: yt-navigate-finish events to background for re-acquisition.
 * Persistence: workspace open state, font size, column width — all survive reloads.
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
  applyFontSize,
  DEFAULT_FONT_SIZE,
  type WorkspaceSettings,
} from "../content/settings";
import {
  mountResizer,
  applyResize,
  clearResize,
  loadResizePreference,
  saveResizePreference,
  DEFAULT_PCT,
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

    // Check if workspace was open before page load (persistence)
    let initialCtx = null;
    try {
      const response = await chrome.runtime.sendMessage({
        type: "query-workspace-state",
      });
      if (response?.open) {
        initialCtx = response.videoContext ?? null;
        mountWorkspace(initialCtx, settings, handleSettingsChange);

        if (resizePct !== null) {
          applyResize(resizePct);
        }
        mountResizer(handleResizeChange);
      }
    } catch {
      // Background might not be ready yet
    }

    chrome.runtime.onMessage.addListener((message) => {
      if (message?.type === "workspace-toggle") {
        if (message.open) {
          mountWorkspace(message.videoContext ?? null, settings, handleSettingsChange);
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
