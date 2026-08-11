/**
 * Background service worker entry point (WXT entrypoint).
 *
 * VS-02: delegates to service-worker module for acquisition + workspace logic.
 */

import { defineBackground } from "wxt/utils/define-background";
import {
  handleToolbarClick,
  handleNavigationMessage,
  handleTabClosed,
} from "../background/service-worker";

export default defineBackground(() => {
  chrome.action.onClicked.addListener((tab) => {
    void handleToolbarClick(tab);
  });

  chrome.runtime.onMessage.addListener((message, sender) => {
    if (
      message?.type === "yt-navigate-finish" &&
      sender.tab?.id &&
      sender.tab.url
    ) {
      void handleNavigationMessage(sender.tab.id, sender.tab.url);
    }
    return false;
  });

  chrome.tabs.onRemoved.addListener((tabId) => {
    handleTabClosed(tabId);
  });
});
