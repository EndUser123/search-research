/**
 * Background service worker entry point.
 *
 * VS-01 scope: toolbar action toggles workspace visibility on YouTube tabs.
 * No-op on non-YouTube tabs. The real acquisition/seek logic lands in VS-02..04.
 */
import { defineBackground } from "wxt/utils/define-background";

const YOUTUBE_HOST_PATTERN = /^https?:\/\/([a-z0-9-]+\.)*youtube\.com\//i;

export default defineBackground(() => {
  chrome.action.onClicked.addListener(async (tab) => {
    if (!tab.id || !tab.url || !YOUTUBE_HOST_PATTERN.test(tab.url)) {
      return;
    }

    const key = `workspace-open-${tab.id}`;
    const result = await chrome.storage.session.get(key);
    const isOpen = result[key] ?? false;
    const nextState = !isOpen;

    await chrome.storage.session.set({ [key]: nextState });

    chrome.tabs.sendMessage(tab.id, {
      type: "workspace-toggle",
      open: nextState,
    }).catch(() => {
      if (nextState) {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content-scripts/content.js"],
        }).catch(() => {});
      }
    });
  });
});
