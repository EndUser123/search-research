/**
 * Settings overlay — font size control for the workspace.
 *
 * Gear icon in the header opens a small popup with a font size slider.
 * Preference persisted in chrome.storage.local as "ytws-settings".
 */

const STORAGE_KEY = "ytws-settings";
const DEFAULT_FONT_SIZE = 14;
const MIN_FONT_SIZE = 11;
const MAX_FONT_SIZE = 22;

export interface WorkspaceSettings {
  fontSize: number;
  autoOpen: boolean;
}

export async function loadSettings(): Promise<WorkspaceSettings> {
  const result = await chrome.storage.local.get(STORAGE_KEY);
  const stored = result[STORAGE_KEY] as Partial<WorkspaceSettings> | undefined;
  return {
    fontSize: stored?.fontSize ?? DEFAULT_FONT_SIZE,
    autoOpen: stored?.autoOpen ?? true,
  };
}

export async function saveSettings(settings: WorkspaceSettings): Promise<void> {
  await chrome.storage.local.set({ [STORAGE_KEY]: settings });
}

export function applyFontSize(
  workspace: HTMLElement,
  fontSize: number,
): void {
  workspace.style.fontSize = `${fontSize}px`;
}

export function createSettingsButton(
  workspace: HTMLElement,
  settings: WorkspaceSettings,
  onSettingsChange: (s: WorkspaceSettings) => void,
): HTMLElement {
  const container = document.createElement("div");
  container.className = "ytws-settings-container";

  const gear = document.createElement("button");
  gear.className = "ytws-gear";
  gear.textContent = "⚙";
  gear.title = "Settings";
  container.appendChild(gear);

  const panel = document.createElement("div");
  panel.className = "ytws-settings-panel";

  const label = document.createElement("label");
  label.textContent = "Font size";
  label.className = "ytws-settings-label";
  panel.appendChild(label);

  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = String(MIN_FONT_SIZE);
  slider.max = String(MAX_FONT_SIZE);
  slider.step = "1";
  slider.value = String(settings.fontSize);
  slider.className = "ytws-settings-slider";
  panel.appendChild(slider);

  const valueDisplay = document.createElement("span");
  valueDisplay.textContent = `${settings.fontSize}px`;
  valueDisplay.className = "ytws-settings-value";
  panel.appendChild(valueDisplay);

  const divider = document.createElement("div");
  divider.style.cssText = "width:100%;height:1px;background:#303030;margin:8px 0;";
  panel.appendChild(divider);

  const autoOpenLabel = document.createElement("label");
  autoOpenLabel.textContent = "Auto-open on YouTube";
  autoOpenLabel.className = "ytws-settings-label";
  panel.appendChild(autoOpenLabel);

  const autoOpenCheckbox = document.createElement("input");
  autoOpenCheckbox.type = "checkbox";
  autoOpenCheckbox.checked = settings.autoOpen;
  autoOpenCheckbox.className = "ytws-settings-checkbox";
  panel.appendChild(autoOpenCheckbox);

  autoOpenCheckbox.addEventListener("change", () => {
    settings.autoOpen = autoOpenCheckbox.checked;
    onSettingsChange(settings);
  });

  slider.addEventListener("input", () => {
    const newSize = Number(slider.value);
    valueDisplay.textContent = `${newSize}px`;
    applyFontSize(workspace, newSize);
    settings.fontSize = newSize;
    onSettingsChange(settings);
  });

  container.appendChild(panel);

  gear.addEventListener("click", (e) => {
    e.stopPropagation();
    panel.classList.toggle("ytws-settings-panel-open");
  });

  document.addEventListener("click", (e) => {
    if (!container.contains(e.target as Node)) {
      panel.classList.remove("ytws-settings-panel-open");
    }
  });

  return container;
}

export { DEFAULT_FONT_SIZE };
