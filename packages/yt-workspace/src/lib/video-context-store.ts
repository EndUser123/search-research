/**
 * VideoContext state machine — freshness invariant + diagnostic emission.
 *
 * The core contract from Gate 2:
 *   result.videoId === state.currentAuthoritativeVideoId ? accepted : rejected_stale
 *
 * Every applyResult() call emits a structured diagnostic via the durable writer.
 * The state machine is per-tab — each tab has its own authoritative videoId.
 */

import {
  appendDiagnostic,
  type Diagnostic,
  type DiagnosticContext,
} from "./structured-diagnostic";

export type ChapterSource = "native" | "auto" | "desc" | "none";
export type TranscriptSource = "timedtext" | "innertube" | "whisper" | "none";

export interface Chapter {
  title: string;
  timeDisplay: string;
  startSeconds: number;
}

export interface VideoContext {
  videoId: string;
  url: string;
  title: string;
  lengthSeconds: number;
  chapters: Chapter[];
  captionTracks: CaptionTrack[];
  chapterSource: ChapterSource;
  transcriptSource: TranscriptSource;
  contextVersion: number;
  description: string | null;
}

export interface CaptionTrack {
  languageCode: string;
  kind: string;
  name: string;
  baseUrl: string;
}

export type Disposition = "accepted" | "rejected_stale";

export interface ApplyResult {
  disposition: Disposition;
  diagnostic: Diagnostic;
  context: VideoContext | null;
}

interface TabState {
  currentAuthoritativeVideoId: string | null;
  currentUrl: string;
  lastAccepted: VideoContext | null;
  contextVersion: number;
}

const tabStates = new Map<number, TabState>();

function getTabState(tabId: number): TabState {
  let state = tabStates.get(tabId);
  if (!state) {
    state = {
      currentAuthoritativeVideoId: null,
      currentUrl: "",
      lastAccepted: null,
      contextVersion: 0,
    };
    tabStates.set(tabId, state);
  }
  return state;
}

export function setAuthoritativeVideoId(
  tabId: number,
  videoId: string,
  url: string,
): void {
  const state = getTabState(tabId);
  state.currentAuthoritativeVideoId = videoId;
  state.currentUrl = url;
}

export function getAuthoritativeVideoId(tabId: number): string | null {
  return getTabState(tabId).currentAuthoritativeVideoId;
}

export function getLastAccepted(tabId: number): VideoContext | null {
  return getTabState(tabId).lastAccepted;
}

export function clearTabState(tabId: number): void {
  tabStates.delete(tabId);
}

export async function applyResult(
  tabId: number,
  result: VideoContext,
): Promise<ApplyResult> {
  const state = getTabState(tabId);
  state.contextVersion += 1;

  const isAccepted =
    state.currentAuthoritativeVideoId === result.videoId;

  const disposition: Disposition = isAccepted ? "accepted" : "rejected_stale";

  const ctx: DiagnosticContext = {
    contextVersion: state.contextVersion,
    chapterCount: result.chapters.length,
    chapterSource: result.chapterSource,
    transcriptSource: result.transcriptSource,
  };

  const diagnostic: Diagnostic = {
    resultVideoId: result.videoId,
    activeVideoId: state.currentAuthoritativeVideoId ?? "(none)",
    disposition,
    timestamp: new Date().toISOString(),
    sourceUrl: result.url,
    activeUrl: state.currentUrl,
    context: ctx,
  };

  await appendDiagnostic(diagnostic);

  if (isAccepted) {
    state.lastAccepted = result;
  }

  return {
    disposition,
    diagnostic,
    context: isAccepted ? result : null,
  };
}

export function persistContext(tabId: number, ctx: VideoContext): Promise<void> {
  return chrome.storage.local.set({
    [`videoContext-${tabId}`]: ctx,
  });
}

export async function readPersistedContext(
  tabId: number,
): Promise<VideoContext | null> {
  const key = `videoContext-${tabId}`;
  const result = await chrome.storage.local.get(key);
  return (result[key] as VideoContext | undefined) ?? null;
}
