/**
 * Acquisition orchestrator — reads YouTube data via MAIN-world eval.
 *
 * Gate 2 correction: chapters come from ytInitialData.engagementPanels,
 * NOT from ytInitialPlayerResponse. The player response has zero chapter
 * fields. This file uses a single MAIN-world eval that reads both
 * player data and chapter data.
 *
 * The readYouTubeData function is serialized by Chrome for MAIN-world
 * injection — it must be fully self-contained (no closures, no imports).
 */

import {
  applyResult,
  setAuthoritativeVideoId,
  persistContext,
  type VideoContext,
  type Chapter,
  type CaptionTrack,
  type ChapterSource,
  type TranscriptSource,
} from "../lib/video-context-store";

// This function is serialized by Chrome for MAIN-world injection.
// Do NOT add closure references, imports, or external types.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function readYouTubeData(): any {
  const parseTimestampToSeconds = (ts: string): number | null => {
    const parts = ts.split(":").map(Number);
    if (parts.length < 2 || parts.some((n) => !Number.isFinite(n))) return null;
    if (parts.length === 3) return (parts[0] ?? 0) * 3600 + (parts[1] ?? 0) * 60 + (parts[2] ?? 0);
    if (parts.length === 2) return (parts[0] ?? 0) * 60 + (parts[1] ?? 0);
    return null;
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result: any = {
    videoId: null,
    title: null,
    lengthSeconds: null,
    captionTracks: [],
    chapters: [],
    chapterSource: "none",
    description: null,
  };

  const mp = document.querySelector("#movie_player") as
    | (HTMLElement & { getPlayerResponse?: () => any })
    | null;
  let pr: any = null;
  if (mp && typeof mp.getPlayerResponse === "function") {
    try {
      pr = mp.getPlayerResponse();
    } catch {
      /* fallthrough */
    }
  }
  if (!pr) {
    pr = (globalThis as any).ytInitialPlayerResponse || null;
  }
  if (!pr) return result;

  const vd = pr.videoDetails || {};
  result.videoId = vd.videoId || null;
  result.title = vd.title || null;
  result.lengthSeconds = vd.lengthSeconds ? Number(vd.lengthSeconds) : null;
  result.description = vd.shortDescription || "";

  const caps =
    pr.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
  result.captionTracks = caps.map((t: any) => ({
    languageCode: t.languageCode || "",
    kind: t.kind || "",
    name: t.name?.simpleText || "",
    baseUrl: t.baseUrl || "",
  }));

  const id = (globalThis as any).ytInitialData;
  if (id && Array.isArray(id.engagementPanels)) {
    for (const panel of id.engagementPanels) {
      const mlmr =
        panel.engagementPanelSectionListRenderer?.content
          ?.macroMarkersListRenderer;
      if (mlmr && Array.isArray(mlmr.contents)) {
        const chapters: any[] = [];
        for (const item of mlmr.contents) {
          const r = item.macroMarkersListItemRenderer;
          if (!r) continue;
          const title: string = r.title?.simpleText || "";
          const timeSimple: string = r.timeDescription?.simpleText || "";
          const startSeconds: number | null =
            r.onTap?.watchEndpoint?.startTimeSeconds ??
            parseTimestampToSeconds(timeSimple);
          if (title) {
            chapters.push({
              title,
              timeDisplay: timeSimple,
              startSeconds: startSeconds != null ? startSeconds : 0,
            });
          }
        }
        if (chapters.length > 0) {
          result.chapters = chapters;
          result.chapterSource = "native";
          break;
        }
      }
    }
  }

  if (result.chapters.length === 0 && result.description) {
    const regex = /(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)/g;
    const descChapters: any[] = [];
    let m: RegExpExecArray | null;
    while ((m = regex.exec(result.description)) !== null) {
      const ts = m[1];
      const label = m[2];
      if (!ts || !label) continue;
      const seconds = parseTimestampToSeconds(ts);
      if (seconds !== null) {
        descChapters.push({
          title: label.trim(),
          timeDisplay: ts,
          startSeconds: seconds,
        });
      }
    }
    if (descChapters.length > 0) {
      result.chapters = descChapters;
      result.chapterSource = "desc";
    }
  }

  return result;
}

interface AcquisitionResult {
  videoId: string | null;
  title: string | null;
  lengthSeconds: number | null;
  captionTracks: Array<{
    languageCode: string;
    kind: string;
    name: string;
    baseUrl: string;
  }>;
  chapters: Chapter[];
  chapterSource: ChapterSource;
  description: string | null;
}

export async function acquireVideoContext(
  tabId: number,
): Promise<VideoContext | null> {
  let result: AcquisitionResult | null = null;

  try {
    const [injection] = await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN" as chrome.scripting.ExecutionWorld,
      func: readYouTubeData,
    });
    result = (injection?.result as AcquisitionResult) ?? null;
  } catch {
    return null;
  }

  if (!result || !result.videoId) {
    return null;
  }

  const transcriptSource: TranscriptSource =
    result.captionTracks.length > 0 ? "timedtext" : "none";

  const ctx: VideoContext = {
    videoId: result.videoId,
    url: `https://www.youtube.com/watch?v=${result.videoId}`,
    title: result.title ?? "(unknown)",
    lengthSeconds: result.lengthSeconds ?? 0,
    chapters: result.chapters,
    captionTracks: result.captionTracks as CaptionTrack[],
    chapterSource: result.chapterSource,
    transcriptSource,
    contextVersion: 0,
  };

  setAuthoritativeVideoId(tabId, ctx.videoId, ctx.url);

  const applied = await applyResult(tabId, ctx);

  if (applied.disposition === "accepted") {
    await persistContext(tabId, ctx);
  }

  return applied.context;
}
