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

async function ensureWorkspaceMounted(
  settings: WorkspaceSettings,
  resizePct: number | null,
  ctx: any | null,
): Promise<void> {
  if (getWorkspaceElement()) return;
  mountWorkspace(ctx, settings, (s) => void saveSettings(s));
  if (resizePct !== null) {
    applyResize(resizePct);
  }
  mountResizer((pct) => void saveResizePreference(pct));
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

    // Auto-open or restore prior workspace state
    let shouldOpen = false;
    let initialCtx = null;

    try {
      const response = await chrome.runtime.sendMessage({
        type: "query-workspace-state",
      });
      if (response?.open) {
        shouldOpen = true;
        initialCtx = response.videoContext ?? null;
      }
    } catch {
      // Background might not be ready
    }

    // If not explicitly opened, check autoOpen setting
    if (!shouldOpen && settings.autoOpen && isYouTubeWatchPage()) {
      shouldOpen = true;
      // Trigger acquisition via background so VideoContext gets populated
      try {
        await chrome.runtime.sendMessage({ type: "auto-open" });
      } catch {
        // proceed — workspace mounts without VideoContext, will update later
      }
    }

    if (shouldOpen) {
      await ensureWorkspaceMounted(settings, resizePct, initialCtx);
    }

    chrome.runtime.onMessage.addListener((message) => {
      if (message?.type === "workspace-toggle") {
        if (message.open) {
          ensureWorkspaceMounted(
            settings,
            resizePct,
            message.videoContext ?? null,
          );
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
