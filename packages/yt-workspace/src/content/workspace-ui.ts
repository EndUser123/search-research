/**
 * Workspace UI — element creation + chapter rendering.
 *
 * All DOM construction uses createElement/textContent (YouTube enforces
 * Trusted Types — innerHTML is blocked).
 */

import type { Chapter } from "../lib/video-context-store";
import { attachSeekHandlers } from "./seek-handler";
import {
  createSettingsButton,
  applyFontSize,
  type WorkspaceSettings,
} from "./settings";

const WORKSPACE_ID = "__yt_workspace";

export interface VideoContextData {
  videoId: string;
  url: string;
  title: string;
  lengthSeconds: number;
  chapters: Chapter[];
  chapterSource: string;
  transcriptSource: string;
  contextVersion: number;
}

export function createWorkspaceElement(
  videoId: string,
  settings: WorkspaceSettings,
  onSettingsChange: (s: WorkspaceSettings) => void,
): HTMLElement {
  const el = document.createElement("div");
  el.id = WORKSPACE_ID;
  el.className = "ytws-workspace";
  applyFontSize(el, settings.fontSize);

  const header = document.createElement("div");
  header.className = "ytws-header";

  const title = document.createElement("strong");
  title.textContent = "YT Workspace";
  title.className = "ytws-title";
  header.appendChild(title);

  const gear = createSettingsButton(el, settings, onSettingsChange);
  gear.className += " ytws-header-gear";
  header.appendChild(gear);

  el.appendChild(header);

  const info = document.createElement("div");
  info.dataset.field = "video-id";
  info.textContent = `videoId: ${videoId}`;
  info.className = "ytws-info";
  el.appendChild(info);

  const provenance = document.createElement("div");
  provenance.dataset.field = "provenance";
  provenance.textContent = "Loading...";
  provenance.className = "ytws-provenance";
  el.appendChild(provenance);

  const tabsBar = document.createElement("div");
  tabsBar.className = "ytws-tabs";
  const tabNames = ["Chapters", "Overview", "Ask", "Transcript", "Links"];
  for (const name of tabNames) {
    const tab = document.createElement("span");
    tab.textContent = name;
    const isChapters = name === "Chapters";
    tab.className = isChapters
      ? "ytws-tab ytws-tab-active"
      : "ytws-tab ytws-tab-disabled";
    if (!isChapters) {
      tab.title = "Coming soon";
    }
    tabsBar.appendChild(tab);
  }
  el.appendChild(tabsBar);

  const chaptersEl = document.createElement("div");
  chaptersEl.dataset.field = "chapters";
  chaptersEl.textContent = "Loading chapters...";
  chaptersEl.className = "ytws-chapters";
  el.appendChild(chaptersEl);

  return el;
}

export function renderVideoContext(
  workspace: HTMLElement,
  ctx: VideoContextData | null,
): void {
  const videoIdEl = workspace.querySelector('[data-field="video-id"]');
  if (videoIdEl) {
    videoIdEl.textContent = `videoId: ${ctx?.videoId ?? "unknown"}`;
  }

  const provenanceEl = workspace.querySelector('[data-field="provenance"]');
  if (provenanceEl) {
    if (ctx) {
      const parts = [
        `chapterSource: ${ctx.chapterSource}`,
        `transcriptSource: ${ctx.transcriptSource}`,
        `v${ctx.contextVersion}`,
        `${ctx.chapters.length} chapters`,
      ];
      provenanceEl.textContent = parts.join(" | ");
    } else {
      provenanceEl.textContent = "No context (stale or rejected)";
    }
  }

  const chaptersEl = workspace.querySelector('[data-field="chapters"]');
  if (chaptersEl) {
    while (chaptersEl.firstChild) {
      chaptersEl.removeChild(chaptersEl.firstChild);
    }
    if (ctx && ctx.chapters.length > 0) {
      for (const ch of ctx.chapters) {
        const row = document.createElement("div");
        row.className = "ytws-chapter-row";

        const time = document.createElement("span");
        time.textContent = ch.timeDisplay;
        time.className = "ytws-chapter-time";
        row.appendChild(time);

        const chapterTitle = document.createElement("span");
        chapterTitle.textContent = ch.title;
        chapterTitle.className = "ytws-chapter-title";
        row.appendChild(chapterTitle);

        chaptersEl.appendChild(row);
      }
      attachSeekHandlers(workspace, ctx.chapters);
    } else {
      const empty = document.createElement("div");
      empty.textContent = "No chapters found";
      empty.className = "ytws-empty";
      chaptersEl.appendChild(empty);
    }
  }
}

export function mountWorkspace(
  ctx: VideoContextData | null,
  settings: WorkspaceSettings,
  onSettingsChange: (s: WorkspaceSettings) => void,
): void {
  const existing = document.querySelectorAll(`#${WORKSPACE_ID}`);
  if (existing.length > 1) {
    existing[1]?.remove();
  }
  if (existing.length === 1) {
    return;
  }
  const url = new URL(location.href);
  const videoId = url.searchParams.get("v") ?? "unknown";
  const workspace = createWorkspaceElement(videoId, settings, onSettingsChange);
  const secondary = document.querySelector("#secondary");
  if (secondary) {
    secondary.prepend(workspace);
    renderVideoContext(workspace, ctx);
  }
}

export function detachWorkspace(): void {
  document.querySelectorAll(`#${WORKSPACE_ID}`).forEach((el) => el.remove());
}

export function getWorkspaceElement(): HTMLElement | null {
  return document.querySelector(`#${WORKSPACE_ID}`) as HTMLElement | null;
}

export { WORKSPACE_ID };
