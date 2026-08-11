/**
 * Content script (WXT entrypoint) — workspace lifecycle + navigation relay.
 *
 * Auto-open: when settings.autoOpen is true (default), the workspace
 * mounts automatically on YouTube watch pages.
 *
 * Uses a poller to wait for #secondary (YouTube's SPA means it may
 * not be ready at document_idle).
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

function waitForElement(
  selector: string,
  timeoutMs = 10000,
): Promise<HTMLElement | null> {
  return new Promise((resolve) => {
    const existing = document.querySelector(selector);
    if (existing) {
      resolve(existing as HTMLElement);
      return;
    }

    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el as HTMLElement);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeoutMs);
  });
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

    let workspaceMounted = false;

    const mountIfNeeded = async () => {
      if (workspaceMounted || !isYouTubeWatchPage()) return;
      if (!settings.autoOpen) return;

      // Wait for #secondary to be available (YouTube SPA timing)
      const secondary = await waitForElement("#secondary", 10000);
      if (!secondary) return;

      if (getWorkspaceElement()) return;

      mountWorkspace(null, settings, handleSettingsChange);
      workspaceMounted = true;

      if (resizePct !== null) {
        applyResize(resizePct);
      }
      mountResizer(handleResizeChange);

      // Trigger acquisition (fire-and-forget)
      chrome.runtime.sendMessage({ type: "acquire" }).catch(() => {});
    };

    // Register message listener for toolbar toggle and workspace-update
    chrome.runtime.onMessage.addListener((message) => {
      if (message?.type === "workspace-toggle") {
        if (message.open) {
          mountWorkspace(
            message.videoContext ?? null,
            settings,
            handleSettingsChange,
          );
          workspaceMounted = true;
          if (resizePct !== null) {
            applyResize(resizePct);
          }
          mountResizer(handleResizeChange);
        } else {
          detachWorkspace();
          workspaceMounted = false;
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

    // Try mounting on initial load
    mountIfNeeded();

    // Re-mount on SPA navigation
    document.addEventListener("yt-navigate-finish", () => {
      chrome.runtime
        .sendMessage({ type: "yt-navigate-finish", url: location.href })
        .catch(() => {});

      // Reset and re-mount if needed
      workspaceMounted = false;
      mountIfNeeded();
    });
  },
});
