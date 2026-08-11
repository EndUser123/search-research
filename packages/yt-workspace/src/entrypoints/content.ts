/**
 * Content script — workspace injector.
 *
 * VS-01 scope: receives workspace-toggle messages from background, mounts/detaches
 * a placeholder workspace element in #secondary. No real VideoContext or chapter
 * rendering yet — that lands in VS-02..03.
 *
 * YouTube enforces Trusted Types — all DOM construction uses createElement/textContent,
 * never innerHTML.
 */
import { defineContentScript } from "wxt/utils/define-content-script";

const WORKSPACE_ID = "__yt_workspace";

function createWorkspaceElement(videoId: string): HTMLElement {
  const el = document.createElement("div");
  el.id = WORKSPACE_ID;
  el.style.cssText = [
    "padding: 12px",
    "margin-bottom: 8px",
    "background: #0f0f0f",
    "color: #f1f1f1",
    "border-radius: 8px",
    "font-family: 'YouTube Sans', Roboto, sans-serif",
    "font-size: 14px",
  ].join("; ");

  const header = document.createElement("strong");
  header.textContent = "YT Workspace";
  header.style.cssText = "display: block; margin-bottom: 8px; font-size: 16px;";
  el.appendChild(header);

  const info = document.createElement("div");
  info.textContent = `videoId: ${videoId}`;
  info.style.cssText = "opacity: 0.7; margin-bottom: 8px;";
  el.appendChild(info);

  const tabsBar = document.createElement("div");
  tabsBar.style.cssText = "display: flex; gap: 12px; margin-bottom: 8px;";
  const tabNames = ["Chapters", "Overview", "Ask", "Transcript", "Links"];
  for (const name of tabNames) {
    const tab = document.createElement("span");
    tab.textContent = name;
    const isChapters = name === "Chapters";
    tab.style.cssText = isChapters
      ? "padding: 4px 8px; border-bottom: 2px solid #3ea6ff; cursor: pointer;"
      : "padding: 4px 8px; opacity: 0.4; cursor: not-allowed;";
    tabsBar.appendChild(tab);
  }
  el.appendChild(tabsBar);

  const chapters = document.createElement("div");
  chapters.textContent = "Loading chapters...";
  chapters.style.cssText = "min-height: 40px;";
  el.appendChild(chapters);

  return el;
}

function getCurrentVideoId(): string | null {
  try {
    const url = new URL(location.href);
    return url.searchParams.get("v");
  } catch {
    return null;
  }
}

function mountWorkspace(): void {
  const existing = document.querySelectorAll(`#${WORKSPACE_ID}`);
  if (existing.length > 1) {
    existing[1].remove();
  }
  if (existing.length === 1) {
    return;
  }
  const videoId = getCurrentVideoId() ?? "unknown";
  const workspace = createWorkspaceElement(videoId);
  const secondary = document.querySelector("#secondary");
  if (secondary) {
    secondary.prepend(workspace);
  }
}

function detachWorkspace(): void {
  document.querySelectorAll(`#${WORKSPACE_ID}`).forEach((el) => el.remove());
}

export default defineContentScript({
  matches: ["*://*.youtube.com/*"],
  runAt: "document_idle",
  async main() {
    chrome.runtime.onMessage.addListener((message) => {
      if (message?.type === "workspace-toggle") {
        if (message.open) {
          mountWorkspace();
        } else {
          detachWorkspace();
        }
      }
      return false;
    });

    document.addEventListener("yt-navigate-finish", () => {
      const workspace = document.querySelector(`#${WORKSPACE_ID}`);
      if (workspace) {
        const videoId = getCurrentVideoId() ?? "unknown";
        const infoEl = workspace.querySelector("div");
        if (infoEl) {
          infoEl.textContent = `videoId: ${videoId}`;
        }
      }
    });
  },
});
