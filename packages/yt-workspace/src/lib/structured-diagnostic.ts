/**
 * Structured diagnostic types + durable writer.
 *
 * Writes diagnostics to chrome.storage.local under the key "diagnostics".
 * Capped at MAX_DIAGNOSTICS entries (oldest evicted on overflow).
 *
 * Diagnostic shape matches Gate 2 spec:
 * {resultVideoId, activeVideoId, disposition, timestamp, sourceUrl, activeUrl, context}
 */

export type Disposition = "accepted" | "rejected_stale";

export interface DiagnosticContext {
  contextVersion: number;
  chapterCount: number;
  chapterSource?: string;
  transcriptSource?: string;
}

export interface Diagnostic {
  resultVideoId: string;
  activeVideoId: string;
  disposition: Disposition;
  timestamp: string;
  sourceUrl: string;
  activeUrl: string;
  context: DiagnosticContext;
}

const STORAGE_KEY = "diagnostics";
const MAX_DIAGNOSTICS = 500;

export async function appendDiagnostic(diag: Diagnostic): Promise<void> {
  const result = await chrome.storage.local.get(STORAGE_KEY);
  const entries: Diagnostic[] = (result[STORAGE_KEY] as Diagnostic[] | undefined) ?? [];

  entries.push(diag);

  if (entries.length > MAX_DIAGNOSTICS) {
    const evicted = entries.length - MAX_DIAGNOSTICS;
    entries.splice(0, evicted);
  }

  await chrome.storage.local.set({ [STORAGE_KEY]: entries });
}

export async function readDiagnostics(): Promise<Diagnostic[]> {
  const result = await chrome.storage.local.get(STORAGE_KEY);
  return (result[STORAGE_KEY] as Diagnostic[] | undefined) ?? [];
}

export async function clearDiagnostics(): Promise<void> {
  await chrome.storage.local.remove(STORAGE_KEY);
}
