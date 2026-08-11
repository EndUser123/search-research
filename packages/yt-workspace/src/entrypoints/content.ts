/**
 * Content script — workspace injector + navigation relay.
 *
 * VS-02: relays yt-navigate-finish events to background for re-acquisition,
 * and handles workspace-toggle / workspace-update messages with real
 * VideoContext data (chapter rendering lands in VS-03).
 *
 * YouTube enforces Trusted Types — all DOM construction uses createElement/textContent.
 */

import { defineContentScript } from "wxt/utils/define-content-script";

const WORKSPACE_ID = "__yt_workspace";

interface Chapter {
  title: string;
  timeDisplay: string;
  startSeconds: number;
}

interface VideoContext {
  videoId: string;
  url: string;
  title: string;
  lengthSeconds: number;
  chapters: Chapter[];
  chapterSource: string;
  transcriptSource: string;
  contextVersion: number;
}

function getCurrentVideoId(): string | null {
  try {
    const url = new URL(location.href);
    return url.searchParams.get("v");
  } catch {
    return null;
  }
}

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
  info.dataset.field = "video-id";
  info.textContent = `videoId: ${videoId}`;
  info.style.cssText = "opacity: 0.7; margin-bottom: 8px;";
  el.appendChild(info);

  const provenance = document.createElement("div");
  provenance.dataset.field = "provenance";
  provenance.textContent = "Loading...";
  provenance.style.cssText = "opacity: 0.6; margin-bottom: 8px; font-size: 12px;";
  el.appendChild(provenance);

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

  const chaptersEl = document.createElement("div");
  chaptersEl.dataset.field = "chapters";
  chaptersEl.textContent = "Loading chapters...";
  chaptersEl.style.cssText = "min-height: 40px;";
  el.appendChild(chaptersEl);

  return el;
}

function renderVideoContext(
  workspace: HTMLElement,
  ctx: VideoContext | null,
): void {
  const videoIdEl = workspace.querySelector('[data-field="video-id"]');
  if (videoIdEl) {
    videoIdEl.textContent = `videoId: ${ctx?.videoId ?? "unknown"}`;
  }

  const provenanceEl = workspace.querySelector('[data-field="provenance"]');
  if (provenanceEl) {
    if (ctx) {
      provenanceEl.textContent = `chapterSource: ${ctx.chapterSource} | transcriptSource: ${ctx.transcriptSource} | v${ctx.contextVersion}`;
    } else {
      provenanceEl.textContent = "No context (stale or rejected)";
    }
  }

  const chaptersEl = workspace.querySelector('[data-field="chapters"]');
  if (chaptersEl) {
    chaptersEl.innerHTML = "";
    if (ctx && ctx.chapters.length > 0) {
      for (const ch of ctx.chapters) {
        const row = document.createElement("div");
        row.style.cssText =
          "padding: 4px 0; cursor: pointer; border-bottom: 1px solid #222;";
        const time = document.createElement("span");
        time.textContent = ch.timeDisplay;
        time.style.cssText = "color: #3ea6ff; margin-right: 8px; min-width: 60px; display: inline-block;";
        row.appendChild(time);
        const title = document.createElement("span");
        title.textContent = ch.title;
        row.appendChild(title);
        chaptersEl.appendChild(row);
      }
    } else {
      chaptersEl.textContent = "No chapters found";
    }
  }
}

function mountWorkspace(ctx: VideoContext | null): void {
  const existing = document.querySelectorAll(`#${WORKSPACE_ID}`);
  if (existing.length > 1) {
    existing[1]?.remove();
  }
  if (existing.length === 1) {
    return;
  }
  const videoId = getCurrentVideoId() ?? "unknown";
  const workspace = createWorkspaceElement(videoId);
  const secondary = document.querySelector("#secondary");
  if (secondary) {
    secondary.prepend(workspace);
    renderVideoContext(workspace, ctx);
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
          mountWorkspace(message.videoContext ?? null);
        } else {
          detachWorkspace();
        }
      } else if (message?.type === "workspace-update") {
        const workspace = document.querySelector(`#${WORKSPACE_ID}`);
        if (workspace) {
          renderVideoContext(workspace as HTMLElement, message.videoContext ?? null);
        }
      }
      return false;
    });

    document.addEventListener("yt-navigate-finish", () => {
      chrome.runtime
        .sendMessage({ type: "yt-navigate-finish", url: location.href })
        .catch(() => {});

      const workspace = document.querySelector(`#${WORKSPACE_ID}`);
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
