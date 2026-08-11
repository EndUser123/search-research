/**
 * Resize handle — draggable divider to adjust YouTube's #primary / #secondary split.
 *
 * Injects a vertical drag bar at the left edge of #secondary.
 * On drag, adjusts #primary flex-basis to resize the columns.
 * Preference persisted in chrome.storage.local as "ytws-primary-width-pct".
 */

const STORAGE_KEY = "ytws-primary-width-pct";
const DEFAULT_PCT = 64; // YouTube default: primary is ~64% width
const MIN_PCT = 30;
const MAX_PCT = 80;
const HANDLE_ID = "__yt_workspace_resizer";

export async function loadResizePreference(): Promise<number | null> {
  const result = await chrome.storage.local.get(STORAGE_KEY);
  const pct = result[STORAGE_KEY] as number | undefined;
  return typeof pct === "number" ? pct : null;
}

export async function saveResizePreference(pct: number): Promise<void> {
  await chrome.storage.local.set({ [STORAGE_KEY]: pct });
}

export function applyResize(pct: number): void {
  const primary = document.querySelector("#primary") as HTMLElement | null;
  const secondary = document.querySelector("#secondary") as HTMLElement | null;
  if (!primary || !secondary) return;

  primary.style.flexBasis = `${pct}%`;
  secondary.style.flexBasis = `${100 - pct}%`;
}

export function clearResize(): void {
  const primary = document.querySelector("#primary") as HTMLElement | null;
  const secondary = document.querySelector("#secondary") as HTMLElement | null;
  if (primary) primary.style.flexBasis = "";
  if (secondary) secondary.style.flexBasis = "";
  const handle = document.getElementById(HANDLE_ID);
  if (handle) handle.remove();
}

export function mountResizer(onChange: (pct: number) => void): void {
  const existing = document.getElementById(HANDLE_ID);
  if (existing) return;

  const secondary = document.querySelector("#secondary") as HTMLElement | null;
  const columns = document.querySelector("#columns") as HTMLElement | null;
  if (!secondary || !columns) return;

  const handle = document.createElement("div");
  handle.id = HANDLE_ID;
  handle.className = "ytws-resizer";
  handle.title = "Drag to resize";

  let isDragging = false;

  handle.addEventListener("mousedown", (e) => {
    e.preventDefault();
    isDragging = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const columnsRect = columns.getBoundingClientRect();
    const x = e.clientX - columnsRect.left;
    let pct = (x / columnsRect.width) * 100;
    pct = Math.max(MIN_PCT, Math.min(MAX_PCT, pct));

    applyResize(pct);
    onChange(pct);
  });

  document.addEventListener("mouseup", () => {
    if (!isDragging) return;
    isDragging = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  });

  // Insert the handle before #secondary (at the boundary between primary and secondary)
  if (secondary.parentElement) {
    secondary.parentElement.insertBefore(handle, secondary);
  }
}

export { DEFAULT_PCT, HANDLE_ID };
