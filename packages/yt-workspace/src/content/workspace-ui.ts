/**
 * Workspace UI — element creation, tab switching, chapter rendering.
 *
 * 5 tabs: Chapters | Overview | Ask | Transcript | Links
 * All DOM construction uses createElement/textContent (Trusted Types).
 */

import type { Chapter } from "../lib/video-context-store";
import { attachSeekHandlers } from "./seek-handler";
import {
  createSettingsButton,
  applyFontSize,
  type WorkspaceSettings,
} from "./settings";
import { renderOverview } from "./overview";
import { renderAsk } from "./ask";
import { renderTranscript, fetchTranscript } from "./transcript";
import { renderLinks } from "./links";

const WORKSPACE_ID = "__yt_workspace";

export interface VideoContextData {
  videoId: string;
  url: string;
  title: string;
  lengthSeconds: number;
  chapters: Chapter[];
  captionTracks: Array<{
    languageCode: string;
    kind: string;
    name: string;
    baseUrl: string;
  }>;
  chapterSource: string;
  transcriptSource: string;
  contextVersion: number;
  description: string | null;
}

type TabName = "chapters" | "overview" | "ask" | "transcript" | "links";

const TAB_LABELS: Array<{ name: TabName; label: string }> = [
  { name: "chapters", label: "Chapters" },
  { name: "overview", label: "Overview" },
  { name: "ask", label: "Ask" },
  { name: "transcript", label: "Transcript" },
  { name: "links", label: "Links" },
];

let activeTab: TabName = "chapters";
let currentCtx: VideoContextData | null = null;
type TranscriptData = {
  segments: Array<{ startMs: number; text: string }>;
  trackLabel: string;
};

let transcriptData: TranscriptData | null = null;
let transcriptFetchPromise: Promise<TranscriptData | null> | null = null;

async function doFetchTranscript(
  tracks: VideoContextData["captionTracks"],
): Promise<TranscriptData | null> {
  const data = await fetchTranscript(tracks as any);
  transcriptData = data as TranscriptData | null;
  transcriptFetchPromise = null;
  return data as TranscriptData | null;
}

function switchTab(tabName: TabName, workspace: HTMLElement): void {
  activeTab = tabName;

  workspace.querySelectorAll(".ytws-tab").forEach((tabEl) => {
    const tab = tabEl as HTMLElement;
    const isActive = tab.dataset.tab === tabName;
    tab.className = isActive
      ? "ytws-tab ytws-tab-active"
      : "ytws-tab ytws-tab-clickable";
  });

  const contentEl = workspace.querySelector('[data-field="tab-content"]');
  if (!contentEl) return;

  while (contentEl.firstChild) {
    contentEl.removeChild(contentEl.firstChild);
  }

  const el = contentEl as HTMLElement;

  switch (tabName) {
    case "chapters":
      renderChapters(el, currentCtx);
      if (currentCtx && currentCtx.chapters.length > 0) {
        attachSeekHandlers(workspace, currentCtx.chapters);
      }
      break;
    case "overview":
      renderOverview(el, {
        description: currentCtx?.description ?? null,
        chapters: currentCtx?.chapters ?? [],
        title: currentCtx?.title ?? "(unknown)",
      });
      break;
    case "ask":
      renderAsk(el, transcriptData?.segments ?? null);
      break;
    case "transcript":
      renderTranscript(el, transcriptData);
      if (!transcriptData && currentCtx && currentCtx.captionTracks.length > 0) {
        if (!transcriptFetchPromise) {
          transcriptFetchPromise = doFetchTranscript(currentCtx.captionTracks);
          transcriptFetchPromise.then((data) => {
            if (activeTab === "transcript") {
              renderTranscript(el, data);
            }
          });
        }
        const loading = document.createElement("div");
        loading.className = "ytws-empty";
        loading.textContent = "Loading transcript...";
        el.appendChild(loading);
      }
      break;
    case "links":
      renderLinks(el, currentCtx?.description ?? null);
      break;
  }
}

function renderChapters(
  el: HTMLElement,
  ctx: VideoContextData | null,
): void {
  if (ctx && ctx.chapters.length > 0) {
    for (const ch of ctx.chapters) {
      const row = document.createElement("div");
      row.className = "ytws-chapter-row";

      const time = document.createElement("span");
      time.textContent = ch.timeDisplay;
      time.className = "ytws-chapter-time";
      row.appendChild(time);

      const title = document.createElement("span");
      title.textContent = ch.title;
      title.className = "ytws-chapter-title";
      row.appendChild(title);

      el.appendChild(row);
    }
  } else {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "No chapters found";
    el.appendChild(empty);
  }
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
  for (const tab of TAB_LABELS) {
    const tabEl = document.createElement("span");
    tabEl.textContent = tab.label;
    tabEl.dataset.tab = tab.name;
    tabEl.className =
      tab.name === "chapters"
        ? "ytws-tab ytws-tab-active"
        : "ytws-tab ytws-tab-clickable";
    tabEl.addEventListener("click", () => {
      switchTab(tab.name, el);
    });
    tabsBar.appendChild(tabEl);
  }
  el.appendChild(tabsBar);

  const contentEl = document.createElement("div");
  contentEl.dataset.field = "tab-content";
  contentEl.className = "ytws-tab-content";
  el.appendChild(contentEl);

  return el;
}

export function renderVideoContext(
  workspace: HTMLElement,
  ctx: VideoContextData | null,
): void {
  currentCtx = ctx;
  transcriptData = null;
  transcriptFetchPromise = null;

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

  switchTab(activeTab, workspace);
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
